> **B-025 Authority Notice**
>
> This file is an advisory summary. Canonical authority is `docs/authority/B025/TRACK_B/B012_ATTACHMENTS.md`.

# anoX V1 — Attachments

**Status:** ADVISORY — see Authority
**Architecture Baseline:** B-012
**Last synchronized:** 2026-09-02

---

## 1. Direction

Do not send large files as ordinary Olm message bodies.

## 2. Encryption

```text
file
  → local metadata minimization
  → random attachment key
  → libsodium crypto_secretstream_xchacha20poly1305 authenticated encryption
  → encrypted blob storage
```

- Attachment key and sensitive metadata are transported **inside the E2EE message payload**.
- Backend must not receive attachment plaintext or the attachment key in plaintext.

## 3. AEAD

- Attachment AEAD: `crypto_secretstream_xchacha20poly1305` via libsodium/Rust.
- This is the frozen V1 attachment crypto direction.

## 4. Thumbnails

- Generate thumbnails locally where possible.
- Do not claim perfect metadata anonymity.

## 5. Storage

- Encrypted blob in object storage.
- Backend stores only the encrypted blob and minimal non-sensitive metadata.
