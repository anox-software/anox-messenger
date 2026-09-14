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
    "docs/reports/security/audits/AUDIT-SECURITY-ANDROID-STORAGE-001.md",
    "docs/reports/security/audits/AUDIT-SECURITY-ATTACKCHAIN-001.md",
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
        self.assert_fails(self.run_validator(), "exactly 9 audits")

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

    # 25. Drop the Auth/DPoP registry record (8 -> 7 audits).
    def test_25_dropped_authdpop_registry_record_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = [r for r in _load_jsonl(rp) if r.get("audit_id") != "AUDIT-SECURITY-AUTH-DPOP-001"]
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "exactly 9 audits")

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

    # 34. Wrong next gate: regress to a stale specialist audit gate.
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

    # 36. Post-merge gate regressed to a non-consolidation candidate.
    def test_36_post_merge_gate_regressed_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["post_merge_state"]["current_gate"] = "AUDIT-SECURITY-ANDROID-STORAGE-001 — Candidate"
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        self.assert_fails(self.run_validator(), "post_merge_state")

    # 37. Preservation-005 task record marked with a non-delivery status.
    def test_37_task_status_mutated_fails(self):
        tp = self.root / "docs/workforce/registries/tasks.jsonl"
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("task_id") == "ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-005":
                r["status"] = "Closed"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "Ready For Remote")

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

    # 41. Break the ledger event chain (last event != ANOX-EVENT-0048).
    def test_41_stale_project_memory_fails(self):
        lp = self.root / "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl"
        recs = _load_jsonl(lp)
        recs = recs[:-1]
        _write_jsonl(lp, recs)
        self.assert_fails(self.run_validator(), "Project Memory stale")

    # 42. Delete the preserved Android/Storage report.
    def test_42_deleted_androidstorage_report_fails(self):
        (self.root / "docs/reports/security/audits/AUDIT-SECURITY-ANDROID-STORAGE-001.md").unlink()
        self.assert_fails(self.run_validator(), "missing")

    # 43. Mutate the preserved Android/Storage report bytes.
    def test_43_mutated_androidstorage_report_fails(self):
        p = self.root / "docs/reports/security/audits/AUDIT-SECURITY-ANDROID-STORAGE-001.md"
        with open(p, "ab") as f:
            f.write(b"\n tampered")
        self.assert_fails(self.run_validator(), "hash mismatch")

    # 44. Wrong recorded hash for the Android/Storage report.
    def test_44_wrong_androidstorage_hash_fails(self):
        hp = self.root / "docs/security/audit-evidence/evidence_hashes.json"
        data = json.loads(hp.read_text(encoding="utf-8"))
        data["reports"]["AUDIT-SECURITY-ANDROID-STORAGE-001"]["sha256"] = "0" * 64
        hp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        self.assert_fails(self.run_validator())

    # 45. Drop the Android/Storage registry record (8 -> 7 audits).
    def test_45_dropped_androidstorage_registry_record_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = [r for r in _load_jsonl(rp) if r.get("audit_id") != "AUDIT-SECURITY-ANDROID-STORAGE-001"]
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "exactly 9 audits")

    # 46. Alter the Android/Storage audited SHA.
    def test_46_altered_androidstorage_audited_sha_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == "AUDIT-SECURITY-ANDROID-STORAGE-001":
                r["audited_sha"] = "0" * 40
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "audited_sha")

    # 47. Remove an Android/Storage candidate from traceability.
    def test_47_removed_androidstorage_candidate_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if not (r.get("record_type") == "androidstorage_candidate" and r.get("candidate_id") == "ANOX-ANDROIDSTORAGE-CANDIDATE-002")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "Android/Storage")

    # 48. Remove an Android/Storage architecture gap.
    def test_48_removed_androidstorage_gap_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if not (r.get("record_type") == "androidstorage_gap" and r.get("gap_id") == "ANOX-ANDROIDSTORAGE-GAP-002")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "gaps")

    # 49. Forge the wrong source audit on an Android/Storage candidate.
    def test_49_wrong_androidstorage_source_audit_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "androidstorage_candidate" and r.get("candidate_id") == "ANOX-ANDROIDSTORAGE-CANDIDATE-001":
                r["source_audit_id"] = "AUDIT-SECURITY-AUTH-DPOP-001"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "source_audit_id")

    # 50. Re-severity an Android/Storage candidate LOW -> MEDIUM.
    def test_50_reseveritized_androidstorage_001_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "androidstorage_candidate" and r.get("candidate_id") == "ANOX-ANDROIDSTORAGE-CANDIDATE-001":
                r["severity"] = "MEDIUM"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "severity")

    # 51. Wrong specialist relation (downgrade ROOT-007 expansion to CONFIRMED).
    def test_51_downgraded_androidstorage_relation_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "specialist_relation" and r.get("source_audit_id") == "AUDIT-SECURITY-ANDROID-STORAGE-001" and r.get("root_id") == "ROOT-007":
                r["relation"] = "CONFIRMED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "CONFIRMED_AND_EXPANDED")

    # 52. Drop a PRE_B004_ANDROIDSTORAGE gate member.
    def test_52_wrong_preb004_androidstorage_gate_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "gate_set" and r.get("gate_set") == "PRE_B004_ANDROIDSTORAGE":
                r["members"] = [m for m in r["members"] if m != "ANOX-ANDROIDSTORAGE-GAP-003 (contract)"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "PRE_B004_ANDROIDSTORAGE")

    # 53. Corrupt the Android/Storage coverage counts.
    def test_53_corrupted_androidstorage_coverage_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "androidstorage_coverage":
                r["architecture_requirements_total"] = 41
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "42")

    # 54. Swap the inventory/executed counts (153 <-> 177 confusion).
    def test_54_swapped_androidstorage_counts_fail(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "androidstorage_coverage":
                r["focused_test_inventory"]["total"] = 177
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "153")

    # 55. Mark the Master Specialist Consolidation gate executed in completed_audit_ids.
    def test_55_consolidation_marked_completed_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["final_pre_product_audit"]["completed_audit_ids"].append("MASTER-SPECIALIST-CONSOLIDATION")
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        self.assert_fails(self.run_validator(), "must NOT be in completed_audit_ids")

    # 56. Drop Attackchain from completed_audit_ids (executed+preserved required).
    def test_56_attackchain_dropped_completed_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["final_pre_product_audit"]["completed_audit_ids"] = [
            a for a in ws["final_pre_product_audit"]["completed_audit_ids"]
            if a != "AUDIT-SECURITY-ATTACKCHAIN-001"
        ]
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        self.assert_fails(self.run_validator(), "AUDIT-SECURITY-ATTACKCHAIN-001")

    # 57. Stale next gate: keep ATTACKCHAIN as the post-merge gate.
    def test_57_stale_next_gate_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["next_phase"] = "AUDIT-SECURITY-ATTACKCHAIN-001"
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        self.assert_fails(self.run_validator(), "next_phase")

    # 58. Drop the preservation-005 task record.
    def test_58_dropped_task_record_fails(self):
        tp = self.root / "docs/workforce/registries/tasks.jsonl"
        recs = [r for r in _load_jsonl(tp) if r.get("task_id") != "ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-005"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "missing from tasks.jsonl")

    # 59. Strip an EVENT-0048 relationship note from a revalidated finding.
    def test_59_missing_event0048_note_fails(self):
        fp = self.root / "docs/workforce/registries/findings.jsonl"
        recs = _load_jsonl(fp)
        for r in recs:
            if r.get("finding_id") == "ANOX-MAINARCH-023":
                r["notes"] = "no event note"
        _write_jsonl(fp, recs)
        self.assert_fails(self.run_validator(), "ANOX-EVENT-0048")

    # 60. Remove the Android/Storage attackchain handoff record.
    def test_60_removed_androidstorage_handoff_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if not (r.get("record_type") == "attackchain_handoff" and r.get("source_audit_id") == "AUDIT-SECURITY-ANDROID-STORAGE-001")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "attackchain_handoff")

    # 61. Claim the Android/Storage physical campaign executed.
    def test_61_androidstorage_physical_executed_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "physical_evidence_requirements" and r.get("source_audit_id") == "AUDIT-SECURITY-ANDROID-STORAGE-001":
                r["status"] = "EXECUTED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "NOT_EXECUTED")


    # --- PRESERVATION-005: 30 attackchain mutations (62-91) ---
    AC = "AUDIT-SECURITY-ATTACKCHAIN-001"
    ACAND = "ANOX-ATTACKCHAIN-CANDIDATE-"

    def _ac_mut(self, cid, **kv):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "attackchain_candidate" and r.get("chain_id") == cid:
                r.update(kv)
        _write_jsonl(tp, recs)

    def _ac_get(self, rtype):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        return tp, recs, next(r for r in recs if r.get("record_type") == rtype
                              and r.get("source_audit_id") == self.AC)

    # 62. Delete the preserved Attackchain report.
    def test_62_deleted_attackchain_report_fails(self):
        (self.root / "docs/reports/security/audits/AUDIT-SECURITY-ATTACKCHAIN-001.md").unlink()
        self.assert_fails(self.run_validator(), "missing")

    # 63. Mutate the preserved Attackchain report bytes.
    def test_63_mutated_attackchain_report_fails(self):
        p = self.root / "docs/reports/security/audits/AUDIT-SECURITY-ATTACKCHAIN-001.md"
        with open(p, "ab") as f:
            f.write(b"\n tampered")
        self.assert_fails(self.run_validator(), "hash mismatch")

    # 64. Wrong recorded hash for the Attackchain report.
    def test_64_wrong_attackchain_hash_fails(self):
        hp = self.root / "docs/security/audit-evidence/evidence_hashes.json"
        data = json.loads(hp.read_text(encoding="utf-8"))
        data["reports"]["AUDIT-SECURITY-ATTACKCHAIN-001"]["sha256"] = "0" * 64
        hp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        self.assert_fails(self.run_validator())

    # 65. Drop the Attackchain registry record (9 -> 8 audits).
    def test_65_dropped_attackchain_registry_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = [r for r in _load_jsonl(rp) if r.get("audit_id") != "AUDIT-SECURITY-ATTACKCHAIN-001"]
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "exactly 9 audits")

    # 66. Inflate the Attackchain chain count.
    def test_66_inflated_attackchain_chain_count_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == "AUDIT-SECURITY-ATTACKCHAIN-001":
                r["chain_count"] = 16
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "chain_count")

    # 67. Mutate the recorded severity distribution (4H -> 5H).
    def test_67_attackchain_severity_count_fails(self):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == "AUDIT-SECURITY-ATTACKCHAIN-001":
                r["high_count"] = 5
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "high_count")

    # 68. Missing chain ID: drop AC-007 from traceability.
    def test_68_missing_attackchain_candidate_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if not (r.get("record_type") == "attackchain_candidate" and r.get("chain_id") == "ANOX-ATTACKCHAIN-CANDIDATE-007")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "15 chains")

    # 69. Duplicate chain ID: append a second AC-002 record.
    def test_69_duplicate_attackchain_candidate_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        dup = next(r for r in recs if r.get("record_type") == "attackchain_candidate" and r.get("chain_id") == "ANOX-ATTACKCHAIN-CANDIDATE-002")
        recs.append(dict(dup))
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator())

    # 70. Re-severity AC-001 HIGH -> CRITICAL.
    def test_70_attackchain_severity_mutation_fails(self):
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-001", severity="CRITICAL")
        self.assert_fails(self.run_validator(), "severity")

    # 71. Evidence-level mutation: AC-013 E0 -> E2.
    def test_71_attackchain_evidence_level_fails(self):
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-013", evidence_level="E2")
        self.assert_fails(self.run_validator(), "evidence_level")

    # 72. Attacker class removed from AC-003.
    def test_72_attackchain_attacker_class_fails(self):
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-003", attacker_class=None)
        self.assert_fails(self.run_validator(), "attacker_class")

    # 73. Activation gate removed from AC-006.
    def test_73_attackchain_activation_gate_fails(self):
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-006", activation_gate=None)
        self.assert_fails(self.run_validator(), "activation_gate")

    # 74. State transitions emptied on AC-001.
    def test_74_attackchain_state_transitions_fails(self):
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-001", state_transitions=[])
        # state_transitions emptied must also drop impact semantics; validator checks impact separately,
        # so empty transitions + no mitigations must fail
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-001", current_mitigations=None)
        self.assert_fails(self.run_validator())

    # 75. Impact emptied on AC-005.
    def test_75_attackchain_impact_fails(self):
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-005", impact=None)
        self.assert_fails(self.run_validator(), "impact")

    # 76. Mitigations emptied on AC-009 (chain_breakers + current_mitigations).
    def test_76_attackchain_mitigations_fails(self):
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-009", chain_breakers=[], current_mitigations=None)
        self.assert_fails(self.run_validator(), "chain_breakers")

    # 77. Server breaker S7 deleted.
    def test_77_attackchain_server_breaker_deleted_fails(self):
        tp, recs, rec = self._ac_get("attackchain_server_breakers")
        rec["items"] = [i for i in rec["items"] if i.get("id") != "S7"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "S1-S18")

    # 78. Client breaker C6 control text altered.
    def test_78_attackchain_client_breaker_altered_fails(self):
        tp, recs, rec = self._ac_get("attackchain_client_breakers")
        rec["items"] = [i for i in rec["items"] if i.get("id") != "C6"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "C1-C14")

    # 79. Cross-group fix dependency record deleted.
    def test_79_attackchain_cross_group_deleted_fails(self):
        tp = self.root / TRACE
        recs = [r for r in _load_jsonl(tp) if r.get("record_type") != "attackchain_cross_group_dependencies"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "cross_group")

    # 80. Whole-chain regression test + retest owner deleted.
    def test_80_attackchain_test_retest_owner_fails(self):
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-012", required_test=None)
        self._ac_mut("ANOX-ATTACKCHAIN-CANDIDATE-014", independent_retest_owner=None)
        self.assert_fails(self.run_validator(), "retest")

    # 81. Rejected-chain set shrunk (13 -> 12).
    def test_81_attackchain_rejected_mutation_fails(self):
        tp, recs, rec = self._ac_get("attackchain_rejected")
        rec["hypotheses"] = rec["hypotheses"][:-1]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "13 rejected")

    # 82. ROOT-016 coverage disposition mutated (revival attempt).
    def test_82_attackchain_root016_revived_fails(self):
        tp, recs, rec = self._ac_get("attackchain_root_coverage")
        rec["roots"]["ROOT-016"]["disposition"] = "CONFIRMED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "ROOT-016")

    # 83. Root coverage record shrunk (18 -> 17).
    def test_83_attackchain_root_coverage_shrunk_fails(self):
        tp, recs, rec = self._ac_get("attackchain_root_coverage")
        del rec["roots"]["ROOT-001"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "18 roots")

    # 84. Specialist-candidate coverage disposition mutated.
    def test_84_attackchain_specialist_coverage_fails(self):
        tp, recs, rec = self._ac_get("attackchain_specialist_coverage")
        rec["candidates"]["ANOX-CRYPTOJNI-CANDIDATE-003"]["disposition"] = "NOT_CHAIN_RELEVANT"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "CRYPTOJNI-CANDIDATE-003")

    # 85. Gap coverage: AUTHDPOP-GAP-002 CHAIN_CRITICAL -> CHAIN_RELEVANT.
    def test_85_attackchain_gap_coverage_fails(self):
        tp, recs, rec = self._ac_get("attackchain_gap_coverage")
        rec["gaps"]["ANOX-AUTHDPOP-GAP-002"]["classification"] = "CHAIN_RELEVANT - ENABLING_CONDITION_ONLY"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "GAP-002")

    # 86. 68-item participation mutated (unmapped 0 -> 1).
    def test_86_attackchain_participation_fails(self):
        tp, recs, rec = self._ac_get("attackchain_participation")
        rec["unmapped"] = 1
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "unmapped")

    # 87. Pre-B004 contract gate member dropped.
    def test_87_attackchain_preb004_gate_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "gate_set" and r.get("gate_set") == "PRE_B004_ATTACKCHAIN_CONTRACT":
                r["members"] = [m for m in r["members"] if not m.startswith("ANOX-AUTHDPOP-GAP-002")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "PRE_B004_ATTACKCHAIN_CONTRACT")

    # 88. Later-gate set member dropped.
    def test_88_attackchain_later_gate_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "gate_set" and r.get("gate_set") == "LATER_GATE_ATTACKCHAINS":
                r["members"] = [m for m in r["members"] if not m.startswith("AC-013")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "LATER_GATE_ATTACKCHAINS")

    # 89. Master consolidation handoff marked EXECUTED.
    def test_89_attackchain_master_handoff_fails(self):
        tp, recs, rec = self._ac_get("master_consolidation_handoff")
        rec["status"] = "EXECUTED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "NOT_EXECUTED")

    # 90. Remediation-coverage handoff shrunk (15 -> 14 chains).
    def test_90_attackchain_remediation_handoff_fails(self):
        tp, recs, rec = self._ac_get("remediation_coverage_handoff")
        rec["chains"].pop("ANOX-ATTACKCHAIN-CANDIDATE-015", None)
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "15 chains")

    # 91. Lifecycle/task evidence mutations: source_status flipped, product-change claim, consolidation executed.
    def test_91_attackchain_source_and_lifecycle_fails(self):
        tp = self.root / TRACE
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("record_type") == "source_status" and r.get("audit_id") == "AUDIT-SECURITY-ATTACKCHAIN-001":
                r["source_present"] = "NO"
        _write_jsonl(tp, recs)
        r1 = self.run_validator()
        self.assertIn("FAIL", r1.stdout)
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["post_merge_state"]["current_gate"] = "MASTER-SPECIALIST-CONSOLIDATION — EXECUTED"
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        r2 = self.run_validator()
        self.assertIn("FAIL", r2.stdout)
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == "AUDIT-SECURITY-ATTACKCHAIN-001":
                r["repository_modified_by_audit"] = "YES"
        _write_jsonl(rp, recs)
        self.assert_fails(self.run_validator(), "repository_modified_by_audit")


if __name__ == "__main__":
    unittest.main()
