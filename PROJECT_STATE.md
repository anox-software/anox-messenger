# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-09-06
**Latest material event:** `ANOX-EVENT-0034` — MAINARCH-RETEST-03-INGEST completed; 5 findings Closed (total Closed 30, remaining Open 6); MAIN architecture remediation phase COMPLETE
**Memory schema:** M2B-v1

<!-- ANOX_EVENT: ANOX-EVENT-0021 -->
<!-- ANOX_EVENT: ANOX-EVENT-0022 -->
<!-- ANOX_EVENT: ANOX-EVENT-0023 -->
<!-- ANOX_EVENT: ANOX-EVENT-0024 -->
<!-- ANOX_EVENT: ANOX-EVENT-0025 -->
<!-- ANOX_EVENT: ANOX-EVENT-0026 -->
<!-- ANOX_EVENT: ANOX-EVENT-0027 -->
<!-- ANOX_EVENT: ANOX-EVENT-0028 -->
<!-- ANOX_EVENT: ANOX-EVENT-0029 -->
<!-- ANOX_EVENT: ANOX-EVENT-0030 -->
<!-- ANOX_EVENT: ANOX-EVENT-0031 -->
<!-- ANOX_EVENT: ANOX-EVENT-0032 -->
<!-- ANOX_EVENT: ANOX-EVENT-0033 -->
<!-- ANOX_EVENT: ANOX-EVENT-0034 -->

## Repository truth

