#!/usr/bin/env python3
"""B027-B workforce runtime and validator.

Imports state_gate_resolver as a library, runs the B027-A validator, checks
role contracts and new schemas/registries, and executes 48 adversarial unit
tests against the resolver.
"""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import state_gate_resolver as sgr

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFORCE_DIR = REPO_ROOT / "docs" / "workforce"
ROLES_DIR = WORKFORCE_DIR / "roles"
SCHEMA_DIR = WORKFORCE_DIR / "schemas"
REGISTRY_DIR = WORKFORCE_DIR / "registries"
B027A_VALIDATOR = REPO_ROOT / "tools" / "workforce" / "validate_b027a.py"

REQUIRED_HEADINGS = [
    "Mission", "Authority", "Allowed responsibilities", "Prohibited responsibilities",
    "Writable/read-only", "Required inputs", "Required outputs", "Escalation path",
    "Evidence expectations", "Independence requirements", "Data-egress ceiling",
    "Remote permission ceiling", "Activation class", "Security-trigger participation",
]


def fail(msg, errors):
    errors.append(msg)


def run_b027a_validator(errors):
    if not B027A_VALIDATOR.exists():
        fail("B027-A validator missing", errors)
        return
    result = subprocess.run(
        [sys.executable, str(B027A_VALIDATOR)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail("B027-A validator failed", errors)
        if result.stdout:
            fail(result.stdout.strip(), errors)
        if result.stderr:
            fail(result.stderr.strip(), errors)


def validate_role_contracts(errors):
    for i in range(1, 20):
        rid = f"ROLE-{i:03d}"
        p = ROLES_DIR / f"{rid}.md"
        if not p.exists():
            fail(f"role contract {p.name} missing", errors)
            continue
        text = p.read_text(encoding="utf-8")
        for h in REQUIRED_HEADINGS:
            pattern = (
                r"^\s*(?:#{1,3}\s+)?\*\*" + re.escape(h) +
                r"(?:\s+[\w/-]+)?\s*:\*\*"
            )
            if not re.search(pattern, text, re.M):
                fail(f"{p.name} missing heading: {h}", errors)


def validate_schemas_b027b(errors):
    for name in ("prompt.schema.json", "communication.schema.json"):
        p = SCHEMA_DIR / name
        if not p.exists():
            fail(f"schema {name} missing", errors)
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                fail(f"schema {name} is not a JSON object", errors)
            elif data.get("$schema") is None:
                fail(f"schema {name} missing $schema", errors)
        except json.JSONDecodeError as e:
            fail(f"schema {name} invalid JSON: {e}", errors)


def validate_registries_b027b(errors):
    for name in ("prompts.jsonl", "communications.jsonl"):
        p = REGISTRY_DIR / name
        if not p.exists():
            fail(f"registry {name} missing", errors)
            continue
        with open(p, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    fail(f"{name} invalid JSON at line {i}: {e}", errors)


def validate_b027b_structural():
    errors = []
    print("[B027-B] Running B027-A validator", flush=True)
    run_b027a_validator(errors)
    print("[B027-B] Role contracts", flush=True)
    validate_role_contracts(errors)
    print("[B027-B] Schemas", flush=True)
    validate_schemas_b027b(errors)
    print("[B027-B] Registries", flush=True)
    validate_registries_b027b(errors)
    if errors:
        for e in errors:
            print(f"  FAIL {e}", flush=True)
        return 1
    print("[B027-B] Structural checks PASSED", flush=True)
    return 0


class B027BResolverTests(unittest.TestCase):
    """48 adversarial and positive resolver tests."""

    def setUp(self):
        self.roles = sgr.load_roles()
        self.sha = "38b619e55082086989bb0713cad42c4c53be14ab"
        self.state = {"current_sha": self.sha, "tasks": []}

    def _task(self, **overrides):
        t = {
            "task_id": "ANOX-TASK-TEST001",
            "title": "Test task",
            "role_id": "ROLE-004",
            "start_sha": self.sha,
            "branch": "governance/test",
            "allowed_paths": ["docs/workforce/", "tools/workforce/"],
            "forbidden_paths": ["android/**", "crypto/rust/**", ".github/workflows/**"],
            "scope": "test scope",
            "non_goals": ["product changes"],
            "security_class": "S2",
            "data_egress": "D2",
            "priority": "P1",
            "required_evidence": "E3",
            "reviewer_role": "ROLE-002",
            "remote_permission": "NONE",
            "stop_conditions": ["validator passes"],
            "authority_refs": ["docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md"],
            "created_at": "2026-08-31",
            "status": "Candidate",
        }
        t.update(overrides)
        return t

    def _state(self, tasks=None, current_sha=None):
        return {
            "current_sha": current_sha or self.sha,
            "tasks": tasks or [],
        }

    def _resolve(self, current, requested, actor, task=None, state=None):
        if task is None:
            task = self._task()
        if state is None:
            state = self._state()
        return sgr.resolve_transition(current, requested, actor, task, state, self.roles)

    # ---- Lifecycle transitions ----

    def test_01_candidate_to_authorized_human(self):
        r = self._resolve("Candidate", "Authorized", "ROLE-001")
        self.assertEqual(r["result"], "ALLOWED")
        self.assertEqual(r["next_state"], "Authorized")

    def test_02_candidate_to_authorized_resolver(self):
        r = self._resolve("Candidate", "Authorized", "ROLE-003")
        self.assertEqual(r["result"], "ALLOWED")

    def test_03_candidate_to_authorized_ai_blocked(self):
        r = self._resolve("Candidate", "Authorized", "ROLE-004")
        self.assertEqual(r["result"], "BLOCKED")

    def test_04_candidate_to_authorized_missing_fields_blocked(self):
        task = self._task(allowed_paths=[])
        r = self._resolve("Candidate", "Authorized", "ROLE-001", task=task)
        self.assertEqual(r["result"], "BLOCKED")

    def test_05_authorized_to_in_progress(self):
        r = self._resolve("Authorized", "In Progress", "ROLE-004")
        self.assertEqual(r["result"], "ALLOWED")
        self.assertEqual(r["next_state"], "In Progress")

    def test_06_in_progress_to_awaiting_evidence(self):
        r = self._resolve("In Progress", "Awaiting Evidence", "ROLE-004")
        self.assertEqual(r["result"], "ALLOWED")

    def test_07_awaiting_evidence_to_awaiting_review(self):
        r = self._resolve("Awaiting Evidence", "Awaiting Review", "ROLE-004")
        self.assertEqual(r["result"], "ALLOWED")

    def test_08_awaiting_review_to_ready_for_remote(self):
        r = self._resolve("Awaiting Review", "Ready For Remote", "ROLE-002")
        self.assertEqual(r["result"], "ALLOWED")

    def test_09_awaiting_review_to_blocked(self):
        r = self._resolve("Awaiting Review", "Blocked", "ROLE-002")
        self.assertEqual(r["result"], "ALLOWED")

    def test_10_ready_for_remote_to_awaiting_human_remote(self):
        r = self._resolve("Ready For Remote", "Awaiting Human Remote Action", "ROLE-004")
        self.assertEqual(r["result"], "ALLOWED")

    def test_11_awaiting_human_to_ci_pending_human(self):
        r = self._resolve("Awaiting Human Remote Action", "CI Pending", "ROLE-001")
        self.assertEqual(r["result"], "ALLOWED")

    def test_12_awaiting_human_to_ci_pending_ai_blocked(self):
        r = self._resolve("Awaiting Human Remote Action", "CI Pending", "ROLE-004")
        self.assertEqual(r["result"], "BLOCKED")

    def test_13_ci_pending_to_ready_to_merge(self):
        current = {"state": "CI Pending", "ci_result": "pass"}
        r = self._resolve(current, "Ready To Merge", "ROLE-002")
        self.assertEqual(r["result"], "ALLOWED")

    def test_14_ci_pending_to_blocked(self):
        current = {"state": "CI Pending", "ci_result": "fail"}
        r = self._resolve(current, "Blocked", "ROLE-002")
        self.assertEqual(r["result"], "ALLOWED")

    def test_15_ready_to_merge_to_merged_human(self):
        r = self._resolve("Ready To Merge", "Merged", "ROLE-001")
        self.assertEqual(r["result"], "ALLOWED")

    def test_16_ready_to_merge_to_merged_ai_blocked(self):
        r = self._resolve("Ready To Merge", "Merged", "ROLE-004")
        self.assertEqual(r["result"], "BLOCKED")

    def test_17_merged_to_closed(self):
        r = self._resolve("Merged", "Closed", "ROLE-004")
        self.assertEqual(r["result"], "ALLOWED")

    def test_18_any_to_blocked(self):
        r = self._resolve("In Progress", "Blocked", "ROLE-004")
        self.assertEqual(r["result"], "ALLOWED")

    def test_19_blocked_to_candidate_human(self):
        r = self._resolve("Blocked", "Candidate", "ROLE-001")
        self.assertEqual(r["result"], "ALLOWED")

    def test_20_blocked_to_candidate_resolver_blocked(self):
        r = self._resolve("Blocked", "Candidate", "ROLE-003")
        self.assertEqual(r["result"], "BLOCKED")

    def test_21_invalid_transition_blocked(self):
        r = self._resolve("In Progress", "Merged", "ROLE-001")
        self.assertEqual(r["result"], "BLOCKED")

    # ---- Task authorization / paths / writers / egress / human boundary ----

    def test_22_authorize_task_valid_t2(self):
        task = self._task(role_id="ROLE-003", status="Candidate")
        r = sgr.authorize_task(task, self.state, self.roles)
        self.assertEqual(r["result"], "ALLOWED")

    def test_23_authorize_task_unknown_role(self):
        task = self._task(role_id="ROLE-999")
        r = sgr.authorize_task(task, self.state, self.roles)
        self.assertEqual(r["result"], "BLOCKED")

    def test_24_authorize_task_dormant_role(self):
        task = self._task(role_id="ROLE-006")
        r = sgr.authorize_task(task, self.state, self.roles)
        self.assertEqual(r["result"], "BLOCKED")

    def test_25_authorize_task_start_sha_mismatch(self):
        state = self._state(current_sha="a" * 40)
        r = sgr.authorize_task(self._task(), state, self.roles)
        self.assertEqual(r["result"], "BLOCKED")

    def test_26_check_path_enforcement_allowed(self):
        paths = ["docs/workforce/WORKFORCE_STATE.json", "tools/workforce/validate_b027b.py"]
        r = sgr.check_path_enforcement(paths, self._task())
        self.assertEqual(r["result"], "ALLOWED")

    def test_27_check_path_enforcement_forbidden(self):
        paths = ["android/src/MainActivity.kt"]
        r = sgr.check_path_enforcement(paths, self._task())
        self.assertEqual(r["result"], "BLOCKED")

    def test_28_check_path_enforcement_outside_allowed(self):
        paths = ["backend/server.py"]
        r = sgr.check_path_enforcement(paths, self._task())
        self.assertEqual(r["result"], "BLOCKED")

    def test_29_check_one_active_writer_pass(self):
        state = self._state(tasks=[{
            "task_id": "ANOX-TASK-OTHER",
            "role_id": "ROLE-004",
            "branch": "governance/other",
            "status": "In Progress",
        }])
        r = sgr.check_one_active_writer(self._task(), state)
        self.assertEqual(r["result"], "ALLOWED")

    def test_30_check_one_active_writer_duplicate_blocked(self):
        state = self._state(tasks=[{
            "task_id": "ANOX-TASK-OTHER",
            "role_id": "ROLE-004",
            "branch": "governance/test",
            "status": "In Progress",
        }])
        r = sgr.check_one_active_writer(self._task(), state)
        self.assertEqual(r["result"], "BLOCKED")

    def test_31_writer_equals_reviewer_blocked(self):
        task = self._task(reviewer_role="ROLE-004")
        r = sgr.authorize_task(task, self.state, self.roles)
        self.assertEqual(r["result"], "BLOCKED")

    def test_32_d4_egress_for_ai_blocked(self):
        task = self._task(data_egress="D4")
        r = sgr.authorize_task(task, self.state, self.roles)
        self.assertEqual(r["result"], "BLOCKED")

    def test_33_ai_remote_write_blocked(self):
        task = self._task(remote_permission="AI_WRITE")
        r = sgr.authorize_task(task, self.state, self.roles)
        self.assertEqual(r["result"], "BLOCKED")

    def test_34_data_egress_ceiling_enforced(self):
        task = self._task(role_id="ROLE-003", data_egress="D3")
        r = sgr.authorize_task(task, self.state, self.roles)
        self.assertEqual(r["result"], "BLOCKED")

    def test_35_remote_permission_ceiling_enforced(self):
        task = self._task(role_id="ROLE-003", remote_permission="HUMAN_REMOTE_ACTION_REQUIRED")
        r = sgr.authorize_task(task, self.state, self.roles)
        self.assertEqual(r["result"], "BLOCKED")

    def test_36_human_action_boundary_remote_push(self):
        r = sgr.check_human_action_boundary("remote push", "ROLE-004")
        self.assertEqual(r["result"], "BLOCKED")

    def test_37_human_action_boundary_merge(self):
        r = sgr.check_human_action_boundary("merge", "ROLE-001")
        self.assertEqual(r["result"], "ALLOWED")

    def test_38_human_action_boundary_release(self):
        r = sgr.check_human_action_boundary("release", "ROLE-004")
        self.assertEqual(r["result"], "BLOCKED")

    def test_39_human_action_boundary_e4(self):
        r = sgr.check_human_action_boundary("E4", "ROLE-002")
        self.assertEqual(r["result"], "BLOCKED")

    # ---- Derived work ----

    def test_40_process_derived_work_detected_to_candidate(self):
        c = {
            "work_candidate_id": "ANOX-WORK-001",
            "suggested_by": "AI",
            "source_run": "ANOX-RUN-001",
            "status": "Detected",
            "authorization_status": "NON-AUTHORIZED",
        }
        r = sgr.process_derived_work(c)
        self.assertEqual(r["result"], "ALLOWED")
        self.assertEqual(r["candidate"]["status"], "Candidate")

    def test_41_process_derived_work_evaluated(self):
        c = {
            "work_candidate_id": "ANOX-WORK-001",
            "suggested_by": "AI",
            "source_run": "ANOX-RUN-001",
            "status": "Candidate",
            "authorization_status": "NON-AUTHORIZED",
        }
        r = sgr.process_derived_work(c)
        self.assertEqual(r["result"], "ALLOWED")
        self.assertEqual(r["candidate"]["status"], "Evaluated")

    def test_42_process_derived_work_ai_self_authorize_blocked(self):
        c = {
            "work_candidate_id": "ANOX-WORK-001",
            "suggested_by": "AI",
            "source_run": "ANOX-RUN-001",
            "status": "Evaluated",
            "authorization_status": "NON-AUTHORIZED",
            "proposed_authorization": "Authorized",
        }
        r = sgr.process_derived_work(c)
        self.assertEqual(r["result"], "BLOCKED")

    def test_43_process_derived_work_not_non_authorized(self):
        c = {
            "work_candidate_id": "ANOX-WORK-001",
            "suggested_by": "AI",
            "source_run": "ANOX-RUN-001",
            "status": "Evaluated",
            "authorization_status": "Authorized",
        }
        r = sgr.process_derived_work(c)
        self.assertEqual(r["result"], "BLOCKED")

    # ---- Routing / security / product gate ----

    def test_44_route_finding_crypto_protocol(self):
        r = sgr.route_finding({"category": "crypto/protocol"})
        self.assertEqual(r["roles"][0], "ROLE-005")
        self.assertEqual(r["independent_reviewer"], "ROLE-007")

    def test_45_route_finding_appsec(self):
        r = sgr.route_finding({"category": "appsec"})
        self.assertEqual(r["roles"][0], "ROLE-008")

    def test_46_route_finding_architecture(self):
        r = sgr.route_finding({"category": "architecture/privacy/security"})
        self.assertEqual(r["roles"][0], "ROLE-009")

    def test_47_route_finding_build_implementation_human(self):
        self.assertEqual(sgr.route_finding({"category": "build/supply-chain"})["roles"][0], "ROLE-010")
        self.assertEqual(sgr.route_finding({"category": "implementation"})["roles"], ["ROLE-004"])
        self.assertEqual(sgr.route_finding({"category": "human-only"})["roles"], ["ROLE-001"])

    def test_48_evaluate_security_trigger_and_legacy_and_final_gate(self):
        r = sgr.evaluate_security_trigger(["cryptography"])
        self.assertTrue(r["triggered"])
        self.assertEqual(r["level"], "SEC-C")
        self.assertTrue(len(r["candidates"]) > 0)

        legacy = sgr.resolve_legacy_revalidation(["crypto", "build"])
        ids = {s["session_id"] for s in legacy}
        self.assertIn("LEGACY-AUDIT-CRYPTO", ids)
        self.assertIn("LEGACY-AUDIT-BUILD", ids)

        gate = sgr.resolve_final_product_gate({
            "final_audit_complete": True,
            "blocking_findings": [],
            "legacy_audits": [{"satisfied": True}],
        })
        self.assertEqual(gate["result"], "BLOCKED")


def main():
    if validate_b027b_structural() != 0:
        return 1
    print("\n[B027-B] Resolver tests", flush=True)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(B027BResolverTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
