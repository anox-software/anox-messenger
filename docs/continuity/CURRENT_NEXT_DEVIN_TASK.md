# CURRENT NEXT DEVIN TASK

**Status:** PENDING ARCHITECT REVIEW
**Task ID:** PROMPT-007
**Date:** 2026-08-21

---

## Purpose

PROMPT-007 implemented the B-002 Device Authentication client foundation on
`feature/b002-device-auth-foundation`. PR #4 is open and awaits architect review before any
merge decision.

## Preconditions satisfied

- CONTINUITY-001 ACCEPTED; `main` baseline `33440823f3d2a785202ca1828e4bf9c71b175008`.
- 69 JVM unit tests PASS, 0 failures, 0 skipped (CI run `32514140072`).
- Rust 15/15, Android debug build, release compile smoke and both APK content gates PASS.
- No product-source, crypto, JNI or build-tooling change.

## Architecture references

- `docs/authority/B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md`
- `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/reports/PROMPT_007_DEVICE_AUTH_FOUNDATION.md`

## Do-not-touch

- `crypto/rust/`
- `CryptoNative.kt` / `CryptoBridge.kt`
- `android/src/main/AndroidManifest.xml`
- `build.gradle.kts`, `gradle-wrapper.properties`
- native `.so` files

## Current gate

`PROMPT-007 ARCHITECT REVIEW / PR #4 MERGE GATE`

## Known open items for review

- `DeviceAuthBindingStore` has only an in-memory implementation; persistence is required
  before real device binding.
- Android instrumentation tests for the real Keystore are NOT RUN in CI (no emulator).
- Physical StrongBox/TEE and GrapheneOS device behaviour remain UNVERIFIED.
- Production token issuance/storage and the shared replay cache remain B-004 work.

## Note

No further B-002 backend work, B-003 registration or messaging work is authorized until an
architect reviews PR #4.
