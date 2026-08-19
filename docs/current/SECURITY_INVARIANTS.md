# anoX V1 — Security Invariants

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

These invariants must remain true for all V1 work unless an explicit architecture decision record (ADR) changes them.

## 1. Identity & Device

- `account_id` and `device_id` are random and non-sequential.
- Account identity, device identity, public username/handle, and E2EE identity are separate concepts.
- No mandatory telephone number or email address.
- V1 supports **one active device per account**. Multi-device is out of scope.
- Device authentication is separate from E2EE identity.
- A lost device does **not** migrate its old E2EE private state to a new device.

## 2. Recovery

**V1 has no account or crypto recovery.**

Prohibited:
- recovery seed / phrase / code
- encrypted server private-key backup
- recovery device / social recovery / multi-device recovery
- hidden master recovery key
- cloud restoration of E2EE private state

If the only device and local crypto state are permanently lost, the old cryptographic identity cannot be restored. A new device creates a new V1 cryptographic identity.

## 3. Cryptography

- E2EE direction: **vodozemac / Olm**.
- No custom DH, KDF, AEAD, MAC, signatures, RNG, safety numbers, or key hierarchy.
- No OpenPGP or libsignal as normal-chat encryption layers.
- Private E2EE identity and Olm session state stay local.
- Public session-initialization material may be stored/distributed by the server.

## 4. Key Separation

The following must remain distinct:
1. E2EE identity / private state
2. Olm session / ratchet state
3. Local state-protection key
4. Device-authentication key
5. Access/refresh/session tokens
6. Future attachment encryption key

## 5. Local Storage

- Android Keystore non-extractable master/wrapping key.
- Random 32-byte local state-protection key.
- AES-256-GCM authenticated protection of serialized Rust/vodozemac state.
- `allowBackup="false"` in `AndroidManifest.xml`.
- No V1 cloud private-state restore.

## 6. Messages

- Plaintext is encrypted locally before leaving the device.
- Server receives and persists ciphertext only.
- Manipulated ciphertext fails safely.
- `message_id` is random and globally unique.
- Retry uses the same logical `message_id` for idempotency.

## 7. Push

- Push is wake-up only.
- Push payload must **not** contain: plaintext, preview, attachment plaintext, or E2EE keys.
- Push provider/transport selection is not frozen.

## 8. Attachments

- File is encrypted locally with a random attachment key.
- Attachment key and metadata travel inside the E2EE message payload.
- Backend must not receive attachment plaintext or the attachment key in plaintext.

## 9. Backend Trust

- Server is untrusted for content.
- Metadata is visible to infrastructure.
- Server is not the final trust authority.
- Backend must not store: message plaintext, E2EE private keys, private session state, attachment plaintext, or recovery secrets.

## 10. Verification

- Accepted contact ≠ verified contact.
- Trust states: `UNKNOWN`, `VERIFIED`, `KEY_CHANGED`/`SECURITY_CHANGE`.
- Changing a verified E2EE identity reverts to `KEY_CHANGED`/`UNVERIFIED` and requires explicit re-verification.
- SAS and/or QR are the V1 UX direction, using established vodozemac/Matrix semantics.
