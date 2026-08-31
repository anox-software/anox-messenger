# CURRENT GIT STATE

**Recorded:** 2026-08-31

---

## Repository

- Canonical repository: `https://github.com/anox-software/anox-messenger`
- Canonical SSH remote: `git@github.com:anox-software/anox-messenger.git`
- Legacy provenance remote: `https://github.com/anox-admin/ax-messenger.git` (historical reference only)
- Local remote name: `origin` → `git@github.com:anox-software/anox-messenger.git`
- Legacy remote name: `legacy-origin` → `https://github.com/anox-admin/ax-messenger.git` (optional)

## Merged baseline

- Branch: `main`
- Current baseline HEAD: `38b619e55082086989bb0713cad42c4c53be14ab`
- Latest merge into baseline: `38b619e55082086989bb0713cad42c4c53be14ab` — B027-A AI Workforce / Work-Control Governance Foundation merged to main (new `anox-software/anox-messenger` PR #6)
- Previous baseline HEAD: `69c1d9b9f7605d5d96e0bc1add3d05ecbc82ee1b`
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`

## Current handoff / work state

- Canonical branch: `main`
- Delivery branch: `governance/b027-work-control-runtime`
- Current handoff branch: `__HANDOFF_BRANCH__` (resolve with `git branch --show-current` or `GIT_SNAPSHOT.txt`)
- Current handoff HEAD: `__HANDOFF_HEAD__` (resolve with `git rev-parse HEAD` or `GIT_SNAPSHOT.txt`)
- Described HEAD: `76849b1a9f1f9aefc913f53645628ddb33f10c51`
- Working tree: `__WORKING_TREE__` (resolve with `git status --short`)
- Open relevant PR: none
- Current task: `B027-B — STATE/GATE RESOLVER + ROLE CONTRACTS + TASK/PROMPT/COMMUNICATION RUNTIME — IN PROGRESS; NEXT: B027-C`
- Current gate: `__EFFECTIVE_GATE__` (resolve from lifecycle state; delivery → `B027-B — STATE/GATE RESOLVER + ROLE CONTRACTS + TASK/PROMPT/COMMUNICATION RUNTIME`, canonical → `B027-C — INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027 INTEGRATION`)
- Pre-merge gate: `B027-B — STATE/GATE RESOLVER + ROLE CONTRACTS + TASK/PROMPT/COMMUNICATION RUNTIME`
- Post-merge gate: `B027-C — INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027 INTEGRATION`

## Merged history on main

- CONTINUITY-001.1 — Freeze registry and initial handoff tooling
- CONTINUITY-001.2A — Historical provenance and master parity
- CONTINUITY-001.3 — Cold new-chat bootstrap PASS
- CONTINUITY-001.3B — Bootstrap pass finalization, B-010 fix, retention policy
- CONTINUITY-001.4 — APK content / secret leakage release gate
- CONTINUITY-001.5 — Final main continuity state synchronization
- CONTINUITY-001 — ACCEPTED
- PROMPT-007 — B-002 Device Authentication client foundation (PR #4 under old remote) — MERGED
- PROMPT-007B — independent security/architecture review — APPROVE, no merge-blocking findings
- PROMPT-007C — merge gate verification, dependency-tree empirical confirmation, merge, and
  continuity synchronization
- PROMPT-008 — B-003 Account/License client domain/state foundation (PR #5 under old remote) — MERGED
- PROMPT-008D — commit-uncertainty closure — MERGED
- PROMPT-009 — Development Security Governance / Handoff Hardening (old PR #6) — MERGED via new PR #1
- PROMPT-010 — GitHub Remote Activity Safety Governance — MERGED via new PR #1
- REMOTE-MIGRATION-SYNC-001 — New GitHub main / post-merge continuity reconciliation — MERGED to `main` at `043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff`
- B-017-Lite — CI / Supply-Chain Security Foundation (PR #2) — MERGED to `main` at `283c1a1fdda012aab51b0164b4b16636e870f3b5`
- PRE-B027-0R2 — Merge-commit payload visibility fix and final continuity remediation — MERGED to `main` at `3e127c7a80e9835ea5631e21c10f066401a884dc` (PR #3)
- PRE-B027-M1R3 — Canonical merge lifecycle M1R3 schema-downgrade remediation — locally implemented and MERGED to `main` at `9bbd4ea185e4149a9ac144d4f7b35d43f35f040f` (PR #4). No final independent M1R3 Delta Review occurred by human decision.
- B027-A — AI Workforce / Work-Control Governance Foundation — MERGED to `main` at `38b619e55082086989bb0713cad42c4c53be14ab` (PR #6)

## Unmerged work

`B027-B` — State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime on `governance/b027-work-control-runtime`; implements runtime execution layer, role contracts, prompt/communication schemas and registries, and resolver tests. B027-C remains deferred.

## B-003 status after this task

- Client domain/state foundation (identifiers, username/license validation, account/device/
  entitlement states, registration state machine, narrow B-004 API contracts, persistent Device
  Auth binding store and registration session storage): MERGED FOUNDATION / VERIFIED where tested.
- Backend implementation of `RegistrationApi`, license generation, server HMAC lookup, real
  network stack, DB enforcement of one-active-device-per-account: MISSING (future B-004/B-005).
- Physical StrongBox/TEE, GrapheneOS physical-device behaviour: UNVERIFIED.

## Verification

- `python3 tools/continuity/validate_continuity.py` expected: PASS
- `python3 tools/continuity/test_handoff_and_validator.py` expected: PASS
- `python3 tools/continuity/generate_handoff.py` expected: PASS
- `git diff --check` expected: PASS
