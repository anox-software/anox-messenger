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


class Fixture:
    """Minimal repository fixture that can run the validator and handoff generator."""

    def __init__(self, add_synthetic_secret=None):
        self.tmp = tempfile.mkdtemp(prefix="anox_handoff_test_")
        self.root = Path(self.tmp)

        # Copy current tools into the fixture so REPO_ROOT resolves correctly
        tools_dir = self.root / "tools" / "continuity"
        tools_dir.mkdir(parents=True)
        for name in ("generate_handoff.py", "validate_continuity.py"):
            src = REPO_ROOT / "tools" / "continuity" / name
            dst = tools_dir / name
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

        # Required authority / continuity files (minimal contents)
        self._write("docs/authority/AUTHORITY_INDEX.md", "# Authority Index\n")
        self._write("docs/authority/CLOUD_AI_SECRET_PROTECTION.md", "# Cloud AI Secret\n")
        self._write("docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md", "# Workflow\n")
        self._write("docs/authority/B025/SECURITY_INVARIANTS_V1_1.md", "# Invariants\n")
        self._write("docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md", "# B026\n")
        self._write("docs/authority/B_FREEZE_REGISTRY.md", "# Freeze\n")
        self._write("docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md", "# Arch\n")

        self._write("docs/continuity/AUTHORITY_INDEX.md", "# C-Authority\n")
        self._write("docs/continuity/CURRENT_HANDOFF.md", self._handoff_md())
        self._write("docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md", "# Bootstrap\nDEVELOPMENT_SECURITY_WORKFLOW_V1.md\n")
        self._write("docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md", "# Upload\n")
        self._write("docs/continuity/CURRENT_IMPLEMENTATION_STATE.md", "# Impl\n")
        self._write("docs/continuity/CURRENT_GIT_STATE.md", self._git_state_md())
        self._write("docs/continuity/CURRENT_OPEN_WORK.md", "# Open\n")
        self._write("docs/continuity/CURRENT_NEXT_DEVIN_TASK.md", "# Next\nDEVELOPMENT SECURITY GOVERNANCE / HANDOFF HARDENING\n")
        self._write("docs/continuity/DEVIN_OUTPUT_CONTRACT.md", "# Contract\n")
        self._write("docs/continuity/HANDOFF_WORKFLOW.md", "# Workflow\n")
        self._write("docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md", "# Checklist\n")
        self._write("docs/continuity/CURRENT_STATE.json", self._state_json())
        self._write("PROJECT_STATE.md", "# State\n- Branch: `governance/development-security-handoff-v1`\nB-002 merged.\n")
        self._write("FORTSCHRITT.md", "# Fortschritt\nApproximately **33%**.\nB-003 merged.\n")
        self._write("DEVIN_PROMPT_OUTPUT_ARCHIV.md", "# Archive\n")
        self._write("tools/security/validate_apk_contents.py", "# APK validator\n")

        # Git init
        self._run(["git", "init"])
        self._run(["git", "config", "user.email", "test@anox.local"])
        self._run(["git", "config", "user.name", "Test"])
        self._run(["git", "checkout", "-b", "governance/development-security-handoff-v1"])
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", "init"])

        if add_synthetic_secret:
            (self.root / add_synthetic_secret).write_text("synthetic secret fixture", encoding="utf-8")

    def _write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _handoff_md(self):
        return (
            "# Handoff\n"
            "- Current work branch: `governance/development-security-handoff-v1`\n"
            "- Merged baseline HEAD: `e7ee54a713e08950c63cf2d61ec97931864b66bc`\n"
        )

    def _git_state_md(self):
        return (
            "# Git\n"
            "- Current handoff branch: `governance/development-security-handoff-v1`\n"
            "- Merged baseline HEAD: `e7ee54a713e08950c63cf2d61ec97931864b66bc`\n"
        )

    def _state_json(self):
        return (
            '{\n'
            '  "schema_version": "B026-1.0",\n'
            '  "handoff_branch": "governance/development-security-handoff-v1",\n'
            '  "baseline_head": "e7ee54a713e08950c63cf2d61ec97931864b66bc",\n'
            '  "continuity_001_status": "ACCEPTED",\n'
            '  "security_invariants_path": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",\n'
            '  "freeze_registry_path": "docs/authority/B_FREEZE_REGISTRY.md",\n'
            '  "current_task": "DEVELOPMENT SECURITY GOVERNANCE / HANDOFF HARDENING",\n'
            '  "current_gate": "DEVELOPMENT SECURITY GOVERNANCE / HANDOFF HARDENING"\n'
            '}\n'
        )

    def _run(self, cmd, **kw):
        kw.setdefault("cwd", str(self.root))
        kw.setdefault("capture_output", True)
        kw.setdefault("text", True)
        return subprocess.run(cmd, **kw)

    def validate(self):
        return self._run([sys.executable, "tools/continuity/validate_continuity.py"])

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


class TestContinuityValidator(unittest.TestCase):
    """A. new governance files are required by continuity validation."""

    def test_a_new_governance_files_required(self):
        f = Fixture()
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
        f = Fixture()
        try:
            f.root.joinpath("docs/continuity/CURRENT_HANDOFF.md").unlink()
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("CURRENT_HANDOFF.md", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_k_inconsistent_state_detected(self):
        """K. validator catches deliberately inconsistent current-state fixture."""
        f = Fixture()
        try:
            # Introduce a stale phrase in the current FORTSCHRITT
            f._write("FORTSCHRITT.md", "# Fortschritt\nApproximately **27%**.\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "stale"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("stale", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_l_historical_entries_allowed(self):
        """L. historical old entries do not falsely fail current-state validation."""
        f = Fixture()
        try:
            # Put the stale phrase in a historical-only file, not current surfaces
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
        f = Fixture()
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
        f = Fixture()
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
        f = Fixture()
        try:
            r = f.generate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            names = f.list_zip()
            self.assertIn("docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md", names)
        finally:
            f.cleanup()

    def _assert_blocks(self, fixture_path, secret_content, reason):
        f = Fixture(add_synthetic_secret=fixture_path)
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
        f = Fixture()
        try:
            # .pem extension is forbidden; use an unblocked extension with PEM content
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
        # Combined assertion in F/G/H; explicit standalone with sensitive token
        f = Fixture()
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


if __name__ == "__main__":
    unittest.main()
