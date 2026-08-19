# anoX V1 — Attachments

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Direction

Do not send large files as ordinary Olm message bodies.

## 2. Encryption

```text
file
  → local metadata minimization
  → random attachment key
  → local authenticated encryption
  → encrypted blob storage
```

- Attachment key and sensitive metadata are transported **inside the E2EE message payload**.
- Backend must not receive attachment plaintext or the attachment key in plaintext.

## 3. AEAD

- XChaCha20-Poly1305 is the **planned** attachment AEAD direction **if** supported by the final established maintained Rust library.
- Do **not** document it as currently implemented.

## 4. Thumbnails

- Generate thumbnails locally where possible.
- Do not claim perfect metadata anonymity.

## 5. Storage

- Encrypted blob in object storage.
- Backend stores only the encrypted blob and minimal non-sensitive metadata.
