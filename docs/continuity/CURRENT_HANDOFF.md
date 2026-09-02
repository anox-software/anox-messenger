# CURRENT HANDOFF — anoX Messenger V1

**Handoff version:** AUDIT-MAIN-ARCHITECTURE — FINDINGS FREEZE
**Date:** 2026-08-31

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
- Delivery branch: `audit/main-architecture-findings-freeze`
- Current work branch: `audit/main-architecture-findings-freeze`
- Current baseline branch: `main`
- Current baseline HEAD: `0a4910eab1a92622383721100879cda46f924ca0`
- Described HEAD: `93c4d3c12da23868a620612a7cd3c2913095ede8`
- Working tree: clean
- Pre-merge gate: `AUDIT-MAIN-ARCHITECTURE FINDINGS FREEZE`
- Post-merge gate: `MAINARCH-FIX-01 — AUTHORITY / SOURCE-OF-TRUTH / B003 / AUDIT-GATE ARCHITECTURE REMEDIATION`
- Open PR: none
- Latest merge into `main`: `0a4910eab1a92622383721100879cda46f924ca0` — B027-C Final B027 Integration / Integrity / System Adversarial Validation + Handoff + Cold Recovery + Final Pre-Product Audit Preparation (new `anox-software/anox-messenger` PR #8)
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
- REMOTE-MIGRATION-SYNC-001 — New GitHub main / post-merge continuity reconciliation: MERGED to `main` at
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
- B027-A — AI Workforce / Work-Control Governance Foundation: MERGED into `main` at
  `38b619e55082086989bb0713cad42c4c53be14ab` (PR #6). Adds B-027 Authority, Runtime/Integration
  Contract, Model Provider Policy, role registry, schemas, registries, workforce state, validator,
  and adversarial tests.
- B027-B — State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime: MERGED into
  `main` at `aca7a8364a89423173440997ac01865c63552ca0` (new `anox-software/anox-messenger` PR #7).
  Adds `tools/workforce/state_gate_resolver.py`, `tools/workforce/validate_b027b.py`, per-role
  contracts `ROLE-001` through `ROLE-019`, prompt/communication schemas and registries, and
  continuity integration.
- B027-C — INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027
  INTEGRATION: merged to `main` at `0a4910eab1a92622383721100879cda46f924ca0` (PR #8).
- AUDIT-MAIN-ARCHITECTURE: COMPLETED — PASS WITH FINDINGS at `93c4d3c12da2...` on
  `audit/main-architecture-findings-freeze`. 36 findings frozen (`ANOX-MAINARCH-001..036`);
  13 blocking HIGH. Product remains blocked pending `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`.
  Next: `MAINARCH-FIX-01`.

## Latest completed work

AUDIT-MAIN-ARCHITECTURE — read-only architecture audit and findings freeze:

- Canonical audited SHA: `0a4910eab1a92622383721100879cda46f924ca0`.
- Result: `PASS WITH FINDINGS` (encoded as `PARTIAL` in the audit-result record).
- 36 findings frozen in `docs/workforce/registries/findings.jsonl` (`ANOX-MAINARCH-001..036`).
- 13 blocking HIGH findings; 0 CRITICAL.
- Audit result recorded in `docs/workforce/registries/audits.jsonl`.
- Master report populated at `docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md`.
- B027 integrity validator, continuity, B017-Lite policy validator, and Rust tests all PASS.
- No architecture fixes, code fixes, product changes, CI changes, or remote mutation.

## Previous completed work

B027-B — State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime:

- Adds `tools/workforce/state_gate_resolver.py` — deterministic, fail-closed State/Gate Resolver.
- Adds `tools/workforce/validate_b027b.py` — B027-B validator and 48 adversarial tests.
- Adds `docs/workforce/roles/ROLE-001.md` through `ROLE-019.md` — canonical per-role contracts.
- Adds `docs/workforce/schemas/prompt.schema.json` and `docs/workforce/schemas/communication.schema.json`.
- Adds `docs/workforce/registries/prompts.jsonl` and `docs/workforce/registries/communications.jsonl`.
- Adds final pre-product architecture/security audit gate contract, product-resume blocking
  semantics, and continuity integration.
- Adds `docs/reports/B027B_WORK_CONTROL_RUNTIME.md`.
- Merged to `main` at `aca7a8364a89423173440997ac01865c63552ca0` (new `anox-software/anox-messenger`
  PR #7).

## Current open work

`MAINARCH-FIX-01 — AUTHORITY / SOURCE-OF-TRUTH / B003 / AUDIT-GATE ARCHITECTURE REMEDIATION`
(not yet authorized; START WHEN HUMAN ASSIGNS):

- Targeted architecture remediation of AUDIT-MAIN-ARCHITECTURE blocking HIGH findings.
- Priority order: 002+004+035 → 005+006+022+032+034 → 001 → 012 → 003 → 009 → 010 etc.
- No product code, CI, backend, database, crypto, or remote mutation without explicit authorization.
- Product development remains `BLOCKED_PENDING_FINAL_AUDIT`.

## Previous open work

B027-C — INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027
INTEGRATION on `governance/b027-final-integration`:

- Adds `tools/workforce/validate_b027_integrity.py` — B027-C integrity validator.
- Adds adversarial system tests that exercise the full resolver-to-handoff path.
- Extends `tools/continuity/generate_handoff.py` and validates cold recovery from `GIT_SNAPSHOT.txt`.
- Ensures `described_head`, `handoff_head`, `working_tree`, and effective gate semantics survive a
  new-chat bootstrap.
- Adds `docs/workforce/audits/FINAL_AUDIT_PLAN.md`, `docs/workforce/audits/LEGACY_AUDIT_PLAN.md`,
  and `docs/workforce/schemas/audit-result.schema.json`.
- Adds `docs/reports/B027C_FINAL_INTEGRATION.md` and
  `docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md`.
- Maintains `WRITER != INDEPENDENT REVIEWER`, `D4` prohibition, no AI remote-write, and
  fail-closed authorization.
- Records all material events in `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` and
  `FORTSCHRITT.md` with `<!-- ANOX_EVENT: ... -->` markers.
- Merged to `main` at `0a4910eab1a92622383721100879cda46f924ca0` (PR #8).

## Current test baseline

- B-017-Lite CI gates: 5/5 PASS
- Rust crypto tests: 15/15 PASS
- Android JVM unit tests: 161/161 PASS
- Android debug build + APK content validation: PASS
- Android release compile + APK content validation: PASS
- Android connected instrumentation: 62/62 PASS on a local API-34 emulator
- GrapheneOS physical device: UNVERIFIED
- B-017-Lite policy validator: 35/35 PASS
- Continuity unit tests: 171/171 PASS
- B027-A adversarial tests: 20/20 PASS
- B027-B adversarial tests: 48/48 PASS
- B027-C integrity validator: PASS

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
- B027-A and B027-B are merged to `main`; B027-C is implemented and validated on
  `governance/b027-final-integration`.
- Product is blocked pending `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`.
- No governance blockers.
- GitHub Free plan: branch protection and secret scanning unavailable.

## Next architecture gate

`FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`

## Next engineering task

Prepare for and conduct the `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT` (session
`AUDIT-MAIN-ARCHITECTURE`). No product/CI changes until the audit is authorized and recorded.

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
