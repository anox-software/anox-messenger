# CURRENT NEXT DEVIN TASK

**Status:** AWAITING INDEPENDENT DELTA RETEST
**Task ID:** `PRE-B027-0R2 INDEPENDENT DELTA RETEST`
**Date:** 2026-08-30

---

## Purpose

PRE-B027-0R2 targeted remediation is complete on `governance/pre-b027-continuity-reconciliation`. It
addresses the merge-commit payload visibility gap (ANOX-PREB027RREV-001) and completes the remediation
of `ANOX-PREB027REV-001`. Findings 002 through 010 remain independently closed. The next gate is an
independent Delta Retest by a reviewer that did not implement this remediation.

## Preconditions satisfied

- `PROMPT-009` / `PROMPT-010` governance is merged to `main`.
- `main` HEAD is `283c1a1fdda012aab51b0164b4b16636e870f3b5`.
- Repository is `anox-software/anox-messenger`.
- `GITHUB_REMOTE_ACTIVITY_SAFETY.md` is binding.
- Remote-write authority remains `HUMAN-CONTROLLED REMOTE WRITE MODE`.
- B-017-Lite is merged to `main` and all five CI gates pass.
- PRE-B027-0 initial implementation and independent focused review are complete.
- PRE-B027-0R remediation is committed at `1afb7a825aaecdf137238ff96f4a1c5cd0bf6242` and the original
  metadata-only sync at `99815a811b9c93710ee17b5485dbc307327fdf79`.
- PRE-B027-0R2 remediation is committed at `53e8d630bc078aa040a0f8f788046c3984472c51` and described by the
  current metadata-only sync.
- `validate_continuity.py` now enforces rename-aware and merge-aware metadata-only classification, archive
  required-key validation, non-self-referential baseline ancestry, missing described_head declarations, and a
  narrow metadata-only allowlist.
- `test_handoff_and_validator.py` includes adversarial regression tests for rename bypass, prefix boundary,
  archive required keys, missing head declarations, baseline ancestry, head precedence, and merge-commit
  payload visibility.
- `docs/reports/PRE_B027_WORKFORCE_ARCHITECTURE_FREEZE.md` contains the complete frozen architecture with
  Finding Security, Role≠Model, Gate Resolver, and Cold Recovery requirements.
- `docs/authority/AUTHORITY_INDEX.md` references the canonical authority precedence and updated freeze
  registry scope.
- No `docs/workforce/**` or `workforce/**` files have been created.
- No Android, Rust/crypto, CI, dependency, or product code changes are present.

## Scope of the next task

- Independently retest `ANOX-PREB027RREV-001` and the final closure of `ANOX-PREB027REV-001`.
- Run `python3 tools/continuity/validate_continuity.py --mode live` and confirm PASS.
- Run `python3 tools/continuity/test_handoff_and_validator.py` and confirm PASS.
- Run `python3 tools/continuity/generate_handoff.py` and confirm a clean Handoff ZIP is produced.
- Run `git diff --check 283c1a1...HEAD` and confirm PASS.
- Verify archive/Handoff validation against a freshly generated ZIP.
- If all checks pass, declare `PRE-B027-0R` ready for controlled human PR/merge.

## Out of scope

- GitHub account/repository migration (already complete).
- Credential or remote URL configuration.
- Pushing, PR creation, or remote automation.
- B-027 Workforce runtime implementation.
- B-004 backend implementation.
- B-005 database/RLS implementation.
- Any Messenger product code change.

## Next authorized sequence after this retest

1. If Delta Retest PASS, preserve the clean local `governance/pre-b027-continuity-reconciliation` branch.
2. Human-controlled remote actions: create PR, merge to `main`.
3. After merge: `B-027 IMPLEMENTATION AUTHORIZED`.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
