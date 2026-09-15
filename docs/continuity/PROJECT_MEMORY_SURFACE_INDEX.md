# Project Memory Surface Index — anoX V1

**Latest material event:** ANOX-EVENT-0053
**Latest human history event:** ANOX-EVENT-0053

| Surface | Latest reference |
|---------|-----------------|
| CURRENT_STATE.json | ANOX-EVENT-0053 |
| CURRENT_GIT_STATE.md | ANOX-EVENT-0053 |
| CURRENT_HANDOFF.md | ANOX-EVENT-0053 |
| CURRENT_OPEN_WORK.md | ANOX-EVENT-0053 |
| CURRENT_NEXT_DEVIN_TASK.md | ANOX-EVENT-0053 |
| CURRENT_IMPLEMENTATION_STATE.md | ANOX-EVENT-0053 |
| PROJECT_STATE.md | ANOX-EVENT-0053 |
| FORTSCHRITT.md | ANOX-EVENT-0053 |
| DEVIN_PROMPT_OUTPUT_ARCHIV.md | ANOX-EVENT-0053 |
| WORKFORCE_STATE.json | ANOX-EVENT-0053 |
| findings.jsonl | ANOX-EVENT-0052 |
| tasks.jsonl | ANOX-EVENT-0053 |
| runs.jsonl | ANOX-EVENT-0044 |
| audits.jsonl | ANOX-EVENT-0044 |
| decisions.jsonl | ANOX-EVENT-0053 |
| PROJECT_HISTORY_LEDGER.jsonl | ANOX-EVENT-0053 |
| docs/authority/* (AUTHORITY_INDEX, B_FREEZE_REGISTRY, B025_MANDATORY_AMENDMENTS_V1_4, contracts/S0_CONTRACT_FREEZE_MANIFEST.json) | ANOX-EVENT-0053 |
| docs/current/DATABASE_ARCHITECTURE.md, BACKEND_ARCHITECTURE.md (schema deference) | ANOX-EVENT-0053 |
| docs/reports/security/remediation/* (S0 task record) | ANOX-EVENT-0053 |
| FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT.md | ANOX-EVENT-0044 |
| FINAL_PRE_PRODUCT_WORKFORCE_ARCHITECTURE_AUDIT.md | ANOX-EVENT-0043 |
| FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md | ANOX-EVENT-0037 |
| FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md | ANOX-EVENT-0035 |
| docs/security/audit-evidence/* (index, registry, traceability, hashes, reproductions) | ANOX-EVENT-0052 (S0 evidence sync pending preservation step) |
| docs/reports/security/audits/* (9 preserved reports) | ANOX-EVENT-0049 |
| docs/reports/security/consolidation/* (master consolidation report) | ANOX-EVENT-0050 |
| docs/reports/security/gates/* (coverage gate report) | ANOX-EVENT-0052 |
| docs/reports/security/decisions/* (human decision records: HUMAN-PRE-REMEDIATION-DECISIONS-001; S0-F01-FILE-OWNERSHIP-RATIFICATION-001) | ANOX-EVENT-0053 |

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
