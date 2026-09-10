#!/usr/bin/env python3
"""Security Architecture findings-freeze validator."""
import json, os, re, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("SECURITY_ARCH_FREEZE_REPO") or Path(__file__).resolve().parents[2])
REGISTRY_DIR = REPO_ROOT / "docs" / "workforce" / "registries"
REPORT_PATH = REPO_ROOT / "docs" / "reports" / "FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT.md"
AUDIT_ID = "ANOX-AUDIT-SECURITY-ARCH-001"
DECISION_ID = "ANOX-DECISION-SECARCHHARDENING001"
BASE_SHA = "c653a1d6a302758c0e006225987281643957f752"
EXPECTED_CANDIDATES = {
    "CANDIDATE-001", "CANDIDATE-002", "CANDIDATE-003", "CANDIDATE-004",
    "CANDIDATE-005", "CANDIDATE-006", "CANDIDATE-007", "CANDIDATE-008",
    "CANDIDATE-009", "CANDIDATE-010", "CANDIDATE-011",
}
PROMOTED = [
    "ANOX-SECURITY-ARCH-001", "ANOX-SECURITY-ARCH-002", "ANOX-SECURITY-ARCH-003",
    "ANOX-SECURITY-ARCH-004", "ANOX-SECURITY-ARCH-005", "ANOX-SECURITY-ARCH-006",
    "ANOX-SECURITY-ARCH-007", "ANOX-SECURITY-ARCH-008", "ANOX-SECURITY-ARCH-009",
    "ANOX-SECURITY-ARCH-010",
]
EXPECTED_SEVERITY = {
    "ANOX-SECURITY-ARCH-001": "HIGH", "ANOX-SECURITY-ARCH-002": "HIGH",
    "ANOX-SECURITY-ARCH-003": "HIGH", "ANOX-SECURITY-ARCH-004": "HIGH",
    "ANOX-SECURITY-ARCH-005": "MEDIUM", "ANOX-SECURITY-ARCH-006": "MEDIUM",
    "ANOX-SECURITY-ARCH-007": "MEDIUM", "ANOX-SECURITY-ARCH-008": "LOW",
    "ANOX-SECURITY-ARCH-009": "LOW", "ANOX-SECURITY-ARCH-010": "INFO",
}
PERMITTED_DISPOSITIONS = {"PROMOTE_CANONICAL", "MERGE_INTO_EXISTING"}
B004_BLOCKING = {"ANOX-SECURITY-ARCH-001", "ANOX-SECURITY-ARCH-002", "ANOX-SECURITY-ARCH-003", "ANOX-SECURITY-ARCH-004"}

def fail(msg, errors):
    errors.append(msg)

def load_jsonl(path):
    r=[]
    if not path.exists(): return r
    for l in path.read_text(encoding="utf-8").splitlines():
        if l.strip(): r.append(json.loads(l))
    return r

