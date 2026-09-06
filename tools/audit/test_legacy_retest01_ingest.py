#!/usr/bin/env python3
"""Adversarial regression tests for the LEGACY-RETEST-01-INGEST validator and
the hardened historical validators.

Each test injects a corruption and proves the deterministic check still fails.
Positive controls prove the legal post-ingest state is accepted.

 1. deleted finding                       -> FAIL
 2. closure without FIX/RETEST chain      -> FAIL
 3. consolidation severity/candidate tampering -> FAIL
 4. rewritten frozen consolidation snapshot  -> FAIL
 5. historical MAINARCH audit evidence removed -> FAIL
 6. illegal lifecycle transition           -> FAIL
 7. fake retest evidence (wrong SHA/IDs)   -> FAIL
 8. wrong retest-base ancestry             -> FAIL
 9. Claude trigger field / prose non-trigger
10. product state unblocked               -> FAIL
11. legal Open->RFR and RFR->Closed       -> PASS (positive controls)
"""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lifecycle_legality as ll  # noqa: E402
import validate_legacy_audit_consolidation as cons  # noqa: E402
import validate_legacy_retest01_ingest as v  # noqa: E402


FINDINGS = "docs/workforce/registries/findings.jsonl"
AUDITS = "docs/workforce/registries/audits.jsonl"


def _findings():
    return v.read_jsonl(FINDINGS)


def _audits():
    return v.read_jsonl(AUDITS)


class TestFindingDeletion(unittest.TestCase):
    def test_deleted_target_detected(self):
        findings = [f for f in _findings() if f["finding_id"] != "ANOX-LEGACY-CRYPTO-005"]
        errors = []
        v.check_target_closures(errors, findings=findings, audits=_audits())
        self.assertTrue(errors, "deleted target finding must fail")

    def test_deleted_nontarget_detected(self):
        findings = [f for f in _findings() if f["finding_id"] != "ANOX-LEGACY-B003-001"]
        errors = []
        v.check_non_target_findings(errors, findings=findings, audits=_audits())
        self.assertTrue(errors, "deleted non-target finding must fail")


class TestClosureChain(unittest.TestCase):
    def test_closure_without_chain_detected(self):
        findings = copy.deepcopy(_findings())
        for f in findings:
            if f["finding_id"] == "ANOX-MAINARCH-019":
                f["closure_evidence"] = ["LEGACY-FIX-01"]  # RETEST + SHAs stripped
                break
        errors = []
        v.check_target_closures(errors, findings=findings, audits=_audits())
        self.assertTrue(errors, "closure without complete chain must fail")

    def test_closure_actor_missing_detected(self):
        findings = copy.deepcopy(_findings())
        for f in findings:
            if f["finding_id"] == "ANOX-MAINARCH-019":
                f["closure_actor"] = ""
                break
        errors = []
        v.check_target_closures(errors, findings=findings, audits=_audits())
        self.assertTrue(errors, "missing closure_actor must fail")

    def test_unauthorized_nontarget_closure_detected(self):
        findings = copy.deepcopy(_findings())
        for f in findings:
            if f["finding_id"] == "ANOX-MAINARCH-013":
                f["status"] = "Closed"
                break
        errors = []
        v.check_non_target_findings(errors, findings=findings, audits=_audits())
        self.assertTrue(errors, "unauthorized non-target closure must fail")


class TestConsolidationTampering(unittest.TestCase):
    def _freeze_data(self):
        return json.loads((v.REPO / "tools/audit/legacy_audit_set_freeze_data.json").read_text())

    def test_severity_tampering_detected(self):
        findings = copy.deepcopy(_findings())
        for f in findings:
            if f["finding_id"] == "ANOX-LEGACY-B003-001":
                f["severity"] = "CRITICAL"
                break
        ok = cons.validate_findings(self._freeze_data(), findings=findings, audits=_audits())
        self.assertFalse(ok, "severity mutation vs frozen data must fail")

    def test_rewritten_freeze_snapshot_detected(self):
        data = self._freeze_data()
        data["new_findings"] = [n for n in data["new_findings"]
                                if n["finding_id"] != "ANOX-LEGACY-INTEGRATION-005"]
        ok = cons.validate_findings(data, findings=_findings(), audits=_audits())
        self.assertFalse(ok, "rewritten frozen snapshot must fail")


class TestHistoricalEvidence(unittest.TestCase):
    def test_removed_retest03_record_detected(self):
        audits = [a for a in _audits() if a.get("audit_id") != "MAINARCH-RETEST-03"]
        errors = []
        v.check_non_target_findings(errors, findings=_findings(), audits=audits)
        self.assertTrue(errors, "removing MAINARCH-RETEST-03 must orphan its closures")

    def test_removed_legac_retest_record_detected(self):
        audits = [a for a in _audits() if a.get("audit_id") != "LEGACY-RETEST-01"]
        errors = []
        v.check_target_closures(errors, findings=_findings(), audits=audits)
        self.assertTrue(errors, "removing LEGACY-RETEST-01 must orphan the 8 closures")


class TestIllegalTransition(unittest.TestCase):
    def test_invented_status_detected(self):
        findings = copy.deepcopy(_findings())
        for f in findings:
            if f["finding_id"] == "ANOX-MAINARCH-013":
                f["status"] = "Resolved"
                break
        errors = []
        v.check_non_target_findings(errors, findings=findings, audits=_audits())
        self.assertTrue(errors, "invented status must fail")

    def test_reopen_with_closure_evidence_detected(self):
        findings = copy.deepcopy(_findings())
        for f in findings:
            if f["finding_id"] == "ANOX-MAINARCH-019":
                f["status"] = "Open"  # retains closure_evidence -> silent reopen
                break
        errors = []
        v.check_non_target_findings(errors, findings=findings, audits=_audits())
        self.assertTrue(errors, "reopened finding retaining closure evidence must fail")


