> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-012 — Attachments (FROZEN).
>
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
