# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-08-31
**Latest material event:** `ANOX-EVENT-0023` — B027-A AI Workforce / Work-Control Governance Foundation
**Memory schema:** M2B-v1

<!-- ANOX_EVENT: ANOX-EVENT-0021 -->
<!-- ANOX_EVENT: ANOX-EVENT-0022 -->
<!-- ANOX_EVENT: ANOX-EVENT-0023 -->
## Repository truth

- Branch: `governance/b027-workforce-foundation`
- **Current HEAD:** `83259e77082150adef6585b3409e062f850a5abc` (B027-A AI Workforce / Work-Control Governance Foundation)
- **Canonical repository:** `https://github.com/anox-software/anox-messenger`
- **Legacy repository:** `https://github.com/anox-admin/ax-messenger.git` (historical provenance only)
- **Merged baseline branch:** `main`
- **Latest merge to baseline:** `9bbd4ea185e4149a9ac144d4f7b35d43f35f040f` (new `anox-software/anox-messenger` PR #4)
- **Previous baseline HEAD:** `3e127c7a80e9835ea5631e21c10f066401a884dc` (PRE-B027-0R2, PR #3)
- **Foundation baseline tag:** `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- **CONTINUITY-001:** ACCEPTED
- **Current effective gate:** `B-027 AI WORKFORCE / WORK-CONTROL GOVERNANCE IMPLEMENTATION`
- **Current authorized task:** `B027-A AI WORKFORCE / WORK-CONTROL GOVERNANCE FOUNDATION — COMPLETED`
- **Open blockers:** NONE
- **Next authorized task:** `B027-B — STATE/GATE RESOLVER + ROLE CONTRACTS + TASK/PROMPT/COMMUNICATION RUNTIME`
- **Latest main CI:** B-017-Lite 5/5 PASS; continuity PASS; B027-A validator PASS; B027-A adversarial tests 20/20 PASS

## Architecture / governance

- B-001…B-023: frozen/defined.
- B-024 Final MAIN Consistency Audit: PASS.
- B-025 New-Chat Handoff: COMPLETE.
- B-026 Continuous Development Governance: FROZEN.
- B-027-A AI Workforce / Work-Control Governance Foundation: IMPLEMENTED at `83259e7...`.
- B-027-B / B-027-C: DEFERRED.

## Functional progress

Approximately **33%**. Architecture freezes and governance do not count as user-facing
messenger functionality; the percentage reflects merged B-002 and B-003 client foundations.

## Merged milestones (summary)

| Event | Date | Task | Merge / Head | Status |
|---|---|---|---|---|
| ANOX-EVENT-0002 | 2026-08-23 | PROMPT-008 MERGE | `e7ee54a...` | B-003 merged foundation |
| ANOX-EVENT-0009 | 2026-08-29 | REMOTE-MIGRATION-SYNC-001 | `043e874...` | new canonical main reconciled |
| ANOX-EVENT-0010 | 2026-08-29 | B-017-Lite | `283c1a1...` | 5/5 CI PASS, 7/7 findings closed |
| ANOX-EVENT-0014 | 2026-08-30 | PRE-B027-0R2 merge | `3e127c7...` | PR #3 merged |
| ANOX-EVENT-0020 | 2026-08-30 | CML V1 merge | `9bbd4ea...` | PR #4 human-merged |
| ANOX-EVENT-0021 | 2026-08-30 | B-027 authorized | `9bbd4ea...` | effective gate transition |
| ANOX-EVENT-0022 | 2026-08-30 | PRE-B027-M2B | `c2d3a04...` | project memory integrity |
| ANOX-EVENT-0023 | 2026-08-31 | B027-A | `83259e7...` | workforce foundation |

## Implemented / accepted at implemented-test level

- Rust vodozemac crypto foundation with real session round-trip and negative tests.
- Android Keystore P-256/ES256 Device Auth key (B-002 client foundation).
- Account/license registration state machine with `CommitArmed` durable guard (B-003 client foundation).
- AES-GCM local state protection with Android Keystore-wrapped state key.
- Versioned state envelope, atomic file persistence, local wipe APIs.
- CI / supply-chain security foundation (B-017-Lite).
- Canonical Merge Lifecycle V1 and continuity governance (B-026/M1R3).
- B027-A AI Workforce / Work-Control Governance Foundation.

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
