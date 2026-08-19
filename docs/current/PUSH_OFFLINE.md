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
