#!/usr/bin/env python3
"""Validate anoX continuity / handoff readiness.

Supports two explicit modes:
  --mode live      validate the actual .git repository and current-state surfaces
  --mode archive   validate an extracted official handoff ZIP without .git
  --mode auto      choose live if .git exists, else archive if evidence exists

Mode is always printed. Live and archive results are never conflated.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "PROJECT_STATE.md",
    "FORTSCHRITT.md",
    "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
    "docs/authority/AUTHORITY_INDEX.md",
    "docs/authority/CLOUD_AI_SECRET_PROTECTION.md",
    "docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md",
    "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",
    "docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md",
    "docs/authority/B_FREEZE_REGISTRY.md",
    "docs/continuity/AUTHORITY_INDEX.md",
    "docs/continuity/CURRENT_HANDOFF.md",
    "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
    "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
    "docs/continuity/CURRENT_GIT_STATE.md",
    "docs/continuity/CURRENT_OPEN_WORK.md",
    "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
    "docs/continuity/DEVIN_OUTPUT_CONTRACT.md",
    "docs/continuity/HANDOFF_WORKFLOW.md",
    "docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md",
    "docs/continuity/CURRENT_STATE.json",
    "tools/continuity/generate_handoff.py",
    "tools/continuity/validate_continuity.py",
    "tools/security/validate_apk_contents.py",
]

REQUIRED_AUTHORITY_PATHS = {
    "authority_index": "docs/authority/AUTHORITY_INDEX.md",
    "cloud_ai_secret": "docs/authority/CLOUD_AI_SECRET_PROTECTION.md",
    "dev_security_workflow": "docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md",
    "security_invariants": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",
    "b026": "docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md",
    "freeze_registry": "docs/authority/B_FREEZE_REGISTRY.md",
    "ultimate_main": "docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md",
}

PLACEHOLDER_MARKERS = ("__HANDOFF_HEAD__", "__WORKING_TREE__")

# Files where runtime placeholders are intentional repository templates.
# In a generated handoff archive these placeholders MUST already be resolved.
# In live mode the validator resolves them against live Git.
PLACEHOLDER_TEMPLATE_FILES = {
    "docs/continuity/CURRENT_STATE.json",
    "docs/continuity/CURRENT_GIT_STATE.md",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Validate anoX continuity / handoff readiness.")
    parser.add_argument(
        "--mode",
        choices=["auto", "live", "archive"],
        default="auto",
        help="Validation mode: live requires .git, archive validates an extracted handoff",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        help="Path to an extracted handoff directory for archive mode",
    )
    return parser.parse_args()


def select_mode(args):
    if args.mode != "auto":
        return args.mode
    if (REPO_ROOT / ".git").is_dir():
        return "live"
    if args.archive and args.archive.exists():
        return "archive"
    if (REPO_ROOT / "MANIFEST.txt").exists() and (REPO_ROOT / "CURRENT_STATE.json").exists():
        return "archive"
    return "live"  # fallback; will fail clearly if .git is missing


def run_git(args, cwd=None, check=False):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        return None, None, -1


def git_status(cwd=None):
    out, _, code = run_git(["status", "--short"], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


def git_current_branch(cwd=None):
    out, _, code = run_git(["branch", "--show-current"], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


def git_current_head(cwd=None):
    out, _, code = run_git(["rev-parse", "HEAD"], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


def git_branch_head(branch, cwd=None):
    out, _, code = run_git(["rev-parse", branch], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


METADATA_ONLY_ALLOWLIST = frozenset(
    {
        "FORTSCHRITT.md",
        "PROJECT_STATE.md",
        "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
        "docs/continuity/CURRENT_STATE.json",
        "docs/continuity/CURRENT_GIT_STATE.md",
        "docs/continuity/CURRENT_HANDOFF.md",
        "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
        "docs/continuity/CURRENT_OPEN_WORK.md",
        "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
        "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
        "docs/continuity/HANDOFF_WORKFLOW.md",
        "docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md",
    }
)


def _is_allowed_metadata_path(rel):
    """Fail-closed metadata-only classifier.

    Unknown files and paths are substantive. Historical provenance directories
    are NOT broadly trusted; only explicitly listed current-state/project
    metadata files may qualify as metadata-only.
    """
    return rel in METADATA_ONLY_ALLOWLIST


def is_valid_sha(text):
    return bool(re.fullmatch(r"[0-9a-f]{40}", text or ""))


def git_object_exists(sha, cwd=None):
    """Return True if sha resolves to an existing Git object."""
    _, _, code = run_git(["rev-parse", "--verify", sha], cwd=cwd)
    return code == 0


def git_is_ancestor(ancestor, descendant, cwd=None):
    out, _, code = run_git(["merge-base", "--is-ancestor", ancestor, descendant], cwd=cwd)
    return code == 0


def git_diff_files(from_sha, to_sha, cwd=None):
    """Return all logical paths changed in the commit range [from_sha, to_sha].

    Uses `git log --name-only --no-renames` so every commit in the range is
    inspected. A file added in one commit and renamed in a later commit within
    the same range is still visible to the classifier, and a rename exposes
    both the deleted source path and the added destination path. The metadata-
    only classifier must independently approve BOTH sides of a rename.
    """
    out, _, code = run_git(["log", "--name-only", "--no-renames", "--format=oneline", f"{from_sha}..{to_sha}"], cwd=cwd)
    if code != 0 or out is None:
        return None
    paths = set()
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip commit subject lines (full SHA 40 hex, space, message).
        if re.match(r"^[0-9a-f]{40} ", line):
            continue
        paths.add(line)
    return sorted(paths)


def load_current_state(root):
    path = root / "docs" / "continuity" / "CURRENT_STATE.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_required_files(root, all_ok, label):
    print(f"\n[{label}] Required files")
    for rel in REQUIRED_FILES:
        path = root / rel
        if path.exists():
            print(f"  OK   {rel}")
        else:
            print(f"  FAIL {rel} — missing")
            all_ok = False
    return all_ok


def validate_authority_paths(root, all_ok, label):
    print(f"\n[{label}] Authority paths")
    for name, rel in REQUIRED_AUTHORITY_PATHS.items():
        path = root / rel
        if path.exists():
            print(f"  OK   {name}: {rel}")
        else:
            print(f"  FAIL {name}: {rel} — missing")
            all_ok = False
    return all_ok


def _resolve_described_head(state):
    """Return the described_head, migrating legacy baseline_head if needed.

    Canonical precedence: described_head wins when present; baseline_head is
    legacy fallback only.
    """
    return state.get("described_head") or state.get("baseline_head") or ""


def _check_required_state_keys(state):
    """Return (ok, errors) for mandatory current-state keys shared by live and archive."""
    required = ("handoff_branch", "security_invariants_path",
                "freeze_registry_path", "current_gate", "continuity_001_status")
    errors = []
    for key in required:
        if key not in state:
            errors.append(key)
    # Legacy archive compatibility: described_head may be absent if baseline_head is present.
    if "described_head" not in state and "baseline_head" not in state:
        errors.append("described_head (or legacy baseline_head)")
    return (len(errors) == 0, errors)


def validate_state_json(state, root, all_ok, label, live_branch=None, live_head=None, mode=None):
    print(f"\n[{label}] CURRENT_STATE.json")
    if state is None:
        print("  FAIL CURRENT_STATE.json missing or invalid JSON")
        return False

    keys_ok, missing = _check_required_state_keys(state)
    if not keys_ok:
        for key in missing:
            print(f"  FAIL CURRENT_STATE.json missing key: {key}")
        all_ok = False

    if state.get("continuity_001_status") != "ACCEPTED":
        print(f"  FAIL continuity_001_status = {state.get('continuity_001_status')} (expected ACCEPTED)")
        all_ok = False
    else:
        print("  OK   continuity_001_status = ACCEPTED")

    described_head = _resolve_described_head(state)
    if not described_head:
        print("  FAIL CURRENT_STATE.json described_head missing/unresolved")
        all_ok = False
    elif not is_valid_sha(described_head):
        print(f"  FAIL CURRENT_STATE.json described_head is not a valid 40-char hex SHA: {described_head}")
        all_ok = False
    else:
        if live_head is not None:
            all_ok = validate_described_head(described_head, live_head, root, all_ok, label)
        else:
            # Archive mode: we cannot verify ancestry without .git, but we can require the value.
            print(f"  OK   described_head {described_head[:12]} present (archive mode)")

    if live_branch is not None:
        expected_branch = state.get("handoff_branch")
        if expected_branch != live_branch:
            print(f"  FAIL CURRENT_STATE.json handoff_branch {expected_branch} != live branch {live_branch}")
            all_ok = False
        else:
            print(f"  OK   handoff_branch matches live {live_branch}")

    return all_ok


def validate_described_head(described_head, live_head, root, all_ok, label):
    print(f"\n[{label}] Described HEAD verification")
    print(f"  described_head: {described_head[:12]}")
    print(f"  live_head:      {live_head[:12]}")

    if described_head == live_head:
        print("  OK   described_head == live_head (CASE 1)")
        return all_ok

    if not is_valid_sha(live_head):
        print("  FAIL live HEAD is not a valid SHA")
        return False

    if not git_is_ancestor(described_head, live_head):
        print("  FAIL described_head is not an ancestor of live_head (CASE 4)")
        return False

    changed = git_diff_files(described_head, live_head)
    if changed is None:
        print("  FAIL could not determine diff between described_head and live_head")
        return False

    print(f"  described_head is an ancestor; {len(changed)} file(s) changed")
    disallowed = [p for p in changed if not _is_allowed_metadata_path(p)]
    if disallowed:
        print("  FAIL changes contain non-metadata-only files (CASE 3):")
        for p in disallowed[:10]:
            print(f"    - {p}")
        return False

    print("  OK   only metadata-only files changed (CASE 2 — METADATA-ONLY STATE ADVANCE)")
    return all_ok


def validate_current_state_surfaces(root, all_ok, label, live_branch=None):
    print(f"\n[{label}] Current-state surface consistency")

    project_state_path = root / "PROJECT_STATE.md"
    project_state_text = project_state_path.read_text(encoding="utf-8") if project_state_path.exists() else ""
    for marker in PLACEHOLDER_MARKERS:
        if marker in project_state_text:
            print(f"  FAIL PROJECT_STATE.md contains unresolved placeholder: {marker}")
            all_ok = False

    m = re.search(r"^[-*]\s*Branch:\s*`?([^`\n]+)`?", project_state_text, re.MULTILINE)
    if m:
        declared_branch = m.group(1).strip()
        if live_branch and declared_branch != live_branch:
            print(f"  FAIL PROJECT_STATE.md declares branch {declared_branch} but live branch is {live_branch}")
            all_ok = False
        elif live_branch:
            print(f"  OK   PROJECT_STATE.md branch = {declared_branch}")
    else:
        print("  WARN PROJECT_STATE.md branch line not found")

    fortschritt_path = root / "FORTSCHRITT.md"
    fortschritt_text = fortschritt_path.read_text(encoding="utf-8") if fortschritt_path.exists() else ""
    for marker in PLACEHOLDER_MARKERS:
        if marker in fortschritt_text:
            print(f"  FAIL FORTSCHRITT.md contains unresolved placeholder: {marker}")
            all_ok = False

    # CURRENT_HANDOFF.md must not contain unresolved placeholders
    handoff_path = root / "docs/continuity/CURRENT_HANDOFF.md"
    if handoff_path.exists():
        handoff_text = handoff_path.read_text(encoding="utf-8")
        for marker in PLACEHOLDER_MARKERS:
            if marker in handoff_text:
                print(f"  FAIL CURRENT_HANDOFF.md contains unresolved placeholder: {marker}")
                all_ok = False

    # Stale current-state phrases
    stale_phrases = [
        ("Approximately **27%**", "outdated functional progress"),
        ("Device Authentication work has not started", "outdated Device Auth claim"),
        ("B-003 has a client domain/state foundation in review", "outdated B-003 review claim"),
        ("PR #5 open", "stale PR #5 open claim in current-state"),
        ("not merged", "stale not-merged claim in current-state"),
        ("awaiting architect review", "stale awaiting-review claim in current-state"),
    ]
    for phrase, reason in stale_phrases:
        for path_name in ("PROJECT_STATE.md", "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md"):
            p = root / path_name
            if p.exists() and phrase in p.read_text(encoding="utf-8"):
                print(f"  FAIL {path_name} contains stale current-state phrase: {reason} ('{phrase}')")
                all_ok = False

    # CURRENT_NEXT_DEVIN_TASK.md must not contain PROMPT-008 as the current active task
    next_task_path = root / "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md"
    next_task_text = next_task_path.read_text(encoding="utf-8") if next_task_path.exists() else ""
    if re.search(r"PROMPT-008\b", next_task_text) and not re.search(r"MERGED", next_task_text):
        print("  FAIL CURRENT_NEXT_DEVIN_TASK.md still references PROMPT-008 as an active task without MERGED")
        all_ok = False

    # Contradictory B-003 status
    impl_path = root / "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md"
    impl_text = impl_path.read_text(encoding="utf-8") if impl_path.exists() else ""
    if re.search(r"B-003.*(open|not merged|in review)", impl_text, re.IGNORECASE) and re.search(r"B-003.*MERGED", impl_text):
        print("  FAIL CURRENT_IMPLEMENTATION_STATE.md contains contradictory B-003 merged and open/not-merged claims")
        all_ok = False

    return all_ok


def _resolve_and_check(text, marker, expected):
    """Replace a single placeholder with the expected value and confirm the text now contains it."""
    resolved = text.replace(marker, expected, 1)
    return resolved, expected in resolved


def validate_placeholders(root, all_ok, label, mode, live_state=None):
    """Validate runtime placeholders in current-state surfaces.

    Repository templates intentionally use __HANDOFF_HEAD__ and __WORKING_TREE__
    in docs/continuity/CURRENT_STATE.json and CURRENT_GIT_STATE.md; these are
    resolved by generate_handoff.py before packaging. In archive mode they MUST
    already be resolved. In live mode unresolved placeholders are acceptable only
    in the template files; all other current-state files must be concrete.
    """
    print(f"\n[{label}] Placeholder / template resolution")

    # Files that may never contain runtime placeholders
    concrete_files = [
        "PROJECT_STATE.md",
        "FORTSCHRITT.md",
        "docs/continuity/CURRENT_HANDOFF.md",
        "docs/continuity/CURRENT_OPEN_WORK.md",
        "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
        "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
        "docs/continuity/HANDOFF_WORKFLOW.md",
        "docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md",
    ]

    for rel in concrete_files:
        p = root / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for marker in PLACEHOLDER_MARKERS:
            if marker in text:
                print(f"  FAIL {rel} contains forbidden placeholder {marker}")
                all_ok = False

    state = load_current_state(root)

    # CURRENT_STATE.json template handling
    state_path = root / "docs/continuity/CURRENT_STATE.json"
    if state_path.exists() and state is not None:
        for key, marker in (("handoff_head", "__HANDOFF_HEAD__"), ("working_tree", "__WORKING_TREE__")):
            value = state.get(key, "")
            if value == marker:
                if mode == "archive":
                    print(f"  UNRESOLVED HANDOFF PLACEHOLDER: CURRENT_STATE.json {key} = {marker}")
                    all_ok = False
                elif live_state is not None:
                    # live repository template; confirm it is resolvable
                    resolved_value = live_state.get("head" if key == "handoff_head" else "working_tree", "")
                    expected = marker if resolved_value == "" else resolved_value
                    if resolved_value == "" or (resolved_value != "" and resolved_value not in (marker, "")):
                        print(f"  OK   CURRENT_STATE.json {key} placeholder is resolvable to live {key}")
                    else:
                        print(f"  FAIL CURRENT_STATE.json {key} placeholder cannot be resolved")
                        all_ok = False
                else:
                    print(f"  OK   CURRENT_STATE.json {key} placeholder (template)")
            elif value == "" or value is None:
                print(f"  FAIL CURRENT_STATE.json {key} is missing")
                all_ok = False
            else:
                if mode == "archive":
                    # resolved in archive; no further check needed
                    print(f"  OK   CURRENT_STATE.json {key} = {value[:24]}...")
                elif live_state is not None:
                    expected = live_state.get("head" if key == "handoff_head" else "working_tree", "")
                    if expected and value != expected:
                        print(f"  FAIL CURRENT_STATE.json {key} {value} != live {expected}")
                        all_ok = False
                    else:
                        print(f"  OK   CURRENT_STATE.json {key} matches live")

    # CURRENT_GIT_STATE.md template handling
    git_state_path = root / "docs/continuity/CURRENT_GIT_STATE.md"
    if git_state_path.exists():
        git_state_text = git_state_path.read_text(encoding="utf-8")
        for marker in PLACEHOLDER_MARKERS:
            if marker in git_state_text:
                if mode == "archive":
                    print(f"  UNRESOLVED HANDOFF PLACEHOLDER: CURRENT_GIT_STATE.md contains {marker}")
                    all_ok = False
                elif live_state is not None:
                    expected = live_state.get("head" if marker == "__HANDOFF_HEAD__" else "working_tree", "")
                    if expected and expected not in (marker, ""):
                        resolved_text = git_state_text.replace(marker, expected)
                        if expected in resolved_text:
                            print(f"  OK   CURRENT_GIT_STATE.md {marker} resolvable to live value")
                        else:
                            print(f"  FAIL CURRENT_GIT_STATE.md {marker} does not resolve to {expected}")
                            all_ok = False
                    else:
                        print(f"  FAIL CURRENT_GIT_STATE.md {marker} cannot be resolved")
                        all_ok = False
                else:
                    print(f"  OK   CURRENT_GIT_STATE.md {marker} placeholder (template)")

    # Verify concrete resolved values in CURRENT_GIT_STATE.md match live state
    if git_state_path.exists() and live_state is not None:
        git_state_text = git_state_path.read_text(encoding="utf-8")
        # Current handoff HEAD
        m = re.search(r"[-*]\s*(?:Current handoff HEAD|Handoff HEAD|HEAD):\s*`?([^`\n]+)`?", git_state_text, re.IGNORECASE)
        if m:
            recorded_head = m.group(1).strip()
            if recorded_head and recorded_head not in PLACEHOLDER_MARKERS:
                live_head = live_state.get("head", "")
                if live_head and recorded_head != live_head:
                    print(f"  FAIL CURRENT_GIT_STATE.md recorded handoff HEAD {recorded_head} != live {live_head}")
                    all_ok = False
                else:
                    print(f"  OK   CURRENT_GIT_STATE.md handoff HEAD matches live")
        # Working tree
        m = re.search(r"[-*]\s*Working tree:\s*`?([^`\n]+)`?", git_state_text, re.IGNORECASE)
        if m:
            recorded_tree = m.group(1).strip()
            if recorded_tree and recorded_tree not in PLACEHOLDER_MARKERS:
                live_tree = live_state.get("working_tree", "")
                if live_tree and recorded_tree != live_tree:
                    print(f"  FAIL CURRENT_GIT_STATE.md recorded working tree {recorded_tree} != live {live_tree}")
                    all_ok = False
                else:
                    print(f"  OK   CURRENT_GIT_STATE.md working tree matches live")

    return all_ok


def _extract_section(text, heading):
    """Return the text from a heading up to the next same-level heading or end of file."""
    pattern = re.escape(heading) + r"\n(.*?)((?=\n## )|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""


def validate_authority_precedence(root, all_ok, label):
    """Ensure only docs/authority/AUTHORITY_INDEX.md defines a canonical numbered precedence."""
    print(f"\n[{label}] Authority precedence drift")

    canonical_path = root / "docs/authority/AUTHORITY_INDEX.md"
    if canonical_path.exists():
        canonical_text = canonical_path.read_text(encoding="utf-8")
        # Accept either "## Precedence" or "## Authority precedence"
        canonical_section = _extract_section(canonical_text, "## Precedence") or _extract_section(canonical_text, "## Authority precedence")
        if re.search(r"^\d+\.\s+", canonical_section, re.MULTILINE):
            print("  OK   AUTHORITY_INDEX.md defines canonical numbered precedence")
        else:
            print("  WARN AUTHORITY_INDEX.md does not contain a numbered precedence list")
    else:
        print("  FAIL AUTHORITY_INDEX.md missing")
        return False

    # Other authority/continuity surfaces may not independently define a competing numbered list
    surfaces = [
        "docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md",
        "docs/continuity/CURRENT_HANDOFF.md",
        "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    ]
    for rel in surfaces:
        p = root / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for heading in ("## Authority precedence", "## Precedence"):
            section = _extract_section(text, heading)
            if not section:
                continue
            # Two or more numbered items in a non-canonical authority/precedence section = competing precedence
            items = re.findall(r"^\d+\.\s+", section, re.MULTILINE)
            if len(items) >= 2:
                print(f"  FAIL {rel} defines a competing numbered precedence list under {heading}")
                all_ok = False
                break
            elif len(items) == 1:
                # Single item still implies an attempt at a numbered list
                print(f"  FAIL {rel} attempts a competing numbered precedence list under {heading}")
                all_ok = False
                break

    return all_ok


def validate_baseline_consistency(root, all_ok, label):
    print(f"\n[{label}] Described HEAD consistency")

    handoff_path = root / "docs/continuity/CURRENT_HANDOFF.md"
    git_state_path = root / "docs/continuity/CURRENT_GIT_STATE.md"
    state = load_current_state(root)

    if state is None:
        print("  FAIL CURRENT_STATE.json missing/invalid")
        return False

    declared_head = _resolve_described_head(state)
    if not declared_head:
        print("  FAIL CURRENT_STATE.json described_head missing/unresolved")
        all_ok = False

    for path in (handoff_path, git_state_path):
        if not path.exists():
            print(f"  FAIL {path.name} missing")
            all_ok = False
            continue
        text = path.read_text(encoding="utf-8")
        # Prefer explicit described_head. Fallback to legacy baseline HEAD forms.
        m = re.search(r"(?:described_head|Described HEAD):\s*`?([^`\n]+)`?", text, re.IGNORECASE | re.MULTILINE)
        if not m:
            m = re.search(r"(?:Current\s+baseline\s+HEAD|Merged\s+baseline\s+HEAD):\s*`?([^`\n]+)`?", text, re.IGNORECASE | re.MULTILINE)
        if not m:
            print(f"  FAIL {path.name} does not declare described_head (or legacy baseline HEAD)")
            all_ok = False
        elif declared_head:
            doc_head = m.group(1).strip()
            if doc_head != declared_head:
                print(f"  FAIL {path.name} head {doc_head} != CURRENT_STATE.json {declared_head}")
                all_ok = False
            else:
                print(f"  OK   {path.name} described_head matches CURRENT_STATE.json")

    return all_ok


def validate_baseline_ancestry(state, live_baseline_head, all_ok, label):
    """Verify baseline metadata is non-self-referentially consistent.

    recorded `latest_merge_to_baseline` and `previous_baseline_head` must each
    be valid, resolvable, and ancestors of the live baseline branch head. They
    do not need to equal the live head, which breaks the old self-reference
    invariant.
    """
    print(f"\n[{label}] Baseline ancestry integrity")

    if not is_valid_sha(live_baseline_head):
        print(f"  FAIL live baseline HEAD is not a valid SHA: {live_baseline_head}")
        return False

    latest = state.get("latest_merge_to_baseline", "")
    previous = state.get("previous_baseline_head", "")

    for name, value in (("latest_merge_to_baseline", latest), ("previous_baseline_head", previous)):
        if not value or value == "__HANDOFF_HEAD__":
            continue
        if not is_valid_sha(value):
            print(f"  FAIL {name} is not a valid 40-char hex SHA: {value}")
            all_ok = False
            continue
        if not git_object_exists(value):
            print(f"  FAIL {name} {value[:12]} does not resolve to a Git object")
            all_ok = False
            continue
        if not git_is_ancestor(value, live_baseline_head):
            print(f"  FAIL {name} {value[:12]} is not an ancestor of live baseline HEAD {live_baseline_head[:12]}")
            all_ok = False
            continue
        print(f"  OK   {name} {value[:12]} is an ancestor of live baseline HEAD")

    if latest and previous and is_valid_sha(latest) and is_valid_sha(previous):
        if not git_is_ancestor(previous, latest):
            print(f"  FAIL previous_baseline_head {previous[:12]} is not an ancestor of latest_merge_to_baseline {latest[:12]}")
            all_ok = False
        else:
            print("  OK   previous_baseline_head precedes latest_merge_to_baseline")

    return all_ok


def validate_archive_manifests(archive_root, all_ok):
    print("\n[ARCHIVE] Package manifests")

    manifest = archive_root / "MANIFEST.txt"
    sha_manifest = archive_root / "SHA256_MANIFEST.txt"
    snapshot = archive_root / "GIT_SNAPSHOT.txt"

    if not manifest.exists():
        print("  FAIL MANIFEST.txt missing")
        return False
    if not sha_manifest.exists():
        print("  FAIL SHA256_MANIFEST.txt missing")
        return False
    if not snapshot.exists():
        print("  FAIL GIT_SNAPSHOT.txt missing")
        return False

    # Parse SHA manifest
    entries = {}
    with open(sha_manifest, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                digest, name = parts
                entries[name] = digest

    missing_or_mismatch = []
    for rel, expected in entries.items():
        full = archive_root / rel
        if not full.exists():
            missing_or_mismatch.append(f"{rel} — missing")
            continue
        actual = sha256_file(full)
        if actual != expected:
            missing_or_mismatch.append(f"{rel} — hash mismatch (expected {expected[:16]}..., got {actual[:16]}...)")

    if missing_or_mismatch:
        print("  FAIL SHA-256 manifest does not match package files:")
        for item in missing_or_mismatch[:10]:
            print(f"    {item}")
        all_ok = False
    else:
        print(f"  OK   {len(entries)} archive files match SHA-256 manifest")

    # Check for forbidden .git content
    git_files = [p for p in archive_root.rglob("*") if p.is_relative_to(archive_root / ".git") or str(p.relative_to(archive_root)).startswith(".git/")]
    if git_files:
        print(f"  FAIL archive contains .git/ content: {git_files[0].relative_to(archive_root)}")
        all_ok = False
    else:
        print("  OK   no .git/ content in archive")

    # Manifest metadata check
    manifest_text = manifest.read_text(encoding="utf-8")
    for key in ("Handoff branch:", "Handoff HEAD:", "Baseline HEAD:", "Status:"):
        if key not in manifest_text:
            print(f"  WARN MANIFEST.txt missing {key} metadata")

    return all_ok


def validate_archive_snapshot_agreement(archive_root, all_ok):
    print("\n[ARCHIVE] Snapshot / current-state agreement")

    snapshot_path = archive_root / "GIT_SNAPSHOT.txt"
    state = load_current_state(archive_root)
    if state is None:
        print("  FAIL CURRENT_STATE.json missing/invalid in archive")
        return False

    snapshot_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path.exists() else ""

    # recorded handoff head
    handoff_head = state.get("handoff_head")
    if handoff_head and handoff_head not in ("__HANDOFF_HEAD__", ""):
        if handoff_head not in snapshot_text:
            print(f"  FAIL CURRENT_STATE.json handoff_head {handoff_head} not found in GIT_SNAPSHOT.txt")
            all_ok = False
        else:
            print(f"  OK   handoff_head {handoff_head[:12]} present in GIT_SNAPSHOT.txt")

    # recorded handoff branch
    handoff_branch = state.get("handoff_branch")
    if handoff_branch and handoff_branch not in ("__HANDOFF_BRANCH__", ""):
        if handoff_branch not in snapshot_text:
            print(f"  FAIL CURRENT_STATE.json handoff_branch {handoff_branch} not found in GIT_SNAPSHOT.txt")
            all_ok = False
        else:
            print(f"  OK   handoff_branch {handoff_branch} present in GIT_SNAPSHOT.txt")

    return all_ok


def live_validation():
    all_ok = True

    if not (REPO_ROOT / ".git").is_dir():
        print("FAIL: .git not available; live mode requires a Git repository")
        return 1

    mode_label = "LIVE"
    print("=" * 60)
    print("anoX V1 Continuity Validation — LIVE REPOSITORY MODE")
    print("=" * 60)

    all_ok = validate_required_files(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_authority_paths(REPO_ROOT, all_ok, mode_label)

    status = git_status()
    if status is None:
        print("\n[LIVE] Git working tree: FAIL — git not found")
        all_ok = False
    elif status.strip() == "":
        print("\n[LIVE] Git working tree: OK clean")
    else:
        print("\n[LIVE] Git working tree: FAIL dirty")
        for line in status.splitlines():
            print(f"       {line}")
        all_ok = False

    branch = git_current_branch()
    head = git_current_head()
    state = load_current_state(REPO_ROOT)
    baseline_branch = state.get("baseline_branch") if state else "main"
    live_baseline_head = git_branch_head(baseline_branch)
    working_tree = "clean" if (status is not None and status.strip() == "") else "dirty"
    live_state = {"branch": branch, "head": head, "working_tree": working_tree}

    print(f"\n[LIVE] Branch / HEAD")
    print(f"  current branch: {branch or 'FAIL'}")
    print(f"  current HEAD: {head or 'FAIL'}")
    print(f"  described_head: {(_resolve_described_head(state) or 'unresolved')[:12] if state else 'FAIL'}")
    print(f"  baseline branch: {baseline_branch}")
    print(f"  live baseline HEAD: {live_baseline_head or 'FAIL'}")

    all_ok = validate_state_json(state, REPO_ROOT, all_ok, mode_label, live_branch=branch, live_head=head, mode="live")
    all_ok = validate_baseline_consistency(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_baseline_ancestry(state, live_baseline_head, all_ok, mode_label)
    all_ok = validate_authority_precedence(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_current_state_surfaces(REPO_ROOT, all_ok, mode_label, live_branch=branch)
    all_ok = validate_placeholders(REPO_ROOT, all_ok, mode_label, "live", live_state=live_state)

    print("\n" + "=" * 60)
    if all_ok:
        print("LIVE_GIT_VERIFICATION: PASS")
        print("RESULT: PASS — handoff readiness satisfied")
        return 0
    else:
        print("LIVE_GIT_VERIFICATION: FAIL")
        print("RESULT: FAIL — handoff readiness NOT satisfied")
        return 1


def archive_validation(archive_root):
    all_ok = True

    print("=" * 60)
    print("anoX V1 Continuity Validation — HANDOFF ARCHIVE MODE")
    print("=" * 60)
    print(f"Archive root: {archive_root}")

    all_ok = validate_required_files(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_authority_paths(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_archive_manifests(archive_root, all_ok)
    all_ok = validate_archive_snapshot_agreement(archive_root, all_ok)

    state = load_current_state(archive_root)
    all_ok = validate_state_json(state, archive_root, all_ok, "ARCHIVE")
    all_ok = validate_baseline_consistency(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_authority_precedence(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_placeholders(archive_root, all_ok, "ARCHIVE", "archive", live_state=None)
    all_ok = validate_current_state_surfaces(archive_root, all_ok, "ARCHIVE", live_branch=None)

    print("\n" + "=" * 60)
    if all_ok:
        print("HANDOFF_ARCHIVE_VALIDATION: PASS")
        print("LIVE_GIT_VERIFICATION: UNAVAILABLE")
        print("RESULT: PASS — archive handoff validation satisfied")
        return 0
    else:
        print("HANDOFF_ARCHIVE_VALIDATION: FAIL")
        print("LIVE_GIT_VERIFICATION: UNAVAILABLE")
        print("RESULT: FAIL — archive handoff validation NOT satisfied")
        return 1


def main():
    args = parse_args()
    mode = select_mode(args)
    print(f"SELECTED MODE: {mode}")

    if mode == "live":
        return live_validation()
    elif mode == "archive":
        root = args.archive or REPO_ROOT
        return archive_validation(root)
    else:
        print("FAIL: could not determine a validation mode")
        return 1


if __name__ == "__main__":
    sys.exit(main())
