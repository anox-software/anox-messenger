# CURRENT HANDOFF — anoX Messenger V1

Handoff version: MAINARCH-RETEST-03-INGEST — CANONICAL RETEST INGESTION, VERIFIED FIX-03 FINDING CLOSURE AND VALIDATOR HARDENING COMPLETE
Date: 2026-09-06
Delivery branch: `audit/mainarch-retest-03-ingest`
Described HEAD: `876e63565942c65df738afc5f4578a6b16a331b0`
Main baseline HEAD: `88ea18c9b7078c376ee027d0cacc4d4f147ebbf5`
Working tree: CLEAN
Effective gate: MAINARCH-RETEST-03-INGEST — CANONICAL RETEST RESULT INGESTION, VERIFIED FINDING CLOSURE AND TARGETED VALIDATOR HARDENING
Pre-merge gate: MAINARCH-RETEST-03-INGEST — CANONICAL RETEST RESULT INGESTION, VERIFIED FINDING CLOSURE AND TARGETED VALIDATOR HARDENING
Post-merge gate: LEGACY-AUDIT-B002 — DEVICE AUTHENTICATION LEGACY VERIFICATION (FIRST SESSION OF THE LEGACY / BUILD / HARDWARE VERIFICATION PHASE)

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
- Delivery branch: `audit/mainarch-retest-03-ingest`
- Current work branch: `audit/mainarch-retest-03-ingest`
- Current HEAD: `876e63565942c65df738afc5f4578a6b16a331b0`
- Main baseline HEAD: `88ea18c9b7078c376ee027d0cacc4d4f147ebbf5`
- Working tree: CLEAN
- Latest material event: `ANOX-EVENT-0034`

## Latest completed work

- `MAINARCH-RETEST-03` PASS ingested: 5 findings (`ANOX-MAINARCH-011`, `024`, `026`, `027`, `036`) verified and Closed.
- `MAINARCH-RETEST-03-INGEST` on branch `audit/mainarch-retest-03-ingest`: canonical retest record, verified finding closures, `MAINARCH-FIX-03` validator hardened, `validate_mainarch_retest03_ingest.py` added.
- **MAIN ARCHITECTURE AUDIT = COMPLETE; MAIN ARCHITECTURE REMEDIATION PHASE = COMPLETE.**
- MAIN findings: 30 Closed, 6 remaining Open (`ANOX-MAINARCH-013`, `018`, `019`, `023`, `030`, `031` — deferred legacy/build/hardware items per canonical plan). No finding remains Ready For Retest.

## Current open work

- `LEGACY / BUILD / HARDWARE VERIFICATION` phase — first session `LEGACY-AUDIT-B002` per `docs/workforce/audits/legacy-audit-plan.json` (planned, pending human authorization).

## Trust-boundary / milestone flags

- `ANOX-MAINARCH-003` (server ↔ DB/RLS), `ANOX-MAINARCH-007` (server ↔ backup/PITR), and `ANOX-MAINARCH-024` (signing/release custody + incident-response trust boundary) remain flagged (`PENDING`) for the next Security Architecture milestone review. Finding closure means architecture remediation verified, not milestone security audit complete.

## Product status

- `BLOCKED_PENDING_FINAL_AUDIT`.
- `B-004` backend: NOT STARTED.
- `B-005` DB/RLS: NOT STARTED.
- No Product/Rust/CI/DB/backend implementation changed.
- `ANOX-MAINARCH-018` physical GrapheneOS/StrongBox verification remains `PHYSICAL_VERIFICATION_REQUIRED`.

## Next task

`LEGACY-AUDIT-B002` — first required specialized verification session per the canonical legacy audit plan; start only with explicit human authorization.
