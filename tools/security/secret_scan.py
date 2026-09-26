#!/usr/bin/env python3
"""Repository secret scan — fail-closed CI gate (MSC-UNIT-003 / B-017-Lite).

Scans every tracked file (or an explicit file list) for committed secret
material:

  * private-key PEM blocks — line-start anchored, PLUS indented/quoted headers
    that are followed by a base64 body, PLUS byte-domain markers inside
    binary blobs; bare marker literals inside tool source do not
    false-positive,
  * well-known token formats (AWS, GitHub, Slack, Supabase service keys,
    generic Bearer/JWT service-role patterns),
  * committed key-store / certificate / env files that must never be tracked.

Binary/unreadable input is handled safely: a NUL-containing file is scanned in
the byte domain rather than skipped, and a file too large to scan is a
finding, never a silent pass.

Tracked paths come from a NUL-delimited Git interface (``git ls-files -z``)
and are handled as raw bytes end to end: filenames containing Unicode,
spaces, leading/trailing spaces, quotes, newlines or shell-sensitive
characters are scanned exactly as Git names them. A tracked path missing
from the working tree still has staged index content (``git add`` followed
by ``rm`` leaves the secret-bearing blob tracked), so its index blob is
scanned instead of skipped. A tracked path resolvable in neither the tree
nor the index is a finding (``tracked_path_unresolvable``) — never a silent
skip.

Prints only file + rule names — never the matched value.
Stdlib only.
"""

import argparse
import os
import re
import stat as _stat
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

