# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-09-07
**Latest material event:** `ANOX-EVENT-0037` — LEGACY-RETEST-01 PASS ingested; 8 Class-A findings Closed; next AUDIT-WORKFORCE-ARCHITECTURE
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
<!-- ANOX_EVENT: ANOX-EVENT-0035 -->
<!-- ANOX_EVENT: ANOX-EVENT-0036 -->
<!-- ANOX_EVENT: ANOX-EVENT-0037 -->

## Repository truth

- Branch: `audit/legacy-retest-01-ingest`
- **Current HEAD:** `f50dc79195c22a9f4e47ccc56f509908940632c2` (LEGACY-RETEST-01-INGEST SUBSTANTIVE)
- **Canonical repository:** `https://github.com/anox-software/anox-messenger`
- **Legacy repository:** `https://github.com/anox-admin/ax-messenger.git` (historical provenance only)
- **Canonical branch:** `main`
- **Merged baseline branch:** `main`
- **Latest merge to baseline:** `3adf56c17936fdf60c864e4a26f1863243478f44` (current main, PR #17 LEGACY-FIX-01)
- **Previous baseline HEAD:** `785e9a574fbbe072c454d8515a9a05022c282c46`
- **Foundation baseline tag:** `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- **CONTINUITY-001:** ACCEPTED
- **Current effective gate:** `LEGACY-RETEST-01-INGEST — VERIFIED FINDING CLOSURE AND VALIDATOR HARDENING`
- **Current authorized task:** `LEGACY-RETEST-01 COMPLETE + INGESTED; 8 Class-A findings Closed; NEXT: AUDIT-WORKFORCE-ARCHITECTURE`
- **Open blockers:** 5 canonical Open findings remain (013, 018, 030, INTEGRATION-005, B003-001) + `ANOX-MAINARCH-018` physical verification + milestone Security Architecture review (003, 007, 024)
- **Previously completed:** `MAINARCH-FIX-01` + `MAINARCH-RETEST-01` (17 findings Closed); `MAINARCH-FIX-02` + `MAINARCH-RETEST-02` (8 findings Closed); `MAINARCH-FIX-03` + `MAINARCH-RETEST-03` (5 findings Closed); **MAIN ARCHITECTURE AUDIT + REMEDIATION PHASE COMPLETE**; **LEGACY AUDIT SET 6/6 COMPLETE**; `LEGACY-FIX-01` + `LEGACY-RETEST-01` COMPLETE (8 findings Closed).
- **Next authorized task:** `AUDIT-WORKFORCE-ARCHITECTURE — B-027 WORKFORCE / WORK-CONTROL GOVERNANCE AUDIT` (Candidate `ANOX-TASK-WORKFORCEARCH001`; START WHEN HUMAN ASSIGNS).
- **Product status:** `BLOCKED_PENDING_FINAL_AUDIT`; no product/CI changes until all final/legacy audits are complete and the human final gate is recorded.

## Architecture / governance

- B-001…B-023: frozen/defined.
- B-025 V1.3: FROZEN (traceability / test-matrix / release-governance / implementation-readiness).
- B-024 Final MAIN Consistency Audit: PASS.
- B-025 New-Chat Handoff: COMPLETE.
- B-026 Continuous Development Governance: FROZEN.
- B-027-A AI Workforce / Work-Control Governance Foundation: MERGED at `38b619e...`.
- B-027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime: MERGED at `aca7a8...`.
- B-027-C / B-027-D: B027-C MERGED at `0a4910e...` (PR #8); AUDIT-MAIN-ARCHITECTURE findings frozen, merged to main, and sealed; MAINARCH-RETEST-01-INGEST completed at `ec71127...`; MAINARCH-RETEST-02-INGEST completed at `8ee4cc...`; MAINARCH-RETEST-03-INGEST completed at `876e635...`; LEGACY-AUDIT-SET-FREEZE consolidated at `1ffe6e7...`; LEGACY-FIX-01 merged at `3adf56c...`; LEGACY-RETEST-01-INGEST delivered at `f50dc79...`.

## Current canonical Open findings

- `ANOX-MAINARCH-013` (build/provenance, Class D)
- `ANOX-MAINARCH-018` (physical, Class E)
- `ANOX-MAINARCH-030` (B-009 wipe/session, Class C)
- `ANOX-LEGACY-INTEGRATION-005` (native handle leak, Class F)
- `ANOX-LEGACY-B003-001` (UUIDv4 variant, Class F)

Closed by `LEGACY-FIX-01` + `LEGACY-RETEST-01` (verified PASS — REMEDIATED):
`ANOX-MAINARCH-019`, `ANOX-MAINARCH-023`, `ANOX-MAINARCH-031`,
`ANOX-LEGACY-ANDROIDSEC-001`, `ANOX-LEGACY-CRYPTO-005`,
`ANOX-LEGACY-INTEGRATION-001`, `ANOX-LEGACY-INTEGRATION-002`, `ANOX-LEGACY-INTEGRATION-003`.
