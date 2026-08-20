# B-008 — Messaging + Sync
**Status:** FROZEN v1.5

- Inner protocol v1 E2EE envelope encrypted with Olm; outer routing envelope contains only necessary server-visible identifiers/protocol/session/message type/ciphertext and optional attachment_id only for attachment message.
- `message_id` UUIDv4 allocated before encryption and immutable. `conversation_id` UUIDv4 stable per relationship.
- Olm types `pre_key` / `normal`; semantic inner kinds `text`, `attachment`, `read_receipt`, `verification`.
- Limits: text 32KiB, inner 64KiB, Olm ciphertext 128KiB.
- Outgoing ratchet mutation + exact encrypted outbox state must be atomic before network send. Retry same logical id/exact ciphertext/session/type/idempotency operation, fresh DPoP.
- Message server ciphertext TTL 14d. Sync events are source of truth; push/realtime only wake.
- Incoming dedup/replay by id/hash, exact session/prekey logic; serialize per session; validate decrypted binding/schema before accept.
- Before delivery ACK, atomically persist changed Olm state + message + dedup/replay + conversation. `DELIVERED` only after that durable commit.
- FIFO per conversation; max one inflight send/conversation.
- Delivered ciphertext cleanup target ≤1h. `READ` is optional E2EE control, default OFF, batches up to 100 IDs.
- Poison/malformed events must be classifiable so sync cursor can advance safely after durable handling.
- Attachment message acceptance atomically links committed unpublished attachment to exactly one message and marks it PUBLISHED after owner/recipient/conversation authorization checks.
