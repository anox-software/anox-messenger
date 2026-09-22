#!/usr/bin/env python3
"""S1 canonical-integration evidence validator — REMEDIATION-S1-CANONICAL-INTEGRATION-001.

Why this file exists (shared-validator follow-up, governance-compliant form)
---------------------------------------------------------------------------
`tools/audit/validate_security_audit_evidence_preservation.py` is a
PROTECTED_SHARED_GOVERNANCE_FILE whose content is pinned by the frozen S0
contract (`tools/audit/validate_s0_contract_freeze.py`) to exactly the two
Human-ratified contents; any other content is "unauthorized modification — a
new Human ratification is required" (`grants_s1_permission = false`).
The S1 integration therefore does NOT modify that file. Instead:

  * the exact minimum S1-era extension is preserved as a ratification proposal
    (`docs/reports/security/decisions/S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-PROPOSAL-001.md`
    + patch), tamper-evident via the pinned post-change SHA-256 below;
  * this validator runs the ratified central module's era-agnostic S0
    protections VERBATIM (imported, unmodified code) and adds the pinned
    S1-era acceptance logic for the four era-bound sections (base/topology,
    registry growth, scope, Project-Memory chain).

Acceptance is pinned to exactly ANOX-EVENT-0055 / SEC-AUDIT-REG-0014 / the
recorded integration topology. Every acceptance condition has a paired
rejection test in tools/audit/test_s1_integration_evidence.py.
Stdlib only. Fails closed.
"""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(os.environ.get("SECURITY_AUDIT_PRESERVATION_REPO") or Path(__file__).resolve().parents[2])
CENTRAL = "tools/audit/validate_security_audit_evidence_preservation.py"
CENTRAL_TESTS = "tools/audit/test_security_audit_evidence_preservation.py"
S0_CONTRACT = "tools/audit/validate_s0_contract_freeze.py"
S0_CONTRACT_TESTS = "tools/audit/test_s0_contract_freeze.py"

# Ratified content of the protected shared validator (pinned by the S0 contract
# under ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001).
CENTRAL_RATIFIED_SHA256 = "89c7358fbbe61c71c8fcde114ffc8a83aa33f52bd3fb763417e00f4131d84bb7"
# Proposed post-change content (S1-era extension) awaiting Human ratification.
#
# FOUR-FILE RATIFICATION TRANSACTION
# (REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001, closing retest S1-004
# blocking finding B-6). A two-path package was verifiable but structurally
# UNCOMMITTABLE: applying it made the protected validator the S1 successor, which
# the frozen S0 contract pinned to only two authorized contents, so committed R1
# failed S0 permanently; an R1 that also carried the S0 contract pin was rejected
# for changing a third path; and a metadata-only R2 may not touch tools/**.
# The ratification is therefore ONE atomic transaction over exactly four paths.
#
# SUPERSESSION — never ratify any of these:
#   e52f626a46f27af59b51acf2af20ec6762ab71f8c1e35239e6c59f70182af1f8  (rev 1)
#   d03e539a49e9126e92b0fdc31fb5c8e424a6e7e82c98cf954881e99e6edbed74  (rev 2)
#   87cd5e202325f1921954fc3a6e23999f987fc65d65bb13652ae34473001fbecd  (rev 3)
CENTRAL_PROPOSED_SHA256 = "859e834e06876e34efbdaf9f209005c86d0562b54237f602c45f110bc72a6148"
CENTRAL_TESTS_PROPOSED_SHA256 = "c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462"
S0_CONTRACT_PROPOSED_SHA256 = "7dbcaf60d7ba4dab1124e2af035eea64a8847a6d7942a6316229eb2bf645d5b4"
S0_CONTRACT_TESTS_PROPOSED_SHA256 = "d22034e61257f3d13588b402b49eba2396ee2b5b9a736774e9a6522ee037f13a"
# Pre-images the transaction applies to. Files 1/2 are the Human-ratified central
# baseline; files 3/4 are the S0 contract pair as delivered pre-ratification.
S1_RATIFICATION_PRE_IMAGES = {
    CENTRAL: CENTRAL_RATIFIED_SHA256,
    CENTRAL_TESTS: "29399c5ddb54909b94bf046d257608da52c39bd4ae94a76508ca21e60ac0ae0c",
    S0_CONTRACT: "0978b8a53ee50f411c07699c0b33ece7da451b6534c9bad5c522af9700cb77b2",
    S0_CONTRACT_TESTS: "6590a218b11bce51d1f360d46206e411e150214acb40bbc5afdbfd6747dc2068",
}
S1_RATIFICATION_POST_IMAGES = {
    CENTRAL: CENTRAL_PROPOSED_SHA256,
    CENTRAL_TESTS: CENTRAL_TESTS_PROPOSED_SHA256,
    S0_CONTRACT: S0_CONTRACT_PROPOSED_SHA256,
    S0_CONTRACT_TESTS: S0_CONTRACT_TESTS_PROPOSED_SHA256,
}
# NO FIXED POINT: this validator is NOT part of the transaction, so it can pin
# all four post-images — including the S0 contract's, which the S0 contract
# itself cannot pin about itself. That is exactly why the external pin lives
# here and why this file must never be added to S1_RATIFICATION_PATHS.
SUPERSEDED_NEVER_RATIFY = (
    "e52f626a46f27af59b51acf2af20ec6762ab71f8c1e35239e6c59f70182af1f8",
    "d03e539a49e9126e92b0fdc31fb5c8e424a6e7e82c98cf954881e99e6edbed74",
    "87cd5e202325f1921954fc3a6e23999f987fc65d65bb13652ae34473001fbecd",
)
PROPOSAL_PATCH = "docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch"
PROPOSAL_RECORD = "docs/reports/security/decisions/S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-PROPOSAL-001.md"

