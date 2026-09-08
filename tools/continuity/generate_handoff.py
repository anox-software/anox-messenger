#!/usr/bin/env python3
"""Generate an anoX V1 handoff ZIP.

The handoff is built in a temporary staging directory so archive-local surfaces
can be rendered with the effective runtime state without modifying any tracked
repository files. The staged tree is then packaged into a ZIP with SHA-256
manifests and a GIT_SNAPSHOT.txt.
"""

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "handoff"

# Make the canonical workforce resolver importable.
WORKFORCE_PATH = REPO_ROOT / "tools" / "workforce"
if str(WORKFORCE_PATH) not in sys.path:
    sys.path.insert(0, str(WORKFORCE_PATH))
import state_gate_resolver

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
    ".env.staging",
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

# Markers that make a current-state surface runtime-derived.
# The generator replaces <!-- ANOX:field -->value<!-- /ANOX:field --> with the
# derived archive value. The tracked file keeps the recorded value as a fallback
# and as a stable historical record.
ANOX_MARKER_RE = re.compile(
    r"<!--\s*ANOX:(\w+)\s*-->(.*?)<!--\s*/ANOX:\1\s*-->",
    re.DOTALL,
)

PLACEHOLDER_MARKERS = (
    b"__HANDOFF_HEAD__",
    b"__WORKING_TREE__",
    b"__HANDOFF_BRANCH__",
    b"__EFFECTIVE_GATE__",
    b"__PRE_MERGE_GATE__",
    b"__POST_MERGE_GATE__",
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
            for marker in PLACEHOLDER_MARKERS:
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


def resolve_placeholders(content, state, head=None, branch=None, working_tree=None):
    """Replace template placeholders with live Git and state values."""
    if head is None:
        head, _ = git_cmd(["rev-parse", "HEAD"])
    if branch is None:
        branch, _ = git_cmd(["branch", "--show-current"])
    if working_tree is None:
        status, _ = git_cmd(["status", "--short"])
        working_tree = "clean" if status.strip() == "" else "dirty"

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


def _find_task_for_phase(phase, repo_root):
    """Locate a task record whose task_id ends with the normalized phase name."""
    if not phase:
        return None
    suffix = re.sub(r"[^A-Z0-9]", "", phase.upper())
    tasks_path = repo_root / "docs" / "workforce" / "registries" / "tasks.jsonl"
    if not tasks_path.exists():
        return None
    try:
        for line in tasks_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            task = json.loads(line)
            task_id = task.get("task_id", "")
            title = task.get("title", "")
            if task_id.upper().endswith(suffix) or title.startswith(phase):
                return task
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _task_bullet(phase, repo_root, fallback=None):
    """Return a concise markdown bullet for the active task of a phase."""
    task = _find_task_for_phase(phase, repo_root)
    if task:
        status = task.get("status", "")
        start = task.get("start_sha", "")
        if start and len(start) > 40:
            start = start[:40] + "..."
        start_note = f" `start_sha` {start}" if start and "NOT YET" not in start.upper() else " `start_sha` NOT YET BOUND — HUMAN SUPPLIES POST-MERGE MAIN SHA"
        return f"`{phase}` (`{task['task_id']}`) — {task.get('title', '')} — `{status}`;{start_note}"
    if fallback:
        return f"`{phase}` — {fallback}"
    return f"`{phase}`"


def _next_task_paragraph(phase, repo_root, fallback=None):
    """Return a full Next-task paragraph for the archive."""
    task = _find_task_for_phase(phase, repo_root)
    if task:
        status = task.get("status", "")
        scope = task.get("scope", "").strip()
        non_goals = task.get("non_goals", [])
        ng = "; ".join(non_goals) if non_goals else "No product code; no Security Architecture audit; remote NONE"
        start = task.get("start_sha", "")
        if "NOT YET" in start.upper():
            start = "NOT YET BOUND — HUMAN SUPPLIES POST-MERGE MAIN SHA"
        return (
            f"`{phase}` (`{task['task_id']}`) — {task.get('title', '')} — `{status}`. "
            f"Scope: {scope} {ng}."
        )
    if fallback:
        return f"`{phase}` — {fallback}"
    return f"`{phase}`"


def derive_archive_context(state, head, branch, working_tree, repo_root):
    """Derive the archive-effective runtime context from resolver/Git truth."""
    workforce_state = {}
    ws_path = repo_root / "docs" / "workforce" / "WORKFORCE_STATE.json"
    if ws_path.exists():
        try:
            workforce_state = json.loads(ws_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    effective_state = state_gate_resolver.derive_effective_workforce_state(
        workforce_state,
        live_branch=branch,
        live_head=head,
        repo_root=repo_root,
    ) or {}

    canonical_branch = state.get("canonical_branch") or state.get("baseline_branch", "main")
    delivery_branch = state.get("delivery_branch", branch)
    if branch == canonical_branch:
        effective_gate = state.get("post_merge_gate", state.get("current_gate", ""))
    elif branch == delivery_branch:
        effective_gate = state.get("pre_merge_gate", state.get("current_gate", ""))
    else:
        effective_gate = state.get("current_gate", "")

    # Active work is the phase currently in effect.
    active_phase = effective_state.get("current_gate") or effective_gate
    # Extract a short phase token (e.g. "WORKFORCE-RETEST-01").
    phase_match = re.match(r"^(WORKFORCE-[A-Z]+-\d+)", active_phase or "")
    active_phase_token = phase_match.group(1) if phase_match else active_phase

    next_phase = effective_state.get("next_phase") or state.get("post_merge_gate", "")
    np_match = re.match(r"^(WORKFORCE-[A-Z]+-\d+)", next_phase or "")
    next_phase_token = np_match.group(1) if np_match else next_phase

    product_status = workforce_state.get("product_development_state") or "BLOCKED_PENDING_FINAL_AUDIT"

    context = {
        "handoff_version": active_phase or effective_gate,
        "working_tree": working_tree,
        "effective_gate": effective_gate,
        "pre_merge_gate": state.get("pre_merge_gate", ""),
        "post_merge_gate": state.get("post_merge_gate", ""),
        "handoff_branch": branch,
        "handoff_head": head,
        "current_work_branch": branch,
        "current_head": head,
        "latest_material_event": state.get("latest_material_event_id", ""),
        "product_status": product_status,
        "b004_status": "NOT_STARTED",
        "b005_status": "NOT_STARTED",
        "current_open_work": _task_bullet(active_phase_token, repo_root, fallback="active work"),
        "next_task": _next_task_paragraph(next_phase_token, repo_root, fallback="next task"),
    }
    return context


def _rewrite_hardcoded_headers(text, state):
    """Synchronize hardcoded handoff header lines with the resolved state.

    CURRENT_HANDOFF.md and CURRENT_GIT_STATE.md intentionally keep human-readable
    copies of described_head, delivery_branch, and main baseline. These must be
    rewritten from the resolved state so that archive-mode validation does not
    see a contradiction between the prose and CURRENT_STATE.json.
    """
    described = state.get("described_head", "")
    delivery = state.get("delivery_branch", "")
    baseline = state.get("main_baseline_head", "") or state.get("previous_baseline_head", "")
    pre = state.get("pre_merge_gate", "")
    post = state.get("post_merge_gate", "")
    current = state.get("current_gate", "")

    # CURRENT_HANDOFF.md uses backticks around values.
    text = re.sub(
        r"^(Delivery branch: `)[^`]+(`)$",
        lambda m: f"{m.group(1)}{delivery}{m.group(2)}",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(Described HEAD: `)[^`]+(`)$",
        lambda m: f"{m.group(1)}{described}{m.group(2)}",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(Main baseline HEAD: `)[^`]+(`)$",
        lambda m: f"{m.group(1)}{baseline}{m.group(2)}",
        text,
        flags=re.MULTILINE,
    )

    # CURRENT_GIT_STATE.md uses plain values (no trailing backtick).
    text = re.sub(
        r"^(- Main baseline: )[0-9a-f]{40}$",
        lambda m: f"{m.group(1)}{baseline}",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(- Described HEAD: )[0-9a-f]{40}$",
        lambda m: f"{m.group(1)}{described}",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(- Pre-merge gate: ).+$",
        lambda m: f"{m.group(1)}{pre}",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(- Post-merge gate: ).+$",
        lambda m: f"{m.group(1)}{post}",
        text,
        flags=re.MULTILINE,
    )
    # Effective gate line may contain a backtick value.
    text = re.sub(
        r"^(- Effective gate: `?)[^`\n]+(`?)$",
        lambda m: f"{m.group(1)}{current}{m.group(2)}",
        text,
        flags=re.MULTILINE,
    )
    return text


def render_archive_surface(text, context, fallback_to_recorded=True):
    """Replace ANOX:field markers with derived archive values."""
    def repl(match):
        field = match.group(1)
        if field in context:
            return str(context[field])
        if fallback_to_recorded:
            return match.group(2)
        return match.group(0)

    return ANOX_MARKER_RE.sub(repl, text)


def stage_archive_files(staging, rel_files, state, head, branch, working_tree, repo_root):
    """Copy all tracked files into the staging directory and render archive surfaces."""
    for rel in rel_files:
        src = repo_root / rel
        dst = staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel in ("docs/continuity/CURRENT_STATE.json", "docs/continuity/CURRENT_GIT_STATE.md"):
            # These are resolved below.
            shutil.copy2(src, dst)
        else:
            shutil.copy2(src, dst)

    # Resolve CURRENT_STATE.json
    state_path = staging / "docs" / "continuity" / "CURRENT_STATE.json"
    state_text = state_path.read_text(encoding="utf-8")
    resolved_state_text = resolve_placeholders(state_text, state, head=head, branch=branch, working_tree=working_tree)
    resolved_state = json.loads(resolved_state_text)
    # Synchronize the current_task with the effective runtime state.
    ws_path = repo_root / "docs" / "workforce" / "WORKFORCE_STATE.json"
    if ws_path.exists():
        try:
            workforce_state = json.loads(ws_path.read_text(encoding="utf-8"))
            effective_state = state_gate_resolver.derive_effective_workforce_state(
                workforce_state,
                live_branch=branch,
                live_head=head,
                repo_root=repo_root,
            ) or {}
            resolved_state["current_task"] = effective_state.get("current_task") or resolved_state.get("current_task", "")
        except (json.JSONDecodeError, OSError):
            pass
    state_path.write_text(json.dumps(resolved_state, indent=2, ensure_ascii=False), encoding="utf-8")

    # Resolve CURRENT_GIT_STATE.md and rewrite hardcoded headers.
    git_state_path = staging / "docs" / "continuity" / "CURRENT_GIT_STATE.md"
    git_state_text = git_state_path.read_text(encoding="utf-8")
    resolved_git_state = resolve_placeholders(git_state_text, state, head=head, branch=branch, working_tree=working_tree)
    resolved_git_state = _rewrite_hardcoded_headers(resolved_git_state, resolved_state)
    git_state_path.write_text(resolved_git_state, encoding="utf-8")

    # Render runtime-derived surfaces in the archive.
    context = derive_archive_context(state, head, branch, working_tree, repo_root)
    archive_surfaces = [
        "docs/continuity/CURRENT_HANDOFF.md",
    ]
    for rel in archive_surfaces:
        p = staging / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        rendered = render_archive_surface(text, context)
        rendered = _rewrite_hardcoded_headers(rendered, resolved_state)
        p.write_text(rendered, encoding="utf-8")

    # Sanity-check that archive surfaces do not contain unrendered ANOX markers.
    for rel in archive_surfaces:
        p = staging / rel
        if ANOX_MARKER_RE.search(p.read_text(encoding="utf-8")):
            raise RuntimeError(f"Archive surface {rel} still contains unrendered ANOX markers")

    return context


def validate_archive_staging(staging):
    """Run the archive-mode continuity validator against the staged tree."""
    validator = REPO_ROOT / "tools" / "continuity" / "validate_continuity.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--mode", "archive", "--archive", str(staging)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Archive validation failed for staged handoff. Generation blocked.", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    return True


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

    working_tree = "clean" if not dirty else "dirty"

    with tempfile.TemporaryDirectory(prefix="anox_handoff_staging_") as td:
        staging = Path(td)

        # Build the archive tree in a temporary staging directory.
        stage_archive_files(staging, rel_files, state, head, branch, working_tree, REPO_ROOT)

        manifest = io.StringIO()
        manifest.write(f"# ANOX V1 Handoff Manifest\n")
        manifest.write(f"# Date: {date_str}\n")
        manifest.write(f"# Handoff branch: {branch}\n")
        manifest.write(f"# Handoff HEAD: {head}\n")
        manifest.write(f"# Baseline branch: {baseline_branch}\n")
        manifest.write(f"# Baseline HEAD: {baseline_head}\n")
        manifest.write(f"# Status: {status_label}\n")
        manifest.write(f"# File count: {len(rel_files) + 3}\n")  # rel_files + GIT_SNAPSHOT + MANIFEST + SHA256
        manifest.write("\n")

        sha_manifest = io.StringIO()
        sha_manifest.write(f"# SHA-256 manifest for {zip_name}\n")
        sha_manifest.write(f"# HEAD: {head}\n\n")

        effective_gate = resolve_placeholders("__EFFECTIVE_GATE__", state, head=head, branch=branch, working_tree=working_tree)
        git_snapshot = build_git_snapshot(state, effective_gate)

        # Write generated integrity surfaces into the staging tree.
        (staging / "GIT_SNAPSHOT.txt").write_text(git_snapshot, encoding="utf-8")

        # Build the human-readable manifest now that the file list is final.
        manifest.write("GIT_SNAPSHOT.txt\n")
        for rel in rel_files:
            manifest.write(f"{rel}\n")
        manifest_text = manifest.getvalue().encode("utf-8")
        (staging / "MANIFEST.txt").write_bytes(manifest_text)

        # Build SHA-256 manifest covering every regular file except SHA256_MANIFEST.txt.
        all_files = sorted(p.relative_to(staging) for p in staging.rglob("*") if p.is_file())
        sha_entries = []
        for fpath in all_files:
            rel = fpath.as_posix()
            if rel == "SHA256_MANIFEST.txt":
                continue
            data = (staging / fpath).read_bytes()
            sha_entries.append((hashlib.sha256(data).hexdigest(), rel))
        sha_manifest_text = sha_manifest.getvalue()
        for digest, rel in sha_entries:
            sha_manifest_text += f"{digest}  {rel}\n"
        (staging / "SHA256_MANIFEST.txt").write_text(sha_manifest_text, encoding="utf-8")

        # Recompute all_files after generated surfaces added.
        all_files = sorted(p.relative_to(staging) for p in staging.rglob("*") if p.is_file())

        # Fail-closed archive validation before packaging.
        if not validate_archive_staging(staging):
            return 1

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fpath in all_files:
                zf.write(staging / fpath, fpath.as_posix())

    zip_digest = sha256_file(zip_path)
    total_files = len(all_files)

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
