# CURRENT NEXT DEVIN TASK

**Status:** AWAITING INDEPENDENT REVIEW
**Task ID:** `PRE-B027-M1R2 — CANONICAL MERGE LIFECYCLE DELTA REMEDIATION`
**Date:** 2026-08-30

---

## Purpose

Perform a second targeted remediation for ANOX-CMLR1REV-001 and ANOX-CMLR1REV-002, the two blocking findings from the PRE-B027-M1R1 focused independent Delta Retest.

The M1R2 fix hardens the merge-resolution range (Range 2) with a delivery-endpoint delta so reviewed delivery content cannot be silently reverted to the canonical-parent version, and adds structured parsing and cross-checking of the resolved lifecycle metadata block materialized in `GIT_SNAPSHOT.txt`.

## Preconditions satisfied

- `PRE-B027-0R2` is merged to `main` at `3e127c7a80e9835ea5631e21c10f066401a884dc` (PR #3).
- `PRE-B027-M1R1` (canonical merge lifecycle implementation) is merged to `governance/canonical-merge-lifecycle-v1` at `c36e45f8cf94baa40913215a2c34389138472fd1`.
- `PRE-B027-M1R2` (delta remediation for CMLR1REV-001 and CMLR1REV-002) is implemented at `24c3bc421ea7f6fffa04bc485884c9e26afcd46b`.
- `governance/canonical-merge-lifecycle-v1` is created directly from canonical `main`.
- `tools/continuity/validate_continuity.py` now supports canonical merge lifecycle validation.
- `tools/continuity/generate_handoff.py` resolves handoff-branch and effective-gate placeholders at generation time.
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` records the canonical merge lifecycle rule.
- No product code, CI, or B-027 runtime files are modified.
- Remote-write authority remains `HUMAN-CONTROLLED REMOTE WRITE MODE`.

## Scope of the next task

- Independently Delta Retest ANOX-CMLR1REV-001 (reviewed-content revert in merge resolution) and ANOX-CMLR1REV-002 (GIT_SNAPSHOT lifecycle block cross-check).
- Run `python3 tools/continuity/test_handoff_and_validator.py` and confirm PASS.
- Run `python3 tools/continuity/validate_continuity.py --mode live` on `governance/canonical-merge-lifecycle-v1` and confirm PASS.
- Run a scratch `--no-ff` merge simulation into `main` and confirm `CANONICAL MERGE TRANSITION: PASS`.
- Run a scratch reviewed-content-revert simulation and confirm `DISCARDED REVIEWED DELIVERY CONTENT` FAIL.
- Run a scratch archive N-1 cross-surface tamper simulation and confirm FAIL.
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
