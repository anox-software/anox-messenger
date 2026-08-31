#!/usr/bin/env python3
"""Adversarial tests for the B027-A workforce foundation validator.

No network. All fixtures are synthetic and in-memory or temporary.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Import the validator under test.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "workforce"))

import validate_b027a as b027


def _copy_tree(src, dst):
    """Copy only files under src to dst, preserving structure."""
    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())


class B027AAdversarialTests(unittest.TestCase):
    """B027-A adversarial and positive tests."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="b027a_test_"))
        self.original_repo_root = b027.REPO_ROOT
        b027.REPO_ROOT = self.tmp
        b027.WORKFORCE_DIR = self.tmp / "docs" / "workforce"
        b027.SCHEMA_DIR = b027.WORKFORCE_DIR / "schemas"
        b027.REGISTRY_DIR = b027.WORKFORCE_DIR / "registries"
        b027.B027_AUTHORITY = self.tmp / "docs" / "authority" / "B027_AI_WORKFORCE_GOVERNANCE.md"
        b027.RUNTIME_CONTRACT = b027.WORKFORCE_DIR / "ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md"
        b027.MODEL_POLICY = b027.WORKFORCE_DIR / "MODEL_PROVIDER_POLICY.md"
        b027.ROLE_REGISTRY = b027.REGISTRY_DIR / "roles.json"
        b027.WORKFORCE_STATE = b027.WORKFORCE_DIR / "WORKFORCE_STATE.json"

    def tearDown(self):
        b027.REPO_ROOT = self.original_repo_root
        b027.WORKFORCE_DIR = b027.REPO_ROOT / "docs" / "workforce"
        b027.SCHEMA_DIR = b027.WORKFORCE_DIR / "schemas"
        b027.REGISTRY_DIR = b027.WORKFORCE_DIR / "registries"
        b027.B027_AUTHORITY = b027.REPO_ROOT / "docs" / "authority" / "B027_AI_WORKFORCE_GOVERNANCE.md"
        b027.RUNTIME_CONTRACT = b027.WORKFORCE_DIR / "ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md"
        b027.MODEL_POLICY = b027.WORKFORCE_DIR / "MODEL_PROVIDER_POLICY.md"
        b027.ROLE_REGISTRY = b027.REGISTRY_DIR / "roles.json"
        b027.WORKFORCE_STATE = b027.WORKFORCE_DIR / "WORKFORCE_STATE.json"
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, content, mode="text"):
        p = self.tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if mode == "text":
            p.write_text(content, encoding="utf-8")
        else:
            p.write_bytes(content)

    def _good_roles(self):
        roles = {
            "schema_version": "B027A-v1",
            "activation_classes": {
                "active": ["ROLE-001", "ROLE-002", "ROLE-003", "ROLE-004"],
                "gate_activated": ["ROLE-005", "ROLE-007", "ROLE-008", "ROLE-009", "ROLE-010"],
                "dormant": ["ROLE-006", "ROLE-011", "ROLE-012", "ROLE-013", "ROLE-014", "ROLE-015", "ROLE-016", "ROLE-017", "ROLE-018", "ROLE-019"],
            },
            "roles": [
                {"role_id": f"ROLE-{i:03d}", "title": f"Role {i}", "authority": "authority", "ai_allowed": True, "activation_class": "active" if i <= 4 else "gate_activated" if i in (5,7,8,9,10) else "dormant"}
                for i in range(1, 20)
            ],
        }
        # Fix human-only roles
        roles["roles"][0]["ai_allowed"] = False
        roles["roles"][17]["ai_allowed"] = False
        return roles

    def _good_task(self, overrides=None):
        tp = {
            "task_id": "ANOX-TASK-TEST001",
            "title": "Test task",
            "role_id": "ROLE-004",
            "start_sha": "a" * 40,
            "branch": "governance/test",
            "allowed_paths": ["docs/workforce/"],
            "forbidden_paths": ["android/"],
            "scope": "test scope",
            "non_goals": ["product changes"],
            "security_class": "S2",
            "data_egress": "D2",
            "priority": "P2",
            "required_evidence": "E3",
            "reviewer_role": "ROLE-007",
            "remote_permission": "NONE",
            "stop_conditions": ["validator passes"],
            "authority_refs": ["docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md"],
            "created_at": "2026-08-31",
            "status": "In Progress",
        }
        if overrides:
            tp.update(overrides)
        return tp

    def _good_state(self, overrides=None):
        state = {
            "schema_version": "B027A-v1",
            "authority_version": "docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md",
            "current_gate": "TEST",
            "active_roles": ["ROLE-001", "ROLE-002", "ROLE-003", "ROLE-004"],
            "blocked_tasks": [],
            "authorized_tasks": ["ANOX-TASK-TEST001"],
            "current_writer": {
                "task_id": "ANOX-TASK-TEST001",
                "role_id": "ROLE-004",
                "branch": "governance/test",
            },
            "pending_human_remote_actions": [],
            "latest_decision_id": None,
            "latest_finding_id": None,
            "latest_run_id": None,
            "latest_work_candidate_id": None,
        }
        if overrides:
            state.update(overrides)
        return state

    def _install_good_foundation(self):
        self._write("docs/authority/AUTHORITY_INDEX.md", "# Authority Index\n## Precedence\n1. `B025/SECURITY_INVARIANTS_V1_1.md`\n9. `B027_AI_WORKFORCE_GOVERNANCE.md`\n")
        self._write("docs/authority/B025/SECURITY_INVARIANTS_V1_1.md", "# Invariants\n")
        self._write("docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md", "# B026\n")
        self._write("docs/authority/B_FREEZE_REGISTRY.md", "# Freeze\n")
        self._write("docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md", "# Arch\n")
        self._write("docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md", "# B027\n## FROZEN ARCHITECTURE\n## IMPLEMENTED IN B027-A\n## DEFERRED TO B027-B\n`docs/authority/AUTHORITY_INDEX.md`\n")
        self._write("docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md", "# Contract\n")
        self._write("docs/workforce/MODEL_PROVIDER_POLICY.md", "# Policy\n")
        self._write("docs/workforce/schemas/task-package.schema.json", json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "required": ["task_id"], "properties": {"task_id": {"type": "string"}}}))
        self._write("docs/workforce/schemas/finding.schema.json", json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}))
        self._write("docs/workforce/schemas/decision.schema.json", json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}))
        self._write("docs/workforce/schemas/run.schema.json", json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}))
        self._write("docs/workforce/schemas/derived-work.schema.json", json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}))
        self._write("docs/workforce/schemas/workforce-state.schema.json", json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}))
        self._write("docs/workforce/registries/roles.json", json.dumps(self._good_roles()))
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(self._good_task()))
        self._write("docs/workforce/registries/findings.jsonl", "")
        self._write("docs/workforce/registries/decisions.jsonl", "")
        self._write("docs/workforce/registries/runs.jsonl", "")
        self._write("docs/workforce/registries/derived_work.jsonl", "")
        self._write("docs/workforce/WORKFORCE_STATE.json", json.dumps(self._good_state()))

    def _run_validator(self):
        return b027.validate_b027a()

    # ---- Positive ----

    def test_valid_foundation_passes(self):
        """20. valid foundation fixture -> PASS."""
        self._install_good_foundation()
        self.assertEqual(self._run_validator(), 0)

    # ---- Required files / Authority ----

    def test_missing_b027_authority_fails(self):
        """1. missing B027 Authority -> FAIL."""
        self._install_good_foundation()
        (self.tmp / "docs" / "authority" / "B027_AI_WORKFORCE_GOVERNANCE.md").unlink()
        self.assertEqual(self._run_validator(), 1)

    # ---- Task Package ----

    def test_malformed_task_package_fails(self):
        """2. malformed Task Package -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task()
        bad.pop("start_sha")
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    def test_unknown_role_fails(self):
        """3. unknown role -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task({"role_id": "ROLE-999"})
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    def test_duplicate_role_fails(self):
        """4. duplicate role -> FAIL."""
        self._install_good_foundation()
        data = self._good_roles()
        data["roles"][0]["role_id"] = "ROLE-002"
        self._write("docs/workforce/registries/roles.json", json.dumps(data))
        self.assertEqual(self._run_validator(), 1)

    def test_role_model_conflation_fails(self):
        """5. role/model conflation attempt -> FAIL."""
        self._install_good_foundation()
        data = self._good_roles()
        data["roles"][0]["title"] = "Devin Product Owner"
        self._write("docs/workforce/registries/roles.json", json.dumps(data))
        self.assertEqual(self._run_validator(), 1)

    def test_d4_assignment_to_ai_fails(self):
        """6. D4 assignment to AI role -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task({"data_egress": "D4"})
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    def test_ai_remote_write_fails(self):
        """7. AI remote write permission -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task({"remote_permission": "AI_WRITE"})
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    def test_two_writers_same_branch_fails(self):
        """8. two writers same branch -> FAIL."""
        self._install_good_foundation()
        tp1 = self._good_task()
        tp2 = self._good_task({
            "task_id": "ANOX-TASK-TEST002",
            "role_id": "ROLE-003",
            "reviewer_role": "ROLE-007",
        })
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(tp1) + "\n" + json.dumps(tp2))
        state = self._good_state({
            "authorized_tasks": ["ANOX-TASK-TEST001", "ANOX-TASK-TEST002"],
            "current_writer": {"task_id": "ANOX-TASK-TEST002", "role_id": "ROLE-003", "branch": "governance/test"},
        })
        self._write("docs/workforce/WORKFORCE_STATE.json", json.dumps(state))
        self.assertEqual(self._run_validator(), 1)

    def test_reviewer_equals_writer_fails(self):
        """9. reviewer == writer where independence required -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task({"reviewer_role": "ROLE-004"})
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    # ---- Enums ----

    def test_unknown_evidence_level_fails(self):
        """10. unknown Evidence level -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task({"required_evidence": "E5"})
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    def test_unknown_egress_level_fails(self):
        """11. unknown Egress level -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task({"data_egress": "D5"})
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    def test_unknown_priority_fails(self):
        """12. unknown Priority -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task({"priority": "P4"})
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    # ---- Stable IDs ----

    def test_malformed_stable_id_fails(self):
        """13. malformed stable ID -> FAIL."""
        self._install_good_foundation()
        bad = self._good_task({"task_id": "TASK-001"})
        self._write("docs/workforce/registries/tasks.jsonl", json.dumps(bad))
        self.assertEqual(self._run_validator(), 1)

    def test_reused_stable_id_fails(self):
        """14. reused stable ID -> FAIL."""
        self._install_good_foundation()
        line = json.dumps(self._good_task())
        self._write("docs/workforce/registries/tasks.jsonl", line + "\n" + line)
        self.assertEqual(self._run_validator(), 1)

    # ---- Findings ----

    def test_finding_disappears_fails(self):
        """15. finding disappears / destructive rewrite fixture -> FAIL where deterministic."""
        self._install_good_foundation()
        f1 = {
            "finding_id": "ANOX-FINDING-TEST001",
            "title": "Original finding",
            "severity": "HIGH",
            "status": "Closed",
            "discovered_by": "AI",
            "discovered_in_run": "ANOX-RUN-TEST001",
            "affected_scope": "scope",
            "evidence_refs": ["ev1"],
            "closure_actor": "human",
            "closure_evidence": ["retest"],
        }
        # destructive rewrite: same id, different title/status without superseded link
        f2 = {
            "finding_id": "ANOX-FINDING-TEST001",
            "title": "Rewritten finding",
            "severity": "LOW",
            "status": "Closed",
            "discovered_by": "AI",
            "discovered_in_run": "ANOX-RUN-TEST001",
            "affected_scope": "scope",
            "evidence_refs": ["ev1"],
            "closure_actor": "human",
            "closure_evidence": ["retest"],
        }
        self._write("docs/workforce/registries/findings.jsonl", json.dumps(f1) + "\n" + json.dumps(f2))
        self.assertEqual(self._run_validator(), 1)

    def test_severity_downgrade_without_rationale_fails(self):
        """16. severity downgrade without rationale -> FAIL."""
        self._install_good_foundation()
        f = {
            "finding_id": "ANOX-FINDING-TEST001",
            "title": "Finding",
            "severity": "LOW",
            "status": "Triaged",
            "discovered_by": "AI",
            "discovered_in_run": "ANOX-RUN-TEST001",
            "affected_scope": "scope",
            "evidence_refs": ["ev1"],
            "rationale_severity_downgrade": "",
        }
        self._write("docs/workforce/registries/findings.jsonl", json.dumps(f))
        self.assertEqual(self._run_validator(), 1)

    def test_closed_finding_without_closure_evidence_fails(self):
        """17. Closed finding without closure evidence -> FAIL."""
        self._install_good_foundation()
        f = {
            "finding_id": "ANOX-FINDING-TEST001",
            "title": "Finding",
            "severity": "HIGH",
            "status": "Closed",
            "discovered_by": "AI",
            "discovered_in_run": "ANOX-RUN-TEST001",
            "affected_scope": "scope",
            "evidence_refs": ["ev1"],
            "closure_actor": "human",
        }
        self._write("docs/workforce/registries/findings.jsonl", json.dumps(f))
        self.assertEqual(self._run_validator(), 1)

    # ---- Derived Work ----

    def test_derived_work_authorized_directly_fails(self):
        """18. Derived Work marked Authorized directly -> FAIL."""
        self._install_good_foundation()
        dw = {
            "work_candidate_id": "ANOX-WORK-TEST001",
            "title": "Candidate",
            "suggested_by": "AI",
            "source_run": "ANOX-RUN-TEST001",
            "authorization_status": "Authorized",
            "rationale": "rationale",
            "created_at": "2026-08-31T00:00:00Z",
        }
        self._write("docs/workforce/registries/derived_work.jsonl", json.dumps(dw))
        self.assertEqual(self._run_validator(), 1)

    # ---- Workforce State ----

    def test_workforce_state_unknown_task_fails(self):
        """19. WORKFORCE_STATE references unknown task -> FAIL."""
        self._install_good_foundation()
        state = self._good_state({"authorized_tasks": ["ANOX-TASK-UNKNOWN"]})
        self._write("docs/workforce/WORKFORCE_STATE.json", json.dumps(state))
        self.assertEqual(self._run_validator(), 1)


if __name__ == "__main__":
    unittest.main()
