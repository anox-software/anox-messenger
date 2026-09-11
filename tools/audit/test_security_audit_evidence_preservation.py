#!/usr/bin/env python3
"""Adversarial tests for the security-audit evidence-preservation validator.

Each test copies the canonical evidence surface into a temporary fixture,
mutates exactly one aspect, and asserts the validator FAILS. Canonical
evidence is never mutated by these tests.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "audit" / "validate_security_audit_evidence_preservation.py"

FIXTURE_FILES = [
    "docs/security/audit-evidence/AUDIT_EVIDENCE_INDEX.md",
    "docs/security/audit-evidence/audit_registry.jsonl",
    "docs/security/audit-evidence/audit_traceability.jsonl",
    "docs/security/audit-evidence/evidence_hashes.json",
    "docs/security/audit-evidence/reproductions/README.md",
    "docs/reports/security/audits/AUDIT-SECURITY-ARCHITECTURE.md",
    "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md",
    "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-002.md",
    "docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md",
    "docs/reports/security/audits/AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001.md",
    "docs/workforce/WORKFORCE_STATE.json",
    "docs/workforce/registries/findings.jsonl",
    "docs/workforce/registries/tasks.jsonl",
    "docs/workforce/registries/implementation_readiness.json",
    "docs/continuity/CURRENT_STATE.json",
    "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
]

TRACE = "docs/security/audit-evidence/audit_traceability.jsonl"


def _load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def _write_jsonl(path, records):
    Path(path).write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


class EvidencePreservationAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in FIXTURE_FILES:
            src = REPO_ROOT / rel
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    def tearDown(self):
        self.tmp.cleanup()

    def run_validator(self):
        env = dict(os.environ)
        env["SECURITY_AUDIT_PRESERVATION_REPO"] = str(self.root)
        return subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=self.root, env=env, capture_output=True, text=True,
        )

    def assert_fails(self, result, needle=None):
        self.assertNotEqual(result.returncode, 0, f"validator must FAIL; stdout:\n{result.stdout}\n{result.stderr}")
        self.assertIn("FAIL", result.stdout)
        if needle:
            self.assertIn(needle, result.stdout, f"missing expected failure detail {needle!r}:\n{result.stdout}")

    # Control: unmutated fixture must PASS.
    def test_00_control_fixture_passes(self):
        r = self.run_validator()
        self.assertEqual(r.returncode, 0, f"unmutated fixture must PASS:\n{r.stdout}\n{r.stderr}")

    # 1. Mutate one preserved report.
    def test_01_mutated_report_fails(self):
        p = self.root / "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md"
        with open(p, "ab") as f:
            f.write(b"\n tampered")
        self.assert_fails(self.run_validator(), "hash mismatch")

    # 2. Delete one preserved report.
    def test_02_deleted_report_fails(self):
        (self.root / "docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md").unlink()
        self.assert_fails(self.run_validator(), "missing")

    # 3. Remove Audit-001 candidate C-019 from traceability.
    def test_03_removed_a1_c019_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if not (r.get("record_type") == "audit001_candidate" and r.get("consensus_ref") == "C-019")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator())

    # 4. Fabricate an Audit-001 source candidate for ROOT-005.
    def test_04_fabricated_root005_a1_source_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "consensus_root" and r.get("root_id") == "ROOT-005":
                r["audit001_sources"] = ["C-003"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "fabricated Audit-001 source")

    # 5. Activate ROOT-016 as a real finding.
    def test_05_activated_root016_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "consensus_root" and r.get("root_id") == "ROOT-016":
                r["status"] = "ACTIVE"
                r["severity"] = "LOW"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "ROOT-016")

    # 6. Remove one Pre-B004 root from the gate set.
    def test_06_removed_preb004_root_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "gate_set" and r.get("gate") == "PRE_B004_ROOTS":
                r["roots"] = [x for x in r["roots"] if x != "ROOT-017"]
                r["count"] = len(r["roots"])
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "PRE_B004")

    # 7. Alter a Build/Supply severity count.
    def test_07_altered_buildsc_severity_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "buildsc_candidate" and r.get("candidate_id") == "ANOX-BUILDSC-CANDIDATE-004":
                r["severity"] = "HIGH"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "severity")

    # 8. Remove Evidence Integrity CRITICAL from BUILDSC-001.
    def test_08_removed_evidence_integrity_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "buildsc_candidate" and r.get("candidate_id") == "ANOX-BUILDSC-CANDIDATE-001":
                r["evidence_integrity"] = "HIGH"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "EVIDENCE_INTEGRITY")

    # 9. Rewrite historical LEGACY-CRYPTO-005 closure as reopened.
    def test_09_reopened_legacy_crypto005_fails(self):
        fp = self.root / "docs/workforce/registries/findings.jsonl"
        recs = _load_jsonl(fp)
        for r in recs:
            if r.get("finding_id") == "ANOX-LEGACY-CRYPTO-005":
                r["status"] = "Open"
        _write_jsonl(fp, recs)
        self.assert_fails(self.run_validator(), "LEGACY-CRYPTO-005")

    # 10. Mark B-004 started.
    def test_10_b004_started_fails(self):
        ip = self.root / "docs/workforce/registries/implementation_readiness.json"
        data = json.loads(ip.read_text(encoding="utf-8"))
        data["domains"]["B-004"]["implementation_state"] = "IN_PROGRESS"
        ip.write_text(json.dumps(data, indent=1), encoding="utf-8")
        self.assert_fails(self.run_validator(), "B-004")

    # 11. Mark the Crypto/JNI audit gate executed.
    def test_11_cryptojni_executed_fails(self):
        tp = self.root / "docs/workforce/registries/tasks.jsonl"
        recs = _load_jsonl(tp)
        recs.append({
            "task_id": "ANOX-TASK-SECURITY-CRYPTO-JNI-001",
            "title": "AUDIT-SECURITY-CRYPTO-JNI-001",
            "status": "Closed",
            "branch": "audit/security-crypto-jni",
            "role_id": "ROLE-009",
        })
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "Crypto/JNI")


if __name__ == "__main__":
    unittest.main()
