# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-08-22
**Architecture:** Track B B-001…B-023 frozen/defined, B-024 PASS, B-025 COMPLETE, B-026 FROZEN.
**Functional implementation:** approximately 32%.

## Repository truth

- Branch: `feature/b003-account-license-foundation`
- Current HEAD: resolve from `CURRENT_GIT_STATE.md` or `GIT_SNAPSHOT.txt`
- Merged baseline branch: `main`
- Merged baseline HEAD: `0785b6001f816f5a6520951dd9a8c5a4af9af4c2`
- Open PR: `#5` → `main`, PROMPT-008 / B-003 Account/License foundation; not merged
- PR #4 (PROMPT-007 / B-002 Device Auth foundation): merged at
  `d281df66a3471dfd6a9bab0bd899be701317afb4`
- B-025 PR #2: merged at `75c11c823ec68cea576912b4095fa7a26ed33a33`
- PR #3: merged at `7320253f27a1eef32847b992f13292d77178c4db`
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- CONTINUITY-001: ACCEPTED
- B-026: FROZEN on `main`
- Current gate: `PROMPT-008 ARCHITECT REVIEW / PR MERGE GATE`
- Latest main CI: see `FORTSCHRITT.md` / `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- GIT-001: FULL PASS in repo documentation.
- TOOLCHAIN-001: PR #1 merged; main CI green.
- Clean Git snapshot is the implementation baseline.

## Checked-in toolchain

AGP 8.13.2; Kotlin Gradle Plugin 2.4.10; Compose plugin 2.4.10; Gradle 9.3.1; JDK 17; NDK 26.2.11394342; compileSdk/targetSdk/minSdk 34/34/26. Rust evidence reports 1.97.1/cargo-ndk 4.1.2; Cargo pins vodozemac 0.10.0 and aes-gcm 0.10.3.

## Implemented / accepted at implemented-test level

- Minimal Android/Compose app foundation.
- Rust vodozemac crypto foundation with real session round-trip/negative tests.
- JNI bridge and typed identity/session handle safety.
- AES-GCM local state protection with Android Keystore-wrapped random state key.
- Versioned state envelope `[ANOX][0x01][12-byte nonce][ciphertext+tag]`, AAD magic/version.
- Atomic file persistence, state lifecycle/fail-closed status, local wipe APIs.
- Historical accepted test evidence: Rust 15/15; Android connected 35/35; release build PASS.

## PROMPT-007 — B-002 Device Authentication foundation — MERGED (2026-08-22)

Merged into `main` at `d281df66a3471dfd6a9bab0bd899be701317afb4` via PR #4. Status per
component below; this is a client foundation merge, not a claim that B-002 is production
complete or that backend enforcement now exists.

**IMPLEMENTED (client foundation)**
- Android Keystore P-256/ES256 non-exportable Device Auth key, separate alias from `K_STATE`.
- StrongBox preferred with TEE fallback; no per-use user authentication.
- Hardware policy: StrongBox/TEE production eligible; software-only and unprovable hardware
  rejected fail-closed.
- Public-only JWK exposure plus RFC7638 `jkt` thumbprint.
- RFC9449 DPoP proof creation (`typ=dpop+jwt`, ES256, `jti`/`htm`/`htu`/`iat`/`ath`/`nonce`).
- DPoP verification boundary with ES256 confinement, key binding, replay control.
- Frozen parameters: `jti` >= 128 bits, `iat` +/-120s, replay window 5 min, opaque 256-bit
  token, SHA-256-only storage, 15 min TTL, no refresh token.
- Terminal Device Auth key loss is fail-closed; no silent replacement key, no re-binding.

**VERIFIED**
- 69 JVM unit tests, 0 failures, 0 skipped — confirmed on CI (runs `32514140072`,
  `32516700604`, `32574948320`) and independently re-run locally against the exact merged
  code, covering the positive path and every required negative path.
- Rust 15/15, Android debug build, Android release compile smoke, debug + release APK content
  gate: all PASS on PR #4 and independently re-run locally.
- Independent security/architecture review (PROMPT-007B): `APPROVE — READY FOR PROMPT-007
  MERGE GATE`; no merge-blocking findings.
- Empirical dependency-tree verification (PROMPT-007C): `./gradlew :android:dependencies` on
  `debugRuntimeClasspath`, `releaseRuntimeClasspath`, and `debugUnitTestRuntimeClasspath`
  confirms `com.nimbusds:nimbus-jose-jwt:10.9.1` resolves as a leaf dependency; BouncyCastle
  (`bcprov`/`bcpkix`/`bcutil`) and `com.google.crypto.tink:tink` are NOT resolved into any of
  these classpaths. Cross-checked with `dexdump` against the built debug/release APKs: zero
  actual BouncyCastle/Tink class definitions in either `classes.dex`.
- PR #4 merged into `main`: merge commit `d281df66a3471dfd6a9bab0bd899be701317afb4`.

**PARTIAL**
- `DeviceAuthBindingStore` has only an in-memory implementation; persistence is required
  before real device binding.
- `isProductionEligible()` is computed but has no registration call site to enforce yet.
- StrongBox cannot be distinguished from TEE below API 31; reported conservatively as TEE.

**MISSING (not attempted in this task)**
- B-003 registration/binding call, B-004 backend token issuance/storage/revocation, shared
  production replay cache, device registry, entitlement enforcement, restricted
  expired-entitlement renewal flow.

**UNVERIFIED**
- Android instrumentation tests for the real Keystore: NOT RUN in CI (no emulator); subsequently
  run and PASSING (10/10) on a local emulator during PROMPT-008 — see that section below. Still
  not run in CI.
- Physical hardware-backed StrongBox/TEE behaviour.
- GrapheneOS physical-device Device Auth behaviour.

## PROMPT-008 — B-003 Account/License foundation (2026-08-22)

Status per component, not a claim that B-003 is production complete.

**IMPLEMENTED (client domain/state foundation)**
- Strongly typed `AccountId`/`DeviceId`/`RegistrationId` (server-issued UUIDv4 only, no client
  generation), `Username` syntax validation, `LicenseCode` structural validation (secret-safe),
  `LicenseDuration` (30/90/180 days only), frozen `AccountState`/`DeviceState`/
  `EntitlementState` enums, non-authoritative `EntitlementRenewal` preview.
- `RegistrationState` transaction state machine and `RegistrationOrchestrator` driving
  reserve -> Device Auth registration -> public E2EE identity upload -> atomic commit, never
  marking the Device Auth key bound before a successful commit.
- Narrow `RegistrationApi` / `LocalE2eeIdentityStep` contracts (no real backend, no fake
  Supabase/PostgreSQL access).
- Persistent `FileDeviceAuthBindingStore` (closes the PROMPT-007 in-memory-only gap) and
  persistent `FileRegistrationSessionStore`, both under `noBackupFilesDir`, fail-closed on
  corruption.

**VERIFIED**
- 146 JVM unit tests (77 new + 69 pre-existing B-002, unchanged), 0 failures.
- 58 Android instrumentation tests on a real emulator (API 34), 0 failures, including — for the
  first time — the 10 B-002 `AndroidKeystoreDeviceAuthKeyManagerTest` tests and 35 pre-existing
  `CryptoInstrumentedTest` tests.
- Rust 15/15, Android debug/release build, debug + release APK content gate: all PASS.

**PARTIAL**
- `LicenseCode` structural validation assumes a placeholder uppercase-alphanumeric charset
  pending the exact "unambiguous character" definition.
- One-active-device-per-account is representable, not enforced (enforcement is DB-level, B-005).

**MISSING (not attempted in this task)**
- B-004 backend implementation of `RegistrationApi`, B-005 database/RLS, license generation,
  server HMAC lookup, real network stack, UI/ViewModel wiring.

**UNVERIFIED**
- Physical hardware-backed StrongBox/TEE behaviour.
- GrapheneOS physical-device behaviour.

## Not implemented

- B-002 Device Authentication: backend/server side and registration binding (client
  foundation only, see PROMPT-007 above).
- B-003 production account/license registration: backend/server side, license generation,
  server HMAC lookup, DB enforcement (client domain/state foundation only, see PROMPT-008
  above).
- B-004 backend service.
- B-005 production database/RLS.
- B-006 server key distribution/claims.
- B-007 production API.
- B-008 network messaging/sync.
- B-009 SQLCipher messenger DB/outbox.
- B-010 contacts/SAS product flow.
- B-011 push/offline jobs.
- B-012 attachment secretstream/storage.
- B-013 production server lifecycle.
- Production privacy/abuse/infrastructure/signing/operations/test/audit/release gates.

## STEP-3B — B-025 repository synchronization (2026-08-20)

- Branch: `architecture/b025-main-sync`
- B-025 authority area added at `docs/authority/B025/`.
- Documentation drift corrected; Device Auth, refresh token, recovery, multi-device, QR/SAS, push, attachments, and other stale statements are now aligned with B-025.
- Android backup/D2D hardening added: `android:allowBackup="false"` retained, `dataExtractionRules` excludes all 9 app-owned storage domains (`root`, `file`, `database`, `sharedpref`, `external`, `device_root`, `device_file`, `device_database`, `device_sharedpref`) from both cloud backup and device transfer.
- Protected foundation (crypto, JNI, build tooling, native `.so`) unchanged.
- `cargo test`: 15/15 PASS (local).
- GitHub Actions CI run `32372225161` on PR #2: Rust, Android debug, and Android release compile smoke all PASS.
- PR #2 merged; main HEAD `75c11c823ec68cea576912b4095fa7a26ed33a33`; post-merge CI `32376668391`: Rust, Android debug, and Android release compile smoke all PASS.
- Connected Android instrumentation: NOT RUN in CI (no emulator); historical 35/35 remains accepted.
- PROMPT-007 was not executed.

## CONTINUITY-001 — Development governance and handoff foundation

- Branch: `governance/continuity-001`
- B-026 governance specification: `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- Master authority index: `docs/authority/AUTHORITY_INDEX.md`
- New `docs/continuity/` directory with handoff, bootstrap, Git state, implementation state, open work, next task, output contract, workflow, and validation checklist.
- New `tools/continuity/validate_continuity.py` and `tools/continuity/generate_handoff.py` (Python 3 standard library only, no network).
- `validate_continuity.py` requires clean working tree, required files, and B-025/B-026 authority.
- `generate_handoff.py` creates `artifacts/handoff/ANOX_HANDOFF_*.zip` with file manifest and SHA-256 manifest.
- Android/Rust product source unchanged.
- Result: PASS — ready for architect review.

