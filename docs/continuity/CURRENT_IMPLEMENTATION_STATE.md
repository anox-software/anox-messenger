# Current Implementation State — anoX V1

**Date:** 2026-09-06
**Latest material event:** ANOX-EVENT-0034
**Current branch:** audit/mainarch-retest-03-ingest
**Current HEAD:** 876e63565942c65df738afc5f4578a6b16a331b0

## Architecture / governance

- B-025 mandatory amendments V1.3 freeze traceability, test-matrix, release-governance, branch-protection, implementation-readiness, and evidence-state model.
- B-025 mandatory amendments V1.2 remain in force for DB/RLS/API/OTK/retention/privacy contracts.
- B_FREEZE_REGISTRY and AUTHORITY_INDEX updated (V1.3 authoritative for amended items).
- B027-A/B/C implemented and passing.
- **MAIN ARCHITECTURE AUDIT = COMPLETE; MAIN ARCHITECTURE REMEDIATION PHASE = COMPLETE** (30 findings Closed; 6 deferred legacy/build/hardware findings remain Open).
- Final pre-product audit still required before Product implementation may resume.

## Product implementation

- B-004 backend: NOT STARTED.
- B-005 DB/RLS: NOT STARTED.
- B-006 OTK/fallback client/server: NOT STARTED.
- B-007 wire/endpoint implementation: NOT STARTED.
- B-008/B-010/B-011/B-012/B-013 product: NOT STARTED.
- Android/Kotlin/Rust/JNI: unchanged.
- CI workflows: unchanged.

## Implementation-readiness architecture

- Per-domain readiness is tracked in `docs/workforce/registries/implementation_readiness.json`.
- Architecture frozen does not imply implementation complete; implementation complete does not imply verified; verified does not imply release ready.
- B-018/B-019/B-023 remain `NOT_STARTED` / `NOT_RELEASE_READY`; release requires verified server-side protection or an explicit recorded ROLE-001 decision (none exists).

## Trust-boundary flags

- ANOX-MAINARCH-003 (server ↔ DB/RLS), ANOX-MAINARCH-007 (server ↔ backup/PITR), and ANOX-MAINARCH-024 (signing/release custody + incident-response boundary) remain flagged (`PENDING`) for milestone Security Architecture review.
- ANOX-MAINARCH-018 physical GrapheneOS/StrongBox verification remains `PHYSICAL_VERIFICATION_REQUIRED`.
