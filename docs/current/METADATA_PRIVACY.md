# anoX V1 — Metadata & Privacy

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Important

Do **not** market V1 as metadata-free.

Backend/infrastructure may observe:
- account/device IDs
- routing/conversation relationship
- timestamps
- ciphertext size
- delivery state
- IP at infrastructure layer
- push provider/token timing metadata

## 2. Defaults

- No last seen.
- No global online status.
- No typing indicator.
- No behavioral analytics.
- No phonebook upload.
- Local contact/chat names stay local where possible.

## 3. IP / Security Logs

- Purpose-limited and minimized.
- Exact retention remains **OPEN**.

## 4. Future Options

Padding, timing obfuscation, and sealed-sender-like routing are future options, **not** current V1 promises.
