# CURRENT GIT STATE

**Recorded:** 2026-08-30

---

## Repository

- Canonical repository: `https://github.com/anox-software/anox-messenger`
- Canonical SSH remote: `git@github.com:anox-software/anox-messenger.git`
- Legacy provenance remote: `https://github.com/anox-admin/ax-messenger.git` (historical reference only)
- Local remote name: `origin` → `git@github.com:anox-software/anox-messenger.git`
- Legacy remote name: `legacy-origin` → `https://github.com/anox-admin/ax-messenger.git` (optional)

## Merged baseline

- Branch: `main`
- Current baseline HEAD: `3e127c7a80e9835ea5631e21c10f066401a884dc`
- Latest merge into baseline: PR #3 `3e127c7a80e9835ea5631e21c10f066401a884dc` — PRE-B027-0R2 continuity reconciliation merged
- Previous baseline HEAD: `283c1a1fdda012aab51b0164b4b16636e870f3b5`
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`

## Current handoff / work state

- Canonical branch: `main`
- Delivery branch: `governance/canonical-merge-lifecycle-v1`
- Current handoff branch: `__HANDOFF_BRANCH__` (resolve with `git branch --show-current` or `GIT_SNAPSHOT.txt`)
- Current handoff HEAD: `__HANDOFF_HEAD__` (resolve with `git rev-parse HEAD` or `GIT_SNAPSHOT.txt`)
- Described HEAD: `cb1bc3ddfe3a469684ea0c98e7d39412f92f7ec0`
- Working tree: `__WORKING_TREE__` (resolve with `git status --short`)
- Open relevant PR: none
- Current task: `CANONICAL MERGE LIFECYCLE M1R3 SCHEMA-DOWNGRADE REMEDIATION`
- Current gate: `__EFFECTIVE_GATE__` (resolve from lifecycle state; delivery → `CANONICAL MERGE LIFECYCLE M1R3 INDEPENDENT DELTA RETEST`, canonical → `B-027 IMPLEMENTATION AUTHORIZED`)
- Pre-merge gate: `CANONICAL MERGE LIFECYCLE M1R3 INDEPENDENT DELTA RETEST`
- Post-merge gate: `B-027 IMPLEMENTATION AUTHORIZED`

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
- PROMPT-008C — commit-uncertainty closure — MERGED
- PROMPT-008D — durable pre-commit guard and legacy cleanup — MERGED
- PROMPT-009 — Development Security Governance / Handoff Hardening (old PR #6) — MERGED via new PR #1
- PROMPT-010 — GitHub Remote Activity Safety Governance — MERGED via new PR #1
- REMOTE-MIGRATION-SYNC-001 — New GitHub main / post-merge continuity reconciliation — MERGED to `main` at `043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff`
- B-017-Lite — CI / Supply-Chain Security Foundation (PR #2) — MERGED to `main` at `283c1a1fdda012aab51b0164b4b16636e870f3b5`
- PRE-B027-0R2 — Merge-commit payload visibility fix and final continuity remediation — MERGED to `main` at `3e127c7a80e9835ea5631e21c10f066401a884dc` (PR #3); all PRE-B027 findings closed

## Unmerged work

PRE-B027-M1R3 — Canonical merge lifecycle M1R3 schema-downgrade remediation on `governance/canonical-merge-lifecycle-v1`; implemented locally and awaiting `CANONICAL MERGE LIFECYCLE M1R3 INDEPENDENT DELTA RETEST`.

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
