#!/usr/bin/env python3
"""Adversarial fail-closed tests for the S1 build-provenance gate stack.

REMEDIATION-SESSION-S1-CLEAN-REBUILD-001 — every negative mutation below
must make the relevant S1 gate FAIL. The canonical repository surfaces are
copied into temporary fixtures; one aspect is mutated per test; the gate is
then exercised directly (importlib-loaded modules, no subprocess cost).

Gates covered:
  * tools/security/native_build.py        (manifest verify / JNI parity / repro)
  * tools/security/validate_apk_contents.py v2 (packaged-artifact binding)
  * tools/security/validate_ci_pipeline.py    (CI structural gate)
  * tools/security/secret_scan.py             (secret material)
  * tools/audit/validate_b021_verification_matrix.py (MSC-038 matrix/stages)
  * tools/audit/validate_s1_build_provenance.py    (repository static gate)
"""

import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import struct
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


nb = _load("anox_native_build", "tools/security/native_build.py")
apk_v = _load("anox_apk_validate", "tools/security/validate_apk_contents.py")
ci_v = _load("anox_ci_validate", "tools/security/validate_ci_pipeline.py")
scan = _load("anox_secret_scan", "tools/security/secret_scan.py")
mx = _load("anox_b021_matrix", "tools/audit/validate_b021_verification_matrix.py")
s1 = _load("anox_s1_static", "tools/audit/validate_s1_build_provenance.py")
ef = _load("anox_elf_fixture", "tools/audit/elf_fixture.py")

CI = ".github/workflows/ci.yml"
GRADLE = "android/build.gradle.kts"
TOOLCHAIN = "crypto/rust/rust-toolchain.toml"
POLICY = "docs/current/REPOSITORY_SECURITY_POLICY.md"
MSC_STATE = "docs/security/remediation/msc_state.jsonl"
MATRIX = "docs/workforce/registries/b021_verification_matrix.jsonl"
INV_REG = "docs/workforce/registries/security_invariant_traceability.jsonl"
CANONICAL = "docs/security/audit-evidence/audit_traceability.jsonl"
EVIDENCE_REG = "docs/security/remediation/evidence_registry.jsonl"

# Files needed for a working static-gate fixture.
STATIC_FIXTURE = [
    CI, GRADLE, TOOLCHAIN, POLICY, MSC_STATE, ".gitignore",
    "tools/security/native_build.py",
    "tools/security/validate_apk_contents.py",
    "tools/security/validate_ci_pipeline.py",
    "tools/security/secret_scan.py",
    "tools/audit/validate_b021_verification_matrix.py",
    "tools/audit/validate_s1_build_provenance.py",
]

# Files the manifest verifier needs to resolve source-level provenance.
NATIVE_SRC_FIXTURE = [
    TOOLCHAIN,
    "crypto/rust/Cargo.lock",
    "crypto/android/src/main/java/com/anox/crypto/CryptoNative.kt",
    "crypto/rust/src/lib.rs",
]


# Source-derived expected JNI surface of the reviewed Kotlin/Rust sources.
EXPECTED_JNI = sorted(nb.expected_jni_exports(str(REPO_ROOT), []))


def _fake_elf(e_machine, exports=None, payload=b""):
    """A REAL minimal ELF64 shared object whose .dynsym defines `exports`
    (default: the full source-derived JNI surface)."""
    return ef.fake_elf_so(e_machine, EXPECTED_JNI if exports is None else exports, payload)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


ARM64_SO = _fake_elf(183, payload=b"arm64-payload")
X86_SO = _fake_elf(62, payload=b"x86_64-payload")
JNI_FP = nb.sha256_text("\n".join(EXPECTED_JNI))


LOCK_SHA = nb.sha256_file(REPO_ROOT / "crypto/rust/Cargo.lock")
FIXTURE_SRC_SHA = "0" * 40


def _manifest(arm64_sha=None, x86_sha=None, repo_sha=FIXTURE_SRC_SHA):
    return {
        "schema_version": "anox-native-manifest-v1",
        "source": {"repo_sha": repo_sha, "crate": "crypto/rust", "crate_manifest": "crypto/rust/Cargo.toml",
                   "cargo_lock_sha256": LOCK_SHA, "rust_toolchain_file": TOOLCHAIN, "working_tree": "clean"},
        "toolchain": {
            "channel": "1.97.1", "ndk_revision": "26.2.11394342",
            "cargo_ndk": "4.1.2", "rustc": "rustc 1.97.1", "host": "x86_64",
        },
        "build": _repro_build(arm64_sha or _sha(ARM64_SO), x86_sha or _sha(X86_SO)),
        "abis": ["arm64-v8a", "x86_64"],
        "artifacts": [
            {"abi": "arm64-v8a", "file": "arm64-v8a/libanox_crypto.so", "rust_target": "aarch64-linux-android",
             "elf_machine": 183, "sha256": arm64_sha or _sha(ARM64_SO), "size": len(ARM64_SO),
             "jni_export_count": len(EXPECTED_JNI), "jni_exports": EXPECTED_JNI, "jni_exports_sha256": JNI_FP},
            {"abi": "x86_64", "file": "x86_64/libanox_crypto.so", "rust_target": "x86_64-linux-android",
             "elf_machine": 62, "sha256": x86_sha or _sha(X86_SO), "size": len(X86_SO),
             "jni_export_count": len(EXPECTED_JNI), "jni_exports": EXPECTED_JNI, "jni_exports_sha256": JNI_FP},
        ],
    }


def _repro_build(arm64_sha, x86_sha, confirmed=True):
    """Authoritative reproducibility attestation as written by rebuild-compare (F5)."""
    return {
        "build_id": "fixture", "profile": "release", "locked": True, "path_remapped": True,
        "reproducible_build_confirmed": confirmed,
        "reproducibility": {
            "method": "two-clean-builds-three-way-compare", "builds": 2,
            "build_ids": ["fixture-repro1", "fixture-repro2"],
            "per_abi_sha256": {"arm64-v8a": arm64_sha, "x86_64": x86_sha},
        } if confirmed else None,
    }


def _apk(path, members):
    """Write a minimal APK zip: manifest + dex + resources + given members."""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("AndroidManifest.xml", b"\x03\x00\x08\x00binary")
        z.writestr("classes.dex", b"dex\n035\0fake")
        z.writestr("resources.arsc", b"arsc")
        for name, data in members.items():
            z.writestr(name, data)


def _good_apk(path):
    _apk(path, {
        "lib/arm64-v8a/libanox_crypto.so": ARM64_SO,
        "lib/x86_64/libanox_crypto.so": X86_SO,
    })


