# FORTSCHRITT — anoX Messenger V1

**Status:** B-017-LITE — CI / SUPPLY-CHAIN SECURITY FOUNDATION; AWAITING INDEPENDENT SECURITY REVIEW
**Updated:** 2026-08-28

## Architecture / governance

- B-001 Master Completeness: DEFINED.
- B-002…B-023: frozen according to `B_FREEZE_REGISTRY.md`.
- B-024 Final MAIN Consistency Audit: PASS.
- B-025 New-Chat Handoff: COMPLETE.
- B-026 Continuous Development Governance: FROZEN on `main`.
- CONTINUITY-001: ACCEPTED.

## Engineering milestones

- PROMPT-001 codebase audit: PASS (historical).
- PROMPT-002 initial crypto foundation: blocker found.
- PROMPT-003 vodozemac message/session handling corrected in code.
- PROMPT-004 Rust validation: 14/14 PASS at that time.
- PROMPT-005 Android/JNI build/link: PASS; runtime initially unverified.
- PROMPT-005B connected Android runtime: 19/19 PASS historically.
- DOCSYNC-001: documentation synchronization, no product functionality.
- PROMPT-005C JNI/FFI hardening: Rust 15/15, Android 27/27, release build PASS.
- PROMPT-006 local protected state lifecycle: Rust 15/15, Android 35/35, release build PASS.
- GIT-001: repository baseline, tag/remote/CI; complete.
- TOOLCHAIN-001: KGP 2.4.10 + Compose plugin 2.4.10 alignment; PR #1 merged; main CI green according to repo report.

## Current repository

