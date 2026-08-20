# anoX Messenger V1 — ULTIMATE MAIN ARCHITECTURE (B-025)

**Status:** CURRENT / AUTHORITATIVE CONSOLIDATED V1 TARGET
**Date:** 2026-08-20
**Supersedes:** 2026-08-19 Ultimate MAIN where later B-specs amended it.

## Product boundary

Closed-source native Android messenger with GrapheneOS as the primary V1 target. Continue the existing project; do not rebuild it as an unrelated application. V1 core is secure 1:1 messaging and an official anoX Support relationship/chat. No groups, calls, multi-device or account recovery in V1. Do not claim the product is unhackable, anonymous in an absolute sense or metadata-free.

## Identity and account model

`account_id` and `device_id` are random UUIDv4 values and separate from username/contact addressing, E2EE identity and Device Auth. One active device per account. No mandatory phone/e-mail. Username is lowercase ASCII `[a-z0-9_.]`, length 3–32, with reserved system names. V1 usernames are immutable after activation and previously activated usernames are not automatically recycled. No global directory; exact username or opaque contact-invite QR only.

Loss of the sole device/private state does not permit re-binding a new Device Auth/E2EE identity to the old account. A new device after loss uses a new account/device/E2EE identity. Commercial license replacement may be handled as a business remedy but must never restore old crypto identity/history/trust.

## License

Standard V1 durations: 30, 90 and 180 days. License format `anox-XXXX-XXXX-XXXX` with 12 unambiguous CSPRNG characters. Plaintext is shown once; canonical lookup uses versioned HMAC-SHA-256 with a server-side lookup key, not plaintext persistence. Registration reserves the license and username, then binds Device Auth and locally created E2EE public material and atomically commits account/device/entitlement. License expiry preserves local data/keys and only restricts normal service access; renewal does not rotate E2EE or Device Auth identity.

## Device Authentication

Android Keystore P-256 private key, ES256 signatures, non-exportable; StrongBox preferred with TEE fallback in production. Software-only Device Auth must fail production registration. Remote attestation is not mandatory V1. RFC9449-style DPoP binds an opaque 256-bit access token to device/key/session. Server stores token hash, TTL 15 minutes, no refresh token. Fresh nonce where required; DPoP `jti` uses at least 128 random bits, `iat` window ±120 seconds, shared replay cache 5 minutes. Key invalidation is not silently repaired with a new Device Auth key under the old account.

## E2EE / verification

Android/Kotlin → narrow interface → JNI/native → Rust → vodozemac/Olm. Current implemented foundation is pinned to vodozemac 0.10.0 until reviewed upgrade. No OpenPGP layer, libsignal or custom ratchet. E2EE identity/public material follows actual vodozemac APIs; private Account/Session state remains local.

Trust states: `UNVERIFIED`, `VERIFIED`, `KEY_CHANGED`; `VERIFYING` transient only. Same active account/device identity mismatch is a security change, not legitimate V1 rotation. It blocks sending/session establishment. Verification uses vodozemac SAS / Matrix SAS-v1 cryptographic semantics; contact QR is discovery only. anoX transport for verification controls is its own hidden E2EE control traffic and does not claim Matrix wire compatibility.

## Session-init / key distribution

Server may distribute only public session-init material. Olm one-time keys/fallback keys follow actual vodozemac semantics. Publish durability order is local Account persist → upload → backend ACK → mark published → persist. Atomic claim states prevent double-consumption. Fallback used only if no OTK. Previous fallback key retention is 15 days (14-day maximum prekey/message delivery window plus 24-hour safety margin). Same active device public identity mismatch is rejected and logged as a security anomaly.

## Messaging / sync

Inner E2EE envelope is encrypted by Olm; outer server-visible envelope contains only routing/protocol/session/message metadata required by the frozen contract. `message_id` and `conversation_id` are UUIDv4. Semantic kinds: text, attachment, read_receipt, verification. Text max 32 KiB, inner envelope max 64 KiB, Olm ciphertext max 128 KiB. Send retries reuse the same logical message ID and exact ciphertext/session/message type/idempotency operation while generating a fresh DPoP proof.

