# CURRENT NEXT DEVIN TASK

**Status:** AWAITING FOCUSED INDEPENDENT REVIEW
**Task ID:** `PRE-B027-0 FOCUSED INDEPENDENT REVIEW`
**Date:** 2026-08-29

---

## Purpose

PRE-B027-0 is complete on `governance/pre-b027-continuity-reconciliation`. It freezes the B-027 AI
Workforce / Work-Control Governance architecture and fixes the continuity `described_head` self-reference
defect. The next gate is a focused independent review before controlled human push/PR/merge.

## Preconditions satisfied

- `PROMPT-009` / `PROMPT-010` governance is merged to `main`.
- `main` HEAD is `283c1a1fdda012aab51b0164b4b16636e870f3b5`.
- Repository is `anox-software/anox-messenger`.
- `GITHUB_REMOTE_ACTIVITY_SAFETY.md` is binding.
- Remote-write authority remains `HUMAN-CONTROLLED REMOTE WRITE MODE`.
- B-017-Lite is merged to `main` and all five CI gates pass.
- `validate_continuity.py` enforces the new `described_head` semantics.
- `test_handoff_and_validator.py` includes focused negative tests.
- `docs/reports/PRE_B027_WORKFORCE_ARCHITECTURE_FREEZE.md` captures the frozen B-027 architecture.
- `docs/authority/B_FREEZE_REGISTRY.md` references the B-027 freeze report.
- No `docs/workforce/**` or `workforce/**` files have been created.
- No Android, Rust/crypto, CI, dependency, or product code changes are present.

## Scope of the next task

- Independently review `tools/continuity/validate_continuity.py` for the new `described_head` semantics
  and metadata-only advancement logic.
- Independently review `tools/continuity/test_handoff_and_validator.py` for the new negative tests,
  including the self-reference regression test.
- Independently review `docs/continuity/HANDOFF_WORKFLOW.md` HEAD semantics documentation.
- Independently review `docs/reports/PRE_B027_WORKFORCE_ARCHITECTURE_FREEZE.md` for correctness and
  completeness against the approved PRE-B027-A/B/C/D architecture.
- Independently review the metadata-only allowlist in `validate_continuity.py` for security boundary
  correctness.
- Run `python3 tools/continuity/validate_continuity.py --mode live` and confirm PASS.
- Run `python3 tools/continuity/test_handoff_and_validator.py` and confirm PASS.
- Run `python3 tools/continuity/generate_handoff.py` and confirm a clean Handoff ZIP is produced.
- Run `python3 -m unittest tools/continuity.test_handoff_and_validator` and confirm PASS.
- Run `git diff --check` and confirm PASS.
- If all checks pass, declare `PRE-B027-0` ready for controlled human PR/merge.

## Out of scope

- GitHub account/repository migration (already complete).
- Credential or remote URL configuration.
- Pushing, PR creation, or remote automation.
- B-027 Workforce runtime implementation.
- B-004 backend implementation.
- B-005 database/RLS implementation.
- Any Messenger product code change.

## Next authorized sequence after this review

1. If review PASS, preserve the clean local `governance/pre-b027-continuity-reconciliation` branch.
2. Human-controlled remote actions: create PR, merge to `main`.
3. After merge: `B-027 IMPLEMENTATION AUTHORIZED`.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