S1_INTEGRATION_EVENT = {
    "event_id": "ANOX-EVENT-0055",
    "type": "remediation_session_integration",
    "task": "ANOX-TASK-REMEDIATION-S1-CANONICAL-INTEGRATION-001",
    "start_head": "29a6643189242a47c4a79c38acd04c1eca748787",
    "merged_head": "e32463ca71b0fec62a5f20026e6dc528f9bff30c",
    "merged_base": "0f932520393feee6d479cc099f179f5766323125",
    "ref": "docs/reports/security/remediation/REMEDIATION-S1-CANONICAL-INTEGRATION-001.md",
    "delivery_branch": "integration/s1-after-s0-001",
    "supersedes_provisional_event": "ANOX-EVENT-0054",
}
S1_INTEGRATION_ID = "REMEDIATION-S1-CANONICAL-INTEGRATION-001"
S1_ORIGINAL_TASK = "ANOX-TASK-REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001"
# Pinned S1 delivery commits (merge is recorded in the registry/event). A
# Human-authorized pre-ratification correction pass may append exactly one
# further task pair [D1 substantive, D2 metadata] on the same delivery branch;
# D1 is bound to CURRENT_STATE.described_head and current_task must be the
# correction task. No other chain shape is accepted.
S1_SUBSTANTIVE_SHA = "ea20aaaf330c9268448df5523e89615aa0a69074"
S1_METADATA_SHA = "573c5f58b91a1871fb6d7a6d722585a8518fa02c"
# N-9 (REMEDIATION-S1-FINAL-CORRECTIONS-001): every correction pair that has
# already been delivered is pinned by SHA and can never again be replaced,
# rewritten or reused as an open "slot". The pre-ratification pair below is now
# CONSUMED; only the single currently authorized correction task may add one
# further (still unpinned) pair. See the disclosed trust boundary in
# lifecycle_legality.canonical_integration_delivery.
CONSUMED_CORRECTION_PAIRS = (
    # REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001 (substantive, metadata)
    ("0d1549d12d02fd7b277bf04fed7530b6605c1023",
     "f08749e2e5ec45e76b1ea98c5c999e4679be3ffe"),
    # REMEDIATION-S1-FINAL-CORRECTIONS-001 — frozen by retest S1-003 and promoted
    # here, so D1'/D2' can no longer be substituted.
    ("a79e3b3db9b441fd81b5f76f6804f90eb44bb36b",
     "4319dacaa7ac94405e8b72fe23effb6e733ab898"),
    # REMEDIATION-S1-RATIFICATION-TAIL-CORRECTION-001 — frozen by
    # TARGETED-INDEPENDENT-FINAL-RATIFICATION-RETEST-S1-004 and promoted here, so
    # the ratification-tail pair can no longer be substituted either.
    ("4b31f680613651772d6006c2d47d1f6ccd1bb837",
     "10cc68c442bc67be03d863ad20e29e4dfcb0bd51"),
    # REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001 — consumed by the
    # delivered R1/R2 transaction and promoted here under
    # ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001, closing the last
    # unpinned correction slot (the disclosed trust boundary is now fully
    # resolved by SHA pins).
    ("7120aedd452bd77bbe208bb76a6d2c421394c820",
     "c57485d7c54f57ab03cb2c896d796b2da787fc13"),
)
S1_CORRECTION_TASKS = (
    "ANOX-TASK-REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001",
    "ANOX-TASK-REMEDIATION-S1-FINAL-CORRECTIONS-001",
    "ANOX-TASK-REMEDIATION-S1-RATIFICATION-TAIL-CORRECTION-001",
    "ANOX-TASK-REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001",
    # Tasks that may legitimately appear as CURRENT_STATE.current_task on the
    # S1 delivery branch under the CI-infrastructure tail disposition
    # (ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001).
    "ANOX-TASK-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001",
    "ANOX-TASK-S1-CI-ARM64-ISOLATION-001",
)
# REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001's pair is now CONSUMED:
# promoted into CONSUMED_CORRECTION_PAIRS under
# ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001, which closes the last
# disclosed unpinned surface — no open correction slot remains authorized.
S1_CORRECTION_TASK = None
# Human-ratification tail: R1 may change EXACTLY these four paths, R2 is
# metadata-only. The set is the atomic four-file transaction — see the
# SUPERSESSION/FOUR-FILE block above. No fifth path is ever admissible.
S1_RATIFICATION_PATHS = frozenset(S1_RATIFICATION_POST_IMAGES)
S1_RATIFICATION_DECISION_ID = "ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001"

# --- Human-authorized post-R2 CI-infrastructure tail disposition -----------
# ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001 ratifies exactly the
# five ci.yml-only commits below — position (after the completed R1/R2 tail),
# order and SHA identity are all bound — plus the disposition pair
# [R3a substantive, R3b metadata] that carries this governance extension and
# the sealing event ANOX-EVENT-0058. Nothing else is admissible: no SHA
# substitution, no reorder, no additional unpinned CI commit, no path other
# than .github/workflows/ci.yml, no tail before R2.
S1_CI_TAIL = (
    ("e7bd2c6547fb23de44a8aa762fe5d046c34d318e", frozenset({".github/workflows/ci.yml"})),
    ("0636a4ee81e2e7ea9dd4ca7615d06bf80ae80827", frozenset({".github/workflows/ci.yml"})),
    ("793246022c0501e85350113871d00db9ee843826", frozenset({".github/workflows/ci.yml"})),
    ("45d1e4a63de45fe10d2fc8f455b321bb675e390a", frozenset({".github/workflows/ci.yml"})),
    # ANOX-TASK-S1-CI-ARM64-ISOLATION-001 — deterministic stale-emulator
    # isolation for the persistent self-hosted ARM64 runner.
    ("4fc5263ff6763768088f0f13856d704bd1772178", frozenset({".github/workflows/ci.yml"})),
)
S1_CI_DISPOSITION_DECISION_ID = "ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001"
S1_CI_DISPOSITION_RECORD = "docs/reports/security/decisions/S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001.md"
S1_CI_DISPOSITION_TASK = "ANOX-TASK-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001"
S1_CI_ARM64_ISOLATION_TASK = "ANOX-TASK-S1-CI-ARM64-ISOLATION-001"
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
S1_CI_DISPOSITION_EVENT = {
    "event_id": "ANOX-EVENT-0058",
    "type": "governance",
    "task": S1_CI_DISPOSITION_TASK,
    "start_head": "45d1e4a63de45fe10d2fc8f455b321bb675e390a",
}
# Exact authorized post-images of every file the disposition transaction may
# change — except this validator itself, which cannot pin its own content
# (NO FIXED POINT; its live hash is pinned externally in the decision record,
# closing the same disclosed residual the R1 transaction documented).
S1_CI_DISPOSITION_POST_IMAGES = {
    "tools/audit/lifecycle_legality.py": "519e99f75139df62e80084933dbbedec18459bb1b97940da057dac501754ec19",
    CENTRAL: "fe5abd4e7a39029a679be336589d8aa766b80c72862a5bb77f05693a30034899",
    CENTRAL_TESTS: "29399c5ddb54909b94bf046d257608da52c39bd4ae94a76508ca21e60ac0ae0c",
    S0_CONTRACT: "0978b8a53ee50f411c07699c0b33ece7da451b6534c9bad5c522af9700cb77b2",
    S0_CONTRACT_TESTS: "97d7896009235e5138aed86d6a7b7361d0cb333b605208d899900dc498832fa4",
    "tools/audit/test_s1_integration_evidence.py": "ef40790e43d0524ac824b199f576a9dcd38a72e943fc24313e414f3725af0ea8",
    "tools/audit/validate_s0_evidence_preservation.py": "671aa5a9350d6b36421d5d94de9360e1414fda258cdc53af2ffbfde33e016ca2",
}
CENTRAL_CI_DISPOSITION_SHA256 = S1_CI_DISPOSITION_POST_IMAGES[CENTRAL]

