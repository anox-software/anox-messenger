# CURRENT HANDOFF — anoX Messenger V1

**Handoff version:** PRE-B027-M1R3 — Canonical merge lifecycle M1R3 schema-downgrade remediation
**Date:** 2026-08-30

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
- Canonical branch: `main`
- Delivery branch: `governance/canonical-merge-lifecycle-v1`
- Current work branch: `governance/canonical-merge-lifecycle-v1`
- Current baseline branch: `main`
- Current baseline HEAD: `3e127c7a80e9835ea5631e21c10f066401a884dc`
- Described HEAD: `cb1bc3ddfe3a469684ea0c98e7d39412f92f7ec0`
- Working tree: expected clean at handoff generation
- Pre-merge gate: `CANONICAL MERGE LIFECYCLE M1R3 INDEPENDENT DELTA RETEST`
- Post-merge gate: `B-027 IMPLEMENTATION AUTHORIZED`
- Open PR: none (PRE-B027-M1R is local and not yet pushed)
- Latest merge into `main`: PR #3 `3e127c7a80e9835ea5631e21c10f066401a884dc` — PRE-B027-0R2 continuity reconciliation
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
- PROMPT-007 — B-002 Device Authentication client foundation (PR #4): MERGED into `main` at `d281df66a3471dfd6a9bab0bd899be701317afb4`.
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
- B-017-Lite — CI / Supply-Chain Security Foundation (PR #2): MERGED into `main` at
  `283c1a1fdda012aab51b0164b4b16636e870f3b5`; all five CI gates PASS; ANOX-B017REV-001 through -007 CLOSED.
- PRE-B027-0 — B-027 AI Workforce / Work-Control Governance architecture freeze and continuity
  head-semantic fix implemented on `governance/pre-b027-continuity-reconciliation`; no B-027
  runtime files created yet; awaiting independent review.
- PRE-B027-0R — Targeted remediation of the PRE-B027-0 focused independent review findings
  (ANOX-PREB027REV-001 through -010) on `governance/pre-b027-continuity-reconciliation`;
  Findings 002 through 010 closed locally; Finding 001 partially closed; awaiting
  independent Delta Retest.
- PRE-B027-0R2 — Merge-commit payload visibility fix (ANOX-PREB027RREV-001) implemented on
  `governance/pre-b027-continuity-reconciliation`; the validator now uses a merge-aware
  `git log -m --name-only --no-renames` history scan and includes regression tests for
  evil-merge, merge-then-revert, clean metadata merge, substantive branch merge, and
  merge-resolution-into-allowlist scenarios. All findings are now remediated locally; awaiting
  the final `PRE-B027-0R2 INDEPENDENT DELTA RETEST` for closure.

## Latest completed work

PRE-B027-0 — Continuity semantics / baseline reconciliation:

- Introduced three distinct HEAD concepts:
  - `described_head` — the substantive Git commit the tracked metadata describes.
  - `live_head` — the runtime `git rev-parse HEAD`, never stored as authoritative.
  - `handoff_snapshot_head` — the external Handoff ZIP manifest value.
- Replaced the self-referential `baseline_head == live HEAD` invariant with a metadata-only
  advancement check between `described_head` and `live_head`.
- Updated `validate_continuity.py` and `test_handoff_and_validator.py` to enforce the new semantics.
- Added focused negative tests for product code, CI, authority, tool, unknown, non-ancestor,
  malformed, and unresolved `described_head` cases.
- Created `docs/reports/PRE_B027_WORKFORCE_ARCHITECTURE_FREEZE.md` capturing the frozen B-027
  purpose, authority hierarchy, 19 roles, security principles, cost/review rule, state design,
  evidence model, data-egress model, priority model, handoff requirement, implementation order,
  and HEAD semantics.
- Added B-027 to `docs/authority/B_FREEZE_REGISTRY.md`.

PRE-B027-0R — Review finding remediation:

- Fixed rename-into-allowlist bypass by inspecting every commit in the metadata-only range with
  `git log --name-only --no-renames`.
- Restored archive-mode required-key enforcement with legacy `baseline_head` compatibility.
- Removed broad `docs/history/**` and `docs/continuity/HISTORICAL_HANDOFFS/**` prefix trust.
- Added non-self-referential baseline ancestry validation.
- Completed the PRE-B027 freeze report with Finding Security, Role≠Model, Gate Resolver, and
  Cold Recovery requirements.
- Replaced the duplicated authority precedence list with a canonical reference.
- Updated `docs/authority/AUTHORITY_INDEX.md` freeze registry scope.
- Aligned generator and validator `described_head` / `baseline_head` precedence.
- Enforced described_head declaration in current continuity surfaces.
- Added adversarial regression tests for all ten findings.

## Current open work

`PRE-B027-M1R3` — Canonical merge lifecycle M1R3 schema-downgrade remediation on `governance/canonical-merge-lifecycle-v1`;
implemented locally and awaiting `CANONICAL MERGE LIFECYCLE M1R3 INDEPENDENT DELTA RETEST`.

## Current test baseline

- B-017-Lite CI gates: 5/5 PASS
- Rust crypto tests: 15/15 PASS
- Android JVM unit tests: 161/161 PASS
- Android debug build + APK content validation: PASS
- Android release compile + APK content validation: PASS
- Android connected instrumentation: 62/62 PASS on a local API-34 emulator
- GrapheneOS physical device: UNVERIFIED
- B-017-Lite policy validator: PASS
- B-017-Lite policy validator unit tests: 35/35 PASS
- Continuity unit tests: 132/132 PASS

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

- `ANOX-CMLR1REV-001` is independently CLOSED.
- `ANOX-CMLR2REV-001`, `ANOX-CMLR2REV-002`, and `ANOX-CMLR2REV-003` are remediated locally and are `READY FOR RETEST`.
  Closure is reserved for the independent M1R3 Delta Reviewer.
- `PRE-B027-M2 PROJECT MEMORY / PROGRESS INTEGRITY` is BLOCKED until M1R3
  independent Delta Retest PASS, controlled Human Push, PR, CI PASS, Human Merge,
  and final canonical main live validation.
- GitHub free plan: branch protection and secret scanning unavailable.
- No product/security blockers.
- No governance blockers.
- No PRE-B027 architecture blockers; the architecture is frozen and the M1R3
  remediation is awaiting independent Delta Retest.

## Next architecture gate

`CANONICAL MERGE LIFECYCLE M1R3 INDEPENDENT DELTA RETEST`

## Next engineering task

After the independent review and controlled human merge, the authorized next gate is `B-027 IMPLEMENTATION AUTHORIZED`.
No B-027 Workforce runtime files are implemented until that gate is explicitly authorized.

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
- B-025, B-026, and the B-027 PRE-FROZEN report are current governance.
