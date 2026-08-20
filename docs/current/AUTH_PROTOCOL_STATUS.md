> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-002 — Device Authentication (FROZEN v1.1).
>
# anoX V1 — Authentication Protocol Status

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Direction

Device authentication is separate from E2EE identity.

Current direction:
- Ed25519 device-auth keypair.
- Private device-auth key stays local.
- Public device-auth key is stored server-side.
- Short-lived access/session token concept.
- Revocable refresh/session mechanism.
- Request freshness and replay protection.

## 2. Signed Request Concept

Historical design requires binding signed requests conceptually to:
- HTTP method
- path
- timestamp / freshness
- nonce / request ID
- body hash
- canonical deterministic bytes

## 3. Important: OPEN

The exact production auth/token/challenge/signature contract is still **OPEN**.

Do not invent the final protocol in code or documentation. A future ADR is required to freeze:
- exact token format and lifetime;
- exact challenge/response contract;
- exact canonical signing bytes;
- exact refresh and revocation flow.
