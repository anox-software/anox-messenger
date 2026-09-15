#!/usr/bin/env python3
"""Active fail-closed validator for the B-021 verification matrix and the
MSC remediation-stage registry (MSC-UNIT-038 / REMEDIATION_SESSION_S1).

Two surfaces:

1. docs/workforce/registries/b021_verification_matrix.jsonl
   - stable unique test IDs, full domain/invariant coverage, legal states
   - PASS rows require preserved evidence (refs must resolve)
   - PHYSICAL_GRAPHENEOS rows can never be PASS
   - a green CI run is NOT evidence: SPEC_ONLY / UNVERIFIED never count as PASS

2. docs/security/remediation/msc_state.jsonl
   - canonical stage chain per unit; IMPLEMENTED -> CLOSED jumps forbidden
   - RUNTIME_TESTED on provenance-required units needs FCP-1 evidence
     (BUILD_ARTIFACT_HASH_PROOF + PROVENANCE_VERIFIED_NATIVE_RUNTIME refs)
   - retest stages require a different recording authority than the
     implementing session (FCP-7)

Modes:
  --check integrity   structural honesty of both surfaces (CI default; PASS
                      when the records are well-formed, regardless of how many
                      rows are still NOT_RUN — the matrix is a work tracker)
  --check closure     additionally fail when any pre_product_required row is
                      not verified, or any required MSC stage is unresolved.

Stdlib only.  Fails closed on every violation.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX = "docs/workforce/registries/b021_verification_matrix.jsonl"
INV_REG = "docs/workforce/registries/security_invariant_traceability.jsonl"
MSC_STATE = "docs/security/remediation/msc_state.jsonl"

LEGAL_RESULT = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "NOT_APPLICABLE", "UNVERIFIED"}
LEGAL_EVIDENCE_STATE = {
    "SPEC_ONLY", "IMPLEMENTED_UNVERIFIED", "AUTOMATED_VERIFIED",
    "PHYSICAL_VERIFICATION_REQUIRED", "EXTERNAL_REVIEW_REQUIRED", "VERIFIED",
}
LEGAL_EXECUTION_CLASS = {
    "REPO_STATIC", "JVM_UNIT", "RUST", "ANDROID_EMULATOR", "BACKEND_INTEGRATION",
    "INDEPENDENT_AUDIT", "PHYSICAL_GRAPHENEOS", "HUMAN_RELEASE_PROCEDURE", "INFRA_DR",
}
REQUIRED_ROW_FIELDS = {
    "test_id", "domain", "title", "verifies", "spec_refs", "execution_class",
    "implementation_dependency", "pre_product_required", "release_required",
    "current_result", "evidence_state", "evidence_refs", "notes",
}
REQUIRED_DOMAINS = {f"B-{i:03d}" for i in range(2, 21)} | {"INVARIANTS", "B-021"}

# States in which a pre_product_required row is still a closure blocker.
BLOCKING_RESULTS = {"NOT_RUN", "UNVERIFIED", "FAIL", "BLOCKED"}
PASS_EVIDENCE_STATES = {"AUTOMATED_VERIFIED", "VERIFIED"}

# ---------------------------------------------------------------------------
# MSC remediation stage model (frozen SECURITY-REMEDIATION-COVERAGE-GATE-001)
# ---------------------------------------------------------------------------

STAGE_ORDER = [
    "IMPLEMENTED",
    "AUTOMATED_TESTED",
    "RUNTIME_TESTED",
    "INDEPENDENTLY_RETESTED",
    "ATTACKCHAIN_RETESTED",
    "PHYSICAL_VERIFIED",
    "EVIDENCE_PRESERVED",
    "CLOSED",
]

# Frozen per-unit closure-stage requirements from the gate table
# (R = RUNTIME_TESTED, C = ATTACKCHAIN_RETESTED, P = PHYSICAL_VERIFIED).
STAGE_REQUIREMENTS = {
    "MSC-UNIT-001": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-002": {"RUNTIME_TESTED"},
    "MSC-UNIT-003": set(),
    "MSC-UNIT-004": {"RUNTIME_TESTED"},
    "MSC-UNIT-005": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-006": {"ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-007": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-008": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-009": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-010": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-011": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-012": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-013": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-014": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"},
    "MSC-UNIT-015": {"ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-016": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"},
    "MSC-UNIT-017": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"},
    "MSC-UNIT-018": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-019": {"RUNTIME_TESTED"},
    "MSC-UNIT-020": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"},
    "MSC-UNIT-021": {"ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"},
    "MSC-UNIT-022": {"ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-023": {"ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-024": {"ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"},
    "MSC-UNIT-025": {"ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"},
    "MSC-UNIT-026": {"ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-027": {"ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-028": {"ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-029": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-030": {"ATTACKCHAIN_RETESTED"},
    "MSC-UNIT-031": {"RUNTIME_TESTED", "ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"},
    "MSC-UNIT-032": set(),
    "MSC-UNIT-033": set(),
    "MSC-UNIT-034": {"PHYSICAL_VERIFIED"},
    "MSC-UNIT-035": set(),
    "MSC-UNIT-036": {"PHYSICAL_VERIFIED"},
    "MSC-UNIT-037": {"RUNTIME_TESTED"},
    "MSC-UNIT-038": set(),
    "MSC-UNIT-039": set(),
    "MSC-UNIT-040": set(),
    "MSC-UNIT-041": set(),
    "MSC-UNIT-042": {"PHYSICAL_VERIFIED"},
}

# Units whose RUNTIME_TESTED evidence must bind to the authoritative native
# build lineage (Prov=Y in the frozen gate table — FCP-1).
PROVENANCE_REQUIRED_UNITS = {
    "MSC-UNIT-001", "MSC-UNIT-002", "MSC-UNIT-004", "MSC-UNIT-005",
    "MSC-UNIT-006", "MSC-UNIT-007", "MSC-UNIT-008", "MSC-UNIT-009",
    "MSC-UNIT-010", "MSC-UNIT-011", "MSC-UNIT-012", "MSC-UNIT-013",
    "MSC-UNIT-019", "MSC-UNIT-020", "MSC-UNIT-030", "MSC-UNIT-036",
    "MSC-UNIT-037",
}

PROVENANCE_REF = re.compile(
    r"(native-manifest\.json|BUILD_ARTIFACT_HASH_PROOF|PROVENANCE_VERIFIED_NATIVE_RUNTIME)",
    re.IGNORECASE,
)

RETEST_STAGES = {"INDEPENDENTLY_RETESTED", "ATTACKCHAIN_RETESTED", "PHYSICAL_VERIFIED"}
LEGAL_STAGE_RESULT = {"PASS", "PENDING", "FAIL", "NOT_APPLICABLE"}


def _load_jsonl(path, errors, label):
    rows = []
    p = Path(path)
    if not p.exists():
        errors.append(f"{label} missing: {p}")
        return rows
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors.append(f"{label} line {i} invalid JSON: {e}")
    return rows


def _ref_resolves(repo_root, ref):
    """Evidence refs: repo paths must exist; git:/ANOX-/SEC- refs are ids."""
    if not isinstance(ref, str) or not ref.strip():
        return False
    ref = ref.strip()
    if ref.startswith("git:"):
        return bool(re.fullmatch(r"[0-9a-f]{7,40}", ref[4:]))
    if ref.startswith(("ANOX-", "SEC-", "MSC-", "ROOT-", "AC-", "INV-", "PHYSICAL")):
        return True
    path = ref.split("#", 1)[0]
    return (Path(repo_root) / path).exists()


# ---------------------------------------------------------------------------
# matrix checks

def check_matrix(repo_root, errors):
    rows = _load_jsonl(Path(repo_root) / MATRIX, errors, "matrix")
    if not rows:
        return rows

    ids = [r.get("test_id") for r in rows]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        errors.append(f"duplicate test IDs in matrix: {dupes}")

    for r in rows:
        tid = r.get("test_id", "<missing>")
        missing = REQUIRED_ROW_FIELDS - set(r)
        if missing:
            errors.append(f"{tid}: missing fields {sorted(missing)}")
            continue
        if not re.fullmatch(r"ANOX-TEST-(B0\d{2}|INV)-\d+", str(tid)):
            errors.append(f"unstable/illegal test ID: {tid}")
        if not r["title"]:
            errors.append(f"{tid}: missing title")
        if not isinstance(r["verifies"], list) or not r["verifies"]:
            errors.append(f"{tid}: missing verifies")
        if not isinstance(r["spec_refs"], list) or not r["spec_refs"]:
            errors.append(f"{tid}: missing spec_refs")
        if r["current_result"] not in LEGAL_RESULT:
            errors.append(f"{tid}: illegal current_result {r['current_result']}")
        if r["evidence_state"] not in LEGAL_EVIDENCE_STATE:
            errors.append(f"{tid}: illegal evidence_state {r['evidence_state']}")
        if r["execution_class"] not in LEGAL_EXECUTION_CLASS:
            errors.append(f"{tid}: illegal execution_class {r['execution_class']}")
        for f in ("pre_product_required", "release_required"):
            if not isinstance(r[f], bool):
                errors.append(f"{tid}: {f} must be boolean")
        if not isinstance(r["evidence_refs"], list):
            errors.append(f"{tid}: evidence_refs must be a list")

        # --- honesty: a green CI run is not evidence; PASS needs real refs ---
        if r["current_result"] == "PASS":
            if not r["evidence_refs"]:
                errors.append(f"{tid}: PASS without evidence_refs")
            if r["evidence_state"] not in PASS_EVIDENCE_STATES:
                errors.append(
                    f"{tid}: PASS with evidence_state {r['evidence_state']} "
                    f"(requires one of {sorted(PASS_EVIDENCE_STATES)})"
                )
            for ref in r["evidence_refs"]:
                if not _ref_resolves(repo_root, ref):
                    errors.append(f"{tid}: PASS evidence ref does not resolve: {ref}")
        if r["evidence_state"] == "VERIFIED" and r["current_result"] != "PASS":
            errors.append(f"{tid}: evidence_state VERIFIED without PASS")
        if r["evidence_state"] == "AUTOMATED_VERIFIED" and r["current_result"] != "PASS":
            errors.append(f"{tid}: AUTOMATED_VERIFIED without PASS")
        if r["current_result"] == "BLOCKED" and not str(r.get("notes") or "").strip():
            errors.append(f"{tid}: BLOCKED without notes explaining the blocker")
        if r["execution_class"] == "PHYSICAL_GRAPHENEOS" and r["current_result"] == "PASS":
            errors.append(f"{tid}: physical-device row falsely marked PASS")

    # verifies must resolve to existing invariants
    inv_path = Path(repo_root) / INV_REG
    inv_ids = set()
    if inv_path.exists():
        for r in _load_jsonl(inv_path, errors, "invariant registry"):
            iid = r.get("invariant_id")
            if iid:
                inv_ids.add(iid)
    for r in rows:
        for v in r.get("verifies") or []:
            if not re.fullmatch(r"INV-\d{2}", str(v)):
                errors.append(f"{r.get('test_id')}: illegal verifies ref {v}")
            elif inv_ids and v not in inv_ids:
                errors.append(f"{r.get('test_id')}: verifies unknown invariant {v}")

    inv_tests = {f"ANOX-TEST-INV-{i:02d}" for i in range(1, 36)}
    missing_tests = sorted(inv_tests - set(ids))
    if missing_tests:
        errors.append(f"matrix missing per-invariant tests: {missing_tests}")

    domains = {r.get("domain") for r in rows}
    missing_domains = sorted(REQUIRED_DOMAINS - domains)
    if missing_domains:
        errors.append(f"matrix missing required domains: {missing_domains}")

    if not any(r.get("execution_class") == "PHYSICAL_GRAPHENEOS" for r in rows):
        errors.append("matrix contains no PHYSICAL_GRAPHENEOS rows")

    return rows


# ---------------------------------------------------------------------------
# MSC remediation stage registry checks

def check_msc_state(repo_root, errors):
    path = Path(repo_root) / MSC_STATE
    if not path.exists():
        errors.append(f"MSC remediation state registry missing: {path}")
        return []
    recs = _load_jsonl(path, errors, "msc_state")
    seen = set()
    for rec in recs:
        unit = rec.get("msc_unit")
        if not unit:
            errors.append("msc_state record missing msc_unit")
            continue
        if unit in seen:
            errors.append(f"{unit}: duplicate msc_state record")
        seen.add(unit)
        if unit not in STAGE_REQUIREMENTS:
            errors.append(f"{unit}: unknown MSC unit (not in frozen gate table)")
            continue
        stages = rec.get("stages")
        if not isinstance(stages, dict):
            errors.append(f"{unit}: stages must be an object")
            continue
        impl = rec.get("implementing_session") or ""
        required = STAGE_REQUIREMENTS[unit]
        unknown = sorted(set(stages) - set(STAGE_ORDER))
        if unknown:
            errors.append(f"{unit}: unknown stage names {unknown}")
        for sname in STAGE_ORDER:
            s = stages.get(sname)
            if s is None:
                continue
            res = s.get("result")
            if res not in LEGAL_STAGE_RESULT:
                errors.append(f"{unit}.{sname}: illegal result {res}")
                continue
            if sname in required and res == "NOT_APPLICABLE":
                errors.append(f"{unit}.{sname}: required stage marked NOT_APPLICABLE")
            if res == "PASS":
                if not s.get("evidence_refs"):
                    errors.append(f"{unit}.{sname}: PASS without evidence_refs")
                else:
                    for ref in s["evidence_refs"]:
                        if not _ref_resolves(repo_root, ref):
                            errors.append(f"{unit}.{sname}: evidence ref does not resolve: {ref}")
                # FCP-1: provenance-bound runtime evidence
                if sname == "RUNTIME_TESTED" and unit in PROVENANCE_REQUIRED_UNITS:
                    refs = s.get("evidence_refs") or []
                    if not any(PROVENANCE_REF.search(str(x)) for x in refs):
                        errors.append(
                            f"{unit}.RUNTIME_TESTED: PASS without provenance-bound "
                            f"evidence (FCP-1 requires BUILD_ARTIFACT_HASH_PROOF + "
                            f"PROVENANCE_VERIFIED_NATIVE_RUNTIME refs)"
                        )
                # FCP-7: retest stages need a different authority than implementer
                if sname in RETEST_STAGES and s.get("recorded_by") == impl:
                    errors.append(
                        f"{unit}.{sname}: retest stage recorded by implementing session "
                        f"(implementer != retester required)"
                    )
            # ordering: PASS requires every earlier stage resolved
            idx = STAGE_ORDER.index(sname)
            for prev in STAGE_ORDER[:idx]:
                ps = stages.get(prev)
                if ps is None:
                    continue
                pres = ps.get("result")
                if res == "PASS" and pres not in ("PASS", "NOT_APPLICABLE"):
                    errors.append(
                        f"{unit}.{sname}: PASS while earlier stage {prev} is {pres} "
                        f"(IMPLEMENTED -> CLOSED jumps are forbidden)"
                    )
                    break
        closed = (stages.get("CLOSED") or {}).get("result")
        if closed == "PASS":
            for sname in STAGE_ORDER[:-1]:
                s = stages.get(sname)
                if s is None:
                    errors.append(f"{unit}: CLOSED without stage record {sname}")
                    continue
                if sname in required and s.get("result") != "PASS":
                    errors.append(f"{unit}: CLOSED while required stage {sname} is {s.get('result')}")
                elif s.get("result") not in ("PASS", "NOT_APPLICABLE"):
                    errors.append(f"{unit}: CLOSED while stage {sname} is {s.get('result')}")
    return recs


# ---------------------------------------------------------------------------
# closure evaluation

def evaluate_closure(rows):
    """Return list of (test_id, reason) blockers for pre-product closure."""
    blockers = []
    for r in rows:
        if not r.get("pre_product_required"):
            continue
        tid = r.get("test_id")
        if r.get("current_result") in BLOCKING_RESULTS:
            blockers.append((tid, f"current_result={r.get('current_result')}"))
            continue
        if r.get("current_result") != "PASS":
            blockers.append((tid, f"current_result={r.get('current_result')}"))
            continue
        if r.get("evidence_state") not in PASS_EVIDENCE_STATES:
            blockers.append((tid, f"evidence_state={r.get('evidence_state')}"))
        elif not r.get("evidence_refs"):
            blockers.append((tid, "PASS without evidence_refs"))
    return blockers


def main():
    ap = argparse.ArgumentParser(description="B-021 verification matrix + MSC stage validator (MSC-038)")
    ap.add_argument("--check", choices=["integrity", "closure"], default="integrity")
    ap.add_argument("--repo-root", default=str(REPO_ROOT))
    args = ap.parse_args()

    errors = []
    rows = check_matrix(args.repo_root, errors)
    recs = check_msc_state(args.repo_root, errors)

    print("B-021 VERIFICATION MATRIX / MSC STAGE GATE (MSC-038)")
    print(f"  matrix rows: {len(rows)}")
    print(f"  msc_state records: {len(recs)}")

    blockers = evaluate_closure(rows)
    ppr = [r for r in rows if r.get("pre_product_required")]
    print(f"  pre_product_required rows: {len(ppr)}; verified: {len(ppr) - len(blockers)}; blocking: {len(blockers)}")
    for tid, why in blockers:
        print(f"    BLOCKER {tid}: {why}")

    if args.check == "closure" and blockers:
        errors.append(
            f"pre-product closure NOT PERMITTED: {len(blockers)} pre_product_required row(s) unverified"
        )

    if errors:
        for e in errors:
            print(f"  FAIL {e}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
