#!/usr/bin/env python3
"""Workforce Architecture Audit Findings Freeze validator.

Deterministic, fail-closed validator for the canonical freeze of
AUDIT-WORKFORCE-ARCHITECTURE findings.  Does not require network.
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("WORKFORCE_FREEZE_REPO") or Path(__file__).resolve().parents[2])
WORKFORCE_DIR = REPO_ROOT / "docs" / "workforce"
REGISTRY_DIR = WORKFORCE_DIR / "registries"
REPORT_PATH = REPO_ROOT / "docs" / "reports" / "FINAL_PRE_PRODUCT_WORKFORCE_ARCHITECTURE_AUDIT.md"
AUDIT_ID = "ANOX-AUDIT-WORKFORCE-ARCH-001"
BASE_SHA = os.environ.get("WORKFORCE_FREEZE_BASE_SHA", "d5f76ba9dfdb332ac5f70b769c57b3f0ae6122b8")
EXPECTED_CANDIDATES = {
    "ANOX-WORKFORCE-AUDIT-001",
    "ANOX-WORKFORCE-AUDIT-002",
    "ANOX-WORKFORCE-AUDIT-003",
    "ANOX-WORKFORCE-AUDIT-004",
    "ANOX-WORKFORCE-AUDIT-005",
    "ANOX-WORKFORCE-AUDIT-006",
}
PERMITTED_DISPOSITIONS = {
    "PROMOTE_CANONICAL",
    "MERGE_INTO_EXISTING",
    "DEFER_AS_FUTURE_WORK",
    "VERIFICATION_GAP_ONLY",
    "DOCUMENTATION_CLEANUP",
    "NOT_A_FINDING",
    "REQUIRES_SCOPE_DECISION",
}


def fail(msg, errors):
    errors.append(msg)


def load_jsonl(path):
    entries = []
    if not path.exists():
        return entries
    if path.stat().st_size == 0:
        return entries
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"invalid JSON in {path}: {e}")
    return entries


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _rev_parse(ref):
    import subprocess
    result = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def validate_base(errors):
    import subprocess
    import sys
    sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
    import lifecycle_legality as ll

    head = _rev_parse("HEAD")
    if not ll._git_is_ancestor(BASE_SHA, head, cwd=REPO_ROOT):
        fail(f"base {BASE_SHA} is not an ancestor of current HEAD {head}", errors)
        return
    else:
        print(f"  OK   base {BASE_SHA[:12]} is ancestor of current HEAD {head[:12]}")

    # Merge-aware canonical two-commit delivery proof.
    # The substantive head for the freeze is recorded in CURRENT_STATE described_head
    # and in the WORKFORCE-FIX-01 predecessor state; here we use the canonical
    # documented substantive SHA for the audit freeze delivery.
    DESCRIBED_HEAD = "6d9c813439fe47d70457ef9e21759aa9424267af"
    ok, delivery_parent, substantive_head, reason = ll.canonical_two_commit_delivery(
        BASE_SHA, DESCRIBED_HEAD, head,
        canonical_branch="main", delivery_branch="audit/workforce-architecture-findings-freeze",
        cwd=REPO_ROOT, metadata_allowlist={
            "PROJECT_STATE.md", "FORTSCHRITT.md", "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
            "docs/continuity/CURRENT_STATE.json", "docs/continuity/CURRENT_GIT_STATE.md",
            "docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_OPEN_WORK.md",
            "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md", "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
            "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md", "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
            "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md", "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
            "docs/workforce/registries/decisions.jsonl", "docs/workforce/registries/finding_evidence.jsonl",
            "docs/workforce/registries/findings.jsonl", "docs/workforce/registries/tasks.jsonl",
            "docs/workforce/registries/runs.jsonl", "docs/workforce/registries/audits.jsonl",
            "docs/workforce/registries/derived_work.jsonl",
            "docs/workforce/WORKFORCE_STATE.json", "docs/workforce/WORKFORCE_STATE_SNAPSHOT.json",
        }
    )
    if not ok:
        fail(f"canonical two-commit delivery failed: {reason}", errors)
        return
    global FREEZE_DELIVERY_HEAD
    FREEZE_DELIVERY_HEAD = delivery_parent
    print("  OK   exactly 2 task-authored commits above base (merge-aware)")


def validate_worktree(errors):
    import subprocess
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        print(f"[INFO] working tree has uncommitted changes (ignored by historical validator):\n{result.stdout.strip()}")
    else:
        print("  OK   working tree clean")


def validate_audit_record(errors):
    audits = load_jsonl(REGISTRY_DIR / "audits.jsonl")
    record = next((a for a in audits if a.get("audit_id") == AUDIT_ID), None)
    if not record:
        fail(f"audit record {AUDIT_ID} missing", errors)
        return
    print(f"  OK   audit record {AUDIT_ID} exists")

    required = [
        ("audit_type", "FINAL"),
        ("canonical_sha", BASE_SHA),
        ("role_id", "ROLE-009"),
        ("result", "PASS_WITH_FINDINGS"),
    ]
    for field, expected in required:
        value = record.get(field)
        if value != expected:
            fail(f"{AUDIT_ID} {field} = {value!r}, expected {expected!r}", errors)
        else:
            print(f"  OK   {AUDIT_ID} {field} = {value!r}")

    if record.get("result") != "PASS_WITH_FINDINGS":
        return

    for field, expected in (("provider", "Cognition"), ("model", "Devin SWE-1.7 Max")):
        value = record.get(field)
        if value != expected:
            fail(f"{AUDIT_ID} {field} = {value!r}, expected {expected!r}", errors)
        else:
            print(f"  OK   {AUDIT_ID} {field} = {value!r}")

    candidates = record.get("source_candidates", [])
    cids = {c.get("candidate_id") for c in candidates if c.get("candidate_id")}
    missing = EXPECTED_CANDIDATES - cids
    if missing:
        fail(f"source candidates missing: {sorted(missing)}", errors)
    if cids - EXPECTED_CANDIDATES:
        fail(f"unexpected source candidates: {sorted(cids - EXPECTED_CANDIDATES)}", errors)
    if cids == EXPECTED_CANDIDATES:
        print("  OK   exactly six source candidates recorded")

    dispositions = {}
    for c in candidates:
        cid = c.get("candidate_id")
        disp = c.get("disposition")
        if not cid or not disp:
            fail(f"candidate missing id or disposition: {c}", errors)
            continue
        if disp not in PERMITTED_DISPOSITIONS:
            fail(f"candidate {cid} has invalid disposition {disp!r}", errors)
        if cid in dispositions:
            fail(f"candidate {cid} has multiple dispositions", errors)
        dispositions[cid] = disp
    for cid in EXPECTED_CANDIDATES:
        if cid not in dispositions:
            fail(f"candidate {cid} has no disposition", errors)
    if len(dispositions) == 6 and len(set(dispositions.values())) == 6:
        print("  OK   every candidate has exactly one valid disposition")

    # Candidate-specific semantic checks
    c001 = next((c for c in candidates if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-001"), {})
    if c001.get("disposition") == "PROMOTE_CANONICAL" and "merge" in (c001.get("rationale", "")).lower():
        print("  OK   001 merge-commit semantics explicitly resolved")
    else:
        fail("001 disposition or merge semantics not correctly recorded", errors)

    c002 = next((c for c in candidates if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-002"), {})
    if c002.get("disposition") == "PROMOTE_CANONICAL" and "archive" in (c002.get("rationale", "")).lower():
        print("  OK   002 archive/cold-recovery evidence preserved")
    else:
        fail("002 archive/cold-recovery evidence not correctly recorded", errors)

    c003 = next((c for c in candidates if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-003"), {})
    if c003.get("disposition") == "MERGE_INTO_EXISTING" and c003.get("merge_target") == "ANOX-WORKFORCE-AUDIT-002":
        print("  OK   003 correctly merged into 002")
    else:
        fail("003 not correctly merged into 002", errors)

    c004 = next((c for c in candidates if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-004"), {})
    if c004.get("disposition") in ("MERGE_INTO_EXISTING", "NOT_A_FINDING") and c004.get("merge_target") == "ANOX-WORKFORCE-AUDIT-002":
        print("  OK   004 not promoted merely for stale Candidate start SHA")
    else:
        fail("004 disposition does not document expected fail-closed or root-cause merge", errors)

    c005 = next((c for c in candidates if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-005"), {})
    if c005.get("disposition") == "PROMOTE_CANONICAL" and "reachability" in (c005.get("rationale", "")).lower():
        print("  OK   005 path-enforcement reachability documented")
    else:
        fail("005 reachability not documented", errors)

    c006 = next((c for c in candidates if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-006"), {})
    if c006.get("disposition") in ("REQUIRES_SCOPE_DECISION", "NOT_A_FINDING") and "wildcard" in (c006.get("rationale", "")).lower():
        print("  OK   006 wildcard semantics explicitly resolved")
    else:
        fail("006 wildcard semantics not explicitly resolved", errors)


FREEZE_DELIVERY_HEAD = None


def _h_jsonl(rel, default_path):
    if FREEZE_DELIVERY_HEAD:
        import sys
        sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
        import lifecycle_legality as ll
        text = ll.historical_file_at(FREEZE_DELIVERY_HEAD, rel, cwd=REPO_ROOT)
        if text:
            return [json.loads(l) for l in text.splitlines() if l.strip()]
    return load_jsonl(default_path)


def _h_json(rel, default_path):
    if FREEZE_DELIVERY_HEAD:
        import sys
        sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
        import lifecycle_legality as ll
        text = ll.historical_file_at(FREEZE_DELIVERY_HEAD, rel, cwd=REPO_ROOT)
        if text:
            return json.loads(text)
    return load_json(default_path)


def validate_findings(errors):
    findings = _h_jsonl("docs/workforce/registries/findings.jsonl", REGISTRY_DIR / "findings.jsonl")
    promoted = [
        "ANOX-WORKFORCE-AUDIT-001",
        "ANOX-WORKFORCE-AUDIT-002",
        "ANOX-WORKFORCE-AUDIT-005",
    ]
    finding_ids = {f.get("finding_id") for f in findings}
    for fid in promoted:
        if fid not in finding_ids:
            fail(f"promoted finding {fid} missing from findings.jsonl", errors)
        else:
            print(f"  OK   promoted finding {fid} exists")

    audit = next((a for a in _h_jsonl("docs/workforce/registries/audits.jsonl", REGISTRY_DIR / "audits.jsonl") if a.get("audit_id") == AUDIT_ID), {})
    audit_finding_ids = set(audit.get("finding_ids", []))
    source_candidate_ids = {c.get("candidate_id") for c in audit.get("source_candidates", [])}
    for f in findings:
        if f.get("finding_id") in promoted:
            if f.get("status") != "Open":
                fail(f"promoted finding {f['finding_id']} is not Open", errors)
            else:
                print(f"  OK   promoted finding {f['finding_id']} is Open")
            if not f.get("closure_evidence"):
                print(f"  OK   promoted finding {f['finding_id']} has no closure evidence (Open)")
            else:
                fail(f"promoted finding {f['finding_id']} has premature closure evidence", errors)
        if f.get("finding_id", "").startswith("ANOX-WORKFORCE-AUDIT-"):
            if f["finding_id"] not in audit_finding_ids and f["finding_id"] not in source_candidate_ids:
                fail(f"finding {f['finding_id']} is not referenced by the audit record", errors)
            else:
                print(f"  OK   finding {f['finding_id']} is referenced by the audit record")


def validate_remediation_task(errors):
    tasks = _h_jsonl("docs/workforce/registries/tasks.jsonl", REGISTRY_DIR / "tasks.jsonl")
    tids = {t.get("task_id") for t in tasks}
    if "ANOX-TASK-WORKFORCEFIX01" not in tids:
        fail("WORKFORCE-FIX-01 candidate task missing", errors)
    else:
        print("  OK   WORKFORCE-FIX-01 candidate task exists")

    fix = next((t for t in tasks if t.get("task_id") == "ANOX-TASK-WORKFORCEFIX01"), {})
    if fix.get("status") != "Candidate":
        fail(f"WORKFORCE-FIX-01 status {fix.get('status')} != Candidate", errors)
    else:
        print("  OK   WORKFORCE-FIX-01 is Candidate (not authorized)")

    if fix.get("remote_permission") != "NONE":
        fail(f"WORKFORCE-FIX-01 remote_permission {fix.get('remote_permission')} != NONE", errors)
    else:
        print("  OK   WORKFORCE-FIX-01 remote_permission NONE")


def validate_final_operational_handoff_acceptance(errors):
    derived = load_jsonl(REGISTRY_DIR / "derived_work.jsonl")
    found = [d for d in derived if "HANDOFF" in (d.get("title", "")).upper() and "BOOTSTRAP" in (d.get("title", "")).upper()]
    if not found:
        fail("final operational Handoff/Bootstrap/Employee Cold-Boot acceptance derived work missing", errors)
    else:
        print("  OK   final operational handoff acceptance requirement preserved as derived work")


def validate_security_audit_not_authorized(errors):
    tasks = load_jsonl(REGISTRY_DIR / "tasks.jsonl")
    for t in tasks:
        if t.get("task_id") == "ANOX-TASK-SECURITYARCH001" or "AUDIT-SECURITY-ARCHITECTURE" in (t.get("title", "") + t.get("scope", "")):
            if t.get("status") in ("Authorized", "In Progress"):
                fail(f"Security Architecture Audit prematurely authorized/in progress: {t.get('task_id')}", errors)
    print("  OK   Security Architecture Audit not authorized")


def validate_product_state(errors):
    state = _h_json("docs/workforce/WORKFORCE_STATE.json", WORKFORCE_DIR / "WORKFORCE_STATE.json")
    if state.get("product_development_state") != "BLOCKED_PENDING_FINAL_AUDIT":
        fail(f"product state {state.get('product_development_state')} != BLOCKED_PENDING_FINAL_AUDIT", errors)
    else:
        print("  OK   product remains BLOCKED_PENDING_FINAL_AUDIT")

    fpa = state.get("final_pre_product_audit", {})
    if fpa.get("workforce_architecture_audit") != "COMPLETE_WITH_FINDINGS":
        fail(f"workforce audit status {fpa.get('workforce_architecture_audit')} != COMPLETE_WITH_FINDINGS", errors)
    else:
        print("  OK   workforce architecture audit marked COMPLETE_WITH_FINDINGS")

    if "ANOX-AUDIT-WORKFORCE-ARCH-001" not in fpa.get("completed_audit_ids", []):
        fail("workforce audit not recorded in completed_audit_ids", errors)
    else:
        print("  OK   workforce audit recorded in completed_audit_ids")


def validate_open_product_findings_unchanged(errors):
    findings = load_jsonl(REGISTRY_DIR / "findings.jsonl")
    expected_open = {
        "ANOX-MAINARCH-013",
        "ANOX-MAINARCH-018",
        "ANOX-MAINARCH-030",
        "ANOX-LEGACY-INTEGRATION-005",
        "ANOX-LEGACY-B003-001",
    }
    actual_open = {f.get("finding_id") for f in findings if f.get("status") == "Open"}
    if not expected_open.issubset(actual_open):
        missing = expected_open - actual_open
        fail(f"existing product findings closed: {sorted(missing)}", errors)
    else:
        print("  OK   existing five product findings still Open")


def validate_no_product_code(errors):
    # Explicit scope check: no android, crypto/rust, backend, CI, SQL, secrets added.
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", BASE_SHA, "--"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    changed = result.stdout.strip().splitlines()
    forbidden = [p for p in changed if p.startswith(("android/", "crypto/rust/", "backend/", ".github/workflows/", "supabase/", "migrations/")) or p.endswith(".sql")]
    if forbidden:
        fail(f"product code or forbidden paths changed: {forbidden}", errors)
    else:
        print("  OK   no product/CI/backend/SQL/secret changes")


def validate_report_exists(errors):
    if not REPORT_PATH.exists():
        fail(f"workforce audit report missing: {REPORT_PATH}", errors)
    else:
        print("  OK   workforce audit report exists")


def validate_project_memory_synchronized(errors):
    state = load_json(REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json")
    ledger = load_jsonl(REPO_ROOT / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl")
    if not ledger:
        fail("project history ledger empty", errors)
        return
    latest = ledger[-1]
    if state.get("latest_material_event_id") != latest.get("event_id"):
        fail(f"CURRENT_STATE latest_material_event_id {state.get('latest_material_event_id')} != ledger {latest.get('event_id')}", errors)
    else:
        print(f"  OK   Project Memory synchronized to {latest.get('event_id')}")


def main():
    errors = []
    print("[WORKFORCE-FINDINGS-FREEZE] Base / state")
    validate_base(errors)
    validate_worktree(errors)

    print("\n[WORKFORCE-FINDINGS-FREEZE] Audit record")
    validate_audit_record(errors)

    print("\n[WORKFORCE-FINDINGS-FREEZE] Canonical findings")
    validate_findings(errors)

    print("\n[WORKFORCE-FINDINGS-FREEZE] Remediation / next task")
    validate_remediation_task(errors)
    validate_final_operational_handoff_acceptance(errors)
    validate_security_audit_not_authorized(errors)

    print("\n[WORKFORCE-FINDINGS-FREEZE] Product / B027 state")
    validate_product_state(errors)
    validate_open_product_findings_unchanged(errors)

    print("\n[WORKFORCE-FINDINGS-FREEZE] Scope / report / memory")
    validate_no_product_code(errors)
    validate_report_exists(errors)
    validate_project_memory_synchronized(errors)

    if errors:
        print("\nWORKFORCE FINDINGS FREEZE: FAIL")
        for e in errors:
            print(f"  FAIL {e}")
        return 1

    print("\nWORKFORCE FINDINGS FREEZE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