def _load_jsonl(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def _write_jsonl(p, rows):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text("\n".join(json.dumps(r) for r in rows) + "\n")


class ApkValidatorV2Tests(unittest.TestCase):
    """Mutations against tools/security/validate_apk_contents.py v2."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.apk = self.root / "app.apk"
        self.mpath = self.root / "native-manifest.json"
        _good_apk(self.apk)
        self.mpath.write_text(json.dumps(_manifest()))
        self.out = io.StringIO()

    def tearDown(self):
        self.tmp.cleanup()

    def _rc(self, manifest="__default__", expected_source_sha=FIXTURE_SRC_SHA):
        m = str(self.mpath) if manifest == "__default__" else manifest
        self.out = io.StringIO()
        with redirect_stdout(self.out):
            rc = apk_v.validate_apk(str(self.apk), manifest_path=m, expected_source_sha=expected_source_sha)
        return rc

    def test_00_control_valid_apk_passes(self):
        self.assertEqual(self._rc(), 0, self.out.getvalue())

    def test_01_unexpected_so_injected_fails(self):
        _good_apk(self.apk)
        with zipfile.ZipFile(self.apk, "a") as z:
            z.writestr("lib/arm64-v8a/libevil.so", _fake_elf(183))
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("unexpected native library", self.out.getvalue())

    def test_02_wrong_abi_elf_machine_fails(self):
        # x86_64 ELF packaged under the arm64-v8a directory.
        _apk(self.apk, {
            "lib/arm64-v8a/libanox_crypto.so": X86_SO,
            "lib/x86_64/libanox_crypto.so": X86_SO,
        })
        rc = self._rc()
        self.assertNotEqual(rc, 0)
        self.assertIn("ELF machine", self.out.getvalue())

    def test_03_missing_abi_fails(self):
        _apk(self.apk, {"lib/arm64-v8a/libanox_crypto.so": ARM64_SO})
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("ABI set", self.out.getvalue())

    def test_04_packaged_hash_mismatch_fails(self):
        _apk(self.apk, {
            "lib/arm64-v8a/libanox_crypto.so": ARM64_SO + b"tampered",
            "lib/x86_64/libanox_crypto.so": X86_SO,
        })
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("hash mismatch", self.out.getvalue())

    def test_05_manifest_artifact_hash_edited_fails(self):
        m = _manifest(arm64_sha="f" * 64)
        self.mpath.write_text(json.dumps(m))
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("hash mismatch", self.out.getvalue())

    def test_06_manifest_source_sha_edited_fails(self):
        m = _manifest(repo_sha="not-a-sha")
        self.mpath.write_text(json.dumps(m))
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("repo_sha", self.out.getvalue())

    def test_07_missing_manifest_arg_fails(self):
        self.assertNotEqual(self._rc(manifest=None), 0)

    def test_08_manifest_file_absent_fails(self):
        self.assertNotEqual(self._rc(manifest=str(self.root / "nope.json")), 0)

    def test_09_manifest_malformed_json_fails(self):
        self.mpath.write_text("{ not json")
        self.assertNotEqual(self._rc(), 0)

    def test_10_private_key_in_apk_member_fails(self):
        _apk(self.apk, {
            "lib/arm64-v8a/libanox_crypto.so": ARM64_SO,
            "lib/x86_64/libanox_crypto.so": X86_SO,
            "assets/keys.pem": b"-----BEGIN PRIVATE KEY-----\nMIIxx\n-----END PRIVATE KEY-----\n",
        })
        # .pem member is also a forbidden path — either signal must fail it.
        rc = self._rc()
        self.assertNotEqual(rc, 0)

    def test_11_pem_inside_native_library_fails(self):
        tainted = ARM64_SO + b"\n-----BEGIN RSA PRIVATE KEY-----\nMIIxx\n"
        m = _manifest(arm64_sha=_sha(tainted))
        self.mpath.write_text(json.dumps(m))
        _apk(self.apk, {
            "lib/arm64-v8a/libanox_crypto.so": tainted,
            "lib/x86_64/libanox_crypto.so": X86_SO,
        })
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("secret marker", self.out.getvalue())

    def test_12_forbidden_member_fails(self):
        _apk(self.apk, {
            "lib/arm64-v8a/libanox_crypto.so": ARM64_SO,
            "lib/x86_64/libanox_crypto.so": X86_SO,
            "assets/.env": b"SECRET=1",
        })
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("forbidden APK member", self.out.getvalue())

    def test_13_not_a_zip_fails(self):
        self.apk.write_bytes(b"definitely not a zip")
        self.assertNotEqual(self._rc(), 0)

    # ---- R-005: the APK validator inspects the ACTUAL packaged binary
    def test_13a_packaged_binary_missing_jni_export_with_rebound_manifest_fails(self):
        missing = EXPECTED_JNI[3]
        mutated = _fake_elf(183, [s for s in EXPECTED_JNI if s != missing], b"arm64-payload")
        self.mpath.write_text(json.dumps(_manifest(arm64_sha=_sha(mutated))))
        _apk(self.apk, {"lib/arm64-v8a/libanox_crypto.so": mutated, "lib/x86_64/libanox_crypto.so": X86_SO})
        self.assertNotEqual(self._rc(), 0)
        out = self.out.getvalue()
        self.assertIn("ACTUAL packaged-binary JNI exports differ from source-derived surface", out)
        self.assertIn(missing, out)

    def test_13b_packaged_binary_missing_export_fully_rebound_manifest_fails(self):
        mutated_list = EXPECTED_JNI[1:]
        mutated = _fake_elf(62, mutated_list, b"x86_64-payload")
        m = _manifest(x86_sha=_sha(mutated))
        m["artifacts"][1].update({"jni_exports": mutated_list, "jni_export_count": len(mutated_list),
                                  "jni_exports_sha256": nb.sha256_text("\n".join(mutated_list))})
        self.mpath.write_text(json.dumps(m))
        _apk(self.apk, {"lib/arm64-v8a/libanox_crypto.so": ARM64_SO, "lib/x86_64/libanox_crypto.so": mutated})
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("differ from source-derived surface", self.out.getvalue())

    def test_13c_header_only_placeholder_so_fails(self):
        ph = ef.fake_elf_header_only(183)
        self.mpath.write_text(json.dumps(_manifest(arm64_sha=_sha(ph))))
        _apk(self.apk, {"lib/arm64-v8a/libanox_crypto.so": ph, "lib/x86_64/libanox_crypto.so": X86_SO})
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("JNI is NOT verified", self.out.getvalue())

    def test_13d_unanchored_source_sha_fails(self):
        # syntactically valid SHA, but no anchor supplied and fixture is not the repo HEAD
        self.assertNotEqual(self._rc(expected_source_sha=None), 0)
        self.assertIn("!= expected anchor", self.out.getvalue())

    def test_13e_wrong_anchor_fails(self):
        self.assertNotEqual(self._rc(expected_source_sha="b" * 40), 0)
        self.assertIn("!= expected anchor", self.out.getvalue())

    def test_13f_wrong_cargo_lock_identity_fails(self):
        m = _manifest(); m["source"]["cargo_lock_sha256"] = "1" * 64
        self.mpath.write_text(json.dumps(m))
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("cargo_lock_sha256 does not match", self.out.getvalue())

    def test_13g_absent_reproducibility_details_fails(self):
        m = _manifest(); m["build"]["reproducibility"]["build_ids"] = ["only-one"]
        self.mpath.write_text(json.dumps(m))
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("two distinct clean rebuilds", self.out.getvalue())

    def test_13h_manifest_export_list_missing_fails(self):
        m = _manifest(); del m["artifacts"][0]["jni_exports"]
        self.mpath.write_text(json.dumps(m))
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("jni_exports list missing", self.out.getvalue())

    # ---- section 18: binary-member token coverage aligned with the repo scanner
    def test_13i_api_token_inside_binary_member_fails(self):
        tainted = ARM64_SO + b"\x00" + b"ghp_" + b"a" * 36 + b"\x00"
        self.mpath.write_text(json.dumps(_manifest(arm64_sha=_sha(tainted))))
        _apk(self.apk, {"lib/arm64-v8a/libanox_crypto.so": tainted, "lib/x86_64/libanox_crypto.so": X86_SO})
        self.assertNotEqual(self._rc(), 0)
        self.assertIn("secret marker in APK member: lib/arm64-v8a/libanox_crypto.so (rule: github_token)", self.out.getvalue())

    def test_13j_aws_key_in_asset_and_generic_assignment_in_dex_fail(self):
        _apk(self.apk, {"lib/arm64-v8a/libanox_crypto.so": ARM64_SO, "lib/x86_64/libanox_crypto.so": X86_SO,
                        "assets/config.bin": b"\x00cfg" + b"AKIA" + b"IOSFODNN7EXAMPLE" + b"\x00",
                        "classes2.dex": b"dex\n035\x00" + b"client_secret=\"" + b"Z" * 40 + b"\""})
        self.assertNotEqual(self._rc(), 0)
        out = self.out.getvalue()
        self.assertIn("assets/config.bin (rule: aws_access_key)", out)
        self.assertIn("classes2.dex (rule: generic_api_secret_assignment)", out)

    def test_13k_all_canonical_forbidden_path_patterns_preserved(self):
        canonical = [r"^docs/authority/", r"^docs/continuity/", r"^docs/history/", r"^docs/security/",
                     r"^docs/workforce/", r"^PROJECT_STATE\.md$", r"^FORTSCHRITT\.md$",
                     r"^DEVIN_PROMPT_OUTPUT_ARCHIV\.md$", r"^MAIN_PLAN_DE\.md$", r"^ANOX_HANDOFF_",
                     r"^GIT_SNAPSHOT\.txt$", r"^CURRENT_HANDOFF\.md$", r"^CURRENT_GIT_STATE\.md$",
                     r"^CURRENT_STATE\.json$", r"^CURRENT_NEXT_DEVIN_TASK\.md$",
                     r"^CURRENT_IMPLEMENTATION_STATE\.md$", r"^CURRENT_OPEN_WORK\.md$", r"^\.git/",
                     r"(^|/)\.env$", r"(^|/)\.env\.", r"^local\.properties$", r"\.jks$", r"\.keystore$",
                     r"\.p12$", r"\.pfx$", r"\.pem$", r"\.key$"]
        self.assertEqual(apk_v.FORBIDDEN_PATH_PATTERNS, canonical)
        for member in ("docs/authority/x.md", "CURRENT_STATE.json", "assets/.env.prod", "keys/a.p12", ".git/HEAD"):
            _apk(self.apk, {"lib/arm64-v8a/libanox_crypto.so": ARM64_SO, "lib/x86_64/libanox_crypto.so": X86_SO,
                            member: b"x"})
            self.assertNotEqual(self._rc(), 0, member)
            self.assertIn("forbidden APK member: " + member, self.out.getvalue())


class NativeBuildManifestTests(unittest.TestCase):
    """Mutations against native_build.verify_manifest + symbol parity."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in NATIVE_SRC_FIXTURE:
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)
        self.prod = self.root / "build/native/jniLibs"
        (self.prod / "arm64-v8a").mkdir(parents=True)
        (self.prod / "x86_64").mkdir(parents=True)
        (self.prod / "arm64-v8a/libanox_crypto.so").write_bytes(ARM64_SO)
        (self.prod / "x86_64/libanox_crypto.so").write_bytes(X86_SO)
        self.mpath = self.root / "build/native/native-manifest.json"
        self._write_manifest()

    def tearDown(self):
        self.tmp.cleanup()

    def _jni_fp(self):
        errs = []
        expected = nb.expected_jni_exports(str(self.root), errs)
        self.assertFalse(errs)
        return nb.sha256_text("\n".join(sorted(expected))), len(expected)

    def _write_manifest(self, **over):
        fp, count = self._jni_fp()
        lock_sha = nb.sha256_file(self.root / "crypto/rust/Cargo.lock")
        channel, _, _ = nb.parse_toolchain_toml(self.root / TOOLCHAIN)
        a_so = (self.prod / "arm64-v8a/libanox_crypto.so").read_bytes()
        x_so = (self.prod / "x86_64/libanox_crypto.so").read_bytes()
        m = {
            "schema_version": "anox-native-manifest-v1",
            "source": {"repo_sha": self.SRC_SHA, "crate": "crypto/rust", "crate_manifest": "crypto/rust/Cargo.toml",
                       "cargo_lock_sha256": lock_sha, "rust_toolchain_file": TOOLCHAIN, "working_tree": "clean"},
            "toolchain": {
                "channel": channel, "ndk_revision": "26.2.11394342",
                "cargo_ndk": "4.1.2", "rustc": f"rustc {channel}", "host": "x86_64",
            },
            "build": _repro_build(_sha(a_so), _sha(x_so)),
            "abis": ["arm64-v8a", "x86_64"],
            "artifacts": [
                {"abi": "arm64-v8a", "file": "arm64-v8a/libanox_crypto.so",
                 "sha256": _sha(a_so), "size": len(a_so),
                 "rust_target": "aarch64-linux-android", "elf_machine": 183,
                 "jni_exports": EXPECTED_JNI, "jni_exports_sha256": fp, "jni_export_count": count},
                {"abi": "x86_64", "file": "x86_64/libanox_crypto.so",
                 "sha256": _sha(x_so), "size": len(x_so),
                 "rust_target": "x86_64-linux-android", "elf_machine": 62,
                 "jni_exports": EXPECTED_JNI, "jni_exports_sha256": fp, "jni_export_count": count},
            ],
        }
        m.update(over)
        self.mpath.write_text(json.dumps(m))
        return m

    SRC_SHA = "0" * 40

    def _verify(self, expected_source_sha=SRC_SHA):
        return nb.verify_manifest(
            str(self.root), str(self.mpath), str(self.prod),
            expected_source_sha=expected_source_sha,
            require_clean_live_tree=False,  # fixture has no git; F7 live-tree tests use real repos
        )

    def _rebind(self, abi, so_bytes):
        """Write a substituted binary AND rebind the manifest hashes/size to it
        (the reviewer's 'rebound manifest' attack)."""
        (self.prod / abi / "libanox_crypto.so").write_bytes(so_bytes)
        m = json.loads(self.mpath.read_text())
        for a in m["artifacts"]:
            if a["abi"] == abi:
                a["sha256"], a["size"] = _sha(so_bytes), len(so_bytes)
        m["build"]["reproducibility"]["per_abi_sha256"][abi] = _sha(so_bytes)
        self.mpath.write_text(json.dumps(m))

    def test_14_control_valid_manifest_passes(self):
        errs = self._verify()
        self.assertEqual(errs, [], str(errs))

    def test_15_stale_artifact_substituted_fails(self):
        # swap the produced .so for a different blob after manifest written
        (self.prod / "arm64-v8a/libanox_crypto.so").write_bytes(ARM64_SO + b"stale")
        errs = self._verify()
        self.assertTrue(any("sha256 mismatch" in e for e in errs), str(errs))

    def test_16_manifest_hash_edited_fails(self):
        m = json.loads(self.mpath.read_text())
        m["artifacts"][0]["sha256"] = "e" * 64
        self.mpath.write_text(json.dumps(m))
        errs = self._verify()
        self.assertTrue(any("sha256 mismatch" in e for e in errs), str(errs))

    def test_17_manifest_source_sha_drift_fails(self):
        errs = self._verify(expected_source_sha="a" * 40)
        self.assertTrue(any("repo_sha" in e for e in errs), str(errs))

    def test_18_missing_abi_artifact_fails(self):
        (self.prod / "x86_64/libanox_crypto.so").unlink()
        errs = self._verify()
        self.assertTrue(errs)

    def test_19_stray_unmanifested_so_fails(self):
        (self.prod / "arm64-v8a/libother.so").write_bytes(ARM64_SO)
        errs = self._verify()
        self.assertTrue(any("not in manifest" in e for e in errs), str(errs))

    def test_20_unexpected_abi_in_manifest_fails(self):
        m = json.loads(self.mpath.read_text())
        m["artifacts"].append({
            "abi": "armeabi-v7a", "file": "armeabi-v7a/libanox_crypto.so",
            "sha256": _sha(ARM64_SO), "size": 1,
            "rust_target": "armv7-linux-androideabi",
            "jni_exports_sha256": "0" * 64, "jni_export_count": 17})
        self.mpath.write_text(json.dumps(m))
        errs = self._verify()
        self.assertTrue(any("unexpected ABI" in e or "ABI set" in e for e in errs), str(errs))

    def test_21_jni_surface_drift_fails(self):
        # remove one Rust export -> fingerprint mismatch + missing export
        lib = self.root / "crypto/rust/src/lib.rs"
        text = lib.read_text()
        text2, n = re.subn(r"fn\s+Java_com_anox_crypto_CryptoNative_(\w+)",
                           "fn REMOVED_\\1", text, count=1)
        self.assertEqual(n, 1)
        lib.write_text(text2)
        errs = self._verify()
        self.assertTrue(errs)

    def test_22_jni_symbol_absent_from_binary_fails(self):
        # R-005 (reviewer-proven bypass): remove one ACTUAL export from the
        # binary and rebind the manifest hashes — verify must still fail.
        missing = EXPECTED_JNI[0]
        self._rebind("arm64-v8a", _fake_elf(183, [s for s in EXPECTED_JNI if s != missing], b"arm64-payload"))
        errs = self._verify()
        self.assertTrue(any("ACTUAL binary JNI exports differ from source-derived surface" in e
                            and missing in e for e in errs), str(errs))
        self.assertTrue(any("manifest jni_exports differ from the ACTUAL binary" in e for e in errs), str(errs))

    def test_22a_jni_export_removed_and_manifest_fully_rebound_fails(self):
        # attacker also rewrites the manifest export list/fingerprint/count to
        # match the mutated binary: source-derived surface still disagrees
        missing = EXPECTED_JNI[-1]
        mutated = [s for s in EXPECTED_JNI if s != missing]
        self._rebind("x86_64", _fake_elf(62, mutated, b"x86_64-payload"))
        m = json.loads(self.mpath.read_text())
        for a in m["artifacts"]:
            if a["abi"] == "x86_64":
                a["jni_exports"], a["jni_export_count"] = mutated, len(mutated)
                a["jni_exports_sha256"] = nb.sha256_text("\n".join(mutated))
        self.mpath.write_text(json.dumps(m))
        errs = self._verify()
        self.assertTrue(any("ACTUAL binary JNI exports differ from source-derived surface" in e for e in errs), str(errs))
        self.assertTrue(any("fingerprint differs from source-derived" in e for e in errs), str(errs))

    def test_22b_extra_foreign_export_in_binary_fails(self):
        self._rebind("arm64-v8a", _fake_elf(183, EXPECTED_JNI + ["Java_com_anox_crypto_CryptoNative_backdoor"]))
        errs = self._verify()
        self.assertTrue(any("(extra: Java_com_anox_crypto_CryptoNative_backdoor)" in e for e in errs), str(errs))

    def test_22c_non_elf_placeholder_fails(self):
        self._rebind("arm64-v8a", b"placeholder bytes, not an ELF\n")
        errs = self._verify()
        self.assertTrue(any("not a verifiable ELF64 shared object" in e for e in errs), str(errs))
        self.assertTrue(any("JNI is NOT verified" in e for e in errs), str(errs))

    def test_22d_header_only_elf_without_symbol_table_fails(self):
        self._rebind("x86_64", ef.fake_elf_header_only(62))
        errs = self._verify()
        self.assertTrue(any("not a verifiable ELF64 shared object" in e for e in errs), str(errs))

    def test_22e_wrong_actual_elf_architecture_fails(self):
        # an x86_64 binary placed under arm64-v8a with manifest hashes rebound
        self._rebind("arm64-v8a", _fake_elf(62, payload=b"wrong-arch"))
        errs = self._verify()
        self.assertTrue(any("ELF e_machine 62 does not match ABI arm64-v8a" in e for e in errs), str(errs))

    def test_22f_manifest_elf_machine_field_mismatch_fails(self):
        m = json.loads(self.mpath.read_text()); m["artifacts"][0]["elf_machine"] = 62
        self.mpath.write_text(json.dumps(m))
        errs = self._verify()
        self.assertTrue(any("manifest elf_machine 62 != 183" in e for e in errs), str(errs))

    def test_22g_wrong_source_sha_fails(self):
        m = json.loads(self.mpath.read_text()); m["source"]["repo_sha"] = "a" * 40
        self.mpath.write_text(json.dumps(m))
        errs = self._verify()
        self.assertTrue(any("repo_sha aaaaaaaa" in e and "!= expected" in e for e in errs), str(errs))

    def test_22h_no_source_anchor_available_fails(self):
        # not a git checkout and no explicit anchor: a syntactically valid SHA is not provenance
        errs = self._verify(expected_source_sha=None)
        self.assertTrue(any("no expected source anchor available" in e for e in errs), str(errs))

    def test_22i_wrong_cargo_lock_identity_fails(self):
        (self.root / "crypto/rust/Cargo.lock").write_text("# different lock\n")
        errs = self._verify()
        self.assertTrue(any("cargo_lock_sha256 does not match Cargo.lock" in e for e in errs), str(errs))

    def test_22j_absent_reproducibility_details_fails(self):
        m = json.loads(self.mpath.read_text())
        m["build"]["reproducibility"] = None
        self.mpath.write_text(json.dumps(m))
        errs = self._verify()
        self.assertTrue(any("reproducibility attestation malformed" in e for e in errs), str(errs))
        m["build"]["reproducibility"] = {"method": "two-clean-builds-three-way-compare", "builds": 2,
                                         "build_ids": ["same", "same"],
                                         "per_abi_sha256": {a["abi"]: a["sha256"] for a in m["artifacts"]}}
        self.mpath.write_text(json.dumps(m))
        errs = self._verify()
        self.assertTrue(any("two distinct clean rebuilds" in e for e in errs), str(errs))

    def test_22k_toolchain_semantics_enforced(self):
        for key, val, msg in (("cargo_ndk", "4.0.0", "cargo_ndk"), ("rustc", "rustc 1.80.0", "not the pinned rustc"),
                              ("ndk_revision", "25.2.9519653", "ndk_revision")):
            m = json.loads(self.mpath.read_text()); m["toolchain"][key] = val
            self.mpath.write_text(json.dumps(m))
            errs = self._verify()
            self.assertTrue(any(msg in e for e in errs), (key, errs))
            self._write_manifest()

    def test_22l_schema_drift_fails(self):
        m = json.loads(self.mpath.read_text()); m["extra"] = {"x": 1}; del m["artifacts"][0]["jni_exports"]
        self.mpath.write_text(json.dumps(m))
        errs = self._verify()
        self.assertTrue(any("differ from exact schema" in e for e in errs), str(errs))
        self.assertTrue(any("jni_exports list missing" in e for e in errs), str(errs))

    def test_22m_alternative_native_input_fails(self):
        d = self.root / "android/src/main/jniLibs/arm64-v8a"; d.mkdir(parents=True)
        (d / "libanox_crypto.so").write_bytes(ARM64_SO)
        (self.root / "android/libs").mkdir(parents=True)
        (self.root / "android/libs/native-prebuilt.aar").write_bytes(b"PK\x03\x04")
        errs = self._verify()
        self.assertTrue(any("uncontrolled alternative native input present: android/src/main/jniLibs/arm64-v8a/libanox_crypto.so"
                            in e for e in errs), str(errs))
        self.assertTrue(any("android/libs/native-prebuilt.aar" in e for e in errs), str(errs))

    def test_22n_symbol_reader_disagreement_refuses(self):
        orig = nb.dynamic_symbols
        try:
            nb.dynamic_symbols = lambda *a, **k: None
            errs = self._verify()
        finally:
            nb.dynamic_symbols = orig
        self.assertTrue(any("readers disagree or binary unreadable" in e for e in errs), str(errs))

    def test_23_rebuild_compare_detects_divergence(self):
        # the attestation writer must refuse when a clean rebuild diverges from the
        # primary manifest, and must leave reproducible_build_confirmed untouched
        primary = json.loads(self.mpath.read_text())
        primary["build"]["reproducible_build_confirmed"] = False
        primary["build"]["reproducibility"] = None
        self.mpath.write_text(json.dumps(primary))
        same = {"artifacts": [{"abi": a["abi"], "sha256": a["sha256"]} for a in primary["artifacts"]]}
        diverged = {"artifacts": [{"abi": "arm64-v8a", "sha256": primary["artifacts"][0]["sha256"]},
                                  {"abi": "x86_64", "sha256": "c" * 64}]}
        errs = nb.attest_reproducibility(str(self.mpath), same, diverged, ["r1", "r2"])
        self.assertTrue(any("DIFF x86_64" in e for e in errs), str(errs))
        self.assertIs(json.loads(self.mpath.read_text())["build"]["reproducible_build_confirmed"], False)
        # and succeeds (writing the attestation) only when all three agree
        errs = nb.attest_reproducibility(str(self.mpath), same, same, ["r1", "r2"])
        self.assertEqual(errs, [], str(errs))
        self.assertIs(json.loads(self.mpath.read_text())["build"]["reproducible_build_confirmed"], True)

    def test_24_unpinned_toolchain_channel_fails(self):
        tc = self.root / TOOLCHAIN
        tc.write_text('[toolchain]\nchannel = "stable"\n'
                      'targets = ["aarch64-linux-android", "x86_64-linux-android"]\n')
        import subprocess as _sp
        orig = nb._run
        try:
            # external tools stubbed as unavailable so only repository-derived errors matter
            nb._run = lambda *a, **k: _sp.CompletedProcess(a, 1, "", "stub")
            errs = nb.check_toolchain(str(self.root), ndk_path=str(self.root / "no-ndk"))
        finally:
            nb._run = orig
        self.assertTrue(any("not an exact version pin" in e for e in errs), str(errs))


