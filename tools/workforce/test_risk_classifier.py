#!/usr/bin/env python3
"""Adversarial tests for B-028 risk_classifier.py — tier + scope gaming."""

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import risk_classifier as rc


def task(**kw):
    t = {"task_id": "ANOX-TASK-R-001", "security_class": "S2",
         "allowed_paths": ["docs/**"]}
    t.update(kw)
    return t


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tiers_path = Path(self.tmp.name) / "domain_tiers.json"
        self.tiers_path.write_text(json.dumps({
            "schema_version": "B028-DT-v1",
            "default_tier": "SEC-C",
            "domains": [
                {"domain": "CONTROL_SURFACE", "tier": "SEC-C",
                 "required_evidence": "E3", "globs": ["tools/audit/**"]},
                {"domain": "TRUST_BOUNDARY", "tier": "SEC-B",
                 "required_evidence": "E3", "globs": ["crypto/**"]},
                {"domain": "DOCS_ONLY", "tier": "SEC-A",
                 "required_evidence": "E1", "globs": ["docs/**", "*.md"]},
            ],
        }))
        self.tmpdir = self.tmp

    def tearDown(self):
        self.tmp.cleanup()

    def classify(self, t, changed=None):
        return rc.classify(t, changed or [], tiers_path=self.tiers_path)


class TierTests(Fixture):
    def test_docs_only_task_is_sec_a(self):
        v = self.classify(task(security_class="S0"), ["docs/x.md"])
        self.assertEqual(v["tier"], "SEC-A")
        self.assertEqual(v["result"], "CLASSIFIED")

    def test_control_surface_forces_sec_c(self):
        t = task(security_class="S0", allowed_paths=["tools/audit/v.py"])
        v = self.classify(t, ["tools/audit/v.py"])
        self.assertEqual(v["tier"], "SEC-C")
        self.assertTrue(v["control_surface"])
        self.assertTrue(v["requires_independent_review"])

    def test_severity_max_with_domain(self):
        t = task(security_class="S4", allowed_paths=["docs/**"])
        v = self.classify(t, ["docs/x.md"])
        self.assertEqual(v["tier"], "SEC-C")

    def test_unknown_path_fails_closed_sec_c(self):
        t = task(allowed_paths=["mystery/**"])
        v = self.classify(t, ["mystery/x.bin"])
        self.assertEqual(v["tier"], "SEC-C")
        self.assertTrue(any("unclassified" in p for p in v["problems"]))


class ScopeGamingTests(Fixture):
    def test_undeclared_changed_path_blocked(self):
        t = task(allowed_paths=["docs/**"])
        v = self.classify(t, ["docs/x.md", "crypto/rust/src/lib.rs"])
        self.assertEqual(v["result"], "BLOCKED")
        self.assertTrue(any("outside declared scope" in p for p in v["problems"]))

    def test_narrow_declaration_gaming_caught(self):
        # Declared docs-only but wrote a validator -> blocked, not downgraded.
        t = task(allowed_paths=["docs/**"])
        v = self.classify(t, ["docs/x.md", "tools/audit/validate_x.py"])
        self.assertEqual(v["result"], "BLOCKED")
        self.assertEqual(v["tier"], "SEC-C")

    def test_metadata_allowlist_not_scope_violation(self):
        t = task(allowed_paths=["docs/**"])
        v = self.classify(t, ["docs/x.md", "PROJECT_STATE.md"])
        self.assertEqual(v["result"], "CLASSIFIED")

    def test_empty_allowed_paths_fail_closed(self):
        t = task(allowed_paths=[])
        v = self.classify(t, ["docs/x.md"])
        self.assertEqual(v["result"], "BLOCKED")

    def test_unknown_security_class_fail_closed(self):
        t = task(security_class="S9")
        v = self.classify(t, ["docs/x.md"])
        self.assertEqual(v["tier"], "SEC-C")

    def test_glob_declaration_covers_nested(self):
        t = task(allowed_paths=["crypto/**"], security_class="S2")
        v = self.classify(t, ["crypto/rust/src/lib.rs"])
        self.assertEqual(v["result"], "CLASSIFIED")
        self.assertEqual(v["tier"], "SEC-B")


if __name__ == "__main__":
    unittest.main()
