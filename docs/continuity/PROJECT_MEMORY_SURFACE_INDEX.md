# Project Memory Surface Index — anoX V1

**Latest material event:** ANOX-EVENT-0052
**Latest human history event:** ANOX-EVENT-0052

| Surface | Latest reference |
|---------|-----------------|
| CURRENT_STATE.json | ANOX-EVENT-0052 |
| CURRENT_GIT_STATE.md | ANOX-EVENT-0052 |
| CURRENT_HANDOFF.md | ANOX-EVENT-0052 |
| CURRENT_OPEN_WORK.md | ANOX-EVENT-0052 |
| CURRENT_NEXT_DEVIN_TASK.md | ANOX-EVENT-0052 |
| CURRENT_IMPLEMENTATION_STATE.md | ANOX-EVENT-0052 |
| PROJECT_STATE.md | ANOX-EVENT-0052 |
| FORTSCHRITT.md | ANOX-EVENT-0052 |
| DEVIN_PROMPT_OUTPUT_ARCHIV.md | ANOX-EVENT-0052 |
| WORKFORCE_STATE.json | ANOX-EVENT-0052 |
| findings.jsonl | ANOX-EVENT-0052 |
| tasks.jsonl | ANOX-EVENT-0052 |
| runs.jsonl | ANOX-EVENT-0044 |
| audits.jsonl | ANOX-EVENT-0044 |
| decisions.jsonl | ANOX-EVENT-0052 |
| PROJECT_HISTORY_LEDGER.jsonl | ANOX-EVENT-0052 |
| FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT.md | ANOX-EVENT-0044 |
| FINAL_PRE_PRODUCT_WORKFORCE_ARCHITECTURE_AUDIT.md | ANOX-EVENT-0043 |
| FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md | ANOX-EVENT-0037 |
| FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md | ANOX-EVENT-0035 |
| docs/security/audit-evidence/* (index, registry, traceability, hashes, reproductions) | ANOX-EVENT-0052 |
| docs/reports/security/audits/* (9 preserved reports) | ANOX-EVENT-0049 |
| docs/reports/security/consolidation/* (master consolidation report) | ANOX-EVENT-0050 |
| docs/reports/security/gates/* (coverage gate report) | ANOX-EVENT-0052 |

Surface updates in this event:
- `docs/reports/security/decisions/` — `HUMAN-PRE-REMEDIATION-DECISIONS-001.md` canonical human governance decision record (SHA-256 `d558471d…`, 10,128 bytes) (ANOX-EVENT-0052)
- `docs/security/audit-evidence/` — `AUDIT_EVIDENCE_INDEX.md`, `audit_registry.jsonl` (12 records; `SEC-AUDIT-REG-0012` HUMAN_GOVERNANCE_DECISION_RECORD), `audit_traceability.jsonl` (+30 decision-layer records: 4 `human_decision`, `human_remediation_authorization`, `canonical_severity_transition` ROOT-013, `finding_retirement_trigger` ARCH-010, 21 `validator_lifecycle`, `decision_artifact`, `next_gate` SECURITY_REMEDIATION_WAVE_1; HUMAN_PRE_REMEDIATION_DECISIONS_AND_AUTHORIZATION pointer → EXECUTED_AND_PRESERVED), `evidence_hashes.json` (decision record entry), `reproductions/README.md` (ANOX-EVENT-0052)
- `tools/audit/validate_security_audit_evidence_preservation.py` + `test_security_audit_evidence_preservation.py` extended (ANOX-EVENT-0052; 235 adversarial tests incl. real-git delivery-topology cases)
- `docs/workforce/registries/tasks.jsonl` (ANOX-EVENT-0052; ANOX-TASK-HUMAN-PRE-REMEDIATION-DECISIONS-001 Ready For Remote)
- `docs/workforce/registries/decisions.jsonl` (ANOX-EVENT-0052; ANOX-DECISION-HUMANPREREMEDIATION001)
- `docs/workforce/registries/findings.jsonl` (ANOX-EVENT-0052; ANOX-SECURITY-ARCH-010 RETIRE_AT_B004_START note; stays Open/INFO)
- `docs/continuity/CURRENT_STATE.json` (ANOX-EVENT-0052; described_head sealed to substantive commit; latest_material_event_id ANOX-EVENT-0052; pre_merge_gate HUMAN-PRE-REMEDIATION-DECISIONS-001; post_merge_gate SECURITY_REMEDIATION_WAVE_1)
- `docs/continuity/CURRENT_GIT_STATE.md` (ANOX-EVENT-0052; described_head = substantive commit; main baseline 9e585468d081)
- `docs/continuity/CURRENT_HANDOFF.md` (ANOX-EVENT-0052; human-pre-remediation-decisions-001 delivery)
- `docs/continuity/CURRENT_OPEN_WORK.md` (ANOX-EVENT-0052; HUMAN-PRE-REMEDIATION-DECISIONS-001 Ready For Remote; SECURITY_REMEDIATION_WAVE_1 Candidate)
- `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md` (ANOX-EVENT-0052; REMEDIATION_SESSION_S0 ∥ S1 authorized-not-started)
- `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md` (ANOX-EVENT-0052; recorded decision + authorization outcome)
- `PROJECT_STATE.md` (ANOX-EVENT-0052; branch governance/human-pre-remediation-decisions-001)
- `FORTSCHRITT.md` (ANOX-EVENT-0052; HUMAN-PRE-REMEDIATION-DECISIONS-001 section)
- `DEVIN_PROMPT_OUTPUT_ARCHIV.md` (ANOX-EVENT-0052; archive entry)
- `docs/workforce/WORKFORCE_STATE.json` (ANOX-EVENT-0052; described_head sealed; next_phase SECURITY_REMEDIATION_WAVE_1; completed_audit_ids += HUMAN_PRE_REMEDIATION_DECISIONS_AND_AUTHORIZATION; previous baseline += 610ed0833753)
- `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` (ANOX-EVENT-0052)
