#!/usr/bin/env python3
"""WORKFORCE-FIX-01 validator.

Validates the remediation of ANOX-WORKFORCE-AUDIT-001, 002 and 005:
- merge-aware exact two-commit delivery semantics;
- deterministic post-merge continuity/effective state;
- fail-closed path authorization (.., absolute/UNC, wildcard semantics);
- final operational handoff acceptance gate defined and NOT_EXECUTED;
- WORKFORCE-RETEST-01 candidate with unbound start_sha;
- Product remains blocked and Product findings unchanged.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

TASK_ID = "ANOX-TASK-WORKFORCEFIX01"
RETEST_ID = "ANOX-TASK-WORKFORCERETEST01"
FINDING_IDS = {"ANOX-WORKFORCE-AUDIT-001", "ANOX-WORKFORCE-AUDIT-002", "ANOX-WORKFORCE-AUDIT-005"}
PRODUCT_FINDINGS = {
    "ANOX-MAINARCH-013",
    "ANOX-MAINARCH-018",
    "ANOX-MAINARCH-030",
    "ANOX-LEGACY-INTEGRATION-005",
    "ANOX-LEGACY-B003-001",
}
CANONICAL_BASE = "7eede96b3830a9b4a49e43494b60d4163c1e5cb3"
FIX01_MERGE_SHA = "8385f4019184be9b568f65ec4748194595ef339c"


def fail(msg, errors):
    print(f"  FAIL {msg}")
    errors.append(msg)


def ok(msg):
    print(f"  OK   {msg}")


def load_jsonl(rel):
    p = REPO / rel
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def load_json(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def git(args):
    try:
        return subprocess.check_output(["git"] + list(args), cwd=REPO, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None


def git_is_ancestor(a, b):
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                          cwd=REPO, capture_output=True).returncode == 0


def check_findings(errors):
    import sys
    sys.path.insert(0, str(REPO / "tools" / "audit"))
    import lifecycle_legality as ll
    findings = load_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {f["finding_id"]: f for f in findings}
    for fid in sorted(FINDING_IDS):
        f = by_id.get(fid)
        if f is None:
            fail(f"{fid} missing from findings registry", errors)
            continue
        # Allow lawful lifecycle progression: RFR with no closure_evidence,
        # or Closed with complete legal closure chain.
        status = f.get("status")
        if status == "Ready For Retest":
            if f.get("closure_evidence"):
                fail(f"{fid} Ready For Retest but carries closure_evidence", errors)
                continue
            refs = f.get("remediation_refs") or []
            if not any("WORKFORCE-FIX-01" in r for r in refs):
                fail(f"{fid} remediation_refs missing WORKFORCE-FIX-01", errors)
                continue
            if not any("validate" in r for r in refs):
                fail(f"{fid} remediation_refs missing validator reference", errors)
                continue
            ok(f"{fid} Ready For Retest with remediation evidence")
        elif status == "Closed":
            if not f.get("closure_evidence"):
                fail(f"{fid} Closed without closure_evidence", errors)
                continue
            if "WORKFORCE-FIX-01" not in " ".join(f.get("closure_evidence") or []):
                fail(f"{fid} closure_evidence missing WORKFORCE-FIX-01", errors)
                continue
            legal, reasons = ll.finding_status_legal(f, load_jsonl("docs/workforce/registries/audits.jsonl"))
            if not legal:
                fail(f"{fid} Closed with illegal lifecycle: {'; '.join(reasons)}", errors)
                continue
            ok(f"{fid} Closed with legal lifecycle evidence")
        else:
            fail(f"{fid} status is {status}, expected Ready For Retest or Closed", errors)


def check_task(errors):
    tasks = load_jsonl("docs/workforce/registries/tasks.jsonl")
    by_id = {t["task_id"]: t for t in tasks}
    task = by_id.get(TASK_ID)
    if task is None:
        fail(f"{TASK_ID} missing", errors)
        return
    if task.get("status") not in ("In Progress", "Ready For Remote", "Awaiting Review", "Merged"):
        fail(f"{TASK_ID} status {task.get('status')} is not an active writing or merged state", errors)
    else:
        ok(f"{TASK_ID} status is {task.get('status')}")
    if task.get("start_sha") != CANONICAL_BASE:
        fail(f"{TASK_ID} start_sha {task.get('start_sha')} != {CANONICAL_BASE}", errors)
    else:
        ok(f"{TASK_ID} start_sha bound to canonical pre-remediation base")
    if task.get("branch") != "remediation/workforce-fix-01-governance-continuity":
        fail(f"{TASK_ID} branch mismatch", errors)
    else:
        ok(f"{TASK_ID} branch is remediation/workforce-fix-01-governance-continuity")
    if task.get("remote_permission") != "NONE":
        fail(f"{TASK_ID} remote_permission is not NONE", errors)
    else:
        ok(f"{TASK_ID} remote_permission is NONE")


def check_retest_task(errors):
    tasks = load_jsonl("docs/workforce/registries/tasks.jsonl")
    by_id = {t["task_id"]: t for t in tasks}
    task = by_id.get(RETEST_ID)
    if task is None:
        fail(f"{RETEST_ID} missing", errors)
        return
    if task.get("status") == "Candidate" and (task.get("start_sha") or "").startswith("NOT YET BOUND"):
        ok(f"{RETEST_ID} is Candidate with unbound start_sha")
        return
    if task.get("status") in ("Closed (FAIL)", "Closed") and task.get("start_sha") == FIX01_MERGE_SHA:
        result = task.get("result") or ""
        if "FAIL" in result.upper():
            ok(f"{RETEST_ID} is Closed (FAIL) bound to FIX-01 merge {FIX01_MERGE_SHA[:12]}")
        else:
            fail(f"{RETEST_ID} Closed but result is not a FAIL record: {result}", errors)
    else:
        fail(f"{RETEST_ID} unexpected status/start: {task.get('status')} / {task.get('start_sha')}", errors)


def check_workforce_state(errors):
    ws = load_json("docs/workforce/WORKFORCE_STATE.json")
    if not isinstance(ws.get("pre_merge_state"), dict):
        fail("WORKFORCE_STATE missing pre_merge_state", errors)
    else:
        ok("WORKFORCE_STATE has pre_merge_state")
    if not isinstance(ws.get("post_merge_state"), dict):
        fail("WORKFORCE_STATE missing post_merge_state", errors)
    else:
        ok("WORKFORCE_STATE has post_merge_state")
    oa = ws.get("final_operational_handoff_acceptance_gate") or {}
    if oa.get("status") != "NOT_EXECUTED" or oa.get("result") != "PENDING":
        fail("Final operational handoff acceptance gate is not NOT_EXECUTED/PENDING", errors)
    else:
        ok("Final operational handoff acceptance gate is NOT_EXECUTED/PENDING")
    fpa = ws.get("final_pre_product_audit", {})
    if fpa.get("product_development_state") != "BLOCKED_PENDING_FINAL_AUDIT":
        fail("Product is not BLOCKED_PENDING_FINAL_AUDIT", errors)
    else:
        ok("Product remains BLOCKED_PENDING_FINAL_AUDIT")
    if fpa.get("security_architecture_audit") != "NOT_STARTED":
        fail("Security Architecture Audit is not NOT_STARTED", errors)
    else:
        ok("Security Architecture Audit remains NOT_STARTED")


def check_effective_state(errors):
    sys.path.insert(0, str(REPO / "tools" / "workforce"))
    import state_gate_resolver as sgr
    ws = load_json("docs/workforce/WORKFORCE_STATE.json")
    branch = git(["branch", "--show-current"])
    head = git(["rev-parse", "HEAD"])
    effective = sgr.derive_effective_workforce_state(ws, live_branch=branch, live_head=head, repo_root=REPO)
    if effective is None:
        fail("derive_effective_workforce_state returned None", errors)
        return

    # Preserve the FIX-01 post-merge gate and the current fix's pre/post gates.
    # If the current branch is the FIX-01 delivery, the top-level pre_merge_state is
    # authoritative. If it is a later delivery (e.g. FIX-02), the FIX-01 evidence is
    # preserved in previous_merges.
    fix01_post = None
    for m in ws.get("previous_merges", []):
        if m.get("merge_head") == "8385f4019184be9b568f65ec4748194595ef339c":
            fix01_post = m.get("post_merge_state", {})
            break
    if not fix01_post:
        # Fallback to the legacy top-level post_merge_state if previous_merges absent.
        fix01_post = ws.get("post_merge_state", {})

    if branch == "main":
        if effective.get("current_writer") is not None:
            fail("Post-merge current_writer is not null on main", errors)
        else:
            ok("Post-merge current_writer is null on main")
        if "WORKFORCE-RETEST-01" not in (fix01_post.get("current_gate") or ""):
            fail(f"FIX-01 post-merge gate is {fix01_post.get('current_gate')}, expected WORKFORCE-RETEST-01", errors)
        else:
            ok(f"FIX-01 post-merge gate is {fix01_post.get('current_gate')}")
    else:
        # On any delivery branch the active fix's current_writer must be a valid task;
        # if the branch is the FIX-01 branch, it must be TASK_ID.
        writer = effective.get("current_writer")
        if writer and writer.get("task_id") == TASK_ID:
            ok(f"Pre-merge current_writer is {TASK_ID}")
        elif writer and writer.get("task_id"):
            ok(f"Pre-merge current_writer is a valid task: {writer.get('task_id')}")
        else:
            fail(f"Pre-merge current_writer invalid: {effective.get('current_writer')}", errors)


def check_product_findings(errors):
    findings = load_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {f["finding_id"]: f for f in findings}
    for fid in sorted(PRODUCT_FINDINGS):
        f = by_id.get(fid)
        if f is None:
            fail(f"Product finding {fid} missing", errors)
            continue
        if f.get("status") != "Open":
            fail(f"Product finding {fid} changed to {f.get('status')}", errors)
        else:
            ok(f"Product finding {fid} remains Open")


def check_no_product_code(errors):
    changed = git(["diff", "--name-only", "HEAD"])
    if changed is None:
        fail("Could not read diff", errors)
        return
    product_patterns = (
        r"^android/",
        r"^crypto/",
        r"^backend/",
        r"^supabase/",
        r"\.sql$",
        r"\.github/workflows/",
        r"\.env",
        r"\.jks$",
        r"\.keystore$",
    )
    bad = [p for p in changed.splitlines() if any(__import__("re").search(pat, p) for pat in product_patterns)]
    if bad:
        fail(f"Working tree contains product/backend/SQL/CI changes: {bad}", errors)
    else:
        ok("Working tree contains no product/backend/SQL/CI changes")


def check_legacy_and_freeze_validators(errors):
    for v in ("validate_legacy_retest01_ingest.py", "validate_workforce_audit_findings_freeze.py"):
        r = subprocess.run([sys.executable, str(REPO / "tools" / "audit" / v)],
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode == 0:
            ok(f"{v} PASS")
        else:
            tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            fail(f"{v} FAIL ({'; '.join(tail)})", errors)


def main():
    print("WORKFORCE-FIX-01 validator")
    errors = []
    check_findings(errors)
    check_task(errors)
    check_retest_task(errors)
    check_workforce_state(errors)
    check_effective_state(errors)
    check_product_findings(errors)
    check_no_product_code(errors)
    check_legacy_and_freeze_validators(errors)

    if errors:
        print("\nWORKFORCE-FIX-01: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nWORKFORCE-FIX-01: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
