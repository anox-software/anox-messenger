# CURRENT GIT STATE

**Recorded:** 2026-08-29

---

## Repository

- Canonical repository: `https://github.com/anox-software/anox-messenger`
- Canonical SSH remote: `git@github.com:anox-software/anox-messenger.git`
- Legacy provenance remote: `https://github.com/anox-admin/ax-messenger.git` (historical reference only)
- Local remote name: `origin` → `git@github.com:anox-software/anox-messenger.git`
- Legacy remote name: `legacy-origin` → `https://github.com/anox-admin/ax-messenger.git` (optional)

## Merged baseline

- Branch: `main`
- Current baseline HEAD: `043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff`
- Latest merge into baseline: PR #1 `9c3fb08c30b743274e2c0779937502bb30b313b0` — Governance: development security and GitHub remote safety hardening
- Previous baseline HEAD: `9c3fb08c30b743274e2c0779937502bb30b313b0`
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`

## Current handoff / work state

- Current handoff branch: `security/b017-lite-supply-chain-foundation`
- Current handoff HEAD: `__HANDOFF_HEAD__` (resolve with `git rev-parse HEAD` or `GIT_SNAPSHOT.txt`)
- Working tree: `__WORKING_TREE__` (resolve with `git status --short`)
- Open relevant PR: none (B-017-Lite is not yet merged)
- Current task: `B-017-Lite-R3 — Validator enforcement gap remediation`
- Current gate: `B-017-LITE FINAL INDEPENDENT RETEST`

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
- B-017-Lite — CI / Supply-Chain Security Foundation — IN REVIEW on `security/b017-lite-supply-chain-foundation`

## Unmerged work

B-017-Lite on `security/b017-lite-supply-chain-foundation`; awaiting independent security review.

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
- `python3 tools/security/b017_lite_policy_validator.py` expected: PASS
- `python3 -m unittest tools.security.test_b017_lite_policy_validator` expected: 35/35 PASS
- `grep -c "write" .github/workflows/ci.yml` expected: 0
- `python3 tools/security/validate_apk_contents.py <debug-apk>` expected: PASS
- `python3 tools/security/validate_apk_contents.py <release-apk>` expected: PASS
- `git diff --check` expected: PASS
