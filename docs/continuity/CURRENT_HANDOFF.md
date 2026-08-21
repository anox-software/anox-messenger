# CURRENT HANDOFF — anoX Messenger V1

**Handoff version:** CONTINUITY-001.3A
**Date:** 2026-08-20

---

## Project

anoX Messenger V1 — closed-source native Android/GrapheneOS messenger with vodozemac/Olm E2EE.

## Architecture authority

Highest to lowest:

1. `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
2. `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
3. `docs/authority/B_FREEZE_REGISTRY.md`
4. `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md`
5. `docs/authority/B025/TRACK_B/B001_MASTER_COMPLETENESS.md` … `B025_NEW_CHAT_HANDOFF.md`

## Merged baseline

- Repository: `https://github.com/anox-admin/ax-messenger.git`
- Baseline branch: `main`
- Baseline HEAD: `648b70391085ea5252cc9f88375064420f1b78d9`
- Last merge: PR #2 `75c11c823ec68cea576912b4095fa7a26ed33a33` (B-025 sync + Android backup hardening)
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`

## Current handoff / work state

- Current handoff branch: `governance/continuity-001`
- Current handoff HEAD: resolve from `CURRENT_STATE.json` or `GIT_SNAPSHOT.txt`
- Working tree: expected clean at handoff generation
- Open PR: `#3` to `main`
- Foundation baseline remains `v1-foundation-baseline`

## Current implementation milestone

- B-025 repository synchronization merged to `main`.
- B-026 continuity governance implemented on `governance/continuity-001`.
- CONTINUITY-001.2A master parity restored.
- CONTINUITY-001.3A atomic handoff state consistency fix in progress.

## Last completed task

CONTINUITY-001.2A — Historical provenance ingestion and master parity correction.

## Last Devin output

CONTINUITY-001.2A structured report (master parity restored, PR #3 open, PROMPT-007 not started).

## Current test baseline

- Rust crypto tests: 15/15 PASS
- Android connected instrumentation: 35/35 PASS (historical, not re-run recently)
- Android debug/release CI: PASS on `main`
- GrapheneOS physical device: UNVERIFIED

## Current CI

GitHub Actions `anoX V1 CI`: Rust, Android debug build, Android release compile smoke — PASS on latest `governance/continuity-001` run.

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

`CONTINUITY-001.3 — COLD NEW-CHAT BOOTSTRAP RETEST`

## Next engineering task

PROMPT-007 / Device Authentication Foundation is not the next task until the cold bootstrap retest passes and an architect explicitly authorizes it.

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

- `docs/history/` and `docs/history/B025/` are provenance only.
- Never reactivate superseded RAW rules.
- B-025 and B-026 are current governance.