- Branch: `audit/mainarch-retest-03-ingest`
- **Current HEAD:** `876e63565942c65df738afc5f4578a6b16a331b0` (MAINARCH-RETEST-03-INGEST SUBSTANTIVE)
- **Canonical repository:** `https://github.com/anox-software/anox-messenger`
- **Legacy repository:** `https://github.com/anox-admin/ax-messenger.git` (historical provenance only)
- **Merged baseline branch:** `main`
- **Latest merge to baseline:** `0a4910eab1a92622383721100879cda46f924ca0` still canonical; MAINARCH-FIX-01 is a delivery-branch remediation, not yet merged. (B027-C Final B027 Integration / Integrity / System Adversarial Validation + Handoff + Cold Recovery + Final Pre-Product Audit Preparation, PR #8)
- **Previous baseline HEAD:** `aca7a8364a89423173440997ac01865c63552ca0` (B027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime, PR #7)
- **Foundation baseline tag:** `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- **CONTINUITY-001:** ACCEPTED
- **Current effective gate:** `MAINARCH-RETEST-03-INGEST — CANONICAL RETEST RESULT INGESTION, VERIFIED FINDING CLOSURE AND TARGETED VALIDATOR HARDENING`
- **Current authorized task:** `MAINARCH-RETEST-03-INGEST COMPLETE; 5 findings Closed; MAIN 30/6; NEXT: LEGACY-AUDIT-B002 (LEGACY / BUILD / HARDWARE VERIFICATION phase)`
- **Open blockers:** 6 deferred MAIN findings (013, 018, 019, 023, 030, 031) + required legacy/build/hardware verification before product gate may advance
- **Previously completed:** `MAINARCH-FIX-01` + `MAINARCH-RETEST-01` (17 findings Closed); `MAINARCH-FIX-02` + `MAINARCH-RETEST-02` (8 findings Closed); `MAINARCH-FIX-03` + `MAINARCH-RETEST-03` (5 findings Closed); **MAIN ARCHITECTURE AUDIT + REMEDIATION PHASE COMPLETE**
- **Next authorized task:** `LEGACY-AUDIT-B002 — DEVICE AUTHENTICATION LEGACY VERIFICATION` (first session per `docs/workforce/audits/legacy-audit-plan.json`; START WHEN HUMAN ASSIGNS)
- **Product status:** `BLOCKED` pending `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`; no product/CI changes until all final/legacy audits are complete and the human final gate is recorded.


## Architecture / governance

- B-001…B-023: frozen/defined.
- B-025 V1.3: FROZEN (traceability / test-matrix / release-governance / implementation-readiness).
- B-024 Final MAIN Consistency Audit: PASS.
- B-025 New-Chat Handoff: COMPLETE.
- B-026 Continuous Development Governance: FROZEN.
- B-027-A AI Workforce / Work-Control Governance Foundation: MERGED at `38b619e...`.
- B-027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime: MERGED at `aca7a8...`.
- B-027-C / B-027-D: B027-C MERGED at `0a4910e...` (PR #8); AUDIT-MAIN-ARCHITECTURE findings frozen, merged to main, and sealed; MAINARCH-RETEST-01-INGEST completed at `ec71127b51c0a4d33d18f14f2bf9c5e8209026da` on `audit/mainarch-retest-01-ingest`; 17 findings Closed; product blocked pending `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`; B027-D DEFERRED.

## ANOX-EVENT-0033 — MAINARCH-FIX-03 Traceability / Test Matrix / Release-Governance / Implementation-Readiness Architecture Remediation

- **Date:** 2026-09-05
- **Branch:** `remediation/mainarch-fix-03-traceability-release-governance`
- **Substantive HEAD:** `4573b64dcc997aaaee8e81675a871201627d454e`
- **Result:** 5 findings (`ANOX-MAINARCH-011`, `024`, `026`, `027`, `036`) moved to `Ready For Retest`; none `Closed`. 25 MAIN findings remain `Closed`; 11 remain Open.
- **Artifacts:** `docs/authority/B025_MANDATORY_AMENDMENTS_V1_3.md`; `docs/security/SECURITY_INVARIANT_TRACEABILITY.md`; `docs/workforce/registries/security_invariant_traceability.jsonl`; `docs/workforce/registries/b021_verification_matrix.jsonl`; `docs/workforce/registries/implementation_readiness.json`; `tools/audit/validate_mainarch_fix03.py`; `tools/audit/test_mainarch_fix03.py`; updated `findings.jsonl`, `WORKFORCE_STATE.json`, Master Audit Report.
- **Product status:** remains `BLOCKED_PENDING_FINAL_AUDIT`.
- **Next:** `MAINARCH-RETEST-03` — targeted delta retest of traceability / release-governance findings (pending human authorization).

## Functional progress

Approximately **33%**. Architecture freezes and governance do not count as user-facing
messenger functionality; the percentage reflects merged B-002 and B-003 client foundations.

## Merged milestones (summary)

||| Event | Date | Task | Merge / Head | Status |
||---|---|---|---|---|---|
||| ANOX-EVENT-0002 | 2026-08-23 | PROMPT-008 MERGE | `e7ee54a...` | B-003 merged foundation |
||| ANOX-EVENT-0009 | 2026-08-29 | REMOTE-MIGRATION-SYNC-001 | `043e874...` | new canonical main reconciled |
||| ANOX-EVENT-0010 | 2026-08-29 | B-017-Lite | `283c1a1...` | 5/5 CI PASS, 7/7 findings closed |
||| ANOX-EVENT-0014 | 2026-08-30 | PRE-B027-0R2 merge | `3e127c7...` | PR #3 merged |
||| ANOX-EVENT-0020 | 2026-08-30 | CML V1 merge | `9bbd4ea...` | PR #4 human-merged |
||| ANOX-EVENT-0021 | 2026-08-30 | B-027 authorized | `9bbd4ea...` | effective gate transition |
||| ANOX-EVENT-0022 | 2026-08-30 | PRE-B027-M2B | `c2d3a04...` | project memory integrity |
||| ANOX-EVENT-0023 | 2026-08-31 | B027-A | `83259e7...` | workforce foundation |
||| ANOX-EVENT-0024 | 2026-08-31 | B027-A merge | `38b619e...` | B027-A merged to main |
||| ANOX-EVENT-0025 | 2026-08-31 | B027-B | `76849b1...` | work-control runtime |
||| ANOX-EVENT-0026 | 2026-08-31 | B027-B merge | `aca7a8...` | B027-B merged to main |
||| ANOX-EVENT-0027 | 2026-08-31 | B027-C | `176ceb...` | final B027 integration |
|||| ANOX-EVENT-0028 | 2026-08-31 | AUDIT-MAIN-ARCHITECTURE | `93c4d3c12da2...` | findings freeze, 36 findings, 13 HIGH |

## Implemented / accepted at implemented-test level

- Rust vodozemac crypto foundation with real session round-trip and negative tests.
- Android Keystore P-256/ES256 Device Auth key (B-002 client foundation).
- Account/license registration state machine with `CommitArmed` durable guard (B-003 client foundation).
- AES-GCM local state protection with Android Keystore-wrapped state key.
- Versioned state envelope, atomic file persistence, local wipe APIs.
- CI / supply-chain security foundation (B-017-Lite).
- Canonical Merge Lifecycle V1 and continuity governance (B-026/M1R3).
- B027-A AI Workforce / Work-Control Governance Foundation.
- B027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime.
- B027-C INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027 INTEGRATION.

## Not implemented

B-004 backend service, B-005 database/RLS, B-006 server key distribution, B-007 production API,
B-008 messaging/sync, B-009 SQLCipher messenger DB/outbox, B-010 contacts/SAS product flow,
B-011 push/offline jobs, B-012 attachments, B-013 production server lifecycle, and remaining
product/infrastructure/release/audit gates.

## Project Memory Integrity V1

- `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl`: append-only material event ledger.
- `docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md`: event→surface update matrix.
- `tools/continuity/validate_continuity.py`: enforces `PROJECT_MEMORY_FRESHNESS`.
- `FORTSCHRITT.md`: chronological human history with `<!-- ANOX_EVENT: ... -->` markers.
- Full historical detail, test counts, and finding status are recorded in the ledger and
  `FORTSCHRITT.md`; this file is the current human summary only.

<!-- ANOX_EVENT: ANOX-EVENT-0031 -->

## ANOX-EVENT-0031 — MAINARCH-FIX-02 Server/DB/API/OTK/Retention/Privacy Architecture Remediation

**Branch:** `remediation/mainarch-fix-02-server-contracts`
**Substantive HEAD:** `568c8083a3e56058fcb6e5076a7fe1ebc15c384b`
**Date:** 2026-09-04

- MAINARCH-FIX-02 complete.
- `docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md` freezes V1.2 server/DB/RLS/API/OTK/retention/privacy contracts.
- 8 findings (`ANOX-MAINARCH-003`, `007`, `008`, `009`, `010`, `015`, `016`, `017`) moved to `Ready For Retest`.
- `ANOX-MAINARCH-003` and `ANOX-MAINARCH-007` remain flagged for milestone Security Architecture review.
- Product development remains `BLOCKED_PENDING_FINAL_AUDIT`.
- No product/Rust/CI/DB/backend implementation changed.
- Next task: `MAINARCH-RETEST-02` (pending human authorization).

<!-- ANOX_EVENT: ANOX-EVENT-0032 -->
<!-- ANOX_EVENT: ANOX-EVENT-0033 -->

## ANOX-EVENT-0032 — MAINARCH-RETEST-02-INGEST Verified Finding Closure + Validator Hardening

**Branch:** `audit/mainarch-retest-02-ingest`
**Substantive HEAD:** `8ee4ccaa33e4ba134a8b85ab87fef164ffed447d`
**Date:** 2026-09-05

- MAINARCH-RETEST-02 PASS ingested: 8/8 findings verified at canonical SHA `739ea1c36c3d6f8eedb9a315fc6fba5173a82289`; no failures, no regressions, no Claude.
- Findings `ANOX-MAINARCH-003`, `007`, `008`, `009`, `010`, `015`, `016`, `017` are `Closed` with severities and original evidence preserved. MAIN Closed total: 25; remaining Open: 11.
- `ANOX-MAINARCH-003` and `ANOX-MAINARCH-007` milestone Security Architecture review remains pending (closure = architecture remediation verified).
- `tools/audit/validate_mainarch_fix02.py` hardened (expected-severity map + report cross-check; pinned-SHA recorded-delivery scope check; semantic spot-checks) with adversarial tests and `tools/audit/validate_mainarch_retest02_ingest.py` added.
- Product development remains `BLOCKED_PENDING_FINAL_AUDIT`.
- No product/Rust/CI/DB/backend/architecture changes.
- Next task: `MAINARCH-FIX-03` (pending human authorization).

## ANOX-EVENT-0034 — MAINARCH-RETEST-03-INGEST Verified Finding Closure + Remediation-Phase Completion + Validator Hardening

**Branch:** `audit/mainarch-retest-03-ingest`
**Substantive HEAD:** `876e63565942c65df738afc5f4578a6b16a331b0`
**Date:** 2026-09-06

- `MAINARCH-RETEST-03` PASS ingested: 5/5 findings verified at canonical SHA `88ea18c9b7078c376ee027d0cacc4d4f147ebbf5`; no failures, no regressions, no Claude.
- Findings `ANOX-MAINARCH-011`, `024`, `026`, `027`, `036` are `Closed` with severities and original evidence preserved. MAIN Closed total: 30; remaining Open: 6 (`013`, `018`, `019`, `023`, `030`, `031`). No finding remains `Ready For Retest`.
- **MAIN ARCHITECTURE AUDIT = COMPLETE; MAIN ARCHITECTURE REMEDIATION PHASE = COMPLETE**; Final Pre-Product Audit remains IN PROGRESS.
- `ANOX-MAINARCH-003`, `007`, `024` milestone Security Architecture review remains `PENDING` (machine-readable `milestone_security_review` field; closure = architecture remediation verified).
- `ANOX-MAINARCH-018` physical GrapheneOS/StrongBox verification remains `PHYSICAL_VERIFICATION_REQUIRED`.
- `tools/audit/validate_mainarch_fix03.py` hardened (verification-ID cross-check; pinned-SHA recorded-delivery scope; governance cross-references) with 26 adversarial tests and `tools/audit/validate_mainarch_retest03_ingest.py` added.
- Product development remains `BLOCKED_PENDING_FINAL_AUDIT`.
- No product/Rust/CI/DB/backend/architecture changes.
- Next task: `LEGACY-AUDIT-B002` — first session of the LEGACY / BUILD / HARDWARE VERIFICATION phase per `docs/workforce/audits/legacy-audit-plan.json` (pending human authorization).