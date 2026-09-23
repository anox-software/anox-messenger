#!/usr/bin/env python3
"""Adversarial fail-closed tests for the S1 build-provenance gate stack.

REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001 — every negative mutation below
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

CI = ".github/workflows/ci.yml"
GRADLE = "android/build.gradle.kts"
TOOLCHAIN = "crypto/rust/rust-toolchain.toml"
POLICY = "docs/current/REPOSITORY_SECURITY_POLICY.md"
MSC_STATE = "docs/security/remediation/msc_state.jsonl"
MATRIX = "docs/workforce/registries/b021_verification_matrix.jsonl"
INV_REG = "docs/workforce/registries/security_invariant_traceability.jsonl"

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


def _fake_elf(e_machine):
    """Minimal ELF64-LE header carrying the given e_machine value."""
    b = bytearray(64)
    b[0:4] = b"\x7fELF"
    b[4] = 2  # ELFCLASS64
    b[5] = 1  # little-endian
    struct.pack_into("<H", b, 18, e_machine)
    return bytes(b)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


ARM64_SO = _fake_elf(183) + b"arm64-payload"
X86_SO = _fake_elf(62) + b"x86_64-payload"


def _manifest(arm64_sha=None, x86_sha=None, repo_sha="0" * 40):
    return {
        "schema_version": "anox-native-manifest-v1",
        "source": {"repo_sha": repo_sha, "cargo_lock_sha256": "0" * 64, "working_tree": "clean"},
        "toolchain": {
            "channel": "1.97.1", "ndk_revision": "26.2.11394342",
            "cargo_ndk": "4.1.2", "rustc": "rustc 1.97.1",
        },
        "build": _repro_build(arm64_sha or _sha(ARM64_SO), x86_sha or _sha(X86_SO)),
        "abis": ["arm64-v8a", "x86_64"],
        "artifacts": [
            {"abi": "arm64-v8a", "file": "arm64-v8a/libanox_crypto.so",
             "sha256": arm64_sha or _sha(ARM64_SO), "size": len(ARM64_SO)},
            {"abi": "x86_64", "file": "x86_64/libanox_crypto.so",
             "sha256": x86_sha or _sha(X86_SO), "size": len(X86_SO)},
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

    def _rc(self, manifest="__default__"):
        m = str(self.mpath) if manifest == "__default__" else manifest
        self.out = io.StringIO()
        with redirect_stdout(self.out):
            rc = apk_v.validate_apk(str(self.apk), manifest_path=m)
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
        m = {
            "schema_version": "anox-native-manifest-v1",
            "source": {"repo_sha": "0" * 40, "cargo_lock_sha256": lock_sha, "working_tree": "clean"},
            "toolchain": {
                "channel": channel, "ndk_revision": "26.2.11394342",
                "cargo_ndk": "4.1.2", "rustc": "rustc 1.97.1",
            },
            "build": _repro_build(_sha(ARM64_SO), _sha(X86_SO)),
            "abis": ["arm64-v8a", "x86_64"],
            "artifacts": [
                {"abi": "arm64-v8a", "file": "arm64-v8a/libanox_crypto.so",
                 "sha256": _sha(ARM64_SO), "size": len(ARM64_SO),
                 "rust_target": "aarch64-linux-android",
                 "jni_exports_sha256": fp, "jni_export_count": count},
                {"abi": "x86_64", "file": "x86_64/libanox_crypto.so",
                 "sha256": _sha(X86_SO), "size": len(X86_SO),
                 "rust_target": "x86_64-linux-android",
                 "jni_exports_sha256": fp, "jni_export_count": count},
            ],
        }
        m.update(over)
        self.mpath.write_text(json.dumps(m))
        return m

    def _verify(self, expected_source_sha=None):
        return nb.verify_manifest(
            str(self.root), str(self.mpath), str(self.prod),
            expected_source_sha=expected_source_sha,
            require_clean_live_tree=False,  # fixture has no git; F7 live-tree tests use real repos
        )

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
        errs = []
        expected = nb.expected_jni_exports(str(self.root), errs)
        self.assertFalse(errs)
        missing = sorted(expected)[0]
        # simulate the parity check against a symbol table missing one export
        fake_syms = set(expected) - {missing}
        orig = nb.dynamic_symbols
        try:
            nb.dynamic_symbols = lambda *a, **k: fake_syms
            perrs = []
            nb.check_symbol_parity("fake.so", expected, perrs)
            self.assertTrue(any("missing expected JNI" in e for e in perrs), str(perrs))
        finally:
            nb.dynamic_symbols = orig

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
        for rel in (MATRIX, INV_REG, MSC_STATE):
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
                    "recorded_by": "REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001",
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


if __name__ == "__main__":
    unittest.main()
