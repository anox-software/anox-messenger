# Project Memory Surface Index — anoX V1

**Latest material event:** ANOX-EVENT-0037
**Latest human history event:** ANOX-EVENT-0037

| Surface | Latest reference |
|---------|-----------------|
| CURRENT_STATE.json | ANOX-EVENT-0037 |
| CURRENT_GIT_STATE.md | ANOX-EVENT-0037 |
| CURRENT_HANDOFF.md | ANOX-EVENT-0037 |
| CURRENT_OPEN_WORK.md | ANOX-EVENT-0037 |
| CURRENT_NEXT_DEVIN_TASK.md | ANOX-EVENT-0037 |
| CURRENT_IMPLEMENTATION_STATE.md | ANOX-EVENT-0037 |
| PROJECT_STATE.md | ANOX-EVENT-0037 |
| FORTSCHRITT.md | ANOX-EVENT-0037 |
| DEVIN_PROMPT_OUTPUT_ARCHIV.md | ANOX-EVENT-0037 |
| WORKFORCE_STATE.json | ANOX-EVENT-0037 |
| findings.jsonl | ANOX-EVENT-0037 |
| audits.jsonl | ANOX-EVENT-0037 |
| FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md | ANOX-EVENT-0037 |
| FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md | ANOX-EVENT-0035 |

Surface updates in this event:
- `docs/workforce/registries/findings.jsonl` (8 LEGACY-FIX-01 findings Closed with immutable closure evidence)
- `docs/workforce/registries/audits.jsonl` (LEGACY-RETEST-01 DELTA record)
- `docs/workforce/registries/runs.jsonl` (retest + ingest run records)
- `docs/workforce/registries/tasks.jsonl` (retest/ingest Closed; ANOX-TASK-WORKFORCEARCH001 Candidate)
- `docs/workforce/WORKFORCE_STATE.json` (next phase AUDIT-WORKFORCE-ARCHITECTURE)
- `docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md` (LEGACY-RETEST-01 section)
- `tools/audit/lifecycle_legality.py` (canonical transition legality, new)
- `tools/audit/validate_legacy_retest01_ingest.py` (new 23-check validator)
- `tools/audit/test_legacy_retest01_ingest.py` (25 adversarial tests, new)
- `tools/audit/validate_mainarch_fix01.py`, `validate_mainarch_fix02.py`, `validate_mainarch_fix03.py`, `validate_mainarch_retest01_ingest.py`, `validate_mainarch_retest02_ingest.py`, `validate_mainarch_retest03_ingest.py`, `validate_legacy_fix01.py`, `validate_legacy_audit_consolidation.py` (hardened: snapshot vs live lifecycle; structured external-audit trigger detection)
- `tools/audit/test_mainarch_fix03.py` (lifecycle-legality + trigger-detection tests)
- `docs/continuity/*` and top-level memory surfaces (ANOX-EVENT-0037)
