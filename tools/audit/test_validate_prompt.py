#!/usr/bin/env python3
"""Adversarial tests for B-028 validate_prompt.py — scope-creep resistance."""

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_prompt as vp


TASK = {
    "task_id": "ANOX-TASK-P-001", "role_id": "ROLE-004",
    "branch": "remediation/p-001", "start_sha": "a" * 40,
    "allowed_paths": ["docs/**", "tools/audit/validate_x.py"],
    "forbidden_paths": ["crypto/**", ".github/**"],
    "data_egress": "D2", "remote_permission": "NONE",
    "status": "Authorized",
}


def prompt(**kw):
    p = {
        "prompt_id": "ANOX-PROMPT-0001",
        "task_id": "ANOX-TASK-P-001",
        "role_id": "ROLE-004",
        "branch": "remediation/p-001",
        "content": "Implement the fix on baseline_sha " + "a" * 40 + " within scope.",
        "allowed_paths": ["docs/**"],
        "forbidden_paths": ["crypto/**", ".github/**"],
        "data_egress": "D2",
        "remote_permission": "NONE",
        "authority_refs": ["docs/authority/AUTHORITY_INDEX.md"],
    }
    p.update(kw)
    return p


class ValidateTests(unittest.TestCase):
    def check(self, p, tasks=None, seen=None):
        return vp.validate_record(p, tasks or [TASK], seen or set())

    def test_valid_prompt_passes(self):
        self.assertEqual(self.check(prompt()), [])

    def test_missing_field_fails(self):
        p = prompt()
        del p["content"]
        self.assertTrue(any("missing" in x for x in self.check(p)))

    def test_scope_expansion_fails(self):
        p = prompt(allowed_paths=["docs/**", "crypto/**"])
        self.assertTrue(any("exceeds task scope" in x for x in self.check(p)))

    def test_single_file_path_outside_scope_fails(self):
        p = prompt(allowed_paths=["docs/**", "tools/audit/validate_y.py"])
        self.assertTrue(any("exceeds task scope" in x for x in self.check(p)))

    def test_exact_declared_file_path_allowed(self):
        p = prompt(allowed_paths=["tools/audit/validate_x.py"])
        self.assertEqual(self.check(p), [])

    def test_weakened_forbidden_paths_fail(self):
        p = prompt(forbidden_paths=["crypto/**"])
        self.assertTrue(any("weakens forbidden" in x for x in self.check(p)))

    def test_egress_exceeds_ceiling_fails(self):
        p = prompt(data_egress="D3")
        self.assertTrue(any("exceeds task ceiling" in x for x in self.check(p)))

    def test_remote_permission_exceeds_fails(self):
        p = prompt(remote_permission="READ_ONLY")
        self.assertTrue(any("exceeds task ceiling" in x for x in self.check(p)))

    def test_model_token_in_content_fails(self):
        p = prompt(content="Use devin2max. baseline_sha " + "a" * 40)
        self.assertTrue(any("model selection token" in x for x in self.check(p)))

    def test_missing_baseline_binding_fails(self):
        p = prompt(content="Implement the fix within scope.")
        self.assertTrue(any("baseline" in x for x in self.check(p)))

    def test_wrong_role_fails(self):
        self.assertTrue(any("role_id" in x for x in self.check(prompt(role_id="ROLE-009"))))

    def test_wrong_branch_fails(self):
        self.assertTrue(any("branch" in x for x in self.check(prompt(branch="other/branch"))))

    def test_unknown_task_fails(self):
        p = prompt(task_id="ANOX-TASK-UNKNOWN-1")
        self.assertTrue(any("registry matches" in x for x in self.check(p)))

    def test_non_authorized_task_fails(self):
        task = dict(TASK, status="Candidate")
        self.assertTrue(any("not delivery-authorized" in x
                            for x in self.check(prompt(), tasks=[task])))

    def test_duplicate_prompt_id_fails(self):
        self.assertTrue(any("duplicate" in x
                            for x in self.check(prompt(), seen={"ANOX-PROMPT-0001"})))

    def test_empty_authority_refs_fails(self):
        self.assertTrue(any("authority_refs" in x
                            for x in self.check(prompt(authority_refs=[]))))


if __name__ == "__main__":
    unittest.main()
