# anoX V1 — Security Requirements

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Identity & Device

- `account_id` and `device_id` must be random and non-sequential.
- Account identity, device identity, public username, and E2EE identity must remain separate.
- No mandatory phone or email.
- V1 supports one active device per account.
- Device authentication must be separate from E2EE identity.
- Device revocation must prevent API authentication and new push/message delivery.

## 2. Recovery

**V1 must not implement** any form of account or cryptographic recovery:
- no recovery seed/phrase/code;
- no encrypted server private-key backup;
- no recovery device, social recovery, multi-device recovery;
- no cloud restoration of E2EE private state.

## 3. E2EE

- Use `vodozemac` 0.10.0 for the Olm / Double Ratchet.
- No custom DH, KDF, AEAD, MAC, signatures, RNG, safety numbers, or key hierarchy.
- No OpenPGP or libsignal as an encryption layer.
- Private E2EE identity and Olm session state must remain on the device.
- Public session-init material may be stored/distributed by the server.

## 4. Local State Protection

- Android Keystore must hold a non-extractable wrapping/master key.
- A separate random 32-byte state key must protect Rust/vodozemac pickles.
- AES-256-GCM must be used for authenticated state encryption.
- `allowBackup="false"` must be set to prevent cloud private-state restore.

## 5. Messages

- Plaintext is encrypted locally before leaving the device.
- Server receives ciphertext only.
- Manipulated ciphertext fails safely.
- `message_id` must be random and globally unique.
- Retry must use the same logical `message_id`.
- No typing indicator, no global online status, no last seen by default.
- Read receipts are optional.

## 6. Push

- Push payloads must not contain plaintext, preview, attachment plaintext, or E2EE keys.
- Push is wake-up only; message sync must work independently.

## 7. Attachments

- Files are encrypted locally before upload.
- Attachment keys travel inside the E2EE message payload.
- Backend must not receive attachment plaintext or the attachment key in plaintext.

## 8. Backend Trust

- Server is not a trust or recovery authority.
- Backend must not store plaintext, E2EE private keys, session state, attachment plaintext, or recovery secrets.

## 9. Verification

- Trust states: `UNKNOWN`/`UNVERIFIED`, `VERIFIED`, `KEY_CHANGED`/`SECURITY_CHANGE`.
- Identity change must warn the user and require explicit re-verification.
- Use established SAS/QR semantics; no custom safety-number protocol.

## 10. Local Device Security

- No plaintext secrets in `SharedPreferences`/JSON/external storage.
- Production logs must not contain plaintext or keys.
- Biometric/app lock is not the E2EE key.
- Wipe destroys local protection material and removes encrypted DB/temp/cache as practical.
