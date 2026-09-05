#!/usr/bin/env python3
"""MAINARCH-FIX-02 deterministic validator.

Validates that the server/database/API/OTK/retention/privacy architecture
remediation is present and that the 8 targeted findings are Ready For Retest.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

TARGETS = {
    "ANOX-MAINARCH-003",
    "ANOX-MAINARCH-007",
    "ANOX-MAINARCH-008",
    "ANOX-MAINARCH-009",
    "ANOX-MAINARCH-010",
    "ANOX-MAINARCH-015",
    "ANOX-MAINARCH-016",
    "ANOX-MAINARCH-017",
}

FIX01_CLOSED = {
    "ANOX-MAINARCH-001","ANOX-MAINARCH-002","ANOX-MAINARCH-004","ANOX-MAINARCH-005",
    "ANOX-MAINARCH-006","ANOX-MAINARCH-012","ANOX-MAINARCH-014","ANOX-MAINARCH-020",
    "ANOX-MAINARCH-021","ANOX-MAINARCH-022","ANOX-MAINARCH-025","ANOX-MAINARCH-028",
    "ANOX-MAINARCH-029","ANOX-MAINARCH-032","ANOX-MAINARCH-033","ANOX-MAINARCH-034","ANOX-MAINARCH-035",
}

V1_2 = "docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md"


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


def check_phrases(text, phrases, label, errors):
    missing = [p for p in phrases if p.lower() not in text.lower()]
    if missing:
        fail(f"{label} missing terms: {missing}", errors)
        return False
    ok(f"{label} contains all required terms")
    return True


def main():
    print("MAINARCH-FIX-02 validator")
    errors = []

    # 1. Amendment file exists and is non-empty
    try:
        v12_text = read_text(V1_2)
    except FileNotFoundError:
        fail(f"{V1_2} not found", errors)
        return 1
    if not v12_text.strip():
        fail(f"{V1_2} is empty", errors)
    else:
        ok(f"{V1_2} exists and has content")

    # 2. B-005 contract terms
    check_phrases(v12_text, [
        "one active device per account",
        "authenticated db context",
        "rls model",
        "server role model",
        "service_role",
        "transaction boundaries",
        "db-schema-v1-frozen",
    ], "B-005 DB/RLS contract", errors)

    # 3. B-004 contract terms
    check_phrases(v12_text, [
        "request pipeline",
        "authenticateddevicecontext",
        "dpop",
        "replay cache",
        "access token",
        "revocation",
        "logging",
        "admin",
        "secret",
    ], "B-004 backend contract", errors)

    # 4. B-007 contract terms
    check_phrases(v12_text, [
        "endpoint inventory",
        "idempotency",
        "concurrency",
        "race",
        "error model",
        "/v1",
    ], "B-007 API contract", errors)

    # 5. B-006 OTK lifecycle
    check_phrases(v12_text, [
        "available",
        "claimed",
        "fallback",
        "replenish",
        "exhaustion",
        "atomic claim",
    ], "B-006 OTK lifecycle", errors)

    # 6. B-014 backup/PITR
    check_phrases(v12_text, [
        "erasure journal",
        "pitr",
        "backup",
        "restore",
        "retention",
    ], "B-014 backup/PITR", errors)

    # 7. B-012 attachment lifecycle
    check_phrases(v12_text, [
        "attachment lifecycle",
        "orphaned",
        "revocation",
        "account deletion",
    ], "B-012 attachment lifecycle", errors)

    # 8. B-011 FCM privacy
    check_phrases(v12_text, [
        "fcm token",
        "threat model",
        "backend",
        "reversible",
    ], "B-011 FCM privacy", errors)

    # 9. B-015 anti-enumeration
    check_phrases(v12_text, [
        "anti-enumeration",
        "rate-limit",
        "ip handling",
        "uniform",
    ], "B-015 anti-enumeration/rate-limit", errors)

    # 10. Cross-domain matrix
    if "Cross-Domain Consistency Matrix" in v12_text and "CONSISTENT" in v12_text:
        ok("Cross-domain consistency matrix present")
    else:
        fail("Cross-domain consistency matrix missing", errors)

    # 11. Milestone security review flags
    if "ANOX-MAINARCH-003" in v12_text and "ANOX-MAINARCH-007" in v12_text and "Milestone" in v12_text:
        ok("Milestone security review flags for 003/007 preserved")
    else:
        fail("Milestone security review flags missing", errors)

    # 12. B_FREEZE_REGISTRY updated
    br = read_text("docs/authority/B_FREEZE_REGISTRY.md")
    expected_ids = {"B-004", "B-005", "B-006", "B-007", "B-011", "B-012", "B-014", "B-015", "B-016"}
    missing = [bid for bid in expected_ids if f"B025_MANDATORY_AMENDMENTS_V1_2.md#{bid}" not in br]
    if missing:
        fail(f"B_FREEZE_REGISTRY missing V1.2 reference for {missing}", errors)
    else:
        ok("B_FREEZE_REGISTRY references V1.2 for all amended B IDs")

    # 13. AUTHORITY_INDEX updated
    ai = read_text("docs/authority/AUTHORITY_INDEX.md")
    if "B025_MANDATORY_AMENDMENTS_V1_2.md" not in ai:
        fail("AUTHORITY_INDEX missing V1.2 reference", errors)
    else:
        ok("AUTHORITY_INDEX references V1.2")

    # 14. Findings
    findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {f["finding_id"]: f for f in findings}
    all_ids = set(by_id.keys())

    missing = TARGETS - all_ids
    if missing:
        fail(f"Missing target findings: {missing}", errors)
    else:
        ok("All 8 target findings exist")

    unexpected_closed = [fid for fid in TARGETS if by_id.get(fid, {}).get("status") == "Closed"]
    if unexpected_closed:
        fail(f"Target findings unexpectedly Closed: {unexpected_closed}", errors)

    ready = [fid for fid in TARGETS if by_id.get(fid, {}).get("status") == "Ready For Retest"]
    if len(ready) == len(TARGETS):
        ok(f"All {len(TARGETS)} target findings are Ready For Retest")
    else:
        fail(f"Not all target findings Ready For Retest: ready={ready}", errors)

    # 15. Severity unchanged
    sev_ok = True
    for fid in TARGETS:
        f = by_id[fid]
        if f.get("severity") != f.get("original_severity", f.get("severity")):
            fail(f"{fid} severity changed", errors)
            sev_ok = False
    if sev_ok:
        ok("Targeted finding severities unchanged")

    # 16. Unrelated findings unchanged
    unrelated_ok = True
    for f in findings:
        fid = f["finding_id"]
        if fid in TARGETS:
            continue
        if fid in FIX01_CLOSED:
            if f["status"] != "Closed":
                fail(f"Previously Closed {fid} is no longer Closed", errors)
                unrelated_ok = False
        elif f["status"] != "Open":
            fail(f"Unrelated {fid} status changed to {f['status']}", errors)
            unrelated_ok = False
    if unrelated_ok:
        ok("Unrelated findings unchanged")

    # 17. Master Audit Report
    master = read_text("docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md")
    if "## MAINARCH-FIX-02" in master:
        ok("Master Audit Report contains MAINARCH-FIX-02 section")
    else:
        fail("Master Audit Report missing MAINARCH-FIX-02 section", errors)

    # 18. No product/CI code changed
    changed = git_diff_name_only("main", "HEAD")
    disallowed = [r"^android/", r"^crypto/rust/", r"^backend/", r"^\.github/workflows/",
                  r"\.kt$", r"\.rs$", r"\.gradle$", r"\.kts$", r"^Cargo\.toml$",
                  r"^build\.gradle", r"^settings\.gradle"]
    bad = [f for f in changed if any(re.search(p, f) for p in disallowed)]
    if bad:
        fail(f"Disallowed product/CI code changes: {bad}", errors)
    else:
        ok("No product/CI code changes vs main")

    # 19. Product blocked
    ws = json.loads((REPO / "docs/workforce/WORKFORCE_STATE.json").read_text(encoding="utf-8"))
    if ws.get("final_pre_product_audit", {}).get("product_development_state") == "BLOCKED_PENDING_FINAL_AUDIT":
        ok("Product development remains BLOCKED_PENDING_FINAL_AUDIT")
    else:
        fail("Product development not blocked", errors)

    if errors:
        print("\nMAINARCH-FIX-02: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nMAINARCH-FIX-02: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
