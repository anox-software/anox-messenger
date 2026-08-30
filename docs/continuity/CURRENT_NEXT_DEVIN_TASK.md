# CURRENT NEXT DEVIN TASK

**Status:** AWAITING INDEPENDENT REVIEW
**Task ID:** `PRE-B027-M1R — PERMANENT CANONICAL MERGE LIFECYCLE HARDENING`
**Date:** 2026-08-30

---

## Purpose

Implement a permanent canonical merge lifecycle for anoX continuity governance. This closes the systemic workflow defect that caused an otherwise fully reviewed and clean GitHub merge to fail continuity validation on `main`.

The fix separates `canonical_branch` and `delivery_branch`, distinguishes the reviewed delivery tail from the merge-resolution range and the post-merge canonical tail, and derives the effective next gate from the verified lifecycle state.

## Preconditions satisfied

- `PRE-B027-0R2` is merged to `main` at `3e127c7a80e9835ea5631e21c10f066401a884dc` (PR #3).
- All PRE-B027 findings are closed; zero new blocking findings.
- `governance/canonical-merge-lifecycle-v1` is created directly from canonical `main`.
- `tools/continuity/validate_continuity.py` now supports canonical merge lifecycle validation.
- `tools/continuity/generate_handoff.py` resolves handoff-branch and effective-gate placeholders at generation time.
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` records the canonical merge lifecycle rule.
- No product code, CI, or B-027 runtime files are modified.
- Remote-write authority remains `HUMAN-CONTROLLED REMOTE WRITE MODE`.

## Scope of the next task

- Independently review the canonical merge lifecycle implementation and its test evidence.
- Run `python3 tools/continuity/test_handoff_and_validator.py` and confirm PASS.
- Run `python3 tools/continuity/validate_continuity.py --mode live` on `governance/canonical-merge-lifecycle-v1` and confirm PASS.
- Run a scratch `--no-ff` merge simulation into `main` and confirm `CANONICAL MERGE TRANSITION: PASS`.
- Run a scratch evil-merge simulation and confirm FAIL.
- Run `python3 tools/continuity/generate_handoff.py` and confirm archive validation PASS.
- Verify no remote mutation occurred.
- If all checks pass, declare ready for controlled human PR/merge.

## Out of scope

- B-027 Workforce runtime implementation.
- B-004 backend implementation.
- B-005 database/RLS implementation.
- Any Messenger product code change.
- Pushing, PR creation, or remote automation.

## Next authorized sequence after this review

1. If focused review PASS, preserve the clean local `governance/canonical-merge-lifecycle-v1` branch.
2. Human-controlled remote actions: create PR, merge to `main`.
3. After verified merge: `B-027 IMPLEMENTATION AUTHORIZED`.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
