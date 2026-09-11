#!/usr/bin/env python3
"""Security Hardening audit evidence-preservation validator.

Fail-closed verification for SECURITY-AUDIT-EVIDENCE-PRESERVATION-001:
the five preserved audit reports, the audit-evidence registry, the
traceability layer, and the lifecycle state that must remain unchanged.

Set SECURITY_AUDIT_PRESERVATION_REPO to validate an alternate tree
(test fixtures); git-dependent checks are skipped when no .git exists.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("SECURITY_AUDIT_PRESERVATION_REPO") or Path(__file__).resolve().parents[2])
EVIDENCE_DIR = REPO_ROOT / "docs" / "security" / "audit-evidence"
REPORTS_DIR = REPO_ROOT / "docs" / "reports" / "security" / "audits"
REGISTRY_DIR = REPO_ROOT / "docs" / "workforce" / "registries"
BASE_SHA = "869b99acac040412a29bbaadc76342070fb2085c"
DELIVERY_BRANCH = "governance/security-audit-evidence-preservation-001"
TASK_ID = "ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-001"
NEXT_GATE_ID = "AUDIT-SECURITY-CRYPTO-JNI-001"
LEDGER_EVENT = "ANOX-EVENT-0045"

EXPECTED_REPORTS = {
    "AUDIT-SECURITY-ARCHITECTURE": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-ARCHITECTURE.md",
        "sha256": "da230ac1a3f623eba559c31641e52ffd2fc5487502d4c6ad2ccbbc1f9eb6dfe6",
    },
    "AUDIT-SECURITY-CODEBASE-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md",
        "sha256": "122d0aae9c1b64d060010092bea77f4d9c3466c5df2d10ccf56955bc4987f153",
    },
    "AUDIT-SECURITY-CODEBASE-002": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-002.md",
        "sha256": "2ce279637bea62c79ced6614318c1fe79fcdc1b30b33519aeb7b2d426d4c09d5",
    },
    "CODEBASE-SECURITY-CONSENSUS-001": {
        "path": "docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md",
        "sha256": "66ea13d75982e83fdb9b316f3b95c0aef4b1fae9604d5e6457abb33e40898f8c",
    },
    "AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001.md",
        "sha256": "6afdd091d64ec9a30d40f8ba4e0fbe73bfb4812f105993bdbb42b49895acda1a",
    },
}

EXPECTED_AUDITS = {
    "ANOX-AUDIT-SECURITY-ARCH-001": {
        "audit_type": "FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT",
        "provider": "Anthropic via Devin CLI / Cognition",
        "actual_model": "Claude Opus 5 High",
        "audited_sha": "c653a1d6a302758c0e006225987281643957f752",
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 11, "critical_count": 0, "high_count": 5,
        "medium_count": 3, "low_count": 2, "info_count": 1,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-CODEBASE-001": {
        "audit_type": "READ_ONLY_FULL_EXISTING_CODEBASE_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Opus 5 Medium",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 21, "critical_count": 1, "high_count": 3,
        "medium_count": 8, "low_count": 7, "info_count": 2,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-CODEBASE-002": {
        "audit_type": "READ_ONLY_BLIND_INDEPENDENT_FULL_CODEBASE_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 17, "critical_count": 0, "high_count": 3,
        "medium_count": 6, "low_count": 6, "info_count": 2,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "YES", "blindness_status_prefix": "PRESERVED",
    },
    "CODEBASE-SECURITY-CONSENSUS-001": {
        "audit_type": "CONSENSUS_ANALYSIS_AND_ARBITRATION",
        "provider": "Anthropic",
        "actual_model": "Claude Opus 5 High",
        "audited_sha": BASE_SHA,
        "result": "PASS",
        "candidate_count": 18,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001": {
        "audit_type": "READ_ONLY_BUILD_NATIVE_PROVENANCE_SUPPLY_CHAIN_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 12, "critical_count": 0, "high_count": 3,
        "medium_count": 5, "low_count": 3, "info_count": 1,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
}

A1_SEVERITY = {"C-003": "CRITICAL"}
for _c in ("C-001", "C-002", "C-004"):
    A1_SEVERITY[_c] = "HIGH"
for _c in ("C-005", "C-006", "C-007", "C-008", "C-009", "C-010", "C-011", "C-012"):
    A1_SEVERITY[_c] = "MEDIUM"
for _c in ("C-013", "C-014", "C-015", "C-016", "C-017", "C-018", "C-019"):
    A1_SEVERITY[_c] = "LOW"
for _c in ("C-020", "C-021"):
    A1_SEVERITY[_c] = "INFO"
A1_IDS = {f"C-{i:03d}" for i in range(1, 22)}

A2_SEVERITY = {"C-001": "HIGH", "C-002": "HIGH", "C-003": "HIGH"}
for _c in ("C-004", "C-005", "C-006", "C-007", "C-008", "C-009"):
    A2_SEVERITY[_c] = "MEDIUM"
for _c in ("C-010", "C-011", "C-012", "C-013", "C-014", "C-015"):
    A2_SEVERITY[_c] = "LOW"
for _c in ("C-016", "C-017"):
    A2_SEVERITY[_c] = "INFO"
A2_IDS = {f"C-{i:03d}" for i in range(1, 18)}

ROOT_IDS = {f"ROOT-{i:03d}" for i in range(1, 19)}
PRE_B004_ROOTS = [
    "ROOT-001", "ROOT-002", "ROOT-003", "ROOT-004", "ROOT-005", "ROOT-006",
    "ROOT-007", "ROOT-008", "ROOT-009", "ROOT-013", "ROOT-014", "ROOT-017",
]
B008_B009_ROOTS = ["ROOT-010", "ROOT-011", "ROOT-012"]
FPG_ROOTS = ["ROOT-012", "ROOT-015"]

BUILDSC_SEVERITY = {
    "ANOX-BUILDSC-CANDIDATE-001": "HIGH", "ANOX-BUILDSC-CANDIDATE-002": "HIGH",
    "ANOX-BUILDSC-CANDIDATE-003": "HIGH",
    "ANOX-BUILDSC-CANDIDATE-004": "MEDIUM", "ANOX-BUILDSC-CANDIDATE-005": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-006": "MEDIUM", "ANOX-BUILDSC-CANDIDATE-007": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-008": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-009": "LOW", "ANOX-BUILDSC-CANDIDATE-010": "LOW",
    "ANOX-BUILDSC-CANDIDATE-011": "LOW", "ANOX-BUILDSC-CANDIDATE-012": "INFO",
}
BUILDSC_IDS = set(BUILDSC_SEVERITY)

METADATA_ALLOWLIST = {
    "PROJECT_STATE.md", "FORTSCHRITT.md", "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
    "docs/continuity/CURRENT_STATE.json", "docs/continuity/CURRENT_GIT_STATE.md",
    "docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_OPEN_WORK.md",
    "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
    "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
    "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
    "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
    "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
    "docs/workforce/registries/decisions.jsonl", "docs/workforce/registries/findings.jsonl",
    "docs/workforce/registries/tasks.jsonl", "docs/workforce/registries/runs.jsonl",
    "docs/workforce/registries/audits.jsonl", "docs/workforce/registries/derived_work.jsonl",
    "docs/workforce/WORKFORCE_STATE.json", "docs/workforce/WORKFORCE_STATE_SNAPSHOT.json",
}
FORBIDDEN_PREFIXES = ("android/", "crypto/rust/", "backend/", ".github/workflows/", "supabase/", "migrations/")


def fail(msg, errors):
    errors.append(msg)


def load_jsonl(path):
    r = []
    if not path.exists():
        return r
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r.append(json.loads(line))
    return r


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _rev_parse(ref):
    out = subprocess.run(["git", "rev-parse", ref], cwd=REPO_ROOT, capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def has_git():
    return (REPO_ROOT / ".git").is_dir()


def validate_base(errors):
    if not has_git():
        print("  SKIP git checks (no .git — fixture mode)")
        return
    sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
    import lifecycle_legality as ll
    head = _rev_parse("HEAD")
    if not ll._git_is_ancestor(BASE_SHA, head, cwd=REPO_ROOT):
        fail(f"base {BASE_SHA} not ancestor of {head}", errors)
        return
    print(f"  OK   base {BASE_SHA[:12]} is ancestor of {head[:12]}")
    state = load_json(REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json")
    described = state.get("described_head") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", described):
        fail(f"CURRENT_STATE described_head is not a valid SHA: {described}", errors)
        return
    ok, _, _, reason = ll.canonical_two_commit_delivery(
        BASE_SHA, described, head,
        canonical_branch="main", delivery_branch=DELIVERY_BRANCH,
        cwd=REPO_ROOT, metadata_allowlist=METADATA_ALLOWLIST,
    )
    if not ok:
        fail(f"canonical two-commit delivery failed: {reason}", errors)
        return
    print("  OK   exactly 2 task-authored commits above base (merge-aware)")


def validate_reports(errors):
    hashes = {}
    hpath = EVIDENCE_DIR / "evidence_hashes.json"
    if not hpath.exists():
        fail("evidence_hashes.json missing", errors)
    else:
        try:
            hashes = (load_json(hpath).get("reports") or {})
        except Exception as e:
            fail(f"evidence_hashes.json unreadable: {e}", errors)
    for name, spec in EXPECTED_REPORTS.items():
        p = REPO_ROOT / spec["path"]
        if not p.exists():
            fail(f"preserved report missing: {spec['path']}", errors)
            continue
        actual = sha256_file(p)
        if actual != spec["sha256"]:
            fail(f"report {name} hash mismatch: {actual} != {spec['sha256']}", errors)
            continue
        rec = hashes.get(name) or {}
        if rec.get("sha256") != spec["sha256"]:
            fail(f"evidence_hashes.json entry for {name} mismatched/missing", errors)
        elif rec.get("source_present") != "YES":
            fail(f"evidence_hashes.json {name} source_present != YES", errors)
        else:
            print(f"  OK   {name} preserved byte-exact ({spec['sha256'][:16]}...)")
    src = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl") if (EVIDENCE_DIR / "audit_traceability.jsonl").exists() else []
    src_recs = [r for r in src if r.get("record_type") == "source_status"]
    for name in EXPECTED_REPORTS:
        rec = next((r for r in src_recs if r.get("audit_name") == name or r.get("audit_id") == name or EXPECTED_AUDITS.get(r.get("audit_id"), {}).get("audit_name") == name or r.get("audit_id") == EXPECTED_AUDITS.get(name, {}).get("audit_id")), None)
        if rec is None:
            # match by preserved_path
            rec = next((r for r in src_recs if r.get("preserved_path") == EXPECTED_REPORTS[name]["path"]), None)
        if rec is None:
            fail(f"source_status record missing for {name}", errors)
        elif rec.get("source_present") != "YES":
            fail(f"source_status for {name} is not YES", errors)


def validate_registry(errors):
    audits = {a.get("audit_id"): a for a in load_jsonl(EVIDENCE_DIR / "audit_registry.jsonl")}
    if not audits:
        fail("audit_registry.jsonl missing or empty", errors)
        return
    if len(audits) != 5:
        fail(f"audit_registry.jsonl must contain exactly 5 audits, found {len(audits)}", errors)
    for aid, spec in EXPECTED_AUDITS.items():
        rec = audits.get(aid)
        if rec is None:
            fail(f"audit registry missing {aid}", errors)
            continue
        for key, expected in spec.items():
            if key == "blindness_status_prefix":
                if not str(rec.get("blindness_status", "")).startswith(expected):
                    fail(f"{aid} blindness_status {rec.get('blindness_status')!r} lacks prefix {expected!r}", errors)
                continue
            if rec.get(key) != expected:
                fail(f"{aid} {key}={rec.get(key)!r}, expected {expected!r}", errors)
        rep = rec.get("report_path")
        if rep not in {s["path"] for s in EXPECTED_REPORTS.values()}:
            fail(f"{aid} report_path not a preserved report: {rep!r}", errors)
        if rec.get("report_sha256") != EXPECTED_REPORTS.get(rec.get("audit_name", ""), {}).get("sha256"):
            fail(f"{aid} report_sha256 mismatch vs evidence_hashes expectation", errors)
    a1 = audits.get("AUDIT-SECURITY-CODEBASE-001") or {}
    if "MODEL_DEVIATION" not in str(a1.get("model_requirement_status", "")):
        fail("AUDIT-SECURITY-CODEBASE-001 model_requirement_status must record MODEL_DEVIATION", errors)
    a2 = audits.get("AUDIT-SECURITY-CODEBASE-002") or {}
    if a2.get("blindness_status", "").startswith("PRESERVED"):
        print("  OK   Audit-002 blindness preserved")
    else:
        fail("AUDIT-SECURITY-CODEBASE-002 blindness_status must start with PRESERVED", errors)
    print("  OK   audit registry records verified")


def validate_traceability(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")
    if not recs:
        fail("audit_traceability.jsonl missing or empty", errors)
        return

    a1 = [r for r in recs if r.get("record_type") == "audit001_candidate"]
    a1_refs = {r.get("consensus_ref") for r in a1}
    if len(a1) != 21 or a1_refs != A1_IDS:
        fail(f"Audit-001 traceability must cover 21/21 candidates; got {len(a1)}", errors)
    else:
        print("  OK   Audit-001 21/21 candidates traced")
    for r in a1:
        cref = r.get("consensus_ref")
        if A1_SEVERITY.get(cref) != r.get("severity"):
            fail(f"Audit-001 {cref} severity {r.get('severity')!r} != {A1_SEVERITY.get(cref)!r}", errors)
        if not r.get("consensus_roots"):
            fail(f"Audit-001 {cref} has no consensus_roots", errors)
    c19 = next((r for r in a1 if r.get("consensus_ref") == "C-019"), None)
    if c19 is None:
        fail("Audit-001 C-019 candidate missing from traceability", errors)
    elif c19.get("candidate_id") != "ANOX-CODESEC-CANDIDATE-019" or "ROOT-008" not in c19.get("consensus_roots", []):
        fail("Audit-001 C-019 traceability content wrong", errors)
    else:
        print("  OK   Audit-001 C-019 present and mapped")

    a2 = [r for r in recs if r.get("record_type") == "audit002_candidate"]
    a2_local = {r.get("audit_local_id") for r in a2}
    if len(a2) != 17 or a2_local != A2_IDS:
        fail(f"Audit-002 traceability must cover 17/17 candidates; got {len(a2)}", errors)
    else:
        print("  OK   Audit-002 17/17 candidates traced")
    for r in a2:
        lid = r.get("audit_local_id")
        if A2_SEVERITY.get(lid) != r.get("severity"):
            fail(f"Audit-002 {lid} severity {r.get('severity')!r} != {A2_SEVERITY.get(lid)!r}", errors)
        if not r.get("consensus_roots"):
            fail(f"Audit-002 {lid} has no consensus_roots", errors)

    roots = {r.get("root_id"): r for r in recs if r.get("record_type") == "consensus_root"}
    if set(roots) != ROOT_IDS:
        fail(f"consensus roots must be exactly ROOT-001..018; got {sorted(roots)}", errors)
    else:
        print("  OK   18 consensus roots ROOT-001..018")
    r5 = roots.get("ROOT-005") or {}
    if r5.get("audit001_sources"):
        fail("ROOT-005 has a fabricated Audit-001 source candidate", errors)
    elif r5.get("audit002_sources") != ["C-003"]:
        fail("ROOT-005 audit002_sources must be [C-003]", errors)
    else:
        print("  OK   ROOT-005 has no Audit-001 source (SINGLE_AUDIT_CONFIRMED_BY_ARBITER)")
    r16 = roots.get("ROOT-016") or {}
    if r16.get("status") != "REJECTED_NOT_A_FINDING" or r16.get("severity") != "NONE":
        fail("ROOT-016 must remain REJECTED_NOT_A_FINDING / severity NONE", errors)
    else:
        print("  OK   ROOT-016 remains rejected, not a real finding")
    for rid in ("ROOT-001", "ROOT-002", "ROOT-003", "ROOT-004", "ROOT-005"):
        if (roots.get(rid) or {}).get("severity") != "HIGH":
            fail(f"{rid} must be HIGH", errors)

    gates = {g.get("gate"): g for g in recs if g.get("record_type") == "gate_set"}
    pre = gates.get("PRE_B004_ROOTS") or {}
    if sorted(pre.get("roots") or []) != sorted(PRE_B004_ROOTS):
        fail(f"PRE_B004_ROOTS set wrong: {pre.get('roots')}", errors)
    else:
        print("  OK   12-root Pre-B004 set exact")
    if sorted((gates.get("B008_B009_ROOTS") or {}).get("roots") or []) != sorted(B008_B009_ROOTS):
        fail("B008_B009_ROOTS set wrong", errors)
    if sorted((gates.get("FINAL_PRODUCT_GATE_ROOTS") or {}).get("roots") or []) != sorted(FPG_ROOTS):
        fail("FINAL_PRODUCT_GATE_ROOTS set wrong", errors)

    bs = {r.get("candidate_id"): r for r in recs if r.get("record_type") == "buildsc_candidate"}
    if set(bs) != BUILDSC_IDS:
        fail(f"Build/Supply traceability must cover 12/12 candidates; got {sorted(bs)}", errors)
    else:
        print("  OK   Build/Supply 12/12 candidates traced")
    for cid, sev in BUILDSC_SEVERITY.items():
        if (bs.get(cid) or {}).get("severity") != sev:
            fail(f"{cid} severity {(bs.get(cid) or {}).get('severity')!r} != {sev!r}", errors)
    b1 = bs.get("ANOX-BUILDSC-CANDIDATE-001") or {}
    if b1.get("evidence_integrity") != "CRITICAL":
        fail("ANOX-BUILDSC-CANDIDATE-001 must carry EVIDENCE_INTEGRITY=CRITICAL", errors)
    else:
        print("  OK   BUILDSC-001 EVIDENCE_INTEGRITY=CRITICAL preserved")

    rels = {r.get("finding_id"): r for r in recs if r.get("record_type") == "historical_relation"}
    c5 = rels.get("ANOX-LEGACY-CRYPTO-005") or {}
    if c5.get("relationship") != "LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION" or c5.get("canonical_status") != "Closed":
        fail("historical relation ANOX-LEGACY-CRYPTO-005 must be Closed + LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION", errors)
    i5 = rels.get("ANOX-LEGACY-INTEGRATION-005") or {}
    if i5.get("relationship") != "NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING" or i5.get("canonical_status") != "Open":
        fail("historical relation ANOX-LEGACY-INTEGRATION-005 must be Open + NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING", errors)

    ng = next((r for r in recs if r.get("record_type") == "next_gate"), None)
    if not ng or ng.get("gate") != NEXT_GATE_ID or "NOT_EXECUTED" not in str(ng.get("status", "")):
        fail(f"next_gate record must be {NEXT_GATE_ID} CANDIDATE / NOT_EXECUTED", errors)


def validate_findings(errors):
    findings = load_jsonl(REGISTRY_DIR / "findings.jsonl")
    f5 = next((f for f in findings if f.get("finding_id") == "ANOX-LEGACY-CRYPTO-005"), None)
    if f5 is None:
        fail("ANOX-LEGACY-CRYPTO-005 missing from findings.jsonl", errors)
    else:
        if f5.get("status") != "Closed":
            fail(f"ANOX-LEGACY-CRYPTO-005 must remain Closed, got {f5.get('status')!r}", errors)
        if not f5.get("closure_actor") or not f5.get("closure_evidence"):
            fail("ANOX-LEGACY-CRYPTO-005 closure evidence/actor removed", errors)
        if "LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION" not in str(f5.get("notes", "")):
            fail("ANOX-LEGACY-CRYPTO-005 lacks the preserved LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION relationship note", errors)
        if f5.get("status") == "Closed":
            print("  OK   ANOX-LEGACY-CRYPTO-005 remains Closed with preserved relationship")
    i5 = next((f for f in findings if f.get("finding_id") == "ANOX-LEGACY-INTEGRATION-005"), None)
    if i5 is None or i5.get("status") != "Open":
        fail("ANOX-LEGACY-INTEGRATION-005 must remain Open", errors)
    else:
        print("  OK   ANOX-LEGACY-INTEGRATION-005 remains Open")
    for fid in ("ANOX-MAINARCH-013", "ANOX-MAINARCH-018", "ANOX-MAINARCH-030", "ANOX-LEGACY-B003-001"):
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") not in ("Open", "Ready For Retest"):
            fail(f"existing product finding {fid} must remain Open/Ready For Retest", errors)


def validate_lifecycle(errors):
    ws_path = REGISTRY_DIR.parent / "WORKFORCE_STATE.json"
    if not ws_path.exists():
        fail("WORKFORCE_STATE.json missing", errors)
        return
    ws = load_json(ws_path)
    if ws.get("product_development_state") != "BLOCKED_PENDING_FINAL_AUDIT":
        fail("product_development_state must remain BLOCKED_PENDING_FINAL_AUDIT", errors)
    else:
        print("  OK   product remains BLOCKED_PENDING_FINAL_AUDIT")
    ir = load_json(REGISTRY_DIR / "implementation_readiness.json")
    for dom in ("B-004", "B-005"):
        st = ((ir.get("domains") or {}).get(dom) or {}).get("implementation_state")
        if st != "NOT_STARTED":
            fail(f"{dom} implementation_state must remain NOT_STARTED, got {st!r}", errors)
    print("  OK   B-004 and B-005 remain NOT_STARTED")
    nxt = ws.get("next_phase") or (ws.get("final_pre_product_audit") or {}).get("next_phase")
    if nxt != NEXT_GATE_ID:
        fail(f"next_phase must be {NEXT_GATE_ID}, got {nxt!r}", errors)
    else:
        print(f"  OK   next gate {NEXT_GATE_ID} recorded")
    completed = set((ws.get("final_pre_product_audit") or {}).get("completed_audit_ids") or [])
    if NEXT_GATE_ID in completed:
        fail(f"{NEXT_GATE_ID} must not be in completed_audit_ids", errors)
    post = (ws.get("post_merge_state") or {}).get("current_gate", "")
    if NEXT_GATE_ID not in post or "CANDIDATE" not in post.upper() and "Candidate" not in post:
        fail("post_merge_state gate must record AUDIT-SECURITY-CRYPTO-JNI-001 as Candidate", errors)


def validate_tasks(errors):
    tasks = load_jsonl(REGISTRY_DIR / "tasks.jsonl")
    t = next((x for x in tasks if x.get("task_id") == TASK_ID), None)
    if t is None:
        fail(f"{TASK_ID} missing from tasks.jsonl", errors)
    else:
        if t.get("status") != "Ready For Remote":
            fail(f"{TASK_ID} status {t.get('status')!r}, expected Ready For Remote", errors)
        if t.get("start_sha") != BASE_SHA:
            fail(f"{TASK_ID} start_sha must be {BASE_SHA}", errors)
        if t.get("branch") != DELIVERY_BRANCH:
            fail(f"{TASK_ID} branch must be {DELIVERY_BRANCH}", errors)
    for x in tasks:
        blob = (x.get("task_id", "") + " " + x.get("title", "")).upper()
        if "CRYPTO-JNI" in blob or "CRYPTO_JNI" in blob or "CRYPTOJNI" in blob:
            if x.get("status") not in ("Candidate",):
                fail(f"Crypto/JNI audit task {x.get('task_id')} is {x.get('status')!r} — must remain Candidate/NOT_EXECUTED", errors)
    print("  OK   Crypto/JNI gate is a candidate, not executed")


def validate_no_product_changes(errors):
    if not has_git():
        return
    out = subprocess.run(["git", "diff", "--name-only", BASE_SHA], cwd=REPO_ROOT, capture_output=True, text=True)
    changed = out.stdout.strip().splitlines()
    forbidden = [p for p in changed if p.startswith(FORBIDDEN_PREFIXES) or p.endswith(".sql")]
    jni = [p for p in changed if "jni" in p.lower() or "AndroidManifest" in p or p.endswith(".so") or "gradle" in p.lower()]
    bad = sorted(set(forbidden + jni))
    if bad:
        fail(f"product/CI/native paths changed: {bad}", errors)
    else:
        print("  OK   no product/CI/native changes")


def validate_project_memory(errors):
    state_path = REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json"
    ledger_path = REPO_ROOT / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl"
    if not state_path.exists() or not ledger_path.exists():
        fail("continuity surfaces missing", errors)
        return
    state = load_json(state_path)
    ledger = load_jsonl(ledger_path)
    if not ledger:
        fail("ledger empty", errors)
        return
    latest = ledger[-1]
    if state.get("latest_material_event_id") != latest.get("event_id"):
        fail("Project Memory stale: latest_material_event_id != last ledger event", errors)
    elif latest.get("event_id") != LEDGER_EVENT:
        fail(f"last ledger event must be {LEDGER_EVENT}, got {latest.get('event_id')}", errors)
    else:
        print(f"  OK   Project Memory synced to {latest.get('event_id')}")


def main():
    errors = []
    print("[EVIDENCE-PRESERVATION] Base / delivery")
    validate_base(errors)
    print("\n[EVIDENCE-PRESERVATION] Preserved reports / hashes / source status")
    validate_reports(errors)
    print("\n[EVIDENCE-PRESERVATION] Audit registry")
    validate_registry(errors)
    print("\n[EVIDENCE-PRESERVATION] Traceability / roots / gates")
    validate_traceability(errors)
    print("\n[EVIDENCE-PRESERVATION] Canonical findings / historical relations")
    validate_findings(errors)
    print("\n[EVIDENCE-PRESERVATION] Lifecycle state")
    validate_lifecycle(errors)
    validate_tasks(errors)
    print("\n[EVIDENCE-PRESERVATION] Scope / memory")
    validate_no_product_changes(errors)
    validate_project_memory(errors)
    if errors:
        print("\nSECURITY AUDIT EVIDENCE PRESERVATION: FAIL")
        for e in errors:
            print(f"  FAIL {e}")
        return 1
    print("\nSECURITY AUDIT EVIDENCE PRESERVATION: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
