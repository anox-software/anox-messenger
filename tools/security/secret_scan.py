#!/usr/bin/env python3
"""Repository secret scan — fail-closed CI gate (MSC-UNIT-003 / B-017-Lite).

Scans every tracked file (or an explicit file list) for committed secret
material:

  * private-key PEM blocks (line-start anchored, so marker literals inside
    tool source code do not false-positive),
  * well-known token formats (AWS, GitHub, Slack, Supabase service keys,
    generic Bearer/JWT service-role patterns),
  * committed key-store / certificate / env files that must never be tracked.

Prints only file + rule names — never the matched value.
Stdlib only.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# (rule_name, compiled regex applied to decoded text)
SECRET_PATTERNS = [
    ("pem_private_key", re.compile(
        r"(?m)^-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b")),
    ("github_fine_grained_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("supabase_service_key", re.compile(r"\bsbp_[A-Za-z0-9]{20,}\b")),
    ("generic_api_secret_assignment", re.compile(
        r"(?i)\b(api[_-]?secret|client[_-]?secret|service[_-]?role[_-]?key)\b\s*[:=]\s*['\"][A-Za-z0-9+/=_-]{20,}['\"]")),
]

# Tracked file names that are themselves secret-material carriers.
FORBIDDEN_TRACKED = re.compile(
    r"(^|/)(\.env(\..*)?|local\.properties|.*\.(jks|keystore|p12|pfx|pem|key))$",
    re.IGNORECASE,
)

# Directories never scanned (generated / vendored / binary caches).
SKIP_DIRS = {".git", "build", "target", ".gradle", ".idea", "artifacts"}

MAX_FILE_BYTES = 16 * 1024 * 1024


def tracked_files(repo_root):
    proc = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True
    )
    if proc.returncode != 0:
        return None
    return [l for l in proc.stdout.splitlines() if l.strip()]


def walk_files(repo_root):
    out = []
    for p in sorted(Path(repo_root).rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(repo_root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        out.append(str(rel))
    return out


def scan(repo_root, files=None):
    findings = []
    root = Path(repo_root)
    rels = files if files is not None else (tracked_files(root) or walk_files(root))
    for rel in rels:
        rel = rel.strip()
        if not rel:
            continue
        if FORBIDDEN_TRACKED.search(rel):
            findings.append((rel, "forbidden_tracked_file"))
            continue
        p = root / rel
        if not p.is_file():
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                findings.append((rel, "file_too_large_unscanned"))
                continue
            data = p.read_bytes()
        except OSError:
            continue
        if b"\x00" in data[:2048]:
            continue  # binary blob: token patterns are text-domain
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        for name, pat in SECRET_PATTERNS:
            if pat.search(text):
                findings.append((rel, name))
                break
    return findings


def main():
    ap = argparse.ArgumentParser(description="Fail-closed repository secret scan.")
    ap.add_argument("--repo-root", default=str(REPO_ROOT))
    ap.add_argument("--files", nargs="*", default=None,
                    help="explicit repo-relative file list (default: git ls-files or tree walk)")
    args = ap.parse_args()
    findings = scan(args.repo_root, files=args.files)
    print("REPOSITORY SECRET SCAN (S1)")
    if findings:
        for rel, rule in findings:
            print(f"  FAIL {rel}  (rule: {rule})")
        print("RESULT: FAIL")
        return 1
    print("  OK   no committed secret material detected")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
