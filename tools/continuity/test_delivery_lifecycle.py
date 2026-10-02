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


class ResyncDeliveryFixture(DeliveryFixture):
    """Delivery branched from canonical AFTER a post-start_sha authority merge.

    Mirrors the B026 controlled-resynchronization shape: task.start_sha anchors
    the authorized lineage; the Human-authorized Task/Decision records are then
    merged into canonical (authority_base); the delivery forks from that head.
    With post_authority=False the delivery forks from the pre-authority base
    instead and must mint its own registry record (the C-01 pattern).
    """

    def __init__(self, post_authority=True):
        super(DeliveryFixture, self).__init__()
        self.checkout("main")
        self.task = {
            "task_id": "ANOX-TASK-RESYNC-FIXTURE", "branch": "delivery",
            "start_sha": self.base, "status": "Awaiting Review",
            "allowed_paths": [
                "docs/continuity/", "docs/workforce/WORKFORCE_STATE.json",
                "tools/audit/", "crypto/rust/", "PROJECT_STATE.md", "FORTSCHRITT.md",
            ],
            "forbidden_paths": [
                "docs/workforce/registries/tasks.jsonl",
                "docs/workforce/registries/decisions.jsonl",
                "android/**",
            ],
        }
        decision = {
            "decision_id": "ANOX-DECISION-RESYNC-FIXTURE",
            "ratified_task": self.task["task_id"],
            "authority_actor": "Human Product & Security Owner",
        }
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(self.task) + "\n")
        self._write("docs/workforce/registries/decisions.jsonl", json.dumps(decision) + "\n")
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", "canonical authority merge"])
        self.authority_base = self.head("main")
        self._run(["git", "update-ref", "refs/remotes/origin/main", self.authority_base])

        fork = self.authority_base if post_authority else self.base
        self._run(["git", "checkout", "-B", "delivery", fork])
        self._write("docs/continuity/CML_SUBSTANTIVE.md", "# Canonical merge lifecycle\n")
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", "delivery substantive payload"])
        self.described = self.head("delivery")
        self._write_state()
        self._write_git_state_md()
        self._write_handoff_md()
        self._write_project_state_md("delivery")
        self._write("docs/workforce/WORKFORCE_STATE.json", json.dumps({
            "canonical_branch": "main", "delivery_branch": "delivery",
            "described_head": self.described,
            "current_gate": self.pre_merge_gate,
            "current_writer": {"task_id": self.task["task_id"], "role_id": "ROLE-004",
                               "branch": "delivery"},
            "pre_merge_state": {"described_head": self.described, "current_gate": self.pre_merge_gate},
            "post_merge_state": {"described_head": self.described, "current_gate": self.post_merge_gate,
                                 "current_writer": None, "active_task": None},
        }))
        if not post_authority:
            # No canonical authority on this line: the delivery mints its own
            # task record — a forbidden registry write that must be caught.
            self._write("docs/workforce/registries/tasks.jsonl", json.dumps(self.task) + "\n")
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", "delivery state sync"])
        self.delivery_head = self.head("delivery")

    def mutate_registry(self, rel):
        path = self.root / rel
        path.write_text(path.read_text(encoding="utf-8")
                        + json.dumps({"forged": True}) + "\n", encoding="utf-8")
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", f"delivery writes {rel}"])


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


class ResyncAuthorityScopeTests(unittest.TestCase):
    """Scope is measured from the delivery fork point, not task.start_sha."""

    def setUp(self):
        self.fixture = ResyncDeliveryFixture()
        self.addCleanup(self.fixture.cleanup)

    def test_canonical_pre_delivery_authority_not_delivery_mutation(self):
        result = self.fixture.check()
        self.assertEqual(result["delivery_scope_base"], self.fixture.authority_base)
        self.assertEqual(result["AUTHORIZED_SCOPE_ONLY"], "PASS", result)
        self.assertEqual(result["PUSH_READINESS"], "READY", result)

    def test_delivery_tasks_registry_mutation_fails(self):
        self.fixture.mutate_registry("docs/workforce/registries/tasks.jsonl")
        result = self.fixture.check()
        self.assertEqual(result["AUTHORIZED_SCOPE_ONLY"], "FAIL", result)

    def test_delivery_decisions_registry_mutation_fails(self):
        self.fixture.mutate_registry("docs/workforce/registries/decisions.jsonl")
        result = self.fixture.check()
        self.assertEqual(result["AUTHORIZED_SCOPE_ONLY"], "FAIL", result)

    def test_allowed_payload_change_after_branch_point_passes(self):
        self.fixture._write("tools/audit/resync_tool.py", "# authorized tooling\n")
        self.fixture._run(["git", "add", "."])
        self.fixture._run(["git", "commit", "-m", "allowed tooling payload"])
        result = self.fixture.check()
        self.assertEqual(result["AUTHORIZED_SCOPE_ONLY"], "PASS", result)

    def test_start_sha_must_anchor_lineage(self):
        empty_tree = self.fixture._run(["git", "mktree"], input="").stdout.strip()
        orphan = self.fixture._run(
            ["git", "commit-tree", empty_tree, "-m", "unrelated root"]).stdout.strip()
        path = self.fixture.root / delivery.TASKS_PATH
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        records[0]["start_sha"] = orphan
        path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
        self.fixture._run(["git", "add", "."])
        self.fixture._run(["git", "commit", "-m", "rebind start sha"])
        result = self.fixture.check()
        self.assertEqual(result["PUSH_READINESS"], "BLOCKED", result)
        self.assertIn("merge-base", result["reason"])

    def test_delivery_minted_authority_still_fails(self):
        # Canonical-drift protection: a delivery forked BEFORE the authority
        # merge cannot mint its own Task authority — the registry write remains
        # inside its true scope base and stays forbidden.
        stale = ResyncDeliveryFixture(post_authority=False)
        self.addCleanup(stale.cleanup)
        result = stale.check()
        self.assertEqual(result["AUTHORIZED_SCOPE_ONLY"], "FAIL", result)
        self.assertIn("tasks.jsonl", result["reason"])


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
