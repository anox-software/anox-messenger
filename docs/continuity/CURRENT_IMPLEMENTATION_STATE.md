# CURRENT IMPLEMENTATION STATE

**Date:** 2026-08-22 (PROMPT-008)

---

## VERIFIED

- Rust crypto crate (`anox_crypto`): `cargo test` 15/15 PASS.
- Android project builds in CI (debug and release compile smoke).
- Git/GitHub baseline connected; `v1-foundation-baseline` preserved.
- TOOLCHAIN-001 merged; AGP 8.13.2 + KGP 2.4.10 + Gradle 9.3.1 green.
- STEP-3B / 3B.1 merged; B-025 authority in `docs/authority/B025/`.
- Android backup/D2D hardening: `allowBackup="false"` + full `dataExtractionRules`.
- B-026 continuity governance files merged to `main` in `docs/continuity/` and `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`.
- B-026 Android APK content and secret-leakage release gate; `tools/security/validate_apk_contents.py` integrated into CI.
- B-002 Device Authentication client foundation: MERGED into `main` at `d281df66a3471dfd6a9bab0bd899be701317afb4` (PR #4). Android Keystore P-256/ES256 key, hardware policy, RFC9449 DPoP proof creation and verification boundary, fail-closed terminal key loss. 69 JVM unit tests PASS (independently reconfirmed locally and in CI). Independent security/architecture review: APPROVE, no merge-blocking findings. Dependency graph empirically confirmed via `./gradlew :android:dependencies`: BouncyCastle/Tink not resolved. Its `AndroidKeystoreDeviceAuthKeyManagerTest` instrumentation suite (10 tests) was executed for the first time during PROMPT-008 on a local emulator: PASS.
- B-003 Account/License client domain/state foundation on branch `feature/b003-account-license-foundation` (PROMPT-008, PR being opened, not merged): identifiers, username/license validation, account/device/entitlement states, registration state machine, narrow `RegistrationApi` contract, persistent Device Auth binding store and registration session storage. 146 JVM unit tests PASS; 58 Android instrumentation tests PASS on a local emulator.

## IMPLEMENTED

- Rust `anox_crypto` with vodozemac 0.10.0 and AES-GCM protected state.
- Typed JNI identity/session handle architecture.
- Android Keystore-wrapped random state key.
- Versioned protected state envelope `[ANOX][0x01][...]`.
- Atomic file persistence and state lifecycle statuses.
- Minimal Android/Compose app shell.
- CI workflow with Rust and Android build jobs.
- Git governance and B-025 authority area.
- Continuity tools: `tools/continuity/generate_handoff.py` and `tools/continuity/validate_continuity.py`.

## PARTIAL

- Release signing and artifact distribution — not configured.
- Physical Android/GrapheneOS runtime — unverified.

## MISSING

- Device Authentication (B-002) server side: token issuance/storage/revocation, device
  registry, shared production replay cache, entitlement enforcement. The client foundation is
  merged (see VERIFIED above).
- Account/license (B-003) server side: backend implementation of `RegistrationApi`, license
  generation, server HMAC lookup, DB-enforced one-active-device-per-account. The client
  domain/state foundation exists in review (see VERIFIED above).
- Backend service (B-004)
- Database/RLS (B-005)
- Server key distribution (B-006)
- `/v1` API (B-007)
- Network messaging/sync (B-008)
- Local messenger DB (B-009)
- Contacts/SAS (B-010)
- Push/offline (B-011)
- Attachments (B-012)
- Server lifecycle (B-013)
- Privacy/retention workers (B-014)
- Abuse controls (B-015)
- Production infrastructure (B-016)
- Hardened CI/supply chain (B-017)
- Release signing/updates (B-018)
- Operations/IR (B-019)
- Full product UX (B-020)
- Security test matrix (B-021)
- Independent audit (B-022)
- Release DoD (B-023)

## UNVERIFIED

- GrapheneOS physical-device behavior
- D2D transfer in practice
- Connected Android instrumentation in CI (no emulator in CI; run and passing on a local
  emulator during PROMPT-008 — 58/58 — but that is not CI)
- Physical StrongBox/TEE Device Auth key behaviour (only proven on an emulator, not physical
  hardware)
- Production-grade abuse/privacy/infrastructure controls
