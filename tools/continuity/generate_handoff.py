#!/usr/bin/env python3
"""Generate an anoX V1 handoff ZIP."""

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "handoff"

EXCLUDED_DIRS = {
    ".git",
    "build",
    ".gradle",
    "target",
    "__pycache__",
    ".kotlin",
    "artifacts",
    "__MACOSX",
}

EXCLUDED_FILES = {
    ".DS_Store",
    "local.properties",
    ".env",
    ".env.local",
    ".env.production",
    "CURRENT_STATE_RESOLVED.json",
}

EXCLUDED_SUFFIXES = (
    ".jks",
    ".keystore",
    ".p12",
    ".apk",
    ".aab",
    ".dex",
    ".class",
    ".o",
    ".so",
    ".dylib",
    ".pyc",
    ".pyo",
    ".zip",
)

# Secret / high-risk export preflight.
# These are MINIMUM guards. B-017-Lite will introduce stronger maintained scanning.
FORBIDDEN_BASENAME_PATTERNS = (
    ".env",
    ".env.local",
    ".env.production",
    ".env.staging",
    "local.properties",
    "google-services.json",
)
FORBIDDEN_NAME_SUBSTRINGS = (
    "service-account",
    "service_account",
    "private-key",
    "private_key",
    "database-dump",
    "db_dump",
)
FORBIDDEN_EXTENSIONS = (
    ".env",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".jks",
    ".keystore",
    ".p8",
    ".pkcs8",
    ".cer",
    ".crt",
)
PEM_PRIVATE_KEY_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN DSA PRIVATE KEY-----",
    b"-----BEGIN ENCRYPTED PRIVATE KEY-----",
    b"-----BEGIN PGP PRIVATE KEY BLOCK-----",
)


