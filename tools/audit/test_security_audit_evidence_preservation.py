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
    "docs/reports/security/consolidation/MASTER-SPECIALIST-CONSOLIDATION-001.md",
    "docs/reports/security/gates/SECURITY-REMEDIATION-COVERAGE-GATE-001.md",
    "docs/reports/security/decisions/HUMAN-PRE-REMEDIATION-DECISIONS-001.md",
    "docs/workforce/WORKFORCE_STATE.json",
    "docs/workforce/registries/findings.jsonl",
    "docs/workforce/registries/tasks.jsonl",
    "docs/workforce/registries/decisions.jsonl",
    "docs/workforce/registries/implementation_readiness.json",
    "docs/continuity/CURRENT_STATE.json",
    "docs/continuity/CURRENT_HANDOFF.md",
    "docs/continuity/CURRENT_GIT_STATE.md",
    "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
    # retired one-shot validators (must exist + keep their integrity pins)
    "tools/audit/validate_security_architecture_findings_freeze.py",
    "tools/audit/validate_legacy_retest01_ingest.py",
    "tools/audit/validate_mainarch_fix03.py",
    "tools/audit/validate_mainarch_retest01_ingest.py",
    "tools/audit/validate_mainarch_retest02_ingest.py",
    "tools/audit/validate_mainarch_retest03_ingest.py",
    "tools/audit/validate_workforce_fix01.py",
    "tools/audit/validate_workforce_fix02.py",
    "tools/audit/validate_workforce_retest_closure_ingest.py",
    "tools/audit/validate_workforce_continuity_sync_fix01.py",
    # active current-state validators (must exist)
    "tools/audit/validate_security_audit_evidence_preservation.py",
    "tools/continuity/validate_continuity.py",
    "tools/workforce/validate_b027a.py",
    "tools/workforce/validate_b027b.py",
    "tools/workforce/validate_b027_integrity.py",
    "tools/security/b017_lite_policy_validator.py",
    "tools/audit/validate_mainarch_fix01.py",
    "tools/audit/validate_mainarch_fix02.py",
    "tools/audit/validate_legacy_fix01.py",
    "tools/audit/validate_legacy_audit_consolidation.py",
    "tools/audit/validate_workforce_audit_findings_freeze.py",
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
        self.assert_fails(self.run_validator(), "exactly 12 records")

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
        self.assert_fails(self.run_validator(), "exactly 12 records")

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

    # 37. Coverage-gate preservation task record marked with a non-delivery status.
    def test_37_task_status_mutated_fails(self):
        tp = self.root / "docs/workforce/registries/tasks.jsonl"
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("task_id") == "ANOX-TASK-HUMAN-PRE-REMEDIATION-DECISIONS-001":
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
        self.assert_fails(self.run_validator(), "exactly 12 records")

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

    # 55. Mark the human pre-remediation decision gate executed in completed_audit_ids.
    def test_55_consolidation_marked_completed_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["final_pre_product_audit"]["completed_audit_ids"].append("SECURITY_REMEDIATION_WAVE_1")
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

    # 58. Drop the coverage-gate preservation task record.
    def test_58_dropped_task_record_fails(self):
        tp = self.root / "docs/workforce/registries/tasks.jsonl"
        recs = [r for r in _load_jsonl(tp) if r.get("task_id") != "ANOX-TASK-HUMAN-PRE-REMEDIATION-DECISIONS-001"]
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
        self.assert_fails(self.run_validator(), "exactly 12 records")

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

    # ------------------------------------------------------------------
    # MASTER-SPECIALIST-CONSOLIDATION-001 adversarial cases (92..141)
    # ------------------------------------------------------------------
    MSC = "MASTER-SPECIALIST-CONSOLIDATION-001"
    MSC_REPORT = "docs/reports/security/consolidation/MASTER-SPECIALIST-CONSOLIDATION-001.md"

    def _msc_recs(self):
        tp = self.root / TRACE
        return tp, _load_jsonl(tp)

    def _msc_one(self, rt):
        recs = _load_jsonl(self.root / TRACE)
        return next((r for r in recs if r.get("record_type") == rt and r.get("source_artifact_id") == self.MSC), None)

    def _msc_mutate_one(self, rt, mutator):
        tp, recs = self._msc_recs()
        for r in recs:
            if r.get("record_type") == rt and r.get("source_artifact_id") == self.MSC:
                mutator(r)
        _write_jsonl(tp, recs)
        return self.run_validator()

    def _msc_mutate_unit(self, uid, mutator):
        tp, recs = self._msc_recs()
        for r in recs:
            if r.get("record_type") == "msc_unit" and r.get("msc_unit_id") == uid:
                mutator(r)
        _write_jsonl(tp, recs)
        return self.run_validator()

    def _registry_mutate(self, mutator):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == self.MSC:
                mutator(r)
        _write_jsonl(rp, recs)
        return self.run_validator()

    # 92. Master consolidation report truncated (content mutation -> hash mismatch).
    def test_92_msc_report_truncated_fails(self):
        p = self.root / self.MSC_REPORT
        p.write_bytes(p.read_bytes()[:-4096])
        self.assert_fails(self.run_validator(), "hash mismatch")

    # 93. Master consolidation report deleted.
    def test_93_msc_report_deleted_fails(self):
        (self.root / self.MSC_REPORT).unlink()
        self.assert_fails(self.run_validator(), "missing")

    # 94. evidence_hashes entry for the consolidation report altered.
    def test_94_msc_hash_entry_altered_fails(self):
        hp = self.root / "docs/security/audit-evidence/evidence_hashes.json"
        h = json.loads(hp.read_text(encoding="utf-8"))
        h["reports"][self.MSC]["sha256"] = "0" * 64
        hp.write_text(json.dumps(h, indent=1), encoding="utf-8")
        self.assert_fails(self.run_validator())

    # 95. Registry artifact_type changed away from MASTER_SECURITY_CONSOLIDATION.
    def test_95_msc_registry_artifact_type_fails(self):
        self.assert_fails(self._registry_mutate(lambda r: r.update(artifact_type="AUDIT")), "artifact_type")

    # 96. Registry base/audited SHA wrong.
    def test_96_msc_registry_base_sha_fails(self):
        self.assert_fails(self._registry_mutate(lambda r: r.update(base_sha="e54584903a353e98ad154d1e8f90f93ed9d7db14")), "base_sha")
        self.assert_fails(self._registry_mutate(lambda r: r.update(audited_sha="0" * 40)), "audited_sha")

    # 97. Registry result mutated.
    def test_97_msc_registry_result_fails(self):
        self.assert_fails(self._registry_mutate(lambda r: r.update(result="PASS")), "result")

    # 98. Registry model mutated.
    def test_98_msc_registry_model_fails(self):
        self.assert_fails(self._registry_mutate(lambda r: r.update(actual_model="Claude Opus 5 High")), "actual_model")

    # 99. Registry unit/source counts mutated.
    def test_99_msc_registry_counts_fails(self):
        self.assert_fails(self._registry_mutate(lambda r: r.update(msc_units=43)), "msc_units")
        self.assert_fails(self._registry_mutate(lambda r: r.update(msc_open=41)), "msc_open")
        self.assert_fails(self._registry_mutate(lambda r: r.update(source_security_items=89)), "source_security_items")

    # 100. One msc_source_item dropped (90 -> 89).
    def test_100_msc_source_item_dropped_fails(self):
        tp, recs = self._msc_recs()
        recs = [r for r in recs if not (r.get("record_type") == "msc_source_item" and r.get("source_id") == "ROOT-017")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "90")

    # 101. A source item rendered unaccounted (empty msc_units).
    def test_101_msc_source_item_unaccounted_fails(self):
        def mut(r):
            if r.get("record_type") == "msc_source_item" and r.get("source_id") == "ROOT-001":
                r["msc_units"] = []
        tp, recs = self._msc_recs()
        for r in recs:
            mut(r)
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "unaccounted")

    # 102. A source item given an unknown disposition.
    def test_102_msc_source_item_unknown_disposition_fails(self):
        tp, recs = self._msc_recs()
        for r in recs:
            if r.get("record_type") == "msc_source_item" and r.get("source_id") == "ROOT-001":
                r["consolidation_disposition"] = "INVENTED_DISPOSITION"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "disposition")

    # 103. Duplicate source_id introduced.
    def test_103_msc_duplicate_source_id_fails(self):
        tp, recs = self._msc_recs()
        dup = dict(next(r for r in recs if r.get("record_type") == "msc_source_item" and r.get("source_id") == "ROOT-001"))
        recs.append(dup)
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator())

    # 104. msc_source_summary totals mutated.
    def test_104_msc_source_summary_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_source_summary", lambda r: r.update(unaccounted=1)), "unaccounted")
        self.assert_fails(self._msc_mutate_one("msc_source_summary", lambda r: r.update(total_source_security_items=91)), "total_source_security_items")

    # 105. One msc_unit dropped (44 -> 43).
    def test_105_msc_unit_dropped_fails(self):
        tp, recs = self._msc_recs()
        recs = [r for r in recs if not (r.get("record_type") == "msc_unit" and r.get("msc_unit_id") == "MSC_UNIT_001")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "MSC_UNIT")

    # 106. msc_unit missing a required field.
    def test_106_msc_unit_missing_field_fails(self):
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_005", lambda r: r.pop("primary_root_cause")), "primary_root_cause")

    # 107. OPEN unit loses provisional_session.
    def test_107_msc_unit_no_session_fails(self):
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_009", lambda r: r.update(provisional_session="")), "provisional_session")

    # 108. OPEN unit loses independent_retest_owners.
    def test_108_msc_unit_no_retest_owner_fails(self):
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_017", lambda r: r.update(independent_retest_owners=[])), "retest_owner")

    # 109. OPEN unit loses all test plans.
    def test_109_msc_unit_no_test_plan_fails(self):
        def m(r):
            r.update(required_automated_tests="", required_instrumented_tests="", required_physical_tests="")
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_021", m), "test plan")

    # 110. OPEN unit loses closure_evidence / gate.
    def test_110_msc_unit_no_closure_or_gate_fails(self):
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_028", lambda r: r.update(closure_evidence=[])), "closure_evidence")
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_028", lambda r: r.update(pre_b004_or_later="")), "gate")

    # 111. Rejected unit MSC_UNIT_043 flipped to OPEN.
    def test_111_msc_unit043_reopened_fails(self):
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_043", lambda r: r.update(proposed_disposition="OPEN_PENDING_REMEDIATION_COVERAGE_GATE")))

    # 112. MSC_UNIT_043 loses its ROOT-016 binding.
    def test_112_msc_unit043_binding_fails(self):
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_043", lambda r: r.update(source_ids=["CS-016"])), "ROOT-016")

    # 113. MSC_UNIT_044 loses its BUILDSC-012 binding.
    def test_113_msc_unit044_binding_fails(self):
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_044", lambda r: r.update(source_ids=["CS-019"])), "BUILDSC-CANDIDATE-012")

    # 114. Rejected unit silently re-severitied to HIGH.
    def test_114_msc_rejected_severity_fails(self):
        self.assert_fails(self._msc_mutate_unit("MSC_UNIT_043", lambda r: r.update(proposed_consolidated_severity="HIGH")), "severity")

    # 115. Severity distribution record mutated.
    def test_115_msc_severity_distribution_fails(self):
        def m(r):
            d = dict(r["distribution"]); d["HIGH"] = 8; r["distribution"] = d
        self.assert_fails(self._msc_mutate_one("msc_severity_distribution", m), "distribution")
        self.assert_fails(self._msc_mutate_one("msc_severity_distribution", lambda r: r.update(open=41)), "open")

    # 116. Severity overlays removed (MSC_UNIT_001 EI / AC-003 conditional).
    def test_116_msc_overlays_removed_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_severity_distribution", lambda r: r["overlays"].pop("MSC_UNIT_001")), "EVIDENCE_INTEGRITY")
        self.assert_fails(self._msc_mutate_one("msc_severity_distribution", lambda r: r["overlays"].pop("ATTACKCHAIN_AC_003")), "conditional-critical")

    # 117. ROOT-013 proposal flipped to canonically mutated.
    def test_117_msc_root013_fails(self):
        def m(r):
            r["roots"]["ROOT-013"]["status"] = "CANONICALLY_MUTATED"
        self.assert_fails(self._msc_mutate_one("msc_root_arbitration", m), "ROOT-013")
        def m2(r):
            r["roots"]["ROOT-013"]["severity"] = "CONFIRMED_NO_CHANGE MEDIUM"
        self.assert_fails(self._msc_mutate_one("msc_root_arbitration", m2), "ROOT-013")

    # 118. ROOT-016 revived inside the arbitration record.
    def test_118_msc_root016_revived_fails(self):
        def m(r):
            r["roots"]["ROOT-016"]["verdict"] = "KEEP_AS_DISTINCT_ROOT"
            r["roots"]["ROOT-016"]["status"] = "OPEN"
        self.assert_fails(self._msc_mutate_one("msc_root_arbitration", m), "ROOT-016")

    # 119. ROOT-017 classification removed.
    def test_119_msc_root017_fails(self):
        def m(r):
            r["roots"]["ROOT-017"]["classification"] = "UNKNOWN"
        self.assert_fails(self._msc_mutate_one("msc_root_arbitration", m), "ROOT-017")

    # 120. Split-root set mutated (ROOT-008 no longer SPLIT_REQUIRED).
    def test_120_msc_split_roots_fails(self):
        def m(r):
            r["roots"]["ROOT-008"]["verdict"] = "KEEP_AS_DISTINCT_ROOT"
        self.assert_fails(self._msc_mutate_one("msc_root_arbitration", m), "split")

    # 121. Specialist candidate arbitration shrunk / permanent-root flag cleared.
    def test_121_msc_spec_candidate_arb_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_specialist_candidate_arbitration", lambda r: r["candidates"].pop("ANOX-AUTHDPOP-CANDIDATE-002")), "candidates")
        self.assert_fails(self._msc_mutate_one("msc_specialist_candidate_arbitration", lambda r: r.update(no_permanent_root_ids_allocated=False)), "permanent")

    # 122. Gap arbitration shrunk / verdict changed.
    def test_122_msc_gap_arb_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_gap_arbitration", lambda r: r["gaps"].pop("ANOX-ANDROIDSTORAGE-GAP-001")), "gaps")
        def m(r):
            r["gaps"]["ANOX-AUTHDPOP-GAP-002"]["verdict"] = "MERGED_AWAY"
        self.assert_fails(self._msc_mutate_one("msc_gap_arbitration", m), "KEEP_DISTINCT_CONTRACT_UNIT")

    # 123. Historical arbitration: original status rewritten.
    def test_123_msc_historical_status_rewrite_fails(self):
        def m(r):
            for row in r["rows"]:
                if row.get("finding_id") == "ANOX-LEGACY-CRYPTO-005":
                    row["original_status"] = "Open"
        self.assert_fails(self._msc_mutate_one("msc_historical_remediation_arbitration", m), "Closed")

    # 124. Historical arbitration: FALSE_CLOSURE interpretation for MAINARCH-031 removed.
    def test_124_msc_historical_false_closure_fails(self):
        def m(r):
            for row in r["rows"]:
                if row.get("finding_id") == "ANOX-MAINARCH-031":
                    row["interpretation"] = "EFFECTIVE"
        self.assert_fails(self._msc_mutate_one("msc_historical_remediation_arbitration", m), "FALSE_CLOSURE")

    # 125. FCP rule dropped (FCP_7 evidence separation).
    def test_125_msc_fcp_dropped_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_false_closure_rules", lambda r: r["rules"].pop("FCP_7")), "FCP")

    # 126. Attackchain mapping: chain dropped (AC-015).
    def test_126_msc_chain_dropped_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_attackchain_mapping", lambda r: r["chains"].pop("ATTACKCHAIN_AC_015")), "15")

    # 127. Attackchain mapping: a chain left without owning units.
    def test_127_msc_chain_unmapped_fails(self):
        def m(r):
            r["chains"]["ATTACKCHAIN_AC_001"]["msc_units"] = []
        self.assert_fails(self._msc_mutate_one("msc_attackchain_mapping", m), "ATTACKCHAIN_AC_001")

    # 128. AC-003 conditional overlay promoted to canonical CRITICAL.
    def test_128_msc_ac003_overlay_fails(self):
        def m(r):
            r["ac003_conditional_overlay"]["canonical_chain_severity"] = "CRITICAL"
        self.assert_fails(self._msc_mutate_one("msc_attackchain_mapping", m), "AC-003")

    # 129. High-chain challenge set mutated.
    def test_129_msc_high_chain_challenge_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_attackchain_mapping", lambda r: r["high_chain_challenge"].pop("ATTACKCHAIN_AC_012")), "high-chain")

    # 130. Server breaker dropped / left unassigned.
    def test_130_msc_server_breaker_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_server_breakers", lambda r: r["items"].pop()), "S1")
        def m(r):
            for i in r["items"]:
                if i["id"] == "SERVER_BREAKER_S1":
                    i["msc_units"] = []
        self.assert_fails(self._msc_mutate_one("msc_server_breakers", m), "SERVER_BREAKER_S1")
        self.assert_fails(self._msc_mutate_one("msc_server_breakers", lambda r: r.update(unassigned=1)), "unassigned")

    # 131. Client breaker dropped / left unassigned.
    def test_131_msc_client_breaker_fails(self):
        def m(r):
            r["items"] = [i for i in r["items"] if i["id"] != "CLIENT_BREAKER_C14"]
        self.assert_fails(self._msc_mutate_one("msc_client_breakers", m), "C14")
        def m2(r):
            for i in r["items"]:
                if i["id"] == "CLIENT_BREAKER_C1":
                    i["msc_units"] = []
        self.assert_fails(self._msc_mutate_one("msc_client_breakers", m2), "CLIENT_BREAKER_C1")

    # 132. Dependency DAG cycles / edges dropped.
    def test_132_msc_dag_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_dependency_dag", lambda r: r.update(unresolved_dependency_cycles=1)), "cycles")
        self.assert_fails(self._msc_mutate_one("msc_dependency_dag", lambda r: r.update(edges=[])), "edges")

    # 133. Remediation session dropped (S2).
    def test_133_msc_session_dropped_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_remediation_sessions", lambda r: r["sessions"].pop("REMEDIATION_SESSION_S2")), "S0..S10")

    # 134. Pre-B004 categories shrunk / emptied.
    def test_134_msc_preb004_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_pre_b004_set", lambda r: r["categories"].pop("A_ARCHITECTURE_CONTRACT")), "categories")
        def m(r):
            r["categories"]["D_VERIFICATION"] = []
        self.assert_fails(self._msc_mutate_one("msc_pre_b004_set", m), "categories")

    # 135. Pre-B004 Definition of Done marked EXECUTED.
    def test_135_msc_dod_executed_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_pre_b004_dod", lambda r: r.update(status="EXECUTED")), "NOT_EXECUTED")

    # 136. Later gate dropped / ownerless later item.
    def test_136_msc_later_gates_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_later_gates", lambda r: r["gates"].pop("PHYSICAL_GRAPHENEOS_FINAL")), "PHYSICAL_GRAPHENEOS_FINAL")
        self.assert_fails(self._msc_mutate_one("msc_later_gates", lambda r: r.update(later_items_without_named_gate=1)), "named_gate")

    # 137. Closure standard rule removed / state machine stage dropped.
    def test_137_msc_closure_fails(self):
        self.assert_fails(self._msc_mutate_one("msc_closure_evidence_standard", lambda r: r.update(rule="code changed = closed")), "CODE_CHANGED_ONLY")
        def m(r):
            r["stages"] = [s for s in r["stages"] if s != "ATTACKCHAIN_RETESTED / NOT_APPLICABLE"]
        self.assert_fails(self._msc_mutate_one("msc_closure_state_machine", m), "stages")

    # 138. Whole-chain mandatory retest set shrunk.
    def test_138_msc_whole_chain_fails(self):
        def m(r):
            r["mandatory"] = [c for c in r["mandatory"] if c != "ATTACKCHAIN_AC_012"]
        self.assert_fails(self._msc_mutate_one("msc_whole_chain_retests", m), "mandatory")

    # 139. Physical campaign shrunk / marked executed.
    def test_139_msc_physical_fails(self):
        def m(r):
            r["items"] = [i for i in r["items"] if i["id"] != "PHYSICAL_P17"]
            r["count"] = 16
        self.assert_fails(self._msc_mutate_one("msc_physical_campaign", m), "P1..P17")
        self.assert_fails(self._msc_mutate_one("msc_physical_campaign", lambda r: r.update(status="EXECUTED")), "NOT_EXECUTED")

    # 140. Coverage losses: architecture unmapped / finding lost / legacy ownerless.
    def test_140_msc_coverage_losses_fail(self):
        def m(r):
            r["android_storage"]["unmapped"] = 1
        self.assert_fails(self._msc_mutate_one("msc_architecture_coverage", m), "42/42")
        self.assert_fails(self._msc_mutate_one("msc_architecture_coverage", lambda r: r.update(architecture_finding_coverage_loss=1)), "coverage_loss")
        self.assert_fails(self._msc_mutate_one("msc_legacy_coverage", lambda r: r.update(legacy_findings_without_current_owner=1)), "without_current_owner")

    # 141. Contracts / precursor / quality gates / findings / verdict / source_status / next_gate mutations.
    def test_141_msc_contracts_precursor_quality_verdict_fail(self):
        self.assert_fails(self._msc_mutate_one("msc_server_contract", lambda r: r["rules"].pop()), "SC-1")
        self.assert_fails(self._msc_mutate_one("msc_server_contract", lambda r: r.update(status="IMPLEMENTED")), "NOT_IMPLEMENTED")
        def mcc(r):
            r["rules"] = [x for x in r["rules"] if x["id"] != "CC-14"]
        self.assert_fails(self._msc_mutate_one("msc_client_contract", mcc), "CC-14")
        self.assert_fails(self._msc_mutate_one("msc_fix_coverage_precursor", lambda r: r.update(open_units=41)), "42")
        self.assert_fails(self._msc_mutate_one("msc_fix_coverage_precursor", lambda r: r.update(unassigned_fix_session=1)), "unassigned_fix_session")
        self.assert_fails(self._msc_mutate_one("msc_quality_gates", lambda r: r["gates"].update(silently_dropped=1)), "silently_dropped")
        self.assert_fails(self._msc_mutate_one("msc_consolidation_findings", lambda r: r.update(result="PASS")), "PASS_WITH_CONSOLIDATION_FINDINGS")
        self.assert_fails(self._msc_mutate_one("msc_consolidation_findings", lambda r: r["reasons"].pop()), "7")
        self.assert_fails(self._msc_mutate_one("msc_verdict", lambda r: r.update(architecture_verdict="COMPONENT_INTERNAL_REDESIGN_ONLY")), "CROSS_COMPONENT")
        self.assert_fails(self._msc_mutate_one("msc_verdict", lambda r: r.update(sec_c_required="YES")), "sec_c")
        self.assert_fails(self._msc_mutate_one("msc_verdict", lambda r: r.update(sec_c_escalation="")), "escalation")
        tp, recs = self._msc_recs()
        for r in recs:
            if r.get("record_type") == "source_status" and r.get("audit_id") == self.MSC:
                r["source_present"] = "NO"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "source_status")
        tp, recs = self._msc_recs()
        for r in recs:
            if r.get("record_type") == "next_gate" and r.get("gate") == "SECURITY-REMEDIATION-COVERAGE-GATE":
                r["status"] = "CANDIDATE / NOT_EXECUTED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "EXECUTED_AND_PRESERVED")

    # ------------------------------------------------------------------
    # SECURITY-REMEDIATION-COVERAGE-GATE-001 adversarial cases (142..201)
    # ------------------------------------------------------------------
    GATE = "SECURITY-REMEDIATION-COVERAGE-GATE-001"
    GATE_REPORT = "docs/reports/security/gates/SECURITY-REMEDIATION-COVERAGE-GATE-001.md"

    def _gate_recs(self):
        tp = self.root / TRACE
        return tp, _load_jsonl(tp)

    def _gate_one(self, rt):
        recs = _load_jsonl(self.root / TRACE)
        return next((r for r in recs if r.get("record_type") == rt and r.get("source_artifact_id") == self.GATE), None)

    def _gate_mutate_one(self, rt, mutator):
        tp, recs = self._gate_recs()
        for r in recs:
            if r.get("record_type") == rt and r.get("source_artifact_id") == self.GATE:
                mutator(r)
        _write_jsonl(tp, recs)
        return self.run_validator()

    def _gate_mutate_unit(self, uid, mutator):
        tp, recs = self._gate_recs()
        for r in recs:
            if r.get("record_type") == "gate_coverage_unit" and r.get("msc_unit") == uid:
                mutator(r)
        _write_jsonl(tp, recs)
        return self.run_validator()

    def _gate_registry_mutate(self, mutator):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == self.GATE:
                mutator(r)
        _write_jsonl(rp, recs)
        return self.run_validator()

    # 142. Gate report truncated (hash mismatch).
    def test_142_gate_report_truncated_fails(self):
        p = self.root / self.GATE_REPORT
        p.write_bytes(p.read_bytes()[:-2048])
        self.assert_fails(self.run_validator(), "hash mismatch")

    # 143. Gate report deleted.
    def test_143_gate_report_deleted_fails(self):
        (self.root / self.GATE_REPORT).unlink()
        self.assert_fails(self.run_validator(), "missing")

    # 144. evidence_hashes entry for the gate report altered.
    def test_144_gate_hash_entry_altered_fails(self):
        hp = self.root / "docs/security/audit-evidence/evidence_hashes.json"
        h = json.loads(hp.read_text(encoding="utf-8"))
        h["reports"][self.GATE]["sha256"] = "0" * 64
        hp.write_text(json.dumps(h, indent=1), encoding="utf-8")
        self.assert_fails(self.run_validator())

    # 145. Registry artifact_type changed away from SECURITY_REMEDIATION_COVERAGE_GATE.
    def test_145_gate_registry_artifact_type_fails(self):
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(artifact_type="AUDIT")), "artifact_type")

    # 146. Registry base/audited SHA wrong.
    def test_146_gate_registry_base_sha_fails(self):
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(base_sha="1eb773069d81ea3d12b76249c73f2f5fb0b6cae9")), "base_sha")
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(audited_sha="0" * 40)), "audited_sha")

    # 147. Registry result mutated away from PASS.
    def test_147_gate_registry_result_fails(self):
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(result="FAIL")), "result")

    # 148. Registry model mutated.
    def test_148_gate_registry_model_fails(self):
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(actual_model="Claude Opus 5 High")), "actual_model")

    # 149. Registry coverage counts mutated.
    def test_149_gate_registry_counts_fail(self):
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(master_units=43)), "master_units")
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(open_units=41)), "open_units")
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(open_units_covered=41)), "open_units_covered")
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(open_units_uncovered=1)), "open_units_uncovered")

    # 150. Registry marked as remediation authorization.
    def test_150_gate_registry_authorization_fails(self):
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(security_remediation_authorized="YES")), "security_remediation_authorized")
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(security_remediation="STARTED")), "security_remediation")

    # 151. Registry preservation event / branch mutated.
    def test_151_gate_registry_event_branch_fails(self):
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(preserved_at_event="ANOX-EVENT-0050")), "preserved_at_event")
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(delivery_branch="governance/master-specialist-consolidation-preservation-001")), "delivery_branch")

    # 152. Registry report binding mutated.
    def test_152_gate_registry_report_binding_fails(self):
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(report_sha256="0" * 64)), "report_sha256")
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(report_bytes=33526)), "report_bytes")
        self.assert_fails(self._gate_registry_mutate(lambda r: r.update(report_path="docs/reports/security/consolidation/MASTER-SPECIALIST-CONSOLIDATION-001.md")), "report_path")

    # 153. One gate_coverage_unit dropped (42 -> 41).
    def test_153_gate_unit_dropped_fails(self):
        tp, recs = self._gate_recs()
        recs = [r for r in recs if not (r.get("record_type") == "gate_coverage_unit" and r.get("msc_unit") == "MSC_UNIT_007")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "MSC_UNIT")

    # 154. Duplicate coverage row introduced.
    def test_154_gate_unit_duplicated_fails(self):
        tp, recs = self._gate_recs()
        dup = dict(next(r for r in recs if r.get("record_type") == "gate_coverage_unit" and r.get("msc_unit") == "MSC_UNIT_001"))
        recs.append(dup)
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator())

    # 155. Row coverage_status flipped away from COVERED.
    def test_155_gate_unit_status_fails(self):
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_005", lambda r: r.update(coverage_status="EXECUTED")), "coverage_status")

    # 156. Conflicting primary execution owner (session split re-arbitrated).
    def test_156_gate_unit_primary_fails(self):
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_005", lambda r: r.update(primary_execution_owner="REMEDIATION_SESSION_S3")), "primary_execution_owner")

    # 157. Ambiguous bare `S3` machine id introduced as an owner.
    def test_157_gate_unit_ambiguous_owner_fails(self):
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_014", lambda r: r.update(primary_execution_owner="S3")))

    # 158. Generic `LATER` gate assigned to a row.
    def test_158_gate_unit_generic_gate_fails(self):
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_030", lambda r: r.update(gate="LATER")), "gate")

    # 159. Unknown gate assigned to a row.
    def test_159_gate_unit_unknown_gate_fails(self):
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_031", lambda r: r.update(gate="B099")), "gate")

    # 160. Row loses its independent retest owner.
    def test_160_gate_unit_no_retest_owner_fails(self):
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_017", lambda r: r.update(independent_retest_owner=[])), "retest")

    # 161. Row loses a required test-plan field.
    def test_161_gate_unit_no_test_plan_fails(self):
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_005", lambda r: r.pop("instrumented_requirement")), "instrumented_requirement")
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_014", lambda r: r.update(physical_requirement="")), "physical_requirement")

    # 162. Row closure stage carries an invalid value.
    def test_162_gate_unit_closure_stage_fails(self):
        self.assert_fails(self._gate_mutate_unit("MSC_UNIT_001", lambda r: r.update(closure_runtime_stage="EXECUTED")), "closure_runtime_stage")

    # 163. Rejected unit gains a remediation/coverage row.
    def test_163_gate_rejected_unit_row_fails(self):
        tp, recs = self._gate_recs()
        row = dict(next(r for r in recs if r.get("record_type") == "gate_coverage_unit" and r.get("msc_unit") == "MSC_UNIT_001"))
        row["msc_unit"] = "MSC_UNIT_043"
        recs.append(row)
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "rejected")

    # 164. Gate verdict flipped / counts mutated.
    def test_164_gate_verdict_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_verdict", lambda r: r.update(result="FAIL")), "result")
        self.assert_fails(self._gate_mutate_one("gate_verdict", lambda r: r.update(open_msc_covered=41)), "open_msc_covered")
        self.assert_fails(self._gate_mutate_one("gate_verdict", lambda r: r.update(unknown=1)), "unknown")

    # 165. Gate verdict dependency cycle / rejected-session counters mutated.
    def test_165_gate_verdict_counters_fail(self):
        self.assert_fails(self._gate_mutate_one("gate_verdict", lambda r: r.update(dependency_cycles=1)), "dependency_cycles")
        self.assert_fails(self._gate_mutate_one("gate_verdict", lambda r: r.update(rejected_with_remediation_session=1)), "rejected_with_remediation_session")

    # 166. Rejected-record disposition mutated (043 revived as finding work).
    def test_166_gate_rejected_disposition_fails(self):
        def m(r):
            r["rejected_records"]["MSC_UNIT_043"]["disposition"] = "OPEN"
        self.assert_fails(self._gate_mutate_one("gate_verdict", m), "disposition")
        def m2(r):
            r["rejected_records"]["MSC_UNIT_043"]["remediation_required"] = "YES"
        self.assert_fails(self._gate_mutate_one("gate_verdict", m2), "remediation")

    # 167. Rejected-record source bindings lost (ROOT-016 / BUILDSC-012).
    def test_167_gate_rejected_binding_fails(self):
        def m(r):
            r["rejected_records"]["MSC_UNIT_043"]["source"] = "CS-016"
        self.assert_fails(self._gate_mutate_one("gate_verdict", m), "ROOT-016")
        def m2(r):
            r["rejected_records"]["MSC_UNIT_044"]["source"] = "CS-019"
        self.assert_fails(self._gate_mutate_one("gate_verdict", m2), "BUILDSC-012")

    # 168. Zero-metric fields mutated.
    def test_168_gate_zero_metrics_fail(self):
        self.assert_fails(self._gate_mutate_one("gate_zero_metrics", lambda r: r.update(uncovered_open_msc_units=1)), "uncovered_open_msc_units")
        self.assert_fails(self._gate_mutate_one("gate_zero_metrics", lambda r: r.update(parallel_writer_collisions=1)), "parallel_writer_collisions")
        self.assert_fails(self._gate_mutate_one("gate_zero_metrics", lambda r: r.update(unmapped_contract_items=1)), "unmapped_contract_items")
        self.assert_fails(self._gate_mutate_one("gate_zero_metrics", lambda r: r.update(fcp_escapes=1)), "fcp_escapes")

    # 169. Severity coverage shrunk.
    def test_169_gate_severity_coverage_fails(self):
        def m(r):
            r["coverage"]["HIGH"]["covered"] = 6
        self.assert_fails(self._gate_mutate_one("gate_severity_coverage", m), "HIGH")

    # 170. Pre-B004 category coverage shrunk / DoD marked executed.
    def test_170_gate_category_coverage_fails(self):
        def m(r):
            r["categories"]["A_ARCHITECTURE_CONTRACT"]["covered"] = 10
        self.assert_fails(self._gate_mutate_one("gate_pre_b004_category_coverage", m), "A_ARCHITECTURE_CONTRACT")
        self.assert_fails(self._gate_mutate_one("gate_pre_b004_category_coverage", lambda r: r.update(dod_status="EXECUTED")), "NOT_EXECUTED")

    # 171. Later-gate coverage shrunk / unnamed later item introduced.
    def test_171_gate_later_coverage_fails(self):
        def m(r):
            r["gates"]["B013"]["covered"] = 3
        self.assert_fails(self._gate_mutate_one("gate_later_gate_coverage", m), "B013")
        self.assert_fails(self._gate_mutate_one("gate_later_gate_coverage", lambda r: r.update(unnamed_later_items=1)), "unnamed_later_items")

    # 172. Execution session dropped (S2).
    def test_172_gate_session_dropped_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_execution_sessions", lambda r: r["sessions"].pop("REMEDIATION_SESSION_S2")), "S0")

    # 173. S2 ordering violated (MSC_UNIT_008 no longer last).
    def test_173_gate_s2_order_fails(self):
        def m(r):
            o = r["sessions"]["REMEDIATION_SESSION_S2"]["execution_order"]
            o.append("MSC_UNIT_009 late re-run")
        self.assert_fails(self._gate_mutate_one("gate_execution_sessions", m), "LAST")

    # 174. S3 writes to CryptoBridge.kt (S2-owned file).
    def test_174_gate_s3_forbidden_file_fails(self):
        def m(r):
            r["sessions"]["REMEDIATION_SESSION_S3"]["files_forbidden"] = []
        self.assert_fails(self._gate_mutate_one("gate_execution_sessions", m), "CryptoBridge")

    # 175. Session record loses a boundary field.
    def test_175_gate_session_field_fails(self):
        def m(r):
            r["sessions"]["REMEDIATION_SESSION_S5"].pop("files_owned")
        self.assert_fails(self._gate_mutate_one("gate_execution_sessions", m), "files_owned")

    # 176. File ownership collision recorded as unresolved.
    def test_176_gate_file_collision_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_file_ownership", lambda r: r.update(unresolved_parallel_writer_collisions=1)), "collisions")

    # 177. CryptoBridge.kt exclusive-S2 resolution removed.
    def test_177_gate_file_resolution_fails(self):
        def m(r):
            for e in r["entries"]:
                if e.get("file") == "CryptoBridge.kt":
                    e["resolution"] = "S3 exclusive"
        self.assert_fails(self._gate_mutate_one("gate_file_ownership", m), "CryptoBridge")

    # 178. Parallel-execution matrix mutated.
    def test_178_gate_parallel_fails(self):
        def m(r):
            r["unsafe_pairs"] = [p for p in r["unsafe_pairs"] if not (p[0] == "REMEDIATION_SESSION_S3" and "S4" in str(p[1]))]
        self.assert_fails(self._gate_mutate_one("gate_parallel_execution", m), "S3")
        def m2(r):
            r["safe_pairs"] = [p for p in r["safe_pairs"] if p != ["REMEDIATION_SESSION_S0", "REMEDIATION_SESSION_S1"]]
        self.assert_fails(self._gate_mutate_one("gate_parallel_execution", m2), "safe")

    # 179. Architecture-prerequisite owner lost.
    def test_179_gate_arch_prereq_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_architecture_prerequisites", lambda r: r.update(prerequisites_without_owner=1)), "without_owner")
        self.assert_fails(self._gate_mutate_one("gate_architecture_prerequisites", lambda r: r.update(count=9)), "count")

    # 180. Dependency DAG: cycle counter mutated.
    def test_180_gate_dag_cycles_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_dependency_dag", lambda r: r.update(unresolved_dependency_cycles=1)), "cycles")
        self.assert_fails(self._gate_mutate_one("gate_dependency_dag", lambda r: r.update(normalized_edge_count=80)), "normalized")

    # 181. Dependency DAG: actual cycle injected into the edge list.
    def test_181_gate_dag_cycle_injected_fails(self):
        def m(r):
            r["minimum_edges"].append(["REMEDIATION_SESSION_S2", "REMEDIATION_SESSION_S1 (MSC_UNIT_001)"])
        self.assert_fails(self._gate_mutate_one("gate_dependency_dag", m), "cycle")

    # 182. Dependency DAG edges truncated.
    def test_182_gate_dag_edges_dropped_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_dependency_dag", lambda r: r.update(master_edges=[])), "edges")

    # 183. FCP rule dropped (FCP_7 evidence separation).
    def test_183_gate_fcp_dropped_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_fcp_enforcement", lambda r: r["rules"].pop("FCP_7")), "FCP")

    # 184. FCP escape recorded.
    def test_184_gate_fcp_escape_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_fcp_enforcement", lambda r: r.update(fcp_escapes=1)), "escapes")

    # 185. False-closure scenario A incorrectly accepted (server half skipped).
    def test_185_gate_false_closure_accepted_fails(self):
        def m(r):
            r["scenarios"]["FALSE_CLOSURE_A"]["verdict"] = "CLOSED"
        self.assert_fails(self._gate_mutate_one("gate_false_closure_tests", m), "FALSE_CLOSURE_A")

    # 186. False-closure scenario dropped (F).
    def test_186_gate_false_closure_dropped_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_false_closure_tests", lambda r: r["scenarios"].pop("FALSE_CLOSURE_F")), "A..F")

    # 187. Server contract coverage shrunk.
    def test_187_gate_server_contract_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_server_contract_coverage", lambda r: r["rules"].pop("SERVER_CONTRACT_SC_6")), "SC")
        self.assert_fails(self._gate_mutate_one("gate_server_contract_coverage", lambda r: r.update(covered=13)), "14/14")

    # 188. Client contract coverage shrunk.
    def test_188_gate_client_contract_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_client_contract_coverage", lambda r: r["rules"].pop("CLIENT_CONTRACT_CC_14")), "CC")
        def m(r):
            r["rules"]["CLIENT_CONTRACT_CC_1"]["covered_units"] = []
        self.assert_fails(self._gate_mutate_one("gate_client_contract_coverage", m), "CC_1")

    # 189. Attackchain mapping shrunk / chain left unmapped.
    def test_189_gate_chain_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_attackchain_coverage", lambda r: r["chains"].pop("ATTACKCHAIN_AC_015")), "AC")
        def m(r):
            r["chains"]["ATTACKCHAIN_AC_001"]["mapped_to_msc"] = []
        self.assert_fails(self._gate_mutate_one("gate_attackchain_coverage", m), "ATTACKCHAIN_AC_001")

    # 190. AC-003 overlay promoted to canonical CRITICAL / ath-alone flag cleared.
    def test_190_gate_ac003_fails(self):
        def m(r):
            r["ac003_conditional_overlay"]["canonical_chain_severity"] = "CRITICAL"
        self.assert_fails(self._gate_mutate_one("gate_attackchain_coverage", m), "HIGH")
        self.assert_fails(self._gate_mutate_one("gate_attackchain_coverage", lambda r: r["ac003_conditional_overlay"].update(mandatory_ath_alone_does_not_close=False)), "ath")

    # 191. Mandatory whole-chain retest set shrunk.
    def test_191_gate_mandatory_chains_fail(self):
        def m(r):
            r["mandatory_whole_chain_retests"] = [c for c in r["mandatory_whole_chain_retests"] if c != "ATTACKCHAIN_AC_012"]
        self.assert_fails(self._gate_mutate_one("gate_attackchain_coverage", m), "mandatory")

    # 192. Physical item dropped / campaign marked executed.
    def test_192_gate_physical_fails(self):
        def m(r):
            r["items"] = [i for i in r["items"] if i["id"] != "PHYSICAL_P17"]
            r["count"] = 16
            r["assigned"] = 16
        self.assert_fails(self._gate_mutate_one("gate_physical_coverage", m), "P1..P17")
        self.assert_fails(self._gate_mutate_one("gate_physical_coverage", lambda r: r.update(status="EXECUTED")), "NOT_EXECUTED")

    # 193. Physical item left unmapped / executed counter mutated.
    def test_193_gate_physical_mapping_fails(self):
        def m(r):
            for i in r["items"]:
                if i["id"] == "PHYSICAL_P4":
                    i["mapped_units"] = []
        self.assert_fails(self._gate_mutate_one("gate_physical_coverage", m), "PHYSICAL_P4")
        self.assert_fails(self._gate_mutate_one("gate_physical_coverage", lambda r: r.update(executed=1)), "executed")

    # 194. Retest coverage mutated (42 -> 41 / missing owner).
    def test_194_gate_retest_coverage_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_retest_coverage", lambda r: r.update(units_with_independent_retest_owner=41)), "42/42")
        self.assert_fails(self._gate_mutate_one("gate_retest_coverage", lambda r: r.update(missing_retest_owner=1)), "missing")

    # 195. Pre-B004 DoD ownership mutated / marked executed.
    def test_195_gate_dod_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_pre_b004_dod_coverage", lambda r: r.update(unowned_items=1)), "unowned")
        self.assert_fails(self._gate_mutate_one("gate_pre_b004_dod_coverage", lambda r: r.update(dod_execution="EXECUTED")), "EXECUTED")
        def m(r):
            r["criteria"][0]["owner"] = ""
        self.assert_fails(self._gate_mutate_one("gate_pre_b004_dod_coverage", m), "owned")

    # 196. Human decision auto-accepted / status mutated.
    def test_196_gate_human_decision_fails(self):
        def m(r):
            r["decisions"]["HUMAN_DECISION_H1"]["status"] = "Decided"
        self.assert_fails(self._gate_mutate_one("gate_human_decision_packet", m), "HUMAN_DECISION_H1")
        self.assert_fails(self._gate_mutate_one("gate_human_decision_packet", lambda r: r.update(auto_accepted=1)), "auto_accepted")

    # 197. Human decision dropped (R1).
    def test_197_gate_human_decision_dropped_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_human_decision_packet", lambda r: r["decisions"].pop("HUMAN_DECISION_R1")), "H1")

    # 198. Primary-execution resolution mutated (018 -> S5 primary).
    def test_198_gate_primary_resolution_fails(self):
        def m(r):
            r["resolutions"]["MSC_UNIT_018"]["primary"] = "REMEDIATION_SESSION_S5"
        self.assert_fails(self._gate_mutate_one("gate_primary_execution_resolutions", m), "MSC_UNIT_018")
        self.assert_fails(self._gate_mutate_one("gate_primary_execution_resolutions", lambda r: r.update(ambiguous_owners=1)), "ambiguous")

    # 199. Readiness: remediation authorization granted / readiness flipped.
    def test_199_gate_readiness_fails(self):
        self.assert_fails(self._gate_mutate_one("gate_readiness", lambda r: r.update(security_remediation_start_authorization="GRANTED")), "NOT_GRANTED")
        self.assert_fails(self._gate_mutate_one("gate_readiness", lambda r: r.update(coverage_readiness="NOT_READY")), "READY")
        self.assert_fails(self._gate_mutate_one("gate_readiness", lambda r: r.update(b004="IN_PROGRESS")), "b004")

    # 200. Lifecycle pointers: gate record reverted to candidate / human gate executed.
    def test_200_gate_lifecycle_pointers_fail(self):
        tp, recs = self._gate_recs()
        for r in recs:
            if r.get("record_type") == "next_gate" and r.get("gate") == "SECURITY-REMEDIATION-COVERAGE-GATE":
                r["status"] = "EXECUTED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "EXECUTED_AND_PRESERVED")
        tp, recs = self._gate_recs()
        for r in recs:
            if r.get("record_type") == "next_gate" and r.get("gate") == "SECURITY_REMEDIATION_WAVE_1":
                r["status"] = "EXECUTED_AND_PRESERVED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "NOT_EXECUTED")

    # 201. Completed set drops the executed coverage gate / source_status flipped.
    def test_201_gate_completed_source_fails(self):
        wp = self.root / "docs/workforce/WORKFORCE_STATE.json"
        ws = json.loads(wp.read_text(encoding="utf-8"))
        ws["final_pre_product_audit"]["completed_audit_ids"] = [
            a for a in ws["final_pre_product_audit"]["completed_audit_ids"]
            if a != "SECURITY-REMEDIATION-COVERAGE-GATE"
        ]
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        self.assert_fails(self.run_validator(), "SECURITY-REMEDIATION-COVERAGE-GATE")
        tp, recs = self._gate_recs()
        for r in recs:
            if r.get("record_type") == "source_status" and r.get("audit_id") == self.GATE:
                r["source_present"] = "NO"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "source_status")

    # ------------------------------------------------------------------
    # HUMAN-PRE-REMEDIATION-DECISIONS-001 adversarial cases (202..234)
    # ------------------------------------------------------------------
    DEC = "HUMAN-PRE-REMEDIATION-DECISIONS-001"
    DEC_REPORT = "docs/reports/security/decisions/HUMAN-PRE-REMEDIATION-DECISIONS-001.md"
    FINDINGS = "docs/workforce/registries/findings.jsonl"
    DECISIONS = "docs/workforce/registries/decisions.jsonl"
    TASKS = "docs/workforce/registries/tasks.jsonl"
    WS = "docs/workforce/WORKFORCE_STATE.json"
    CS = "docs/continuity/CURRENT_STATE.json"
    CH = "docs/continuity/CURRENT_HANDOFF.md"
    LEDGER = "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl"

    def _dec_recs(self):
        tp = self.root / TRACE
        return tp, _load_jsonl(tp)

    def _dec_mutate_one(self, rt, mutator, decision_id=None):
        tp, recs = self._dec_recs()
        for r in recs:
            if r.get("record_type") == rt and r.get("source_artifact_id") == self.DEC:
                if decision_id is not None and r.get("decision_id") != decision_id:
                    continue
                mutator(r)
        _write_jsonl(tp, recs)
        return self.run_validator()

    def _dec_registry_mutate(self, mutator):
        rp = self.root / "docs/security/audit-evidence/audit_registry.jsonl"
        recs = _load_jsonl(rp)
        for r in recs:
            if r.get("audit_id") == self.DEC:
                mutator(r)
        _write_jsonl(rp, recs)
        return self.run_validator()

    def _findings_mutate_a10(self, mutator):
        fp = self.root / self.FINDINGS
        recs = _load_jsonl(fp)
        for r in recs:
            if r.get("finding_id") == "ANOX-SECURITY-ARCH-010":
                mutator(r)
        _write_jsonl(fp, recs)
        return self.run_validator()

    def _ws_mutate(self, mutator):
        wp = self.root / self.WS
        ws = json.loads(wp.read_text(encoding="utf-8"))
        mutator(ws)
        wp.write_text(json.dumps(ws, indent=2), encoding="utf-8")
        return self.run_validator()

    # 202. H1 human_decision record missing.
    def test_202_h1_record_missing_fails(self):
        tp, recs = self._dec_recs()
        recs = [r for r in recs if not (r.get("record_type") == "human_decision" and r.get("decision_id") == "HUMAN_DECISION_H1")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "H1")

    # 203. H2 human_decision record missing.
    def test_203_h2_record_missing_fails(self):
        tp, recs = self._dec_recs()
        recs = [r for r in recs if not (r.get("record_type") == "human_decision" and r.get("decision_id") == "HUMAN_DECISION_H2")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "H2")

    # 204. H3 human_decision record missing.
    def test_204_h3_record_missing_fails(self):
        tp, recs = self._dec_recs()
        recs = [r for r in recs if not (r.get("record_type") == "human_decision" and r.get("decision_id") == "HUMAN_DECISION_H3")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "H3")

    # 205. R1 human_decision record missing.
    def test_205_r1_record_missing_fails(self):
        tp, recs = self._dec_recs()
        recs = [r for r in recs if not (r.get("record_type") == "human_decision" and r.get("decision_id") == "HUMAN_DECISION_R1")]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "R1")

    # 206. Wrong decision id substituted for H1.
    def test_206_wrong_decision_id_fails(self):
        self.assert_fails(
            self._dec_mutate_one("human_decision", lambda r: r.update(decision_id="HUMAN_DECISION_H9"),
                                 decision_id="HUMAN_DECISION_H1"), "H1")

    # 207. Decision recorded as auto-accepted / decided by AI.
    def test_207_auto_accepted_fails(self):
        self.assert_fails(
            self._dec_mutate_one("human_decision", lambda r: r.update(auto_accepted=True),
                                 decision_id="HUMAN_DECISION_H1"), "auto_accepted")
        self.assert_fails(
            self._dec_mutate_one("human_decision",
                                 lambda r: r.update(decided_by="AI_AGENT", authority_actor="Devin CLI"),
                                 decision_id="HUMAN_DECISION_H2"), "Human")

    # 208. Authorization recorded with non-human authority.
    def test_208_authorization_nonhuman_fails(self):
        self.assert_fails(
            self._dec_mutate_one("human_remediation_authorization",
                                 lambda r: r.update(authority_actor="Devin CLI", decided_by="AI_AGENT")), "Human")

    # 209. Authorization accidentally starts remediation.
    def test_209_authorization_starts_remediation_fails(self):
        self.assert_fails(
            self._dec_mutate_one("human_remediation_authorization",
                                 lambda r: r.update(security_remediation="STARTED")), "NOT_STARTED")

    # 210. ROOT-013 transition not canonical MEDIUM.
    def test_210_root013_not_medium_fails(self):
        self.assert_fails(
            self._dec_mutate_one("canonical_severity_transition",
                                 lambda r: r.update(current_canonical_severity="LOW")), "MEDIUM")
        self.assert_fails(
            self._dec_mutate_one("canonical_severity_transition",
                                 lambda r: r.update(prior_canonical_severity="MEDIUM")), "LOW")

    # 211. ROOT-013 incorrectly closed / fixed.
    def test_211_root013_closed_fails(self):
        self.assert_fails(
            self._dec_mutate_one("canonical_severity_transition", lambda r: r.update(status="CLOSED")), "OPEN")
        self.assert_fails(
            self._dec_mutate_one("canonical_severity_transition", lambda r: r.update(fixed="YES")), "fixed")

    # 212. ARCH-010 retired too early in findings.jsonl.
    def test_212_arch010_retired_early_fails(self):
        self.assert_fails(self._findings_mutate_a10(lambda f: f.update(status="Closed")), "Open")

    # 213. ARCH-010 B004-start trigger missing.
    def test_213_arch010_trigger_missing_fails(self):
        tp, recs = self._dec_recs()
        recs = [r for r in recs if r.get("record_type") != "finding_retirement_trigger"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "RETIRE_AT_B004_START")
        self.assert_fails(self._findings_mutate_a10(lambda f: f.update(notes="positive scope only")), "RETIRE_AT_B004_START")

    # 214. Retired validator deleted.
    def test_214_retired_validator_deleted_fails(self):
        (self.root / "tools/audit/validate_security_architecture_findings_freeze.py").unlink()
        self.assert_fails(self.run_validator(), "deleted")

    # 215. Retired validator rewritten to current HEAD (pin removed).
    def test_215_retired_validator_rewritten_fails(self):
        p = self.root / "tools/audit/validate_security_architecture_findings_freeze.py"
        p.write_text(p.read_text(encoding="utf-8").replace(
            "c653a1d6a302758c0e006225987281643957f752", "9e585468d081272398e022f12e76e7500d55cbee"),
            encoding="utf-8")
        self.assert_fails(self.run_validator(), "integrity marker")

    # 216. Retired validator treated as active acceptance.
    def test_216_retired_validator_marked_active_fails(self):
        tp, recs = self._dec_recs()
        for r in recs:
            if (r.get("record_type") == "validator_lifecycle"
                    and r.get("validator") == "tools/audit/validate_security_architecture_findings_freeze.py"):
                r["current_active_acceptance"] = "ACTIVE"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "RETIRED")

    # 217. All validator_lifecycle records dropped.
    def test_217_validator_lifecycle_missing_fails(self):
        tp, recs = self._dec_recs()
        recs = [r for r in recs if r.get("record_type") != "validator_lifecycle"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "validator_lifecycle")

    # 218. B-004/B-005 started by the authorization.
    def test_218_b004_b005_started_fails(self):
        self.assert_fails(
            self._dec_mutate_one("human_remediation_authorization", lambda r: r.update(b004="STARTED")), "b004")
        self.assert_fails(
            self._dec_mutate_one("human_remediation_authorization", lambda r: r.update(b005="STARTED")), "b005")

    # 219. Product unblocked prematurely.
    def test_219_product_unblocked_fails(self):
        self.assert_fails(
            self._ws_mutate(lambda ws: ws.update(product_development_state="UNBLOCKED")),
            "BLOCKED_PENDING_FINAL_AUDIT")

    # 220. Open MSC unit count changed (an open unit flipped to rejected).
    def test_220_open_msc_count_changed_fails(self):
        tp, recs = self._dec_recs()
        for r in recs:
            if r.get("record_type") == "msc_unit" and r.get("msc_unit_id") == "MSC_UNIT_001":
                r["proposed_disposition"] = "REJECTED_NOT_A_FINDING"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "42 open")

    # 221. MSC unit marked remediated / fixed.
    def test_221_fixed_msc_nonzero_fails(self):
        tp, recs = self._dec_recs()
        for r in recs:
            if r.get("record_type") == "msc_unit" and r.get("msc_unit_id") == "MSC_UNIT_001":
                r["proposed_disposition"] = "REMEDIATED"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "disposition")

    # 222. Coverage gate no longer PASS.
    def test_222_coverage_gate_not_pass_fails(self):
        self.assert_fails(
            self._gate_registry_mutate(lambda r: r.update(result="FAIL")), "result")
        self.assert_fails(
            self._gate_mutate_one("gate_verdict", lambda r: r.update(result="FAIL")), "result")

    # 223. First authorized wave incorrect.
    def test_223_first_wave_incorrect_fails(self):
        self.assert_fails(
            self._dec_mutate_one("human_remediation_authorization",
                                 lambda r: r.update(first_authorized_wave="S0")), "S0_AND_S1")
        self.assert_fails(
            self._dec_mutate_one("human_remediation_authorization",
                                 lambda r: r.update(first_authorized_sessions=["REMEDIATION_SESSION_S2"])), "S0")

    # 224. Event id collision / wrong latest event.
    def test_224_event_id_collision_fails(self):
        lp = self.root / self.LEDGER
        recs = _load_jsonl(lp)
        recs[-1]["event_id"] = "ANOX-EVENT-0051"
        _write_jsonl(lp, recs)
        self.assert_fails(self.run_validator(), "stale")
        lp = self.root / self.LEDGER
        recs = _load_jsonl(lp)
        recs.append(dict(recs[-1], event_id="ANOX-EVENT-0053"))
        _write_jsonl(lp, recs)
        cs = self.root / self.CS
        state = json.loads(cs.read_text(encoding="utf-8"))
        state["latest_material_event_id"] = "ANOX-EVENT-0053"
        cs.write_text(json.dumps(state, indent=1), encoding="utf-8")
        self.assert_fails(self.run_validator(), "ANOX-EVENT-0052")

    # 225. Ledger line-size violation.
    def test_225_ledger_line_size_fails(self):
        lp = self.root / self.LEDGER
        with open(lp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event_id": "ANOX-EVENT-0052", "pad": "x" * 5000}) + "\n")
        self.assert_fails(self.run_validator(), "line-size")

    # 226. Task registry entry missing / wrong status or start_sha.
    def test_226_task_registry_schema_fails(self):
        tp = self.root / self.TASKS
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("task_id") == "ANOX-TASK-HUMAN-PRE-REMEDIATION-DECISIONS-001":
                r["status"] = "In Progress"
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "Ready For Remote")
        tp = self.root / self.TASKS
        recs = _load_jsonl(tp)
        for r in recs:
            if r.get("task_id") == "ANOX-TASK-HUMAN-PRE-REMEDIATION-DECISIONS-001":
                r["start_sha"] = "0" * 40
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "start_sha")

    # 227. Handoff missing decision/authorization metadata.
    def test_227_handoff_missing_decision_metadata_fails(self):
        ch = self.root / self.CH
        ch.write_text(ch.read_text(encoding="utf-8").replace("GRANTED_BY_HUMAN_OWNER", "NOT_GRANTED"),
                      encoding="utf-8")
        self.assert_fails(self.run_validator(), "GRANTED_BY_HUMAN_OWNER")
        ch = self.root / self.CH
        ch.write_text(ch.read_text(encoding="utf-8").replace("HUMAN-PRE-REMEDIATION-DECISIONS-001", "X-OLD-001"),
                      encoding="utf-8")
        self.assert_fails(self.run_validator(), "HUMAN-PRE-REMEDIATION-DECISIONS-001")

    # 228. Handoff described-head mismatch vs CURRENT_STATE.
    def test_228_handoff_described_head_mismatch_fails(self):
        cs = self.root / self.CS
        state = json.loads(cs.read_text(encoding="utf-8"))
        state["described_head"] = "1" * 40
        cs.write_text(json.dumps(state, indent=1), encoding="utf-8")
        self.assert_fails(self.run_validator(), "Described HEAD")

    # 231. Decision record mutated (hash mismatch).
    def test_231_decision_doc_mutated_fails(self):
        p = self.root / self.DEC_REPORT
        with open(p, "ab") as f:
            f.write(b"\n tampered")
        self.assert_fails(self.run_validator(), "hash mismatch")

    # 232. Decision record deleted.
    def test_232_decision_doc_deleted_fails(self):
        (self.root / self.DEC_REPORT).unlink()
        self.assert_fails(self.run_validator(), "missing")

    # 233. human_remediation_authorization record dropped.
    def test_233_authorization_record_missing_fails(self):
        tp, recs = self._dec_recs()
        recs = [r for r in recs if r.get("record_type") != "human_remediation_authorization"]
        _write_jsonl(tp, recs)
        self.assert_fails(self.run_validator(), "human_remediation_authorization")

    # 234. decisions.jsonl record missing / non-human authority.
    def test_234_decisions_registry_fails(self):
        dp = self.root / self.DECISIONS
        recs = [r for r in _load_jsonl(dp) if r.get("decision_id") != "ANOX-DECISION-HUMANPREREMEDIATION001"]
        _write_jsonl(dp, recs)
        self.assert_fails(self.run_validator(), "ANOX-DECISION-HUMANPREREMEDIATION001")
        dp = self.root / self.DECISIONS
        recs = _load_jsonl(dp)
        for r in recs:
            if r.get("decision_id") == "ANOX-DECISION-HUMANPREREMEDIATION001":
                r["authority_actor"] = "Devin CLI"
        _write_jsonl(dp, recs)
        self.assert_fails(self.run_validator(), "Human")


