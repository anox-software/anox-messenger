#!/usr/bin/env python3
"""MAINARCH-RETEST-03-INGEST deterministic validator.

Validates that the MAINARCH-RETEST-03 result (PASS, 5/5) was canonically
ingested: the five verified MAINARCH-FIX-03 findings are Closed with preserved
severity/evidence, no unrelated finding was closed, no finding remains
Ready For Retest, the 003/007/024 milestone security-review flags remain
PENDING, the MAIN architecture remediation phase is recorded complete while
the Final Pre-Product Audit stays in progress, no immediate Claude audit was
triggered, the next phase resolves to the canonical Legacy / Build / Hardware
verification plan, and the hardened FIX-03 validator still passes.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

RETEST_SHA = "88ea18c9b7078c376ee027d0cacc4d4f147ebbf5"
FIX03_SUBSTANTIVE_SHA = "4573b64dcc997aaaee8e81675a871201627d454e"
FIX03_METADATA_SHA = "c81ed78aee82eabc816d858e03e01231f5b28461"
ORIGINAL_AUDIT_SHA = "0a4910eab1a92622383721100879cda46f924ca0"

TARGETS = {
    "ANOX-MAINARCH-011", "ANOX-MAINARCH-024", "ANOX-MAINARCH-026",
    "ANOX-MAINARCH-027", "ANOX-MAINARCH-036",
}

EXPECTED_SEVERITIES = {
    "ANOX-MAINARCH-011": "HIGH",
    "ANOX-MAINARCH-024": "MEDIUM",
    "ANOX-MAINARCH-026": "MEDIUM",
    "ANOX-MAINARCH-027": "MEDIUM",
    "ANOX-MAINARCH-036": "INFO",
}

PRE_FIX03_CLOSED = {
    "ANOX-MAINARCH-001", "ANOX-MAINARCH-002", "ANOX-MAINARCH-004", "ANOX-MAINARCH-005",
    "ANOX-MAINARCH-006", "ANOX-MAINARCH-012", "ANOX-MAINARCH-014", "ANOX-MAINARCH-020",
    "ANOX-MAINARCH-021", "ANOX-MAINARCH-022", "ANOX-MAINARCH-025", "ANOX-MAINARCH-028",
    "ANOX-MAINARCH-029", "ANOX-MAINARCH-032", "ANOX-MAINARCH-033", "ANOX-MAINARCH-034",
    "ANOX-MAINARCH-035",
    "ANOX-MAINARCH-003", "ANOX-MAINARCH-007", "ANOX-MAINARCH-008", "ANOX-MAINARCH-009",
    "ANOX-MAINARCH-010", "ANOX-MAINARCH-015", "ANOX-MAINARCH-016", "ANOX-MAINARCH-017",
}

EXPECTED_REMAINING_OPEN = {
    "ANOX-MAINARCH-013", "ANOX-MAINARCH-018", "ANOX-MAINARCH-019",
    "ANOX-MAINARCH-023", "ANOX-MAINARCH-030", "ANOX-MAINARCH-031",
}

MILESTONE_FLAGGED = {"ANOX-MAINARCH-003", "ANOX-MAINARCH-007", "ANOX-MAINARCH-024"}

LEGACY_PLAN = "docs/workforce/audits/legacy-audit-plan.json"
LEGACY_PLAN_DOC = "docs/workforce/audits/LEGACY_AUDIT_PLAN.md"
EXPECTED_LEGACY_AUDITS = [
    "LEGACY-AUDIT-B002", "LEGACY-AUDIT-B003", "LEGACY-AUDIT-CRYPTO",
    "LEGACY-AUDIT-ANDROID-SEC", "LEGACY-AUDIT-BUILD", "LEGACY-AUDIT-INTEGRATION",
]

MASTER = "docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md"
IR_REG = "docs/workforce/registries/implementation_readiness.json"
MAT_REG = "docs/workforce/registries/b021_verification_matrix.jsonl"
V1_3 = "docs/authority/B025_MANDATORY_AMENDMENTS_V1_3.md"


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
    print("MAINARCH-RETEST-03-INGEST validator")
    errors = []

    # --- 1-5. Retest result record ---
    audits = read_jsonl("docs/workforce/registries/audits.jsonl")
    retest = next((a for a in audits if a.get("audit_id") == "MAINARCH-RETEST-03"), None)
    if retest is None:
        fail("MAINARCH-RETEST-03 audit record missing", errors)
        retest = {}
    else:
        ok("MAINARCH-RETEST-03 audit record present")
    if retest.get("result") == "PASS":
        ok("MAINARCH-RETEST-03 result is PASS")
    else:
        fail(f"MAINARCH-RETEST-03 result is {retest.get('result')}, expected PASS", errors)
    if (retest.get("canonical_sha") == RETEST_SHA
            and retest.get("retest_canonical_sha") == RETEST_SHA
            and retest.get("fix_canonical_merge_sha") == RETEST_SHA):
        ok("MAINARCH-RETEST-03 canonical/retest/FIX-03 merge SHA recorded correctly")
    else:
        fail("MAINARCH-RETEST-03 canonical/retest/merge SHA mismatch", errors)
    if (set(retest.get("finding_ids", [])) == TARGETS
            and set(retest.get("closure_eligible_ids", [])) == TARGETS
            and set(retest.get("closed_findings", [])) == TARGETS):
        ok("MAINARCH-RETEST-03 records exactly the 5 finding IDs")
    else:
        fail("MAINARCH-RETEST-03 finding_ids/closure_eligible_ids/closed_findings mismatch", errors)
    if (retest.get("source_audit_id") == "AUDIT-MAIN-ARCHITECTURE"
            and retest.get("remediation_task") == "MAINARCH-FIX-03"
            and retest.get("original_audit_sha") == ORIGINAL_AUDIT_SHA
            and retest.get("fix_substantive_sha") == FIX03_SUBSTANTIVE_SHA
            and retest.get("fix_metadata_sha") == FIX03_METADATA_SHA):
        ok("MAINARCH-RETEST-03 source/remediation/SHA chain recorded")
    else:
        fail("MAINARCH-RETEST-03 source/remediation/SHA chain missing or wrong", errors)
    if (retest.get("failed_ids") == [] and retest.get("regression_ids") == []
            and retest.get("not_reviewable_ids") == []):
        ok("MAINARCH-RETEST-03 records zero failures, regressions, not-reviewable")
    else:
        fail("MAINARCH-RETEST-03 failed/regression/not_reviewable ids not empty", errors)
    if retest.get("mode") == "READ_ONLY_TARGETED_DELTA_RETEST":
        ok("MAINARCH-RETEST-03 mode recorded")
    else:
        fail("MAINARCH-RETEST-03 mode missing/wrong", errors)

    # --- 6-13. Finding transitions ---
    findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {f["finding_id"]: f for f in findings}
    expected_ids = {f"ANOX-MAINARCH-{i:03d}" for i in range(1, 37)}
    extra_ids = set(by_id) - expected_ids
    legacy_extra = {fid for fid in extra_ids if fid.startswith("ANOX-LEGACY-")}
    if extra_ids == legacy_extra:
        ok("All 36 ANOX-MAINARCH-001..036 IDs preserved; new ANOX-LEGACY-* findings allowed")
    else:
        fail(f"Finding ID set mismatch: missing {expected_ids - set(by_id)}, extra {extra_ids - legacy_extra}", errors)

    for fid in sorted(TARGETS):
        f = by_id.get(fid, {})
        if f.get("status") != "Closed":
            fail(f"{fid} is not Closed (status={f.get('status')})", errors)
            continue
        if f.get("severity") != EXPECTED_SEVERITIES[fid]:
            fail(f"{fid} severity changed to {f.get('severity')}", errors)
            continue
        ev = f.get("closure_evidence", [])
        if not any("MAINARCH-FIX-03" in e for e in ev) or not any("MAINARCH-RETEST-03" in e for e in ev):
            fail(f"{fid} closure evidence missing FIX-03/RETEST-03 reference", errors)
            continue
        if not any(f"git:{RETEST_SHA}" in e for e in ev):
            fail(f"{fid} closure evidence missing retest canonical SHA", errors)
            continue
        if not any(ORIGINAL_AUDIT_SHA in e for e in f.get("evidence_refs", [])):
            fail(f"{fid} original audit evidence reference lost", errors)
            continue
        if not f.get("closure_actor"):
            fail(f"{fid} missing closure_actor", errors)
            continue
        ok(f"{fid} Closed with preserved severity, original evidence, and FIX-03/RETEST-03 closure refs")

    rfr = [f["finding_id"] for f in findings if f.get("status") == "Ready For Retest"]
    if not rfr:
        ok("No finding remains Ready For Retest")
    else:
        fail(f"Findings still Ready For Retest: {rfr}", errors)

    closed = {f["finding_id"] for f in findings if f.get("status") == "Closed"}
    if closed == PRE_FIX03_CLOSED | TARGETS and len(closed) == 30:
        ok("Closed set is exactly the 25 pre-FIX-03 verified + 5 RETEST-03 verified = 30")
    else:
        fail(f"Closed set mismatch: {sorted(closed)}", errors)

    open_ids = {f["finding_id"] for f in findings if f.get("status") == "Open"}
    legacy_open = {fid for fid in open_ids if fid.startswith("ANOX-LEGACY-")}
    if open_ids == EXPECTED_REMAINING_OPEN | legacy_open:
        ok(f"Remaining Open set includes the 6 deferred MAIN findings plus {len(legacy_open)} new ANOX-LEGACY-* findings: {sorted(open_ids)}")
    else:
        fail(f"Remaining Open set mismatch: {sorted(open_ids)}", errors)

    # --- 14-16. Milestone flags remain PENDING ---
    v13 = read_text(V1_3)
    audit_flags = set(retest.get("milestone_security_review_flags", []))
    for fid in sorted(MILESTONE_FLAGGED):
        f = by_id.get(fid, {})
        note_ok = "ilestone" in f.get("notes", "") and "PENDING" in f.get("notes", "")
        field_ok = f.get("milestone_security_review") == "PENDING"
        audit_ok = fid in audit_flags
        text_ok = fid in v13 and "milestone" in v13.lower()
        if note_ok and field_ok and audit_ok and text_ok:
            ok(f"{fid} milestone security-review flag remains PENDING (machine-readable)")
        else:
            fail(f"{fid} milestone flag lost/incomplete (notes={note_ok}, field={field_ok}, audit={audit_ok}, v13={text_ok})", errors)

    # --- 17. No immediate Claude audit ---
    reassess = retest.get("security_reassessment", "")
    ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    ws_blob = json.dumps(ws).lower()
    tasks = read_jsonl("docs/workforce/registries/tasks.jsonl")
    # Only tasks that existed at or before MAINARCH-RETEST-03 ingest are in scope.
    pre_legacy_tasks = [t for t in tasks if t.get("created_at", "") <= "2026-09-06"]
    claude_tasks = [t for t in pre_legacy_tasks if "claude" in json.dumps(t).lower()
                    and t.get("status") in ("Open", "In Progress", "Authorized", "Candidate")]
    if "NO IMMEDIATE SECURITY AUDIT REQUIRED" in reassess or "NO NEW SECURITY AUDIT REQUIRED" in reassess:
        reassess_ok = True
    else:
        reassess_ok = False
    if reassess_ok and not claude_tasks and "claude" not in ws_blob:
        ok("No immediate Claude/security audit triggered")
    else:
        fail("Immediate Claude/security audit appears triggered or reassessment text missing", errors)

    # --- 18. Product remains blocked ---
    fpa = ws.get("final_pre_product_audit", {})
    if fpa.get("product_development_state") == "BLOCKED_PENDING_FINAL_AUDIT":
        ok("Product development remains BLOCKED_PENDING_FINAL_AUDIT")
    else:
        fail("Product development not blocked", errors)

    # --- 19-20. Phase state ---
    if (fpa.get("main_architecture_audit") == "COMPLETE"
            and fpa.get("main_architecture_remediation_phase") == "COMPLETE"):
        ok("MAIN architecture audit + remediation phase recorded COMPLETE")
    else:
        fail("MAIN architecture audit/remediation phase not recorded COMPLETE", errors)
    if fpa.get("status") == "IN_PROGRESS" and fpa.get("product_development_unblocked") is not True:
        ok("Final Pre-Product Audit remains IN PROGRESS (not complete)")
    else:
        fail("Final Pre-Product Audit wrongly marked complete", errors)

    # --- 21. Implementation readiness unchanged for B-004/B-005 ---
    ir = json.loads(read_text(IR_REG))
    bad_ir = []
    for d in ("B-004", "B-005"):
        dom = ir.get("domains", {}).get(d, {})
        if dom.get("architecture_state") != "FROZEN" or dom.get("implementation_state") != "NOT_STARTED":
            bad_ir.append(d)
    if not bad_ir:
        ok("implementation_readiness still shows B-004/B-005 FROZEN + NOT_STARTED")
    else:
        fail(f"implementation_readiness drifted for: {bad_ir}", errors)

    # --- 22. Physical GrapheneOS verification remains required/pending ---
    mat = read_jsonl(MAT_REG)
    phys = [r for r in mat if r.get("execution_class") == "PHYSICAL_GRAPHENEOS"]
    phys_ok = phys and not any(r.get("current_result") == "PASS" for r in phys) and \
        any(r.get("evidence_state") == "PHYSICAL_VERIFICATION_REQUIRED" for r in phys)
    f018 = by_id.get("ANOX-MAINARCH-018", {})
    if phys_ok and f018.get("status") == "Open":
        ok("Physical GrapheneOS/StrongBox verification remains PHYSICAL_VERIFICATION_REQUIRED (018 Open)")
    else:
        fail("Physical verification state weakened or finding 018 closed", errors)

    # --- 23. Next phase = Legacy / Build / Hardware per canonical plan ---
    plan = json.loads(read_text(LEGACY_PLAN))
    plan_ids = [a.get("audit_id") for a in plan.get("one_time_audits", [])]
    gate = ws.get("current_gate", "")
    notes_blob = " ".join(ws.get("notes", []))
    if plan_ids == EXPECTED_LEGACY_AUDITS and (REPO / LEGACY_PLAN_DOC).exists():
        ok(f"Canonical legacy audit plan preserved: {plan_ids}")
    else:
        fail(f"Legacy audit plan mismatch: {plan_ids}", errors)
    if ("LEGACY-AUDIT-B002" in gate and "LEGACY" in gate.upper()) or \
       ("LEGACY-AUDIT-B002" in notes_blob and "LEGACY" in notes_blob.upper()):
        ok("Next planned task resolves to first canonical legacy session (LEGACY-AUDIT-B002)")
    else:
        fail("Next planned task does not resolve to the canonical legacy phase", errors)
    required_legacy = fpa.get("required_legacy_audits", [])
    if required_legacy == EXPECTED_LEGACY_AUDITS:
        ok("required_legacy_audits preserved in WORKFORCE_STATE")
    else:
        fail(f"required_legacy_audits mismatch: {required_legacy}", errors)

    # --- 24. Project Memory synchronized ---
    cur = json.loads(read_text("docs/continuity/CURRENT_STATE.json"))
    ledger = read_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
    last_event = ledger[-1] if ledger else {}
    has_event = any(
        e.get("event_id") == "ANOX-EVENT-0034" and "MAINARCH-RETEST-03" in e.get("summary", "")
        for e in ledger
    )
    if has_event:
        ok("Project History Ledger contains ANOX-EVENT-0034")
    else:
        fail("Project History Ledger missing ANOX-EVENT-0034", errors)
    if cur.get("latest_material_event_id") == last_event.get("event_id") and last_event.get("event_id"):
        ok(f"CURRENT_STATE latest_material_event_id matches last sealed ledger event {last_event.get('event_id')}")
    else:
        fail(f"latest_material_event_id={cur.get('latest_material_event_id')} vs last ledger {last_event.get('event_id')}", errors)
    if cur.get("described_head") and len(cur.get("described_head")) == 40:
        ok(f"CURRENT_STATE described_head recorded: {cur['described_head'][:12]}")
    else:
        fail("CURRENT_STATE described_head missing/invalid", errors)

    # --- 25. Master Audit Report synchronized ---
    master = read_text(MASTER)
    if "## MAINARCH-RETEST-03" in master:
        ok("Master Audit Report contains MAINARCH-RETEST-03 section")
    else:
        fail("Master Audit Report missing MAINARCH-RETEST-03 section", errors)
    if "verified by MAINARCH-RETEST-03" in master:
        ok("Master Audit Report FIX-03 status updated to verified")
    else:
        fail("Master Audit Report FIX-03 status not updated to verified", errors)
    if "IN PROGRESS" in master.splitlines()[3]:
        ok("Overall Final Pre-Product Audit remains IN PROGRESS")
    else:
        fail("Overall audit status line changed unexpectedly", errors)
    if "Closed = 30" in master and "Remaining = 6" in master:
        ok("Master Audit Report records MAIN totals 30 Closed / 6 Open")
    else:
        fail("Master Audit Report missing 30/6 totals", errors)

    # --- 26. Hardened FIX-03 validator passes ---
    r = subprocess.run([sys.executable, str(REPO / "tools/audit/validate_mainarch_fix03.py")],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode == 0:
        ok("Hardened validate_mainarch_fix03.py PASS")
    else:
        fail("Hardened validate_mainarch_fix03.py FAIL", errors)

    if errors:
        print("\nMAINARCH-RETEST-03-INGEST: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nMAINARCH-RETEST-03-INGEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
