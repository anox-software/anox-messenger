# Current Implementation State — anoX V1

**Date:** 2026-09-05
**Latest material event:** ANOX-EVENT-0032
**Current branch:** audit/mainarch-retest-02-ingest
**Current HEAD:** 8ee4ccaa33e4ba134a8b85ab87fef164ffed447d

## Architecture / governance

- B-025 mandatory amendments V1.2 freeze DB/RLS/API/OTK/retention/privacy contracts; MAINARCH-RETEST-02 verified them (8/8 PASS).
- B_FREEZE_REGISTRY and AUTHORITY_INDEX updated (V1.2 authoritative for amended items).
- B027-A/B/C implemented and passing.
- Final pre-product audit still required before Product implementation may resume.

## Product implementation

- B-004 backend: NOT STARTED.
- B-005 DB/RLS: NOT STARTED.
- B-006 OTK/fallback client/server: NOT STARTED.
- B-007 wire/endpoint implementation: NOT STARTED.
- B-008/B-010/B-011/B-012/B-013 product: NOT STARTED.
- Android/Kotlin/Rust/JNI: unchanged.
- CI workflows: unchanged.

## Trust-boundary flags

- ANOX-MAINARCH-003 (server ↔ DB/RLS) and ANOX-MAINARCH-007 (server ↔ backup/PITR) remain flagged for milestone Security Architecture review; both findings are Closed as architecture-remediation-verified.