class DeliveryTopologyAdversarialTests(unittest.TestCase):
    """Adversarial checks on the canonical two-commit delivery rule itself,
    exercised against throwaway git repositories."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=self.root, check=True)
        sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
        import lifecycle_legality as ll  # noqa: E402
        self.ll = ll

    def tearDown(self):
        self.tmp.cleanup()

    def _commit(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", name], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", name], cwd=self.root, check=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()

    # 229. Third task-authored commit above base is rejected.
    def test_229_third_task_authored_commit_fails(self):
        base = self._commit("base.txt", "base")
        c1 = self._commit("substantive.txt", "sub")
        c2 = self._commit("docs/continuity/CURRENT_STATE.json", "{}")
        c3 = self._commit("docs/continuity/CURRENT_GIT_STATE.md", "x")
        ok, _, _, reason = self.ll.canonical_two_commit_delivery(
            base, c2, c3, cwd=self.root, metadata_allowlist=set())
        self.assertFalse(ok, "a third task-authored commit must be rejected")
        self.assertIn("expected exactly 2", reason)

    # 230. Metadata commit touching a substantive (non-allowlisted) file is rejected.
    def test_230_metadata_commit_substantive_file_fails(self):
        base = self._commit("base.txt", "base")
        c1 = self._commit("substantive.txt", "sub")
        c2 = self._commit("android/Fake.kt", "product change")
        ok, _, _, reason = self.ll.canonical_two_commit_delivery(
            base, c1, c2, cwd=self.root,
            metadata_allowlist={"docs/continuity/CURRENT_STATE.json"})
        self.assertFalse(ok, "metadata commit touching a substantive file must be rejected")
        self.assertIn("metadata commit touches non-metadata files", reason)


if __name__ == "__main__":
    unittest.main()
