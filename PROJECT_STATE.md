# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-09-02
**Latest material event:** `ANOX-EVENT-0030` — MAINARCH-RETEST-01-INGEST completed; 17 findings Closed
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

## Repository truth

- Branch: `audit/mainarch-retest-01-ingest`
- **Current HEAD:** `ec71127b51c0a4d33d18f14f2bf9c5e8209026da` (AUDIT-MAIN-ARCHITECTURE FINDINGS FREEZE)
- **Canonical repository:** `https://github.com/anox-software/anox-messenger`
- **Legacy repository:** `https://github.com/anox-admin/ax-messenger.git` (historical provenance only)
- **Merged baseline branch:** `main`
- **Latest merge to baseline:** `0a4910eab1a92622383721100879cda46f924ca0` still canonical; MAINARCH-FIX-01 is a delivery-branch remediation, not yet merged. (B027-C Final B027 Integration / Integrity / System Adversarial Validation + Handoff + Cold Recovery + Final Pre-Product Audit Preparation, PR #8)
- **Previous baseline HEAD:** `aca7a8364a89423173440997ac01865c63552ca0` (B027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime, PR #7)
- **Foundation baseline tag:** `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- **CONTINUITY-001:** ACCEPTED
- **Current effective gate:** `MAINARCH-FIX-02 — SERVER / DATABASE / RLS / API / OTK / RETENTION ARCHITECTURE REMEDIATION`
- **Current authorized task:** `MAINARCH-RETEST-01-INGEST COMPLETE; 17 findings Closed; NEXT: MAINARCH-FIX-02`
- **Open blockers:** MAINARCH-FIX-02 required before product gate may advance
- **Current authorized task:** `MAINARCH-FIX-01` — AUTHORITY / SOURCE-OF-TRUTH / B003 / AUDIT-GATE ARCHITECTURE REMEDIATION (COMPLETE)
- **Next authorized task:** `MAINARCH-FIX-02 — SERVER / DATABASE / RLS / API / OTK / RETENTION ARCHITECTURE REMEDIATION` (START WHEN HUMAN ASSIGNS)
- **Product status:** `BLOCKED` pending `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`; no product/CI changes until all final/legacy audits are complete and the human final gate is recorded.
- **Latest main CI:** B-017-Lite 5/5 PASS; continuity PASS; B027-A validator PASS; B027-A adversarial tests 20/20 PASS; B027-B validator PASS; B027-B adversarial tests 48/48 PASS; B027-C integrity validator PASS; B017 policy validator 35/35 PASS; Rust 15/15 PASS

## Architecture / governance

- B-001…B-023: frozen/defined.
- B-024 Final MAIN Consistency Audit: PASS.
- B-025 New-Chat Handoff: COMPLETE.
- B-026 Continuous Development Governance: FROZEN.
- B-027-A AI Workforce / Work-Control Governance Foundation: MERGED at `38b619e...`.
- B-027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime: MERGED at `aca7a8...`.
- B-027-C / B-027-D: B027-C MERGED at `0a4910e...` (PR #8); AUDIT-MAIN-ARCHITECTURE findings frozen, merged to main, and sealed; MAINARCH-RETEST-01-INGEST completed at `ec71127b51c0a4d33d18f14f2bf9c5e8209026da` on `audit/mainarch-retest-01-ingest`; 17 findings Closed; product blocked pending `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`; B027-D DEFERRED.

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
