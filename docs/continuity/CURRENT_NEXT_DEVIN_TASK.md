# CURRENT NEXT DEVIN TASK

**Status:** IN PROGRESS
**Task ID:** CONTINUITY-001.4
**Date:** 2026-08-21

---

## Purpose

Establish the permanent APK content / secret leakage release gate. Add `tools/security/validate_apk_contents.py`, integrate it into CI, and ensure repository/governance material and obvious secrets cannot be accidentally shipped in the Android APK.

## Preconditions

- B-025 repository synchronization is merged.
- B-026 continuity governance is in place.
- `tools/continuity/validate_continuity.py` and `tools/continuity/generate_handoff.py` exist.

## Architecture references

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/authority/B017_CICD_SUPPLY_CHAIN.md`
- `docs/authority/B018_RELEASE_SIGNING_UPDATES.md`
- `docs/authority/B023_RELEASE_DOD.md`

## Do-not-touch

- `crypto/rust/`
- `CryptoNative.kt` / `CryptoBridge.kt`
- `android/src/main/AndroidManifest.xml`
- `build.gradle.kts`, `gradle-wrapper.properties`
- native `.so` files
- all product source

## Expected tests

- `python3 tools/continuity/validate_continuity.py` → returns 0
- `python3 tools/security/validate_apk_contents.py <debug-apk>` → returns 0 on real CI artifact
- `python3 tools/security/validate_apk_contents.py <release-apk>` → returns 0 on real CI artifact, or `NOT RUN` if no artifact
- synthetic APK negative tests → non-zero for forbidden paths and secret markers
- `git diff --check` → clean
- PR #3 CI passes

## Current gate

`CONTINUITY-001.4 — APK content / secret leakage release gate`

## Next gate

`CONTINUITY-001 FINAL ARCHITECT REVIEW / PR #3 MERGE GATE`

## Note

- PROMPT-007 / Device Authentication Foundation is not the next task until this branch is merged and an architect explicitly authorizes it.
- A handoff ZIP should only be generated if a chat handoff is actually requested or an explicit milestone is reached.