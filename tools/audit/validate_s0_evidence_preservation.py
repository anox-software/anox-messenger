#!/usr/bin/env python3
"""Validate the preserved S0 remediation evidence chain.

SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001 (ANOX-EVENT-0054) preserved the
four authoritative S0 outputs — implementation, first independent architecture
retest (human-authorized provenance-marked reconstruction), correction pass and
targeted independent correction retest — as canonical repository evidence.  This
validator fails closed if the preservation is incomplete, altered, or if the
recorded state claims more than the lifecycle authorizes (no MSC closure, no
product implementation, no S1 attribution, no B004/B005 start).

Set S0_EVIDENCE_PRESERVATION_REPO to validate an alternate tree (fixture mode;
git-dependent checks are skipped when .git is absent).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("S0_EVIDENCE_PRESERVATION_REPO") or Path(__file__).resolve().parents[2])
EVIDENCE_DIR = REPO_ROOT / "docs" / "security" / "audit-evidence"
DECISIONS_PATH = "docs/workforce/registries/decisions.jsonl"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")

S0_ORIGINAL_BASE = "0f932520393feee6d479cc099f179f5766323125"
S0_SUBSTANTIVE_SHA = "8756a94824ba9baef678176ef2ee24a2c302f1d0"
S0_FINAL_HEAD = "0be57335adaa25ad584357dde74666eb97339a01"
S0_DELIVERY_BRANCH = "security/remediation-s0-contract-freeze-001"
PRESERVATION_EVENT_ID = "ANOX-EVENT-0054"
PRESERVATION_TASK = "ANOX-TASK-SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001"
PRESERVATION_BRANCH = "governance/security-remediation-s0-evidence-preservation-001"
LEDGER_EVENT_0053 = "ANOX-EVENT-0053"
LEDGER_EVENT_0052 = "ANOX-EVENT-0052"

PRESERVATION_RECORD = "docs/reports/security/remediation/SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001.md"
DECISION_ID = "ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001"
DECISION_PATH = "docs/reports/security/decisions/S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001.md"
F01_DECISION_ID = "ANOX-DECISION-S0-F01-RATIFICATION-001"

SOURCE_REPORTS = {
    "implementation": {
        "id": "REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001",
        "path": "docs/reports/security/remediation/REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md",
        "sha256": "19cb339f398c4bd9b702a1442ea21d0bf96ffc57ed97ff351d9b49c1eed9484a",
        "result": "PASS",
        "source_class": "CANONICAL_REPOSITORY_REPORT",
    },
    "first_independent_retest": {
        "id": "INDEPENDENT-ARCHITECTURE-RETEST-S0-001",
        "path": "docs/reports/security/retests/INDEPENDENT-ARCHITECTURE-RETEST-S0-001.md",
        "sha256": "fb2f4b8cb83b6b812dfb3656d9f6b1b0c2541b8f9b1af22c55787422e4fa5d29",
        "result": "PASS_WITH_FINDINGS",
        "finding_count": 10,
        "source_class": "HUMAN_AUTHORIZED_RECONSTRUCTED_SECURITY_EVIDENCE",
        "required_markers": [
            "VERBATIM_ORIGINAL_TRANSCRIPT_AVAILABLE = NO",
            "RECONSTRUCTED = YES",
            "RECONSTRUCTION_HUMAN_AUTHORIZED = YES",
            "SOURCE_CLASS = HUMAN_AUTHORIZED_RECONSTRUCTED_SECURITY_EVIDENCE",
            "ORIGINAL_RESULT = PASS_WITH_FINDINGS",
            "ORIGINAL_FINDING_COUNT = 10",
        ],
        # Regexes matching AFFIRMATIVE verbatim/original-hash claims only —
        # provenance disclaimers ("does not assert an original report SHA-256")
        # must not trip them.
        "forbidden_claims": [
            r"VERBATIM_ORIGINAL_TRANSCRIPT_AVAILABLE\s*=\s*YES",
            r"RECONSTRUCTED\s*=\s*NO",
            r"RECONSTRUCTION_HUMAN_AUTHORIZED\s*=\s*NO",
            r"original[^\n]{0,80}?sha-?256[^\n]{0,30}?[0-9a-f]{64}",
            r"byte-exact[^\n]{0,30}(original|transcript)",
            r"verbatim[^\n]{0,30}transcript[^\n]{0,30}(preserved|attached|included)",
        ],
    },
    "correction": {
        "id": "REMEDIATION-SESSION-S0-CORRECTION-001",
        "path": "docs/reports/security/remediation/REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md",
        "sha256": "19cb339f398c4bd9b702a1442ea21d0bf96ffc57ed97ff351d9b49c1eed9484a",
        "result": "PASS",
        "source_class": "CANONICAL_REPOSITORY_REPORT_APPENDIX",
    },
    "targeted_correction_retest": {
        "id": "TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001",
        "path": "docs/reports/security/retests/TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001.md",
        "sha256": "67cb2c152c234397fe94259207492263200123db6acd07e2d97f80ecb5d5b951",
        "result": "PASS_WITH_FINDINGS",
        "source_class": "VERBATIM_SESSION_TRANSCRIPT_PRESERVED",
    },
}

FINDING_DISPOSITIONS = {
    "F-01": "RATIFIED_DISCLOSED_FILE_OWNERSHIP_DEVIATION",
    "F-02": "FIXED", "F-03": "FIXED", "F-04": "FIXED", "F-05": "FIXED",
    "F-06": "FIXED", "F-07": "FIXED", "F-08": "FIXED", "F-09": "FIXED",
    "F-10": "FIXED",
}
RESIDUAL_LOW_FOLLOWUPS = {
    "S0-RESIDUAL-LOW-F05-UNANCHORED-CC-CLAUSES": "F-05",
    "S0-RESIDUAL-LOW-F08-AUTHORITY-HOME-FREETEXT": "F-08",
}
S0_PRIMARY_UNITS = [f"MSC-UNIT-{u}" for u in ("018", "020", "025", "026", "027", "028", "032", "033", "034", "040", "042")]
S0_SUPPORTING_UNIT = "MSC-UNIT-022"
S0_CONSUMED_UNIT = "MSC-UNIT-039"
S0_AC_COVERED = ["AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-008", "AC-009", "AC-010", "AC-014"]

PINNED_TEST_COUNTS = {
    "tools/audit/test_s0_contract_freeze.py": 100,
    "tools/audit/test_security_audit_evidence_preservation.py": 277,
    "tools/audit/test_s0_evidence_preservation.py": 40,
}

FORBIDDEN_PRODUCT_PREFIXES = ("android/", "crypto/", "backend/", "supabase/", "tests/", ".github/")
S1_OWNED_FILES = (
    ".github/workflows/ci.yml",
    "docs/current/REPOSITORY_SECURITY_POLICY.md",
    "tools/security/validate_apk_contents.py",
    "docs/workforce/registries/b021_verification_matrix.jsonl",
)


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def load_jsonl(rel):
    p = REPO_ROOT / rel
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def load_json(rel):
    p = REPO_ROOT / rel
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def read_text(rel):
    p = REPO_ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else None


def has_git():
    return (REPO_ROOT / ".git").is_dir()


def check_source_reports(errors):
    """§22 — all four source reports present, hash-verified, correctly classed."""
    print("\n[S0-PRESERVE] Source reports (existence + byte-exact hash)")
    before = len(errors)
    hashes = load_json("docs/security/audit-evidence/evidence_hashes.json").get("reports") or {}
    for key, spec in SOURCE_REPORTS.items():
        p = REPO_ROOT / spec["path"]
        if not p.exists():
            fail(f"{spec['id']} report missing: {spec['path']}", errors)
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest != spec["sha256"]:
            fail(f"{spec['id']} report hash mismatch: {digest[:16]}… != {spec['sha256'][:16]}…", errors)
        hrec = hashes.get(spec["id"]) or {}
        if hrec.get("sha256") != spec["sha256"]:
            fail(f"evidence_hashes.json entry for {spec['id']} mismatched/missing", errors)
        # Content checks run even when the hash mismatches — a mutated file
        # must still be inspected for dropped markers / forbidden claims.
        for marker in spec.get("required_markers") or []:
            if marker not in p.read_text(encoding="utf-8"):
                fail(f"{spec['id']} reconstruction marker missing: {marker!r}", errors)
        for bad in spec.get("forbidden_claims") or []:
            if re.search(bad, p.read_text(encoding="utf-8"), re.IGNORECASE):
                fail(f"{spec['id']} makes a forbidden verbatim/original-hash claim: {bad!r}", errors)
    if len(errors) == before:
        ok("all four S0 preservation sources present and hash-verified (A verbatim, B reconstructed-marked, C appendix, D verbatim)")


def check_delivery_topology(errors):
    """§22 — corrected S0 substantive/final SHAs pinned; topology verified live."""
    print("\n[S0-PRESERVE] Corrected S0 delivery pins")
    before = len(errors)
    reg = {r.get("audit_id"): r for r in load_jsonl("docs/security/audit-evidence/audit_registry.jsonl")}
    rec = reg.get("SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001") or {}
    for key, want in (("s0_original_base_sha", S0_ORIGINAL_BASE),
                      ("s0_corrected_substantive_sha", S0_SUBSTANTIVE_SHA),
                      ("s0_corrected_final_head_sha", S0_FINAL_HEAD)):
        if rec.get(key) != want:
            fail(f"preservation registry {key}={rec.get(key)!r}, expected {want}", errors)
    if has_git():
        for label, sha in (("S0 original base", S0_ORIGINAL_BASE),
                           ("S0 substantive", S0_SUBSTANTIVE_SHA),
                           ("S0 final head", S0_FINAL_HEAD)):
            if subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=REPO_ROOT,
                              capture_output=True).returncode != 0:
                fail(f"{label} commit {sha[:12]} does not exist", errors)
                continue
            if subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                              cwd=REPO_ROOT, capture_output=True).returncode != 0:
                fail(f"{label} {sha[:12]} is not an ancestor of HEAD", errors)
        parents = subprocess.run(["git", "rev-list", "--parents", "-1", S0_SUBSTANTIVE_SHA],
                                 cwd=REPO_ROOT, capture_output=True, text=True).stdout.split()
        if len(parents) != 2 or parents[1] != S0_ORIGINAL_BASE:
            fail(f"S0 substantive {S0_SUBSTANTIVE_SHA[:12]} must be the direct child of base {S0_ORIGINAL_BASE[:12]}", errors)
        parents = subprocess.run(["git", "rev-list", "--parents", "-1", S0_FINAL_HEAD],
                                 cwd=REPO_ROOT, capture_output=True, text=True).stdout.split()
        if len(parents) != 2 or parents[1] != S0_SUBSTANTIVE_SHA:
            fail(f"S0 final head {S0_FINAL_HEAD[:12]} must be the direct child of substantive {S0_SUBSTANTIVE_SHA[:12]}", errors)
        n = subprocess.run(["git", "rev-list", "--count", f"{S0_ORIGINAL_BASE}..{S0_FINAL_HEAD}"],
                           cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
        if n != "2":
            fail(f"corrected S0 delivery must contain exactly 2 commits above base, got {n}", errors)
        # S0 range must not touch product/S1-owned paths.
        out = subprocess.run(["git", "diff", "--name-only", S0_ORIGINAL_BASE, S0_FINAL_HEAD],
                             cwd=REPO_ROOT, capture_output=True, text=True).stdout.splitlines()
        bad = sorted(p for p in out if p and (p.startswith(FORBIDDEN_PRODUCT_PREFIXES)
                     or p.endswith(".sql") or p.endswith(".so") or p in S1_OWNED_FILES))
        if bad:
            fail(f"S0 delivery changed product/S1-owned paths: {bad}", errors)
    else:
        print("  SKIP git topology checks (no .git — fixture mode)")
    if len(errors) == before:
        ok("S0 delivery pins verified (substantive 8756a94…, final 0be5733…, 2-commit topology)")


def check_findings_and_followups(errors):
    """§22 — F-01 ratified; F-02…F-10 FIXED; two residual LOW follow-ups open."""
    print("\n[S0-PRESERVE] Finding dispositions + residual LOW follow-ups")
    before = len(errors)
    trace = load_jsonl("docs/security/audit-evidence/audit_traceability.jsonl")
    dispositions = {r.get("finding_id"): r for r in trace if r.get("record_type") == "s0_finding_disposition"}
    for fid, want in FINDING_DISPOSITIONS.items():
        rec = dispositions.get(fid)
        if rec is None:
            fail(f"{fid} s0_finding_disposition traceability record missing", errors)
            continue
        if rec.get("final_disposition") != want:
            fail(f"{fid} final_disposition={rec.get('final_disposition')!r}, expected {want!r}", errors)
        if rec.get("verified_by") != "TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001":
            fail(f"{fid} not verified by the targeted independent retest", errors)
        if rec.get("merge_blocker") is not False:
            fail(f"{fid} must record merge_blocker=false", errors)
    f01 = dispositions.get("F-01") or {}
    if f01.get("human_ratification") != F01_DECISION_ID:
        fail("F-01 disposition must reference the Human ratification ANOX-DECISION-S0-F01-RATIFICATION-001", errors)
    f01rec = next((r for r in load_jsonl(DECISIONS_PATH) if r.get("decision_id") == F01_DECISION_ID), None)
    if f01rec is None:
        fail(f"F-01 ratification {F01_DECISION_ID} missing from {DECISIONS_PATH}", errors)
    else:
        if f01rec.get("scope") != "ONE_TIME_CHANGE_SPECIFIC":
            fail("F-01 ratification must remain ONE_TIME_CHANGE_SPECIFIC (not generalized)", errors)
        for flag in ("grants_general_ownership", "grants_s1_permission", "grants_future_sessions"):
            if f01rec.get(flag) is not False:
                fail(f"F-01 ratification generalized: {flag} != false", errors)
    for rid, src in RESIDUAL_LOW_FOLLOWUPS.items():
        rec = next((r for r in trace if r.get("record_type") == "s0_residual_low_followup"
                    and r.get("followup_id") == rid), None)
        if rec is None:
            fail(f"residual LOW follow-up {rid} missing from traceability", errors)
            continue
        if rec.get("severity") != "LOW":
            fail(f"{rid} severity {rec.get('severity')!r} — silent severity change", errors)
        if rec.get("s0_merge_blocker") is not False or rec.get("followup_required") is not True:
            fail(f"{rid} must be NON_BLOCKING with followup_required=true", errors)
        if "OPEN" not in str(rec.get("status", "")):
            fail(f"{rid} must remain OPEN_FOLLOWUP — false closure", errors)
        if rec.get("source_finding") != src:
            fail(f"{rid} source_finding must be {src}", errors)
    if len(errors) == before:
        ok("F-01 RATIFIED; F-02…F-10 FIXED (9/9); 2 residual LOW follow-ups open/non-blocking")


def check_lifecycle_claims(errors):
    """§22 — no MSC closure, no product implementation claim, no S1 attribution,
    invariants unchanged."""
    print("\n[S0-PRESERVE] Lifecycle claims / invariants")
    before = len(errors)
    reg = {r.get("audit_id"): r for r in load_jsonl("docs/security/audit-evidence/audit_registry.jsonl")}
    rec = reg.get("SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001") or {}
    pinned = {
        "implementation_result": "PASS",
        "first_independent_retest": "PASS_WITH_FINDINGS",
        "correction_result": "PASS",
        "targeted_retest_result": "PASS_WITH_FINDINGS",
        "merge_blockers_remaining": 0,
        "medium_or_higher_open_retest_findings": 0,
        "residual_low_followups": 2,
        "evidence_preserved": "YES",
        "msc_closed_by_s0": 0,
        "open_msc_units": 42,
        "security_remediation": "IN_PROGRESS",
        "s0_merge_readiness": "READY",
        "s0_residual_low_followups": "2_NON_BLOCKING",
        "b004": "NOT_STARTED",
        "b005": "NOT_STARTED",
        "product": "BLOCKED_PENDING_FINAL_AUDIT",
        "s1": "ISOLATED_IMPLEMENTATION_COMPLETE_NOT_INTEGRATED",
        "s1_files_changed_by_s0": 0,
        "product_behavior_changed": "NO",
        "previous_evidence_weakened": "NO",
        "status": "PRESERVED",
        "preserved_at_event": PRESERVATION_EVENT_ID,
    }
    for key, want in pinned.items():
        if rec.get(key) != want:
            fail(f"preservation registry {key}={rec.get(key)!r}, expected {want!r}", errors)
    if sorted(rec.get("s0_primary_units") or []) != sorted(u.replace("UNIT-", "") for u in S0_PRIMARY_UNITS):
        fail("preservation registry s0_primary_units must be the 11 primary S0 units", errors)
    if rec.get("s0_supporting_units") != ["MSC-022"]:
        fail("MSC-022 must be supporting_contract_entry_only — not a primary S0 unit", errors)
    if rec.get("s0_consumed_units") != ["MSC-039"]:
        fail("MSC-039 must be consumed/not reopened", errors)
    # no closure claims anywhere in the S0 evidence layer
    trace = load_jsonl("docs/security/audit-evidence/audit_traceability.jsonl")
    for r in trace:
        if str(r.get("record_type", "")).startswith("s0_") and r.get("closed_by_s0") is True:
            fail(f"s0 traceability record claims closure by S0: {r.get('msc_unit') or r.get('finding_id')}", errors)
    # previous evidence not weakened: all 12 prior registry records still bound
    # to their preserved report hash and result (fields they carry canonically).
    # REMEDIATION-S1-CANONICAL-INTEGRATION-001 appends exactly one later record
    # (SEC-AUDIT-REG-0014, S1 integration evidence); it is pinned and validated
    # by the central validator and is not a "prior" record of S0. The 12-record
    # prior-evidence protection is unchanged.
    later = {"SEC-AUDIT-REG-0013",
             ("SEC-AUDIT-REG-0014", "REMEDIATION-S1-CANONICAL-INTEGRATION-001")}
    prior = [a for a in reg.values()
             if a.get("record_id") != "SEC-AUDIT-REG-0013"
             and (a.get("record_id"), a.get("audit_id")) not in later]
    if len(prior) != 12:
        fail(f"prior evidence registry must still hold exactly 12 records, got {len(prior)}", errors)
    for a in prior:
        if not re.fullmatch(r"[0-9a-f]{64}", str(a.get("report_sha256") or "")) or not a.get("result"):
            fail(f"prior registry record {a.get('audit_id')} lost its preserved hash/result — previous evidence weakened", errors)
    if len(errors) == before:
        ok("MSC_CLOSED_BY_S0=0 · 42 open · IN_PROGRESS · B004/B005 NOT_STARTED · no S1 attribution · prior evidence intact")


def check_root_arch_invariants(errors):
    """§22 — ROOT-013 MEDIUM/OPEN, ROOT-016 rejected, ARCH-010 open/info."""
    print("\n[S0-PRESERVE] ROOT/ARCH invariants")
    before = len(errors)
    trace = load_jsonl("docs/security/audit-evidence/audit_traceability.jsonl")
    r13 = next((r for r in trace if r.get("record_type") == "canonical_severity_transition"
                and r.get("finding_id") == "ROOT-013"), None)
    if r13 is None or r13.get("current_canonical_severity") != "MEDIUM" or r13.get("status") != "OPEN":
        fail("ROOT-013 canonical transition must remain MEDIUM / OPEN", errors)
    r16 = next((r for r in trace if r.get("record_type") == "consensus_root"
                and r.get("root_id") == "ROOT-016"), None)
    if r16 is None or r16.get("status") != "REJECTED_NOT_A_FINDING":
        fail("ROOT-016 must remain REJECTED_NOT_A_FINDING — revived or missing", errors)
    findings = {f.get("finding_id"): f for f in load_jsonl("docs/workforce/registries/findings.jsonl")}
    a10 = findings.get("ANOX-SECURITY-ARCH-010") or {}
    if a10.get("severity") != "INFO" or str(a10.get("status")) != "Open":
        fail(f"ARCH-010 must remain Open/INFO, got {a10.get('severity')}/{a10.get('status')}", errors)
    pres = read_text(PRESERVATION_RECORD) or ""
    for req in ("ROOT-013 = MEDIUM / OPEN", "ROOT-016 = REJECTED_NOT_A_FINDING",
                "ARCH-010 = OPEN / INFO / RETIRE_AT_B004_START"):
        if req not in pres:
            fail(f"preservation record missing invariant statement {req!r}", errors)
    if len(errors) == before:
        ok("ROOT-013 MEDIUM/OPEN · ROOT-016 REJECTED · ARCH-010 OPEN/INFO/RETIRE_AT_B004_START")


def check_coverage_pins(errors):
    """§22 — coverage counts and contract-ambiguity zero pins."""
    print("\n[S0-PRESERVE] Coverage pins")
    before = len(errors)
    pres = read_text(PRESERVATION_RECORD) or ""
    for req in ("SC-1…SC-14 = 14/14", "CC-1…CC-14 = 14/14", "SERVER_BREAKER_S1…S18 = 18/18",
                "CANONICAL_CONTRACT_AMBIGUITIES = 0", "CANONICAL_SCHEMA_HOMES = 1",
                "EQUAL_PRECEDENCE_CONFLICTS = 0", "98/98", "253/253"):
        if req not in pres:
            fail(f"preservation record missing coverage pin {req!r}", errors)
    man = load_json("docs/authority/contracts/S0_CONTRACT_FREEZE_MANIFEST.json")
    amb = man.get("contract_ambiguities", man.get("ambiguities"))
    if amb not in (None, 0, [], {}):
        fail(f"manifest contract ambiguities must be 0, got {amb!r}", errors)
    for ac in S0_AC_COVERED:
        if ac not in pres:
            fail(f"preservation record missing attack-chain status for {ac}", errors)
    if len(errors) == before:
        ok("SC 14/14 · CC 14/14 · S1–S18 18/18 · ambiguities 0 · AC status 9/9 recorded")


def check_test_counts(errors):
    """§22 — pinned adversarial test counts (fail closed on silent change)."""
    print("\n[S0-PRESERVE] Adversarial test-count pins")
    before = len(errors)
    for rel, want in PINNED_TEST_COUNTS.items():
        text = read_text(rel)
        if text is None:
            fail(f"test file {rel} missing", errors)
            continue
        got = len(re.findall(r"def test_", text))
        if got != want:
            fail(f"{rel} must contain exactly {want} tests, got {got}", errors)
    if len(errors) == before:
        ok(f"test counts pinned: {sum(PINNED_TEST_COUNTS.values())} total")


def check_event(errors):
    """§22 — ANOX-EVENT-0054 in the ledger with pinned identity; state synced."""
    print("\n[S0-PRESERVE] Preservation event")
    before = len(errors)
    ledger = load_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
    ev = next((e for e in ledger if e.get("event_id") == PRESERVATION_EVENT_ID), None)
    if ev is None:
        fail(f"ledger missing {PRESERVATION_EVENT_ID}", errors)
    else:
        if ev.get("type") != "audit_evidence_preservation":
            fail(f"{PRESERVATION_EVENT_ID} type {ev.get('type')!r} != audit_evidence_preservation", errors)
        if ev.get("task") != PRESERVATION_TASK:
            fail(f"{PRESERVATION_EVENT_ID} task {ev.get('task')!r} != {PRESERVATION_TASK}", errors)
        if ev.get("start_head") != S0_FINAL_HEAD:
            fail(f"{PRESERVATION_EVENT_ID} start_head {ev.get('start_head')!r} != {S0_FINAL_HEAD}", errors)
        if PRESERVATION_RECORD not in (ev.get("refs") or []):
            fail(f"{PRESERVATION_EVENT_ID} missing preservation-record evidence ref", errors)
        idx = ledger.index(ev)
        if idx < 2 or ledger[idx - 1].get("event_id") != LEDGER_EVENT_0053 \
                or ledger[idx - 2].get("event_id") != LEDGER_EVENT_0052:
            fail(f"{PRESERVATION_EVENT_ID} must directly follow {LEDGER_EVENT_0053} ← {LEDGER_EVENT_0052}", errors)
        # Era-precision (REMEDIATION-S1-CANONICAL-INTEGRATION-001): S0 preservation
        # is a sealed chain position, not a freeze of the ledger. Later canonical
        # events may follow, but 0054 must occur exactly once, nothing after it may
        # re-record an S0 task or reuse 0054, and later ids must strictly ascend.
        ids = [e.get("event_id") for e in ledger]
        if ids.count(PRESERVATION_EVENT_ID) != 1:
            fail(f"{PRESERVATION_EVENT_ID} must occur exactly once in the ledger", errors)
        s0_tasks = {PRESERVATION_TASK, "ANOX-TASK-REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001",
                    "ANOX-TASK-REMEDIATION-SESSION-S0-CORRECTION-001"}
        prev_num = int(PRESERVATION_EVENT_ID.rsplit("-", 1)[1])
        for later in ledger[idx + 1:]:
            lid = str(later.get("event_id") or "")
            m = re.fullmatch(r"ANOX-EVENT-(\d{4})", lid)
            if not m or int(m.group(1)) <= prev_num:
                fail(f"event after {PRESERVATION_EVENT_ID} has non-ascending/illegal id {lid!r}", errors)
                break
            prev_num = int(m.group(1))
            if later.get("task") in s0_tasks:
                fail(f"S0 task re-recorded after preservation ({lid}) — preserved S0 evidence may not be re-opened", errors)
    state = load_json("docs/continuity/CURRENT_STATE.json")
    if ledger and state.get("latest_material_event_id") != ledger[-1].get("event_id"):
        fail("CURRENT_STATE.latest_material_event_id != last ledger event (Project Memory stale)", errors)
    if not ledger or PRESERVATION_EVENT_ID not in [e.get("event_id") for e in ledger]:
        fail(f"CURRENT_STATE/ledger no longer carry {PRESERVATION_EVENT_ID}", errors)
    if len(errors) == before:
        ok(f"{PRESERVATION_EVENT_ID} recorded, ordered 0052 → 0053 → 0054, state synced")


def check_decision(errors):
    """§22 — the preservation shared-validator ratification exists and is pinned."""
    print("\n[S0-PRESERVE] Preservation ratification decision")
    before = len(errors)
    rec = next((r for r in load_jsonl(DECISIONS_PATH) if r.get("decision_id") == DECISION_ID), None)
    if rec is None:
        fail(f"{DECISION_ID} missing from {DECISIONS_PATH}", errors)
    else:
        if rec.get("scope") != "ONE_TIME_CHANGE_SPECIFIC":
            fail("preservation ratification scope must be ONE_TIME_CHANGE_SPECIFIC", errors)
        if rec.get("ratified_task") != PRESERVATION_TASK:
            fail("preservation ratification ratified_task mismatch", errors)
        if rec.get("ratified_files") != ["tools/audit/validate_security_audit_evidence_preservation.py"]:
            fail("preservation ratification must authorize exactly one file", errors)
        if rec.get("authorized_file_count") != 1:
            fail("preservation ratification authorized_file_count must be 1", errors)
        for flag in ("grants_general_ownership", "grants_s1_permission", "grants_future_sessions",
                     "grants_future_event_numbers", "grants_arbitrary_registry_growth"):
            if rec.get(flag) is not False:
                fail(f"preservation ratification generalized: {flag} != false", errors)
        if "Human Product & Security Owner" not in str(rec.get("authority_actor", "")):
            fail("preservation ratification authority must be the Human Product & Security Owner", errors)
    if read_text(DECISION_PATH) is None:
        fail(f"canonical decision record {DECISION_PATH} missing", errors)
    if len(errors) == before:
        ok(f"{DECISION_ID} recorded and pinned (one file, no blanket grants)")


def main():
    errors = []
    print("[S0-PRESERVE] Source reports")
    check_source_reports(errors)
    print("\n[S0-PRESERVE] Delivery pins")
    check_delivery_topology(errors)
    print("\n[S0-PRESERVE] Findings / follow-ups")
    check_findings_and_followups(errors)
    print("\n[S0-PRESERVE] Lifecycle / invariants")
    check_lifecycle_claims(errors)
    print("\n[S0-PRESERVE] ROOT/ARCH invariants")
    check_root_arch_invariants(errors)
    print("\n[S0-PRESERVE] Coverage pins")
    check_coverage_pins(errors)
    print("\n[S0-PRESERVE] Test-count pins")
    check_test_counts(errors)
    print("\n[S0-PRESERVE] Event / decision")
    check_event(errors)
    check_decision(errors)
    if errors:
        print(f"\nRESULT: FAIL — {len(errors)} violation(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nRESULT: PASS — S0 remediation evidence chain preserved and verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
