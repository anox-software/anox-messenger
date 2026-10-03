#!/usr/bin/env python3
"""Adversarial tests for B-028 ingest_ci_verdict.py — spoofing resistance."""

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest_ci_verdict as icv


def verdict(**kw):
    v = {
        "verdict_id": "ANOX-CIV-0001",
        "commit_sha": "a" * 40,
        "run_id": "36275286174",
        "workflow": "ci.yml",
        "job": "instrumented-x86_64",
        "map_version": "TM-v1",
        "result": "PASS",
        "units": ["MSC-UNIT-001"],
        "created_at": "2026-10-02",
    }
    v.update(kw)
    return v


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs/workforce/registries").mkdir(parents=True)
        (self.root / icv.TEST_MAP_PATH).write_text(
            json.dumps({"map_version": "TM-v1", "unit": "MSC-UNIT-001",
                        "test_refs": ["tools/audit/t.py"], "ci_jobs": ["instrumented-x86_64"]}) + "\n")
        (self.root / icv.REGISTRY_PATH).write_text("")

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, v, seen=None):
        return icv.check_record(v, self.root, seen or set())


class RecordTests(Fixture):
    def test_valid_verdict_passes(self):
        self.assertEqual(self.check(verdict()), [])

    def test_missing_field_fails(self):
        v = verdict()
        del v["run_id"]
        self.assertTrue(any("missing" in p for p in self.check(v)))

    def test_unknown_field_fails(self):
        v = verdict(extra="x")
        self.assertTrue(any("unknown fields" in p for p in self.check(v)))

    def test_non_canonical_sha_fails(self):
        self.assertTrue(any("commit_sha" in p for p in self.check(verdict(commit_sha="abc123"))))

    def test_non_numeric_run_id_fails(self):
        self.assertTrue(any("run_id" in p for p in self.check(verdict(run_id="local"))))

    def test_local_job_marker_fails(self):
        self.assertTrue(any("local evidence" in p for p in self.check(verdict(job="local"))))

    def test_local_workflow_marker_fails(self):
        self.assertTrue(any("local evidence" in p for p in self.check(verdict(workflow="manual"))))

    def test_stale_map_version_fails(self):
        self.assertTrue(any("map_version" in p for p in self.check(verdict(map_version="TM-v0"))))

    def test_unmapped_unit_fails(self):
        self.assertTrue(any("test_map binding" in p for p in self.check(verdict(units=["MSC-UNIT-099"]))))

    def test_duplicate_id_fails(self):
        self.assertTrue(any("duplicate" in p for p in self.check(verdict(), {"ANOX-CIV-0001"})))

    def test_bad_result_fails(self):
        self.assertTrue(any("result" in p for p in self.check(verdict(result="GREEN"))))

    def test_empty_units_fails(self):
        self.assertTrue(any("non-empty" in p for p in self.check(verdict(units=[]))))


class RegistryTests(Fixture):
    def test_verify_empty_registry_passes(self):
        ok, problems = icv.verify_registry(self.root)
        self.assertTrue(ok, problems)

    def test_ingest_then_verify(self):
        path = self.root / "v.json"
        path.write_text(json.dumps(verdict()))
        rec, problems = icv.ingest(path, self.root)
        self.assertEqual(problems, [])
        ok, problems = icv.verify_registry(self.root)
        self.assertTrue(ok, problems)

    def test_double_ingest_rejected(self):
        path = self.root / "v.json"
        path.write_text(json.dumps(verdict()))
        icv.ingest(path, self.root)
        rec, problems = icv.ingest(path, self.root)
        self.assertIsNone(rec)
        self.assertTrue(any("duplicate" in p for p in problems))

    def test_spoofed_verdict_rejected(self):
        path = self.root / "v.json"
        path.write_text(json.dumps(verdict(run_id="1", job="local")))
        rec, problems = icv.ingest(path, self.root)
        self.assertIsNone(rec)


if __name__ == "__main__":
    unittest.main()