Message states: `COMPOSING → ENCRYPTING → QUEUED → SENDING → SENT → DELIVERED → READ`, with retryable/permanent failure and expiry. `SENT` means backend authenticated/authorized/validated and durably persisted ciphertext plus recipient queue. `DELIVERED` requires recipient decrypt + validation + durable local transaction of changed Olm state/message/dedup/replay/conversation, followed by ACK. `READ` is optional E2EE control and disabled by default. Ciphertext queue TTL 14 days; delivered ciphertext deletion target ≤1 hour.

`/v1/sync` is authoritative. Cursor is opaque random 32 bytes, base64url-no-padding, server stores hash bound to account/device and internal `sync_seq`; cursor lifetime 30 days. Reusing an older valid cursor after a client crash must safely replay the page; local cursor advances only after durable page processing.

Preferred outbound Olm session is a deterministic locally persisted `preferred_session_id`; existing valid preferred session is used. New inbound PreKey does not silently replace a valid preferred session. Incoming normal messages use their exact outer session ID. Missing/corrupt preferred state does not trigger trial-decrypt/random session selection.

## Contacts

Exact username and opaque QR invite only. Requests support create/accept/reject/cancel/expire/block, with relationship state separate from cryptographic trust. Request TTL 7 days. Anti-enumeration responses hide existence/block status. Local nickname remains local. Blocking prevents new requests/session-init/message/verification and causes undelivered pair ciphertext cleanup ≤1 hour. Removing a relationship ends new claims/messages but may retain local history/trust for the exact same identity. Contact export/import contains public identifiers/nickname only; no sessions/keys/verification transfer.

## Push

Primary V1 provider is FCM HTTP v1 for wake-up only, but FCM is optional for core messaging. Minimal payload conceptually `{"v":"1","type":"sync"}`; no message/sender/conversation/account/device IDs, content, keys or license. High priority only for timely user-visible activity; collapse key `anox_sync`, provider wake TTL 5 minutes. Do not signal “new message” until post-sync classification. Without Google Play/FCM, core messaging still works via app open/resume/manual sync and conservative WorkManager best-effort scheduling; no permanent background websocket/foreground service in V1.

## Local database / storage

V1 local messenger DB target: Room 2.8.4 + SQLCipher for Android 4.17.x. `K_DB` is independent 256-bit random key wrapped by its own Keystore AES-GCM alias. Existing `K_STATE` AES-GCM protected envelope remains for serialized vodozemac Account/Session state, with migration into the encrypted DB when B-009 is implemented. Plain normal message text may reside inside SQLCipher; do not invent per-row crypto. Missing keys/corruption fail closed; destructive migration/silent new DB under old account is forbidden. Current file-based protected crypto state is legacy foundation and must be migrated deliberately, not deleted casually.

## Attachments

Fresh 256-bit key per attachment. V1 crypto: libsodium `crypto_secretstream_xchacha20poly1305` through Rust/native integration. Initial chosen wrapper integration is libsodium-rs 0.2.4 + pinned transitive/source dependency; build must be proven for Android ABIs before acceptance. 1 attachment/message, plaintext size 1 byte–100 MiB, fixed 1 MiB plaintext chunks, conservative ciphertext cap 101 MiB. Secretstream header then authenticated chunks; `TAG_MESSAGE` non-final and `TAG_FINAL` final. SHA-256 exact ciphertext blob; attachment key + filename/MIME/plaintext size + expected ciphertext hash/size stay inside E2EE descriptor.

