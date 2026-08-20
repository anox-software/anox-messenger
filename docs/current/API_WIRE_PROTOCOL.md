> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-007 — API + Wire Protocol (FROZEN v1.9).
>
# anoX V1 — API / Wire Protocol

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Transport

- REST/HTTPS `/v1` direction.
- API version is independent of cryptographic/wire protocol version.

## 2. Envelope

- Outer envelope contains only server-required operational data.
- Sensitive semantic metadata belongs inside the encrypted payload when the server does not need it.
- Sender identity is derived/validated from authenticated device context, not blindly accepted from JSON.

## 3. Sync & Pagination

- Cursor-based sync and pagination direction.
- Exact endpoint names and final `/sync` contract remain OPEN.

## 4. Security

- TLS.
- Device auth.
- Freshness / replay checks.
- Input validation.
- Authorization.
- Rate limits and abuse controls.
- Object-level authorization.
- Idempotency via request ID / nonce.
- Request and body size limits.
- Anti-enumeration.
- Parameterized queries / safe ORM.

## 5. Certificate Pinning

Certificate pinning is **OPEN**, not a mandatory V1 architecture decision.

## 6. Dummy Traffic

Dummy traffic is not an implemented V1 feature.
