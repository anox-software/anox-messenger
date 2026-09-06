# FINAL PRE-PRODUCT LEGACY AUDIT CONSOLIDATION

**Status:** COMPLETE
**Audit set:** LEGACY-AUDIT-SET-FREEZE
**Mode:** READ-ONLY
**Model:** `Devin SWE-1.7 Max`
**Canonical base SHA (all six audits):** `f245dc429a9e4bd10f51692eb452d03ccb9a6749`
**Ending SHA:** `f245dc429a9e4bd10f51692eb452d03ccb9a6749`
**Repository modified:** NO (ingest is part of committed consolidation)
**Remote mutation:** NONE
**Claude audit triggered:** NO

## 1. Frozen baseline

All six legacy audits used exactly:

```
f245dc429a9e4bd10f51692eb452d03ccb9a6749
```

`git status --short` was clean at start and end of every session.

## 2. Canonical preconditions

- `validate_mainarch_retest03_ingest.py`: PASS
- `validate_b027_integrity.py`: PASS
- `b017_lite_policy_validator.py`: PASS
- `validate_continuity.py --mode live`: PASS
- MAIN architecture audit: COMPLETE
- MAIN architecture remediation: COMPLETE
- MAIN findings: 30 Closed, 6 Open
- Product: `BLOCKED_PENDING_FINAL_AUDIT`
- B-004/B-005: `NOT_STARTED`

## 3. Six-audit set completion

| # | Audit ID | Result | Model | Base SHA | Ending SHA |
|---|---|---|---|---|---|
| 1 | `LEGACY-AUDIT-B002` | `PASS WITH FINDINGS` | `Devin SWE-1.7 Max` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` |
| 2 | `LEGACY-AUDIT-B003` | `PASS WITH FINDINGS` | `Devin SWE-1.7 Max` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` |
| 3 | `LEGACY-AUDIT-CRYPTO` | `PASS WITH FINDINGS` | `Devin SWE-1.7 Max` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` |
| 4 | `LEGACY-AUDIT-ANDROID-SEC` | `PASS WITH FINDINGS` | `Devin SWE-1.7 Max` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` |
| 5 | `LEGACY-AUDIT-BUILD` | `PASS WITH FINDINGS` | `Devin SWE-1.7 Max` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` |
| 6 | `LEGACY-AUDIT-INTEGRATION` | `PASS WITH FINDINGS` | `Devin SWE-1.7 Max` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` | `f245dc429a9e4bd10f51692eb452d03ccb9a6749` |

**Set state:** 6 / 6 COMPLETE

## 4. Existing MAIN findings revalidated

| ID | Title | Disposition | Class |
|---|---|---|---|
| `ANOX-MAINARCH-013` | Build / supply-chain / native artifact provenance | Revalidated; new byte-reproducibility evidence appended; remains Open | D |
| `ANOX-MAINARCH-018` | Physical GrapheneOS / StrongBox verification | Revalidated; `PHYSICAL_VERIFICATION_REQUIRED` preserved | E |
| `ANOX-MAINARCH-019` | Device Auth production eligibility not enforced by RegistrationOrchestrator | Revalidated; Class A blocker | A |
| `ANOX-MAINARCH-023` | K_STATE read-path silent recreation | Revalidated; narrow hypothesis confirmed; Class A blocker | A |
| `ANOX-MAINARCH-030` | Local wipe / session-persistence forward-model gap | Revalidated; decomposed into current (none) and future B-009/B-013 | C |
| `ANOX-MAINARCH-031` | Rust/JNI output-buffer error mapping | Revalidated; Class A blocker | A |

## 5. Candidate dispositions

