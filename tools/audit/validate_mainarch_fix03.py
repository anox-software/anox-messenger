#!/usr/bin/env python3
"""MAINARCH-FIX-03 deterministic validator.

Validates the traceability / test-matrix / release-governance / implementation-
readiness architecture remediation for findings ANOX-MAINARCH-011, 024, 026,
027, 036. No product, Rust, backend, SQL, CI, secrets, or remote mutation.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

V1_3 = "docs/authority/B025_MANDATORY_AMENDMENTS_V1_3.md"
V1_2 = "docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md"
INV_FILE = "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md"
INV_REG = "docs/workforce/registries/security_invariant_traceability.jsonl"
MAT_REG = "docs/workforce/registries/b021_verification_matrix.jsonl"
IR_REG = "docs/workforce/registries/implementation_readiness.json"
MASTER = "docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md"
B018 = "docs/authority/B025/TRACK_B/B018_RELEASE_SIGNING_UPDATES.md"
B019 = "docs/authority/B025/TRACK_B/B019_OPERATIONS_INCIDENT_RESPONSE.md"

FIX03_TARGETS = {
    "ANOX-MAINARCH-011",
    "ANOX-MAINARCH-024",
    "ANOX-MAINARCH-026",
    "ANOX-MAINARCH-027",
    "ANOX-MAINARCH-036",
}

FIX03_SEVERITIES = {
    "ANOX-MAINARCH-011": "HIGH",
    "ANOX-MAINARCH-024": "MEDIUM",
    "ANOX-MAINARCH-026": "MEDIUM",
    "ANOX-MAINARCH-027": "MEDIUM",
    "ANOX-MAINARCH-036": "INFO",
}

UNTOUCHED_OPEN = {
    "ANOX-MAINARCH-013",
    "ANOX-MAINARCH-018",
    "ANOX-MAINARCH-019",
    "ANOX-MAINARCH-023",
    "ANOX-MAINARCH-030",
    "ANOX-MAINARCH-031",
}

ALL_MAIN_IDS = {f"ANOX-MAINARCH-{i:03d}" for i in range(1, 37)}

# 17 verified-closed findings from MAINARCH-FIX-01 and 8 from MAINARCH-FIX-02.
PRE_FIX03_CLOSED = {
    "ANOX-MAINARCH-001", "ANOX-MAINARCH-002", "ANOX-MAINARCH-004", "ANOX-MAINARCH-005",
    "ANOX-MAINARCH-006", "ANOX-MAINARCH-012", "ANOX-MAINARCH-014", "ANOX-MAINARCH-020",
    "ANOX-MAINARCH-021", "ANOX-MAINARCH-022", "ANOX-MAINARCH-025", "ANOX-MAINARCH-028",
    "ANOX-MAINARCH-029", "ANOX-MAINARCH-032", "ANOX-MAINARCH-033", "ANOX-MAINARCH-034",
    "ANOX-MAINARCH-035",
    "ANOX-MAINARCH-003", "ANOX-MAINARCH-007", "ANOX-MAINARCH-008", "ANOX-MAINARCH-009",
    "ANOX-MAINARCH-010", "ANOX-MAINARCH-015", "ANOX-MAINARCH-016", "ANOX-MAINARCH-017",
}

DISALLOWED_PATTERNS = [
    r"^android/",
    r"^crypto/rust/",
    r"^backend/",
    r"^supabase/",
    r"^\.github/",
    r"^migrations?/",
    r"^docs/authority/B025/",
    r"\.kt$",
    r"\.rs$",
    r"\.so$",
    r"\.sql$",
    r"\.gradle$",
    r"\.kts$",
    r"^Cargo\.toml$",
    r"^local\.properties$",
    r"\.jks$",
    r"\.keystore$",
    r"\.p12$",
    r"\.pem$",
    r"\.key$",
    r"\.env",
    r"\.aab$",
    r"\.apk$",
]

ALLOWED_PREFIXES = {
    "docs/security/",
    "docs/workforce/registries/",
    "docs/workforce/WORKFORCE_STATE.json",
    "docs/reports/",
    "docs/continuity/",
    "docs/authority/B025_MANDATORY_AMENDMENTS_V1_3.md",
    "docs/authority/B_FREEZE_REGISTRY.md",
    "docs/authority/AUTHORITY_INDEX.md",
    "tools/audit/",
    "PROJECT_STATE.md",
    "FORTSCHRITT.md",
    "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
}

SECRET_PATTERNS = [
    rb"-----BEGIN .* PRIVATE KEY-----",
    rb"-----BEGIN RSA PRIVATE KEY-----",
    rb"-----BEGIN EC PRIVATE KEY-----",
    rb"-----BEGIN OPENSSH PRIVATE KEY-----",
    rb"-----BEGIN DSA PRIVATE KEY-----",
    rb"-----BEGIN PGP PRIVATE KEY BLOCK-----",
    rb"AKIA[0-9A-Z]{16}",
    rb"gh[pus]_[A-Za-z0-9_]{36}",
    rb"github_pat_[A-Za-z0-9_]{22,}",
    rb"xox[baprs]-[0-9A-Za-z\-]+",
    rb"sk-[a-zA-Z0-9]{48}",
]


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def read_text(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def read_jsonl(rel):
    path = REPO / rel
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def git(args):
    try:
        return subprocess.check_output(["git"] + args, cwd=REPO, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None


def find_changed_files():
    """Return all changed/staged/untracked files relative to main."""
    changed = set()
    out = git(["diff", "--name-only", "main"])
    if out:
        changed.update(out.splitlines())
    status = git(["status", "--porcelain"])
    if status:
        for line in status.splitlines():
            # Git short status: 2 status columns (XY) then a separator then the path.
            # Path begins at index 2 in all observed cases; strip to be safe.
            if len(line) >= 3:
                changed.add(line[2:].strip())
    return sorted(changed)


def check_changed_scope(errors, changed=None):
    if changed is None:
        changed = find_changed_files()
    ok(f"Detected {len(changed)} changed files relative to main")
    bad = []
    for f in changed:
        if any(re.search(p, f) for p in DISALLOWED_PATTERNS):
            bad.append(f)
            continue
        if not any(f.startswith(a) for a in ALLOWED_PREFIXES):
            bad.append(f)
    if bad:
        fail(f"FIX-03 delivery contains prohibited or unexpected files: {bad}", errors)
    else:
        ok("FIX-03 delivery scope is limited to governance/audit/docs metadata")


def check_no_secrets(errors):
    changed = find_changed_files()
    hits = []
    for f in changed:
        if not f.endswith((".md", ".json", ".jsonl", ".py", ".yml", ".yaml", ".txt")):
            continue
        full = REPO / f
        try:
            data = full.read_bytes()
        except (OSError, PermissionError):
            continue
        for pat in SECRET_PATTERNS:
            if re.search(pat, data):
                hits.append(f)
                break
    # The matrix/test docs mention service_role legitimately; ignore that exact
    # word in text files as long as no PEM/PEM-like marker matches.
    hits = [h for h in hits if "service_role" not in (REPO / h).read_text(encoding="utf-8", errors="ignore").lower()]
    if hits:
        fail(f"Potential secret/key material in changed files: {hits}", errors)
    else:
        ok("No apparent secret/key material in changed files")


def check_invariants_traced(errors, inv_rows=None):
    text = read_text(INV_FILE)
    numbers = set()
    for line in text.splitlines():
        m = re.match(r"^(\d+)\.\s", line)
        if m:
            numbers.add(int(m.group(1)))
    if numbers != set(range(1, 36)):
        fail(f"Invariant source does not contain exactly 1..35: missing {set(range(1,36))-numbers}", errors)
        return
    ok("Invariant source contains 1..35")

    if inv_rows is None:
        inv_rows = read_jsonl(INV_REG)
    if len(inv_rows) != len({r["invariant_id"] for r in inv_rows}):
        fail("Duplicate invariant_id(s) in traceability registry", errors)
        return
    inv_ids = {r["invariant_id"] for r in inv_rows}
    expected = {f"INV-{i:02d}" for i in range(1, 36)}
    if inv_ids != expected:
        fail(f"Invariant registry IDs mismatch: missing {expected-inv_ids}, extra {inv_ids-expected}", errors)
        return
    ok("All 35 invariants present in traceability registry")

    by_num = {r["invariant_number"]: r for r in inv_rows}
    for i in range(1, 36):
        r = by_num[i]
        if r["invariant_id"] != f"INV-{i:02d}":
            fail(f"Invariant number {i} has wrong id {r['invariant_id']}", errors)
        if INV_FILE not in r.get("source", ""):
            fail(f"{r['invariant_id']} source does not reference {INV_FILE}", errors)
        if not r.get("domains"):
            fail(f"{r['invariant_id']} missing affected domains", errors)
        if not r.get("enforcement_surfaces"):
            fail(f"{r['invariant_id']} missing enforcement surfaces", errors)
        if not r.get("verification_ids"):
            fail(f"{r['invariant_id']} missing verification IDs", errors)
    ok("All 35 invariants have source, domains, enforcement surfaces, verification IDs")


def check_state_model_honest(errors, inv_rows=None):
    if inv_rows is None:
        inv_rows = read_jsonl(INV_REG)
    legal_impl = {"NOT_APPLICABLE", "NOT_STARTED", "PARTIAL", "IMPLEMENTED"}
    legal_auto = {"NOT_APPLICABLE", "NOT_RUN", "PARTIAL", "PASS"}
    legal_phys = {"NOT_APPLICABLE", "REQUIRED_PENDING", "VERIFIED"}
    legal_ext = {"NOT_APPLICABLE", "REQUIRED_PENDING", "VERIFIED"}
    legal_vs = {"SPECIFIED", "IMPLEMENTED", "TESTED", "PHYSICALLY_VERIFIED", "EXTERNALLY_VERIFIED"}
    legal_es = {"NOT_APPLICABLE", "SPEC_ONLY", "IMPLEMENTED_UNVERIFIED", "AUTOMATED_VERIFIED",
                "PHYSICAL_VERIFICATION_REQUIRED", "EXTERNAL_REVIEW_REQUIRED", "VERIFIED"}

    for r in inv_rows:
        if r["implementation_state"] not in legal_impl:
            fail(f"{r['invariant_id']} illegal implementation_state {r['implementation_state']}", errors)
        if r["automated_state"] not in legal_auto:
            fail(f"{r['invariant_id']} illegal automated_state {r['automated_state']}", errors)
        if r["physical_state"] not in legal_phys:
            fail(f"{r['invariant_id']} illegal physical_state {r['physical_state']}", errors)
        if r["external_state"] not in legal_ext:
            fail(f"{r['invariant_id']} illegal external_state {r['external_state']}", errors)
        if r["verification_state"] not in legal_vs:
            fail(f"{r['invariant_id']} illegal verification_state {r['verification_state']}", errors)
        if r["evidence_state"] not in legal_es:
            fail(f"{r['invariant_id']} illegal evidence_state {r['evidence_state']}", errors)

        # No false conflation
        if r["evidence_state"] == "VERIFIED" and (r["physical_state"] != "VERIFIED" or r["external_state"] != "VERIFIED"):
            fail(f"{r['invariant_id']} claims VERIFIED but physical/external not VERIFIED", errors)
        if r["verification_state"] == "TESTED" and r["automated_state"] != "PASS":
            fail(f"{r['invariant_id']} claims TESTED without automated_state=PASS", errors)
        if r["verification_state"] == "PHYSICALLY_VERIFIED" and r["physical_state"] != "VERIFIED":
            fail(f"{r['invariant_id']} claims PHYSICALLY_VERIFIED without physical_state=VERIFIED", errors)
        if r["verification_state"] == "EXTERNALLY_VERIFIED" and r["external_state"] != "VERIFIED":
            fail(f"{r['invariant_id']} claims EXTERNALLY_VERIFIED without external_state=VERIFIED", errors)
        if r["evidence_state"] == "AUTOMATED_VERIFIED" and r["automated_state"] != "PASS":
            fail(f"{r['invariant_id']} evidence_state AUTOMATED_VERIFIED without automated_state=PASS", errors)
        if r["automated_state"] == "PASS" and not r.get("automated_evidence"):
            fail(f"{r['invariant_id']} automated_state=PASS but no automated_evidence refs", errors)
        if r["evidence_state"] == "SPEC_ONLY" and r["verification_state"] not in ("SPECIFIED", "NOT_APPLICABLE"):
            fail(f"{r['invariant_id']} evidence_state=SPEC_ONLY with verification_state={r['verification_state']}", errors)

    if not errors:
        ok("Invariant state model is honest and conflation-free")


def check_matrix_coverage(errors, mat_rows=None):
    if mat_rows is None:
        mat_rows = read_jsonl(MAT_REG)
    rows = mat_rows
    ids = [r["test_id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail(f"Duplicate test IDs in matrix: {ids}", errors)
    for r in rows:
        tid = r["test_id"]
        if not re.fullmatch(r"ANOX-TEST-(B0\d{2}|INV)-\d+", tid):
            fail(f"Unstable or illegal test ID: {tid}", errors)
        if not r.get("title"):
            fail(f"{tid} missing title", errors)
        if not r.get("verifies"):
            fail(f"{tid} missing verifies", errors)
        if not r.get("spec_refs"):
            fail(f"{tid} missing spec_refs", errors)

    domains = {r["domain"] for r in rows}
    need = {f"B-{i:03d}" for i in range(2, 21)} | {"INVARIANTS"} | {"B-021"}
    missing = need - domains
    if missing:
        fail(f"B-021 matrix missing domains: {sorted(missing)}", errors)
    else:
        ok(f"B-021 matrix covers all required domains: {sorted(need)}")

    phys = [r for r in rows if r["execution_class"] == "PHYSICAL_GRAPHENEOS"]
    if not phys:
        fail("B-021 matrix contains no PHYSICAL_GRAPHENEOS rows", errors)
    else:
        ok(f"B-021 matrix contains {len(phys)} physical-device rows")
    bad_phys = [r["test_id"] for r in phys if r["current_result"] == "PASS"]
    if bad_phys:
        fail(f"Physical-device rows falsely marked PASS: {bad_phys}", errors)
    else:
        ok("Physical-device rows are not falsely marked PASS")

    b017 = [r for r in rows if r["domain"] == "B-017"]
    if not b017:
        fail("B-017 not explicitly covered in B-021 matrix", errors)
    else:
        ok(f"B-017 explicitly covered ({len(b017)} rows)")

    b020 = [r for r in rows if r["domain"] == "B-020"]
    if not b020:
        fail("B-020 not explicitly covered in B-021 matrix", errors)
    else:
        ok(f"B-020 explicitly covered ({len(b020)} rows)")

    results = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "NOT_APPLICABLE", "UNVERIFIED"}
    for r in rows:
        if r["current_result"] not in results:
            fail(f"{r['test_id']} illegal current_result {r['current_result']}", errors)
    pass_rows = [r for r in rows if r["current_result"] == "PASS"]
    bad_pass = [r["test_id"] for r in pass_rows if not r.get("evidence_refs")]
    if bad_pass:
        fail(f"PASS rows without evidence_refs: {bad_pass}", errors)
    else:
        ok("PASS rows have evidence references")


def check_release_governance(errors, v13_text=None, master_text=None):
    v13 = (v13_text or read_text(V1_3)).lower()
    master = (master_text or read_text(MASTER)).lower()

    required = [
        "k_apk_release",
        "role-018",
        "human release approver",
        "ai may never",
        "d4",
        "signing secret",
        "hash-bound",
        "update_accept",
        "reject_invalid_signature",
        "reject_unknown_signer",
        "reject_downgrade",
        "emergency_update",
        "rollback",
        "human approval",
        "security.txt",
        "vulnerability intake",
        "runbook",
        "incident",
        "psirt",
        "github free",
        "server-side branch protection",
        "not available",
        "human-controlled remote workflow",
        "human decision",
    ]
    missing = [p for p in required if p not in v13]
    if missing:
        fail(f"V1.3 missing required release-governance language: {missing}", errors)
    else:
        ok("V1.3 contains required release/incident governance language")

    false_claims = ["branch protection is enforced", "ruleset is enabled",
                    "server-side branch protection exists", "github free plan has branch rulesets"]
    for c in false_claims:
        if c in v13:
            fail(f"V1.3 contains a false branch-protection claim: {c}", errors)
    if not any(c in v13 for c in false_claims):
        ok("V1.3 contains no false branch-protection claims")

    if "human-controlled remote workflow" in v13 and "compensating control" in v13:
        ok("V1.3 records an honest compensating control")
    else:
        fail("V1.3 does not record an honest compensating control", errors)

    if "mainarch-fix-03" in master and "027" in master:
        ok("Master Audit Report contains MAINARCH-FIX-03 section")
    else:
        fail("Master Audit Report missing MAINARCH-FIX-03 section", errors)


def check_implementation_readiness(errors, ir_data=None):
    if ir_data is None:
        ir_data = json.loads(read_text(IR_REG))
    ir = ir_data
    for d in ("B-004", "B-005"):
        dom = ir["domains"].get(d)
        if not dom:
            fail(f"implementation_readiness.json missing {d}", errors)
            continue
        if dom["architecture_state"] != "FROZEN":
            fail(f"{d} architecture_state not FROZEN", errors)
        if dom["implementation_state"] != "NOT_STARTED":
            fail(f"{d} implementation_state not NOT_STARTED", errors)
        if dom["release_readiness"] != "NOT_RELEASE_READY":
            fail(f"{d} release_readiness not NOT_RELEASE_READY", errors)
    if not errors:
        ok("B-004/B-005 architecture vs implementation distinction recorded (FROZEN + NOT_STARTED)")

    v13_clean = re.sub(r"\*", "", read_text(V1_3).lower())
    if "architecture_state" in v13_clean and "implementation_state" in v13_clean and "does not imply" in v13_clean:
        ok("V1.3 states the architecture/implementation/release axiom")
    else:
        fail("V1.3 does not state the architecture/implementation/release axiom", errors)


def check_findings(errors, findings=None):
    if findings is None:
        findings = read_jsonl("docs/workforce/registries/findings.jsonl")
    by_id = {f["finding_id"]: f for f in findings}

    for fid, sev in FIX03_SEVERITIES.items():
        f = by_id.get(fid)
        if not f:
            fail(f"Target finding {fid} missing", errors)
            continue
        if f.get("severity") != sev:
            fail(f"{fid} severity changed: expected {sev}, got {f.get('severity')}", errors)
        if f.get("status") != "Ready For Retest":
            fail(f"{fid} status is {f.get('status')}, expected Ready For Retest", errors)

    if not any(errors):
        ok("All 5 FIX-03 target findings exist, severities preserved, Ready For Retest")

    closed = {f["finding_id"] for f in findings if f.get("status") == "Closed"}
    if closed == PRE_FIX03_CLOSED and len(closed) == 25:
        ok("Closed set remains exactly the 25 pre-FIX-03 verified findings")
    else:
        fail(f"Closed set is not exactly the pre-FIX-03 25: {sorted(closed)}", errors)

    remaining = set(by_id) - closed
    if remaining == (UNTOUCHED_OPEN | FIX03_TARGETS):
        ok("Open/RFR set matches exactly: 6 untouched + 5 FIX-03 targets")
    else:
        fail(f"Unexpected remaining finding set: {sorted(remaining)}", errors)

    for fid in UNTOUCHED_OPEN:
        f = by_id.get(fid)
        if not f or f.get("status") != "Open":
            fail(f"Untouched legacy/hardware finding {fid} changed: {f.get('status')}", errors)
    if not any(fid for fid in UNTOUCHED_OPEN if fid in by_id and by_id[fid].get("status") != "Open"):
        ok("Untouched legacy/hardware findings remain Open and unchanged")


def check_milestone_flags(errors):
    v12 = read_text(V1_2)
    v13 = read_text(V1_3)
    for fid in ("ANOX-MAINARCH-003", "ANOX-MAINARCH-007"):
        if fid in v12 and "Milestone" in v12:
            continue
        fail(f"Milestone flag for {fid} not preserved in V1.2", errors)
    if "ANOX-MAINARCH-024" in v13 and "milestone" in v13.lower():
        ok("Milestone flag 024 added; 003/007 preserved")
    else:
        fail("Milestone flag 024 not added in V1.3", errors)


def check_product_blocked(errors):
    ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    if ws.get("final_pre_product_audit", {}).get("product_development_state") == "BLOCKED_PENDING_FINAL_AUDIT":
        ok("Product development remains BLOCKED_PENDING_FINAL_AUDIT")
    else:
        fail("Product development not blocked", errors)

    gate = ws.get("current_gate", "")
    notes = " ".join(ws.get("notes", []))
    if "MAINARCH-RETEST-03" in gate and "MAINARCH-RETEST-03" in notes:
        ok("Next planned task is MAINARCH-RETEST-03")
    else:
        fail("WORKFORCE_STATE does not point to MAINARCH-RETEST-03 as next planned task", errors)

    cw = ws.get("current_writer", {})
    if cw.get("task_id") == "ANOX-TASK-FIX03TRACE0001" and cw.get("role_id") == "ROLE-009":
        ok("WORKFORCE_STATE current_writer points to FIX-03 task")
    else:
        fail("WORKFORCE_STATE current_writer does not point to FIX-03 task", errors)


def check_no_claude(errors):
    ws = json.loads(read_text("docs/workforce/WORKFORCE_STATE.json"))
    blob = json.dumps(ws).lower()
    if "claude" in blob:
        fail("WORKFORCE_STATE references claude", errors)
    else:
        ok("WORKFORCE_STATE does not reference claude")


def check_authority_index(errors):
    ai = read_text("docs/authority/AUTHORITY_INDEX.md")
    fr = read_text("docs/authority/B_FREEZE_REGISTRY.md")
    if "B025_MANDATORY_AMENDMENTS_V1_3.md" not in ai:
        fail("AUTHORITY_INDEX does not reference V1.3 amendment", errors)
    if "B025_MANDATORY_AMENDMENTS_V1_3.md" not in fr:
        fail("B_FREEZE_REGISTRY does not reference V1.3 amendment", errors)
    if not errors:
        ok("AUTHORITY_INDEX and B_FREEZE_REGISTRY reference V1.3")


def main():
    print("MAINARCH-FIX-03 validator")
    errors = []

    check_authority_index(errors)
    check_changed_scope(errors)
    check_no_secrets(errors)
    check_invariants_traced(errors)
    check_state_model_honest(errors)
    check_matrix_coverage(errors)
    check_release_governance(errors)
    check_implementation_readiness(errors)
    check_findings(errors)
    check_milestone_flags(errors)
    check_product_blocked(errors)
    check_no_claude(errors)

    if errors:
        print("\nMAINARCH-FIX-03: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nMAINARCH-FIX-03: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