class CiPipelineStructureTests(unittest.TestCase):
    """Mutations against .github/workflows/ci.yml structural gate."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.wf = self.root / "ci.yml"
        self.wf.write_text((REPO_ROOT / CI).read_text())

    def tearDown(self):
        self.tmp.cleanup()

    def _mutate(self, fn):
        self.wf.write_text(fn(self.wf.read_text()))
        return ci_v.validate(str(self.wf))

    def _drop_job(self, name):
        def fn(text):
            lines = text.splitlines()
            out, skip = [], False
            for line in lines:
                if re.match(r"^  [\w-]+:\s*$", line):
                    skip = line.strip() == name + ":"
                if not skip:
                    out.append(line)
            return "\n".join(out)
        return fn

    def test_25_control_workflow_passes(self):
        self.assertEqual(ci_v.validate(str(self.wf)), [])

    def test_26_native_build_job_removed_fails(self):
        errs = self._mutate(self._drop_job("native-build"))
        self.assertTrue(any("native-build" in e for e in errs), str(errs))

    def test_27_instrumented_arm64_removed_fails(self):
        errs = self._mutate(self._drop_job("instrumented-arm64"))
        self.assertTrue(errs)

    def test_28_instrumented_x86_64_removed_fails(self):
        errs = self._mutate(self._drop_job("instrumented-x86_64"))
        self.assertTrue(errs)

    def test_29_advisory_scan_removed_fails(self):
        errs = self._mutate(lambda t: t.replace("cargo audit", "echo audit"))
        self.assertTrue(any("advisory" in e for e in errs), str(errs))

    def test_30_secret_scan_removed_fails(self):
        errs = self._mutate(lambda t: re.sub(r"^\s*run: python3 tools/security/secret_scan\.py.*$", "", t, flags=re.M))
        self.assertTrue(any("secret scan" in e for e in errs), str(errs))

    def test_31_lint_gate_removed_fails(self):
        def fn(text):
            # remove the entire lint step (name + run) from the android-debug job
            return re.sub(
                r"      - name: Android lint \(errors fatal\)\n        run: \./gradlew --no-daemon :android:lintDebug\n",
                "", text)
        errs = self._mutate(fn)
        self.assertTrue(any("lint" in e for e in errs), str(errs))

    def test_32_b021_validator_removed_fails(self):
        errs = self._mutate(lambda t: t.replace("validate_b021_verification_matrix.py", "echo matrix"))
        self.assertTrue(any("B-021" in e for e in errs), str(errs))

    def test_33_apk_manifest_binding_removed_fails(self):
        errs = self._mutate(lambda t: t.replace("--native-manifest build/native/native-manifest.json", ""))
        self.assertTrue(any("provenance binding" in e for e in errs), str(errs))

    def test_34_artifact_download_removed_fails(self):
        errs = self._mutate(lambda t: t.replace("download-artifact@", "checkout@"))
        self.assertTrue(any("download" in e or "consumes" in e for e in errs), str(errs))


class SecretScanTests(unittest.TestCase):
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

    def test_35_control_clean_tree_passes(self):
        self.assertEqual(self._scan({"src/main.kt": "fun main() {}\n"}), [])

    def test_36_pem_private_key_fails(self):
        f = self._scan({"keys/id.pem": "-----BEGIN PRIVATE KEY-----\nMII\n-----END PRIVATE KEY-----\n"})
        self.assertTrue(f)

    def test_37_pem_block_in_text_file_fails(self):
        f = self._scan({"config/notes.txt": "backup:\n-----BEGIN RSA PRIVATE KEY-----\nMII\n"})
        self.assertTrue(f)

    def test_38_tracked_env_file_fails(self):
        f = self._scan({".env": "A=1"})
        self.assertTrue(f)

    def test_39_keystore_file_fails(self):
        f = self._scan({"app/keystore.jks": "binary"})
        self.assertTrue(f)

    def test_40_aws_key_fails(self):
        # built dynamically so this test file does not itself contain the marker
        f = self._scan({"c.txt": "key = " + "AKIA" + "IOSFODNN" + "7EXAMPLE"})
        self.assertTrue(f)

    def test_41_github_token_fails(self):
        f = self._scan({"t.txt": "ghp_" + "a" * 36})
        self.assertTrue(f)

    def test_42_marker_string_in_tool_source_not_flagged(self):
        # the validator's own literal marker (mid-line) must not false-positive
        src = 'SECRET_MARKERS = [b"-----BEGIN PRIVATE KEY-----"]\n'
        self.assertEqual(self._scan({"tools/x.py": src}), [])


class MatrixGateTests(unittest.TestCase):
    """Mutations against the B-021 matrix + MSC stage registry (MSC-038)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in (MATRIX, INV_REG, MSC_STATE, CANONICAL, EVIDENCE_REG):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)
        # evidence refs are validated for existence — copy every referenced
        # repo path so the unmutated fixture is a PASS control
        for rel in self._evidence_paths():
            src = REPO_ROOT / rel
            if src.is_file():
                dst = self.root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)

    def _evidence_paths(self):
        refs = set()
        for rel in (MATRIX, MSC_STATE):
            for row in _load_jsonl(REPO_ROOT / rel):
                refs.update(row.get("evidence_refs") or [])
                for s in (row.get("stages") or {}).values():
                    refs.update(s.get("evidence_refs") or [])
        out = set()
        for r in refs:
            if not isinstance(r, str):
                continue
            if r.startswith(("git:", "ANOX-", "SEC-", "MSC-", "ROOT-", "AC-", "INV-", "PHYSICAL")):
                continue
            out.add(r.split("#", 1)[0])
        return out

    def tearDown(self):
        self.tmp.cleanup()

    def _check(self):
        errs = []
        rows = mx.check_matrix(str(self.root), errs)
        mx.check_msc_state(str(self.root), errs)
        return rows, errs

    def _rows(self):
        return _load_jsonl(self.root / MATRIX)

    def _write_rows(self, rows):
        _write_jsonl(self.root / MATRIX, rows)

    def _msc(self):
        return _load_jsonl(self.root / MSC_STATE)

    def _write_msc(self, recs):
        _write_jsonl(self.root / MSC_STATE, recs)

    def test_43_control_matrix_passes(self):
        rows, errs = self._check()
        self.assertEqual(errs, [], str(errs))

    def test_44_pass_without_evidence_fails(self):
        rows = self._rows()
        for r in rows:
            if r["current_result"] == "NOT_RUN":
                r["current_result"] = "PASS"
                r["evidence_state"] = "AUTOMATED_VERIFIED"
                r["evidence_refs"] = []
                break
        self._write_rows(rows)
        _, errs = self._check()
        self.assertTrue(any("PASS without evidence" in e for e in errs), str(errs))

    def test_45_pass_with_spec_only_evidence_state_fails(self):
        rows = self._rows()
        for r in rows:
            if r["current_result"] == "NOT_RUN":
                r["current_result"] = "PASS"
                r["evidence_state"] = "SPEC_ONLY"
                r["evidence_refs"] = ["docs/security/remediation/README.md"]
                break
        self._write_rows(rows)
        _, errs = self._check()
        self.assertTrue(any("evidence_state" in e for e in errs), str(errs))

    def _all_pre_product_verified(self):
        rows = self._rows()
        for r in rows:
            if r["pre_product_required"]:
                r["current_result"] = "PASS"
                r["evidence_state"] = "AUTOMATED_VERIFIED"
                r["evidence_refs"] = ["docs/security/remediation/README.md"]
        self.assertEqual(mx.evaluate_closure(rows), [], "fixture control must have zero blockers")
        return rows

    def test_46_failed_row_accepted_fails_closure(self):
        rows = self._all_pre_product_verified()
        victim = next(r for r in rows if r["pre_product_required"])
        victim["current_result"] = "FAIL"
        blockers = mx.evaluate_closure(rows)
        self.assertEqual([b[0] for b in blockers], [victim["test_id"]], str(blockers))
        self.assertIn("FAIL", blockers[0][1])

    def test_47_not_run_pre_product_row_fails_closure(self):
        rows = self._all_pre_product_verified()
        victim = next(r for r in rows if r["pre_product_required"])
        victim["current_result"] = "NOT_RUN"
        victim["evidence_state"] = "SPEC_ONLY"
        victim["evidence_refs"] = []
        blockers = mx.evaluate_closure(rows)
        self.assertEqual([b[0] for b in blockers], [victim["test_id"]], str(blockers))
        self.assertIn("NOT_RUN", blockers[0][1])

    def test_48_physical_row_marked_pass_fails(self):
        rows = self._rows()
        for r in rows:
            if r["execution_class"] == "PHYSICAL_GRAPHENEOS":
                r["current_result"] = "PASS"
                r["evidence_state"] = "VERIFIED"
                r["evidence_refs"] = ["ANOX-TEST-FAKE"]
                break
        self._write_rows(rows)
        _, errs = self._check()
        self.assertTrue(any("physical-device" in e for e in errs), str(errs))

    def test_49_duplicate_test_id_fails(self):
        rows = self._rows()
        rows.append(dict(rows[0]))
        self._write_rows(rows)
        _, errs = self._check()
        self.assertTrue(any("duplicate" in e for e in errs), str(errs))

    def test_50_msc_closed_without_stages_fails(self):
        recs = self._msc()
        for rec in recs:
            if rec["msc_unit"] == "MSC-UNIT-001":
                rec["stages"] = {"CLOSED": {"result": "PASS", "evidence_refs": ["x"]}}
        self._write_msc(recs)
        _, errs = self._check()
        self.assertTrue(any("CLOSED without stage" in e for e in errs), str(errs))

    def test_51_msc_implemented_to_closed_jump_fails(self):
        recs = self._msc()
        for rec in recs:
            if rec["msc_unit"] == "MSC-UNIT-001":
                rec["stages"]["RUNTIME_TESTED"] = {"result": "PENDING"}
                rec["stages"]["INDEPENDENTLY_RETESTED"] = {"result": "PASS", "evidence_refs": ["docs/security/remediation/README.md"]}
        self._write_msc(recs)
        _, errs = self._check()
        self.assertTrue(any("earlier stage" in e for e in errs), str(errs))

    def test_52_runtime_tested_without_provenance_ref_fails(self):
        recs = self._msc()
        for rec in recs:
            if rec["msc_unit"] == "MSC-UNIT-001":
                rec["stages"]["RUNTIME_TESTED"] = {
                    "result": "PASS",
                    "evidence_refs": ["docs/security/remediation/README.md"],
                }
        self._write_msc(recs)
        _, errs = self._check()
        self.assertTrue(any("FCP-1" in e or "provenance" in e for e in errs), str(errs))

    def test_53_retest_by_implementing_session_fails(self):
        recs = self._msc()
        for rec in recs:
            if rec["msc_unit"] == "MSC-UNIT-001":
                rec["stages"]["INDEPENDENTLY_RETESTED"] = {
                    "result": "PASS",
                    "evidence_refs": ["docs/security/remediation/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME.md"],
                    "recorded_by": rec["implementing_session"],
                }
        self._write_msc(recs)
        _, errs = self._check()
        self.assertTrue(any("retest stage recorded by implementing session" in e for e in errs), str(errs))

    def test_54_illegal_result_value_fails(self):
        rows = self._rows()
        rows[0]["current_result"] = "GREEN"
        self._write_rows(rows)
        _, errs = self._check()
        self.assertTrue(any("illegal current_result" in e for e in errs), str(errs))

    def test_55_unknown_verifies_ref_fails(self):
        rows = self._rows()
        rows[0]["verifies"] = ["INV-99"]
        self._write_rows(rows)
        _, errs = self._check()
        self.assertTrue(any("unknown invariant" in e or "illegal verifies" in e for e in errs), str(errs))

    def test_56_missing_msc_state_fails(self):
        (self.root / MSC_STATE).unlink()
        _, errs = self._check()
        self.assertTrue(any("msc_state" in e.lower() or "MSC" in e for e in errs), str(errs))

    # ---- R-001: the S1 overlay is not the MSC universe
    def test_56a_empty_msc_state_registry_fails(self):
        self._write_msc([])
        _, errs = self._check()
        self.assertTrue(any("msc_state registry is EMPTY" in e for e in errs), str(errs))

    def test_56b_incomplete_universe_presented_as_global_closure_fails(self):
        # all four overlay units forced to CLOSED=PASS-shaped records: still 38 OPEN
        # canonical units and the CLOSED records themselves are rejected
        recs = self._msc()
        for rec in recs:
            for s in rec["stages"].values():
                if s["result"] == "PENDING":
                    s.update({"result": "PASS", "evidence_refs": ["ANOX-EV-FAKE-0001"],
                              "recorded_by": "SOMEONE", "recorded_at": "2026-09-24"})
        self._write_msc(recs)
        _, errs = self._check()
        self.assertTrue(any("ANOX-EV-FAKE-0001 does not resolve" in e for e in errs), str(errs))
        open_units, _ = mx.load_canonical_universe(str(self.root), [])
        msc_open, msc_closed = mx.msc_global_state(open_units, recs)
        self.assertEqual(len(msc_open) + len(msc_closed), 42)
        self.assertGreaterEqual(len(msc_open), 38)

    def test_56c_unknown_unit_fails(self):
        recs = self._msc()
        extra = dict(recs[0]); extra["msc_unit"] = "MSC-UNIT-077"
        self._write_msc(recs + [extra])
        _, errs = self._check()
        self.assertTrue(any("MSC-UNIT-077: unknown MSC unit" in e for e in errs), str(errs))

    def test_56d_duplicate_unit_fails(self):
        recs = self._msc()
        self._write_msc(recs + [dict(recs[0])])
        _, errs = self._check()
        self.assertTrue(any("MSC-UNIT-001: duplicate msc_state record" in e for e in errs), str(errs))

    def test_56e_four_pending_units_global_closure_fails(self):
        r = subprocess.run([sys.executable, str(REPO_ROOT / "tools/audit/validate_b021_verification_matrix.py"),
                            "--check", "closure", "--repo-root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("MSC OPEN = 42   MSC CLOSED = 0", r.stdout)
        self.assertIn("global closure NOT PERMITTED: MSC OPEN = 42", r.stdout)

    def test_56f_zero_state_records_global_closure_fails(self):
        self._write_msc([])
        r = subprocess.run([sys.executable, str(REPO_ROOT / "tools/audit/validate_b021_verification_matrix.py"),
                            "--check", "closure", "--repo-root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("zero MSC state records", r.stdout)

    def test_56g_bare_identifier_prefix_is_not_evidence(self):
        rows = self._rows()
        for r in rows:
            if r["current_result"] == "NOT_RUN":
                r.update({"current_result": "PASS", "evidence_state": "AUTOMATED_VERIFIED",
                          "evidence_refs": ["ANOX-CI-RUN-123456", "SEC-EVIDENCE-9"]})
                break
        self._write_rows(rows)
        _, errs = self._check()
        self.assertTrue(any("PASS evidence ref does not resolve: ANOX-CI-RUN-123456" in e for e in errs), str(errs))
        self.assertTrue(any("PASS evidence ref does not resolve: SEC-EVIDENCE-9" in e for e in errs), str(errs))


class StaticGateTests(unittest.TestCase):
    """Mutations against the S1 repository-surface static gate."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in STATIC_FIXTURE:
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)

    def tearDown(self):
        self.tmp.cleanup()

    def _check(self):
        # fixture has no git; the F2 git-context tests use real repositories
        return s1.check_static(str(self.root), git_scope_check=False)

    def test_57_control_fixture_passes(self):
        errs = self._check()
        self.assertEqual(errs, [], str(errs))

    def test_58_committed_so_injected_fails(self):
        d = self.root / "android/src/main/jniLibs/arm64-v8a"
        d.mkdir(parents=True)
        (d / "libanox_crypto.so").write_bytes(ARM64_SO)
        errs = self._check()
        self.assertTrue(any("committed .so bypass" in e for e in errs), str(errs))

    def test_59_unpinned_toolchain_fails(self):
        (self.root / TOOLCHAIN).write_text(
            '[toolchain]\nchannel = "stable"\n'
            'targets = ["aarch64-linux-android", "x86_64-linux-android"]\n')
        errs = self._check()
        self.assertTrue(any("not an exact version pin" in e for e in errs), str(errs))

    def test_60_gradle_bypasses_produced_output_fails(self):
        g = (self.root / GRADLE).read_text()
        g = g.replace('$rootDir/build/native/jniLibs', '"src/main/jniLibs"')
        (self.root / GRADLE).write_text(g)
        errs = self._check()
        self.assertTrue(any("jniLibs" in e for e in errs), str(errs))

    def test_61_gradle_keep_debug_symbols_removed_fails(self):
        g = (self.root / GRADLE).read_text()
        g = g.replace('keepDebugSymbols += "**/*.so"', "")
        (self.root / GRADLE).write_text(g)
        errs = self._check()
        self.assertTrue(any("keepDebugSymbols" in e for e in errs), str(errs))

    def test_62_gitignore_bypass_fails(self):
        gi = (self.root / ".gitignore").read_text()
        gi = gi.replace("android/src/main/jniLibs/", "")
        (self.root / ".gitignore").write_text(gi)
        errs = self._check()
        self.assertTrue(any(".gitignore" in e for e in errs), str(errs))

    def test_63_policy_doc_reverted_fails(self):
        (self.root / POLICY).write_text("# policy\nNative .so libraries are committed.\n")
        errs = self._check()
        self.assertTrue(any("policy" in e.lower() or "POLICY" in e or "provenance" in e for e in errs), str(errs))

    def test_64_verify_guard_removed_fails(self):
        g = (self.root / GRADLE).read_text().replace("verifyNativeArtifacts", "xGuard")
        (self.root / GRADLE).write_text(g)
        errs = self._check()
        self.assertTrue(any("verifyNativeArtifacts" in e for e in errs), str(errs))

    def test_65_abi_filter_removed_fails(self):
        g = (self.root / GRADLE).read_text().replace('"x86_64"', '"arm64-v8a"', 1)
        # remove the abiFilters line entirely instead
        g2 = re.sub(r"abiFilters\.addAll\([^\n]+\n", "", g)
        (self.root / GRADLE).write_text(g2)
        errs = self._check()
        self.assertTrue(errs)

    # ---- R-004: Gradle guard must be the canonical fail-closed verifier
    def test_66_gradle_guard_downgraded_to_existence_check_fails(self):
        g = (self.root / GRADLE).read_text().replace("tasks.registering(Exec::class)", "tasks.registering")
        (self.root / GRADLE).write_text(g)
        errs = self._check()
        self.assertTrue(any("not an Exec of the canonical verifier" in e for e in errs), str(errs))

    def test_67_gradle_guard_verify_command_removed_fails(self):
        g = (self.root / GRADLE).read_text().replace('nativeVerifier.path, "verify"', 'nativeVerifier.path, "symbols"')
        (self.root / GRADLE).write_text(g)
        errs = self._check()
        self.assertTrue(any("does not invoke native_build.py verify" in e for e in errs), str(errs))

    def test_68_gradle_guard_exit_ignored_or_cached_fails(self):
        g = (self.root / GRADLE).read_text()
        (self.root / GRADLE).write_text(g.replace("isIgnoreExitValue = false", "isIgnoreExitValue = true"))
        errs = self._check()
        self.assertTrue(any("exit status may be ignored" in e for e in errs), str(errs))
        (self.root / GRADLE).write_text(g.replace("outputs.upToDateWhen { false }", ""))
        errs = self._check()
        self.assertTrue(any("may be cached" in e for e in errs), str(errs))

    def test_69_gradle_package_dependency_removed_fails(self):
        g = (self.root / GRADLE).read_text().replace("dependsOn(verifyNativeArtifacts)", "// no-op")
        (self.root / GRADLE).write_text(g)
        errs = self._check()
        self.assertTrue(any("do not dependsOn(verifyNativeArtifacts)" in e for e in errs), str(errs))

    def test_70_gradle_merge_task_class_ungated_fails(self):
        g = (self.root / GRADLE).read_text().replace("merge.*NativeLibs|", "")
        (self.root / GRADLE).write_text(g)
        errs = self._check()
        self.assertTrue(any("'merge.*NativeLibs' not gated" in e for e in errs), str(errs))

    def test_71_gradle_jnilibs_srcdir_fallback_fails(self):
        g = (self.root / GRADLE).read_text().replace(
            'setSrcDirs(listOf("$rootDir/build/native/jniLibs"))', 'srcDir("$rootDir/build/native/jniLibs")')
        (self.root / GRADLE).write_text(g)
        errs = self._check()
        self.assertTrue(any("setSrcDirs (exclusive)" in e for e in errs), str(errs))


class GradlePackagingGuardBehaviorTests(unittest.TestCase):
    """R-004 behavioral proof of the packaging boundary WITHOUT a JVM.

    ``verifyNativeArtifacts`` is an Exec of exactly
    ``python3 tools/security/native_build.py verify --repo-root R --out-dir O --manifest M``
    with ``isIgnoreExitValue = false``. These tests run that exact command
    line against a real Git fixture for each reviewer scenario and require a
    non-zero exit — i.e. the Gradle task would throw before any package*/merge*
    task consumes native input. Full Gradle execution remains
    LOCAL_ANDROID_VALIDATION_BLOCKED_NO_JDK17 where no JDK 17 is installed.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        for rel in NATIVE_SRC_FIXTURE + [GRADLE, "tools/security/native_build.py"]:
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, dst)
        (self.root / ".gitignore").write_text("build/\n")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "fixture"],
                       cwd=self.root, check=True)
        self.out_dir = self.root / "build/native/jniLibs"
        self.mpath = self.root / "build/native/native-manifest.json"
        for abi, so in (("arm64-v8a", ARM64_SO), ("x86_64", X86_SO)):
            (self.out_dir / abi).mkdir(parents=True)
            (self.out_dir / abi / "libanox_crypto.so").write_bytes(so)
        m, errs = nb.write_manifest(str(self.root), self.out_dir, self.mpath, ndk=None)
        self.assertEqual(errs, [], str(errs))
        same = {"artifacts": [{"abi": a["abi"], "sha256": a["sha256"]} for a in m["artifacts"]]}
        self.assertEqual(nb.attest_reproducibility(str(self.mpath), same, same, ["r1", "r2"]), [])

    def tearDown(self):
        self.tmp.cleanup()

    def _gradle_exec(self):
        """The exact command line the Gradle Exec task issues (see build.gradle.kts)."""
        g = (REPO_ROOT / GRADLE).read_text()
        self.assertIn('commandLine(\n        "python3", nativeVerifier.path, "verify",\n'
                      '        "--repo-root", rootDir.path,\n        "--out-dir", nativeArtifactsDir.path,\n'
                      '        "--manifest", nativeManifestFile.path,\n    )', g)
        return subprocess.run([sys.executable, str(self.root / "tools/security/native_build.py"), "verify",
                               "--repo-root", str(self.root), "--out-dir", str(self.out_dir),
                               "--manifest", str(self.mpath)], cwd=self.root, capture_output=True, text=True)

    def _rebind(self, abi, data):
        (self.out_dir / abi / "libanox_crypto.so").write_bytes(data)
        m = json.loads(self.mpath.read_text())
        for a in m["artifacts"]:
            if a["abi"] == abi:
                a["sha256"], a["size"] = _sha(data), len(data)
        m["build"]["reproducibility"]["per_abi_sha256"][abi] = _sha(data)
        self.mpath.write_text(json.dumps(m))

    def test_g0_control_verified_artifacts_pass(self):
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ACTUAL-binary JNI surface", r.stdout)

    def test_g1_no_manifest_fails(self):
        self.mpath.unlink()
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("manifest missing", r.stdout)

    def test_g2_placeholder_so_fails(self):
        # the reviewer's exact scenario: two non-ELF placeholders (hashes rebound)
        self._rebind("arm64-v8a", b"placeholder\n")
        self._rebind("x86_64", b"placeholder\n")
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("not a verifiable ELF64 shared object", r.stdout)

    def test_g2b_placeholders_without_manifest_fail(self):
        self._rebind("arm64-v8a", b"placeholder\n")
        self._rebind("x86_64", b"placeholder\n")
        self.mpath.unlink()
        self.assertEqual(self._gradle_exec().returncode, 1)

    def test_g3_wrong_hash_fails(self):
        (self.out_dir / "x86_64/libanox_crypto.so").write_bytes(X86_SO + b"\x00tamper")
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("sha256 mismatch", r.stdout)

    def test_g4_extra_native_input_fails(self):
        d = self.root / "android/src/main/jniLibs/arm64-v8a"; d.mkdir(parents=True)
        (d / "libanox_crypto.so").write_bytes(ARM64_SO)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "stale"],
                       cwd=self.root, check=True)
        m = json.loads(self.mpath.read_text())
        m["source"]["repo_sha"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True,
                                                 text=True).stdout.strip()
        self.mpath.write_text(json.dumps(m))
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("uncontrolled alternative native input present: android/src/main/jniLibs/arm64-v8a/libanox_crypto.so",
                      r.stdout)

    def test_g4b_extra_unmanifested_so_in_produced_dir_fails(self):
        (self.out_dir / "arm64-v8a/libextra.so").write_bytes(ARM64_SO)
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("not in manifest", r.stdout)

    def test_g5_missing_abi_fails(self):
        shutil.rmtree(self.out_dir / "x86_64")
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("manifest artifact missing on disk: x86_64/libanox_crypto.so", r.stdout)

    def test_g6_wrong_elf_architecture_fails(self):
        self._rebind("arm64-v8a", _fake_elf(62, payload=b"x86 under arm64"))
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("ELF e_machine 62 does not match ABI arm64-v8a", r.stdout)

    def test_g7_jni_export_removed_fails(self):
        self._rebind("x86_64", _fake_elf(62, EXPECTED_JNI[:-1], b"x86_64-payload"))
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("ACTUAL binary JNI exports differ", r.stdout)

    def test_g8_reproducibility_absent_fails(self):
        m = json.loads(self.mpath.read_text()); m["build"]["reproducible_build_confirmed"] = False
        self.mpath.write_text(json.dumps(m))
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("reproducible_build_confirmed is not True", r.stdout)

    def test_g9_dirty_tree_fails(self):
        (self.root / "crypto/rust/src/lib.rs").write_text("// edited after build\n")
        r = self._gradle_exec()
        self.assertEqual(r.returncode, 1)
        self.assertIn("working tree is dirty", r.stdout)


if __name__ == "__main__":
    unittest.main()
