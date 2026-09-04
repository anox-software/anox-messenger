> **B-025 Authority Notice**
>
> This file is an advisory summary. Canonical authority is `docs/authority/B025/TRACK_B/B008_MESSAGING_SYNC.md` and `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md` (B-008 v1.6).

# anoX V1 — Message Lifecycle

**Status:** ADVISORY — see Authority
**Architecture Baseline:** B-008
**Last synchronized:** 2026-09-02

---

V1 message lifecycle is governed by B-008.

Canonical protocol states:

- `QUEUED`
- `SENT`
- `DELIVERED`
- `READ` (optional)

`COMPOSING`, `ENCRYPTING`, `FAILED`, and `RETRY` are UI/client process states, not canonical protocol states.

`DELIVERED` is defined as recipient device received the message **and** completed the durable atomic commit of changed Olm state, message, dedup/replay, and conversation state. Server timestamp and push are not delivery truth.
