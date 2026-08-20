> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-004 — Backend Service Architecture (FROZEN).
>
# anoX V1 — Backend Architecture

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

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
- Final DB schema is **not frozen**.
