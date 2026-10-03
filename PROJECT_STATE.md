# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-10-03
**Latest local delivery (unsealed, `Awaiting Review` — bounded correction applied, delta review pending):** `HANDOFF-UNSEALED-EXCEPTION-001` (`ANOX-TASK-HANDOFF-UNSEALED-EXCEPTION-001`, ROLE-004) on `governance/handoff-unsealed-exception-001` under `ANOX-DECISION-HANDOFF-UNSEALED-EXCEPTION-001` — SEC-C governance-tool change: `generate_handoff.py --allow-unsealed` stamps `MANIFEST.txt` (`SEAL_STATUS=UNSEALED_AT_GENERATION` + `SEAL_DESCRIBED_HEAD` + `SEAL_LAST_SEALED`); `validate_continuity.py --mode archive` accepts exactly-matching declarations as `PASS — DECLARED_UNSEALED` (undeclared/forged/tampered/partial/duplicate stamps fail closed — ANY `SEAL_*` field = stamp present, complete triple exactly-once required); 19 adversarial tests; `HANDOFF_WORKFLOW.md` documents the exception; sealing remains recommended. ROLE-002 verdict `BLOCKED` 2026-10-03 → bounded correction applied (strict stamp parsing, hermetic fixtures, stale-state sync; findings `ANOX-FINDING-ROLE002-HANDOFF-UNSEALED-001..003` Closed; `ANOX-TASK-REVIEW-HANDOFF-UNSEALED-001` + `ANOX-PROMPT-REVIEWHU001` retro-registered; `required_evidence E3`) — ROLE-002 delta review pending. Prior lifecycle delivery `B028-SYNC-LIFECYCLE-FINALIZATION-001` was **merged to `main`** via PR #48 at canonical merge `b4e10e70811ae2e567a2289410c490c347fe3e6e` (parents `c1a7ebf` + `170e88f`; merge tree verified identical to the reviewed delivery) — its bundled records (`ANOX-EVENT-0068` seal sync, `previous_merges += b4e10e7`, task → `Merged`) ride in this delivery. Advisory boundary unchanged: pinned validators remain acceptance authority; `ANOX-TASK-B028-DUAL-RUN-CUTOVER-001` remains Candidate (unbound) pending real dual-run parity + separate human cutover decision. SEC-C tooling change only; no product/crypto/android/CI/secret change; no finding/MSC closure (OPEN=42/CLOSED=0); no ledger event appended by this delivery (tail `ANOX-EVENT-0068`); remote mutation NONE; HANDOFF_REQUESTED=NO. S2 C-01 resync delivery on `remediation/s2-c01-resync-correction-002` continues independently awaiting ROLE-002 delta review.
**Latest material event:** `ANOX-EVENT-0054` — SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001: complete corrected S0 evidence chain preserved (implementation PASS; INDEPENDENT-ARCHITECTURE-RETEST-S0-001 PASS_WITH_FINDINGS as human-authorized reconstruction; correction PASS; TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001 PASS_WITH_FINDINGS — F-01 RATIFIED, F-02…F-10 FIXED, merge blockers 0, 2 residual LOW non-blocking); shared validator extended one-time under ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001 (EVENT-0054 + registry 12→13, all pinned); dedicated validator + 40 tests; S0_MERGE_READINESS=READY; security remediation IN_PROGRESS; S1 isolated/not integrated; 0 MSC units closed (42 open); B-004/B-005 NOT_STARTED; product BLOCKED_PENDING_FINAL_AUDIT.
**Post-0054 delivery state (unsealed, recorded in current-state surfaces only):** the S0 evidence chain is merged to `main` at `29a6643` (PR #36), and `REMEDIATION_SESSION_S1` is **merged to `main`** at canonical merge `2dc6b7453ef292c30f32c02e0eb213e1ef5496cb` (PR #38 via `integration/s1-fresh-after-s0-001` — now a historical delivery branch; integrated delivery tip `3ed46b717172d512f75672c83d58327a52ac3c61` = implementation `62b07a1` + continuity seal `69279ce` + ARM64 CI disposition). No new canonical Project Memory event is sealed in this transition: the ledger tail remains pinned to `ANOX-EVENT-0054` by the S0-era preservation validators, and the canonical S1 event identity is regenerated under a human-ratified validator extension.
**Memory schema:** M2B-v1

<!-- ANOX_EVENT: ANOX-EVENT-0021 -->
<!-- ANOX_EVENT: ANOX-EVENT-0022 -->
<!-- ANOX_EVENT: ANOX-EVENT-0023 -->
<!-- ANOX_EVENT: ANOX-EVENT-0024 -->
<!-- ANOX_EVENT: ANOX-EVENT-0025 -->
<!-- ANOX_EVENT: ANOX-EVENT-0026 -->
<!-- ANOX_EVENT: ANOX-EVENT-0027 -->
<!-- ANOX_EVENT: ANOX-EVENT-0028 -->
<!-- ANOX_EVENT: ANOX-EVENT-0029 -->
<!-- ANOX_EVENT: ANOX-EVENT-0030 -->
<!-- ANOX_EVENT: ANOX-EVENT-0031 -->
<!-- ANOX_EVENT: ANOX-EVENT-0032 -->
<!-- ANOX_EVENT: ANOX-EVENT-0033 -->
<!-- ANOX_EVENT: ANOX-EVENT-0034 -->
<!-- ANOX_EVENT: ANOX-EVENT-0035 -->
<!-- ANOX_EVENT: ANOX-EVENT-0036 -->
<!-- ANOX_EVENT: ANOX-EVENT-0037 -->
<!-- ANOX_EVENT: ANOX-EVENT-0038 -->
<!-- ANOX_EVENT: ANOX-EVENT-0039 -->
<!-- ANOX_EVENT: ANOX-EVENT-0040 -->
<!-- ANOX_EVENT: ANOX-EVENT-0041 -->
<!-- ANOX_EVENT: ANOX-EVENT-0042 -->
<!-- ANOX_EVENT: ANOX-EVENT-0043 -->
<!-- ANOX_EVENT: ANOX-EVENT-0044 -->
<!-- ANOX_EVENT: ANOX-EVENT-0045 -->
<!-- ANOX_EVENT: ANOX-EVENT-0046 -->
<!-- ANOX_EVENT: ANOX-EVENT-0047 -->
<!-- ANOX_EVENT: ANOX-EVENT-0048 -->
<!-- ANOX_EVENT: ANOX-EVENT-0049 -->
<!-- ANOX_EVENT: ANOX-EVENT-0050 -->
<!-- ANOX_EVENT: ANOX-EVENT-0051 -->
<!-- ANOX_EVENT: ANOX-EVENT-0052 -->
<!-- ANOX_EVENT: ANOX-EVENT-0053 -->
<!-- ANOX_EVENT: ANOX-EVENT-0054 -->
<!-- ANOX_EVENT: ANOX-EVENT-0060 -->
<!-- ANOX_EVENT: ANOX-EVENT-0061 -->
<!-- ANOX_EVENT: ANOX-EVENT-0062 -->
<!-- ANOX_EVENT: ANOX-EVENT-0063 -->
<!-- ANOX_EVENT: ANOX-EVENT-0064 -->
<!-- ANOX_EVENT: ANOX-EVENT-0065 -->
<!-- ANOX_EVENT: ANOX-EVENT-0066 -->
<!-- ANOX_EVENT: ANOX-EVENT-0068 -->

## Active delivery — Handoff unsealed exception (2026-10-03)

`ANOX-TASK-HANDOFF-UNSEALED-EXCEPTION-001` is the authorized SEC-C governance-tool delivery on `governance/handoff-unsealed-exception-001` (ROLE-004, reviewer ROLE-002, `security_class S1`, `data_egress D2`, `priority P2`, `required_evidence E3`, `remote_permission NONE`), based on canonical merge `b4e10e70811ae2e567a2289410c490c347fe3e6e` (PR #48 — `B028-SYNC-LIFECYCLE-FINALIZATION-001` merged to `main`; parents `c1a7ebf` + `170e88f`; merge tree identical to the reviewed delivery). Under `ANOX-DECISION-HANDOFF-UNSEALED-EXCEPTION-001` (Human Owner, canonically registered): `generate_handoff.py --allow-unsealed` stamps `MANIFEST.txt` (`SEAL_STATUS=UNSEALED_AT_GENERATION` + `SEAL_DESCRIBED_HEAD` + `SEAL_LAST_SEALED`); `validate_continuity.py --mode archive` reports `PASS — DECLARED_UNSEALED` only for exactly-matching declarations — undeclared unsealed, forged/mismatched/partial stamps, and stamps on sealed packages fail closed; no other check weakened; ledger/seal semantics unchanged; sealing remains recommended. `described_head` = this delivery's own substantive checkpoint — unsealed by design. The bundled `ANOX-EVENT-0068` seal sync was separately human-authorized under the finalization task's second scope extension. `HANDOFF_REQUESTED=NO`; `HANDOFF_PACKAGE_GENERATION=NOT_EXECUTED`; no push/PR/real merge by this delivery.

## Repository truth

- Branch: `governance/handoff-unsealed-exception-001` (created from PR #48 merge `b4e10e7`)
- **Described HEAD:** `28e92beb68b5e958abd54636ba3650014149290c` (this delivery's own substantive checkpoint — the SEC-C tools + registries commit; **unsealed** — the declared-unsealed exception covers handoff generation; merged finalization checkpoint `b8248b5` sealed as `ANOX-EVENT-0068` `end_head` remains the semantic anchor recorded in `previous_merges`; live HEAD is derived from Git, not predicted in tracked metadata)
- **Canonical base:** `b4e10e70811ae2e567a2289410c490c347fe3e6e` (verified `main` = `origin/main` — PR #48 merge)
- **Canonical repository:** `https://github.com/anox-software/anox-messenger`
- **Legacy repository:** `https://github.com/anox-admin/ax-messenger.git` (historical provenance only)
- SEC-C governance-tooling change only (`tools/continuity/` + `HANDOFF_WORKFLOW.md`); no product, backend, SQL, CI, native-artifact, or secret changes; remote mutation NONE; no MSC unit closed; no finding re-severitied; no audit re-run; no ledger/seal semantics change.
- Next: human review/merge of this delivery to `main`; S2 C-01 delta review continues independently on `remediation/s2-c01-resync-correction-002`; `ANOX-TASK-B028-DUAL-RUN-CUTOVER-001` remains Candidate pending parity evidence + separate human decision.

## ANOX-EVENT-0060…0066 — POST-0054-LEDGER-CANONICALIZATION-001 (2026-09-30) — MERGED via PR #42 (`3414fb2…`)


- Branch: `governance/post-0054-ledger-canonicalization-001`
- Substantive commit: `978b7d03273b588599668e7fe02f87a74de98169` (pinned validator extension + Human decision/task records + 50-test adversarial suite)
- Canonical base SHA: `270cdb92762965eea3236177710c88c259d4b33f` (PR #41 merge)
- Task ID: `ANOX-TASK-POST-0054-LEDGER-CANONICALIZATION-001`
- Decision: `ANOX-DECISION-POST-0054-LEDGER-CANONICALIZATION-001` (`HUMAN_RATIFIED_CHANGE_SPECIFIC_SHARED_VALIDATOR_EXTENSION`, `ONE_TIME_CHANGE_SPECIFIC`); record `docs/reports/security/decisions/POST-0054-LEDGER-CANONICALIZATION-001.md`
- Result: `Ready For Remote` — resolves the post-PR-#41 final-handoff blocker `PROJECT_MEMORY_FRESHNESS: FAIL — AUTHORED MATERIAL CHECKPOINT WITHOUT LEDGER EVENT`
- `ANOX-EVENT-0060…0065` record the six real canonical merges after `ANOX-EVENT-0054` (`canonical_merge`): `ea838fa5` PR #35 CI hotfix; `29a6643` PR #36 S0 evidence preservation; `2dc6b745` PR #38 S1 integration; `cb9aee0` PR #39 S1 post-merge continuity; `02179ecd` PR #40 S2 bootstrap/scope freeze; `270cdb92` PR #41 S2 C-01 pre-authorization anchor. `ANOX-EVENT-0066` (`post_0054_ledger_canonicalization`) seals the correction's substantive checkpoint `978b7d03`.
- Event ids `0055–0059` remain reserved to the non-canonical archived line `archive/local-main-pre-pr38-20260926` and were not reused.
- Protected shared validator `tools/audit/validate_security_audit_evidence_preservation.py` extended fail-closed: accepts only the exact `ANOX-EVENT-0060…0066` chain after `ANOX-EVENT-0054`; new ratified hash `adde793ed921c02d2c741826e0a8beca144e78a14cb5e4cd06d76702b2687879` (prior ratified hashes remain accepted). `validate_s0_evidence_preservation.py` accepts this exact chain only with the canonicalization decision/report present; `validate_s0_contract_freeze.py` ratifies the new digest. New adversarial suite `tools/audit/test_post_0054_ledger_canonicalization.py` (50 tests).
- S0 evidence and `ANOX-EVENT-0054` unchanged. `MSC OPEN=42 / CLOSED=0`; `B004/B005` `NOT_STARTED`; S2/S3/S4 remediation not closed; C-01/R09 **not fixed** (correction pending on `remediation/s2-correction-001`); product `BLOCKED_PENDING_FINAL_AUDIT`; `ARM64 UNVERIFIED_PENDING_REAL_ARM64_RUNTIME`; remote mutation `NONE`.
- Next: human review/merge of this governance delivery to `main`, then the authorized C-01 validator correction on `remediation/s2-correction-001`.