| Candidate ID | Source | Severity | Disposition | Canonical ID / Merged into | Rationale |
|---|---|---|---|---|---|
| `ANOX-LEGACY-B002-001` | B002 | LOW | `DOCUMENTATION_CLEANUP` | `` | Stale `Future Ed25519 device authentication` and `Access/Refresh Tokens` prose in docs/current/LOCAL_KEY_STATE_LIFECYCLE_V1_FROZEN.md contradicts frozen B-002 v1.1 (P-256/ES256, no refresh token). Class F documentation cleanup; no runtime defect. |
| `ANOX-LEGACY-B002-002` | B002 | INFO | `DEFER_AS_FUTURE_WORK` | `` | DPoP HTU normalization is implemented on the client (DpopHtu.kt) but the server-side contract cannot be pinned until B-004/B-007 implementation starts. Class B (implement with B-004/B-007). |
| `ANOX-LEGACY-B003-001` | B003 | INFO | `PROMOTE_CANONICAL` | `ANOX-LEGACY-B003-001` | Verified: UuidV4.parse checks version() == 4 but not variant(). Promoted as LOW non-blocking parser-correctness finding (Class F). |
| `ANOX-LEGACY-CRYPTO-001` | CRYPTO | MEDIUM | `MERGE_INTO_EXISTING` | `ANOX-MAINARCH-023` | Replacement K_STATE on read paths is the same root cause as ANOX-MAINARCH-023. Merged with updated evidence. |
| `ANOX-LEGACY-CRYPTO-002` | CRYPTO | LOW | `MERGE_INTO_EXISTING` | `ANOX-MAINARCH-031` | JNI buffer-too-small error misclassification is the same root cause as ANOX-MAINARCH-031. Merged. |
| `ANOX-LEGACY-CRYPTO-003` | CRYPTO | MEDIUM | `MERGE_INTO_EXISTING` | `ANOX-MAINARCH-030` | wipeLocalCrypto not covering DB/WAL/SHM/attachments/temp is future B-009/B-013 work, merged into ANOX-MAINARCH-030 (Class C). |
| `ANOX-LEGACY-CRYPTO-004` | CRYPTO | MEDIUM | `MERGE_INTO_EXISTING` | `ANOX-MAINARCH-030` | Single-session persistence / no preferred_session_id is future B-009/B-013 work, merged into ANOX-MAINARCH-030 (Class C). |
| `ANOX-LEGACY-CRYPTO-005` | CRYPTO | MEDIUM | `PROMOTE_CANONICAL` | `ANOX-LEGACY-CRYPTO-005` | Verified: Rust JNI functions take &mut and & references to the same Identity handle without serialization; latent data race in future concurrent Product use. Promoted as HIGH memory-safety finding (Class A). |
| `ANOX-LEGACY-CRYPTO-006` | CRYPTO | INFO | `DEFER_AS_FUTURE_WORK` | `` | Fallback keys not implemented; B-004/B-005/B-006 server distribution work is NOT_STARTED. Class B. |
| `ANOX-LEGACY-CRYPTO-007` | CRYPTO | LOW | `DEFER_AS_FUTURE_WORK` | `` | B-008 message-size limits not enforced in CryptoBridge; Product B-008 layer not started. Class C. |
| `ANOX-LEGACY-CRYPTO-008` | CRYPTO | INFO | `VERIFICATION_GAP_ONLY` | `` | No JVM unit tests for CryptoBridge/Kotlin JNI mapping; only androidTest exists. Map to B-021 test-matrix maintenance. Class F. |
| `ANOX-LEGACY-ANDROIDSEC-001` | ANDROID-SEC | MEDIUM | `PROMOTE_CANONICAL` | `ANOX-LEGACY-ANDROIDSEC-001` | Verified: CryptoBridge.getLocalStateStatus directly references android.security.KeyStoreException (API 33+) while minSdk=26; path reachable from registration. Promoted as HIGH (Class A). |
| `ANOX-LEGACY-BUILD-001` | BUILD | MEDIUM | `MERGE_INTO_EXISTING` | `ANOX-MAINARCH-013` | Toolchain/recipe pinning gap is the same root cause as ANOX-MAINARCH-013 build/provenance. Merged. |
| `ANOX-LEGACY-BUILD-002` | BUILD | LOW | `NOT_A_FINDING` | `` | Unstripped .so strings do not violate any frozen B017/B023 requirement; reverse-engineering difficulty is not a core security control per current Authority. |
| `ANOX-LEGACY-INTEGRATION-001` | INTEGRATION | HIGH | `PROMOTE_CANONICAL` | `ANOX-LEGACY-INTEGRATION-001` | Verified: commit() uses stored thumbprint and never re-verifies the Device Auth key. Promoted as HIGH (Class A). |
| `ANOX-LEGACY-INTEGRATION-002` | INTEGRATION | HIGH | `PROMOTE_CANONICAL` | `ANOX-LEGACY-INTEGRATION-002` | Verified: identity file persisted before OTK generation; OTK private state not re-serialized. Promoted as HIGH (Class A). |
| `ANOX-LEGACY-INTEGRATION-003` | INTEGRATION | MEDIUM | `PROMOTE_CANONICAL` | `ANOX-LEGACY-INTEGRATION-003` | Verified: markArmed failure leaves CommitArmed session but unarmed binding; expiry can downgrade. Promoted as MEDIUM (Class A). |
| `ANOX-LEGACY-INTEGRATION-004` | INTEGRATION | HIGH | `REQUIRES_SCOPE_DECISION` | `` | Missing 32-bit ABI .so is only a production defect if Authority explicitly promises 32-bit device support. Primary V1 target is GrapheneOS (64-bit Pixel); minSdk=26 is API level, not ABI promise. No auto-promotion. Human/scope decision required. |
| `ANOX-LEGACY-INTEGRATION-005` | INTEGRATION | MEDIUM | `PROMOTE_CANONICAL` | `ANOX-LEGACY-INTEGRATION-005` | Verified: native Identity handles created in registration path are not destroyed. Promoted as MEDIUM Class F non-blocking cleanup. |
| `ANOX-LEGACY-INTEGRATION-006` | INTEGRATION | INFO | `NOT_A_FINDING` | `` | MainActivity does not wire the registration/Product flow; B-020 product implementation is NOT_STARTED. Expected state, not a current defect. |

