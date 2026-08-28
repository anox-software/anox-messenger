# CURRENT NEXT DEVIN TASK

**Status:** PROMPT-009 GOVERNANCE REMEDIATION / REVIEW
**Task ID:** PROMPT-009R
**Date:** 2026-08-28

---

## Purpose

PROMPT-009 introduced development security governance and handoff hardening. PROMPT-009R repairs
current-state contradictions, canonicalizes authority precedence, restores the frozen B-026 Devin
output contract, distinguishes live and archive validation modes, and proves a new handoff can be
reconstructed and reconciled.

## Preconditions satisfied

- B-002 (PR #4) and B-003 (PR #5) are merged into `main`.
- `main` baseline is `881c85ec726d8a32eb84b00955b6b9db7912fe1e`.
- B-003 merge commit is `e7ee54a713e08950c63cf2d61ec97931864b66bc`.
- PROMPT-009 is implemented on `governance/development-security-handoff-v1` (PR #6 open).
- Rust 15/15, JVM 161/161, Android instrumentation 62/62 all previously PASS.

## Architecture references

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`
- `docs/authority/CLOUD_AI_SECRET_PROTECTION.md`

## Scope

- Repair current-state contradictions (baseline, B-003 merge status, PR #5 status).
- Make `AUTHORITY_INDEX.md` the single canonical precedence source.
- Restore B-026 A–Q Devin output contract with PROMPT-009 subfields.
- Add live and archive validation modes to `validate_continuity.py`.
- Add baseline drift detection.
- Extend `generate_handoff.py` metadata for archive validation.
- Add 009R regression tests.
- Generate and verify a fresh handoff with both archive and live reconciliation tests.

## Out of scope

- B-004 backend implementation.
- B-005 PostgreSQL/RLS implementation.
- B-017-Lite implementation.
- B-027 Workforce implementation.
- Any Messenger product code change.

## Next authorized sequence after this remediation

1. Independent governance review of PROMPT-009/009R.
2. Merge PR #6 after review.
3. Continuity synchronization on `main` through reviewable workflow.
4. Fresh canonical handoff.
5. B-017-Lite (after governance is fully accepted/merged).
