# CURRENT HANDOFF — anoX Messenger V1

**Handoff version:** PROMPT-007 MERGED
**Date:** 2026-08-22

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

## Current repository state

- Repository: `https://github.com/anox-admin/ax-messenger.git`
- Branch: `main`
- Merged baseline HEAD: `d281df66a3471dfd6a9bab0bd899be701317afb4`
- Working tree: expected clean at handoff generation
- Open PR: `none` — PR #4 merged and closed
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`

## Implementation milestone

- B-025 repository synchronization merged to `main`.
- B-026 continuity governance merged to `main`.
- CONTINUITY-001.2A master parity restored.
- CONTINUITY-001.3A atomic handoff state consistency fix applied.
- CONTINUITY-001.3 cold new-chat bootstrap retest PASS.
- CONTINUITY-001.4 APK content / secret leakage release gate merged.
- CONTINUITY-001.5 final main continuity state synchronization fix applied.
- CONTINUITY-001: ACCEPTED.
- PROMPT-007 — B-002 Device Authentication client foundation (PR #4): MERGED into `main` at
  `d281df66a3471dfd6a9bab0bd899be701317afb4`.
- PROMPT-007B — independent security/architecture review: APPROVE, no merge-blocking findings.
- PROMPT-007C — dependency-tree empirically verified (BouncyCastle/Tink not resolved), merge
  gate finalized, PR #4 merged, continuity synchronized.

## Latest completed work

PROMPT-007C — B-002 Device Authentication foundation merge and continuity synchronization.

## Current open work

None. B-002 client foundation is merged. B-003 Account/License foundation is the next
architecture-authorized area but has not been started and is not authorized by this task.

## Current test baseline

- Rust crypto tests: 15/15 PASS
- Android debug build + APK content validation: PASS
- Android release compile + APK content validation: PASS
- Android connected instrumentation: historical 35/35 PASS (not re-run)
- GrapheneOS physical device: UNVERIFIED

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
- Android instrumentation for Device Auth real Keystore behaviour
- Physical StrongBox / TEE Device Auth key behaviour
- GrapheneOS physical-device Device Auth behaviour
- FCM/push runtime behavior
- Network messaging/sync at scale

## Current blockers

- GitHub free plan: branch protection and secret scanning unavailable.
- No product/security blockers.

## Next architecture gate

`B-003 ACCOUNT / LICENSE FOUNDATION — NOT STARTED, NOT AUTHORIZED`

## Next engineering task

B-002 client foundation is merged. The likely next architecture-authorized area is B-003
Account/License per `B_FREEZE_REGISTRY.md`, but implementation is NOT authorized by this task
and has not been started.

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