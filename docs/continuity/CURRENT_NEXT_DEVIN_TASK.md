# CURRENT NEXT DEVIN TASK

**Status:** PENDING ARCHITECT REVIEW
**Task ID:** PROMPT-008
**Date:** 2026-08-22

---

## Purpose

PROMPT-008 implemented the B-003 Account/License client domain/state foundation on
`feature/b003-account-license-foundation`. PR `#5` is open against `main` and awaits
architect review before any merge decision.

## Preconditions satisfied

- CONTINUITY-001 ACCEPTED; PROMPT-007 (B-002) merged; `main` baseline
  `0785b6001f816f5a6520951dd9a8c5a4af9af4c2`.
- 146 JVM unit tests PASS, 0 failures, 0 errors (77 new B-003 tests + 69 pre-existing B-002).
- 58 Android instrumentation tests PASS, 0 failures, on a local emulator (API 34).
- Rust 15/15, Android debug/release build, and both APK content gates PASS.
- No product-source, crypto, JNI or build-tooling change.

## Architecture references

- `docs/authority/B_FREEZE_REGISTRY.md`
- `docs/authority/B025/TRACK_B/B003_ACCOUNT_LICENSE.md`
- `docs/authority/B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md`
- `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/reports/PROMPT_008_B003_ACCOUNT_LICENSE_FOUNDATION.md`

## Do-not-touch

- `crypto/rust/`
- `CryptoNative.kt` / `CryptoBridge.kt` (called through its existing public API only)
- `android/src/main/AndroidManifest.xml`
- `build.gradle.kts`, `gradle-wrapper.properties`
- native `.so` files
- the B-002 Device Auth security model

## Current gate

`PROMPT-008 ARCHITECT REVIEW / PR MERGE GATE`

## Known open items for review

- `LicenseCode`'s structural validator assumes a placeholder uppercase-alphanumeric charset
  pending the exact "unambiguous character" alphabet definition (not specified by current
  authority).
- One-active-device-per-account is representable but not enforced (DB enforcement is B-005).
- `RegistrationApi` has no real implementation; threading/network model is a future B-004
  decision.
- Physical StrongBox/TEE and GrapheneOS device behaviour remain UNVERIFIED (emulator only).

## Note

No B-004 backend work, B-005 database/RLS work, or further B-003 work beyond this foundation is
authorized until an architect reviews the PROMPT-008 PR.
