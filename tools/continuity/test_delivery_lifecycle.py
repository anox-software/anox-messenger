import json
import os
import subprocess
import unittest
from pathlib import Path

from test_handoff_and_validator import CMLFixture, REPO_ROOT
import validate_delivery_lifecycle as delivery


class DeliveryFixture(CMLFixture):
    def _run(self, cmd, **kw):
        if cmd[:2] == ["git", "config"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        kw.setdefault("env", dict(os.environ, GIT_AUTHOR_NAME="Fixture",
                                 GIT_AUTHOR_EMAIL="fixture@example.invalid",
                                 GIT_COMMITTER_NAME="Fixture",
                                 GIT_COMMITTER_EMAIL="fixture@example.invalid"))
        return super()._run(cmd, **kw)

    def __init__(self):
        super().__init__()
        self._run(["git", "update-ref", "refs/remotes/origin/main", self.base])
        self.task = {
            "task_id": "ANOX-TASK-FIXTURE", "branch": "delivery",
            "start_sha": self.base, "status": "Awaiting Review",
            "allowed_paths": ["docs/continuity/", "docs/workforce/", "PROJECT_STATE.md", "FORTSCHRITT.md"],
            "forbidden_paths": ["android/**"],
        }
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(self.task) + "\n")
        self._write("docs/workforce/WORKFORCE_STATE.json", json.dumps({
            "canonical_branch": "main", "delivery_branch": "delivery",
            "described_head": self.described,
            "current_gate": self.pre_merge_gate,
            "current_writer": {"task_id": self.task["task_id"], "role_id": "ROLE-009", "branch": "delivery"},
            "pre_merge_state": {"described_head": self.described, "current_gate": self.pre_merge_gate},
            "post_merge_state": {"described_head": self.described, "current_gate": self.post_merge_gate,
                                 "current_writer": None, "active_task": None},
        }))
        self.commit_meta("task metadata")

    def check(self, finalize=False):
        return delivery.validate(self.root, self.task["task_id"], finalize=finalize)

    def mutate_state(self, key, value):
        path = self.root / delivery.STATE_PATH
        state = json.loads(path.read_text())
        state[key] = value
        path.write_text(json.dumps(state))
        self.commit_meta("state mutation")


class DeliveryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = DeliveryFixture()
        self.addCleanup(self.fixture.cleanup)

    def test_valid_delivery_and_normal_synthetic_merge(self):
        result = self.fixture.check()
        self.assertEqual(result["PUSH_READINESS"], "READY", result)
        self.assertEqual(result["SYNTHETIC_POST_MERGE_VALIDATION"], "PASS")
        self.assertEqual(result["synthetic_parents"], [self.fixture.base, self.fixture.head("HEAD")])

    def test_invalid_described_head_lineage(self):
        self.fixture.mutate_state("described_head", "f" * 40)
        self.assertEqual(self.fixture.check()["PUSH_READINESS"], "BLOCKED")

    def test_wrong_delivery_branch(self):
        self.fixture.mutate_state("delivery_branch", "wrong")
        self.assertEqual(self.fixture.check()["PUSH_READINESS"], "BLOCKED")

    def test_unauthorized_path(self):
        self.fixture._write("android/feature.kt", "unauthorized\n")
        self.fixture.commit_meta("unauthorized payload")
        result = self.fixture.check()
        self.assertEqual(result["AUTHORIZED_SCOPE_ONLY"], "FAIL", result)

    def test_post_merge_validator_rejects_substantive_base_drift(self):
        self.fixture.checkout("main")
        self.fixture._write("docs/authority/NEW_POLICY.md", "substantive base drift\n")
        self.fixture.commit_meta("substantive canonical advance")
        self.fixture._run(["git", "update-ref", "refs/remotes/origin/main", self.fixture.head("main")])
        self.fixture.checkout("delivery")
        result = self.fixture.check()
        self.assertEqual(result["DELIVERY_BRANCH_VALIDATION"], "PASS", result)
        self.assertEqual(result["SYNTHETIC_POST_MERGE_VALIDATION"], "FAIL", result)
        self.assertIn("SUBSTANTIVE CANONICAL BASE DRIFT", result["reason"])

    def test_workforce_post_merge_gate_mismatch(self):
        path = self.fixture.root / delivery.WORKFORCE_PATH
        state = json.loads(path.read_text())
        state["post_merge_state"]["current_gate"] = "WRONG POST GATE"
        path.write_text(json.dumps(state))
        self.fixture.commit_meta("bad post merge metadata")
        self.assertEqual(self.fixture.check()["PUSH_READINESS"], "BLOCKED")

    def test_deterministic_metadata_correction_requires_commit_and_revalidation(self):
        self.fixture.mutate_state("current_gate", self.fixture.pre_merge_gate)
        self.assertEqual(self.fixture.check()["PUSH_READINESS"], "BLOCKED")
        result = self.fixture.check(finalize=True)
        self.assertEqual(result["PUSH_READINESS"], "BLOCKED", result)
        self.assertEqual(result["correction"], "APPLIED_COMMIT_AND_REVALIDATE", result)
        self.assertEqual(json.loads((self.fixture.root / delivery.STATE_PATH).read_text())["current_gate"],
                         "__EFFECTIVE_GATE__")
        self.fixture.commit_meta("seal deterministic correction")
        self.assertEqual(self.fixture.check()["PUSH_READINESS"], "READY")

    def test_scope_expansion_stops_without_correction(self):
        self.fixture.mutate_state("current_gate", self.fixture.pre_merge_gate)
        self.fixture._write("android/feature.kt", "scope expansion\n")
        self.fixture.commit_meta("scope expansion")
        before = (self.fixture.root / delivery.STATE_PATH).read_bytes()
        result = self.fixture.check(finalize=True)
        self.assertEqual(result["PUSH_READINESS"], "BLOCKED")
        self.assertEqual(before, (self.fixture.root / delivery.STATE_PATH).read_bytes())

    def test_simulation_does_not_mutate_source_repository(self):
        def snapshot():
            return [self.fixture._run(["git", *args]).stdout for args in (
                ["show-ref"], ["status", "--porcelain=v1", "--untracked-files=all"],
                ["rev-parse", "HEAD"], ["symbolic-ref", "HEAD"], ["reflog", "--all"],
                ["worktree", "list", "--porcelain"], ["remote", "-v"], ["ls-files", "--stage"],
            )]
        before = snapshot()
        self.assertEqual(self.fixture.check()["PUSH_READINESS"], "READY")
        self.assertEqual(before, snapshot())

    def test_dirty_source_fails_closed(self):
        self.fixture._write("untracked", "dirty")
        self.assertEqual(self.fixture.check()["WORKING_TREE"], "DIRTY")

    def test_missing_origin_main_fails_closed(self):
        self.fixture._run(["git", "update-ref", "-d", "refs/remotes/origin/main"])
        self.assertEqual(self.fixture.check()["PUSH_READINESS"], "BLOCKED")

    def test_merge_conflict_fails_closed(self):
        self.fixture.checkout("main")
        self.fixture._write("PROJECT_STATE.md", "conflicting canonical state\n")
        self.fixture.commit_meta("canonical metadata drift")
        self.fixture._run(["git", "update-ref", "refs/remotes/origin/main", self.fixture.head("main")])
        self.fixture.checkout("delivery")
        self.assertEqual(self.fixture.check()["SYNTHETIC_POST_MERGE_VALIDATION"], "FAIL")


class BootstrapDiscoveryTests(unittest.TestCase):
    def test_canonical_bootstrap_reference_chain(self):
        self.assertEqual(delivery.bootstrap_errors(REPO_ROOT), [])

    def test_removed_policy_link_is_detected(self):
        fixture = DeliveryFixture()
        self.addCleanup(fixture.cleanup)
        for rel in delivery.BOOTSTRAP_PATHS:
            fixture._write(rel, (REPO_ROOT / rel).read_text())
        self.assertEqual(delivery.bootstrap_errors(fixture.root), [])
        path = fixture.root / delivery.BOOTSTRAP_PATHS[0]
        path.write_text(path.read_text().replace(delivery.RULE_ANCHORS[0], "removed-rule"))
        self.assertTrue(delivery.bootstrap_errors(fixture.root))


if __name__ == "__main__":
    unittest.main()
