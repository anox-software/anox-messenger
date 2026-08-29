# CURRENT HANDOFF — anoX Messenger V1

**Handoff version:** B-017-Lite — CI / Supply-Chain Security Foundation
**Date:** 2026-08-29

---

## Project

anoX Messenger V1 — closed-source native Android/GrapheneOS messenger with vodozemac/Olm E2EE.

## Architecture authority

Authority precedence is canonical in `docs/authority/AUTHORITY_INDEX.md`.
New sessions must read that file first.

## Current repository state

- Canonical repository: `https://github.com/anox-software/anox-messenger`
- Canonical SSH remote: `git@github.com:anox-software/anox-messenger.git`
- Legacy provenance remote: `https://github.com/anox-admin/ax-messenger.git` (historical only)
- Current work branch: `security/b017-lite-supply-chain-foundation`
- Current baseline branch: `main`
- Current baseline HEAD: `043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff`
- Working tree: expected clean at handoff generation
- Open PR: none (B-017-Lite is not yet merged)
- Latest merge into `main`: PR #1 `9c3fb08c30b743274e2c0779937502bb30b313b0` — Governance: development security and GitHub remote safety hardening
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
- PROMPT-007C — merge gate verification, dependency-tree empirical confirmation, merge, and
  continuity synchronization.
- PROMPT-008 / PROMPT-008C / PROMPT-008D — B-003 Account/License client domain/state foundation,
  security review remediation, and final commit-uncertainty closure: MERGED into `main` at
  `e7ee54a713e08950c63cf2d61ec97931864b66bc` (PR #5). B-003 is MERGED FOUNDATION, not
  production complete.
- PROMPT-009 — Development Security Governance / Handoff Hardening: MERGED via new PR #1.
- PROMPT-010 — GitHub Remote Activity Safety Governance: MERGED via new PR #1.
- REMOTE-MIGRATION-SYNC-001 — New GitHub main reconciliation: `main` at
  `043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff`.
- B-017-Lite — CI / Supply-Chain Security Foundation: implemented on
  `security/b017-lite-supply-chain-foundation` and awaiting independent security review.

## Latest completed work

B-017-Lite — CI / Supply-Chain Security Foundation:

- Hardened `.github/workflows/ci.yml` with least-privilege `GITHUB_TOKEN` permissions,
  immutable action SHA pinning, bounded concurrency, and fail-closed shell semantics.
- Added `distributionSha256Sum` to `gradle/wrapper/gradle-wrapper.properties` with checksum
  from `services.gradle.org`.
- Confirmed Gradle dependencies are pinned and no `+`, `latest.release`, `latest.integration`,
  `SNAPSHOT`, `mavenLocal()`, or insecure repositories are used.
- Switched Rust CI to `cargo test --locked` and added `cargo generate-lockfile --locked` freshness
  check.
- Created `tools/security/b017_lite_policy_validator.py` with deterministic, local, fail-closed
  supply-chain/CI checks and `tools/security/test_b017_lite_policy_validator.py` with PASS/FAIL
  test cases.
- Created `docs/reports/B017_LITE_CI_SUPPLY_CHAIN_SECURITY.md` documenting threat, controls,
  residual risks, and deferred hardening.

No product code, cryptographic behavior, or architecture changed.

## Current open work

`B-017-Lite` — CI / Supply-Chain Security Foundation: implemented, awaiting independent security
review.

## Current test baseline

- Rust crypto tests: 15/15 PASS
- Android JVM unit tests: 161/161 PASS
- Android debug build + APK content validation: PASS
- Android release compile + APK content validation: PASS
- Android connected instrumentation: 62/62 PASS on a local API-34 emulator
- GrapheneOS physical device: UNVERIFIED
- B-017-Lite policy validator: PASS
- B-017-Lite policy validator unit tests: 9/9 PASS

## Historical provenance

- Current authority: `docs/authority/AUTHORITY_INDEX.md`.
- B-025 master handoff provenance archived under `docs/history/B025/`.
- `docs/history/B025/README.md` and `docs/history/B025/SOURCE_INDEX.md` map every imported historical source.
- `docs/history/B025/REPOSITORY_PROVENANCE/GIT_BUNDLE_STATUS.md` documents why the full-history Git bundle is not automatically replicated.
- Historical material is non-authoritative; it must not override `docs/authority/` or `docs/continuity/`.

## Known unverified items

- GrapheneOS physical-device testing
- Connected Android instrumentation in CI (no emulator; run and passing locally)
- Physical StrongBox / TEE Device Auth key behaviour
- FCM/push runtime behavior
- Network messaging/sync at scale

## Current blockers

- GitHub free plan: branch protection and secret scanning unavailable.
- No product/security blockers.
- No governance blockers.

## Next architecture gate

`B-017-LITE INDEPENDENT SECURITY REVIEW`

## Next engineering task

B-017-Lite is implemented and awaits independent security review. No B-004/B-005/B-027
implementation is authorized until B-017-Lite is reviewed and merged.

## Do-not-touch foundation

- `crypto/rust/` source (identity, session, serialization, lib, error)
- `CryptoNative.kt`, `CryptoBridge.kt`
- vodozemac 0.10.0
- Typed JNI identity/session handle architecture
- `K_STATE` / AES-256-GCM protected local state
- `[ANOX][0x01]` envelope
- Android Keystore state-key wrapping
- AGP 8.13.2, KGP 2.4.10, Compose 2.4.10, Gradle 9.3.1, NDK 26.2.11394342
- `arm64-v8a` and `x86_64` native `.so` files

## Historical material rule

- `docs/history/` and `docs/history/B025/` are provenance only.
- Never reactivate superseded RAW rules.
- B-025 and B-026 are current governance.
