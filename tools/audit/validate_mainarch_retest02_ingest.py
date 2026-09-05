#!/usr/bin/env python3
"""MAINARCH-RETEST-02-INGEST deterministic validator.

Validates that the MAINARCH-RETEST-02 result was canonically ingested, the 8
verified FIX-02 findings are Closed with preserved severity/evidence, no
unrelated finding was closed, the 003/007 milestone security-review flags are
preserved, no immediate Claude audit was triggered, workforce/Project Memory
surfaces are synchronized, and the hardened FIX-02 validator still passes.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

RETEST_SHA = "739ea1c36c3d6f8eedb9a315fc6fba5173a82289"
ORIGINAL_AUDIT_SHA = "0a4910eab1a92622383721100879cda46f924ca0"
INGEST_EVENT_ID = "ANOX-EVENT-0032"

TARGETS = {
    "ANOX-MAINARCH-003", "ANOX-MAINARCH-007", "ANOX-MAINARCH-008", "ANOX-MAINARCH-009",
    "ANOX-MAINARCH-010", "ANOX-MAINARCH-015", "ANOX-MAINARCH-016", "ANOX-MAINARCH-017",
}

FIX01_CLOSED = {
    "ANOX-MAINARCH-001", "ANOX-MAINARCH-002", "ANOX-MAINARCH-004", "ANOX-MAINARCH-005",
    "ANOX-MAINARCH-006", "ANOX-MAINARCH-012", "ANOX-MAINARCH-014", "ANOX-MAINARCH-020",
    "ANOX-MAINARCH-021", "ANOX-MAINARCH-022", "ANOX-MAINARCH-025", "ANOX-MAINARCH-028",
    "ANOX-MAINARCH-029", "ANOX-MAINARCH-032", "ANOX-MAINARCH-033", "ANOX-MAINARCH-034",
    "ANOX-MAINARCH-035",
}

EXPECTED_REMAINING_OPEN = {
    "ANOX-MAINARCH-011", "ANOX-MAINARCH-013", "ANOX-MAINARCH-018", "ANOX-MAINARCH-019",
    "ANOX-MAINARCH-023", "ANOX-MAINARCH-024", "ANOX-MAINARCH-026", "ANOX-MAINARCH-027",
    "ANOX-MAINARCH-030", "ANOX-MAINARCH-031", "ANOX-MAINARCH-036",
}

# Findings that MAINARCH-FIX-03 may legitimately move out of "Open" into
# "Ready For Retest" (they may only become "Closed" with MAINARCH-RETEST-03
# evidence). The non-target remainder must stay "Open".
FIX03_TARGETS = {
    "ANOX-MAINARCH-011", "ANOX-MAINARCH-024", "ANOX-MAINARCH-026",
    "ANOX-MAINARCH-027", "ANOX-MAINARCH-036",
}
EXPECTED_NONFIX03_OPEN = EXPECTED_REMAINING_OPEN - FIX03_TARGETS

EXPECTED_SEVERITIES = {
    "ANOX-MAINARCH-003": "HIGH",
    "ANOX-MAINARCH-007": "HIGH",
    "ANOX-MAINARCH-008": "HIGH",
    "ANOX-MAINARCH-009": "HIGH",
    "ANOX-MAINARCH-010": "HIGH",
    "ANOX-MAINARCH-015": "MEDIUM",
    "ANOX-MAINARCH-016": "MEDIUM",
    "ANOX-MAINARCH-017": "MEDIUM",
}

MILESTONE_FLAGGED = {"ANOX-MAINARCH-003", "ANOX-MAINARCH-007"}

V1_2 = "docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md"
MASTER = "docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md"


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def read_text(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def read_jsonl(rel):
    return [json.loads(l) for l in (REPO / rel).read_text().splitlines() if l.strip()]


def main():
    print("MAINARCH-RETEST-02-INGEST validator")
    errors = []

    # --- 1-4. Retest result record ---
    audits = read_jsonl("docs/workforce/registries/audits.jsonl")
    retest = next((a for a in audits if a.get("audit_id") == "MAINARCH-RETEST-02"), None)
    if retest is None:
        fail("MAINARCH-RETEST-02 audit record missing", errors)
        retest = {}
    else:
        ok("MAINARCH-RETEST-02 audit record present")
    if retest.get("result") == "PASS":
        ok("MAINARCH-RETEST-02 result is PASS")
    else:
        fail(f"MAINARCH-RETEST-02 result is {retest.get('result')}, expected PASS", errors)
    if retest.get("canonical_sha") == RETEST_SHA and retest.get("retest_canonical_sha") == RETEST_SHA:
        ok("MAINARCH-RETEST-02 canonical/retest SHA recorded correctly")
    else:
        fail("MAINARCH-RETEST-02 canonical/retest SHA mismatch", errors)
    if set(retest.get("finding_ids", [])) == TARGETS and set(retest.get("closure_eligible_ids", [])) == TARGETS:
        ok("MAINARCH-RETEST-02 records exactly the 8 finding IDs")
    else:
        fail("MAINARCH-RETEST-02 finding_ids/closure_eligible_ids mismatch", errors)
    if retest.get("source_audit_id") == "AUDIT-MAIN-ARCHITECTURE" and retest.get("remediation_task") == "MAINARCH-FIX-02":
        ok("MAINARCH-RETEST-02 source audit and remediation task recorded")
    else:
        fail("MAINARCH-RETEST-02 source_audit_id/remediation_task missing or wrong", errors)
    if retest.get("original_audit_sha") == ORIGINAL_AUDIT_SHA and retest.get("fix_canonical_merge_sha") == RETEST_SHA:
        ok("MAINARCH-RETEST-02 original audit SHA and FIX-02 merge SHA recorded")
    else:
        fail("MAINARCH-RETEST-02 original_audit_sha/fix_canonical_merge_sha missing or wrong", errors)
    if retest.get("failed_ids") == [] and retest.get("regression_ids") == []:
        ok("MAINARCH-RETEST-02 records zero failures and zero regressions")
    else:
        fail("MAINARCH-RETEST-02 failed_ids/regression_ids not empty", errors)

    # --- 5-13. Finding transitions ---
    findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {f["finding_id"]: f for f in findings}
    finding_ids = set(by_id.keys())
    expected_ids = {f"ANOX-MAINARCH-{i:03d}" for i in range(1, 37)}
    if finding_ids == expected_ids:
        ok("All 36 ANOX-MAINARCH-001..036 IDs preserved")
    else:
        fail(f"Finding ID set mismatch: missing {expected_ids - finding_ids}, extra {finding_ids - expected_ids}", errors)

    for fid in sorted(TARGETS):
        f = by_id.get(fid, {})
        if f.get("status") != "Closed":
            fail(f"{fid} is not Closed (status={f.get('status')})", errors)
            continue
        if f.get("severity") != EXPECTED_SEVERITIES[fid]:
            fail(f"{fid} severity changed to {f.get('severity')}", errors)
            continue
        ev = f.get("closure_evidence", [])
        if not any("MAINARCH-FIX-02" in e for e in ev) or not any("MAINARCH-RETEST-02" in e for e in ev):
            fail(f"{fid} closure evidence missing FIX-02/RETEST-02 reference", errors)
            continue
        if not any("RETEST_SHA" not in e and f"git:{RETEST_SHA}" in e or f"git:{RETEST_SHA}" in e for e in ev):
            fail(f"{fid} closure evidence missing retest canonical SHA", errors)
            continue
        if not any(ORIGINAL_AUDIT_SHA in e for e in f.get("evidence_refs", [])):
            fail(f"{fid} original audit evidence reference lost", errors)
            continue
        ok(f"{fid} Closed with preserved severity, original evidence, and FIX-02/RETEST-02 closure refs")

    # A FIX-03 target may only be Closed with recorded MAINARCH-RETEST-03 PASS evidence.
    retest03_ids = set()
    for a in read_jsonl("docs/workforce/registries/audits.jsonl"):
        if a.get("audit_id") == "MAINARCH-RETEST-03" and a.get("result") == "PASS":
            if a.get("finding_id"):
                retest03_ids.add(a["finding_id"])
            for fid in (a.get("findings") or a.get("closed_findings") or []):
                retest03_ids.add(fid)

    still_rfr = [f["finding_id"] for f in findings if f.get("status") == "Ready For Retest"]
    bad_rfr = [fid for fid in still_rfr if fid not in FIX03_TARGETS]
    if not bad_rfr:
        if still_rfr:
            ok(f"Ready For Retest set is limited to FIX-03 targets: {sorted(still_rfr)}")
        else:
            ok("No finding remains Ready For Retest")
    else:
        fail(f"Non-FIX-03 findings Ready For Retest: {bad_rfr}", errors)

    bad_fix03 = [
        fid for fid in FIX03_TARGETS
        if by_id.get(fid, {}).get("status") == "Closed" and fid not in retest03_ids
    ]
    if bad_fix03:
        fail(f"FIX-03 findings Closed without MAINARCH-RETEST-03 PASS evidence: {bad_fix03}", errors)

    closed = {f["finding_id"] for f in findings if f.get("status") == "Closed"}
    if closed == FIX01_CLOSED | TARGETS | retest03_ids:
        if retest03_ids:
            ok(f"Closed set matches verified findings (25 pre-FIX-03 + RETEST-03 verified: {sorted(retest03_ids)})")
        else:
            ok("Closed set is exactly the 25 verified findings (17 FIX-01 + 8 FIX-02)")
    else:
        fail(f"Closed set mismatch: {sorted(closed)}", errors)
    if len(closed) >= 25 and (FIX01_CLOSED | TARGETS) <= closed:
        ok(f"Total Closed MAIN findings = {len(closed)} (>= 25 verified pre-FIX-03 baseline)")
    else:
        fail(f"Total Closed = {len(closed)}, expected >= 25 including all pre-FIX-03 closures", errors)

    open_ids = {f["finding_id"] for f in findings if f.get("status") == "Open"}
    non_target_open = open_ids - FIX03_TARGETS
    if non_target_open == EXPECTED_NONFIX03_OPEN:
        ok("Non-FIX-03 Open findings exactly match expected deferred set")
    else:
        fail(f"Non-FIX-03 Open set mismatch: {sorted(non_target_open)}", errors)
    unexpected_status = [
        fid for fid in FIX03_TARGETS
        if by_id.get(fid, {}).get("status") not in ("Open", "Ready For Retest", "Closed")
    ]
    if unexpected_status:
        fail(f"FIX-03 targets with unexpected status: {unexpected_status}", errors)

    # --- 14-15. Milestone flags preserved ---
    v12 = read_text(V1_2)
    audit_flags = set(retest.get("milestone_security_review_flags", []))
    for fid in sorted(MILESTONE_FLAGGED):
        f = by_id.get(fid, {})
        note_ok = "Milestone" in f.get("notes", "") and "PENDING" in f.get("notes", "")
        v12_ok = fid in v12 and "Milestone Security Review" in v12
        audit_ok = fid in audit_flags
        if note_ok and v12_ok and audit_ok:
            ok(f"{fid} milestone security-review flag preserved (registry + V1.2 + retest record)")
        else:
            fail(f"{fid} milestone security-review flag lost (notes={note_ok}, v12={v12_ok}, audit={audit_ok})", errors)

    # --- 16. No immediate Claude audit triggered ---
    reassess = retest.get("security_reassessment", "")
    ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    ws_blob = json.dumps(ws).lower()
    tasks = read_jsonl("docs/workforce/registries/tasks.jsonl")
    claude_tasks = [t for t in tasks if "claude" in json.dumps(t).lower() and t.get("status") in ("Open", "In Progress", "Authorized", "Candidate")]
    if "NO IMMEDIATE SECURITY AUDIT REQUIRED" in reassess and not claude_tasks and "claude" not in ws_blob:
        ok("No immediate Claude/security audit triggered")
    else:
        fail("Immediate Claude/security audit appears triggered or reassessment text missing", errors)

    # --- 17. Product remains blocked ---
    if ws.get("final_pre_product_audit", {}).get("product_development_state") == "BLOCKED_PENDING_FINAL_AUDIT":
        ok("Product development remains BLOCKED_PENDING_FINAL_AUDIT")
    else:
        fail("Product development not blocked", errors)

    # --- 18. Next planned task advanced past RETEST-02-INGEST ---
    # Valid successor states: MAINARCH-FIX-03 planned/running (pre-FIX-03), or
    # MAINARCH-RETEST-03 planned (post-FIX-03).
    gate = ws.get("current_gate", "")
    notes_blob = " ".join(ws.get("notes", []))
    successor_ok = (
        ("MAINARCH-FIX-03" in gate and "MAINARCH-FIX-03" in notes_blob)
        or ("MAINARCH-RETEST-03" in gate and "MAINARCH-RETEST-03" in notes_blob)
        or ("MAINARCH-FIX-03" in notes_blob and "MAINARCH-RETEST-03" in notes_blob)
    )
    if successor_ok:
        ok("Next planned task is a valid post-RETEST-02 successor (FIX-03 or RETEST-03)")
    else:
        fail("WORKFORCE_STATE does not reference a valid post-RETEST-02 successor task", errors)
    stale_writers = {"ANOX-TASK-FIX02SERVER0001", "ANOX-TASK-RET02INGEST"}
    if ws.get("current_writer", {}).get("task_id") in stale_writers:
        fail("WORKFORCE_STATE current_writer still references a stale pre-FIX-03 writer", errors)
    else:
        ok("WORKFORCE_STATE current_writer no longer references a stale pre-FIX-03 writer")

    # --- 19. Project Memory synchronized ---
    cur = json.loads(read_text("docs/continuity/CURRENT_STATE.json"))
    ledger = read_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
    ledger_ids = [e.get("event_id") for e in ledger]
    has_event = any(e.get("event_id") == INGEST_EVENT_ID and "MAINARCH-RETEST-02" in e.get("summary", "") for e in ledger)
    if has_event:
        ok(f"Project History Ledger contains {INGEST_EVENT_ID}")
    else:
        fail(f"Project History Ledger missing {INGEST_EVENT_ID}", errors)
    # Post-ingest invariant: CURRENT_STATE must always track the last sealed ledger
    # event (INGEST_EVENT_ID at ingest time; a later event such as MAINARCH-FIX-03's
    # after that task completes).
    last_event_id = ledger_ids[-1] if ledger_ids else None
    if cur.get("latest_material_event_id") == last_event_id and last_event_id:
        ok(f"CURRENT_STATE latest_material_event_id matches last sealed ledger event {last_event_id}")
    else:
        fail(f"latest_material_event_id={cur.get('latest_material_event_id')} vs last ledger {last_event_id}", errors)

    # --- 20. Master Audit Report synchronized ---
    master = read_text(MASTER)
    if "## MAINARCH-RETEST-02" in master:
        ok("Master Audit Report contains MAINARCH-RETEST-02 section")
    else:
        fail("Master Audit Report missing MAINARCH-RETEST-02 section", errors)
    if "verified by MAINARCH-RETEST-02" in master:
        ok("Master Audit Report FIX-02 status updated to verified")
    else:
        fail("Master Audit Report FIX-02 status not updated to verified", errors)
    if "FINAL_PRE_PRODUCT" in master and "COMPLETE" not in master.split("## MAINARCH-RETEST-02")[0].split("**Status:**")[1].split("\n")[0].replace("IN PROGRESS", ""):
        pass  # overall audit status remains IN PROGRESS; checked implicitly below
    if "IN PROGRESS" in master.splitlines()[3]:
        ok("Overall Final Pre-Product Audit remains IN PROGRESS (not marked complete)")
    else:
        fail("Overall audit status line changed unexpectedly", errors)

    # --- 21. Hardened FIX-02 validator passes ---
    r = subprocess.run([sys.executable, str(REPO / "tools/audit/validate_mainarch_fix02.py")],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode == 0:
        ok("Hardened validate_mainarch_fix02.py PASS")
    else:
        fail("Hardened validate_mainarch_fix02.py FAIL", errors)

    if errors:
        print("\nMAINARCH-RETEST-02-INGEST: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nMAINARCH-RETEST-02-INGEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