class TestFakeRetestEvidence(unittest.TestCase):
    def test_wrong_canonical_sha_detected(self):
        audits = copy.deepcopy(_audits())
        for a in audits:
            if a.get("audit_id") == "LEGACY-RETEST-01":
                a["canonical_sha"] = "0" * 40
                break
        errors = []
        v.check_retest_identity(errors, audits=audits)
        self.assertTrue(errors, "wrong retest base SHA must fail")

    def test_wrong_finding_set_detected(self):
        audits = copy.deepcopy(_audits())
        retest = next(a for a in audits if a.get("audit_id") == "LEGACY-RETEST-01")
        retest["finding_ids"] = ["ANOX-MAINARCH-001"]
        errors = []
        v.check_retest_result(errors, retest)
        self.assertTrue(errors, "wrong retest finding set must fail")

    def test_fail_ids_recorded_detected(self):
        audits = copy.deepcopy(_audits())
        retest = next(a for a in audits if a.get("audit_id") == "LEGACY-RETEST-01")
        retest["failed_ids"] = ["ANOX-MAINARCH-019"]
        errors = []
        v.check_retest_result(errors, retest)
        self.assertTrue(errors, "recorded FAIL ids must fail")


class TestBaseAncestry(unittest.TestCase):
    def test_bogus_base_not_ancestor(self):
        self.assertFalse(v.git_is_ancestor("0" * 40, "HEAD"),
                         "a bogus base SHA must not be an ancestor")

    def test_real_base_is_ancestor(self):
        self.assertTrue(v.git_is_ancestor(v.RETEST_BASE_SHA, "HEAD"),
                        "the canonical retest base must be an ancestor of HEAD")

    def test_fix01_commits_are_ancestors(self):
        self.assertTrue(v.git_is_ancestor(v.FIX01_SUBSTANTIVE_SHA, v.RETEST_BASE_SHA))
        self.assertTrue(v.git_is_ancestor(v.FIX01_METADATA_SHA, v.RETEST_BASE_SHA))


class TestClaudeTrigger(unittest.TestCase):
    def test_structured_trigger_detected(self):
        tasks = [{"task_id": "ANOX-TASK-X", "status": "Open", "claude_audit_triggered": True}]
        errors = []
        v.check_no_claude(errors, tasks=tasks, audits=[], ws={}, retest={})
        self.assertTrue(errors, "structured claude trigger must fail")

    def test_provider_field_detected(self):
        audits = [{"audit_id": "X", "model": "claude-3"}]
        errors = []
        v.check_no_claude(errors, tasks=[], audits=audits, ws={}, retest={})
        self.assertTrue(errors, "provider/model field naming the external model must fail")

    def test_prose_prohibition_not_a_trigger(self):
        tasks = [{"task_id": "ANOX-TASK-X", "status": "Candidate",
                  "non_goals": ["Immediate Claude/security audit — prohibited"],
                  "scope": "no claude usage allowed"}]
        evidence = ll.detect_claude_trigger(tasks=tasks)
        self.assertEqual(evidence, [], f"prohibition prose must not trigger: {evidence}")


class TestProductGate(unittest.TestCase):
    def test_product_unblocked_detected(self):
        ws = {"final_pre_product_audit": {"product_development_state": "UNBLOCKED"}}
        ir = json.loads(v.read_text(v.IR_REG))
        errors = []
        v.check_product_blocked(errors, ws=ws, ir=ir)
        self.assertTrue(errors, "unblocked product state must fail")

    def test_b004_started_detected(self):
        ws = json.loads(v.read_text("docs/workforce/WORKFORCE_STATE.json"))
        ir = json.loads(v.read_text(v.IR_REG))
        ir["domains"]["B-004"]["implementation_state"] = "STARTED"
        errors = []
        v.check_product_blocked(errors, ws=ws, ir=ir)
        self.assertTrue(errors, "B-004 implementation start must fail")


class TestPositiveControls(unittest.TestCase):
    def test_legal_rfr_transition_accepted(self):
        f = {"finding_id": "X", "status": "Ready For Retest",
             "remediation_refs": ["SOME-FIX-01", "tools/audit/validate_some_fix01.py"]}
        ok, reason = ll.finding_status_legal(f, [])
        self.assertTrue(ok, f"legal RFR must pass: {reason}")

    def test_legal_closure_accepted(self):
        audits = [{"audit_id": "SOME-RETEST-01", "audit_type": "DELTA", "result": "PASS",
                   "closed_findings": ["X"]}]
        f = {"finding_id": "X", "status": "Closed", "closure_actor": "independent",
             "closure_evidence": ["SOME-FIX-01", "SOME-RETEST-01", "git:" + "a" * 40]}
        ok, reason = ll.finding_status_legal(f, audits)
        self.assertTrue(ok, f"legal closure must pass: {reason}")

    def test_real_post_ingest_state_accepted(self):
        errors = []
        v.check_target_closures(errors, findings=_findings(), audits=_audits())
        v.check_non_target_findings(errors, findings=_findings(), audits=_audits())
        self.assertFalse(errors, f"real post-ingest state must pass: {errors}")


if __name__ == "__main__":
    unittest.main()
