#!/usr/bin/env python3
"""Focused tests for the handoff generator and continuity validator."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class LiveFixture:
    """Minimal repository fixture that can run live validator and handoff generator."""

    def __init__(self, baseline_override=None, add_synthetic_secret=None, stale_claims=None,
                 handoff_branch_override=None, competing_precedence=False):
        self.tmp = tempfile.mkdtemp(prefix="anox_handoff_test_")
        self.root = Path(self.tmp)

        tools_dir = self.root / "tools" / "continuity"
        tools_dir.mkdir(parents=True)
        for name in ("generate_handoff.py", "validate_continuity.py"):
            src = REPO_ROOT / "tools" / "continuity" / name
            dst = tools_dir / name
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

        sec_dir = self.root / "tools" / "security"
        sec_dir.mkdir(parents=True)
        (sec_dir / "validate_apk_contents.py").write_text("# APK\n", encoding="utf-8")

        self._setup_files(stale_claims)

        self._run(["git", "init"])
        self._run(["git", "config", "user.email", "test@anox.local"])
        self._run(["git", "config", "user.name", "Test"])
        # Create main branch with an initial commit, then a governance branch from it
        self._run(["git", "checkout", "-b", "main"])
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", "init"])
        main_head = self._run(["git", "rev-parse", "main"]).stdout.strip()
        self._run(["git", "checkout", "-b", "governance/development-security-handoff-v1"])

        self.baseline_head = baseline_override if baseline_override else main_head
        self.handoff_branch = handoff_branch_override if handoff_branch_override else "governance/development-security-handoff-v1"
        self._write("docs/continuity/CURRENT_STATE.json", self._state_json(self.baseline_head, self.handoff_branch))
        self._write("docs/continuity/CURRENT_GIT_STATE.md", self._git_state_md(self.baseline_head, self.handoff_branch))
        self._write("docs/continuity/CURRENT_HANDOFF.md", self._handoff_md(self.baseline_head, self.handoff_branch))

        if competing_precedence:
            self._write("docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md", self._competing_precedence_md())

        if add_synthetic_secret:
            (self.root / add_synthetic_secret).write_text("synthetic secret fixture", encoding="utf-8")

    def _setup_files(self, stale_claims=None):
        self._write("docs/authority/AUTHORITY_INDEX.md", "# Authority Index\n## Precedence\n1. `B025/SECURITY_INVARIANTS_V1_1.md`\n## Canonical source\nThis file is canonical.\n")
        self._write("docs/authority/CLOUD_AI_SECRET_PROTECTION.md", "# Cloud AI Secret\n")
        self._write("docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md", "# Workflow\n")
        self._write("docs/authority/B025/SECURITY_INVARIANTS_V1_1.md", "# Invariants\n")
        self._write("docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md", "# B026\n")
        self._write("docs/authority/B_FREEZE_REGISTRY.md", "# Freeze\n")
        self._write("docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md", "# Arch\n")

        self._write("docs/continuity/AUTHORITY_INDEX.md", "# C-Authority\n")
        self._write("docs/continuity/CURRENT_HANDOFF.md", "# Handoff\nplaceholder\n")
        self._write("docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md", "# Bootstrap\nDEVELOPMENT_SECURITY_WORKFLOW_V1.md\n")
        self._write("docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md", "# Upload\n")
        self._write("docs/continuity/CURRENT_IMPLEMENTATION_STATE.md", self._impl_md(stale_claims))
        self._write("docs/continuity/CURRENT_GIT_STATE.md", "# Git\nplaceholder\n")
        self._write("docs/continuity/CURRENT_OPEN_WORK.md", "# Open\n")
        self._write("docs/continuity/CURRENT_NEXT_DEVIN_TASK.md", "# Next\nPROMPT-009 GOVERNANCE REMEDIATION / REVIEW\n")
        self._write("docs/continuity/DEVIN_OUTPUT_CONTRACT.md", "# Contract\nA. TASK\nQ. NEXT RECOMMENDED GATE\n")
        self._write("docs/continuity/HANDOFF_WORKFLOW.md", "# Workflow\n")
        self._write("docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md", "# Checklist\n")
        self._write("PROJECT_STATE.md", "# State\n- Branch: `governance/development-security-handoff-v1`\nB-002 merged.\n")
        self._write("FORTSCHRITT.md", "# Fortschritt\nApproximately **33%**.\nB-003 merged.\n")
        self._write("DEVIN_PROMPT_OUTPUT_ARCHIV.md", "# Archive\n")

    def _impl_md(self, stale_claims=None):
        base = "# Impl\nB-002 MERGED.\nB-003 MERGED FOUNDATION.\n"
        if stale_claims:
            base += stale_claims + "\n"
        return base

    def _write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _handoff_md(self, baseline_head, handoff_branch=None):
        branch = handoff_branch or "governance/development-security-handoff-v1"
        return (
            "# Handoff\n"
            f"- Current work branch: `{branch}`\n"
            f"- Current baseline HEAD: `{baseline_head}`\n"
            f"- Merged baseline HEAD: `{baseline_head}`\n"
        )

    def _git_state_md(self, baseline_head, handoff_branch=None):
        branch = handoff_branch or "governance/development-security-handoff-v1"
        return (
            "# Git\n"
            f"- Current handoff branch: `{branch}`\n"
            f"- Current baseline HEAD: `{baseline_head}`\n"
            f"- Merged baseline HEAD: `{baseline_head}`\n"
        )

    def _state_json(self, baseline_head, handoff_branch=None):
        branch = handoff_branch or "governance/development-security-handoff-v1"
        return (
            '{\n'
            '  "schema_version": "B026-1.0",\n'
            f'  "handoff_branch": "{branch}",\n'
            '  "handoff_head": "__HANDOFF_HEAD__",\n'
            f'  "baseline_branch": "main",\n'
            f'  "baseline_head": "{baseline_head}",\n'
            '  "working_tree": "__WORKING_TREE__",\n'
            '  "continuity_001_status": "ACCEPTED",\n'
            '  "security_invariants_path": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",\n'
            '  "freeze_registry_path": "docs/authority/B_FREEZE_REGISTRY.md",\n'
            '  "current_task": "PROMPT-009 GOVERNANCE REMEDIATION / REVIEW",\n'
            '  "current_gate": "PROMPT-009 GOVERNANCE REMEDIATION / REVIEW"\n'
            '}\n'
        )

    def _competing_precedence_md(self):
        return (
            "# Workflow\n"
            "## Authority precedence\n"
            "1. `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md` is the winner.\n"
            "2. `docs/authority/AUTHORITY_INDEX.md` is subordinate.\n"
            "\n"
            "## S0–S4 Security Classification\n"
        )

    def _run(self, cmd, **kw):
        kw.setdefault("cwd", str(self.root))
        kw.setdefault("capture_output", True)
        kw.setdefault("text", True)
        return subprocess.run(cmd, **kw)

    def validate(self, mode="live"):
        return self._run([sys.executable, "tools/continuity/validate_continuity.py", "--mode", mode])

    def generate(self, emergency=True):
        return self._run([sys.executable, "tools/continuity/generate_handoff.py"] + (["--emergency"] if emergency else []))

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def list_zip(self):
        artifacts = sorted(self.root.glob("artifacts/handoff/*.zip"))
        if not artifacts:
            return []
        with zipfile.ZipFile(artifacts[0]) as zf:
            return zf.namelist()

    def zip_path(self):
        artifacts = sorted(self.root.glob("artifacts/handoff/*.zip"))
        return artifacts[0] if artifacts else None


class ArchiveFixture:
    """Fixture extracted from a generated handoff ZIP, without .git."""

    def __init__(self, zip_path):
        self.tmp = tempfile.mkdtemp(prefix="anox_archive_test_")
        self.root = Path(self.tmp)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(self.tmp)

        # Copy validator so REPO_ROOT resolves to the extracted tree
        tools_dir = self.root / "tools" / "continuity"
        (tools_dir / "validate_continuity.py").write_text(
            (REPO_ROOT / "tools" / "continuity" / "validate_continuity.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def validate(self):
        return subprocess.run(
            [sys.executable, "tools/continuity/validate_continuity.py", "--mode", "archive"],
            cwd=str(self.root),
            capture_output=True,
            text=True,
        )

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestContinuityValidator(unittest.TestCase):
    """A. new governance files are required by continuity validation."""

    def test_a_new_governance_files_required(self):
        f = LiveFixture()
        try:
            f.root.joinpath("docs/authority/CLOUD_AI_SECRET_PROTECTION.md").unlink()
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("CLOUD_AI_SECRET_PROTECTION.md", r.stdout + r.stderr)

            f._write("docs/authority/CLOUD_AI_SECRET_PROTECTION.md", "# Cloud AI Secret\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add authority"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_b_handoff_file_required(self):
        """B. official handoff generator/validator require CURRENT_HANDOFF.md."""
        f = LiveFixture()
        try:
            f.root.joinpath("docs/continuity/CURRENT_HANDOFF.md").unlink()
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("CURRENT_HANDOFF.md", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_k_inconsistent_state_detected(self):
        """K. validator catches deliberately inconsistent current-state fixture."""
        f = LiveFixture()
        try:
            f._write("PROJECT_STATE.md", "# State\n- Branch: `governance/development-security-handoff-v1`\nApproximately **27%**.\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "stale"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("stale", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_l_historical_entries_allowed(self):
        """L. historical old entries do not falsely fail current-state validation."""
        f = LiveFixture()
        try:
            f._write("docs/history/old_fortschritt.md", "Approximately **27%**.\nDevice Authentication work has not started.\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "history"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            f.cleanup()


class TestHandoffGenerator(unittest.TestCase):
    """C–I. handoff ZIP and secret preflight behavior."""

    def test_c_handoff_includes_new_governance(self):
        """C. official handoff includes the new governance files."""
        f = LiveFixture()
        try:
            r = f.generate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            names = f.list_zip()
            self.assertIn("docs/authority/CLOUD_AI_SECRET_PROTECTION.md", names)
            self.assertIn("docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md", names)
        finally:
            f.cleanup()

    def test_d_handoff_excludes_dot_git(self):
        """D. official handoff excludes .git/."""
        f = LiveFixture()
        try:
            r = f.generate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            names = f.list_zip()
            for n in names:
                self.assertFalse(n.startswith(".git/"), f"found .git/ file: {n}")
        finally:
            f.cleanup()

    def test_e_handoff_includes_bootstrap(self):
        """E. official handoff includes CURRENT_CHAT_BOOTSTRAP_PROMPT.md."""
        f = LiveFixture()
        try:
            r = f.generate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            names = f.list_zip()
            self.assertIn("docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md", names)
        finally:
            f.cleanup()

    def _assert_blocks(self, fixture_path, secret_content, reason):
        f = LiveFixture(add_synthetic_secret=fixture_path)
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add fixture"])
            r = f.generate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn(reason, r.stdout + r.stderr)
            combined = (r.stdout or "") + (r.stderr or "")
            self.assertNotIn(secret_content, combined, "secret content leaked to output")
        finally:
            f.cleanup()

    def test_f_env_blocks_handoff(self):
        """F. synthetic .env-style forbidden fixture blocks handoff."""
        self._assert_blocks("config.env", "PROD_SECRET=xyz", "forbidden file extension")

    def test_g_pem_blocks_handoff(self):
        """G. synthetic private-key PEM marker blocks handoff."""
        pem = "-----BEGIN EC PRIVATE KEY-----\nMIHcAgEBBEIA\n-----END EC PRIVATE KEY-----\n"
        f = LiveFixture()
        try:
            (f.root / "evil.txt").write_text(pem, encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add pem"])
            r = f.generate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("private-key PEM marker", r.stdout + r.stderr)
            combined = (r.stdout or "") + (r.stderr or "")
            self.assertNotIn("MIHcAgEBBEIA", combined)
        finally:
            f.cleanup()

    def test_h_keystore_blocks_handoff(self):
        """H. synthetic key/high-risk filename blocks handoff."""
        self._assert_blocks("my.key", "deadbeef", "forbidden file extension")

    def test_i_secret_not_printed(self):
        """I. secret contents are NOT reproduced in error output."""
        f = LiveFixture()
        try:
            secret = "sk_prod_1234567890abcdef"
            (f.root / "service-account.json").write_text(secret, encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add service account"])
            r = f.generate()
            self.assertNotEqual(r.returncode, 0)
            combined = (r.stdout or "") + (r.stderr or "")
            self.assertNotIn(secret, combined)
        finally:
            f.cleanup()


class TestBootstrapPrompt(unittest.TestCase):
    """J. bootstrap prompt references the new governance documents."""

    def test_j_bootstrap_references_governance(self):
        path = REPO_ROOT / "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("CLOUD_AI_SECRET_PROTECTION.md", text)
        self.assertIn("DEVELOPMENT_SECURITY_WORKFLOW_V1.md", text)
        self.assertIn("LIVE SOURCE MODE", text)
        self.assertIn("SNAPSHOT MODE", text)


class Test009RRegression(unittest.TestCase):
    """009R-A through L."""

    def test_009r_a_live_baseline_drift(self):
        """A. recorded baseline != live baseline fails."""
        f = LiveFixture(baseline_override="1111111111111111111111111111111111111111")
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "wrong baseline"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("BASELINE DRIFT", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_009r_b_live_baseline_match(self):
        """B. recorded baseline == live baseline passes."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "match"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("LIVE_GIT_VERIFICATION: PASS", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_009r_c_archive_without_git(self):
        """C. extracted handoff validates in archive mode without .git."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "generate"])
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                r2 = a.validate()
                self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: PASS", r2.stdout + r2.stderr)
                self.assertIn("LIVE_GIT_VERIFICATION: UNAVAILABLE", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    def test_009r_d_archive_tampering(self):
        """D. modified file after generation fails archive validation."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "generate"])
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                (a.root / "PROJECT_STATE.md").write_text("tampered", encoding="utf-8")
                r2 = a.validate()
                self.assertNotEqual(r2.returncode, 0, r2.stdout + r2.stderr)
                self.assertIn("hash mismatch", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    def test_009r_e_snapshot_head_mismatch(self):
        """E. mismatch between snapshot and CURRENT_STATE handoff_head fails."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "generate"])
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                state_path = a.root / "docs" / "continuity" / "CURRENT_STATE.json"
                import json
                data = json.loads(state_path.read_text(encoding="utf-8"))
                data["handoff_head"] = "0000000000000000000000000000000000000000"
                state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                r2 = a.validate()
                # Archive manifest still matches but current-state is inconsistent with snapshot
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: FAIL", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    def test_009r_g_stale_pr5_claim(self):
        """G. stale PR #5 open claim fails current-state validation."""
        f = LiveFixture(stale_claims="PR #5 open, not merged, awaiting architect review.")
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "stale pr5"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("stale PR #5 open", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_009r_h_contradictory_b003(self):
        """H. contradictory B-003 merged and open claims fail."""
        f = LiveFixture(stale_claims="B-003 client domain/state foundation open, not merged, in review.")
        try:
            # impl already says B-003 MERGED, plus the stale line creates contradiction
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "contradiction"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("contradictory B-003", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_009r_j_devin_contract_compatible(self):
        """J. output contract has A–Q with Q = NEXT RECOMMENDED GATE."""
        path = REPO_ROOT / "docs/continuity/DEVIN_OUTPUT_CONTRACT.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("A. TASK", text)
        self.assertIn("Q. NEXT RECOMMENDED GATE", text)
        self.assertIn("SECURITY CLASS", text)
        self.assertIn("CLOUD-AI SECRET STATUS", text)

    def test_009r_f_branch_mismatch(self):
        """F. recorded handoff branch does not match live branch."""
        f = LiveFixture(handoff_branch_override="main")
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "branch mismatch"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            # Validate concrete branch mismatch is reported, not merely a stale phrase
            self.assertIn("handoff_branch", r.stdout + r.stderr)
            self.assertIn("governance/development-security-handoff-v1", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_009r_i_authority_precedence_drift(self):
        """I. non-canonical authority document defines a competing precedence list."""
        f = LiveFixture(competing_precedence=True)
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "precedence drift"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            # The validator must detect a competing numbered authority list
            self.assertIn("competing numbered precedence", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_009r_k_archive_unresolved_handoff_head(self):
        """K. archive containing unresolved __HANDOFF_HEAD__ placeholder must fail."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "generate"])
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                state_path = a.root / "docs" / "continuity" / "CURRENT_STATE.json"
                import json
                data = json.loads(state_path.read_text(encoding="utf-8"))
                data["handoff_head"] = "__HANDOFF_HEAD__"
                data["working_tree"] = "__WORKING_TREE__"
                state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                r2 = a.validate()
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: FAIL", r2.stdout + r2.stderr)
                self.assertIn("UNRESOLVED HANDOFF PLACEHOLDER", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    def test_009r_l_live_resolved_placeholder_drift(self):
        """L. live validator rejects resolved current-state values that drift from live."""
        f = LiveFixture()
        try:
            # Set CURRENT_GIT_STATE.md to a concrete but wrong head
            bad_head = "0000000000000000000000000000000000000000"
            f._write(
                "docs/continuity/CURRENT_GIT_STATE.md",
                f"# Git\n- Current handoff branch: `governance/development-security-handoff-v1`\n- Current handoff HEAD: `{bad_head}`\n- Current baseline HEAD: `{f.baseline_head}`\n- Working tree: `clean`\n"
            )
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "placeholder drift"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("CURRENT_GIT_STATE.md", r.stdout + r.stderr)
        finally:
            f.cleanup()


if __name__ == "__main__":
    unittest.main()
