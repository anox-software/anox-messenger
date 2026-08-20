> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-013 — Account / Device Lifecycle (FROZEN v1.2).
>
# anoX V1 — Account & Device Lifecycle

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Account Creation

- New random `account_id`.
- New random `device_id`.
- New local E2EE identity (vodozemac account).
- New device-auth Ed25519 keypair.
- License status is separate from cryptographic identity.

## 2. V1 Device Model

- One active device per account.
- Device auth and E2EE are separate.
- Multi-device is out of scope.

## 3. Device Revocation

- Revocation must prevent API authentication and new push/message delivery.
- A lost device does **not** migrate its old private E2EE identity to a new device.

## 4. Loss / Replacement

- V1 has no recovery.
- If the only device and local crypto state are lost, the old identity is unrecoverable.
- A new device creates a new V1 cryptographic identity.
- Do not route old pending messages to a new identity.

## 5. Account Deletion

- Revoke server sessions.
- Destroy local protection material.
- Remove local DB, cache, and temp files as practical.

## 6. License Lifecycle

- License expiry does **not** delete E2EE private keys.
- License expiry does **not** become the encryption key.
- License expiry controls product/service access.
