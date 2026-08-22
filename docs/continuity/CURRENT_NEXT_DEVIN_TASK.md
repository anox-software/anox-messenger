# CURRENT NEXT DEVIN TASK

**Status:** NOT STARTED, NOT AUTHORIZED
**Task ID:** none active
**Date:** 2026-08-22

---

## Purpose

PROMPT-007 (B-002 Device Authentication client foundation) was implemented, independently
reviewed (PROMPT-007B: `APPROVE — READY FOR PROMPT-007 MERGE GATE`), verified, and merged into
`main` (PROMPT-007C) at `d281df66a3471dfd6a9bab0bd899be701317afb4` via PR #4.

No new task is currently authorized or in progress.

## Completed

- CONTINUITY-001 ACCEPTED.
- PROMPT-007 — B-002 Device Authentication client foundation: MERGED.
- PROMPT-007B — independent security/architecture review: APPROVE, no merge-blocking findings.
- PROMPT-007C — merge gate verification, empirical dependency-tree confirmation (BouncyCastle/
  Tink not resolved), PR #4 merged, continuity synchronized.

## Architecture references

- `docs/authority/B_FREEZE_REGISTRY.md`
- `docs/authority/B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md`
- `docs/authority/B025/TRACK_B/B003_ACCOUNT_LICENSE.md`
- `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/reports/PROMPT_007_DEVICE_AUTH_FOUNDATION.md`

## Do-not-touch (still applies to any future task)

- `crypto/rust/`
- `CryptoNative.kt` / `CryptoBridge.kt`
- `android/src/main/AndroidManifest.xml`
- `build.gradle.kts`, `gradle-wrapper.properties`
- native `.so` files

## Current gate

`B-003 ACCOUNT / LICENSE FOUNDATION — NOT STARTED, NOT AUTHORIZED`

Per `docs/authority/B_FREEZE_REGISTRY.md`, B-003 (Account + License, FROZEN v1.4) is the next
architecture-frozen specification after B-002 in Track B sequence. Recording this as the likely
next gate is informational only; implementation is NOT authorized until an architect explicitly
starts it.

## Known open items carried forward

- `DeviceAuthBindingStore` has only an in-memory implementation; persistence is required
  before real device binding (future B-003/B-004 integration).
- Android instrumentation tests for the real Keystore are NOT RUN (no emulator/device in CI or
  in any review environment to date).
- Physical StrongBox/TEE and GrapheneOS device behaviour remain UNVERIFIED.
- Production token issuance/storage and the shared replay cache remain B-004 work.

## Note

No B-002 backend work, B-003 registration, or messaging work is authorized by this record. Any
future task must explicitly confirm its own authorization before implementation begins.
