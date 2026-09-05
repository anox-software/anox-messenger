# CURRENT HANDOFF — anoX Messenger V1

Handoff version: MAINARCH-RETEST-02-INGEST — CANONICAL RETEST RESULT INGESTION, VERIFIED FINDING CLOSURE AND TARGETED VALIDATOR HARDENING COMPLETE
Date: 2026-09-05
Delivery branch: `audit/mainarch-retest-02-ingest`
Described HEAD: `8ee4ccaa33e4ba134a8b85ab87fef164ffed447d`
Main baseline HEAD: `739ea1c36c3d6f8eedb9a315fc6fba5173a82289`
Working tree: CLEAN
Effective gate: MAINARCH-RETEST-02-INGEST — CANONICAL RETEST RESULT INGESTION, VERIFIED FINDING CLOSURE AND TARGETED VALIDATOR HARDENING
Pre-merge gate: MAINARCH-RETEST-02-INGEST — CANONICAL RETEST RESULT INGESTION, VERIFIED FINDING CLOSURE AND TARGETED VALIDATOR HARDENING
Post-merge gate: MAINARCH-FIX-03 — TRACEABILITY / TEST MATRIX / RELEASE-GOVERNANCE ARCHITECTURE REMEDIATION

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
- Delivery branch: `audit/mainarch-retest-02-ingest`
- Current work branch: `audit/mainarch-retest-02-ingest`
- Current HEAD: `8ee4ccaa33e4ba134a8b85ab87fef164ffed447d`
- Main baseline HEAD: `739ea1c36c3d6f8eedb9a315fc6fba5173a82289`
- Working tree: CLEAN
- Latest material event: `ANOX-EVENT-0032`

## Latest completed work

- `MAINARCH-RETEST-02` PASS: independent read-only targeted delta retest of the 8 MAINARCH-FIX-02 findings at canonical SHA `739ea1c36c3d6f8eedb9a315fc6fba5173a82289`; 8/8 remediated, 0 failures, 0 regressions, no Claude.
- `MAINARCH-RETEST-02-INGEST` complete: retest result recorded in `docs/workforce/registries/audits.jsonl`; the 8 verified findings (`ANOX-MAINARCH-003`, `007`, `008`, `009`, `010`, `015`, `016`, `017`) are `Closed` with preserved severities and original evidence.
- MAIN findings: 25 Closed, 11 remaining Open (`ANOX-MAINARCH-011`, `013`, `018`, `019`, `023`, `024`, `026`, `027`, `030`, `031`, `036`).
- `tools/audit/validate_mainarch_fix02.py` hardened (real severity check, pinned-SHA post-merge delivery scope check, semantic spot-checks) plus adversarial tests `tools/audit/test_mainarch_fix02.py` and ingest validator `tools/audit/validate_mainarch_retest02_ingest.py`.

## Current open work

- `MAINARCH-FIX-03` — traceability / test matrix / release-governance architecture remediation (planned, pending human authorization).

## Trust-boundary / milestone flags

- `ANOX-MAINARCH-003` (server ↔ DB/RLS) and `ANOX-MAINARCH-007` (server ↔ backup/PITR) remain flagged for the next Security Architecture milestone review. Finding closure means architecture remediation verified, not milestone security audit complete.

## Product status

- `BLOCKED_PENDING_FINAL_AUDIT`.
- `B-004` backend: NOT STARTED.
- `B-005` DB/RLS: NOT STARTED.
- No Product/Rust/CI/DB/backend implementation changed.

## Next task

`MAINARCH-FIX-03` — start only with explicit human authorization.
