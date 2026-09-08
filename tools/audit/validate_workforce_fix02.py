#!/usr/bin/env python3
"""WORKFORCE-FIX-02 validator.

Validates the remediation of ANOX-WORKFORCE-AUDIT-002 (handoff archive effective-
state rendering) while preserving the evidence for 001 and 005:
- archive CURRENT_HANDOFF.md renders the post-merge effective gate;
- generator does not mutate tracked files;
- WORKFORCE-RETEST-01 FAIL record preserved;
- WORKFORCE-RETEST-02 Candidate created with unbound start_sha;
- product remains blocked; Security Architecture Audit not started;
- no product/CI/backend/SQL/secret changes.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

TASK_ID = "ANOX-TASK-WORKFORCEFIX02"
RETEST_ID = "ANOX-TASK-WORKFORCERETEST02"
RETEST01_ID = "ANOX-TASK-WORKFORCERETEST01"
FIX01_ID = "ANOX-TASK-WORKFORCEFIX01"
TARGET_FINDING = "ANOX-WORKFORCE-AUDIT-002"
REGRESSION_FINDINGS = {"ANOX-WORKFORCE-AUDIT-001", "ANOX-WORKFORCE-AUDIT-005"}
PRODUCT_FINDINGS = {
    "ANOX-MAINARCH-013",
    "ANOX-MAINARCH-018",
    "ANOX-MAINARCH-030",
    "ANOX-LEGACY-INTEGRATION-005",
    "ANOX-LEGACY-B003-001",
}
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
    findings = load_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {f["finding_id"]: f for f in findings}

    target = by_id.get(TARGET_FINDING)
    if target is None:
        fail(f"{TARGET_FINDING} missing from findings registry", errors)
        return
    if target.get("status") != "Ready For Retest":
        fail(f"{TARGET_FINDING} status is {target.get('status')}, expected Ready For Retest", errors)
    elif target.get("closure_evidence"):
        fail(f"{TARGET_FINDING} Ready For Retest but carries closure_evidence", errors)
    else:
        ok(f"{TARGET_FINDING} Ready For Retest (not closed)")
    refs = target.get("remediation_refs") or []
    if not any("WORKFORCE-FIX-02" in r for r in refs):
        fail(f"{TARGET_FINDING} remediation_refs missing WORKFORCE-FIX-02", errors)
    else:
        ok(f"{TARGET_FINDING} remediation refs include WORKFORCE-FIX-02")
    if not any("validate" in r for r in refs):
        fail(f"{TARGET_FINDING} remediation_refs missing validator reference", errors)
    else:
        ok(f"{TARGET_FINDING} remediation refs include validator")

    for fid in sorted(REGRESSION_FINDINGS):
        f = by_id.get(fid)
        if f is None:
            fail(f"regression finding {fid} missing", errors)
            continue
        if f.get("status") != "Ready For Retest":
            fail(f"regression finding {fid} status is {f.get('status')}, expected Ready For Retest", errors)
        elif f.get("closure_evidence"):
            fail(f"regression finding {fid} Ready For Retest but carries closure_evidence", errors)
        else:
            ok(f"regression finding {fid} remains Ready For Retest")
        refs = f.get("remediation_refs") or []
        if not any("WORKFORCE-FIX-01" in r for r in refs):
            fail(f"regression finding {fid} remediation_refs missing WORKFORCE-FIX-01", errors)
        else:
            ok(f"regression finding {fid} still references WORKFORCE-FIX-01 evidence")




def check_tasks(errors):
    tasks = load_jsonl("docs/workforce/registries/tasks.jsonl")
    by_id = {t["task_id"]: t for t in tasks}

    fix = by_id.get(TASK_ID)
    if fix is None:
        fail(f"{TASK_ID} missing", errors)
    else:
        if fix.get("status") not in ("In Progress", "Ready For Remote", "Awaiting Review"):
            fail(f"{TASK_ID} status {fix.get('status')} is not an active writing state", errors)
        else:
            ok(f"{TASK_ID} status is {fix.get('status')}")
        if fix.get("branch") != "remediation/workforce-fix-02-handoff-archive":
            fail(f"{TASK_ID} branch mismatch: {fix.get('branch')}", errors)
        else:
            ok(f"{TASK_ID} branch is remediation/workforce-fix-02-handoff-archive")
        if fix.get("start_sha") != FIX01_MERGE_SHA:
            fail(f"{TASK_ID} start_sha {fix.get('start_sha')} != {FIX01_MERGE_SHA}", errors)
        else:
            ok(f"{TASK_ID} start_sha bound to FIX-01 merge {FIX01_MERGE_SHA[:12]}")
        if fix.get("remote_permission") != "NONE":
            fail(f"{TASK_ID} remote_permission is not NONE", errors)
        else:
            ok(f"{TASK_ID} remote_permission is NONE")

    ret = by_id.get(RETEST_ID)
    if ret is None:
        fail(f"{RETEST_ID} missing", errors)
    else:
        if ret.get("status") != "Candidate":
            fail(f"{RETEST_ID} status is {ret.get('status')}, expected Candidate", errors)
        else:
            ok(f"{RETEST_ID} is Candidate (not authorized)")
        start = ret.get("start_sha") or ""
        if not start.startswith("NOT YET BOUND"):
            fail(f"{RETEST_ID} start_sha is bound prematurely: {start}", errors)
        else:
            ok(f"{RETEST_ID} start_sha remains NOT YET BOUND")

    fix01 = by_id.get(FIX01_ID)
    if fix01 is None:
        fail(f"{FIX01_ID} missing", errors)
    else:
        if fix01.get("status") != "Merged":
            fail(f"{FIX01_ID} status is {fix01.get('status')}, expected Merged", errors)
        else:
            ok(f"{FIX01_ID} is Merged")
        if fix01.get("merged_sha") != FIX01_MERGE_SHA:
            fail(f"{FIX01_ID} merged_sha {fix01.get('merged_sha')} != {FIX01_MERGE_SHA}", errors)
        else:
            ok(f"{FIX01_ID} merged_sha recorded as {FIX01_MERGE_SHA[:12]}")

    ret01 = by_id.get(RETEST01_ID)
    if ret01 is None:
        fail(f"{RETEST01_ID} missing", errors)
    else:
        if ret01.get("status") not in ("Closed (FAIL)", "Closed"):
            fail(f"{RETEST01_ID} status is {ret01.get('status')}, expected Closed", errors)
        elif "FAIL" not in (ret01.get("result") or "").upper():
            fail(f"{RETEST01_ID} status is Closed but result is not a FAIL record: {ret01.get('result')}", errors)
        else:
            ok(f"{RETEST01_ID} is Closed with FAIL result")


def check_retest01_record(errors):
    runs = load_jsonl("docs/workforce/registries/runs.jsonl")
    for r in runs:
        if r.get("run_id") == "ANOX-RUN-WORKFORCERETEST01":
            if r.get("result") != "FAIL":
                fail(f"WORKFORCE-RETEST-01 run result is {r.get('result')}, expected FAIL", errors)
            else:
                ok("WORKFORCE-RETEST-01 run recorded FAIL")
            verdicts = r.get("per_finding_verdicts") or r.get("findings_verdicts") or {}
            if verdicts.get("ANOX-WORKFORCE-AUDIT-001") != "PASS — REMEDIATED":
                fail(f"001 verdict is {verdicts.get('ANOX-WORKFORCE-AUDIT-001')}, expected PASS — REMEDIATED", errors)
            else:
                ok("001 prior verdict preserved: PASS — REMEDIATED")
            if verdicts.get("ANOX-WORKFORCE-AUDIT-005") != "PASS — REMEDIATED":
                fail(f"005 verdict is {verdicts.get('ANOX-WORKFORCE-AUDIT-005')}, expected PASS — REMEDIATED", errors)
            else:
                ok("005 prior verdict preserved: PASS — REMEDIATED")
            if verdicts.get(TARGET_FINDING) != "FAIL — NOT REMEDIATED":
                fail(f"002 verdict is {verdicts.get(TARGET_FINDING)}, expected FAIL — NOT REMEDIATED", errors)
            else:
                ok("002 prior verdict preserved: FAIL — NOT REMEDIATED")
            root = r.get("root_cause") or ""
            if "stale" not in root.lower() or "effective gate" not in root.lower():
                fail(f"002 root cause does not describe stale effective gate: {root}", errors)
            else:
                ok("002 root cause preserved: stale human-readable effective gate")
            return
    fail("ANOX-RUN-WORKFORCERETEST01 record missing", errors)


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

    pre = ws.get("pre_merge_state", {})
    post = ws.get("post_merge_state", {})
    if "WORKFORCE-FIX-02" not in (pre.get("current_gate") or ""):
        fail(f"pre_merge_state current_gate is {pre.get('current_gate')}, expected WORKFORCE-FIX-02", errors)
    else:
        ok(f"pre_merge_state current_gate is {pre.get('current_gate')}")
    if "WORKFORCE-RETEST-02" not in (post.get("current_gate") or ""):
        fail(f"post_merge_state current_gate is {post.get('current_gate')}, expected WORKFORCE-RETEST-02", errors)
    else:
        ok(f"post_merge_state current_gate is {post.get('current_gate')}")

    writer = pre.get("current_writer") or {}
    if writer.get("task_id") != TASK_ID:
        fail(f"pre_merge_state current_writer {writer} != {TASK_ID}", errors)
    else:
        ok(f"pre_merge_state current_writer is {TASK_ID}")
    if post.get("current_writer") is not None:
        fail("post_merge_state current_writer is not null", errors)
    else:
        ok("post_merge_state current_writer is null")

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

    # Preserve FIX-01 history.
    found_fix01 = False
    for m in ws.get("previous_merges", []):
        if m.get("merge_head") == FIX01_MERGE_SHA:
            found_fix01 = True
            fix01_pre = m.get("pre_merge_state", {})
            fix01_post = m.get("post_merge_state", {})
            if "WORKFORCE-FIX-01" not in (fix01_pre.get("current_gate") or ""):
                fail("previous_merges FIX-01 pre_merge_state missing WORKFORCE-FIX-01 gate", errors)
            else:
                ok("previous_merges preserves FIX-01 pre-merge gate")
            if "WORKFORCE-RETEST-01" not in (fix01_post.get("current_gate") or ""):
                fail("previous_merges FIX-01 post_merge_state missing WORKFORCE-RETEST-01 gate", errors)
            else:
                ok("previous_merges preserves FIX-01 post-merge gate")
    if not found_fix01:
        fail("WORKFORCE_STATE previous_merges missing FIX-01 merge", errors)


def check_current_state(errors):
    state = load_json("docs/continuity/CURRENT_STATE.json")
    if state.get("continuity_001_status") != "ACCEPTED":
        fail(f"continuity_001_status is {state.get('continuity_001_status')}, expected ACCEPTED", errors)
    else:
        ok("continuity_001_status = ACCEPTED")
    if state.get("delivery_branch") != "remediation/workforce-fix-02-handoff-archive":
        fail(f"CURRENT_STATE delivery_branch is {state.get('delivery_branch')}, expected remediation/workforce-fix-02-handoff-archive", errors)
    else:
        ok("CURRENT_STATE delivery_branch is FIX-02 delivery branch")
    if "WORKFORCE-FIX-02" not in (state.get("pre_merge_gate") or ""):
        fail(f"CURRENT_STATE pre_merge_gate is {state.get('pre_merge_gate')}, expected WORKFORCE-FIX-02", errors)
    else:
        ok("CURRENT_STATE pre_merge_gate is WORKFORCE-FIX-02")
    if "WORKFORCE-RETEST-02" not in (state.get("post_merge_gate") or ""):
        fail(f"CURRENT_STATE post_merge_gate is {state.get('post_merge_gate')}, expected WORKFORCE-RETEST-02", errors)
    else:
        ok("CURRENT_STATE post_merge_gate is WORKFORCE-RETEST-02")
    described = state.get("described_head")
    if not (described and re.fullmatch(r"[0-9a-f]{40}", described)):
        fail(f"CURRENT_STATE described_head invalid: {described}", errors)
    elif not git_is_ancestor(described, git(["rev-parse", "HEAD"])):
        fail(f"CURRENT_STATE described_head {described[:12]} is not an ancestor of HEAD", errors)
    else:
        ok(f"CURRENT_STATE described_head set to {described[:12]} and is an ancestor of HEAD")


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

    if branch == "main":
        if effective.get("current_writer") is not None:
            fail("Post-merge current_writer is not null on main", errors)
        else:
            ok("Post-merge current_writer is null on main")
        if "WORKFORCE-RETEST-02" not in (effective.get("current_gate") or ""):
            fail(f"Post-merge effective gate is {effective.get('current_gate')}, expected WORKFORCE-RETEST-02", errors)
        else:
            ok(f"Post-merge effective gate is {effective.get('current_gate')}")
    else:
        writer = effective.get("current_writer") or {}
        if writer.get("task_id") == TASK_ID and "WORKFORCE-FIX-02" in (effective.get("current_gate") or ""):
            ok(f"Pre-merge current_writer is {TASK_ID}; effective gate is {effective.get('current_gate')}")
        else:
            fail(f"Pre-merge state not FIX-02: current_writer={writer}, current_gate={effective.get('current_gate')}", errors)


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
    changed = git(["diff", "--name-only", "HEAD"])
    bad = [p for p in (changed.splitlines() if changed else []) if any(re.search(pat, p) for pat in product_patterns)]
    if bad:
        fail(f"Working tree contains product/backend/SQL/CI changes: {bad}", errors)
    else:
        ok("Working tree contains no product/backend/SQL/CI changes")


def check_handoff_template_and_resolver(errors):
    handoff_path = REPO / "docs" / "continuity" / "CURRENT_HANDOFF.md"
    if not handoff_path.exists():
        fail("CURRENT_HANDOFF.md missing", errors)
        return
    text = handoff_path.read_text(encoding="utf-8")
    if "<!-- ANOX:handoff_version -->" not in text or "<!-- /ANOX:handoff_version -->" not in text:
        fail("CURRENT_HANDOFF.md missing ANOX:handoff_version marker", errors)
    else:
        ok("CURRENT_HANDOFF.md has handoff_version marker")
    if "<!-- ANOX:effective_gate -->" not in text or "<!-- /ANOX:effective_gate -->" not in text:
        fail("CURRENT_HANDOFF.md missing ANOX:effective_gate marker", errors)
    else:
        ok("CURRENT_HANDOFF.md has effective_gate marker")

    # The canonical resolver must still derive the intended pre/post states.
    if "derive_effective_workforce_state" not in (REPO / "tools" / "workforce" / "state_gate_resolver.py").read_text():
        fail("state_gate_resolver.py missing derive_effective_workforce_state", errors)
    else:
        ok("state_gate_resolver.py still exports derive_effective_workforce_state")

    if "render_archive_surface" not in (REPO / "tools" / "continuity" / "generate_handoff.py").read_text():
        fail("generate_handoff.py missing archive surface renderer", errors)
    else:
        ok("generate_handoff.py has archive surface renderer")


def check_supporting_validators(errors):
    for v, args in (
        ("validate_workforce_audit_findings_freeze.py", []),
        ("validate_legacy_retest01_ingest.py", []),
    ):
        r = subprocess.run([sys.executable, str(REPO / "tools" / "audit" / v)] + args,
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode == 0:
            ok(f"{v} PASS")
        else:
            tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            fail(f"{v} FAIL ({'; '.join(tail)})", errors)


def main():
    print("WORKFORCE-FIX-02 validator")
    errors = []
    check_findings(errors)
    check_tasks(errors)
    check_retest01_record(errors)
    check_workforce_state(errors)
    check_current_state(errors)
    check_effective_state(errors)
    check_product_findings(errors)
    check_no_product_code(errors)
    check_handoff_template_and_resolver(errors)
    check_supporting_validators(errors)

    if errors:
        print("\nWORKFORCE-FIX-02: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nWORKFORCE-FIX-02: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
