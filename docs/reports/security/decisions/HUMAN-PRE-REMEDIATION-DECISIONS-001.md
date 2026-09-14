# HUMAN-PRE-REMEDIATION-DECISIONS-001 — HUMAN SECURITY DECISION + REMEDIATION AUTHORIZATION RECORD

**Record type:** `HUMAN_GOVERNANCE_DECISION_RECORD`
**Authority:** Human Product & Security Owner (the only authority that may accept human decisions or authorize security remediation; per `docs/authority/AUTHORITY_INDEX.md`, `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`, `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`, `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`)
**Baseline:** `9e585468d081272398e022f12e76e7500d55cbee` (`main`, post-merge baseline containing `SECURITY-REMEDIATION-COVERAGE-GATE-001` preserved at `ANOX-EVENT-0051`)
**Delivery branch:** `governance/human-pre-remediation-decisions-001`
**Task:** `ANOX-TASK-HUMAN-PRE-REMEDIATION-DECISIONS-001`
**Project Memory event:** `ANOX-EVENT-0052`
**Remote mutation:** `NONE` (no push, no PR, no merge, no remote write)
**Source gate:** `SECURITY-REMEDIATION-COVERAGE-GATE-001` (PASS — coverage proof only; `security_remediation_start_authorization = NOT_GRANTED` at gate time)

---

## Decision packet disposition

The `SECURITY-REMEDIATION-COVERAGE-GATE-001` Human Decision Packet (`HUMAN_DECISION_H1/H2/H3/R1`, all `Pending`, 0 auto-accepted) is hereby decided by the Human Product & Security Owner. **Nothing in this record was auto-accepted or decided by an AI.** The preserved gate record remains unchanged — its `Pending` statuses are historical evidence of the gate-time state; this record supersedes them prospectively.

| ID | Decision | Affected | Effective state | Trigger |
|---|---|---|---|---|
| `HUMAN_DECISION_H1` | `ARCHIVE_AND_RETIRE_SHA_PINNED_VALIDATORS` | SHA/event-pinned one-shot validators | `HISTORICAL_ONE_SHOT` / `CURRENT_ACTIVE_ACCEPTANCE = RETIRED` / `HISTORICAL_EVIDENCE = PRESERVED` | Immediate (governance bookkeeping only) |
| `HUMAN_DECISION_H2` | `ACCEPT_MODEL_DEVIATION_WITH_PRESERVED_RATIONALE` | `AUDIT-SECURITY-CODEBASE-001` | `MODEL_DEVIATION` accepted as disclosed; provenance preserved | None — provenance acceptance only |
| `HUMAN_DECISION_H3` | `RETIRE_ARCH_010_AT_B004_START` | `ANOX-SECURITY-ARCH-010` | `ACTIVE / RETIRE_AT_B004_START` (remains `Open` / `INFO` now) | `B004` start |
| `HUMAN_DECISION_R1` | `RATIFY_ROOT_013_AS_MEDIUM` | `ROOT-013` | Canonical severity `MEDIUM`; status `OPEN` | Immediate (severity ratification only) |

## H1 — ARCHIVE_AND_RETIRE_SHA_PINNED_VALIDATORS

Historical one-shot validators that are intentionally SHA/event-pinned to an old event or base SHA are **no longer part of the active current-state acceptance set** once their lifecycle event has been superseded. They:

- remain in the repository and in Git history — **not deleted** (and never deleted merely to make CI green),
- remain traceable to the event they validated (`validator_lifecycle` records in `audit_traceability.jsonl` carry the pin and the sealing event),
- retain their historical PASS/FAIL evidence (Project Memory events + preserved reports),
- are **not rewritten** to validate current HEAD (the pinned SHA/marker must remain in the file),
- produce **no active current-state CI/acceptance failure** after formal retirement (a retirement-time FAIL caused by a superseded pin is `NOT_A_CURRENT_REGRESSION`).

**Enumerated retired validators** (each proven SHA/event-pinned, lifecycle event superseded, failure verified to be supersession — not a current regression):

