> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-011 — Push + Offline Queue (FROZEN v1.2).
>
# anoX V1 — Push & Offline Handling

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Push

- Push is **wake-up only**.
- Push payload must **not** contain:
  - message plaintext
  - message preview
  - attachment plaintext
  - E2EE keys

## 2. Push Provider

- Push provider is not a trust source.
- Push may be delayed, lost, or duplicated.
- Message sync must work independently of push.
- Provider/transport selection is **not fully frozen**.
- Do **not** state UnifiedPush+FCM fallback as the current binding architecture.

## 3. Push Tokens

- Separate from E2EE and device auth.
- Can rotate.
- Revoked with the device.

## 4. Offline Recipient

- The backend may temporarily queue ciphertext.
- Exact TTL remains **OPEN**.

## 5. Privacy

- No global online status.
- No last seen.
- Push wake-up is metadata; provider may see timing.
