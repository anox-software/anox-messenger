# CURRENT NEXT DEVIN TASK

**Status:** PENDING ARCHITECT REVIEW  
**Task ID:** CONTINUITY-001  
**Date:** 2026-08-20

---

## Purpose

Establish the repository-based continuity and handoff system defined by B-026. This is the first task using the new governance.

## Preconditions

- B-025 repository synchronization is merged.
- `docs/continuity/` exists.
- `tools/continuity/generate_handoff.py` and `tools/continuity/validate_continuity.py` exist.

## Architecture references

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`

## Do-not-touch

- `crypto/rust/`
- `CryptoNative.kt` / `CryptoBridge.kt`
- `android/src/main/AndroidManifest.xml` (except `dataExtractionRules` already merged)
- `build.gradle.kts`, `gradle-wrapper.properties`
- native `.so` files
- all product source

## Expected tests

- `python3 tools/continuity/validate_continuity.py` → returns 0
- `python3 tools/continuity/generate_handoff.py` → creates a clean handoff ZIP with manifest and SHA-256
- `git diff --check` → clean
- Rust `cargo test` if modified code (no product source changes expected)

## Current gate

`CONTINUITY-001 ARCHITECT REVIEW`

## Note

PROMPT-007 / Device Authentication Foundation is not the next task until architect handoff explicitly authorizes it.
