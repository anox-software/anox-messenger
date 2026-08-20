# B-005 — Database Schema + RLS
**Status:** FROZEN v1.10

- Logical schemas: `core`, `auth`, `licensing`, `crypto`, `social`, `messaging`, `push`, `security`, `admin`.
- Roles: migrator/runtime/worker/admin_service/monitor. Runtime is nonowner, nonsuperuser, no BYPASSRLS. Transaction-local RLS context.
- Random external IDs, explicit unique/FK/check constraints, restricted cascades and transactional race protection.
- Core tables cover account/device/account status; auth sessions/device auth keys/replay/nonces; licenses/entitlements/registrations; E2EE public identity/session-init material; contact invites/requests/relationships/blocks; messages/delivery receipts/sync events; attachment lifecycle; push registrations/jobs; security/admin audit.
- One-active-device/account is DB-enforced. Registration/license redemption is atomic.
- `messaging.messages` stores ciphertext/routing/session type/state/expiry; no semantic server `read_at` truth.
- Delivery receipts are server records only after recipient durable decrypt/persist ACK.
- Contact invite token stored hash-only; contact request TTL 7d.
- E2EE identity includes public Ed25519/Curve25519 material and identity revision; no server trust status.
- Session-init material has atomic claim state; OTK/FALLBACK terminology follows actual vodozemac.
- Attachment server row may include opaque IDs, owner/recipient/device/conversation/message link, storage object id, ciphertext size/hash/state/timestamps; never attachment key, filename, MIME or plaintext size/hash.
- Sync cursor server state stores hash bound to account/device and internal monotonic `sync_seq`; public cursor is random opaque 32 bytes with 30d lifetime.
