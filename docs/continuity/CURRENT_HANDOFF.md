# CURRENT HANDOFF — anoX Messenger V1

**Handoff version:** CONTINUITY-001  
**Date:** 2026-08-20

---

## Project

anoX Messenger V1 — closed-source native Android/GrapheneOS messenger with vodozemac/Olm E2EE.

## Architecture authority

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/SECURITY_INVARIANTS_V1_1.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/authority/B025/B_FREEZE_REGISTRY.md`
- `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md`
- `docs/authority/B025/IMPLEMENTATION_GAP_MATRIX.md`

## Current main

- Repository: `https://github.com/anox-admin/ax-messenger.git`
- Branch: `main`
- Current HEAD: `648b70391085ea5252cc9f88375064420f1b78d9`
- Last merge: PR #2 `75c11c823ec68cea576912b4095fa7a26ed33a33` (B-025 sync + Android backup hardening)
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`

## Current implementation milestone

B-025 repository synchronization merged; B-026 continuity governance added on branch `governance/continuity-001` (not yet merged).

## Last completed task

STEP-4A — PR #2 merge and post-merge verification.

## Last Devin output

STEP-4A structured report (PR #2 merged, main green, PROMPT-007 not started).

## Current test baseline

- Rust crypto tests: 15/15 PASS (historical and re-run)
- Android connected instrumentation: 35/35 PASS (historical, not re-run recently)
- Android debug/release CI: PASS on `main` runs `32376668391` and `32377964672`
- GrapheneOS physical device: UNVERIFIED

## Current CI

GitHub Actions `anoX V1 CI`: Rust, Android debug build, Android release compile smoke — PASS on latest `main`.

## Historical provenance

- Current authority: `docs/authority/AUTHORITY_INDEX.md`.
- B-025 master handoff provenance archived under `docs/history/B025/`.
- `docs/history/B025/README.md` and `docs/history/B025/SOURCE_INDEX.md` map every imported historical source.
- `docs/history/B025/REPOSITORY_PROVENANCE/GIT_BUNDLE_STATUS.md` documents why the full-history Git bundle is not automatically replicated.
- Historical material is non-authoritative; it must not override `docs/authority/` or `docs/continuity/`.

## Known unverified items

- GrapheneOS physical-device testing
- Local Android release build tooling
- Connected Android instrumentation in CI (no emulator)
- FCM/push runtime behavior
- Network messaging/sync at scale

## Current blockers

- GitHub free plan: branch protection and secret scanning unavailable.
- No product/security blockers.

## Next architecture gate

`CONTINUITY-001 ARCHITECT REVIEW` (this task).

## Next engineering task

To be authorized after architect review. PROMPT-007 / Device Authentication Foundation is not automatically next.

## Do-not-touch foundation

- `crypto/rust/` source (identity, session, serialization, lib, error)
- `CryptoNative.kt`, `CryptoBridge.kt`
- vodozemac 0.10.0
- JNI typed-handle architecture
- `K_STATE` / AES-256-GCM protected local state
- `[ANOX][0x01]` envelope
- Android Keystore state-key wrapping
- AGP 8.13.2, KGP 2.4.10, Compose 2.4.10, Gradle 9.3.1, NDK 26.2.11394342
- `arm64-v8a` and `x86_64` native `.so` files

## Historical material rule

- `docs/history/` and `docs/history/raw1.1/` are provenance only.
- Never reactivate superseded RAW rules.
- B-025 and B-026 are current governance.
