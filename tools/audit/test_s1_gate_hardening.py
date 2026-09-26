#!/usr/bin/env python3
"""Adversarial regression tests for the S1 security gates — hardening coverage
carried forward from the preserved INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001
findings F1–F9 (historical evidence), re-applied to the clean rebuild under
REMEDIATION-SESSION-S1-CLEAN-REBUILD-001.

Every negative mutation must make the relevant gate FAIL for the intended
reason (asserted by message), and every control must PASS. F2/F7 use real
Git repositories (normal + linked worktree); F1/F6 use real ZIP archives.
"""

import hashlib
import importlib.util
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nb = _load("rr_native_build", "tools/security/native_build.py")
apk_v = _load("rr_apk_validate", "tools/security/validate_apk_contents.py")
ci_v = _load("rr_ci_validate", "tools/security/validate_ci_pipeline.py")
scan = _load("rr_secret_scan", "tools/security/secret_scan.py")
mx = _load("rr_b021_matrix", "tools/audit/validate_b021_verification_matrix.py")
s1 = _load("rr_s1_static", "tools/audit/validate_s1_build_provenance.py")
ef = _load("rr_elf_fixture", "tools/audit/elf_fixture.py")

CI = ".github/workflows/ci.yml"
MSC_STATE = "docs/security/remediation/msc_state.jsonl"
MATRIX = "docs/workforce/registries/b021_verification_matrix.jsonl"
INV_REG = "docs/workforce/registries/security_invariant_traceability.jsonl"


EXPECTED_JNI = sorted(nb.expected_jni_exports(str(REPO_ROOT), []))
JNI_FP = nb.sha256_text("\n".join(EXPECTED_JNI))


def _fake_elf(e_machine, exports=None, payload=b""):
    return ef.fake_elf_so(e_machine, EXPECTED_JNI if exports is None else exports, payload)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


ARM64_SO = _fake_elf(183, payload=b"arm64-payload")
X86_SO = _fake_elf(62, payload=b"x86_64-payload")


LOCK_SHA = nb.sha256_file(REPO_ROOT / "crypto/rust/Cargo.lock")
FIXTURE_SRC_SHA = "0" * 40


def _manifest(confirmed=True, working_tree="clean", arm64_sha=None, x86_sha=None):
    a, x = arm64_sha or _sha(ARM64_SO), x86_sha or _sha(X86_SO)
    return {
        "schema_version": "anox-native-manifest-v1",
        "source": {"repo_sha": FIXTURE_SRC_SHA, "crate": "crypto/rust", "crate_manifest": "crypto/rust/Cargo.toml",
                   "cargo_lock_sha256": LOCK_SHA, "rust_toolchain_file": "crypto/rust/rust-toolchain.toml",
                   "working_tree": working_tree},
        "toolchain": {"channel": "1.97.1", "ndk_revision": "26.2.11394342",
                      "cargo_ndk": "4.1.2", "rustc": "rustc 1.97.1", "host": "x86_64"},
        "build": {
            "build_id": "fixture", "profile": "release", "locked": True, "path_remapped": True,
            "reproducible_build_confirmed": confirmed,
            "reproducibility": {"method": "two-clean-builds-three-way-compare", "builds": 2,
                                "build_ids": ["r1", "r2"],
                                "per_abi_sha256": {"arm64-v8a": a, "x86_64": x}} if confirmed else None,
        },
        "abis": ["arm64-v8a", "x86_64"],
        "artifacts": [
            {"abi": "arm64-v8a", "file": "arm64-v8a/libanox_crypto.so", "sha256": a, "size": len(ARM64_SO),
             "rust_target": "aarch64-linux-android", "elf_machine": 183, "jni_export_count": len(EXPECTED_JNI),
             "jni_exports": EXPECTED_JNI, "jni_exports_sha256": JNI_FP},
            {"abi": "x86_64", "file": "x86_64/libanox_crypto.so", "sha256": x, "size": len(X86_SO),
             "rust_target": "x86_64-linux-android", "elf_machine": 62, "jni_export_count": len(EXPECTED_JNI),
             "jni_exports": EXPECTED_JNI, "jni_exports_sha256": JNI_FP},
        ],
    }


def _apk(path, members, base=True):
    with zipfile.ZipFile(path, "w") as z:
        if base:
            z.writestr("AndroidManifest.xml", b"\x03\x00\x08\x00binary")
            z.writestr("classes.dex", b"dex\n035\0fake")
            z.writestr("resources.arsc", b"arsc")
            z.writestr("lib/arm64-v8a/libanox_crypto.so", ARM64_SO)
            z.writestr("lib/x86_64/libanox_crypto.so", X86_SO)
        for name, data in members.items():
            z.writestr(name, data)


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


# ===========================================================================
# F1 — APK validator path normalization
# ===========================================================================

