# CURRENT HANDOFF — anoX Messenger V1

Handoff version: MAINARCH-FIX-03 — TRACEABILITY / TEST MATRIX / RELEASE-GOVERNANCE / IMPLEMENTATION-READINESS ARCHITECTURE REMEDIATION COMPLETE
Date: 2026-09-05
Delivery branch: `remediation/mainarch-fix-03-traceability-release-governance`
Described HEAD: `4573b64dcc997aaaee8e81675a871201627d454e`
Main baseline HEAD: `349509b63fc0f516a88bee69833b5caf8a244b9c`
Working tree: CLEAN
Effective gate: MAINARCH-FIX-03 — TRACEABILITY / TEST MATRIX / RELEASE-GOVERNANCE / IMPLEMENTATION-READINESS ARCHITECTURE REMEDIATION
Pre-merge gate: MAINARCH-FIX-03 — TRACEABILITY / TEST MATRIX / RELEASE-GOVERNANCE / IMPLEMENTATION-READINESS ARCHITECTURE REMEDIATION
Post-merge gate: MAINARCH-RETEST-03 — TARGETED DELTA RETEST OF TRACEABILITY / RELEASE-GOVERNANCE FINDINGS

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
- Delivery branch: `remediation/mainarch-fix-03-traceability-release-governance`
- Current work branch: `remediation/mainarch-fix-03-traceability-release-governance`
- Current HEAD: `4573b64dcc997aaaee8e81675a871201627d454e`
- Main baseline HEAD: `349509b63fc0f516a88bee69833b5caf8a244b9c`
- Working tree: CLEAN
- Latest material event: `ANOX-EVENT-0033`

## Latest completed work

- `MAINARCH-FIX-03` architecture remediation on branch `remediation/mainarch-fix-03-traceability-release-governance`: 5 findings (`ANOX-MAINARCH-011`, `024`, `026`, `027`, `036`) moved to `Ready For Retest`; no findings Closed.
- Artifacts: `docs/authority/B025_MANDATORY_AMENDMENTS_V1_3.md` (B-018/019/021/023 + traceability + evidence model + implementation-readiness model); `docs/security/SECURITY_INVARIANT_TRACEABILITY.md`; `docs/workforce/registries/security_invariant_traceability.jsonl` (35 invariants); `docs/workforce/registries/b021_verification_matrix.jsonl` (150 stable test IDs); `docs/workforce/registries/implementation_readiness.json`; `tools/audit/validate_mainarch_fix03.py`; `tools/audit/test_mainarch_fix03.py`.
- `MAINARCH-RETEST-02` PASS remains canonical: 8 findings (`003`, `007`, `008`, `009`, `010`, `015`, `016`, `017`) Closed.
- MAIN findings: 25 Closed, 11 remaining Open (the 6 deferred legacy/hardware findings + the 5 FIX-03 targets still Ready For Retest).

## Current open work

- `MAINARCH-RETEST-03` — targeted delta retest of traceability / release-governance / implementation-readiness findings (planned, pending human authorization).

## Trust-boundary / milestone flags

- `ANOX-MAINARCH-003` (server ↔ DB/RLS), `ANOX-MAINARCH-007` (server ↔ backup/PITR), and `ANOX-MAINARCH-024` (signing/release custody + incident-response trust boundary) flagged for the next Security Architecture milestone review. Finding Ready For Retest status means architecture remediation is prepared for retest, not that the milestone security audit is complete.

## Product status

- `BLOCKED_PENDING_FINAL_AUDIT`.
- `B-004` backend: NOT STARTED.
- `B-005` DB/RLS: NOT STARTED.
- No Product/Rust/CI/DB/backend implementation changed.

## Next task

`MAINARCH-RETEST-03` — start only with explicit human authorization.
