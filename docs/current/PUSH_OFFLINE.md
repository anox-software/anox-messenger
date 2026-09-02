> **B-025 Authority Notice**
>
> This file is an advisory summary. Canonical authority is `docs/authority/B025/TRACK_B/B011_PUSH_OFFLINE.md`.

# anoX V1 — Push & Offline Handling

**Status:** ADVISORY — see Authority
**Architecture Baseline:** B-011
**Last synchronized:** 2026-09-02

---

## 1. Push

- Push is **wake-up only**.
- Push payload must **not** contain:
  - message plaintext
  - message preview
  - attachment plaintext
  - E2EE keys

## 2. Push Provider

- Primary V1 push provider: FCM HTTP v1 (optional for core messaging).
- UnifiedPush-only or FCM-fallback architectures are **not** current V1 binding promises.
- Push may be delayed, lost, or duplicated; `/v1/sync` is authoritative.

## 3. Push Tokens

- Separate from E2EE and device auth.
- Can rotate.
- Revoked with the device.

## 4. Offline Recipient

- Backend ciphertext queue TTL: 14 days.
- Provider queue/acceptance never changes message state.

## 5. Privacy

- No global online status.
- No last seen.
- Push wake-up is metadata; provider may see timing.
