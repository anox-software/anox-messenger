#!/usr/bin/env python3
"""REMEDIATION_SESSION_S0 — Pre-B004 security contract-freeze authority validator.

Fail-closed verification that the canonical S0 contracts frozen in
``docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md`` are present, indexed by
``docs/authority/contracts/S0_CONTRACT_FREEZE_MANIFEST.json``, wired into
``AUTHORITY_INDEX.md`` / ``B_FREEZE_REGISTRY.md`` with unambiguous precedence,
and still carry the security invariants that break AC-001/002/003/004/005/
008/009/010/014:

* SERVER_BREAKER_S1/S2/S3 device-binding invariants, S4 idempotency, S5 typed
  registration PoP, S7 mandatory JKT, S8 ath, S9 nonce, S10/S11 replay,
  S12 raw-path HTU, S15 epoch, S16 identity immutability, S17 rejection
  taxonomy, S18 wipe/revocation;
* first-run/marker contract, backup/restore contract, hardware-trust decision;
* single schema authority (MSC-040) and the preserved governance decisions
  (ROOT-013 MEDIUM/OPEN, ROOT-016 REJECTED, ARCH-010 RETIRE_AT_B004_START).

The validator is structural: it parses clause identifiers ``[S0-uuu-nn]`` and
section headings, cross-references them with the manifest, the SC/CC/S maps,
the authority index and the freeze registry, and only then applies per-clause
invariant regexes.  Set ``S0_CONTRACT_FREEZE_REPO`` to validate an alternate
tree (test fixtures); git-dependent checks are skipped without ``.git``.

This file is S0-owned (distinct from the S1-owned validators and from
``validate_security_audit_evidence_preservation.py``).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(os.environ.get("S0_CONTRACT_FREEZE_REPO") or Path(__file__).resolve().parents[2])
MANIFEST_PATH = "docs/authority/contracts/S0_CONTRACT_FREEZE_MANIFEST.json"
AMENDMENT_PATH = "docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md"
AUTHORITY_INDEX_PATH = "docs/authority/AUTHORITY_INDEX.md"
FREEZE_REGISTRY_PATH = "docs/authority/B_FREEZE_REGISTRY.md"
FINDINGS_PATH = "docs/workforce/registries/findings.jsonl"
IMPL_READINESS_PATH = "docs/workforce/registries/implementation_readiness.json"
PRIOR_AMENDMENT = "B025_MANDATORY_AMENDMENTS_V1_3.md"
THIS_AMENDMENT = "B025_MANDATORY_AMENDMENTS_V1_4.md"
SNAPSHOT_ENTRY = "B025/TRACK_B/B0xx_*.md"
EXPECTED_SCHEMA_VERSION = "S0-CONTRACT-FREEZE-1"
EXPECTED_CONTRACT_VERSION = "S0-CONTRACT-FREEZE v1"
SC_IDS = [f"SC-{i}" for i in range(1, 15)]
CC_IDS = [f"CC-{i}" for i in range(1, 15)]
BREAKER_IDS = [f"S{i}" for i in range(1, 19)]
REQUIRED_CHAINS = ["AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-008", "AC-009", "AC-010", "AC-014"]
BREAKER_STATUSES = {"FROZEN_IN_AUTHORITY", "RETAINED_V1_2"}
FORBIDDEN_PRODUCT_PREFIXES = ("android/", "crypto/", "backend/", ".github/workflows/", "supabase/", "migrations/")
S1_OWNED_FILES = (
    ".github/workflows/ci.yml", "android/build.gradle.kts", "rust-toolchain.toml",
    "tools/security/validate_apk_contents.py", "docs/current/REPOSITORY_SECURITY_POLICY.md",
    "docs/workforce/registries/b021_verification_matrix.jsonl",
)

# ---------------------------------------------------------------------------
# F-02 — the authorized S0 scope base is validator-owned, never manifest-driven.
# A manifest `base_sha` that is absent, malformed, unauthorized, non-existent or
# not an ancestor of HEAD is a VALIDATION FAILURE, never a silent SKIP.
# ---------------------------------------------------------------------------
AUTHORIZED_S0_BASE_SHA = "0f932520393feee6d479cc099f179f5766323125"
# Pinned corrected S0 final head (metadata commit of the corrected S0 delivery,
# preserved by SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001). The S0 scope
# gate evaluates S0's own range base..final-head; both must be HEAD ancestors.
AUTHORIZED_S0_FINAL_HEAD_SHA = "0be57335adaa25ad584357dde74666eb97339a01"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")

# ---------------------------------------------------------------------------
# F-03 — protected shared governance files. These are NOT S0-owned. A change is
# admissible only under an exact, change-specific Human ratification record.
# `authorized_sha256` pins the one ratified post-change content; any further
# modification fails closed and requires a new Human ratification.
# ---------------------------------------------------------------------------
DECISIONS_PATH = "docs/workforce/registries/decisions.jsonl"
F01_RATIFICATION_DECISION_ID = "ANOX-DECISION-S0-F01-RATIFICATION-001"
F01_RATIFICATION_REPORT = "docs/reports/security/decisions/S0-F01-FILE-OWNERSHIP-RATIFICATION-001.md"
S0_TASK_ID = "ANOX-TASK-REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001"
PRESERVATION_RATIFICATION_DECISION_ID = "ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001"
PRESERVATION_RATIFICATION_REPORT = "docs/reports/security/decisions/S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001.md"
PRESERVATION_TASK_ID = "ANOX-TASK-SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001"

# ---------------------------------------------------------------------------
# THIRD (and last) authorized content of the protected central validator:
# the S1 integration lifecycle extension.
#
# Why this exists (retest S1-004 blocking finding B-6): applying the S1
# ratification package makes the protected validator the S1 successor, which
# F-03 below pinned to only TWO authorized contents. So committing the package
# failed S0 no matter what — an R1 that also carried this pin was rejected for
# changing a third path, and a metadata-only R2 may not touch tools/**. The
# ratification is therefore ONE atomic four-path transaction.
#
# SCOPE — this grants NO general future successor permission. Exactly one hash,
# one four-path set, one decision id, one ratified_change. Any other content of
# a PROTECTED_SHARED_GOVERNANCE_FILE remains a hard failure and a new Human
# ratification is required, exactly as before.
S1_INTEGRATION_RATIFICATION_DECISION_ID = "ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001"
S1_INTEGRATION_RATIFICATION_REPORT = "docs/reports/security/decisions/S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-PROPOSAL-001.md"

# --- Human-authorized post-R2 CI-infrastructure tail disposition -----------
# ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001 ratifies exactly the
# five ci.yml-only commits below — position (after the completed R1/R2 tail),
# order and SHA identity are all bound — plus the disposition pair
# [R3a substantive, R3b metadata] carrying the governance extension, and the
# sealing event ANOX-EVENT-0058. Kept self-contained on purpose: these pins
# must NOT be read out of an S1-writable module.
S1_CI_DISPOSITION_DECISION_ID = "ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001"
S1_CI_DISPOSITION_RECORD = "docs/reports/security/decisions/S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001.md"
S1_CI_DISPOSITION_TASK = "ANOX-TASK-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001"
S1_CI_TAIL_SHAS = (
    "e7bd2c6547fb23de44a8aa762fe5d046c34d318e",
    "0636a4ee81e2e7ea9dd4ca7615d06bf80ae80827",
    "793246022c0501e85350113871d00db9ee843826",
    "45d1e4a63de45fe10d2fc8f455b321bb675e390a",
    # ANOX-TASK-S1-CI-ARM64-ISOLATION-001 — deterministic stale-emulator
    # isolation for the persistent self-hosted ARM64 runner.
    "4fc5263ff6763768088f0f13856d704bd1772178",
)
S1_CI_TAIL_ALLOWED_PATHS = frozenset({".github/workflows/ci.yml"})
S1_CI_DISPOSITION_PATHS = frozenset({
    "tools/audit/lifecycle_legality.py",
    "tools/audit/validate_s1_integration_evidence.py",
    "tools/audit/validate_security_audit_evidence_preservation.py",
    "tools/audit/validate_s0_contract_freeze.py",
    "tools/audit/test_s1_integration_evidence.py",
    "tools/audit/test_security_audit_evidence_preservation.py",
    "tools/audit/test_s0_contract_freeze.py",
    "tools/audit/validate_s0_evidence_preservation.py",
    S1_CI_DISPOSITION_RECORD,
})
# Exact authorized post-images of the package files this validator pins —
# the same three externally pinnable members as the R1 transaction. This
# file's own post-image cannot be self-pinned; the decision record pins it
# (and the S1 validator's) externally, verified against live content below.
S1_CI_DISPOSITION_CENTRAL_SHA256 = "fe5abd4e7a39029a679be336589d8aa766b80c72862a5bb77f05693a30034899"
S1_CI_DISPOSITION_POST_IMAGES = {
    "tools/audit/validate_security_audit_evidence_preservation.py": S1_CI_DISPOSITION_CENTRAL_SHA256,
    "tools/audit/test_security_audit_evidence_preservation.py": "29399c5ddb54909b94bf046d257608da52c39bd4ae94a76508ca21e60ac0ae0c",
    "tools/audit/test_s0_contract_freeze.py": "97d7896009235e5138aed86d6a7b7361d0cb333b605208d899900dc498832fa4",
}
S1_INTEGRATION_RATIFIED_CHANGE = "S1_INTEGRATION_LIFECYCLE_EXTENSION"
S1_INTEGRATION_TASK_ID = "ANOX-TASK-REMEDIATION-S1-CANONICAL-INTEGRATION-001"
# The four paths R1 must change, and nothing else.
S1_RATIFICATION_PATHS = (
    "tools/audit/test_s0_contract_freeze.py",
    "tools/audit/test_security_audit_evidence_preservation.py",
    "tools/audit/validate_s0_contract_freeze.py",
    "tools/audit/validate_security_audit_evidence_preservation.py",
)
# Pinned post-images of the transaction. THIS file's own post-image is
# deliberately ABSENT: pinning a file's digest inside itself is an unsatisfiable
# fixed point. Its integrity comes from three independent places instead — the
# exact changed-path set of R1, the external pin in
# tools/audit/validate_s1_integration_evidence.py (which is NOT part of R1), and
# the Human ratification record, which must pin all four.
S1_RATIFICATION_POST_IMAGES = {
    "tools/audit/validate_security_audit_evidence_preservation.py":
        "859e834e06876e34efbdaf9f209005c86d0562b54237f602c45f110bc72a6148",
    "tools/audit/test_security_audit_evidence_preservation.py":
        "c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462",
    "tools/audit/test_s0_contract_freeze.py":
        "d22034e61257f3d13588b402b49eba2396ee2b5b9a736774e9a6522ee037f13a",
}
# Nothing substantive may follow R1: the only admissible successor commit is the
# required metadata synchronisation R2. Kept self-contained on purpose — reading
# the allow-list out of an S1-writable module would let the S1 session widen the
# acceptance criteria of the contract meant to constrain it.
POST_R1_FORBIDDEN_PREFIXES = (
    "tools/", "crypto/", "android/", ".github/", "backend/", "supabase/",
    "migrations/", "docs/authority/",
)
PROTECTED_SHARED_FILES = {
    "tools/audit/validate_security_audit_evidence_preservation.py": {
        "classification": "PROTECTED_SHARED_GOVERNANCE_FILE",
        "owner": "SHARED_GOVERNANCE (not S0, not S1)",
        "ratification_decision_id": F01_RATIFICATION_DECISION_ID,
        "ratified_task": S0_TASK_ID,
        "ratified_change": "S0_SUCCESSOR_EVENT_SUPPORT",
        # SHA-256 of the single Human-ratified post-change content.
        "authorized_sha256": "756141b378a19e3e30c225e1e158bbcd61d6d0b7dc921a3f4fe591c81e497b80",
        # Second Human-ratified content: the S0 preservation lifecycle
        # extension (EVENT-0054 + 13th registry record), ratified separately
        # under ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001.
        "preservation_decision_id": PRESERVATION_RATIFICATION_DECISION_ID,
        "preservation_ratified_task": PRESERVATION_TASK_ID,
        "preservation_ratified_change": "S0_PRESERVATION_LIFECYCLE_EXTENSION",
        "preservation_authorized_sha256": "89c7358fbbe61c71c8fcde114ffc8a83aa33f52bd3fb763417e00f4131d84bb7",
        "preservation_record_path": PRESERVATION_RATIFICATION_REPORT,
        # Third Human-ratified content: the S1 integration lifecycle extension,
        # ratified as the atomic four-path transaction described above under
        # ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001.
        "s1_integration_decision_id": S1_INTEGRATION_RATIFICATION_DECISION_ID,
        "s1_integration_authorized_sha256":
            "859e834e06876e34efbdaf9f209005c86d0562b54237f602c45f110bc72a6148",
        "s1_integration_record_path": S1_INTEGRATION_RATIFICATION_REPORT,
        # Fourth Human-ratified content: the CI-infrastructure tail
        # disposition extension, ratified under
        # ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001.
        "s1_ci_disposition_decision_id": S1_CI_DISPOSITION_DECISION_ID,
        "s1_ci_disposition_authorized_sha256": S1_CI_DISPOSITION_CENTRAL_SHA256,
        "s1_ci_disposition_record_path": S1_CI_DISPOSITION_RECORD,
        "base_sha256": "2ab59295301e65ed17a7b7256209530bd69e3aeaa57364b0db68aaa0af90bcc9",
        "s1_prohibited_before_integration": True,
    },
}

# ---------------------------------------------------------------------------
# F-04 — deference documents required by the frozen MSC-040 contract are
# validator-owned. Removing one from the manifest must not remove the check.
# ---------------------------------------------------------------------------
REQUIRED_DEFERRING_DOCUMENTS = (
    "docs/current/DATABASE_ARCHITECTURE.md",
    "docs/current/BACKEND_ARCHITECTURE.md",
)
REQUIRED_SCHEMA_HOME_MARKER = "SCHEMA-AUTHORITY-HOME: DB-SCHEMA-V1-FROZEN"
REQUIRED_SCHEMA_DEFERENCE_MARKER = "DEFERS-TO: DB-SCHEMA-V1-FROZEN"

# ---------------------------------------------------------------------------
# F-05 — independent mapping anchors.
#
# Derived from the hash-preserved canonical security model
# (`MASTER-SPECIALIST-CONSOLIDATION-001` §CONSOLIDATED SERVER/CLIENT SECURITY
# CONTRACT, §SERVER BREAKER COVERAGE, §ATTACKCHAIN -> MSC UNIT MAPPING) and held
# in validator source so that a *coherent* rewrite of both the manifest and the
# V1.4 tables cannot silently re-point a security-critical rule at an unrelated
# clause. These are anchors (required subsets), not a competing authority: they
# add no new normative requirement, they only pin where each already-frozen rule
# must live.
# ---------------------------------------------------------------------------
SC_ANCHOR_CLAUSES = {
    "SC-1":  {"S0-027-01", "S0-027-04", "S0-027-05"},   # typed PoP, 3 phases, JWK equality
    "SC-2":  {"S0-026-01", "S0-026-03"},                # (registration_id, jkt) idempotency
    "SC-3":  {"S0-028-01", "S0-028-03", "S0-028-09"},   # global UNIQUE, known-key reject, one-wins
    "SC-4":  {"S0-028-05", "S0-028-06"},                # context from validated key, immutable
    "SC-5":  {"S0-028-11"},                             # identity key immutability
    "SC-6":  {"S0-026-04", "S0-026-07", "S0-026-18"},   # jkt mandatory, ath mandatory, ES256/P-256
    "SC-7":  {"S0-025-01", "S0-025-03", "S0-025-04"},   # nonce required, binding scope, TTL/single-use
    "SC-8":  {"S0-026-08", "S0-026-12"},                # shared atomic store, iat-keyed retention
    "SC-9":  {"S0-022-01", "S0-022-03", "S0-026-14"},   # raw path, no double-decode, router raw
    "SC-10": {"S0-020-02"},                             # epoch coupling (base retained in V1.2 B-006)
    "SC-11": {"S0-020-01", "S0-034-09"},                # monotonic epoch, server authority
    "SC-12": {"S0-026-15", "S0-026-16"},                # rejection_class taxonomy
    "SC-13": {"S0-032-03", "S0-032-07"},                # revocation terminal, deletion order
    "SC-14": {"S0-042-02", "S0-042-03"},                # identity from key, self-report untrusted
}
CC_ANCHOR_CLAUSES = {
    "CC-1":  {"S0-033-06"},
    "CC-3":  {"S0-020-04"},
    "CC-5":  {"S0-042-04", "S0-033-03", "S0-032-08"},
    "CC-6":  {"S0-026-05", "S0-026-09"},
    "CC-7":  {"S0-033-04"},
    "CC-8":  {"S0-033-07", "S0-018-01"},
    "CC-9":  {"S0-033-09"},
    "CC-10": {"S0-020-04", "S0-034-08"},
    "CC-11": {"S0-032-06"},
    "CC-12": {"S0-033-07"},
}
BREAKER_ANCHOR_CLAUSES = {
    "S1":  {"S0-028-01", "S0-028-03"},
    "S2":  {"S0-028-05"},
    "S3":  {"S0-028-08", "S0-028-09"},
    "S4":  {"S0-026-01"},
    "S5":  {"S0-027-01", "S0-027-05"},
    "S6":  {"S0-026-18"},
    "S7":  {"S0-026-04", "S0-026-06"},
    "S8":  {"S0-026-07"},
    "S9":  {"S0-025-01"},
    "S10": {"S0-026-08"},
    "S11": {"S0-026-12"},
    "S12": {"S0-022-01"},
    "S15": {"S0-020-01", "S0-034-09"},
    "S16": {"S0-028-11"},
    "S17": {"S0-026-15"},
    "S18": {"S0-032-03"},
}
# S13/S14 stay RETAINED_V1_2 with no V1.4 clause of their own (retained_base only).
BREAKER_RETAINED_ONLY = {"S13", "S14"}
BREAKER_EXPECTED_STATUS = {
    **{b: "FROZEN_IN_AUTHORITY" for b in BREAKER_ANCHOR_CLAUSES if b != "S6"},
    "S6": "RETAINED_V1_2", "S13": "RETAINED_V1_2", "S14": "RETAINED_V1_2",
}
AC_ANCHORS = {
    "AC-001": {"breakers": {"C1", "S1", "S2"}, "clauses": {"S0-033-04", "S0-028-01"},
               "rule": "uniqueness_alone_not_accepted"},
    "AC-002": {"breakers": {"S12", "C9"}, "clauses": {"S0-022-01"}, "rule": None},
    "AC-003": {"breakers": {"S7", "C9"}, "clauses": {"S0-026-04", "S0-026-06"},
               "rule": "ath_alone_insufficient"},
    "AC-004": {"breakers": {"S10", "S11"}, "clauses": {"S0-026-08"}, "rule": None},
    "AC-005": {"breakers": {"S15", "C12"}, "clauses": {"S0-020-05"}, "rule": None},
    "AC-008": {"breakers": {"C11", "S16", "S18"}, "clauses": {"S0-028-11"}, "rule": None},
    "AC-009": {"breakers": {"S4", "C4"}, "clauses": {"S0-026-01"}, "rule": None},
    "AC-010": {"breakers": {"S5", "C10"}, "clauses": {"S0-027-08", "S0-027-05"},
               "rule": "pop_tied_to_deviceauth_identity"},
    "AC-014": {"breakers": {"C13", "S17"}, "clauses": {"S0-018-01"}, "rule": None},
}

# ---------------------------------------------------------------------------
# F-07 — MSC-022 is a SUPPORTING contract entry frozen in service of MSC-026 /
# SERVER_BREAKER_S12. It is never a primary S0 unit and never advances stage.
# ---------------------------------------------------------------------------
PRIMARY_S0_MSC_UNITS = {
    "MSC_UNIT_018", "MSC_UNIT_020", "MSC_UNIT_025", "MSC_UNIT_026", "MSC_UNIT_027",
    "MSC_UNIT_028", "MSC_UNIT_032", "MSC_UNIT_033", "MSC_UNIT_034", "MSC_UNIT_040",
    "MSC_UNIT_042",
}
SUPPORTING_S0_MSC_UNITS = {"MSC_UNIT_022"}
CONSUMED_S0_MSC_UNITS = {"MSC_UNIT_039"}

# ---------------------------------------------------------------------------
# F-08 — CC rules whose normative home must be an AUTHORITY_INDEX-indexed
# document. The Master consolidation is traceability/evidence, never authority.
# ---------------------------------------------------------------------------
NON_AUTHORITY_EVIDENCE_SOURCES = ("MASTER-SPECIALIST-CONSOLIDATION", "SECURITY-REMEDIATION-COVERAGE-GATE")

# ---------------------------------------------------------------------------
# F-09 — no dangling internal section reference may survive in the amendment.
# ---------------------------------------------------------------------------
SECTION_REF_RE = re.compile(r"§(\d+)\.(\d+)")

# ---------------------------------------------------------------------------
# F-10 — amended freeze-registry rows must keep BOTH their base pointer and the
# S0 amendment pointer.
# ---------------------------------------------------------------------------
FREEZE_REGISTRY_BASE_POINTERS = {
    "B-002": "B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md",
    "B-003": "B025_MANDATORY_AMENDMENTS_V1_1.md#B-003",
    "B-004": "B025_MANDATORY_AMENDMENTS_V1_2.md#B-004",
    "B-005": "B025_MANDATORY_AMENDMENTS_V1_2.md#B-005",
    "B-006": "B025_MANDATORY_AMENDMENTS_V1_2.md#B-006",
    "B-007": "B025_MANDATORY_AMENDMENTS_V1_2.md#B-007",
    "B-009": "B025/TRACK_B/B009_LOCAL_DATABASE.md",
    "B-013": "B025_MANDATORY_AMENDMENTS_V1_1.md#B-013",
}

CLAUSE_RE = re.compile(r"\*\*\[(S0-\d{3}-\d{2})\]\*\*")
CLAUSE_REF_RE = re.compile(r"\[(S0-\d{3}-\d{2})\](?:[–-]\[(S0-\d{3}-\d{2})\])?")
HEADING_RE = re.compile(r"^## (.+)$")

# ---------------------------------------------------------------------------
# Core per-clause invariants (independent of the manifest, so a coherent
# rewrite of manifest + document still has to keep the security content).
# Patterns are matched case-sensitively against the single clause line unless
# prefixed with (?i).
# ---------------------------------------------------------------------------
CORE_INVARIANTS = {
    # framework / status
    "S0-000-03": {"require": [r"IMPLEMENTED = FROZEN_IN_CANONICAL_AUTHORITY", r"CLOSED_BY_S0 = 0", r"OPEN MSC UNITS = 42"]},
    "S0-000-06": {"require": [r"SERVER CONTRACT RULES = 14", r"AMBIGUOUS = 0", r"CONTRADICTORY = 0"]},
    "S0-000-07": {"require": [r"CLIENT CONTRACT RULES = 14", r"AUTHORITY OWNER KNOWN = 14"]},
    "S0-000-08": {"require": [r"SERVER BREAKERS TOTAL = 18"]},
    "S0-000-09": {"require": [r"uniqueness alone \(S1\) is \*\*not\*\* accepted", r"`ath` alone is insufficient",
                              r"tied to the authoritative DeviceAuth identity"]},
    "S0-000-12": {"require": [r"B004 = NOT_STARTED", r"B005 = NOT_STARTED", r"BACKEND = NOT_IMPLEMENTED",
                              r"S1 = NOT_EXECUTED_BY_THIS_TASK", r"S2 = NOT_STARTED", r"S3 = NOT_STARTED", r"S4 = NOT_STARTED"],
                  "forbid": [r"B00[45] = (STARTED|IN_PROGRESS|IMPLEMENTED)"]},
    "S0-000-13": {"require": [r"FULLY CLOSED MSC UNITS = 0", r"OPEN MSC UNITS = 42"],
                  "forbid": [r"→ `?CLOSED`?"]},
    # MSC-040 schema authority
    "S0-040-01": {"require": [r"\*\*single canonical frozen schema contract\*\*", r"exactly one chain", r"this document wins"]},
    "S0-040-02": {"require": [r"docs/current/DATABASE_ARCHITECTURE\.md", r"docs/current/BACKEND_ARCHITECTURE\.md",
                              r"MUST explicitly defer", r"superseded and has no normative effect"]},
    "S0-040-05": {"require": [r"second equal-precedence schema authority is prohibited", r"CANONICAL CONTRACT AMBIGUITIES = 0"]},
    # MSC-028 S1/S2/S3/S16
    "S0-028-01": {"require": [r"\*\*globally unique\*\*", r"UNIQUE\(device_auth_keys\.public_key\)", r"UNIQUE\(device_auth_keys\.jkt\)",
                              r"including `REVOKED`", r"mandatory"],
                  "forbid": [r"(?i)unique per account", r"(?i)not required"]},
    "S0-028-02": {"require": [r"\*\*never deleted\*\*", r"`ACTIVE` → `REVOKED` \(terminal\)"]},
    "S0-028-03": {"require": [r"\*\*Known-key rejection:\*\*", r"already exists in `device_auth_keys`", r"`ACTIVE` or `REVOKED`",
                              r"device_auth_key_reuse_rejected", r"`PERMANENT`", r"never re-binds, re-activates"],
                  "forbid": [r"(?i)\bMAY (re-bind|re-activate|adopt|accept)"]},
    "S0-028-05": {"require": [r"derived \*\*exclusively\*\* from the validated Device Auth key", r"MUST NOT override"],
                  "forbid": [r"(?i)JSON (MAY|may) (override|supply)"]},
    "S0-028-06": {"require": [r"\*\*immutable\*\* after the registration commit", r"No `UPDATE` may re-point"],
                  "forbid": [r"(?i)(?<!im)mutable after", r"(?i)(?<!no `update` )may re-point"]},
    "S0-028-08": {"require": [r"one_active_device_per_account ON devices\(account_id\) WHERE status = 'ACTIVE'", r"mandatory"]},
    "S0-028-09": {"require": [r"\*\*One wins:\*\*", r"first transaction to commit the `ACTIVE` device wins", r"rolls back completely",
                              r"No last-write-wins"],
                  "forbid": [r"(?i)last-write-wins is (permitted|allowed|acceptable)", r"(?i)both (win|succeed)"]},
    "S0-028-11": {"require": [r"UNIQUE\(account_id, device_id\)", r"UNIQUE\(ed25519_public_key\)", r"UNIQUE\(curve25519_public_key\)",
                              r"identity_key_immutable", r"`PERMANENT`", r"never updated or deleted"],
                  "forbid": [r"(?i)MAY (be )?(rotate|replace|update)d?"]},
    # MSC-026
    "S0-026-01": {"require": [r"idempotent on the key `\(registration_id, jkt\)`", r"\*\*same authoritative result\*\*", r"no additional write"]},
    "S0-026-03": {"require": [r"`commit` is idempotent", r"never create a second account, device, key or identity row"]},
    "S0-026-04": {"require": [r"For \*\*every\*\* request that presents an access token", r"MUST compute the JKT", r"MUST require it to equal",
                              r"KEY_BINDING_MISMATCH", r"`PERMANENT`"],
                  "forbid": [r"\bMAY\b", r"(?i)optional", r"(?i)\bSHOULD\b"]},
    "S0-026-05": {"require": [r"There is \*\*no\*\* server mode", r"non-nullable input"],
                  "forbid": [r"(?i)(?<!non-)nullable input", r"(?i)binding (MAY|may|can) be (skipped|optional|nullable)"]},
    "S0-026-06": {"require": [r"never substitutes for JKT binding", r"MUST be rejected on every token-bearing endpoint"]},
    "S0-026-07": {"require": [r"MUST contain `ath`", r"base64url\(SHA-256\(ASCII\(access_token\)\)\)", r"Missing or mismatching `ath`", r"`PERMANENT`"],
                  "forbid": [r"\bMAY contain", r"(?i)ath (is|MAY be) optional", r"(?i)\bSHOULD contain"]},
    "S0-026-08": {"require": [r"\*\*shared\*\* by every verifier instance and replica", r"\*\*atomic\*\*", r"insert-if-absent", r"`\(jkt, jti\)`",
                              r"replay_detected"]},
    "S0-026-09": {"require": [r"Process-local verifier memory", r"\*\*prohibited\*\* as the production replay store", r"no default replay cache"],
                  "forbid": [r"(?i)process-local .*(permitted|acceptable|allowed|sufficient) (as|for) (the )?production"]},
    "S0-026-11": {"require": [r"±120 s", r"MUST fail closed"]},
    "S0-026-12": {"require": [r"keyed by the proof's \*\*`iat`\*\*", r"never by wall-clock insertion time alone", r"MUST NOT re-admit",
                              r"MUST NOT shorten retention"],
                  "forbid": [r"(?i)wall-clock insertion time (is|MAY be) (sufficient|used alone|the key)"]},
    "S0-026-13": {"require": [r"fails closed", r"never degrades to process-local acceptance"]},
    "S0-026-14": {"require": [r"dispatches on the \*\*raw\*\* request path", r"neither side percent-decodes"]},
    "S0-026-15": {"require": [r"`rejection_class` member", r"`transient`", r"`permanent`", r"MUST NOT retry"]},
    "S0-026-16": {"require": [r"`TRANSIENT` = `use_dpop_nonce`", r"`PERMANENT` = `invalid_dpop`", r"invalid_registration_pop",
                              r"device_auth_key_reuse_rejected", r"identity_key_immutable"]},
    "S0-026-17": {"require": [r"generic rejection without `rejection_class` is non-conformant"]},
    "S0-026-18": {"require": [r"`alg = \"ES256\"` only", r"`crv = \"P-256\"`", r"no private members", r"≥ 128 random bits"]},
    # MSC-022 HTU
    "S0-022-01": {"require": [r"`raw_path` is the request-target path \*\*exactly as received, byte for byte\*\*", r"\*\*not decoded\*\*",
                              r"`port` is included \*\*only\*\* when present in the request and \*\*not\*\* the scheme default",
                              r"`scheme` is lowercased", r"`host` is lowercased", r"no trailing-slash normalization"],
                  "forbid": [r"(?i)decoded path", r"(?i)percent-decoded path", r"(?i)after decoding"]},
    "S0-022-02": {"require": [r"\*\*no userinfo\*\*", r"\*\*no query\*\*", r"\*\*no fragment\*\*", r"is rejected with `invalid_dpop`"],
                  "forbid": [r"(?i)userinfo (is|MAY be|are) (permitted|allowed|accepted|retained)"]},
    "S0-022-03": {"require": [r"neither client nor server decodes", r"no double-decoding", r"`/v1/a%2Fb` vs `/v1/a/b`", r"%3F", r"%23", r"%00", r"%2520"],
                  "forbid": [r"(?i)MAY decode", r"(?i)double-decoding is (permitted|acceptable)"]},
    "S0-022-04": {"require": [r":443/v1/a`", r"`/v1/a` ≠ `/v1/a/`", r"empty path is canonicalized to `/`"]},
    "S0-022-05": {"require": [r"`htm` MUST equal the request method byte-exactly", r"`GET`, `POST`, `PUT`, `DELETE`, `PATCH`", r"no case normalization"]},
    "S0-022-06": {"require": [r"lock-step", r"raw encoded path"]},
    # MSC-025 nonce
    "S0-025-01": {"require": [r"\*\*Nonce is required, not optional\*\*", r"\*\*every token-bearing request\*\*",
                              r"nonce is optional, defaulted or skipped for these classes is prohibited"],
                  "forbid": [r"(?i)nonce (is|MAY be|remains) optional(?!, defaulted or skipped)", r"(?i)implementation choice", r"(?i)(MAY|may) (omit|skip) the nonce"]},
    "S0-025-02": {"require": [r"`POST /v1/auth/challenge`", r"`DPoP-Nonce` response header", r"\*\*every\*\* response from a nonce-required endpoint class"]},
    "S0-025-03": {"require": [r"≥ 128 bits of entropy", r"`\(jkt, endpoint_class\)`"]},
    "S0-025-04": {"require": [r"\*\*TTL:\*\* 300 s", r"\*\*Single use:\*\*", r"consumed atomically in the shared store", r"replay_detected",
                              r"neither replaces the other"]},
    "S0-025-05": {"require": [r"`code = \"use_dpop_nonce\"`", r"`rejection_class = \"transient\"`", r"fresh `DPoP-Nonce` header"]},
    "S0-025-06": {"require": [r"retries \*\*once\*\*", r"fresh `jti`", r"no unbounded retry loop"]},
    "S0-025-07": {"require": [r"process memory only", r"never written to the registration store", r"After process restart"]},
    # MSC-027 PoP
    "S0-027-01": {"require": [r"\*\*typed\*\* structure `RegistrationPoP v1`", r"`typ = \"anox-reg-pop\+jwt\"`", r"`alg = \"ES256\"`",
                              r"signed by the \*\*Device Auth private key\*\*", r"opaque, untyped `proof` field is \*\*not\*\* a conformant contract"],
                  "forbid": [r"(?i)opaque .*(is )?(acceptable|sufficient|conformant)(?! contract)", r"(?i)any signer"]},
    "S0-027-02": {"require": [r"`registration_id`", r"`grant_hash`", r"`nonce`", r"`jkt`", r"`identity_material_hash`", r"`phase`",
                              r"registration_id ‖ grant-hash ‖ nonce ‖ DeviceAuth JWK ‖ identity-material-hash"]},
    "S0-027-03": {"require": [r"\*\*Deterministic encoding:\*\*", r"anox\.reg\.identity\.v1", r"domain separation", r"MUST never be accepted as a registration PoP"]},
    "S0-027-04": {"require": [r"required at all three security-relevant phases", r"`submit-device-auth`, `submit-public-identity` and `commit`",
                              r"invalid_registration_pop"]},
    "S0-027-05": {"require": [r"\*\*JWK equality:\*\*", r"MUST be byte-canonically equal", r"thumbprint MUST equal the payload `jkt`",
                              r"A second JWK per `registration_id` is never accepted"],
                  "forbid": [r"(?i)different JWK .*(MAY|may) be (accepted|permitted)", r"(?i)second JWK .*(MAY|may) be accepted"]},
    "S0-027-06": {"require": [r"single-use in the shared `\(jkt, jti\)` store", r"idempotent on `\(registration_id, jkt\)`"]},
    "S0-027-07": {"require": [r"\*\*Failure taxonomy:\*\*", r"invalid_registration_pop", r"MUST carry the PoP, the nonce and the idempotency key explicitly",
                              r"un-typed proof or omits any of them is non-conformant"]},
    "S0-027-08": {"require": [r"tied to the authoritative Device Auth identity", r"never from JSON fields"]},
    # MSC-033 first-run / marker
    "S0-033-01": {"require": [r"`ABSENT`", r"`ARMED`", r"`BOUND`", r"`EXPLICIT_RESET`", r"`CORRUPT`", r"treated as `BOUND`"]},
    "S0-033-02": {"require": [r"\*\*authenticated\*\*", r"HMAC-SHA-256", r"anox\.deviceauth\.marker\.hmac\.v1", r"treats the marker as `BOUND`",
                              r"HMAC key missing ⇒ bound", r"invalid tag ⇒ `CORRUPT`"]},
    "S0-033-03": {"require": [r"never revert to `ABSENT` except through the explicit reset path", r"not public API", r"one guarded store primitive"]},
    "S0-033-04": {"require": [r"marker `BOUND` or `ARMED` ⇒ \*\*NOT FIRST RUN\*\*",
                              r"marker `CORRUPT` ⇒ \*\*NOT FIRST RUN\*\*",
                              r"marker `ABSENT` \*\*AND any relevant anoX Keystore alias or local state indicates prior initialization\*\* ⇒ \*\*NOT FIRST RUN\*\*",
                              r"explicit recovery-reset path only",
                              r"marker `ABSENT` AND no alias AND no state/residue file ⇒ \*\*FIRST RUN\*\*"],
                  "forbid": [r"(?i)alias (present|exists|is present|indicates prior initialization).{0,80}⇒ \*\*FIRST RUN", r"`CORRUPT` ⇒ \*\*FIRST RUN"]},
    "S0-033-05": {"require": [r"anox\.deviceauth\.p256\.v1", r"anox\.b003\.session\.v1", r"anox_crypto_master_key", r"anox_db_wrap_v1",
                              r"anox\.deviceauth\.marker\.hmac\.v1", r"anox_registration_session\.enc", r"anox_identity\.enc"]},
    "S0-033-06": {"require": [r"never creates a Keystore key, a file or a marker", r"this section wins"]},
    "S0-033-07": {"require": [r"`EMPTY`", r"`TRUNCATED`", r"`AUTH_FAILED`", r"`KEY_MISSING`", r"`UNSUPPORTED_VERSION`", r"`IO_FAILURE`",
                              r"\*\*Every\*\* one of these is consumed as \*\*NOT FIRST RUN\*\*", r"\*\*none\*\* maps to `NotStarted`",
                              r"superseded"],
                  "forbid": [r"(?i)(EMPTY|CORRUPT|corrupt|TRUNCATED|KEY_MISSING)`? (maps?|→) (to )?`?NotStarted",
                             r"(?i)NotStarted`? is safe(?!\"\s*\(PROMPT-008)"]},
    "S0-033-08": {"require": [r"`\.bak` file is \*\*never\*\* auto-restored", r"strictly \*\*after\*\* the first-run resolver"]},
    "S0-033-09": {"require": [r"`fsync` file", r"atomic rename", r"`fsync` parent directory", r"rename result is checked"]},
    "S0-033-10": {"require": [r"`CommitArmed` persisted → marker `ARMED` → remote `commit`", r"→ marker `BOUND`", r"never account recovery"]},
    "S0-033-11": {"require": [r"\*\*Single-process assumption:\*\*", r"exactly one process", r"fail closed"]},
    # MSC-018 RejectedAfterArm
    "S0-018-01": {"require": [r"`RejectedAfterArm\(registrationId, jkt, rejectionClass, code\)`", r"\*\*only\*\* from `CommitArmed`",
                              r"MUST NOT be persisted as `Failed`, `NotStarted`"],
                  "forbid": [r"(?i)MAY be persisted as `?Failed"]},
    "S0-018-02": {"require": [r"\*\*Transient rejection\*\*", r"marker stays `ARMED`", r"\*\*same\*\* `registration_id`"]},
    "S0-018-03": {"require": [r"\*\*Permanent rejection\*\*", r"marker stays `ARMED`", r"\*\*no\*\* retry and \*\*no\*\* fresh registration",
                              r"\*\*explicit reset path\*\*"],
                  "forbid": [r"(?i)marker (is cleared|becomes `?ABSENT|is removed)", r"(?i)(?<!\*\*no\*\* )fresh registration is (permitted|allowed)"]},
    "S0-018-04": {"require": [r"guard lives at the store", r"no caller can persist a downgrade", r"Direct `save\(\)` bypasses are non-conformant"]},
    "S0-018-05": {"require": [r"\*\*Explicit reset contract \(deletion order\):\*\*", r"\(2\) destroy the Device Auth key alias `anox\.deviceauth\.p256\.v1`",
                              r"delete the marker file \*\*last\*\*", r"Device Auth alias is always deleted \*\*before\*\* the marker"],
                  "forbid": [r"(?i)marker (file )?(is deleted )?first", r"(?i)before the Device Auth alias"]},
    "S0-018-06": {"require": [r"released only by `BOUND`", r"Silent release on `Rejected`", r"prohibited"]},
    # MSC-032 wipe matrix
    "S0-032-01": {"require": [r"`logout`", r"`local wipe`", r"`account deletion`", r"`explicit reset`", r"`device revocation`",
                              r"`license-expiry restricted flow`"]},
    "S0-032-02": {"require": [r"\*\*Logout keeps the key:\*\*", r"Device Auth key, E2EE identity/sessions, local DB and marker are retained"]},
    "S0-032-03": {"require": [r"\*\*Device revocation is terminal\*\*", r"`ACTIVE → REVOKED`", r"never silently generates a replacement key",
                              r"row is retained"]},
    "S0-032-04": {"require": [r"\*\*Account deletion\*\*", r"terminal erasure intent durably server-side first", r"revokes device/sessions/push",
                              r"forces the local wipe"]},
    "S0-032-06": {"require": [r"\*\*truthful per-item outcomes\*\*", r"`DELETED`, `NOT_PRESENT`, or `FAILED\(reason\)`",
                              r"reporting `Success` on partial failure is non-conformant"]},
    "S0-032-07": {"require": [r"\*\*Frozen deletion order\*\*", r"\(3\) close the local DB and destroy live native handles",
                              r"\(5\) destroy aliases", r"then `anox\.deviceauth\.p256\.v1`", r"\(6\) set marker `EXPLICIT_RESET`, delete the marker file \*\*last\*\*",
                              r"never removed early", r"AC-001 not re-created"],
                  "forbid": [r"(?i)marker (file )?first", r"(?i)any order"]},
    "S0-032-08": {"require": [r"callable only from the single wipe/reset orchestrator", r"not public API"]},
    # MSC-034 backup / restore
    "S0-034-01": {"require": [r"\*\*CONTRACTUAL\*\*", r"\*\*PHYSICAL_TEST_DEPENDENT\*\*", r"\*\*PROHIBITED_ASSUMPTION\*\*",
                              r"`PHYSICAL_P4`, `P5`, `P7`, `P8`, `P10`, `P11`", r"provenance-verified binary"]},
    "S0-034-02": {"require": [r"\*\*PROHIBITED_ASSUMPTIONS:\*\*", r"Keystore aliases are deleted by app-data clear",
                              r"\*\*CONTRACTUAL:\*\*", r"fails closed whenever any alias or file indicates prior initialization",
                              r"`allowBackup=\"false\"`", r"server is the sole freshness/uniqueness authority"]},
    "S0-034-03": {"require": [r"`pm clear`", r"NOT FIRST RUN → explicit reset only", r"rejects re-registration of the surviving key",
                              r"old identity unrecoverable"]},
    "S0-034-04": {"require": [r"Uninstall / reinstall", r"never transfers or recovers the account"]},
    "S0-034-05": {"require": [r"Seedvault", r"device-to-device", r"no anoX private file, marker or registration store is included in any backup",
                              r"NOT FIRST RUN, fail closed", r"No recovery path may be created by any restore"]},
    "S0-034-06": {"require": [r"work profile", r"\*\*independent device\*\*", r"Owner profile is unaffected"]},
    "S0-034-07": {"require": [r"OS update", r"bound state unchanged", r"never silent regeneration"]},
    "S0-034-08": {"require": [r"Rollback scenarios", r"MUST bind the server publication epoch", r"security anomaly",
                              r"local counter is not an anti-rollback authority"]},
    "S0-034-09": {"require": [r"server is the \*\*authoritative\*\* source", r"freshness/anti-rollback of published key material",
                              r"No client-local mechanism may claim these roles", r"`SERVER_BREAKER_S15` authority entry"]},
    "S0-034-10": {"require": [r"No physical test is executed by this freeze", r"`PHYSICAL_P1…P17 = NOT_EXECUTED`"]},
    # MSC-020 epoch
    "S0-020-01": {"require": [r"\*\*monotonic\*\* integer `publication_epoch`", r"incremented \*\*only by the server\*\*",
                              r"crypto\.identity_public_keys\.publication_epoch", r"same transaction"],
                  "forbid": [r"(?i)client (increments|MAY increment)"]},
    "S0-020-02": {"require": [r"\*\*When it changes:\*\*", r"every accepted OTK batch publication", r"does \*\*not\*\* increment it"]},
    "S0-020-03": {"require": [r"\*\*How the client receives it:\*\*", r"`publication_epoch`", r"`GET /v1/account/status`",
                              r"only \*\*after\*\* the server ACK"]},
    "S0-020-04": {"require": [r"\*\*Local binding:\*\*", r"AAD", r"magic ‖ version ‖ object_type ‖ context ‖ epoch", r"\*\*stale\*\*"]},
    "S0-020-05": {"require": [r"\*\*Stale re-publication:\*\*", r"`expected_epoch`", r"stale_publication_epoch", r"`PERMANENT`",
                              r"MUST reconcile", r"rolled back \(restore\)", r"never silent acceptance"],
                  "forbid": [r"(?i)MAY (accept|ignore) (the )?stale"]},
    "S0-020-06": {"require": [r"\*\*Behaviour on client rollback:\*\*", r"MUST NOT use or re-publish OTKs", r"S15 breaker for AC-005"]},
    "S0-020-07": {"require": [r"No anti-rollback code is created by this freeze", r"`identity_revision` remains `1`"]},
    # MSC-042 hardware trust
    "S0-042-01": {"require": [r"does \*\*NOT\*\* require remote hardware attestation", r"No attestation backend"],
                  "forbid": [r"(?i)V1 requires remote hardware attestation", r"(?i)attestation backend is (introduced|created)"]},
    "S0-042-02": {"require": [r"\*\*Identity derives from validated key material only:\*\*",
                              r"client-reported hardware level is \*\*never\*\* an input to authentication, authorization"]},
    "S0-042-03": {"require": [r"stores it as \*\*informational\*\*", r"MUST NOT treat it as a fact about the key",
                              r"MUST NOT reject or privilege a registration based on it",
                              r"Self-reported StrongBox is not a server authorization fact"],
                  "forbid": [r"(?i)self-reported StrongBox is (a|an) (server )?authorization fact",
                             r"(?i)StrongBox (is|MAY be) trusted (as|for) (an )?authoriz"]},
    "S0-042-04": {"require": [r"StrongBox \*\*preferred\*\*", r"TEE \*\*acceptable\*\* in production", r"`SOFTWARE` fails production registration \*\*client-side\*\*",
                              r"pre-existing bound alias is never deleted"]},
    "S0-042-05": {"require": [r"\*\*Residual risk \(accepted, documented\):\*\*", r"confined to the attacker's own account/device",
                              r"AC-003 remains broken at S7", r"`PHYSICAL_P1`"]},
    # preserved decisions
    "S0-017-01": {"require": [r"`ROOT-013` canonical severity is `MEDIUM`", r"remains `OPEN`", r"does not alter its severity"],
                  "forbid": [r"(?i)severity is `?(LOW|HIGH|CRITICAL)`?", r"(?i)ROOT-013.*(CLOSED|remediated by S0)"]},
    "S0-017-02": {"require": [r"`ROOT-016` remains `REJECTED_NOT_A_FINDING`", r"\*\*DO NOT REVIVE\*\*", r"`MSC-UNIT-029`"],
                  "forbid": [r"(?i)ROOT-016 (is|has been|becomes) (revived|reopened|a finding|an? (active|open) finding)",
                             r"(?i)revived as a finding"]},
    "S0-017-03": {"require": [r"`ANOX-SECURITY-ARCH-010` remains `OPEN` / `INFO`", r"`RETIRE_AT_B004_START`", r"\*\*not\*\* retired by S0",
                              r"B004 has not started"],
                  "forbid": [r"(?i)is retired (by S0|immediately|effective immediately|now)", r"(?i)ARCH-010`? (is|has been) `?RETIRED",
                             r"`RETIRED`"]},
    "S0-017-04": {"require": [r"`MSC-UNIT-039`", r"not reopened"]},
}

SCHEMA_NOT_FROZEN_RE = re.compile(r"schema is (\*\*)?not (\*\*)?frozen|schema is NOT frozen|not yet frozen\b(?!.*superseded)", re.IGNORECASE)


def fail(msg, errors):
    errors.append(msg)
    print(f"  FAIL {msg}")


def ok(msg):
    print(f"  OK   {msg}")


def read_text(rel):
    p = REPO_ROOT / rel
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def load_json(rel):
    p = REPO_ROOT / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_jsonl(rel):
    p = REPO_ROOT / rel
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def expand_clause_refs(text):
    """Expand `[S0-027-01]–[S0-027-08]` ranges and single refs to a set of IDs."""
    ids = set()
    for a, b in CLAUSE_REF_RE.findall(text):
        if not b:
            ids.add(a)
            continue
        pa, pb = a.rsplit("-", 1), b.rsplit("-", 1)
        if pa[0] != pb[0]:
            ids.update({a, b})
            continue
        lo, hi = int(pa[1]), int(pb[1])
        for n in range(min(lo, hi), max(lo, hi) + 1):
            ids.add(f"{pa[0]}-{n:02d}")
    return ids


class Amendment:
    """Structural parse of the V1.4 amendment: headings, clauses, sections."""

    def __init__(self, text):
        self.text = text
        self.lines = text.splitlines()
        self.headings = []  # (line_no, heading_text)
        self.clauses = {}   # id -> (line_no, clause_text)
        self.duplicates = []
        for i, line in enumerate(self.lines):
            m = HEADING_RE.match(line)
            if m:
                self.headings.append((i, m.group(1).strip()))
            for cm in CLAUSE_RE.finditer(line):
                cid = cm.group(1)
                if cid in self.clauses:
                    self.duplicates.append(cid)
                    continue
                self.clauses[cid] = (i, line[cm.end():].strip())

    def section_of(self, line_no):
        current = None
        for h_line, h_text in self.headings:
            if h_line <= line_no:
                current = h_text
            else:
                break
        return current

    def heading_lines(self, prefix):
        return [h for h in self.headings if ("## " + h[1]).startswith(prefix)]

    def section_text(self, prefix):
        hits = self.heading_lines(prefix)
        if len(hits) != 1:
            return None
        start = hits[0][0]
        end = len(self.lines)
        for h_line, _ in self.headings:
            if h_line > start:
                end = h_line
                break
        return "\n".join(self.lines[start:end])

    def table_row(self, first_cell):
        for line in self.lines:
            if line.startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if cells and cells[0] == first_cell:
                    return cells
        return None


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------

def check_manifest(errors):
    print("[S0-CONTRACT] Manifest")
    man = load_json(MANIFEST_PATH)
    if not isinstance(man, dict):
        fail(f"{MANIFEST_PATH} missing or not valid JSON", errors)
        return None
    if man.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        fail(f"manifest schema_version {man.get('schema_version')!r} != {EXPECTED_SCHEMA_VERSION}", errors)
    if man.get("contract_version") != EXPECTED_CONTRACT_VERSION:
        fail(f"manifest contract_version {man.get('contract_version')!r} != {EXPECTED_CONTRACT_VERSION}", errors)
    if man.get("authority_document") != AMENDMENT_PATH:
        fail("manifest authority_document must point at the V1.4 amendment", errors)
    for key in ("contracts", "server_contract_authority", "client_contract_authority", "server_breaker_authority",
                "attackchain_contract_coverage", "preserved_decisions", "msc_stage_proposals", "lifecycle",
                "schema_authority_home_marker", "schema_deference_marker", "schema_deferring_documents",
                "freeze_registry_rows_referencing_v1_4", "framework_clauses"):
        if key not in man:
            fail(f"manifest missing key {key}", errors)
    if errors:
        return man
    ok(f"manifest {EXPECTED_SCHEMA_VERSION} / {EXPECTED_CONTRACT_VERSION}")
    return man


def check_document(man, errors):
    print("\n[S0-CONTRACT] Amendment document structure")
    text = read_text(AMENDMENT_PATH)
    if text is None:
        fail(f"{AMENDMENT_PATH} missing", errors)
        return None
    doc = Amendment(text)
    if not re.search(r"^\*\*Status:\*\* FROZEN / CURRENT", text, re.MULTILINE):
        fail("amendment status must be FROZEN / CURRENT", errors)
    if EXPECTED_CONTRACT_VERSION not in text:
        fail(f"amendment must declare contract version {EXPECTED_CONTRACT_VERSION}", errors)
    if doc.duplicates:
        fail(f"duplicate clause identifiers: {sorted(set(doc.duplicates))}", errors)
    if re.search(r"^\s*(CREATE|ALTER|DROP)\s+(TABLE|INDEX|SCHEMA|POLICY)\b", text, re.MULTILINE | re.IGNORECASE):
        fail("amendment contains SQL DDL — S0 is contract-only (no schema SQL)", errors)

    registered = set(man.get("framework_clauses") or [])
    contracts = man.get("contracts") or []
    for c in contracts:
        registered.update(c.get("clauses") or [])
    present = set(doc.clauses)
    missing = sorted(registered - present)
    orphan = sorted(present - registered)
    if missing:
        fail(f"registered clauses missing from amendment: {missing}", errors)
    if orphan:
        fail(f"amendment clauses not registered in manifest: {orphan}", errors)

    for c in contracts:
        heading = c.get("heading", "")
        hits = doc.heading_lines(heading)
        if len(hits) != 1:
            fail(f"{c.get('contract_id')} heading {heading!r} must appear exactly once (found {len(hits)})", errors)
            continue
        for cid in c.get("clauses") or []:
            if cid not in doc.clauses:
                continue
            sec = doc.section_of(doc.clauses[cid][0])
            if sec is None or not ("## " + sec).startswith(heading):
                fail(f"clause {cid} is not under its contract heading {heading!r} (found under {sec!r})", errors)
        if not c.get("msc_unit", "").startswith("MSC_UNIT_"):
            fail(f"{c.get('contract_id')} must name its MSC unit", errors)
    if not errors:
        ok(f"{len(present)} clauses registered, {len(contracts)} contracts, {len(doc.headings)} sections; no orphans/duplicates")
    return doc


def check_core_invariants(doc, errors):
    print("\n[S0-CONTRACT] Core security invariants (per clause)")
    before = len(errors)
    for cid, spec in CORE_INVARIANTS.items():
        if cid not in doc.clauses:
            fail(f"core clause {cid} missing", errors)
            continue
        ctext = doc.clauses[cid][1]
        for pat in spec.get("require", []):
            if not re.search(pat, ctext):
                fail(f"{cid} lost required invariant text /{pat}/", errors)
        for pat in spec.get("forbid", []):
            if re.search(pat, ctext):
                fail(f"{cid} contains forbidden weakening text /{pat}/", errors)
    if len(errors) == before:
        ok(f"{len(CORE_INVARIANTS)} core clauses carry their invariants")


def check_domain_matrix(doc, errors):
    print("\n[S0-CONTRACT] Wipe / revocation domain matrix")
    before = len(errors)
    header = doc.table_row("Domain")
    if header is None or header[1:7] != ["logout", "local wipe", "account deletion", "explicit reset", "device revocation", "license expiry"]:
        fail("domain matrix header must enumerate logout | local wipe | account deletion | explicit reset | device revocation | license expiry", errors)
    row = doc.table_row("Server `devices` row")
    if row is None or len(row) < 7:
        fail("domain matrix must contain the `Server devices row` line", errors)
    else:
        if not row[1].startswith("R"):
            fail("logout must retain the server device (logout keeps key)", errors)
        if not row[2].startswith("V") or not row[3].startswith("V") or not row[5].startswith("V"):
            fail("local wipe / account deletion / device revocation must revoke the server device (S18)", errors)
    dev = doc.table_row("Device Auth alias `anox.deviceauth.p256.v1`")
    if dev is None or len(dev) < 7 or not dev[1].startswith("R") or not dev[2].startswith("D") or not dev[3].startswith("D") or not dev[4].startswith("D"):
        fail("Device Auth alias row must be R (logout) / D (wipe, deletion, reset)", errors)
    marker = doc.table_row("Binding marker `anox_deviceauth_binding.state`")
    if marker is None or len(marker) < 7 or not all(marker[i].startswith("D (last)") for i in (2, 3, 4)):
        fail("binding marker must be deleted last in wipe / deletion / reset", errors)
    if len(errors) == before:
        ok("domain matrix: logout retains, wipe/deletion/revocation revoke server device, marker last")


def check_contract_maps(man, doc, errors):
    print("\n[S0-CONTRACT] SC / CC / server-breaker / attackchain authority maps")
    before = len(errors)
    known = set(doc.clauses)

    sc = man.get("server_contract_authority") or {}
    for sid in SC_IDS:
        entry = sc.get(sid)
        if not isinstance(entry, dict):
            fail(f"{sid} has no authority home in manifest", errors)
            continue
        cl = entry.get("clauses") or []
        if not cl and not entry.get("retained_base"):
            fail(f"{sid} authority home is empty (ambiguous)", errors)
        bad = [c for c in cl if c not in known]
        if bad:
            fail(f"{sid} references unknown clauses {bad}", errors)
        row = doc.table_row(sid)
        if row is None:
            fail(f"{sid} row missing from §13 authority map", errors)
        else:
            refs = expand_clause_refs(row[2] if len(row) > 2 else "")
            if cl and not (refs & set(cl)):
                fail(f"{sid} §13 row does not reference its manifest clauses", errors)
            if any(r not in known for r in refs):
                fail(f"{sid} §13 row references unknown clauses {sorted(r for r in refs if r not in known)}", errors)
    extra = sorted(set(sc) - set(SC_IDS))
    if extra:
        fail(f"unexpected server contract ids {extra}", errors)

    cc = man.get("client_contract_authority") or {}
    for cid in CC_IDS:
        entry = cc.get(cid)
        if not isinstance(entry, dict) or not entry.get("owner"):
            fail(f"{cid} authority owner unknown", errors)
            continue
        bad = [c for c in (entry.get("clauses") or []) if c not in known]
        if bad:
            fail(f"{cid} references unknown clauses {bad}", errors)
        if not entry.get("sessions"):
            fail(f"{cid} has no implementing session", errors)
        row = doc.table_row(cid)
        if row is None or len(row) < 4 or not row[2].strip():
            fail(f"{cid} row missing/empty in §14 authority map", errors)
        else:
            refs = expand_clause_refs(row[2])
            if any(r not in known for r in refs):
                fail(f"{cid} §14 row references unknown clauses", errors)

    sb = man.get("server_breaker_authority") or {}
    for bid in BREAKER_IDS:
        entry = sb.get(bid)
        if not isinstance(entry, dict):
            fail(f"SERVER_BREAKER_{bid} has no authority entry", errors)
            continue
        status = entry.get("status")
        cl = entry.get("clauses") or []
        if status not in BREAKER_STATUSES:
            fail(f"SERVER_BREAKER_{bid} status {status!r} not in {sorted(BREAKER_STATUSES)}", errors)
        if status == "FROZEN_IN_AUTHORITY" and not cl:
            fail(f"SERVER_BREAKER_{bid} FROZEN_IN_AUTHORITY without clauses", errors)
        if status == "RETAINED_V1_2" and not cl and not entry.get("retained_base"):
            fail(f"SERVER_BREAKER_{bid} RETAINED_V1_2 without retained_base", errors)
        bad = [c for c in cl if c not in known]
        if bad:
            fail(f"SERVER_BREAKER_{bid} references unknown clauses {bad}", errors)
        row = doc.table_row(bid)
        if row is None or len(row) < 4:
            fail(f"{bid} row missing from §15 breaker map", errors)
        else:
            if status and status not in row[3]:
                fail(f"{bid} §15 row status {row[3]!r} != manifest {status}", errors)
            refs = expand_clause_refs(row[2])
            if cl and not (refs & set(cl)):
                fail(f"{bid} §15 row does not reference its manifest clauses", errors)
    # S15 must be carried by both 034 and 020
    s15 = set((sb.get("S15") or {}).get("clauses") or [])
    if not ({"S0-034-09"} & s15) or not any(c.startswith("S0-020-") for c in s15):
        fail("SERVER_BREAKER_S15 must be anchored in both the MSC-034 entry (S0-034-09) and the MSC-020 epoch contract", errors)

    ac = man.get("attackchain_contract_coverage") or {}
    for chain in REQUIRED_CHAINS:
        entry = ac.get(chain)
        if not isinstance(entry, dict) or not entry.get("breakers") or not entry.get("clauses"):
            fail(f"{chain} contract coverage missing", errors)
            continue
        bad = [c for c in entry["clauses"] if c not in known]
        if bad:
            fail(f"{chain} references unknown clauses {bad}", errors)
    if (ac.get("AC-001") or {}).get("rule") != "uniqueness_alone_not_accepted" or not ({"S1", "C1"} <= set((ac.get("AC-001") or {}).get("breakers") or [])):
        fail("AC-001 must retain client resolver (C1) + server binding (S1) — uniqueness alone not accepted", errors)
    if (ac.get("AC-003") or {}).get("rule") != "ath_alone_insufficient" or "S7" not in ((ac.get("AC-003") or {}).get("breakers") or []):
        fail("AC-003 must keep mandatory JKT binding (S7) as the single point; ath alone insufficient", errors)
    if (ac.get("AC-010") or {}).get("rule") != "pop_tied_to_deviceauth_identity" or "S5" not in ((ac.get("AC-010") or {}).get("breakers") or []):
        fail("AC-010 must keep the registration PoP tied to the DeviceAuth identity (S5)", errors)
    if len(errors) == before:
        ok("SC 14/14 · CC 14/14 · SERVER_BREAKER 18/18 · attackchain contract coverage 9/9; ambiguities 0")


def check_authority_index(man, errors):
    print("\n[S0-CONTRACT] Authority index precedence")
    before = len(errors)
    text = read_text(AUTHORITY_INDEX_PATH)
    if text is None:
        fail(f"{AUTHORITY_INDEX_PATH} missing", errors)
        return
    numbered = [(int(m.group(1)), m.group(2)) for m in re.finditer(r"^(\d+)\. (.+)$", text, re.MULTILINE)]
    pos = {}
    for n, body in numbered:
        if f"`{THIS_AMENDMENT}`" in body and "V1_4" not in pos:
            pos["V1_4"] = n
        if f"`{PRIOR_AMENDMENT}`" in body and "V1_3" not in pos:
            pos["V1_3"] = n
        if SNAPSHOT_ENTRY in body and "TRACK_B" not in pos:
            pos["TRACK_B"] = n
    if "V1_4" not in pos:
        fail(f"{THIS_AMENDMENT} not listed in AUTHORITY_INDEX precedence", errors)
    elif "V1_3" not in pos or "TRACK_B" not in pos:
        fail("AUTHORITY_INDEX precedence list must contain V1_3 and the TRACK_B snapshot entry", errors)
    elif not (pos["V1_3"] < pos["V1_4"] < pos["TRACK_B"]):
        fail(f"{THIS_AMENDMENT} must rank immediately below V1_3 and above the TRACK_B snapshot (got V1_3={pos['V1_3']}, V1_4={pos['V1_4']}, TRACK_B={pos['TRACK_B']})", errors)
    elif pos["V1_4"] != pos["V1_3"] + 1:
        fail("V1_4 must directly follow V1_3 in precedence (no equal-precedence gap)", errors)
    if "### Schema authority (single source of truth)" not in text or "exactly one authority home" not in text:
        fail("AUTHORITY_INDEX must declare the single schema authority home", errors)
    if "CANONICAL CONTRACT AMBIGUITIES = 0" not in text:
        fail("AUTHORITY_INDEX must record CANONICAL CONTRACT AMBIGUITIES = 0", errors)
    if not re.search(r"^\| `" + re.escape(THIS_AMENDMENT) + r"` \|", text, re.MULTILINE):
        fail("AUTHORITY_INDEX contents table must list the V1.4 amendment", errors)
    if "contracts/S0_CONTRACT_FREEZE_MANIFEST.json" not in text:
        fail("AUTHORITY_INDEX must reference the S0 contract manifest", errors)
    if len(errors) == before:
        ok(f"V1_4 ranks {pos.get('V1_4')} (directly after V1_3, above snapshot); schema authority home declared")


def check_freeze_registry(man, errors):
    print("\n[S0-CONTRACT] Freeze registry")
    before = len(errors)
    text = read_text(FREEZE_REGISTRY_PATH)
    if text is None:
        fail(f"{FREEZE_REGISTRY_PATH} missing", errors)
        return
    declared = list(man.get("freeze_registry_rows_referencing_v1_4") or [])
    dropped = [b for b in FREEZE_REGISTRY_BASE_POINTERS if b not in declared]
    if dropped:
        fail(f"manifest freeze_registry_rows_referencing_v1_4 omits amended row(s) {dropped}", errors)
    for bid in sorted(set(declared) | set(FREEZE_REGISTRY_BASE_POINTERS)):
        m = re.search(r"^\| " + re.escape(bid) + r" \|.*$", text, re.MULTILINE)
        if m is None:
            fail(f"freeze registry row {bid} missing", errors)
            continue
        row = m.group(0)
        if THIS_AMENDMENT not in row:
            fail(f"freeze registry row {bid} does not reference {THIS_AMENDMENT}", errors)
        # F-10: an amended row must keep BOTH its base pointer and the S0 amendment pointer.
        base_ptr = FREEZE_REGISTRY_BASE_POINTERS.get(bid)
        if base_ptr and base_ptr not in row:
            fail(f"freeze registry row {bid} lost its base-document pointer {base_ptr!r} — "
                 f"amended rows must record base + S0 amendments", errors)
    m5 = re.search(r"^\| B-005 \|.*$", text, re.MULTILINE)
    if m5 and "DB-SCHEMA-V1-FROZEN" not in m5.group(0):
        fail("freeze registry B-005 row must name DB-SCHEMA-V1-FROZEN single authority home", errors)
    if len(errors) == before:
        ok(f"freeze registry rows {sorted(FREEZE_REGISTRY_BASE_POINTERS)} reference V1.4 and keep base pointers")


def check_schema_authority(man, errors):
    print("\n[S0-CONTRACT] Schema authority single source of truth (MSC-040)")
    before = len(errors)
    # F-04: markers and the deferring-document set are validator-owned. The manifest
    # may only *agree*; it can never shrink the enforced set.
    home_marker = REQUIRED_SCHEMA_HOME_MARKER
    defer_marker = REQUIRED_SCHEMA_DEFERENCE_MARKER
    if man.get("schema_authority_home_marker") != home_marker:
        fail(f"manifest schema_authority_home_marker must be {home_marker!r}", errors)
    if man.get("schema_deference_marker") != defer_marker:
        fail(f"manifest schema_deference_marker must be {defer_marker!r}", errors)
    declared = list(man.get("schema_deferring_documents") or [])
    dropped = [r for r in REQUIRED_DEFERRING_DOCUMENTS if r not in declared]
    if dropped:
        fail(f"manifest schema_deferring_documents omits required deference document(s) {dropped} — "
             f"the deference set is validator-owned and may not be narrowed", errors)
    homes = []
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        for p in sorted(docs_dir.rglob("*.md")):
            try:
                if home_marker in p.read_text(encoding="utf-8", errors="replace"):
                    homes.append(p.relative_to(REPO_ROOT).as_posix())
            except OSError:
                continue
    if homes != [AMENDMENT_PATH]:
        fail(f"exactly one schema authority home marker expected in {AMENDMENT_PATH}; found {homes}", errors)
    # Enforce over the union of validator-required and manifest-declared documents.
    for rel in sorted(set(REQUIRED_DEFERRING_DOCUMENTS) | set(declared)):
        t = read_text(rel)
        if t is None:
            fail(f"deferring document {rel} missing", errors)
            continue
        if defer_marker not in t:
            fail(f"{rel} lacks deference marker {defer_marker!r}", errors)
        for line in t.splitlines():
            if SCHEMA_NOT_FROZEN_RE.search(line) and "superseded" not in line.lower():
                fail(f"{rel} still asserts the schema is not frozen (competing authority): {line.strip()[:80]!r}", errors)
                break
    if len(errors) == before:
        ok(f"single schema authority home; {len(REQUIRED_DEFERRING_DOCUMENTS)} required deferring document(s) "
           f"defer and no longer claim 'not frozen'")


def check_mapping_anchors(man, doc, errors):
    """F-05 — pin security-critical mappings against validator-owned anchors so a
    coherent manifest+document remap cannot re-point a rule at an unrelated clause."""
    print("\n[S0-CONTRACT] Independent mapping anchors (F-05)")
    before = len(errors)

    sc = man.get("server_contract_authority") or {}
    for sid, anchors in SC_ANCHOR_CLAUSES.items():
        got = set((sc.get(sid) or {}).get("clauses") or [])
        missing = sorted(anchors - got)
        if missing:
            fail(f"{sid} authority home lost its anchor clause(s) {missing} "
                 f"(expected superset of {sorted(anchors)}, got {sorted(got)})", errors)
        row = doc.table_row(sid)
        if row is not None and len(row) > 2:
            refs = expand_clause_refs(row[2])
            row_missing = sorted(anchors - refs)
            if row_missing:
                fail(f"{sid} §13 row lost its anchor clause(s) {row_missing}", errors)

    cc = man.get("client_contract_authority") or {}
    for cid, anchors in CC_ANCHOR_CLAUSES.items():
        got = set((cc.get(cid) or {}).get("clauses") or [])
        missing = sorted(anchors - got)
        if missing:
            fail(f"{cid} authority owner lost its anchor clause(s) {missing}", errors)

    sb = man.get("server_breaker_authority") or {}
    for bid, anchors in BREAKER_ANCHOR_CLAUSES.items():
        got = set((sb.get(bid) or {}).get("clauses") or [])
        missing = sorted(anchors - got)
        if missing:
            fail(f"SERVER_BREAKER_{bid} lost its anchor clause(s) {missing}", errors)
    for bid in BREAKER_RETAINED_ONLY:
        entry = sb.get(bid) or {}
        if entry.get("clauses"):
            fail(f"SERVER_BREAKER_{bid} must stay RETAINED_V1_2 with no V1.4 clause of its own", errors)
        if not entry.get("retained_base"):
            fail(f"SERVER_BREAKER_{bid} must name its retained V1.2 base", errors)
    for bid, want in BREAKER_EXPECTED_STATUS.items():
        got = (sb.get(bid) or {}).get("status")
        if got != want:
            fail(f"SERVER_BREAKER_{bid} status {got!r} != frozen expectation {want!r}", errors)

    ac = man.get("attackchain_contract_coverage") or {}
    for chain, spec in AC_ANCHORS.items():
        entry = ac.get(chain) or {}
        breakers = set(entry.get("breakers") or [])
        missing_b = sorted(spec["breakers"] - breakers)
        if missing_b:
            fail(f"{chain} lost required breaker(s) {missing_b} (got {sorted(breakers)})", errors)
        clauses = set(entry.get("clauses") or [])
        missing_c = sorted(spec["clauses"] - clauses)
        if missing_c:
            fail(f"{chain} lost required anchor clause(s) {missing_c}", errors)
        if spec["rule"] is not None and entry.get("rule") != spec["rule"]:
            fail(f"{chain} rule {entry.get('rule')!r} != required {spec['rule']!r}", errors)

    if len(errors) == before:
        ok(f"mapping anchors hold: SC {len(SC_ANCHOR_CLAUSES)} · CC {len(CC_ANCHOR_CLAUSES)} · "
           f"breakers {len(BREAKER_ANCHOR_CLAUSES)}+{len(BREAKER_RETAINED_ONLY)} · chains {len(AC_ANCHORS)}")


def check_unit_roles(man, doc, errors):
    """F-07 — MSC-022 is a supporting contract entry, never a primary S0 unit and
    never lifecycle-advanced."""
    print("\n[S0-CONTRACT] MSC unit roles (F-07)")
    before = len(errors)
    contracts = man.get("contracts") or []
    roles = {c.get("msc_unit"): c.get("s0_role") for c in contracts}
    for unit in sorted(PRIMARY_S0_MSC_UNITS):
        if roles.get(unit) != "PRIMARY_CONTRACT_UNIT":
            fail(f"{unit} must carry s0_role=PRIMARY_CONTRACT_UNIT, got {roles.get(unit)!r}", errors)
    for unit in sorted(SUPPORTING_S0_MSC_UNITS):
        if roles.get(unit) != "SUPPORTING_CONTRACT_ENTRY":
            fail(f"{unit} must carry s0_role=SUPPORTING_CONTRACT_ENTRY, got {roles.get(unit)!r}", errors)
    for unit in sorted(CONSUMED_S0_MSC_UNITS):
        if roles.get(unit) != "CONSUMED_DECISION_RECORD":
            fail(f"{unit} must carry s0_role=CONSUMED_DECISION_RECORD, got {roles.get(unit)!r}", errors)
    units = ((man.get("msc_stage_proposals") or {}).get("units") or {})
    for unit in sorted(SUPPORTING_S0_MSC_UNITS | CONSUMED_S0_MSC_UNITS):
        if unit in units:
            fail(f"{unit} must NOT appear in msc_stage_proposals (supporting/consumed units do not advance)", errors)
    if set(units) != PRIMARY_S0_MSC_UNITS:
        fail(f"msc_stage_proposals units {sorted(units)} != the 11 primary S0 units", errors)
    # the amendment must state the primary/supporting distinction, not "no other unit is touched"
    scope_clause = doc.clauses.get("S0-000-02", (0, ""))[1]
    if not re.search(r"11 \*\*primary\*\* S0 contract units", scope_clause):
        fail("[S0-000-02] must declare the 11 **primary** S0 contract units", errors)
    if not re.search(r"MSC-UNIT-022", scope_clause):
        fail("[S0-000-02] must name MSC-UNIT-022 as the supporting contract entry", errors)
    if re.search(r"No other MSC unit is touched", scope_clause):
        fail("[S0-000-02] still claims 'No other MSC unit is touched' while MSC-022 carries a "
             "supporting contract entry (F-07)", errors)
    if len(errors) == before:
        ok(f"{len(PRIMARY_S0_MSC_UNITS)} primary units staged · MSC-022 supporting (not staged) · MSC-039 consumed")


def check_cc_authority_homes(man, errors):
    """F-08 — no CC rule may name consolidation/gate evidence as its normative home."""
    print("\n[S0-CONTRACT] Client-contract authority homes (F-08)")
    before = len(errors)
    cc = man.get("client_contract_authority") or {}
    for cid in CC_IDS:
        entry = cc.get(cid) or {}
        owner = str(entry.get("owner", ""))
        for bad in NON_AUTHORITY_EVIDENCE_SOURCES:
            if bad in owner:
                fail(f"{cid} names non-authority evidence {bad!r} as its normative owner — "
                     f"the Master consolidation is traceability, not an AUTHORITY_INDEX document", errors)
        if not entry.get("authority_home"):
            fail(f"{cid} must name an authority_home (AUTHORITY_INDEX-indexed normative document)", errors)
        trace = entry.get("traceability")
        if trace is not None and not isinstance(trace, list):
            fail(f"{cid} traceability must be a list of evidence references", errors)
    if len(errors) == before:
        ok(f"CC 14/14 normative homes are authority-indexed; consolidation kept as traceability only")


def check_internal_references(doc, errors):
    """F-09 — every §n.m reference in the amendment must resolve to a real subsection."""
    print("\n[S0-CONTRACT] Internal cross-references (F-09)")
    before = len(errors)
    subsections = set()
    for line in doc.lines:
        m = re.match(r"^### (\d+)\.(\d+)\b", line)
        if m:
            subsections.add((m.group(1), m.group(2)))
    dangling = {}
    for i, line in enumerate(doc.lines):
        for maj, minor in SECTION_REF_RE.findall(line):
            if (maj, minor) not in subsections:
                dangling.setdefault(f"§{maj}.{minor}", []).append(i + 1)
    if dangling:
        fail(f"dangling internal section reference(s): "
             f"{ {k: v[:4] for k, v in sorted(dangling.items())} }", errors)
    if len(errors) == before:
        ok(f"DANGLING_INTERNAL_REFERENCES = 0 ({len(subsections)} subsections resolved)")


def check_preserved_decisions(man, doc, errors):
    print("\n[S0-CONTRACT] Preserved governance decisions")
    before = len(errors)
    pd = man.get("preserved_decisions") or {}
    r13 = pd.get("ROOT-013") or {}
    if r13.get("severity") != "MEDIUM" or r13.get("status") != "OPEN":
        fail("manifest must record ROOT-013 MEDIUM / OPEN", errors)
    if (pd.get("ROOT-016") or {}).get("status") != "REJECTED_NOT_A_FINDING":
        fail("manifest must record ROOT-016 REJECTED_NOT_A_FINDING", errors)
    a10 = pd.get("ANOX-SECURITY-ARCH-010") or {}
    if a10.get("status") != "Open" or a10.get("severity") != "INFO" or a10.get("trigger") != "RETIRE_AT_B004_START":
        fail("manifest must record ARCH-010 Open / INFO / RETIRE_AT_B004_START", errors)
    for key, entry in pd.items():
        cl = entry.get("clause")
        if cl not in doc.clauses:
            fail(f"preserved decision {key} clause {cl} missing from amendment", errors)
    findings = load_jsonl(FINDINGS_PATH)
    if findings:
        f10 = next((f for f in findings if f.get("finding_id") == "ANOX-SECURITY-ARCH-010"), None)
        if f10 is None:
            fail("ANOX-SECURITY-ARCH-010 missing from findings.jsonl", errors)
        else:
            if f10.get("status") != "Open" or f10.get("severity") != "INFO":
                fail(f"ANOX-SECURITY-ARCH-010 must remain Open/INFO, got {f10.get('status')}/{f10.get('severity')}", errors)
            if "RETIRE_AT_B004_START" not in str(f10.get("notes", "")):
                fail("ANOX-SECURITY-ARCH-010 lost its RETIRE_AT_B004_START trigger note", errors)
    if len(errors) == before:
        ok("ROOT-013 MEDIUM/OPEN · ROOT-016 REJECTED not revived · ARCH-010 Open/INFO RETIRE_AT_B004_START · MSC-039 not reopened")


def check_no_implementation(man, errors):
    print("\n[S0-CONTRACT] No implementation / no closure claims")
    before = len(errors)
    lc = man.get("lifecycle") or {}
    for key, want in (("b004", "NOT_STARTED"), ("b005", "NOT_STARTED"), ("backend", "NOT_IMPLEMENTED"),
                      ("product_development", "BLOCKED_PENDING_FINAL_AUDIT"),
                      ("remediation_session_s0", "IMPLEMENTED_PENDING_INDEPENDENT_RETEST"),
                      ("security_remediation", "IN_PROGRESS")):
        if lc.get(key) != want:
            fail(f"manifest lifecycle {key}={lc.get(key)!r}, expected {want!r}", errors)
    st = man.get("msc_stage_proposals") or {}
    allowed = set(st.get("allowed_stages") or [])
    forbidden = set(st.get("forbidden_stages") or [])
    if not ({"CLOSED", "EVIDENCE_PRESERVED", "INDEPENDENTLY_RETESTED"} <= forbidden) or (allowed & forbidden):
        fail("msc_stage_proposals must forbid INDEPENDENTLY_RETESTED/EVIDENCE_PRESERVED/CLOSED", errors)
    units = st.get("units") or {}
    # Only the 11 PRIMARY S0 contract units may be staged. MSC-022 (supporting HTU
    # contract entry for MSC-026/S12) and MSC-039 (consumed decision record) never
    # advance — enforced against validator-owned sets, see check_unit_roles (F-07).
    if set(units) != PRIMARY_S0_MSC_UNITS:
        fail(f"msc_stage_proposals units {sorted(units)} != the 11 primary S0 contract units "
             f"{sorted(PRIMARY_S0_MSC_UNITS)}", errors)
    for uid, u in units.items():
        if u.get("stage") not in allowed or u.get("stage") in forbidden:
            fail(f"{uid} stage {u.get('stage')!r} not permitted for S0 (allowed {sorted(allowed)})", errors)
    if st.get("closed_by_s0") != 0 or st.get("open_msc_units") != 42:
        fail("closed_by_s0 must be 0 and open_msc_units 42", errors)
    ir = load_json(IMPL_READINESS_PATH)
    if isinstance(ir, dict):
        for dom in ("B-004", "B-005"):
            s = ((ir.get("domains") or {}).get(dom) or {}).get("implementation_state")
            if s != "NOT_STARTED":
                fail(f"implementation_readiness {dom} must remain NOT_STARTED, got {s!r}", errors)
    if len(errors) == before:
        ok("B004/B005 NOT_STARTED · backend NOT_IMPLEMENTED · CLOSED_BY_S0=0 · 42 open · stages ≤ AUTOMATED_TESTED")


def _f01_ratification(errors):
    """Locate and validate the Human F-01 file-ownership ratification record (F-03).

    Returns the record on success, else None.  The record is the *only* thing that
    may admit a change to a PROTECTED_SHARED_GOVERNANCE_FILE, so every identifying
    field is checked and a blanket/forward-looking grant is rejected.
    """
    recs = load_jsonl(DECISIONS_PATH)
    rec = next((r for r in recs if r.get("decision_id") == F01_RATIFICATION_DECISION_ID), None)
    if rec is None:
        fail(f"F-01 ratification {F01_RATIFICATION_DECISION_ID} missing from {DECISIONS_PATH} — "
             f"a PROTECTED_SHARED_GOVERNANCE_FILE change requires an explicit Human ratification", errors)
        return None
    actor = str(rec.get("authority_actor", ""))
    if "Human Product & Security Owner" not in actor:
        fail(f"F-01 ratification authority_actor must be the Human Product & Security Owner, got {actor!r}", errors)
    if rec.get("ratified_task") != S0_TASK_ID:
        fail(f"F-01 ratification ratified_task must be {S0_TASK_ID}, got {rec.get('ratified_task')!r}", errors)
    files = rec.get("ratified_files") or []
    if list(files) != list(PROTECTED_SHARED_FILES):
        fail(f"F-01 ratification ratified_files must be exactly {sorted(PROTECTED_SHARED_FILES)}, got {files!r}", errors)
    if rec.get("scope") != "ONE_TIME_CHANGE_SPECIFIC":
        fail("F-01 ratification scope must be ONE_TIME_CHANGE_SPECIFIC", errors)
    for flag, want in (("grants_general_ownership", False), ("grants_s1_permission", False),
                       ("grants_future_sessions", False)):
        if rec.get(flag) is not False:
            fail(f"F-01 ratification must record {flag}=false (no blanket grant), got {rec.get(flag)!r}", errors)
    if rec.get("s1_prohibited_before_integration") is not True:
        fail("F-01 ratification must record s1_prohibited_before_integration=true", errors)
    digests = rec.get("ratified_sha256") or {}
    for rel, spec in PROTECTED_SHARED_FILES.items():
        if digests.get(rel) != spec["authorized_sha256"]:
            fail(f"F-01 ratification ratified_sha256[{rel}] must pin the ratified content "
                 f"{spec['authorized_sha256'][:16]}…, got {str(digests.get(rel))[:16]!r}", errors)
    if F01_RATIFICATION_REPORT not in str(rec.get("record_path", "")):
        fail(f"F-01 ratification must reference its canonical record {F01_RATIFICATION_REPORT}", errors)
    if read_text(F01_RATIFICATION_REPORT) is None:
        fail(f"F-01 ratification canonical record {F01_RATIFICATION_REPORT} missing", errors)
    return rec


def _preservation_ratification(errors):
    """Locate and validate the Human S0-preservation shared-validator ratification
    record.  Mirrors _f01_ratification; separate authority, same fail-closed
    pinning discipline (ONE_TIME_CHANGE_SPECIFIC, no blanket grants)."""
    recs = load_jsonl(DECISIONS_PATH)
    rec = next((r for r in recs if r.get("decision_id") == PRESERVATION_RATIFICATION_DECISION_ID), None)
    if rec is None:
        fail(f"S0 preservation ratification {PRESERVATION_RATIFICATION_DECISION_ID} missing from "
             f"{DECISIONS_PATH} — a PROTECTED_SHARED_GOVERNANCE_FILE change requires an explicit "
             f"Human ratification", errors)
        return None
    actor = str(rec.get("authority_actor", ""))
    if "Human Product & Security Owner" not in actor:
        fail(f"S0 preservation ratification authority_actor must be the Human Product & Security Owner, got {actor!r}", errors)
    if rec.get("ratified_task") != PRESERVATION_TASK_ID:
        fail(f"S0 preservation ratification ratified_task must be {PRESERVATION_TASK_ID}, got {rec.get('ratified_task')!r}", errors)
    files = rec.get("ratified_files") or []
    if list(files) != list(PROTECTED_SHARED_FILES):
        fail(f"S0 preservation ratification ratified_files must be exactly {sorted(PROTECTED_SHARED_FILES)}, got {files!r}", errors)
    if rec.get("ratified_change") != "S0_PRESERVATION_LIFECYCLE_EXTENSION":
        fail(f"S0 preservation ratification ratified_change must be S0_PRESERVATION_LIFECYCLE_EXTENSION, got {rec.get('ratified_change')!r}", errors)
    if rec.get("scope") != "ONE_TIME_CHANGE_SPECIFIC":
        fail("S0 preservation ratification scope must be ONE_TIME_CHANGE_SPECIFIC", errors)
    for flag in ("grants_general_ownership", "grants_s1_permission", "grants_future_sessions",
                 "grants_future_event_numbers", "grants_arbitrary_registry_growth"):
        if rec.get(flag) is not False:
            fail(f"S0 preservation ratification must record {flag}=false (no blanket grant), got {rec.get(flag)!r}", errors)
    if rec.get("s1_prohibited_before_integration") is not True:
        fail("S0 preservation ratification must record s1_prohibited_before_integration=true", errors)
    digests = rec.get("ratified_sha256") or {}
    for rel, spec in PROTECTED_SHARED_FILES.items():
        if digests.get(rel) != spec["preservation_authorized_sha256"]:
            fail(f"S0 preservation ratification ratified_sha256[{rel}] must pin the ratified content "
                 f"{spec['preservation_authorized_sha256'][:16]}…, got {str(digests.get(rel))[:16]!r}", errors)
    if PRESERVATION_RATIFICATION_REPORT not in str(rec.get("record_path", "")):
        fail(f"S0 preservation ratification must reference its canonical record {PRESERVATION_RATIFICATION_REPORT}", errors)
    if read_text(PRESERVATION_RATIFICATION_REPORT) is None:
        fail(f"S0 preservation ratification canonical record {PRESERVATION_RATIFICATION_REPORT} missing", errors)
    return rec


def _git_out(*args):
    """Run a read-only git command in REPO_ROOT; return stdout or None."""
    r = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _s1_ratification_transaction(errors):
    """Structural proof of the authorized four-path ratification transaction R1.

    Non-circular by construction: nothing here needs a future commit SHA. R1 is
    located as the newest first-parent commit that touches the protected central
    validator, and is then required to be
      * a single-parent commit,
      * changing EXACTLY S1_RATIFICATION_PATHS and nothing else,
      * producing exactly the pinned post-images for the three externally
        pinnable package files,
    with at most ONE further commit after it (the metadata synchronisation R2),
    which may not touch any POST_R1_FORBIDDEN_PREFIXES path. Anything else is a
    hard failure. Returns "R1", "R1R2" or None.
    """
    head = (_git_out("rev-parse", "HEAD") or "").strip()
    if not head:
        fail("S1 ratification: cannot resolve HEAD", errors)
        return None
    central = "tools/audit/validate_security_audit_evidence_preservation.py"
    # R1 is located by SIGNATURE, not by "newest commit touching the file":
    # the authorized CI-disposition transaction R3a legitimately changes the
    # protected validator again, so the newest toucher is not necessarily R1.
    # Scan newest-first; a commit that changes the protected validator without
    # matching either authorized signature is itself a hard failure.
    log = _git_out("log", "--first-parent", "--format=%H", "--", central)
    r1 = None
    for cand in (log or "").splitlines():
        changed_c = sorted(p for p in (_git_out("diff", "--name-only", f"{cand}~1", cand) or "").splitlines() if p.strip())
        if changed_c == sorted(S1_RATIFICATION_PATHS):
            r1 = cand
            break
        if changed_c == sorted(S1_CI_DISPOSITION_PATHS):
            continue
        fail(f"unauthorized commit {cand[:12]} changed protected shared validator {central} "
             f"(paths {changed_c} match neither the ratification nor the disposition signature)", errors)
        return None
    if r1 is None:
        fail("S1 ratification: no commit changing the protected central validator was found", errors)
        return None
    parents = (_git_out("rev-list", "--parents", "-n", "1", r1) or "").split()
    if len(parents) != 2:
        fail(f"S1 ratification commit R1 {r1[:12]} must be a single-parent commit", errors)
        return None
    changed = sorted(p for p in (_git_out("diff", "--name-only", f"{r1}~1", r1) or "").splitlines() if p.strip())
    if changed != sorted(S1_RATIFICATION_PATHS):
        fail(f"S1 ratification commit R1 {r1[:12]} must change exactly the four package paths "
             f"{sorted(S1_RATIFICATION_PATHS)}, changed {changed}", errors)
        return None
    for rel, want in sorted(S1_RATIFICATION_POST_IMAGES.items()):
        blob = subprocess.run(["git", "show", f"{r1}:{rel}"], cwd=REPO_ROOT, capture_output=True)
        if blob.returncode != 0:
            fail(f"S1 ratification: {rel} unreadable at R1 {r1[:12]}", errors)
            return None
        got = hashlib.sha256(blob.stdout).hexdigest()
        if got != want:
            fail(f"S1 ratification: {rel} at R1 is {got[:16]}… but the authorized transaction "
                 f"pins {want[:16]}…", errors)
            return None
    after = [c for c in (_git_out("rev-list", "--first-parent", "--reverse", f"{r1}..{head}") or "").splitlines() if c.strip()]
    if not after:
        return "R1"
    r2 = after[0]
    bad = sorted(p for p in (_git_out("diff", "--name-only", f"{r2}~1", r2) or "").splitlines()
                 if p.strip() and p.startswith(POST_R1_FORBIDDEN_PREFIXES))
    if bad:
        fail(f"S1 ratification: metadata commit R2 {r2[:12]} touches non-metadata paths: {bad}", errors)
        return None
    rest = after[1:]
    if not rest:
        return "R1R2"
    # Beyond R2 only the Human-authorized CI-infrastructure tail disposition
    # is admissible: exactly the pinned tail SHAs (ci.yml-only each), then the
    # disposition substantive R3a (exact path signature), then the metadata
    # synchronisation R3b. Position, order and SHA identity are all bound.
    n_tail = len(S1_CI_TAIL_SHAS)
    if len(rest) < n_tail or list(rest[:n_tail]) != list(S1_CI_TAIL_SHAS):
        fail(f"S1 ratification: commits following R2 {r2[:12]} do not equal the pinned "
             f"authorized CI tail (order, completeness and SHA identity are all bound): "
             f"{[c[:12] for c in rest]}", errors)
        return None
    for sha in S1_CI_TAIL_SHAS:
        extra = sorted(p for p in (_git_out("diff", "--name-only", f"{sha}~1", sha) or "").splitlines()
                       if p.strip() and p not in S1_CI_TAIL_ALLOWED_PATHS)
        if extra:
            fail(f"S1 ratification: authorized CI tail commit {sha[:12]} touches paths outside "
                 f"{sorted(S1_CI_TAIL_ALLOWED_PATHS)}: {extra}", errors)
            return None
    rest = rest[n_tail:]
    if not rest:
        return "R1R2_TAIL"
    if len(rest) != 2:
        fail(f"S1 ratification: {len(rest)} commits follow the authorized CI tail; only the "
             f"disposition pair [R3a substantive, R3b metadata] is authorized", errors)
        return None
    r3a, r3b = rest
    changed_r3a = sorted(p for p in (_git_out("diff", "--name-only", f"{r3a}~1", r3a) or "").splitlines() if p.strip())
    if changed_r3a != sorted(S1_CI_DISPOSITION_PATHS):
        fail(f"S1 ratification: disposition substantive R3a {r3a[:12]} must change exactly "
             f"{sorted(S1_CI_DISPOSITION_PATHS)}, changed {changed_r3a}", errors)
        return None
    bad = sorted(p for p in (_git_out("diff", "--name-only", f"{r3b}~1", r3b) or "").splitlines()
                 if p.strip() and p.startswith(POST_R1_FORBIDDEN_PREFIXES))
    if bad:
        fail(f"S1 ratification: disposition metadata commit R3b {r3b[:12]} touches "
             f"non-metadata paths: {bad}", errors)
        return None
    return "R1R2_DISPOSITION"


def _s1_integration_ratification(errors, require_record=False):
    """Validate the third authorized content of the protected central validator.

    Era-aware and fail-closed:
      * the three externally pinnable post-images must match exactly;
      * in a Git context the four-path transaction R1 must be proven
        structurally (see _s1_ratification_transaction), and nothing beyond the
        single metadata commit R2 may follow it;
      * the Human decision record is validated with the same discipline as F-01
        and the S0 preservation ratification WHENEVER IT IS PRESENT
        (ONE_TIME_CHANGE_SPECIFIC, is_human_authority, every grants_* false, every
        pinned digest exact) — present-but-weakened/widened/forged always fails.

    DISCLOSED RESIDUAL — read this before "hardening" it.
    The decision record is deliberately NOT mandatory inside the authorized tail.
    Making it mandatory re-creates the very defect this transaction exists to fix
    (retest S1-004, B-6), and that was observed in the committed simulation:
      * R1 is restricted to the four package paths, so it cannot touch registries;
      * R2 is restricted to metadata, and
        tools/continuity/validate_continuity.py::METADATA_ONLY_ALLOWLIST does NOT
        contain docs/workforce/registries/decisions.jsonl (it lists runs, tasks and
        findings only), so an R2 carrying the record fails continuity live;
      * nothing beyond R1/R2 is admitted here.
    The Human's ACT of ratification is the R1 commit itself, proven structurally;
    CURRENT_STATE.ratification_decision_id — which IS metadata-allowlisted and IS
    required at the R1+R2 stage by
    tools/audit/validate_s1_integration_evidence.py — carries the declared
    decision id inside the tail; and the full registry record is a later, separate
    governance commit outside this delivery's authority.
    In fixture mode (no Git) only content identity can be checked; that is the same
    limitation the scope gate already discloses.
    Returns True when the content is admitted, else False.
    """
    for rel, want in sorted(S1_RATIFICATION_POST_IMAGES.items()):
        p = REPO_ROOT / rel
        if not p.exists():
            fail(f"S1 ratification package file missing: {rel}", errors)
            return False
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != want:
            fail(f"S1 ratification package file {rel} is {got[:16]}… but the authorized "
                 f"transaction pins {want[:16]}… — the four-file package is not intact", errors)
            return False
    if read_text(S1_INTEGRATION_RATIFICATION_REPORT) is None:
        fail(f"S1 ratification canonical record {S1_INTEGRATION_RATIFICATION_REPORT} missing", errors)
        return False
    git_dir, why = _resolve_git_dir()
    stage = None
    if git_dir is None and why != "absent":
        fail(f"S1 ratification: Git metadata unusable ({why}) — the four-path transaction "
             f"cannot be proven and must not be assumed", errors)
        return False
    if git_dir is not None:
        stage = _s1_ratification_transaction(errors)
        if stage is None:
            return False
        if stage not in ("R1", "R1R2"):
            fail(f"S1 ratification: R1-era protected content is live but the chain carries "
                 f"post-R1 commits (stage {stage}) — the four-file package and the chain "
                 f"are different eras", errors)
            return False
    recs = load_jsonl(DECISIONS_PATH)
    rec = next((r for r in recs if r.get("decision_id") == S1_INTEGRATION_RATIFICATION_DECISION_ID), None)
    if rec is None:
        if require_record:
            fail(f"S1 ratification {S1_INTEGRATION_RATIFICATION_DECISION_ID} missing from "
                 f"{DECISIONS_PATH}", errors)
            return False
        print(f"  OK   S1 four-path ratification transaction proven structurally "
              f"({stage or 'content identity, fixture mode'}); the Human decision record is "
              f"validated in full whenever present (see the disclosed residual)")
        return True
    before = len(errors)
    actor = str(rec.get("authority_actor", ""))
    if "Human Product & Security Owner" not in actor:
        fail(f"S1 ratification authority_actor must be the Human Product & Security Owner, got {actor!r}", errors)
    if rec.get("ratified_change") != S1_INTEGRATION_RATIFIED_CHANGE:
        fail(f"S1 ratification ratified_change must be {S1_INTEGRATION_RATIFIED_CHANGE}, "
             f"got {rec.get('ratified_change')!r}", errors)
    if rec.get("ratified_task") != S1_INTEGRATION_TASK_ID:
        fail(f"S1 ratification ratified_task must be {S1_INTEGRATION_TASK_ID}, got {rec.get('ratified_task')!r}", errors)
    if rec.get("scope") != "ONE_TIME_CHANGE_SPECIFIC":
        fail("S1 ratification scope must be ONE_TIME_CHANGE_SPECIFIC", errors)
    if rec.get("is_human_authority") is not True:
        fail("S1 ratification must record is_human_authority=true", errors)
    for flag in ("grants_general_ownership", "grants_future_sessions", "grants_future_successor_contents",
                 "grants_future_correction_pairs", "grants_future_ratification_tails",
                 "grants_s2_s3_s4_authority", "grants_msc_closure", "grants_b004_b005_start"):
        if rec.get(flag) is not False:
            fail(f"S1 ratification must record {flag}=false (no blanket grant), got {rec.get(flag)!r}", errors)
    files = sorted(rec.get("ratified_files") or [])
    if files != sorted(S1_RATIFICATION_PATHS):
        fail(f"S1 ratification ratified_files must be exactly the four package paths "
             f"{sorted(S1_RATIFICATION_PATHS)}, got {files!r}", errors)
    digests = rec.get("ratified_sha256") or {}
    if sorted(digests) != sorted(S1_RATIFICATION_PATHS):
        fail(f"S1 ratification ratified_sha256 must pin exactly the four package paths, "
             f"got {sorted(digests)!r}", errors)
    for rel, want in sorted(S1_RATIFICATION_POST_IMAGES.items()):
        if digests.get(rel) != want:
            fail(f"S1 ratification ratified_sha256[{rel}] must pin {want[:16]}…, "
                 f"got {str(digests.get(rel))[:16]!r}", errors)
    # This file's own post-image is not self-pinnable; require the record to pin
    # the content that is actually live, which closes the gap externally.
    self_rel = "tools/audit/validate_s0_contract_freeze.py"
    self_live = hashlib.sha256((REPO_ROOT / self_rel).read_bytes()).hexdigest() if (REPO_ROOT / self_rel).exists() else None
    if digests.get(self_rel) != self_live:
        fail(f"S1 ratification ratified_sha256[{self_rel}] must pin the live S0 contract content "
             f"{str(self_live)[:16]}…, got {str(digests.get(self_rel))[:16]!r}", errors)
    if S1_INTEGRATION_RATIFICATION_REPORT not in str(rec.get("record_path", "")):
        fail(f"S1 ratification must reference its canonical record {S1_INTEGRATION_RATIFICATION_REPORT}", errors)
    if len(errors) != before:
        return False
    print(f"  OK   S1 four-path ratification transaction proven ({stage or 'fixture mode'}) and "
          f"Human-recorded {S1_INTEGRATION_RATIFICATION_DECISION_ID} "
          f"(ONE_TIME_CHANGE_SPECIFIC, no blanket grant)")
    return True


def _s1_ci_disposition_ratification(errors):
    """Validate the fourth authorized content of the protected central validator:
    the CI-infrastructure tail disposition extension ratified under
    ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001.

    Fail-closed structure:
      * the three externally pinnable package files must match the disposition
        post-images exactly (same-era atomicity, never conflated);
      * in a Git context the post-R2 chain must prove the exact authorized
        topology R2 → five pinned ci.yml-only tail commits → R3a (exact
        disposition path signature) → R3b (metadata-only);
      * the Human decision record must exist and bind the decision id, every
        tail SHA, the required invariant statements, and sha256 bindings for
        every disposition path — and every bound digest is verified against
        live content (including this file's own, which cannot self-pin);
      * a decisions.jsonl record, whenever present, is validated with the same
        discipline as the R1 record (Human authority, ONE_TIME scope, every
        grants_* false, exact ratified paths and digests).
    """
    for rel, want in sorted(S1_CI_DISPOSITION_POST_IMAGES.items()):
        p = REPO_ROOT / rel
        if not p.exists():
            fail(f"S1 CI-disposition package file missing: {rel}", errors)
            return False
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != want:
            fail(f"S1 CI-disposition package file {rel} is {got[:16]}… but the authorized "
                 f"disposition pins {want[:16]}… — the package is not intact", errors)
            return False
    rec_text = read_text(S1_CI_DISPOSITION_RECORD)
    if rec_text is None:
        fail(f"S1 CI-disposition canonical record {S1_CI_DISPOSITION_RECORD} missing", errors)
        return False
    # Required record content: the decision id, every pinned tail SHA, the
    # task ids, and the explicit invariant statements.
    required_markers = [
        S1_CI_DISPOSITION_DECISION_ID,
        S1_CI_DISPOSITION_TASK,
        "ANOX-TASK-S1-CI-ARM64-ISOLATION-001",
        *S1_CI_TAIL_SHAS,
        "ONE_TIME",
        "x86_64",
        "arm64-v8a",
    ]
    for marker in required_markers:
        if marker not in rec_text:
            fail(f"S1 CI-disposition record {S1_CI_DISPOSITION_RECORD} lacks required "
                 f"content marker {marker!r}", errors)
            return False
    # The record must pin the live content of every disposition path —
    # including the files that cannot self-pin (this validator and the S1
    # integration validator). A forged or stale binding fails closed.
    sha_re = re.compile(r"[0-9a-f]{64}")
    for rel in sorted(S1_CI_DISPOSITION_PATHS - {S1_CI_DISPOSITION_RECORD}):
        p = REPO_ROOT / rel
        if not p.exists():
            fail(f"S1 CI-disposition path missing: {rel}", errors)
            return False
        live = hashlib.sha256(p.read_bytes()).hexdigest()
        bound = {h for line in rec_text.splitlines() if rel in line
                 for h in sha_re.findall(line)}
        if live not in bound:
            fail(f"S1 CI-disposition record must pin live sha256 of {rel} "
                 f"({live[:16]}…)", errors)
            return False
    git_dir, why = _resolve_git_dir()
    stage = None
    if git_dir is None and why != "absent":
        fail(f"S1 CI-disposition: Git metadata unusable ({why}) — the transaction "
             f"cannot be proven and must not be assumed", errors)
        return False
    if git_dir is not None:
        stage = _s1_ratification_transaction(errors)
        if stage is None:
            return False
        if stage != "R1R2_DISPOSITION":
            fail(f"S1 CI-disposition: protected content is the disposition era but the "
                 f"chain proves stage {stage!r} — the package and the chain are different eras",
                 errors)
            return False
    recs = load_jsonl(DECISIONS_PATH)
    rec = next((r for r in recs if r.get("decision_id") == S1_CI_DISPOSITION_DECISION_ID), None)
    if rec is None:
        print(f"  OK   S1 CI-infrastructure tail disposition proven structurally "
              f"({stage or 'content identity, fixture mode'}); record pins all live post-images")
        return True
    before = len(errors)
    actor = str(rec.get("authority_actor", ""))
    if "Human Product & Security Owner" not in actor:
        fail(f"S1 CI-disposition authority_actor must be the Human Product & Security Owner, got {actor!r}", errors)
    if rec.get("scope") != "ONE_TIME_CHANGE_SPECIFIC":
        fail("S1 CI-disposition scope must be ONE_TIME_CHANGE_SPECIFIC", errors)
    if rec.get("is_human_authority") is not True:
        fail("S1 CI-disposition must record is_human_authority=true", errors)
    for flag in ("grants_general_ownership", "grants_future_sessions", "grants_future_successor_contents",
                 "grants_future_correction_pairs", "grants_future_ratification_tails",
                 "grants_s2_s3_s4_authority", "grants_msc_closure", "grants_b004_b005_start"):
        if rec.get(flag) is not False:
            fail(f"S1 CI-disposition must record {flag}=false (no blanket grant), got {rec.get(flag)!r}", errors)
    files = sorted(rec.get("ratified_files") or [])
    if files != sorted(S1_CI_DISPOSITION_PATHS):
        fail(f"S1 CI-disposition ratified_files must be exactly "
             f"{sorted(S1_CI_DISPOSITION_PATHS)}, got {files!r}", errors)
    if S1_CI_DISPOSITION_RECORD not in str(rec.get("record_path", "")):
        fail(f"S1 CI-disposition must reference its canonical record {S1_CI_DISPOSITION_RECORD}", errors)
    if len(errors) != before:
        return False
    print(f"  OK   S1 CI-infrastructure tail disposition proven ({stage or 'fixture mode'}) and "
          f"Human-recorded {S1_CI_DISPOSITION_DECISION_ID} (ONE_TIME_CHANGE_SPECIFIC, no blanket grant)")
    return True


def check_protected_shared_files(errors):
    """F-03 — protected shared governance files are content-pinned to Human-ratified
    changes only; any other content fails closed.  Three ratified contents exist:
    S0_SUCCESSOR_EVENT_SUPPORT (F-01), S0_PRESERVATION_LIFECYCLE_EXTENSION
    (preservation decision) and S1_INTEGRATION_LIFECYCLE_EXTENSION (the atomic
    four-path ratification transaction); each requires its own Human authority."""
    print("\n[S0-CONTRACT] Protected shared governance files (F-03)")
    before = len(errors)
    ratified = _f01_ratification(errors)
    pres_ratified = _preservation_ratification(errors)
    for rel, spec in PROTECTED_SHARED_FILES.items():
        p = REPO_ROOT / rel
        if not p.exists():
            fail(f"protected shared file {rel} missing", errors)
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest == spec["authorized_sha256"]:
            if ratified is None:
                fail(f"{rel} carries the S0 successor-support change but no valid Human ratification exists", errors)
            continue
        if digest == spec["preservation_authorized_sha256"]:
            if pres_ratified is None:
                fail(f"{rel} carries the S0 preservation lifecycle extension but no valid Human ratification exists", errors)
            continue
        if digest == spec.get("s1_integration_authorized_sha256"):
            if not _s1_integration_ratification(errors):
                fail(f"{rel} carries the S1 integration lifecycle extension but the authorized "
                     f"four-path ratification transaction is not proven", errors)
            continue
        if digest == spec.get("s1_ci_disposition_authorized_sha256"):
            if not _s1_ci_disposition_ratification(errors):
                fail(f"{rel} carries the S1 CI-infrastructure tail disposition extension but the "
                     f"authorized disposition transaction is not proven", errors)
            continue
        if digest == spec["base_sha256"]:
            fail(f"{rel} is at its pre-S0 content — the ratified S0 successor-support change is absent", errors)
            continue
        fail(f"{rel} content {digest[:16]}… is neither the pre-S0 baseline nor a Human-ratified "
             f"change ({spec['authorized_sha256'][:16]}… / {spec['preservation_authorized_sha256'][:16]}… / "
             f"{str(spec.get('s1_integration_authorized_sha256'))[:16]}…) — "
             f"unauthorized modification of a {spec['classification']}; a new Human ratification is required", errors)
    if len(errors) == before:
        ok(f"{len(PROTECTED_SHARED_FILES)} protected shared file(s) pinned to the ratified change(s); "
           f"S1 prohibited before integration")


def _resolve_git_dir():
    """Fail-closed Git metadata resolution (F-02 era-precision hardening,
    REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001).

    Returns (git_dir, None) on success or (None, reason). A normal ``.git``
    directory AND a linked-worktree ``.git`` pointer file (``gitdir: <path>``)
    both resolve; the only soft result is ``"absent"`` — no ``.git`` at all,
    which is the test-fixture mode. A malformed, unreadable or dangling Git
    context is a hard failure reason so the scope gate can never be silently
    skipped in a real worktree."""
    dot_git = REPO_ROOT / ".git"
    if not dot_git.exists():
        return None, "absent"
    if dot_git.is_dir():
        if not (dot_git / "HEAD").exists():
            return None, ".git directory has no HEAD"
        return dot_git, None
    if not dot_git.is_file():
        return None, ".git is neither a directory nor a file"
    try:
        text = dot_git.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeDecodeError):
        return None, ".git pointer file unreadable"
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) != 1 or not lines[0].startswith("gitdir:"):
        return None, ".git pointer file malformed"
    target = lines[0][len("gitdir:"):].strip()
    if not target or "\x00" in target:
        return None, ".git pointer target empty or invalid"
    tpath = Path(target)
    if not tpath.is_absolute():
        tpath = REPO_ROOT / tpath
    try:
        tpath = tpath.resolve(strict=True)
    except (OSError, RuntimeError):
        return None, ".git pointer target does not exist"
    if not tpath.is_dir() or not (tpath / "HEAD").exists():
        return None, ".git pointer target is not a git directory"
    return tpath, None


def check_scope(man, errors):
    """F-02 — the scope gate fails closed. The authorized base is validator-owned;
    an absent, malformed, unauthorized, missing or non-ancestor base is a FAILURE,
    never a SKIP."""
    print("\n[S0-CONTRACT] Scope (git)")
    before = len(errors)
    base = man.get("base_sha")
    if not base or not isinstance(base, str):
        fail("manifest base_sha missing", errors)
        return
    if not SHA1_RE.match(base):
        fail(f"manifest base_sha {base!r} is malformed (expected 40 lowercase hex)", errors)
        return
    if base != AUTHORIZED_S0_BASE_SHA:
        fail(f"manifest base_sha {base[:12]} is not the authorized S0 base "
             f"{AUTHORIZED_S0_BASE_SHA[:12]} — scope base may not be redeclared", errors)
        return
    git_dir, why = _resolve_git_dir()
    if git_dir is None:
        if why == "absent":
            print("  SKIP git-diff checks (no .git — fixture mode); authorized base pinned")
            return
        fail(f"Git metadata unusable ({why}) — the S0 scope gate cannot be evaluated "
             f"and must not be skipped", errors)
        return
    exists = subprocess.run(["git", "cat-file", "-e", f"{base}^{{commit}}"], cwd=REPO_ROOT, capture_output=True)
    if exists.returncode != 0:
        fail(f"authorized S0 base {base[:12]} does not exist in this repository", errors)
        return
    anc = subprocess.run(["git", "merge-base", "--is-ancestor", base, "HEAD"], cwd=REPO_ROOT, capture_output=True)
    if anc.returncode != 0:
        fail(f"authorized S0 base {base[:12]} is not an ancestor of HEAD — "
             f"the S0 scope gate cannot be evaluated and must not be skipped", errors)
        return
    # The S0 scope property is about S0's OWN delivery: the pinned corrected S0
    # range base..S0_FINAL_HEAD must not touch product/S1-owned paths. Evaluating
    # against a moving HEAD would conflate S0 with every later authorized
    # delivery (e.g. the S1 integration, which legitimately changes S1-owned
    # files). The S0 final head is pinned and must be an ancestor of HEAD.
    # (Era-precision correction recorded by REMEDIATION-S1-CANONICAL-INTEGRATION-001;
    # forbidden set and protected-file checks unchanged.)
    fin = subprocess.run(["git", "cat-file", "-e", f"{AUTHORIZED_S0_FINAL_HEAD_SHA}^{{commit}}"],
                         cwd=REPO_ROOT, capture_output=True)
    if fin.returncode != 0:
        fail(f"pinned corrected S0 final head {AUTHORIZED_S0_FINAL_HEAD_SHA[:12]} does not exist in this repository", errors)
        return
    fin_anc = subprocess.run(["git", "merge-base", "--is-ancestor", AUTHORIZED_S0_FINAL_HEAD_SHA, "HEAD"],
                             cwd=REPO_ROOT, capture_output=True)
    if fin_anc.returncode != 0:
        fail(f"pinned corrected S0 final head {AUTHORIZED_S0_FINAL_HEAD_SHA[:12]} is not an ancestor of HEAD — "
             f"S0 delivery lineage broken", errors)
        return
    if subprocess.run(["git", "merge-base", "--is-ancestor", base, AUTHORIZED_S0_FINAL_HEAD_SHA],
                      cwd=REPO_ROOT, capture_output=True).returncode != 0:
        fail(f"pinned S0 final head does not descend from the authorized S0 base", errors)
        return
    out = subprocess.run(["git", "diff", "--name-only", base, AUTHORIZED_S0_FINAL_HEAD_SHA],
                         cwd=REPO_ROOT, capture_output=True, text=True)
    changed = [p for p in out.stdout.splitlines() if p.strip()]
    bad = sorted(p for p in changed if p.startswith(FORBIDDEN_PRODUCT_PREFIXES) or p.endswith(".sql") or p.endswith(".so")
                 or p in S1_OWNED_FILES)
    if bad:
        fail(f"S0 changed product/S1-owned paths: {bad}", errors)
    # Protected shared files are checked at their CURRENT content (below), so a
    # later unratified modification is still caught regardless of range.
    head_changed = subprocess.run(["git", "diff", "--name-only", base], cwd=REPO_ROOT,
                                  capture_output=True, text=True).stdout.splitlines()
    changed = sorted(set(changed) | {p for p in head_changed if p in PROTECTED_SHARED_FILES})
    def _protected_change_ratified(rel):
        digest = hashlib.sha256((REPO_ROOT / rel).read_bytes()).hexdigest() if (REPO_ROOT / rel).exists() else None
        spec = PROTECTED_SHARED_FILES[rel]
        if digest == spec["authorized_sha256"]:
            return _f01_ratification([]) is not None
        if digest == spec["preservation_authorized_sha256"]:
            return _preservation_ratification([]) is not None
        if digest == spec.get("s1_integration_authorized_sha256"):
            return _s1_integration_ratification([])
        if digest == spec.get("s1_ci_disposition_authorized_sha256"):
            return _s1_ci_disposition_ratification([])
        return False
    unratified = sorted(p for p in changed
                        if p in PROTECTED_SHARED_FILES and not _protected_change_ratified(p))
    if unratified:
        fail(f"S0 changed protected shared governance file(s) without Human ratification: {unratified}", errors)
    if len(errors) == before:
        ok(f"no product, SQL, native, CI or S1-owned paths changed since {base[:12]}; "
           f"protected shared changes ratified")


def run():
    errors = []
    man = check_manifest(errors)
    if man is None:
        return errors
    doc = check_document(man, errors)
    if doc is None:
        return errors
    check_core_invariants(doc, errors)
    check_domain_matrix(doc, errors)
    check_contract_maps(man, doc, errors)
    check_mapping_anchors(man, doc, errors)
    check_internal_references(doc, errors)
    check_authority_index(man, errors)
    check_freeze_registry(man, errors)
    check_schema_authority(man, errors)
    check_cc_authority_homes(man, errors)
    check_preserved_decisions(man, doc, errors)
    check_no_implementation(man, errors)
    check_unit_roles(man, doc, errors)
    check_protected_shared_files(errors)
    check_scope(man, errors)
    return errors


def main():
    errors = run()
    if errors:
        print(f"\nS0 CONTRACT FREEZE AUTHORITY: FAIL ({len(errors)} error(s))")
        for e in errors:
            print(f"  FAIL {e}")
        return 1
    print("\nS0 CONTRACT FREEZE AUTHORITY: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
