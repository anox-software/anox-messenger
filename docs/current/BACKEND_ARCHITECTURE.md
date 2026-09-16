> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-004 — Backend Service Architecture (FROZEN v1.2-f04).
>
> **Schema authority notice (DEFERS-TO: DB-SCHEMA-V1-FROZEN).** This document is **informative** for schema and security-contract matters.
> The single canonical frozen schema contract is `DB-SCHEMA-V1-FROZEN` (`docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md §B-005`
> as amended by `docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md §1–§2, §11`); the backend security contracts (Device Auth binding,
> DPoP verifier, nonce, registration PoP, rejection taxonomy) are frozen in `B025_MANDATORY_AMENDMENTS_V1_4.md`.
>
# anoX V1 — Backend Architecture

**Status:** CURRENT (informative; defers to B-004 v1.2-f04 and DB-SCHEMA-V1-FROZEN)
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated
**Last synchronized:** 2026-09-14

---

## 1. Infrastructure

```text
Android
  → authenticated HTTPS API
  → anoX backend/service layer
  → Supabase/PostgreSQL infrastructure
```

Supabase is **infrastructure**, not:
- E2EE key vault
- cryptographic trust authority
- recovery authority
- message plaintext processor

## 2. Style

- Modular monolith for V1, not premature microservices.
- Logical modules:
  - account/identity
  - license
  - auth/device
  - keys/session-init
  - contacts
  - messaging
  - delivery/sync
  - attachments
  - push
  - abuse/security
  - account lifecycle

## 3. Secrets

Never ship in APK/Git/logs:
- service-role keys
- DB passwords
- backend secrets
- provider secrets

## 4. Database

- PostgreSQL via Supabase.
- RLS is defense in depth, not a replacement for backend authorization.
- Use migrations.
- Separate dev/staging/prod.
- The V1 logical schema **is frozen** as `DB-SCHEMA-V1-FROZEN` (see the schema authority notice above); the earlier "schema not yet frozen" statement in this file is **superseded** (`ANOX-SECURITY-ARCH-004`, `MSC-UNIT-040`). No SQL/migrations are deployed (B-005 `implementation_state = NOT_STARTED`).
