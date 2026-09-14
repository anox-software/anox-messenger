#!/usr/bin/env python3
"""Security Hardening audit evidence-preservation validator.

Fail-closed verification for SECURITY-AUDIT-EVIDENCE-PRESERVATION-001,
-002, -003, -004, -005 and MASTER-SPECIALIST-CONSOLIDATION-PRESERVATION-001:
the nine preserved audit reports (including AUDIT-SECURITY-CRYPTO-JNI-001,
AUDIT-SECURITY-AUTH-DPOP-001, AUDIT-SECURITY-ANDROID-STORAGE-001 and
AUDIT-SECURITY-ATTACKCHAIN-001), the preserved MASTER-SPECIALIST-CONSOLIDATION-001
MASTER_SECURITY_CONSOLIDATION artifact (90 source items, 44 MSC units,
arbitrations, attackchain/breaker mappings, dependency DAG, sessions,
Pre-B004 set + DoD, gates, closure standard/state machine, retest matrix,
physical campaign, consolidated contracts, fix coverage precursor, quality
gates), the audit-evidence registry, the traceability layer (including
cryptojni, authdpop, androidstorage and attackchain candidates/gaps,
specialist relations, severity overlays, provenance limitation, temp-build
evidence, the ABI revision record, coverage/test evidence, historical
revalidation, remediation coverage, chain breakers, gate sets and
specialist handoffs), and the lifecycle state that must remain unchanged.

Set SECURITY_AUDIT_PRESERVATION_REPO to validate an alternate tree
(test fixtures); git-dependent checks are skipped when no .git exists.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("SECURITY_AUDIT_PRESERVATION_REPO") or Path(__file__).resolve().parents[2])
EVIDENCE_DIR = REPO_ROOT / "docs" / "security" / "audit-evidence"
REPORTS_DIR = REPO_ROOT / "docs" / "reports" / "security" / "audits"
REGISTRY_DIR = REPO_ROOT / "docs" / "workforce" / "registries"
WAVE_BASE_SHA = "869b99acac040412a29bbaadc76342070fb2085c"
CRYPTOJNI_AUDIT_SHA = "a79166ab7e65db71ba70e3a427df2ad017dc9225"
AUTHDPOP_AUDIT_SHA = "638e63a22c91ca81365bf55c8a59ec47878dd7fd"
ANDROIDSTORAGE_AUDIT_SHA = "b9abeb0850a476716403d224b87a857c1147502e"
ATTACKCHAIN_AUDIT_SHA = "e54584903a353e98ad154d1e8f90f93ed9d7db14"
CONSOLIDATION_BASE_SHA = "1eb773069d81ea3d12b76249c73f2f5fb0b6cae9"
GATE_BASE_SHA = "610ed08337536857db73259168498c49b786caa1"
BASE_SHA = "610ed08337536857db73259168498c49b786caa1"
DELIVERY_BRANCH = "governance/security-remediation-coverage-gate-preservation-001"
TASK_ID = "ANOX-TASK-SECURITY-REMEDIATION-COVERAGE-GATE-PRESERVATION-001"
NEXT_GATE_ID = "HUMAN_PRE_REMEDIATION_DECISIONS_AND_AUTHORIZATION"
PRIOR_GATE_ID = "SECURITY-REMEDIATION-COVERAGE-GATE"
LEDGER_EVENT = "ANOX-EVENT-0051"
MSC_ID = "MASTER-SPECIALIST-CONSOLIDATION-001"
MSC_LEDGER_EVENT = "ANOX-EVENT-0050"
MSC_DELIVERY_BRANCH = "governance/master-specialist-consolidation-preservation-001"
GATE_ID = "SECURITY-REMEDIATION-COVERAGE-GATE-001"

EXPECTED_REPORTS = {
    "AUDIT-SECURITY-ARCHITECTURE": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-ARCHITECTURE.md",
        "sha256": "da230ac1a3f623eba559c31641e52ffd2fc5487502d4c6ad2ccbbc1f9eb6dfe6",
    },
    "AUDIT-SECURITY-CODEBASE-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md",
        "sha256": "122d0aae9c1b64d060010092bea77f4d9c3466c5df2d10ccf56955bc4987f153",
    },
    "AUDIT-SECURITY-CODEBASE-002": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-002.md",
        "sha256": "2ce279637bea62c79ced6614318c1fe79fcdc1b30b33519aeb7b2d426d4c09d5",
    },
    "CODEBASE-SECURITY-CONSENSUS-001": {
        "path": "docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md",
        "sha256": "66ea13d75982e83fdb9b316f3b95c0aef4b1fae9604d5e6457abb33e40898f8c",
    },
    "AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001.md",
        "sha256": "6afdd091d64ec9a30d40f8ba4e0fbe73bfb4812f105993bdbb42b49895acda1a",
    },
    "AUDIT-SECURITY-CRYPTO-JNI-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-CRYPTO-JNI-001.md",
        "sha256": "c7367e3419b709d9675b16ddcf1fee23fd114283482523ee036be99e4ecc836b",
    },
    "AUDIT-SECURITY-AUTH-DPOP-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-AUTH-DPOP-001.md",
        "sha256": "57516d7d47e56447b7ab7a91aadaa2b7c3acdeda71e572b2b4366d2a6526b18e",
    },
    "AUDIT-SECURITY-ANDROID-STORAGE-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-ANDROID-STORAGE-001.md",
        "sha256": "7532877dd14b97011d19f0b07a79bb50e529e4130feb0226c242b60d3e995720",
    },
    "AUDIT-SECURITY-ATTACKCHAIN-001": {
        "path": "docs/reports/security/audits/AUDIT-SECURITY-ATTACKCHAIN-001.md",
        "sha256": "a4feac55f49066647ec0c1665c40deab581115da4b102e81eb6742e72b80ca9e",
    },
    "MASTER-SPECIALIST-CONSOLIDATION-001": {
        "path": "docs/reports/security/consolidation/MASTER-SPECIALIST-CONSOLIDATION-001.md",
        "sha256": "a22c779833e6334067405ebd158f1cbadeee5dc51d9b7795c31ef12758060b00",
    },
    "SECURITY-REMEDIATION-COVERAGE-GATE-001": {
        "path": "docs/reports/security/gates/SECURITY-REMEDIATION-COVERAGE-GATE-001.md",
        "sha256": "175aa756fa1a260311c3d8b3c3680aa26de38d58bd2d8ebb782320cc27e2b27e",
    },
}

# ---------------------------------------------------------------------------
# MASTER-SPECIALIST-CONSOLIDATION-001 preserved expectations
# ---------------------------------------------------------------------------
# The consolidation is a read-only analytical artifact (result
# PASS_WITH_CONSOLIDATION_FINDINGS) executed at CONSOLIDATION_BASE_SHA. Its
# preserved machine-readable layer uses namespaced identities
# (MSC_UNIT_*, ATTACKCHAIN_AC_*, SERVER_BREAKER_S*, CLIENT_BREAKER_C*,
# REMEDIATION_SESSION_S*, PHYSICAL_P*, FCP_*). These constants pin the
# fail-closed expectations; the content lives in audit_traceability.jsonl.
MSC_SOURCE_ITEM_COUNT = 90
MSC_SOURCE_CLASS_COUNTS = {
    "CONSENSUS_ROOT": 18,
    "SPECIALIST_CANDIDATE": 23,
    "ATTACKCHAIN": 15,
    "ARCHITECTURE_GAP": 6,
    "ARCHITECTURE_FINDING": 10,
    "HISTORICAL_FINDING": 16,
    "GOVERNANCE_ITEM": 2,
}
MSC_SOURCE_DISPOSITIONS = {
    "DISTINCT_ROOT_CAUSE", "DISTINCT_ROOT_CAUSE_SPLIT", "MERGE_INTO_EXISTING_ROOT",
    "ATTACKCHAIN_ONLY", "SUPERSEDED_BUT_TRACEABLE", "ARCHITECTURE_CONTRACT_GAP",
    "META_EVIDENCE_OR_BUILD_RISK", "REJECTED_NOT_A_FINDING",
    "ENABLING_CONDITION", "STANDALONE_SECURITY_ITEM",
}
MSC_UNIT_IDS = {f"MSC_UNIT_{i:03d}" for i in range(1, 45)}
MSC_REJECTED_UNITS = {"MSC_UNIT_043", "MSC_UNIT_044"}
MSC_OPEN_STATUS = "OPEN_PENDING_REMEDIATION_COVERAGE_GATE"
MSC_REJECTED_STATUS = "REJECTED_NOT_A_FINDING"
MSC_SEVERITY_DISTRIBUTION = {
    "CRITICAL": 0, "HIGH": 7, "MEDIUM": 16, "LOW": 6,
    "INFO_META": 4, "CONTRACT_GAPS": 9, "REJECTED": 2,
}
MSC_SPLIT_ROOTS = {"ROOT-008", "ROOT-011", "ROOT-012", "ROOT-018"}
MSC_ROOT_IDS = {f"ROOT-{i:03d}" for i in range(1, 19)}
MSC_SPEC_CANDIDATE_IDS = (
    {f"ANOX-CRYPTOJNI-CANDIDATE-{i:03d}" for i in range(1, 7)}
    | {f"ANOX-AUTHDPOP-CANDIDATE-{i:03d}" for i in range(1, 4)}
    | {f"ANOX-ANDROIDSTORAGE-CANDIDATE-{i:03d}" for i in range(1, 3)}
)
MSC_GAP_IDS = (
    {f"ANOX-AUTHDPOP-GAP-{i:03d}" for i in range(1, 4)}
    | {f"ANOX-ANDROIDSTORAGE-GAP-{i:03d}" for i in range(1, 4)}
)
MSC_CHAIN_IDS = {f"ATTACKCHAIN_AC_{i:03d}" for i in range(1, 16)}
MSC_SERVER_BREAKER_IDS = {f"SERVER_BREAKER_S{i}" for i in range(1, 19)}
MSC_CLIENT_BREAKER_IDS = {f"CLIENT_BREAKER_C{i}" for i in range(1, 15)}
MSC_SESSION_IDS = {f"REMEDIATION_SESSION_S{i}" for i in range(0, 11)}
MSC_PHYSICAL_IDS = {f"PHYSICAL_P{i}" for i in range(1, 18)}
MSC_FCP_IDS = {f"FCP_{i}" for i in range(1, 9)}
MSC_SERVER_CONTRACT_IDS = {f"SC-{i}" for i in range(1, 15)}
MSC_CLIENT_CONTRACT_IDS = {f"CC-{i}" for i in range(1, 15)}
MSC_CSM_STAGES = {
    "FOUND", "CONSOLIDATED", "ASSIGNED", "IMPLEMENTED", "AUTOMATED_TESTED",
    "RUNTIME_TESTED / NOT_APPLICABLE", "INDEPENDENTLY_RETESTED",
    "ATTACKCHAIN_RETESTED / NOT_APPLICABLE", "PHYSICAL_VERIFIED / NOT_APPLICABLE",
    "EVIDENCE_PRESERVED", "CLOSED",
}
MSC_UNIT_REQUIRED_FIELDS = (
    "msc_unit_id", "title", "unit_type", "proposed_consolidated_severity",
    "chain_severity_relation", "evidence_integrity_severity", "confidence",
    "primary_root_cause", "source_ids", "consensus_root_relation",
    "architecture_findings", "legacy_findings", "specialist_findings",
    "attackchains", "affected_architecture", "affected_code",
    "current_reachability", "activation_gate", "pre_b004_or_later",
    "fix_groups", "provisional_session", "dependencies",
    "architecture_prerequisites", "must_fix_together", "must_not_fix_alone",
    "chain_breakers", "required_automated_tests", "required_instrumented_tests",
    "required_physical_tests", "independent_retest_owners", "closure_evidence",
    "proposed_disposition",
)
MSC_QUALITY_GATE_ZERO_FIELDS = (
    "source_items_unaccounted", "msc_units_without_source",
    "attackchains_without_msc_unit", "server_breakers_unassigned",
    "client_breakers_unassigned", "architecture_gaps_lost",
    "legacy_findings_without_owner", "pre_b004_items_without_gate",
    "later_items_without_named_gate", "msc_units_without_test_plan",
    "msc_units_without_retest_owner", "unknown_dispositions",
    "silently_dropped", "unresolved_dependency_cycles",
)
MSC_PRE_B004_CATEGORIES = (
    "A_ARCHITECTURE_CONTRACT", "B_BUILD_PROVENANCE", "C_CODE_REMEDIATION",
    "C_RECOMMENDED_PULL_FORWARD", "D_VERIFICATION", "E_B004_IMPLEMENTATION_TIME",
)
MSC_LATER_GATES = (
    "B006", "B008_B009", "B012", "B013", "RELEASE_CANDIDATE",
    "PHYSICAL_GRAPHENEOS_FINAL", "FINAL_PRODUCT_GATE_OPERATIONAL_ACCEPTANCE",
    "HUMAN_DECISION_PRE_REMEDIATION",
)

# ---------------------------------------------------------------------------
# SECURITY-REMEDIATION-COVERAGE-GATE-001 preserved expectations
# ---------------------------------------------------------------------------
# The gate is a read-only verification artifact (result PASS) executed at
# GATE_BASE_SHA. Its preserved machine-readable layer uses namespaced
# identities only (MSC_UNIT_*, ATTACKCHAIN_AC_*, SERVER_BREAKER_S*,
# CLIENT_BREAKER_C*, REMEDIATION_SESSION_S*, SERVER_CONTRACT_SC_*,
# CLIENT_CONTRACT_CC_*, PHYSICAL_P*, FCP_*, FALSE_CLOSURE_*,
# HUMAN_DECISION_*). PASS proves coverage; it never authorizes remediation.
GATE_REPORT_BYTES = 33527
GATE_OPEN_UNIT_IDS = {f"MSC_UNIT_{i:03d}" for i in range(1, 43)}
GATE_REJECTED_UNITS = {"MSC_UNIT_043", "MSC_UNIT_044"}
GATE_SESSION_IDS = {f"REMEDIATION_SESSION_S{i}" for i in range(0, 11)}
GATE_FCP_IDS = {f"FCP_{i}" for i in range(1, 9)}
GATE_SC_IDS = {f"SERVER_CONTRACT_SC_{i}" for i in range(1, 15)}
GATE_CC_IDS = {f"CLIENT_CONTRACT_CC_{i}" for i in range(1, 15)}
GATE_PHYSICAL_IDS = {f"PHYSICAL_P{i}" for i in range(1, 18)}
GATE_CHAIN_IDS = {f"ATTACKCHAIN_AC_{i:03d}" for i in range(1, 16)}
GATE_FALSE_CLOSURE_IDS = {f"FALSE_CLOSURE_{c}" for c in "ABCDEF"}
GATE_HUMAN_DECISION_IDS = {
    "HUMAN_DECISION_H1", "HUMAN_DECISION_H2", "HUMAN_DECISION_H3", "HUMAN_DECISION_R1",
}
GATE_MANDATORY_CHAIN_RETESTS = {
    "ATTACKCHAIN_AC_001", "ATTACKCHAIN_AC_003", "ATTACKCHAIN_AC_005",
    "ATTACKCHAIN_AC_006", "ATTACKCHAIN_AC_008", "ATTACKCHAIN_AC_010",
    "ATTACKCHAIN_AC_012",
}
GATE_ALLOWED_GATES = {
    "PRE_B004", "B004", "B004_B005", "B005", "B006", "B008_B009", "B012",
    "B012_GATE", "B013", "RELEASE_CANDIDATE", "PHYSICAL_FINAL",
    "FINAL_PRODUCT_OPERATIONAL", "HUMAN_DECISION_PRE_REMEDIATION",
    "HUMAN_GOVERNANCE",
}
GATE_ALLOWED_OWNERS = GATE_SESSION_IDS | {
    "HUMAN_GOVERNANCE_DECISION", "B012_GATE",
}
GATE_ZERO_METRIC_FIELDS = (
    "source_items_unaccounted", "duplicate_source_ids", "dangling_unit_references",
    "attackchains_without_msc_unit", "unassigned_server_breakers",
    "unassigned_client_breakers", "architecture_coverage_loss",
    "legacy_findings_without_current_owner", "unresolved_dependency_cycles",
    "unknown_obligations", "uncovered_open_msc_units",
    "parallel_writer_collisions", "unowned_pre_b004_dod_items",
    "unmapped_contract_items", "fcp_escapes", "unresolved_ids",
)
GATE_PRIMARY = {
    "MSC_UNIT_001": "REMEDIATION_SESSION_S1", "MSC_UNIT_002": "REMEDIATION_SESSION_S1",
    "MSC_UNIT_003": "REMEDIATION_SESSION_S1", "MSC_UNIT_004": "REMEDIATION_SESSION_S9",
    "MSC_UNIT_005": "REMEDIATION_SESSION_S2", "MSC_UNIT_006": "REMEDIATION_SESSION_S2",
    "MSC_UNIT_007": "REMEDIATION_SESSION_S2", "MSC_UNIT_008": "REMEDIATION_SESSION_S2",
    "MSC_UNIT_009": "REMEDIATION_SESSION_S2", "MSC_UNIT_010": "REMEDIATION_SESSION_S2",
    "MSC_UNIT_011": "REMEDIATION_SESSION_S2", "MSC_UNIT_012": "REMEDIATION_SESSION_S7",
    "MSC_UNIT_013": "REMEDIATION_SESSION_S6", "MSC_UNIT_014": "REMEDIATION_SESSION_S3",
    "MSC_UNIT_015": "REMEDIATION_SESSION_S3", "MSC_UNIT_016": "REMEDIATION_SESSION_S3",
    "MSC_UNIT_017": "REMEDIATION_SESSION_S3", "MSC_UNIT_018": "REMEDIATION_SESSION_S3",
    "MSC_UNIT_019": "REMEDIATION_SESSION_S3", "MSC_UNIT_020": "REMEDIATION_SESSION_S6",
    "MSC_UNIT_021": "REMEDIATION_SESSION_S4", "MSC_UNIT_022": "REMEDIATION_SESSION_S4",
    "MSC_UNIT_023": "REMEDIATION_SESSION_S4", "MSC_UNIT_024": "REMEDIATION_SESSION_S4",
    "MSC_UNIT_025": "REMEDIATION_SESSION_S0", "MSC_UNIT_026": "REMEDIATION_SESSION_S0",
    "MSC_UNIT_027": "REMEDIATION_SESSION_S4", "MSC_UNIT_028": "REMEDIATION_SESSION_S0",
    "MSC_UNIT_029": "REMEDIATION_SESSION_S3", "MSC_UNIT_030": "REMEDIATION_SESSION_S7",
    "MSC_UNIT_031": "REMEDIATION_SESSION_S8", "MSC_UNIT_032": "REMEDIATION_SESSION_S0",
    "MSC_UNIT_033": "REMEDIATION_SESSION_S0", "MSC_UNIT_034": "REMEDIATION_SESSION_S0",
    "MSC_UNIT_035": "REMEDIATION_SESSION_S3", "MSC_UNIT_036": "REMEDIATION_SESSION_S10",
    "MSC_UNIT_037": "REMEDIATION_SESSION_S10", "MSC_UNIT_038": "REMEDIATION_SESSION_S1",
    "MSC_UNIT_039": "HUMAN_GOVERNANCE_DECISION", "MSC_UNIT_040": "REMEDIATION_SESSION_S0",
    "MSC_UNIT_041": "B012_GATE", "MSC_UNIT_042": "REMEDIATION_SESSION_S0",
}
GATE_ROW_REQUIRED_FIELDS = (
    "msc_unit", "title", "unit_type", "severity", "attackchains", "gate",
    "primary_execution_owner", "secondary_execution_owner", "session_order",
    "session_role", "architecture_prerequisites", "independent_retest_owner",
    "instrumented_requirement", "synthetic_backend_requirement",
    "physical_requirement", "provenance_requirement", "attackchain_retest",
    "closure_runtime_stage", "closure_chain_stage", "closure_physical_stage",
    "coverage_status",
)
# Bare/short-form machine ids that collide between namespaces (SERVER_BREAKER_S1
# vs REMEDIATION_SESSION_S1 vs SERVER_CONTRACT_SC_1...). Canonical namespaced
# forms (MSC_UNIT_001, ATTACKCHAIN_AC_001, REMEDIATION_SESSION_S1,
# SERVER_CONTRACT_SC_1, CLIENT_CONTRACT_CC_1, PHYSICAL_P1, FCP_1, ...) do NOT
# match this pattern.
GATE_AMBIGUOUS_KEY_RE = re.compile(
    r"^(?:(?:S|C|P)[-_]?\d+|(?:SC|CC|AC|MSC)[-_]\d+|FCP\d+)$")

EXPECTED_AUDITS = {
    "ANOX-AUDIT-SECURITY-ARCH-001": {
        "audit_type": "FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT",
        "provider": "Anthropic via Devin CLI / Cognition",
        "actual_model": "Claude Opus 5 High",
        "audited_sha": "c653a1d6a302758c0e006225987281643957f752",
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 11, "critical_count": 0, "high_count": 5,
        "medium_count": 3, "low_count": 2, "info_count": 1,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-CODEBASE-001": {
        "audit_type": "READ_ONLY_FULL_EXISTING_CODEBASE_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Opus 5 Medium",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": WAVE_BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 21, "critical_count": 1, "high_count": 3,
        "medium_count": 8, "low_count": 7, "info_count": 2,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-CODEBASE-002": {
        "audit_type": "READ_ONLY_BLIND_INDEPENDENT_FULL_CODEBASE_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": WAVE_BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 17, "critical_count": 0, "high_count": 3,
        "medium_count": 6, "low_count": 6, "info_count": 2,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "YES", "blindness_status_prefix": "PRESERVED",
    },
    "CODEBASE-SECURITY-CONSENSUS-001": {
        "audit_type": "CONSENSUS_ANALYSIS_AND_ARBITRATION",
        "provider": "Anthropic",
        "actual_model": "Claude Opus 5 High",
        "audited_sha": WAVE_BASE_SHA,
        "result": "PASS",
        "candidate_count": 18,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001": {
        "audit_type": "READ_ONLY_BUILD_NATIVE_PROVENANCE_SUPPLY_CHAIN_SECURITY_AUDIT",
        "provider": "Anthropic",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "audited_sha": WAVE_BASE_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 12, "critical_count": 0, "high_count": 3,
        "medium_count": 5, "low_count": 3, "info_count": 1,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-CRYPTO-JNI-001": {
        "audit_type": "security_specialist_crypto_jni",
        "provider": "Anthropic",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "model_requirement_status": "SATISFIED",
        "audited_sha": CRYPTOJNI_AUDIT_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 6, "critical_count": 0, "high_count": 1,
        "medium_count": 3, "low_count": 1, "info_count": 1,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-AUTH-DPOP-001": {
        "audit_type": "security_specialist_device_auth_dpop",
        "provider": "Devin CLI (Cognition) session runtime",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "model_requirement_status": "SATISFIED",
        "audited_sha": AUTHDPOP_AUDIT_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 3, "architecture_gap_count": 3,
        "critical_count": 0, "high_count": 0,
        "medium_count": 1, "low_count": 2, "info_count": 0,
        "b002_production_files": "29/29 (100%)",
        "b002_relevant_test_files": "14/14 (100%)",
        "architecture_requirements": 40, "architecture_unmapped": 0,
        "focused_relevant_test_inventory": 155,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-ANDROID-STORAGE-001": {
        "audit_type": "security_specialist_android_storage",
        "provider": "Devin CLI (Cognition) session runtime",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "model_requirement_status": "SATISFIED",
        "audited_sha": ANDROIDSTORAGE_AUDIT_SHA,
        "result": "PASS_WITH_FINDINGS",
        "candidate_count": 2, "architecture_gap_count": 3,
        "critical_count": 0, "high_count": 0,
        "medium_count": 0, "low_count": 2, "info_count": 0,
        "android_storage_production_files": "49/49 (100%)",
        "android_storage_relevant_test_files": "14/14 (100%)",
        "architecture_requirements": 42, "architecture_unmapped": 0,
        "focused_relevant_test_inventory": 153,
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
    "AUDIT-SECURITY-ATTACKCHAIN-001": {
        "audit_type": "cross_component_attackchain_security_audit",
        "provider": "Devin CLI (Cognition) session runtime",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "model_requirement_status": "SATISFIED",
        "audited_sha": ATTACKCHAIN_AUDIT_SHA,
        "result": "PASS_WITH_FINDINGS",
        "chain_count": 15, "critical_count": 0, "high_count": 4,
        "medium_count": 7, "low_count": 3, "info_count": 1,
        "e2_count": 8, "e1_count": 6, "e0_count": 1,
        "security_items_considered": 68, "security_items_unmapped": 0,
        "architecture_verdict": "CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED",
        "sec_c_required": "NO",
        "repository_modified_by_audit": "NO", "remote_mutation_by_audit": "NONE",
        "blindness_required": "NO",
    },
}

A1_SEVERITY = {"C-003": "CRITICAL"}
for _c in ("C-001", "C-002", "C-004"):
    A1_SEVERITY[_c] = "HIGH"
for _c in ("C-005", "C-006", "C-007", "C-008", "C-009", "C-010", "C-011", "C-012"):
    A1_SEVERITY[_c] = "MEDIUM"
for _c in ("C-013", "C-014", "C-015", "C-016", "C-017", "C-018", "C-019"):
    A1_SEVERITY[_c] = "LOW"
for _c in ("C-020", "C-021"):
    A1_SEVERITY[_c] = "INFO"
A1_IDS = {f"C-{i:03d}" for i in range(1, 22)}

A2_SEVERITY = {"C-001": "HIGH", "C-002": "HIGH", "C-003": "HIGH"}
for _c in ("C-004", "C-005", "C-006", "C-007", "C-008", "C-009"):
    A2_SEVERITY[_c] = "MEDIUM"
for _c in ("C-010", "C-011", "C-012", "C-013", "C-014", "C-015"):
    A2_SEVERITY[_c] = "LOW"
for _c in ("C-016", "C-017"):
    A2_SEVERITY[_c] = "INFO"
A2_IDS = {f"C-{i:03d}" for i in range(1, 18)}

ROOT_IDS = {f"ROOT-{i:03d}" for i in range(1, 19)}
PRE_B004_ROOTS = [
    "ROOT-001", "ROOT-002", "ROOT-003", "ROOT-004", "ROOT-005", "ROOT-006",
    "ROOT-007", "ROOT-008", "ROOT-009", "ROOT-013", "ROOT-014", "ROOT-017",
]
B008_B009_ROOTS = ["ROOT-010", "ROOT-011", "ROOT-012"]
FPG_ROOTS = ["ROOT-012", "ROOT-015"]

BUILDSC_SEVERITY = {
    "ANOX-BUILDSC-CANDIDATE-001": "HIGH", "ANOX-BUILDSC-CANDIDATE-002": "HIGH",
    "ANOX-BUILDSC-CANDIDATE-003": "HIGH",
    "ANOX-BUILDSC-CANDIDATE-004": "MEDIUM", "ANOX-BUILDSC-CANDIDATE-005": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-006": "MEDIUM", "ANOX-BUILDSC-CANDIDATE-007": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-008": "MEDIUM",
    "ANOX-BUILDSC-CANDIDATE-009": "LOW", "ANOX-BUILDSC-CANDIDATE-010": "LOW",
    "ANOX-BUILDSC-CANDIDATE-011": "LOW", "ANOX-BUILDSC-CANDIDATE-012": "INFO",
}
BUILDSC_IDS = set(BUILDSC_SEVERITY)

CRYPTOJNI_SEVERITY = {
    "ANOX-CRYPTOJNI-CANDIDATE-001": "HIGH",
    "ANOX-CRYPTOJNI-CANDIDATE-002": "MEDIUM",
    "ANOX-CRYPTOJNI-CANDIDATE-003": "MEDIUM",
    "ANOX-CRYPTOJNI-CANDIDATE-004": "MEDIUM",
    "ANOX-CRYPTOJNI-CANDIDATE-005": "LOW",
    "ANOX-CRYPTOJNI-CANDIDATE-006": "INFO",
}
CRYPTOJNI_IDS = set(CRYPTOJNI_SEVERITY)
CRYPTOJNI_PRE_B004 = {"ANOX-CRYPTOJNI-CANDIDATE-001", "ANOX-CRYPTOJNI-CANDIDATE-003"}
CRYPTOJNI_RELATIONS = {
    "ROOT-002": "CONFIRMED", "ROOT-014": "CONFIRMED",
    "ROOT-003": "CONFIRMED_AND_EXPANDED", "ROOT-004": "CONFIRMED_AND_EXPANDED",
    "ROOT-005": "CONFIRMED_AND_EXPANDED", "ROOT-013": "CONFIRMED_AND_EXPANDED",
    "ROOT-010": "ADJACENT_EXPANDED", "ROOT-011": "CONFIRMED_NO_EXPANSION",
}
PRE_B004_CRYPTOJNI_GATE = [
    "ROOT-002", "ROOT-003", "ROOT-004", "ROOT-005", "ROOT-013", "ROOT-014",
    "ANOX-CRYPTOJNI-CANDIDATE-001", "ANOX-CRYPTOJNI-CANDIDATE-003",
]
B008_B009_CRYPTOJNI_GATE = [
    "ANOX-CRYPTOJNI-CANDIDATE-002", "ANOX-CRYPTOJNI-CANDIDATE-004",
    "ANOX-CRYPTOJNI-CANDIDATE-005", "ROOT-010", "ROOT-011",
]
TEMP_BUILD_HASHES = {
    "arm64-v8a": "05f3f40cd4122ddd4286c513470f8bb6cdf54ca69b4c1879e53cb6a8ba22d7a2",
    "x86_64": "c002cc420813f3b8473be7aa82eb0af334bd73e6847cd1c893ce500845dfe798",
}

AUTHDPOP_ID = "AUDIT-SECURITY-AUTH-DPOP-001"
AUTHDPOP_REPORT_SHA = "57516d7d47e56447b7ab7a91aadaa2b7c3acdeda71e572b2b4366d2a6526b18e"
AUTHDPOP_SEVERITY = {
    "ANOX-AUTHDPOP-CANDIDATE-001": "MEDIUM",
    "ANOX-AUTHDPOP-CANDIDATE-002": "LOW",
    "ANOX-AUTHDPOP-CANDIDATE-003": "LOW",
}
AUTHDPOP_CANDIDATE_IDS = set(AUTHDPOP_SEVERITY)
AUTHDPOP_GAP_IDS = {"ANOX-AUTHDPOP-GAP-001", "ANOX-AUTHDPOP-GAP-002", "ANOX-AUTHDPOP-GAP-003"}
AUTHDPOP_RELATIONS = {
    "ROOT-006": "CONFIRMED", "ROOT-007": "CONFIRMED",
    "ROOT-008": "CONFIRMED_AND_EXPANDED", "ROOT-009": "CONFIRMED_AND_EXPANDED",
}
PRE_B004_AUTHDPOP_GATE = [
    "ROOT-006", "ROOT-007", "ROOT-008", "ROOT-009",
    "ANOX-AUTHDPOP-CANDIDATE-001",
    "ANOX-AUTHDPOP-GAP-001", "ANOX-AUTHDPOP-GAP-002", "ANOX-AUTHDPOP-GAP-003",
]
LATER_AUTHDPOP_GATE = [
    "ANOX-AUTHDPOP-CANDIDATE-002 (fix inside AD-A during B-004 Device-Auth wiring; NON_BLOCKING)",
    "ANOX-AUTHDPOP-CANDIDATE-003 (B-004 backend verifier implementation gate; contract entry in GAP-002 now)",
    "ANOX-MAINARCH-018 (physical StrongBox/TEE/Keystore semantics — Final Product Gate on provenance-verified binary)",
    "logout/wipe/revoke Device-Auth behaviour (B-013 lifecycle gate)",
    "instrumented DeviceAuth suites in CI (ROOT-017 track)",
]
AUTHDPOP_HIST_RELATIONS = {
    "ANOX-LEGACY-INTEGRATION-001": ("PARTIALLY_EFFECTIVE", "Closed"),
    "ANOX-LEGACY-INTEGRATION-003": ("STILL_EFFECTIVE", "Closed"),
    "ANOX-MAINARCH-019": ("STILL_EFFECTIVE", "Closed"),
    "ANOX-MAINARCH-008": ("STILL_EFFECTIVE_DOC_LAYER_RELATED_NEW_ROOT_CAUSE", "Closed"),
    "ANOX-SECURITY-ARCH-006": ("STILL_EFFECTIVE_OPEN", "Open"),
    "ANOX-SECURITY-ARCH-003": ("RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-007": ("INEFFECTIVE_REMEDIATION_SCOPE", "Open"),
    "ANOX-MAINARCH-005": ("STILL_EFFECTIVE", "Closed"),
    "ANOX-MAINARCH-014": ("NO_LONGER_APPLICABLE", "Closed"),
}
AUTHDPOP_COVERAGE_COUNTS = {
    "IMPLEMENTED_AND_VERIFIED": 15, "IMPLEMENTED_NOT_VERIFIED": 7,
    "PARTIALLY_IMPLEMENTED": 6, "IMPLEMENTATION_DRIFT": 6,
    "MISSING": 3, "NOT_APPLICABLE_YET": 3,
    "PHYSICAL_VERIFICATION_REQUIRED": 2, "UNMAPPED": 0,
}
AUTHDPOP_GROUPS = {"AD-A", "AD-B", "AD-C", "AD-D", "AD-E", "AD-F"}

ANDROIDSTORAGE_ID = "AUDIT-SECURITY-ANDROID-STORAGE-001"
ANDROIDSTORAGE_REPORT_SHA = "7532877dd14b97011d19f0b07a79bb50e529e4130feb0226c242b60d3e995720"
ANDROIDSTORAGE_SEVERITY = {
    "ANOX-ANDROIDSTORAGE-CANDIDATE-001": "LOW",
    "ANOX-ANDROIDSTORAGE-CANDIDATE-002": "LOW",
}
ANDROIDSTORAGE_CANDIDATE_IDS = set(ANDROIDSTORAGE_SEVERITY)
ANDROIDSTORAGE_GAP_IDS = {
    "ANOX-ANDROIDSTORAGE-GAP-001", "ANOX-ANDROIDSTORAGE-GAP-002",
    "ANOX-ANDROIDSTORAGE-GAP-003",
}
ANDROIDSTORAGE_RELATIONS = {
    "ROOT-006": "CONFIRMED_AND_EXPANDED", "ROOT-007": "CONFIRMED_AND_EXPANDED",
    "ROOT-010": "CONFIRMED", "ROOT-011": "CONFIRMED_AND_EXPANDED",
    "ROOT-012": "CONFIRMED_AND_EXPANDED", "ROOT-015": "CONFIRMED",
    "ROOT-017": "CONFIRMED",
}
PRE_B004_ANDROIDSTORAGE_GATE = [
    "ROOT-006", "ROOT-007",
    "ROOT-011 (registration/marker slice only - AAD/version binding, marker freshness cross-check; inseparable from ROOT-007 fix)",
    "ROOT-017",
    "ANOX-ANDROIDSTORAGE-CANDIDATE-001 (contract half via GAP-001/Auth GAP-002; code fix in AS-B)",
    "ANOX-ANDROIDSTORAGE-CANDIDATE-002",
    "ANOX-ANDROIDSTORAGE-GAP-001",
    "ANOX-ANDROIDSTORAGE-GAP-002 (contract)",
    "ANOX-ANDROIDSTORAGE-GAP-003 (contract)",
]
LATER_ANDROIDSTORAGE_GATE = [
    "ROOT-010 (Android best-effort clearing - B008/B009; AS-C/CJ-F; no exploit path before messaging)",
    "ROOT-011 identity/session anti-rollback mechanism (server epoch + AAD hook - B008/B009 with CJ-C)",
    "ROOT-012 wipe truthfulness + residue + cross-domain wipe implementation (B-013 lifecycle + Final Product Gate; design contract Pre-B004 via GAP-002)",
    "ROOT-015 (Final Product Gate; no storage consequence)",
    "ANOX-ANDROIDSTORAGE-CANDIDATE-001 code change (AS-B during B-004 registration wiring, after GAP-001 freeze)",
    "physical GrapheneOS campaign P1-P14 (Final gate on provenance-verified binary; ROOT-001 prerequisite)",
]
ANDROIDSTORAGE_HIST_RELATIONS = {
    "ANOX-SECURITY-ARCH-003": ("STILL_EFFECTIVE_OPEN_RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-007": ("INEFFECTIVE_REMEDIATION_SCOPE", "Open"),
    "ANOX-MAINARCH-023": ("PARTIALLY_EFFECTIVE", "Closed"),
    "ANOX-SECURITY-ARCH-008": ("STILL_EFFECTIVE_OPEN", "Open"),
    "ANOX-SECURITY-ARCH-009": ("STILL_EFFECTIVE_OPEN_RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-MAINARCH-030": ("STILL_EFFECTIVE_OPEN", "Open"),
    "ANOX-MAINARCH-018": ("PHYSICAL_REVALIDATION_REQUIRED", "Open"),
    "ANOX-LEGACY-INTEGRATION-002": ("STILL_EFFECTIVE_ORDERING_RELATED_NEW_ROOT_CAUSE", "Closed"),
    "ANOX-LEGACY-INTEGRATION-003": ("PARTIALLY_EFFECTIVE", "Closed"),
    "ANOX-LEGACY-ANDROIDSEC-001": ("STILL_EFFECTIVE", "Closed"),
    "ANOX-LEGACY-B003-001": ("SUPERSEDED_BY_SAME_ROOT_ROOT-015", "Open"),
}
ANDROIDSTORAGE_COVERAGE_COUNTS = {
    "IMPLEMENTED_AND_VERIFIED": 6, "IMPLEMENTED_NOT_VERIFIED": 5,
    "PARTIALLY_IMPLEMENTED": 10, "IMPLEMENTATION_DRIFT": 10,
    "MISSING": 4, "NOT_APPLICABLE_YET": 3,
    "PHYSICAL_VERIFICATION_REQUIRED": 3, "SERVER_PREREQUISITE": 0,
    "ARCHITECTURE_GAP": 1, "UNMAPPED": 0,
}
ANDROIDSTORAGE_GROUPS = {"AS-A", "AS-B", "AS-C", "AS-D", "AS-E", "AS-F", "AS-G"}

ATTACKCHAIN_ID = "AUDIT-SECURITY-ATTACKCHAIN-001"
ATTACKCHAIN_REPORT_SHA = "a4feac55f49066647ec0c1665c40deab581115da4b102e81eb6742e72b80ca9e"
ATTACKCHAIN_SEVERITY = {
    "ANOX-ATTACKCHAIN-CANDIDATE-001": "HIGH",
    "ANOX-ATTACKCHAIN-CANDIDATE-002": "MEDIUM",
    "ANOX-ATTACKCHAIN-CANDIDATE-003": "HIGH",
    "ANOX-ATTACKCHAIN-CANDIDATE-004": "MEDIUM",
    "ANOX-ATTACKCHAIN-CANDIDATE-005": "MEDIUM",
    "ANOX-ATTACKCHAIN-CANDIDATE-006": "HIGH",
    "ANOX-ATTACKCHAIN-CANDIDATE-007": "MEDIUM",
    "ANOX-ATTACKCHAIN-CANDIDATE-008": "MEDIUM",
    "ANOX-ATTACKCHAIN-CANDIDATE-009": "LOW",
    "ANOX-ATTACKCHAIN-CANDIDATE-010": "MEDIUM",
    "ANOX-ATTACKCHAIN-CANDIDATE-011": "MEDIUM",
    "ANOX-ATTACKCHAIN-CANDIDATE-012": "HIGH",
    "ANOX-ATTACKCHAIN-CANDIDATE-013": "INFO",
    "ANOX-ATTACKCHAIN-CANDIDATE-014": "LOW",
    "ANOX-ATTACKCHAIN-CANDIDATE-015": "LOW",
}
ATTACKCHAIN_IDS = set(ATTACKCHAIN_SEVERITY)
ATTACKCHAIN_EVIDENCE = {
    "ANOX-ATTACKCHAIN-CANDIDATE-001": "E2", "ANOX-ATTACKCHAIN-CANDIDATE-002": "E2",
    "ANOX-ATTACKCHAIN-CANDIDATE-003": "E2", "ANOX-ATTACKCHAIN-CANDIDATE-004": "E2",
    "ANOX-ATTACKCHAIN-CANDIDATE-005": "E1", "ANOX-ATTACKCHAIN-CANDIDATE-006": "E1",
    "ANOX-ATTACKCHAIN-CANDIDATE-007": "E2", "ANOX-ATTACKCHAIN-CANDIDATE-008": "E1",
    "ANOX-ATTACKCHAIN-CANDIDATE-009": "E2", "ANOX-ATTACKCHAIN-CANDIDATE-010": "E1",
    "ANOX-ATTACKCHAIN-CANDIDATE-011": "E1", "ANOX-ATTACKCHAIN-CANDIDATE-012": "E2",
    "ANOX-ATTACKCHAIN-CANDIDATE-013": "E0", "ANOX-ATTACKCHAIN-CANDIDATE-014": "E2",
    "ANOX-ATTACKCHAIN-CANDIDATE-015": "E1",
}
ATTACKCHAIN_HIGH = {"ANOX-ATTACKCHAIN-CANDIDATE-001", "ANOX-ATTACKCHAIN-CANDIDATE-003",
                    "ANOX-ATTACKCHAIN-CANDIDATE-006", "ANOX-ATTACKCHAIN-CANDIDATE-012"}
ATTACKCHAIN_ROOT_COVERAGE = {
    "ROOT-001": "META_EVIDENCE_ISSUE", "ROOT-002": "PARTICIPATES_IN_CONFIRMED_CHAIN",
    "ROOT-003": "CONFIRMED", "ROOT-004": "CONFIRMED", "ROOT-005": "CONFIRMED",
    "ROOT-006": "CONFIRMED", "ROOT-007": "CONFIRMED", "ROOT-008": "CONFIRMED",
    "ROOT-009": "CONFIRMED", "ROOT-010": "POTENTIAL", "ROOT-011": "CONFIRMED",
    "ROOT-012": "CONFIRMED", "ROOT-013": "CONFIRMED", "ROOT-014": "CONFIRMED",
    "ROOT-015": "STANDALONE_SECURITY_ISSUE", "ROOT-016": "NOT_CHAIN_RELEVANT",
    "ROOT-017": "ENABLING_CONDITION_ONLY", "ROOT-018": "META_EVIDENCE_ISSUE",
}
ATTACKCHAIN_SPEC_COVERAGE = {
    "ANOX-BUILDSC-CANDIDATE-001": "META_EVIDENCE_ISSUE",
    "ANOX-BUILDSC-CANDIDATE-002": "ENABLING_CONDITION_ONLY",
    "ANOX-BUILDSC-CANDIDATE-003": "ENABLING_CONDITION_ONLY",
    "ANOX-BUILDSC-CANDIDATE-004": "META_EVIDENCE_ISSUE",
    "ANOX-BUILDSC-CANDIDATE-005": "ENABLING_CONDITION_ONLY",
    "ANOX-BUILDSC-CANDIDATE-006": "ENABLING_CONDITION_ONLY",
    "ANOX-BUILDSC-CANDIDATE-007": "STANDALONE_SECURITY_ISSUE",
    "ANOX-BUILDSC-CANDIDATE-008": "ENABLING_CONDITION_ONLY",
    "ANOX-BUILDSC-CANDIDATE-009": "NOT_CHAIN_RELEVANT",
    "ANOX-BUILDSC-CANDIDATE-010": "NOT_CHAIN_RELEVANT",
    "ANOX-BUILDSC-CANDIDATE-011": "NOT_CHAIN_RELEVANT",
    "ANOX-BUILDSC-CANDIDATE-012": "NOT_CHAIN_RELEVANT",
    "ANOX-CRYPTOJNI-CANDIDATE-001": "PARTICIPATES_IN_CONFIRMED_CHAIN",
    "ANOX-CRYPTOJNI-CANDIDATE-002": "PARTICIPATES_IN_POTENTIAL_CHAIN",
    "ANOX-CRYPTOJNI-CANDIDATE-003": "PARTICIPATES_IN_CONFIRMED_CHAIN",
    "ANOX-CRYPTOJNI-CANDIDATE-004": "PARTICIPATES_IN_POTENTIAL_CHAIN",
    "ANOX-CRYPTOJNI-CANDIDATE-005": "PARTICIPATES_IN_POTENTIAL_CHAIN",
    "ANOX-CRYPTOJNI-CANDIDATE-006": "ENABLING_CONDITION_ONLY",
    "ANOX-AUTHDPOP-CANDIDATE-001": "PARTICIPATES_IN_CONFIRMED_CHAIN",
    "ANOX-AUTHDPOP-CANDIDATE-002": "PARTICIPATES_IN_CONFIRMED_CHAIN",
    "ANOX-AUTHDPOP-CANDIDATE-003": "PARTICIPATES_IN_CONFIRMED_CHAIN",
    "ANOX-ANDROIDSTORAGE-CANDIDATE-001": "PARTICIPATES_IN_CONFIRMED_CHAIN",
    "ANOX-ANDROIDSTORAGE-CANDIDATE-002": "PARTICIPATES_IN_CONFIRMED_CHAIN",
}
ATTACKCHAIN_GAP_COVERAGE = {
    "ANOX-AUTHDPOP-GAP-001": "CHAIN_RELEVANT",
    "ANOX-AUTHDPOP-GAP-002": "CHAIN_CRITICAL",
    "ANOX-AUTHDPOP-GAP-003": "CHAIN_CRITICAL",
    "ANOX-ANDROIDSTORAGE-GAP-001": "CHAIN_CRITICAL",
    "ANOX-ANDROIDSTORAGE-GAP-002": "CHAIN_RELEVANT",
    "ANOX-ANDROIDSTORAGE-GAP-003": "CHAIN_RELEVANT",
}
ATTACKCHAIN_PARTICIPATION = {
    "total_security_items": 68, "mapped_to_confirmed_chain": 29,
    "mapped_to_potential_chain": 6, "standalone": 3, "enabling_only": 14,
    "meta_only": 9, "not_chain_relevant": 7, "unmapped": 0,
}
ATTACKCHAIN_SERVER_BREAKER_IDS = {f"S{i}" for i in range(1, 19)}
ATTACKCHAIN_CLIENT_BREAKER_IDS = {f"C{i}" for i in range(1, 15)}
ATTACKCHAIN_HIST_RELATIONS = {
    "ANOX-SECURITY-ARCH-007": ("INEFFECTIVE_REMEDIATION_SCOPE", "Open"),
    "ANOX-LEGACY-INTEGRATION-001": ("PARTIALLY_EFFECTIVE", "Closed"),
    "ANOX-LEGACY-INTEGRATION-003": ("PARTIALLY_EFFECTIVE", "Closed"),
    "ANOX-LEGACY-CRYPTO-005": ("LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION", "Closed"),
    "ANOX-MAINARCH-023": ("PARTIALLY_EFFECTIVE", "Closed"),
    "ANOX-MAINARCH-031": ("FALSE_CLOSURE_HISTORICAL_INSTANCE", "Closed"),
    "ANOX-SECURITY-ARCH-001": ("RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-002": ("RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-003": ("RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-004": ("RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-006": ("RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-008": ("RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-SECURITY-ARCH-009": ("STILL_EFFECTIVE_OPEN_RELATED_NEW_ROOT_CAUSE", "Open"),
    "ANOX-MAINARCH-013": ("STILL_EFFECTIVE_OPEN", "Open"),
    "ANOX-MAINARCH-018": ("PHYSICAL_REVALIDATION_REQUIRED", "Open"),
    "ANOX-MAINARCH-030": ("STILL_EFFECTIVE_OPEN", "Open"),
    "ANOX-LEGACY-INTEGRATION-005": ("NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING", "Open"),
    "ANOX-LEGACY-B003-001": ("SUPERSEDED_BY_SAME_ROOT_ROOT-015", "Open"),
}
ATTACKCHAIN_REAUDIT_MANDATORY = [
    "ANOX-ATTACKCHAIN-CANDIDATE-001", "ANOX-ATTACKCHAIN-CANDIDATE-003",
    "ANOX-ATTACKCHAIN-CANDIDATE-006", "ANOX-ATTACKCHAIN-CANDIDATE-012",
]
PRE_B004_ATTACKCHAIN_CODE_GATE = [
    "AC-001 client half (C1-C5; AS-A/AS-B/AD-E)",
    "AC-006 + AC-007 merged JNI ABI revision (CJ-A/B/C/D/E; C6-C8)",
    "AC-011 (singletons + serialized creation; CJ-E/AD-A/AS-A)",
    "AC-012 native build chain (pin, cross-build, hash gate, validator v2, instrumented JNI - precondition)",
    "AC-002/AC-003/AC-004 client-side API hardening (C9; AD-B/AD-C/AD-D)",
    "AC-009 (C4)",
]
PRE_B004_ATTACKCHAIN_CONTRACT_GATE = [
    "ANOX-AUTHDPOP-GAP-003 (S1, S2, S16)",
    "ANOX-AUTHDPOP-GAP-002 (S7, S8, S10, S11, S12, S17, S4)",
    "ANOX-AUTHDPOP-GAP-001 (S9)",
    "ANOX-AUTHDPOP-CANDIDATE-001 (S5)",
    "ANOX-ANDROIDSTORAGE-GAP-001 (marker/session/first-run/armed-release contract)",
    "ANOX-ANDROIDSTORAGE-GAP-002 (wipe/logout/delete contract)",
    "ANOX-ANDROIDSTORAGE-GAP-003 (backup/reinstall/anti-rollback authority - S15)",
]
B004_IMPLEMENTATION_GATE = [
    "server enforces S1-S12 and S17",
    "shared replay store",
    "registration PoP verification",
    "AuthenticatedDeviceContext from validated key",
    "AC-014 RejectedAfterArm code change during registration wiring (after GAP-001 freeze)",
    "ANOX-AUTHDPOP-CANDIDATE-002 fix inside Device-Auth wiring",
]
LATER_GATE_ATTACKCHAINS_GATE = [
    "AC-005 -> B006 (publication/ACK/epoch, S13-S15) and B008/B009 (session rollback, CJ-CAND-002)",
    "AC-008 -> B013 (wipe/logout/delete) + B006 (S16) + Final gate (ROOT-012 retest); contract half Pre-B004 via AS-GAP-002",
    "AC-015 -> B008/B009 (CJ-F/AS-C)",
    "AC-013 -> Final/Physical only, on provenance-verified binary (ROOT-001 prerequisite)",
    "AC-004 server half -> B004 backend implementation gate (contract entry Pre-B004)",
]
ATTACKCHAIN_EVENT0049_FINDINGS = {
    "ANOX-SECURITY-ARCH-001": "Open", "ANOX-SECURITY-ARCH-002": "Open",
    "ANOX-SECURITY-ARCH-003": "Open", "ANOX-SECURITY-ARCH-004": "Open",
    "ANOX-SECURITY-ARCH-006": "Open", "ANOX-SECURITY-ARCH-007": "Open",
    "ANOX-SECURITY-ARCH-008": "Open", "ANOX-SECURITY-ARCH-009": "Open",
    "ANOX-MAINARCH-013": "Open", "ANOX-MAINARCH-018": "Open",
    "ANOX-MAINARCH-023": "Closed", "ANOX-MAINARCH-030": "Open",
    "ANOX-MAINARCH-031": "Closed", "ANOX-LEGACY-INTEGRATION-001": "Closed",
    "ANOX-LEGACY-INTEGRATION-003": "Closed", "ANOX-LEGACY-INTEGRATION-005": "Open",
    "ANOX-LEGACY-CRYPTO-005": "Closed", "ANOX-LEGACY-B003-001": "Open",
}

METADATA_ALLOWLIST = {
    "PROJECT_STATE.md", "FORTSCHRITT.md", "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
    "docs/continuity/CURRENT_STATE.json", "docs/continuity/CURRENT_GIT_STATE.md",
    "docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_OPEN_WORK.md",
    "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
    "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
    "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
    "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
    "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
    "docs/workforce/registries/decisions.jsonl", "docs/workforce/registries/findings.jsonl",
    "docs/workforce/registries/tasks.jsonl", "docs/workforce/registries/runs.jsonl",
    "docs/workforce/registries/audits.jsonl", "docs/workforce/registries/derived_work.jsonl",
    "docs/workforce/WORKFORCE_STATE.json", "docs/workforce/WORKFORCE_STATE_SNAPSHOT.json",
}
FORBIDDEN_PREFIXES = ("android/", "crypto/rust/", "backend/", ".github/workflows/", "supabase/", "migrations/")


def fail(msg, errors):
    errors.append(msg)


def load_jsonl(path):
    r = []
    if not path.exists():
        return r
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r.append(json.loads(line))
    return r


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _rev_parse(ref):
    out = subprocess.run(["git", "rev-parse", ref], cwd=REPO_ROOT, capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def has_git():
    return (REPO_ROOT / ".git").is_dir()


def validate_base(errors):
    if not has_git():
        print("  SKIP git checks (no .git — fixture mode)")
        return
    sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
    import lifecycle_legality as ll
    head = _rev_parse("HEAD")
    if not ll._git_is_ancestor(BASE_SHA, head, cwd=REPO_ROOT):
        fail(f"base {BASE_SHA} not ancestor of {head}", errors)
        return
    print(f"  OK   base {BASE_SHA[:12]} is ancestor of {head[:12]}")
    state = load_json(REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json")
    described = state.get("described_head") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", described):
        fail(f"CURRENT_STATE described_head is not a valid SHA: {described}", errors)
        return
    ok, _, _, reason = ll.canonical_two_commit_delivery(
        BASE_SHA, described, head,
        canonical_branch="main", delivery_branch=DELIVERY_BRANCH,
        cwd=REPO_ROOT, metadata_allowlist=METADATA_ALLOWLIST,
    )
    if not ok:
        fail(f"canonical two-commit delivery failed: {reason}", errors)
        return
    print("  OK   exactly 2 task-authored commits above base (merge-aware)")


def validate_reports(errors):
    hashes = {}
    hpath = EVIDENCE_DIR / "evidence_hashes.json"
    if not hpath.exists():
        fail("evidence_hashes.json missing", errors)
    else:
        try:
            hashes = (load_json(hpath).get("reports") or {})
        except Exception as e:
            fail(f"evidence_hashes.json unreadable: {e}", errors)
    for name, spec in EXPECTED_REPORTS.items():
        p = REPO_ROOT / spec["path"]
        if not p.exists():
            fail(f"preserved report missing: {spec['path']}", errors)
            continue
        actual = sha256_file(p)
        if actual != spec["sha256"]:
            fail(f"report {name} hash mismatch: {actual} != {spec['sha256']}", errors)
            continue
        rec = hashes.get(name) or {}
        if rec.get("sha256") != spec["sha256"]:
            fail(f"evidence_hashes.json entry for {name} mismatched/missing", errors)
        elif rec.get("source_present") != "YES":
            fail(f"evidence_hashes.json {name} source_present != YES", errors)
        else:
            print(f"  OK   {name} preserved byte-exact ({spec['sha256'][:16]}...)")
    src = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl") if (EVIDENCE_DIR / "audit_traceability.jsonl").exists() else []
    src_recs = [r for r in src if r.get("record_type") == "source_status"]
    for name in EXPECTED_REPORTS:
        rec = next((r for r in src_recs if r.get("audit_name") == name or r.get("audit_id") == name or EXPECTED_AUDITS.get(r.get("audit_id"), {}).get("audit_name") == name or r.get("audit_id") == EXPECTED_AUDITS.get(name, {}).get("audit_id")), None)
        if rec is None:
            # match by preserved_path
            rec = next((r for r in src_recs if r.get("preserved_path") == EXPECTED_REPORTS[name]["path"]), None)
        if rec is None:
            fail(f"source_status record missing for {name}", errors)
        elif rec.get("source_present") != "YES":
            fail(f"source_status for {name} is not YES", errors)


def validate_registry(errors):
    audits = {a.get("audit_id"): a for a in load_jsonl(EVIDENCE_DIR / "audit_registry.jsonl")}
    if not audits:
        fail("audit_registry.jsonl missing or empty", errors)
        return
    if len(audits) != 11:
        fail(f"audit_registry.jsonl must contain exactly 11 records (9 audits + 1 master consolidation artifact + 1 coverage gate artifact), found {len(audits)}", errors)
    msc_rec = audits.get(MSC_ID) or {}
    if msc_rec.get("artifact_type") != "MASTER_SECURITY_CONSOLIDATION":
        fail(f"{MSC_ID} registry record missing or artifact_type != MASTER_SECURITY_CONSOLIDATION", errors)
    gate_rec = audits.get(GATE_ID) or {}
    if gate_rec.get("artifact_type") != "SECURITY_REMEDIATION_COVERAGE_GATE":
        fail(f"{GATE_ID} registry record missing or artifact_type != SECURITY_REMEDIATION_COVERAGE_GATE", errors)
    if (audits.keys() - set(EXPECTED_AUDITS) - {MSC_ID, GATE_ID}):
        fail(f"audit_registry.jsonl contains unexpected records: {sorted(audits.keys() - set(EXPECTED_AUDITS) - {MSC_ID, GATE_ID})}", errors)
    for aid, spec in EXPECTED_AUDITS.items():
        rec = audits.get(aid)
        if rec is None:
            fail(f"audit registry missing {aid}", errors)
            continue
        for key, expected in spec.items():
            if key == "blindness_status_prefix":
                if not str(rec.get("blindness_status", "")).startswith(expected):
                    fail(f"{aid} blindness_status {rec.get('blindness_status')!r} lacks prefix {expected!r}", errors)
                continue
            if rec.get(key) != expected:
                fail(f"{aid} {key}={rec.get(key)!r}, expected {expected!r}", errors)
        rep = rec.get("report_path")
        if rep not in {s["path"] for s in EXPECTED_REPORTS.values()}:
            fail(f"{aid} report_path not a preserved report: {rep!r}", errors)
        if rec.get("report_sha256") != EXPECTED_REPORTS.get(rec.get("audit_name", ""), {}).get("sha256"):
            fail(f"{aid} report_sha256 mismatch vs evidence_hashes expectation", errors)
    a1 = audits.get("AUDIT-SECURITY-CODEBASE-001") or {}
    if "MODEL_DEVIATION" not in str(a1.get("model_requirement_status", "")):
        fail("AUDIT-SECURITY-CODEBASE-001 model_requirement_status must record MODEL_DEVIATION", errors)
    a2 = audits.get("AUDIT-SECURITY-CODEBASE-002") or {}
    if a2.get("blindness_status", "").startswith("PRESERVED"):
        print("  OK   Audit-002 blindness preserved")
    else:
        fail("AUDIT-SECURITY-CODEBASE-002 blindness_status must start with PRESERVED", errors)
    print("  OK   audit registry records verified")


def validate_traceability(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")
    if not recs:
        fail("audit_traceability.jsonl missing or empty", errors)
        return

    a1 = [r for r in recs if r.get("record_type") == "audit001_candidate"]
    a1_refs = {r.get("consensus_ref") for r in a1}
    if len(a1) != 21 or a1_refs != A1_IDS:
        fail(f"Audit-001 traceability must cover 21/21 candidates; got {len(a1)}", errors)
    else:
        print("  OK   Audit-001 21/21 candidates traced")
    for r in a1:
        cref = r.get("consensus_ref")
        if A1_SEVERITY.get(cref) != r.get("severity"):
            fail(f"Audit-001 {cref} severity {r.get('severity')!r} != {A1_SEVERITY.get(cref)!r}", errors)
        if not r.get("consensus_roots"):
            fail(f"Audit-001 {cref} has no consensus_roots", errors)
    c19 = next((r for r in a1 if r.get("consensus_ref") == "C-019"), None)
    if c19 is None:
        fail("Audit-001 C-019 candidate missing from traceability", errors)
    elif c19.get("candidate_id") != "ANOX-CODESEC-CANDIDATE-019" or "ROOT-008" not in c19.get("consensus_roots", []):
        fail("Audit-001 C-019 traceability content wrong", errors)
    else:
        print("  OK   Audit-001 C-019 present and mapped")

    a2 = [r for r in recs if r.get("record_type") == "audit002_candidate"]
    a2_local = {r.get("audit_local_id") for r in a2}
    if len(a2) != 17 or a2_local != A2_IDS:
        fail(f"Audit-002 traceability must cover 17/17 candidates; got {len(a2)}", errors)
    else:
        print("  OK   Audit-002 17/17 candidates traced")
    for r in a2:
        lid = r.get("audit_local_id")
        if A2_SEVERITY.get(lid) != r.get("severity"):
            fail(f"Audit-002 {lid} severity {r.get('severity')!r} != {A2_SEVERITY.get(lid)!r}", errors)
        if not r.get("consensus_roots"):
            fail(f"Audit-002 {lid} has no consensus_roots", errors)

    roots = {r.get("root_id"): r for r in recs if r.get("record_type") == "consensus_root"}
    if set(roots) != ROOT_IDS:
        fail(f"consensus roots must be exactly ROOT-001..018; got {sorted(roots)}", errors)
    else:
        print("  OK   18 consensus roots ROOT-001..018")
    r5 = roots.get("ROOT-005") or {}
    if r5.get("audit001_sources"):
        fail("ROOT-005 has a fabricated Audit-001 source candidate", errors)
    elif r5.get("audit002_sources") != ["C-003"]:
        fail("ROOT-005 audit002_sources must be [C-003]", errors)
    else:
        print("  OK   ROOT-005 has no Audit-001 source (SINGLE_AUDIT_CONFIRMED_BY_ARBITER)")
    r16 = roots.get("ROOT-016") or {}
    if r16.get("status") != "REJECTED_NOT_A_FINDING" or r16.get("severity") != "NONE":
        fail("ROOT-016 must remain REJECTED_NOT_A_FINDING / severity NONE", errors)
    else:
        print("  OK   ROOT-016 remains rejected, not a real finding")
    for rid in ("ROOT-001", "ROOT-002", "ROOT-003", "ROOT-004", "ROOT-005"):
        if (roots.get(rid) or {}).get("severity") != "HIGH":
            fail(f"{rid} must be HIGH", errors)

    gates = {g.get("gate"): g for g in recs if g.get("record_type") == "gate_set"}
    pre = gates.get("PRE_B004_ROOTS") or {}
    if sorted(pre.get("roots") or []) != sorted(PRE_B004_ROOTS):
        fail(f"PRE_B004_ROOTS set wrong: {pre.get('roots')}", errors)
    else:
        print("  OK   12-root Pre-B004 set exact")
    if sorted((gates.get("B008_B009_ROOTS") or {}).get("roots") or []) != sorted(B008_B009_ROOTS):
        fail("B008_B009_ROOTS set wrong", errors)
    if sorted((gates.get("FINAL_PRODUCT_GATE_ROOTS") or {}).get("roots") or []) != sorted(FPG_ROOTS):
        fail("FINAL_PRODUCT_GATE_ROOTS set wrong", errors)

    bs = {r.get("candidate_id"): r for r in recs if r.get("record_type") == "buildsc_candidate"}
    if set(bs) != BUILDSC_IDS:
        fail(f"Build/Supply traceability must cover 12/12 candidates; got {sorted(bs)}", errors)
    else:
        print("  OK   Build/Supply 12/12 candidates traced")
    for cid, sev in BUILDSC_SEVERITY.items():
        if (bs.get(cid) or {}).get("severity") != sev:
            fail(f"{cid} severity {(bs.get(cid) or {}).get('severity')!r} != {sev!r}", errors)
    b1 = bs.get("ANOX-BUILDSC-CANDIDATE-001") or {}
    if b1.get("evidence_integrity") != "CRITICAL":
        fail("ANOX-BUILDSC-CANDIDATE-001 must carry EVIDENCE_INTEGRITY=CRITICAL", errors)
    else:
        print("  OK   BUILDSC-001 EVIDENCE_INTEGRITY=CRITICAL preserved")

    rels = {r.get("finding_id"): r for r in recs if r.get("record_type") == "historical_relation"}
    c5 = rels.get("ANOX-LEGACY-CRYPTO-005") or {}
    if c5.get("relationship") != "LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION" or c5.get("canonical_status") != "Closed":
        fail("historical relation ANOX-LEGACY-CRYPTO-005 must be Closed + LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION", errors)
    i5 = rels.get("ANOX-LEGACY-INTEGRATION-005") or {}
    if i5.get("relationship") != "NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING" or i5.get("canonical_status") != "Open":
        fail("historical relation ANOX-LEGACY-INTEGRATION-005 must be Open + NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING", errors)

    ng = next((r for r in recs if r.get("record_type") == "next_gate" and r.get("gate") == NEXT_GATE_ID), None)
    if not ng or "NOT_EXECUTED" not in str(ng.get("status", "")):
        fail(f"next_gate record must be {NEXT_GATE_ID} CANDIDATE / NOT_EXECUTED", errors)
    pg = next((r for r in recs if r.get("record_type") == "next_gate" and r.get("gate") == PRIOR_GATE_ID), None)
    if not pg or "EXECUTED_AND_PRESERVED" not in str(pg.get("status", "")):
        fail(f"next_gate record for {PRIOR_GATE_ID} must be EXECUTED_AND_PRESERVED", errors)


def validate_cryptojni(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")

    cj = {r.get("candidate_id"): r for r in recs if r.get("record_type") == "cryptojni_candidate"}
    if set(cj) != CRYPTOJNI_IDS:
        fail(f"Crypto/JNI traceability must cover exactly 6 candidates; got {sorted(cj)}", errors)
    else:
        print("  OK   Crypto/JNI 6/6 candidates traced")
    for cid, sev in CRYPTOJNI_SEVERITY.items():
        r = cj.get(cid) or {}
        if r.get("severity") != sev:
            fail(f"{cid} severity {r.get('severity')!r} != {sev!r}", errors)
        if r.get("source_audit_id") != "AUDIT-SECURITY-CRYPTO-JNI-001":
            fail(f"{cid} source_audit_id wrong: {r.get('source_audit_id')!r}", errors)
        if r.get("status") != "Open":
            fail(f"{cid} must remain Open (candidate), got {r.get('status')!r}", errors)
        want_pre = cid in CRYPTOJNI_PRE_B004
        if bool(r.get("pre_b004_blocker")) != want_pre:
            fail(f"{cid} pre_b004_blocker={r.get('pre_b004_blocker')!r}, expected {want_pre}", errors)

    rels = {r.get("root_id"): r for r in recs if r.get("record_type") == "specialist_relation" and r.get("source_audit_id") == "AUDIT-SECURITY-CRYPTO-JNI-001"}
    if set(rels) != set(CRYPTOJNI_RELATIONS):
        fail(f"specialist_relation roots must be exactly {sorted(CRYPTOJNI_RELATIONS)}; got {sorted(rels)}", errors)
    for rid, rel in CRYPTOJNI_RELATIONS.items():
        if (rels.get(rid) or {}).get("relation") != rel:
            fail(f"specialist_relation {rid} relation {(rels.get(rid) or {}).get('relation')!r} != {rel!r}", errors)

    ov = next((r for r in recs if r.get("record_type") == "severity_overlay" and r.get("root_id") == "ROOT-013"), None)
    if ov is None:
        fail("ROOT-013 severity overlay record missing", errors)
    else:
        if ov.get("prior_severity") != "LOW" or ov.get("proposed_severity") != "MEDIUM":
            fail("ROOT-013 overlay must record prior LOW -> proposed MEDIUM", errors)
        if ov.get("status") != "PENDING_SPECIALIST_CONSOLIDATION":
            fail("ROOT-013 overlay status must be PENDING_SPECIALIST_CONSOLIDATION", errors)
    roots = {r.get("root_id"): r for r in recs if r.get("record_type") == "consensus_root"}
    if (roots.get("ROOT-013") or {}).get("severity") != "LOW":
        fail("consensus_root ROOT-013 severity was silently overwritten (must remain LOW; overlay only)", errors)
    else:
        print("  OK   ROOT-013 overlay pending consolidation; consensus severity untouched")

    gsets = {r.get("gate_set"): r for r in recs if r.get("record_type") == "gate_set" and r.get("gate_set")}
    pre = gsets.get("PRE_B004_CRYPTOJNI") or {}
    if sorted(pre.get("members") or []) != sorted(PRE_B004_CRYPTOJNI_GATE):
        fail(f"PRE_B004_CRYPTOJNI members wrong: {pre.get('members')}", errors)
    else:
        print("  OK   PRE_B004_CRYPTOJNI 8-member gate set exact")
    b89 = gsets.get("B008_B009_CRYPTOJNI") or {}
    if sorted(b89.get("members") or []) != sorted(B008_B009_CRYPTOJNI_GATE):
        fail(f"B008_B009_CRYPTOJNI members wrong: {b89.get('members')}", errors)
    else:
        print("  OK   B008_B009_CRYPTOJNI 5-member gate set exact")

    prov = next((r for r in recs if r.get("record_type") == "provenance_limitation"), None)
    if prov is None:
        fail("provenance_limitation record missing", errors)
    else:
        for k, h in (("committed_arm64", "11a958a5f8b653692fdbf189dd42fa373cff729fdfef0cc5748afc5bfd3ea6c3"),
                     ("committed_x86_64", "ecf9fdc1e83e419f1e1b9da6e83e184f5b3dfe694ee5de13529d68fc60653c88"),
                     ("temp_arm64", TEMP_BUILD_HASHES["arm64-v8a"]),
                     ("temp_x86_64", TEMP_BUILD_HASHES["x86_64"])):
            if prov.get(k) != h:
                fail(f"provenance_limitation {k} hash wrong", errors)
        if "TEMP_CURRENT_SOURCE_BUILD_EVIDENCE" not in str(prov.get("runtime_policy", "")):
            fail("provenance_limitation must restrict runtime claims to TEMP_CURRENT_SOURCE_BUILD_EVIDENCE", errors)
        if "PROVENANCE_VERIFIED_CANONICAL_BINARY" not in str(prov.get("runtime_policy", "")):
            fail("provenance_limitation must require PROVENANCE_VERIFIED_CANONICAL_BINARY for final closure", errors)
        if "7db20fa4df8dc70392afd803fabaaf20c0b50d7d" not in str(prov.get("binary_source_commit", "")):
            fail("provenance_limitation must record committed .so source commit 7db20fa", errors)

    tb = next((r for r in recs if r.get("record_type") == "temp_build_evidence"), None)
    if tb is None:
        fail("temp_build_evidence record missing", errors)
    else:
        outs = tb.get("outputs") or {}
        for abi, h in TEMP_BUILD_HASHES.items():
            if (outs.get(abi) or {}).get("sha256") != h:
                fail(f"temp_build_evidence {abi} hash wrong/missing", errors)
        if tb.get("audited_sha") != CRYPTOJNI_AUDIT_SHA:
            fail("temp_build_evidence audited_sha must equal audited SHA a79166ab", errors)
        if "NOT" not in str(tb.get("canonicality", "")):
            fail("temp_build_evidence must record non-canonical / temporary status", errors)

    abi = next((r for r in recs if r.get("record_type") == "abi_revision"), None)
    if abi is None:
        fail("abi_revision record missing", errors)
    else:
        if abi.get("jni_abi_revision") != "YES":
            fail("abi_revision must record JNI_ABI_REVISION=YES", errors)
        if abi.get("sec_c_required") != "NO":
            fail("abi_revision must record SEC_C_REQUIRED=NO", errors)
        if abi.get("architecture_verdict") != "COMPONENT_INTERNAL_REDESIGN_ONLY":
            fail("abi_revision verdict must be COMPONENT_INTERNAL_REDESIGN_ONLY", errors)

    coupling = {(r.get("list")): r for r in recs if r.get("record_type") == "fix_coupling"}
    if "MUST_FIX_TOGETHER" not in coupling or "MUST_NOT_FIX_ALONE" not in coupling:
        fail("fix_coupling records (MUST_FIX_TOGETHER / MUST_NOT_FIX_ALONE) missing", errors)
    else:
        print("  OK   Crypto/JNI provenance limitation, temp-build evidence, ABI revision, fix couplings recorded")


def validate_authdpop(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")

    cands = {r.get("candidate_id"): r for r in recs if r.get("record_type") == "authdpop_candidate"}
    if set(cands) != AUTHDPOP_CANDIDATE_IDS:
        fail(f"Auth/DPoP traceability must cover exactly 3 candidates; got {sorted(cands)}", errors)
    else:
        print("  OK   Auth/DPoP 3/3 candidates traced")
    for cid, sev in AUTHDPOP_SEVERITY.items():
        r = cands.get(cid) or {}
        if r.get("severity") != sev:
            fail(f"{cid} severity {r.get('severity')!r} != {sev!r}", errors)
        if r.get("source_audit_id") != AUTHDPOP_ID:
            fail(f"{cid} source_audit_id wrong: {r.get('source_audit_id')!r}", errors)
        if r.get("status") != "Open" or r.get("disposition") != "OPEN_PENDING_CONSOLIDATION":
            fail(f"{cid} must remain Open/OPEN_PENDING_CONSOLIDATION", errors)
        want_pre = cid == "ANOX-AUTHDPOP-CANDIDATE-001"
        if bool(r.get("pre_b004_blocker")) != want_pre:
            fail(f"{cid} pre_b004_blocker={r.get('pre_b004_blocker')!r}, expected {want_pre}", errors)
        if not (r.get("group") or r.get("remediation_group")):
            fail(f"{cid} missing remediation-coverage group", errors)
        if r.get("retest_required") != "YES" or not r.get("independent_retest_owner"):
            fail(f"{cid} missing independent retest requirement", errors)
    if (cands.get("ANOX-AUTHDPOP-CANDIDATE-001") or {}).get("pre_b004_blocker") is True:
        print("  OK   CANDIDATE-001 is the sole Pre-B004 blocker candidate")

    gaps = {r.get("gap_id"): r for r in recs if r.get("record_type") == "authdpop_gap"}
    if set(gaps) != AUTHDPOP_GAP_IDS:
        fail(f"Auth/DPoP gaps must be exactly GAP-001..003; got {sorted(gaps)}", errors)
    else:
        print("  OK   Auth/DPoP 3/3 architecture gaps traced")
    for gid in AUTHDPOP_GAP_IDS:
        r = gaps.get(gid) or {}
        if r.get("source_audit_id") != AUTHDPOP_ID or r.get("status") != "Open":
            fail(f"{gid} source/status wrong", errors)
        if r.get("pre_b004_contract_freeze") is not True:
            fail(f"{gid} must record pre_b004_contract_freeze=True", errors)

    rels = {r.get("root_id"): r for r in recs
            if r.get("record_type") == "specialist_relation" and r.get("source_audit_id") == AUTHDPOP_ID}
    if set(rels) != set(AUTHDPOP_RELATIONS):
        fail(f"Auth/DPoP specialist_relation roots must be exactly {sorted(AUTHDPOP_RELATIONS)}; got {sorted(rels)}", errors)
    for rid, rel in AUTHDPOP_RELATIONS.items():
        if (rels.get(rid) or {}).get("relation") != rel:
            fail(f"specialist_relation {rid} relation {(rels.get(rid) or {}).get('relation')!r} != {rel!r}", errors)
    roots = {r.get("root_id"): r for r in recs if r.get("record_type") == "consensus_root"}
    for rid in AUTHDPOP_RELATIONS:
        if rid not in roots:
            fail(f"specialist_relation {rid} points at a consensus root that does not exist", errors)
    if (roots.get("ROOT-016") or {}).get("status") != "REJECTED_NOT_A_FINDING":
        fail("ROOT-016 must remain REJECTED_NOT_A_FINDING (Auth/DPoP CANDIDATE-002 must not revive it)", errors)
    else:
        print("  OK   ROOT-016 remains rejected; Auth/DPoP relations exact (006/007 CONFIRMED, 008/009 CONFIRMED_AND_EXPANDED)")

    gsets = {r.get("gate_set"): r for r in recs if r.get("record_type") == "gate_set" and r.get("gate_set")}
    pre = gsets.get("PRE_B004_AUTHDPOP") or {}
    if sorted(pre.get("members") or []) != sorted(PRE_B004_AUTHDPOP_GATE):
        fail(f"PRE_B004_AUTHDPOP members wrong: {pre.get('members')}", errors)
    else:
        print("  OK   PRE_B004_AUTHDPOP 8-member gate set exact")
    lat = gsets.get("LATER_AUTHDPOP") or {}
    if sorted(lat.get("members") or []) != sorted(LATER_AUTHDPOP_GATE):
        fail(f"LATER_AUTHDPOP members wrong: {lat.get('members')}", errors)
    else:
        print("  OK   LATER_AUTHDPOP 5-item gate set exact")

    relmap = {r.get("finding_id"): r for r in recs
              if r.get("record_type") == "historical_relation" and r.get("source_audit_id") == AUTHDPOP_ID}
    if set(relmap) != set(AUTHDPOP_HIST_RELATIONS):
        fail(f"Auth/DPoP historical_relation records must cover {sorted(AUTHDPOP_HIST_RELATIONS)}; got {sorted(relmap)}", errors)
    for fid, (rel, st) in AUTHDPOP_HIST_RELATIONS.items():
        r = relmap.get(fid) or {}
        if r.get("relationship") != rel or r.get("canonical_status") != st:
            fail(f"historical_relation {fid}: relationship {r.get('relationship')!r}/{r.get('canonical_status')!r} != {rel!r}/{st!r}", errors)
    reval = next((r for r in recs if r.get("record_type") == "authdpop_historical_revalidation"
                  and r.get("source_audit_id") == AUTHDPOP_ID), None)
    if reval is None or len(reval.get("rows") or []) != 17:
        fail("authdpop_historical_revalidation record missing or must contain the 17 revalidation rows", errors)
    else:
        print("  OK   Auth/DPoP historical revalidation table preserved (17 rows)")

    cov = next((r for r in recs if r.get("record_type") == "authdpop_coverage"
                and r.get("source_audit_id") == AUTHDPOP_ID), None)
    if cov is None:
        fail("authdpop_coverage record missing", errors)
    else:
        if (cov.get("b002_production_files_reviewed"), cov.get("b002_production_files_discovered")) != (29, 29):
            fail("authdpop_coverage must record 29/29 production files", errors)
        if (cov.get("b002_relevant_test_files_reviewed"), cov.get("b002_relevant_test_files_discovered")) != (14, 14):
            fail("authdpop_coverage must record 14/14 relevant test files", errors)
        if cov.get("architecture_requirements_total") != 40:
            fail("authdpop_coverage must record 40 architecture requirements", errors)
        if cov.get("status_counts") != AUTHDPOP_COVERAGE_COUNTS:
            fail(f"authdpop_coverage status_counts wrong: {cov.get('status_counts')}", errors)
        inv = cov.get("focused_test_inventory") or {}
        if (inv.get("total"), inv.get("jvm"), inv.get("instrumented"), inv.get("physical")) != (155, 128, 27, 0):
            fail("authdpop_coverage focused_test_inventory must be 155 (128 JVM / 27 instrumented / 0 physical)", errors)
        ex = cov.get("audit_test_execution") or {}
        if (ex.get("executed"), ex.get("passed"), ex.get("failed"), ex.get("errors"), ex.get("skipped")) != (173, 173, 0, 0, 0):
            fail("authdpop_coverage audit_test_execution must record 173/173 PASS", errors)
        if (cov.get("adversarial_harness") or {}).get("cases") != 22:
            fail("authdpop_coverage must record 22 adversarial cases", errors)
        else:
            print("  OK   Auth/DPoP coverage 29/29 + 14/14 + 40 reqs (0 unmapped); inventory 155; executed 173/173; 22 adversarial cases")

    phys = next((r for r in recs if r.get("record_type") == "physical_evidence_requirements"
                 and r.get("source_audit_id") == AUTHDPOP_ID), None)
    if phys is None or "NOT_EXECUTED" not in str(phys.get("status", "")):
        fail("physical_evidence_requirements record missing or not NOT_EXECUTED", errors)
    else:
        print("  OK   Auth/DPoP physical evidence requirements recorded as NOT_EXECUTED")

    rem = next((r for r in recs if r.get("record_type") == "authdpop_remediation"
                and r.get("source_audit_id") == AUTHDPOP_ID), None)
    if rem is None:
        fail("authdpop_remediation record missing", errors)
    else:
        if set(rem.get("groups") or {}) != AUTHDPOP_GROUPS:
            fail(f"authdpop_remediation groups must be AD-A..AD-F; got {sorted(rem.get('groups') or {})}", errors)
        if rem.get("sec_c_required") != "NO" or rem.get("architecture_verdict") != "COMPONENT_INTERNAL_REDESIGN_ONLY":
            fail("authdpop_remediation SEC-C=NO / COMPONENT_INTERNAL_REDESIGN_ONLY verdict wrong", errors)
        else:
            print("  OK   Auth/DPoP remediation groups AD-A..AD-F; SEC-C=NO; COMPONENT_INTERNAL_REDESIGN_ONLY")

    coupling = {(r.get("list"), r.get("source_audit_id")): r for r in recs if r.get("record_type") == "authdpop_fix_coupling"}
    if ("MUST_FIX_TOGETHER", AUTHDPOP_ID) not in coupling or ("MUST_NOT_FIX_ALONE", AUTHDPOP_ID) not in coupling:
        fail("Auth/DPoP fix_coupling records (MUST_FIX_TOGETHER / MUST_NOT_FIX_ALONE) missing", errors)

    for rt in ("attackchain_handoff", "android_storage_handoff"):
        h = next((r for r in recs if r.get("record_type") == rt and r.get("source_audit_id") == AUTHDPOP_ID), None)
        if h is None or "NOT_EXECUTED" not in str(h.get("status", "")):
            fail(f"{rt} record missing or not CANDIDATE/NOT_EXECUTED", errors)
    print("  OK   Auth/DPoP fix couplings + Android/Storage + Attackchain handoffs recorded")


def validate_androidstorage(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")

    cands = {r.get("candidate_id"): r for r in recs if r.get("record_type") == "androidstorage_candidate"}
    if set(cands) != ANDROIDSTORAGE_CANDIDATE_IDS:
        fail(f"Android/Storage traceability must cover exactly 2 candidates; got {sorted(cands)}", errors)
    else:
        print("  OK   Android/Storage 2/2 candidates traced")
    for cid, sev in ANDROIDSTORAGE_SEVERITY.items():
        r = cands.get(cid) or {}
        if r.get("severity") != sev:
            fail(f"{cid} severity {r.get('severity')!r} != {sev!r}", errors)
        if r.get("source_audit_id") != ANDROIDSTORAGE_ID:
            fail(f"{cid} source_audit_id wrong: {r.get('source_audit_id')!r}", errors)
        if r.get("status") != "Open" or r.get("disposition") != "OPEN_PENDING_CONSOLIDATION":
            fail(f"{cid} must remain Open/OPEN_PENDING_CONSOLIDATION", errors)
        if r.get("pre_b004_blocker") is not True:
            fail(f"{cid} pre_b004_blocker={r.get('pre_b004_blocker')!r}, expected True", errors)
        if not (r.get("group") or r.get("remediation_group")):
            fail(f"{cid} missing remediation-coverage group", errors)
        if r.get("retest_required") != "YES" or not r.get("independent_retest_owner"):
            fail(f"{cid} missing independent retest requirement", errors)

    gaps = {r.get("gap_id"): r for r in recs if r.get("record_type") == "androidstorage_gap"}
    if set(gaps) != ANDROIDSTORAGE_GAP_IDS:
        fail(f"Android/Storage gaps must be exactly GAP-001..003; got {sorted(gaps)}", errors)
    else:
        print("  OK   Android/Storage 3/3 architecture gaps traced")
    for gid in ANDROIDSTORAGE_GAP_IDS:
        r = gaps.get(gid) or {}
        if r.get("source_audit_id") != ANDROIDSTORAGE_ID or r.get("status") != "Open":
            fail(f"{gid} source/status wrong", errors)
        if r.get("pre_b004_contract_freeze") is not True:
            fail(f"{gid} must record pre_b004_contract_freeze=True", errors)

    rels = {r.get("root_id"): r for r in recs
            if r.get("record_type") == "specialist_relation" and r.get("source_audit_id") == ANDROIDSTORAGE_ID}
    if set(rels) != set(ANDROIDSTORAGE_RELATIONS):
        fail(f"Android/Storage specialist_relation roots must be exactly {sorted(ANDROIDSTORAGE_RELATIONS)}; got {sorted(rels)}", errors)
    for rid, rel in ANDROIDSTORAGE_RELATIONS.items():
        if (rels.get(rid) or {}).get("relation") != rel:
            fail(f"specialist_relation {rid} relation {(rels.get(rid) or {}).get('relation')!r} != {rel!r}", errors)
    roots = {r.get("root_id"): r for r in recs if r.get("record_type") == "consensus_root"}
    for rid in ANDROIDSTORAGE_RELATIONS:
        if rid not in roots:
            fail(f"specialist_relation {rid} points at a consensus root that does not exist", errors)
    # Consensus severities must remain untouched by specialist relations.
    unchanged = {"ROOT-006": "MEDIUM", "ROOT-007": "MEDIUM", "ROOT-010": "LOW",
                 "ROOT-011": "MEDIUM", "ROOT-012": "LOW", "ROOT-015": "LOW"}
    for rid, sev in unchanged.items():
        if (roots.get(rid) or {}).get("severity") != sev:
            fail(f"consensus_root {rid} severity silently overwritten (expected {sev})", errors)
    if (roots.get("ROOT-016") or {}).get("status") != "REJECTED_NOT_A_FINDING":
        fail("ROOT-016 must remain REJECTED_NOT_A_FINDING (Android/Storage must not revive it)", errors)
    else:
        print("  OK   Android/Storage relations exact (006/007/011/012 expanded; 010/015/017 confirmed); ROOT-016 remains rejected")

    gsets = {r.get("gate_set"): r for r in recs if r.get("record_type") == "gate_set" and r.get("gate_set")}
    pre = gsets.get("PRE_B004_ANDROIDSTORAGE") or {}
    if sorted(pre.get("members") or []) != sorted(PRE_B004_ANDROIDSTORAGE_GATE):
        fail(f"PRE_B004_ANDROIDSTORAGE members wrong: {pre.get('members')}", errors)
    else:
        print("  OK   PRE_B004_ANDROIDSTORAGE 9-member gate set exact")
    lat = gsets.get("LATER_ANDROIDSTORAGE") or {}
    if sorted(lat.get("members") or []) != sorted(LATER_ANDROIDSTORAGE_GATE):
        fail(f"LATER_ANDROIDSTORAGE members wrong: {lat.get('members')}", errors)
    else:
        print("  OK   LATER_ANDROIDSTORAGE 6-item gate set exact")

    relmap = {r.get("finding_id"): r for r in recs
              if r.get("record_type") == "historical_relation" and r.get("source_audit_id") == ANDROIDSTORAGE_ID}
    if set(relmap) != set(ANDROIDSTORAGE_HIST_RELATIONS):
        fail(f"Android/Storage historical_relation records must cover {sorted(ANDROIDSTORAGE_HIST_RELATIONS)}; got {sorted(relmap)}", errors)
    for fid, (rel, st) in ANDROIDSTORAGE_HIST_RELATIONS.items():
        r = relmap.get(fid) or {}
        if r.get("relationship") != rel or r.get("canonical_status") != st:
            fail(f"historical_relation {fid}: relationship {r.get('relationship')!r}/{r.get('canonical_status')!r} != {rel!r}/{st!r}", errors)
    reval = next((r for r in recs if r.get("record_type") == "androidstorage_historical_revalidation"
                  and r.get("source_audit_id") == ANDROIDSTORAGE_ID), None)
    if reval is None or len(reval.get("rows") or []) != 23:
        fail("androidstorage_historical_revalidation record missing or must contain the 23 revalidation rows", errors)
    else:
        print("  OK   Android/Storage historical revalidation table preserved (23 rows)")

    cov = next((r for r in recs if r.get("record_type") == "androidstorage_coverage"
                and r.get("source_audit_id") == ANDROIDSTORAGE_ID), None)
    if cov is None:
        fail("androidstorage_coverage record missing", errors)
    else:
        if (cov.get("android_storage_production_files_reviewed"), cov.get("android_storage_production_files_discovered")) != (49, 49):
            fail("androidstorage_coverage must record 49/49 production files", errors)
        if (cov.get("android_storage_relevant_test_files_reviewed"), cov.get("android_storage_relevant_test_files_discovered")) != (14, 14):
            fail("androidstorage_coverage must record 14/14 relevant test files", errors)
        if cov.get("architecture_requirements_total") != 42:
            fail("androidstorage_coverage must record 42 architecture requirements", errors)
        if cov.get("status_counts") != ANDROIDSTORAGE_COVERAGE_COUNTS:
            fail(f"androidstorage_coverage status_counts wrong: {cov.get('status_counts')}", errors)
        inv = cov.get("focused_test_inventory") or {}
        if (inv.get("total"), inv.get("jvm"), inv.get("instrumented"), inv.get("physical")) != (153, 87, 66, 0):
            fail("androidstorage_coverage focused_test_inventory must be 153 (87 JVM / 66 instrumented / 0 physical)", errors)
        ex = cov.get("audit_test_execution") or {}
        if (ex.get("executed"), ex.get("passed"), ex.get("failed"), ex.get("errors"), ex.get("skipped")) != (177, 177, 0, 0, 0):
            fail("androidstorage_coverage audit_test_execution must record 177/177 PASS", errors)
        else:
            print("  OK   Android/Storage coverage 49/49 + 14/14 + 42 reqs (0 unmapped); inventory 153; executed 177/177")

    phys = next((r for r in recs if r.get("record_type") == "physical_evidence_requirements"
                 and r.get("source_audit_id") == ANDROIDSTORAGE_ID), None)
    if phys is None or "NOT_EXECUTED" not in str(phys.get("status", "")):
        fail("Android/Storage physical_evidence_requirements record missing or not NOT_EXECUTED", errors)
    elif len(phys.get("items") or []) != 14:
        fail("Android/Storage physical_evidence_requirements must record the P1-P14 campaign", errors)
    else:
        print("  OK   Android/Storage physical evidence requirements (P1-P14) recorded as NOT_EXECUTED")

    rem = next((r for r in recs if r.get("record_type") == "androidstorage_remediation"
                and r.get("source_audit_id") == ANDROIDSTORAGE_ID), None)
    if rem is None:
        fail("androidstorage_remediation record missing", errors)
    else:
        if set(rem.get("groups") or {}) != ANDROIDSTORAGE_GROUPS:
            fail(f"androidstorage_remediation groups must be AS-A..AS-G; got {sorted(rem.get('groups') or {})}", errors)
        if rem.get("sec_c_required") != "NO" or rem.get("architecture_verdict") != "COMPONENT_INTERNAL_REDESIGN_ONLY":
            fail("androidstorage_remediation SEC-C=NO / COMPONENT_INTERNAL_REDESIGN_ONLY verdict wrong", errors)
        else:
            print("  OK   Android/Storage remediation groups AS-A..AS-G; SEC-C=NO; COMPONENT_INTERNAL_REDESIGN_ONLY")

    coupling = {(r.get("list"), r.get("source_audit_id")): r for r in recs if r.get("record_type") == "androidstorage_fix_coupling"}
    if ("MUST_FIX_TOGETHER", ANDROIDSTORAGE_ID) not in coupling or ("MUST_NOT_FIX_ALONE", ANDROIDSTORAGE_ID) not in coupling:
        fail("Android/Storage fix_coupling records (MUST_FIX_TOGETHER / MUST_NOT_FIX_ALONE) missing", errors)

    h = next((r for r in recs if r.get("record_type") == "attackchain_handoff"
              and r.get("source_audit_id") == ANDROIDSTORAGE_ID), None)
    if h is None or "NOT_EXECUTED" not in str(h.get("status", "")):
        fail("Android/Storage attackchain_handoff record missing or not CANDIDATE/NOT_EXECUTED", errors)
    else:
        print("  OK   Android/Storage fix couplings + Attackchain handoff recorded")


def validate_attackchain(errors):
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")

    ac_raw = [r for r in recs if r.get("record_type") == "attackchain_candidate"
              and r.get("source_audit_id") == ATTACKCHAIN_ID]
    if len(ac_raw) != 15:
        fail(f"Attackchain traceability must contain exactly 15 chain records (no missing/duplicates); got {len(ac_raw)}", errors)
    cands = {r.get("chain_id"): r for r in recs if r.get("record_type") == "attackchain_candidate"}
    if set(cands) != ATTACKCHAIN_IDS:
        fail(f"Attackchain traceability must cover exactly 15 chains; got {sorted(cands)}", errors)
    else:
        print("  OK   Attackchain 15/15 chain candidates traced")
    for cid, sev in ATTACKCHAIN_SEVERITY.items():
        r = cands.get(cid) or {}
        if r.get("severity") != sev:
            fail(f"{cid} severity {r.get('severity')!r} != {sev!r}", errors)
        if r.get("evidence_level") != ATTACKCHAIN_EVIDENCE.get(cid):
            fail(f"{cid} evidence_level {r.get('evidence_level')!r} != {ATTACKCHAIN_EVIDENCE.get(cid)!r}", errors)
        if r.get("source_audit_id") != ATTACKCHAIN_ID:
            fail(f"{cid} source_audit_id wrong: {r.get('source_audit_id')!r}", errors)
        if r.get("status") != "Open" or r.get("disposition") != "OPEN_PENDING_CONSOLIDATION":
            fail(f"{cid} must remain Open/OPEN_PENDING_CONSOLIDATION", errors)
        if not r.get("attacker_class"):
            fail(f"{cid} missing attacker_class", errors)
        if not r.get("activation_gate"):
            fail(f"{cid} missing activation_gate", errors)
        if not r.get("impact"):
            fail(f"{cid} missing impact", errors)
        if cid not in ("ANOX-ATTACKCHAIN-CANDIDATE-013", "ANOX-ATTACKCHAIN-CANDIDATE-015") \
                and not r.get("state_transitions"):
            fail(f"{cid} missing state_transitions", errors)
        if not r.get("current_mitigations"):
            fail(f"{cid} missing current_mitigations", errors)
        if not r.get("required_test"):
            fail(f"{cid} missing required_test", errors)
        if not r.get("chain_breakers"):
            fail(f"{cid} missing chain_breakers", errors)
        if r.get("retest_required") != "YES" or not r.get("independent_retest_owner"):
            fail(f"{cid} missing independent retest requirement", errors)
        if not r.get("pre_b004_or_later"):
            fail(f"{cid} missing pre_b004_or_later classification", errors)
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for r in cands.values():
        sev_counts[r.get("severity", "")] = sev_counts.get(r.get("severity", ""), 0) + 1
    if sev_counts != {"CRITICAL": 0, "HIGH": 4, "MEDIUM": 7, "LOW": 3, "INFO": 1}:
        fail(f"Attackchain severity distribution must be 0C/4H/7M/3L/1I; got {sev_counts}", errors)
    ev_counts = {"E0": 0, "E1": 0, "E2": 0}
    for r in cands.values():
        ev_counts[r.get("evidence_level", "")] = ev_counts.get(r.get("evidence_level", ""), 0) + 1
    if ev_counts != {"E0": 1, "E1": 6, "E2": 8}:
        fail(f"Attackchain evidence distribution must be E2=8/E1=6/E0=1; got {ev_counts}", errors)
    ac3 = cands.get("ANOX-ATTACKCHAIN-CANDIDATE-003") or {}
    if ac3.get("severity_overlay") != "CONDITIONAL_CRITICAL_AT_B004_IF_VERIFIER_DEFAULTS_PORTED":
        fail("AC-003 must carry the CONDITIONAL_CRITICAL_AT_B004_IF_VERIFIER_DEFAULTS_PORTED overlay (canonical severity stays HIGH)", errors)
    ac12 = cands.get("ANOX-ATTACKCHAIN-CANDIDATE-012") or {}
    if "FALSE_CLOSURE" not in str(ac12.get("classification", "")):
        fail("AC-012 must remain classified FALSE_CLOSURE_CHAIN", errors)
    if "CURRENTLY_REACHABLE" not in str(ac12.get("reachability", "")):
        fail("AC-012 reachability must be CURRENTLY_REACHABLE", errors)
    print("  OK   severity 0C/4H/7M/3L/1I; evidence E2=8/E1=6/E0=1; AC-003 overlay; AC-012 FALSE_CLOSURE/CURRENTLY_REACHABLE")

    part = next((r for r in recs if r.get("record_type") == "attackchain_participation"
                 and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if part is None:
        fail("attackchain_participation record missing", errors)
    else:
        for k, v in ATTACKCHAIN_PARTICIPATION.items():
            if part.get(k) != v:
                fail(f"attackchain_participation {k}={part.get(k)!r}, expected {v!r}", errors)
        if part.get("unmapped") != 0 or part.get("total_security_items") != 68:
            fail("attackchain_participation must record 68 items / UNMAPPED=0", errors)
        else:
            print("  OK   security-item coverage 68 total / 0 unmapped (29/6/3/14/9/7)")

    roots = next((r for r in recs if r.get("record_type") == "attackchain_root_coverage"
                  and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if roots is None or set((roots.get("roots") or {}).keys()) != ROOT_IDS:
        fail("attackchain_root_coverage must record all 18 roots", errors)
    else:
        rr = roots.get("roots") or {}
        for rid, disp in ATTACKCHAIN_ROOT_COVERAGE.items():
            if (rr.get(rid) or {}).get("disposition") != disp:
                fail(f"attackchain_root_coverage {rid} disposition {(rr.get(rid) or {}).get('disposition')!r} != {disp!r}", errors)
        if "REJECTED" not in str((rr.get("ROOT-016") or {}).get("note", "")):
            fail("attackchain_root_coverage ROOT-016 note must record it remains REJECTED/not revived", errors)
        else:
            print("  OK   root coverage 18/18; ROOT-016 remains REJECTED / not revived")

    spec = next((r for r in recs if r.get("record_type") == "attackchain_specialist_coverage"
                 and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if spec is None or set((spec.get("candidates") or {}).keys()) != set(ATTACKCHAIN_SPEC_COVERAGE):
        fail("attackchain_specialist_coverage must record all 23 specialist candidates", errors)
    else:
        cc = spec.get("candidates") or {}
        for cid, disp in ATTACKCHAIN_SPEC_COVERAGE.items():
            if (cc.get(cid) or {}).get("disposition") != disp:
                fail(f"attackchain_specialist_coverage {cid} {(cc.get(cid) or {}).get('disposition')!r} != {disp!r}", errors)
        print("  OK   specialist candidate coverage 23/23")

    gaps = next((r for r in recs if r.get("record_type") == "attackchain_gap_coverage"
                 and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if gaps is None or set((gaps.get("gaps") or {}).keys()) != set(ATTACKCHAIN_GAP_COVERAGE):
        fail("attackchain_gap_coverage must record all 6 architecture gaps", errors)
    else:
        gg = gaps.get("gaps") or {}
        for gid, cls in ATTACKCHAIN_GAP_COVERAGE.items():
            if cls not in str((gg.get(gid) or {}).get("classification", "")):
                fail(f"attackchain_gap_coverage {gid} classification lacks {cls}", errors)
        print("  OK   architecture gap coverage 6/6 (3 CHAIN_CRITICAL)")

    sb = next((r for r in recs if r.get("record_type") == "attackchain_server_breakers"
               and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if sb is None or {i.get("id") for i in (sb.get("items") or [])} != ATTACKCHAIN_SERVER_BREAKER_IDS:
        fail("attackchain_server_breakers must record S1-S18", errors)
    else:
        print("  OK   server breakers S1-S18 complete")
    cb = next((r for r in recs if r.get("record_type") == "attackchain_client_breakers"
               and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if cb is None or {i.get("id") for i in (cb.get("items") or [])} != ATTACKCHAIN_CLIENT_BREAKER_IDS:
        fail("attackchain_client_breakers must record C1-C14", errors)
    else:
        print("  OK   client breakers C1-C14 complete")

    for rt, key in (("attackchain_cross_group_dependencies", "relations"),
                    ("attackchain_must_not_fix_alone", "warnings"),
                    ("attackchain_threat_actors", "actors"),
                    ("attackchain_trust_boundaries", "boundaries"),
                    ("attackchain_state_graph", "transitions")):
        r = next((x for x in recs if x.get("record_type") == rt and x.get("source_audit_id") == ATTACKCHAIN_ID), None)
        if r is None or not r.get(key):
            fail(f"{rt} record missing or empty ({key})", errors)
    ta = next((x for x in recs if x.get("record_type") == "attackchain_threat_actors"
               and x.get("source_audit_id") == ATTACKCHAIN_ID), None) or {}
    if set((ta.get("actors") or {}).keys()) != {f"A{i}" for i in range(10)}:
        fail("attackchain_threat_actors must record A0-A9", errors)
    tb = next((x for x in recs if x.get("record_type") == "attackchain_trust_boundaries"
               and x.get("source_audit_id") == ATTACKCHAIN_ID), None) or {}
    if len(tb.get("boundaries") or []) != 9:
        fail("attackchain_trust_boundaries must record 9 boundaries", errors)
    print("  OK   cross-group dependencies, must-not-fix-alone, actors A0-A9, 9 trust boundaries, state graph")

    rej = next((r for r in recs if r.get("record_type") == "attackchain_rejected"
                and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if rej is None or len(rej.get("hypotheses") or []) != 13:
        fail("attackchain_rejected must record 13 rejected hypotheses", errors)
    else:
        print("  OK   13 rejected chain hypotheses preserved")

    rea = next((r for r in recs if r.get("record_type") == "attackchain_reaudit_set"
                and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if rea is None or sorted(rea.get("mandatory") or []) != sorted(ATTACKCHAIN_REAUDIT_MANDATORY):
        fail("attackchain_reaudit_set mandatory must be AC-001/003/006/012", errors)
    elif sorted(rea.get("mandatory_plus_trust_boundary") or []) != sorted(
            ["ANOX-ATTACKCHAIN-CANDIDATE-005", "ANOX-ATTACKCHAIN-CANDIDATE-008",
             "ANOX-ATTACKCHAIN-CANDIDATE-010"]):
        fail("attackchain_reaudit_set mandatory_plus_trust_boundary must be AC-005/008/010", errors)
    else:
        print("  OK   final re-audit set recorded (mandatory + trust-boundary)")

    gsets = {r.get("gate_set"): r for r in recs if r.get("record_type") == "gate_set" and r.get("gate_set")}
    for name, members in (("PRE_B004_ATTACKCHAIN_CODE", PRE_B004_ATTACKCHAIN_CODE_GATE),
                          ("PRE_B004_ATTACKCHAIN_CONTRACT", PRE_B004_ATTACKCHAIN_CONTRACT_GATE),
                          ("B004_IMPLEMENTATION_REQUIREMENTS", B004_IMPLEMENTATION_GATE),
                          ("LATER_GATE_ATTACKCHAINS", LATER_GATE_ATTACKCHAINS_GATE)):
        g = gsets.get(name) or {}
        if g.get("source_audit_id") != ATTACKCHAIN_ID or sorted(g.get("members") or []) != sorted(members):
            fail(f"gate_set {name} members wrong: {g.get('members')}", errors)
    print("  OK   Pre-B004 code/contract, B004 implementation and later-gate sets exact")

    relmap = {r.get("finding_id"): r for r in recs
              if r.get("record_type") == "historical_relation" and r.get("source_audit_id") == ATTACKCHAIN_ID}
    if set(relmap) != set(ATTACKCHAIN_HIST_RELATIONS):
        fail(f"Attackchain historical_relation records must cover {sorted(ATTACKCHAIN_HIST_RELATIONS)}; got {sorted(relmap)}", errors)
    for fid, (rel, st) in ATTACKCHAIN_HIST_RELATIONS.items():
        r = relmap.get(fid) or {}
        if r.get("relationship") != rel or r.get("canonical_status") != st:
            fail(f"historical_relation {fid}: {r.get('relationship')!r}/{r.get('canonical_status')!r} != {rel!r}/{st!r}", errors)
    print("  OK   18 historical participation relations preserved (no status rewrites)")

    tee = next((r for r in recs if r.get("record_type") == "test_execution_evidence"
                and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if tee is None or "Harness.java" not in str(tee.get("result", "")):
        fail("attackchain test_execution_evidence missing or lacks harness results", errors)
    adv = next((r for r in recs if r.get("record_type") == "adversarial_evidence"
                and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if adv is None or adv.get("cases") != 36 or not adv.get("failures"):
        fail("attackchain adversarial_evidence must record 36 cases with failure rows", errors)
    phys = next((r for r in recs if r.get("record_type") == "physical_evidence_requirements"
                 and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if phys is None or "NOT_EXECUTED" not in str(phys.get("status", "")):
        fail("attackchain physical_evidence_requirements must record NOT_EXECUTED", errors)
    else:
        print("  OK   test/adversarial/physical evidence records (36 harness cases; physical NOT_EXECUTED)")

    mch = next((r for r in recs if r.get("record_type") == "master_consolidation_handoff"
                and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if mch is None or "NOT_EXECUTED" not in str(mch.get("status", "")) or len(mch.get("chain_ids") or []) != 15:
        fail("master_consolidation_handoff must record all 15 chains and NOT_EXECUTED status", errors)
    rch = next((r for r in recs if r.get("record_type") == "remediation_coverage_handoff"
                and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if rch is None or len(rch.get("chains") or {}) != 15:
        fail("remediation_coverage_handoff must record all 15 chains", errors)
    lim = next((r for r in recs if r.get("record_type") == "attackchain_evidence_limits"
                and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if lim is None or not lim.get("limits"):
        fail("attackchain_evidence_limits record missing", errors)
    print("  OK   master consolidation + remediation coverage handoffs; evidence limits recorded")

    v = next((r for r in recs if r.get("record_type") == "attackchain_verdict"
              and r.get("source_audit_id") == ATTACKCHAIN_ID), None)
    if v is None or v.get("architecture_verdict") != "CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED" or v.get("sec_c_required") != "NO":
        fail("attackchain_verdict must record CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED / SEC-C=NO", errors)


def validate_master_consolidation(errors):
    """Fail-closed verification of the preserved MASTER-SPECIALIST-CONSOLIDATION-001
    evidence layer (artifact_type MASTER_SECURITY_CONSOLIDATION)."""
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")
    msc = [r for r in recs if r.get("source_artifact_id") == MSC_ID]
    by_type = {}
    for r in msc:
        by_type.setdefault(r.get("record_type"), []).append(r)

    def one(rt):
        rows = by_type.get(rt) or []
        if len(rows) != 1:
            fail(f"expected exactly 1 {rt} record for {MSC_ID}, found {len(rows)}", errors)
            return {}
        return rows[0]

    audits = {a.get("audit_id"): a for a in load_jsonl(EVIDENCE_DIR / "audit_registry.jsonl")}
    reg = audits.get(MSC_ID) or {}
    reg_expected = {
        "artifact_type": "MASTER_SECURITY_CONSOLIDATION",
        "base_sha": CONSOLIDATION_BASE_SHA,
        "audited_sha": CONSOLIDATION_BASE_SHA,
        "requested_start_sha": CONSOLIDATION_BASE_SHA,
        "result": "PASS_WITH_CONSOLIDATION_FINDINGS",
        "actual_model": "Claude Fable 5.1 High",
        "requested_model": "Claude Fable 5.1 High",
        "model_requirement_status": "SATISFIED",
        "repository_modified_by_audit": "NO",
        "remote_mutation_by_audit": "NONE",
        "status": "PRESERVED",
        "preserved_at_event": MSC_LEDGER_EVENT,
        "report_path": EXPECTED_REPORTS[MSC_ID]["path"],
        "report_sha256": EXPECTED_REPORTS[MSC_ID]["sha256"],
        "report_bytes": 121113,
        "source_reports": 9,
        "source_reports_hash_verified": 9,
        "source_security_items": 90,
        "source_items_accounted": 90,
        "source_items_unaccounted": 0,
        "msc_units": 44,
        "msc_open": 42,
        "msc_rejected": 2,
        "attackchains": 15,
        "attackchains_without_msc_unit": 0,
        "server_breakers": 18,
        "server_breakers_unassigned": 0,
        "client_breakers": 14,
        "client_breakers_unassigned": 0,
        "dependency_cycles": 0,
        "silent_dropped": 0,
        "architecture_finding_coverage_loss": 0,
        "legacy_findings_without_owner": 0,
        "architecture_verdict": "CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED",
        "sec_c_required": "NO",
    }
    for key, expected in reg_expected.items():
        if reg.get(key) != expected:
            fail(f"{MSC_ID} registry {key}={reg.get(key)!r}, expected {expected!r}", errors)
    if reg.get("delivery_branch") != MSC_DELIVERY_BRANCH:
        fail(f"{MSC_ID} registry delivery_branch must be {MSC_DELIVERY_BRANCH}", errors)
    if not reg:
        fail(f"{MSC_ID} registry record missing", errors)
    else:
        print(f"  OK   {MSC_ID} registry artifact record verified")

    # --- source accountability: 90 items -------------------------------------
    src_items = by_type.get("msc_source_item") or []
    if len(src_items) != MSC_SOURCE_ITEM_COUNT:
        fail(f"msc_source_item must contain exactly {MSC_SOURCE_ITEM_COUNT} items, found {len(src_items)}", errors)
    sids = [r.get("source_id") for r in src_items]
    if len(set(sids)) != len(sids):
        fail("duplicate msc_source_item source_id values", errors)
    cls = {}
    for r in src_items:
        cls[r.get("item_type")] = cls.get(r.get("item_type"), 0) + 1
        if r.get("consolidation_disposition") not in MSC_SOURCE_DISPOSITIONS:
            fail(f"msc_source_item {r.get('source_id')} unknown disposition {r.get('consolidation_disposition')!r}", errors)
        if not r.get("msc_units"):
            fail(f"msc_source_item {r.get('source_id')} unaccounted (no msc_units)", errors)
    if cls != MSC_SOURCE_CLASS_COUNTS:
        fail(f"msc_source_item class counts {cls} != {MSC_SOURCE_CLASS_COUNTS}", errors)
    summ = one("msc_source_summary")
    if summ:
        for k, v in (("total_source_security_items", 90), ("accounted_for", 90),
                     ("unaccounted", 0), ("duplicate_source_ids", 0), ("unknown_disposition", 0)):
            if summ.get(k) != v:
                fail(f"msc_source_summary {k}={summ.get(k)!r}, expected {v}", errors)
        if summ.get("by_class") != MSC_SOURCE_CLASS_COUNTS:
            fail("msc_source_summary by_class mismatch", errors)
    if src_items and cls == MSC_SOURCE_CLASS_COUNTS:
        print("  OK   90/90 source items accounted (18 roots / 23 candidates / 15 chains / 6 gaps / 10 arch / 16 historical / 2 governance)")

    # --- 44 MSC units ---------------------------------------------------------
    units = {r.get("msc_unit_id"): r for r in by_type.get("msc_unit") or []}
    if set(units) != MSC_UNIT_IDS:
        fail(f"msc_unit set must be exactly MSC_UNIT_001..044; missing {sorted(MSC_UNIT_IDS - set(units))}, extra {sorted(set(units) - MSC_UNIT_IDS)}", errors)
    else:
        print("  OK   44 MSC units MSC_UNIT_001..044 present")
    # Secondary-layer identifiers legitimately referenced by unit source_ids:
    # audit-local candidate IDs (Audit-001 CS-*, Audit-002 C-*), folded
    # sub-items (CS-102, CS-103), and the UNWIRED-001 reachability note.
    a1_locals = {r.get("audit_local_id") for r in recs if r.get("record_type") == "audit001_candidate"}
    a2_locals = {r.get("audit_local_id") for r in recs if r.get("record_type") == "audit002_candidate"}
    a1_cand = {r.get("candidate_id") for r in recs if r.get("record_type") == "audit001_candidate"}
    a2_cand = {r.get("candidate_id") for r in recs if r.get("record_type") == "audit002_candidate"}
    secondary_ids = {x for x in (a1_locals | a2_locals | a1_cand | a2_cand) if x}
    secondary_ids |= {"CS-102", "CS-103", "UNWIRED-001"}
    sid_set = set(sids) | secondary_ids
    open_units = [u for u in units.values() if u.get("proposed_disposition") == MSC_OPEN_STATUS]
    rej_units = [u for u in units.values() if u.get("proposed_disposition") == MSC_REJECTED_STATUS]
    if len(open_units) != 42:
        fail(f"OPEN_PENDING_REMEDIATION_COVERAGE_GATE units must be 42, found {len(open_units)}", errors)
    if {u.get("msc_unit_id") for u in rej_units} != MSC_REJECTED_UNITS:
        fail(f"rejected units must be exactly {sorted(MSC_REJECTED_UNITS)}, found {sorted(u.get('msc_unit_id') for u in rej_units)}", errors)
    if len(open_units) == 42 and {u.get("msc_unit_id") for u in rej_units} == MSC_REJECTED_UNITS:
        print("  OK   42 OPEN + 2 REJECTED (MSC_UNIT_043/044) unit dispositions")
    for u in units.values():
        uid = u.get("msc_unit_id")
        for f_ in MSC_UNIT_REQUIRED_FIELDS:
            if f_ not in u:
                fail(f"{uid} missing required field {f_}", errors)
        for sid in u.get("source_ids") or []:
            if sid not in sid_set:
                fail(f"{uid} references unknown source_id {sid!r}", errors)
        if u.get("proposed_disposition") == MSC_OPEN_STATUS:
            if not u.get("provisional_session"):
                fail(f"{uid} OPEN but missing provisional_session", errors)
            if not u.get("independent_retest_owners"):
                fail(f"{uid} OPEN but missing independent_retest_owners", errors)
            if not (u.get("required_automated_tests") or u.get("required_instrumented_tests") or u.get("required_physical_tests")):
                fail(f"{uid} OPEN but has no required test plan", errors)
            if not u.get("closure_evidence"):
                fail(f"{uid} OPEN but missing closure_evidence", errors)
            if not u.get("activation_gate") or not u.get("pre_b004_or_later"):
                fail(f"{uid} OPEN but missing gate assignment", errors)
    for u in rej_units:
        if u.get("proposed_consolidated_severity") not in ("NONE", "INFO"):
            fail(f"{u.get('msc_unit_id')} rejected unit carries severity {u.get('proposed_consolidated_severity')!r}", errors)
    # rejected unit bindings
    u43 = units.get("MSC_UNIT_043") or {}
    if set(u43.get("source_ids") or []) != {"ROOT-016", "CS-016"}:
        fail("MSC_UNIT_043 must bind ROOT-016 + CS-016", errors)
    if "DO_NOT_REVIVE" not in str(u43.get("closure_evidence")) and "REMAINS REJECTED" not in str(u43.get("closure_evidence")):
        fail("MSC_UNIT_043 must carry the DO-NOT-REVIVE disposition note", errors)
    u44 = units.get("MSC_UNIT_044") or {}
    if set(u44.get("source_ids") or []) != {"ANOX-BUILDSC-CANDIDATE-012", "CS-019"}:
        fail("MSC_UNIT_044 must bind ANOX-BUILDSC-CANDIDATE-012 + CS-019", errors)
    # severity distribution
    sev = one("msc_severity_distribution")
    if sev:
        if sev.get("distribution") != MSC_SEVERITY_DISTRIBUTION:
            fail(f"msc_severity_distribution {sev.get('distribution')} != {MSC_SEVERITY_DISTRIBUTION}", errors)
        if sev.get("total") != 44 or sev.get("open") != 42:
            fail("msc_severity_distribution total/open wrong", errors)
        ov = sev.get("overlays") or {}
        if ov.get("MSC_UNIT_001") != "EVIDENCE_INTEGRITY CRITICAL":
            fail("MSC_UNIT_001 EVIDENCE_INTEGRITY CRITICAL overlay missing", errors)
        if "CONDITIONAL_CRITICAL" not in str(ov.get("ATTACKCHAIN_AC_003", "")):
            fail("AC-003 conditional-critical overlay missing", errors)
        print("  OK   severity distribution 0C/7H/16M/6L/4I-META/9CONTRACT/2R preserved")

    # --- arbitrations ----------------------------------------------------------
    rarb = one("msc_root_arbitration")
    if rarb:
        roots = rarb.get("roots") or {}
        if set(roots) != MSC_ROOT_IDS:
            fail(f"msc_root_arbitration must cover ROOT-001..018; got {sorted(roots)}", errors)
        r13 = roots.get("ROOT-013") or {}
        if "SEVERITY_CHANGE_PROPOSED" not in str(r13.get("severity")) or r13.get("status") != "PROPOSED_NOT_YET_CANONICALLY_MUTATED":
            fail("ROOT-013 must record SEVERITY_CHANGE_PROPOSED LOW->MEDIUM, PROPOSED_NOT_YET_CANONICALLY_MUTATED", errors)
        r16 = roots.get("ROOT-016") or {}
        if r16.get("verdict") != "REJECTED_REMAINS_REJECTED" or r16.get("status") != "DO_NOT_REVIVE":
            fail("ROOT-016 must remain REJECTED / DO_NOT_REVIVE", errors)
        r17 = roots.get("ROOT-017") or {}
        if r17.get("classification") != "SECURITY_EVIDENCE_GAP" or r17.get("gate") != "PRE_B004_PRECONDITION":
            fail("ROOT-017 must be classified SECURITY_EVIDENCE_GAP / PRE_B004_PRECONDITION", errors)
        splits = {rid for rid, rr in roots.items() if rr.get("verdict") == "SPLIT_REQUIRED"}
        if splits != MSC_SPLIT_ROOTS:
            fail(f"split roots must be {sorted(MSC_SPLIT_ROOTS)}; got {sorted(splits)}", errors)
        else:
            print("  OK   ROOT-001..018 arbitrations preserved (013 proposed, 016 rejected, 017 classified, 4 splits)")
    sarb = one("msc_specialist_candidate_arbitration")
    if sarb:
        cands = sarb.get("candidates") or {}
        if set(cands) != MSC_SPEC_CANDIDATE_IDS:
            fail(f"specialist candidate arbitration must cover 11 candidates; got {sorted(cands)}", errors)
        if not sarb.get("no_permanent_root_ids_allocated"):
            fail("no_permanent_root_ids_allocated must be true", errors)
    garb = one("msc_gap_arbitration")
    if garb:
        gaps = garb.get("gaps") or {}
        if set(gaps) != MSC_GAP_IDS:
            fail(f"gap arbitration must cover 6 gaps; got {sorted(gaps)}", errors)
        for gid, g in gaps.items():
            if g.get("verdict") != "KEEP_DISTINCT_CONTRACT_UNIT":
                fail(f"{gid} must remain KEEP_DISTINCT_CONTRACT_UNIT", errors)
        print("  OK   11 specialist candidates + 6 architecture gap arbitrations preserved")
    har = one("msc_historical_remediation_arbitration")
    if har:
        rows = har.get("rows") or []
        if len(rows) < 19:
            fail(f"historical remediation arbitration must cover >=19 rows; got {len(rows)}", errors)
        by_fid = {r.get("finding_id"): r for r in rows}
        if (by_fid.get("ANOX-LEGACY-CRYPTO-005") or {}).get("original_status") != "Closed":
            fail("historical arbitration must preserve ANOX-LEGACY-CRYPTO-005 original Closed status", errors)
        if "INEFFECTIVE" not in str((by_fid.get("ANOX-LEGACY-CRYPTO-005") or {}).get("interpretation", "")):
            fail("ANOX-LEGACY-CRYPTO-005 ineffective-remediation interpretation missing", errors)
        if (by_fid.get("ANOX-MAINARCH-031") or {}).get("interpretation", "").find("FALSE_CLOSURE") < 0:
            fail("ANOX-MAINARCH-031 FALSE_CLOSURE interpretation missing", errors)

    # --- FCP / chains / breakers / DAG / sessions --------------------------------
    fcp = one("msc_false_closure_rules")
    if fcp:
        if set((fcp.get("rules") or {}).keys()) != MSC_FCP_IDS:
            fail(f"FCP rules must be exactly FCP_1..8; got {sorted((fcp.get('rules') or {}).keys())}", errors)
        else:
            print("  OK   FCP_1..FCP_8 false-closure rules preserved")
    acm = one("msc_attackchain_mapping")
    if acm:
        chains = acm.get("chains") or {}
        if set(chains) != MSC_CHAIN_IDS:
            fail(f"attackchain mapping must cover 15 chains; got {sorted(chains)}", errors)
        for cid, ch in chains.items():
            if not ch.get("msc_units"):
                fail(f"{cid} has no owning msc_units", errors)
            for m in ch.get("msc_units") or []:
                if m not in units:
                    fail(f"{cid} references unknown unit {m}", errors)
        ov = acm.get("ac003_conditional_overlay") or {}
        if ov.get("canonical_chain_severity") != "HIGH" or "CONDITIONAL_CRITICAL" not in str(ov.get("overlay", "")):
            fail("AC-003 overlay must keep canonical HIGH + conditional-critical overlay", errors)
        hc = set((acm.get("high_chain_challenge") or {}).keys())
        if hc != {"ATTACKCHAIN_AC_001", "ATTACKCHAIN_AC_003", "ATTACKCHAIN_AC_006", "ATTACKCHAIN_AC_012"}:
            fail(f"high-chain challenge set wrong: {sorted(hc)}", errors)
        else:
            print("  OK   15/15 attackchains mapped; 4 high-chain challenges preserved; AC-003 overlay intact")
    sb = one("msc_server_breakers")
    if sb:
        items = {i.get("id"): i for i in sb.get("items") or []}
        if set(items) != MSC_SERVER_BREAKER_IDS or sb.get("total") != 18:
            fail(f"server breakers must be S1..S18 (total 18); got {sorted(items)}", errors)
        for bid, it in items.items():
            if not it.get("msc_units"):
                fail(f"{bid} unassigned (no msc_units)", errors)
        if sb.get("unassigned") != 0:
            fail("server_breakers unassigned must be 0", errors)
        else:
            print("  OK   SERVER_BREAKER_S1..S18 all assigned")
    cb = one("msc_client_breakers")
    if cb:
        items = {i.get("id"): i for i in cb.get("items") or []}
        if set(items) != MSC_CLIENT_BREAKER_IDS or cb.get("total") != 14:
            fail(f"client breakers must be C1..C14 (total 14); got {sorted(items)}", errors)
        for bid, it in items.items():
            if not it.get("msc_units"):
                fail(f"{bid} unassigned (no msc_units)", errors)
        if cb.get("unassigned") != 0:
            fail("client_breakers unassigned must be 0", errors)
        else:
            print("  OK   CLIENT_BREAKER_C1..C14 all assigned")
    if not one("msc_cross_group_dependencies"):
        pass
    dag = one("msc_dependency_dag")
    if dag:
        if dag.get("unresolved_dependency_cycles") != 0:
            fail("msc_dependency_dag unresolved_dependency_cycles must be 0", errors)
        if not dag.get("edges"):
            fail("msc_dependency_dag has no edges", errors)
        else:
            print("  OK   dependency DAG preserved; unresolved cycles = 0")
    sess = one("msc_remediation_sessions")
    if sess:
        if set((sess.get("sessions") or {}).keys()) != MSC_SESSION_IDS:
            fail(f"remediation sessions must be S0..S10; got {sorted((sess.get('sessions') or {}).keys())}", errors)
        else:
            print("  OK   REMEDIATION_SESSION_S0..S10 provisional sessions preserved")
    if not one("msc_remediation_order"):
        pass

    # --- Pre-B004 set, DoD, later gates ------------------------------------------
    pre = one("msc_pre_b004_set")
    if pre:
        cats = pre.get("categories") or {}
        if set(cats.keys()) != set(MSC_PRE_B004_CATEGORIES):
            fail(f"pre_b004_set categories wrong: {sorted(cats.keys())}", errors)
        if not cats.get("A_ARCHITECTURE_CONTRACT") or not cats.get("D_VERIFICATION"):
            fail("pre_b004_set categories must be non-empty", errors)
        else:
            print("  OK   Pre-B004 Master Set (6 categories incl. pull-forward + B004-impl) preserved")
    dod = one("msc_pre_b004_dod")
    if dod:
        if "PROPOSED" not in str(dod.get("status")) or "NOT_EXECUTED" not in str(dod.get("status")):
            fail("pre_b004_dod status must be PROPOSED / NOT_EXECUTED", errors)
        if not dod.get("criteria"):
            fail("pre_b004_dod missing criteria", errors)
    lg = one("msc_later_gates")
    if lg:
        gates = lg.get("gates") or {}
        for g in MSC_LATER_GATES:
            if g not in gates:
                fail(f"later gate {g} missing", errors)
        if lg.get("later_items_without_named_gate") != 0:
            fail("later_items_without_named_gate must be 0", errors)
        else:
            print("  OK   later named gates preserved; later_items_without_named_gate = 0")

    # --- closure standard / state machine / retests ------------------------------
    ce = one("msc_closure_evidence_standard")
    if ce:
        if "CODE_CHANGED_ONLY" not in str(ce.get("rule")):
            fail("closure evidence standard must carry CODE_CHANGED_ONLY != CLOSURE rule", errors)
        if not ce.get("allowed_classes") or not ce.get("minimums"):
            fail("closure evidence standard missing classes/minimums", errors)
    csm = one("msc_closure_state_machine")
    if csm:
        if set(csm.get("stages") or []) != MSC_CSM_STAGES:
            fail(f"closure state machine stages wrong: {csm.get('stages')}", errors)
        else:
            print("  OK   closure evidence standard + 11-stage state machine preserved")
    if not one("msc_independent_retest_matrix"):
        pass
    wcr = one("msc_whole_chain_retests")
    if wcr:
        if set(wcr.get("mandatory") or []) != {"ATTACKCHAIN_AC_001", "ATTACKCHAIN_AC_003", "ATTACKCHAIN_AC_006", "ATTACKCHAIN_AC_012", "ATTACKCHAIN_AC_005", "ATTACKCHAIN_AC_008", "ATTACKCHAIN_AC_010"}:
            fail("whole-chain mandatory retest set wrong", errors)

    # --- physical campaign ---------------------------------------------------------
    phys = one("msc_physical_campaign")
    if phys:
        items = {i.get("id"): i for i in phys.get("items") or []}
        if set(items) != MSC_PHYSICAL_IDS or phys.get("count") != 17:
            fail(f"physical campaign must be PHYSICAL_P1..P17 (count 17); got {sorted(items)}", errors)
        if "NOT_EXECUTED" not in str(phys.get("status", "")):
            fail("physical campaign status must record NOT_EXECUTED", errors)
        else:
            print("  OK   PHYSICAL_P1..P17 campaign preserved, NOT_EXECUTED")

    # --- coverage / contracts / precursor / quality / findings / verdict -----------
    acov = one("msc_architecture_coverage")
    if acov:
        ad = acov.get("auth_deviceauth") or {}
        ast = acov.get("android_storage") or {}
        if ad.get("mapped") != 40 or ad.get("total") != 40 or ad.get("unmapped") != 0:
            fail("architecture coverage auth/deviceauth must be 40/40 unmapped 0", errors)
        if ast.get("mapped") != 42 or ast.get("total") != 42 or ast.get("unmapped") != 0:
            fail("architecture coverage android/storage must be 42/42 unmapped 0", errors)
        if acov.get("architecture_finding_coverage_loss") != 0:
            fail("architecture_finding_coverage_loss must be 0", errors)
    lcov = one("msc_legacy_coverage")
    if lcov:
        if lcov.get("legacy_findings_without_current_owner") != 0:
            fail("legacy_findings_without_current_owner must be 0", errors)
        if not lcov.get("areas"):
            fail("legacy coverage areas missing", errors)
    scc = one("msc_server_contract")
    if scc:
        if {r.get("id") for r in scc.get("rules") or []} != MSC_SERVER_CONTRACT_IDS:
            fail("server contract must contain SC-1..SC-14", errors)
        if "NOT_IMPLEMENTED" not in str(scc.get("status", "")):
            fail("server contract status must record NOT_IMPLEMENTED", errors)
        else:
            print("  OK   consolidated server contract SC-1..14 preserved (NOT_IMPLEMENTED)")
    ccc = one("msc_client_contract")
    if ccc:
        if {r.get("id") for r in ccc.get("rules") or []} != MSC_CLIENT_CONTRACT_IDS:
            fail("client contract must contain CC-1..CC-14", errors)
        else:
            print("  OK   consolidated client contract CC-1..14 preserved")
    pre_fcp = one("msc_fix_coverage_precursor")
    if pre_fcp:
        if pre_fcp.get("open_units") != 42:
            fail("fix coverage precursor open_units must be 42", errors)
        for k in ("unassigned_fix_session", "missing_affected_code", "missing_architecture_owner",
                  "missing_required_test", "missing_retest_owner", "unknown_gate"):
            if pre_fcp.get(k) != 0:
                fail(f"fix coverage precursor {k} must be 0", errors)
        else:
            print("  OK   Master Fix Coverage Precursor: 42/42 open units assigned, all zero fields")
    qg = one("msc_quality_gates")
    if qg:
        gates = qg.get("gates") or {}
        for k in MSC_QUALITY_GATE_ZERO_FIELDS:
            if gates.get(k) != 0:
                fail(f"quality gate {k} must be 0, got {gates.get(k)!r}", errors)
        else:
            print("  OK   all 14 zero-valued quality gates preserved")
    cf = one("msc_consolidation_findings")
    if cf:
        if cf.get("result") != "PASS_WITH_CONSOLIDATION_FINDINGS":
            fail("consolidation result must be PASS_WITH_CONSOLIDATION_FINDINGS", errors)
        if len(cf.get("reasons") or []) != 7:
            fail("consolidation findings must record the 7 reasons", errors)
    vd = one("msc_verdict")
    if vd:
        if vd.get("architecture_verdict") != "CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED":
            fail("architecture verdict must be CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED", errors)
        if vd.get("sec_c_required") != "NO":
            fail("sec_c_required must be NO", errors)
        if not vd.get("sec_c_escalation"):
            fail("sec_c_escalation condition must be preserved", errors)

    # --- source_status for the consolidation artifact -----------------------------
    ss = next((r for r in recs if r.get("record_type") == "source_status" and r.get("audit_id") == MSC_ID), None)
    if not ss or ss.get("source_present") != "YES":
        fail(f"source_status record for {MSC_ID} missing or not YES", errors)
    # next_gate for the coverage gate (checked again here for the master layer)
    ng = next((r for r in recs if r.get("record_type") == "next_gate" and r.get("gate") == NEXT_GATE_ID), None)
    if not ng or "NOT_EXECUTED" not in str(ng.get("status", "")):
        fail(f"next_gate {NEXT_GATE_ID} must be CANDIDATE / NOT_EXECUTED", errors)


def _dag_has_cycle(edges):
    """Return True if the edge list [(a, b), ...] contains a directed cycle."""
    adj = {}
    nodes = set()
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        nodes.add(a)
        nodes.add(b)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}

    def visit(n):
        color[n] = GRAY
        for m in adj.get(n, []):
            if color.get(m, WHITE) == GRAY:
                return True
            if color.get(m, WHITE) == WHITE and visit(m):
                return True
        color[n] = BLACK
        return False

    return any(visit(n) for n in nodes if color[n] == WHITE)


def validate_coverage_gate(errors):
    """Fail-closed verification of the preserved SECURITY-REMEDIATION-COVERAGE-GATE-001
    evidence layer (artifact_type SECURITY_REMEDIATION_COVERAGE_GATE)."""
    recs = load_jsonl(EVIDENCE_DIR / "audit_traceability.jsonl")
    gate = [r for r in recs if r.get("source_artifact_id") == GATE_ID]
    by_type = {}
    for r in gate:
        by_type.setdefault(r.get("record_type"), []).append(r)

    def one(rt):
        rows = by_type.get(rt) or []
        if len(rows) != 1:
            fail(f"expected exactly 1 {rt} record for {GATE_ID}, found {len(rows)}", errors)
            return {}
        return rows[0]

    # --- registry artifact record --------------------------------------------
    audits = {a.get("audit_id"): a for a in load_jsonl(EVIDENCE_DIR / "audit_registry.jsonl")}
    reg = audits.get(GATE_ID)
    if not reg:
        fail(f"{GATE_ID} registry record missing", errors)
    else:
        reg_expected = {
            "artifact_type": "SECURITY_REMEDIATION_COVERAGE_GATE",
            "base_sha": GATE_BASE_SHA,
            "audited_sha": GATE_BASE_SHA,
            "requested_start_sha": GATE_BASE_SHA,
            "mode": "READ_ONLY_SECURITY_REMEDIATION_COVERAGE_GATE",
            "result": "PASS",
            "coverage_verdict": "COVERAGE_PROVEN_100_PERCENT",
            "actual_model": "Claude Fable 5.1 High",
            "requested_model": "Claude Fable 5.1 High",
            "model_requirement_status": "SATISFIED",
            "repository_modified_by_audit": "NO",
            "remote_mutation_by_audit": "NONE",
            "status": "PRESERVED",
            "preserved_at_event": LEDGER_EVENT,
            "delivery_branch": DELIVERY_BRANCH,
            "report_path": EXPECTED_REPORTS[GATE_ID]["path"],
            "report_sha256": EXPECTED_REPORTS[GATE_ID]["sha256"],
            "report_bytes": GATE_REPORT_BYTES,
            "master_units": 44, "open_units": 42, "rejected_units": 2,
            "open_units_covered": 42, "open_units_uncovered": 0, "open_units_unknown": 0,
            "coverage_percent": 100, "source_items": 90, "source_items_accounted": 90,
            "attackchains": 15, "attackchains_without_msc_unit": 0,
            "server_breakers": 18, "server_breakers_unassigned": 0,
            "client_breakers": 14, "client_breakers_unassigned": 0,
            "parallel_writer_collisions": 0, "dependency_cycles": 0,
            "pre_b004_dod_unowned": 0, "silent_dropped": 0, "unresolved_ids": 0,
            "security_remediation_authorized": "NO",
            "security_remediation": "NOT_STARTED",
            "task_id": TASK_ID,
        }
        for key, expected in reg_expected.items():
            if reg.get(key) != expected:
                fail(f"{GATE_ID} registry {key}={reg.get(key)!r}, expected {expected!r}", errors)
        if "does NOT authorize" not in str(reg.get("notes", "")):
            fail(f"{GATE_ID} registry must record that PASS grants no remediation authorization", errors)
        if not errors or all(GATE_ID not in e for e in errors):
            print(f"  OK   {GATE_ID} registry artifact record verified")

    # --- report file identity --------------------------------------------------
    rp = REPO_ROOT / EXPECTED_REPORTS[GATE_ID]["path"]
    if rp.exists():
        body = rp.read_text(encoding="utf-8")
        if not body.startswith("# SECURITY-REMEDIATION-COVERAGE-GATE-001 — FINAL REPORT"):
            fail(f"{GATE_ID} report missing required opening marker", errors)
        if not body.rstrip().endswith("`SECURITY-REMEDIATION-COVERAGE-GATE-001` — **PASS**. STOP."):
            fail(f"{GATE_ID} report missing required closing marker", errors)
        for marker in ("## GATE RESULT", "**PASS**",
                       "READ_ONLY_SECURITY_REMEDIATION_COVERAGE_GATE",
                       "610ed08337536857db73259168498c49b786caa1",
                       "REPOSITORY MODIFIED: NO", "REMOTE MUTATION: NONE",
                       "WORKING TREE CLEAN",
                       "Claude Fable 5.1 High", "MODEL REQUIREMENT SATISFIED: YES"):
            if marker not in body:
                fail(f"{GATE_ID} report missing required identity marker {marker!r}", errors)
        if len(rp.read_bytes()) != GATE_REPORT_BYTES:
            fail(f"{GATE_ID} report byte count must be {GATE_REPORT_BYTES}", errors)

    # --- ambiguous machine-id hygiene ------------------------------------------
    def _scan_ambiguous(obj, where):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(k, str) and GATE_AMBIGUOUS_KEY_RE.match(k):
                    fail(f"{GATE_ID} {where}: ambiguous machine id key {k!r}", errors)
                _scan_ambiguous(v, where)
        elif isinstance(obj, list):
            for v in obj:
                _scan_ambiguous(v, where)

    for r in gate:
        _scan_ambiguous(r, r.get("record_type"))

    # --- 42-row coverage matrix --------------------------------------------------
    rows = by_type.get("gate_coverage_unit") or []
    by_id = {r.get("msc_unit"): r for r in rows}
    if set(by_id) != GATE_OPEN_UNIT_IDS:
        fail(f"gate_coverage_unit set must be exactly MSC_UNIT_001..042; missing {sorted(GATE_OPEN_UNIT_IDS - set(by_id))}, extra {sorted(set(by_id) - GATE_OPEN_UNIT_IDS)}", errors)
    elif len(rows) != 42:
        fail(f"gate_coverage_unit must contain exactly 42 unique rows, found {len(rows)}", errors)
    else:
        print("  OK   42/42 gate coverage rows present (MSC_UNIT_001..042)")
    rejected_rows = [r for r in rows if r.get("msc_unit") in GATE_REJECTED_UNITS]
    if rejected_rows:
        fail(f"rejected units must not carry gate coverage rows: {[r.get('msc_unit') for r in rejected_rows]}", errors)
    for uid, r in by_id.items():
        for f_ in GATE_ROW_REQUIRED_FIELDS:
            if f_ not in r:
                fail(f"gate_coverage_unit {uid} missing field {f_}", errors)
        if r.get("coverage_status") != "COVERED":
            fail(f"gate_coverage_unit {uid} coverage_status {r.get('coverage_status')!r} != COVERED", errors)
        if r.get("primary_execution_owner") != GATE_PRIMARY.get(uid):
            fail(f"gate_coverage_unit {uid} primary_execution_owner {r.get('primary_execution_owner')!r} != {GATE_PRIMARY.get(uid)!r}", errors)
        if r.get("primary_execution_owner") not in GATE_ALLOWED_OWNERS:
            fail(f"gate_coverage_unit {uid} primary owner {r.get('primary_execution_owner')!r} outside allowed owner namespace", errors)
        if r.get("gate") not in GATE_ALLOWED_GATES:
            fail(f"gate_coverage_unit {uid} gate {r.get('gate')!r} is not a named gate", errors)
        if r.get("gate") in ("LATER", "UNKNOWN", ""):
            fail(f"gate_coverage_unit {uid} carries a generic/unknown gate", errors)
        if not r.get("independent_retest_owner"):
            fail(f"gate_coverage_unit {uid} missing independent retest owner", errors)
        for tf in ("instrumented_requirement", "synthetic_backend_requirement",
                   "physical_requirement", "provenance_requirement", "attackchain_retest"):
            if not r.get(tf):
                fail(f"gate_coverage_unit {uid} missing {tf}", errors)
        for st in ("closure_runtime_stage", "closure_chain_stage", "closure_physical_stage"):
            if r.get(st) not in ("REQUIRED", "NOT_APPLICABLE"):
                fail(f"gate_coverage_unit {uid} {st}={r.get(st)!r} not in REQUIRED/NOT_APPLICABLE", errors)

    # --- verdict + zero metrics ---------------------------------------------------
    v = one("gate_verdict")
    if v:
        for k, exp in (("result", "PASS"), ("coverage_verdict", "COVERAGE_PROVEN_100_PERCENT"),
                       ("base_sha", GATE_BASE_SHA), ("head_at_end", GATE_BASE_SHA),
                       ("origin_main", GATE_BASE_SHA), ("working_tree", "CLEAN"),
                       ("repository_modified", "NO"), ("remote_mutation", "NONE"),
                       ("model", "Claude Fable 5.1 High"), ("model_requirement_satisfied", "YES"),
                       ("mode", "READ_ONLY_SECURITY_REMEDIATION_COVERAGE_GATE"),
                       ("total_master_units", 44), ("open_msc_units", 42),
                       ("rejected_units", 2), ("open_msc_covered", 42),
                       ("open_msc_uncovered", 0), ("unknown", 0),
                       ("coverage_percent", 100), ("counting_ambiguity", "NONE"),
                       ("dependency_cycles", 0), ("rejected_with_remediation_session", 0),
                       ("rejected_with_traceability", 2),
                       ("security_remediation_authorized", "NO")):
            if v.get(k) != exp:
                fail(f"gate_verdict {k}={v.get(k)!r}, expected {exp!r}", errors)
        rr = v.get("rejected_records") or {}
        if set(rr) != GATE_REJECTED_UNITS:
            fail(f"gate_verdict rejected_records must be exactly {sorted(GATE_REJECTED_UNITS)}", errors)
        else:
            for uid, e in rr.items():
                if e.get("disposition") != "REJECTED_NOT_A_FINDING":
                    fail(f"gate_verdict {uid} disposition {e.get('disposition')!r} != REJECTED_NOT_A_FINDING", errors)
                if e.get("remediation_required") != "NO" or e.get("closure_work") != "NO" or e.get("traceability") != "YES":
                    fail(f"gate_verdict {uid} must record remediation NO / closure NO / traceability YES", errors)
            if rr.get("MSC_UNIT_043", {}).get("source") != "ROOT-016":
                fail("gate_verdict MSC_UNIT_043 must be bound to ROOT-016", errors)
            if "BUILDSC-012" not in str(rr.get("MSC_UNIT_044", {}).get("source", "")):
                fail("gate_verdict MSC_UNIT_044 must be bound to BUILDSC-012", errors)
    zm = one("gate_zero_metrics")
    if zm:
        for f_ in GATE_ZERO_METRIC_FIELDS:
            if zm.get(f_) != 0:
                fail(f"gate_zero_metrics {f_}={zm.get(f_)!r}, expected 0", errors)
        print("  OK   gate zero metrics all 0")

    # --- severity + category + later-gate coverage --------------------------------
    sev = one("gate_severity_coverage")
    if sev:
        exp = {"HIGH": 7, "MEDIUM": 16, "LOW": 6, "INFO_META": 4, "CONTRACT": 9}
        cov = sev.get("coverage") or {}
        for bucket, n in exp.items():
            c = cov.get(bucket) or {}
            if c.get("count") != n or c.get("covered") != n or c.get("uncovered") != 0:
                fail(f"gate_severity_coverage {bucket}={c}, expected {n}/{n}/0", errors)
        if sev.get("rejected") != 2 or sev.get("uncovered_by_severity") != 0:
            fail("gate_severity_coverage rejected/uncovered mutated", errors)
    cat = one("gate_pre_b004_category_coverage")
    if cat:
        exp = {"A_ARCHITECTURE_CONTRACT": 11, "B_BUILD_PROVENANCE": 4, "C_CODE_REMEDIATION": 17,
               "C_RECOMMENDED_PULL_FORWARD": 4, "D_VERIFICATION": 5, "E_B004_IMPLEMENTATION_TIME": 9}
        cats = cat.get("categories") or {}
        if set(cats) != set(exp):
            fail(f"gate_pre_b004_category_coverage categories {sorted(cats)} != {sorted(exp)}", errors)
        for k, n in exp.items():
            c = cats.get(k) or {}
            if c.get("count") != n or c.get("covered") != n or len(c.get("units") or []) != n:
                fail(f"gate_pre_b004_category_coverage {k}={c.get('count')}/{c.get('covered')}, expected {n}/{n}", errors)
        if cat.get("items_without_category") != 0:
            fail("gate_pre_b004_category_coverage items_without_category != 0", errors)
        if "NOT_EXECUTED" not in str(cat.get("dod_status", "")):
            fail("gate_pre_b004_category_coverage DoD must remain PROPOSED / NOT_EXECUTED", errors)
    lg = one("gate_later_gate_coverage")
    if lg:
        exp = {"B006": 4, "B008_B009": 3, "B012": 1, "B013": 4, "RELEASE_CANDIDATE": 2,
               "PHYSICAL_GRAPHENEOS_FINAL": 4, "FINAL_PRODUCT_GATE_OPERATIONAL_ACCEPTANCE": 6,
               "HUMAN_DECISION_PRE_REMEDIATION": 1}
        gates = lg.get("gates") or {}
        if set(gates) != set(exp):
            fail(f"gate_later_gate_coverage gates {sorted(gates)} != {sorted(exp)}", errors)
        for k, n in exp.items():
            c = gates.get(k) or {}
            if c.get("count") != n or c.get("covered") != n or len(c.get("units") or []) != n:
                fail(f"gate_later_gate_coverage {k}={c.get('count')}/{c.get('covered')}, expected {n}/{n}", errors)
        for k in ("unnamed_later_items", "unknown_gates", "generic_later_gates"):
            if lg.get(k) != 0:
                fail(f"gate_later_gate_coverage {k} != 0", errors)

    # --- execution sessions S0..S10 -------------------------------------------------
    sess = one("gate_execution_sessions")
    if sess:
        s = sess.get("sessions") or {}
        if set(s) != GATE_SESSION_IDS:
            fail(f"gate_execution_sessions keys must be exactly S0..S10; got {sorted(s)}", errors)
        else:
            print("  OK   REMEDIATION_SESSION_S0..S10 boundaries preserved (11/11)")
        for sid, spec in s.items():
            for f_ in ("role", "in_scope", "out_of_scope", "base_sha_requirement",
                       "prerequisite_events", "files_owned", "files_forbidden",
                       "tests_in_session", "independent_retest"):
                if f_ not in spec:
                    fail(f"{sid} missing session field {f_}", errors)
            if not spec.get("role") or spec.get("in_scope") is None:
                fail(f"{sid} role/in_scope empty", errors)
        s2 = s.get("REMEDIATION_SESSION_S2") or {}
        order = s2.get("execution_order") or []
        if order:
            if not any("MSC_UNIT_008" in str(x) for x in order[-1:]):
                fail("REMEDIATION_SESSION_S2 must execute MSC_UNIT_008 LAST", errors)
            idx5 = [i for i, x in enumerate(order) if "MSC_UNIT_005" in str(x)]
            idx8 = [i for i, x in enumerate(order) if "MSC_UNIT_008" in str(x)]
            if idx5 and idx8 and idx5[0] > idx8[0]:
                fail("REMEDIATION_SESSION_S2 must order MSC_UNIT_005 before MSC_UNIT_008", errors)
        else:
            fail("REMEDIATION_SESSION_S2 missing execution_order", errors)
        s3 = s.get("REMEDIATION_SESSION_S3") or {}
        if not any("CryptoBridge" in str(x) for x in (s3.get("files_forbidden") or [])):
            fail("REMEDIATION_SESSION_S3 files_forbidden must exclude CryptoBridge.kt (S2-owned)", errors)

    # --- file ownership + parallel execution -----------------------------------------
    fo = one("gate_file_ownership")
    if fo:
        if fo.get("unresolved_parallel_writer_collisions") != 0:
            fail("gate_file_ownership unresolved_parallel_writer_collisions != 0", errors)
        entries = {e.get("file"): e for e in fo.get("entries") or []}
        expected_res = {
            "CryptoBridge.kt": "S2",
            "RegistrationOrchestrator.kt": "S3",
            "FileRegistrationSessionStore.kt": "S3",
            ".github/workflows/ci.yml / build.gradle.kts": "S1",
        }
        for f_, token in expected_res.items():
            e = entries.get(f_)
            if not e or token not in str(e.get("resolution", "")):
                fail(f"file ownership for {f_} missing or resolution lacks {token}", errors)
            elif e and not str(e.get("collision", "")).startswith("RESOLVED"):
                fail(f"file ownership for {f_} collision not RESOLVED_*", errors)
        if len(entries) < 10:
            fail("gate_file_ownership matrix incomplete (<10 entries)", errors)
    px = one("gate_parallel_execution")
    if px:
        safe = {tuple(p) for p in px.get("safe_pairs") or []}
        if ("REMEDIATION_SESSION_S0", "REMEDIATION_SESSION_S1") not in safe:
            fail("parallel execution must record S0||S1 as safe", errors)
        if ("REMEDIATION_SESSION_S2", "REMEDIATION_SESSION_S3") not in safe:
            fail("parallel execution must record S2||S3 as safe", errors)
        unsafe = {tuple(p) for p in px.get("unsafe_pairs") or []}
        if not any(p[0] == "REMEDIATION_SESSION_S3" and "S4" in str(p[1]) for p in unsafe):
            fail("parallel execution must record S3||S4 as unsafe", errors)

    # --- architecture prerequisites + dependency DAG ----------------------------------
    ap = one("gate_architecture_prerequisites")
    if ap:
        if ap.get("prerequisites_without_owner") != 0 or ap.get("count") != 10:
            fail("gate_architecture_prerequisites count/without_owner mutated", errors)
        if not (ap.get("entries") or []):
            fail("gate_architecture_prerequisites entries missing", errors)
    dag = one("gate_dependency_dag")
    if dag:
        if dag.get("unresolved_dependency_cycles") != 0:
            fail("gate_dependency_dag unresolved_dependency_cycles != 0", errors)
        if dag.get("normalized_edge_count") != 81 or dag.get("normalized_node_count") != 53:
            fail("gate_dependency_dag normalized edge/node counts mutated", errors)
        all_edges = [tuple(e) for e in (dag.get("master_edges") or []) + (dag.get("minimum_edges") or [])]
        if len(all_edges) < 70:
            fail("gate_dependency_dag edges missing/truncated", errors)
        if _dag_has_cycle(all_edges):
            fail("gate_dependency_dag contains a directed cycle", errors)
        blob = json.dumps(all_edges)
        for token in ("MSC_UNIT_001", "MSC_UNIT_008", "MSC_UNIT_038", "MSC_UNIT_040", "PHYSICAL"):
            if token not in blob:
                fail(f"gate_dependency_dag edges missing required token {token}", errors)

    # --- FCP enforcement + false-closure scenarios -------------------------------------
    fcp = one("gate_fcp_enforcement")
    if fcp:
        rules = fcp.get("rules") or {}
        if set(rules) != GATE_FCP_IDS:
            fail(f"gate_fcp_enforcement rules must be exactly FCP_1..FCP_8; got {sorted(rules)}", errors)
        for fid, spec in rules.items():
            if not spec.get("enforcing_units") or not spec.get("enforcing_sessions"):
                fail(f"gate_fcp_enforcement {fid} has no enforcing units/sessions", errors)
        if fcp.get("fcp_count") != 8 or fcp.get("fcp_escapes") != 0:
            fail("gate_fcp_enforcement count/escapes mutated", errors)
    fc = one("gate_false_closure_tests")
    if fc:
        sc = fc.get("scenarios") or {}
        if set(sc) != GATE_FALSE_CLOSURE_IDS:
            fail(f"gate_false_closure_tests scenarios must be exactly A..F; got {sorted(sc)}", errors)
        exp_v = {"FALSE_CLOSURE_A": "BLOCKED", "FALSE_CLOSURE_B": "BLOCKED", "FALSE_CLOSURE_C": "BLOCKED",
                 "FALSE_CLOSURE_D": "REMAINS_OPEN", "FALSE_CLOSURE_E": "REMAINS_OPEN", "FALSE_CLOSURE_F": "REMAINS_OPEN"}
        for sid, verdict in exp_v.items():
            if (sc.get(sid) or {}).get("verdict") != verdict:
                fail(f"gate_false_closure_tests {sid} verdict must be {verdict}", errors)
        if fc.get("escapes") != 0:
            fail("gate_false_closure_tests escapes != 0", errors)

    # --- contract coverage --------------------------------------------------------------
    scc = one("gate_server_contract_coverage")
    if scc:
        rules = scc.get("rules") or {}
        if set(rules) != GATE_SC_IDS:
            fail(f"gate_server_contract_coverage rules must be exactly SERVER_CONTRACT_SC_1..SC_14; got {sorted(rules)}", errors)
        for rid, spec in rules.items():
            if not spec.get("covered_units") or not spec.get("conformance_test") or not spec.get("independent_retest"):
                fail(f"gate_server_contract_coverage {rid} incomplete coverage", errors)
        if scc.get("covered") != 14 or scc.get("uncovered") != 0:
            fail("gate_server_contract_coverage must be 14/14 with uncovered=0", errors)
    ccc = one("gate_client_contract_coverage")
    if ccc:
        rules = ccc.get("rules") or {}
        if set(rules) != GATE_CC_IDS:
            fail(f"gate_client_contract_coverage rules must be exactly CLIENT_CONTRACT_CC_1..CC_14; got {sorted(rules)}", errors)
        for rid, spec in rules.items():
            if not spec.get("covered_units") or not spec.get("conformance_test") or not spec.get("independent_retest"):
                fail(f"gate_client_contract_coverage {rid} incomplete coverage", errors)
        if ccc.get("covered") != 14 or ccc.get("uncovered") != 0:
            fail("gate_client_contract_coverage must be 14/14 with uncovered=0", errors)

    # --- attackchain coverage -------------------------------------------------------------
    ac = one("gate_attackchain_coverage")
    if ac:
        chains = ac.get("chains") or {}
        if set(chains) != GATE_CHAIN_IDS:
            fail(f"gate_attackchain_coverage chains must be exactly ATTACKCHAIN_AC_001..015; got {sorted(chains)}", errors)
        for cid, spec in chains.items():
            if not spec.get("mapped_to_msc") or not spec.get("breakpoints") or not spec.get("retest_owner") or not spec.get("gate"):
                fail(f"gate_attackchain_coverage {cid} incomplete mapping", errors)
        if ac.get("mapped_to_msc") != 15 or ac.get("chains_without_msc_unit") != []:
            fail("gate_attackchain_coverage must map 15/15 chains with none unmapped", errors)
        if set(ac.get("mandatory_whole_chain_retests") or []) != GATE_MANDATORY_CHAIN_RETESTS:
            fail("gate_attackchain_coverage mandatory whole-chain retest set mutated", errors)
        ov = ac.get("ac003_conditional_overlay") or {}
        if ov.get("canonical_chain_severity") != "HIGH":
            fail("gate_attackchain_coverage AC-003 canonical severity must remain HIGH", errors)
        if "CONDITIONAL_CRITICAL" not in str(ov.get("overlay", "")):
            fail("gate_attackchain_coverage AC-003 conditional-critical overlay must be preserved", errors)
        if ov.get("mandatory_ath_alone_does_not_close") is not True:
            fail("gate_attackchain_coverage must preserve that mandatory ath alone does not close AC-003", errors)

    # --- physical coverage -------------------------------------------------------------------
    pc = one("gate_physical_coverage")
    if pc:
        items = {i.get("id"): i for i in pc.get("items") or []}
        if set(items) != GATE_PHYSICAL_IDS:
            fail(f"gate_physical_coverage items must be exactly PHYSICAL_P1..P17; got {sorted(items)}", errors)
        for pid, it in items.items():
            if not it.get("mapped_units"):
                fail(f"gate_physical_coverage {pid} unmapped", errors)
            if "NOT_EXECUTED" in str(it.get("coverage_status", "")):
                pass
            if "COVERED" not in str(it.get("coverage_status", "")):
                fail(f"gate_physical_coverage {pid} coverage_status must record COVERED (mapped)", errors)
        if pc.get("count") != 17 or pc.get("assigned") != 17 or pc.get("unassigned") != 0:
            fail("gate_physical_coverage must be 17/17 assigned, 0 unassigned", errors)
        if pc.get("executed") != 0 or "NOT_EXECUTED" not in str(pc.get("status", "")):
            fail("gate_physical_coverage must record NOT_EXECUTED with executed=0", errors)
        if "PROVENANCE_VERIFIED_BINARY" not in str(pc.get("prerequisite", "")):
            fail("gate_physical_coverage prerequisite must require a provenance-verified binary", errors)

    # --- retest coverage + DoD -------------------------------------------------------------------
    rc = one("gate_retest_coverage")
    if rc:
        if rc.get("open_units") != 42 or rc.get("units_with_independent_retest_owner") != 42 or rc.get("missing_retest_owner") != 0:
            fail("gate_retest_coverage must be 42/42 with missing=0", errors)
        if "never" not in str(rc.get("rule", "")):
            fail("gate_retest_coverage must preserve implementer-not-sole-retest-authority rule", errors)
    dod = one("gate_pre_b004_dod_coverage")
    if dod:
        if "NOT_EXECUTED" not in str(dod.get("status", "")):
            fail("gate_pre_b004_dod_coverage status must remain PROPOSED / NOT_EXECUTED", errors)
        if dod.get("unowned_items") != 0 or dod.get("dod_execution") != "NOT_EXECUTED":
            fail("gate_pre_b004_dod_coverage unowned/execution mutated", errors)
        crit = dod.get("criteria") or []
        if len(crit) != 12 or any(not c.get("criterion") or not c.get("owner") for c in crit):
            fail("gate_pre_b004_dod_coverage must carry all 12 owned criteria", errors)

    # --- human decision packet ----------------------------------------------------------------------
    hd = one("gate_human_decision_packet")
    if hd:
        dec = hd.get("decisions") or {}
        if set(dec) != GATE_HUMAN_DECISION_IDS:
            fail(f"gate_human_decision_packet decisions must be exactly H1/H2/H3/R1; got {sorted(dec)}", errors)
        exp_status = {
            "HUMAN_DECISION_H1": "Pending", "HUMAN_DECISION_H2": "Pending",
            "HUMAN_DECISION_H3": "Pending timing decision", "HUMAN_DECISION_R1": "Pending optional ratification",
        }
        for did, st in exp_status.items():
            d = dec.get(did) or {}
            if d.get("status") != st:
                fail(f"gate_human_decision_packet {did} status {d.get('status')!r}, expected {st!r}", errors)
            for f_ in ("impact", "options", "recommendation", "blocking_effect"):
                if not d.get(f_):
                    fail(f"gate_human_decision_packet {did} missing {f_}", errors)
        for did in ("HUMAN_DECISION_H1", "HUMAN_DECISION_H2"):
            if "block" not in str((dec.get(did) or {}).get("blocking_effect", "")).lower():
                fail(f"{did} must record a blocking effect on remediation start", errors)
        for did in ("HUMAN_DECISION_H3", "HUMAN_DECISION_R1"):
            if "NOT block" not in str((dec.get(did) or {}).get("blocking_effect", "")) and "does NOT block" not in str((dec.get(did) or {}).get("blocking_effect", "")):
                fail(f"{did} must record that it does not block remediation start", errors)
        if hd.get("decided") != 0 or hd.get("auto_accepted") != 0:
            fail("gate_human_decision_packet must record decided=0, auto_accepted=0", errors)

    # --- primary-execution resolutions -----------------------------------------------------------------
    pr = one("gate_primary_execution_resolutions")
    if pr:
        res = pr.get("resolutions") or {}
        exp = {
            "MSC_UNIT_018": ("REMEDIATION_SESSION_S3", "REMEDIATION_SESSION_S5"),
            "MSC_UNIT_029": ("REMEDIATION_SESSION_S3", "REMEDIATION_SESSION_S5"),
            "MSC_UNIT_014": ("REMEDIATION_SESSION_S3", "REMEDIATION_SESSION_S2"),
            "MSC_UNIT_019": ("REMEDIATION_SESSION_S3", "REMEDIATION_SESSION_S2"),
            "MSC_UNIT_027": ("REMEDIATION_SESSION_S4", "REMEDIATION_SESSION_S0"),
            "MSC_UNIT_039": ("HUMAN_GOVERNANCE_DECISION", None),
            "MSC_UNIT_041": ("B012_GATE", None),
        }
        for uid, (prim, alt) in exp.items():
            r = res.get(uid) or {}
            if r.get("primary") != prim:
                fail(f"primary execution resolution {uid} primary={r.get('primary')!r}, expected {prim!r}", errors)
            if alt and alt not in str(json.dumps(r)):
                fail(f"primary execution resolution {uid} must record contingency/secondary {alt}", errors)
        if pr.get("ambiguous_owners") != 0:
            fail("gate_primary_execution_resolutions ambiguous_owners != 0", errors)

    # --- readiness / authorization separation -------------------------------------------------------------
    rd = one("gate_readiness")
    if rd:
        for k, exp in (("coverage_readiness", "READY"),
                       ("security_remediation_start_authorization", "NOT_GRANTED"),
                       ("security_remediation", "NOT_STARTED"),
                       ("b004", "NOT_STARTED"), ("b005", "NOT_STARTED"),
                       ("product", "BLOCKED_PENDING_FINAL_AUDIT"),
                       ("human_final_product_gate", "NOT_EXECUTED")):
            if rd.get(k) != exp:
                fail(f"gate_readiness {k}={rd.get(k)!r}, expected {exp!r}", errors)
        if "HUMAN_PRE_REMEDIATION_DECISIONS_AND_AUTHORIZATION" not in str(rd.get("next_state", "")):
            fail("gate_readiness next_state must be HUMAN_PRE_REMEDIATION_DECISIONS_AND_AUTHORIZATION — PENDING", errors)
        if "READY_AFTER_PRESERVATION_AND_HUMAN_AUTHORIZATION" not in str(rd.get("remediation_start_readiness", "")):
            fail("gate_readiness remediation_start_readiness mutated", errors)

    # --- source status + gate lifecycle pointers ------------------------------------------------------
    ss = next((r for r in recs if r.get("record_type") == "source_status" and r.get("audit_id") == GATE_ID), None)
    if not ss or ss.get("source_present") != "YES":
        fail(f"source_status record for {GATE_ID} missing or not YES", errors)
    elif ss.get("artifact_type") != "SECURITY_REMEDIATION_COVERAGE_GATE":
        fail(f"source_status for {GATE_ID} artifact_type must be SECURITY_REMEDIATION_COVERAGE_GATE", errors)
    elif ss.get("preserved_path") != EXPECTED_REPORTS[GATE_ID]["path"]:
        fail(f"source_status for {GATE_ID} preserved_path mismatch", errors)
    # the gate record's own next_gate pointer
    pg = next((r for r in recs if r.get("record_type") == "next_gate" and r.get("gate") == "SECURITY-REMEDIATION-COVERAGE-GATE"), None)
    if not pg or "EXECUTED_AND_PRESERVED" not in str(pg.get("status", "")):
        fail("next_gate record for SECURITY-REMEDIATION-COVERAGE-GATE must be EXECUTED_AND_PRESERVED", errors)
    hg = next((r for r in recs if r.get("record_type") == "next_gate" and r.get("gate") == NEXT_GATE_ID), None)
    if not hg or "NOT_EXECUTED" not in str(hg.get("status", "")):
        fail(f"next_gate {NEXT_GATE_ID} must be PENDING / NOT_EXECUTED", errors)
    print(f"  OK   {GATE_ID} lifecycle pointers verified (gate preserved; human-decision state pending)")


def validate_findings(errors):
    findings = load_jsonl(REGISTRY_DIR / "findings.jsonl")
    f5 = next((f for f in findings if f.get("finding_id") == "ANOX-LEGACY-CRYPTO-005"), None)
    if f5 is None:
        fail("ANOX-LEGACY-CRYPTO-005 missing from findings.jsonl", errors)
    else:
        if f5.get("status") != "Closed":
            fail(f"ANOX-LEGACY-CRYPTO-005 must remain Closed, got {f5.get('status')!r}", errors)
        if not f5.get("closure_actor") or not f5.get("closure_evidence"):
            fail("ANOX-LEGACY-CRYPTO-005 closure evidence/actor removed", errors)
        if "LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION" not in str(f5.get("notes", "")):
            fail("ANOX-LEGACY-CRYPTO-005 lacks the preserved LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION relationship note", errors)
        if f5.get("status") == "Closed":
            print("  OK   ANOX-LEGACY-CRYPTO-005 remains Closed with preserved relationship")
    i5 = next((f for f in findings if f.get("finding_id") == "ANOX-LEGACY-INTEGRATION-005"), None)
    if i5 is None or i5.get("status") != "Open":
        fail("ANOX-LEGACY-INTEGRATION-005 must remain Open", errors)
    else:
        print("  OK   ANOX-LEGACY-INTEGRATION-005 remains Open")
    for fid in ("ANOX-MAINARCH-013", "ANOX-MAINARCH-018", "ANOX-MAINARCH-030", "ANOX-LEGACY-B003-001"):
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") not in ("Open", "Ready For Retest"):
            fail(f"existing product finding {fid} must remain Open/Ready For Retest", errors)
    for fid, want in (("ANOX-LEGACY-CRYPTO-005", "Closed"), ("ANOX-LEGACY-INTEGRATION-005", "Open"),
                      ("ANOX-MAINARCH-031", "Closed"), ("ANOX-SECURITY-ARCH-001", "Open"),
                      ("ANOX-SECURITY-ARCH-007", "Open"), ("ANOX-SECURITY-ARCH-008", "Open")):
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") != want:
            fail(f"EVENT-0046 finding {fid} must remain {want}, got {(f or {}).get('status')!r}", errors)
        elif "ANOX-EVENT-0046" not in str(f.get("notes", "")):
            fail(f"{fid} lacks the preserved ANOX-EVENT-0046 relationship note", errors)
    for fid, want in (("ANOX-LEGACY-INTEGRATION-001", "Closed"), ("ANOX-LEGACY-INTEGRATION-003", "Closed"),
                      ("ANOX-MAINARCH-019", "Closed"), ("ANOX-MAINARCH-008", "Closed"),
                      ("ANOX-SECURITY-ARCH-006", "Open"), ("ANOX-SECURITY-ARCH-003", "Open"),
                      ("ANOX-SECURITY-ARCH-007", "Open"), ("ANOX-MAINARCH-018", "Open"),
                      ("ANOX-MAINARCH-005", "Closed"), ("ANOX-MAINARCH-014", "Closed")):
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") != want:
            fail(f"EVENT-0047 finding {fid} must remain {want}, got {(f or {}).get('status')!r}", errors)
        elif "ANOX-EVENT-0047" not in str(f.get("notes", "")):
            fail(f"{fid} lacks the preserved ANOX-EVENT-0047 relationship note", errors)
    for fid, want in (("ANOX-SECURITY-ARCH-003", "Open"), ("ANOX-SECURITY-ARCH-007", "Open"),
                      ("ANOX-SECURITY-ARCH-008", "Open"), ("ANOX-SECURITY-ARCH-009", "Open"),
                      ("ANOX-MAINARCH-018", "Open"), ("ANOX-MAINARCH-023", "Closed"),
                      ("ANOX-MAINARCH-030", "Open"), ("ANOX-LEGACY-INTEGRATION-002", "Closed"),
                      ("ANOX-LEGACY-INTEGRATION-003", "Closed"), ("ANOX-LEGACY-ANDROIDSEC-001", "Closed"),
                      ("ANOX-LEGACY-B003-001", "Open")):
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") != want:
            fail(f"EVENT-0048 finding {fid} must remain {want}, got {(f or {}).get('status')!r}", errors)
        elif "ANOX-EVENT-0048" not in str(f.get("notes", "")):
            fail(f"{fid} lacks the preserved ANOX-EVENT-0048 relationship note", errors)
    for fid, want in ATTACKCHAIN_EVENT0049_FINDINGS.items():
        f = next((x for x in findings if x.get("finding_id") == fid), None)
        if f is None or f.get("status") != want:
            fail(f"EVENT-0049 finding {fid} must remain {want}, got {(f or {}).get('status')!r}", errors)
        elif "ANOX-EVENT-0049" not in str(f.get("notes", "")):
            fail(f"{fid} lacks the preserved ANOX-EVENT-0049 relationship note", errors)
    print("  OK   EVENT-0049 participation notes preserved on 18 findings (no status rewrites)")


def validate_lifecycle(errors):
    ws_path = REGISTRY_DIR.parent / "WORKFORCE_STATE.json"
    if not ws_path.exists():
        fail("WORKFORCE_STATE.json missing", errors)
        return
    ws = load_json(ws_path)
    if ws.get("product_development_state") != "BLOCKED_PENDING_FINAL_AUDIT":
        fail("product_development_state must remain BLOCKED_PENDING_FINAL_AUDIT", errors)
    else:
        print("  OK   product remains BLOCKED_PENDING_FINAL_AUDIT")
    ir = load_json(REGISTRY_DIR / "implementation_readiness.json")
    for dom in ("B-004", "B-005"):
        st = ((ir.get("domains") or {}).get(dom) or {}).get("implementation_state")
        if st != "NOT_STARTED":
            fail(f"{dom} implementation_state must remain NOT_STARTED, got {st!r}", errors)
    print("  OK   B-004 and B-005 remain NOT_STARTED")
    nxt = ws.get("next_phase") or (ws.get("final_pre_product_audit") or {}).get("next_phase")
    if nxt != NEXT_GATE_ID:
        fail(f"next_phase must be {NEXT_GATE_ID}, got {nxt!r}", errors)
    else:
        print(f"  OK   next gate {NEXT_GATE_ID} recorded")
    completed = set((ws.get("final_pre_product_audit") or {}).get("completed_audit_ids") or [])
    if NEXT_GATE_ID in completed:
        fail(f"{NEXT_GATE_ID} must not be in completed_audit_ids", errors)
    post = (ws.get("post_merge_state") or {}).get("current_gate", "")
    if NEXT_GATE_ID not in post or "CANDIDATE" not in post.upper() and "Candidate" not in post:
        fail(f"post_merge_state gate must record {NEXT_GATE_ID} as Candidate", errors)
    completed = set((ws.get("final_pre_product_audit") or {}).get("completed_audit_ids") or [])
    if "AUDIT-SECURITY-CRYPTO-JNI-001" not in completed:
        fail("completed_audit_ids must record AUDIT-SECURITY-CRYPTO-JNI-001 as executed+preserved", errors)
    if "AUDIT-SECURITY-AUTH-DPOP-001" not in completed:
        fail("completed_audit_ids must record AUDIT-SECURITY-AUTH-DPOP-001 as executed+preserved", errors)
    if "AUDIT-SECURITY-ANDROID-STORAGE-001" not in completed:
        fail("completed_audit_ids must record AUDIT-SECURITY-ANDROID-STORAGE-001 as executed+preserved", errors)
    if "AUDIT-SECURITY-ATTACKCHAIN-001" not in completed:
        fail("completed_audit_ids must record AUDIT-SECURITY-ATTACKCHAIN-001 as executed+preserved", errors)
    if PRIOR_GATE_ID not in completed:
        fail(f"completed_audit_ids must record {PRIOR_GATE_ID} as executed+preserved", errors)
    if NEXT_GATE_ID in completed:
        fail(f"{NEXT_GATE_ID} must NOT be in completed_audit_ids", errors)


def validate_tasks(errors):
    tasks = load_jsonl(REGISTRY_DIR / "tasks.jsonl")
    t = next((x for x in tasks if x.get("task_id") == TASK_ID), None)
    if t is None:
        fail(f"{TASK_ID} missing from tasks.jsonl", errors)
    else:
        if t.get("status") != "Ready For Remote":
            fail(f"{TASK_ID} status {t.get('status')!r}, expected Ready For Remote", errors)
        if t.get("start_sha") != BASE_SHA:
            fail(f"{TASK_ID} start_sha must be {BASE_SHA}", errors)
        if t.get("branch") != DELIVERY_BRANCH:
            fail(f"{TASK_ID} branch must be {DELIVERY_BRANCH}", errors)
    for x in tasks:
        if x.get("task_id") == TASK_ID or str(x.get("task_id", "")).startswith("ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-"):
            continue
        blob = (x.get("task_id", "") + " " + x.get("title", "")).upper()
        audit_markers = ("CRYPTO-JNI", "CRYPTO_JNI", "CRYPTOJNI", "AUTH-DPOP", "AUTH_DPOP", "AUTHDPOP",
                         "ANDROID-STORAGE", "ANDROID_STORAGE", "ATTACKCHAIN")
        if any(m in blob for m in audit_markers):
            if x.get("status") not in ("Candidate",):
                fail(f"Specialist audit task {x.get('task_id')} is {x.get('status')!r} — specialist audits are evidence-preserved via the audit-evidence registry, not executed task records; must remain Candidate/NOT_EXECUTED", errors)
    print("  OK   next specialist gates are candidates, not executed")


def validate_no_product_changes(errors):
    if not has_git():
        return
    out = subprocess.run(["git", "diff", "--name-only", BASE_SHA], cwd=REPO_ROOT, capture_output=True, text=True)
    changed = out.stdout.strip().splitlines()
    forbidden = [p for p in changed if p.startswith(FORBIDDEN_PREFIXES) or p.endswith(".sql")]
    jni = [p for p in changed
           if not p.startswith("docs/")
           and ("jni" in p.lower() or "AndroidManifest" in p or p.endswith(".so") or "gradle" in p.lower())]
    bad = sorted(set(forbidden + jni))
    if bad:
        fail(f"product/CI/native paths changed: {bad}", errors)
    else:
        print("  OK   no product/CI/native changes")


def validate_project_memory(errors):
    state_path = REPO_ROOT / "docs" / "continuity" / "CURRENT_STATE.json"
    ledger_path = REPO_ROOT / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl"
    if not state_path.exists() or not ledger_path.exists():
        fail("continuity surfaces missing", errors)
        return
    state = load_json(state_path)
    ledger = load_jsonl(ledger_path)
    if not ledger:
        fail("ledger empty", errors)
        return
    latest = ledger[-1]
    if state.get("latest_material_event_id") != latest.get("event_id"):
        fail("Project Memory stale: latest_material_event_id != last ledger event", errors)
    elif latest.get("event_id") != LEDGER_EVENT:
        fail(f"last ledger event must be {LEDGER_EVENT}, got {latest.get('event_id')}", errors)
    else:
        print(f"  OK   Project Memory synced to {latest.get('event_id')}")


def main():
    errors = []
    print("[EVIDENCE-PRESERVATION] Base / delivery")
    validate_base(errors)
    print("\n[EVIDENCE-PRESERVATION] Preserved reports / hashes / source status")
    validate_reports(errors)
    print("\n[EVIDENCE-PRESERVATION] Audit registry")
    validate_registry(errors)
    print("\n[EVIDENCE-PRESERVATION] Traceability / roots / gates")
    validate_traceability(errors)
    print("\n[EVIDENCE-PRESERVATION] Crypto/JNI specialist evidence")
    validate_cryptojni(errors)
    print("\n[EVIDENCE-PRESERVATION] Auth/DPoP specialist evidence")
    validate_authdpop(errors)
    print("\n[EVIDENCE-PRESERVATION] Android/Storage specialist evidence")
    validate_androidstorage(errors)
    print("\n[EVIDENCE-PRESERVATION] Attackchain specialist evidence")
    validate_attackchain(errors)
    print("\n[EVIDENCE-PRESERVATION] Master Specialist Consolidation evidence")
    validate_master_consolidation(errors)
    print("\n[EVIDENCE-PRESERVATION] Security-Remediation Coverage Gate evidence")
    validate_coverage_gate(errors)
    print("\n[EVIDENCE-PRESERVATION] Canonical findings / historical relations")
    validate_findings(errors)
    print("\n[EVIDENCE-PRESERVATION] Lifecycle state")
    validate_lifecycle(errors)
    validate_tasks(errors)
    print("\n[EVIDENCE-PRESERVATION] Scope / memory")
    validate_no_product_changes(errors)
    validate_project_memory(errors)
    if errors:
        print("\nSECURITY AUDIT EVIDENCE PRESERVATION: FAIL")
        for e in errors:
            print(f"  FAIL {e}")
        return 1
    print("\nSECURITY AUDIT EVIDENCE PRESERVATION: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
