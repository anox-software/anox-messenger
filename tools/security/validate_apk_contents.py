#!/usr/bin/env python3
"""Validate an Android APK for forbidden repository/governance and secret artifacts.

Uses only Python 3 standard library. Reads the APK as a ZIP archive.
Never prints discovered secret values.
"""

import argparse
import hashlib
import os
import re
import sys
import zipfile
from pathlib import Path

FORBIDDEN_PATH_PATTERNS = [
    r"^docs/authority/",
    r"^docs/continuity/",
    r"^docs/history/",
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
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
]

# Text-like extensions we will scan for secret markers.
TEXT_SUFFIXES = (
    ".xml",
    ".json",
    ".txt",
    ".md",
    ".properties",
    ".kt",
    ".java",
    ".rs",
    ".kts",
    ".gradle",
    ".yml",
    ".yaml",
    ".pro",
    ".mf",
)

# Maximum size for in-memory text scan (1 MiB).
MAX_TEXT_SCAN_BYTES = 1 * 1024 * 1024


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_text_like(name):
    name_lower = name.lower()
    return any(name_lower.endswith(s) for s in TEXT_SUFFIXES) or name_lower == "androidmanifest.xml"


def validate_apk(apk_path):
    apk_path = Path(apk_path)
    if not apk_path.exists():
        print(f"ERROR: APK not found: {apk_path}")
        return 1

    print("=" * 60)
    print("anoX APK Content / Secret Leakage Validation")
    print("=" * 60)
    print(f"APK path:  {apk_path}")
    print(f"APK SHA-256: {sha256_file(apk_path)}")

    forbidden_findings = []
    secret_findings = []

    classes_dex_count = 0
    native_libs = []
    asset_count = 0
    has_manifest = False
    has_resources = False

    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            all_members = zf.namelist()
            print(f"Member count: {len(all_members)}")

            for m in all_members:
                # inventory
                if re.match(r"^classes\d*\.dex$", os.path.basename(m)):
                    classes_dex_count += 1
                if m.startswith("lib/") and m.endswith(".so"):
                    native_libs.append(m)
                if m.startswith("assets/") and not m.endswith("/"):
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

                # secret marker scan on text-like members (bounded size)
                if is_text_like(m):
                    try:
                        info = zf.getinfo(m)
                        if info.file_size <= MAX_TEXT_SCAN_BYTES:
                            data = zf.read(m)
                            for marker in SECRET_MARKERS:
                                if marker in data:
                                    secret_findings.append((m, marker.decode("utf-8")))
                                    break
                    except (zipfile.BadZipFile, RuntimeError):
                        pass

    except zipfile.BadZipFile as e:
        print(f"ERROR: not a valid APK/ZIP: {e}")
        return 1

    print(f"classes*.dex count: {classes_dex_count}")
    print(f"Native libraries ({len(native_libs)}):")
    for lib in native_libs[:20]:
        print(f"  - {lib}")
    if len(native_libs) > 20:
        print(f"  ... and {len(native_libs) - 20} more")
    print(f"Assets count: {asset_count}")
    print(f"Resources present: {'YES' if has_resources else 'NO'}")
    print(f"Manifest present: {'YES' if has_manifest else 'NO'}")
    print(f"Forbidden member findings: {len(forbidden_findings)}")
    print(f"Secret-marker findings: {len(secret_findings)}")

    if forbidden_findings:
        print("\n--- Forbidden item findings ---")
        for m, rule in forbidden_findings:
            print(f"  {m}  (rule: {rule})")

    if secret_findings:
        print("\n--- Secret-marker findings ---")
        for m, rule in secret_findings:
            # rule is the marker string; we do not print its value, just the rule name.
            print(f"  {m}  (rule: {rule})")

    print("\n" + "=" * 60)
    if forbidden_findings or secret_findings:
        print("RESULT: FAIL — APK content validation failed")
        return 1

    print("RESULT: PASS — APK content validation passed")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate an anox Android APK for forbidden content and obvious secret leakage.")
    parser.add_argument("apk_path", help="Path to the APK file to validate")
    args = parser.parse_args()
    return validate_apk(args.apk_path)


if __name__ == "__main__":
    sys.exit(main())