`main` is the active branch in the canonical repository `anox-software/anox-messenger`
(`git@github.com:anox-software/anox-messenger.git`). `main` HEAD is
`9c3fb08c30b743274e2c0779937502bb30b313b0` (PR #1 merged). The legacy remote
`anox-admin/ax-messenger` remains historical provenance only.

PROMPT-009R2 hardened the validator and tests; independent retest CLOSED findings
`ANOX-GOVREV-009R-001`, `ANOX-GOVREV-009R-002`, `ANOX-GOVREV-009R-004`. The retest discovered
`ANOX-GOVREV-009R-005` (missing archive record). PROMPT-009R3 recorded `PROMPT-009R2` and
synchronized continuity surfaces. PROMPT-009R4 amended the `PROMPT-009R2` archive entry with the
missing 005/remote provenance, recorded `PROMPT-009R3`, and fixed the recursive
"last Devin task archived" checklist rule. The independent R4 retest CLOSED
`ANOX-GOVREV-009R-005` and `ANOX-GOVREV-009R-006`. PROMPT-010 introduced `docs/authority/GITHUB_REMOTE_ACTIVITY_SAFETY.md` and updated
continuity surfaces. The independent PROMPT-010 review found `ANOX-GOVREV-010-001` (duplicate
authority-index numbering) and `ANOX-GOVREV-010-002` (missing remote-write quick-reference row).
PROMPT-010R1 corrected the numbering in `AUTHORITY_INDEX.md` and added the quick-reference row to
`DEVELOPMENT_SECURITY_WORKFLOW_V1.md`. The independent retest CLOSED `ANOX-GOVREV-010-001` and
`ANOX-GOVREV-010-002`; `PROMPT-010` is ACCEPTED.

REMOTE-MIGRATION-SYNC-001 completed the controlled migration to `anox-software/anox-messenger`,
merged governance PR #1 into `main` at `9c3fb08c30b743274e2c0779937502bb30b313b0`, and reconciled
all current continuity surfaces. `B-017-Lite` was implemented on
`security/b017-lite-supply-chain-foundation`, hardening `.github/workflows/ci.yml`,
`gradle/wrapper/gradle-wrapper.properties`, Rust `cargo test --locked`, and adding
`tools/security/b017_lite_policy_validator.py` with tests. The next authorized gate is
`B-017-LITE INDEPENDENT SECURITY REVIEW`.

## Functional progress

Approximately **33%**. Architecture freezes/governance do not count as completed user-facing
messenger functionality; the percentage reflects merged B-002 plus B-003 client foundations.

## STEP-3B / 3B.1 — B-025 Synchronisation / Android-Backup-Härtung

- Branch: `architecture/b025-main-sync`
- Commits: `c54496c` (Docs/Governance), `2acca43` (Android-Backup/D2D), 3B.1-Korrektur
- B-025-Autoritätsbereich `docs/authority/B025/` hinzugefügt.
- Dokumentdrift zu B-025 korrigiert.
- `android:allowBackup="false"` beibehalten, `dataExtractionRules` mit allen 9 App-Domains (`root`, `file`, `database`, `sharedpref`, `external`, `device_root`, `device_file`, `device_database`, `device_sharedpref`) hinzugefügt.
- `cargo test`: 15/15 PASS.
- CI `32372225161` und anschließende PR-CI: Rust, Android debug, Android release compile smoke PASS.
- Post-Merge-CI auf `main` (`75c11c8`) `32376668391`: Rust, Android debug, Android release compile smoke PASS.
- Connected Instrumentation: NICHT in CI gelaufen.
- PR #2 gemergt in `main`; finaler HEAD `75c11c823ec68cea576912b4095fa7a26ed33a33`.

## PROMPT-008 MERGE

- PR #5 merged via `e7ee54a713e08950c63cf2d61ec97931864b66bc` on `main`.
- 160 JVM unit tests, 62/62 Android instrumentation, Rust 15/15, builds and APK gates green.
- B-003 is MERGED FOUNDATION, not production complete.

## Next approved sequence

1. `DEVELOPMENT SECURITY GOVERNANCE / HANDOFF HARDENING` (cloud-AI secret protection, S0–S4, PR-only-main, cold-chat bootstrap persistence, secure handoff ZIP).
2. After that: `B-017-Lite`.
3. After that: `B-004 Backend DEV`.

## CONTINUITY-001 — Development Governance and Chat Handoff

- **Date:** 2026-08-20
- **Starting HEAD:** `648b70391085ea5252cc9f88375064420f1b78d9`
- **Branch:** `governance/continuity-001`
- **Objective:** Create B-026, the `docs/continuity/` handoff system, and the `tools/continuity/` scripts.
- **Architecture references:** `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Files changed:** `docs/authority/B026_*.md`, `docs/authority/AUTHORITY_INDEX.md`, `docs/continuity/`, `tools/continuity/`, `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- **Implementation summary:** B-026 frozen governance, continuity directory with machine-readable handoff and bootstrap docs, `generate_handoff.py` and `validate_continuity.py` using Python 3 stdlib, updated `PROJECT_STATE`, `FORTSCHRITT`, and `DEVIN` archive.
- **Tests actually run:**
  - `python3 tools/continuity/validate_continuity.py` PASS (after commit)
  - `python3 tools/continuity/generate_handoff.py` PASS (after commit)
  - `git diff --check` PASS
  - `cargo test` 15/15 PASS
- **Tests not run:** `./gradlew` (no local JDK/Android SDK); connected instrumentation; GrapheneOS physical device.
- **CI:** GitHub Actions `32380551703` on PR #3: Rust crypto tests, Android debug build, Android release compile smoke all PASS.
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Commits:** `734e20e` (B-026 continuity and chat handoff foundation).
- **PR:** https://github.com/anox-admin/ax-messenger/pull/3
- **Merge status:** not merged.
- **Final HEAD:** to be recorded after merge.
- **Next gate:** `CONTINUITY-001 ARCHITECT RE-REVIEW`

## CONTINUITY-001.1 — Governance Registry + Handoff Package Validation

- **Date:** 2026-08-20
- **Starting HEAD:** `a2d6e5bc2e0ed7b682f2e0f8e69437b7ff6fb797`
- **Branch:** `governance/continuity-001`
- **Objective:** Resolve architect-review findings: create current `B_FREEZE_REGISTRY.md` and prove handoff ZIP integrity/exclusion/secret/dirty-tree/validator-negative tests.
- **Architecture references:** `docs/authority/AUTHORITY_INDEX.md`, `B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Files changed:** `docs/authority/B_FREEZE_REGISTRY.md`, `docs/authority/AUTHORITY_INDEX.md`, `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`, `tools/continuity/validate_continuity.py`, `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- **Tests actually run:**
  - `ZipFile.testzip()` PASS
  - Internal SHA-256 manifest verification: 170/170 entries verified, 0 mismatches
  - Exclusion scan: 0 prohibited members
  - Secret-pattern sanity scan: 0 obvious secret artifacts
  - Dirty-tree negative test: generator/validator both fail on dirty tree
  - Validator missing-file negative test: non-zero exit with clear reason
  - `git diff --check` PASS
  - `validate_continuity.py` PASS (after commit)
  - `generate_handoff.py` PASS (after commit)
- **Tests not run:** `cargo test` (optional for this governance correction), Android builds
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Commits:** to be recorded after final commit.
- **PR:** https://github.com/anox-admin/ax-messenger/pull/3
- **Merge status:** not merged.
- **Final HEAD:** to be recorded after merge.
- **Next gate:** `CONTINUITY-001 ARCHITECT RE-REVIEW`

## CONTINUITY-001.2A — Historical Provenance Ingestion + Master Parity Correction

- **Date:** 2026-08-20
- **Starting HEAD:** `1bd306d696057c92bfd84dd9c14f1de506066994`
- **Branch:** `governance/continuity-001`
- **Objective:** Ingest missing B-025 historical/provenance material into `docs/history/B025/` and re-establish master handoff parity.
- **Architecture references:** `docs/authority/AUTHORITY_INDEX.md`, `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Files changed:** `docs/history/B025/` (66+ files), `docs/history/README.md`, `docs/continuity/CURRENT_HANDOFF.md`, `docs/continuity/HISTORICAL_HANDOFFS/README.md`, `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`, `docs/reports/CONTINUITY_001_2_MASTER_PARITY_AUDIT.md`
- **Tests actually run:**
  - `python3 tools/continuity/validate_continuity.py` PASS
  - `python3 tools/continuity/generate_handoff.py` PASS
  - `git diff --check` PASS
  - Handoff ZIP integrity, manifest, exclusion, secret checks PASS
  - `ZipFile.testzip()` PASS
  - Internal SHA-256 manifest: 238/238 verified, 0 mismatches
  - Prohibited/secret scan: 0/0
  - 20/20 reconstruction questions ANSWERABLE
- **Tests not run:** `cargo test` (governance correction); Android builds
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Commits:** to be recorded after final commit.
- **PR:** https://github.com/anox-admin/ax-messenger/pull/3
- **Merge status:** not merged.
- **Final HEAD:** to be recorded after merge.
- **Next gate:** `CONTINUITY-001.3 — COLD NEW-CHAT BOOTSTRAP TEST`

## CONTINUITY-001.3A — Atomic Handoff State Consistency Fix

- **Date:** 2026-08-20
- **Starting HEAD:** `6fd123f13ac1...`
- **Branch:** `governance/continuity-001`
- **Objective:** Fix the atomic handoff state consistency defect detected by the cold new-chat bootstrap (stale `CURRENT_GIT_STATE.md`, `PROJECT_STATE.md`, `CURRENT_NEXT_DEVIN_TASK.md`, incorrect Security Invariants path, no machine-readable state).
- **Architecture references:** `docs/authority/AUTHORITY_INDEX.md`, `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Files changed:** `docs/continuity/CURRENT_GIT_STATE.md`, `docs/continuity/CURRENT_HANDOFF.md`, `docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md`, `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md`, `docs/continuity/CURRENT_STATE.json`, `PROJECT_STATE.md`, `tools/continuity/validate_continuity.py`, `tools/continuity/generate_handoff.py`
- **Tests actually run:**
  - `python3 tools/continuity/validate_continuity.py` PASS
  - `python3 tools/continuity/generate_handoff.py` PASS
  - `git diff --check` PASS
  - Negative regression tests for stale HEAD, branch, security-invariants path, next gate, dirty tree → validator FAIL
  - Restored correct state → validator PASS
  - `ZipFile.testzip()` PASS
  - Internal SHA-256 manifest verified
  - Exclusion/secret scan 0/0
  - 20/20 reconstruction questions remain ANSWERABLE
- **Tests not run:** `cargo test` (governance correction); Android builds
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Commits:** to be recorded after final commit.
- **PR:** https://github.com/anox-admin/ax-messenger/pull/3
- **Merge status:** not merged.
- **Final HEAD:** to be recorded after merge.
- **Next gate:** `CONTINUITY-001.3 — COLD NEW-CHAT BOOTSTRAP RETEST`

## CONTINUITY-001.3 — Cold New-Chat Bootstrap Retest

- **Date:** 2026-08-21
- **Branch:** `governance/continuity-001`
- **Objective:** Verify that a clean new ChatGPT conversation can reconstruct the project state from the generated handoff package.
- **Architecture references:** `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Tests actually run:**
  - New-chat bootstrap on `ANOX_HANDOFF_2026-08-21_06023258f60e.zip`
  - Result: `BOOTSTRAP RESULT: PASS — READY TO ACCEPT HANDOFF`
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Next gate:** `CONTINUITY-001 FINAL ARCHITECT REVIEW / PR #3 MERGE GATE`

## CONTINUITY-001.3B — Cold-Bootstrap Pass Finalization

- **Date:** 2026-08-21
- **Branch:** `governance/continuity-001`
- **Objective:** Record the PASS result, apply the B-010 path correction, add the handoff retention/performance policy, and fix README evidence drift.
- **Architecture references:** `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Files changed:** `README.md`, `docs/authority/B_FREEZE_REGISTRY.md`, `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`, `docs/continuity/CURRENT_STATE.json`, `docs/continuity/CURRENT_GIT_STATE.md`, `docs/continuity/CURRENT_HANDOFF.md`, `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md`, `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- **Tests actually run:**
  - `python3 tools/continuity/validate_continuity.py` PASS
  - `git diff --check` PASS
  - B-010 path now resolves to existing `B010_CONTACTS_VERIFICATION.md`
- **Tests not run:** `cargo test` (documentation/governance-only); no new handoff ZIP generated
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Next gate:** `CONTINUITY-001 FINAL ARCHITECT REVIEW / PR #3 MERGE GATE`

## CONTINUITY-001.4 — APK Content / Secret Leakage Release Gate

- **Date:** 2026-08-21
- **Branch:** `governance/continuity-001`
- **Objective:** Establish a permanent APK content / secret leakage release gate and integrate it into CI.
- **Architecture references:** `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`, `docs/authority/B017_CICD_SUPPLY_CHAIN.md`, `docs/authority/B018_RELEASE_SIGNING_UPDATES.md`, `docs/authority/B023_RELEASE_DOD.md`
- **Files changed:** `tools/security/validate_apk_contents.py` (new), `.github/workflows/ci.yml`, `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`, `docs/continuity/CURRENT_STATE.json`, `docs/continuity/CURRENT_GIT_STATE.md`, `docs/continuity/CURRENT_HANDOFF.md`, `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md`, `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- **Tests actually run:**
  - `python3 tools/continuity/validate_continuity.py` PASS
  - `python3 tools/security/validate_apk_contents.py` on synthetic forbidden APKs → FAIL (expected)
  - `python3 tools/security/validate_apk_contents.py` on synthetic benign APK → PASS
  - `python3 tools/security/validate_apk_contents.py` on real debug APK from CI → PASS
  - `python3 tools/security/validate_apk_contents.py` on real release APK from CI → PASS
  - `git diff --check` PASS
- **Tests not run:** `cargo test` (tooling/governance-only)
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Next gate:** `CONTINUITY-001 FINAL ARCHITECT REVIEW / PR #3 MERGE GATE`

## CONTINUITY-001 FINAL — PR #3 Merge and Main Finalization

- **Date:** 2026-08-21
- **Branch:** `main`
- **Objective:** Merge the authorized CONTINUITY-001 branch and finalize main-branch continuity state.
- **Architecture references:** `docs/authority/AUTHORITY_INDEX.md`, `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Files changed:** `docs/continuity/CURRENT_STATE.json`, `docs/continuity/CURRENT_GIT_STATE.md`, `docs/continuity/CURRENT_HANDOFF.md`, `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md`, `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md`, `docs/continuity/CURRENT_OPEN_WORK.md`, `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- **Tests actually run:**
  - `python3 tools/continuity/validate_continuity.py` PASS
  - `python3 tools/continuity/generate_handoff.py` PASS
  - `python3 tools/security/validate_apk_contents.py` on final main debug APK from CI → PASS
  - `python3 tools/security/validate_apk_contents.py` on final main release APK from CI → PASS
  - `git diff --check` PASS
- **Tests not run:** `cargo test` (merged from CI)
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Next gate:** `FINAL NEW-CHAT HANDOFF ACCEPTANCE`

## CONTINUITY-001.5 — Final Main Continuity State Synchronization Fix

- **Date:** 2026-08-21
- **Branch:** `main`
- **Objective:** Fix stale current-state records in `PROJECT_STATE.md` and `FORTSCHRITT.md` that caused the new-chat bootstrap to BLOCK.
- **Architecture references:** `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Files changed:** `PROJECT_STATE.md`, `FORTSCHRITT.md`, `docs/continuity/CURRENT_GIT_STATE.md`, `docs/continuity/CURRENT_HANDOFF.md`, `tools/continuity/validate_continuity.py`, `tools/continuity/generate_handoff.py`
- **Tests actually run:**
  - `python3 tools/continuity/validate_continuity.py` PASS
  - `python3 tools/continuity/generate_handoff.py` PASS
  - `git diff --check` PASS
  - negative regression tests: stale branch, unresolved placeholder, stale gate, inconsistent CONTINUITY status, dirty tree → all FAIL as expected
  - restored correct state → PASS
- **Tests not run:** `cargo test` (merged from CI)
- **Security invariants:** No invariants changed.
- **Blockers:** none.
- **Next gate:** `FINAL NEW-CHAT HANDOFF ACCEPTANCE RETEST`

## PROMPT-007 — B-002 Device Authentication Foundation

- **Date:** 2026-08-21
- **Branch:** `feature/b002-device-auth-foundation`
- **Starting HEAD:** `33440823f3d2a785202ca1828e4bf9c71b175008` (`main`)
- **Objective:** Implement the minimum production-oriented B-002 Device Authentication client foundation.
- **Architecture references:** `docs/authority/B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md`, `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`, `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Implemented:**
  - Android Keystore P-256/ES256 non-exportable Device Auth key, dedicated alias separate from `K_STATE`.
  - StrongBox preferred with TEE fallback; no per-use user authentication.
  - Hardware policy: StrongBox/TEE production eligible; software-only and unprovable hardware rejected fail-closed.
  - Public-only JWK exposure plus RFC7638 `jkt` thumbprint.
  - RFC9449 DPoP proof creation and a testable verification boundary.
  - Frozen parameters: `jti` >= 128 bits, `iat` +/-120s, replay window 5 min, opaque 256-bit token, SHA-256-only storage, 15 min TTL, no refresh token.
  - Terminal Device Auth key loss fail-closed; no silent replacement key, no re-binding.
- **Dependency added:** `com.nimbusds:nimbus-jose-jwt:10.9.1` (pinned; standards-compliant ES256/JWK/JWS; supports non-extractable Keystore keys). No AGP/Kotlin/Compose/Gradle/NDK change.
- **Files changed:** 15 new sources under `android/src/main/java/com/anox/messenger/security/deviceauth/`, 6 new JVM test files, 1 new instrumentation test file, `android/build.gradle.kts`, `.github/workflows/ci.yml`, `docs/reports/PROMPT_007_DEVICE_AUTH_FOUNDATION.md`
- **Tests actually run:**
  - JVM unit tests: **69 tests, 0 failures, 0 skipped** (CI run `32514140072`)
  - Rust `cargo test`: PASS (CI)
  - Android debug build: PASS (CI)
  - Android release compile smoke: PASS (CI)
  - Debug APK content/secret gate: PASS (CI)
  - Release APK content/secret gate: PASS (CI)
  - `git diff --check`: PASS
- **Tests NOT run / UNVERIFIED:**
  - Android instrumentation tests for the real Keystore: NOT RUN (no emulator in CI)
  - Physical hardware-backed StrongBox/TEE behaviour: UNVERIFIED
  - GrapheneOS physical-device Device Auth behaviour: UNVERIFIED
- **Security invariants:** No invariants changed. No `docs/authority/` file modified.
- **Product foundation:** crypto, JNI, vodozemac, `K_STATE`, `[ANOX][0x01]`, native `.so` and build tooling unchanged.
- **Blockers:** none.
- **PR:** https://github.com/anox-admin/ax-messenger/pull/4 (open, not merged)
- **Next gate:** `PROMPT-007 ARCHITECT REVIEW / PR #4 MERGE GATE`

## PROMPT-007B — B-002 Independent Security / Architecture Review

- **Date:** 2026-08-21
- **Mode:** strict read-only review, no source/test/doc/CI changes.
- **Result:** `APPROVE — READY FOR PROMPT-007 MERGE GATE`; `NO MERGE-BLOCKING SECURITY FINDINGS`.
- Verified live baseline, diff, and PR #4 state directly against GitHub; no unexpected drift.
- Independently downloaded and read the actual `nimbus-jose-jwt:10.9.1` sources jar to verify: `ECDSASigner`/`ECDSAVerifier` use standard JCA (no hand-rolled crypto); `ECDSAVerifier` guards against invalid-curve attacks and CVE-2022-21449; private JWK headers are rejected at the library level (`JWSHeader.Builder.jwk`, `CommonSEHeader.parsePublicJWK`); `alg=none` is structurally impossible (`JWSHeader` constructor throws).
- Analytically confirmed (POM `optional=true`, no Gradle Module Metadata, no BC/Tink declared in `build.gradle.kts`, source-level confirmation the only BC-referencing method is unreachable) that BouncyCastle/Tink are not expected in the runtime dependency graph; recommended empirical `./gradlew :android:dependencies` confirmation as non-blocking follow-up.
- Findings: 1 LOW (stale `PROJECT_STATE.md` current-gate line), 4 INFO (dependency-tree not empirically captured; Keystore instrumentation unexecuted; replay cache dedups on `jti` alone; no explicit `alg=none` test). None merge-blocking.
- `git status --short` confirmed clean at end of review; no tracked file modified.
- **Next gate:** `PROMPT-007C — B-002 MERGE / CONTINUITY SYNCHRONIZATION`

## PROMPT-007C — B-002 Merge / Continuity Synchronization

- **Date:** 2026-08-22
- **Starting HEAD:** `d36eaf4f668f3dc12164fc2dae3b71c11d2ca303` on `feature/b002-device-auth-foundation`
- **Objective:** Verify PR #4 final state, close remaining PROMPT-007B non-blocking items where
  possible, synchronize governance, merge PR #4, and synchronize continuity to the new `main`.
- **Pre-merge fixes (commit `9197fe7`):** corrected stale `PROJECT_STATE.md` current-gate line;
  empirically verified the Android runtime dependency graph.
- **Dependency-tree verification:** obtained a local JDK 17 (Temurin) and ran
  `./gradlew :android:dependencies` on `debugRuntimeClasspath`, `releaseRuntimeClasspath`, and
  `debugUnitTestRuntimeClasspath`, plus `dependencyInsight --dependency nimbus-jose-jwt`.
  Result: `com.nimbusds:nimbus-jose-jwt:10.9.1` resolves as a leaf dependency in all three;
  BouncyCastle (`bcprov`/`bcpkix`/`bcutil-jdk18on`) and `com.google.crypto.tink:tink` are NOT
  resolved anywhere. Additionally built the debug and release APKs locally and used `dexdump`
  to confirm zero actual BouncyCastle/Tink class definitions in either `classes.dex`; the raw
  strings `org/bouncycastle` and `com/google/crypto/tink` present in the dex string pool are
  unresolved type-name references from Nimbus's own unused optional classes (`Ed25519Signer`,
  `X25519Encrypter`, `BouncyCastleProviderSingleton`), never invoked by anoX, and remain only
  because `isMinifyEnabled=false`.
