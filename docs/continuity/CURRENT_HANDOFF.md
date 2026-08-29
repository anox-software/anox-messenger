# CURRENT HANDOFF — anoX Messenger V1

**Handoff version:** PROMPT-010R1 — GOVERNANCE REVIEW FINDING REMEDIATION
**Date:** 2026-08-28

---

## Project

anoX Messenger V1 — closed-source native Android/GrapheneOS messenger with vodozemac/Olm E2EE.

## Architecture authority

Authority precedence is canonical in `docs/authority/AUTHORITY_INDEX.md`.
New sessions must read that file first.

## Current repository state

- Repository: `https://github.com/anox-software/anox-messenger` (SSH: `git@github.com:anox-software/anox-messenger.git`)
- Legacy provenance remote: `https://github.com/anox-admin/ax-messenger.git` (historical only)
- Current work branch: `main`
- Current baseline branch: `main`
- Current baseline HEAD: `9c3fb08c30b743274e2c0779937502bb30b313b0`
- Working tree: expected clean at handoff generation
- Open PR: none (governance PR #1 merged)
- Latest merge into `main`: PR #1 (`anox-software/anox-messenger#1`) — Governance: development security and GitHub remote safety hardening; merge commit `9c3fb08c30b743274e2c0779937502bb30b313b0`
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
- Post-PROMPT-008 main continuity synchronization: `881c85ec726d8a32eb84b00955b6b9db7912fe1e`.

## Latest completed work

PROMPT-009R2 — Governance Validator Final Hardening: closed `ANOX-GOVREV-009R-001`,
`ANOX-GOVREV-009R-002`, and `ANOX-GOVREV-009R-004`.

PROMPT-009R3 — Continuity Bookkeeping Closure: recorded `PROMPT-009R2` in
`DEVIN_PROMPT_OUTPUT_ARCHIV.md` and synchronized current-state surfaces.

PROMPT-009R4 — Final Continuity Closure: amended the `PROMPT-009R2` archive entry with the
missing `ANOX-GOVREV-009R-005` discovery and `REMOTE_SYNC_STATUS` evidence, recorded
`PROMPT-009R3`, and replaced the recursive "last Devin task archived" checklist rule with a
finite, auditable distinction between substantive tasks and continuity-sync runs. The independent
R4 retest CLOSED `ANOX-GOVREV-009R-005` and `ANOX-GOVREV-009R-006`.

PROMPT-010 — GitHub Remote Activity Safety Governance: introduced
`docs/authority/GITHUB_REMOTE_ACTIVITY_SAFETY.md`, added it to the authority index, updated
`DEVELOPMENT_SECURITY_WORKFLOW_V1.md`, `CURRENT_CHAT_BOOTSTRAP_PROMPT.md`, `HANDOFF_WORKFLOW.md`,
and current-state surfaces. Hard invariant: `NO RAPID REPETITIVE REMOTE AUTOMATION`.

PROMPT-010R1 — Governance review finding remediation: corrected the duplicate numbering in
`AUTHORITY_INDEX.md` and added the `AI remote-write authority assumed? → NO` quick-reference row
to `DEVELOPMENT_SECURITY_WORKFLOW_V1.md`.

REMOTE-MIGRATION-SYNC-001 — Controlled migration to `anox-software/anox-messenger`: repository
re-published under SSH origin, legacy `anox-admin/ax-messenger` demoted to historical provenance,
governance PR #1 merged into `main` at `9c3fb08c30b743274e2c0779937502bb30b313b0`, and all
current continuity surfaces reconciled to the new canonical remote/main state.

## Current open work

`ANOX-GOVREV-009R-005` — Continuity Bookkeeping Closure: `CLOSED` by independent R4 retest.

`ANOX-GOVREV-009R-006` — Recursive Bookkeeping Invariant: `CLOSED` by independent R4 retest.

`ANOX-GOVREV-010-001` — Duplicate authority-index numbering: `CLOSED` by independent retest.

`ANOX-GOVREV-010-002` — Missing remote-write quick-reference row: `CLOSED` by independent retest.

`PROMPT-010` — GitHub Remote Activity Safety Governance: `ACCEPTED` and merged via PR #1.

`REMOTE-MIGRATION-SYNC-001` — New GitHub main post-merge continuity reconciliation: `COMPLETE`.

## Current test baseline

- Rust crypto tests: 15/15 PASS
- Android JVM unit tests: 161/161 PASS
- Android debug build + APK content validation: PASS
- Android release compile + APK content validation: PASS
- Android connected instrumentation: 62/62 PASS on a local API-34 emulator
- GrapheneOS physical device: UNVERIFIED

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

- GitHub free plan: branch protection and secret scanning unavailable under the current private plan.
- No product/security blockers.
- No governance blockers.

## Next architecture gate

`B-017-LITE — CI / SUPPLY-CHAIN SECURITY FOUNDATION`

## Next engineering task

The governance branch has been merged into `main` of the new canonical repository.
`B-017-Lite — CI / Supply-Chain Security Foundation` is the next authorized engineering gate.
No B-004/B-005/B-027 implementation is authorized before B-017-Lite is scoped and accepted.

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
