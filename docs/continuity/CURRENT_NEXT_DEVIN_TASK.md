# CURRENT NEXT DEVIN TASK

**Status:** AWAITING INDEPENDENT REVIEW
**Task ID:** `PRE-B027-M1R3 — CANONICAL MERGE LIFECYCLE SCHEMA-DOWNGRADE REMEDIATION`
**Date:** 2026-08-30

---

## Purpose

Perform the third targeted remediation for ANOX-CMLR2REV-001 (archive lifecycle schema-class downgrade), ANOX-CMLR2REV-002 (placeholder regression test defect), and ANOX-CMLR2REV-003 (SHA-256 manifest coverage gap).

The M1R3 fix prevents an attacker-controlled archive from disabling current Canonical Merge Lifecycle validation by removing lifecycle/schema fields and triggering a silent fallback to legacy validation. It also forces lifecycle enforcement from the independently generated `GIT_SNAPSHOT.txt` resolved lifecycle metadata block, requires all lifecycle keys in `CURRENT_STATE.json`, hardens lifecycle snapshot placeholder parsing, and covers `GIT_SNAPSHOT.txt` and `MANIFEST.txt` in the archive SHA-256 manifest.

## Preconditions satisfied

- `PRE-B027-0R2` is merged to `main` at `3e127c7a80e9835ea5631e21c10f066401a884dc` (PR #3).
- `PRE-B027-M1R1` (canonical merge lifecycle implementation) is merged to `governance/canonical-merge-lifecycle-v1` at `c36e45f8cf94baa40913215a2c34389138472fd1`.
- `PRE-B027-M1R2` (delta remediation for CMLR1REV-001 and CMLR1REV-002) is implemented at `24c3bc421ea7f6fffa04bc485884c9e26afcd46b`.
- `PRE-B027-M1R3` (schema-downgrade remediation) is implemented at `cb1bc3ddfe3a469684ea0c98e7d39412f92f7ec0`.
- `governance/canonical-merge-lifecycle-v1` is created directly from canonical `main`.
- `tools/continuity/validate_continuity.py` uses explicit, fail-closed archive schema classification.
- `tools/continuity/generate_handoff.py` covers `GIT_SNAPSHOT.txt` and `MANIFEST.txt` in the SHA-256 manifest.
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` records the schema-downgrade invariants.
- No product code, CI, or B-027 runtime files are modified.
- Remote-write authority remains `HUMAN-CONTROLLED REMOTE WRITE MODE`.

## Scope of the next task

- Independently Delta Retest ANOX-CMLR2REV-001, ANOX-CMLR2REV-002, and ANOX-CMLR2REV-003.
- Confirm ANOX-CMLREV-002 and ANOX-CMLR1REV-002 remain REMEDIATED / READY FOR RETEST and can be closed.
- Run `python3 tools/continuity/test_handoff_and_validator.py` and confirm PASS.
- Run `python3 tools/continuity/validate_continuity.py --mode live` on `governance/canonical-merge-lifecycle-v1` and confirm PASS.
- Run a scratch `--no-ff` merge simulation into `main` and confirm `CANONICAL MERGE TRANSITION: PASS`.
- Run a scratch archive schema-downgrade simulation and confirm `HANDOFF_ARCHIVE_VALIDATION: FAIL`.
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
