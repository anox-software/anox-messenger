#!/usr/bin/env python3
"""Focused tests for the handoff generator and continuity validator."""

import json
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

        # Historical provenance file with stale phrases. It must not falsely fail
        # current-state validation because stale-phrase checks do not scan docs/history/.
        self._write(
            "docs/history/old_fortschritt.md",
            "Approximately **27%**.\nDevice Authentication work has not started.\n",
        )

    def _impl_md(self, stale_claims=None):
        base = "# Impl\nB-002 MERGED.\nB-003 MERGED FOUNDATION.\n"
        if stale_claims:
            base += stale_claims + "\n"
        return base

    def _write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _handoff_md(self, described_head, handoff_branch=None):
        branch = handoff_branch or "governance/development-security-handoff-v1"
        return (
            "# Handoff\n"
            f"- Current work branch: `{branch}`\n"
            f"- Described HEAD: `{described_head}`\n"
        )

    def _git_state_md(self, described_head, handoff_branch=None):
        branch = handoff_branch or "governance/development-security-handoff-v1"
        return (
            "# Git\n"
            f"- Current handoff branch: `{branch}`\n"
            f"- Described HEAD: `{described_head}`\n"
        )

    def _state_json(self, described_head, handoff_branch=None):
        branch = handoff_branch or "governance/development-security-handoff-v1"
        return (
            '{\n'
            '  "schema_version": "B026-1.0",\n'
            f'  "handoff_branch": "{branch}",\n'
            '  "handoff_head": "__HANDOFF_HEAD__",\n'
            f'  "baseline_branch": "main",\n'
            f'  "described_head": "{described_head}",\n'
            '  "working_tree": "__WORKING_TREE__",\n'
            '  "continuity_001_status": "ACCEPTED",\n'
            '  "security_invariants_path": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",\n'
            '  "freeze_registry_path": "docs/authority/B_FREEZE_REGISTRY.md",\n'
            '  "current_task": "PROMPT-009 GOVERNANCE REMEDIATION / REVIEW",\n'
            '  "current_gate": "PROMPT-009 GOVERNANCE REMEDIATION / REVIEW",\n'
            f'  "latest_merge_to_baseline": "{described_head}",\n'
            f'  "previous_baseline_head": "{described_head}"\n'
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
        """A. recorded described_head not an ancestor of live HEAD fails."""
        f = LiveFixture(baseline_override="1111111111111111111111111111111111111111")
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "wrong baseline"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("described_head", r.stdout + r.stderr)
            self.assertIn("not an ancestor", r.stdout + r.stderr)
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


import validate_continuity as vc


class TestDescribedHeadSemantics(unittest.TestCase):
    """PRE-B027-0: described_head semantics, metadata-only advancement, and self-reference regression."""

    def test_case_1_equal_heads(self):
        """1. live_head == described_head -> PASS."""
        same = "0" * 40
        result = vc.validate_described_head(same, same, Path("."), True, "TEST")
        self.assertTrue(result)

    def test_case_2_metadata_only_advance(self):
        """2. described_head is an ancestor and only metadata files changed -> PASS."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            described = f.baseline_head
            live = f._run(["git", "rev-parse", "HEAD"]).stdout.strip()
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertNotEqual(described, live)
            self.assertIn("METADATA-ONLY", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_case_3_product_code_change(self):
        """3. Product code change after described_head -> FAIL."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            evil = f.root / "android" / "src" / "main" / "java" / "com" / "anox" / "messenger" / "Evil.kt"
            evil.parent.mkdir(parents=True, exist_ok=True)
            evil.write_text("// product code\n", encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add product code"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn(str(evil.relative_to(f.root)), r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_case_4_ci_workflow_change(self):
        """4. CI workflow change after described_head -> FAIL."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            ci = f.root / ".github" / "workflows" / "ci.yml"
            ci.parent.mkdir(parents=True, exist_ok=True)
            ci.write_text("name: ci\n", encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add ci"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn(".github/workflows/ci.yml", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_case_5_authority_change(self):
        """5. Authority file change after described_head -> FAIL."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            ai = f.root / "docs" / "authority" / "AUTHORITY_INDEX.md"
            ai.write_text("# changed\n", encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "change authority"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn("AUTHORITY_INDEX.md", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_case_6_validator_change(self):
        """6. Validator/tool code change after described_head -> FAIL."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            sec = f.root / "tools" / "security" / "validate_apk_contents.py"
            sec.write_text("# changed\n", encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "change tool"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn("tools/security/validate_apk_contents.py", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_case_7_unknown_file(self):
        """7. Unknown file change after described_head -> FAIL."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            evil = f.root / "evil.txt"
            evil.write_text("unknown\n", encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "unknown file"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn("evil.txt", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_case_9_malformed_sha(self):
        """9. malformed described_head -> FAIL."""
        f = LiveFixture(baseline_override="notavalidsha")
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "malformed"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("not a valid 40-char", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_case_10_unresolved_placeholder(self):
        """10. unresolved placeholder described_head -> FAIL."""
        f = LiveFixture(baseline_override="__HANDOFF_HEAD__")
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "placeholder"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("not a valid 40-char", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_no_self_reference_required(self):
        """Regression: a tracked state file no longer needs to contain its own future commit SHA."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            # live_head is a descendant, not equal to described_head, yet validation passes.
            self.assertIn("METADATA-ONLY", r.stdout + r.stderr)
        finally:
            f.cleanup()


class TestRenameAndPrefixSecurity(unittest.TestCase):
    """ANOX-PREB027REV-001, -003, -010: rename and historical-prefix bypass tests."""

    def _run_rename_scenario(self, source_rel, dest_rel, source_text="substantive\n"):
        """Create source, commit, rename to dest, commit; expect validation FAIL."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            (f.root / source_rel).parent.mkdir(parents=True, exist_ok=True)
            (f.root / source_rel).write_text(source_text, encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add source"])
            (f.root / dest_rel).parent.mkdir(parents=True, exist_ok=True)
            f._run(["git", "mv", source_rel, dest_rel])
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "rename"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_rename_ci_to_history_fails(self):
        """Rename .github/workflows/ci.yml into docs/history/ fails."""
        self._run_rename_scenario(".github/workflows/ci.yml", "docs/history/ci.yml")

    def test_rename_product_to_history_fails(self):
        """Rename product source into docs/history/ fails."""
        self._run_rename_scenario("android/src/Foo.kt", "docs/history/Foo.kt")

    def test_rename_tool_to_history_fails(self):
        """Rename tool into docs/history/ fails."""
        self._run_rename_scenario(
            "tools/continuity/evil.py", "docs/history/evil.py"
        )

    def test_rename_authority_to_history_fails(self):
        """Rename authority file into docs/history/ fails."""
        self._run_rename_scenario(
            "docs/authority/NEW_POLICY.md", "docs/history/NEW_POLICY.md"
        )

    def _add_file_and_expect_substantive(self, rel, content="content\n"):
        """Add a file after described_head and expect validation to fail."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            f._write(rel, content)
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add file"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_history_arbitrary_markdown_fails(self):
        self._add_file_and_expect_substantive("docs/history/ARBITRARY_SECURITY_INSTRUCTIONS.md")

    def test_history_arbitrary_nested_fails(self):
        self._add_file_and_expect_substantive("docs/history/foo/bar/unexpected.md")

    def test_history_arbitrary_script_fails(self):
        self._add_file_and_expect_substantive("docs/history/evil.py", "print('evil')\n")

    def test_history_arbitrary_shell_fails(self):
        self._add_file_and_expect_substantive("docs/history/evil.sh", "#!/bin/sh\nexit\n")

    def test_history_arbitrary_js_fails(self):
        self._add_file_and_expect_substantive("docs/history/deploy.js", "console.log(1);\n")

    def test_historical_handoff_zip_fails(self):
        self._add_file_and_expect_substantive(
            "docs/continuity/HISTORICAL_HANDOFFS/anything.zip", b"PK\x00".decode("latin-1")
        )

    def test_historical_handoff_nested_script_fails(self):
        self._add_file_and_expect_substantive(
            "docs/continuity/HISTORICAL_HANDOFFS/sub/dir/x.py", "print(1)\n"
        )

    def test_git_diff_files_exposes_rename_sides(self):
        """--no-renames causes git_diff_files to return both sides of a rename."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            f._write(".github/workflows/ci.yml", "name: ci\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add ci"])
            (f.root / "docs/history").mkdir(parents=True, exist_ok=True)
            f._run(["git", "mv", ".github/workflows/ci.yml", "docs/history/ci.yml"])
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "rename"])
            live = f._run(["git", "rev-parse", "HEAD"]).stdout.strip()
            changed = vc.git_diff_files(f.baseline_head, live, cwd=str(f.root))
            self.assertIn(".github/workflows/ci.yml", changed)
            self.assertIn("docs/history/ci.yml", changed)
        finally:
            f.cleanup()


class TestArchiveRequiredKeys(unittest.TestCase):
    """ANOX-PREB027REV-002, -010: archive mode must enforce mandatory state keys."""

    @staticmethod
    def _recompute_sha_manifest(archive_root):
        """Recompute SHA256_MANIFEST.txt entries for CURRENT_STATE.json after editing it."""
        import hashlib
        sha_manifest_path = archive_root / "SHA256_MANIFEST.txt"
        rel = "docs/continuity/CURRENT_STATE.json"
        new_digest = hashlib.sha256((archive_root / rel).read_bytes()).hexdigest()
        lines = []
        for line in sha_manifest_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                lines.append(line)
                continue
            parts = line.split(None, 1)
            if len(parts) == 2 and parts[1] == rel:
                lines.append(f"{new_digest}  {rel}")
            else:
                lines.append(line)
        sha_manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _archive_missing_key(self, key_to_remove):
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "generate"])
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                import json
                state_path = a.root / "docs" / "continuity" / "CURRENT_STATE.json"
                data = json.loads(state_path.read_text(encoding="utf-8"))
                data.pop(key_to_remove, None)
                state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                self._recompute_sha_manifest(a.root)
                r2 = a.validate()
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: FAIL", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    def test_archive_missing_current_gate_fails(self):
        self._archive_missing_key("current_gate")

    def test_archive_missing_security_invariants_path_fails(self):
        self._archive_missing_key("security_invariants_path")

    def test_archive_missing_freeze_registry_path_fails(self):
        self._archive_missing_key("freeze_registry_path")

    def test_archive_missing_described_and_baseline_head_fails(self):
        self._archive_missing_key("described_head")

    def test_archive_legacy_baseline_head_allowed(self):
        """Archive with legacy baseline_head but no described_head still passes."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "generate"])
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                import json
                state_path = a.root / "docs" / "continuity" / "CURRENT_STATE.json"
                data = json.loads(state_path.read_text(encoding="utf-8"))
                data["baseline_head"] = data.pop("described_head")
                state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                self._recompute_sha_manifest(a.root)
                r2 = a.validate()
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: PASS", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()


class TestMissingHeadDeclaration(unittest.TestCase):
    """ANOX-PREB027REV-009, -010: current continuity surfaces must declare described_head."""

    def _missing_declaration(self, rel, content):
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            f._write(rel, content)
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "remove head declaration"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("does not declare described_head", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_handoff_missing_described_head_fails(self):
        self._missing_declaration(
            "docs/continuity/CURRENT_HANDOFF.md",
            "# Handoff\n- Current work branch: `governance/development-security-handoff-v1`\n",
        )

    def test_git_state_missing_described_head_fails(self):
        self._missing_declaration(
            "docs/continuity/CURRENT_GIT_STATE.md",
            "# Git\n- Current handoff branch: `governance/development-security-handoff-v1`\n",
        )

    def test_git_state_legacy_baseline_decl_passes(self):
        """Legacy 'Current baseline HEAD' declaration remains accepted."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            f._write(
                "docs/continuity/CURRENT_GIT_STATE.md",
                f"# Git\n- Current handoff branch: `governance/development-security-handoff-v1`\n"
                f"- Current baseline HEAD: `{f.baseline_head}`\n",
            )
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "legacy baseline declaration"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            f.cleanup()


class TestBaselineAncestry(unittest.TestCase):
    """ANOX-PREB027REV-004, -010: non-self-referential baseline ancestry."""

    def _main_head(self):
        r = subprocess.run(
            ["git", "rev-parse", "main"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        return r.stdout.strip()

    def test_valid_ancestors_pass(self):
        main = self._main_head()
        state = {
            "latest_merge_to_baseline": "043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff",
            "previous_baseline_head": "043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff",
        }
        result = vc.validate_baseline_ancestry(state, main, True, "TEST")
        self.assertTrue(result)

    def test_unrelated_sha_fails(self):
        main = self._main_head()
        state = {
            "latest_merge_to_baseline": "1111111111111111111111111111111111111111",
        }
        result = vc.validate_baseline_ancestry(state, main, True, "TEST")
        self.assertFalse(result)

    def test_malformed_sha_fails(self):
        main = self._main_head()
        state = {
            "latest_merge_to_baseline": "notavalidsha",
        }
        result = vc.validate_baseline_ancestry(state, main, True, "TEST")
        self.assertFalse(result)

    def test_nonexistent_sha_fails(self):
        main = self._main_head()
        state = {
            "latest_merge_to_baseline": "0000000000000000000000000000000000000000",
        }
        result = vc.validate_baseline_ancestry(state, main, True, "TEST")
        self.assertFalse(result)

    def test_invalid_order_fails(self):
        main = self._main_head()
        state = {
            "latest_merge_to_baseline": "043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff",
            "previous_baseline_head": main,
        }
        result = vc.validate_baseline_ancestry(state, main, True, "TEST")
        self.assertFalse(result)


class TestHeadPrecedence(unittest.TestCase):
    """ANOX-PREB027REV-008, -010: described_head wins over legacy baseline_head."""

    def test_resolve_described_head_precedence(self):
        self.assertEqual(
            vc._resolve_described_head({"described_head": "a" * 40, "baseline_head": "b" * 40}),
            "a" * 40,
        )
        self.assertEqual(
            vc._resolve_described_head({"baseline_head": "b" * 40}),
            "b" * 40,
        )

    def test_generator_prefers_described_head(self):
        """If baseline branch does not resolve, generator manifest falls back to described_head."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            described = "a68eca5248f1ab315c34ba00387030bfd58c138e"
            fallback = "1111111111111111111111111111111111111111"
            f._write(
                "docs/continuity/CURRENT_STATE.json",
                '{'
                f'"handoff_branch": "governance/development-security-handoff-v1",'
                f'"described_head": "{described}",'
                f'"baseline_head": "{fallback}",'
                f'"baseline_branch": "nonexistent-branch",'
                '"security_invariants_path": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",'
                '"freeze_registry_path": "docs/authority/B_FREEZE_REGISTRY.md",'
                '"current_gate": "TEST",'
                '"continuity_001_status": "ACCEPTED"'
                '}\n',
            )
            # Also update handoff surface to match described_head
            f._write(
                "docs/continuity/CURRENT_HANDOFF.md",
                "# Handoff\n- Current work branch: `governance/development-security-handoff-v1`\n"
                f"- Described HEAD: `{described}`\n",
            )
            f._write(
                "docs/continuity/CURRENT_GIT_STATE.md",
                "# Git\n- Current handoff branch: `governance/development-security-handoff-v1`\n"
                f"- Described HEAD: `{described}`\n",
            )
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "precedence"])
            r = f.generate(emergency=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            names = f.list_zip()
            with zipfile.ZipFile(f.zip_path()) as zf:
                manifest = zf.read("MANIFEST.txt").decode("utf-8")
            self.assertIn(f"Baseline HEAD: {described}", manifest)
            self.assertNotIn(f"Baseline HEAD: {fallback}", manifest)
        finally:
            f.cleanup()


class TestMergeCommitSecurity(unittest.TestCase):
    """ANOX-PREB027RREV-001: merge commit classification must not hide substantive work."""

    def test_merge_resolution_product_change_fails(self):
        """Substantive Product code introduced only in merge resolution fails."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            # Create two side branches, each with an allowed metadata-only change
            f._run(["git", "checkout", "-b", "side-a"])
            f._write("FORTSCHRITT.md", "# Fortschritt\nside A metadata\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "side a metadata"])
            f._run(["git", "checkout", "governance/development-security-handoff-v1"])
            f._run(["git", "checkout", "-b", "side-b"])
            f._write("PROJECT_STATE.md", "# State\n- Branch: `governance/development-security-handoff-v1`\nside B metadata\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "side b metadata"])
            f._run(["git", "checkout", "governance/development-security-handoff-v1"])
            # Prepare a no-ff merge and inject product code during the merge resolution
            subprocess.run(
                ["git", "merge", "--no-commit", "--no-ff", "side-a"],
                cwd=f.root, check=False, capture_output=True, text=True
            )
            subprocess.run(
                ["git", "merge", "--no-commit", "--no-ff", "side-b"],
                cwd=f.root, check=False, capture_output=True, text=True
            )
            evil = f.root / "android" / "src" / "main" / "java" / "com" / "anox" / "messenger" / "Evil.kt"
            evil.parent.mkdir(parents=True, exist_ok=True)
            evil.write_text("// product merge payload\n", encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "merge with product payload"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn(str(evil.relative_to(f.root)), r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_merge_then_revert_substantive_still_fails(self):
        """Substantive work introduced in merge and reverted later is still detected."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            f._run(["git", "checkout", "-b", "side"])
            f._write("FORTSCHRITT.md", "# Fortschritt\nside metadata\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "side metadata"])
            f._run(["git", "checkout", "governance/development-security-handoff-v1"])
            subprocess.run(
                ["git", "merge", "--no-commit", "--no-ff", "side"],
                cwd=f.root, check=False, capture_output=True, text=True
            )
            evil = f.root / "android" / "src" / "main" / "java" / "com" / "anox" / "messenger" / "Evil.kt"
            evil.parent.mkdir(parents=True, exist_ok=True)
            evil.write_text("// transient product payload\n", encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "merge with transient product payload"])
            merge = f._run(["git", "rev-parse", "HEAD"]).stdout.strip()
            # Revert the merge-introduced product file in an ordinary follow-up commit
            f._run(["git", "rm", "-f", str(evil.relative_to(f.root))])
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "revert product change"])
            # Endpoint diff from described to HEAD no longer contains the product file,
            # but the full-range scan must still detect it.
            ep = subprocess.run(
                ["git", "diff", "--name-only", f.baseline_head, "HEAD"],
                cwd=f.root, capture_output=True, text=True
            ).stdout.split()
            self.assertNotIn(str(evil.relative_to(f.root)), ep)
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn(str(evil.relative_to(f.root)), r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_clean_metadata_only_merge_passes(self):
        """Two metadata-only branches merged with no substantive resolution pass."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            f._run(["git", "checkout", "-b", "side-a"])
            f._write("FORTSCHRITT.md", "# Fortschritt\nside A\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "side a metadata"])
            f._run(["git", "checkout", "governance/development-security-handoff-v1"])
            f._run(["git", "checkout", "-b", "side-b"])
            f._write("PROJECT_STATE.md", "# State\n- Branch: `governance/development-security-handoff-v1`\nside B\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "side b metadata"])
            f._run(["git", "checkout", "governance/development-security-handoff-v1"])
            # Merge both branches with a clean, no-conflict resolution (no extra files)
            for side in ("side-a", "side-b"):
                subprocess.run(
                    ["git", "merge", "--no-commit", "--no-ff", side],
                    cwd=f.root, check=False, capture_output=True, text=True
                )
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "merge metadata branches"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("METADATA-ONLY", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_substantive_branch_merged_fails(self):
        """A branch containing substantive Product code, merged cleanly, fails."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            f._run(["git", "checkout", "-b", "feature"])
            evil = f.root / "android" / "src" / "main" / "java" / "com" / "anox" / "messenger" / "Evil.kt"
            evil.parent.mkdir(parents=True, exist_ok=True)
            evil.write_text("// feature product code\n", encoding="utf-8")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "feature with product code"])
            f._run(["git", "checkout", "governance/development-security-handoff-v1"])
            subprocess.run(
                ["git", "merge", "--no-ff", "feature"],
                cwd=f.root, check=False, capture_output=True, text=True
            )
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn(str(evil.relative_to(f.root)), r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_merge_resolution_into_allowlist_fails(self):
        """Merge resolution that renames substantive work into allowlisted path still fails."""
        f = LiveFixture()
        try:
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync"])
            # Put a substantive file on a feature branch
            f._run(["git", "checkout", "-b", "feature"])
            f._write("docs/authority/NEW_POLICY.md", "# New policy\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add authority proposal"])
            f._run(["git", "checkout", "governance/development-security-handoff-v1"])
            # Prepare merge, then rename the authority file into an allowlisted metadata filename
            subprocess.run(
                ["git", "merge", "--no-commit", "--no-ff", "feature"],
                cwd=f.root, check=False, capture_output=True, text=True
            )
            f._run(["git", "rm", "-f", "docs/authority/NEW_POLICY.md"])
            f._write("docs/continuity/CURRENT_OPEN_WORK.md", "# Open\nmerge-resolved evil\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "merge and route into allowlist"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn("docs/authority/NEW_POLICY.md", r.stdout + r.stderr)
        finally:
            f.cleanup()


class CMLFixture:
    """Real-Git fixture for canonical merge lifecycle tests."""

    DUMMY_SHA = "0" * 40

    def __init__(self, pre_merge_gate="CML PRE-MERGE GATE", post_merge_gate="CML POST-MERGE GATE"):
        self.tmp = tempfile.mkdtemp(prefix="anox_cml_test_")
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

        self.pre_merge_gate = pre_merge_gate
        self.post_merge_gate = post_merge_gate
        self.delivery_branch = "delivery"
        self._setup_files()

        self._run(["git", "init"])
        self._run(["git", "config", "user.email", "test@anox.local"])
        self._run(["git", "config", "user.name", "Test"])

        self._run(["git", "checkout", "-b", "main"])
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", "base"])
        self.base = self._run(["git", "rev-parse", "main"]).stdout.strip()

        # Delivery branch starts with a substantive lifecycle payload.
        self._run(["git", "checkout", "-b", "delivery"])
        self._write("docs/continuity/CML_SUBSTANTIVE.md", "# Canonical merge lifecycle\n")
        self._run(["git", "add", "."])
        r = self._run(["git", "commit", "-m", "delivery init"])
        if r.returncode != 0:
            raise RuntimeError(f"delivery init commit failed: {r.stderr}")
        self.described = self._run(["git", "rev-parse", "delivery"]).stdout.strip()

        # Metadata-only state sync sets the real described_head.
        self._write_state()
        self._write_git_state_md()
        self._write_handoff_md()
        self._write_project_state_md("delivery")
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", "delivery state sync"])
        self.delivery_head = self._run(["git", "rev-parse", "delivery"]).stdout.strip()

    def _setup_files(self):
        self._write(
            "docs/authority/AUTHORITY_INDEX.md",
            "# Authority Index\n## Precedence\n1. `B025/SECURITY_INVARIANTS_V1_1.md`\n## Canonical source\nThis file is canonical.\n",
        )
        self._write("docs/authority/CLOUD_AI_SECRET_PROTECTION.md", "# Cloud AI Secret\n")
        self._write("docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md", "# Workflow\n")
        self._write("docs/authority/B025/SECURITY_INVARIANTS_V1_1.md", "# Invariants\n")
        self._write("docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md", "# B026\n")
        self._write("docs/authority/B_FREEZE_REGISTRY.md", "# Freeze\n")
        self._write("docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md", "# Arch\n")

        self._write("docs/continuity/AUTHORITY_INDEX.md", "# C-Authority\n")
        self._write("docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md", "# Bootstrap\n")
        self._write("docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md", "# Upload\n")
        self._write("docs/continuity/CURRENT_IMPLEMENTATION_STATE.md", "# Impl\nCML TEST\n")
        self._write("docs/continuity/CURRENT_OPEN_WORK.md", "# Open\n")
        self._write("docs/continuity/CURRENT_NEXT_DEVIN_TASK.md", "# Next\n")
        self._write("docs/continuity/DEVIN_OUTPUT_CONTRACT.md", "# Contract\n")
        self._write("docs/continuity/HANDOFF_WORKFLOW.md", "# Workflow\n")
        self._write("docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md", "# Checklist\n")
        self._write("FORTSCHRITT.md", "# Fortschritt\nCML TEST\n")
        self._write("DEVIN_PROMPT_OUTPUT_ARCHIV.md", "# Archive\n")

    def _write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _state_json(self):
        return (
            "{\n"
            '  "schema_version": "B026-1.2",\n'
            '  "handoff_branch": "__HANDOFF_BRANCH__",\n'
            '  "handoff_head": "__HANDOFF_HEAD__",\n'
            '  "canonical_branch": "main",\n'
            f'  "delivery_branch": "{self.delivery_branch}",\n'
            f'  "described_head": "{self.described}",\n'
            '  "working_tree": "__WORKING_TREE__",\n'
            '  "continuity_001_status": "ACCEPTED",\n'
            '  "current_task": "CML TEST",\n'
            '  "current_gate": "__EFFECTIVE_GATE__",\n'
            f'  "pre_merge_gate": "{self.pre_merge_gate}",\n'
            f'  "post_merge_gate": "{self.post_merge_gate}",\n'
            '  "security_invariants_path": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",\n'
            '  "freeze_registry_path": "docs/authority/B_FREEZE_REGISTRY.md",\n'
            f'  "latest_merge_to_baseline": "{self.base}",\n'
            f'  "previous_baseline_head": "{self.base}"\n'
            "}\n"
        )

    def _git_state_md(self):
        return (
            "# Git\n"
            "- Canonical branch: `main`\n"
            f"- Delivery branch: `{self.delivery_branch}`\n"
            "- Current handoff branch: `__HANDOFF_BRANCH__`\n"
            "- Current handoff HEAD: `__HANDOFF_HEAD__`\n"
            f"- Described HEAD: `{self.described}`\n"
            "- Working tree: `__WORKING_TREE__`\n"
            "- Current gate: `__EFFECTIVE_GATE__`\n"
            f"- Pre-merge gate: `__PRE_MERGE_GATE__`\n"
            f"- Post-merge gate: `__POST_MERGE_GATE__`\n"
        )

    def _handoff_md(self, work_branch="delivery"):
        return (
            "# Handoff\n"
            "- Canonical branch: `main`\n"
            f"- Delivery branch: `{self.delivery_branch}`\n"
            f"- Current work branch: `{work_branch}`\n"
            f"- Described HEAD: `{self.described}`\n"
            f"- Pre-merge gate: `{self.pre_merge_gate}`\n"
            f"- Post-merge gate: `{self.post_merge_gate}`\n"
        )

    def _project_state_md(self, branch):
        return f"# State\n- Branch: `{branch}`\n"

    def _write_state(self):
        self._write("docs/continuity/CURRENT_STATE.json", self._state_json())

    def _write_git_state_md(self):
        self._write("docs/continuity/CURRENT_GIT_STATE.md", self._git_state_md())

    def _write_handoff_md(self, work_branch="delivery"):
        self._write("docs/continuity/CURRENT_HANDOFF.md", self._handoff_md(work_branch))

    def _write_project_state_md(self, branch):
        self._write("PROJECT_STATE.md", self._project_state_md(branch))

    def _run(self, cmd, **kw):
        kw.setdefault("cwd", str(self.root))
        kw.setdefault("capture_output", True)
        kw.setdefault("text", True)
        return subprocess.run(cmd, **kw)

    def commit_meta(self, msg, rel="FORTSCHRITT.md", text="metadata update\n"):
        path = self.root / rel
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", msg])

    def checkout(self, branch):
        self._run(["git", "checkout", branch])

    def set_described_head(self, sha):
        """Update described_head to the given SHA and commit the metadata sync."""
        self.described = sha
        self._write_state()
        self._write_git_state_md()
        self._write_handoff_md()
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", "set described_head"])

    def merge_no_ff(self, branch, msg, resolution_payload=None):
        r = self._run(["git", "merge", "--no-ff", "--no-commit", branch])
        if resolution_payload:
            for rel, content in resolution_payload.items():
                path = self.root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                self._run(["git", "add", "."])
        r2 = self._run(["git", "commit", "-m", msg])
        return r2

    def validate(self, mode="live"):
        return self._run([sys.executable, "tools/continuity/validate_continuity.py", "--mode", mode])

    def generate(self, emergency=False):
        return self._run([sys.executable, "tools/continuity/generate_handoff.py"] + (["--emergency"] if emergency else []))

    def head(self, branch):
        return self._run(["git", "rev-parse", branch]).stdout.strip()

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def zip_path(self):
        artifacts = sorted(self.root.glob("artifacts/handoff/*.zip"))
        return artifacts[0] if artifacts else None


class TestCanonicalMergeLifecycle(unittest.TestCase):
    """ANOX-CMLREV-001: automated canonical merge lifecycle tests."""

    # 1. delivery context normal PASS
    def test_delivery_context_metadata_only_passes(self):
        f = CMLFixture()
        try:
            f.commit_meta("metadata tail")
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("delivery context", r.stdout + r.stderr)
            self.assertIn(f.pre_merge_gate, r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 2. clean canonical --no-ff merge PASS
    def test_clean_canonical_merge_passes(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            r = f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            f._write_project_state_md("main")
            f._write_handoff_md("main")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "--amend", "--no-edit"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("canonical merge transition verified", r.stdout + r.stderr)
            self.assertIn(f.post_merge_gate, r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 3. clean canonical merge requires NO reconciliation commit
    def test_clean_merge_no_reconciliation_commit(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            # Direct pass, no extra metadata reconciliation needed.
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 4. Product merge-resolution payload FAIL
    def test_product_merge_resolution_payload_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f.merge_no_ff(
                "delivery",
                "merge with product payload",
                resolution_payload={
                    "android/src/main/java/com/anox/messenger/Evil.kt": "// evil\n"
                },
            )
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 5. CI merge-resolution payload FAIL
    def test_ci_merge_resolution_payload_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f.merge_no_ff(
                "delivery",
                "merge with ci payload",
                resolution_payload={".github/workflows/evil.yml": "name: evil\n"},
            )
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn("evil.yml", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 6. Authority merge-resolution payload FAIL
    def test_authority_merge_resolution_payload_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f.merge_no_ff(
                "delivery",
                "merge with authority payload",
                resolution_payload={"docs/authority/NEW_POLICY.md": "# evil\n"},
            )
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn("NEW_POLICY.md", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 7. Tool/validator merge-resolution payload FAIL
    def test_tool_merge_resolution_payload_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f.merge_no_ff(
                "delivery",
                "merge with tool payload",
                resolution_payload={"tools/security/validate_apk_contents.py": "# evil\n"},
            )
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
            self.assertIn("validate_apk_contents.py", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 8. substantive deletion during merge resolution FAIL
    def test_deletion_merge_resolution_fails(self):
        f = CMLFixture()
        try:
            # Add a substantive file on delivery before the described point is not possible.
            # Instead, create a side branch from delivery, add a file, merge side into delivery,
            # then merge delivery into main and delete the file during the main merge.
            f._run(["git", "checkout", "-b", "side"])
            f._write("android/src/Foo.kt", "// foo\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "side file"])
            f._run(["git", "checkout", "delivery"])
            f._run(["git", "merge", "--no-ff", "-m", "merge side", "side"])
            # The file is now in the reviewed delivery ancestry.
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "--no-commit", "delivery"])
            f._run(["git", "rm", "-f", "android/src/Foo.kt"])
            f._run(["git", "commit", "-m", "merge with deletion"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 9. explicitly permitted metadata-only merge-resolution PASS
    def test_metadata_only_merge_resolution_passes(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f.merge_no_ff(
                "delivery",
                "merge with metadata resolution",
                resolution_payload={"FORTSCHRITT.md": "merge resolved\n"},
            )
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 10. substantive delivery tail after described_head FAIL
    def test_substantive_delivery_tail_fails(self):
        f = CMLFixture()
        try:
            f._write("android/src/Evil.kt", "// evil\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "product tail"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 11. ordinary substantive intermediate commit then revert FAIL
    def test_intermediate_product_then_revert_fails(self):
        f = CMLFixture()
        try:
            f._write("android/src/Evil.kt", "// evil\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add evil"])
            f._run(["git", "rm", "-f", "android/src/Evil.kt"])
            f._run(["git", "commit", "-m", "revert evil"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 12. merge intermediate substantive payload then revert FAIL
    def test_merge_intermediate_payload_then_revert_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "--no-commit", "delivery"])
            f._write("android/src/Evil.kt", "// transient\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "merge with transient product"])
            f._run(["git", "rm", "-f", "android/src/Evil.kt"])
            f._run(["git", "commit", "-m", "revert product"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 13. rename bypass remains closed
    def test_rename_bypass_fails(self):
        f = CMLFixture()
        try:
            f._write(".github/workflows/ci.yml", "name: ci\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "add ci"])
            (f.root / "docs/history").mkdir(parents=True, exist_ok=True)
            f._run(["git", "mv", ".github/workflows/ci.yml", "docs/history/ci.yml"])
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "rename"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 14. historical broad-prefix bypass remains closed
    def test_history_prefix_bypass_fails(self):
        f = CMLFixture()
        try:
            f._write("docs/history/evil.py", "print('evil')\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "history evil"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 15. unknown path FAIL
    def test_unknown_path_fails(self):
        f = CMLFixture()
        try:
            f._write("evil.txt", "evil\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "unknown"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("non-metadata-only", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 16. squash integration FAIL CLOSED
    def test_squash_merge_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--squash", "delivery"])
            f._run(["git", "commit", "-m", "squash merge"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("canonical integration", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 17. rebase/linear integration FAIL CLOSED
    def test_linear_merge_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--ff-only", "delivery"])
            r = f.validate()
            # fast-forward is not a merge, so no merge found.
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("canonical integration", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 18. octopus integration FAIL CLOSED
    def test_octopus_merge_fails(self):
        f = CMLFixture()
        try:
            # side1 must not be an ancestor/descendant of delivery for a real octopus.
            f._run(["git", "checkout", "-b", "side1", f.base])
            f._write("android/src/Side1.kt", "// side1\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "side1"])
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "delivery", "side1", "-m", "octopus"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("two-parent", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 19. wrong canonical branch FAIL
    def test_wrong_canonical_branch_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            # Set canonical_branch to a non-existent ref.
            state = json.loads((f.root / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
            state["canonical_branch"] = "not-the-real-main"
            (f.root / "docs/continuity/CURRENT_STATE.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
            (f.root / "docs/continuity/CURRENT_HANDOFF.md").write_text(
                f._handoff_md("main").replace("Canonical branch: `main`", "Canonical branch: `not-the-real-main`"),
                encoding="utf-8",
            )
            (f.root / "docs/continuity/CURRENT_GIT_STATE.md").write_text(
                f._git_state_md().replace("Canonical branch: `main`", "Canonical branch: `not-the-real-main`"),
                encoding="utf-8",
            )
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "state sync post merge"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("FAIL", r.stdout + r.stderr)
            self.assertIn("canonical", (r.stdout + r.stderr).lower())
        finally:
            f.cleanup()

    # 20. wrong/unrelated delivery lineage FAIL
    def test_wrong_delivery_lineage_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            # Create an unrelated branch from the base (does not contain described).
            f._run(["git", "checkout", "-b", "unrelated", f.base])
            f._write("FORTSCHRITT.md", "# Fortschritt\nunrelated\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "unrelated work"])
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge unrelated", "unrelated"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("FAIL", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 21. missing canonical branch FAIL
    def test_missing_canonical_branch_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            state = json.loads((f.root / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
            state["canonical_branch"] = "does-not-exist"
            (f.root / "docs/continuity/CURRENT_STATE.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
            (f.root / "docs/continuity/CURRENT_HANDOFF.md").write_text(
                f._handoff_md("main").replace("Canonical branch: `main`", "Canonical branch: `does-not-exist`"),
                encoding="utf-8",
            )
            (f.root / "docs/continuity/CURRENT_GIT_STATE.md").write_text(
                f._git_state_md().replace("Canonical branch: `main`", "Canonical branch: `does-not-exist`"),
                encoding="utf-8",
            )
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "bad canonical"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("FAIL", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 22. missing delivery provenance FAIL
    def test_missing_delivery_provenance_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            # Create an unrelated branch from the base (does not contain described).
            f._run(["git", "checkout", "-b", "not-delivery", f.base])
            f._write("FORTSCHRITT.md", "# Fortschritt\nnot delivery\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "not delivery"])
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge not-delivery", "not-delivery"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("FAIL", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 23. pre-merge effective gate correct
    def test_pre_merge_effective_gate(self):
        f = CMLFixture()
        try:
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn(f"effective gate: {f.pre_merge_gate}", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 24. post-merge effective gate correct
    def test_post_merge_effective_gate(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            f._write_project_state_md("main")
            f._write_handoff_md("main")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "--amend", "--no-edit"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn(f"effective gate: {f.post_merge_gate}", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 25. pre-merge Handoff does NOT authorize post-merge gate
    def test_pre_merge_handoff_gate(self):
        f = CMLFixture()
        try:
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                state = json.loads((a.root / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
                self.assertEqual(state["current_gate"], f.pre_merge_gate)
                self.assertNotEqual(state["current_gate"], f.post_merge_gate)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    # 26. post-merge Handoff resolves post-merge gate
    def test_post_merge_handoff_gate(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            f._write_project_state_md("main")
            f._write_handoff_md("main")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "--amend", "--no-edit"])
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                state = json.loads((a.root / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
                self.assertEqual(state["current_gate"], f.post_merge_gate)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    # 27. archive lifecycle partial-tamper FAIL
    def test_archive_lifecycle_tamper_fails(self):
        f = CMLFixture()
        try:
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                state_path = a.root / "docs/continuity/CURRENT_STATE.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                state["canonical_branch"] = "evil-main"
                state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
                TestArchiveLifecycleTamper._recompute_sha_manifest(a.root)
                r2 = a.validate()
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: FAIL", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    # 28. self-reference regression remains fixed
    def test_no_self_reference_required(self):
        f = CMLFixture()
        try:
            f.commit_meta("metadata tail")
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("delivery context; only metadata-only files changed", r.stdout + r.stderr)
        finally:
            f.cleanup()


    # 29. baseline ancestry regression remains fixed
    def test_baseline_ancestry_in_canonical_context(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("latest_merge_to_baseline", r.stdout + r.stderr)
            self.assertIn("previous_baseline_head", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 30. multiple canonical-merge ambiguity policy
    def test_multiple_qualifying_merges_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            # Second merge from an unrelated branch that does not contain described.
            f._run(["git", "checkout", "-b", "side2", f.base])
            f._write("android/src/Evil.kt", "// second\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "side2 product"])
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge side2", "side2"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("ambiguous/multiple", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 31. substantive canonical base drift policy
    def test_substantive_base_drift_fails(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            # Add product on main before the canonical merge.
            f._write("android/src/MainProduct.kt", "// product on main\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "main product"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SUBSTANTIVE CANONICAL BASE DRIFT", r.stdout + r.stderr)
        finally:
            f.cleanup()

    # 32. metadata-only canonical base drift policy if supported
    def test_metadata_only_base_drift_passes(self):
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            # Add metadata on main before the canonical merge.
            f._write("FORTSCHRITT.md", "# Fortschritt\nmain metadata\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "main metadata"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("metadata-only canonical base drift", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_old_unrelated_merge_and_current_transition_passes(self):
        """Older nested delivery merge must not be mistaken for canonical integration."""
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "checkout", "-b", "old-side"])
            f._write("FORTSCHRITT.md", "# Fortschritt\nold side\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "old side"])
            f._run(["git", "checkout", "delivery"])
            f._run(["git", "merge", "--no-ff", "-m", "merge old-side", "old-side"])
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("canonical merge transition verified", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_nested_delivery_merge_not_canonical(self):
        """A merge inside the delivery branch is not a canonical integration."""
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._run(["git", "checkout", "-b", "nested"])
            f._write("FORTSCHRITT.md", "# Fortschritt\nnested\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "nested work"])
            f._run(["git", "checkout", "delivery"])
            f._run(["git", "merge", "--no-ff", "-m", "merge nested", "nested"])
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_resynchronization_after_base_drift_passes(self):
        """After substantive base drift, a fresh lifecycle from the new base passes."""
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            # Simulate canonical main advancing with product.
            f._write("android/src/MainProduct.kt", "// product on main\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "main product"])
            # New delivery from the new main.
            new_main = f._run(["git", "rev-parse", "main"]).stdout.strip()
            f._run(["git", "checkout", "-b", "delivery-resync", new_main])
            f.base = new_main
            f.delivery_branch = "delivery-resync"
            # First commit on the new delivery is the described payload.
            f._write("docs/continuity/CML_SUBSTANTIVE.md", "# Resync lifecycle payload\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "resync payload"])
            f.described = f._run(["git", "rev-parse", "delivery-resync"]).stdout.strip()
            # State sync commit updates metadata to point back at the payload.
            f._write_state()
            f._write_git_state_md()
            f._write_handoff_md("delivery-resync")
            f._write_project_state_md("delivery-resync")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "resync state"])
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "-m", "merge resync", "delivery-resync"])
            r = f.validate()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            f.cleanup()

    # M1R2: reviewed-content discard (revert to canonical parent) must fail.

    def _revert_to_canonical(self, path, new_content, drift_commit=None):
        """Helper: put a substantive change on delivery, then force the merge back to main's version."""
        f = CMLFixture()
        try:
            if drift_commit:
                f._run(["git", "checkout", "main"])
                f._write("FORTSCHRITT.md", "# Fortschritt\nmain metadata\n")
                f._run(["git", "add", "."])
                f._run(["git", "commit", "-m", "main metadata"])
            f._run(["git", "checkout", "delivery"])
            f._write(path, new_content)
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "reviewed change"])
            f.set_described_head(f._run(["git", "rev-parse", "delivery"]).stdout.strip())
            f._run(["git", "checkout", "main"])
            f._run(["git", "merge", "--no-ff", "--no-commit", "delivery"])
            # Force the merge tree back to the canonical-parent version of this path.
            # --no-overlay copies the tree from main faithfully, deleting the path if main does not have it.
            f._run(["git", "checkout", "--no-overlay", "main", "--", path])
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "merge with revert"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("DISCARDED REVIEWED DELIVERY CONTENT", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_product_revert_to_canonical_no_drift_fails(self):
        """Product file added on delivery, deleted in merge to restore canonical (empty) version."""
        self._revert_to_canonical("android/src/Product.kt", "// reviewed product\n")

    def test_product_revert_to_canonical_with_metadata_drift_fails(self):
        """Metadata base drift accepted, but product revert in merge still fails."""
        self._revert_to_canonical("android/src/Product.kt", "// reviewed product\n", drift_commit=True)

    def test_ci_revert_to_canonical_no_drift_fails(self):
        """CI workflow added on delivery, deleted in merge to restore canonical (empty) version."""
        self._revert_to_canonical(".github/workflows/ci-revert.yml", "name: evil\n")

    def test_ci_revert_to_canonical_with_metadata_drift_fails(self):
        """Metadata base drift accepted, but CI revert in merge still fails."""
        self._revert_to_canonical(".github/workflows/ci-revert.yml", "name: evil\n", drift_commit=True)

    def test_authority_revert_to_canonical_no_drift_fails(self):
        """Authority file modified on delivery, reverted to canonical version in merge."""
        self._revert_to_canonical("docs/authority/AUTHORITY_INDEX.md", "# changed\n")

    def test_authority_revert_to_canonical_with_metadata_drift_fails(self):
        """Metadata base drift accepted, but authority revert in merge still fails."""
        self._revert_to_canonical("docs/authority/AUTHORITY_INDEX.md", "# changed\n", drift_commit=True)

    def test_tool_revert_to_canonical_no_drift_fails(self):
        """Tool file modified on delivery, reverted to canonical version in merge."""
        self._revert_to_canonical("tools/security/validate_apk_contents.py", "# reviewed\n")

    def test_tool_revert_to_canonical_with_metadata_drift_fails(self):
        """Metadata base drift accepted, but tool revert in merge still fails."""
        self._revert_to_canonical("tools/security/validate_apk_contents.py", "# reviewed\n", drift_commit=True)

    # M1R2: base-drift matrix items 34-36 (CI/Authority/Tool substantive drift).

    def test_ci_base_drift_fails(self):
        """Substantive CI change on canonical main before merge requires resynchronization."""
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._write(".github/workflows/ci-drift.yml", "name: drift\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "ci drift"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SUBSTANTIVE CANONICAL BASE DRIFT", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_authority_base_drift_fails(self):
        """Substantive Authority change on canonical main before merge requires resynchronization."""
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._write("docs/authority/B_FREEZE_REGISTRY.md", "drift\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "authority drift"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SUBSTANTIVE CANONICAL BASE DRIFT", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_tool_base_drift_fails(self):
        """Substantive Tool change on canonical main before merge requires resynchronization."""
        f = CMLFixture()
        try:
            f._run(["git", "checkout", "main"])
            f._write("tools/security/validate_apk_contents.py", "# drift\n")
            f._run(["git", "add", "."])
            f._run(["git", "commit", "-m", "tool drift"])
            f._run(["git", "merge", "--no-ff", "-m", "merge delivery", "delivery"])
            r = f.validate()
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SUBSTANTIVE CANONICAL BASE DRIFT", r.stdout + r.stderr)
        finally:
            f.cleanup()


class TestArchiveLifecycleTamper(unittest.TestCase):
    """ANOX-CMLREV-002: archive semantic cross-checks and trust model."""

    @staticmethod
    def _recompute_sha_manifest(archive_root):
        """Recompute SHA256_MANIFEST.txt after editing a packaged file."""
        sha_manifest_path = archive_root / "SHA256_MANIFEST.txt"
        import hashlib
        new_lines = []
        for line in sha_manifest_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                new_lines.append(line)
                continue
            digest, name = line.split(None, 1)
            p = archive_root / name
            if p.exists():
                new_digest = hashlib.sha256(p.read_bytes()).hexdigest()
                new_lines.append(f"{new_digest}  {name}")
            else:
                new_lines.append(line)
        sha_manifest_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    def _generate_archive(self):
        f = CMLFixture()
        try:
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            return f.zip_path(), f
        except Exception:
            f.cleanup()
            raise

    def _tamper_and_fail(self, tamper_fn):
        f = CMLFixture()
        try:
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                tamper_fn(a.root)
                self._recompute_sha_manifest(a.root)
                r2 = a.validate()
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: FAIL", r2.stdout + r2.stderr, r2.stdout + r2.stderr)
                return a
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    def test_canonical_branch_tamper_fails(self):
        def t(root):
            p = root / "docs/continuity/CURRENT_STATE.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["canonical_branch"] = "evil"
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_delivery_branch_tamper_fails(self):
        def t(root):
            p = root / "docs/continuity/CURRENT_STATE.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["delivery_branch"] = "evil"
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_current_gate_tamper_fails(self):
        def t(root):
            p = root / "docs/continuity/CURRENT_STATE.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["current_gate"] = "EVIL GATE"
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_pre_merge_gate_tamper_fails(self):
        def t(root):
            p = root / "docs/continuity/CURRENT_STATE.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["pre_merge_gate"] = "EVIL PRE"
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_post_merge_gate_tamper_fails(self):
        def t(root):
            p = root / "docs/continuity/CURRENT_STATE.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["post_merge_gate"] = "EVIL POST"
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_handoff_head_tamper_fails(self):
        def t(root):
            p = root / "docs/continuity/CURRENT_STATE.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["handoff_head"] = "0" * 40
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_described_head_tamper_fails(self):
        def t(root):
            p = root / "docs/continuity/CURRENT_STATE.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["described_head"] = "0" * 40
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_snapshot_branch_tamper_fails(self):
        def t(root):
            snapshot = (root / "GIT_SNAPSHOT.txt").read_text(encoding="utf-8")
            lines = snapshot.splitlines()
            for i, line in enumerate(lines):
                if "git branch --show-current" in line:
                    lines[i + 1] = "evil-branch"
                    break
            (root / "GIT_SNAPSHOT.txt").write_text("\n".join(lines), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_working_tree_tamper_fails(self):
        def t(root):
            p = root / "docs/continuity/CURRENT_STATE.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["working_tree"] = "dirty"
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._tamper_and_fail(t)

    # M1R2: N-1 cross-surface tampering (three state/human surfaces rewritten,
    # GIT_SNAPSHOT.txt resolved lifecycle block left untouched).

    def _n_minus_1_tamper(self, root, state_key, new_value, human_pattern=None):
        """Change a lifecycle value in CURRENT_STATE.json and both human surfaces, but NOT GIT_SNAPSHOT."""
        state_path = root / "docs" / "continuity" / "CURRENT_STATE.json"
        data = json.loads(state_path.read_text(encoding="utf-8"))
        original = data.get(state_key, "")
        data[state_key] = new_value
        state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        for rel in ("docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_GIT_STATE.md"):
            p = root / rel
            text = p.read_text(encoding="utf-8")
            if original:
                text = text.replace(original, new_value)
            if human_pattern:
                text = text.replace(human_pattern[0], human_pattern[1])
            p.write_text(text, encoding="utf-8")

    def test_n1_canonical_branch_tamper_fails(self):
        """Canonical branch rewritten on state/human surfaces but not GIT_SNAPSHOT."""
        def t(root):
            self._n_minus_1_tamper(root, "canonical_branch", "attacker-main")
        self._tamper_and_fail(t)

    def test_n1_delivery_branch_tamper_fails(self):
        """Delivery branch rewritten on state/human surfaces but not GIT_SNAPSHOT."""
        def t(root):
            self._n_minus_1_tamper(root, "delivery_branch", "attacker-delivery")
        self._tamper_and_fail(t)

    def test_n1_described_head_tamper_fails(self):
        """Described head rewritten on state/human surfaces but not GIT_SNAPSHOT."""
        def t(root):
            self._n_minus_1_tamper(root, "described_head", "a" * 40)
        self._tamper_and_fail(t)

    def test_n1_pre_merge_gate_tamper_fails(self):
        """Pre-merge gate rewritten on state/human surfaces but not GIT_SNAPSHOT."""
        def t(root):
            state = json.loads((root / "docs" / "continuity" / "CURRENT_STATE.json").read_text(encoding="utf-8"))
            self._n_minus_1_tamper(root, "pre_merge_gate", "ATTACKER PRE", (f"Pre-merge gate: `{state['pre_merge_gate']}`", "Pre-merge gate: `ATTACKER PRE`"))
        self._tamper_and_fail(t)

    def test_n1_post_merge_gate_tamper_fails(self):
        """Post-merge gate rewritten on state/human surfaces but not GIT_SNAPSHOT."""
        def t(root):
            state = json.loads((root / "docs" / "continuity" / "CURRENT_STATE.json").read_text(encoding="utf-8"))
            self._n_minus_1_tamper(root, "post_merge_gate", "ATTACKER POST", (f"Post-merge gate: `{state['post_merge_gate']}`", "Post-merge gate: `ATTACKER POST`"))
        self._tamper_and_fail(t)

    def test_n1_effective_gate_tamper_fails(self):
        """Resolved current/effective gate rewritten on state/human surfaces but not GIT_SNAPSHOT."""
        def t(root):
            state = json.loads((root / "docs" / "continuity" / "CURRENT_STATE.json").read_text(encoding="utf-8"))
            state["current_gate"] = "ATTACKER GATE"
            (root / "docs" / "continuity" / "CURRENT_STATE.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
            for rel in ("docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_GIT_STATE.md"):
                p = root / rel
                text = p.read_text(encoding="utf-8")
                # Replace the resolved current-gate value and its parenthetical references.
                text = text.replace(f"Current gate: `{state['pre_merge_gate']}`", "Current gate: `ATTACKER GATE`")
                text = text.replace(f"delivery -> `{state['pre_merge_gate']}`", "delivery -> `ATTACKER GATE`")
                text = text.replace(f"canonical -> `{state['post_merge_gate']}`", "canonical -> `ATTACKER GATE`")
                p.write_text(text, encoding="utf-8")
        self._tamper_and_fail(t)

    # M1R2: GIT_SNAPSHOT.txt lifecycle block integrity.

    def test_missing_lifecycle_snapshot_block_fails(self):
        """Current-schema archive missing the resolved lifecycle metadata block fails."""
        def t(root):
            text = (root / "GIT_SNAPSHOT.txt").read_text(encoding="utf-8")
            # Remove the lifecycle block entirely.
            lines = text.splitlines()
            new = []
            skip = False
            for line in lines:
                if line.strip() == "### Resolved lifecycle metadata":
                    skip = True
                    continue
                if skip and line.startswith("### "):
                    skip = False
                if not skip:
                    new.append(line)
            (root / "GIT_SNAPSHOT.txt").write_text("\n".join(new), encoding="utf-8")
        self._tamper_and_fail(t)

    def test_duplicate_lifecycle_snapshot_field_fails(self):
        """Duplicate field in the resolved lifecycle metadata block fails."""
        def t(root):
            text = (root / "GIT_SNAPSHOT.txt").read_text(encoding="utf-8")
            text = text.replace(
                "### Resolved lifecycle metadata",
                "### Resolved lifecycle metadata\ncanonical_branch: extra",
            )
            (root / "GIT_SNAPSHOT.txt").write_text(text, encoding="utf-8")
        self._tamper_and_fail(t)

    def test_unresolved_lifecycle_snapshot_placeholder_fails(self):
        """Unresolved placeholder in the resolved lifecycle metadata block fails."""
        def t(root):
            text = (root / "GIT_SNAPSHOT.txt").read_text(encoding="utf-8")
            text = text.replace(
                "effective_gate:",
                "effective_gate: __EFFECTIVE_GATE__",
            )
            (root / "GIT_SNAPSHOT.txt").write_text(text, encoding="utf-8")
        self._tamper_and_fail(t)

    def test_untampered_archive_passes(self):
        f = CMLFixture()
        try:
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                r2 = a.validate()
                self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: PASS", r2.stdout + r2.stderr)
                self.assertIn("ARCHIVE AUTHENTICITY: UNVERIFIED", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    def test_coherent_reauthored_archive_passes_but_unauthenticated(self):
        f = CMLFixture()
        try:
            r = f.generate(emergency=False)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            a = ArchiveFixture(z)
            try:
                # Rewrite all internal surfaces to a new consistent but externally unverified state.
                new_canonical = "reauthored-main"
                new_delivery = "reauthored-delivery"
                new_described = "1" * 40
                new_head = "2" * 40
                new_branch = "reauthored-branch"
                new_gate = "REAUTHORED GATE"

                state = json.loads((a.root / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
                original_head = state["handoff_head"]
                original_branch = state["handoff_branch"]
                original_described = state["described_head"]
                original_pre = state["pre_merge_gate"]
                original_post = state["post_merge_gate"]
                state.update({
                    "canonical_branch": new_canonical,
                    "delivery_branch": new_delivery,
                    "described_head": new_described,
                    "handoff_branch": new_branch,
                    "handoff_head": new_head,
                    "working_tree": "clean",
                    "current_gate": new_gate,
                    "pre_merge_gate": new_gate,
                    "post_merge_gate": new_gate,
                })
                (a.root / "docs/continuity/CURRENT_STATE.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

                for rel in ("docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_GIT_STATE.md"):
                    p = a.root / rel
                    text = p.read_text(encoding="utf-8")
                    text = text.replace("main", new_canonical)
                    text = text.replace("delivery", new_delivery)
                    # described_head appears in backticks
                    text = text.replace(original_described, new_described)
                    # update pre/post gate declarations
                    text = text.replace(f"Pre-merge gate: `{original_pre}`", f"Pre-merge gate: `{new_gate}`")
                    text = text.replace(f"Post-merge gate: `{original_post}`", f"Post-merge gate: `{new_gate}`")
                    # update the resolved current/effective gate and its parenthetical references
                    text = text.replace(f"Current gate: `{original_pre}`", f"Current gate: `{new_gate}`")
                    text = text.replace(f"Current gate: `{original_post}`", f"Current gate: `{new_gate}`")
                    p.write_text(text, encoding="utf-8")

                snapshot = (a.root / "GIT_SNAPSHOT.txt").read_text(encoding="utf-8")
                snapshot_lines = snapshot.splitlines()
                new_snapshot = []
                in_lifecycle = False
                i = 0
                while i < len(snapshot_lines):
                    line = snapshot_lines[i]
                    if line.strip() == "### Resolved lifecycle metadata":
                        in_lifecycle = True
                        new_snapshot.append(line)
                        i += 1
                        continue
                    if in_lifecycle and line.startswith("### "):
                        in_lifecycle = False
                    if in_lifecycle and ":" in line:
                        key = line.split(":", 1)[0].strip()
                        if key == "canonical_branch":
                            new_snapshot.append(f"canonical_branch: {new_canonical}")
                        elif key == "delivery_branch":
                            new_snapshot.append(f"delivery_branch: {new_delivery}")
                        elif key == "described_head":
                            new_snapshot.append(f"described_head: {new_described}")
                        elif key == "pre_merge_gate":
                            new_snapshot.append(f"pre_merge_gate: {new_gate}")
                        elif key == "post_merge_gate":
                            new_snapshot.append(f"post_merge_gate: {new_gate}")
                        elif key == "effective_gate":
                            new_snapshot.append(f"effective_gate: {new_gate}")
                        else:
                            new_snapshot.append(line)
                        i += 1
                        continue
                    if "git branch --show-current" in line:
                        new_snapshot.append(line)
                        i += 1
                        while i < len(snapshot_lines) and not snapshot_lines[i].strip():
                            new_snapshot.append(snapshot_lines[i])
                            i += 1
                        if i < len(snapshot_lines):
                            new_snapshot.append(new_branch)
                            i += 1
                        continue
                    if "git rev-parse HEAD" in line:
                        new_snapshot.append(line)
                        i += 1
                        while i < len(snapshot_lines) and not snapshot_lines[i].strip():
                            new_snapshot.append(snapshot_lines[i])
                            i += 1
                        if i < len(snapshot_lines):
                            new_snapshot.append(new_head)
                            i += 1
                        continue
                    new_snapshot.append(line)
                    i += 1
                (a.root / "GIT_SNAPSHOT.txt").write_text("\n".join(new_snapshot), encoding="utf-8")

                manifest = (a.root / "MANIFEST.txt").read_text(encoding="utf-8")
                manifest = manifest.replace(f"Handoff branch: {original_branch}", f"Handoff branch: {new_branch}")
                manifest = manifest.replace(f"Handoff HEAD: {original_head}", f"Handoff HEAD: {new_head}")
                (a.root / "MANIFEST.txt").write_text(manifest, encoding="utf-8")

                self._recompute_sha_manifest(a.root)
                r2 = a.validate()
                self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: PASS", r2.stdout + r2.stderr)
                self.assertIn("ARCHIVE AUTHENTICITY: UNVERIFIED", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()


if __name__ == "__main__":
    unittest.main()
