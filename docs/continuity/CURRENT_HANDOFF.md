# CURRENT HANDOFF — anoX Messenger V1

**Handoff version:** PRE-B027-M2B — Project Memory / Progress Integrity V1
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
- Delivery branch: `governance/project-memory-progress-integrity-v1`
- Current work branch: `governance/project-memory-progress-integrity-v1`
- Current baseline branch: `main`
- Current baseline HEAD: `9bbd4ea185e4149a9ac144d4f7b35d43f35f040f`
- Described HEAD: `c2d3a04e4b91071bd0d8c9f080b32bcd1770a18a`
- Working tree: clean
- Pre-merge gate: `B-027 IMPLEMENTATION AUTHORIZED`
- Post-merge gate: `B-027 AI WORKFORCE / WORK-CONTROL GOVERNANCE IMPLEMENTATION`
- Open PR: none
- Latest merge into `main`: `9bbd4ea185e4149a9ac144d4f7b35d43f35f040f` — Canonical Merge Lifecycle V1 (new `anox-software/anox-messenger` PR #4)
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
  security review remediation, and durable pre-commit guard: MERGED into `main` at
  `e7ee54a713e08950c63cf2d61ec97931864b66bc` (PR #5). B-003 is MERGED FOUNDATION, not
  production complete.
- PROMPT-009 — Development Security Governance / Handoff Hardening: MERGED via new PR #1.
- PROMPT-010 — GitHub Remote Activity Safety Governance: MERGED via new PR #1.
- REMOTE-MIGRATION-SYNC-001 — New GitHub main reconciliation: `main` at
  `043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff`.
- B-017-Lite — CI / Supply-Chain Security Foundation (PR #2): MERGED into `main` at
  `283c1a1fdda012aab51b0164b4b16636e870f3b5`; all five CI gates PASS; ANOX-B017REV-001 through -007 CLOSED.
- PRE-B027-0 — B-027 AI Workforce / Work-Control Governance architecture freeze and continuity
  head-semantic fix; B-027 runtime not yet implemented.
- PRE-B027-0R — Targeted remediation of the PRE-B027-0 focused independent review findings
  (ANOX-PREB027REV-001 through -010); all findings remediated.
- PRE-B027-0R2 — Merge-commit payload visibility fix (ANOX-PREB027RREV-001); the validator now
  uses merge-aware `git log -m --name-only --no-renames`, Range-2 merge-resolution union, and
  adversarial regression tests.
- PRE-B027-M1R3 — Canonical merge lifecycle M1R3 schema-downgrade remediation; M1R3
  implementation/local verification, Handoff, archive, attack-reproduction, and live validation all
  PASS. Final independent M1R3 Delta Review was NOT performed by human decision; the Human Product &
  Security Owner authorized controlled Human Push / PR / CI / Merge. Merged to `main` at
  `9bbd4ea185e4149a9ac144d4f7b35d43f35f040f` (PR #4).

## Latest completed work

PRE-B027-M2B — Project Memory / Progress Integrity V1 on `governance/project-memory-progress-integrity-v1`:

- Reconstructs missing project history from PROMPT-008D through M1R3 human merge and B-027
  authorization.
- Adds append-only `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` with 22 material events
  (`ANOX-EVENT-0001` through `ANOX-EVENT-0022`).
- Adds `docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md` defining T0/T1/T2/T3 materiality and the
  minimal surfaces updated per material event.
- Adds `docs/reports/PROJECT_MEMORY_PROGRESS_RECONSTRUCTION_V1.md` discovery report.
- Repairs `FORTSCHRITT.md`, `PROJECT_STATE.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`, and all relevant
  `docs/continuity/CURRENT_*.md` surfaces.
- Extends `tools/continuity/validate_continuity.py` with deterministic ledger parsing, event ID
  ordering, freshness, and pending runtime transition checks.
- Adds `tools/continuity/test_handoff_and_validator.py` regression tests for the new memory rules,
  including pending canonical merge, second checkpoint without seal, and next-sync seal.
- Updates `docs/continuity/DEVIN_OUTPUT_CONTRACT.md` to require material-event reporting for future
  T2/T3 tasks.

## Current open work

`PRE-B027-M2B` — Project Memory / Progress Integrity V1 on `governance/project-memory-progress-integrity-v1`;
implemented locally; awaiting final metadata synchronization and live validation.

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
- Continuity unit tests: 171/171 PASS

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
- `ANOX-CMLR2REV-001`, `ANOX-CMLR2REV-002`, and `ANOX-CMLR2REV-003` are remediated and verified.
- Final independent M1R3 Delta Review was NOT performed by human decision; controlled human merge
  completed.
- No product/security blockers.
- No governance blockers.
- GitHub Free plan: branch protection and secret scanning unavailable.

## Next architecture gate

`B-027 AI WORKFORCE / WORK-CONTROL GOVERNANCE IMPLEMENTATION`

## Next engineering task

After M2B metadata sync: implement the B-027 workforce runtime from the architecture freeze.
No B-027 runtime files are implemented until that task is explicitly authorized and recorded.

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
- B-025, B-026, B-017-Lite, and the B-027 PRE-FROZEN architecture are current governance.