S1_ALLOWED_EXACT = {
    ".github/workflows/ci.yml", ".gitignore", "android/build.gradle.kts",
    "crypto/rust/rust-toolchain.toml", "docs/current/REPOSITORY_SECURITY_POLICY.md",
    "docs/reports/security/retests/INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001.md",
    "docs/reports/security/remediation/REMEDIATION-S1-CANONICAL-INTEGRATION-001.md",
    PROPOSAL_RECORD, PROPOSAL_PATCH,
    "docs/security/audit-evidence/audit_registry.jsonl",
    "tools/audit/lifecycle_legality.py",
    "tools/audit/validate_s0_evidence_preservation.py",  # explicit: SEC-AUDIT-REG-0014 is not an S0 "prior" record
    "tools/audit/validate_s0_contract_freeze.py",  # explicit: S0 scope evaluated over S0's own pinned range
    "tools/audit/test_security_audit_evidence_preservation.py",  # fixture normalisation only (277 tests pinned)
    "tools/audit/test_s0_contract_freeze.py",  # paired fail-closed worktree tests (S1-PRE-RAT-CORR)
    "docs/reports/security/remediation/REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001.md",
    "tools/audit/validate_b021_verification_matrix.py",
    "tools/audit/validate_s1_build_provenance.py",
    "tools/audit/test_s1_build_provenance.py",
    "tools/audit/test_s1_retest_remediation.py",
    "tools/audit/validate_s1_integration_evidence.py",
    "tools/audit/test_s1_integration_evidence.py",
    # REMEDIATION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001 evidence surface
    "docs/reports/security/decisions/S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001.md",
    # REMEDIATION-S1-FINAL-CORRECTIONS-001 evidence surfaces
    "docs/reports/security/decisions/S1-FINAL-CORRECTION-AUTHORIZATION-001.md",
    "docs/reports/security/remediation/REMEDIATION-S1-FINAL-CORRECTIONS-001.md",
    "docs/reports/security/retests/TARGETED-INDEPENDENT-PRE-RATIFICATION-RETEST-S1-002.md",
    # REMEDIATION-S1-RATIFICATION-TAIL-CORRECTION-001 evidence surfaces
    "docs/reports/security/decisions/S1-RATIFICATION-TAIL-CORRECTION-AUTHORIZATION-001.md",
    "docs/reports/security/remediation/REMEDIATION-S1-RATIFICATION-TAIL-CORRECTION-001.md",
    "docs/reports/security/retests/TARGETED-INDEPENDENT-RATIFICATION-COMMITTABILITY-RETEST-S1-003.md",
    # REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001 evidence surfaces
    "docs/reports/security/decisions/S1-FOUR-FILE-RATIFICATION-AUTHORIZATION-001.md",
    "docs/reports/security/remediation/REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001.md",
    "docs/reports/security/retests/TARGETED-INDEPENDENT-FINAL-RATIFICATION-RETEST-S1-004.md",
}
S1_ALLOWED_PREFIXES = (
    "android/src/main/jniLibs/",   # deletions of the committed-.so bypass only
    "tools/security/",
    "docs/security/remediation/",
)
S1_FORBIDDEN_PREFIXES = (
    "crypto/rust/src/", "android/src/main/java/", "android/src/androidTest/", "android/src/test/",
    "backend/", "supabase/", "migrations/", "docs/authority/",
)

S1_INTEGRATION_REGISTRY_REQUIRED = {
    "record_id": "SEC-AUDIT-REG-0014",
    "audit_id": S1_INTEGRATION_ID,
    "artifact_type": "SECURITY_REMEDIATION_EVIDENCE",
    "task_id": S1_INTEGRATION_EVENT["task"],
    "base_sha": S1_INTEGRATION_EVENT["start_head"],
    "s1_original_base_sha": "0f932520393feee6d479cc099f179f5766323125",
    "s1_original_substantive_sha": "fc58414b6790c07f65d1dc9f72c019abd42efc86",
    "s1_original_final_head_sha": "e32463ca71b0fec62a5f20026e6dc528f9bff30c",
    "s1_integration_merge_sha": "dd6e2c5d82f0777aedfea9fd7a2516cb83254fdb",
    "s1_provisional_event": "ANOX-EVENT-0054",
    "s1_provisional_event_status": "NONCANONICAL",
    "canonical_event": "ANOX-EVENT-0055",
    "independent_retest_id": "INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001",
    "independent_retest_result": "PASS_WITH_FINDINGS",
    "findings_final_disposition": {
        "F-1": "FIXED", "F-2": "FIXED", "F-3": "FIXED", "F-4": "FIXED", "F-5": "FIXED",
        "F-6": "FIXED", "F-7": "FIXED", "F-8": "DOCUMENTED_PIN_PROVENANCE_UNVERIFIED_PINS_UNCHANGED",
        "F-9": "FIXED",
    },
    "shared_validator_followup": "PROPOSAL_PREPARED_PENDING_HUMAN_RATIFICATION",
    "shared_validator_proposed_sha256": CENTRAL_PROPOSED_SHA256,
    "shared_validator_paired_tests_proposed_sha256": CENTRAL_TESTS_PROPOSED_SHA256,
    # Four-file ratification transaction (B-6): the S0 contract that pins the
    # protected validator, and its paired suite, move in the SAME commit.
    "shared_validator_s0_contract_proposed_sha256": S0_CONTRACT_PROPOSED_SHA256,
    "shared_validator_s0_contract_tests_proposed_sha256": S0_CONTRACT_TESTS_PROPOSED_SHA256,
    "shared_validator_ratification_transaction": "FOUR_FILE_ATOMIC_R1_PLUS_METADATA_R2",
    "shared_validator_superseded_never_ratify": list(SUPERSEDED_NEVER_RATIFY),
    "medium_or_higher_open_retest_findings": 0,
    "msc_closed_by_s1": 0,
    "open_msc_units": 42,
    "security_remediation": "IN_PROGRESS",
    "b004": "NOT_STARTED",
    "b005": "NOT_STARTED",
    "product": "BLOCKED_PENDING_FINAL_AUDIT",
    "native_behavior_source_changed": "NO",
    "arm64_runtime_evidence": "IMPLEMENTER_ONLY_NOT_INDEPENDENT",
    "x86_64_runtime_evidence": "PENDING_REAL_CI_OR_INDEPENDENT_RUNTIME_EVIDENCE",
    "msc_runtime_tested_downgraded_under_exact_fcp1": ["MSC-UNIT-001", "MSC-UNIT-002"],
    "s0_files_changed_by_s1": 0,
    "previous_evidence_weakened": "NO",
    "status": "INTEGRATED_PENDING_TARGETED_INDEPENDENT_RETEST",
    "delivery_branch": S1_INTEGRATION_EVENT["delivery_branch"],
    "report_path": S1_INTEGRATION_EVENT["ref"],
    "report_sha256": "cbe0831071ea71e311cb9ad4458fd5be14a61bd2033a5ea0e9940c5321602d05",
}
S1_INTEGRATION_SOURCE_SHA256 = {
    "independent_retest": ("docs/reports/security/retests/INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001.md",
                           "c3e6a564c32992731af42358a5c42a206b76baff95a2c0408147f732b91d95ae"),
    "s1_runtime_evidence_record": ("docs/security/remediation/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME.md",
                                   "0db8adb9dc607e1e718babd7355e9e879b964270d3b1c5bd7b4fa713f58d727c"),
    "s1_task_report": ("docs/security/remediation/S1_TASK_REPORT.md", "a487f0c4b0f1fb00ca4cb79dde7a17463b3092733a2b9f804ac795e6d37ae3ca"),
}


