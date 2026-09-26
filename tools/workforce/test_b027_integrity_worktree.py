#!/usr/bin/env python3
"""Regression tests: B027-C integrity validator Git detection in linked worktrees.

The validator previously required (REPO_ROOT / ".git").is_dir(), which is false
for legitimate Git linked worktrees (.git is a pointer file). These tests pin
Git-native, fail-closed detection using real temporary repositories/worktrees.

No network. All fixtures are synthetic and temporary.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "workforce"))

import validate_b027_integrity as b027i


def _git(root, *cmd):
    return subprocess.run(["git", *cmd], cwd=str(root), capture_output=True, text=True)


class B027CWorktreeTests(unittest.TestCase):
    """_is_git_worktree / _git_diff_names / _ancestor_or_equal in real repos and linked worktrees."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="b027c_wt_test_"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir(parents=True)
        _git(self.repo, "init")
        _git(self.repo, "config", "user.email", "test@anox.local")
        _git(self.repo, "config", "user.name", "Test")
        (self.repo / "tracked.txt").write_text("base\n", encoding="utf-8")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-m", "init")
        self.sha_a = _git(self.repo, "rev-parse", "HEAD").stdout.strip()
        (self.repo / "tracked.txt").write_text("base\nsecond\n", encoding="utf-8")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-m", "second")
        self.sha_b = _git(self.repo, "rev-parse", "HEAD").stdout.strip()

        self.original_repo_root = b027i.REPO_ROOT
        b027i.REPO_ROOT = self.repo
        self.validator = b027i.B027CIntegrityValidator()

    def tearDown(self):
        b027i.REPO_ROOT = self.original_repo_root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _linked_worktree(self):
        wt = self.tmp / "linked"
        r = _git(self.repo, "worktree", "add", str(wt), "-b", "linked-test", "HEAD")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((wt / ".git").is_file())
        b027i.REPO_ROOT = wt
        return wt

    # -- _is_git_worktree ----------------------------------------------------

    def test_normal_repo_accepted(self):
        self.assertTrue((self.repo / ".git").is_dir())
        self.assertTrue(self.validator._is_git_worktree())

    def test_linked_worktree_accepted(self):
        self._linked_worktree()
        self.assertTrue(self.validator._is_git_worktree())

    def test_non_git_dir_rejected(self):
        b027i.REPO_ROOT = self.tmp / "plain"
        (self.tmp / "plain").mkdir()
        self.assertFalse(self.validator._is_git_worktree())

    def test_fake_dotgit_file_rejected(self):
        fake = self.tmp / "fake"
        fake.mkdir()
        (fake / ".git").write_text("gitdir: /nonexistent/fake\n", encoding="utf-8")
        b027i.REPO_ROOT = fake
        self.assertFalse(self.validator._is_git_worktree())

    def test_repo_subdirectory_rejected(self):
        sub = self.repo / "sub" / "dir"
        sub.mkdir(parents=True)
        b027i.REPO_ROOT = sub
        self.assertFalse(self.validator._is_git_worktree())

    # -- _ancestor_or_equal ---------------------------------------------------

    def test_ancestor_passes_in_normal_repo(self):
        self.assertTrue(self.validator._ancestor_or_equal(self.sha_a, self.sha_b))

    def test_ancestor_passes_in_linked_worktree(self):
        """BC-12 regression: real ancestry must be evaluated in a linked worktree."""
        self._linked_worktree()
        self.assertTrue(self.validator._ancestor_or_equal(self.sha_a, self.sha_b))

    def test_non_ancestor_rejected_in_normal_repo(self):
        self.assertFalse(self.validator._ancestor_or_equal(self.sha_b, self.sha_a))

    def test_non_ancestor_rejected_in_linked_worktree(self):
        self._linked_worktree()
        self.assertFalse(self.validator._ancestor_or_equal(self.sha_b, self.sha_a))

    def test_equal_sha_passes_without_git(self):
        """Non-Git fallback semantics preserved: equal SHAs still pass."""
        b027i.REPO_ROOT = self.tmp / "plain2"
        (self.tmp / "plain2").mkdir()
        self.assertTrue(self.validator._ancestor_or_equal(self.sha_a, self.sha_a))
        self.assertFalse(self.validator._ancestor_or_equal(self.sha_a, self.sha_b))

    # -- _git_diff_names ------------------------------------------------------

    def test_git_diff_names_real_diff_in_normal_repo(self):
        (self.repo / "tracked.txt").write_text("base\nsecond\nthird\n", encoding="utf-8")
        self.assertIn("tracked.txt", self.validator._git_diff_names("HEAD"))

    def test_git_diff_names_real_diff_in_linked_worktree(self):
        wt = self._linked_worktree()
        (wt / "tracked.txt").write_text("base\nsecond\nthird\n", encoding="utf-8")
        self.assertIn("tracked.txt", self.validator._git_diff_names("HEAD"))

    def test_git_diff_names_empty_without_git(self):
        b027i.REPO_ROOT = self.tmp / "plain3"
        (self.tmp / "plain3").mkdir()
        self.assertEqual(self.validator._git_diff_names("HEAD"), [])


if __name__ == "__main__":
    unittest.main()
