#!/usr/bin/env python3
"""Validate an Android APK for forbidden repository/governance artifacts,
secret leakage, and native-artifact provenance (VALIDATOR V2).

REMEDIATION_SESSION_S1 / MSC-UNIT-001 + AC-012:

  * every packaged ``lib/<abi>/*.so`` is bound by SHA-256 to the authoritative
    native artifact manifest produced by tools/security/native_build.py;
  * the packaged ABI set must equal exactly the required set (no missing ABI,
    no extra unreviewed ABI);
  * each packaged .so's ELF machine must match its claimed ABI directory;
  * every APK member (binary or text) is scanned for private-key/secret
    markers — not just text-like files;
  * all pre-existing forbidden-path checks are preserved.

Fail-closed: any mismatch, missing artifact, unexpected library, marker hit or
malformed manifest exits 1.  No string-presence heuristic counts as provenance.

Uses only Python 3 standard library. Reads the APK as a ZIP archive.
Never prints discovered secret values.
"""

import argparse
import hashlib
import json
import os
import re
import struct
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_PATH_PATTERNS = [
    r"^docs/authority/",
    r"^docs/continuity/",
    r"^docs/history/",
    r"^docs/security/",
    r"^docs/workforce/",
    r"^PROJECT_STATE\.md$",
    r"^FORTSCHRITT\.md$",
    r"^DEVIN_PROMPT_OUTPUT_ARCHIV\.md$",
    r"^MAIN_PLAN_DE\.md$",
    r"^ANOX_HANDOFF_",
    r"^GIT_SNAPSHOT\.txt$",
    r"^CURRENT_HANDOFF\.md$",
    r"^CURRENT_GIT_STATE\.md$",
    r"^CURRENT_STATE\.json$",
    r"^CURRENT_NEXT_DEVIN_TASK\.md$",
    r"^CURRENT_IMPLEMENTATION_STATE\.md$",
    r"^CURRENT_OPEN_WORK\.md$",
    r"^\.git/",
    r"(^|/)\.env$",
    r"(^|/)\.env\.",
    r"^local\.properties$",
    r"\.jks$",
    r"\.keystore$",
    r"\.p12$",
    r"\.pfx$",
    r"\.pem$",
    r"\.key$",
]

SECRET_MARKERS = [
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN DSA PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN ENCRYPTED PRIVATE KEY-----",
    b"-----BEGIN PGP PRIVATE KEY BLOCK-----",
]

# Required frozen ABI set for V1 (Master/Coverage Gate ownership).
REQUIRED_ABIS = {"arm64-v8a", "x86_64"}
EXPECTED_LIB_NAME = "libanox_crypto.so"
MANIFEST_SCHEMA = "anox-native-manifest-v1"

# ELF e_machine values for the required ABIs.
ELF_MACHINE = {
    "arm64-v8a": 183,   # EM_AARCH64
    "x86_64": 62,       # EM_X86_64
}

# Maximum size for in-memory member scans (64 MiB covers any legitimate APK member).
# F6: members above this bound are NOT skipped — they fail closed as unscannable.
MAX_SCAN_BYTES = 64 * 1024 * 1024
# DoS bounds (F6): total uncompressed payload and per-member compression ratio.
MAX_TOTAL_UNCOMPRESSED = 1024 * 1024 * 1024
MAX_MEMBERS = 50000
BOMB_RATIO = 1000
BOMB_MIN_BYTES = 1024 * 1024

_CANONICAL_SEGMENT = re.compile(r"^[A-Za-z0-9._~!$&'()*+,;=@\[\]{}^ -]+$")