## CONTINUITY-001.1 — Governance registry and handoff package validation

- Branch: `governance/continuity-001`
- Created current `docs/authority/B_FREEZE_REGISTRY.md` (B-001…B-026) while preserving `docs/authority/B025/B_FREEZE_REGISTRY.md` as immutable B-025 snapshot.
- Updated `docs/authority/AUTHORITY_INDEX.md`, `B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`, and `validate_continuity.py` to reference the current registry.
- Generated handoff ZIP on current branch; ran `ZipFile.testzip()` (PASS), internal SHA-256 manifest verification (170/170 entries verified, 0 mismatches), exclusion scan (0 prohibited members), secret-pattern sanity scan (0 obvious secret artifacts), dirty-tree negative test (generator and validator both fail on dirty tree), and validator missing-file negative test (non-zero exit, clear reason).
- Re-ran `validate_continuity.py` and `generate_handoff.py` after commit: expected PASS.
- Product source unchanged; next gate remains `CONTINUITY-001 ARCHITECT RE-REVIEW`.

## CONTINUITY-001.2A — Historical provenance ingestion and master parity correction

- Branch: `governance/continuity-001`
- Ingested historical provenance from `ANOX_MASTER_HANDOFF_B025_2026-08-20.zip` into `docs/history/B025/`:
  - `00_START/`, `03_WORKFLOWS/`, `05_ENGINEERING_NEXT/`, `06_AUDITS/`, `07_DEVIN_HISTORY/`, `90_HISTORICAL/`
  - `REPOSITORY_PROVENANCE/` with `REPOSITORY_SNAPSHOT_MANIFEST.md` and `GIT_BUNDLE_STATUS.md`