# ---------------------------------------------------------------------------
def fail(msg, errors):
    errors.append(msg)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def has_git():
    dot_git = REPO_ROOT / ".git"
    if dot_git.is_dir():
        return True
    if dot_git.is_file():
        try:
            line = dot_git.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            return False
        if line.startswith("gitdir:"):
            target = line[len("gitdir:"):].strip()
            tpath = Path(target) if Path(target).is_absolute() else REPO_ROOT / target
            return tpath.is_dir() and (tpath / "HEAD").exists()
    return False


def _git(args):
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)


def load_central():
    """Import the ratified central validator unmodified (fail closed on drift)."""
    p = REPO_ROOT / CENTRAL
    if not p.exists():
        return None, f"protected shared validator missing: {CENTRAL}"
    digest = sha256_file(p)
    # BLOCKER-2 (retest S1-003): pinning ONLY the pre-ratification content made this
    # validator fail permanently the moment the Human ratified the package. Exactly
    # two contents are admissible and they are distinguished, never conflated:
    #   * CENTRAL_RATIFIED_SHA256  — the current Human-ratified content (pre-ratification state)
    #   * CENTRAL_PROPOSED_SHA256  — the exact successor this proposal yields, admissible
    #                                only once it has actually been ratified and applied
    # Any other content is still a hard fail.
    if digest == CENTRAL_RATIFIED_SHA256:
        central_state = "PRE_RATIFICATION"
    elif digest == CENTRAL_PROPOSED_SHA256:
        central_state = "RATIFIED_SUCCESSOR_APPLIED"
    elif digest == CENTRAL_CI_DISPOSITION_SHA256:
        central_state = "CI_DISPOSITION_APPLIED"
    elif digest in SUPERSEDED_NEVER_RATIFY:
        return None, (f"protected shared validator content {digest[:16]}… is a SUPERSEDED ratification "
                      f"revision that must NEVER be ratified — only the Human-ratified baseline "
                      f"{CENTRAL_RATIFIED_SHA256[:16]}… or the current four-file successor "
                      f"{CENTRAL_PROPOSED_SHA256[:16]}… are admissible")
    else:
        return None, (f"protected shared validator content {digest[:16]}… is not the Human-ratified content "
                      f"{CENTRAL_RATIFIED_SHA256[:16]}…, the exact proposed successor "
                      f"{CENTRAL_PROPOSED_SHA256[:16]}…, or the authorized CI-disposition successor "
                      f"{CENTRAL_CI_DISPOSITION_SHA256[:16]}… — S1 must not run on a modified shared validator")
    # The transaction is ATOMIC: all four package files must sit in the SAME era.
    # A half-applied package (any member from the other era, or any third content)
    # is never a legitimate state and must never be conflated with either era.
    if central_state == "CI_DISPOSITION_APPLIED":
        want = {rel: S1_CI_DISPOSITION_POST_IMAGES[rel] for rel in S1_RATIFICATION_POST_IMAGES}
        era_label = "CI-disposition successor"
    elif central_state == "RATIFIED_SUCCESSOR_APPLIED":
        want = S1_RATIFICATION_POST_IMAGES
        era_label = "ratified successor"
    else:
        want = S1_RATIFICATION_PRE_IMAGES
        era_label = "pre-ratification"
    for rel, expected in sorted(want.items()):
        fp = REPO_ROOT / rel
        if not fp.exists():
            return None, f"ratification package file missing: {rel}"
        got = sha256_file(fp)
        if got != expected:
            return None, (f"four-file ratification transaction is half-applied: {rel} is {got[:16]}… but the "
                          f"{era_label} era pins {expected[:16]}… — the package moves atomically or not at all")
    os.environ["SECURITY_AUDIT_PRESERVATION_REPO"] = str(REPO_ROOT)
    spec = importlib.util.spec_from_file_location("anox_central_ratified", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._anox_central_state = central_state
    return mod, None


# ---------------------------------------------------------------------------
def _s1_delivery_active(state):
    return (state.get("current_task") in (S1_INTEGRATION_EVENT["task"],) + S1_CORRECTION_TASKS
            and state.get("delivery_branch") == S1_INTEGRATION_EVENT["delivery_branch"])


def _is_s1_integration_event(ev):
    return (ev.get("event_id") == S1_INTEGRATION_EVENT["event_id"]
            and ev.get("type") == S1_INTEGRATION_EVENT["type"]
            and ev.get("task") == S1_INTEGRATION_EVENT["task"]
            and ev.get("start_head") == S1_INTEGRATION_EVENT["start_head"]
            and ev.get("merged_head") == S1_INTEGRATION_EVENT["merged_head"]
            and ev.get("supersedes_provisional_event") == S1_INTEGRATION_EVENT["supersedes_provisional_event"]
            and S1_INTEGRATION_EVENT["ref"] in (ev.get("refs") or []))


def validate_base_s1(central, errors):
    print("[S1-INTEGRATION] Base / integration topology")
    if not has_git():
        print("  SKIP git checks (no .git — fixture mode)")
        return
    sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
    import lifecycle_legality as ll
    head = _git(["rev-parse", "HEAD"]).stdout.strip()
    state = json.loads((REPO_ROOT / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
    if not _s1_delivery_active(state):
        fail("CURRENT_STATE does not declare the S1 integration delivery (current_task/delivery_branch)", errors)
        return
    described = state.get("described_head") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", described):
        fail(f"CURRENT_STATE described_head is not a valid SHA: {described}", errors)
        return
    s1 = S1_INTEGRATION_EVENT
    for label, sha in (("BASE_SHA", central.BASE_SHA),
                       ("S0 successor base", central.S0_SUCCESSOR_EVENT["start_head"]),
                       ("S0 preservation base", central.S0_PRESERVATION_EVENT["start_head"])):
        if not ll._git_is_ancestor(sha, s1["start_head"], cwd=REPO_ROOT):
            fail(f"S1 integration base {s1['start_head'][:12]} does not descend from {label} {sha[:12]}", errors)
            return
    _delivery_out = {}
    ok, merge_sha, sub, meta, reason = ll.canonical_integration_delivery(
        s1["start_head"], s1["merged_head"], s1["merged_base"], described, head,
        cwd=REPO_ROOT, metadata_allowlist=central.METADATA_ALLOWLIST,
        s1_substantive_sha=S1_SUBSTANTIVE_SHA, s1_metadata_sha=S1_METADATA_SHA,
        correction_task=S1_CORRECTION_TASK,
        consumed_correction_pairs=CONSUMED_CORRECTION_PAIRS,
        ratification_paths=S1_RATIFICATION_PATHS,
        authorized_ci_tail=S1_CI_TAIL,
        disposition_paths=S1_CI_DISPOSITION_PATHS, out=_delivery_out)
    if not ok:
        fail(f"canonical S1 integration delivery failed: {reason}", errors)
        return
    tail = _delivery_out.get("ratification_tail", "NONE")
    ci_tail = _delivery_out.get("ci_tail") or []
    disposition = _delivery_out.get("disposition")
    central_state = getattr(central, "_anox_central_state", "PRE_RATIFICATION")
    if tail == "NONE" and central_state != "PRE_RATIFICATION":
        fail("ratified successor content is present without an authorized ratification tail", errors)
        return
    if tail != "NONE" and central_state not in ("RATIFIED_SUCCESSOR_APPLIED", "CI_DISPOSITION_APPLIED"):
        fail("ratification tail present but the protected shared validator is not the exact "
             "proposed successor content", errors)
        return
    if disposition and central_state != "CI_DISPOSITION_APPLIED":
        fail("CI-tail disposition pair present but the protected shared validator is not the "
             "authorized disposition successor content", errors)
        return
    if disposition:
        if not (REPO_ROOT / S1_CI_DISPOSITION_RECORD).exists():
            fail(f"CI-tail disposition decision record missing: {S1_CI_DISPOSITION_RECORD}", errors)
            return
        if state.get("ci_disposition_decision_id") != S1_CI_DISPOSITION_DECISION_ID:
            fail(f"disposition metadata commit must declare ci_disposition_decision_id "
                 f"{S1_CI_DISPOSITION_DECISION_ID}, got {state.get('ci_disposition_decision_id')!r}", errors)
            return
        print(f"  OK   authorized CI-infrastructure tail {len(ci_tail)} commit(s) pinned "
              f"({S1_CI_DISPOSITION_DECISION_ID}); disposition pair "
              f"[{disposition[0][:12]}, {disposition[1][:12]}] proven")
    if tail == "R1R2" and state.get("ratification_decision_id") != S1_RATIFICATION_DECISION_ID:
        fail(f"ratification metadata commit must declare ratification_decision_id "
             f"{S1_RATIFICATION_DECISION_ID}, got {state.get('ratification_decision_id')!r}", errors)
        return
    if tail != "NONE":
        print(f"  OK   authorized Human-ratification tail {tail} "
              f"(R1 {(_delivery_out.get('r1') or '')[:12]}"
              f"{', R2 ' + (_delivery_out.get('r2') or '')[:12] if _delivery_out.get('r2') else ''}); "
              f"exact package paths only; successor content matches the pinned proposal")
    _consumed_heads = {S1_METADATA_SHA} | {m for _, m in CONSUMED_CORRECTION_PAIRS}
    if head not in _consumed_heads and tail == "NONE" and state.get("current_task") != S1_CORRECTION_TASK:
        fail(f"correction-delivery commits present but CURRENT_STATE.current_task "
             f"{state.get('current_task')!r} is not the authorized correction task "
             f"{S1_CORRECTION_TASK}", errors)
        return
    print(f"  OK   merge {merge_sha[:12]} = ({s1['start_head'][:12]}, pinned {s1['merged_head'][:12]}); "
          f"substantive {sub[:12]}; metadata {meta[:12]}; exactly 2 task-authored commits; metadata allowlisted")


def validate_registry_s1(central, errors):
    print("\n[S1-INTEGRATION] Audit registry (S0 protections verbatim + pinned S1 record)")
    reg_path = REPO_ROOT / "docs/security/audit-evidence/audit_registry.jsonl"
    audits = {a.get("audit_id"): a for a in load_jsonl(reg_path)}
    if len(audits) != 14:
        fail(f"audit_registry.jsonl must contain exactly 14 records (13 ratified + 1 S1 integration record), found {len(audits)}", errors)
    # Run the central registry validator unchanged. The S0-era ratified validator
    # is era-pinned to 13 records, so the S1 record is hidden from it; the ratified
    # SUCCESSOR expects all 14 and must therefore see the registry unfiltered.
    # Applying the S0-era view to the successor silently removed the very record it
    # validates (retest S1-003 follow-up).
    central_state = getattr(central, "_anox_central_state", "PRE_RATIFICATION")
    if central_state == "PRE_RATIFICATION":
        original = central.load_jsonl

        def _view(path):
            recs = original(path)
            if Path(path).name == "audit_registry.jsonl":
                return [r for r in recs if r.get("audit_id") != S1_INTEGRATION_ID]
            return recs
        central.load_jsonl = _view
        try:
            central.validate_registry(errors)
        finally:
            central.load_jsonl = original
    else:
        central.validate_registry(errors)
    rec = audits.get(S1_INTEGRATION_ID)
    if rec is None:
        fail(f"{S1_INTEGRATION_ID} registry record missing (registry must carry exactly one S1 integration evidence record)", errors)
        return
    for key, expected in S1_INTEGRATION_REGISTRY_REQUIRED.items():
        if rec.get(key) != expected:
            fail(f"{S1_INTEGRATION_ID} field {key}={rec.get(key)!r}, expected {expected!r}", errors)
    srcs = rec.get("preserved_sources") or {}
    if set(srcs) != set(S1_INTEGRATION_SOURCE_SHA256):
        fail(f"{S1_INTEGRATION_ID} preserved_sources keys {sorted(srcs)} != {sorted(S1_INTEGRATION_SOURCE_SHA256)}", errors)
    for skey, (path, expected_sha) in S1_INTEGRATION_SOURCE_SHA256.items():
        srec = srcs.get(skey) or {}
        if srec.get("path") != path or srec.get("sha256") != expected_sha:
            fail(f"{S1_INTEGRATION_ID} preserved_sources.{skey} path/sha256 mismatch", errors)
        sp = REPO_ROOT / path
        if not sp.exists():
            fail(f"{S1_INTEGRATION_ID} preserved source missing: {path}", errors)
        elif sha256_file(sp) != expected_sha:
            fail(f"{S1_INTEGRATION_ID} preserved source hash mismatch: {path}", errors)
    pp = REPO_ROOT / str(rec.get("report_path", ""))
    if not pp.exists():
        fail(f"{S1_INTEGRATION_ID} integration report missing: {rec.get('report_path')}", errors)
    elif sha256_file(pp) != rec.get("report_sha256"):
        fail(f"{S1_INTEGRATION_ID} integration report hash mismatch", errors)
    print("  OK   S0 registry protections executed verbatim on the 13-record view; SEC-AUDIT-REG-0014 pinned")


def validate_scope_s1(errors):
    print("\n[S1-INTEGRATION] Scope")
    if not has_git():
        print("  SKIP git scope (no .git — fixture mode)")
        return
    s1 = S1_INTEGRATION_EVENT
    changed = [p for p in _git(["diff", "--name-only", s1["start_head"]]).stdout.splitlines() if p]
    forbidden = sorted(p for p in changed if p.startswith(S1_FORBIDDEN_PREFIXES) or p.endswith(".sql"))
    if forbidden:
        fail(f"S1 integration changed forbidden paths (product/S2+/B004+/authority): {forbidden}", errors)
    meta = set()
    central_mod, _ = load_central()
    if central_mod is not None:
        meta = set(central_mod.METADATA_ALLOWLIST)
    # After an authorized ratification tail the package paths have legitimately
    # changed — that change IS the ratification, already bound by the tail proof
    # (exact parent, exact changed-path set, exact successor content). Before it,
    # any change to the protected validator remains a hard failure.
    central_state = getattr(central_mod, "_anox_central_state", "PRE_RATIFICATION")
    ratified = central_state in ("RATIFIED_SUCCESSOR_APPLIED", "CI_DISPOSITION_APPLIED")
    exempt = set(S1_RATIFICATION_PATHS) if ratified else set()
    if central_state == "CI_DISPOSITION_APPLIED":
        exempt |= set(S1_CI_DISPOSITION_PATHS)
    outside = sorted(p for p in changed
                     if p not in S1_ALLOWED_EXACT and not p.startswith(S1_ALLOWED_PREFIXES)
                     and p not in meta and p not in exempt)
    if outside:
        fail(f"S1 integration changed paths outside the enumerated S1 surfaces: {outside}", errors)
    if CENTRAL in changed and not ratified:
        fail(f"protected shared validator {CENTRAL} changed without Human ratification", errors)
    if _git(["ls-files", "--", "*.so"]).stdout.strip():
        fail("S1 integration leaves tracked native binaries", errors)
    rust = _git(["diff", "--name-only", s1["merged_base"], "--", "crypto/rust/src/"]).stdout.strip()
    if rust:
        fail(f"crypto/rust/src/** changed vs S1 original base (native behavior change forbidden): {rust.split()}", errors)
    ci = REPO_ROOT / ".github/workflows/ci.yml"
    text = ci.read_text(encoding="utf-8") if ci.exists() else ""
    if "tools platform-tools" in text or "packages: 'platform-tools'" not in text:
        fail("CI hotfix invariant violated: setup-android must use packages: 'platform-tools' (no 'tools platform-tools')", errors)
    print(f"  OK   {len(changed)} changed path(s) within enumerated S1 surfaces; shared validator untouched; "
          f"no tracked .so; crypto/rust/src unchanged; CI hotfix intact")


def _is_s1_ci_disposition_event(ev, described_head):
    """The sealing governance event for the CI-infrastructure tail disposition.

    end_head is bound DYNAMICALLY to CURRENT_STATE.described_head (the
    disposition substantive R3a) — the event cannot pin the R3a SHA literally
    because the sealing metadata commit is authored before that SHA exists in
    the validator source; the binding is nonetheless exact through
    described_head, which the delivery topology already pins to R3a.
    """
    s1 = S1_CI_DISPOSITION_EVENT
    return (ev.get("event_id") == s1["event_id"]
            and ev.get("type") == s1["type"]
            and ev.get("task") == s1["task"]
            and ev.get("start_head") == s1["start_head"]
            and ev.get("end_head") == described_head
            and S1_CI_DISPOSITION_RECORD in (ev.get("refs") or []))


def validate_project_memory_s1(central, errors):
    print("\n[S1-INTEGRATION] Project memory chain (0052 → 0053 → 0054 → 0055)")
    state = json.loads((REPO_ROOT / "docs/continuity/CURRENT_STATE.json").read_text(encoding="utf-8"))
    ledger = load_jsonl(REPO_ROOT / "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
    if not ledger:
        fail("ledger empty", errors)
        return
    ids = [e.get("event_id") for e in ledger]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        fail(f"ledger contains duplicate event ids: {dupes}", errors)
    for e in ledger:
        if e.get("task") == S1_ORIGINAL_TASK:
            fail(f"ledger admits the isolated S1 provisional event {e.get('event_id')} as canonical "
                 f"(S1 is canonically recorded only by {S1_INTEGRATION_EVENT['event_id']})", errors)
        if e.get("task") == S1_INTEGRATION_EVENT["task"] and e.get("event_id") != S1_INTEGRATION_EVENT["event_id"]:
            fail(f"S1 integration recorded under wrong event id {e.get('event_id')}", errors)
        if e.get("task") == S1_CI_DISPOSITION_TASK and e.get("event_id") != S1_CI_DISPOSITION_EVENT["event_id"]:
            fail(f"S1 CI-tail disposition recorded under wrong event id {e.get('event_id')}", errors)
    latest = ledger[-1]
    if state.get("latest_material_event_id") != latest.get("event_id"):
        fail("Project Memory stale: latest_material_event_id != last ledger event", errors)
        return
    if _is_s1_ci_disposition_event(latest, state.get("described_head") or ""):
        # ANOX-EVENT-0058 seals the CI-infrastructure tail disposition on top
        # of the pinned S1 integration event — verify 0055 immediately below,
        # and the Human decision record it references must exist.
        if not (REPO_ROOT / S1_CI_DISPOSITION_RECORD).exists():
            fail(f"CI-tail disposition decision record missing: {S1_CI_DISPOSITION_RECORD}", errors)
            return
        s1_index = len(ledger) - 2
    else:
        s1_index = len(ledger) - 1
    s1_event = ledger[s1_index] if s1_index >= 0 else None
    if s1_event is None or not _is_s1_integration_event(s1_event):
        fail(f"the pinned S1 integration event {S1_INTEGRATION_EVENT['event_id']} must be the last "
             f"ledger event or sit directly below the pinned CI-disposition event "
             f"{S1_CI_DISPOSITION_EVENT['event_id']}, got {latest.get('event_id')}", errors)
        return
    if not (s1_index >= 3 and central._is_s0_preservation_event(ledger[s1_index - 1])
            and central._is_s0_successor_event(ledger[s1_index - 2])
            and ledger[s1_index - 3].get("event_id") == central.LEDGER_EVENT):
        fail(f"{S1_INTEGRATION_EVENT['event_id']} must directly follow the pinned chain "
             f"{central.LEDGER_EVENT} → {central.S0_SUCCESSOR_EVENT['event_id']} → {central.S0_PRESERVATION_EVENT['event_id']}", errors)
    if not _s1_delivery_active(state):
        fail(f"{S1_INTEGRATION_EVENT['event_id']} recorded but CURRENT_STATE does not declare the S1 integration "
             f"delivery (task/branch) — S0 one-time exception is not reusable for S1", errors)
    raw = (REPO_ROOT / "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl").read_bytes().splitlines()
    overlong = [i + 1 for i, line in enumerate(raw) if len(line) > central.LEDGER_MAX_LINE_BYTES]
    if overlong:
        fail(f"ledger line-size violation (> {central.LEDGER_MAX_LINE_BYTES} bytes) at lines {overlong}", errors)
    if not errors:
        print(f"  OK   Project Memory synced to {latest.get('event_id')} (S1 canonical-integration successor of "
              f"{central.S0_PRESERVATION_EVENT['event_id']}; provisional isolated "
              f"{S1_INTEGRATION_EVENT['supersedes_provisional_event']} NONCANONICAL)")


def _normalise_pin(value):
    """Order-insensitive, container-insensitive comparison of pin values."""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(sorted(_normalise_pin(v) for v in value))
    return value


def _check_proposed_pin_drift(proposed_path, errors):
    """B-2/N-9 anti-drift gate (REMEDIATION-S1-FINAL-CORRECTIONS-001).

    The delivery-shape pins are duplicated on purpose: the Human-ratified central
    validator is authoritative, and this S1-side validator carries the same
    values. They are deliberately NOT collapsed into a shared module, because the
    only file both could import (tools/audit/lifecycle_legality.py) is S1-writable
    — delegating there would let the S1 session widen the acceptance criteria of
    the validator meant to constrain it.

    The cost of duplication is silent drift, and that is exactly what made the
    previous ratification proposal reject the tree it governs: it pinned the
    pre-ratification task id and a 3/5-commit chain. So the PROPOSED content (the
    artifact actually awaiting Human ratification) is imported here and every
    duplicated pin must match this validator EXACTLY, or ratification is blocked.
    This runs pre-ratification, which is precisely when it is useful.
    """
    spec = importlib.util.spec_from_file_location("anox_proposed_central", proposed_path)
    if spec is None or spec.loader is None:
        fail("cannot load the proposed central validator for pin-drift comparison", errors)
        return
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001 - any import failure is fail-closed
        fail(f"proposed central validator is not importable ({type(exc).__name__}: {exc})", errors)
        return
    before = len(errors)
    for name, mine in (("S1_CORRECTION_TASKS", S1_CORRECTION_TASKS),
                       ("S1_CORRECTION_TASK", S1_CORRECTION_TASK),
                       ("S1_CONSUMED_CORRECTION_PAIRS", CONSUMED_CORRECTION_PAIRS),
                       ("S1_SUBSTANTIVE_SHA", S1_SUBSTANTIVE_SHA),
                       ("S1_METADATA_SHA", S1_METADATA_SHA),
                       # B-6: the four-path set is the whole point of the
                       # transaction; silent drift here is what made the previous
                       # package uncommittable, so it is pin-checked too.
                       ("S1_RATIFICATION_PATHS", S1_RATIFICATION_PATHS),
                       # CI-infrastructure tail disposition pins (same
                       # duplicated-on-purpose discipline).
                       ("S1_CI_TAIL", S1_CI_TAIL),
                       ("S1_CI_DISPOSITION_PATHS", S1_CI_DISPOSITION_PATHS),
                       ("S1_CI_DISPOSITION_TASK", S1_CI_DISPOSITION_TASK),
                       ("S1_CI_ARM64_ISOLATION_TASK", S1_CI_ARM64_ISOLATION_TASK)):
        if not hasattr(mod, name):
            fail(f"proposed central validator does not define {name} — the ratification package "
                 f"would not recognise the authorized delivery shape", errors)
            continue
        theirs = getattr(mod, name)
        if _normalise_pin(theirs) != _normalise_pin(mine):
            fail(f"pin drift: proposed central {name}={theirs!r} != S1-side {mine!r}", errors)
    missing = sorted(set(S1_ALLOWED_EXACT) - set(getattr(mod, "S1_ALLOWED_EXACT", ())))
    if missing:
        fail(f"scope drift: paths allowed S1-side but not by the proposed central validator: {missing}", errors)
    if len(errors) == before:
        print("  OK   proposed central validator agrees with every S1-side delivery pin "
              "(tasks, consumed correction pairs, C1/C2 pins, scope allow-list)")


def validate_ratification_proposal(errors):
    """The prepared S1-era extension is preserved tamper-evidently: applying the
    patch to the pre-ratification content must yield exactly the pinned post-image
    for ALL FOUR files of the atomic ratification transaction — the protected
    central validator, its paired adversarial suite, the frozen S0 contract that
    pins the protected validator, and the S0 contract's paired suite."""
    print("\n[S1-INTEGRATION] Shared-validator ratification proposal integrity")
    central_mod, _ = load_central()
    central_state = getattr(central_mod, "_anox_central_state", "PRE_RATIFICATION") if central_mod else "PRE_RATIFICATION"
    applied_images = {
        "RATIFIED_SUCCESSOR_APPLIED": S1_RATIFICATION_POST_IMAGES,
        "CI_DISPOSITION_APPLIED": {rel: S1_CI_DISPOSITION_POST_IMAGES[rel]
                                   for rel in S1_RATIFICATION_POST_IMAGES},
    }
    if central_state in applied_images:
        # The transaction has been ratified and applied: the patch can no
        # longer be re-applied to already-migrated files. Integrity is instead
        # the identity of the live content with the pinned post-images of the
        # authorized era — for all four package files.
        want_map = applied_images[central_state]
        for rel, want in sorted(want_map.items()):
            got = sha256_file(REPO_ROOT / rel)
            if got != want:
                fail(f"applied {rel} {got[:16]}… != pinned authorized {want[:16]}…", errors)
        if not errors:
            if central_state == "CI_DISPOSITION_APPLIED":
                print("  OK   applied four-file transaction matches the pinned authorized post-images exactly ("
                      + ", ".join(f"{v[:12]}…" for _, v in sorted(want_map.items())) + ")")
            else:
                print("  OK   ratified four-file transaction matches the pinned proposal exactly ("
                      + ", ".join(f"{v[:12]}…" for _, v in sorted(want_map.items())) + ")")
        return
    patch = REPO_ROOT / PROPOSAL_PATCH
    record = REPO_ROOT / PROPOSAL_RECORD
    if not record.exists():
        fail(f"ratification proposal record missing: {PROPOSAL_RECORD}", errors)
    else:
        rec_text = record.read_text(encoding="utf-8")
        for rel, want in sorted(S1_RATIFICATION_POST_IMAGES.items()):
            if want not in rec_text:
                fail(f"ratification proposal record does not carry the proposed post-image for {rel}", errors)
        for dead in SUPERSEDED_NEVER_RATIFY:
            if dead in rec_text and "SUPERSEDED" not in rec_text:
                fail("ratification proposal record names a superseded revision without marking it SUPERSEDED", errors)
    if not patch.exists():
        fail(f"ratification proposal patch missing: {PROPOSAL_PATCH}", errors)
        return
    with tempfile.TemporaryDirectory(prefix="anox-s1-proposal-") as td:
        td = Path(td)
        subprocess.run(["git", "init", "-q"], cwd=td, check=True)
        for rel, pre in sorted(S1_RATIFICATION_PRE_IMAGES.items()):
            src = REPO_ROOT / rel
            if not src.exists():
                fail(f"ratification package pre-image missing: {rel}", errors)
                return
            got = sha256_file(src)
            if got != pre:
                fail(f"ratification package pre-image {rel} is {got[:16]}… != pinned {pre[:16]}… — "
                     f"the transaction no longer applies to the delivered tree", errors)
                return
            dst = td / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
        r = subprocess.run(["git", "apply", str(patch)], cwd=td, capture_output=True, text=True)
        if r.returncode != 0:
            fail(f"ratification proposal patch does not apply to the delivered content: {r.stderr.strip()[:200]}", errors)
            return
        changed = sorted(p.relative_to(td).as_posix() for p in td.rglob("*.py"))
        if changed != sorted(S1_RATIFICATION_POST_IMAGES):
            fail(f"ratification transaction touches {changed} — it must be exactly the four package paths "
                 f"{sorted(S1_RATIFICATION_POST_IMAGES)}", errors)
            return
        for rel, want in sorted(S1_RATIFICATION_POST_IMAGES.items()):
            got = sha256_file(td / rel)
            if got != want:
                fail(f"ratification proposal yields {rel} {got[:16]}… != pinned proposed {want[:16]}…", errors)
                return
        _check_proposed_pin_drift(td / CENTRAL, errors)
    print(f"  OK   proposal patch applies to the delivered four-file pre-image set and yields exactly "
          f"{CENTRAL_PROPOSED_SHA256[:12]}… + {CENTRAL_TESTS_PROPOSED_SHA256[:12]}… + "
          f"{S0_CONTRACT_PROPOSED_SHA256[:12]}… + {S0_CONTRACT_TESTS_PROPOSED_SHA256[:12]}… "
          f"(awaiting Human ratification; {len(SUPERSEDED_NEVER_RATIFY)} superseded revisions must never be ratified)")


def main():
    errors = []
    central, why = load_central()
    if central is None:
        print(f"  FAIL {why}")
        print("\nS1 INTEGRATION EVIDENCE: FAIL")
        return 1
    validate_base_s1(central, errors)
    # S0 protections — executed verbatim from the ratified module.
    print("\n[S1-INTEGRATION] Ratified S0 protections (verbatim)")
    for fn in (central.validate_reports, central.validate_traceability, central.validate_cryptojni,
               central.validate_authdpop, central.validate_androidstorage, central.validate_attackchain,
               central.validate_master_consolidation, central.validate_coverage_gate,
               central.validate_human_decision_layer, central.validate_findings, central.validate_lifecycle,
               central.validate_tasks):
        fn(errors)
    validate_registry_s1(central, errors)
    validate_scope_s1(errors)
    validate_project_memory_s1(central, errors)
    validate_ratification_proposal(errors)
    if errors:
        print("\nS1 INTEGRATION EVIDENCE: FAIL")
        for e in errors:
            print(f"  FAIL {e}")
        return 1
    print("\nS1 INTEGRATION EVIDENCE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
