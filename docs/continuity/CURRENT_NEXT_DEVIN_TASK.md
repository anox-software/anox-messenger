# CURRENT NEXT DEVIN TASK

**Status:** AUTHORIZED — START WHEN HUMAN ASSIGNS
**Task ID:** `B027-B — STATE/GATE RESOLVER + ROLE CONTRACTS + TASK/PROMPT/COMMUNICATION RUNTIME`
**Date:** 2026-08-31

---

## Purpose

Implement the B027-B AI Workforce execution layer from `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
and `docs/reports/PRE_B027_WORKFORCE_ARCHITECTURE_FREEZE.md`.

B027-A is complete on `governance/b027-workforce-foundation` at `83259e7...`. B027-B is the
next authorized engineering task.

## Preconditions satisfied

- B-027 architecture is frozen and implementation-authorized.
- 19 roles, evidence/egress/priority models, and role-versus-model distinction are defined.
- Canonical Merge Lifecycle V1 is merged to `main`.
- Human-Controlled Remote Write Mode is in effect.
- Project Memory / Progress Integrity V1 ledger, surface index, and validator checks are active.

## Scope of the next task

- Implement the B027-B State/Gate Resolver execution engine.
- Add per-role contracts and concrete Devin/agent prompts for ROLE-001 through ROLE-019.
- Add the Task Package / Finding / Decision / Run / Derived Work runtime.
- Add the communication bus for role/runtime coordination.
- Maintain `WRITER != INDEPENDENT REVIEWER`, `D4` prohibition, no AI remote-write, and
  fail-closed authorization.
- Record all material events in `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` and
  `FORTSCHRITT.md` with `<!-- ANOX_EVENT: ... -->` markers.
- Update only the minimum surfaces required for each event type per
  `docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md`.
- Run the full continuity suite and confirm `PROJECT_MEMORY_FRESHNESS: PASS`.

## Out of scope

- B027-C Cold Recovery integration (deferred).
- B-004 backend implementation.
- B-005 database/RLS implementation.
- Messenger product code change unrelated to B-027 governance.
- Pushing, PR creation, or remote automation.

## Next authorized sequence

1. Create a B027-B work branch from canonical `main`.
2. Implement B027-B runtime.
3. Review, human PR/merge.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