| Validator | Pin / pin evidence | Sealing event | Retirement-time failure cause |
|---|---|---|---|
| `tools/audit/validate_security_architecture_findings_freeze.py` | `c653a1d6a302758c0e006225987281643957f752` | `ANOX-EVENT-0044` | two-commit delivery pin superseded (23 commits above base) |
| `tools/audit/validate_legacy_retest01_ingest.py` | `3adf56c17936fdf60c864e4a26f1863243478f44` | `ANOX-EVENT-0037` | audit-trigger heuristic trips on later-recorded `ANOX-AUDIT-SECURITY-ARCH-001` provider fields |
| `tools/audit/validate_mainarch_fix03.py` | `88ea18c9b7078c376ee027d0cacc4d4f147ebbf5` | `ANOX-EVENT-0033` | post-FIX-03 successor chain superseded + later-recorded audit fields |
| `tools/audit/validate_mainarch_retest01_ingest.py` | `fd1fbddbddcba7d8705f7a76318856ad56dafb19` | `ANOX-EVENT-0030` | post-FIX-01 successor chain superseded |
| `tools/audit/validate_mainarch_retest02_ingest.py` | `739ea1c36c3d6f8eedb9a315fc6fba5173a82289` | `ANOX-EVENT-0032` | post-RETEST-02 successor chain superseded + later-recorded audit fields |
| `tools/audit/validate_mainarch_retest03_ingest.py` | `88ea18c9b7078c376ee027d0cacc4d4f147ebbf5` | `ANOX-EVENT-0034` | pre-SECARCH finding-set snapshot superseded + later-recorded audit fields |
| `tools/audit/validate_workforce_fix01.py` | `8385f4019184be9b568f65ec4748194595ef339c` | `ANOX-EVENT-0040` | snapshot expects Security-Architecture audit `NOT_STARTED`; it was later executed (`ANOX-EVENT-0044`) |
| `tools/audit/validate_workforce_fix02.py` | `81e091f3346a7c8653c100a334a1dbfe2c54d464` | `ANOX-EVENT-0041` | handoff-surface marker format evolved after the event + chained superseded ingest check |
| `tools/audit/validate_workforce_retest_closure_ingest.py` | event-pinned state snapshot (requires `ANOX-TASK-SECURITY-ARCH-001` = `Candidate`) | `ANOX-EVENT-0043` | task later executed/Closed; next-phase pointer advanced |
| `tools/audit/validate_workforce_continuity_sync_fix01.py` | `88b312fb2d7f3ba36fd49d95e80bdbfdded3d71f` | `ANOX-EVENT-0043` era | live checks pass; simulated-merge fixture diverges on handoff described-head format drift — real `generate_handoff` archive path still validates independently |

The active current-state acceptance set is unchanged: `tools/audit/validate_security_audit_evidence_preservation.py` + `test_security_audit_evidence_preservation.py`, `tools/continuity/validate_continuity.py`, `tools/workforce/validate_b027a.py`, `tools/workforce/validate_b027b.py`, `tools/workforce/validate_b027_integrity.py`, `tools/security/b017_lite_policy_validator.py`, and the lifecycle-aware audit validators that still pass at current HEAD (`validate_mainarch_fix01.py`, `validate_mainarch_fix02.py`, `validate_legacy_fix01.py`, `validate_legacy_audit_consolidation.py`, `validate_workforce_audit_findings_freeze.py`).

## H2 — ACCEPT_MODEL_DEVIATION_WITH_PRESERVED_RATIONALE

The disclosed `AUDIT-SECURITY-CODEBASE-001` model deviation is **accepted** as governance/provenance context:

- **Requested model:** `Claude Fable 5.1 High` — **Actual model:** `Claude Opus 5 Medium` (both preserved in `audit_registry.jsonl` and this record).
- Rationale preserved: `CODEBASE-002` (blind, Claude Fable 5.1 High) + `CODEBASE-SECURITY-CONSENSUS-001` covered the corpus independently; every consensus root is arbiter-confirmed; no Audit-001-only finding was admitted without arbiter confirmation.
- **No audit re-run** is required solely due to this accepted deviation.
- **No finding** is closed, re-severitied, or otherwise manipulated by this acceptance.

