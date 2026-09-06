# CURRENT HANDOFF — anoX Messenger V1

Handoff version: LEGACY-AUDIT-SET-FREEZE — SIX-SESSION LEGACY AUDIT CONSOLIDATION AND CANONICAL FINDINGS FREEZE
Date: 2026-09-07
Delivery branch: `audit/legacy-audit-set-freeze-consolidation`
Described HEAD: `1ffe6e7c2ee387cb925d74c8ba9a3a672bd9d27a`
Main baseline HEAD: `f245dc429a9e4bd10f51692eb452d03ccb9a6749`
Working tree: CLEAN
Effective gate: LEGACY-FIX-01 — FOUNDATION STATE / REGISTRATION / CRYPTO SAFETY REMEDIATION
Pre-merge gate: LEGACY-AUDIT-SET-FREEZE — CONSOLIDATE SIX LEGACY AUDITS ON FROZEN BASELINE
Post-merge gate: LEGACY-FIX-01 — FOUNDATION STATE / REGISTRATION / CRYPTO SAFETY REMEDIATION

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
- Delivery branch: `audit/legacy-audit-set-freeze-consolidation`
- Current work branch: `audit/legacy-audit-set-freeze-consolidation`
- Current HEAD: `1ffe6e7c2ee387cb925d74c8ba9a3a672bd9d27a`
- Main baseline HEAD: `f245dc429a9e4bd10f51692eb452d03ccb9a6749`
- Working tree: CLEAN
- Latest material event: `ANOX-EVENT-0035`

## Latest completed work

- `LEGACY-AUDIT-SET-FREEZE` PASS WITH FINDINGS: six legacy audits 6/6 complete.
- `LEGACY-AUDIT-SET-FREEZE` on branch `audit/legacy-audit-set-freeze-consolidation`: canonical consolidation, 7 promoted Legacy findings, 6 revalidated MAIN findings, disposition map, Class-A remediation batch, consolidated report, and validator.
- **MAIN ARCHITECTURE AUDIT = COMPLETE; MAIN ARCHITECTURE REMEDIATION PHASE = COMPLETE; LEGACY AUDIT SET = 6/6 COMPLETE.**
- MAIN + Legacy findings: 30 Closed, 13 Open (6 MAIN + 7 Legacy). No finding remains Ready For Retest.

## Current open work

- `LEGACY-FIX-01 — FOUNDATION STATE / REGISTRATION / CRYPTO SAFETY REMEDIATION` — dependency-sorted remediation of Class-A legacy blockers.
- Class-A blockers: `ANOX-MAINARCH-019`, `023`, `031`, `ANOX-LEGACY-ANDROIDSEC-001`, `ANOX-LEGACY-CRYPTO-005`, `ANOX-LEGACY-INTEGRATION-001`, `ANOX-LEGACY-INTEGRATION-002`, `ANOX-LEGACY-INTEGRATION-003`.

## Trust-boundary / milestone flags

- `ANOX-MAINARCH-003` (server ↔ DB/RLS), `ANOX-MAINARCH-007` (server ↔ backup/PITR), and `ANOX-MAINARCH-024` (signing/release custody + incident-response trust boundary) remain flagged (`PENDING`) for the next Security Architecture milestone review. Finding closure means architecture remediation verified, not milestone security audit complete.

## Product status

- `BLOCKED_PENDING_FINAL_AUDIT`.
- `B-004` backend: NOT STARTED.
- `B-005` DB/RLS: NOT STARTED.
- No Product/Rust/CI/DB/backend implementation changed.
- `ANOX-MAINARCH-018` physical GrapheneOS/StrongBox verification remains `PHYSICAL_VERIFICATION_REQUIRED`.

## Next task

`LEGACY-FIX-01` — remediate Class-A legacy foundation blockers; start only with explicit human authorization.
