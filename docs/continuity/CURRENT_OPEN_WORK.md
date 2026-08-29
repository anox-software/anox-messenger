# CURRENT OPEN WORK

**Date:** 2026-08-29 (REMOTE-MIGRATION-SYNC-001 complete)

---

## ARCHITECTURE OPEN

None. B-024 closed the last known architecture-open items. B-025 is frozen. B-026 is frozen.

## RECENTLY MERGED

- `PROMPT-007` — B-002 Device Authentication client foundation. Merged into `main` at
  `d281df66a3471dfd6a9bab0bd899be701317afb4` (old remote, PR #4) after independent security/architecture
  review (APPROVE, no merge-blocking findings) and empirical dependency-tree verification.
- `PROMPT-008` / `PROMPT-008C` / `PROMPT-008D` — B-003 Account/License client domain/state
  foundation, security review remediation, and final commit-uncertainty closure. Merged into
  `main` at `e7ee54a713e08950c63cf2d61ec97931864b66bc` (old remote, PR #5).
- `PROMPT-009` / `PROMPT-009R` — Development Security Governance / Handoff Hardening. Merged into
  `main` of `anox-software/anox-messenger` via PR #1 at `9c3fb08c30b743274e2c0779937502bb30b313b0`.
- `PROMPT-010` / `PROMPT-010R1` — GitHub Remote Activity Safety Governance. Merged into `main` of
  `anox-software/anox-messenger` via PR #1 at `9c3fb08c30b743274e2c0779937502bb30b313b0`.
- `REMOTE-MIGRATION-SYNC-001` — New GitHub main / post-merge continuity reconciliation. Current
  `main` HEAD `9c3fb08c30b743274e2c0779937502bb30b313b0`.

## IN REVIEW / RETEST

None. All governance findings are CLOSED. All governance work is merged to `main`.

## NEXT AUTHORIZED ENGINEERING GATE

`B-017-Lite` — CI / Supply-Chain Security Foundation.

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