def canonical_member_path(name):
    """Return (is_canonical, reason) for a ZIP member name (F1).

    A canonical path is exactly what the Android packager emits: relative,
    forward-slash separated, no empty / '.' / '..' segments, no leading './'
    or '/', no backslashes, no NUL, no control characters. Anything else can
    be used to hide a native library from a prefix-based inventory and is
    rejected outright rather than normalized.
    """
    if not name:
        return False, "empty member name"
    if "\x00" in name:
        return False, "NUL in member name"
    if "\\" in name:
        return False, "backslash in member name"
    if name.startswith("/"):
        return False, "absolute member path"
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        return False, "control character in member name"
    is_dir = name.endswith("/")
    segs = name[:-1].split("/") if is_dir else name.split("/")
    for s in segs:
        if s == "":
            return False, "empty path segment (leading '/' or '//')"
        if s in (".", ".."):
            return False, f"non-canonical segment {s!r}"
    return True, ""


def is_native_library_member(name):
    """True for any member that could be interpreted as a native library
    under ANY spelling of lib/<abi>/*.so (case-insensitive), so that no
    variant can hide from the provenance inventory."""
    low = name.lower()
    return (low.endswith(".so") or ".so." in low.rsplit("/", 1)[-1]) or low.startswith("lib/")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def elf_machine(data):
    """Return (ei_class, e_machine) for an ELF blob, else (None, None)."""
    if len(data) < 20 or data[:4] != b"\x7fELF":
        return None, None
    ei_class = data[4]
    endian = "<" if data[5] == 1 else ">"
    (e_machine,) = struct.unpack_from(endian + "H", data, 18)
    return ei_class, e_machine