## 6. Promoted canonical Legacy findings

| ID | Severity | Affected scope | Root-cause class |
|---|---|---|---|
| `ANOX-LEGACY-ANDROIDSEC-001` | HIGH | B-009, B-003, Android local security | RUNTIME_DEFECT |
| `ANOX-LEGACY-CRYPTO-005` | HIGH | B-006, JNI, concurrency | MEMORY_SAFETY |
| `ANOX-LEGACY-INTEGRATION-001` | HIGH | B-002, B-003, registration | STATE_MACHINE |
| `ANOX-LEGACY-INTEGRATION-002` | HIGH | B-006, B-003 | DATA_INCONSISTENCY |
| `ANOX-LEGACY-INTEGRATION-003` | MEDIUM | B-003, B-002 | STATE_MACHINE |
| `ANOX-LEGACY-INTEGRATION-005` | MEDIUM | B-006, JNI, resource management | RESOURCE_LEAK |
| `ANOX-LEGACY-B003-001` | LOW | B-003, parser | PARSER_CORRECTNESS |

## 7. Root-cause consolidation

### Canonical Open findings after freeze

**Six existing MAIN findings** (preserved Open):

- `ANOX-MAINARCH-013`
- `ANOX-MAINARCH-018`
- `ANOX-MAINARCH-019`
- `ANOX-MAINARCH-023`
- `ANOX-MAINARCH-030`
- `ANOX-MAINARCH-031`

**Seven new Legacy findings** (promoted Open):

- `ANOX-LEGACY-ANDROIDSEC-001`
- `ANOX-LEGACY-CRYPTO-005`
- `ANOX-LEGACY-INTEGRATION-001`
- `ANOX-LEGACY-INTEGRATION-002`
- `ANOX-LEGACY-INTEGRATION-003`
- `ANOX-LEGACY-INTEGRATION-005`
- `ANOX-LEGACY-B003-001`

**No duplicate root causes.** `CRYPTO-001/002/003/004` and `BUILD-001` were merged into existing MAIN findings rather than promoted.

## 8. Remediation classification

### Class A — foundation fix before B-004/B-005 implementation

ANOX-MAINARCH-019, ANOX-MAINARCH-023, ANOX-MAINARCH-031, ANOX-LEGACY-ANDROIDSEC-001, ANOX-LEGACY-CRYPTO-005, ANOX-LEGACY-INTEGRATION-001, ANOX-LEGACY-INTEGRATION-002, ANOX-LEGACY-INTEGRATION-003