## H3 — RETIRE_ARCH_010_AT_B004_START

`ANOX-SECURITY-ARCH-010` ("B-004/B-005 implementation correctly NOT_STARTED; freeze boundary confirmed") remains **active now**: severity `INFO`, status `Open`, positive-scope/hygiene finding. Scheduled trigger: **`RETIRE_AT_B004_START`** — it is retired exactly when `B004` implementation starts (before `REMEDIATION_SESSION_S5` per the canonical plan). It is **not** retired in this record. Premature retirement is forbidden.

## R1 — RATIFY_ROOT_013_AS_MEDIUM

`ROOT-013` ("JNI error-code non-injective / semantics collapse") canonical severity is ratified: **`LOW` → `MEDIUM`**. The finding remains **`OPEN`** — not closed, not fixed, not retested-complete. Preserved history:

- `consensus_root` record keeps `severity = LOW` (the `CODEBASE-SECURITY-CONSENSUS-001` output — historical, unchanged).
- `severity_overlay` `ROOT-013-SEVERITY-OVERLAY-CRYPTOJNI` keeps `PENDING_SPECIALIST_CONSOLIDATION` (the Crypto/JNI-era proposal — historical, unchanged).
- `msc_root_arbitration` keeps `SEVERITY_CHANGE_PROPOSED` / `PROPOSED_NOT_YET_CANONICALLY_MUTATED` (the Master proposal — historical, unchanged).
- The canonical transition is recorded in `audit_traceability.jsonl` as `canonical_severity_transition` (prior `LOW` → current `MEDIUM`, ratified by `HUMAN_DECISION_R1`, status `OPEN`).

## SECURITY_REMEDIATION_START_AUTHORIZATION — GRANTED_BY_HUMAN_OWNER

The Human Product & Security Owner grants: **`SECURITY_REMEDIATION_START_AUTHORIZATION = GRANTED_BY_HUMAN_OWNER`**.

**Authorization is not execution.** This grant:

- authorizes the approved first remediation wave **`S0 ∥ S1`** (`REMEDIATION_SESSION_S0` architecture/contract freeze ∥ `REMEDIATION_SESSION_S1` build/provenance remediation), each on a fresh post-merge `main` SHA under its own authorized task, per the preserved dependency graph and file-ownership matrix;
- does **not** start remediation: `SECURITY_REMEDIATION = NOT_STARTED`;
- does **not** start `B004` (`NOT_STARTED`) or `B005` (`NOT_STARTED`);
- does **not** unblock product development: `BLOCKED_PENDING_FINAL_AUDIT`;
- does **not** execute the physical campaign (`PHYSICAL_P1..P17` remain `NOT_EXECUTED`);
- does **not** fix, close, or retest-complete any finding or MSC unit: `42` open `MSC_UNIT_*` remain open, `0` fixed.

## Invariants confirmed at decision time

- `SECURITY-REMEDIATION-COVERAGE-GATE-001` = `PASS` (preserved byte-exact, SHA-256 `175aa756…`); 42/42 open MSC units covered.
- Open MSC units: `42` — unchanged; fixed: `0`.
- Product: `BLOCKED_PENDING_FINAL_AUDIT`; `B004`/`B005`: `NOT_STARTED`.
- No product code, native artifact, CI, SQL, DPoP, Registration, or Storage change is made by this record.
- No completed audit is re-run; no preserved record is rewritten or deleted.

## Next state

`SECURITY_REMEDIATION_WAVE_1_READY` — the first authorized remediation wave (`REMEDIATION_SESSION_S0 ∥ REMEDIATION_SESSION_S1`) is ready for scheduling on a fresh post-merge `main` SHA after this record merges. All later sessions remain gated by the preserved dependency DAG, the parallel-execution matrix, and the Pre-B004 Definition of Done.
