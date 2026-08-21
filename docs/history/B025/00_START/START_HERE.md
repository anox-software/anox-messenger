# anoX Messenger V1 — START HERE (B-025)

**Status:** CURRENT / HANDOFF AUTHORITY  
**Date:** 2026-08-20  
**Architecture freeze:** B-001 through B-023 frozen/defined; B-024 consistency audit PASS with mandatory amendments; B-025 handoff package COMPLETE.  
**Implementation truth at package creation:** Git `main` at `c076528e26e5e3ed05b4d0aeed794894f1f78b5e`.

## 1. Read order

Read in this order before changing code:

1. `01_CURRENT_AUTHORITY/SECURITY_INVARIANTS_V1_1.md`
2. `01_CURRENT_AUTHORITY/B_FREEZE_REGISTRY.md`
3. `01_CURRENT_AUTHORITY/ULTIMATE_MAIN_ARCHITECTURE_B025.md`
4. relevant file(s) in `01_CURRENT_AUTHORITY/TRACK_B/`
5. `02_STATE/PROJECT_STATE_2026-08-20.md`
6. `02_STATE/FORTSCHRITT.md`
7. `02_STATE/IMPLEMENTATION_GAP_MATRIX.md`
8. `04_REPOSITORY/REPOSITORY_SNAPSHOT_MANIFEST.md`
9. actual source in `04_REPOSITORY/CURRENT_HEAD_SOURCE/`
10. historical material only when provenance is needed.

## 2. Authority model

**Architecture/target truth:** Security Invariants → latest Frozen B-spec → accepted ADR → Ultimate MAIN → Product/UX spec → project state/progress → historical material.

**Implementation truth:** actual repository code + executed test/CI evidence.

If current code violates a frozen security rule, do not reinterpret the architecture to fit the code. Mark the code non-compliant and prepare a scoped change.

## 3. Current exact engineering state

- `GIT-001`: complete.
- `TOOLCHAIN-001`: PR #1 merged and verified on `main` according to repository evidence.
- Current main commit: `c076528e26e5e3ed05b4d0aeed794894f1f78b5e`.
- Toolchain in checked-in source: AGP 8.13.2, KGP 2.4.10, Compose plugin 2.4.10, Gradle 9.3.1, JDK 17, NDK 26.2.11394342, compile/target/min SDK 34/34/26.
- Rust crypto dependency: vodozemac 0.10.0; aes-gcm 0.10.3.
- Accepted historical test evidence: Rust 15/15 PASS; Android connected instrumentation 35/35 PASS; release build PASS.
- GrapheneOS crypto/local-state runtime remains UNVERIFIED in the accepted state.
- Backend, production DB/RLS, Device Auth, registration/license, network messaging/sync, contacts, verification UX, push, attachments and production lifecycle are not implemented.
- Functional product progress remains approximately 27%; B-track architecture work does not increase that functional percentage.

## 4. Critical correction to old repo docs

The repository snapshot predates Track B consolidation. Old/current repo docs still contain stale statements such as Device Auth = Ed25519 and many items marked OPEN. Do not implement from those stale statements. The B-025 authority documents in this package supersede them.

## 5. Immediate next workflow

Do **not** jump straight into Device Authentication. First run `03_WORKFLOWS/STEP3_CODE_UPDATE_COMPATIBILITY_WORKFLOW.md` to determine which existing code/docs require a compatibility update against the new MAIN. Then run `03_WORKFLOWS/STEP4_GIT_CLOSE_AND_RESUME_DEVELOPMENT_WORKFLOW.md` to merge that synchronization safely. Only after that begin the next product implementation gate: Device Authentication under B-002 P-256/ES256/DPoP.

## 6. Historical material

`90_HISTORICAL/` exists for traceability only. Raw1.1 and older plans are not implementation authority. Full Raw1.0 verbatim text is not recoverable from the available sources and is intentionally not fabricated.
