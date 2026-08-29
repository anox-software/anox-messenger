# CURRENT NEXT DEVIN TASK

**Status:** AWAITING AUTHORIZATION
**Task ID:** `B-017-Lite — CI / Supply-Chain Security Foundation`
**Date:** 2026-08-29

---

## Purpose

The governance and migration gates are complete. PR #1 of `anox-software/anox-messenger` has
merged the PROMPT-009 / PROMPT-010 governance work into `main`. The next authorized engineering
gate is `B-017-Lite — CI / Supply-Chain Security Foundation`.

## Preconditions satisfied

- `PROMPT-009` / `PROMPT-009R` governance is merged.
- `PROMPT-010` / `PROMPT-010R1` is `ACCEPTED`.
- `REMOTE-MIGRATION-SYNC-001` post-merge reconciliation is complete.
- `main` HEAD is `9c3fb08c30b743274e2c0779937502bb30b313b0`.
- Repository is `anox-software/anox-messenger`.
- `GITHUB_REMOTE_ACTIVITY_SAFETY.md` is binding.
- Remote-write authority remains `HUMAN-CONTROLLED REMOTE WRITE MODE`.

## Scope (when authorized)

- Android lint / static analysis
- Repository secret scanning
- Diff-aware secret scanning
- History-aware secret scanning where practical
- `cargo audit`
- Dependency vulnerability scanning
- OSV or equivalent advisory checks
- Dependency locking / verification improvements
- GitHub Actions immutable SHA pinning where practical
- CI hardening
- Android instrumentation CI where technically reliable
- Supply-chain evidence foundation

## Out of scope

- B-004 backend implementation
- B-005 database/RLS implementation
- B-027 AI Workforce policy implementation (may run in parallel if explicitly authorized)
- Messaging UI, accounts, transport, attachments, multi-device, push

## Next authorized sequence after B-017-Lite

1. B-017-Lite implementation, review, and merge.
2. B-027 AI Workforce / work-control governance (if not done in parallel).
3. Resume remaining anoX product-development blocks per architecture authority.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