Private Supabase Storage receives only opaque encrypted blob. Signed upload capability 2 hours; signed recipient download 5 minutes. Standard signed upload for small objects and resumable TUS for >6 MiB. Server links one attachment to one message atomically; no server plaintext thumbnails/scanning/dedup. Recipient verifies size/hash/secretstream/final tag/plaintext size, stores encrypted local blob + key/metadata in SQLCipher, then sends storage-received ACK. Unpublished object max 24h; published undelivered follows 14-day message TTL; after message delivered but attachment not fetched, max additional 14 days; after received ACK or message expiry delete server blob ≤1 hour.

## Backend/API/DB

Architecture: Android → authenticated HTTPS `/v1` API → anoX modular monolith → Supabase/PostgreSQL/private object storage. No direct privileged Supabase access from APK. Request pipeline: TLS → Device Auth → DPoP/replay → validation → authorization → abuse controls → business logic → repository → transaction. Server derives authenticated account/device context; never trusts client identity fields blindly. Parameterized SQL, migrations, DEV/STAGE/PROD separation and RLS defense-in-depth.

API uses snake_case UTF-8 JSON, UUIDv4, RFC3339 UTC, base64url-no-padding for binary fields, unknown request fields rejected, response unknown fields tolerated, RFC9457 problem JSON. Default page 50/max100. Generic idempotency key UUIDv4 retained 24h with exact-body fingerprint. No secrets in query strings. Certificate pinning is not a V1 requirement.

DB schemas logically separate core/auth/licensing/crypto/social/messaging/push/security/admin. Runtime role is nonowner/nonsuperuser/no BYPASSRLS with transaction-local RLS context. One-active-device and license/account registration races are DB-enforced. No server read_at truth. Push token stored reversibly encrypted plus hash. Attachment DB does not contain key/filename/MIME/plaintext size/hash.

## Lifecycle

App lock is local only. Logout revokes network session/token/push registration but keeps Device Auth key, E2EE identity/sessions, encrypted DB/history and contacts. Entitlement expiry preserves local state and disables normal network messaging while allowing restricted renewal/security actions. Suspension is reversible server policy; account/device revoke is terminal for V1 access. Local wipe is always possible offline and deletes local keys/wrappers/DB/state/attachments/temp best-effort; server revoke is attempted first when reachable but local wipe never depends on network success.

Account deletion is irreversible: durable independent terminal deletion intent is written to erasure journal before DB account deletion so restore cannot resurrect the account. Server revokes access/push and purges undelivered ciphertext/attachments/relationships per retention; local wipe follows. Recipient local copies/history are not remotely erased. Uninstall/factory reset destroying Keystore/app state strands the old account; reinstall is first-run/new account, not recovery.

## Privacy / metadata / retention

Do not claim metadata-free. Infrastructure may learn account/device IDs, routing relationships, timing, ciphertext size, delivery state, IP and push token/timing. Ordinary anoX raw IP/request logging is minimized; raw IP target is ≤24h where controlled by anoX, without misrepresenting third-party provider retention. No behavioral analytics. Exact retention jobs must be tested before production. Previous fallback public/private session-init state follows the 15-day B-006 safety rule.

## Production security / release

B-015 abuse controls, B-016 infrastructure, B-017 CI/supply chain, B-018 signing/updates, B-019 operations, B-021 test matrix, B-022 independent audit and B-023 Release DoD are all release gates. Production release is binary GO/NO-GO. No unresolved Critical/High or core-security Medium findings. Physical supported GrapheneOS testing, backup restore/DR rehearsal, offline hardware-protected release signing and recovery rehearsal, immutable artifact hashes, SBOM, admin hardware MFA, on-call/runbooks and public audit summary are required according to the frozen specs.

## Official Support

Official Support is a normal one-device anoX account using the same E2EE protocol and no universal decryption capability. Server-side product metadata may identify it as official, but that label is not `VERIFIED`. Support private E2EE keys remain on its endpoint with no special server backup. If its device/identity is lost, V1 creates a new account/device/E2EE identity; old VERIFIED trust does not silently transfer. Multi-device Support HA is future scope.
