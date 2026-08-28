# CURRENT NEXT DEVIN TASK

**Status:** AWAITING INDEPENDENT REVIEW
**Task ID:** PROMPT-010 — GITHUB REMOTE ACTIVITY SAFETY GOVERNANCE
**Date:** 2026-08-28

---

## Purpose

The independent R4 retest closed `ANOX-GOVREV-009R-005` and `ANOX-GOVREV-009R-006`. The next local
governance gate is `PROMPT-010 — GitHub Remote Activity Safety Governance`. This introduces the hard
invariant `NO RAPID REPETITIVE REMOTE AUTOMATION` before any AI agent regains remote-write
capability.

## Preconditions satisfied

- `ANOX-GOVREV-009R-001` through `ANOX-GOVREV-009R-006` are `CLOSED`.
- `docs/authority/GITHUB_REMOTE_ACTIVITY_SAFETY.md` is created and indexed.
- `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`, `CURRENT_CHAT_BOOTSTRAP_PROMPT.md`, and
  `HANDOFF_WORKFLOW.md` reference the new policy.
- 24 regression tests PASS.
- Live and archive validators PASS.
- `git diff --check` clean.
- No remote mutation performed; `REMOTE_SYNC_STATUS = BLOCKED — HUMAN ACTION REQUIRED`.

## Scope of the next task

- Independently review `docs/authority/GITHUB_REMOTE_ACTIVITY_SAFETY.md` for:
  - authority under `AUTHORITY_INDEX.md`;
  - clear `NO RAPID REPETITIVE REMOTE AUTOMATION` invariant;
  - local-first workflow;
  - meaningful commit / controlled push / no rapid-loop policy;
  - stop-on-auth/error and account-enforcement rules;
  - human-controlled initial remote-write mode;
  - no substantive-work archival bypass.
- Verify the rule is discoverable in bootstrap and handoff surfaces.
- Verify current-state surfaces agree that `PROMPT-010` is the active gate.
- Run `validate_continuity.py --mode live` and confirm `LIVE_GIT_VERIFICATION: PASS`.
- Run `python3 tools/continuity/test_handoff_and_validator.py` and confirm 24 tests PASS.
- If review PASS, declare `PROMPT-010` ready and preserve the clean local governance checkpoint.

## Out of scope

- GitHub account/repository migration.
- Credential or remote URL configuration.
- Pushing, PR creation, or remote automation.
- B-017-Lite implementation.
- B-027 Workforce implementation.
- B-004 backend implementation.
- B-005 database/RLS implementation.
- Any Messenger product code change.

## Next authorized sequence after this review

1. If PROMPT-010 review PASS, preserve the clean local governance checkpoint.
2. Separately perform the controlled large-update workflow:
   - old Mac GitHub credential logout/removal;
   - new GitHub account initialization;
   - new SSH identity;
   - new empty repository verification;
   - controlled origin migration;
   - safe initial repository publication;
   - remote verification;
   - protection/settings setup;
   - fresh canonical handoff.
3. Merge the governance branch to `main` through review workflow.
4. Declare `PROMPT-009` and `PROMPT-010` complete.
5. Authorize `B-017-Lite` as the next engineering gate.