- **Tests actually run (local, independent of CI):**
  - `cargo test` (crypto/rust): 15/15 PASS
  - `./gradlew :android:testDebugUnitTest`: 69/69 PASS, 0 failures, 0 errors (verified via
    `test-results/testDebugUnitTest/*.xml`)
  - `./gradlew :android:assembleDebug`: PASS
  - `./gradlew :android:assembleRelease`: PASS
  - `python3 tools/security/validate_apk_contents.py` on both the freshly built debug and
    release APKs: PASS (0 forbidden findings, 0 secret markers)
  - `git diff --check`: PASS
  - `python3 tools/continuity/validate_continuity.py`: PASS (pre-merge, on the feature branch)
- **Tests NOT run / UNVERIFIED:** Android instrumentation for the real Keystore (no
  `adb`/emulator/device available); physical StrongBox/TEE behaviour; GrapheneOS physical
  device behaviour. Unchanged from PROMPT-007/007B.
- **CI:** final feature-branch CI run `32574948320` on commit `9197fe7`: Rust, JVM unit tests,
  Android debug build + APK content validation, Android release compile smoke + APK content
  validation — all `success`.
- **Security gate:** no new blocker discovered; all PROMPT-007B non-blocking findings addressed
  or explicitly re-confirmed unchanged.
