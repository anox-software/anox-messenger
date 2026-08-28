# CURRENT NEXT DEVIN TASK

**Status:** AWAITING INDEPENDENT RETEST
**Task IDs:** ANOX-GOVREV-010-001, ANOX-GOVREV-010-002
**Date:** 2026-08-28

---

## Purpose

The independent PROMPT-010 review identified two findings. PROMPT-010R1 has remediated them:

- `ANOX-GOVREV-010-001` — duplicate numbering in `docs/authority/AUTHORITY_INDEX.md`.
- `ANOX-GOVREV-010-002` — missing `AI remote-write authority assumed?` quick-reference row in
  `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`.

The next local gate is the independent retest of both findings.

## Preconditions satisfied

- `ANOX-GOVREV-009R-001` through `ANOX-GOVREV-009R-006` are `CLOSED`.
- `docs/authority/AUTHORITY_INDEX.md` canonical precedence list has unique, sequential numbering.
- `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md` quick-reference table includes the
  remote-write authority question.
- `docs/authority/GITHUB_REMOTE_ACTIVITY_SAFETY.md` remains unchanged and authoritative.
- 24 regression tests PASS.
- Live and archive validators PASS.
- `git diff --check` clean.
- No remote mutation performed; `REMOTE_SYNC_STATUS = BLOCKED — HUMAN ACTION REQUIRED`.

## Scope of the next task

- Independently verify `docs/authority/AUTHORITY_INDEX.md` has no duplicate numbering and that the
  intended precedence order is preserved.
- Independently verify `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md` quick-reference table
  includes a row with the semantic `Is AI remote-write authority assumed? → NO` and a pointer to
  `GITHUB_REMOTE_ACTIVITY_SAFETY.md`.
- Verify current-state surfaces agree that `ANOX-GOVREV-010-001` and `ANOX-GOVREV-010-002` are
  `FIX_READY` and the active gate is their independent retest.
- Run `validate_continuity.py --mode live` and confirm `LIVE_GIT_VERIFICATION: PASS`.
- Run `python3 tools/continuity/test_handoff_and_validator.py` and confirm 24 tests PASS.
- If all checks pass, declare `ANOX-GOVREV-010-001` and `ANOX-GOVREV-010-002` `CLOSED` and
  `PROMPT-010` accepted.

## Out of scope

- GitHub account/repository migration.
- Credential or remote URL configuration.
- Pushing, PR creation, or remote automation.
- B-017-Lite implementation.
- B-027 Workforce implementation.
- B-004 backend implementation.
- B-005 database/RLS implementation.
- Any Messenger product code change.

## Next authorized sequence after this retest

1. If `ANOX-GOVREV-010-001` and `ANOX-GOVREV-010-002` retest PASS, the independent reviewer
   closes both findings and accepts `PROMPT-010`.
2. Preserve the clean local governance checkpoint.
3. Separately perform the controlled new GitHub environment migration.
4. Merge the governance branch to `main` through the reviewable workflow.
5. Synchronize `main` continuity surfaces and generate a fresh canonical handoff.
6. Cold archive bootstrap PASS and live-source reconciliation PASS.
7. Declare `PROMPT-009` and `PROMPT-010` complete.
8. Authorize `B-017-Lite` as the next engineering gate.
