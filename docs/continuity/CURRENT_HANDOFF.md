# CURRENT_HANDOFF — anoX V1

**Event:** `ANOX-EVENT-0052` — HUMAN-PRE-REMEDIATION-DECISIONS-001  
**Delivery branch:** `governance/human-pre-remediation-decisions-001`  
**Substantive HEAD:** `30fe6e9afa7033ee94c31f79d8cc1774716ee386`  
**Main baseline:** `9e585468d081272398e022f12e76e7500d55cbee`  
**Effective gate:** `HUMAN-PRE-REMEDIATION-DECISIONS-001 — RECORD HUMAN PRE-REMEDIATION DECISIONS AND REMEDIATION AUTHORIZATION (Ready For Remote; awaiting human merge)`

Described HEAD: 30fe6e9afa7033ee94c31f79d8cc1774716ee386

## Pre-merge gate

`HUMAN-PRE-REMEDIATION-DECISIONS-001 — RECORD HUMAN PRE-REMEDIATION DECISIONS AND REMEDIATION AUTHORIZATION (Ready For Remote; awaiting human merge)`

- Authored the canonical human governance decision record `docs/reports/security/decisions/HUMAN-PRE-REMEDIATION-DECISIONS-001.md` (SHA-256 `d558471d…`, 10,128 bytes): the Human Product & Security Owner decided the preserved gate's Human Decision Packet with **zero auto-acceptance** — `H1=ARCHIVE_AND_RETIRE_SHA_PINNED_VALIDATORS`, `H2=ACCEPT_MODEL_DEVIATION_WITH_PRESERVED_RATIONALE`, `H3=RETIRE_ARCH_010_AT_B004_START`, `R1=RATIFY_ROOT_013_AS_MEDIUM`.
- Recorded `SECURITY_REMEDIATION_START_AUTHORIZATION = GRANTED_BY_HUMAN_OWNER` for the first authorized wave `S0 ∥ S1` (`REMEDIATION_SESSION_S0` ∥ `REMEDIATION_SESSION_S1`). **Authorization is not execution**: security remediation `NOT_STARTED`; `B-004`/`B-005` `NOT_STARTED`; product `BLOCKED_PENDING_FINAL_AUDIT`; `PHYSICAL_P1..P17` `NOT_EXECUTED`; 42 open `MSC_UNIT_*` unchanged, 0 fixed.
- Recorded registry entry `SEC-AUDIT-REG-0012` (`artifact_type=HUMAN_GOVERNANCE_DECISION_RECORD`; registry now 12 records) and the decision layer in `audit_traceability.jsonl`: 4× `human_decision` (human authority only), `human_remediation_authorization` (`GRANTED_BY_HUMAN_OWNER`, `S0_AND_S1`), `canonical_severity_transition` (`ROOT-013` LOW→MEDIUM, status OPEN — consensus LOW + overlay PENDING preserved), `finding_retirement_trigger` (`ANOX-SECURITY-ARCH-010` `RETIRE_AT_B004_START`, stays Open/INFO), `validator_lifecycle` (10 SHA/event-pinned one-shot validators `RETIRED` — files, pins and historical evidence preserved, not rewritten, not deleted; 11 active current-state validators), `decision_artifact`, `next_gate` `SECURITY_REMEDIATION_WAVE_1` Candidate / NOT_EXECUTED.
- Extended `tools/audit/validate_security_audit_evidence_preservation.py` fail-closed for the decision layer and added 33 adversarial tests (235 total incl. two real-git delivery-topology cases).
- No product/CI/SQL/native/secret changes; remote mutation NONE; no remediation session executed; no finding closed or re-severitied except the canonical ROOT-013 severity ratification (still OPEN); no audit re-run.

## Post-merge gate

`SECURITY_REMEDIATION_WAVE_1 — REMEDIATION_SESSION_S0 ∥ REMEDIATION_SESSION_S1 (Candidate; authorized by HUMAN-PRE-REMEDIATION-DECISIONS-001 — remediation NOT_STARTED)`

## Preserved audit outcomes