- **PR merge:** PR #4 merged into `main` via GitHub API (`merge` method). Merge commit:
  `d281df66a3471dfd6a9bab0bd899be701317afb4`.
- **Post-merge main verification:** `main` fast-forwarded to `d281df66a3471dfd6a9bab0bd899be701317afb4`;
  working tree clean; `python3 tools/continuity/validate_continuity.py` re-run post-sync: PASS.
- **Continuity synchronization:** `PROJECT_STATE.md`, `FORTSCHRITT.md`,
  `DEVIN_PROMPT_OUTPUT_ARCHIV.md`, `docs/continuity/CURRENT_STATE.json`,
  `CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, `CURRENT_IMPLEMENTATION_STATE.md`,
  `CURRENT_OPEN_WORK.md`, `CURRENT_NEXT_DEVIN_TASK.md` all updated to reflect the merged
  `main` state; B-002 explicitly kept as client-foundation-only, not production-complete.
- **Security invariants:** No invariants changed. No `docs/authority/` file modified.
- **Blockers:** none.
- **Next gate:** `B-003 ACCOUNT / LICENSE FOUNDATION — NOT STARTED, NOT AUTHORIZED`

## PROMPT-008 — B-003 Account / License Foundation

- **Date:** 2026-08-22
- **Branch:** `feature/b003-account-license-foundation`
- **Starting HEAD:** `0785b6001f816f5a6520951dd9a8c5a4af9af4c2` (`main`)
- **Objective:** Implement the minimum B-003 Account/License client domain/state foundation
  without implementing B-004 backend or B-005 database/RLS.
- **Architecture references:** `docs/authority/B025/TRACK_B/B003_ACCOUNT_LICENSE.md`,
  `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`,
  `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- **Implemented:**
  - `AccountId`/`DeviceId`/`RegistrationId` value types: server-issued UUIDv4 only, no client
    generation, non-v4 UUIDs rejected.
  - `Username` syntax validation (lowercase ASCII `[a-z0-9_.]`, 3-32); invalid input is rejected,
    never silently lowercased.
  - `LicenseCode` structural validation (`anox-XXXX-XXXX-XXXX`), secret-safe `toString()`, no
    generation method (server responsibility).
  - `LicenseDuration` with exactly `{30, 90, 180}` days; no 365-day/one-week variant.
  - Frozen `AccountState`/`DeviceState`/`EntitlementState` enums; non-authoritative
    `EntitlementRenewal` preview taking server time as an explicit input, never the local clock.
  - `RegistrationState` sealed state machine and `RegistrationOrchestrator` driving
    reserve -> Device Auth registration (reusing the existing B-002 boundary unmodified) ->
    public E2EE identity upload (via a new `LocalE2eeIdentityStep` boundary calling the existing,
    unmodified `CryptoBridge` public API) -> atomic commit. The Device Auth key is marked bound
    from exactly one call site, only after a successful commit.
  - `RegistrationApi` narrow contract interface (no real HTTP stack, no fake backend).
  - `FileDeviceAuthBindingStore`: persistent, no-backup, fail-closed (corrupt -> bound) —
    closes the PROMPT-007 in-memory-only gap.
  - `FileRegistrationSessionStore`: persistent, no-backup, crash-resumable registration session
    state; corrupt -> `NotStarted` (opposite fail-closed direction, deliberately, since there is
    no security asymmetry to preserve there).
