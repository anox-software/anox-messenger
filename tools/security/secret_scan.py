#!/usr/bin/env python3
"""Repository secret scan — fail-closed CI gate (MSC-UNIT-003 / B-017-Lite).

Scans every tracked file (or an explicit file list) for committed secret
material:

  * private-key PEM blocks — line-start anchored, PLUS indented/quoted headers
    that are followed by a base64 body (F6), PLUS byte-domain markers inside
    binary blobs (F6); bare marker literals inside tool source do not
    false-positive,
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

# F6: byte-domain rules applied to EVERY file, including binary blobs (a NUL
# byte no longer exempts a file). PEM markers inside binaries are always a
# finding; token formats are byte-exact.
BINARY_PATTERNS = [
    ("pem_private_key_in_binary", re.compile(
        rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----")),
    ("aws_access_key", re.compile(rb"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])")),
    ("github_token", re.compile(rb"(?<![A-Za-z0-9])(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}")),
    ("github_fine_grained_pat", re.compile(rb"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{22,}")),
    ("slack_token", re.compile(rb"(?<![A-Za-z0-9])xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("supabase_service_key", re.compile(rb"(?<![A-Za-z0-9])sbp_[A-Za-z0-9]{20,}")),
    # F6: escaped single-line PEM — a key serialised as a JSON/env string with
    # literal \n separators (e.g. a GCP service-account "private_key" field).
    ("pem_private_key_escaped_in_binary", re.compile(
        rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----\\n"
        rb"(?:[A-Za-z0-9+/=]{8,}\\n){2,}")),
]

# F6: indented / quoted / list-prefixed PEM header that is followed by a
# base64 body line — i.e. a real key block embedded in YAML/JSON/Markdown.
# A marker literal inside tool source (mid-line, followed by a quote/comma,
# no base64 body) does not match, so scanner/validator sources stay clean.
PEM_HEADER_ANYWHERE = re.compile(
    r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----")
PEM_BODY_LINE = re.compile(r"^\s*[\"']?[A-Za-z0-9+/=]{20,}[\"']?,?\s*$")
# F6: the same key material serialised onto ONE line with literal backslash-n
# separators (JSON / .env / YAML single-line strings). Requires at least two
# escaped base64 body segments so a lone pattern literal cannot match.
PEM_ESCAPED_LINE = re.compile(
    r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----\\n"
    r"(?:[A-Za-z0-9+/=]{8,}\\n){2,}")


def indented_pem_block(text):
    """True if any PEM private-key header (at any indentation / quoting) is
    directly followed by a base64-looking body line."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not PEM_HEADER_ANYWHERE.search(line):
            continue
        for nxt in lines[i + 1:i + 3]:
            if not nxt.strip():
                continue
            if PEM_BODY_LINE.match(nxt):
                return True
            break
    return False


def is_binary(data):
    return b"\x00" in data[:2048]


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
        if is_binary(data):
            # F6: binary blobs are scanned in the byte domain — never skipped.
            for name, pat in BINARY_PATTERNS:
                if pat.search(data):
                    findings.append((rel, name))
                    break
            continue
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        hit = None
        for name, pat in SECRET_PATTERNS:
            if pat.search(text):
                hit = name
                break
        if hit is None and indented_pem_block(text):
            hit = "pem_private_key_indented"
        if hit is None and PEM_ESCAPED_LINE.search(text):
            hit = "pem_private_key_escaped"
        if hit:
            findings.append((rel, hit))
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
