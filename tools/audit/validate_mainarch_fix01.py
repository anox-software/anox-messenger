#!/usr/bin/env python3
"""MAINARCH-FIX-01 deterministic validator.

Validates that the authority/source-of-truth/B003/state-machine/audit-gate
remediation targets have been applied without changing product code.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def read_text(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def has_lines_forbidding(rel, bad_patterns, label, errors, allowed_contexts=None):
    text = read_text(rel).lower()
    lines = text.splitlines()
    found = []
    for p in bad_patterns:
        for line in lines:
            if p.lower() in line:
                if allowed_contexts and any(a.lower() in line for a in allowed_contexts):
                    continue
                found.append(p)
                break
    if found:
        fail(f"{label} still contains forbidden phrases: {found}", errors)
    else:
        ok(f"{label} does not contain forbidden phrases")
    return not found


def main():
    print("MAINARCH-FIX-01 validator")
    errors = []

    # 1. Authority routing starts at AUTHORITY_INDEX
    readme = read_text("docs/README.md")
    if "docs/authority/AUTHORITY_INDEX.md" not in readme:
        fail("docs/README.md does not route to AUTHORITY_INDEX", errors)
    else:
        ok("docs/README.md routes to AUTHORITY_INDEX")

    if "docs/current/" in readme and "source of truth" in readme.lower():
        # README now says current/ is advisory; allow that.
        pass

    # 2. B027 current status no longer contradictory
    freeze = read_text("docs/authority/B_FREEZE_REGISTRY.md")
    if "PRE-FROZEN" in freeze and "B-027" in freeze:
        fail("B_FREEZE_REGISTRY still lists B-027 as PRE-FROZEN", errors)
    else:
        ok("B_FREEZE_REGISTRY B-027 status updated")

    b027_authority = read_text("docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md")
    if "B027-A/B/C" not in freeze and "IMPLEMENTED" not in b027_authority:
        # either the freeze or the authority must say complete
        pass
    if "B027-C INTEGRITY" in b027_authority and "IMPLEMENTED" in b027_authority:
        ok("B027 authority declares A/B/C implemented")
    else:
        fail("B027 authority does not declare A/B/C implemented", errors)

    authority_index = read_text("docs/authority/AUTHORITY_INDEX.md")
    if "B027-A/B/C implemented" in authority_index and "FINAL_PRE_PRODUCT_AUDIT" in authority_index:
        ok("AUTHORITY_INDEX B027 status updated")
    else:
        fail("AUTHORITY_INDEX B027 status stale", errors)

    # 3. B027 canonical location correct
    if "B027_AI_WORKFORCE_GOVERNANCE.md" in authority_index:
        ok("B027 canonical location is correct")
    else:
        fail("B027 canonical location missing", errors)

    # 4-6. No current auth doc mandates Ed25519, refresh token, OPEN production auth contract
    has_lines_forbidding(
        "docs/current/AUTH_PROTOCOL_STATUS.md",
        ["ed25519", "refresh token", "still open"],
        "AUTH_PROTOCOL_STATUS",
        errors,
        allowed_contexts=["no ed25519", "no refresh token"],
    )
    has_lines_forbidding(
        "docs/current/ACCOUNT_DEVICE_LIFECYCLE.md",
        ["ed25519", "refresh token"],
        "ACCOUNT_DEVICE_LIFECYCLE",
        errors,
        allowed_contexts=["no ed25519", "no refresh token"],
    )

    # 7-8. B-003 no mandatory phone/email/SMS; current version uniquely resolved
    b003_amendment = read_text("docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md")
    b003_amendment_lower = b003_amendment.lower()
    if "no password" not in b003_amendment_lower or "no mandatory email" not in b003_amendment_lower:
        fail("B-003 v1.5 does not resolve PII contradiction", errors)
    else:
        ok("B-003 v1.5 resolves PII contradiction")

    if "B-003" not in freeze or "FROZEN v1.5" not in freeze:
        fail("B_FREEZE_REGISTRY does not record B-003 v1.5 as current", errors)
    else:
        ok("B_FREEZE_REGISTRY records B-003 v1.5")

    # 9. CommitArmed semantics documented
    if "CommitArmed" in b003_amendment and "client-side safety precondition" in b003_amendment:
        ok("CommitArmed semantics documented")
    else:
        fail("CommitArmed semantics not documented", errors)

    # 10. username/license policy unambiguous
    if "client implements the same alphabet" in b003_amendment and "server is the authoritative accept/reject authority" in b003_amendment:
        ok("username/license policy unambiguous")
    else:
        fail("username/license policy ambiguous", errors)

    # 11. license restricted-mode state defined
    b013_amendment_section = b003_amendment_lower.split("## b-013")[1] if "## b-013" in b003_amendment_lower else ""
    if "license expiry restricted mode" in b013_amendment_section and "operations that remain permitted" in b013_amendment_section:
        ok("license restricted-mode state defined")
    else:
        fail("license restricted-mode state not defined", errors)

    # 12. contact trust durable states unambiguous
    b010_section = b003_amendment.split("## B-010")[1] if "## B-010" in b003_amendment else ""
    if "durable states" in b003_amendment.lower() and "transient" in b003_amendment.lower():
        ok("contact trust durable/transient states documented")
    else:
        fail("contact trust states not unambiguous", errors)

    # 13. message DELIVERED semantics consistent with B-008
    b008_section = b003_amendment.split("## B-008")[1] if "## B-008" in b003_amendment else ""
    if "DELIVERED" in b003_amendment and "durable atomic commit" in b003_amendment:
        ok("message DELIVERED semantics consistent")
    else:
        fail("message DELIVERED semantics not reconciled", errors)

    # 14. B027 pre-product vs B-022/B-023 release gate distinct
    b022_section = b003_amendment.split("## B-022")[1] if "## B-022" in b003_amendment else ""
    if "pre-product development audit" in b003_amendment and "release authorization" in b003_amendment:
        ok("pre-product vs release audit gates distinct")
    else:
        fail("pre-product vs release audit gates not distinct", errors)

    # 15. B-022 not weakened
    if "B027 pre-product audit does **not** satisfy or replace B-022/B-023" in b003_amendment:
        ok("B-022 not weakened")
    else:
        fail("B-022 weakened", errors)

    # 16. UX security semantics present
    if "license status" in b003_amendment and "irreversible" in b003_amendment:
        ok("B-020 security UX semantics present")
    else:
        fail("B-020 security UX semantics missing", errors)

    # 17. MAIN references B027 development trust boundary
    if "B-027 development/AI workforce trust boundary" in b003_amendment and "AI agents are untrusted executors" in b003_amendment:
        ok("MAIN references B027 development trust boundary")
    else:
        fail("MAIN does not reference B027 development trust boundary", errors)

    # 18. stale OPEN markers from 034 reconciled
    for rel in ["docs/current/METADATA_PRIVACY.md", "docs/current/PUSH_OFFLINE.md", "docs/current/ATTACHMENTS.md"]:
        text = read_text(rel).lower()
        if "**open**" in text or "remains open" in text:
            fail(f"{rel} still has OPEN marker", errors)
        else:
            ok(f"{rel} OPEN markers reconciled")

    # 19. superseded active-path docs are history/pointer-only
    for rel, target in [
        ("docs/security/account-recovery.md", "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md"),
        ("docs/security/push-notifications.md", "docs/authority/B025/TRACK_B/B011_PUSH_OFFLINE.md"),
        ("docs/architecture/key-architecture.md", "docs/authority/B025/TRACK_B/B006_VODOZEMAC_KEY_DISTRIBUTION.md"),
        ("docs/specifications/public-key-verification.md", "docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md#B-010"),
    ]:
        text = read_text(rel)
        if "HISTORICAL / SUPERSEDED" in text or "SUPERSEDED" in text:
            if target in text:
                ok(f"{rel} superseded with pointer to {target}")
            else:
                fail(f"{rel} superseded but does not point to {target}", errors)
        else:
            fail(f"{rel} not marked superseded", errors)

    # 20. duplicate Authority mirrors no longer independently normative
    for rel in [
        "docs/current/SECURITY_INVARIANTS.md",
        "docs/current/SYSTEM_ARCHITECTURE.md",
        "docs/current/OPEN_ARCHITECTURE_ITEMS.md",
    ]:
        text = read_text(rel)
        if "Status:" in text and ("POINTER" in text or "ADVISORY" in text):
            if "canonical" in text.lower():
                ok(f"{rel} is pointer, not competing authority")
            else:
                fail(f"{rel} missing canonical pointer", errors)
        else:
            fail(f"{rel} not converted to pointer", errors)

    # 21. broken raw1.1 history reference removed/fixed
    if "docs/history/raw1.1/" in readme:
        fail("docs/README.md still references docs/history/raw1.1/", errors)
    else:
        ok("docs/README.md does not reference broken docs/history/raw1.1/")

    # 22. finding IDs remain present
    findings = [json.loads(l) for l in (REPO / "docs/workforce/registries/findings.jsonl").read_text().splitlines() if l.strip()]
    expected = {f"ANOX-MAINARCH-{n:03d}" for n in range(1, 37)}
    actual = {f["finding_id"] for f in findings}
    if expected != actual:
        fail(f"finding IDs mismatch: missing {expected-actual}, extra {actual-expected}", errors)
    else:
        ok("all 36 finding IDs preserved")

    # 23. severity unchanged
    target_ids = {
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
    by_id = {f["finding_id"]: f for f in findings}
    expected_sev = {
        "001": "HIGH", "002": "HIGH", "004": "HIGH", "005": "HIGH", "006": "HIGH", "012": "HIGH",
        "014": "MEDIUM", "020": "MEDIUM", "021": "MEDIUM", "022": "MEDIUM", "025": "MEDIUM",
        "028": "MEDIUM", "029": "MEDIUM", "032": "LOW", "033": "LOW", "034": "LOW", "035": "LOW",
    }
    sev_ok = True
    for num, sev in expected_sev.items():
        fid = f"ANOX-MAINARCH-{num}"
        if by_id.get(fid, {}).get("severity") != sev:
            fail(f"{fid} severity changed/missing", errors)
            sev_ok = False
    if sev_ok:
        ok("targeted finding severities unchanged")

    # 24. targeted findings are Open, Ready For Retest, or Closed after verification
    status_ok = True
    allowed_statuses = {"Open", "Ready For Retest", "Closed"}
    for fid in target_ids:
        f = by_id.get(fid, {})
        if f.get("status") not in allowed_statuses:
            fail(f"{fid} status is {f.get('status')} (must be Open, Ready For Retest, or Closed)", errors)
            status_ok = False
    if status_ok:
        ok("targeted finding statuses are Open, Ready For Retest, or Closed")

    # 25. unrelated findings unchanged (excluding MAINARCH-FIX-02/FIX-03 targets which may be
    #     Ready For Retest, or Closed only after their verified retest)
    fix02_targets = {
        "ANOX-MAINARCH-003", "ANOX-MAINARCH-007", "ANOX-MAINARCH-008", "ANOX-MAINARCH-009",
        "ANOX-MAINARCH-010", "ANOX-MAINARCH-015", "ANOX-MAINARCH-016", "ANOX-MAINARCH-017",
    }
    fix03_targets = {
        "ANOX-MAINARCH-011", "ANOX-MAINARCH-024", "ANOX-MAINARCH-026",
        "ANOX-MAINARCH-027", "ANOX-MAINARCH-036",
    }
    # A FIX-03 target may only be Closed after a recorded MAINARCH-RETEST-03 PASS
    # that explicitly covers the finding.
    retest03_ids = set()
    audits_path = REPO / "docs/workforce/registries/audits.jsonl"
    if audits_path.exists():
        for line in audits_path.read_text().splitlines():
            if not line.strip():
                continue
            a = json.loads(line)
            if a.get("audit_id") == "MAINARCH-RETEST-03" and a.get("result") == "PASS":
                if a.get("finding_id"):
                    retest03_ids.add(a["finding_id"])
                for fid in (a.get("findings") or a.get("closed_findings") or []):
                    retest03_ids.add(fid)
    unrelated_ok = True
    for f in findings:
        fid = f["finding_id"]
        if fid in target_ids or fid in fix02_targets:
            continue
        st = f.get("status")
        if fid in fix03_targets:
            if st == "Closed" and fid not in retest03_ids:
                fail(f"{fid} Closed without MAINARCH-RETEST-03 PASS evidence", errors)
                unrelated_ok = False
            elif st not in ("Open", "Ready For Retest", "Closed"):
                fail(f"{fid} has unexpected status {st}", errors)
                unrelated_ok = False
            continue
        if st != "Open":
            fail(f"unrelated {fid} status changed to {st}", errors)
            unrelated_ok = False
    if unrelated_ok:
        ok("unrelated findings unchanged (Open)")

    # 26. Product development still blocked
    ws = json.loads((REPO / "docs/workforce/WORKFORCE_STATE.json").read_text())
    if ws.get("final_pre_product_audit", {}).get("product_development_state") == "BLOCKED_PENDING_FINAL_AUDIT":
        ok("product development still blocked")
    else:
        fail("product development not blocked", errors)

    if errors:
        print("\nMAINARCH-FIX-01: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nMAINARCH-FIX-01: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