- Created `docs/history/B025/README.md`, `SOURCE_INDEX.md`, `docs/history/README.md`.
- Updated `docs/continuity/CURRENT_HANDOFF.md` and `docs/continuity/HISTORICAL_HANDOFFS/README.md` to reference the historical archive.
- Full-history Git bundle intentionally not replicated; reason documented.
- Product source unchanged.
- Re-generated handoff `ANOX_HANDOFF_2026-08-20_c2b3afc1b93e.zip`; parity verified PASS: 241 members, 238/238 manifest entries verified, 0 prohibited, 0 secret, 20/20 reconstruction questions ANSWERABLE.
- New `docs/reports/CONTINUITY_001_2_MASTER_PARITY_AUDIT.md` created.

## CONTINUITY-001.3A — Atomic handoff state consistency fix

- Branch: `governance/continuity-001`
- Cold new-chat bootstrap for `ANOX_HANDOFF_2026-08-20_c2b3afc1b93e.zip` returned `BLOCKED` because recorded `CURRENT_GIT_STATE.md`, `PROJECT_STATE.md`, `CURRENT_NEXT_DEVIN_TASK.md`, and `CURRENT_HANDOFF.md` described the merged `main` baseline instead of the current handoff branch `governance/continuity-001`.
- Corrected `CURRENT_GIT_STATE.md` and `PROJECT_STATE.md` to explicitly separate **merged baseline** (`main`) from **current handoff / work state** (`governance/continuity-001`).
- Introduced `docs/continuity/CURRENT_STATE.json` as machine-readable canonical continuity metadata with placeholders for `handoff_head` and `working_tree` that `generate_handoff.py` resolves at generation time.
- Updated `CURRENT_HANDOFF.md` and `CURRENT_CHAT_BOOTSTRAP_PROMPT.md` to reference the canonical `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md` path.
- Extended `validate_continuity.py` to fail on branch/HEAD/authority/gate inconsistencies.
- Extended `generate_handoff.py` to validate continuity state before packaging and to fail closed if validation fails.
- Product source unchanged.

