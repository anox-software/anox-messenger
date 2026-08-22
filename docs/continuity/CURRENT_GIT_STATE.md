# CURRENT GIT STATE

**Recorded:** 2026-08-22

---

## Repository

- URL: `https://github.com/anox-admin/ax-messenger.git`
- Remote: `origin`

## Merged baseline

- Branch: `main`
- Merged baseline HEAD: `d281df66a3471dfd6a9bab0bd899be701317afb4`
- Latest merge into baseline: PR #4 `d281df66a3471dfd6a9bab0bd899be701317afb4` — PROMPT-007, B-002
  Device Authentication client foundation
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`

## Current handoff / work state

- Current handoff branch: `main`
- Current handoff HEAD: `__HANDOFF_HEAD__` (resolve with `git rev-parse HEAD` or `GIT_SNAPSHOT.txt`)
- Working tree: `__WORKING_TREE__` (resolve with `git status --short`)
- Open relevant PR: `none` — PR #4 merged and closed
- Current task: `PROMPT-007` — MERGED
- Current gate: `B-003 ACCOUNT / LICENSE FOUNDATION — NOT STARTED, NOT AUTHORIZED`

## Merged history on main

- CONTINUITY-001.1 — Freeze registry and initial handoff tooling
- CONTINUITY-001.2A — Historical provenance and master parity
- CONTINUITY-001.3 — Cold new-chat bootstrap PASS
- CONTINUITY-001.3B — Bootstrap pass finalization, B-010 fix, retention policy
- CONTINUITY-001.4 — APK content / secret leakage release gate
- CONTINUITY-001.5 — Final main continuity state synchronization
- CONTINUITY-001 — ACCEPTED
- PROMPT-007 — B-002 Device Authentication client foundation (PR #4) — MERGED
- PROMPT-007B — Independent security/architecture review — APPROVE, no merge-blocking findings
- PROMPT-007C — Merge gate verification, dependency-tree empirical confirmation, merge, and
  continuity synchronization

## Unmerged work

- None on `main`.

## B-002 status after merge

- Client foundation (Android Keystore key, hardware policy, RFC9449 DPoP proof creation and
  verification boundary, fail-closed terminal key loss): IMPLEMENTED / VERIFIED where tested.
- Backend token issuance/storage/revocation, shared production replay cache, device registry,
  entitlement enforcement, persistent `DeviceAuthBindingStore`, registration binding call:
  MISSING (future B-003/B-004 work).
- Android instrumentation (real Keystore), physical StrongBox/TEE, GrapheneOS physical-device
  Device Auth: UNVERIFIED.

## Verification

- `python3 tools/continuity/validate_continuity.py` expected: PASS
- `python3 tools/security/validate_apk_contents.py <debug-apk>` expected: PASS
- `python3 tools/security/validate_apk_contents.py <release-apk>` expected: PASS
- `git diff --check` expected: PASS
