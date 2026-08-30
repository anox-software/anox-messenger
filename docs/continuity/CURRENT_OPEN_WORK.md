# CURRENT OPEN WORK

**Date:** 2026-08-30 (PRE-B027-M2B Project Memory / Progress Integrity V1)

---

## ARCHITECTURE OPEN

None. B-024 closed the last known architecture-open items. B-025, B-026, and the CML V1 are
merged to `main`. B-027 is PRE-FROZEN and implementation-authorized by the canonical live
validator at `9bbd4ea...`.

## RECENTLY MERGED

- `PROMPT-007` — B-002 Device Authentication client foundation. Merged into `main` at
  `d281df66a3471dfd6a9bab0bd899be701317afb4` (old remote, PR #4).
- `PROMPT-008` / `PROMPT-008C` / `PROMPT-008D` — B-003 Account/License client domain/state
  foundation. Merged into `main` at
  `e7ee54a713e08950c63cf2d61ec97931864b66bc` (old remote, PR #5).
- `PROMPT-009` / `PROMPT-009R` — Development Security Governance / Handoff Hardening. Merged into
  `main` of `anox-software/anox-messenger` via PR #1 at `9c3fb08c30b743274e2c0779937502bb30b313b0`.
- `PROMPT-010` / `PROMPT-010R1` — GitHub Remote Activity Safety Governance. Merged into `main` of
  `anox-software/anox-messenger` via PR #1.
- `REMOTE-MIGRATION-SYNC-001` — New GitHub main / post-merge continuity reconciliation. `main`
  synchronized to `043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff`.
- `B-017-Lite` — CI / Supply-Chain Security Foundation (PR #2). Merged into `main` of
  `anox-software/anox-messenger` at `283c1a1fdda012aab51b0164b4b16636e870f3b5`.
- `PRE-B027-0R2` — Merge-commit payload visibility fix and final continuity remediation (PR #3).
  Merged into `main` at `3e127c7a80e9835ea5631e21c10f066401a884dc`.
- `PRE-B027-M1R..M1R3` — Canonical Merge Lifecycle V1 (PR #4). Merged into `main` of
  `anox-software/anox-messenger` at `9bbd4ea185e4149a9ac144d4f7b35d43f35f040f`.

## CURRENT AUTHORIZED WORK

`PRE-B027-M2B PROJECT MEMORY / PROGRESS INTEGRITY` on `governance/project-memory-progress-integrity-v1`:
reconstruct the missing project history, implement the append-only ledger, surface index,
FORTSCHRITT event markers, and `PROJECT_MEMORY_FRESHNESS` validation.

## NEXT AUTHORIZED ENGINEERING GATE

After M2B is complete and its metadata sync committed:

`B-027 AI WORKFORCE / WORK-CONTROL GOVERNANCE IMPLEMENTATION`

## RELEASE BLOCKERS

None yet. V1 release is gated by B-021…B-023, all future release gates.

## EXTERNAL BLOCKERS

None. The controlled migration to `anox-software/anox-messenger` is complete. Remote-write
authority remains `HUMAN-CONTROLLED REMOTE WRITE MODE` per `GITHUB_REMOTE_ACTIVITY_SAFETY.md`.

## FUTURE / OUT OF V1

- Multi-device
- Account recovery
- Group messaging
- Calls
- Web/desktop clients
