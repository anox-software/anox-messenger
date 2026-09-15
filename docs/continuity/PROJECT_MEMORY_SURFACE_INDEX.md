# Project Memory Surface Index — anoX V1

**Latest material event:** ANOX-EVENT-0054
**Latest human history event:** ANOX-EVENT-0052

| Surface | Latest reference |
|---------|-----------------|
| CURRENT_STATE.json | ANOX-EVENT-0054 |
| CURRENT_GIT_STATE.md | ANOX-EVENT-0054 |
| CURRENT_HANDOFF.md | ANOX-EVENT-0054 |
| CURRENT_OPEN_WORK.md | ANOX-EVENT-0054 |
| CURRENT_NEXT_DEVIN_TASK.md | ANOX-EVENT-0054 |
| CURRENT_IMPLEMENTATION_STATE.md | ANOX-EVENT-0054 |
| PROJECT_STATE.md | ANOX-EVENT-0054 |
| FORTSCHRITT.md | ANOX-EVENT-0054 |
| DEVIN_PROMPT_OUTPUT_ARCHIV.md | ANOX-EVENT-0054 |
| WORKFORCE_STATE.json | ANOX-EVENT-0054 |
| findings.jsonl | ANOX-EVENT-0052 |
| tasks.jsonl | ANOX-EVENT-0054 |
| runs.jsonl | ANOX-EVENT-0044 |
| audits.jsonl | ANOX-EVENT-0044 |
| decisions.jsonl | ANOX-EVENT-0052 |
| PROJECT_HISTORY_LEDGER.jsonl | ANOX-EVENT-0054 |
| FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT.md | ANOX-EVENT-0044 |
| FINAL_PRE_PRODUCT_WORKFORCE_ARCHITECTURE_AUDIT.md | ANOX-EVENT-0043 |
| FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md | ANOX-EVENT-0037 |
| FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md | ANOX-EVENT-0035 |
| docs/security/audit-evidence/* (index, registry, traceability, hashes, reproductions) | ANOX-EVENT-0052 |
| docs/reports/security/audits/* (9 preserved reports) | ANOX-EVENT-0049 |
| docs/reports/security/consolidation/* (master consolidation report) | ANOX-EVENT-0050 |
| docs/reports/security/gates/* (coverage gate report) | ANOX-EVENT-0052 |

| docs/security/remediation/* (MSC state, S1 task report, runtime evidence) | ANOX-EVENT-0054 |

Surface updates in this event:
- `crypto/rust/rust-toolchain.toml`, `tools/security/native_build.py`, `tools/security/validate_apk_contents.py`, `tools/security/secret_scan.py`, `tools/security/validate_ci_pipeline.py`, `tools/audit/validate_b021_verification_matrix.py`, `tools/audit/validate_s1_build_provenance.py`, `tools/audit/test_s1_build_provenance.py` (66 adversarial tests), `.github/workflows/ci.yml`, `android/build.gradle.kts`, `.gitignore`, `docs/current/REPOSITORY_SECURITY_POLICY.md`, `docs/security/remediation/README.md`, `docs/security/remediation/S1_TASK_REPORT.md`, `docs/security/remediation/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME.md`, `docs/security/remediation/msc_state.jsonl` — substantive S1 implementation (ANOX-EVENT-0054, substantive `fc58414b6790`; committed `.so` files deleted)
- `docs/continuity/CURRENT_STATE.json` (ANOX-EVENT-0054; described_head sealed to substantive commit; latest_material_event_id ANOX-EVENT-0054; pre_merge_gate REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001; post_merge_gate SECURITY_REMEDIATION_WAVE_1)
- `docs/continuity/CURRENT_GIT_STATE.md` (ANOX-EVENT-0054; described_head = substantive commit; main baseline 0f932520393f)
- `docs/continuity/CURRENT_HANDOFF.md` (ANOX-EVENT-0054; remediation-s1-build-provenance-001 delivery)
- `docs/continuity/CURRENT_OPEN_WORK.md` (ANOX-EVENT-0054; S1 Ready For Remote; independent Build/Supply retest next)
- `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md` (ANOX-EVENT-0054; INDEPENDENT BUILD/SUPPLY RETEST OF S1)
- `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md` (ANOX-EVENT-0054; S1 delivery outcome)
- `PROJECT_STATE.md` (ANOX-EVENT-0054; branch security/remediation-s1-build-provenance-001)
- `FORTSCHRITT.md` (ANOX-EVENT-0054; REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001 section)
- `DEVIN_PROMPT_OUTPUT_ARCHIV.md` (ANOX-EVENT-0054; archive entry)
- `docs/workforce/WORKFORCE_STATE.json` (ANOX-EVENT-0054; described_head sealed; next_phase SECURITY_REMEDIATION_WAVE_1; current task ANOX-TASK-REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001)
- `docs/workforce/registries/tasks.jsonl` (ANOX-EVENT-0054; ANOX-TASK-REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001 Ready For Remote)
- `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` (ANOX-EVENT-0054)
- `tools/audit/validate_security_audit_evidence_preservation.py` — NOT modified (frozen read-only for S1; era-pinned to ANOX-EVENT-0052; `S1_SHARED_VALIDATOR_FOLLOWUP_REQUIRED` recorded — S1-era extension required post-integration)
