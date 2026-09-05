#!/usr/bin/env python3
"""Adversarial regression tests for the hardened MAINARCH-FIX-02 validator.

Proves the deterministic weaknesses identified by MAINARCH-RETEST-02 are
actually closed:

1. target severity mutation -> FAIL
2. prohibited Product file in recorded FIX-02 delivery -> FAIL
3. prohibited CI file in recorded FIX-02 delivery -> FAIL
4. removal of the ANOX-MAINARCH-003 milestone flag -> FAIL
5. removal of the ANOX-MAINARCH-007 milestone flag -> FAIL
6. loss of honest backup residual-retention language -> FAIL
7. valid canonical FIX-02 state -> PASS
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_mainarch_fix02 as v  # noqa: E402


def _load_findings():
    return v.read_jsonl("docs/workforce/registries/findings.jsonl")


def _load_master():
    return v.read_text(v.MASTER_REPORT)


def _load_v12():
    return v.read_text(v.V1_2)


class TestSeverityCheck(unittest.TestCase):
    def test_severity_mutation_fails(self):
        findings = _load_findings()
        master = _load_master()
        for f in findings:
            if f["finding_id"] == "ANOX-MAINARCH-003":
                f["severity"] = "LOW"
        errors = []
        v.check_target_severities(findings, master, errors)
        self.assertTrue(errors, "severity mutation must produce an error")

    def test_severity_correct_passes(self):
        errors = []
        v.check_target_severities(_load_findings(), _load_master(), errors)
        self.assertEqual(errors, [])


class TestDeliveryScopeCheck(unittest.TestCase):
    def test_product_file_fails(self):
        errors = []
        ok = v.check_fix02_delivery_scope(
            errors,
            changed=["docs/authority/x.md", "android/app/src/main/kotlin/Foo.kt"],
        )
        self.assertFalse(ok)
        self.assertTrue(errors)

    def test_ci_file_fails(self):
        errors = []
        ok = v.check_fix02_delivery_scope(
            errors, changed=["docs/authority/x.md", ".github/workflows/ci.yml"]
        )
        self.assertFalse(ok)
        self.assertTrue(errors)

    def test_rust_file_fails(self):
        errors = []
        ok = v.check_fix02_delivery_scope(
            errors, changed=["crypto/rust/src/lib.rs"]
        )
        self.assertFalse(ok)
        self.assertTrue(errors)

    def test_sql_file_fails(self):
        errors = []
        ok = v.check_fix02_delivery_scope(
            errors, changed=["backend/migrations/0001_init.sql"]
        )
        self.assertFalse(ok)
        self.assertTrue(errors)

    def test_recorded_delivery_is_clean(self):
        errors = []
        ok = v.check_fix02_delivery_scope(errors)
        self.assertTrue(ok, f"recorded FIX-02 delivery must be clean: {errors}")


class TestMilestoneFlags(unittest.TestCase):
    def test_remove_003_flag_fails(self):
        text = _load_v12().replace("ANOX-MAINARCH-003", "ANOX-MAINARCH-XXX")
        errors = []
        v.check_milestone_flags(text, errors)
        self.assertTrue(errors)

    def test_remove_007_flag_fails(self):
        text = _load_v12().replace("ANOX-MAINARCH-007", "ANOX-MAINARCH-XXX")
        errors = []
        v.check_milestone_flags(text, errors)
        self.assertTrue(errors)


class TestHonestRetention(unittest.TestCase):
    def test_remove_instant_global_deletion_language_fails(self):
        text = _load_v12().replace("instant global deletion", "fast deletion")
        errors = []
        v.check_honest_backup_retention(text, errors)
        self.assertTrue(errors)

    def test_remove_pitr_horizon_fails(self):
        text = _load_v12().replace("PITR horizon", "recovery window")
        errors = []
        v.check_honest_backup_retention(text, errors)
        self.assertTrue(errors)


class TestCanonicalState(unittest.TestCase):
    def test_valid_state_passes(self):
        self.assertEqual(v.main(), 0)


if __name__ == "__main__":
    unittest.main()
