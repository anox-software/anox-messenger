#!/usr/bin/env python3
"""Adversarial tests for B-028 next_step.py — deterministic resolution."""

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import next_step


def task(tid, status="Authorized", branch="governance/x-001"):
    return {"task_id": tid, "role_id": "ROLE-003", "branch": branch,
            "start_sha": "a" * 40, "allowed_paths": ["docs/**"],
            "status": status, "security_class": "S2", "data_egress": "D2",
            "required_evidence": "E3", "remote_permission": "NONE"}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs/workforce/registries").mkdir(parents=True)
        (self.root / "docs/continuity").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, tasks, state):
        (self.root / next_step.TASKS_PATH).write_text(
            "".join(json.dumps(t) + "\n" for t in tasks))
        (self.root / next_step.STATE_PATH).write_text(json.dumps(state))


class ResolveTests(Fixture):
    def test_current_writer_resolves_bundle(self):
        t = task("ANOX-TASK-X-001")
        self.write([t], {"current_writer": {"task_id": "ANOX-TASK-X-001",
                                            "branch": "governance/x-001"},
                         "authorized_tasks": ["ANOX-TASK-X-001"]})
        r = next_step.resolve(self.root)
        self.assertEqual(r["status"], "AUTHORIZED_NEXT_STEP")
        self.assertEqual(r["task_id"], "ANOX-TASK-X-001")
        self.assertEqual(r["baseline_sha"], "a" * 40)

    def test_single_authorized_task_resolves(self):
        t = task("ANOX-TASK-X-001")
        self.write([t], {"current_writer": None,
                         "authorized_tasks": ["ANOX-TASK-X-001"]})
        r = next_step.resolve(self.root)
        self.assertEqual(r["status"], "AUTHORIZED_NEXT_STEP")

    def test_writer_branch_mismatch_blocked(self):
        t = task("ANOX-TASK-X-001")
        self.write([t], {"current_writer": {"task_id": "ANOX-TASK-X-001",
                                            "branch": "other/branch"}})
        r = next_step.resolve(self.root)
        self.assertEqual(r["status"], "BLOCKED")

    def test_writer_task_missing_from_registry_blocked(self):
        self.write([], {"current_writer": {"task_id": "ANOX-TASK-X-001",
                                           "branch": "b"}})
        r = next_step.resolve(self.root)
        self.assertEqual(r["status"], "BLOCKED")

    def test_multiple_authorized_tasks_blocked(self):
        self.write([task("ANOX-TASK-A-001"), task("ANOX-TASK-B-001")],
                   {"current_writer": None,
                    "authorized_tasks": ["ANOX-TASK-A-001", "ANOX-TASK-B-001"]})
        r = next_step.resolve(self.root)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertTrue(any("one-writer" in p for p in r["problems"]))

    def test_no_authorized_returns_candidates(self):
        self.write([task("ANOX-TASK-C-001", status="Candidate")],
                   {"current_writer": None, "authorized_tasks": []})
        r = next_step.resolve(self.root)
        self.assertEqual(r["status"], "NO_AUTHORIZED_NEXT_STEP")
        self.assertIn("ANOX-TASK-C-001", r["candidates"])

    def test_duplicate_task_id_blocked(self):
        self.write([task("ANOX-TASK-X-001"), task("ANOX-TASK-X-001")],
                   {"current_writer": None})
        r = next_step.resolve(self.root)
        self.assertEqual(r["status"], "BLOCKED")

    def test_merged_task_not_resolvable(self):
        self.write([task("ANOX-TASK-X-001", status="Merged")],
                   {"current_writer": None,
                    "authorized_tasks": ["ANOX-TASK-X-001"]})
        r = next_step.resolve(self.root)
        self.assertEqual(r["status"], "NO_AUTHORIZED_NEXT_STEP")


if __name__ == "__main__":
    unittest.main()
