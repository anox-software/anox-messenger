# anoX V1 — Message Lifecycle

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. States

- `COMPOSING`
- `ENCRYPTING`
- `QUEUED`
- `SENT`
- `DELIVERED`
- `READ` (optional)
- `FAILED`
- `RETRY`

## 2. Meanings

- `SENT` = backend accepted and persisted the ciphertext.
- `DELIVERED` = recipient device received the encrypted message.
- `READ` = optional read receipt.

## 3. Sender Flow

```text
plaintext local
  → CryptoService
  → vodozemac encrypt
  → encrypted outbox
  → authenticated API
  → server persists ciphertext
  → ACK
  → SENT
```

## 4. Recipient Flow

```text
sync/fetch ciphertext
  → local deduplication
  → local decrypt
  → local protected storage / UI
```

## 5. Requirements

- Random, globally unique `message_id`.
- Retry uses the same logical `message_id`.
- Deduplication and idempotency.
- Replay handling.
- Manipulated ciphertext fails safely.
- Server timestamp is not cryptographic truth.
- Push is not delivery truth.

## 6. Privacy Defaults

- No typing indicator.
- No global online status.
- No last seen.
- Read receipts are optional / user-configurable.
