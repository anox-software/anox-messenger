#!/usr/bin/env python3
"""MAINARCH-FIX-02 deterministic validator.

Validates that the server/database/API/OTK/retention/privacy architecture
remediation is present and that the 8 targeted findings are in an allowed
post-remediation lifecycle state (Ready For Retest, or Closed with
MAINARCH-RETEST-02 closure evidence).

Hardened after MAINARCH-RETEST-02 identified deterministic weaknesses:

1. Severity preservation now compares each target finding against an explicit
   expected-severity mapping frozen from the original audit evidence, and
   cross-checks the severity text still present in the frozen Master Audit
   Report entries. A severity mutation now FAILs.
2. The product/CI scope check no longer uses ``git diff main HEAD`` (which is
   vacuous after merge). It pins the recorded FIX-02 base, substantive,
   metadata and canonical-merge SHAs, verifies merge ancestry, and evaluates
   the recorded delivery diff ``FIX02_BASE..FIX02_MERGE``.
3. Deterministic high-value semantic checks were added for properties the
   retest identified as materially important (B-002 replay window, DPoP
   replay vs application idempotency distinction, honest backup/PITR residual
   retention language, honest server-visible attachment ciphertext metadata,
   003/007 milestone flags).
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

# Expected severities for the 8 FIX-02 targets, frozen from the original
# AUDIT-MAIN-ARCHITECTURE evidence (findings registry + Master Audit Report
# entries at original audit SHA 0a4910eab1a92622383721100879cda46f924ca0).
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

# Recorded FIX-02 delivery SHAs. These are stable historical evidence; the
# scope check does not depend on the delivery branch still existing or on
# current main/HEAD position.
FIX02_BASE_SHA = "4ee8fe94c71923ae4be038fc250c9ac980ccc7c1"  # main before PR #12 (MAINARCH-RETEST-01-INGEST merge)
FIX02_SUBSTANTIVE_SHA = "568c8083a3e56058fcb6e5076a7fe1ebc15c384b"
FIX02_METADATA_SHA = "ced01aacb74678d3585af8e39f61c580b3343d4b"
FIX02_MERGE_SHA = "739ea1c36c3d6f8eedb9a315fc6fba5173a82289"  # canonical merge (PR #12)

V1_2 = "docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md"
B002 = "docs/authority/B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md"
MASTER_REPORT = "docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md"

DISALLOWED_PATTERNS = [
    r"^android/",
    r"^crypto/rust/",
    r"^backend/",
    r"^\.github/workflows/",
    r"\.kt$",
    r"\.rs$",
    r"\.gradle$",
    r"\.kts$",
    r"\.sql$",
    r"^migrations?/",
    r"^supabase/",
    r"^Cargo\.toml$",
    r"^build\.gradle",
    r"^settings\.gradle",
]


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def read_text(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def read_jsonl(rel):
    return [json.loads(l) for l in (REPO / rel).read_text().splitlines() if l.strip()]


def git(args):
    try:
        return subprocess.check_output(["git"] + args, cwd=REPO, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None


def git_is_ancestor(ancestor, descendant):
    return subprocess.call(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ) == 0


def git_diff_name_only(base, head):
    out = git(["diff", "--name-only", base, head])
    return [l for l in out.splitlines() if l] if out else []


def check_phrases(text, phrases, label, errors):
    missing = [p for p in phrases if p.lower() not in text.lower()]
    if missing:
        fail(f"{label} missing terms: {missing}", errors)
        return False
    ok(f"{label} contains all required terms")
    return True


def find_disallowed_files(paths):
    """Return the subset of changed paths that are prohibited FIX-02 scope."""
    return [f for f in paths if any(re.search(p, f) for p in DISALLOWED_PATTERNS)]


def check_target_severities(findings, master_text, errors):
    """Severity must equal the expected severity frozen from original audit
    evidence, and (defense in depth) must still agree with the severity text
    recorded in the Master Audit Report entries."""
    by_id = {f["finding_id"]: f for f in findings}
    ok_all = True
    for fid, expected in EXPECTED_SEVERITIES.items():
        f = by_id.get(fid)
        if f is None:
            fail(f"{fid} missing from findings registry", errors)
            ok_all = False
            continue
        actual = f.get("severity")
        if actual != expected:
            fail(f"{fid} severity changed: expected {expected}, found {actual}", errors)
            ok_all = False
            continue
        # Cross-check the frozen audit-report entry (format: **ANOX-... | SEV | ...)
        m = re.search(re.escape(fid) + r"\s*\|\s*([A-Z]+)", master_text)
        if m and m.group(1) != expected:
            fail(f"{fid} Master Audit Report severity {m.group(1)} != registry {expected}", errors)
            ok_all = False
    if ok_all:
        ok("Targeted finding severities match frozen audit evidence")
    return ok_all


def check_findings_status(findings, errors):
    """Targets must exist and be Ready For Retest, or Closed only with
    MAINARCH-RETEST-02 closure evidence."""
    by_id = {f["finding_id"]: f for f in findings}
    ok_all = True
    for fid in TARGETS:
        f = by_id.get(fid)
        if f is None:
            continue  # reported by severity/existence checks
        status = f.get("status")
        if status == "Ready For Retest":
            continue
        if status == "Closed":
            ev = " ".join(f.get("closure_evidence", []))
            if "MAINARCH-RETEST-02" not in ev:
                fail(f"{fid} Closed without MAINARCH-RETEST-02 closure evidence", errors)
                ok_all = False
            continue
        fail(f"{fid} has unexpected status {status}", errors)
        ok_all = False
    if ok_all:
        ok("All 8 target findings are Ready For Retest or Closed with RETEST-02 evidence")
    return ok_all


def check_fix02_delivery_scope(errors, changed=None):
    """Verify the recorded FIX-02 delivery (base..merge) contains no product,
    Rust, backend, SQL, or CI changes. Uses pinned historical SHAs so the
    check is deterministic post-merge and branch-independent."""
    if changed is None:
        for label, anc in (("substantive", FIX02_SUBSTANTIVE_SHA),
                           ("metadata", FIX02_METADATA_SHA)):
            if not git_is_ancestor(anc, FIX02_MERGE_SHA):
                fail(f"FIX-02 {label} commit {anc[:12]} is not an ancestor of merge {FIX02_MERGE_SHA[:12]}", errors)
                return False
        changed = git_diff_name_only(FIX02_BASE_SHA, FIX02_MERGE_SHA)
        if not changed:
            fail(f"Could not resolve FIX-02 delivery diff {FIX02_BASE_SHA[:12]}..{FIX02_MERGE_SHA[:12]}", errors)
            return False
    bad = find_disallowed_files(changed)
    if bad:
        fail(f"FIX-02 delivery contains prohibited product/CI/backend/SQL changes: {bad}", errors)
        return False
    ok("No product/CI/backend/SQL changes in recorded FIX-02 delivery")
    return True


def check_milestone_flags(v12_text, errors):
    """003/007 milestone Security Architecture review flags must exist."""
    ok_all = True
    if "Milestone Security Review" not in v12_text:
        fail("V1.2 milestone security review section missing", errors)
        ok_all = False
    for fid in MILESTONE_FLAGGED:
        if fid not in v12_text:
            fail(f"V1.2 milestone security review flag for {fid} missing", errors)
            ok_all = False
    if ok_all:
        ok("Milestone security review flags for 003/007 preserved")
    return ok_all


def check_b002_replay_window(b002_text, errors):
    """B-002 replay contract must remain intact: shared replay cache 5m."""
    if "shared replay cache" in b002_text.lower() and "5m" in b002_text:
        ok("B-002 shared replay cache 5m contract intact")
        return True
    fail("B-002 shared replay cache / 5m replay window contract missing", errors)
    return False


def check_dpop_idempotency_distinction(v12_text, errors):
    """Application idempotency must remain explicitly distinct from DPoP
    replay protection."""
    low = v12_text.lower()
    if "distinct from dpop replay" in low and "application-level" in low:
        ok("DPoP replay protection vs application idempotency distinction present")
        return True
    fail("V1.2 lost the explicit DPoP-replay vs application-idempotency distinction", errors)
    return False


def check_honest_backup_retention(v12_text, errors):
    """Backup/PITR residual retention must be explicitly distinguished from
    live deletion; the spec must forbid claiming instant global deletion."""
    low = v12_text.lower()
    required = [
        "residual",
        "pitr horizon",
        "base backup retention",
        "erasure journal",
        "instant global deletion",
    ]
    missing = [p for p in required if p not in low]
    if missing:
        fail(f"Honest backup/PITR residual-retention language missing terms: {missing}", errors)
        return False
    ok("Backup/PITR residual retention explicitly distinguished from live deletion")
    return True


def check_attachment_metadata_honesty(v12_text, errors):
    """The attachment contract must honestly admit server-visible ciphertext
    size/hash metadata (no impossible privacy claim)."""
    low = v12_text.lower()
    if "ciphertext_size" in low and "ciphertext_hash" in low:
        ok("Attachment contract admits server-visible ciphertext size/hash metadata")
        return True
    fail("V1.2 attachment contract no longer admits server-visible ciphertext size/hash", errors)
    return False


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
        fail("Cross-Domain consistency matrix missing", errors)

    # 11. Milestone security review flags (hardened)
    check_milestone_flags(v12_text, errors)

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

    # 14. Findings exist and are in an allowed post-remediation state
    findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {f["finding_id"]: f for f in findings}
    all_ids = set(by_id.keys())

    missing = TARGETS - all_ids
    if missing:
        fail(f"Missing target findings: {missing}", errors)
    else:
        ok("All 8 target findings exist")

    check_findings_status(findings, errors)

    # 15. Severity unchanged (hardened: explicit expected mapping + report cross-check)
    master = read_text(MASTER_REPORT)
    check_target_severities(findings, master, errors)

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
    if "## MAINARCH-FIX-02" in master:
        ok("Master Audit Report contains MAINARCH-FIX-02 section")
    else:
        fail("Master Audit Report missing MAINARCH-FIX-02 section", errors)

    # 18. No product/CI/backend/SQL changes in the recorded FIX-02 delivery
    #     (hardened: pinned base/merge SHAs, ancestry verified, not main..HEAD)
    check_fix02_delivery_scope(errors)

    # 19. Semantic spot-checks for retest-identified material properties
    check_b002_replay_window(read_text(B002), errors)
    check_dpop_idempotency_distinction(v12_text, errors)
    check_honest_backup_retention(v12_text, errors)
    check_attachment_metadata_honesty(v12_text, errors)

    # 20. Product blocked
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