- `AUDIT-SECURITY-CODEBASE-001`: PASS_WITH_FINDINGS; 21 candidates (1C/3H/8M/7L/2I); actual model Claude Opus 5 Medium (MODEL_DEVIATION vs requested Fable 5.1 High — accepted by HUMAN_DECISION_H2 with preserved rationale).
- `AUDIT-SECURITY-CODEBASE-002` (blind): PASS_WITH_FINDINGS; 17 candidates (0C/3H/6M/6L/2I); Claude Fable 5.1 High.
- `CODEBASE-SECURITY-CONSENSUS-001`: PASS; 18 normalized roots; `ROOT-005` single-audit/arbiter-confirmed; `ROOT-016` NOT_A_FINDING; Pre-B004 set = 12 roots.
- `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`: PASS_WITH_FINDINGS; 12 candidates; `ANOX-BUILDSC-CANDIDATE-001` EVIDENCE_INTEGRITY=CRITICAL (committed `.so` stale vs source `7db20fa`).
- `AUDIT-SECURITY-CRYPTO-JNI-001` (specialist): PASS_WITH_FINDINGS at `a79166ab`; 6 candidates (0C/1H/3M/1L/1I); `JNI_ABI_REVISION=YES`; verdict `COMPONENT_INTERNAL_REDESIGN_ONLY`; Pre-B004 Crypto/JNI gate set = 8 members; ROOT-013 overlay LOW→MEDIUM proposal preserved (now human-ratified to canonical MEDIUM by HUMAN_DECISION_R1 — finding remains OPEN); provenance limitation active (temp current-source evidence only).
- `AUDIT-SECURITY-AUTH-DPOP-001` (specialist): PASS_WITH_FINDINGS at `638e63a2`; 3 candidates (0C/0H/1M/2L/0I) + 3 architecture gaps; B-002 29/29 production + 14/14 test files; 40 requirements, 0 unmapped; 173/173 focused tests pass; physical verification still required; verdict `COMPONENT_INTERNAL_REDESIGN_ONLY`, SEC-C not required; Pre-B004 additions = `CANDIDATE-001` + `GAP-001/002/003` contract freeze.
- `AUDIT-SECURITY-ANDROID-STORAGE-001` (specialist): PASS_WITH_FINDINGS at `b9abeb08`; 2 candidates (0C/0H/0M/2L/0I) + 3 architecture gaps; 49/49 production + 14/14 test files; 42 requirements, 0 unmapped; 177/177 focused tests pass; physical verification still required; verdict `COMPONENT_INTERNAL_REDESIGN_ONLY`, SEC-C not required; Pre-B004 additions = `ROOT-006/007/017` + `ROOT-011` registration/marker slice + `CANDIDATE-001` contract half + `CANDIDATE-002` + `GAP-001/002/003` contract freeze.
- `AUDIT-SECURITY-ATTACKCHAIN-001` (specialist): PASS_WITH_FINDINGS at `e5458490`; 15 chains (0C/4H/7M/3L/1I; HIGH = AC-001/003/006/012; AC-003 `CONDITIONAL_CRITICAL_AT_B004_IF_VERIFIER_DEFAULTS_PORTED` overlay only); evidence E2=8/E1=6/E0=1; 68 security items, UNMAPPED=0; verdict `CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED`, SEC-C not required; 13 rejected hypotheses; final re-audit mandatory = AC-001/003/006/012 + AC-005/008/010.
- `MASTER-SPECIALIST-CONSOLIDATION-001` (consolidation): PASS_WITH_CONSOLIDATION_FINDINGS at `1eb773069d81`; 90/90 source items accounted; 44 `MSC_UNIT_001..044` (42 OPEN + 2 REJECTED); verdict `CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED`; SEC-C not required; provisional `REMEDIATION_SESSION_S0..S10` + Pre-B004 Master Set + closure standards preserved for the coverage gate.
- `SECURITY-REMEDIATION-COVERAGE-GATE-001` (coverage gate): PASS at `610ed0833753`; 42/42 OPEN `MSC_UNIT_*` covered (0 uncovered/unknown); dependency cycles 0; parallel-writer collisions 0; `FCP_1..8` enforced; false-closure A–F blocked; `SC/CC 14/14`; `PHYSICAL_P1..P17` assigned 17/17, executed 0; retest owners 42/42; DoD unowned 0; `HUMAN_DECISION_H1/H2/H3/R1` pending in the preserved gate record (now decided — see decision record); PASS is coverage proof only.
- `HUMAN-PRE-REMEDIATION-DECISIONS-001` (human governance decision record): `DECIDED — REMEDIATION_WAVE_1_AUTHORIZED` at `9e585468d081`; H1/H2/H3/R1 decided by Human Product & Security Owner; `SECURITY_REMEDIATION_START_AUTHORIZATION = GRANTED_BY_HUMAN_OWNER` for first wave `S0 ∥ S1`; authorization is not execution.

## Open product findings

- `ANOX-MAINARCH-013`, `ANOX-MAINARCH-018` (`PHYSICAL_VERIFICATION_REQUIRED`), `ANOX-MAINARCH-030`, `ANOX-LEGACY-INTEGRATION-005`, `ANOX-LEGACY-B003-001`
- `ANOX-SECURITY-ARCH-001`..`010` (Open; 001..004 are B-004 blockers; `ANOX-SECURITY-ARCH-010` scheduled trigger `RETIRE_AT_B004_START` — stays Open/INFO until B004 start)
- Active consensus roots `ROOT-001`..`ROOT-015`, `ROOT-017`, `ROOT-018` (`ROOT-013` canonical severity now `MEDIUM`, remains OPEN) + `ANOX-CRYPTOJNI-CANDIDATE-001..006` + `ANOX-AUTHDPOP-CANDIDATE-001..003` + `ANOX-AUTHDPOP-GAP-001..003` + `ANOX-ANDROIDSTORAGE-CANDIDATE-001..002` + `ANOX-ANDROIDSTORAGE-GAP-001..003` + `ANOX-ATTACKCHAIN-CANDIDATE-001..015` + consolidated `MSC_UNIT_001..042` open units (see `docs/security/audit-evidence/audit_traceability.jsonl`)

## Product state

- `PRODUCT_DEVELOPMENT = BLOCKED_PENDING_FINAL_AUDIT`
- `B004 = NOT_STARTED`
- `B005 = NOT_STARTED`
- `SECURITY-REMEDIATION-COVERAGE-GATE = EXECUTED_AND_PRESERVED (PASS — coverage only, NOT a remediation authorization)`
- `HUMAN_PRE_REMEDIATION_DECISIONS_AND_AUTHORIZATION = EXECUTED_AND_PRESERVED (decided; SECURITY_REMEDIATION_START_AUTHORIZATION = GRANTED_BY_HUMAN_OWNER)`
- `SECURITY REMEDIATION = NOT_STARTED`
- `SECURITY_REMEDIATION_WAVE_1 (REMEDIATION_SESSION_S0 ∥ S1) = CANDIDATE / NOT_EXECUTED`
- `FINAL-OPERATIONAL-HANDOFF-BOOTSTRAP-ACCEPTANCE = PENDING / NOT_EXECUTED`
- `Human final product gate = NOT_EXECUTED`