def load_manifest(path):
    """Load and minimally schema-check the native artifact manifest."""
    errors = []
    p = Path(path)
    if not p.exists():
        return None, [f"native manifest not found: {p}"]
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, [f"native manifest is not valid JSON: {e}"]
    if m.get("schema_version") != MANIFEST_SCHEMA:
        errors.append(f"manifest schema_version != {MANIFEST_SCHEMA}")
    src = m.get("source") or {}
    if not re.fullmatch(r"[0-9a-f]{40}", str(src.get("repo_sha") or "")):
        errors.append("manifest source.repo_sha is not a 40-hex SHA")
    # F7: a manifest may only claim an unqualified clean source SHA if the
    # producing tree was clean; anything else is rejected here as well.
    if src.get("working_tree") != "clean":
        errors.append(
            f"manifest source.working_tree={src.get('working_tree')!r}; provenance from a "
            "non-clean tree cannot bind an APK"
        )
    tc = m.get("toolchain") or {}
    for k in ("channel", "ndk_revision", "cargo_ndk", "rustc"):
        if not tc.get(k):
            errors.append(f"manifest toolchain.{k} missing")
    # F5: reproducibility is an authoritative, verified attestation — not a
    # decorative field. It must be exactly True (set only by rebuild-compare).
    build = m.get("build") or {}
    if build.get("reproducible_build_confirmed") is not True:
        errors.append(
            "manifest build.reproducible_build_confirmed is not True — artifacts have not "
            "passed the two-clean-build reproducibility attestation"
        )
    arts = m.get("artifacts") or []
    if not arts:
        errors.append("manifest has no artifacts")
    abis = set()
    for a in arts:
        abi = a.get("abi")
        f = a.get("file") or ""
        if not abi or not f:
            errors.append("manifest artifact missing abi/file")
            continue
        if f != f"{abi}/{EXPECTED_LIB_NAME}":
            errors.append(f"manifest artifact path unexpected: {f!r}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(a.get("sha256") or "")):
            errors.append(f"manifest artifact {abi} sha256 invalid")
        abis.add(abi)
    if abis != REQUIRED_ABIS:
        errors.append(
            f"manifest ABI set {sorted(abis)} != required {sorted(REQUIRED_ABIS)}"
        )
    return m, errors


def validate_apk(apk_path, manifest_path=None):
    apk_path = Path(apk_path)
    errors = []
    if not apk_path.exists():
        print(f"ERROR: APK not found: {apk_path}")
        return 1

    print("=" * 60)
    print("anoX APK Content / Secret / Native-Provenance Validation (v2)")
    print("=" * 60)
    print(f"APK path:  {apk_path}")
    print(f"APK SHA-256: {sha256_file(apk_path)}")

    manifest = None
    if manifest_path is None:
        errors.append(
            "--native-manifest is required: an APK without provenance binding cannot pass"
        )
    else:
        manifest, merr = load_manifest(manifest_path)
        errors.extend(merr)
        print(f"Native manifest: {manifest_path}")

    forbidden_findings = []
    secret_findings = []

    classes_dex_count = 0
    native_libs = {}          # packaged .so member name -> sha256
    native_abis = set()
    asset_count = 0
    has_manifest = False
    has_resources = False

    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            infos = zf.infolist()
            all_members = [i.filename for i in infos]
            print(f"Member count: {len(all_members)}")

            # ---- F1/F6: archive-structure fail-closed checks -----------------
            if len(infos) > MAX_MEMBERS:
                errors.append(f"APK has {len(infos)} members > bound {MAX_MEMBERS}")
            total_uncompressed = sum(i.file_size for i in infos)
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                errors.append(
                    f"APK total uncompressed size {total_uncompressed} > bound {MAX_TOTAL_UNCOMPRESSED}"
                )
            # exact duplicate entries (central-directory ambiguity: verifier and
            # installer may disagree on which copy wins)
            seen_exact = set()
            for name in all_members:
                if name in seen_exact:
                    errors.append(f"duplicate ZIP entry: {name}")
                seen_exact.add(name)
            # canonical-path + collision-after-folding checks
            folded = {}
            for name in all_members:
                ok, why = canonical_member_path(name)
                if not ok:
                    errors.append(f"non-canonical ZIP member path {name!r}: {why}")
                key = name.lower()
                if key in folded and folded[key] != name:
                    errors.append(
                        f"ambiguous ZIP entries differing only by case: {folded[key]!r} vs {name!r}"
                    )
                folded.setdefault(key, name)

            for info in infos:
                m = info.filename
                is_dir = m.endswith("/")
                # F6: zip-bomb style members are rejected before any read
                if (not is_dir and info.file_size >= BOMB_MIN_BYTES and info.compress_size > 0
                        and info.file_size // info.compress_size > BOMB_RATIO):
                    errors.append(
                        f"{m}: compression ratio {info.file_size // info.compress_size}:1 exceeds bound"
                    )
                    continue

                # inventory
                if re.match(r"^classes\d*\.dex$", os.path.basename(m)):
                    classes_dex_count += 1
                # F1: any spelling that could denote a native library is
                # inventoried; only the exact canonical lib/<abi>/<name>.so form
                # is admissible, every other variant is a hard failure.
                if not is_dir and is_native_library_member(m):
                    parts = m.split("/")
                    canonical_form = (
                        m.startswith("lib/") and len(parts) == 3 and parts[2].endswith(".so")
                        and parts[1] != "" and parts[2] != ".so"
                    )
                    if not canonical_form:
                        errors.append(
                            f"native-library-like member outside canonical lib/<abi>/<name>.so form: {m!r}"
                        )
                    else:
                        if info.file_size > MAX_SCAN_BYTES:
                            errors.append(f"{m}: native library exceeds scan bound; refusing to bind")
                            continue
                        data = zf.read(m)
                        native_libs[m] = sha256_bytes(data)
                        native_abis.add(parts[1])
                if m.startswith("assets/") and not is_dir:
                    asset_count += 1
                if m == "AndroidManifest.xml" or m.lower() == "androidmanifest.xml":
                    has_manifest = True
                if m == "resources.arsc" or m.startswith("res/"):
                    has_resources = True

                # forbidden path / name checks
                for pat in FORBIDDEN_PATH_PATTERNS:
                    if re.search(pat, m, re.IGNORECASE):
                        forbidden_findings.append((m, pat))
                        break

                # secret marker scan on ALL members (binary included); F6:
                # oversize members fail closed instead of being skipped.
                if is_dir or info.file_size == 0:
                    continue
                if info.file_size > MAX_SCAN_BYTES:
                    errors.append(f"{m}: member size {info.file_size} exceeds scan bound; unscannable member is a failure")
                    continue
                try:
                    data = zf.read(m)
                except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as e:
                    errors.append(f"{m}: unreadable member ({e.__class__.__name__}); cannot be scanned")
                    continue
                for marker in SECRET_MARKERS:
                    if marker in data:
                        secret_findings.append((m, marker.decode("utf-8")))
                        break

    except zipfile.BadZipFile as e:
        print(f"ERROR: not a valid APK/ZIP: {e}")
        return 1

    print(f"classes*.dex count: {classes_dex_count}")
    print(f"Native libraries ({len(native_libs)}):")
    for lib in sorted(native_libs)[:20]:
        print(f"  - {lib}  sha256={native_libs[lib]}")
    print(f"Assets count: {asset_count}")
    print(f"Resources present: {'YES' if has_resources else 'NO'}")
    print(f"Manifest present: {'YES' if has_manifest else 'NO'}")
    print(f"Forbidden member findings: {len(forbidden_findings)}")
    print(f"Secret-marker findings: {len(secret_findings)}")

    for m, rule in forbidden_findings:
        errors.append(f"forbidden APK member: {m} (rule: {rule})")
    for m, rule in secret_findings:
        # rule is the marker name only; values are never printed.
        errors.append(f"secret marker in APK member: {m} (rule: {rule})")

    # ---- native provenance binding -------------------------------------
    if manifest is not None:
        manifest_map = {}
        for a in manifest.get("artifacts") or []:
            manifest_map[f"lib/{a.get('file')}"] = a

        # 1. ABI set must match exactly.
        if native_abis != REQUIRED_ABIS:
            errors.append(
                f"packaged ABI set {sorted(native_abis)} != required {sorted(REQUIRED_ABIS)}"
            )

        # 2. Packaged library set must equal the manifest set exactly.
        packaged = set(native_libs)
        expected_members = set(manifest_map)
        for extra in sorted(packaged - expected_members):
            errors.append(f"unexpected native library in APK (not in manifest): {extra}")
        for missing in sorted(expected_members - packaged):
            errors.append(f"missing expected native library in APK: {missing}")

        # 3. Hash binding per artifact.
        for member in sorted(packaged & expected_members):
            want = manifest_map[member].get("sha256")
            got = native_libs[member]
            if want != got:
                errors.append(
                    f"native hash mismatch {member}: manifest {want} != packaged {got}"
                )

        # 4. ELF machine must match the claimed ABI directory.
        with zipfile.ZipFile(apk_path, "r") as zf:
            for member in sorted(packaged):
                abi = member.split("/")[1]
                data = zf.read(member)
                ei_class, e_machine = elf_machine(data)
                if e_machine is None:
                    errors.append(f"{member}: not an ELF binary")
                elif abi in ELF_MACHINE and e_machine != ELF_MACHINE[abi]:
                    errors.append(
                        f"{member}: ELF machine {e_machine} does not match ABI dir {abi}"
                    )

    print("\n" + "=" * 60)
    if errors:
        print(f"RESULT: FAIL — {len(errors)} violation(s)")
        for e in errors:
            print(f"  FAIL {e}")
        return 1

    print("RESULT: PASS — APK content, secrets and native provenance verified")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate an anox Android APK: forbidden content, secret leakage, native provenance binding."
    )
    parser.add_argument("apk_path", help="Path to the APK file to validate")
    parser.add_argument(
        "--native-manifest",
        default=None,
        help="Path to native-manifest.json produced by tools/security/native_build.py (required)",
    )
    args = parser.parse_args()
    return validate_apk(args.apk_path, manifest_path=args.native_manifest)


if __name__ == "__main__":
    sys.exit(main())
