#!/usr/bin/env python3
"""Adversarial tests for B-028 validate_session_evidence.py — fail closed."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_session_evidence as vse


TASK = {"task_id": "ANOX-TASK-SES-001", "role_id": "ROLE-004",
        "branch": "remediation/ses-001", "start_sha": "a" * 40,
        "allowed_paths": ["docs/**"], "status": "Authorized"}


def manifest(**kw):
    m = {
        "schema_version": "B028-SES-v1",
        "session_id": "REMEDIATION-SESSION-TEST-001",
        "security_class": "S2",
        "authorized_task_id": "ANOX-TASK-SES-001",
        "covered_units": ["MSC-UNIT-001"],
        "artifacts": [{"path": "EVIDENCE.md", "sha256": "", "kind": "report"}],
        "required_retests": [
            {"unit": "MSC-UNIT-001", "level": "E3",
             "binding": "independent_retest", "satisfied_by": "RETEST-001",
             "status": "SATISFIED"}
        ],
        "provenance": {"base_sha": "b" * 40, "delivery_branch": "remediation/ses-001"},
    }
    m.update(kw)
    return m


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs/workforce/registries").mkdir(parents=True)
        (self.root / "docs/security/remediation").mkdir(parents=True)
        (self.root / "EVIDENCE.md").write_text("pinned content")
        self.evid_hash = hashlib.sha256(b"pinned content").hexdigest()
        (self.root / vse.TASKS_PATH).write_text(json.dumps(TASK) + "\n")
        (self.root / vse.MSC_PATH).write_text(
            json.dumps({"msc_unit": "MSC-UNIT-001"}) + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def run_manifest(self, m):
        path = self.root / "session.json"
        path.write_text(json.dumps(m))
        return vse.validate(path, self.root)

    def good(self):
        m = manifest()
        m["artifacts"][0]["sha256"] = self.evid_hash
        return m


class SchemaTests(Fixture):
    def test_valid_manifest_schema_passes(self):
        self.assertEqual(vse.check_schema(self.good()), [])

    def test_missing_required_field_fails(self):
        m = self.good()
        del m["security_class"]
        self.assertTrue(any("missing required" in p for p in vse.check_schema(m)))

    def test_unknown_field_fails(self):
        m = self.good()
        m["injected"] = True
        self.assertTrue(any("unknown fields" in p for p in vse.check_schema(m)))

    def test_unknown_schema_version_fails(self):
        m = self.good()
        m["schema_version"] = "B028-SES-v2"
        self.assertTrue(any("schema_version" in p for p in vse.check_schema(m)))

    def test_retest_for_uncovered_unit_fails(self):
        m = self.good()
        m["required_retests"][0]["unit"] = "MSC-UNIT-099"
        self.assertTrue(any("not in covered_units" in p for p in vse.check_schema(m)))

    def test_malformed_unit_fails(self):
        m = self.good()
        m["covered_units"] = ["unit-1"]
        self.assertTrue(any("malformed" in p for p in vse.check_schema(m)))


class SemanticTests(Fixture):
    def test_valid_manifest_passes(self):
        ok, problems = self.run_manifest(self.good())
        self.assertTrue(ok, problems)

    def test_artifact_hash_mismatch_fails(self):
        m = self.good()
        m["artifacts"][0]["sha256"] = "0" * 64
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)
        self.assertTrue(any("hash mismatch" in p for p in problems))

    def test_missing_artifact_fails(self):
        m = self.good()
        m["artifacts"][0]["path"] = "MISSING.md"
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)
        self.assertTrue(any("missing" in p.lower() for p in problems))

    def test_unknown_task_fails(self):
        m = self.good()
        m["authorized_task_id"] = "ANOX-TASK-OTHER-001"
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)

    def test_blocked_task_status_fails(self):
        (self.root / vse.TASKS_PATH).write_text(
            json.dumps(dict(TASK, status="Blocked")) + "\n")
        ok, problems = self.run_manifest(self.good())
        self.assertFalse(ok)

    def test_unknown_msc_unit_fails(self):
        m = self.good()
        m["covered_units"] = ["MSC-UNIT-042"]
        m["required_retests"][0]["unit"] = "MSC-UNIT-042"
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)
        self.assertTrue(any("unknown in msc_state" in p for p in problems))

    def test_ci_verdict_cannot_satisfy_e3(self):
        m = self.good()
        m["required_retests"] = [{"unit": "MSC-UNIT-001", "level": "E3",
                                  "binding": "ci_verdict",
                                  "satisfied_by": "ANOX-CIV-1", "status": "SATISFIED"}]
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)
        self.assertTrue(any("ci_verdict may not satisfy" in p for p in problems))

    def test_ci_verdict_satisfies_e2(self):
        m = self.good()
        m["required_retests"] = [{"unit": "MSC-UNIT-001", "level": "E2",
                                  "binding": "ci_verdict",
                                  "satisfied_by": "ANOX-CIV-1", "status": "SATISFIED"}]
        ok, problems = self.run_manifest(m)
        self.assertTrue(ok, problems)

    def test_satisfied_without_reference_fails(self):
        m = self.good()
        m["required_retests"][0]["satisfied_by"] = ""
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)

    def test_pending_retest_blocks_closure(self):
        m = self.good()
        m["required_retests"][0]["status"] = "PENDING"
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)
        self.assertTrue(any("not closable" in p for p in problems))

    def test_failed_retest_blocks_closure(self):
        m = self.good()
        m["required_retests"][0]["status"] = "FAILED"
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)
        self.assertTrue(any("FAILED" in p for p in problems))

    def test_non_civ_reference_for_ci_verdict_fails(self):
        m = self.good()
        m["required_retests"] = [{"unit": "MSC-UNIT-001", "level": "E2",
                                  "binding": "ci_verdict",
                                  "satisfied_by": "local-run", "status": "SATISFIED"}]
        ok, problems = self.run_manifest(m)
        self.assertFalse(ok)

    def test_malformed_json_fails(self):
        path = self.root / "session.json"
        path.write_text("{bad")
        ok, problems = vse.validate(path, self.root)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
