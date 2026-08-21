# CURRENT NEXT DEVIN TASK

**Status:** PENDING ARCHITECT REVIEW  
**Task ID:** CONTINUITY-001.3A
**Date:** 2026-08-20

---

## Purpose

Fix the atomic handoff state consistency defect detected by the cold new-chat bootstrap. Synchronize recorded continuity state with the live Git/work state from which any handoff is generated.

## Preconditions

- B-025 repository synchronization is merged.
- `docs/continuity/` exists.
- `tools/continuity/generate_handoff.py` and `tools/continuity/validate_continuity.py` exist.
- `CONTINUITY-001.2A` has reached PASS.

## Architecture references

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`

## Do-not-touch

- `crypto/rust/`
- `CryptoNative.kt` / `CryptoBridge.kt`
- `android/src/main/AndroidManifest.xml`
- `build.gradle.kts`, `gradle-wrapper.properties`
- native `.so` files
- all product source

## Expected tests

- `python3 tools/continuity/validate_continuity.py` → returns 0
- `python3 tools/continuity/generate_handoff.py` → creates a clean handoff ZIP with manifest and SHA-256
- `git diff --check` → clean
- Negative regression tests for stale HEAD, branch, security-invariants path, next gate, dirty tree
- `ZipFile.testzip()`, internal SHA-256 manifest, exclusion/secret scan → PASS
- 20/20 reconstruction questions remain ANSWERABLE

## Current gate

`CONTINUITY-001.3 — COLD NEW-CHAT BOOTSTRAP RETEST`

## Note

PROMPT-007 / Device Authentication Foundation is not the next task until the cold bootstrap retest passes and an architect explicitly authorizes it.