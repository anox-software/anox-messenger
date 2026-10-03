# Project Memory Surface Index — anoX V1

**Latest material event:** ANOX-EVENT-0066
**Latest human history event:** ANOX-EVENT-0066

| Surface | Latest reference |
|---------|-----------------|
| CURRENT_STATE.json | ANOX-EVENT-0066 |
| CURRENT_GIT_STATE.md | ANOX-EVENT-0066 |
| CURRENT_HANDOFF.md | ANOX-EVENT-0066 |
| CURRENT_OPEN_WORK.md | ANOX-EVENT-0066 |
| CURRENT_NEXT_DEVIN_TASK.md | ANOX-EVENT-0066 |
| CURRENT_IMPLEMENTATION_STATE.md | ANOX-EVENT-0066 |
| PROJECT_STATE.md | ANOX-EVENT-0066 |
| FORTSCHRITT.md | ANOX-EVENT-0066 |
| DEVIN_PROMPT_OUTPUT_ARCHIV.md | ANOX-EVENT-0066 |
| WORKFORCE_STATE.json | ANOX-EVENT-0066 |
| findings.jsonl | ANOX-EVENT-0052 |
| tasks.jsonl | ANOX-EVENT-0066 |
| runs.jsonl | ANOX-EVENT-0044 |
| audits.jsonl | ANOX-EVENT-0044 |
| decisions.jsonl | ANOX-EVENT-0066 |
| PROJECT_HISTORY_LEDGER.jsonl | ANOX-EVENT-0066 |
| docs/authority/* (AUTHORITY_INDEX, B_FREEZE_REGISTRY, B025_MANDATORY_AMENDMENTS_V1_4, contracts/S0_CONTRACT_FREEZE_MANIFEST.json) | ANOX-EVENT-0053 |
| docs/current/DATABASE_ARCHITECTURE.md, BACKEND_ARCHITECTURE.md (schema deference) | ANOX-EVENT-0053 |
| docs/reports/security/remediation/* (S0 task record; S0 preservation task record) | ANOX-EVENT-0054 |
| FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT.md | ANOX-EVENT-0044 |
| FINAL_PRE_PRODUCT_WORKFORCE_ARCHITECTURE_AUDIT.md | ANOX-EVENT-0043 |
| FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md | ANOX-EVENT-0037 |
| FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md | ANOX-EVENT-0035 |
| docs/security/audit-evidence/* (index, registry, traceability, hashes, reproductions) | ANOX-EVENT-0054 (13-record registry incl. SEC-AUDIT-REG-0013) |
| docs/reports/security/audits/* (9 preserved reports) | ANOX-EVENT-0049 |
| docs/reports/security/consolidation/* (master consolidation report) | ANOX-EVENT-0050 |
| docs/reports/security/gates/* (coverage gate report) | ANOX-EVENT-0052 |
| docs/reports/security/decisions/* (human decision records: HUMAN-PRE-REMEDIATION-DECISIONS-001; S0-F01-FILE-OWNERSHIP-RATIFICATION-001; S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001; POST-0054-LEDGER-CANONICALIZATION-001) | ANOX-EVENT-0066 |

Surface updates in this event:
- `docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md` — new canonical Pre-B004 Security Contract Freeze (`S0-CONTRACT-FREEZE v1`, 124 clauses) (ANOX-EVENT-0053)
- `docs/authority/contracts/S0_CONTRACT_FREEZE_MANIFEST.json` — clause registry / SC-CC-breaker maps / stage proposals (ANOX-EVENT-0053)
- `docs/authority/AUTHORITY_INDEX.md` (precedence entry 11; schema authority home; B004/B005 contract precedence rule), `docs/authority/B_FREEZE_REGISTRY.md` (B-002/003/004/005/006/007/009/013 → V1.4; B-002/B-009 retain TRACK_B base pointers) (ANOX-EVENT-0053)
- `docs/current/DATABASE_ARCHITECTURE.md`, `docs/current/BACKEND_ARCHITECTURE.md` — defer to `DB-SCHEMA-V1-FROZEN`; "not frozen" superseded (ARCH-004) (ANOX-EVENT-0053)
- `tools/audit/validate_s0_contract_freeze.py` + `tools/audit/test_s0_contract_freeze.py` — new S0-owned fail-closed validator (PASS) + 98 adversarial tests (53 original + 45 correction) (ANOX-EVENT-0053)
- `tools/audit/validate_security_audit_evidence_preservation.py` — additive acceptance of the single recorded S0 successor event (ANOX-EVENT-0053); `PROTECTED_SHARED_GOVERNANCE_FILE` under `ANOX-DECISION-S0-F01-RATIFICATION-001`; tests 253/253
- `tools/audit/test_security_audit_evidence_preservation.py` — +18 F-06 successor-event adversarial tests (ANOX-EVENT-0053)
- `docs/reports/security/decisions/S0-F01-FILE-OWNERSHIP-RATIFICATION-001.md` — Human ratification record for the disclosed file-ownership deviation (F-01; one-time, change-specific) (ANOX-EVENT-0053)
- `docs/workforce/registries/decisions.jsonl` — `ANOX-DECISION-S0-F01-RATIFICATION-001` (ANOX-EVENT-0053)
- `docs/reports/security/remediation/REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md` — S0 task record incl. correction appendix F-01…F-10 (ANOX-EVENT-0053)
- `docs/workforce/registries/tasks.jsonl` (ANOX-EVENT-0053; `ANOX-TASK-REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001` Ready For Remote)
- `docs/continuity/CURRENT_STATE.json` (ANOX-EVENT-0053; described_head sealed to substantive commit; pre_merge_gate REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001; post_merge_gate SECURITY_REMEDIATION_WAVE_1 in progress)
- `docs/continuity/CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, `CURRENT_OPEN_WORK.md`, `CURRENT_NEXT_DEVIN_TASK.md`, `CURRENT_IMPLEMENTATION_STATE.md` (ANOX-EVENT-0053)
- `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md` (ANOX-EVENT-0053)
- `docs/workforce/WORKFORCE_STATE.json` (ANOX-EVENT-0053; described_head sealed; next_phase SECURITY_REMEDIATION_WAVE_1 (in progress); previous baseline += 9e585468d081)
- `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` (ANOX-EVENT-0053)
- `docs/reports/security/decisions/S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001.md` — Human ratification record for the one-time shared-validator lifecycle extension (ANOX-EVENT-0054)
- `docs/reports/security/remediation/SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001.md` — S0 preservation task record (ANOX-EVENT-0054)
- `docs/reports/security/retests/INDEPENDENT-ARCHITECTURE-RETEST-S0-001.md` — first independent S0 retest preserved as HUMAN_AUTHORIZED_RECONSTRUCTED_SECURITY_EVIDENCE (ANOX-EVENT-0054)
- `docs/reports/security/retests/TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001.md` — targeted independent retest of F-01…F-10 corrections, PASS_WITH_FINDINGS (ANOX-EVENT-0054)
- `docs/security/audit-evidence/audit_registry.jsonl` — +`SEC-AUDIT-REG-0013` SECURITY_REMEDIATION_EVIDENCE (12 → 13 records, pinned) (ANOX-EVENT-0054)
- `docs/security/audit-evidence/audit_traceability.jsonl`, `evidence_hashes.json`, `AUDIT_EVIDENCE_INDEX.md` — S0 unit/finding/follow-up/summary/lifecycle records (ANOX-EVENT-0054)
- `tools/audit/validate_security_audit_evidence_preservation.py` — pinned lifecycle extension: sole successor `ANOX-EVENT-0054` after `ANOX-EVENT-0053`, registry 12 → 13 for exactly `SEC-AUDIT-REG-0013`; PROTECTED_SHARED_GOVERNANCE_FILE under `ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001` (ONE_TIME_CHANGE_SPECIFIC) (ANOX-EVENT-0054)
- `tools/audit/validate_s0_evidence_preservation.py` + `tools/audit/test_s0_evidence_preservation.py` — dedicated fail-closed S0-preservation validator + 40 adversarial tests (ANOX-EVENT-0054)
- `tools/audit/test_security_audit_evidence_preservation.py` — +24 preservation-lifecycle adversarial tests (253 → 277) (ANOX-EVENT-0054)
- `tools/audit/validate_s0_contract_freeze.py` + `tools/audit/test_s0_contract_freeze.py` — protected-file pin extended for the ratified post-extension SHA (ANOX-EVENT-0054)
- `docs/workforce/registries/decisions.jsonl` — `ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001` (ANOX-EVENT-0054)
- `docs/workforce/registries/tasks.jsonl` (ANOX-EVENT-0054; `ANOX-TASK-SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001` Ready For Remote)
- `docs/continuity/CURRENT_STATE.json` (ANOX-EVENT-0054; described_head sealed to substantive commit `24576ec333f3`; pre_merge_gate SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001; post_merge_gate MERGE_S0_INTO_MAIN → post-S0 S1 integration)
- `docs/continuity/CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, `CURRENT_OPEN_WORK.md`, `CURRENT_NEXT_DEVIN_TASK.md`, `CURRENT_IMPLEMENTATION_STATE.md` (ANOX-EVENT-0054)
- `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md` (ANOX-EVENT-0054)
- `docs/workforce/WORKFORCE_STATE.json` (ANOX-EVENT-0054; described_head sealed; next_phase SECURITY_REMEDIATION_WAVE_1 (in progress))
- `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` (ANOX-EVENT-0054)

Post-merge surface updates (metadata-only, still under sealed tail ANOX-EVENT-0054):
- `S1-CLEAN-REBUILD-CONTINUITY-TRANSITION-001` (2026-09-23, commit `69279ce` on `integration/s1-fresh-after-s0-001`): CURRENT_STATE.json, CURRENT_GIT_STATE.md, CURRENT_HANDOFF.md, CURRENT_OPEN_WORK.md, CURRENT_NEXT_DEVIN_TASK.md, CURRENT_IMPLEMENTATION_STATE.md, PROJECT_STATE.md, FORTSCHRITT.md, WORKFORCE_STATE.json, tasks.jsonl.
- `S1-POST-MERGE-CONTINUITY-SYNC-001` (2026-09-27, uncommitted on `main@2dc6b745`): the same current-state/handoff/workforce surfaces resynchronized to post-merge truth — `described_head = 3ed46b717172d512f75672c83d58327a52ac3c61` (integrated S1 delivery tip), canonical merge `2dc6b745` (PR #38), `post_merge_state` effective on `main`, tasks.jsonl += `ANOX-TASK-S1-POST-MERGE-CONTINUITY-SYNC-001` (S1 transition task → Merged); no new canonical event appended (`latest_material_event_id` remains `ANOX-EVENT-0054`; event IDs `0055`–`0059` exist only on the archived line `archive/local-main-pre-pr38-20260926` and are not canonical).
- `S1-POST-MERGE-LIFECYCLE-FINALIZATION-001` (2026-09-27, uncommitted on `main@2dc6b745`): lifecycle-only finalization after `HUMAN-S1-POST-MERGE-CONTINUITY-CHECK` = PASS/ACCEPTED — `current_writer`/`active_task` cleared, `authorized_tasks`/`pending_human_remote_actions` emptied, `ANOX-TASK-S1-POST-MERGE-CONTINUITY-SYNC-001` → `Merged`, gate texts advanced to `SELECT_NEXT_OPEN_MSC_REMEDIATION_WAVE` (no wave selected or started); ledger tail still `ANOX-EVENT-0054` (no new canonical event).

Surface updates in this event (ANOX-EVENT-0060…0066 — POST-0054-LEDGER-CANONICALIZATION-001):
- `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` — `ANOX-EVENT-0060…0065` (`canonical_merge`, one per real post-0054 merge: PR #35 `ea838fa5`, PR #36 `29a6643`, PR #38 `2dc6b745`, PR #39 `cb9aee0`, PR #40 `02179ecd`, PR #41 `270cdb92`) + `ANOX-EVENT-0066` (`post_0054_ledger_canonicalization`, seals substantive checkpoint `978b7d03`) (ANOX-EVENT-0060…0066)
- `docs/reports/security/decisions/POST-0054-LEDGER-CANONICALIZATION-001.md` — Human decision record (HUMAN_RATIFIED_CHANGE_SPECIFIC_SHARED_VALIDATOR_EXTENSION, ONE_TIME_CHANGE_SPECIFIC) (ANOX-EVENT-0066)
- `docs/workforce/registries/decisions.jsonl` — `ANOX-DECISION-POST-0054-LEDGER-CANONICALIZATION-001` (ANOX-EVENT-0066)
- `docs/workforce/registries/tasks.jsonl` — `ANOX-TASK-POST-0054-LEDGER-CANONICALIZATION-001` (Awaiting Review) (ANOX-EVENT-0066)
- `tools/audit/validate_security_audit_evidence_preservation.py` — pinned fail-closed extension accepting only the exact `ANOX-EVENT-0060…0066` chain after `ANOX-EVENT-0054`; new ratified hash `adde793ed921c02d2c741826e0a8beca144e78a14cb5e4cd06d76702b2687879` (ANOX-EVENT-0066)
- `tools/audit/validate_s0_evidence_preservation.py` — accepts the exact canonicalization chain only with decision/report present (ANOX-EVENT-0066)
- `tools/audit/validate_s0_contract_freeze.py` — ratifies the new protected-validator digest under the canonicalization decision (ANOX-EVENT-0066)
- `tools/audit/test_post_0054_ledger_canonicalization.py` — 50 adversarial tests for the pinned chain (ANOX-EVENT-0066)
- `docs/continuity/CURRENT_STATE.json` (described_head sealed to substantive commit `978b7d03`; latest events → `ANOX-EVENT-0066`; canonical base `270cdb92`) (ANOX-EVENT-0066)
- `docs/continuity/CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, `CURRENT_OPEN_WORK.md`, `CURRENT_NEXT_DEVIN_TASK.md`, `CURRENT_IMPLEMENTATION_STATE.md` (ANOX-EVENT-0066)
- `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md` (ANOX-EVENT-0066)
- `docs/workforce/WORKFORCE_STATE.json` (described_head sealed; next_phase SECURITY_REMEDIATION_WAVE_1 (in progress)) (ANOX-EVENT-0066)
- Event ids `0055–0059` remain reserved to the non-canonical archived line `archive/local-main-pre-pr38-20260926`; not reused.
## Delivery surface updates — `B028-SCALABLE-GOVERNANCE-FOUNDATION-001`

- `docs/continuity/CURRENT_STATE.json` — delivery branch `governance/b028-foundation-001`; described checkpoint `d97770db07dd15e670f194b44535ea516b6c359a`; canonical base `32c729ceb6991447698c7ec8deee7278e36d333d` (PR #45 merged); latest merge to baseline = `32c729c`; no new ledger event.
- `docs/workforce/WORKFORCE_STATE.json` — same delivery fields; `previous_merges` synchronized for canonical merges `cb9aee0`/`02179ecd`/`270cdb92`/`3414fb2`/`d59ef474`/`fce371b`/`32c729c` (carried verbatim from reviewed S2 delivery surfaces); `current_writer` = ROLE-003 foundation task; `latest_decision_id` = `ANOX-DECISION-B028-SCALABLE-GOVERNANCE-FOUNDATION-001`.
- `docs/continuity/CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, `CURRENT_IMPLEMENTATION_STATE.md`, `CURRENT_OPEN_WORK.md`, `CURRENT_NEXT_DEVIN_TASK.md` — updated for the B-028 foundation local delivery awaiting review; POST-0054-LEDGER-CANONICALIZATION-001 marked merged via PR #42.
- `docs/reports/security/decisions/B028-SCALABLE-GOVERNANCE-FOUNDATION-001.md` — new decision report.
- `docs/workforce/registries/decisions.jsonl` — appended `ANOX-DECISION-B028-SCALABLE-GOVERNANCE-FOUNDATION-001` (PROGRAM_FOUNDATION).
- `docs/workforce/registries/tasks.jsonl` — appended `ANOX-TASK-B028-SCALABLE-GOVERNANCE-FOUNDATION-001` (Authorized) + `ANOX-TASK-B028-DUAL-RUN-CUTOVER-001` (Candidate, unbound).
- `docs/workforce/registries/prompts.jsonl` — first record `ANOX-PROMPT-B028F001` bound to this delivery.
- `docs/authority/B028_SCALABLE_GOVERNANCE.md`, `B_FREEZE_REGISTRY.md`, `AUTHORITY_INDEX.md` — B-028 registered as additive Candidate authority (§J cutover contract).
- No ledger event appended; `ANOX-EVENT-0066` remains the sealed tail.
