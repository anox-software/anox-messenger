#!/usr/bin/env python3
"""Adversarial regression tests for the MAINARCH-FIX-03 validator.

Proves the deterministic weaknesses the retest is meant to close:

 1. target severity mutation -> FAIL
 2. missing traceability row -> FAIL
 3. duplicate test ID -> FAIL
 4. fabricated PASS for physical GrapheneOS test -> FAIL
 5. conflated SPEC_ONLY with TESTED -> FAIL
 6. missing B-004/B-005 NOT_STARTED implementation state -> FAIL
 7. false branch-protection claim -> FAIL
 8. product/CI/Rust/backend/SQL file in recorded delivery -> FAIL
 9. missing/malformed invariant verification_id reference -> FAIL
10. removal of 003/007/024 milestone security-review flag -> FAIL
11. fabricated branch-protection human decision -> FAIL
12. release/incident domains falsely marked release-ready -> FAIL
13. valid canonical FIX-03 state -> PASS
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_mainarch_fix03 as v  # noqa: E402


class TestSeverity(unittest.TestCase):
    def test_severity_mutation_fails(self):
        findings = v.read_jsonl("docs/workforce/registries/findings.jsonl")
        for f in findings:
            if f["finding_id"] == "ANOX-MAINARCH-011":
                f["severity"] = "LOW"
                break
        errors = []
        v.check_findings(errors, findings)
        self.assertTrue(errors, "severity mutation must produce an error")

    def test_severity_correct_passes(self):
        errors = []
        v.check_findings(errors)
        self.assertFalse(any("severity" in e for e in errors), f"severity check failed: {errors}")


class TestTraceability(unittest.TestCase):
    def test_missing_invariant_row_fails(self):
        rows = v.read_jsonl(v.INV_REG)
        rows = [r for r in rows if r["invariant_id"] != "INV-08"]
        errors = []
        v.check_invariants_traced(errors, inv_rows=rows)
        self.assertTrue(errors, "missing invariant row must produce an error")

    def test_duplicate_invariant_id_fails(self):
        rows = v.read_jsonl(v.INV_REG)
        dup = dict(rows[0])
        rows.append(dup)
        errors = []
        v.check_invariants_traced(errors, inv_rows=rows)
        self.assertTrue(errors, "duplicate invariant must produce an error")


class TestMatrix(unittest.TestCase):
    def test_duplicate_test_id_fails(self):
        rows = v.read_jsonl(v.MAT_REG)
        dup = dict(rows[0])
        rows.append(dup)
        errors = []
        v.check_matrix_coverage(errors, mat_rows=rows)
        self.assertTrue(errors, "duplicate test id must produce an error")

    def test_physical_pass_fabrication_fails(self):
        rows = v.read_jsonl(v.MAT_REG)
        for r in rows:
            if r["execution_class"] == "PHYSICAL_GRAPHENEOS":
                r["current_result"] = "PASS"
                r["evidence_refs"] = ["nonsense"]
                break
        errors = []
        v.check_matrix_coverage(errors, mat_rows=rows)
        self.assertTrue(errors, "fabricated physical PASS must fail")

    def test_b017_b020_missing_fails(self):
        rows = v.read_jsonl(v.MAT_REG)
        rows = [r for r in rows if r["domain"] not in ("B-017", "B-020")]
        errors = []
        v.check_matrix_coverage(errors, mat_rows=rows)
        self.assertTrue(errors, "missing B-017/B-020 must produce an error")


class TestVerificationIdRefs(unittest.TestCase):
    def test_missing_verification_id_reference_fails(self):
        inv = v.read_jsonl(v.INV_REG)
        inv[0]["verification_ids"] = ["ANOX-TEST-B999-999"]  # not in matrix
        errors = []
        v.check_verification_id_refs(errors, inv_rows=inv)
        self.assertTrue(errors, "missing referenced matrix test must fail")

    def test_malformed_verification_id_fails(self):
        inv = v.read_jsonl(v.INV_REG)
        inv[1]["verification_ids"] = ["NOT-A-TEST-ID"]
        errors = []
        v.check_verification_id_refs(errors, inv_rows=inv)
        self.assertTrue(errors, "malformed verification_id must fail")

    def test_duplicate_referenced_target_fails(self):
        mat = v.read_jsonl(v.MAT_REG)
        dup = dict(mat[0])
        mat.append(dup)  # now the referenced test_id exists twice
        errors = []
        v.check_verification_id_refs(errors, mat_rows=mat)
        self.assertTrue(errors, "duplicated referenced matrix test must fail")

    def test_unknown_verifies_invariant_fails(self):
        mat = v.read_jsonl(v.MAT_REG)
        mat[0]["verifies"] = ["INV-99"]
        errors = []
        v.check_verification_id_refs(errors, mat_rows=mat)
        self.assertTrue(errors, "unknown verifies invariant must fail")

    def test_missing_per_invariant_test_fails(self):
        mat = [r for r in v.read_jsonl(v.MAT_REG) if r["test_id"] != "ANOX-TEST-INV-12"]
        errors = []
        v.check_verification_id_refs(errors, mat_rows=mat)
        self.assertTrue(errors, "missing ANOX-TEST-INV-NN row must fail")


class TestConflation(unittest.TestCase):
    def test_spec_only_conflation_fails(self):
        rows = v.read_jsonl(v.INV_REG)
        for r in rows:
            if r["invariant_id"] == "INV-02":
                r["evidence_state"] = "VERIFIED"
                r["verification_state"] = "TESTED"
                r["physical_state"] = "VERIFIED"
                r["external_state"] = "VERIFIED"
                r["automated_state"] = "PASS"
                break
        errors = []
        v.check_state_model_honest(errors, inv_rows=rows)
        self.assertTrue(errors, "conflated SPEC_ONLY->VERIFIED must fail")


class TestReadiness(unittest.TestCase):
    def test_b004_b005_implementation_started_fails(self):
        ir = json.loads(v.read_text(v.IR_REG))
        ir["domains"]["B-004"]["implementation_state"] = "VERIFIED"
        ir["domains"]["B-005"]["implementation_state"] = "IMPLEMENTED_UNVERIFIED"
        errors = []
        v.check_implementation_readiness(errors, ir_data=ir)
        self.assertTrue(errors, "B-004/B-005 implemented must fail")


class TestScope(unittest.TestCase):
    def test_product_file_in_delivery_fails(self):
        errors = []
        v.check_fix03_delivery_scope(errors, changed=["android/app/src/main/Foo.kt", "docs/security/x.md"])
        self.assertTrue(errors)

    def test_ci_workflow_in_delivery_fails(self):
        errors = []
        v.check_fix03_delivery_scope(errors, changed=[".github/workflows/ci.yml"])
        self.assertTrue(errors)

    def test_rust_backend_sql_in_delivery_fails(self):
        for bad in ("crypto/rust/src/lib.rs", "backend/src/main.py",
                    "migrations/001_init.sql", "supabase/seed.sql"):
            errors = []
            v.check_fix03_delivery_scope(errors, changed=[bad, "docs/workforce/registries/x.jsonl"])
            self.assertTrue(errors, f"{bad} must fail scope check")


class TestReleaseGovernance(unittest.TestCase):
    def test_false_branch_protection_claim(self):
        text = v.read_text(v.V1_3) + "\nserver-side branch protection is enforced.\n"
        errors = []
        v.check_release_governance(errors, v13_text=text)
        self.assertTrue(errors, "false branch protection claim must fail")

    def test_false_branch_protection_claim_variants(self):
        for claim in ("branch protection is enabled", "rulesets are active",
                      "branch protection is active", "protection is enforced by GitHub"):
            errors = []
            v.check_release_governance(errors, v13_text=v.read_text(v.V1_3) + f"\n{claim}.\n")
            self.assertTrue(errors, f"false claim '{claim}' must fail")

    def test_fabricated_branch_protection_decision_fails(self):
        decisions = [{"decision_id": "ANOX-DECISION-9999", "role_id": "ROLE-001",
                      "decision": "approve equivalent control instead of branch protection"}]
        errors = []
        v.check_release_governance(errors, decisions=decisions)
        self.assertTrue(errors, "fabricated equivalent-control decision must fail")

    def test_release_domains_marked_ready_fails(self):
        ir = json.loads(v.read_text(v.IR_REG))
        ir["domains"]["B-023"]["release_readiness"] = "RELEASE_AUTHORIZED"
        errors = []
        v.check_release_governance(errors, ir_data=ir)
        self.assertTrue(errors, "B-023 falsely release-authorized must fail")


class TestMilestoneFlags(unittest.TestCase):
    def _findings_without_flag(self, fid):
        findings = v.read_jsonl("docs/workforce/registries/findings.jsonl")
        for f in findings:
            if f["finding_id"] == fid:
                f.pop("milestone_security_review", None)
        return findings

    def test_003_flag_removal_fails(self):
        errors = []
        v.check_milestone_flags(errors, findings=self._findings_without_flag("ANOX-MAINARCH-003"))
        self.assertTrue(errors, "003 milestone flag removal must fail")

    def test_007_flag_removal_fails(self):
        errors = []
        v.check_milestone_flags(errors, findings=self._findings_without_flag("ANOX-MAINARCH-007"))
        self.assertTrue(errors, "007 milestone flag removal must fail")

    def test_024_flag_removal_fails(self):
        errors = []
        v.check_milestone_flags(errors, findings=self._findings_without_flag("ANOX-MAINARCH-024"))
        self.assertTrue(errors, "024 milestone flag removal must fail")

    def test_024_flag_text_removal_fails(self):
        v13 = v.read_text(v.V1_3).replace("ANOX-MAINARCH-024", "ANOX-MAINARCH-999")
        errors = []
        v.check_milestone_flags(errors, v13_text=v13)
        self.assertTrue(errors, "024 milestone text removal must fail")


class TestCanonicalState(unittest.TestCase):
    def test_valid_state_passes(self):
        self.assertEqual(v.main(), 0)


if __name__ == "__main__":
    unittest.main()
