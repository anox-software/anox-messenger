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


def build_git_snapshot(state, effective_gate=""):
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

    # Resolved lifecycle metadata for archive-mode consistency checks.
    # This is NOT a cryptographic authentication; it is a materialized copy of the
    # state that the generator resolved at packaging time.
    #
    # Only emit the block for explicitly current-lifecycle archives, so a legacy
    # archive cannot be confused with a current one. The presence of this block
    # in an archive forces current-lifecycle validation regardless of what an
    # attacker writes in CURRENT_STATE.json.
    if state.get("canonical_branch") and state.get("delivery_branch") and state.get("pre_merge_gate") and state.get("post_merge_gate"):
        lines.append("### Resolved lifecycle metadata")
        lines.append(f"canonical_branch: {state.get('canonical_branch')}")
        lines.append(f"delivery_branch: {state.get('delivery_branch')}")
        lines.append(f"described_head: {state.get('described_head') or state.get('baseline_head', '')}")
        lines.append(f"pre_merge_gate: {state.get('pre_merge_gate')}")
        lines.append(f"post_merge_gate: {state.get('post_merge_gate')}")
        lines.append(f"effective_gate: {effective_gate}")
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
            for marker in (b"__HANDOFF_HEAD__", b"__WORKING_TREE__", b"__HANDOFF_BRANCH__", b"__EFFECTIVE_GATE__", b"__PRE_MERGE_GATE__", b"__POST_MERGE_GATE__"):
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

    canonical_branch = state.get("canonical_branch") or state.get("baseline_branch", "main")
    delivery_branch = state.get("delivery_branch", branch)
    if branch == canonical_branch:
        effective_gate = state.get("post_merge_gate", state.get("current_gate", ""))
    elif branch == delivery_branch:
        effective_gate = state.get("pre_merge_gate", state.get("current_gate", ""))
    else:
        effective_gate = state.get("current_gate", "")

    # CURRENT_GIT_STATE placeholders
    content = content.replace("__HANDOFF_HEAD__", head)
    content = content.replace("__WORKING_TREE__", working_tree)
    content = content.replace("__HANDOFF_BRANCH__", branch)
    content = content.replace("__EFFECTIVE_GATE__", effective_gate)
    content = content.replace("__PRE_MERGE_GATE__", state.get("pre_merge_gate", ""))
    content = content.replace("__POST_MERGE_GATE__", state.get("post_merge_gate", ""))

    # CURRENT_STATE.json placeholder object support
    if "__HANDOFF_HEAD__" in content:
        content = content.replace('"__HANDOFF_HEAD__"', json.dumps(head))
    if "__WORKING_TREE__" in content:
        content = content.replace('"__WORKING_TREE__"', json.dumps(working_tree))
    if "__HANDOFF_BRANCH__" in content:
        content = content.replace('"__HANDOFF_BRANCH__"', json.dumps(branch))
    if "__EFFECTIVE_GATE__" in content:
        content = content.replace('"__EFFECTIVE_GATE__"', json.dumps(effective_gate))
    if '"__PRE_MERGE_GATE__"' in content:
        content = content.replace('"__PRE_MERGE_GATE__"', json.dumps(state.get("pre_merge_gate", "")))
    if '"__POST_MERGE_GATE__"' in content:
        content = content.replace('"__POST_MERGE_GATE__"', json.dumps(state.get("post_merge_gate", "")))

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
        state = {}
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
    # Ensure the canonical project-memory ledger and surface index are included.
    for mandatory in (
        "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
        "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
    ):
        if mandatory not in rel_files:
            rel_files.append(mandatory)
    rel_files.sort()
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

    effective_gate = resolve_placeholders("__EFFECTIVE_GATE__", state)
    git_snapshot = build_git_snapshot(state, effective_gate)

    # Load current state template
    state_path = REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json"
    state_text = state_path.read_text(encoding="utf-8") if state_path.exists() else ""
    resolved_state = resolve_placeholders(state_text, state)

    git_state_path = REPO_ROOT / "docs" / "continuity" / "CURRENT_GIT_STATE.md"
    git_state_text = git_state_path.read_text(encoding="utf-8") if git_state_path.exists() else ""
    resolved_git_state = resolve_placeholders(git_state_text, state)

    # Collect all archive entries (relative path, bytes) before writing any
    # manifest, so the SHA-256 manifest can cover every file except itself.
    entries = []
    for rel in rel_files:
        if rel == "docs/continuity/CURRENT_STATE.json":
            entries.append((rel, resolved_state.encode("utf-8")))
        elif rel == "docs/continuity/CURRENT_GIT_STATE.md":
            entries.append((rel, resolved_git_state.encode("utf-8")))
        else:
            entries.append((rel, (REPO_ROOT / rel).read_bytes()))

    # Git snapshot is a generated integrity-critical surface.
    entries.append(("GIT_SNAPSHOT.txt", git_snapshot.encode("utf-8")))

    # Build the human-readable manifest now that the file list is final.
    manifest.write("GIT_SNAPSHOT.txt\n")
    for rel, _ in entries:
        manifest.write(f"{rel}\n")
    manifest_text = manifest.getvalue().encode("utf-8")
    entries.append(("MANIFEST.txt", manifest_text))

    # Build SHA-256 manifest covering every regular file except SHA256_MANIFEST.txt.
    sha_entries = []
    for rel, data in entries:
        sha_entries.append((hashlib.sha256(data).hexdigest(), rel))
    sha_manifest_text = sha_manifest.getvalue()
    for digest, rel in sha_entries:
        sha_manifest_text += f"{digest}  {rel}\n"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, data in entries:
            zf.writestr(rel, data)
        zf.writestr("SHA256_MANIFEST.txt", sha_manifest_text)

    zip_digest = sha256_file(zip_path)
    total_files = len(entries) + 1  # +1 for SHA256_MANIFEST.txt

    print(f"ZIP PATH:     {zip_path}")
    print(f"ZIP SHA-256:  {zip_digest}")
    print(f"HANDOFF_SHA256: {zip_digest}")
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
