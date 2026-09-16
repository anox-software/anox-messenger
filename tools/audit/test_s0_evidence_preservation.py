#!/usr/bin/env python3
"""Adversarial tests for the S0 remediation-evidence preservation validator.

Each test copies the canonical preservation surface into a temporary fixture,
mutates exactly one aspect, and asserts the validator FAILS for the intended
reason.  Canonical evidence is never mutated by these tests.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "audit" / "validate_s0_evidence_preservation.py"

IMPL = "docs/reports/security/remediation/REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md"
RETEST_B = "docs/reports/security/retests/INDEPENDENT-ARCHITECTURE-RETEST-S0-001.md"
RETEST_D = "docs/reports/security/retests/TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001.md"
PRES = "docs/reports/security/remediation/SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001.md"
DECISION = "docs/reports/security/decisions/S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001.md"
REGISTRY = "docs/security/audit-evidence/audit_registry.jsonl"
TRACE = "docs/security/audit-evidence/audit_traceability.jsonl"
HASHES = "docs/security/audit-evidence/evidence_hashes.json"
LEDGER = "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl"
STATE = "docs/continuity/CURRENT_STATE.json"
DECISIONS = "docs/workforce/registries/decisions.jsonl"
FINDINGS = "docs/workforce/registries/findings.jsonl"
MANIFEST = "docs/authority/contracts/S0_CONTRACT_FREEZE_MANIFEST.json"

FIXTURE_FILES = [
    IMPL, RETEST_B, RETEST_D, PRES, DECISION,
    "docs/reports/security/decisions/S0-F01-FILE-OWNERSHIP-RATIFICATION-001.md",
    REGISTRY, TRACE, HASHES, LEDGER, STATE, DECISIONS, FINDINGS, MANIFEST,
    "tools/audit/test_s0_contract_freeze.py",
    "tools/audit/test_security_audit_evidence_preservation.py",
    "tools/audit/test_s0_evidence_preservation.py",
]

PRES_ID = "SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001"


def _load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def _write_jsonl(path, records):
    Path(path).write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


class S0EvidencePreservationAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in FIXTURE_FILES:
            src = REPO_ROOT / rel
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    def tearDown(self):
        self.tmp.cleanup()

    def run_validator(self):
        env = dict(os.environ)
        env["S0_EVIDENCE_PRESERVATION_REPO"] = str(self.root)
        return subprocess.run([sys.executable, str(VALIDATOR)],
                              cwd=self.root, env=env, capture_output=True, text=True)

    def assert_fails(self, needle=None):
        r = self.run_validator()
        self.assertNotEqual(r.returncode, 0, f"validator must FAIL; stdout:\n{r.stdout}\n{r.stderr}")
        self.assertIn("FAIL", r.stdout)
        if needle:
            self.assertIn(needle, r.stdout, f"missing expected failure detail {needle!r}:\n{r.stdout}")
        return r

    def _registry(self):
        return _load_jsonl(self.root / REGISTRY)

    def _write_registry(self, recs):
        _write_jsonl(self.root / REGISTRY, recs)

    def _pres(self):
        recs = self._registry()
        return recs, next(r for r in recs if r.get("audit_id") == PRES_ID)

    def _trace(self):
        return _load_jsonl(self.root / TRACE)

    def _write_trace(self, recs):
        _write_jsonl(self.root / TRACE, recs)

    def _mutate_finding(self, fid, **fields):
        recs = self._trace()
        for r in recs:
            if r.get("record_type") == "s0_finding_disposition" and r.get("finding_id") == fid:
                r.update(fields)
        self._write_trace(recs)

    # -- control --------------------------------------------------------------
    # 01. The unmutated preservation surface must PASS.
    def test_01_control_fixture_passes(self):
        r = self.run_validator()
        self.assertEqual(r.returncode, 0, f"unmutated fixture must PASS:\n{r.stdout}\n{r.stderr}")
        self.assertIn("PASS", r.stdout)

    # -- four source reports ----------------------------------------------------
    # 02. S0 implementation report removed.
    def test_02_implementation_report_removed(self):
        (self.root / IMPL).unlink()
        self.assert_fails("missing")

    # 03. First independent retest report removed.
    def test_03_first_retest_removed(self):
        (self.root / RETEST_B).unlink()
        self.assert_fails("missing")

    # 04. Correction report removed (correction shares the canonical record file;
    #     its removal also removes the implementation source — both must fail).
    def test_04_correction_report_removed(self):
        (self.root / IMPL).unlink()
        self.assert_fails("missing")

    # 05. Targeted retest report removed.
    def test_05_targeted_retest_removed(self):
        (self.root / RETEST_D).unlink()
        self.assert_fails("missing")

    # 06. Report hash changed (tampered preserved report).
    def test_06_report_hash_changed(self):
        with open(self.root / RETEST_D, "ab") as f:
            f.write(b"\n tampered")
        self.assert_fails("hash mismatch")

    # -- delivery pins -----------------------------------------------------------
    # 07. Substantive SHA changed.
    def test_07_substantive_sha_changed(self):
        recs, rec = self._pres()
        rec["s0_corrected_substantive_sha"] = "0" * 40
        self._write_registry(recs)
        self.assert_fails("s0_corrected_substantive_sha")

    # 08. Final HEAD changed.
    def test_08_final_head_changed(self):
        recs, rec = self._pres()
        rec["s0_corrected_final_head_sha"] = "0" * 40
        self._write_registry(recs)
        self.assert_fails("s0_corrected_final_head_sha")

    # -- F-01 ratification ---------------------------------------------------------
    # 09. F-01 ratification record removed.
    def test_09_f01_ratification_removed(self):
        recs = [r for r in _load_jsonl(self.root / DECISIONS)
                if r.get("decision_id") != "ANOX-DECISION-S0-F01-RATIFICATION-001"]
        _write_jsonl(self.root / DECISIONS, recs)
        self.assert_fails("RATIFICATION")

    # 10. F-01 ratification generalized.
    def test_10_f01_ratification_generalized(self):
        recs = _load_jsonl(self.root / DECISIONS)
        for r in recs:
            if r.get("decision_id") == "ANOX-DECISION-S0-F01-RATIFICATION-001":
                r["grants_general_ownership"] = True
        _write_jsonl(self.root / DECISIONS, recs)
        self.assert_fails("grants_general_ownership")

    # -- F-02…F-10 flipped to OPEN ------------------------------------------------
    # 11-19. Each finding's final disposition must remain FIXED.
    def test_11_f02_reopened(self):
        self._mutate_finding("F-02", final_disposition="OPEN")
        self.assert_fails("F-02")

    def test_12_f03_reopened(self):
        self._mutate_finding("F-03", final_disposition="OPEN")
        self.assert_fails("F-03")

    def test_13_f04_reopened(self):
        self._mutate_finding("F-04", final_disposition="OPEN")
        self.assert_fails("F-04")

    def test_14_f05_reopened(self):
        self._mutate_finding("F-05", final_disposition="OPEN")
        self.assert_fails("F-05")

    def test_15_f06_reopened(self):
        self._mutate_finding("F-06", final_disposition="OPEN")
        self.assert_fails("F-06")

    def test_16_f07_reopened(self):
        self._mutate_finding("F-07", final_disposition="OPEN")
        self.assert_fails("F-07")

    def test_17_f08_reopened(self):
        self._mutate_finding("F-08", final_disposition="OPEN")
        self.assert_fails("F-08")

    def test_18_f09_reopened(self):
        self._mutate_finding("F-09", final_disposition="OPEN")
        self.assert_fails("F-09")

    def test_19_f10_reopened(self):
        self._mutate_finding("F-10", final_disposition="OPEN")
        self.assert_fails("F-10")

    # -- residual LOW follow-ups ---------------------------------------------------
    # 20. Residual LOW A (F-05) removed.
    def test_20_residual_low_a_removed(self):
        recs = [r for r in self._trace()
                if r.get("followup_id") != "S0-RESIDUAL-LOW-F05-UNANCHORED-CC-CLAUSES"]
        self._write_trace(recs)
        self.assert_fails("S0-RESIDUAL-LOW-F05")

    # 21. Residual LOW B (F-08) removed.
    def test_21_residual_low_b_removed(self):
        recs = [r for r in self._trace()
                if r.get("followup_id") != "S0-RESIDUAL-LOW-F08-AUTHORITY-HOME-FREETEXT"]
        self._write_trace(recs)
        self.assert_fails("S0-RESIDUAL-LOW-F08")

    # 22. A LOW follow-up falsely marked CLOSED.
    def test_22_low_followup_falsely_closed(self):
        recs = self._trace()
        for r in recs:
            if r.get("followup_id") == "S0-RESIDUAL-LOW-F05-UNANCHORED-CC-CLAUSES":
                r["status"] = "CLOSED"
        self._write_trace(recs)
        self.assert_fails("OPEN")

    # -- lifecycle claims ------------------------------------------------------------
    # 23. An S0 MSC unit marked CLOSED.
    def test_23_s0_msc_marked_closed(self):
        recs = self._trace()
        for r in recs:
            if r.get("record_type") == "s0_unit_evidence" and r.get("msc_unit") == "MSC-UNIT-040":
                r["closed_by_s0"] = True
        self._write_trace(recs)
        self.assert_fails("closure")

    # 24. Global open MSC changed from 42 without authority.
    def test_24_open_msc_changed(self):
        recs, rec = self._pres()
        rec["open_msc_units"] = 41
        self._write_registry(recs)
        self.assert_fails("open_msc_units")

    # 25. S1 file attributed to S0.
    def test_25_s1_file_attributed(self):
        recs, rec = self._pres()
        rec["s1_files_changed_by_s0"] = 1
        self._write_registry(recs)
        self.assert_fails("s1_files_changed_by_s0")

    # 26. Product behavior claimed changed.
    def test_26_product_behavior_claimed(self):
        recs, rec = self._pres()
        rec["product_behavior_changed"] = "YES"
        self._write_registry(recs)
        self.assert_fails("product_behavior_changed")

    # -- coverage pins -----------------------------------------------------------------
    # 27-29. Coverage pins downgraded (record claims <14/<14/<18).
    def test_27_sc_coverage_downgraded(self):
        p = self.root / PRES
        p.write_text(p.read_text(encoding="utf-8").replace("SC-1…SC-14 = 14/14", "SC-1…SC-14 = 13/14"), encoding="utf-8")
        self.assert_fails("coverage pin")

    def test_28_cc_coverage_downgraded(self):
        p = self.root / PRES
        p.write_text(p.read_text(encoding="utf-8").replace("CC-1…CC-14 = 14/14", "CC-1…CC-14 = 13/14"), encoding="utf-8")
        self.assert_fails("coverage pin")

    def test_29_breaker_coverage_downgraded(self):
        p = self.root / PRES
        p.write_text(p.read_text(encoding="utf-8").replace("SERVER_BREAKER_S1…S18 = 18/18", "SERVER_BREAKER_S1…S18 = 17/18"), encoding="utf-8")
        self.assert_fails("coverage pin")

    # 30. Contract ambiguities become nonzero.
    def test_30_ambiguities_nonzero(self):
        p = self.root / MANIFEST
        man = json.loads(p.read_text(encoding="utf-8"))
        man["contract_ambiguities"] = 1
        p.write_text(json.dumps(man, indent=1), encoding="utf-8")
        self.assert_fails("ambiguit")

    # -- prior evidence / invariants -----------------------------------------------------
    # 31. Previous evidence weakened (a prior registry record loses its preserved
    # report hash — the field that binds it to byte-exact evidence).
    def test_31_previous_evidence_weakened(self):
        recs = self._registry()
        for r in recs:
            if r.get("record_id") == "SEC-AUDIT-REG-0012":
                r["report_sha256"] = "REWRITTEN"
        self._write_registry(recs)
        self.assert_fails("weakened")

    # 32. ROOT-016 revived.
    def test_32_root016_revived(self):
        recs = self._trace()
        for r in recs:
            if r.get("record_type") == "consensus_root" and r.get("root_id") == "ROOT-016":
                r["status"] = "ACTIVE"
        self._write_trace(recs)
        self.assert_fails("ROOT-016")

    # 33. ROOT-013 severity changed.
    def test_33_root013_severity_changed(self):
        recs = self._trace()
        for r in recs:
            if r.get("record_type") == "canonical_severity_transition" and r.get("finding_id") == "ROOT-013":
                r["current_canonical_severity"] = "LOW"
        self._write_trace(recs)
        self.assert_fails("ROOT-013")

    # 34. ARCH-010 retired prematurely.
    def test_34_arch010_retired(self):
        recs = _load_jsonl(self.root / FINDINGS)
        for r in recs:
            if r.get("finding_id") == "ANOX-SECURITY-ARCH-010":
                r["status"] = "Closed"
        _write_jsonl(self.root / FINDINGS, recs)
        self.assert_fails("ARCH-010")

    # -- event / S1 / B004 -----------------------------------------------------------------
    # 35. Preservation event mutated (wrong start_head — also breaks ordering claim).
    def test_35_event_start_head_mutated(self):
        recs = _load_jsonl(self.root / LEDGER)
        for r in recs:
            if r.get("event_id") == "ANOX-EVENT-0054":
                r["start_head"] = "0" * 40
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_fails("start_head")

    # 36. Event/state claims S1 already integrated.
    def test_36_s1_integration_claimed(self):
        recs, rec = self._pres()
        rec["s1"] = "INTEGRATED"
        self._write_registry(recs)
        self.assert_fails()

    # 37. B004 marked started.
    def test_37_b004_started(self):
        recs, rec = self._pres()
        rec["b004"] = "STARTED"
        self._write_registry(recs)
        self.assert_fails("b004")

    # -- extra guards ------------------------------------------------------------------------
    # 38. Preservation event dropped from the ledger.
    def test_38_event_removed(self):
        recs = [r for r in _load_jsonl(self.root / LEDGER) if r.get("event_id") != "ANOX-EVENT-0054"]
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_fails("ANOX-EVENT-0054")

    # 39. Preservation ratification decision removed.
    def test_39_preservation_decision_removed(self):
        recs = [r for r in _load_jsonl(self.root / DECISIONS)
                if r.get("decision_id") != "ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001"]
        _write_jsonl(self.root / DECISIONS, recs)
        self.assert_fails("RATIFICATION-001")

    # 40. Source-B reconstruction marker dropped (verbatim claim / unmarked reconstruction).
    def test_40_source_b_marker_dropped(self):
        p = self.root / RETEST_B
        p.write_text(p.read_text(encoding="utf-8").replace(
            "VERBATIM_ORIGINAL_TRANSCRIPT_AVAILABLE = NO", "VERBATIM_ORIGINAL_TRANSCRIPT_AVAILABLE = YES"),
            encoding="utf-8")
        self.assert_fails("marker")


if __name__ == "__main__":
    unittest.main()
