#!/usr/bin/env python3
"""Adversarial tests for ANOX-DECISION-HANDOFF-UNSEALED-EXCEPTION-001.

Covers the declared-unsealed handoff exception:
- generate_handoff.py --allow-unsealed stamps MANIFEST.txt with
  SEAL_STATUS=UNSEALED_AT_GENERATION + described_head + last_sealed,
- validate_continuity.py --mode archive accepts a declared unsealed package
  as PASS — DECLARED_UNSEALED,
- undeclared unsealed state fails exactly as before (fail-closed),
- forged/mismatched/partial stamps and stamps on sealed packages fail,
- the no-flag path is byte-identical to the legacy manifest format.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from test_handoff_and_validator import ArchiveFixture, CMLFixture, REPO_ROOT

import validate_continuity as vc


class TestUnsealedHandoffException(unittest.TestCase):
    """Freshness-layer tests: declared vs undeclared vs forged unsealed packages."""

    SHA_A = "a" * 40  # canonical merge head
    SHA_B = "b" * 40  # last sealed ledger event head
    SHA_C = "c" * 40  # unsealed described_head
    SHA_D = "d" * 40  # packaged handoff head (metadata-advanced)

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="anox_unsealed_")
        self.root = Path(self.tmp)
        self._write("docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md", "# Project Memory Surface Index\n")
        self._write("PROJECT_STATE.md", "# State\n")
        self._write("FORTSCHRITT.md", "# Fortschritt\n")
        self._write_ledger(self._events())
        self._write_state(**self._state_overrides())
        self._write_markers("ANOX-EVENT-0002")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _events(self):
        return [
            {
                "event_id": "ANOX-EVENT-0001",
                "date": "2026-08-30",
                "type": "canonical_merge",
                "task": "PR-1",
                "summary": "merge",
                "status": "merged",
                "start_head": self.SHA_A,
                "end_head": self.SHA_A,
                "merge_head": self.SHA_A,
            },
            {
                "event_id": "ANOX-EVENT-0002",
                "date": "2026-08-30",
                "type": "implementation",
                "task": "T2",
                "summary": "sealed checkpoint",
                "status": "closed",
                "start_head": self.SHA_A,
                "end_head": self.SHA_B,
            },
        ]

    def _state_overrides(self, described=None):
        return {
            "handoff_head": self.SHA_D,
            "described_head": described or self.SHA_C,
            "latest_material_event_id": "ANOX-EVENT-0002",
            "latest_human_history_event_id": "ANOX-EVENT-0002",
        }

    def _write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_ledger(self, events):
        path = self.root / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")

    def _write_state(self, **overrides):
        state = {
            "schema_version": "B026-1.2",
            "canonical_branch": "main",
            "delivery_branch": "delivery",
            "pre_merge_gate": "PRE-MERGE",
            "post_merge_gate": "POST-MERGE",
        }
        state.update(overrides)
        self._write("docs/continuity/CURRENT_STATE.json", json.dumps(state))

    def _write_markers(self, event_id):
        ps_path = self.root / "PROJECT_STATE.md"
        ps_path.write_text(ps_path.read_text(encoding="utf-8") + f"\n<!-- ANOX_EVENT: {event_id} -->\n", encoding="utf-8")
        ft_path = self.root / "FORTSCHRITT.md"
        ft_path.write_text(ft_path.read_text(encoding="utf-8") + f"\n## Latest section\n<!-- ANOX_EVENT: {event_id} -->\n", encoding="utf-8")

    def _write_manifest(self, status=None, described=None, last_sealed=None):
        lines = [
            "# ANOX V1 Handoff Manifest",
            "# Date: 2026-10-03 00:00:00",
            "# Handoff branch: delivery",
            f"# Handoff HEAD: {self.SHA_D}",
            "# Baseline branch: main",
            f"# Baseline HEAD: {self.SHA_A}",
            "# Status: clean",
            "# File count: 3",
        ]
        if status is not None:
            lines.append(f"# SEAL_STATUS: {status}")
        if described is not None:
            lines.append(f"# SEAL_DESCRIBED_HEAD: {described}")
        if last_sealed is not None:
            lines.append(f"# SEAL_LAST_SEALED: {last_sealed}")
        lines += ["", "GIT_SNAPSHOT.txt", "MANIFEST.txt", "SHA256_MANIFEST.txt"]
        self._write("MANIFEST.txt", "\n".join(lines) + "\n")

    def _write_manifest_seal_lines(self, seal_lines):
        """Manifest carrying caller-controlled raw SEAL_* lines — used to
        build partial, duplicated and contradictory stamps (F-001 cases)."""
        lines = [
            "# ANOX V1 Handoff Manifest",
            "# Date: 2026-10-03 00:00:00",
            "# Handoff branch: delivery",
            f"# Handoff HEAD: {self.SHA_D}",
            "# Baseline branch: main",
            f"# Baseline HEAD: {self.SHA_A}",
            "# Status: clean",
            "# File count: 3",
            *seal_lines,
            "",
            "GIT_SNAPSHOT.txt",
            "MANIFEST.txt",
            "SHA256_MANIFEST.txt",
        ]
        self._write("MANIFEST.txt", "\n".join(lines) + "\n")

    def _call(self, described=None):
        state = json.loads((self.root / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
        if described is not None:
            state["described_head"] = described
        return vc.validate_project_memory_freshness(
            self.root, True, "TEST", "delivery", self.SHA_D, state, "archive"
        )

    def test_unsealed_declared_stamp_PASS(self):
        """Declared unsealed package: stamp matches packaged state + ledger tail."""
        self._write_manifest("UNSEALED_AT_GENERATION", self.SHA_C, self.SHA_B)
        all_ok, status = self._call()
        self.assertTrue(all_ok, status)
        self.assertTrue(status.startswith("PASS"), status)
        self.assertIn("DECLARED_UNSEALED", status)

    def test_unsealed_undeclared_FAIL(self):
        """No stamp: identical fail-closed behavior as before the exception."""
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("FAIL — AUTHORED MATERIAL CHECKPOINT WITHOUT LEDGER EVENT", status)

    def test_unsealed_forged_described_head_FAIL(self):
        """Stamp claims a described_head different from the packaged state."""
        self._write_manifest("UNSEALED_AT_GENERATION", "e" * 40, self.SHA_B)
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("FAIL", status)
        self.assertIn("SEAL_STATUS STAMP", status)

    def test_unsealed_forged_last_sealed_FAIL(self):
        """Stamp claims a last_sealed value different from the packaged ledger tail."""
        self._write_manifest("UNSEALED_AT_GENERATION", self.SHA_C, "f" * 40)
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("SEAL_STATUS STAMP", status)

    def test_unsealed_partial_stamp_FAIL(self):
        """SEAL_STATUS alone without matching head fields is a malformed stamp."""
        self._write_manifest("UNSEALED_AT_GENERATION")
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("PARTIAL OR CONTRADICTORY", status)

    def test_unsealed_unknown_status_value_FAIL(self):
        """A SEAL_STATUS value other than UNSEALED_AT_GENERATION fails closed."""
        self._write_manifest("SEALED_AT_GENERATION", self.SHA_C, self.SHA_B)
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("SEAL_STATUS STAMP", status)

    def test_sealed_package_without_stamp_PASS(self):
        """Sealed package (described_head == last sealed) unchanged: PASS, no stamp."""
        self._write_state(**self._state_overrides(described=self.SHA_B))
        all_ok, status = self._call()
        self.assertTrue(all_ok, status)
        self.assertIn("SEALED EVENT SYNCHRONIZED", status)

    def test_sealed_package_with_stamp_FAIL(self):
        """A stamp on a sealed package is contradictory — treated as tamper."""
        self._write_state(**self._state_overrides(described=self.SHA_B))
        self._write_manifest("UNSEALED_AT_GENERATION", self.SHA_B, self.SHA_B)
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("tamper", status.lower())

    # --- ANOX-ROLE002-HANDOFF-UNSEALED-001: partial / contradictory stamps ---

    def test_sealed_stray_described_head_FAIL(self):
        """Sealed package + stray SEAL_DESCRIBED_HEAD without SEAL_STATUS is a
        partial stamp and must FAIL (previously silently passed)."""
        self._write_state(**self._state_overrides(described=self.SHA_B))
        self._write_manifest_seal_lines([f"# SEAL_DESCRIBED_HEAD: {self.SHA_B}"])
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("FAIL", status)

    def test_sealed_stray_last_sealed_FAIL(self):
        """Sealed package + stray SEAL_LAST_SEALED without SEAL_STATUS — FAIL."""
        self._write_state(**self._state_overrides(described=self.SHA_B))
        self._write_manifest_seal_lines([f"# SEAL_LAST_SEALED: {self.SHA_B}"])
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("FAIL", status)

    def test_sealed_both_heads_without_status_FAIL(self):
        """Sealed package + both head fields but no SEAL_STATUS — partial stamp
        must FAIL (was the reported reproduction that passed)."""
        self._write_state(**self._state_overrides(described=self.SHA_B))
        self._write_manifest_seal_lines([
            f"# SEAL_DESCRIBED_HEAD: {self.SHA_B}",
            f"# SEAL_LAST_SEALED: {self.SHA_B}",
        ])
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("FAIL", status)

    def test_unsealed_partial_stamp_fields_FAIL(self):
        """On an unsealed package a stray head field without SEAL_STATUS is a
        partial stamp — must FAIL, not be treated as 'no declaration'."""
        self._write_manifest_seal_lines([f"# SEAL_DESCRIBED_HEAD: {self.SHA_C}"])
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("PARTIAL OR CONTRADICTORY", status)

    def test_duplicate_seal_status_FAIL(self):
        """Contradictory duplicate SEAL_STATUS (UNKNOWN then valid) — the
        last-value-wins behaviour must not rescue the forged declaration."""
        self._write_manifest_seal_lines([
            "# SEAL_STATUS: UNKNOWN",
            f"# SEAL_DESCRIBED_HEAD: {self.SHA_C}",
            f"# SEAL_LAST_SEALED: {self.SHA_B}",
            "# SEAL_STATUS: UNSEALED_AT_GENERATION",
        ])
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("PARTIAL OR CONTRADICTORY", status)

    def test_duplicate_described_head_FAIL(self):
        """Duplicate SEAL_DESCRIBED_HEAD where the last (correct) value would
        otherwise pass — duplicates themselves must FAIL."""
        self._write_manifest_seal_lines([
            "# SEAL_STATUS: UNSEALED_AT_GENERATION",
            f"# SEAL_DESCRIBED_HEAD: {'e' * 40}",
            f"# SEAL_LAST_SEALED: {self.SHA_B}",
            f"# SEAL_DESCRIBED_HEAD: {self.SHA_C}",
        ])
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("PARTIAL OR CONTRADICTORY", status)

    def test_duplicate_last_sealed_FAIL(self):
        """Duplicate SEAL_LAST_SEALED with contradictory values — FAIL."""
        self._write_manifest_seal_lines([
            "# SEAL_STATUS: UNSEALED_AT_GENERATION",
            f"# SEAL_DESCRIBED_HEAD: {self.SHA_C}",
            f"# SEAL_LAST_SEALED: {'f' * 40}",
            f"# SEAL_LAST_SEALED: {self.SHA_B}",
        ])
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("PARTIAL OR CONTRADICTORY", status)

    def test_unknown_seal_field_FAIL(self):
        """An unknown SEAL_* field alongside a complete valid stamp — the stamp
        is malformed as a whole and must FAIL."""
        self._write_manifest_seal_lines([
            "# SEAL_STATUS: UNSEALED_AT_GENERATION",
            f"# SEAL_DESCRIBED_HEAD: {self.SHA_C}",
            f"# SEAL_LAST_SEALED: {self.SHA_B}",
            "# SEAL_FUTURE_FIELD: forged",
        ])
        all_ok, status = self._call()
        self.assertFalse(all_ok)
        self.assertIn("PARTIAL OR CONTRADICTORY", status)


class TestUnsealedHandoffE2E(unittest.TestCase):
    """End-to-end: generate_handoff.py --allow-unsealed against a real git fixture."""

    def _rebind_ledger(self, f, last_sealed):
        """Seal the fixture ledger tail at the given real commit while
        described_head stays f.described."""
        events = [
            {
                "event_id": "ANOX-EVENT-0001",
                "date": "2026-08-30",
                "type": "canonical_merge",
                "task": "PR-1",
                "summary": "merge",
                "status": "merged",
                "start_head": f.base,
                "end_head": f.base,
                "merge_head": f.base,
            },
            {
                "event_id": "ANOX-EVENT-0002",
                "date": "2026-08-30",
                "type": "implementation",
                "task": "T2",
                "summary": "sealed checkpoint",
                "status": "closed",
                "start_head": f.base,
                "end_head": last_sealed,
            },
        ]
        ledger = f.root / "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl"
        with open(ledger, "w", encoding="utf-8") as fh:
            for ev in events:
                fh.write(json.dumps(ev) + "\n")
        f._run(["git", "add", "."])
        f._run(["git", "commit", "-m", "rebind ledger tail"])
        return f

    def _make_unsealed(self):
        """Ledger tail sealed at base; described_head (a descendant) is unsealed."""
        f = CMLFixture()
        return self._rebind_ledger(f, f.base)

    def _make_sealed(self):
        """Ledger tail sealed at described_head."""
        f = CMLFixture()
        return self._rebind_ledger(f, f.described)

    @staticmethod
    def _manifest_from_zip(zip_path):
        with zipfile.ZipFile(zip_path) as zf:
            return zf.read("MANIFEST.txt").decode("utf-8")

    def test_unsealed_without_flag_FAIL_closed(self):
        """Unsealed state without --allow-unsealed: generation fails as before."""
        f = self._make_unsealed()
        try:
            r = f.generate(emergency=False)
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("AUTHORED MATERIAL CHECKPOINT WITHOUT LEDGER EVENT", r.stdout + r.stderr)
        finally:
            f.cleanup()

    def test_unsealed_with_flag_PASS_and_stamped(self):
        """--allow-unsealed produces a package stamped UNSEALED_AT_GENERATION that
        archive validation accepts as DECLARED_UNSEALED."""
        f = self._make_unsealed()
        try:
            r = f._run([sys.executable, "tools/continuity/generate_handoff.py", "--allow-unsealed"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            z = f.zip_path()
            self.assertIsNotNone(z)
            manifest = self._manifest_from_zip(z)
            self.assertIn("# SEAL_STATUS: UNSEALED_AT_GENERATION", manifest)
            self.assertIn(f"# SEAL_DESCRIBED_HEAD: {f.described}", manifest)
            self.assertIn(f"# SEAL_LAST_SEALED: {f.base}", manifest)
            a = ArchiveFixture(z)
            try:
                r2 = a.validate()
                self.assertIn("HANDOFF_ARCHIVE_VALIDATION: PASS", r2.stdout + r2.stderr)
                self.assertIn("DECLARED_UNSEALED", r2.stdout + r2.stderr)
            finally:
                a.cleanup()
        finally:
            f.cleanup()

    def test_no_flag_manifest_byte_identical(self):
        """Without --allow-unsealed the manifest keeps the legacy byte format —
        the flag is a no-op on a sealed package."""
        f = self._make_sealed()
        try:
            r1 = f.generate(emergency=False)
            self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
            z1 = f.zip_path()
            self.assertIsNotNone(z1)
            m1 = self._manifest_from_zip(z1)
            self.assertNotIn("SEAL_STATUS", m1)
            self.assertNotIn("SEAL_DESCRIBED_HEAD", m1)
            self.assertNotIn("SEAL_LAST_SEALED", m1)
            # Remove generated artifacts so the second run sees a clean tree.
            shutil.rmtree(f.root / "artifacts", ignore_errors=True)
            # Flag on a sealed package must not alter a single manifest byte.
            r2 = f._run([sys.executable, "tools/continuity/generate_handoff.py", "--allow-unsealed"])
            self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
            z2 = f.zip_path()
            self.assertIsNotNone(z2)
            m2 = self._manifest_from_zip(z2)
            strip_date = lambda m: "\n".join(l for l in m.splitlines() if not l.startswith("# Date:"))
            self.assertEqual(strip_date(m1), strip_date(m2))
        finally:
            f.cleanup()


if __name__ == "__main__":
    unittest.main()
