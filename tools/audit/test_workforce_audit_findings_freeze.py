#!/usr/bin/env python3
"""Adversarial tests for validate_workforce_audit_findings_freeze.py.

Each test builds a temporary copy of the repo, commits the (possibly mutated)
state, and asserts that the validator fails closed for the relevant corruption.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ORIGIN = Path(__file__).resolve().parents[2]
VALIDATOR = ORIGIN / "tools" / "audit" / "validate_workforce_audit_findings_freeze.py"


def _git(cmd, cwd):
    result = subprocess.run(
        ["git"] + cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result


def _setup_repo(mutation=None):
    """Copy .git, reset to the canonical base, overlay current docs/tools,
    commit base state, apply mutation, commit again.

    This yields two task-authored commits above the original base so that the
    validator's two-commit and base-ancestor checks accept the temp repo, while
    preserving product files so that product-scope checks do not false-positive.
    """
    tmp = tempfile.mkdtemp(prefix="workforce-freeze-adv-")
    git_src = ORIGIN / ".git"
    if git_src.exists():
        shutil.copytree(git_src, Path(tmp) / ".git", symlinks=True)

    _git(["config", "user.email", "test@anox.software"], tmp)
    _git(["config", "user.name", "Test Runner"], tmp)

    # Start a fresh test branch from the canonical base.
    base = "d5f76ba9dfdb332ac5f70b769c57b3f0ae6122b8"
    _git(["reset", "--hard", base], tmp)
    _git(["checkout", "-b", "test-adversarial"], tmp)

    # Overlay the current docs/tools state (the freeze deliverables).
    for sub in ("docs", "tools"):
        src = ORIGIN / sub
        dst = Path(tmp) / sub
        if dst.exists():
            shutil.rmtree(dst)
        if src.exists():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".DS_Store"))

    # First commit: the base (unmutated) freeze state.
    _git(["add", "-A"], tmp)
    _git(["commit", "-m", "adversarial test base freeze state", "--no-verify"], tmp)

    if mutation:
        mutation(tmp)

    # Second commit: the mutation (or an empty marker for the base-pass case).
    _git(["add", "-A"], tmp)
    _git(["commit", "-m", "adversarial test mutation", "--allow-empty", "--no-verify"], tmp)
    head = _git(["rev-parse", "HEAD"], tmp).stdout.strip()
    return tmp, head


def _run_validator(tmp, head):
    env = os.environ.copy()
    env["WORKFORCE_FREEZE_REPO"] = str(tmp)
    # BASE_SHA is the original main baseline (d5f76ba...) in the copied repo.
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=tmp,
        env=env,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def _read_jsonl(tmp, rel):
    p = Path(tmp) / rel
    lines = []
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if l.strip():
                lines.append(json.loads(l))
    return lines


def _write_jsonl(tmp, rel, lines):
    p = Path(tmp) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")


def _read_json(tmp, rel):
    with open(Path(tmp) / rel, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(tmp, rel, data):
    with open(Path(tmp) / rel, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class FreezeAdversarialTests(unittest.TestCase):
    def test_base_pass(self):
        tmp, head = _setup_repo()
        try:
            code, out, err = _run_validator(tmp, head)
            self.assertEqual(code, 0, f"base should pass:\n{out}\n{err}")
        finally:
            shutil.rmtree(tmp)

    def test_001_candidate_disappears(self):
        def mutate(tmp):
            audits = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for a in audits:
                if a.get("audit_id") == "ANOX-AUDIT-WORKFORCE-ARCH-001":
                    a["source_candidates"] = [c for c in a["source_candidates"] if c.get("candidate_id") != "ANOX-WORKFORCE-AUDIT-001"]
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", audits)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
            self.assertIn("ANOX-WORKFORCE-AUDIT-001", out)
        finally:
            shutil.rmtree(tmp)

    def test_002_two_dispositions(self):
        def mutate(tmp):
            audits = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for a in audits:
                if a.get("audit_id") == "ANOX-AUDIT-WORKFORCE-ARCH-001":
                    c = a["source_candidates"][0]
                    a["source_candidates"].append({**c, "disposition": "PROMOTE_CANONICAL"})
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", audits)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
            self.assertIn("multiple dispositions", out)
        finally:
            shutil.rmtree(tmp)

    def test_003_archive_failure_ignored(self):
        def mutate(tmp):
            audits = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for a in audits:
                if a.get("audit_id") == "ANOX-AUDIT-WORKFORCE-ARCH-001":
                    for c in a["source_candidates"]:
                        if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-002":
                            c["disposition"] = "NOT_A_FINDING"
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", audits)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
            self.assertIn("002", out)
        finally:
            shutil.rmtree(tmp)

    def test_004_merge_commit_counted_as_task_commit(self):
        def mutate(tmp):
            audits = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for a in audits:
                if a.get("audit_id") == "ANOX-AUDIT-WORKFORCE-ARCH-001":
                    for c in a["source_candidates"]:
                        if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-001":
                            c["rationale"] = "count all commits on branch"
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", audits)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
        finally:
            shutil.rmtree(tmp)

    def test_005_path_escape_promoted_without_reachability(self):
        def mutate(tmp):
            audits = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for a in audits:
                if a.get("audit_id") == "ANOX-AUDIT-WORKFORCE-ARCH-001":
                    for c in a["source_candidates"]:
                        if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-005":
                            c["rationale"] = "path escape found"
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", audits)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
            self.assertIn("reachability", out)
        finally:
            shutil.rmtree(tmp)

    def test_006_wildcard_silently_assumed_recursive(self):
        def mutate(tmp):
            audits = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for a in audits:
                if a.get("audit_id") == "ANOX-AUDIT-WORKFORCE-ARCH-001":
                    for c in a["source_candidates"]:
                        if c.get("candidate_id") == "ANOX-WORKFORCE-AUDIT-006":
                            c["disposition"] = "NOT_A_FINDING"
                            c["rationale"] = "fnmatch is recursive by design"
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", audits)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            # Acceptable if rationale mentions wildcard/scope.
            self.assertIn("wildcard", out.lower())
        finally:
            shutil.rmtree(tmp)

    def test_007_autonomous_runtime_absence_fake_finding(self):
        def mutate(tmp):
            findings = _read_jsonl(tmp, "docs/workforce/registries/findings.jsonl")
            findings.append({
                "finding_id": "ANOX-WORKFORCE-AUDIT-099",
                "title": "Autonomous employee runtime missing",
                "severity": "LOW",
                "status": "Open",
                "discovered_by": "AI",
                "discovered_in_run": "ANOX-RUN-WORKFORCE0001",
                "affected_scope": "workforce",
            })
            _write_jsonl(tmp, "docs/workforce/registries/findings.jsonl", findings)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
        finally:
            shutil.rmtree(tmp)

    def test_008_final_handoff_acceptance_disappears(self):
        def mutate(tmp):
            derived = _read_jsonl(tmp, "docs/workforce/registries/derived_work.jsonl")
            derived = [d for d in derived if "BOOTSTRAP" not in (d.get("title", "")).upper()]
            _write_jsonl(tmp, "docs/workforce/registries/derived_work.jsonl", derived)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
            self.assertIn("handoff", out.lower())
        finally:
            shutil.rmtree(tmp)

    def test_009_product_unblocked(self):
        def mutate(tmp):
            state = _read_json(tmp, "docs/workforce/WORKFORCE_STATE.json")
            state["product_development_state"] = "UNBLOCKED"
            _write_json(tmp, "docs/workforce/WORKFORCE_STATE.json", state)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
            self.assertIn("BLOCKED_PENDING_FINAL_AUDIT", out)
        finally:
            shutil.rmtree(tmp)

    def test_010_security_audit_authorized_while_workforce_blocked(self):
        def mutate(tmp):
            tasks = _read_jsonl(tmp, "docs/workforce/registries/tasks.jsonl")
            tasks.append({
                "task_id": "ANOX-TASK-SECURITYARCH001",
                "title": "AUDIT-SECURITY-ARCHITECTURE",
                "role_id": "ROLE-009",
                "start_sha": "d" * 40,
                "branch": "audit/security-architecture",
                "allowed_paths": ["docs/current/"],
                "forbidden_paths": ["android/"],
                "scope": "security audit",
                "non_goals": ["product"],
                "security_class": "S2",
                "data_egress": "D2",
                "priority": "P1",
                "required_evidence": "E3",
                "reviewer_role": "ROLE-002",
                "remote_permission": "NONE",
                "stop_conditions": ["pass"],
                "authority_refs": ["docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md"],
                "created_at": "2026-09-08",
                "status": "Authorized",
            })
            _write_jsonl(tmp, "docs/workforce/registries/tasks.jsonl", tasks)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
            self.assertIn("Security Architecture Audit", out)
        finally:
            shutil.rmtree(tmp)

    def test_011_existing_product_finding_closed(self):
        def mutate(tmp):
            findings = _read_jsonl(tmp, "docs/workforce/registries/findings.jsonl")
            for f in findings:
                if f.get("finding_id") == "ANOX-MAINARCH-013":
                    f["status"] = "Closed"
                    f["closure_actor"] = "AI"
                    f["closure_evidence"] = ["test"]
            _write_jsonl(tmp, "docs/workforce/registries/findings.jsonl", findings)

        tmp, head = _setup_repo(mutate)
        try:
            code, out, _ = _run_validator(tmp, head)
            self.assertNotEqual(code, 0)
            self.assertIn("ANOX-MAINARCH-013", out)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
