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
    "docs/reports/security/audits/AUDIT-SECURITY-CRYPTO-JNI-001.md",
    "docs/reports/security/audits/AUDIT-SECURITY-AUTH-DPOP-001.md",
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
        self.assert_fails(self.run_validator(), "must remain Candidate")

    # 12. Mutate the preserved Crypto/JNI report.
    def test_12_mutated_cryptojni_report_fails(self):
        p = self.root / "docs/reports/security/audits/AUDIT-SECURITY-CRYPTO-JNI-001.md"
        with open(p, "ab") as f:
            f.write(b"\n tampered")
        self.assert_fails(self.run_validator(), "hash mismatch")

    # 13. Remove Crypto/JNI Candidate-001 from traceability.
    def test_13_removed_cryptojni_candidate_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if not (r.get("record_type") == "cryptojni_candidate" and r.get("candidate_id") == "ANOX-CRYPTOJNI-CANDIDATE-001")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "Crypto/JNI")

    # 14. Reduce the audit registry from 6 to 5 records.
    def test_14_dropped_cryptojni_registry_record_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = [r for r in _load_jsonl(rp) if r.get("audit_id") != "AUDIT-SECURITY-CRYPTO-JNI-001"]
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "exactly 7 audits")

    # 15. Downgrade Crypto/JNI Candidate-001 severity HIGH -> MEDIUM.
    def test_15_downgraded_cryptojni_001_severity_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "cryptojni_candidate" and r.get("candidate_id") == "ANOX-CRYPTOJNI-CANDIDATE-001":
                r["severity"] = "MEDIUM"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "ANOX-CRYPTOJNI-CANDIDATE-001")

    # 16. Mark Crypto/JNI Candidate-004 as a Pre-B004 blocker.
    def test_16_cryptojni_004_preb004_flag_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "cryptojni_candidate" and r.get("candidate_id") == "ANOX-CRYPTOJNI-CANDIDATE-004":
                r["pre_b004_blocker"] = True
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "pre_b004")

    # 17. Silently overwrite consensus ROOT-013 severity LOW -> MEDIUM.
    def test_17_root013_silent_severity_overwrite_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "consensus_root" and r.get("root_id") == "ROOT-013":
                r["severity"] = "MEDIUM"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "silently overwritten")

    # 18. Remove the build-provenance limitation record.
    def test_18_removed_provenance_limitation_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if r.get("record_type") != "provenance_limitation"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "provenance_limitation")

    # 19. Replace the recorded temporary arm64 build hash.
    def test_19_replaced_temp_arm64_hash_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "temp_build_evidence":
                r["outputs"]["arm64-v8a"]["sha256"] = "0" * 64
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "temp_build_evidence")

    # 20. Claim no JNI ABI revision is required.
    def test_20_abi_revision_denied_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "abi_revision":
                r["jni_abi_revision"] = "NO"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "JNI_ABI_REVISION")

    # 21. Mark the Auth/DPoP audit gate executed.
    def test_21_auth_dpop_executed_fails(self):
        tp = self.root / "docs/workforce/registries/tasks.jsonl"
        recs = _load_jsonl(tp)
        recs.append({
            "task_id": "ANOX-TASK-SECURITY-AUTH-DPOP-001",
            "title": "AUDIT-SECURITY-AUTH-DPOP-001",
            "status": "Closed",
            "branch": "audit/security-auth-dpop",
            "role_id": "ROLE-009",
        })
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "must remain Candidate")

    # 22. Delete the preserved Auth/DPoP report.
    def test_22_deleted_authdpop_report_fails(self):
        (self.root / "docs/reports/security/audits/AUDIT-SECURITY-AUTH-DPOP-001.md").unlink()
        self.assert_fails(self.run_validator(), "missing")

    # 23. Mutate the preserved Auth/DPoP report bytes.
    def test_23_mutated_authdpop_report_fails(self):
        p = self.root / "docs/reports/security/audits/AUDIT-SECURITY-AUTH-DPOP-001.md"
        with open(p, "ab") as f:
            f.write(b"\n tampered")
        self.assert_fails(self.run_validator(), "hash mismatch")

    # 24. Wrong recorded hash for the Auth/DPoP report.
    def test_24_wrong_authdpop_hash_fails(self):
        hp = self.root / "docs/security/audit-evidence/evidence_hashes.json"
        data = json.loads(hp.read_text(encoding="utf-8"))
        data["reports"]["AUDIT-SECURITY-AUTH-DPOP-001"]["sha256"] = "0" * 64
        hp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        self.assert_fails(self.run_validator())

    # 25. Drop the Auth/DPoP registry record (7 -> 6 audits).
    def test_25_dropped_authdpop_registry_record_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = [r for r in _load_jsonl(rp) if r.get("audit_id") != "AUDIT-SECURITY-AUTH-DPOP-001"]
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "exactly 7 audits")

    # 26. Alter the Auth/DPoP audited SHA.
    def test_26_altered_authdpop_audited_sha_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == "AUDIT-SECURITY-AUTH-DPOP-001":
                r["audited_sha"] = "0" * 40
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "audited_sha")

    # 27. Rewrite the Auth/DPoP result as a clean PASS.
    def test_27_altered_authdpop_result_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == "AUDIT-SECURITY-AUTH-DPOP-001":
                r["result"] = "PASS"
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "result")

    # 28. Remove an Auth/DPoP candidate from traceability.
    def test_28_removed_authdpop_candidate_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if not (r.get("record_type") == "authdpop_candidate" and r.get("candidate_id") == "ANOX-AUTHDPOP-CANDIDATE-003")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "Auth/DPoP")

    # 29. Remove an Auth/DPoP architecture gap.
    def test_29_removed_authdpop_gap_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if not (r.get("record_type") == "authdpop_gap" and r.get("gap_id") == "ANOX-AUTHDPOP-GAP-002")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "gaps")

    # 30. Forge the wrong source audit on an Auth/DPoP candidate.
    def test_30_wrong_source_audit_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "authdpop_candidate" and r.get("candidate_id") == "ANOX-AUTHDPOP-CANDIDATE-001":
                r["source_audit_id"] = "AUDIT-SECURITY-CRYPTO-JNI-001"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "source_audit_id")

    # 31. Fabricate executed state for a non-executed specialist gate.
    def test_31_fabricated_executed_gate_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "next_gate":
                r["status"] = "EXECUTED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "NOT_EXECUTED")

    # 32. Alter the Auth/DPoP model metadata.
    def test_32_altered_authdpop_model_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == "AUDIT-SECURITY-AUTH-DPOP-001":
                r["actual_model"] = "Claude Opus 5 High"
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "actual_model")

    # 33. Inflate the Auth/DPoP candidate count.
    def test_33_inflated_authdpop_count_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == "AUDIT-SECURITY-AUTH-DPOP-001":
                r["candidate_count"] = 4
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "candidate_count")

    # 34. Wrong next gate: keep AUTH-DPOP as the post-merge gate.
    def test_34_stale_next_gate_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["next_phase"] = "AUDIT-SECURITY-AUTH-DPOP-001"
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        self.assert_fails(self.run_validator(), "next_phase")

    # 35. Unblock product development.
    def test_35_product_unblocked_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["product_development_state"] = "UNBLOCKED"
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        self.assert_fails(self.run_validator(), "BLOCKED_PENDING_FINAL_AUDIT")

    # 36. Mark the Android/Storage gate executed in completed_audit_ids.
    def test_36_android_storage_marked_completed_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["final_pre_product_audit"]["completed_audit_ids"].append("AUDIT-SECURITY-ANDROID-STORAGE-001")
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        self.assert_fails(self.run_validator(), "must NOT be in completed_audit_ids")

    # 37. Drop the preservation-003 task record.
    def test_37_dropped_task_record_fails(self):
        tp = self.root / "docs/workforce/registries/tasks.jsonl"
        recs = [r for r in _load_jsonl(tp) if r.get("task_id") != "ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-003"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "missing from tasks.jsonl")

    # 38. Forge a wrong gate member (drop a PRE_B004_AUTHDPOP member).
    def test_38_wrong_preb004_authdpop_gate_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "gate_set" and r.get("gate_set") == "PRE_B004_AUTHDPOP":
                r["members"] = [m for m in r["members"] if m != "ANOX-AUTHDPOP-GAP-003"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "PRE_B004_AUTHDPOP")

    # 39. Re-severity Auth/DPoP CANDIDATE-001 MEDIUM -> HIGH.
    def test_39_reseveritized_authdpop_001_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "authdpop_candidate" and r.get("candidate_id") == "ANOX-AUTHDPOP-CANDIDATE-001":
                r["severity"] = "HIGH"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "severity")

    # 40. Corrupt the Auth/DPoP coverage counts.
    def test_40_corrupted_authdpop_coverage_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "authdpop_coverage":
                r["architecture_requirements_total"] = 39
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "40")

    # 41. Break the ledger event chain (last event != ANOX-EVENT-0047).
    def test_41_stale_project_memory_fails(self):
        lp = self.root / "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl"
        recs = _load_jsonl(lp)
        recs = recs[:-1]
        _write_jsonl(lp, recs)
        self.assert_fails(self.run_validator(), "Project Memory stale")


if __name__ == "__main__":
    unittest.main()
