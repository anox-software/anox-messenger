# anoX V1 — System Architecture

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Overview

anoX Messenger V1 is a closed-source, native Android/GrapheneOS messenger built around 1:1 end-to-end encrypted (E2EE) messaging.

High-level flow:

```text
Android (Kotlin)
  → narrow CryptoService / JNI boundary
  → Rust crypto crate
  → vodozemac Olm / Double Ratchet
  → authenticated HTTPS API
  → anoX backend / service layer
  → Supabase/PostgreSQL infrastructure
```

## 2. Core Boundaries

- **E2EE identity and Olm session state** stay on the device.
- **Message plaintext** never reaches the backend.
- **Backend/infrastructure** may observe routing metadata, timestamps, ciphertext size, and delivery state.
- **Device authentication** is separate from E2EE identity.
- **Local state-protection key** is separate from E2EE keys.

## 3. Components

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Android UI/Service | Kotlin / Jetpack Compose | User-facing app, offline storage, sync |
| Crypto bridge | JNI + Rust `anox_crypto` | vodozemac Olm, AES-256-GCM state protection |
| Authentication | Ed25519 device-auth keys + short-lived tokens | Device authentication and request freshness |
| API | REST/HTTPS `/v1` | Outer envelope, transport, rate limits, abuse controls |
| Backend | Modular monolith | Domain modules: account, license, auth, keys, contacts, messages, delivery, attachments, push, security |
| Infrastructure | Supabase/PostgreSQL + object storage | Persistence, RLS, migrations |

## 4. V1 Scope Guardrails

- One active device per account in V1. Multi-device is out of scope.
- No account or cryptographic recovery in V1.
- No push plaintext, no typing/online status by default.
- No custom cryptographic primitives; actual vodozemac API is the source of truth.

## 5. Document Map

- Implementation source of truth: repository code + executed tests.
- Architecture source of truth: `docs/current/` + this file + `SECURITY_INVARIANTS.md`.
- Historical analysis: `docs/history/raw1.1/`.