- **Files changed:** 17 new sources under `android/src/main/java/com/anox/messenger/account/`,
  1 new file under `security/deviceauth/`, 1 new shared storage utility, 10 new JVM test files,
  2 new instrumentation test files, `docs/reports/PROMPT_008_B003_ACCOUNT_LICENSE_FOUNDATION.md`.
- **Tests actually run:**
  - JVM unit tests: **146/146 PASS** (77 new, 69 pre-existing unchanged), 0 failures, 0 errors
    (local run against a downloaded JDK 17; no build.gradle.kts/CI change was required since the
    existing `testDebugUnitTest` step already covers the whole `src/test/java` tree)
  - Android instrumentation: **58/58 PASS**, 0 failures, 0 errors, on a real emulator
    (`anox_api34_arm64`, API 34) that was unexpectedly available in this environment. This
    includes, for the first time, the 10 B-002 `AndroidKeystoreDeviceAuthKeyManagerTest` tests
    (previously never executed) and the 35 pre-existing `CryptoInstrumentedTest` tests, plus 7
    new `FileDeviceAuthBindingStoreTest` and 6 new `FileRegistrationSessionStoreTest` tests.
  - `cargo test`: 15/15 PASS
  - `./gradlew :android:assembleDebug` / `:android:assembleRelease`: PASS
  - Debug + release APK content/secret gate: PASS
  - `git diff --check`: PASS
