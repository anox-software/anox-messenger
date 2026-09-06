# CURRENT HANDOFF — anoX Messenger V1

Handoff version: LEGACY-RETEST-01-INGEST — VERIFIED FINDING CLOSURE AND VALIDATOR HARDENING
Date: 2026-09-07
Delivery branch: `audit/legacy-retest-01-ingest`
Described HEAD: `f50dc79195c22a9f4e47ccc56f509908940632c2`
Main baseline HEAD: `3adf56c17936fdf60c864e4a26f1863243478f44`
Working tree: CLEAN
Effective gate: LEGACY-RETEST-01-INGEST — VERIFIED FINDING CLOSURE AND VALIDATOR HARDENING
Pre-merge gate: LEGACY-RETEST-01-INGEST — VERIFIED FINDING CLOSURE AND VALIDATOR HARDENING
Post-merge gate: AUDIT-WORKFORCE-ARCHITECTURE — B-027 WORKFORCE / WORK-CONTROL GOVERNANCE AUDIT (pending human authorization)

---

## Project

anoX Messenger V1 — closed-source native Android/GrapheneOS messenger with vodozemac/Olm E2EE.

## Architecture authority

Authority precedence is canonical in `docs/authority/AUTHORITY_INDEX.md`.
New sessions must read that file first.

## Current repository state

- Canonical repository: `https://github.com/anox-software/anox-messenger`
- Canonical SSH remote: `git@github.com:anox-software/anox-messenger.git`
- Legacy provenance remote: `https://github.com/anox-admin/ax-messenger.git` (historical only)
- Canonical branch: `main`
- Delivery branch: `audit/legacy-retest-01-ingest`
- Current work branch: `audit/legacy-retest-01-ingest`
- Current HEAD: `f50dc79195c22a9f4e47ccc56f509908940632c2`
- Main baseline HEAD: `3adf56c17936fdf60c864e4a26f1863243478f44`
- Working tree: CLEAN
- Latest material event: `ANOX-EVENT-0037`

## Latest completed work

- `LEGACY-RETEST-01` PASS: independent read-only targeted delta retest at canonical base `3adf56c` verified all 8 LEGACY-FIX-01 Class-A findings `PASS — REMEDIATED`; no FAIL/PARTIAL/REGRESSION/NOT-REVIEWABLE.
- `LEGACY-RETEST-01-INGEST`: exactly 8 findings Closed (`019`, `023`, `031`, `ANDROIDSEC-001`, `CRYPTO-005`, `INTEGRATION-001/002/003`) with immutable FIX-01 → RETEST-01 closure chains; 38 Closed / 5 Open; no finding remains Ready For Retest.
- Historical validators hardened to lifecycle-aware semantics (`tools/audit/lifecycle_legality.py`); new `validate_legacy_retest01_ingest.py` (23 checks) + 25 adversarial tests; structured Claude-trigger detection replaces prose substring matching.
- JVM unit tests 177/0; Rust tests 17/0; Android lint 0 errors / 0 NewApi; instrumentation NOT_RUN (device/emulator required).
- B027 integrity and continuity live validation PASS.

## Current open work

- `AUDIT-WORKFORCE-ARCHITECTURE` — second required Final Pre-Product audit session (B-027 workforce/work-control governance), Candidate `ANOX-TASK-WORKFORCEARCH001`, pending human authorization.

## Trust-boundary / milestone flags

- `ANOX-MAINARCH-003`, `007`, `024` remain `PENDING` milestone Security Architecture review.

## Product status

- `BLOCKED_PENDING_FINAL_AUDIT`.
- `B-004` backend: NOT_STARTED.
- `B-005` DB/RLS: NOT_STARTED.
- `ANOX-MAINARCH-018` physical verification remains `PHYSICAL_VERIFICATION_REQUIRED`.

## Next task

`AUDIT-WORKFORCE-ARCHITECTURE` — B-027 workforce/work-control governance audit per `docs/workforce/audits/final-audit-plan.json` (`ANOX-AUDIT-WORKFORCE-ARCH-001`); start only with explicit human authorization.
