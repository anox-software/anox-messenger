# CURRENT_GIT_STATE — anoX V1

**Event:** `ANOX-EVENT-0058`
**Branch (runtime):** `__HANDOFF_BRANCH__`
**HEAD (runtime):** `__HANDOFF_HEAD__`
**Working tree (runtime):** `__WORKING_TREE__`

- **Canonical branch:** `main`
- **Canonical baseline:** `29a6643189242a47c4a79c38acd04c1eca748787`
- **Substantive HEAD:** `ca94bb91f3d2489c0e4db46cec6549043930e09d` (R3a disposition substantive — sealed by ANOX-EVENT-0058)
- **Previous baseline:** `0f932520393feee6d479cc099f179f5766323125`
- **Effective gate (runtime):** `__EFFECTIVE_GATE__`

Described HEAD: ca94bb91f3d2489c0e4db46cec6549043930e09d

## Post-R2 delivery tail — DISPOSITIONED 2026-09-22 (ANOX-EVENT-0058)

Under Human decision `ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001` the four post-R2 ci.yml-only commits `e7bd2c6547fb` (full Git history for S1 provenance gate), `0636a4ee81e2` (pinned NDK path), `793246022c05` (emulator startup + x86 AVD hardening), `45d1e4a63de4` (self-hosted ARM64 routing) plus ARM64-isolation commit `4fc5263ff676` (`ANOX-TASK-S1-CI-ARM64-ISOLATION-001`: deterministic stale-emulator kill + bounded wait + fail-closed + single-device assertion + `if: always()` cleanup) are admitted as the pinned authorized CI tail — bound by exact SHA, exact order, position only after the completed R1/R2 pair (`e65c23d0b8a9`/`05dbcad25ab7`), and ci.yml-only paths. Disposition pair [`R3a ca94bb91f3d2` substantive + `R3b` metadata] seals the transaction; sealing governance event `ANOX-EVENT-0058` follows `ANOX-EVENT-0055`; `described_head` = R3a `ca94bb91f3d2`. The canonical decision record `docs/reports/security/decisions/S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001.md` pins every post-image sha256. No product/crypto code authorized; no required gate removed; x86_64 remains REQUIRED (INFRASTRUCTURE_BLOCKED by GitHub billing — not a code pass); ARM64 runtime re-verification pending next CI run. PR #37 NOT merged.

## Pre-merge gate

`REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001 — HUMAN-AUTHORIZED FOUR-FILE RATIFICATION TRANSACTION (retest S1-004 B-6 closed: the ratification is now ONE atomic R1 over exactly four paths — validate/test_security_audit_evidence_preservation.py plus the frozen S0 contract validate/test_s0_contract_freeze.py that pins it — because a two-path R1 broke the S0 contract with no authorized repair path; optional metadata-only R2 advances described_head and records the Human ratification; nothing beyond R1/R2; consumed pairs [0d1549d12d02, f08749e2e5ec], [a79e3b3db9b4, 4319dacaa7ac] and [4b31f6806136, 10cc68c442bc]; N-13/N-14 corrected; 859e834e0687… + c305c21c9405… + 7dbcaf60d7ba… + d22034e61257… CURRENT PROPOSAL (four-file transaction); e52f626a46f2… SUPERSEDED/NEVER RATIFY; d03e539a49e9… SUPERSEDED/NOT COMMITTABLE/NEVER RATIFY; 87cd5e202325… SUPERSEDED BY THE FOUR-FILE PACKAGE/NEVER RATIFY; Shared Validator remains a PROPOSAL, NOT Human-ratified; NOT INDEPENDENTLY VERIFIED — targeted independent re-verification of the committed R1/R1+R2 simulation required; MSC 42 open / 0 closed; B004/B005 NOT_STARTED; no push/PR/merge)`

## Post-merge gate

`SECURITY_REMEDIATION_WAVE_1 — REMEDIATION_SESSION_S0 MERGED_TO_MAIN ∥ REMEDIATION_SESSION_S1 INTEGRATED_ON_MAIN_LINEAGE + F1-F9 REMEDIATED (pending targeted independent integration retest; wave-completion Candidate; security remediation IN_PROGRESS; x86_64 runtime evidence PENDING_REAL_CI_OR_INDEPENDENT_RUNTIME_EVIDENCE; next: TARGETED-INDEPENDENT-INTEGRATION-RETEST-S1-001 → human merge → S2 ∥ S3)`