def load_json(path):
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def _rev_parse(ref):
    out = subprocess.run(["git","rev-parse",ref], cwd=REPO_ROOT, capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None

def validate_base(errors):
    import sys
    sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
    import lifecycle_legality as ll
    head = _rev_parse("HEAD")
    if not ll._git_is_ancestor(BASE_SHA, head, cwd=REPO_ROOT):
        fail(f"base {BASE_SHA} not ancestor of {head}", errors); return
    print(f"  OK   base {BASE_SHA[:12]} is ancestor of {head[:12]}")
    state = load_json(REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json")
    described = state.get("described_head") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", described):
        fail(f"CURRENT_STATE described_head is not a valid SHA: {described}", errors); return
    ok, _, _, reason = ll.canonical_two_commit_delivery(
        BASE_SHA, described, head,
        canonical_branch="main", delivery_branch="governance/security-architecture-findings-freeze",
        cwd=REPO_ROOT, metadata_allowlist={
            "PROJECT_STATE.md", "FORTSCHRITT.md", "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
            "docs/continuity/CURRENT_STATE.json", "docs/continuity/CURRENT_GIT_STATE.md",
            "docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_OPEN_WORK.md",
            "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md", "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
            "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md", "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
            "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md", "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
            "docs/workforce/registries/decisions.jsonl", "docs/workforce/registries/findings.jsonl",
            "docs/workforce/registries/tasks.jsonl", "docs/workforce/registries/runs.jsonl",
            "docs/workforce/registries/audits.jsonl", "docs/workforce/registries/derived_work.jsonl",
            "docs/workforce/WORKFORCE_STATE.json", "docs/workforce/WORKFORCE_STATE_SNAPSHOT.json",
        }
    )
    if not ok:
        fail(f"canonical two-commit delivery failed: {reason}", errors); return
    print("  OK   exactly 2 task-authored commits above base (merge-aware)")

def validate_audit(errors):
    audits = load_jsonl(REGISTRY_DIR / "audits.jsonl")
    rec = next((a for a in audits if a.get("audit_id") == AUDIT_ID), None)
    if not rec: fail(f"audit {AUDIT_ID} missing", errors); return
    print(f"  OK   audit {AUDIT_ID} exists")
    for k,v in [("audit_type","FINAL"),("canonical_sha",BASE_SHA),("role_id","ROLE-009"),("result","PASS_WITH_FINDINGS")]:
        if rec.get(k) != v: fail(f"{AUDIT_ID} {k}={rec.get(k)!r}, expected {v!r}", errors)
    cands = rec.get("source_candidates", [])
    cids = {c.get("candidate_id") for c in cands}
    missing = EXPECTED_CANDIDATES - cids
    extra = cids - EXPECTED_CANDIDATES
    if missing: fail(f"candidates missing: {sorted(missing)}", errors)
    if extra: fail(f"unexpected candidates: {sorted(extra)}", errors)
    if not missing and not extra: print("  OK   exactly 11 source candidates")
    for c in cands:
        d = c.get("disposition")
        if d not in PERMITTED_DISPOSITIONS:
            fail(f"candidate {c.get('candidate_id')} invalid disposition {d!r}", errors)
    c006 = next((c for c in cands if c.get("candidate_id")=="CANDIDATE-006"), {})
    if c006.get("disposition") != "MERGE_INTO_EXISTING" or c006.get("merge_target") != "ANOX-SECURITY-ARCH-001":
        fail("CANDIDATE-006 not merged into ANOX-SECURITY-ARCH-001", errors)
    else: print("  OK   CANDIDATE-006 merged into ANOX-SECURITY-ARCH-001")
    if rec.get("security_reassessment") != "NO NEW SECURITY AUDIT REQUIRED":
        fail("security reassessment not NO NEW SECURITY AUDIT REQUIRED", errors)
    else: print("  OK   security reassessment recorded as NO")

def validate_findings(errors):
    findings = load_jsonl(REGISTRY_DIR / "findings.jsonl")
    fids = {f.get("finding_id") for f in findings}
    for fid in PROMOTED:
        if fid not in fids: fail(f"promoted finding {fid} missing", errors)
    for f in findings:
        if f.get("finding_id") in PROMOTED:
            if f.get("status") != "Open":
                fail(f"promoted {f['finding_id']} not Open", errors)
            if EXPECTED_SEVERITY.get(f["finding_id"]) != f.get("severity"):
                fail(f"{f['finding_id']} severity {f.get('severity')} != {EXPECTED_SEVERITY.get(f['finding_id'])}", errors)
    print("  OK   10 canonical findings Open with correct severity")
    for fid in B004_BLOCKING:
        f = next((x for x in findings if x.get("finding_id") == fid), {})
        if f.get("severity") != "HIGH":
            fail(f"B004 blocker {fid} not HIGH", errors)
    print("  OK   B-004 blocking set is all HIGH")
    for fid in ["ANOX-MAINARCH-013","ANOX-MAINARCH-018","ANOX-MAINARCH-030","ANOX-LEGACY-INTEGRATION-005","ANOX-LEGACY-B003-001"]:
        f = next((x for x in findings if x.get("finding_id") == fid), {})
        if f.get("status") not in ("Open", "Ready For Retest"):
            fail(f"existing product finding {fid} not Open/Ready", errors)
    print("  OK   existing open product findings preserved")
    for fid in ["ANOX-MAINARCH-003","ANOX-MAINARCH-007","ANOX-MAINARCH-024"]:
        f = next((x for x in findings if x.get("finding_id") == fid), {})
        if f.get("milestone_security_review") != "PENDING":
            fail(f"milestone finding {fid} not PENDING", errors)
    print("  OK   milestone findings PENDING")

def validate_tasks(errors):
    tasks = load_jsonl(REGISTRY_DIR / "tasks.jsonl")
    audit = next((t for t in tasks if t.get("task_id") == "ANOX-TASK-SECURITY-ARCH-001"), {})
    if audit.get("status") != "Closed": fail("audit task not Closed", errors)
    else: print("  OK   ANOX-TASK-SECURITY-ARCH-001 Closed")
    freeze = next((t for t in tasks if t.get("task_id") == "ANOX-TASK-SECURITY-ARCH-FREEZE-001"), {})
    if freeze.get("status") != "Ready For Remote": fail("freeze task not Ready For Remote", errors)
    else: print("  OK   freeze task Ready For Remote")
    for t in tasks:
        if t.get("task_id") in ("ANOX-TASK-SECURITY-ARCH-001","ANOX-TASK-SECURITY-ARCH-FREEZE-001"):
            if t.get("start_sha") != BASE_SHA: fail(f"task {t['task_id']} start_sha wrong", errors)

def validate_product(errors):
    state = load_json(REGISTRY_DIR.parent / "WORKFORCE_STATE.json")
    if state.get("product_development_state") != "BLOCKED_PENDING_FINAL_AUDIT":
        fail("product not BLOCKED_PENDING_FINAL_AUDIT", errors)
    else: print("  OK   product blocked")
    fpa = state.get("final_pre_product_audit", {})
    if fpa.get("security_architecture_audit") != "COMPLETE_WITH_FINDINGS":
        fail("security_architecture_audit not COMPLETE_WITH_FINDINGS", errors)
    if AUDIT_ID not in fpa.get("completed_audit_ids", []):
        fail("audit not in completed_audit_ids", errors)
    print("  OK   workforce state records audit complete")

def validate_decision(errors):
    decs = load_jsonl(REGISTRY_DIR / "decisions.jsonl")
    d = next((x for x in decs if x.get("decision_id") == DECISION_ID), None)
    if not d: fail("Human hardening decision missing", errors)
    else: print("  OK   hardening decision present")

def validate_no_product_code(errors):
    out = subprocess.run(["git","diff","--name-only", BASE_SHA], cwd=REPO_ROOT, capture_output=True, text=True)
    changed = out.stdout.strip().splitlines()
    forbidden = [p for p in changed if p.startswith(("android/","crypto/rust/","backend/",".github/workflows/","supabase/","migrations/")) or p.endswith(".sql")]
    if forbidden: fail(f"product/CI/SQL paths changed: {forbidden}", errors)
    else: print("  OK   no product/CI/SQL changes")

def validate_report(errors):
    if not REPORT_PATH.exists(): fail("audit report missing", errors)
    else: print("  OK   audit report exists")

def validate_project_memory(errors):
    state = load_json(REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json")
    ledger = load_jsonl(REPO_ROOT / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl")
    if not ledger: fail("ledger empty", errors); return
    latest = ledger[-1]
    if state.get("latest_material_event_id") != latest.get("event_id"):
        fail("Project Memory stale", errors)
    else: print(f"  OK   Project Memory synced to {latest.get('event_id')}")

def main():
    errors=[]
    print("[SECARCH-FREEZE] Base / delivery")
    validate_base(errors)
    print("\n[SECARCH-FREEZE] Audit / candidates")
    validate_audit(errors)
    print("\n[SECARCH-FREEZE] Findings")
    validate_findings(errors)
    print("\n[SECARCH-FREEZE] Tasks")
    validate_tasks(errors)
    print("\n[SECARCH-FREEZE] Product / decision")
    validate_product(errors)
    validate_decision(errors)
    print("\n[SECARCH-FREEZE] Scope / report / memory")
    validate_no_product_code(errors)
    validate_report(errors)
    validate_project_memory(errors)
    if errors:
        print("\nSECARCH FINDINGS FREEZE: FAIL")
        for e in errors: print(f"  FAIL {e}")
        return 1
    print("\nSECARCH FINDINGS FREEZE: PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
