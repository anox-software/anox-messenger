#!/usr/bin/env python3
"""Validate anoX continuity / handoff readiness."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "PROJECT_STATE.md",
    "FORTSCHRITT.md",
    "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
    "docs/authority/AUTHORITY_INDEX.md",
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
    "security_invariants": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",
    "b026": "docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md",
    "freeze_registry": "docs/authority/B_FREEZE_REGISTRY.md",
    "ultimate_main": "docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md",
}

PLACEHOLDER_MARKERS = ("__HANDOFF_HEAD__", "__WORKING_TREE__")


def run_git(args):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        return None, None, -1


def git_status():
    out, _, code = run_git(["status", "--short"])
    if code != 0 or out is None:
        return None
    return out


def git_current_branch():
    out, _, code = run_git(["branch", "--show-current"])
    if code != 0 or out is None:
        return None
    return out


def git_current_head():
    out, _, code = run_git(["rev-parse", "HEAD"])
    if code != 0 or out is None:
        return None
    return out


def load_current_state():
    path = REPO_ROOT / "docs/continuity/CURRENT_STATE.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def is_current_section_project_state(content):
    """Return True for lines in the initial/current-state portion of PROJECT_STATE.md."""
    # We consider the whole file for unresolved placeholder scan.
    return content


def main():
    all_ok = True

    print("=" * 60)
    print("anoX V1 Continuity Validation")
    print("=" * 60)

    # 1. Required files
    print("\n[1/7] Required files")
    for rel in REQUIRED_FILES:
        path = REPO_ROOT / rel
        if path.exists():
            print(f"  OK   {rel}")
        else:
            print(f"  FAIL {rel} — missing")
            all_ok = False

    # 2. CURRENT_STATE.json
    print("\n[2/7] CURRENT_STATE.json")
    state = load_current_state()
    if state is None:
        print("  FAIL CURRENT_STATE.json missing or invalid JSON")
        all_ok = False
    else:
        for key in ("handoff_branch", "baseline_head", "security_invariants_path", "freeze_registry_path", "current_gate", "continuity_001_status"):
            if key not in state:
                print(f"  FAIL CURRENT_STATE.json missing key: {key}")
                all_ok = False

        if state.get("continuity_001_status") != "ACCEPTED":
            print(f"  FAIL continuity_001_status = {state.get('continuity_001_status')} (expected ACCEPTED)")
            all_ok = False
        else:
            print("  OK   continuity_001_status = ACCEPTED")

    # 3. Git working tree
    print("\n[3/7] Git working tree")
    status = git_status()
    if status is None:
        print("  FAIL git not found or not a repo")
        all_ok = False
    elif status.strip() == "":
        print("  OK   working tree is clean")
    else:
        print("  FAIL working tree is dirty:")
        for line in status.splitlines():
            print(f"       {line}")
        all_ok = False

    # 4. Branch and HEAD consistency
    print("\n[4/7] Branch / HEAD consistency")
    branch = git_current_branch()
    head = git_current_head()
    if branch is None:
        print("  FAIL could not determine current branch")
        all_ok = False
    else:
        print(f"  OK   current branch: {branch}")

    if head is None:
        print("  FAIL could not determine current HEAD")
        all_ok = False
    else:
        print(f"  OK   current HEAD: {head[:12]}")

    if state is not None:
        expected_branch = state.get("handoff_branch")
        if branch != expected_branch:
            print(f"  FAIL CURRENT_STATE.json handoff_branch {expected_branch} != live branch {branch}")
            all_ok = False
        else:
            print(f"  OK   handoff_branch matches")

    # 5. Authority paths
    print("\n[5/7] Authority paths")
    for name, rel in REQUIRED_AUTHORITY_PATHS.items():
        path = REPO_ROOT / rel
        if path.exists():
            print(f"  OK   {name}: {rel}")
        else:
            print(f"  FAIL {name}: {rel} — missing")
            all_ok = False

    if state is not None:
        declared = state.get("security_invariants_path")
        if declared and not (REPO_ROOT / declared).exists():
            print(f"  FAIL CURRENT_STATE.json security_invariants_path missing: {declared}")
            all_ok = False

    # 6. Current gate consistency
    print("\n[6/7] Current gate consistency")
    if state is not None:
        gate = state.get("current_gate", "")
        next_task_path = REPO_ROOT / "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md"
        if next_task_path.exists():
            content = next_task_path.read_text(encoding="utf-8")
            if gate in content:
                print(f"  OK   current_gate '{gate}' found in CURRENT_NEXT_DEVIN_TASK.md")
            else:
                print(f"  FAIL current_gate '{gate}' NOT found in CURRENT_NEXT_DEVIN_TASK.md")
                all_ok = False
        else:
            print("  FAIL CURRENT_NEXT_DEVIN_TASK.md missing")
            all_ok = False

    # 7. Current-state surface checks
    print("\n[7/7] Current-state surface consistency")

    # 7a. PROJECT_STATE.md must not contain unresolved runtime placeholders
    project_state_path = REPO_ROOT / "PROJECT_STATE.md"
    project_state_text = project_state_path.read_text(encoding="utf-8") if project_state_path.exists() else ""
    for marker in PLACEHOLDER_MARKERS:
        if marker in project_state_text:
            print(f"  FAIL PROJECT_STATE.md contains unresolved placeholder: {marker}")
            all_ok = False

    # 7b. PROJECT_STATE.md current branch line must match live branch
    m = re.search(r"^[-*]\s*Branch:\s*`?([^`\n]+)`?", project_state_text, re.MULTILINE)
    if m:
        declared_branch = m.group(1).strip()
        if declared_branch != branch:
            print(f"  FAIL PROJECT_STATE.md declares branch {declared_branch} but live branch is {branch}")
            all_ok = False
        else:
            print(f"  OK   PROJECT_STATE.md branch = {declared_branch}")
    else:
        print("  WARN PROJECT_STATE.md branch line not found")

    # 7c. PROJECT_STATE.md must not claim the current work branch is the old PR branch
    if re.search(r"Current work branch:\s*`?governance/continuity-001`?", project_state_text):
        print("  FAIL PROJECT_STATE.md still claims current work branch is governance/continuity-001")
        all_ok = False

    # 7d. FORTSCHRITT.md must not contain unresolved placeholders
    fortschritt_path = REPO_ROOT / "FORTSCHRITT.md"
    fortschritt_text = fortschritt_path.read_text(encoding="utf-8") if fortschritt_path.exists() else ""
    for marker in PLACEHOLDER_MARKERS:
        if marker in fortschritt_text:
            print(f"  FAIL FORTSCHRITT.md contains unresolved placeholder: {marker}")
            all_ok = False

    # 7e. CURRENT_HANDOFF.md branch must match live
    handoff_path = REPO_ROOT / "docs/continuity/CURRENT_HANDOFF.md"
    handoff_text = handoff_path.read_text(encoding="utf-8") if handoff_path.exists() else ""
    m = re.search(r"- Current handoff branch:\s*`?([^`\n]+)`?", handoff_text, re.MULTILINE)
    if m:
        declared = m.group(1).strip()
        if declared != branch:
            print(f"  FAIL CURRENT_HANDOFF.md handoff branch {declared} != live {branch}")
            all_ok = False
        else:
            print(f"  OK   CURRENT_HANDOFF.md handoff branch = {declared}")

    print("\n" + "=" * 60)
    if all_ok:
        print("RESULT: PASS — handoff readiness satisfied")
        return 0
    else:
        print("RESULT: FAIL — handoff readiness NOT satisfied")
        return 1


if __name__ == "__main__":
    sys.exit(main())
