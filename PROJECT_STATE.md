# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-08-31
**Latest material event:** `ANOX-EVENT-0027` — B027-C Final B027 Integration / Integrity / System Adversarial Validation + Handoff + Cold Recovery + Final Pre-Product Audit Preparation
**Memory schema:** M2B-v1

<!-- ANOX_EVENT: ANOX-EVENT-0021 -->
<!-- ANOX_EVENT: ANOX-EVENT-0022 -->
<!-- ANOX_EVENT: ANOX-EVENT-0023 -->
<!-- ANOX_EVENT: ANOX-EVENT-0024 -->
<!-- ANOX_EVENT: ANOX-EVENT-0025 -->
<!-- ANOX_EVENT: ANOX-EVENT-0026 -->
<!-- ANOX_EVENT: ANOX-EVENT-0027 -->

## Repository truth

- Branch: `governance/b027-final-integration`
- **Current HEAD:** `176cebca7a693282de09f0ea08169c6d1f485dff` (B027-C INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027 INTEGRATION)
- **Canonical repository:** `https://github.com/anox-software/anox-messenger`
- **Legacy repository:** `https://github.com/anox-admin/ax-messenger.git` (historical provenance only)
- **Merged baseline branch:** `main`
- **Latest merge to baseline:** `aca7a8364a89423173440997ac01865c63552ca0` (B027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime, new `anox-software/anox-messenger` PR #7)
- **Previous baseline HEAD:** `38b619e55082086989bb0713cad42c4c53be14ab` (B027-A AI Workforce / Work-Control Governance Foundation, PR #6)
- **Foundation baseline tag:** `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- **CONTINUITY-001:** ACCEPTED
- **Current effective gate:** `B027-C — INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027 INTEGRATION`
- **Current authorized task:** `B027-C — INTEGRITY VALIDATOR + ADVERSARIAL SYSTEM TESTS + HANDOFF + COLD RECOVERY + FINAL B027 INTEGRATION — IN PROGRESS; NEXT: FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`
- **Open blockers:** NONE
- **Next authorized task:** `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT` (`AUDIT-MAIN-ARCHITECTURE`)
- **Product status:** `BLOCKED` pending `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`; no product/CI changes until audit is authorized.
- **Latest main CI:** B-017-Lite 5/5 PASS; continuity PASS; B027-A validator PASS; B027-A adversarial tests 20/20 PASS; B027-B validator PASS; B027-B adversarial tests 48/48 PASS; B027-C integrity validator PASS; B017 policy validator 35/35 PASS; Rust 15/15 PASS

## Architecture / governance

- B-001…B-023: frozen/defined.
- B-024 Final MAIN Consistency Audit: PASS.
- B-025 New-Chat Handoff: COMPLETE.
- B-026 Continuous Development Governance: FROZEN.
- B-027-A AI Workforce / Work-Control Governance Foundation: MERGED at `38b619e...`.
- B-027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime: MERGED at `aca7a8...`.
- B-027-C / B-027-D: B027-C IMPLEMENTED at `176ceb...`; product blocked pending `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`; B027-D DEFERRED.

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
