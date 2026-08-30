# CURRENT IMPLEMENTATION STATE

**Date:** 2026-08-30 (PRE-B027-M2B Project Memory / Progress Integrity V1)

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
- B-002 Device Authentication client foundation: MERGED into `main` at `d281df66a3471dfd6a9bab0bd899be701317afb4` (PR #4). Android Keystore P-256/ES256 key, hardware policy, RFC9449 DPoP proof creation and verification boundary, fail-closed terminal key loss. 69 JVM unit tests PASS. Independent security/architecture review: APPROVE, no merge-blocking findings. Its `AndroidKeystoreDeviceAuthKeyManagerTest` instrumentation suite ran on a local emulator.
- B-003 Account/License client domain/state foundation: MERGED into `main` at `e7ee54a713e08950c63cf2d61ec97931864b66bc` (PR #5). Includes identifiers, username/license validation, account/device/entitlement states, registration state machine, narrow `RegistrationApi` contract, persistent Device Auth binding store and registration session storage, `BinaryRegistrationStateCodec`, `DeviceAuthBindingStore.isArmed`, `RegistrationState.CommitArmed`, and legacy plaintext artifact cleanup. 161 JVM unit tests PASS; 62 Android instrumentation tests PASS on a local API-34 emulator. B-003 is MERGED FOUNDATION, not production complete.
- B-017-Lite CI / supply-chain security foundation: MERGED into `main` at `283c1a1fdda012aab51b0164b4b16636e870f3b5` (PR #2). Five GitHub CI gates PASS. Review findings ANOX-B017REV-001 through -007 CLOSED.
- PRE-B027-0R2 continuity reconciliation: MERGED into `main` at `3e127c7a80e9835ea5631e21c10f066401a884dc` (PR #3). All PRE-B027 findings are closed.
- Canonical Merge Lifecycle V1: MERGED into `main` at `9bbd4ea185e4149a9ac144d4f7b35d43f35f040f` (PR #4). `ANOX-CMLREV-001/003/004` and `ANOX-CMLR1REV-001` independently CLOSED; `ANOX-CMLR1REV-002`, `ANOX-CMLREV-002`, and `ANOX-CMLR2REV-001..003` implemented/remediated with automated verification. No final independent M1R3 Delta Review occurred. Final canonical `main` live validation PASS.
- Project Memory / Progress Integrity V1: implemented on `governance/project-memory-progress-integrity-v1`. Adds append-only `PROJECT_HISTORY_LEDGER.jsonl`, `PROJECT_MEMORY_SURFACE_INDEX.md`, FORTSCHRITT event markers, and `PROJECT_MEMORY_FRESHNESS` validation.

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
- B-017-Lite CI / supply-chain security foundation (validator, pinned Actions, Gradle wrapper checksum, Rust locked builds).
- Project Memory Integrity V1 tooling and surfaces.

## PARTIAL

- Release signing and artifact distribution — not configured.
- Physical Android/GrapheneOS runtime — unverified.
- Cloud-AI secret protection governance — added in PROMPT-009 and merged into `main` of the new canonical repository.

## MISSING

- B-027 AI Workforce / Work-Control Governance runtime (architecture frozen; implementation authorized at `9bbd4ea...` but runtime not yet built).
- Device Authentication (B-002) server side: token issuance/storage/revocation, device registry, shared production replay cache, entitlement enforcement. The client foundation is merged (see VERIFIED above).
- Account/license (B-003) server side: backend implementation of `RegistrationApi`, license generation, server HMAC lookup, DB-enforced one-active-device-per-account. The client domain/state foundation is merged (see VERIFIED above).
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
  emulator during PROMPT-008 — 62/62 — but that is not CI)
- Physical StrongBox/TEE Device Auth key behaviour (only proven on an emulator, not physical
  hardware)
- Production-grade abuse/privacy/infrastructure controls
