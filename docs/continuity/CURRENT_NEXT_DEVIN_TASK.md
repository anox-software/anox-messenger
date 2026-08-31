# CURRENT NEXT DEVIN TASK

**Status:** AUTHORIZED — START WHEN HUMAN ASSIGNS
**Task ID:** `B027-C — INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027 INTEGRATION`
**Date:** 2026-08-31

---

## Purpose

Integrate, validate, and harden the B027 workforce runtime from `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
and `docs/reports/B027B_WORK_CONTROL_RUNTIME.md`.

B027-B is in progress on `governance/b027-work-control-runtime` at `76849b1...`. B027-C is the
next authorized engineering task.

## Preconditions satisfied

- B-027 architecture is frozen and implementation-authorized.
- B027-A governance foundation is merged to `main`.
- B027-B runtime (state/gate resolver, role contracts, prompt/communication runtime) is implemented and passing.
- 19 roles, evidence/egress/priority models, and role-versus-model distinction are defined.
- Canonical Merge Lifecycle V1 is merged to `main`.
- Human-Controlled Remote Write Mode is in effect.
- Project Memory / Progress Integrity V1 ledger, surface index, and validator checks are active.

## Scope of the next task

- Implement the B027-C integrity validator for workforce governance.
- Add adversarial system tests that exercise the full resolver-to-handoff path.
- Extend `tools/continuity/generate_handoff.py` and validate cold recovery from `GIT_SNAPSHOT.txt`.
- Ensure `described_head`, `handoff_head`, `working_tree`, and effective gate semantics survive a new-chat bootstrap.
- Maintain `WRITER != INDEPENDENT REVIEWER`, `D4` prohibition, no AI remote-write, and
  fail-closed authorization.
- Record all material events in `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` and
  `FORTSCHRITT.md` with `<!-- ANOX_EVENT: ... -->` markers.
- Update only the minimum surfaces required for each event type per
  `docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md`.
- Run the full continuity suite and confirm `PROJECT_MEMORY_FRESHNESS: PASS`.

## Out of scope

- Product features (B-004 backend, B-005 database/RLS, messaging, etc.).
- Pushing, PR creation, or remote automation.

## Next authorized sequence

1. Author and review B027-C changes on a delivery branch from `main` (or continue on the B027-B branch if explicitly authorized).
2. Run the full continuity, B027-A, B027-B, B017, and Rust test suites.
3. Human PR/merge to `main`.
4. Metadata synchronization and final validation.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
