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


def validate_state_json(state, root, all_ok, label, live_branch=None, live_baseline_head=None):
    print(f"\n[{label}] CURRENT_STATE.json")
    if state is None:
        print("  FAIL CURRENT_STATE.json missing or invalid JSON")
        return False

    for key in ("handoff_branch", "baseline_head", "security_invariants_path", "freeze_registry_path", "current_gate", "continuity_001_status"):
        if key not in state:
            print(f"  FAIL CURRENT_STATE.json missing key: {key}")
            all_ok = False

    if state.get("continuity_001_status") != "ACCEPTED":
        print(f"  FAIL continuity_001_status = {state.get('continuity_001_status')} (expected ACCEPTED)")
        all_ok = False
    else:
        print("  OK   continuity_001_status = ACCEPTED")

    if live_baseline_head is not None:
        recorded_baseline = state.get("baseline_head")
        if recorded_baseline and recorded_baseline != live_baseline_head:
            print(f"  FAIL BASELINE DRIFT: CURRENT_STATE.json baseline_head {recorded_baseline} != live {live_baseline_head}")
            all_ok = False
        elif recorded_baseline:
            print(f"  OK   CURRENT_STATE.json baseline_head matches live {live_baseline_head[:12]}")

    if live_branch is not None:
        expected_branch = state.get("handoff_branch")
        if expected_branch != live_branch:
            print(f"  FAIL CURRENT_STATE.json handoff_branch {expected_branch} != live branch {live_branch}")
            all_ok = False
        else:
            print(f"  OK   handoff_branch matches live {live_branch}")

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


def validate_baseline_consistency(root, all_ok, label):
    print(f"\n[{label}] Baseline current-state consistency")

    handoff_path = root / "docs/continuity/CURRENT_HANDOFF.md"
    git_state_path = root / "docs/continuity/CURRENT_GIT_STATE.md"
    state = load_current_state(root)

    if state is None:
        print("  FAIL CURRENT_STATE.json missing/invalid")
        return False

    declared_baseline = state.get("baseline_head")

    for path in (handoff_path, git_state_path):
        if not path.exists():
            print(f"  FAIL {path.name} missing")
            all_ok = False
            continue
        text = path.read_text(encoding="utf-8")
        # accept either "Current baseline HEAD" or "Merged baseline HEAD"
        m = re.search(r"(?:Current|Merged)\s+baseline\s+HEAD:\s*`?([^`\n]+)`?", text, re.MULTILINE)
        if m and declared_baseline:
            doc_baseline = m.group(1).strip()
            if doc_baseline != declared_baseline:
                print(f"  FAIL {path.name} baseline {doc_baseline} != CURRENT_STATE.json {declared_baseline}")
                all_ok = False
            else:
                print(f"  OK   {path.name} baseline matches CURRENT_STATE.json")

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
    for key in ("HEAD:", "Branch:", "Status:"):
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

    print(f"\n[LIVE] Branch / HEAD")
    print(f"  current branch: {branch or 'FAIL'}")
    print(f"  current HEAD: {head or 'FAIL'}")
    print(f"  baseline branch: {baseline_branch}")
    print(f"  live baseline HEAD: {live_baseline_head or 'FAIL'}")

    all_ok = validate_state_json(state, REPO_ROOT, all_ok, mode_label, live_branch=branch, live_baseline_head=live_baseline_head)
    all_ok = validate_baseline_consistency(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_current_state_surfaces(REPO_ROOT, all_ok, mode_label, live_branch=branch)

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
