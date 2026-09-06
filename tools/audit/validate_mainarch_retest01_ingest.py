#!/usr/bin/env python3
"""MAINARCH-RETEST-01-INGEST deterministic validator.

Validates that the MAINARCH-RETEST-01 result was ingested, the 17 verified
FIX-01 findings are Closed, history is preserved, no unrelated findings were
closed, and no product/CI code was changed.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

RETEST_SHA = "fd1fbddbddcba7d8705f7a76318856ad56dafb19"
ORIGINAL_AUDIT_SHA = "0a4910eab1a92622383721100879cda46f924ca0"

# After MAINARCH-FIX-02, the 8 FIX-02 findings may be Ready For Retest.
FIX02_TARGETS = {
    "ANOX-MAINARCH-003", "ANOX-MAINARCH-007", "ANOX-MAINARCH-008", "ANOX-MAINARCH-009",
    "ANOX-MAINARCH-010", "ANOX-MAINARCH-015", "ANOX-MAINARCH-016", "ANOX-MAINARCH-017",
}

FIX03_TARGETS = {
    "ANOX-MAINARCH-011", "ANOX-MAINARCH-024", "ANOX-MAINARCH-026",
    "ANOX-MAINARCH-027", "ANOX-MAINARCH-036",
}

RETEST03_CLOSED = set()


TARGETS = {
    "ANOX-MAINARCH-001",
    "ANOX-MAINARCH-002",
    "ANOX-MAINARCH-004",
    "ANOX-MAINARCH-005",
    "ANOX-MAINARCH-006",
    "ANOX-MAINARCH-012",
    "ANOX-MAINARCH-014",
    "ANOX-MAINARCH-020",
    "ANOX-MAINARCH-021",
    "ANOX-MAINARCH-022",
    "ANOX-MAINARCH-025",
    "ANOX-MAINARCH-028",
    "ANOX-MAINARCH-029",
    "ANOX-MAINARCH-032",
    "ANOX-MAINARCH-033",
    "ANOX-MAINARCH-034",
    "ANOX-MAINARCH-035",
}

EXPECTED_SEVERITIES = {
    "ANOX-MAINARCH-001": "HIGH",
    "ANOX-MAINARCH-002": "HIGH",
    "ANOX-MAINARCH-004": "HIGH",
    "ANOX-MAINARCH-005": "HIGH",
    "ANOX-MAINARCH-006": "HIGH",
    "ANOX-MAINARCH-012": "HIGH",
    "ANOX-MAINARCH-014": "MEDIUM",
    "ANOX-MAINARCH-020": "MEDIUM",
    "ANOX-MAINARCH-021": "MEDIUM",
    "ANOX-MAINARCH-022": "MEDIUM",
    "ANOX-MAINARCH-025": "MEDIUM",
    "ANOX-MAINARCH-028": "MEDIUM",
    "ANOX-MAINARCH-029": "MEDIUM",
    "ANOX-MAINARCH-032": "LOW",
    "ANOX-MAINARCH-033": "LOW",
    "ANOX-MAINARCH-034": "LOW",
    "ANOX-MAINARCH-035": "LOW",
}


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def read_text(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def read_jsonl(rel):
    return [json.loads(l) for l in (REPO / rel).read_text().splitlines() if l.strip()]


def git_diff_name_only(base, head):
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", base, head],
            cwd=REPO,
            text=True,
        )
        return [l for l in out.splitlines() if l]
    except subprocess.CalledProcessError:
        return []


def main():
    print("MAINARCH-RETEST-01-INGEST validator")
    errors = []

    # 1. Retest result exists in audits.jsonl
    audits = read_jsonl("docs/workforce/registries/audits.jsonl")
    retest_audit = next((a for a in audits if a.get("audit_id") == "MAINARCH-RETEST-01"), None)
    if retest_audit is None:
        fail("MAINARCH-RETEST-01 audit record missing", errors)
    else:
        ok("MAINARCH-RETEST-01 audit record present")
        if retest_audit.get("result") != "PASS":
            fail(f"MAINARCH-RETEST-01 result is {retest_audit.get('result')}, expected PASS", errors)
        else:
            ok("MAINARCH-RETEST-01 result is PASS")
        if retest_audit.get("canonical_sha") != RETEST_SHA:
            fail(f"MAINARCH-RETEST-01 canonical_sha mismatch: {retest_audit.get('canonical_sha')}", errors)
        else:
            ok("MAINARCH-RETEST-01 canonical_sha matches")
        if retest_audit.get("source_audit_id") != "AUDIT-MAIN-ARCHITECTURE":
            fail("MAINARCH-RETEST-01 source_audit_id missing/wrong", errors)
        else:
            ok("MAINARCH-RETEST-01 source_audit_id correct")
        if retest_audit.get("remediation_task") != "MAINARCH-FIX-01":
            fail("MAINARCH-RETEST-01 remediation_task missing/wrong", errors)
        else:
            ok("MAINARCH-RETEST-01 remediation_task correct")
        if set(retest_audit.get("closure_eligible_ids", [])) != TARGETS:
            fail("MAINARCH-RETEST-01 closure_eligible_ids mismatch", errors)
        else:
            ok("MAINARCH-RETEST-01 closure_eligible_ids match")
        if retest_audit.get("security_reassessment") != "NO NEW SECURITY AUDIT REQUIRED":
            fail("MAINARCH-RETEST-01 security_reassessment missing/wrong", errors)
        else:
            ok("MAINARCH-RETEST-01 security_reassessment correct")

    # 2. Findings: 17 target IDs, all Closed, severities preserved, unrelated Open, no unexpected Closed
    findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    finding_ids = {f["finding_id"] for f in findings}
    if set(f"ANOX-MAINARCH-{i:03d}" for i in range(1, 37)) != finding_ids:
        missing = set(f"ANOX-MAINARCH-{i:03d}" for i in range(1, 37)) - finding_ids
        extra = finding_ids - set(f"ANOX-MAINARCH-{i:03d}" for i in range(1, 37))
        fail(f"Finding ID set mismatch: missing {missing}, extra {extra}", errors)
    else:
        ok("All 36 ANOX-MAINARCH-001..036 IDs preserved")

    closed_count = 0
    for f in findings:
        fid = f["finding_id"]
        if fid in TARGETS:
            if f.get("status") != "Closed":
                fail(f"{fid} is not Closed (status={f.get('status')})", errors)
            elif f.get("severity") != EXPECTED_SEVERITIES.get(fid):
                fail(f"{fid} severity changed to {f.get('severity')}", errors)
            elif not any("MAINARCH-RETEST-01" in e or "git:fd1fbdd" in e for e in f.get("closure_evidence", [])):
                fail(f"{fid} closure evidence missing MAINARCH-RETEST-01", errors)
            else:
                closed_count += 1
        elif fid in FIX02_TARGETS:
            if f.get("status") not in ("Open", "Ready For Retest", "Closed"):
                fail(f"FIX-02 target {fid} changed unexpectedly to {f.get('status')}", errors)
            elif f.get("status") == "Closed" and not any(
                "MAINARCH-RETEST-02" in e for e in f.get("closure_evidence", [])
            ):
                fail(f"FIX-02 target {fid} Closed without MAINARCH-RETEST-02 evidence", errors)
        elif fid in FIX03_TARGETS:
            if f.get("status") == "Closed" and fid not in RETEST03_CLOSED:
                fail(f"FIX-03 target {fid} Closed without MAINARCH-RETEST-03 evidence", errors)
            elif f.get("status") not in ("Open", "Ready For Retest", "Closed"):
                fail(f"FIX-03 target {fid} changed unexpectedly to {f.get('status')}", errors)
        else:
            if f.get("status") != "Open":
                fail(f"Unrelated {fid} changed to {f.get('status')}", errors)
    if closed_count == len(TARGETS):
        ok(f"All {len(TARGETS)} targeted findings Closed with preserved severities and closure evidence")

    # 3. No unexpected Closed (after MAINARCH-RETEST-02 ingest the FIX-02
    # targets may also be Closed; the closed set must remain a subset of the
    # two verified closure groups).
    all_closed = {f["finding_id"] for f in findings if f.get("status") == "Closed"}
    if TARGETS <= all_closed and all_closed <= (TARGETS | FIX02_TARGETS):
        ok(f"Closed findings set contains the 17 targets and only verified groups ({len(all_closed)} closed)")
    else:
        fail(f"Closed set mismatch: expected subset of {TARGETS | FIX02_TARGETS} containing {TARGETS}, got {all_closed}", errors)

    # 4. Workforce state synchronized
    state = (REPO / "docs/workforce/WORKFORCE_STATE.json").read_text(encoding="utf-8")
    ws = json.loads(state)
    notes = ws.get("notes", [])
    if any("MAINARCH-RETEST-01 PASS" in n for n in notes):
        ok("WORKFORCE_STATE notes reflect MAINARCH-RETEST-01 PASS")
    else:
        fail("WORKFORCE_STATE notes missing MAINARCH-RETEST-01 PASS", errors)
    if any("MAINARCH-FIX-01" in n and "pending" in n.lower() for n in notes):
        fail("WORKFORCE_STATE notes still claim MAINARCH-FIX-01 is pending", errors)
    else:
        ok("WORKFORCE_STATE notes do not claim MAINARCH-FIX-01 is pending")
    if ws.get("final_pre_product_audit", {}).get("product_development_state") == "BLOCKED_PENDING_FINAL_AUDIT":
        ok("Product development remains BLOCKED_PENDING_FINAL_AUDIT")
    else:
        fail("Product development not blocked", errors)
    if ws.get("current_writer", {}).get("task_id") != "ANOX-TASK-MAINARCH0001":
        ok("WORKFORCE_STATE current_writer is not the stale audit-freeze task")
    else:
        fail("WORKFORCE_STATE current_writer still references stale ANOX-TASK-MAINARCH0001", errors)
    current_gate = ws.get("current_gate") or ""
    if any(t in current_gate for t in ("MAINARCH-FIX-02", "MAINARCH-RETEST-02", "MAINARCH-FIX-03", "MAINARCH-RETEST-03")):
        ok("WORKFORCE_STATE current_gate points to a recognized post-FIX-01 task")
    else:
        fail("WORKFORCE_STATE current_gate does not point to a recognized post-FIX-01 task", errors)

    # 5. Master audit report has retest section
    master = read_text("docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md")
    if "## MAINARCH-RETEST-01" in master:
        ok("Master Audit Report contains MAINARCH-RETEST-01 section")
    else:
        fail("Master Audit Report missing MAINARCH-RETEST-01 section", errors)
    if "verified by MAINARCH-RETEST-01" in master:
        ok("Master Audit Report FIX-01 status updated to verified")
    else:
        fail("Master Audit Report FIX-01 status not updated to verified", errors)

    # 6. Project Memory ledger has ANOX-EVENT-0030 (may be followed by later events)
    ledger = read_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
    has_0030 = any(e.get("event_id") == "ANOX-EVENT-0030" and "MAINARCH-RETEST-01" in e.get("summary", "") for e in ledger)
    if has_0030:
        ok("Project History Ledger contains ANOX-EVENT-0030")
    else:
        fail("Project History Ledger missing ANOX-EVENT-0030", errors)

    # 7. CURRENT_STATE latest event must match the last sealed ledger event
    #    (dynamic: ANOX-EVENT-0030 after RETEST-01 ingest, may advance after
    #    later verified material events such as FIX-02 / RETEST-02 ingest).
    cur = json.loads(read_text("docs/continuity/CURRENT_STATE.json"))
    last_event_id = ledger[-1].get("event_id") if ledger else None
    if cur.get("latest_material_event_id") == last_event_id:
        ok(f"CURRENT_STATE.json latest_material_event_id matches last ledger event {last_event_id}")
    else:
        fail(f"CURRENT_STATE.json latest_material_event_id {cur.get('latest_material_event_id')} != last ledger event {last_event_id}", errors)

    # 8. No product/CI code changed vs canonical main
    changed = git_diff_name_only("main", "HEAD")
    disallowed_patterns = [
        r"^android/",
        r"^crypto/rust/",
        r"^backend/",
        r"^\.github/workflows/",
        r"\.kt$",
        r"\.rs$",
        r"\.gradle$",
        r"\.kts$",
        r"^Cargo\.toml$",
        r"^build\.gradle",
        r"^settings\.gradle",
    ]
    bad = [f for f in changed if any(re.search(p, f) for p in disallowed_patterns)]
    if bad:
        fail(f"Disallowed product/CI code changes: {bad}", errors)
    else:
        ok("No product/CI code changes vs main")

    if errors:
        print("\nMAINARCH-RETEST-01-INGEST: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nMAINARCH-RETEST-01-INGEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