def git_cmd(args):
    result = subprocess.run(
        ["git"] + args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip(), result.returncode


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_excluded(rel_path):
    parts = Path(rel_path).parts
    if any(p in EXCLUDED_DIRS for p in parts):
        return True
    name = parts[-1]
    if name in EXCLUDED_FILES:
        return True
    if name.startswith(".") and (name.endswith(".env") or name.endswith(".local")):
        return True
    if name.endswith(EXCLUDED_SUFFIXES):
        return True
    if name.startswith("._"):
        return True
    return False


def collect_files():
    files = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        # Prune excluded directories in place to avoid walking them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            full = Path(dirpath) / name
            rel = full.relative_to(REPO_ROOT).as_posix()
            if is_excluded(rel):
                continue
            files.append(rel)
    return sorted(files)


def preflight_security(rel_files):
    """Fail closed if high-risk secret material may be exported."""
    findings = []

    for rel in rel_files:
        name = Path(rel).name.lower()

        if name in FORBIDDEN_BASENAME_PATTERNS:
            findings.append((rel, "forbidden basename"))
            continue

        if any(sub in name for sub in FORBIDDEN_NAME_SUBSTRINGS):
            findings.append((rel, "forbidden filename marker"))
            continue

        if any(name.endswith(ext) for ext in FORBIDDEN_EXTENSIONS):
            findings.append((rel, "forbidden file extension"))
            continue

        # PEM / key marker scan (binary-safe, first 8 KiB).
        # Skip .py source files to avoid tripping over the detector's own marker list.
        full = REPO_ROOT / rel
        if full.suffix == ".py":
            continue
        try:
            with open(full, "rb") as f:
                head = f.read(8192)
        except (OSError, PermissionError):
            continue
        for marker in PEM_PRIVATE_KEY_MARKERS:
            if marker in head:
                findings.append((rel, "private-key PEM marker"))
                break

    if findings:
        print("ERROR: handoff secret preflight failed. Rejecting the following high-risk artifacts:", file=sys.stderr)
        for path, reason in findings:
            print(f"  - {path}: {reason}", file=sys.stderr)
        return False
    return True


def build_git_snapshot():
    lines = []
    for cmd, label in [
        (["remote", "-v"], "git remote -v"),
        (["branch", "--show-current"], "git branch --show-current"),
        (["rev-parse", "HEAD"], "git rev-parse HEAD"),
        (["status", "--short"], "git status --short"),
        (["tag", "--list"], "git tag --list"),
        (["log", "--oneline", "-n", "15"], "git log --oneline -n 15"),
    ]:
        out, _ = git_cmd(cmd)
        lines.append(f"### {label}")
        lines.append(out if out else "(empty)")
        lines.append("")
    return "\n".join(lines)


def check_unresolved_placeholders(rel_files):
    """Fail if a current-state surface still contains unresolved runtime placeholders."""
    watched = {
        "PROJECT_STATE.md",
        "FORTSCHRITT.md",
        "docs/continuity/CURRENT_HANDOFF.md",
        "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
        "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
        "docs/continuity/CURRENT_OPEN_WORK.md",
        "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
        "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    }
    placeholder_files = []
    for rel in rel_files:
        if rel not in watched:
            continue
        if rel in ("docs/continuity/CURRENT_STATE.json", "docs/continuity/CURRENT_GIT_STATE.md"):
            # These are resolved before writestr()
            continue
        full = REPO_ROOT / rel
        try:
            with open(full, "rb") as f:
                data = f.read()
            for marker in (b"__HANDOFF_HEAD__", b"__WORKING_TREE__"):
                if marker in data:
                    placeholder_files.append(f"{rel} ({marker.decode('utf-8')})")
                    break
        except OSError:
            pass
    if placeholder_files:
        print("ERROR: unresolved runtime placeholders found in current-state surfaces:", file=sys.stderr)
        for pf in placeholder_files:
            print(f"  {pf}", file=sys.stderr)
        return False
    return True


def resolve_placeholders(content, state):
    """Replace template placeholders with live Git and state values."""
    head, _ = git_cmd(["rev-parse", "HEAD"])
    status, _ = git_cmd(["status", "--short"])
    working_tree = "clean" if status.strip() == "" else "dirty"
    branch, _ = git_cmd(["branch", "--show-current"])

    # CURRENT_GIT_STATE placeholders
    content = content.replace("__HANDOFF_HEAD__", head)
    content = content.replace("__WORKING_TREE__", working_tree)

    # CURRENT_STATE.json placeholder object support
    if "__HANDOFF_HEAD__" in content:
        # for JSON strings
        content = content.replace('"__HANDOFF_HEAD__"', json.dumps(head))
    if "__WORKING_TREE__" in content:
        content = content.replace('"__WORKING_TREE__"', json.dumps(working_tree))

    # Additional simple state placeholders for future use
    content = content.replace("__HANDOFF_BRANCH__", branch)
    return content


def validate_or_fail():
    """Run the continuity validator in live mode and fail closed if it does not pass."""
    validator = REPO_ROOT / "tools" / "continuity" / "validate_continuity.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--mode", "live"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Continuity validation failed. Handoff generation blocked.", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate an anoX handoff package.")
    parser.add_argument(
        "--emergency",
        action="store_true",
        help="Allow a dirty working tree and label the package as emergency/dirty.",
    )
    args = parser.parse_args()

    head, _ = git_cmd(["rev-parse", "HEAD"])
    short = head[:12]
    branch, _ = git_cmd(["branch", "--show-current"])
    status, _ = git_cmd(["status", "--short"])

    # Baseline information from CURRENT_STATE.json or default
    state_path = REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json"
    baseline_branch = "main"
    baseline_head = ""
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        baseline_branch = state.get("baseline_branch", "main")
        # Canonical precedence: described_head wins; baseline_head is legacy fallback.
        baseline_head = state.get("described_head", "") or state.get("baseline_head", "")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    # If possible, resolve the real baseline branch HEAD. Use --verify so an
    # unresolvable ref returns empty and the fallback precedence is preserved.
    real_baseline_head, code = git_cmd(["rev-parse", "--verify", baseline_branch]) if baseline_branch else ("", -1)
    if real_baseline_head and code == 0:
        baseline_head = real_baseline_head

    dirty = status.strip() != ""
    if dirty and not args.emergency:
        print("ERROR: Working tree is dirty. Clean it or use --emergency.", file=sys.stderr)
        print(status, file=sys.stderr)
        return 1

    # Fail-closed validation for normal handoffs
    if not args.emergency:
        if not validate_or_fail():
            return 1

    rel_files = collect_files()
    if not check_unresolved_placeholders(rel_files):
        return 1
    if not preflight_security(rel_files):
        return 1

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    status_label = "EMERGENCY_DIRTY" if (dirty and args.emergency) else "CLEAN"
    zip_name = f"ANOX_HANDOFF_{date_str}_{short}.zip"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = ARTIFACT_DIR / zip_name

    manifest = io.StringIO()
    manifest.write(f"# ANOX V1 Handoff Manifest\n")
    manifest.write(f"# Date: {date_str}\n")
    manifest.write(f"# Handoff branch: {branch}\n")
    manifest.write(f"# Handoff HEAD: {head}\n")
    manifest.write(f"# Baseline branch: {baseline_branch}\n")
    manifest.write(f"# Baseline HEAD: {baseline_head}\n")
    manifest.write(f"# Status: {status_label}\n")
    manifest.write(f"# File count: {len(rel_files)}\n")
    manifest.write("\n")

    sha_manifest = io.StringIO()
    sha_manifest.write(f"# SHA-256 manifest for {zip_name}\n")
    sha_manifest.write(f"# HEAD: {head}\n\n")

    git_snapshot = build_git_snapshot()

    # Load current state template
    state_path = REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json"
    state_text = state_path.read_text(encoding="utf-8") if state_path.exists() else ""
    resolved_state = resolve_placeholders(state_text, {})

    git_state_path = REPO_ROOT / "docs" / "continuity" / "CURRENT_GIT_STATE.md"
    git_state_text = git_state_path.read_text(encoding="utf-8") if git_state_path.exists() else ""
    resolved_git_state = resolve_placeholders(git_state_text, {})

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in rel_files:
            if rel == "docs/continuity/CURRENT_STATE.json":
                zf.writestr(rel, resolved_state)
                digest = hashlib.sha256(resolved_state.encode("utf-8")).hexdigest()
                manifest.write(f"{rel}\n")
                sha_manifest.write(f"{digest}  {rel}\n")
            elif rel == "docs/continuity/CURRENT_GIT_STATE.md":
                zf.writestr(rel, resolved_git_state)
                digest = hashlib.sha256(resolved_git_state.encode("utf-8")).hexdigest()
                manifest.write(f"{rel}\n")
                sha_manifest.write(f"{digest}  {rel}\n")
            else:
                full = REPO_ROOT / rel
                zf.write(full, rel)
                digest = sha256_file(full)
                manifest.write(f"{rel}\n")
                sha_manifest.write(f"{digest}  {rel}\n")

        # Git snapshot
        zf.writestr("GIT_SNAPSHOT.txt", git_snapshot)

        # Manifests
        zf.writestr("MANIFEST.txt", manifest.getvalue())
        zf.writestr("SHA256_MANIFEST.txt", sha_manifest.getvalue())

    zip_digest = sha256_file(zip_path)
    total_files = len(rel_files) + 3  # 3 generated text files

    print(f"ZIP PATH:     {zip_path}")
    print(f"ZIP SHA-256:  {zip_digest}")
    print(f"FILE COUNT:   {total_files}")
    print(f"HEAD:         {head}")
    print(f"STATUS:       {status_label}")

    if dirty:
        print("\nWARNING: EMERGENCY / DIRTY HANDOFF")
        print("Dirty files:")
        print(status)

    return 0


if __name__ == "__main__":
    sys.exit(main())
