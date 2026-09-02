# CURRENT NEXT DEVIN TASK

**Status:** PENDING HUMAN ASSIGNMENT
**Task ID:** `MAINARCH-FIX-01 — AUTHORITY / SOURCE-OF-TRUTH / B003 / AUDIT-GATE ARCHITECTURE REMEDIATION`
**Date:** 2026-08-31

---

## Purpose

Conduct the first targeted architecture remediation session for the `AUDIT-MAIN-ARCHITECTURE` findings freeze.

`AUDIT-MAIN-ARCHITECTURE` is COMPLETE — PASS WITH FINDINGS at `93c4d3c12da23868a620612a7cd3c2913095ede8` on `audit/main-architecture-findings-freeze`. 36 findings are frozen, 13 are blocking HIGH. Product development remains `BLOCKED_PENDING_FINAL_AUDIT`.

## Preconditions satisfied

- `AUDIT-MAIN-ARCHITECTURE` completed against canonical SHA `0a4910eab1a92622383721100879cda46f924ca0`.
- 36 findings frozen in `docs/workforce/registries/findings.jsonl`.
- Master report populated at `docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md`.
- B027-A/B/C, continuity, B017-Lite, and Rust validation suites PASS.
- Human-controlled remote write mode remains in effect.

## Scope of the next task (when authorized)

- Remediate the `AUDIT-MAIN-ARCHITECTURE` blocking HIGH findings in the dependency-aware order defined in the master report:
  1. 002 + 004 + 035 (authority/routing/source-of-truth correctness)
  2. 005 + 006 + 022 + 032 + 034 (stale/duplicate doc reconciliation)
  3. 001 (B-003 ADR/version bump)
  4. 012 (audit-gate ADR)
  5. 003 → 009 → 010 and related 017/014/015/016/020/021
  6. 011 + 026 (traceability matrix)
  7. 013/024/025/027/028 (release/build/boundary)
  8. 007 coordinated with DB/infra design
- Do not touch code for 019/023/030/031; those are handled by later Legacy sessions or architecture clarification.
- Do not resume B-004/B-005 product implementation.
- Record material events as `ANOX-EVENT-0029+`.
- Maintain `WRITER != INDEPENDENT REVIEWER`, D4 prohibition, no AI remote-write, and fail-closed authorization.

## Out of scope

- Product features (B-004 backend, B-005 database/RLS, messaging, etc.).
- Pushing, PR creation, or remote automation.
- Closing findings without evidence/human review.
- Risk acceptance or severity changes without a recorded human decision.

## Next authorized sequence

1. Human assigns and scopes `MAINARCH-FIX-01`.
2. Targeted fixes against frozen `ANOX-MAINARCH-xxx` findings.
3. Targeted delta retest and evidence recording.
4. Human authorizes next gate (AUDIT-WORKFORCE-ARCHITECTURE, AUDIT-SECURITY-ARCHITECTURE, or continued MAINARCH-FIX).

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