### Class B — implement with B-004/B-005/B-006

- B002-002 DPoP HTU server-side contract
- CRYPTO-006 fallback key server lifecycle
- B-004/B-005 one-active-device server enforcement
- B-004/B-005 authenticated-device context / DPoP replay cache

### Class C — implement with B-008/B-009/B-013

- ANOX-MAINARCH-030
- CRYPTO-007 B-008 message-size enforcement
- DB/WAL/SHM/attachment/temp wipe
- per-peer preferred_session_id persistence

### Class D — release / build gate

- ANOX-MAINARCH-013
- ANOX-LEGACY-INTEGRATION-004 (if promoted after scope decision)

### Class E — physical verification

- ANOX-MAINARCH-018

### Class F — non-blocking cleanup / verification debt

- ANOX-LEGACY-B003-001
- ANOX-LEGACY-INTEGRATION-005
- B002-001 stale documentation cleanup
- CRYPTO-008 JVM CryptoBridge test gap
- B-021 test-matrix mapping maintenance

## 9. Pre-B004 foundation blockers

- ANOX-MAINARCH-019
- ANOX-MAINARCH-023
- ANOX-MAINARCH-031
- ANOX-LEGACY-ANDROIDSEC-001
- ANOX-LEGACY-CRYPTO-005
- ANOX-LEGACY-INTEGRATION-001
- ANOX-LEGACY-INTEGRATION-002
- ANOX-LEGACY-INTEGRATION-003

## 10. Release blockers

- ANOX-MAINARCH-013
- ANOX-MAINARCH-018
- ANOX-LEGACY-ANDROIDSEC-001

## 11. Physical verification blockers

- ANOX-MAINARCH-018

## 12. MAINARCH-030 current-vs-future decomposition

- **Current foundation:** `wipeLocalCrypto()` correctly removes existing local crypto files.
- **Future B-009/B-013:** DB/WAL/SHM/attachments/temp cleanup, `preferred_session_id`, per-peer session persistence.

No current product path invokes a false complete-wipe.

## 13. INTEGRATION-004 32-bit ABI scope decision

`ANOX-LEGACY-INTEGRATION-004` is **not promoted** without a product-device-scope decision. `minSdk=26` is an API-level floor, not a CPU-ABI guarantee. The frozen product boundary names GrapheneOS (64-bit Pixel) as the primary target. If a future authority explicitly promises 32-bit production support, this can be re-evaluated.

## 14. Milestone security-review flags

Preserved Open:

- `ANOX-MAINARCH-003` (server ↔ DB/RLS)
- `ANOX-MAINARCH-007` (server ↔ backup/PITR)
- `ANOX-MAINARCH-024` (signing/release custody + incident-response trust boundary)

## 15. Additional milestone security coverage

NONE. No new Product trust boundary was introduced by this consolidation.

## 16. Test / instrumentation status

- JVM unit tests: 161 passed, 0 failed (local `testDebugUnitTest` on baseline)
- Rust tests: 15 passed, 0 failed (`cargo test --locked`)
- Android instrumentation: `NOT_RUN` (device/emulator not available)
- True cross-domain integration test: ABSENT
- B-021 matrix: updated with `ANOX-EVENT-0035`; several client rows remain `NOT_RUN`

## 17. Next task

`ANOX-TASK-LEGACYFIX01` — `LEGACY-FIX-01 — FOUNDATION STATE / REGISTRATION / CRYPTO SAFETY REMEDIATION`

Dependency-sorted remediation of the verified Class-A legacy foundation blockers: ANOX-MAINARCH-019, 023, 031, ANOX-LEGACY-ANDROIDSEC-001, ANOX-LEGACY-CRYPTO-005, ANOX-LEGACY-INTEGRATION-001/002/003. No B-004/B-005 implementation. No Claude.

**Priority:** Class A legacy foundation blockers before product implementation may resume.

## 18. Handoff and cold recovery

Run `python3 tools/continuity/generate_handoff.py` after the metadata commit to produce the cold-recovery archive. The archive must include the `ANOX-EVENT-0035` ledger event, the canonical findings set, the disposition map, and the Class-A remediation batch.
