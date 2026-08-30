# CURRENT NEXT DEVIN TASK

**Status:** AWAITING START
**Task ID:** `B-027 AI WORKFORCE / WORK-CONTROL GOVERNANCE IMPLEMENTATION`
**Date:** 2026-08-30

---

## Purpose

Implement the B-027 AI Workforce / Work-Control Governance runtime described in
`docs/reports/PRE_B027_WORKFORCE_ARCHITECTURE_FREEZE.md`.

B-027 is authorized by the canonical live validator at `9bbd4ea...` (PR #4 merge). M2B is the
intermediate project-memory repair task and is the current authorized work; once M2B is
complete and its metadata is synchronized, the next engineering task is B-027 implementation.

## Preconditions satisfied

- B-027 architecture is frozen and implementation-authorized.
- 19 roles, evidence/egress/priority models, and role-versus-model distinction are defined.
- Canonical Merge Lifecycle V1 is merged to `main`.
- Human-Controlled Remote Write Mode is in effect.
- Project Memory / Progress Integrity V1 ledger, surface index, and validator checks are active.

## Scope of the next task

- Implement the B-027 execution layer (role contracts, task packages, concrete prompts, legacy
  bridge) as defined by the architecture freeze.
- Maintain `WRITER != INDEPENDENT REVIEWER` and fail-closed gates.
- Record all material events in `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` and
  `FORTSCHRITT.md` with `<!-- ANOX_EVENT: ... -->` markers.
- Update only the minimum surfaces required for each event type per
  `docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md`.
- Run the full continuity suite and confirm `PROJECT_MEMORY_FRESHNESS: PASS`.

## Out of scope

- B-004 backend implementation.
- B-005 database/RLS implementation.
- Messenger product code change unrelated to B-027 governance.
- Pushing, PR creation, or remote automation.

## Next authorized sequence

1. Complete `PRE-B027-M2B` and its metadata sync.
2. Create a B-027 work branch from canonical `main`.
3. Implement B-027 runtime.
4. Review, human PR/merge.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
