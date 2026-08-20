#!/usr/bin/env python3
"""Validate anoX continuity / handoff readiness."""

import os
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
    "tools/continuity/generate_handoff.py",
    "tools/continuity/validate_continuity.py",
]


def git_status():
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout
    except FileNotFoundError:
        return None


def main():
    all_ok = True

    print("=" * 60)
    print("anoX V1 Continuity Validation")
    print("=" * 60)

    # 1. Required files
    print("\n[1/3] Required files")
    for rel in REQUIRED_FILES:
        path = REPO_ROOT / rel
        if path.exists():
            print(f"  OK   {rel}")
        else:
            print(f"  FAIL {rel} — missing")
            all_ok = False

    # 2. Git cleanliness
    print("\n[2/3] Git working tree")
    status = git_status()
    if status is None:
        print("  FAIL git not found in PATH")
        all_ok = False
    elif status.strip() == "":
        print("  OK   working tree is clean")
    else:
        print("  FAIL working tree is dirty:")
        for line in status.splitlines():
            print(f"       {line}")
        all_ok = False

    # 3. Architecture authority present
    print("\n[3/3] Architecture authority")
    b025 = REPO_ROOT / "docs/authority/B025"
    b026 = REPO_ROOT / "docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md"
    if b025.exists():
        print("  OK   docs/authority/B025/")
    else:
        print("  FAIL docs/authority/B025/ missing")
        all_ok = False
    if b026.exists():
        print("  OK   B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md")
    else:
        print("  FAIL B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md missing")
        all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("RESULT: PASS — handoff readiness satisfied")
        return 0
    else:
        print("RESULT: FAIL — handoff readiness NOT satisfied")
        return 1


if __name__ == "__main__":
    sys.exit(main())