# Byte-domain rules applied to EVERY binary file: a NUL byte no longer exempts
# a file. PEM markers inside binaries are always a finding; token formats are
# byte-exact.
BINARY_PATTERNS = [
    ("pem_private_key_in_binary", re.compile(
        rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----")),
    ("aws_access_key", re.compile(rb"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])")),
    ("github_token", re.compile(rb"(?<![A-Za-z0-9])(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}")),
    ("github_fine_grained_pat", re.compile(rb"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{22,}")),
    ("slack_token", re.compile(rb"(?<![A-Za-z0-9])xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("supabase_service_key", re.compile(rb"(?<![A-Za-z0-9])sbp_[A-Za-z0-9]{20,}")),
    # A key serialised as a JSON/env string with literal \n separators
    # (e.g. a GCP service-account "private_key" field).
    ("pem_private_key_escaped_in_binary", re.compile(
        rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----\\n"
        rb"(?:[A-Za-z0-9+/=]{8,}\\n){2,}")),
    # Material text rules aligned into the byte domain: a generic secret
    # assignment does not stop being a secret because the carrier contains
    # NUL bytes (string tables, serialized blobs, resource archives).
    ("generic_api_secret_assignment", re.compile(
        rb"(?i)(?<![A-Za-z0-9_])(api[_-]?secret|client[_-]?secret|service[_-]?role[_-]?key)"
        rb"(?![A-Za-z0-9_])\s*[:=]\s*['\"][A-Za-z0-9+/=_-]{20,}['\"]")),
]

# Indented / quoted / list-prefixed PEM header that is followed by a base64
# body line — i.e. a real key block embedded in YAML/JSON/Markdown. A marker
# literal inside tool source (mid-line, followed by a quote/comma, no base64
# body) does not match, so scanner/validator sources stay clean.
PEM_HEADER_ANYWHERE = re.compile(
    r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----")
# A base64 body line may carry textual/container prefixes: YAML/Markdown list
# markers (- * + >), ordered-list markers (1.), heading marks (#...), table
# cell marks (|), indentation and an optional quote. Prefixes are only
# tolerated in the marker run before the base64 span — arbitrary prose does
# not match, and a match still requires a preceding PEM header line.
PEM_BODY_LINE = re.compile(
    r"^\s*(?:(?:[-*+>|]|#{1,6}|\d+\.)[ \t]*)*[\"']?[A-Za-z0-9+/=]{20,}[\"']?,?[ \t]*\|?[ \t]*$")
# The same key material serialised onto ONE line with literal backslash-n
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
    """Tracked paths as raw bytes from ``git ls-files -z`` (NUL-delimited).

    Never newline-split, never stripped: a filename may legitimately contain
    newlines, leading/trailing spaces, quotes or any non-NUL byte. Returns
    None when Git cannot enumerate the tree (caller fails closed).
    """
    try:
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=off", "ls-files", "-z"],
            cwd=repo_root, capture_output=True, timeout=600,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.split(b"\x00") if p]


def tracked_index_blobs(repo_root):
    """Map of tracked path bytes -> staged blob SHA from ``git ls-files -z -s``.

    The ``-s`` record is ``<mode> SP <sha> SP <stage> TAB <path>`` per NUL-
    terminated entry; the path portion is raw bytes and may contain anything
    except NUL. Returns {} when Git cannot enumerate the index (a missing
    worktree path then stays unresolvable — fail-closed).
    """
    try:
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=off", "ls-files", "-z", "-s"],
            cwd=repo_root, capture_output=True, timeout=600,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if proc.returncode != 0:
        return {}
    out = {}
    for rec in proc.stdout.split(b"\x00"):
        if not rec:
            continue
        meta, sep, path = rec.partition(b"\t")
        if not sep or not path:
            continue
        parts = meta.split()
        if len(parts) >= 2 and re.fullmatch(rb"[0-9a-f]{40}", parts[1]):
            out[path] = parts[1]
    return out


def index_blob_bytes(repo_root, sha):
    """Content of a staged blob, or None when it cannot be read."""
    try:
        proc = subprocess.run(
            ["git", "cat-file", "blob", sha.decode("ascii")],
            cwd=repo_root, capture_output=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def walk_files(repo_root):
    out = []
    for p in sorted(Path(repo_root).rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(repo_root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        out.append(os.fsencode(str(rel)))
    return out


def _display(rel_bytes):
    """Printable form of a byte path: never leaks control characters into
    the log, never alters the path used for scanning."""
    return repr(os.fsdecode(rel_bytes))


def scan(repo_root, files=None):
    """Scan the given repo-relative paths (str or bytes; str is fsencoded).

    ``files=None`` scans ``git ls-files -z``; when Git is unavailable the tree
    walk is used. Every listed path either scans successfully or produces a
    finding — there is no silent skip for a tracked path.
    """
    findings = []
    root = Path(repo_root)
    root_b = os.fsencode(str(root))
    index_blobs = {}
    if files is None:
        rels = tracked_files(root)
        if rels is None:
            rels = walk_files(root)
        else:
            index_blobs = tracked_index_blobs(root)
    else:
        rels = [os.fsencode(f) if isinstance(f, str) else bytes(f) for f in files]
    for rel_b in rels:
        if not rel_b:
            continue
        rel = _display(rel_b)
        try:
            rel_text = rel_b.decode("utf-8")
        except UnicodeDecodeError:
            rel_text = rel_b.decode("utf-8", errors="surrogateescape")
        if FORBIDDEN_TRACKED.search(rel_text):
            findings.append((rel, "forbidden_tracked_file"))
            continue
        if rel_b.startswith(b"/") or b".." in rel_b.split(b"/"):
            findings.append((rel, "tracked_path_unresolvable"))
            continue
        p = os.path.join(root_b, rel_b)
        try:
            st = os.lstat(p)
        except OSError:
            st = None
        if st is None:
            # Tracked but absent from the tree (e.g. a pending deletion):
            # the staged index blob is still committed content and could
            # carry a staged secret — scan it instead of skipping.
            blob = index_blobs.get(rel_b)
            data = index_blob_bytes(root, blob) if blob else None
            if data is None:
                findings.append((rel, "tracked_path_unresolvable"))
                continue
        elif _stat.S_ISLNK(st.st_mode):
            # symlink content is the link target text; scan it as data
            try:
                data = os.readlink(p)
            except OSError:
                findings.append((rel, "tracked_path_unresolvable"))
                continue
        elif _stat.S_ISDIR(st.st_mode):
            findings.append((rel, "tracked_path_unresolvable"))
            continue
        else:
            if st.st_size > MAX_FILE_BYTES:
                findings.append((rel, "file_too_large_unscanned"))
                continue
            try:
                with open(p, "rb") as fh:
                    data = fh.read()
            except OSError:
                findings.append((rel, "tracked_path_unresolvable"))
                continue
        if len(data) > MAX_FILE_BYTES:
            findings.append((rel, "file_too_large_unscanned"))
            continue
        if is_binary(data):
            # Binary blobs are scanned in the byte domain — never skipped.
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