## CONTINUITY-001.3 — Cold new-chat bootstrap retest

- Tested handoff: `ANOX_HANDOFF_2026-08-21_06023258f60e.zip`
- Branch: `governance/continuity-001`, HEAD `06023258f60e086d3a8f04e6fe98dc8bab0a0493`
- Result: `BOOTSTRAP RESULT: PASS — READY TO ACCEPT HANDOFF`
- The clean ChatGPT conversation successfully reconstructed: merged baseline, current handoff/work state, authority hierarchy, Security Invariants, implementation truth, missing features, current gate, historical provenance, and Git snapshot.
- Next gate: `CONTINUITY-001 FINAL ARCHITECT REVIEW / PR #3 MERGE GATE`

## CONTINUITY-001.3B — Cold-bootstrap pass finalization

- Branch: `governance/continuity-001`
- Recorded `CONTINUITY-001.3` PASS.
- Corrected B-010 path in `docs/authority/B_FREEZE_REGISTRY.md` from `B010_CONTACTS_AND_VERIFICATION.md` to `B010_CONTACTS_VERIFICATION.md`.
- Added handoff ZIP retention/performance policy to `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`.
- Synchronized `README.md` test evidence with current records (15/15 Rust, 35/35 Android instrumentation historical).
- Updated `CURRENT_STATE.json`, `CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, and `CURRENT_NEXT_DEVIN_TASK.md` to the final architect-review gate.

## CONTINUITY-001.4 — APK content / secret leakage release gate

- Branch: `governance/continuity-001`
- Added APK content / secret leakage release gate to `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`.
- Created `tools/security/validate_apk_contents.py` (Python 3 standard library only, no network) that:
  - reads an APK as a ZIP,
  - inventories members (dex, native libs, assets, manifest, resources),
  - detects forbidden repository/governance paths and names,
  - scans text-like members for obvious private-key / secret markers,
  - never prints discovered secret values.
- Integrated `validate_apk_contents.py` into `.github/workflows/ci.yml` to validate the debug and release APK artifacts after each build.
- Ran synthetic APK negative tests: all forbidden-path and secret-marker fixtures returned non-zero with safe output; benign fixture returned PASS.
- CI ran on PR #3: debug and release APK content validation PASS (details in FORTSCHRITT and DEVIN archive).
- Product source unchanged.
- PR #3 merged into `main` at `7320253f27a1eef32847b992f13292d77178c4db`.

## CONTINUITY-001 FINAL — PR #3 merge and main continuity finalization

- Merged `governance/continuity-001` into `main`.
- Final `main` HEAD at handoff generation: see `CURRENT_GIT_STATE.md` or `GIT_SNAPSHOT.txt`.
- PR #3 closed and merged.
- Synchronized `CURRENT_STATE.json`, `CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, `CURRENT_NEXT_DEVIN_TASK.md`, `CURRENT_IMPLEMENTATION_STATE.md`, `CURRENT_OPEN_WORK.md` to the merged `main` state.
- Final handoff generated on `main` and validated.
- CONTINUITY-001: ACCEPTED.
- Next gate: `FINAL NEW-CHAT HANDOFF ACCEPTANCE`.

## CONTINUITY-001.5 — Final main continuity state synchronization fix

- Branch: `main`
- Trigger: new-chat bootstrap of `ANOX_HANDOFF_2026-08-21_cc0ad020f6aa.zip` returned `BLOCKED` due to stale current-state information in `PROJECT_STATE.md` and `FORTSCHRITT.md` (pre-merge dates/HEADs/branch, unresolved runtime HEAD placeholder).
- Synchronized `PROJECT_STATE.md` and `FORTSCHRITT.md` current state to `main` after PR #3 merge.
- Updated `CURRENT_IMPLEMENTATION_STATE.md`, `CURRENT_OPEN_WORK.md`, `CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md` to reflect the accepted `main` state.
- Hardened `tools/continuity/validate_continuity.py` to detect stale current branch, unresolved placeholders in `PROJECT_STATE.md`/`FORTSCHRITT.md`, inconsistent `continuity_001_status`, and current-gate disagreement.
- Strengthened `tools/continuity/generate_handoff.py` to fail closed if any packaged file contains unresolved runtime HEAD/working-tree placeholders.
- Ran negative regression tests: all expected failures now detected.
- Product source unchanged.
- New final handoff generated and validated.