- **Tests NOT run / UNVERIFIED:**
  - Physical hardware-backed StrongBox/TEE behaviour: UNVERIFIED (emulator only, not physical).
  - GrapheneOS physical-device behaviour: UNVERIFIED.
- **CI:** no workflow change required; existing `Run JVM unit tests` step already covers the new
  package. Instrumentation remains not runnable in CI (no emulator there), unchanged from
  PROMPT-007.
- **Security invariants:** No invariants changed. No `docs/authority/` file modified.
- **Product foundation:** crypto, JNI, vodozemac, `K_STATE`, `[ANOX][0x01]`, native `.so`, build
  tooling, and the B-002 Device Auth security model unchanged; `CryptoBridge` called through its
  existing public API only, never modified.
- **Blockers:** none.
- **PR:** https://github.com/anox-admin/ax-messenger/pull/5 (open, not merged; requires a
  separate architect security/architecture review, per PROMPT-008B)
- **CI on PR #5 HEAD `3e06af9`:** run `32578497395` — Rust, Android debug build, Android
  release compile smoke all `success`
- **Next gate:** `PROMPT-008 ARCHITECT REVIEW / PR MERGE GATE`

### 2026-08-23 — PROMPT-008C — B-003 Account/License security review remediation

- **Task:** close all PROMPT-008B findings before any PR #5 merge decision.
- **Findings remediated:**
  - HIGH-1: remote-commit / local-binding crash-consistency fixed by marking Device Auth binding
    before persisting `Committed`; `failStep` will not overwrite terminal/bound state.
  - MEDIUM-2: registration grant persisted with dedicated Android Keystore AES-256-GCM
    (`anox.b003.session.v1`), fresh IV per write; never plaintext at rest.
  - MEDIUM-3: stale `.tmp` / plaintext artifacts eliminated via `androidx.core.util.AtomicFile`
    and `BinaryRegistrationStateCodec`.
  - LOW-4: new `FileRegistrationSessionStore` uses the established `AtomicFile` primitive.
  - LOW-5: `RegistrationState.Committed` is now terminal.
  - LOW-6: fragile newline/equals text codec replaced with versioned length-prefixed binary codec.
- **Changes:** new `RegistrationSessionKey`, `BinaryRegistrationStateCodec`,
  `RegistrationSessionSecurityException`; rewritten `FileRegistrationSessionStore`;
  hardened `RegistrationOrchestrator`; `RegistrationGrantGenerator` moved to `src/test`;
  new `RegistrationCrashConsistencyTest` with fault-injection crash matrix.
- **Tests:** 160 JVM unit tests PASS, 0 failures; Rust 15/15 PASS; Android debug + release build
  and both APK content gates PASS. Instrumentation NOT RUN (no emulator/device available).
- **Authority:** unchanged. No `docs/authority/` file modified.
- **Cloud-AI secret status:** no production/root/user secret introduced or exposed.
- **Next gate:** `PROMPT-008 MERGE GATE`.