class F1ApkPathNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.apk = self.root / "app.apk"
        self.mpath = self.root / "m.json"
        self.mpath.write_text(json.dumps(_manifest()))

    def tearDown(self):
        self.tmp.cleanup()

    def _rc(self, members):
        _apk(self.apk, members)
        out = io.StringIO()
        with redirect_stdout(out):
            rc = apk_v.validate_apk(str(self.apk), manifest_path=str(self.mpath), expected_source_sha=FIXTURE_SRC_SHA)
        return rc, out.getvalue()

    def test_control_clean_apk_passes(self):
        rc, out = self._rc({})
        self.assertEqual(rc, 0, out)

    def test_dot_slash_lib_prefix_fails(self):
        rc, out = self._rc({"./lib/arm64-v8a/libevil.so": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("non-canonical ZIP member path", out)
        self.assertIn("native-library-like member outside canonical", out)

    def test_uppercase_lib_prefix_fails(self):
        rc, out = self._rc({"LIB/arm64-v8a/libevil.so": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("native-library-like member outside canonical", out)

    def test_mixed_case_so_extension_fails(self):
        rc, out = self._rc({"lib/arm64-v8a/libevil.SO": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("native-library-like member outside canonical", out)

    def test_so_outside_lib_fails(self):
        rc, out = self._rc({"assets/payload.so": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("native-library-like member outside canonical", out)

    def test_double_slash_fails(self):
        rc, out = self._rc({"lib//arm64-v8a/libevil.so": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("non-canonical ZIP member path", out)

    def test_traversal_segment_fails(self):
        rc, out = self._rc({"lib/arm64-v8a/../../x/libevil.so": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("non-canonical segment '..'", out)

    def test_absolute_path_fails(self):
        rc, out = self._rc({"/lib/arm64-v8a/libevil.so": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("absolute member path", out)

    def test_backslash_path_fails(self):
        rc, out = self._rc({"lib\\arm64-v8a\\libevil.so": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("backslash in member name", out)

    def test_duplicate_entry_fails_structurally(self):
        _apk(self.apk, {})
        with zipfile.ZipFile(self.apk, "a") as z:
            z.writestr("lib/arm64-v8a/libanox_crypto.so", ARM64_SO)  # identical bytes, still ambiguous
        out = io.StringIO()
        with redirect_stdout(out):
            rc = apk_v.validate_apk(str(self.apk), manifest_path=str(self.mpath), expected_source_sha=FIXTURE_SRC_SHA)
        self.assertNotEqual(rc, 0)
        self.assertIn("duplicate ZIP entry", out.getvalue())

    def test_case_ambiguous_entries_fail(self):
        rc, out = self._rc({"Assets/readme.txt": b"a", "assets/readme.txt": b"b"})
        self.assertNotEqual(rc, 0)
        self.assertIn("differing only by case", out)

    def test_nested_lib_subdir_fails(self):
        rc, out = self._rc({"lib/arm64-v8a/sub/libevil.so": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("native-library-like member outside canonical", out)

    def test_versioned_so_suffix_fails(self):
        rc, out = self._rc({"lib/arm64-v8a/libevil.so.1": _fake_elf(183)})
        self.assertNotEqual(rc, 0)
        self.assertIn("native-library-like member outside canonical", out)


# ===========================================================================
# F5 / F7 — manifest attestation fields on the APK side
# ===========================================================================

class F5F7ApkManifestAttestationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.apk = self.root / "app.apk"
        _apk(self.apk, {})
        self.mpath = self.root / "m.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _rc(self, m):
        self.mpath.write_text(json.dumps(m))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = apk_v.validate_apk(str(self.apk), manifest_path=str(self.mpath), expected_source_sha=FIXTURE_SRC_SHA)
        return rc, out.getvalue()

    def test_control_passes(self):
        rc, out = self._rc(_manifest())
        self.assertEqual(rc, 0, out)

    def test_unconfirmed_reproducibility_fails(self):
        rc, out = self._rc(_manifest(confirmed=False))
        self.assertNotEqual(rc, 0)
        self.assertIn("reproducible_build_confirmed is not True", out)

    def test_null_reproducibility_fails(self):
        m = _manifest()
        m["build"]["reproducible_build_confirmed"] = None
        rc, out = self._rc(m)
        self.assertNotEqual(rc, 0)
        self.assertIn("reproducible_build_confirmed is not True", out)

    def test_string_true_is_not_true(self):
        m = _manifest()
        m["build"]["reproducible_build_confirmed"] = "true"
        rc, out = self._rc(m)
        self.assertNotEqual(rc, 0)

    def test_dirty_tree_manifest_fails(self):
        rc, out = self._rc(_manifest(working_tree="dirty"))
        self.assertNotEqual(rc, 0)
        self.assertIn("working_tree='dirty'", out)

    def test_missing_working_tree_fails(self):
        m = _manifest()
        del m["source"]["working_tree"]
        rc, out = self._rc(m)
        self.assertNotEqual(rc, 0)
        self.assertIn("working_tree=None", out)


# ===========================================================================
# F5 / F7 — native_build verify + attestation writer
# ===========================================================================

class F5F7NativeBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in ("crypto/rust/rust-toolchain.toml", "crypto/rust/Cargo.lock",
                    "crypto/android/src/main/java/com/anox/crypto/CryptoNative.kt",
                    "crypto/rust/src/lib.rs"):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)
        self.prod = self.root / "build/native/jniLibs"
        (self.prod / "arm64-v8a").mkdir(parents=True)
        (self.prod / "x86_64").mkdir(parents=True)
        (self.prod / "arm64-v8a/libanox_crypto.so").write_bytes(ARM64_SO)
        (self.prod / "x86_64/libanox_crypto.so").write_bytes(X86_SO)
        self.mpath = self.root / "build/native/native-manifest.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, **over):
        errs = []
        expected = nb.expected_jni_exports(str(self.root), errs)
        fp = nb.sha256_text("\n".join(sorted(expected)))
        m = _manifest()
        m["source"].update({"cargo_lock_sha256": nb.sha256_file(self.root / "crypto/rust/Cargo.lock"),
                            "crate": "crypto/rust", "crate_manifest": "crypto/rust/Cargo.toml",
                            "rust_toolchain_file": "crypto/rust/rust-toolchain.toml"})
        m["toolchain"]["host"] = "x86_64"
        for a in m["artifacts"]:
            a["rust_target"] = nb.REQUIRED_ABIS[a["abi"]]
            a["jni_exports_sha256"] = fp
            a["jni_export_count"] = len(expected)
        for k, v in over.items():
            sect, key = k.split(".")
            m[sect][key] = v
        self.mpath.write_text(json.dumps(m))
        return m

    def _verify(self):
        return nb.verify_manifest(str(self.root), str(self.mpath), str(self.prod),
                                  expected_source_sha="0" * 40, require_clean_live_tree=False)

    def test_control_passes(self):
        self._write()
        self.assertEqual(self._verify(), [])

    def test_unconfirmed_fails(self):
        m = self._write()
        m["build"]["reproducible_build_confirmed"] = False
        self.mpath.write_text(json.dumps(m))
        self.assertTrue(any("reproducible_build_confirmed is not True" in e for e in self._verify()))

    def test_attestation_hash_mismatch_fails(self):
        m = self._write()
        m["build"]["reproducibility"]["per_abi_sha256"]["x86_64"] = "f" * 64
        self.mpath.write_text(json.dumps(m))
        self.assertTrue(any("per_abi_sha256 does not equal artifact hashes" in e for e in self._verify()))

    def test_attestation_malformed_fails(self):
        m = self._write()
        m["build"]["reproducibility"]["builds"] = 1
        self.mpath.write_text(json.dumps(m))
        self.assertTrue(any("attestation malformed" in e for e in self._verify()))

    def test_dirty_manifest_fails(self):
        self._write(**{"source.working_tree": "dirty"})
        self.assertTrue(any("working_tree='dirty'" in e for e in self._verify()))

    def test_attest_refuses_missing_primary(self):
        errs = nb.attest_reproducibility(str(self.root / "nope.json"), {"artifacts": []}, {"artifacts": []}, [])
        self.assertTrue(any("primary manifest missing" in e for e in errs))

    def test_attest_refuses_partial_abi(self):
        m = self._write()
        m["build"]["reproducible_build_confirmed"] = False
        m["artifacts"] = m["artifacts"][:1]
        self.mpath.write_text(json.dumps(m))
        same = {"artifacts": [{"abi": "arm64-v8a", "sha256": _sha(ARM64_SO)}]}
        errs = nb.attest_reproducibility(str(self.mpath), same, same, ["a", "b"])
        self.assertTrue(any("required ABI set" in e for e in errs), str(errs))
        self.assertIs(json.loads(self.mpath.read_text())["build"]["reproducible_build_confirmed"], False)


class F7DirtyTreeRealGitTests(unittest.TestCase):
    """write_manifest / verify against real repositories (clean vs dirty)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        for rel in ("crypto/rust/rust-toolchain.toml", "crypto/rust/Cargo.lock",
                    "crypto/android/src/main/java/com/anox/crypto/CryptoNative.kt",
                    "crypto/rust/src/lib.rs"):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)
        (self.root / ".gitignore").write_text("build/\n")
        _git(self.root, "init", "-q")
        _git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
        _git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init")
        self.prod = self.root / "build/native/jniLibs"
        (self.prod / "arm64-v8a").mkdir(parents=True)
        (self.prod / "x86_64").mkdir(parents=True)
        (self.prod / "arm64-v8a/libanox_crypto.so").write_bytes(ARM64_SO)
        (self.prod / "x86_64/libanox_crypto.so").write_bytes(X86_SO)
        self.mpath = self.root / "build/native/native-manifest.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_tree_manifest_records_clean(self):
        m, errs = nb.write_manifest(str(self.root), self.prod, self.mpath, ndk=None)
        self.assertEqual(m["source"]["working_tree"], "clean")
        self.assertFalse(any("dirty" in e for e in errs), str(errs))
        self.assertIs(m["build"]["reproducible_build_confirmed"], False)

    def test_modified_tracked_file_fails(self):
        (self.root / "crypto/rust/src/lib.rs").write_text("// tampered\n", encoding="utf-8")
        m, errs = nb.write_manifest(str(self.root), self.prod, self.mpath, ndk=None)
        self.assertEqual(m["source"]["working_tree"], "dirty")
        self.assertTrue(any("working tree is dirty" in e for e in errs), str(errs))

    def test_untracked_file_fails(self):
        (self.root / "crypto/rust/src/extra.rs").write_text("fn x(){}\n")
        m, errs = nb.write_manifest(str(self.root), self.prod, self.mpath, ndk=None)
        self.assertTrue(any("working tree is dirty" in e for e in errs), str(errs))

    def test_verify_live_dirty_tree_fails(self):
        m, errs = nb.write_manifest(str(self.root), self.prod, self.mpath, ndk=None)
        m["build"]["reproducible_build_confirmed"] = True
        m["build"]["reproducibility"] = {"method": "two-clean-builds-three-way-compare", "builds": 2,
                                          "build_ids": ["a", "b"],
                                          "per_abi_sha256": {a["abi"]: a["sha256"] for a in m["artifacts"]}}
        self.mpath.write_text(json.dumps(m))
        (self.root / "crypto/rust/src/lib.rs").write_text("// tampered after build\n")
        errs = nb.verify_manifest(str(self.root), str(self.mpath), str(self.prod))
        self.assertTrue(any("working tree is dirty" in e for e in errs), str(errs))

    def test_no_git_context_fails_closed(self):
        shutil.rmtree(self.root / ".git")
        m, errs = nb.write_manifest(str(self.root), self.prod, self.mpath, ndk=None)
        self.assertTrue(any("cannot determine working-tree state" in e for e in errs), str(errs))

    # ---- R-005 end to end on a real repository: build-manifest -> attest -> verify
    def _attested(self):
        m, errs = nb.write_manifest(str(self.root), self.prod, self.mpath, ndk=None)
        self.assertEqual(errs, [], str(errs))
        same = {"artifacts": [{"abi": a["abi"], "sha256": a["sha256"]} for a in m["artifacts"]]}
        self.assertEqual(nb.attest_reproducibility(str(self.mpath), same, same, ["r1", "r2"]), [])
        return json.loads(self.mpath.read_text())

    def test_written_manifest_records_actual_exports_and_verifies(self):
        m = self._attested()
        for a in m["artifacts"]:
            self.assertEqual(a["jni_exports"], EXPECTED_JNI)
            self.assertEqual(a["elf_machine"], {"arm64-v8a": 183, "x86_64": 62}[a["abi"]])
        self.assertEqual(nb.verify_manifest(str(self.root), str(self.mpath), str(self.prod)), [])

    def test_actual_export_removed_then_manifest_rebound_fails(self):
        self._attested()
        mutated = _fake_elf(183, EXPECTED_JNI[1:], b"arm64-payload")
        (self.prod / "arm64-v8a/libanox_crypto.so").write_bytes(mutated)
        m = json.loads(self.mpath.read_text())
        m["artifacts"][0].update({"sha256": _sha(mutated), "size": len(mutated)})
        m["build"]["reproducibility"]["per_abi_sha256"]["arm64-v8a"] = _sha(mutated)
        self.mpath.write_text(json.dumps(m))
        errs = nb.verify_manifest(str(self.root), str(self.mpath), str(self.prod))
        self.assertTrue(any("ACTUAL binary JNI exports differ" in e and EXPECTED_JNI[0] in e for e in errs), str(errs))

    def test_write_manifest_refuses_placeholder_binary(self):
        (self.prod / "x86_64/libanox_crypto.so").write_bytes(b"not an elf")
        m, errs = nb.write_manifest(str(self.root), self.prod, self.mpath, ndk=None)
        self.assertTrue(any("not a verifiable ELF64 shared object" in e for e in errs), str(errs))

    def test_write_manifest_refuses_alternative_native_input(self):
        d = self.root / "android/src/main/jniLibs/x86_64"; d.mkdir(parents=True)
        (d / "libanox_crypto.so").write_bytes(X86_SO)
        _git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
        _git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "commit a .so")
        m, errs = nb.write_manifest(str(self.root), self.prod, self.mpath, ndk=None)
        self.assertTrue(any("uncontrolled alternative native input present: android/src/main/jniLibs/x86_64/libanox_crypto.so"
                            in e for e in errs), str(errs))


# ===========================================================================
# F2 — .git directory / linked worktree / malformed metadata
# ===========================================================================

class F2GitContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.main = Path(self.tmp.name) / "main"
        self.main.mkdir()
        (self.main / "crypto/rust/src").mkdir(parents=True)
        (self.main / "crypto/rust/src/lib.rs").write_text("fn a() {}\n")
        _git(self.main, "init", "-q")
        _git(self.main, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
        _git(self.main, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")
        self.base = _git(self.main, "rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def test_normal_repo_clean_passes(self):
        self.assertEqual(s1.check_rust_behavior_unchanged(str(self.main), base_sha=self.base), [])

    def test_normal_repo_detects_change(self):
        (self.main / "crypto/rust/src/lib.rs").write_text("fn a() { /* changed */ }\n")
        errs = s1.check_rust_behavior_unchanged(str(self.main), base_sha=self.base)
        self.assertTrue(any("crypto/rust/src/** changed" in e for e in errs), str(errs))

    def test_linked_worktree_clean_passes(self):
        wt = Path(self.tmp.name) / "wt"
        _git(self.main, "worktree", "add", "-q", "--detach", str(wt), self.base)
        self.assertTrue((wt / ".git").is_file())
        self.assertEqual(s1.check_rust_behavior_unchanged(str(wt), base_sha=self.base), [])

    def test_linked_worktree_detects_change(self):
        wt = Path(self.tmp.name) / "wt"
        _git(self.main, "worktree", "add", "-q", "--detach", str(wt), self.base)
        (wt / "crypto/rust/src/lib.rs").write_text("fn a() { /* changed in worktree */ }\n")
        errs = s1.check_rust_behavior_unchanged(str(wt), base_sha=self.base)
        self.assertTrue(any("crypto/rust/src/** changed" in e for e in errs), str(errs))

    def test_missing_git_fails_closed(self):
        shutil.rmtree(self.main / ".git")
        errs = s1.check_rust_behavior_unchanged(str(self.main), base_sha=self.base)
        self.assertTrue(any("non-repository context" in e for e in errs), str(errs))

    def test_malformed_pointer_fails_closed(self):
        shutil.rmtree(self.main / ".git")
        (self.main / ".git").write_text("this is not a gitdir pointer\n")
        errs = s1.check_rust_behavior_unchanged(str(self.main), base_sha=self.base)
        self.assertTrue(any("malformed" in e for e in errs), str(errs))

    def test_pointer_to_nonexistent_fails_closed(self):
        shutil.rmtree(self.main / ".git")
        (self.main / ".git").write_text("gitdir: /nonexistent/path/.git/worktrees/x\n")
        errs = s1.check_rust_behavior_unchanged(str(self.main), base_sha=self.base)
        self.assertTrue(any("does not exist" in e for e in errs), str(errs))

    def test_pointer_to_non_git_dir_fails_closed(self):
        shutil.rmtree(self.main / ".git")
        (self.main / "notgit").mkdir()
        (self.main / ".git").write_text("gitdir: notgit\n")
        errs = s1.check_rust_behavior_unchanged(str(self.main), base_sha=self.base)
        self.assertTrue(any("lacks HEAD" in e for e in errs), str(errs))

    def test_empty_pointer_fails_closed(self):
        shutil.rmtree(self.main / ".git")
        (self.main / ".git").write_text("gitdir:   \n")
        errs = s1.check_rust_behavior_unchanged(str(self.main), base_sha=self.base)
        self.assertTrue(any("empty/invalid gitdir" in e for e in errs), str(errs))

    def test_base_commit_absent_fails_closed(self):
        errs = s1.check_rust_behavior_unchanged(str(self.main), base_sha="1" * 40)
        self.assertTrue(any("not present in repository" in e for e in errs), str(errs))

    def test_git_dir_without_head_fails_closed(self):
        os.remove(self.main / ".git/HEAD")
        errs = s1.check_rust_behavior_unchanged(str(self.main), base_sha=self.base)
        self.assertTrue(any("no HEAD" in e for e in errs), str(errs))

    def test_cli_static_gate_never_skips_git_check(self):
        # check_static default must run the git scope check (no silent skip)
        shutil.rmtree(self.main / ".git")
        errs = s1.check_static(str(self.main))
        self.assertTrue(any("Rust behavior-scope check cannot run" in e for e in errs), str(errs))


# ===========================================================================
# F4 — CI lineage graph
# ===========================================================================

class F4CiLineageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.wf = Path(self.tmp.name) / "ci.yml"
        self.wf.write_text((REPO_ROOT / CI).read_text())

    def tearDown(self):
        self.tmp.cleanup()

    def _mut(self, fn):
        self.wf.write_text(fn(self.wf.read_text()))
        return ci_v.validate(str(self.wf))

    def test_control_passes(self):
        self.assertEqual(ci_v.validate(str(self.wf)), [])

    def test_release_drops_native_build_edge_fails(self):
        def fn(t):
            i = t.index("  android-release:")
            return t[:i] + t[i:].replace("      - native-build\n", "", 1)
        errs = self._mut(fn)
        self.assertTrue(any("'android-release' must declare needs: native-build" in e for e in errs), str(errs))

    def test_debug_redirected_to_rust_fails(self):
        def fn(t):
            i = t.index("  android-debug:")
            return t[:i] + t[i:].replace("      - native-build\n", "      - rust\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("'android-debug' must declare needs: native-build" in e for e in errs), str(errs))
        self.assertTrue(any("does not descend from native-build" in e for e in errs), str(errs))

    def test_instrumented_arm64_needs_removed_fails(self):
        def fn(t):
            i = t.index("  instrumented-arm64:")
            j = t.index("    steps:", i)
            return t[:i] + t[i:j].replace("    needs:\n      - native-build\n      - android-debug\n", "") + t[j:]
        errs = self._mut(fn)
        self.assertTrue(any("'instrumented-arm64' must declare needs: native-build" in e for e in errs), str(errs))

    def test_consumer_reverify_removed_fails(self):
        def fn(t):
            i = t.index("  android-release:")
            return t[:i] + t[i:].replace(
                "      - name: Re-verify downloaded artifacts vs manifest\n        run: python3 tools/security/native_build.py verify\n", "", 1)
        errs = self._mut(fn)
        self.assertTrue(any("'android-release' does not re-verify" in e for e in errs), str(errs))

    def test_consumer_verifies_after_gradle_fails(self):
        def fn(t):
            i = t.index("  android-debug:")
            seg = t[i:]
            step = "      - name: Re-verify downloaded artifacts vs manifest\n        run: python3 tools/security/native_build.py verify\n\n"
            seg = seg.replace(step, "", 1)
            seg = seg.replace("      - name: Android lint (errors fatal)\n", step + "      - name: Android lint (errors fatal)\n", 1)
            return t[:i] + seg
        errs = self._mut(fn)
        self.assertTrue(any("consumes the artifact (Gradle) before re-verifying" in e for e in errs), str(errs))

    def test_wrong_artifact_name_fails(self):
        def fn(t):
            i = t.index("  android-debug:")
            return t[:i] + t[i:].replace("name: native-artifacts-${{ github.sha }}", "name: native-artifacts-latest", 1)
        errs = self._mut(fn)
        self.assertTrue(any("downloads an artifact other than" in e for e in errs), str(errs))

    def test_conditional_download_fails(self):
        def fn(t):
            i = t.index("  instrumented-x86_64:")
            return t[:i] + t[i:].replace("      - name: Download authoritative native artifacts\n",
                                         "      - name: Download authoritative native artifacts\n        continue-on-error: true\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("download step is conditional/non-fatal" in e for e in errs), str(errs))

    def test_consumer_rebuilding_natively_fails(self):
        def fn(t):
            i = t.index("  android-release:")
            return t[:i] + t[i:].replace("      - name: Assemble release\n",
                                         "      - name: Rebuild\n        run: python3 tools/security/native_build.py build\n      - name: Assemble release\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("rebuilds native artifacts instead of consuming" in e for e in errs), str(errs))

    def test_upload_before_verify_fails(self):
        def fn(t):
            i = t.index("  native-build:")
            j = t.index("  android-debug:")
            seg = t[i:j]
            ver = "      - name: Verify artifacts vs manifest (hashes, ABI set, JNI parity)\n        run: python3 tools/security/native_build.py verify\n\n"
            seg = seg.replace(ver, "")
            return t[:i] + seg.rstrip("\n") + "\n\n" + ver + t[j:]
        errs = self._mut(fn)
        self.assertTrue(any("uploads the artifact before verifying" in e for e in errs), str(errs))

    def test_upload_if_no_files_ignore_fails(self):
        def fn(t):
            i = t.index("  native-build:")
            j = t.index("  android-debug:")
            return t[:i] + t[i:j].replace("if-no-files-found: error", "if-no-files-found: ignore") + t[j:]
        errs = self._mut(fn)
        self.assertTrue(any("if-no-files-found: error" in e for e in errs), str(errs))

    def test_needs_parser_handles_inline_list(self):
        self.assertEqual(ci_v.parse_needs("    needs: [a, 'b', \"c\"]\n"), {"a", "b", "c"})
        self.assertEqual(ci_v.parse_needs("    needs: solo\n"), {"solo"})
        self.assertEqual(ci_v.parse_needs("    needs:\n      - x\n      - y\n    steps:\n"), {"x", "y"})

    def test_consumer_verify_or_true_softfail_fails(self):
        def fn(t):
            i = t.index("  android-debug:")
            return t[:i] + t[i:].replace(
                "run: python3 tools/security/native_build.py verify\n",
                "run: python3 tools/security/native_build.py verify || true\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("masks failure via shell chaining" in e for e in errs), str(errs))

    def test_consumer_verify_semicolon_softfail_fails(self):
        def fn(t):
            i = t.index("  android-release:")
            return t[:i] + t[i:].replace(
                "run: python3 tools/security/native_build.py verify\n",
                "run: python3 tools/security/native_build.py verify ; exit 0\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("masks failure via shell chaining" in e for e in errs), str(errs))

    def test_consumer_download_or_true_softfail_fails(self):
        def fn(t):
            i = t.index("  instrumented-arm64:")
            return t[:i] + t[i:].replace(
                "uses: actions/download-artifact@",
                "run: true || true\n        uses: actions/download-artifact@", 1)
        errs = self._mut(fn)
        self.assertTrue(any("masks failure via shell chaining" in e for e in errs), str(errs))

    def test_consumer_gradle_semicolon_softfail_fails(self):
        def fn(t):
            i = t.index("  android-debug:")
            return t[:i] + t[i:].replace("./gradlew --no-daemon :android:lintDebug",
                                        "./gradlew --no-daemon :android:lintDebug ; echo done", 1)
        errs = self._mut(fn)
        self.assertTrue(any("masks failure via shell chaining" in e for e in errs), str(errs))

    def test_producer_verify_softfail_fails(self):
        # R-006 correction: the PRODUCER's own verify step is a mandatory gate.
        # The previous expectation (soft-fail "not in scope") was a proven blind
        # spot; the corrected expectation is FAIL.
        def fn(t):
            i = t.index("  native-build:")
            return t[:i] + t[i:].replace(
                "run: python3 tools/security/native_build.py verify\n",
                "run: python3 tools/security/native_build.py verify || true\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("native-build: artifact verify" in e and "masks failure via shell chaining" in e
                            for e in errs), str(errs))

    # ---- R-006: mandatory jobs/gates must be MANDATORY (execution semantics)
    def _job_key(self, job, line):
        def fn(t):
            i = t.index(f"  {job}:\n")
            j = t.index("    steps:", i)
            return t[:j] + f"    {line}\n" + t[j:]
        return fn

    def test_required_job_if_false_fails(self):
        errs = self._mut(self._job_key("instrumented-arm64", "if: false"))
        self.assertTrue(any("required job 'instrumented-arm64' carries a job-level if" in e for e in errs), str(errs))

    def test_required_job_static_disable_variants_fail(self):
        for cond in ("${{ false }}", "github.event_name == 'never'", "${{ github.repository == 'x/y' }}", "'false'"):
            errs = self._mut(self._job_key("native-build", f"if: {cond}"))
            self.assertTrue(any("required job 'native-build' carries a job-level if" in e for e in errs), (cond, errs))
            self.setUp()

    def test_required_job_continue_on_error_fails(self):
        errs = self._mut(self._job_key("instrumented-arm64", "continue-on-error: true"))
        self.assertTrue(any("required job 'instrumented-arm64' is non-fatal" in e for e in errs), str(errs))

    def test_required_job_continue_on_error_expression_fails(self):
        errs = self._mut(self._job_key("supply-chain-policy", "continue-on-error: ${{ true }}"))
        self.assertTrue(any("required job 'supply-chain-policy' is non-fatal" in e for e in errs), str(errs))

    def _step_key(self, job, run_fragment, line):
        """Insert a step-level key right after the (single-line) run fragment."""
        def fn(t):
            i = t.index(f"  {job}:\n")
            j = t.index(run_fragment, i)
            return t[:j] + t[j:].replace("\n", f"\n        {line}\n", 1)
        return fn

    def test_soft_fail_secret_scan_step_fails(self):
        errs = self._mut(self._step_key("supply-chain-policy", "run: python3 tools/security/secret_scan.py",
                                        "continue-on-error: true"))
        self.assertTrue(any("policy gate: secret scan" in e and "non-fatal" in e for e in errs), str(errs))

    def test_soft_fail_producer_build_fails(self):
        errs = self._mut(self._step_key("native-build", "--build-id \"gha-${{ github.run_id }}-${{ github.run_attempt }}\"",
                                        "continue-on-error: true"))
        self.assertTrue(any("native-build: authoritative build step" in e and "non-fatal" in e for e in errs), str(errs))

    def test_soft_fail_producer_verify_step_key_fails(self):
        def fn(t):
            i = t.index("  native-build:")
            return t[:i] + t[i:].replace(
                "run: python3 tools/security/native_build.py verify\n",
                "run: python3 tools/security/native_build.py verify\n        continue-on-error: true\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("native-build: artifact verify" in e and "non-fatal" in e for e in errs), str(errs))

    def test_conditional_b021_gate_fails(self):
        errs = self._mut(self._step_key("supply-chain-policy",
                                        "run: python3 tools/audit/validate_b021_verification_matrix.py --check integrity",
                                        "if: github.event_name == 'push'"))
        self.assertTrue(any("policy gate: B-021 matrix validator" in e and "conditional" in e for e in errs), str(errs))

    def test_conditional_cargo_audit_fails(self):
        errs = self._mut(self._step_key("supply-chain-policy", "run: cargo audit", "if: ${{ false }}"))
        self.assertTrue(any("cargo audit" in e and "conditional" in e for e in errs), str(errs))

    def test_producer_build_shell_masked_fails(self):
        def fn(t):
            return t.replace('--build-id "gha-${{ github.run_id }}-${{ github.run_attempt }}"\n',
                             '--build-id "gha-${{ github.run_id }}-${{ github.run_attempt }}" || true\n', 1)
        errs = self._mut(fn)
        self.assertTrue(any("native-build: authoritative build step" in e and "masks failure" in e for e in errs), str(errs))

    def test_producer_rebuild_compare_exit0_fails(self):
        def fn(t):
            return t.replace("run: python3 tools/security/native_build.py rebuild-compare\n",
                             "run: |\n          python3 tools/security/native_build.py rebuild-compare\n          exit 0\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("reproducibility" in e and "forced success" in e for e in errs), str(errs))

    def test_secret_scan_shell_masked_fails(self):
        errs = self._mut(lambda t: t.replace("run: python3 tools/security/secret_scan.py\n",
                                             "run: python3 tools/security/secret_scan.py ; true\n", 1))
        self.assertTrue(any("policy gate: secret scan" in e and "masks failure" in e for e in errs), str(errs))

    def test_missing_needs_x86_64_fails(self):
        def fn(t):
            i = t.index("  instrumented-x86_64:")
            return t[:i] + t[i:].replace("    needs:\n      - native-build\n      - android-debug\n", "", 1)
        errs = self._mut(fn)
        self.assertTrue(any("'instrumented-x86_64' must declare needs: native-build" in e for e in errs), str(errs))

    def test_self_hosted_arm64_runner_substitution_fails(self):
        errs = self._mut(lambda t: t.replace("    runs-on: macos-latest\n",
                                             "    runs-on: [self-hosted, macOS, ARM64]\n", 1))
        self.assertTrue(any("required job 'instrumented-arm64' runs-on must be a single hosted runner label" in e
                            and "self-hosted" in e for e in errs), str(errs))

    def test_self_hosted_scalar_and_dynamic_runner_fail(self):
        for runner in ("self-hosted", "${{ vars.RUNNER }}", "windows-latest", "ubuntu-latest"):
            errs = self._mut(lambda t, r=runner: t.replace("    runs-on: macos-latest\n", f"    runs-on: {r}\n", 1))
            self.assertTrue(any("required job 'instrumented-arm64' runs-on" in e for e in errs), (runner, errs))
            self.setUp()

    def test_x86_64_job_moved_to_macos_fails(self):
        def fn(t):
            i = t.index("  instrumented-x86_64:")
            return t[:i] + t[i:].replace("    runs-on: ubuntu-latest\n", "    runs-on: macos-latest\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("'instrumented-x86_64' runs-on 'macos-latest' is not the required hosted runner class" in e
                            for e in errs), str(errs))

    def test_hosted_runner_classes_preserved_in_candidate(self):
        d = ci_v.parse_workflow(self.wf.read_text())
        self.assertEqual(d["jobs"]["instrumented-arm64"]["runs-on"], "macos-latest")
        self.assertEqual(d["jobs"]["instrumented-x86_64"]["runs-on"], "ubuntu-latest")
        for j in ci_v.REQUIRED_JOBS - {"instrumented-arm64"}:
            self.assertEqual(d["jobs"][j]["runs-on"], "ubuntu-latest", j)

    def test_consumer_native_rebuild_fails(self):
        def fn(t):
            i = t.index("  instrumented-x86_64:")
            return t[:i] + t[i:].replace(
                "      - name: Re-verify downloaded artifacts vs manifest\n",
                "      - name: Rebuild natively\n        run: python3 tools/security/native_build.py build\n"
                "      - name: Re-verify downloaded artifacts vs manifest\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("'instrumented-x86_64' rebuilds native artifacts" in e for e in errs), str(errs))

    def test_missing_artifact_reverification_in_arm64_fails(self):
        def fn(t):
            i = t.index("  instrumented-arm64:")
            return t[:i] + t[i:].replace(
                "      - name: Re-verify downloaded artifacts vs manifest\n"
                "        run: python3 tools/security/native_build.py verify\n", "", 1)
        errs = self._mut(fn)
        self.assertTrue(any("'instrumented-arm64' does not re-verify" in e for e in errs), str(errs))

    # ---- fail-closed parsing: anything outside the strict subset is a FAIL
    def test_yaml_anchor_alias_rejected(self):
        errs = self._mut(lambda t: t.replace("    runs-on: macos-latest\n", "    runs-on: &r macos-latest\n", 1))
        self.assertTrue(any("outside the strict supported subset" in e for e in errs), str(errs))

    def test_yaml_flow_mapping_rejected(self):
        errs = self._mut(lambda t: t.replace("    needs: supply-chain-policy\n", "    needs: {a: b}\n", 1))
        self.assertTrue(any("outside the strict supported subset" in e for e in errs), str(errs))

    def test_yaml_duplicate_key_rejected(self):
        # a second `if:` / `runs-on:` key would let a lenient parser pick either
        errs = self._mut(self._job_key("instrumented-arm64", "runs-on: [self-hosted, macOS, ARM64]"))
        self.assertTrue(any("duplicate key 'runs-on'" in e for e in errs), str(errs))

    def test_yaml_tab_indentation_rejected(self):
        errs = self._mut(lambda t: t.replace("    runs-on: macos-latest\n", "\t    runs-on: macos-latest\n", 1))
        self.assertTrue(any("tab character" in e for e in errs), str(errs))

    def test_yaml_multidoc_rejected(self):
        errs = self._mut(lambda t: t + "---\njobs: {}\n")
        self.assertTrue(any("outside the strict supported subset" in e for e in errs), str(errs))

    def test_quoted_semicolon_in_echo_not_a_mask_but_substitution_is(self):
        self.assertIsNone(ci_v.shell_masks_failure('echo "a; b"\ntest "$X" = "$Y"\n'))
        self.assertEqual(ci_v.shell_masks_failure('echo "$(cmd || true)"\n'), "shell chaining (|| / ;)")
        self.assertEqual(ci_v.shell_masks_failure("cmd; exit 0\n"), "shell chaining (|| / ;)")
        self.assertIsNone(ci_v.shell_masks_failure('if [ -z "$APK" ]; then\n  exit 1\nfi\n'))

    # -- N-8: a multi-line `run: |` block can swallow the exit status without
    # ever using `||` or `;` (REMEDIATION-S1-FINAL-CORRECTIONS-001).
    def _verify_block(self, body_lines):
        def fn(t):
            i = t.index("  android-debug:")
            return t[:i] + t[i:].replace(
                "run: python3 tools/security/native_build.py verify\n",
                "run: |\n" + "".join(f"          {l}\n" for l in body_lines), 1)
        return self._mut(fn)

    def test_consumer_verify_multiline_set_plus_e_fails(self):
        errs = self._verify_block(["set +e", "python3 tools/security/native_build.py verify"])
        self.assertTrue(any("errexit relaxation" in e for e in errs), str(errs))

    def test_consumer_verify_multiline_trailing_exit0_fails(self):
        errs = self._verify_block(["python3 tools/security/native_build.py verify", "exit 0"])
        self.assertTrue(any("forced success" in e for e in errs), str(errs))

    def test_consumer_verify_multiline_trailing_noop_fails(self):
        errs = self._verify_block(["python3 tools/security/native_build.py verify", "true"])
        self.assertTrue(any("trailing no-op success" in e for e in errs), str(errs))

    def test_consumer_gradle_multiline_exit0_fails(self):
        def fn(t):
            i = t.index("  android-debug:")
            return t[:i] + t[i:].replace(
                "run: ./gradlew --no-daemon :android:assembleDebug\n",
                "run: |\n          ./gradlew --no-daemon :android:assembleDebug\n          exit 0\n", 1)
        errs = self._mut(fn)
        self.assertTrue(any("forced success" in e for e in errs), str(errs))

    def test_consumer_verify_strict_multiline_still_accepted(self):
        # `set -euo pipefail` is the hardened form and must NOT be rejected.
        errs = self._verify_block(["set -euo pipefail", "python3 tools/security/native_build.py verify"])
        self.assertFalse(any("masks failure" in e for e in errs), str(errs))

    def test_run_body_keeps_first_block_line(self):
        # Regression guard: the body extractor must not lose the FIRST line of a
        # block scalar, or `set +e` on line 1 becomes invisible to every rule.
        step = ("      - name: Re-verify downloaded artifacts vs manifest\n"
                "        run: |\n"
                "          set +e\n"
                "          python3 tools/security/native_build.py verify\n")
        self.assertIn("set +e", ci_v.run_body(step))
        self.assertEqual(ci_v.softfail_reason(step), "errexit relaxation (set +e)")

    # ---- S1CRC-R-002: a mandatory step matched by substring alone lets a
    # non-executing decoy ("echo <cmd>") satisfy the gate. Required commands
    # must match at an executable command position.
    _VERIFY = "        run: python3 tools/security/native_build.py verify\n"

    def _verify_run(self, new_run):
        return self._mut(lambda t: t.replace(self._VERIFY, new_run, 1))

    def test_decoy_echo_verify_fails(self):
        errs = self._verify_run("        run: echo python3 tools/security/native_build.py verify\n")
        self.assertTrue(any("native-build: artifact verify" in e and "command position" in e for e in errs), str(errs))

    def test_decoy_printf_verify_fails(self):
        errs = self._verify_run("        run: printf 'python3 tools/security/native_build.py verify'\n")
        self.assertTrue(any("native-build: artifact verify" in e and "command position" in e for e in errs), str(errs))

    def test_decoy_colon_verify_fails(self):
        errs = self._verify_run("        run: : python3 tools/security/native_build.py verify\n")
        self.assertTrue(any("native-build: artifact verify" in e and "command position" in e for e in errs), str(errs))

    def test_decoy_true_verify_fails(self):
        errs = self._verify_run("        run: true python3 tools/security/native_build.py verify\n")
        self.assertTrue(any("native-build: artifact verify" in e and "command position" in e for e in errs), str(errs))

    def test_decoy_quoted_echo_verify_fails(self):
        errs = self._verify_run('        run: echo "python3 tools/security/native_build.py verify"\n')
        self.assertTrue(any("native-build: artifact verify" in e and "command position" in e for e in errs), str(errs))

    def test_decoy_comment_verify_fails(self):
        errs = self._verify_run("        run: |\n          # python3 tools/security/native_build.py verify\n")
        self.assertTrue(any("native-build: artifact verify" in e for e in errs), str(errs))

    def test_decoy_if_condition_verify_fails(self):
        # `if cmd; then` executes cmd but discards its status — condition
        # position must not satisfy a mandatory gate.
        errs = self._verify_run("        run: |\n"
                                "          if python3 tools/security/native_build.py verify; then\n"
                                "            echo verified\n"
                                "          fi\n")
        self.assertTrue(any("native-build: artifact verify" in e and "status-masked" in e for e in errs), str(errs))

    def test_decoy_backgrounded_verify_fails(self):
        errs = self._verify_run("        run: python3 tools/security/native_build.py verify &\n")
        self.assertTrue(any("native-build: artifact verify" in e and "status-masked" in e for e in errs), str(errs))

    def test_decoy_piped_verify_fails(self):
        errs = self._verify_run("        run: python3 tools/security/native_build.py verify | tee log\n")
        self.assertTrue(any("native-build: artifact verify" in e and "status-masked" in e for e in errs), str(errs))

    def test_decoy_or_rhs_verify_fails(self):
        errs = self._verify_run("        run: test -d build || python3 tools/security/native_build.py verify\n")
        self.assertTrue(any("native-build: artifact verify" in e and "status-masked" in e for e in errs), str(errs))

    def test_decoy_heredoc_verify_fails(self):
        errs = self._verify_run("        run: |\n"
                                "          cat <<EOF\n"
                                "          python3 tools/security/native_build.py verify\n"
                                "          EOF\n")
        self.assertTrue(any("native-build: artifact verify" in e for e in errs), str(errs))

    def test_decoy_echo_secret_scan_fails(self):
        # the executable-position rule is generic — same decoy on another gate
        errs = self._mut(lambda t: t.replace(
            "        run: python3 tools/security/secret_scan.py\n",
            "        run: echo python3 tools/security/secret_scan.py\n", 1))
        self.assertTrue(any("policy gate: secret scan" in e and "command position" in e for e in errs), str(errs))

    def test_decoy_b021_gate_echo_fails(self):
        errs = self._mut(lambda t: t.replace(
            "        run: python3 tools/audit/validate_b021_verification_matrix.py --check integrity\n",
            "        run: printf 'python3 tools/audit/validate_b021_verification_matrix.py --check integrity'\n", 1))
        self.assertTrue(any("B-021 matrix validator" in e and "command position" in e for e in errs), str(errs))

    def test_decoy_action_in_run_field_fails(self):
        # a `uses:` requirement can only be satisfied by the uses field —
        # echoing the action ref in a run body does not download anything
        errs = self._mut(lambda t: t.replace(
            "        uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093",
            "        run: echo actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093", 1))
        self.assertTrue(any("downloads native artifacts" in e for e in errs), str(errs))

    def test_setup_then_command_passes(self):
        errs = self._verify_run("        run: |\n"
                                "          set -euo pipefail\n"
                                "          cd \"$GITHUB_WORKSPACE\"\n"
                                "          python3 tools/security/native_build.py verify\n")
        self.assertEqual(errs, [], str(errs))

    def test_env_assignment_prefix_passes(self):
        errs = self._verify_run("        run: ANOX_NATIVE=1 python3 tools/security/native_build.py verify\n")
        self.assertEqual(errs, [], str(errs))

    def test_cd_chain_prefix_passes(self):
        errs = self._verify_run("        run: cd \"$GITHUB_WORKSPACE\" && python3 tools/security/native_build.py verify\n")
        self.assertEqual(errs, [], str(errs))

# ===========================================================================
# S1-ARM64-RUNTIME-INFRA-DISPOSITION-001 — two-path arm64 disposition gate
# ===========================================================================

class Arm64InfraDispositionTests(unittest.TestCase):
    """The arm64 job has exactly two lawful outcomes: the emulator runtime
    path genuinely executes (probe reports 'available'), or the job records
    INFRASTRUCTURE_BLOCKED_GITHUB_HOSTED_NESTED_VIRTUALIZATION ('unavailable').
    Anything that fakes, forces, widens, or removes that contract must FAIL."""

    AVAIL = "steps.arm64_virt.outputs.virtualization == 'available'"
    UNAVAIL = "steps.arm64_virt.outputs.virtualization == 'unavailable'"
    BLOCKED = "INFRASTRUCTURE_BLOCKED_GITHUB_HOSTED_NESTED_VIRTUALIZATION"
    TEST_STEP = ("      - name: Run instrumented tests (arm64-v8a produced artifact)\n"
                 f"        if: steps.arm64_virt.outputs.virtualization == 'available'\n"
                 "        run: ./gradlew --no-daemon :android:connectedDebugAndroidTest\n")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.wf = Path(self.tmp.name) / "ci.yml"
        self.wf.write_text((REPO_ROOT / CI).read_text())

    def tearDown(self):
        self.tmp.cleanup()

    def _mut(self, fn):
        self.wf.write_text(fn(self.wf.read_text()))
        return ci_v.validate(str(self.wf))

    @staticmethod
    def _arm(fn):
        """Apply `fn` to the tail of the workflow starting at the arm64 job."""
        def wrap(t):
            i = t.index("  instrumented-arm64:")
            return t[:i] + fn(t[i:])
        return wrap

    # ---- control: the real two-path workflow must validate cleanly
    def test_control_real_disposition_workflow_passes(self):
        self.assertEqual(ci_v.validate(str(self.wf)), [])

    # ---- continue-on-error remains forbidden, incl. on the probe
    def test_continue_on_error_on_capability_probe_fails(self):
        errs = self._mut(lambda t: t.replace("        id: arm64_virt\n",
                                             "        id: arm64_virt\n        continue-on-error: true\n", 1))
        self.assertTrue(any("capability probe" in e and "non-fatal" in e for e in errs), str(errs))

    # ---- generic `exit 0` — inside a disposition step and standalone
    def test_exit0_appended_to_disposition_step_fails(self):
        errs = self._mut(lambda t: t.replace(
            '            echo "- deferred: REAL_ARM64_RUNTIME_EVIDENCE required before the final security / pre-product acceptance gate"\n'
            '          } >> "$GITHUB_STEP_SUMMARY"\n',
            '            echo "- deferred: REAL_ARM64_RUNTIME_EVIDENCE required before the final security / pre-product acceptance gate"\n'
            '          } >> "$GITHUB_STEP_SUMMARY"\n          exit 0\n', 1))
        self.assertTrue(any("forced success" in e for e in errs), str(errs))

    def test_standalone_exit0_step_fails(self):
        fake = ("      - name: Greenwash\n        run: |\n          echo done\n          exit 0\n")
        errs = self._mut(self._arm(lambda s: s.replace("      - name: Install SDK platform", fake + "      - name: Install SDK platform", 1)))
        self.assertTrue(any("exit 0" in e for e in errs), str(errs))

    # ---- generic `echo INFRASTRUCTURE_BLOCKED` + `exit 0` without the probe contract
    def test_generic_blocked_echo_exit0_fails(self):
        fake = ("      - name: Fake infrastructure disposition\n"
                "        run: |\n"
                f'          echo "ARM64_RUNTIME_STATUS={self.BLOCKED}"\n'
                "          exit 0\n")
        errs = self._mut(self._arm(lambda s: s.replace("      - name: Install SDK platform", fake + "      - name: Install SDK platform", 1)))
        self.assertTrue(any("INFRASTRUCTURE_BLOCKED" in e or "ARM64_RUNTIME_STATUS" in e for e in errs), str(errs))

    # ---- a runtime/test failure must not be convertible into 'infrastructure'
    def test_runtime_failure_followed_by_blocked_status_fails(self):
        fake = ("      - name: Convert test failure to infrastructure\n"
                "        if: failure()\n"
                "        run: |\n"
                f'          echo "ARM64_RUNTIME_STATUS={self.BLOCKED}"\n\n')
        anchor = "      - name: Verify tested APK is bound to the manifest\n"
        errs = self._mut(self._arm(lambda s: s.replace(anchor, fake + anchor, 1)))
        self.assertTrue(any("non-canonical condition" in e or "infrastructure-blocked status" in e
                            for e in errs), str(errs))

    # ---- forced environment variable claiming infrastructure blocked
    def test_job_level_env_blocked_status_fails(self):
        def fn(s):
            return s.replace("    steps:\n",
                             "    env:\n      ARM64_RUNTIME_STATUS: " + self.BLOCKED + "\n    steps:\n", 1)
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("env asserts ARM64 runtime status" in e for e in errs), str(errs))

    def test_step_level_env_blocked_status_fails(self):
        def fn(s):
            return s.replace("        id: arm64_virt\n",
                             "        id: arm64_virt\n        env:\n          ARM64_RUNTIME_STATUS: "
                             + self.BLOCKED + "\n", 1)
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("env asserts ARM64 runtime status" in e for e in errs), str(errs))

    # ---- removal of ARM64 provenance verification (artifact consumer verify)
    def test_arm64_provenance_verify_removed_fails(self):
        def fn(s):
            return s.replace("      - name: Re-verify downloaded artifacts vs manifest\n"
                             "        run: python3 tools/security/native_build.py verify\n", "", 1)
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("'instrumented-arm64' does not re-verify" in e for e in errs), str(errs))

    def test_arm64_artifact_download_removed_fails(self):
        step = ("      - name: Download authoritative native artifacts\n"
                "        uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093 # v4.3.0\n"
                "        with:\n"
                "          name: native-artifacts-${{ github.sha }}\n"
                "          path: build/native\n\n")
        errs = self._mut(self._arm(lambda s: s.replace(step, "", 1)))
        self.assertTrue(any("never downloads the native artifact" in e for e in errs), str(errs))

    # ---- removal of the ARM64 runtime path entirely
    def test_arm64_runtime_path_removed_fails(self):
        errs = self._mut(self._arm(lambda s: s.replace(self.TEST_STEP, "", 1)))
        self.assertTrue(any("no step in job 'instrumented-arm64' executes" in e for e in errs), str(errs))

    # ---- self-hosted ARM64 runner substitution
    def test_self_hosted_arm64_runner_fails(self):
        errs = self._mut(lambda t: t.replace("    runs-on: macos-latest\n",
                                             "    runs-on: [self-hosted, macOS, ARM64]\n", 1))
        self.assertTrue(any("required job 'instrumented-arm64' runs-on must be a single hosted runner label" in e
                            for e in errs), str(errs))

    # ---- `if: false` on the runtime step (or any non-canonical condition)
    def test_if_false_on_runtime_step_fails(self):
        def fn(s):
            return s.replace(f"        if: {self.AVAIL}\n        run: ./gradlew --no-daemon :android:connectedDebugAndroidTest\n",
                             "        if: false\n        run: ./gradlew --no-daemon :android:connectedDebugAndroidTest\n", 1)
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("must run iff" in e or "non-canonical condition" in e for e in errs), str(errs))

    def test_runtime_step_gated_on_unavailable_fails(self):
        def fn(s):
            return s.replace(f"        if: {self.AVAIL}\n        run: ./gradlew --no-daemon :android:connectedDebugAndroidTest\n",
                             f"        if: {self.UNAVAIL}\n        run: ./gradlew --no-daemon :android:connectedDebugAndroidTest\n", 1)
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("must run iff" in e for e in errs), str(errs))

    def test_runtime_step_unconditioned_fails(self):
        def fn(s):
            return s.replace(f"        if: {self.AVAIL}\n        run: ./gradlew --no-daemon :android:connectedDebugAndroidTest\n",
                             "        run: ./gradlew --no-daemon :android:connectedDebugAndroidTest\n", 1)
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("must run iff" in e for e in errs), str(errs))

    # ---- `|| true` on the capability probe
    def test_or_true_on_capability_probe_fails(self):
        errs = self._mut(lambda t: t.replace("          echo virtualization=$VIRT >> $GITHUB_OUTPUT\n",
                                             "          echo virtualization=$VIRT >> $GITHUB_OUTPUT || true\n", 1))
        self.assertTrue(any("masks failure" in e for e in errs), str(errs))

    # ---- the capability probe itself is mandatory and must be real
    def test_capability_probe_removed_fails(self):
        def fn(s):
            start = s.index("      - name: Probe macOS ARM64 virtualization capability (HVF)\n")
            end = s.index("      - name: Install SDK platform")
            return s[:start] + s[end:]
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("no virtualization capability probe" in e for e in errs), str(errs))

    def test_probe_without_accel_check_fails(self):
        errs = self._mut(lambda t: t.replace("-accel-check", "-version", 1))
        self.assertTrue(any("-accel-check" in e for e in errs), str(errs))

    def test_probe_hardcoded_unavailable_fails(self):
        # only one outcome remains -> the disposition is hardcoded, not derived
        errs = self._mut(lambda t: t.replace("            VIRT=available\n", "            VIRT=unavailable\n", 1))
        self.assertTrue(any("derive BOTH" in e for e in errs), str(errs))

    def test_probe_without_github_output_write_fails(self):
        errs = self._mut(lambda t: t.replace("          echo virtualization=$VIRT >> $GITHUB_OUTPUT\n",
                                             "          echo virtualization=$VIRT\n", 1))
        self.assertTrue(any("GITHUB_OUTPUT" in e for e in errs), str(errs))

    # ---- the blocked disposition step is mandatory and must stay canonical
    def test_blocked_disposition_step_removed_fails(self):
        def fn(s):
            start = s.index("      - name: Record ARM64 runtime disposition (infrastructure blocked)\n")
            end = s.index("      - name: Upload instrumented test report\n")
            return s[:start] + s[end:]
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("no infrastructure-disposition step" in e for e in errs), str(errs))

    def test_blocked_status_under_available_condition_fails(self):
        def fn(s):
            return s.replace(
                f"        if: {self.UNAVAIL}\n        run: |\n          set -euo pipefail\n"
                f'          echo "ARM64_RUNTIME_STATUS={self.BLOCKED}"',
                f"        if: {self.AVAIL}\n        run: |\n          set -euo pipefail\n"
                f'          echo "ARM64_RUNTIME_STATUS={self.BLOCKED}"', 1)
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("infrastructure-blocked status emitted outside" in e
                            or "no infrastructure-disposition step" in e for e in errs), str(errs))

    def test_pass_status_under_unavailable_condition_fails(self):
        def fn(s):
            return s.replace(
                f"        if: {self.AVAIL}\n        run: |\n          set -euo pipefail\n"
                '          echo "ARM64_RUNTIME_STATUS=PASS"',
                f"        if: {self.UNAVAIL}\n        run: |\n          set -euo pipefail\n"
                '          echo "ARM64_RUNTIME_STATUS=PASS"', 1)
        errs = self._mut(self._arm(fn))
        self.assertTrue(any("PASS marker emitted outside" in e or "no step records" in e
                            for e in errs), str(errs))

    # ---- a misleading job name must not imply a runtime pass
    def test_misleading_job_name_fails(self):
        errs = self._mut(self._arm(lambda s: s.replace(
            "    name: ARM64 runtime / infrastructure disposition\n",
            "    name: Instrumented tests on arm64-v8a emulator (S1 artifact)\n", 1)))
        self.assertTrue(any("must state the runtime / infrastructure disposition" in e for e in errs), str(errs))


class F6SecretScannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _scan(self, files):
        for rel, data in files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data if isinstance(data, bytes) else data.encode())
        return scan.scan(str(self.root), files=list(files))

    def test_control_binary_without_secrets_passes(self):
        self.assertEqual(self._scan({"a.bin": b"\x00\x01\x02" * 100}), [])

    def test_nul_prefixed_aws_key_detected(self):
        f = self._scan({"a.bin": b"\x00\x00padding" + b"AKIA" + b"IOSFODNN7EXAMPLE" + b"\x00"})
        self.assertEqual([r for _, r in f], ["aws_access_key"])

    def test_pem_inside_binary_detected(self):
        f = self._scan({"blob.dat": b"\x7fELF\x00\x00" + b"-----BEGIN RSA PRIVATE KEY-----\nMIIE" + b"\x00" * 10})
        self.assertEqual([r for _, r in f], ["pem_private_key_in_binary"])

    def test_github_token_in_binary_detected(self):
        f = self._scan({"t.bin": b"\x00" + b"ghp_" + b"a" * 36 + b"\x00"})
        self.assertEqual([r for _, r in f], ["github_token"])

    def test_indented_pem_in_yaml_detected(self):
        y = "secrets:\n  key: |\n      -----BEGIN RSA PRIVATE KEY-----\n      MIIEowIBAAKCAQEAxyz0123456789abcdefgh\n      -----END RSA PRIVATE KEY-----\n"
        f = self._scan({"c.yaml": y})
        self.assertEqual([r for _, r in f], ["pem_private_key_indented"])

    def test_quoted_pem_in_json_detected(self):
        j = '{\n  "key": "-----BEGIN PRIVATE KEY-----\n  "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC",\n}\n'
        f = self._scan({"c.json": j})
        self.assertEqual([r for _, r in f], ["pem_private_key_indented"])

    def test_tool_source_marker_literal_not_flagged(self):
        src = 'SECRET_MARKERS = [\n    b"-----BEGIN PRIVATE KEY-----",\n    b"-----BEGIN RSA PRIVATE KEY-----",\n]\n'
        self.assertEqual(self._scan({"tools/x.py": src}), [])

    def test_indented_marker_followed_by_prose_not_flagged(self):
        txt = "  -----BEGIN RSA PRIVATE KEY----- is the header format\n  used by OpenSSL, described here.\n"
        self.assertEqual(self._scan({"docs/note.md": txt}), [])

    def test_escaped_singleline_pem_detected(self):
        # GCP service-account shape: a PEM key serialised onto ONE line with
        # literal backslash-n separators inside a JSON string.
        b64 = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDA"
        j = ('{"type": "service_account", "private_key": "-----BEGIN PRIVATE KEY-----\\n'
             + b64 + "\\n" + b64 + "\\n-----END PRIVATE KEY-----\\n\"}")
        f = self._scan({"sa.json": j})
        self.assertEqual([r for _, r in f], ["pem_private_key_escaped"])

    def test_escaped_marker_literal_without_body_not_flagged(self):
        src = 'HELP = "-----BEGIN PRIVATE KEY-----\\\\n is the escaped header"\n'
        self.assertEqual(self._scan({"tools/x.py": src}), [])

    def test_oversize_file_reported_not_skipped(self):
        p = self.root / "big.bin"
        with open(p, "wb") as fh:
            fh.truncate(scan.MAX_FILE_BYTES + 1)
        f = scan.scan(str(self.root), files=["big.bin"])
        self.assertEqual([r for _, r in f], ["file_too_large_unscanned"])

    # ---- R-003: binary generic assignment (reviewer-proven blind spot)
    def test_generic_secret_assignment_in_binary_detected(self):
        blob = b"\x00\x00hdr\x00" + b"client_secret = \"" + b"Q" * 32 + b"\"\x00tail"
        f = self._scan({"res.bin": blob})
        self.assertEqual([r for _, r in f], ["generic_api_secret_assignment"])

    def test_generic_secret_assignment_in_binary_case_and_separator_variants(self):
        for key in (b"API_SECRET", b"Api-Secret", b"service_role_key", b"SERVICE-ROLE-KEY"):
            blob = b"\x00" + key + b": '" + b"z" * 24 + b"'"
            f = self._scan({"v.bin": blob})
            self.assertEqual([r for _, r in f], ["generic_api_secret_assignment"], key)

    def test_binary_word_boundary_prevents_false_positive(self):
        # `myapi_secret_len = "..."` is an identifier, not an assignment of api_secret
        blob = b"\x00myapi_secret_len = \"" + b"Q" * 32 + b"\""
        self.assertEqual(self._scan({"ok.bin": blob}), [])

    def test_invalid_utf8_token_detected_in_binary_and_text(self):
        # invalid UTF-8 around a token must not derail either domain
        tok = b"AKIA" + b"IOSFODNN7EXAMPLE"
        self.assertEqual([r for _, r in self._scan({"x.bin": b"\xff\xfe\x00" + tok})], ["aws_access_key"])
        self.assertEqual([r for _, r in self._scan({"x.txt": b"\xff\xfe " + tok + b"\n"})], ["aws_access_key"])

    def test_text_and_binary_material_rules_are_aligned(self):
        text_rules = {n for n, _ in scan.SECRET_PATTERNS}
        bin_rules = {n.replace("_in_binary", "") for n, _ in scan.BINARY_PATTERNS}
        self.assertTrue(text_rules <= bin_rules, text_rules - bin_rules)

    # ---- S1CRC-R-001: a PEM block where EVERY line carries a markup prefix
    # used to evade the scanner entirely. The header is found mid-line, so the
    # body-line matcher must tolerate list/quote/table/heading prefixes.
    B64 = "MIIEowIBAAKCAQEA7eGzFakeKeyMaterialForProbeOnlyNotReal0000000"

    def test_yaml_list_prefixed_pem_detected(self):
        y = (f"- -----BEGIN RSA PRIVATE KEY-----\n- {self.B64}\n- {self.B64}\n"
             "- -----END RSA PRIVATE KEY-----\n")
        self.assertEqual([r for _, r in self._scan({"k.yaml": y})], ["pem_private_key_indented"])

    def test_markdown_blockquote_pem_detected(self):
        m = (f"> -----BEGIN PRIVATE KEY-----\n> {self.B64}\n> {self.B64}\n"
             "> -----END PRIVATE KEY-----\n")
        self.assertEqual([r for _, r in self._scan({"doc.md": m})], ["pem_private_key_indented"])

    def test_star_and_plus_bullet_pem_detected(self):
        for marker in ("*", "+"):
            t = (f"{marker} -----BEGIN PRIVATE KEY-----\n{marker} {self.B64}\n{marker} {self.B64}\n")
            self.assertEqual([r for _, r in self._scan({"n.md": t})], ["pem_private_key_indented"], marker)

    def test_numbered_list_pem_detected(self):
        t = f"1. -----BEGIN PRIVATE KEY-----\n2. {self.B64}\n3. {self.B64}\n"
        self.assertEqual([r for _, r in self._scan({"n.md": t})], ["pem_private_key_indented"])

    def test_markdown_table_cell_pem_detected(self):
        t = f"| -----BEGIN PRIVATE KEY----- |\n| {self.B64} |\n| {self.B64} |\n"
        self.assertEqual([r for _, r in self._scan({"t.md": t})], ["pem_private_key_indented"])

    def test_nested_list_prefixed_pem_detected(self):
        t = f"- - -----BEGIN PRIVATE KEY-----\n- - {self.B64}\n- - {self.B64}\n"
        self.assertEqual([r for _, r in self._scan({"n.yaml": t})], ["pem_private_key_indented"])

    def test_plain_pem_control_still_detected(self):
        t = f"-----BEGIN RSA PRIVATE KEY-----\n{self.B64}\n{self.B64}\n-----END RSA PRIVATE KEY-----\n"
        self.assertEqual([r for _, r in self._scan({"plain.txt": t})], ["pem_private_key"])

    def test_clean_list_and_blockquote_controls_pass(self):
        for t in ("- item one\n- item two\n- item three\n",
                  "> quoted prose line\n> another prose line\n",
                  f"## a heading\n- {self.B64[:10]} short bullet\n"):
            self.assertEqual(self._scan({"clean.md": t}), [], t)

    def test_prefixed_header_without_base64_body_not_flagged(self):
        t = "> -----BEGIN PRIVATE KEY----- is the header format\n> described here in prose.\n"
        self.assertEqual(self._scan({"docs/note.md": t}), [])


class R003SecretScannerPathTests(unittest.TestCase):
    """Tracked-path handling through the NUL-delimited Git interface: every
    hostile filename must be scanned (or fail closed) — never skipped."""

    SECRET = "key = " + "AKIA" + "IOSFODNN" + "7EXAMPLE" + "\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "t@anox.local")
        _git(self.root, "config", "user.name", "t")
        _git(self.root, "config", "core.quotepath", "on")  # default: hostile to newline-parsers
        (self.root / "README.md").write_text("clean\n")
        _git(self.root, "add", "README.md")
        _git(self.root, "commit", "-q", "-m", "init")

    def tearDown(self):
        self.tmp.cleanup()

    def _track(self, name, data):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
        subprocess.run(["git", "add", "--", name], cwd=str(self.root), check=True, capture_output=True)
        return name

    def _findings(self):
        return scan.scan(str(self.root))

    def test_control_clean_repo_passes(self):
        self.assertEqual(self._findings(), [])
        self.assertEqual(scan.tracked_files(self.root), [b"README.md"])

    def test_unicode_filename_secret_detected(self):
        self._track("docs/schlüssel-🔑.txt", self.SECRET)
        f = self._findings()
        self.assertEqual([r for _, r in f], ["aws_access_key"], str(f))
        self.assertIn("schlüssel", f[0][0])

    def test_newline_filename_secret_detected(self):
        self._track("cfg/line1\nline2.txt", self.SECRET)
        f = self._findings()
        self.assertEqual([r for _, r in f], ["aws_access_key"], str(f))

    def test_quoted_filename_secret_detected(self):
        self._track('cfg/"quoted" \'file\'.txt', self.SECRET)
        f = self._findings()
        self.assertEqual([r for _, r in f], ["aws_access_key"], str(f))

    def test_leading_space_filename_secret_detected(self):
        self._track("cfg/ leading-space.txt", self.SECRET)
        self._track("cfg/trailing-space .txt", self.SECRET)
        f = self._findings()
        self.assertEqual(sorted(r for _, r in f), ["aws_access_key", "aws_access_key"], str(f))

    def test_shell_sensitive_filename_secret_detected(self):
        self._track("cfg/$(id)`;rm` &|<>.txt", self.SECRET)
        f = self._findings()
        self.assertEqual([r for _, r in f], ["aws_access_key"], str(f))

    def test_tracked_path_missing_from_tree_scans_staged_blob(self):
        # worktree-deleted tracked file: staged index content is scanned, not skipped
        self._track("cfg/present.txt", "x\n")
        (self.root / "cfg/present.txt").unlink()
        self.assertEqual(self._findings(), [])

    def test_staged_secret_then_rm_detected_in_index_blob(self):
        # git add secret; rm file -> secret still lives in the staged blob
        self._track("cfg/gone.txt", self.SECRET + "\n")
        (self.root / "cfg/gone.txt").unlink()
        f = self._findings()
        self.assertEqual(f, [("'cfg/gone.txt'", "aws_access_key")], str(f))

    def test_tracked_directory_symlink_fails_closed(self):
        # a tracked symlink pointing outside the tree: link text is scanned, target never followed
        os.symlink("/etc", self.root / "cfg-link")
        subprocess.run(["git", "add", "--", "cfg-link"], cwd=str(self.root), check=True, capture_output=True)
        self.assertEqual(self._findings(), [])

    def test_git_unavailable_falls_back_to_tree_walk(self):
        (self.root / "hidden dir" / "s.txt").parent.mkdir()
        (self.root / "hidden dir" / "s.txt").write_text(self.SECRET)
        orig = scan.tracked_files
        try:
            scan.tracked_files = lambda root: None
            f = scan.scan(str(self.root))
        finally:
            scan.tracked_files = orig
        self.assertEqual([r for _, r in f], ["aws_access_key"], str(f))

    def test_explicit_nonexistent_file_argument_fails_closed(self):
        f = scan.scan(str(self.root), files=["does/not/exist.txt"])
        self.assertEqual([r for _, r in f], ["tracked_path_unresolvable"])

    def test_cli_reports_hostile_names_without_leaking_control_chars(self):
        self._track("cfg/a\nb.txt", self.SECRET)
        r = subprocess.run([sys.executable, str(REPO_ROOT / "tools/security/secret_scan.py"),
                            "--repo-root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("'cfg/a\\nb.txt'  (rule: aws_access_key)", r.stdout)


class F6ApkBoundsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.apk = self.root / "app.apk"
        self.mpath = self.root / "m.json"
        self.mpath.write_text(json.dumps(_manifest()))

    def tearDown(self):
        self.tmp.cleanup()

    def _rc(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = apk_v.validate_apk(str(self.apk), manifest_path=str(self.mpath), expected_source_sha=FIXTURE_SRC_SHA)
        return rc, out.getvalue()

    def test_oversize_member_fails_not_skipped(self):
        _apk(self.apk, {})
        old = apk_v.MAX_SCAN_BYTES
        try:
            apk_v.MAX_SCAN_BYTES = 1024
            with zipfile.ZipFile(self.apk, "a") as z:
                z.writestr("assets/huge.bin", b"x" * 4096)
            rc, out = self._rc()
        finally:
            apk_v.MAX_SCAN_BYTES = old
        self.assertNotEqual(rc, 0)
        self.assertIn("exceeds scan bound; unscannable member is a failure", out)

    def test_zip_bomb_ratio_fails(self):
        _apk(self.apk, {})
        old = (apk_v.BOMB_MIN_BYTES, apk_v.BOMB_RATIO)
        try:
            apk_v.BOMB_MIN_BYTES, apk_v.BOMB_RATIO = 1024, 50
            with zipfile.ZipFile(self.apk, "a", compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("assets/bomb.bin", b"\x00" * (1024 * 1024))
            rc, out = self._rc()
        finally:
            apk_v.BOMB_MIN_BYTES, apk_v.BOMB_RATIO = old
        self.assertNotEqual(rc, 0)
        self.assertIn("compression ratio", out)

    def test_total_uncompressed_bound_fails(self):
        _apk(self.apk, {})
        old = apk_v.MAX_TOTAL_UNCOMPRESSED
        try:
            apk_v.MAX_TOTAL_UNCOMPRESSED = 16
            rc, out = self._rc()
        finally:
            apk_v.MAX_TOTAL_UNCOMPRESSED = old
        self.assertNotEqual(rc, 0)
        self.assertIn("total uncompressed size", out)

    def test_member_count_bound_fails(self):
        _apk(self.apk, {})
        old = apk_v.MAX_MEMBERS
        try:
            apk_v.MAX_MEMBERS = 3
            rc, out = self._rc()
        finally:
            apk_v.MAX_MEMBERS = old
        self.assertNotEqual(rc, 0)
        self.assertIn("members > bound", out)


# ===========================================================================
# F3 / F9 — B-021 stage registry: exact FCP-1, complete ordering, FCP-7
# ===========================================================================

class F3F9MscStateTests(unittest.TestCase):
    IMPL = "REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001"
    RETESTER = "INDEPENDENT-BUILD-SUPPLY-RETEST-S1-002"
    SRC_SHA = "1" * 40
    BUILD_ID = "gha-4242-1"
    A, X = "a" * 64, "b" * 64
    EV_REG = "docs/security/remediation/evidence_registry.jsonl"
    CANON = "docs/security/audit-evidence/audit_traceability.jsonl"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in (MATRIX, INV_REG, self.CANON):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)
        (self.root / "ev").mkdir()
        for n in ("impl.md", "manifest.json", "arm64.xml", "x86.xml", "retest.md", "auth.md"):
            (self.root / "ev" / n).write_text(n)
        (self.root / MSC_STATE).parent.mkdir(parents=True, exist_ok=True)
        self._reg(*self._default_registry())

    def tearDown(self):
        self.tmp.cleanup()

    # ---- preserved-evidence registry fixtures (R-002: identifiers must resolve)
    def _ev(self, eid, etype, unit="MSC-UNIT-001", path="ev/impl.md", session=None, by=None, **over):
        session = session or self.IMPL
        rec = {"record_type": "remediation_evidence", "evidence_id": eid, "evidence_type": etype,
               "msc_unit": unit, "status": "PRESERVED", "recorded_by": by or session, "session": session,
               "recorded_at": "2026-09-16", "authority_ref": "ev/auth.md",
               "artifact": {"path": path, "sha256": _sha((self.root / path).read_bytes())}}
        if etype in mx.BUILD_BOUND_CLASSES:
            rec["build"] = {"source_sha": self.SRC_SHA, "build_id": self.BUILD_ID,
                            "per_abi_sha256": {"arm64-v8a": self.A, "x86_64": self.X}}
        if etype in mx.RETEST_CLASSES:
            rec["retest_of"] = self.IMPL
        rec.update(over)
        return rec

    def _default_registry(self):
        hp = self._ev("ANOX-EV-HP-001", "BUILD_ARTIFACT_HASH_PROOF", path="ev/manifest.json", session="CI",
                      provenance_relation={"derived_from": [], "reproducible_build_confirmed": True})
        rt_a = self._ev("ANOX-EV-RT-ARM64-001", "PROVENANCE_VERIFIED_NATIVE_RUNTIME", path="ev/arm64.xml",
                        session="CI", abi="arm64-v8a", provenance_relation={"derived_from": ["ANOX-EV-HP-001"]})
        rt_x = self._ev("ANOX-EV-RT-X86-001", "PROVENANCE_VERIFIED_NATIVE_RUNTIME", path="ev/x86.xml",
                        session="CI", abi="x86_64", provenance_relation={"derived_from": ["ANOX-EV-HP-001"]})
        retest = self._ev("ANOX-EV-RETEST-001", "INDEPENDENT_SPECIALIST_RETEST", path="ev/retest.md",
                          session=self.RETESTER)
        return [hp, rt_a, rt_x, retest]

    def _reg(self, *recs):
        (self.root / self.EV_REG).write_text("".join(json.dumps(r) + "\n" for r in recs))

    def _stage(self, res, by=None, refs=None, **extra):
        d = {"result": res}
        if res == "PASS":
            d.update({"evidence_refs": refs or ["ev/impl.md"], "recorded_by": by or self.IMPL,
                      "recorded_at": "2026-09-16"})
        if res == "NOT_APPLICABLE":
            d["reason"] = "gate table"
        d.update(extra)
        return d

    def _retest_stage(self, by=None, refs=None):
        return self._stage("PASS", by=by or self.RETESTER, refs=refs or ["ANOX-EV-RETEST-001"])

    def _fcp1(self, a=None, x=None, rt_a=None, rt_x=None, ref_a="ANOX-EV-RT-ARM64-001",
              ref_x="ANOX-EV-RT-X86-001", **hp_over):
        a, x = a or self.A, x or self.X
        hp = {"manifest_ref": "ANOX-EV-HP-001", "reproducible_build_confirmed": True,
              "per_abi_sha256": {"arm64-v8a": a, "x86_64": x}}
        hp.update(hp_over)
        return {
            "build_artifact_hash_proof": hp,
            "provenance_verified_native_runtime": {"per_abi": {
                "arm64-v8a": {"result": "PASS", "tests": 66, "failures": 0, "artifact_sha256": rt_a or a,
                              "evidence_ref": ref_a, "recorded_by": "CI"},
                "x86_64": {"result": "PASS", "tests": 66, "failures": 0, "artifact_sha256": rt_x or x,
                           "evidence_ref": ref_x, "recorded_by": "CI"},
            }},
        }

    def _runtime_pass(self, **fcp1):
        return self._stage("PASS", refs=["ANOX-EV-RT-ARM64-001", "ANOX-EV-RT-X86-001"],
                           provenance=self._fcp1(**fcp1))

    def _unit(self, unit="MSC-UNIT-001", **stages):
        base = {
            "IMPLEMENTED": self._stage("PASS"), "AUTOMATED_TESTED": self._stage("PASS"),
            "RUNTIME_TESTED": self._stage("PENDING"), "INDEPENDENTLY_RETESTED": self._stage("PENDING"),
            "ATTACKCHAIN_RETESTED": self._stage("PENDING"), "PHYSICAL_VERIFIED": self._stage("NOT_APPLICABLE"),
            "EVIDENCE_PRESERVED": self._stage("PENDING"), "CLOSED": self._stage("PENDING"),
        }
        base.update(stages)
        return {"record_type": "msc_unit_remediation_state", "msc_unit": unit,
                "implementing_session": self.IMPL, "stages": base}

    def _errs(self, *recs):
        (self.root / MSC_STATE).write_text("\n".join(json.dumps(r) for r in recs) + "\n")
        errs = []
        mx.check_msc_state(str(self.root), errs)
        return errs

    # ---- controls
    def test_control_pending_chain_passes(self):
        self.assertEqual(self._errs(self._unit()), [])

    def test_control_exact_fcp1_runtime_passes(self):
        u = self._unit(RUNTIME_TESTED=self._runtime_pass())
        self.assertEqual(self._errs(u), [])

    # ---- F3 exact FCP-1
    def test_runtime_pass_by_filename_token_fails(self):
        st = self._stage("PASS")
        (self.root / "ev/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME_BUILD_ARTIFACT_HASH_PROOF.md").write_text("x")
        st["evidence_refs"] = ["ev/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME_BUILD_ARTIFACT_HASH_PROOF.md"]
        errs = self._errs(self._unit(RUNTIME_TESTED=st))
        self.assertTrue(any("requires a structured `provenance` object" in e for e in errs), str(errs))
        self.assertTrue(any("is not a preserved-evidence identifier" in e for e in errs), str(errs))

    def test_runtime_missing_hash_proof_component_fails(self):
        p = self._fcp1(); del p["build_artifact_hash_proof"]
        errs = self._errs(self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=p)))
        self.assertTrue(any("BUILD_ARTIFACT_HASH_PROOF component missing" in e for e in errs), str(errs))

    def test_runtime_missing_runtime_component_fails(self):
        p = self._fcp1(); del p["provenance_verified_native_runtime"]
        errs = self._errs(self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=p)))
        self.assertTrue(any("PROVENANCE_VERIFIED_NATIVE_RUNTIME component missing" in e for e in errs), str(errs))

    def test_runtime_partial_abi_fails(self):
        p = self._fcp1(); del p["provenance_verified_native_runtime"]["per_abi"]["x86_64"]
        errs = self._errs(self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=p)))
        self.assertTrue(any("partial ABI coverage is not RUNTIME_TESTED" in e for e in errs), str(errs))

    def test_runtime_same_run_hash_mismatch_fails(self):
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(rt_x="c" * 64)))
        self.assertTrue(any("same-run violation for x86_64" in e for e in errs), str(errs))

    def test_runtime_with_failures_fails(self):
        st = self._runtime_pass()
        st["provenance"]["provenance_verified_native_runtime"]["per_abi"]["arm64-v8a"]["failures"] = 1
        errs = self._errs(self._unit(RUNTIME_TESTED=st))
        self.assertTrue(any("not a PASS with >=1 test and 0 failures" in e for e in errs), str(errs))

    def test_runtime_unconfirmed_reproducibility_fails(self):
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(reproducible_build_confirmed=False)))
        self.assertTrue(any("lacks reproducible_build_confirmed=true" in e for e in errs), str(errs))

    def test_runtime_bad_hash_hex_fails(self):
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(a="nothex")))
        self.assertTrue(any("is not a SHA-256 hex" in e for e in errs), str(errs))

    def test_runtime_evidence_ref_unresolvable_fails(self):
        # a repo path that exists is still NOT runtime evidence
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(ref_x="ev/x86.xml")))
        self.assertTrue(any("runtime[x86_64]: evidence ref 'ev/x86.xml' is not a preserved-evidence identifier"
                            in e for e in errs), str(errs))

    def test_non_provenance_unit_runtime_needs_no_fcp1(self):
        u = self._unit(unit="MSC-UNIT-003", RUNTIME_TESTED=self._stage("NOT_APPLICABLE"))
        self.assertEqual(self._errs(u), [])

    # ---- R-002: identifier-shaped strings are not evidence
    def test_nonexistent_runtime_evidence_id_fails(self):
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(ref_a="ANOX-EV-RT-ARM64-999")))
        self.assertTrue(any("ANOX-EV-RT-ARM64-999 does not resolve to a preserved registry record" in e
                            for e in errs), str(errs))

    def test_fabricated_hash_proof_id_fails(self):
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(manifest_ref="ANOX-EV-HP-FAKE-777")))
        self.assertTrue(any("hash proof: evidence ANOX-EV-HP-FAKE-777 does not resolve" in e for e in errs), str(errs))

    def test_self_asserted_hashes_without_backing_record_fail(self):
        # hashes syntactically valid but the preserved hash-proof record binds different artifacts
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(a="d" * 64, x="e" * 64, rt_a="d" * 64, rt_x="e" * 64)))
        self.assertTrue(any("wrong-artifact evidence" in e for e in errs), str(errs))

    def test_wrong_unit_runtime_evidence_fails(self):
        recs = self._default_registry()
        recs[1]["msc_unit"] = "MSC-UNIT-002"
        self._reg(*recs)
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass()))
        self.assertTrue(any("belongs to MSC-UNIT-002 (wrong-unit evidence)" in e for e in errs), str(errs))

    def test_wrong_build_runtime_evidence_fails(self):
        recs = self._default_registry()
        recs[2]["build"]["build_id"] = "gha-other-run"
        self._reg(*recs)
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass()))
        self.assertTrue(any("wrong-build evidence" in e for e in errs), str(errs))

    def test_runtime_record_without_provenance_relation_fails(self):
        recs = self._default_registry()
        recs[1]["provenance_relation"] = {"derived_from": []}
        self._reg(*recs)
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass()))
        self.assertTrue(any("not derived_from the hash-proof record" in e for e in errs), str(errs))

    def test_runtime_record_wrong_abi_fails(self):
        recs = self._default_registry()
        recs[1]["abi"] = "x86_64"
        self._reg(*recs)
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass()))
        self.assertTrue(any("ran on 'x86_64', not arm64-v8a" in e for e in errs), str(errs))

    def test_evidence_artifact_hash_drift_fails(self):
        (self.root / "ev/arm64.xml").write_text("tampered after preservation")
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass()))
        self.assertTrue(any("hash != recorded sha256" in e for e in errs), str(errs))
        self.assertTrue(any("ANOX-EV-RT-ARM64-001 does not resolve" in e for e in errs), str(errs))

    def test_evidence_artifact_missing_fails(self):
        (self.root / "ev/x86.xml").unlink()
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass()))
        self.assertTrue(any("does not exist in the repository" in e for e in errs), str(errs))

    def test_evidence_not_preserved_status_fails(self):
        recs = self._default_registry(); recs[3]["status"] = "DRAFT"; self._reg(*recs)
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(), INDEPENDENTLY_RETESTED=self._retest_stage()))
        self.assertTrue(any("status 'DRAFT' != PRESERVED" in e for e in errs), str(errs))

    def test_evidence_authority_ref_unresolvable_fails(self):
        recs = self._default_registry(); recs[3]["authority_ref"] = "docs/nope/authorization.md"; self._reg(*recs)
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(), INDEPENDENTLY_RETESTED=self._retest_stage()))
        self.assertTrue(any("authority_ref missing/unresolvable" in e for e in errs), str(errs))

    def test_duplicate_evidence_id_fails(self):
        recs = self._default_registry(); self._reg(*recs, recs[3])
        errs = self._errs(self._unit(RUNTIME_TESTED=self._runtime_pass(), INDEPENDENTLY_RETESTED=self._retest_stage()))
        self.assertTrue(any("duplicate evidence_id" in e for e in errs), str(errs))

    # ---- F9 ordering / omission / FCP-7
    def test_omitted_intermediate_stage_fails(self):
        u = self._unit(); del u["stages"]["RUNTIME_TESTED"]
        errs = self._errs(u)
        self.assertTrue(any("lifecycle stage record missing: RUNTIME_TESTED" in e for e in errs), str(errs))

    def test_independent_retest_without_runtime_fails(self):
        u = self._unit(INDEPENDENTLY_RETESTED=self._retest_stage())
        errs = self._errs(u)
        self.assertTrue(any("INDEPENDENTLY_RETESTED: PASS while earlier stage RUNTIME_TESTED is PENDING" in e
                            for e in errs), str(errs))

    def test_independent_retest_with_runtime_omitted_fails(self):
        u = self._unit(INDEPENDENTLY_RETESTED=self._retest_stage())
        del u["stages"]["RUNTIME_TESTED"]
        errs = self._errs(u)
        self.assertTrue(any("earlier stage RUNTIME_TESTED is missing" in e for e in errs), str(errs))

    def test_required_stage_not_applicable_cannot_be_skipped(self):
        u = self._unit(RUNTIME_TESTED=self._stage("NOT_APPLICABLE"),
                       INDEPENDENTLY_RETESTED=self._retest_stage())
        errs = self._errs(u)
        self.assertTrue(any("RUNTIME_TESTED: required stage marked NOT_APPLICABLE" in e for e in errs), str(errs))
        self.assertTrue(any("earlier stage RUNTIME_TESTED is NOT_APPLICABLE" in e for e in errs), str(errs))

    def test_reordered_lifecycle_fails(self):
        u = self._unit(AUTOMATED_TESTED=self._stage("PENDING"), RUNTIME_TESTED=self._runtime_pass())
        errs = self._errs(u)
        self.assertTrue(any("RUNTIME_TESTED: PASS while earlier stage AUTOMATED_TESTED is PENDING" in e
                            for e in errs), str(errs))

    def test_closed_without_complete_chain_fails(self):
        u = self._unit(CLOSED=self._stage("PASS", by="GOV", refs=["ANOX-EV-RETEST-001"]))
        errs = self._errs(u)
        self.assertTrue(any("CLOSED while required stage RUNTIME_TESTED is PENDING" in e for e in errs), str(errs))

    def test_closed_with_omitted_stage_fails(self):
        u = self._unit(CLOSED=self._stage("PASS", by="GOV", refs=["ANOX-EV-RETEST-001"]))
        del u["stages"]["EVIDENCE_PRESERVED"]
        errs = self._errs(u)
        self.assertTrue(any("CLOSED without stage record EVIDENCE_PRESERVED" in e for e in errs), str(errs))

    def test_closed_with_bare_identifier_evidence_fails(self):
        u = self._unit(CLOSED=self._stage("PASS", by="GOV", refs=["ANOX-CLOSURE-DECISION-001"]))
        errs = self._errs(u)
        self.assertTrue(any("CLOSED: evidence ref 'ANOX-CLOSURE-DECISION-001' is not a preserved-evidence identifier"
                            in e for e in errs), str(errs))

    def test_fcp7_missing_recorded_by_fails(self):
        st = self._retest_stage(); del st["recorded_by"]
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(), INDEPENDENTLY_RETESTED=st)
        errs = self._errs(u)
        self.assertTrue(any("retest stage PASS without recorded_by" in e for e in errs), str(errs))

    def test_fcp7_whitespace_case_variant_of_implementer_fails(self):
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(),
                       INDEPENDENTLY_RETESTED=self._retest_stage(by=" remediation-session-s1-build-provenance-001 "))
        errs = self._errs(u)
        self.assertTrue(any("recorded by implementing session" in e for e in errs), str(errs))

    def test_fcp7_implementer_prefixed_alias_fails(self):
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(),
                       INDEPENDENTLY_RETESTED=self._retest_stage(by=self.IMPL + "-retest"))
        errs = self._errs(u)
        self.assertTrue(any("recorded by implementing session" in e for e in errs), str(errs))

    def test_fcp7_distinct_authority_string_alone_fails(self):
        # R-002: FCP-7 is NOT `implementer_name != retester_name`. A different
        # actor string backed only by a repo path is NOT an independent retest.
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(),
                       INDEPENDENTLY_RETESTED=self._stage("PASS", by=self.RETESTER))
        errs = self._errs(u)
        self.assertTrue(any("INDEPENDENTLY_RETESTED: evidence ref 'ev/impl.md' is not a preserved-evidence identifier"
                            in e for e in errs), str(errs))
        self.assertTrue(any("no preserved independent retest record resolves" in e for e in errs), str(errs))

    def test_fcp7_nonexistent_retest_id_fails(self):
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(),
                       INDEPENDENTLY_RETESTED=self._retest_stage(refs=["ANOX-EV-RETEST-404"]))
        errs = self._errs(u)
        self.assertTrue(any("ANOX-EV-RETEST-404 does not resolve" in e for e in errs), str(errs))
        self.assertTrue(any("no preserved independent retest record resolves" in e for e in errs), str(errs))

    def test_fcp7_self_authored_fake_independent_actor_fails(self):
        # the retest record carries a foreign actor name but was produced by the implementing session
        recs = self._default_registry()
        recs[3]["session"] = self.IMPL
        recs[3]["recorded_by"] = "TOTALLY-INDEPENDENT-AUDITOR"
        self._reg(*recs)
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(),
                       INDEPENDENTLY_RETESTED=self._retest_stage(by="TOTALLY-INDEPENDENT-AUDITOR"))
        errs = self._errs(u)
        self.assertTrue(any("retest session/actor is the implementing session (self-retest)" in e for e in errs), str(errs))
        self.assertTrue(any("no preserved independent retest record resolves" in e for e in errs), str(errs))

    def test_fcp7_retest_record_for_other_unit_fails(self):
        recs = self._default_registry(); recs[3]["msc_unit"] = "MSC-UNIT-038"; self._reg(*recs)
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(), INDEPENDENTLY_RETESTED=self._retest_stage())
        errs = self._errs(u)
        self.assertTrue(any("ANOX-EV-RETEST-001 belongs to MSC-UNIT-038 (wrong-unit evidence)" in e for e in errs), str(errs))

    def test_fcp7_retest_record_actor_mismatch_fails(self):
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(),
                       INDEPENDENTLY_RETESTED=self._retest_stage(by="SOMEONE-ELSE-ENTIRELY"))
        errs = self._errs(u)
        self.assertTrue(any("stage recorded_by 'SOMEONE-ELSE-ENTIRELY' != evidence actor" in e for e in errs), str(errs))

    def test_fcp7_retest_of_other_session_fails(self):
        recs = self._default_registry(); recs[3]["retest_of"] = "REMEDIATION-SESSION-S0-OTHER"; self._reg(*recs)
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(), INDEPENDENTLY_RETESTED=self._retest_stage())
        errs = self._errs(u)
        self.assertTrue(any("not this unit's implementing session" in e for e in errs), str(errs))

    def test_fcp7_resolved_independent_retest_record_passes(self):
        u = self._unit(RUNTIME_TESTED=self._runtime_pass(), INDEPENDENTLY_RETESTED=self._retest_stage())
        self.assertEqual(self._errs(u), [])

    def test_pass_without_recorded_at_fails(self):
        st = self._stage("PASS"); del st["recorded_at"]
        errs = self._errs(self._unit(AUTOMATED_TESTED=st))
        self.assertTrue(any("PASS without recorded_at" in e for e in errs), str(errs))

    def test_missing_implementing_session_fails(self):
        u = self._unit(); u["implementing_session"] = ""
        errs = self._errs(u)
        self.assertTrue(any("implementing_session missing" in e for e in errs), str(errs))

    # ---- R-001: overlay is not the universe
    def test_empty_state_registry_fails(self):
        (self.root / MSC_STATE).write_text("")
        errs = []
        mx.check_msc_state(str(self.root), errs)
        self.assertTrue(any("msc_state registry is EMPTY" in e for e in errs), str(errs))

    def test_unknown_unit_fails(self):
        errs = self._errs(self._unit(), self._unit(unit="MSC-UNIT-099"))
        self.assertTrue(any("MSC-UNIT-099: unknown MSC unit" in e for e in errs), str(errs))

    def test_rejected_unit_state_record_fails(self):
        errs = self._errs(self._unit(unit="MSC-UNIT-043"))
        self.assertTrue(any("MSC-UNIT-043: canonical disposition is REJECTED_NOT_A_FINDING" in e for e in errs), str(errs))

    def test_duplicate_unit_fails(self):
        errs = self._errs(self._unit(), self._unit())
        self.assertTrue(any("MSC-UNIT-001: duplicate msc_state record" in e for e in errs), str(errs))

    def test_conflicting_duplicate_unit_fails(self):
        errs = self._errs(self._unit(), self._unit(AUTOMATED_TESTED=self._stage("PENDING")))
        self.assertTrue(any("conflicting state records" in e for e in errs), str(errs))

    def test_malformed_unit_id_fails(self):
        errs = self._errs(self._unit(unit="MSC_UNIT_001"))
        self.assertTrue(any("malformed MSC unit id" in e for e in errs), str(errs))

    def test_malformed_lifecycle_state_fails(self):
        errs = self._errs(self._unit(CLOSED={"result": "DONE"}))
        self.assertTrue(any("CLOSED: illegal result DONE" in e for e in errs), str(errs))

    def test_missing_canonical_universe_fails(self):
        (self.root / self.CANON).unlink()
        errs = self._errs(self._unit())
        self.assertTrue(any("canonical MSC universe unavailable" in e for e in errs), str(errs))

    def test_truncated_canonical_universe_fails(self):
        lines = (self.root / self.CANON).read_text().splitlines()
        keep = [l for l in lines if not ('"record_type": "msc_unit"' in l and "MSC_UNIT_04" in l)]
        (self.root / self.CANON).write_text("\n".join(keep) + "\n")
        errs = self._errs(self._unit())
        self.assertTrue(any("canonical MSC universe size" in e for e in errs), str(errs))

    def test_four_unit_overlay_is_not_global_closure(self):
        # four S1 units fully PENDING -> 42 OPEN; an overlay never shrinks the universe
        recs = [self._unit(unit=u) for u in ("MSC-UNIT-001", "MSC-UNIT-002", "MSC-UNIT-003", "MSC-UNIT-038")]
        for r in recs[1:]:
            r["stages"]["RUNTIME_TESTED"] = self._stage("NOT_APPLICABLE") if r["msc_unit"] != "MSC-UNIT-002" \
                else self._stage("PENDING")
        errs = self._errs(*recs)
        self.assertEqual(errs, [], str(errs))
        open_units, _ = mx.load_canonical_universe(str(self.root), [])
        msc_open, msc_closed = mx.msc_global_state(open_units, recs)
        self.assertEqual((len(msc_open), len(msc_closed)), (42, 0))

    def test_closed_overlay_unit_still_leaves_41_open(self):
        open_units, _ = mx.load_canonical_universe(str(self.root), [])
        u = self._unit(); u["stages"]["CLOSED"] = {"result": "PASS"}
        msc_open, msc_closed = mx.msc_global_state(open_units, [u])
        self.assertEqual((len(msc_open), msc_closed), (41, ["MSC-UNIT-001"]))
        self.assertNotIn("MSC-UNIT-001", msc_open)

    def _cli(self, check, state_text):
        (self.root / MSC_STATE).write_text(state_text)
        for row in (json.loads(l) for l in (REPO_ROOT / MATRIX).read_text().splitlines() if l.strip()):
            for ref in row.get("evidence_refs") or []:
                src = REPO_ROOT / ref.split("#", 1)[0]
                if src.is_file():
                    (self.root / ref).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, self.root / ref)
        r = subprocess.run([sys.executable, str(REPO_ROOT / "tools/audit/validate_b021_verification_matrix.py"),
                            "--check", check, "--repo-root", str(self.root)], capture_output=True, text=True)
        return r.returncode, r.stdout

    def test_cli_global_closure_with_four_pending_units_fails(self):
        recs = [self._unit(unit=u) for u in ("MSC-UNIT-001", "MSC-UNIT-002", "MSC-UNIT-003", "MSC-UNIT-038")]
        for r in recs[1:]:
            r["stages"]["RUNTIME_TESTED"] = self._stage("NOT_APPLICABLE") if r["msc_unit"] != "MSC-UNIT-002" \
                else self._stage("PENDING")
        rc, out = self._cli("closure", "".join(json.dumps(r) + "\n" for r in recs))
        self.assertEqual(rc, 1)
        self.assertIn("global closure NOT PERMITTED: MSC OPEN = 42", out)
        self.assertIn("SCOPE: GLOBAL REMEDIATION CLOSURE", out)

    def test_cli_global_closure_with_zero_state_records_fails(self):
        rc, out = self._cli("closure", "")
        self.assertEqual(rc, 1)
        self.assertIn("msc_state registry is EMPTY", out)
        self.assertIn("global closure NOT PERMITTED", out)

    def test_cli_integrity_reports_unit_scope_not_global_closure(self):
        rc, out = self._cli("integrity", json.dumps(self._unit()) + "\n")
        self.assertEqual(rc, 0, out)
        self.assertIn("MSC OPEN = 42   MSC CLOSED = 0", out)
        self.assertIn("NOT GLOBAL REMEDIATION CLOSURE", out)

    def test_repository_msc_state_passes_exact_rules(self):
        errs = []
        mx.check_msc_state(str(REPO_ROOT), errs)
        self.assertEqual(errs, [], str(errs))
        recs = [json.loads(l) for l in (REPO_ROOT / MSC_STATE).read_text().splitlines() if l.strip()]
        for r in recs:
            if r["msc_unit"] in ("MSC-UNIT-001", "MSC-UNIT-002"):
                self.assertEqual(r["stages"]["RUNTIME_TESTED"]["result"], "PENDING",
                                 "arm64-only implementer evidence must not be RUNTIME_TESTED=PASS under exact FCP-1")
            self.assertEqual(r["stages"]["INDEPENDENTLY_RETESTED"]["result"], "PENDING")
            self.assertNotEqual(r["stages"]["CLOSED"]["result"], "PASS")
        open_units, rejected = mx.load_canonical_universe(str(REPO_ROOT), errs)
        self.assertEqual(errs, [], str(errs))
        self.assertEqual((len(open_units), len(rejected)), (42, 2))
        self.assertEqual(mx.msc_global_state(open_units, recs), (sorted(open_units), []))


if __name__ == "__main__":
    unittest.main()
