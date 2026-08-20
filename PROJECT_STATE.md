# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-08-20
**Architecture:** Track B B-001…B-023 frozen/defined, B-024 PASS, B-025 complete.
**Functional implementation:** approximately 27%.

## Repository truth

- Branch: `main`
- HEAD: `c076528e26e5e3ed05b4d0aeed794894f1f78b5e`
- Remote main in uploaded repo: same HEAD.
- GIT-001: FULL PASS in repo documentation.
- TOOLCHAIN-001: PR #1 merged; main CI run `32344459447` recorded PASS for Rust/debug/release compile smoke.
- Current extracted upload showed only executable-mode changes on `gradlew` and two `.so` files; their content hashes equal HEAD. Use clean Git snapshot as implementation baseline.

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

## Not implemented

- B-002 Device Authentication.
- B-003 production account/license registration.
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
- Connected Android instrumentation: NOT RUN in CI (no emulator); historical 35/35 remains accepted.
- PROMPT-007 was not executed.
