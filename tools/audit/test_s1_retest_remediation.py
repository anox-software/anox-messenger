#!/usr/bin/env python3
"""Adversarial regression tests for the INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001
findings F1–F9, remediated by REMEDIATION-S1-CANONICAL-INTEGRATION-001.

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

CI = ".github/workflows/ci.yml"
MSC_STATE = "docs/security/remediation/msc_state.jsonl"
MATRIX = "docs/workforce/registries/b021_verification_matrix.jsonl"
INV_REG = "docs/workforce/registries/security_invariant_traceability.jsonl"


def _fake_elf(e_machine):
    b = bytearray(64)
    b[0:4] = b"\x7fELF"
    b[4] = 2
    b[5] = 1
    struct.pack_into("<H", b, 18, e_machine)
    return bytes(b)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


ARM64_SO = _fake_elf(183) + b"arm64-payload"
X86_SO = _fake_elf(62) + b"x86_64-payload"


def _manifest(confirmed=True, working_tree="clean", arm64_sha=None, x86_sha=None):
    a, x = arm64_sha or _sha(ARM64_SO), x86_sha or _sha(X86_SO)
    return {
        "schema_version": "anox-native-manifest-v1",
        "source": {"repo_sha": "0" * 40, "cargo_lock_sha256": "0" * 64, "working_tree": working_tree},
        "toolchain": {"channel": "1.97.1", "ndk_revision": "26.2.11394342",
                      "cargo_ndk": "4.1.2", "rustc": "rustc 1.97.1"},
        "build": {
            "build_id": "fixture", "profile": "release", "locked": True, "path_remapped": True,
            "reproducible_build_confirmed": confirmed,
            "reproducibility": {"method": "two-clean-builds-three-way-compare", "builds": 2,
                                "build_ids": ["r1", "r2"],
                                "per_abi_sha256": {"arm64-v8a": a, "x86_64": x}} if confirmed else None,
        },
        "abis": ["arm64-v8a", "x86_64"],
        "artifacts": [
            {"abi": "arm64-v8a", "file": "arm64-v8a/libanox_crypto.so", "sha256": a, "size": len(ARM64_SO)},
            {"abi": "x86_64", "file": "x86_64/libanox_crypto.so", "sha256": x, "size": len(X86_SO)},
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
            rc = apk_v.validate_apk(str(self.apk), manifest_path=str(self.mpath))
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
            rc = apk_v.validate_apk(str(self.apk), manifest_path=str(self.mpath))
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
            rc = apk_v.validate_apk(str(self.apk), manifest_path=str(self.mpath))
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
        m["source"]["cargo_lock_sha256"] = nb.sha256_file(self.root / "crypto/rust/Cargo.lock")
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
                                  require_clean_live_tree=False)

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


# ===========================================================================
# F6 — secret scanner
# ===========================================================================

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

    def test_oversize_file_reported_not_skipped(self):
        p = self.root / "big.bin"
        with open(p, "wb") as fh:
            fh.truncate(scan.MAX_FILE_BYTES + 1)
        f = scan.scan(str(self.root), files=["big.bin"])
        self.assertEqual([r for _, r in f], ["file_too_large_unscanned"])


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
            rc = apk_v.validate_apk(str(self.apk), manifest_path=str(self.mpath))
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

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in (MATRIX, INV_REG):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)
        (self.root / "ev").mkdir()
        (self.root / "ev/impl.md").write_text("impl")
        (self.root / "ev/manifest.json").write_text("{}")
        (self.root / "ev/arm64.xml").write_text("x")
        (self.root / "ev/x86.xml").write_text("x")
        (self.root / MSC_STATE).parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _stage(self, res, by=None, **extra):
        d = {"result": res}
        if res == "PASS":
            d.update({"evidence_refs": ["ev/impl.md"], "recorded_by": by or self.IMPL, "recorded_at": "2026-09-16"})
        if res == "NOT_APPLICABLE":
            d["reason"] = "gate table"
        d.update(extra)
        return d

    def _fcp1(self, a="a" * 64, x="b" * 64, rt_a=None, rt_x=None, **hp_over):
        hp = {"manifest_ref": "ev/manifest.json", "reproducible_build_confirmed": True,
              "per_abi_sha256": {"arm64-v8a": a, "x86_64": x}}
        hp.update(hp_over)
        return {
            "build_artifact_hash_proof": hp,
            "provenance_verified_native_runtime": {"per_abi": {
                "arm64-v8a": {"result": "PASS", "tests": 66, "failures": 0, "artifact_sha256": rt_a or a,
                              "evidence_ref": "ev/arm64.xml", "recorded_by": "CI"},
                "x86_64": {"result": "PASS", "tests": 66, "failures": 0, "artifact_sha256": rt_x or x,
                           "evidence_ref": "ev/x86.xml", "recorded_by": "CI"},
            }},
        }

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
        u = self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=self._fcp1()))
        self.assertEqual(self._errs(u), [])

    # ---- F3 exact FCP-1
    def test_runtime_pass_by_filename_token_fails(self):
        st = self._stage("PASS")
        st["evidence_refs"] = ["ev/impl.md"]
        (self.root / "ev/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME_BUILD_ARTIFACT_HASH_PROOF.md").write_text("x")
        st["evidence_refs"] = ["ev/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME_BUILD_ARTIFACT_HASH_PROOF.md"]
        errs = self._errs(self._unit(RUNTIME_TESTED=st))
        self.assertTrue(any("requires a structured `provenance` object" in e for e in errs), str(errs))

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
        p = self._fcp1(rt_x="c" * 64)
        errs = self._errs(self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=p)))
        self.assertTrue(any("same-run violation for x86_64" in e for e in errs), str(errs))

    def test_runtime_with_failures_fails(self):
        p = self._fcp1(); p["provenance_verified_native_runtime"]["per_abi"]["arm64-v8a"]["failures"] = 1
        errs = self._errs(self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=p)))
        self.assertTrue(any("not a PASS with >=1 test and 0 failures" in e for e in errs), str(errs))

    def test_runtime_unconfirmed_reproducibility_fails(self):
        p = self._fcp1(reproducible_build_confirmed=False)
        errs = self._errs(self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=p)))
        self.assertTrue(any("lacks reproducible_build_confirmed=true" in e for e in errs), str(errs))

    def test_runtime_bad_hash_hex_fails(self):
        p = self._fcp1(a="nothex")
        errs = self._errs(self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=p)))
        self.assertTrue(any("is not a SHA-256 hex" in e for e in errs), str(errs))

    def test_runtime_evidence_ref_unresolvable_fails(self):
        p = self._fcp1(); p["provenance_verified_native_runtime"]["per_abi"]["x86_64"]["evidence_ref"] = "ev/nope.xml"
        errs = self._errs(self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=p)))
        self.assertTrue(any("evidence_ref for x86_64 missing/unresolvable" in e for e in errs), str(errs))

    def test_non_provenance_unit_runtime_needs_no_fcp1(self):
        u = self._unit(unit="MSC-UNIT-003", RUNTIME_TESTED=self._stage("NOT_APPLICABLE"))
        self.assertEqual(self._errs(u), [])

    # ---- F9 ordering / omission / FCP-7
    def test_omitted_intermediate_stage_fails(self):
        u = self._unit(); del u["stages"]["RUNTIME_TESTED"]
        errs = self._errs(u)
        self.assertTrue(any("lifecycle stage record missing: RUNTIME_TESTED" in e for e in errs), str(errs))

    def test_independent_retest_without_runtime_fails(self):
        u = self._unit(INDEPENDENTLY_RETESTED=self._stage("PASS", by="INDEPENDENT-RETEST-X"))
        errs = self._errs(u)
        self.assertTrue(any("INDEPENDENTLY_RETESTED: PASS while earlier stage RUNTIME_TESTED is PENDING" in e
                            for e in errs), str(errs))

    def test_independent_retest_with_runtime_omitted_fails(self):
        u = self._unit(INDEPENDENTLY_RETESTED=self._stage("PASS", by="INDEPENDENT-RETEST-X"))
        del u["stages"]["RUNTIME_TESTED"]
        errs = self._errs(u)
        self.assertTrue(any("earlier stage RUNTIME_TESTED is missing" in e for e in errs), str(errs))

    def test_required_stage_not_applicable_cannot_be_skipped(self):
        u = self._unit(RUNTIME_TESTED=self._stage("NOT_APPLICABLE"),
                       INDEPENDENTLY_RETESTED=self._stage("PASS", by="INDEPENDENT-RETEST-X"))
        errs = self._errs(u)
        self.assertTrue(any("RUNTIME_TESTED: required stage marked NOT_APPLICABLE" in e for e in errs), str(errs))
        self.assertTrue(any("earlier stage RUNTIME_TESTED is NOT_APPLICABLE" in e for e in errs), str(errs))

    def test_reordered_lifecycle_fails(self):
        u = self._unit(AUTOMATED_TESTED=self._stage("PENDING"),
                       RUNTIME_TESTED=self._stage("PASS", provenance=self._fcp1()))
        errs = self._errs(u)
        self.assertTrue(any("RUNTIME_TESTED: PASS while earlier stage AUTOMATED_TESTED is PENDING" in e
                            for e in errs), str(errs))

    def test_closed_without_complete_chain_fails(self):
        u = self._unit(CLOSED=self._stage("PASS", by="GOV"))
        errs = self._errs(u)
        self.assertTrue(any("CLOSED while required stage RUNTIME_TESTED is PENDING" in e for e in errs), str(errs))

    def test_closed_with_omitted_stage_fails(self):
        u = self._unit(CLOSED=self._stage("PASS", by="GOV")); del u["stages"]["EVIDENCE_PRESERVED"]
        errs = self._errs(u)
        self.assertTrue(any("CLOSED without stage record EVIDENCE_PRESERVED" in e for e in errs), str(errs))

    def test_fcp7_missing_recorded_by_fails(self):
        st = self._stage("PASS"); del st["recorded_by"]
        u = self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=self._fcp1()), INDEPENDENTLY_RETESTED=st)
        errs = self._errs(u)
        self.assertTrue(any("retest stage PASS without recorded_by" in e for e in errs), str(errs))

    def test_fcp7_whitespace_case_variant_of_implementer_fails(self):
        u = self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=self._fcp1()),
                       INDEPENDENTLY_RETESTED=self._stage("PASS", by=" remediation-session-s1-build-provenance-001 "))
        errs = self._errs(u)
        self.assertTrue(any("recorded by implementing session" in e for e in errs), str(errs))

    def test_fcp7_implementer_prefixed_alias_fails(self):
        u = self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=self._fcp1()),
                       INDEPENDENTLY_RETESTED=self._stage("PASS", by=self.IMPL + "-retest"))
        errs = self._errs(u)
        self.assertTrue(any("recorded by implementing session" in e for e in errs), str(errs))

    def test_fcp7_distinct_authority_passes(self):
        u = self._unit(RUNTIME_TESTED=self._stage("PASS", provenance=self._fcp1()),
                       INDEPENDENTLY_RETESTED=self._stage("PASS", by="INDEPENDENT-BUILD-SUPPLY-RETEST-S1-002"))
        self.assertEqual(self._errs(u), [])

    def test_pass_without_recorded_at_fails(self):
        st = self._stage("PASS"); del st["recorded_at"]
        errs = self._errs(self._unit(AUTOMATED_TESTED=st))
        self.assertTrue(any("PASS without recorded_at" in e for e in errs), str(errs))

    def test_missing_implementing_session_fails(self):
        u = self._unit(); u["implementing_session"] = ""
        errs = self._errs(u)
        self.assertTrue(any("implementing_session missing" in e for e in errs), str(errs))

    def test_repository_msc_state_passes_exact_rules(self):
        errs = []
        mx.check_msc_state(str(REPO_ROOT), errs)
        self.assertEqual(errs, [], str(errs))
        recs = [json.loads(l) for l in (REPO_ROOT / MSC_STATE).read_text().splitlines() if l.strip()]
        for r in recs:
            if r["msc_unit"] in ("MSC-UNIT-001", "MSC-UNIT-002"):
                self.assertEqual(r["stages"]["RUNTIME_TESTED"]["result"], "PENDING",
                                 "arm64-only implementer evidence must not be RUNTIME_TESTED=PASS under exact FCP-1")
            self.assertNotEqual(r["stages"]["CLOSED"]["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
