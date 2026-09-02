> **B-025 Authority Notice**
>
> This file is an advisory summary. Canonical authority is `docs/authority/B025/TRACK_B/B014_PRIVACY_RETENTION_LOGGING.md`.

# anoX V1 — Metadata & Privacy

**Status:** ADVISORY — see Authority
**Architecture Baseline:** B-014
**Last synchronized:** 2026-09-02

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

- Raw IP/request logging under anoX control: retention target ≤24h.
- Cloudflare/FCM/other provider retention is not necessarily the same; never claim otherwise.
- Purpose-limited and minimized.

## 4. Future Options

Padding, timing obfuscation, and sealed-sender-like routing are future options, **not** current V1 promises.
