# CURRENT GIT STATE

**Recorded:** 2026-08-28

---

## Repository

- URL: `https://github.com/anox-admin/ax-messenger.git`
- Remote: `origin`

## Merged baseline

- Branch: `main`
- Current baseline HEAD: `881c85ec726d8a32eb84b00955b6b9db7912fe1e`
- Latest merge into baseline: PR #5 `e7ee54a713e08950c63cf2d61ec97931864b66bc` — PROMPT-008 /
  B-003 Account/License client foundation
- Previous merge: PR #4 `d281df66a3471dfd6a9bab0bd899be701317afb4` — PROMPT-007,
  B-002 Device Authentication client foundation
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`

## Current handoff / work state

- Current handoff branch: `governance/development-security-handoff-v1`
- Current handoff HEAD: `__HANDOFF_HEAD__` (resolve with `git rev-parse HEAD` or `GIT_SNAPSHOT.txt`)
- Working tree: `__WORKING_TREE__` (resolve with `git status --short`)
- Open relevant PR: PR #6 — PROMPT-009 / PROMPT-009R governance, open against `main`
- Current task: `PROMPT-010R1 — Remediation of 010-001/002`
- Current gate: `INDEPENDENT RETEST OF ANOX-GOVREV-010-001 AND ANOX-GOVREV-010-002`

## Merged history on main

- CONTINUITY-001.1 — Freeze registry and initial handoff tooling
- CONTINUITY-001.2A — Historical provenance and master parity
- CONTINUITY-001.3 — Cold new-chat bootstrap PASS
- CONTINUITY-001.3B — Bootstrap pass finalization, B-010 fix, retention policy
- CONTINUITY-001.4 — APK content / secret leakage release gate
- CONTINUITY-001.5 — Final main continuity state synchronization
- CONTINUITY-001 — ACCEPTED
- PROMPT-007 — B-002 Device Authentication client foundation (PR #4) — MERGED
- PROMPT-007B — independent security/architecture review — APPROVE, no merge-blocking findings
- PROMPT-007C — merge gate verification, dependency-tree empirical confirmation, merge, and
  continuity synchronization
- PROMPT-008 — B-003 Account/License client domain/state foundation (PR #5) — MERGED
- PROMPT-008C — commit-uncertainty closure — MERGED
- PROMPT-008D — durable pre-commit guard and legacy cleanup — MERGED
- Post-PROMPT-008 continuity synchronization — `881c85ec726d8a32eb84b00955b6b9db7912fe1e`
- PROMPT-009 — Development Security Governance / Handoff Hardening (PR #6) — OPEN, not yet merged

## Unmerged work

PR #6 (PROMPT-009 / PROMPT-009R) is open against `main`.

## B-003 status after this task

- Client domain/state foundation (identifiers, username/license validation, account/device/
  entitlement states, registration state machine, narrow B-004 API contracts, persistent Device
  Auth binding store and registration session storage): MERGED FOUNDATION / VERIFIED where tested.
- Backend implementation of `RegistrationApi`, license generation, server HMAC lookup, real
  network stack, DB enforcement of one-active-device-per-account: MISSING (future B-004/B-005).
- Physical StrongBox/TEE, GrapheneOS physical-device behaviour: UNVERIFIED.

## Verification

- `python3 tools/continuity/validate_continuity.py` expected: PASS
- `python3 tools/security/validate_apk_contents.py <debug-apk>` expected: PASS
- `python3 tools/security/validate_apk_contents.py <release-apk>` expected: PASS
- `git diff --check` expected: PASS
