#!/usr/bin/env python3
"""WORKFORCE-FIX-01 adversarial and synthetic tests.

Tests the same invariants the validator checks under manipulated conditions:
- true third task commit detection;
- human merge commit exclusion;
- later main history exclusion;
- post-merge effective state derivation;
- path authorization reachability;
- wildcard semantics;
- final operational acceptance gate fail-closed.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def git(args, cwd, check=True):
    cmd = ["git"] + list(args)
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result


def make_temp_repo():
    """Create a scratch git repo to exercise merge-aware delivery invariants."""
    td = tempfile.mkdtemp(prefix="anox_workforce_fix01_")
    git(["init", "--quiet"], td)
    git(["config", "user.email", "test@anox.software"], td)
    git(["config", "user.name", "Test"], td)
    git(["checkout", "-b", "main"], td, check=False)

    def commit(msg, files=None, branch=None):
        if branch:
            git(["checkout", "-b", branch, "HEAD"], td, check=True)
        if files:
            for rel, content in files.items():
                p = Path(td) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content)
                git(["add", rel], td)
        else:
            git(["add", "-A"], td)
        git(["commit", "--quiet", "-m", msg], td)
        return git(["rev-parse", "HEAD"], td).stdout.strip()

    base = commit("base", {"a.txt": "1"})
    return td, base, commit


class MergeAwareDeliveryTests(unittest.TestCase):
    """Synthetic tests for Finding 001."""

    def test_exact_two_commits_on_delivery_branch(self):
        td, base, commit = make_temp_repo()
        commit("substantive", {"b.txt": "2"}, branch="fix")
        commit("metadata", {"b.txt": "3"}, branch=None)
        try:
            sys.path.insert(0, str(REPO / "tools" / "audit"))
            import lifecycle_legality as ll
            ok, dp, sh, reason = ll.canonical_two_commit_delivery(
                base, git(["rev-parse", "HEAD~1"], td).stdout.strip(),
                git(["rev-parse", "HEAD"], td).stdout.strip(),
                cwd=td
            )
            self.assertTrue(ok, reason)
        finally:
            pass

    def test_human_merge_excluded(self):
        td, base, commit = make_temp_repo()
        sub = commit("substantive", {"b.txt": "2"}, branch="fix")
        meta = commit("metadata", {"b.txt": "3"}, branch=None)
        # Human merges fix to main.
        git(["checkout", "main"], td)
        git(["merge", "--no-ff", "-m", "human merge", "fix"], td)
        head = git(["rev-parse", "HEAD"], td).stdout.strip()
        # Add another commit on main after merge (later history).
        commit("later", {"c.txt": "4"}, branch=None)
        live = git(["rev-parse", "HEAD"], td).stdout.strip()

        sys.path.insert(0, str(REPO / "tools" / "audit"))
        import lifecycle_legality as ll
        ok, dp, sh, reason = ll.canonical_two_commit_delivery(
            base, sub, live, cwd=td
        )
        self.assertTrue(ok, reason)
        self.assertEqual(dp, meta)

    def test_true_third_task_commit_rejected(self):
        td, base, commit = make_temp_repo()
        sub = commit("substantive", {"b.txt": "2"}, branch="fix")
        commit("extra", {"b.txt": "3"}, branch=None)
        meta = commit("metadata", {"b.txt": "4"}, branch=None)
        git(["checkout", "main"], td)
        git(["merge", "--no-ff", "-m", "human merge", "fix"], td)
        live = git(["rev-parse", "HEAD"], td).stdout.strip()

        sys.path.insert(0, str(REPO / "tools" / "audit"))
        import lifecycle_legality as ll
        ok, dp, sh, reason = ll.canonical_two_commit_delivery(
            base, sub, live, cwd=td
        )
        self.assertFalse(ok, "three task-authored commits must be rejected")

    def test_later_main_history_excluded(self):
        td, base, commit = make_temp_repo()
        sub = commit("substantive", {"b.txt": "2"}, branch="fix")
        meta = commit("metadata", {"b.txt": "3"}, branch=None)
        git(["checkout", "main"], td)
        git(["merge", "--no-ff", "-m", "human merge", "fix"], td)
        commit("later main", {"c.txt": "4"}, branch=None)
        commit("even later", {"d.txt": "5"}, branch=None)
        live = git(["rev-parse", "HEAD"], td).stdout.strip()

        sys.path.insert(0, str(REPO / "tools" / "audit"))
        import lifecycle_legality as ll
        ok, dp, sh, reason = ll.canonical_two_commit_delivery(
            base, sub, live, cwd=td
        )
        self.assertTrue(ok, reason)
        self.assertEqual(dp, meta)


class PathAuthorizationTests(unittest.TestCase):
    """Reachability tests for Finding 005."""

    def _allowed(self, path):
        sys.path.insert(0, str(REPO / "tools" / "workforce"))
        import state_gate_resolver as sgr
        ok, reason = sgr._path_allowed(path, ["docs/workforce/"], ["backend/"])
        return ok

    def test_dotdot_escape_blocked(self):
        self.assertFalse(self._allowed("docs/workforce/../backend/x.py"))

    def test_multi_dotdot_blocked(self):
        self.assertFalse(self._allowed("docs/workforce/../../backend/x.py"))

    def test_root_escape_blocked(self):
        self.assertFalse(self._allowed("../backend/x.py"))

    def test_absolute_posix_blocked(self):
        self.assertFalse(self._allowed("/etc/passwd"))

    def test_absolute_windows_blocked(self):
        self.assertFalse(self._allowed("C:/Windows/System32/foo.dll"))

    def test_unc_blocked(self):
        self.assertFalse(self._allowed("\\\\server\\share\\secret"))

    def test_dot_component_allowed(self):
        self.assertTrue(self._allowed("docs/workforce/./x.py"))

    def test_duplicate_separators_allowed(self):
        self.assertTrue(self._allowed("docs//workforce//x.py"))

    def test_single_component_wildcard_not_recursive(self):
        sys.path.insert(0, str(REPO / "tools" / "workforce"))
        import state_gate_resolver as sgr
        allowed = ["docs/workforce/*.py"]
        self.assertTrue(sgr._path_allowed("docs/workforce/a.py", allowed, [])[0])
        self.assertFalse(sgr._path_allowed("docs/workforce/sub/a.py", allowed, [])[0])

    def test_double_recursive_wildcard_allowed(self):
        sys.path.insert(0, str(REPO / "tools" / "workforce"))
        import state_gate_resolver as sgr
        allowed = ["docs/workforce/**"]
        self.assertTrue(sgr._path_allowed("docs/workforce/a.py", allowed, [])[0])
        self.assertTrue(sgr._path_allowed("docs/workforce/sub/a.py", allowed, [])[0])


class PostMergeStateTests(unittest.TestCase):
    """Tests for Finding 002."""

    def test_derive_effective_on_main(self):
        sys.path.insert(0, str(REPO / "tools" / "workforce"))
        import state_gate_resolver as sgr
        ws = {
            "canonical_branch": "main",
            "pre_merge_state": {
                "current_writer": {"task_id": "ANOX-TASK-WORKFORCEFIX01"},
                "current_gate": "WORKFORCE-FIX-01",
            },
            "post_merge_state": {
                "current_writer": None,
                "current_gate": "WORKFORCE-RETEST-01",
            },
        }
        effective = sgr.derive_effective_workforce_state(ws, live_branch="main",
                                                          live_head="a" * 40, repo_root=REPO)
        # Without an actual merge in git, it falls back to pre_merge.
        self.assertIsNotNone(effective)


class FinalAcceptanceGateTests(unittest.TestCase):
    """Tests for final operational handoff acceptance gate."""

    def test_gate_not_executed_blocks_product(self):
        sys.path.insert(0, str(REPO / "tools" / "workforce"))
        import state_gate_resolver as sgr
        r = sgr.resolve_final_product_gate({
            "final_audit_complete": True,
            "legacy_audits": [{"satisfied": True}],
            "blocking_findings": [],
            "final_operational_handoff_acceptance": {"status": "NOT_EXECUTED"},
            "machine_decision": True,
            "human_decision": True,
        })
        self.assertEqual(r["result"], "BLOCKED")

    def test_gate_pass_but_human_missing_blocks(self):
        sys.path.insert(0, str(REPO / "tools" / "workforce"))
        import state_gate_resolver as sgr
        r = sgr.resolve_final_product_gate({
            "final_audit_complete": True,
            "legacy_audits": [{"satisfied": True}],
            "blocking_findings": [],
            "final_operational_handoff_acceptance": {"status": "PASS"},
            "machine_decision": True,
            "human_decision": False,
        })
        self.assertEqual(r["result"], "BLOCKED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
