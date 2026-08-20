> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-002 — Device Authentication (FROZEN v1.1).
>
# anoX V1 — Local Device Security

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Protected Assets

- E2EE identity / private Olm keys
- Olm sessions
- Device authentication private key
- Local SQLite DB
- Contacts and conversation metadata
- Encrypted outbox
- Attachment keys and encrypted blobs

## 2. Local Storage Rules

- No plaintext secrets in `SharedPreferences`, JSON, or external storage.
- Sensitive temp files are short-lived.
- Production logs are privacy-minimal and must not contain plaintext or keys.
- Biometric/app lock may be used for app access but is **not** the E2EE key.
- `allowBackup="false"` to prevent cloud backup of private state.

## 3. Keystore State Key

- Android Keystore generates a non-extractable AES-256-GCM master key.
- A random 32-byte state key is wrapped by the Keystore key.
- Identity and session pickles are encrypted with the state key in Rust.

## 4. Wipe / Delete

Logout or account delete should:
- Revoke server sessions/state as appropriate.
- Cryptographically destroy local protection material (drop Keystore entries, wipe wrapped key file).
- Remove local encrypted DB, cache, and temp files as practical.

Do not claim guaranteed physical flash erasure.

## 5. UI/UX

- Neutral lock-screen notifications by default.
- Screenshot/recent-app protection where appropriate.
- Clipboard minimization for sensitive fields.
