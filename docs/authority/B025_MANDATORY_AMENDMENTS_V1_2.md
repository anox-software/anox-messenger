# B-025 Mandatory Amendments V1.2

**Status:** FROZEN / CURRENT  
**Date:** 2026-09-02  
**Authority:** Human-authorized `MAINARCH-FIX-02` server/database/API/OTK/retention/privacy architecture remediation.  
**Supersedes:** This document is an authoritative successor amendment to specific provisions in `docs/authority/B025/TRACK_B/` for B-004, B-005, B-006, B-007, B-011, B-012, B-014, B-015, B-016, and the ULTIMATE MAIN trust-boundary section, and to `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md` for the same domains where V1.2 contains more specific provisions. `B025_MANDATORY_AMENDMENTS_V1_1.md` remains in force for B-003, B-008, B-010, B-013, B-020, B-022 and ULTIMATE B027 trust boundary.

This document does **not** modify the B-025 historical snapshot in `docs/authority/B025/TRACK_B/`. The B-025 snapshot files remain immutable provenance. The `docs/authority/B_FREEZE_REGISTRY.md` and `docs/authority/AUTHORITY_INDEX.md` record the amended current versions.

This is an **architecture-only** freeze. B-004, B-005, B-006, B-007, B-011, B-012, B-014, B-015 and B-016 Product implementation remains `NOT STARTED` and is blocked until the `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT` human final gate records an acceptable result.

---

## B-004 — Backend Service Architecture (amended v1.1-f02)

The following items supersede `docs/authority/B025/TRACK_B/B004_BACKEND_SERVICE_ARCHITECTURE.md` for the clauses listed. In case of conflict, this section wins.

### 1. Request pipeline and trust zones

The canonical request pipeline is:

`TLS termination → WAF/edge → B-004 public API → Device Auth proof-of-possession verification (B-002) → DPoP replay-cache check → access-token verification/binding → request validation → entitlement/device-state check → abuse/rate-limit check → application service → repository → database transaction.`

Each stage must fail closed on any validation failure unless an explicit higher Authority documents a safe degraded path. The pipeline must not proceed to business logic with an unverified identity.

### 2. AuthenticatedDeviceContext

Every authenticated user-facing request must derive a server-side `AuthenticatedDeviceContext` containing at least:

- `account_id` (UUIDv4, server-side from validated token/session binding)
- `device_id` (UUIDv4, bound to the validated Device Auth key)
- `device_auth_key_id` or equivalent public-key reference (not the private key)
- `session_id` / token reference
- `entitlement_state` (`ACTIVE`, `EXPIRED`, `RESTRICTED`, `REVOKED`, `DELETED` cascade)
- `request_id` (UUIDv4 for tracing, never logged with secrets)
- `issued_at` / token lifetime

This context is the **only** source of identity/authorization in the service and repository layers. Client-supplied JSON fields must not override `account_id`, `device_id`, or entitlement. The context is created by the Device Auth + access-token layer and is immutable from that point onward for the request.

### 3. Service/repository layering

- Controllers handle HTTP/serialization and produce `AuthenticatedDeviceContext` via B-004 security middleware.
- Application services receive the context and enforce authorization/entitlement checks.
- Repositories issue parameterized SQL and rely on DB RLS, transaction-local identity, and repository-level ownership checks as defense in depth.
- No application service or repository may trust client JSON for identity or authorization.
- Dynamic table/column identifiers are whitelisted; no string concatenation into SQL.

### 4. Logging and observability

- Logs must not contain plaintext messages, attachment keys, DPoP proofs, full tokens, license codes, FCM tokens, account/device recovery secrets, or full request bodies.
- Error responses must use the stable error classes in B-007 §10; internal details are not returned to clients.
- Security events (auth failures, replay, rate limit, device mismatch, entitlement revocation, account deletion) record class, request_id, account/device references, and outcome, but not plaintext or recoverable secrets.
- Operational metrics must not produce cross-account or cross-device fingerprints.

### 5. Admin and worker planes

- Admin plane is on a separate origin/ingress with its own authentication (identity-aware access, WebAuthn/hardware MFA, RBAC, CSRF protection).
- Admin access does not grant ability to decrypt E2EE content, recover Device Auth private keys, or impersonate user requests without audit and explicit break-glass authorization.
- Worker roles run with narrowly scoped DB credentials. They may use RLS-bypass privilege only for defined tasks (see B-005 §9). Workers do not process user requests.
- Durable jobs/queues are plaintext-free: they carry only identifiers, ciphertext references, and operational hints, never message plaintext or E2EE keys.

### 6. Secret and configuration handling

- Secrets (DB credentials, signing keys, lookup keys, FCM service-account keys, object-storage access keys, admin credentials) live in a secret manager with per-environment (DEV/STAGING/PROD) values.
- AI context never contains plaintext secret values; only role/secret names and type are referenced in architecture.
- Configuration (provider regions, hostnames, project IDs) is frozen as evidence before RC, not hard-coded in source.

---

## B-005 — Database Schema + RLS (amended v1.11-f02)

The following items constitute `DB-SCHEMA-V1-FROZEN`, the authoritative V1 logical database and RLS contract. They supersede `docs/authority/B025/TRACK_B/B005_DATABASE_SCHEMA_RLS.md` for the listed clauses; unamended clauses remain in force.

### 1. Logical schemas

V1 logical PostgreSQL schemas:

- `core` — account, device, username, account_status, lifecycle.
- `auth` — device_auth_keys, access_tokens/sessions, replay_cache, nonces.
- `licensing` — license_codes, license_redemptions, entitlements.
- `crypto` — identity_public_keys, signed_prekeys, one_time_prekeys, fallback_keys.
- `social` — contact_requests, contacts, blocks, invite_tokens.
- `messaging` — messages, delivery_receipts, sync_cursor, conversation_state.
- `attachments` — attachment_metadata, attachment_blobs, upload_sessions.
- `push` — push_registrations, push_jobs.
- `security` — security_events, rate_limit_buckets, idempotency_keys.
- `admin` — operational/admin-only records (not user content).

### 2. Security-relevant entity definitions

For each entity the implementation contract must specify: canonical internal `uuid` ID, `owner_account_id` (where applicable), `owner_device_id` (where applicable), foreign-key relationships, security-sensitive columns, server-readable vs encrypted-at-rest/ciphertext columns, retention policy, deletion behavior, uniqueness constraints, and concurrency-sensitive constraints.

At minimum the V1 schema must define:

| Entity | Owner | Key fields | Server-readable | Encrypted/ciphertext | Retention/deletion |
|--------|-------|------------|-----------------|----------------------|--------------------|
| `accounts` | account | `account_id`, `username`, `status`, `created_at` | account_id, username, status, timestamps | none at rest | deleted account: terminal tombstone, username retained blocked, user data purged per retention |
| `devices` | account/device | `device_id`, `account_id`, `status`, `device_auth_key_id`, `created_at`, `revoked_at` | all of the above | none | revoked device: status=REVOKED, no new auth, retained for audit/operational needs per B-014 |
| `device_auth_keys` | account/device | `key_id`, `account_id`, `device_id`, `public_key_pem`, `key_type`, `created_at`, `revoked_at` | public key, type, status | none | terminal on revoke |
| `access_tokens` / `sessions` | account/device | `token_hash`, `account_id`, `device_id`, `issued_at`, `expires_at`, `revoked_at` | token hash, account/device/timestamps | none | TTL 15m; revoked immediately; cleanup after expiry |
| `license_codes` | server | `license_id`, `lookup_hash`, `issued_at`, `valid_from`, `valid_until`, `revoked` | lookup hash, validity, status | none | never plaintext code; valid_until bounded by license duration; revocation possible |
| `license_redemptions` | account | `redemption_id`, `account_id`, `license_id`, `redeemed_at` | all | none | immutable record |
| `entitlements` | account | `entitlement_id`, `account_id`, `state`, `effective_from`, `expires_at` | all | none | updated by atomic license redemption/renewal; history per B-014 |
| `usernames` | account | `username`, `account_id`, `reserved_until`, `activated` | username, status, timestamps | none | released usernames are not automatically reused per B-003 |
| `registration_sessions` | account/grant | `registration_id`, `grant_hash`, `license_id`, `reserved_username`, `created_at`, `expires_at`, `committed_at` | grant hash, reserved names/timestamps | none | TTL 30m; abandoned grants release reservation atomically |
| `identity_public_keys` | account/device | `account_id`, `device_id`, `identity_revision`, `ed25519_public_key`, `curve25519_public_key`, `created_at` | public keys only | none | immutable; rotation is a new device/account in V1 |
| `signed_prekeys` | account/device | `prekey_id`, `account_id`, `device_id`, `public_key`, `created_at` | public key | none | replaced on rotation; old retained per fallback/retention rules |
| `one_time_prekeys` | account/device | `otk_id`, `account_id`, `device_id`, `public_key`, `key_state`, `created_at`, `claimed_at`, `claimed_by` | public key, state | none | see B-006 claim lifecycle |
| `fallback_keys` | account/device | `fallback_id`, `account_id`, `device_id`, `public_key`, `created_at`, `superseded_at`, `superseded_by` | public key | none | retained 15d after superseded |
| `messages` | account/recipient account | `message_id`, `conversation_id`, `sender_account_id`, `sender_device_id`, `recipient_account_id`, `recipient_device_id`, `ciphertext`, `message_type`, `session_type`, `state`, `created_at`, `expires_at` | message_id, conversation_id, routing, state, timestamps, ciphertext size | ciphertext | undelivered 14d; after delivered or expiry delete ≤1h |
| `delivery_receipts` | account/recipient | `receipt_id`, `message_id`, `recipient_account_id`, `recipient_device_id`, `received_at`, `read_at` (if enabled) | all | none | linked to message lifecycle |
| `sync_cursor` | account/device | `cursor_id`, `account_id`, `device_id`, `sync_seq`, `hash`, `expires_at` | all | none | 30d lifetime; safe replay of older cursor |
| `contact_requests` | account | `request_id`, `from_account_id`, `to_account_id`, `state`, `created_at`, `expires_at` | all | none | TTL 7d; block state may persist |
| `contacts` | account | `contact_id`, `owner_account_id`, `contact_account_id`, `trust_state`, `created_at`, `updated_at` | all | none | follows account deletion lifecycle |
| `blocks` | account | `block_id`, `owner_account_id`, `blocked_account_id`, `created_at` | all | none | follows account deletion |
| `push_registrations` | account/device | `registration_id`, `account_id`, `device_id`, `token_hash`, `token_encrypted`, `provider`, `created_at`, `updated_at`, `invalidated_at` | token hash | token ciphertext | follows device lifecycle; removed on revoke/delete |
| `push_jobs` | server | `job_id`, `account_id`, `device_id`, `provider`, `created_at`, `attempted_at`, `succeeded_at`, `failed_at` | operational hints only | none | TTL aligned with wake/delivery window |
| `attachment_metadata` | account | `attachment_id`, `owner_account_id`, `recipient_account_id`, `message_id`, `storage_object_id`, `ciphertext_size`, `ciphertext_hash`, `state`, `created_at`, `expires_at`, `received_ack_at` | opaque ids, size, hash, state, timestamps | none | see B-012 lifecycle |
| `attachment_blobs` | account/server | `blob_id`, `storage_object_id`, `owner_account_id`, `state`, `created_at`, `expires_at` | opaque id, owner, state | encrypted ciphertext in object storage | object storage lifecycle: unpublished 24h; after received ACK or expiry delete ≤1h |
| `upload_sessions` | account | `session_id`, `attachment_id`, `capability_hash`, `created_at`, `expires_at` | capability hash | none | TTL 2h (standard) / TUS resumable for >6MiB |
| `security_events` | server | `event_id`, `class`, `request_id`, `account_id`, `device_id`, `outcome`, `created_at` | class, request_id, ids, outcome, timestamp | none | operational retention per B-014; no plaintext/secrets |
| `rate_limit_buckets` | server/account | `bucket_id`, `class`, `account_id`, `device_id`, `coarse_signal_hash`, `window_start`, `count`, `created_at` | class, hashed signals, counts, window | none | TTL per rate-limit class; no raw IPs beyond 24h |
| `idempotency_keys` | account/device | `idempotency_id`, `account_id`, `device_id`, `method`, `path`, `idempotency_key`, `request_body_hash`, `response_ref`, `created_at` | all except body | request body hash | TTL 24h |
| `erasure_journal` | server | `journal_id`, `account_id`, `device_id`, `resource_class`, `resource_id`, `erased_at`, `reason` | class, ids, timestamp | none | retained beyond PITR horizon; replayed on restore |

### 3. One active device per account — DB-level enforcement

V1 enforces one active device per account at the database level.

The canonical enforcement model is a partial unique index on `devices(account_id)` where `status = 'ACTIVE'`.

In SQL-like terms (contract, not production SQL):

```
UNIQUE INDEX one_active_device_per_account
ON devices(account_id)
WHERE status = 'ACTIVE'
```

Concurrent registration or device-activation attempts are serialized. The first transaction to commit the `ACTIVE` device for an account wins; subsequent concurrent transactions on the same `account_id` fail with a uniqueness violation and must roll back cleanly. The application layer must not paper over this with last-write-wins.

If a device is `REVOKED` or `DELETED`, the account may, in a later separate authorized operation, activate a new device through the B-003 registration flow. V1 does not allow reusing an old `device_id` or Device Auth key.

### 4. Authenticated DB context

Each normal user request sets the database-scoped authorization context from the `AuthenticatedDeviceContext`. The implementation contract is that the context contains:

- `current.account_id`
- `current.device_id`
- `current.request_id`

These are set by the B-004 controller/security middleware before the repository enters a transaction. They are not set by client request body fields. RLS policies read from this context; they do not read from JSON.

The context lifetime is the request transaction. A connection pool must not leak context across requests; on checkout/reset the context is cleared and set for the current request.

If using Postgres `SET LOCAL` or equivalent transaction-local settings, the semantics are:

```
SET LOCAL anox.current_account_id = '<uuid>';
SET LOCAL anox.current_device_id = '<uuid>';
SET LOCAL anox.current_request_id = '<uuid>';
```

These are invisible to clients and cannot be overridden by client input. On transaction end (commit/rollback) they are discarded.

### 5. RLS model

RLS policies must be defined for every user-data table. The default policy posture is:

- `SELECT`: row is returned only if `current.account_id` equals the row's `owner_account_id` or, for recipient-visible rows (messages, delivery receipts, contact requests), the recipient's `account_id`.
- `INSERT`: allowed only with `owner_account_id` and any sender/recipient IDs matching the request context or explicitly derived by application logic (e.g., a message the authenticated device is sending to a known contact).
- `UPDATE`: allowed only on rows owned by `current.account_id` and, where applicable, `current.device_id`; service-owned operational columns (state, timestamps, expires_at) may be updated by authorized internal workers.
- `DELETE`: user-facing `DELETE` is generally restricted to explicit account/device deletion flows and erasure jobs; user-initiated message/attachment deletion is implemented as a state transition + erasure journal entry, not a literal row `DELETE`, where retention semantics require durable tracking.

Important: user-controlled request JSON does not create RLS context. The context is the verified `AuthenticatedDeviceContext`. RLS policies may use `current_setting('anox.current_account_id')` or equivalent; they must not trust request body values.

### 6. Server role model

Canonical V1 database/server roles:

| Role | Purpose | Allowed | Prohibited | RLS bypass | Secret type | Where credential lives |
|------|---------|---------|------------|------------|-------------|------------------------|
| `migrator` | Schema migrations, DDL, seed static reference data. | DDL on schema; seed non-secret data. | DML on user data; bypass RLS in production request paths. | NO for user data (migrations use ownership/elevated schema privileges, but do not rely on RLS bypass for row access). | DB password/certificate. | Secret manager, CI/CD with human approval, not in AI context. |
| `runtime` | User-facing B-004 request handlers. | `SELECT/INSERT/UPDATE` through RLS on user tables; `INSERT` security events. | Direct DML outside RLS; `DELETE` user data; `TRUNCATE`; DDL. | NO. | DB password/certificate per environment. | Secret manager, backend runtime environment. |
| `worker` | Background jobs: push, cleanup, erasure replay, idempotency expiry. | `UPDATE/DELETE` on operational/state rows as explicitly authorized by service code; `INSERT` journal. | Direct read of message ciphertext; user identity impersonation. | Allowed only on explicit worker tables or through security-definer functions scoped to specific tasks. | DB password/certificate. | Secret manager, worker runtime environment. |
| `admin_service` | Admin-plane operations, break-glass, audit reads. | Read operational records, write admin audit, manage non-content operational state. | Decrypt E2EE; impersonate user; read message plaintext. | Allowed only on admin/operational tables; never on user message/attachment content. | Strong credential + MFA. | Secret manager, admin bastion. |
| `monitor` | Read-only operational metrics, health, sanitized logs. | `SELECT` on non-sensitive operational views. | User data; plaintext; secrets. | NO. | Read-only credentials. | Secret manager, monitoring stack. |

### 7. Supabase `service_role` policy

Production user-facing request paths must **not** use Supabase `service_role` or any other RLS-bypass credential. Normal requests use the `runtime` role subject to RLS.

`service_role` or equivalent may be used only for:

- Database migrations under the `migrator` role with human approval.
- Narrowly scoped worker/admin tasks that are explicitly authorized and audited.
- Recovery/ops break-glass with human authorization and incident logging.

Constraints:

- `service_role` is never exposed to the B-004 public API runtime.
- Worker/admin use of `service_role` is logged as a security event.
- Credentials are stored in a secret manager and rotated.
- Blast radius is limited to the specific authorized operation.

### 8. Security-critical transaction boundaries

The following operations must be atomic. If any step fails, the transaction must roll back cleanly and the failure must be logged as a security event.

| Operation | Atomic unit | Rollback behavior |
|-----------|------------|-------------------|
| Account/device registration | Reserve license+username → create account → create active device → bind Device Auth key → create E2EE public-key rows → create entitlement. | Roll back all; release reserved license/username/grant. Idempotent retry uses same registration grant. |
| License redemption | Verify license → create/update entitlement → record redemption. | Roll back; license remains valid. |
| Username reservation/assignment | Reserve username (or claim during registration) → activate with account. | Roll back reservation; username not activated. |
| One-active-device activation | See §3. | Concurrent attempts fail with uniqueness violation. |
| OTK claim | `AVAILABLE → CLAIMED` for exactly one OTK. See B-006. | If claim fails, OTK stays AVAILABLE. |
| Message durable state transition | Server persistence of ciphertext, recipient queue, and sender outbox state transition must be atomic. | Roll back; client can retry with same idempotency key. |
| Attachment metadata/blob state transition | `upload_sessions` + `attachment_metadata` + `attachment_blobs` linkage. | Roll back; blob remains unpublished. |
| Account/device revocation | Revoke device → revoke active sessions/tokens → remove push registration → write erasure journal for queued data. | Roll back if any step cannot be durably recorded; revocation is a terminal state transition. |
| Deletion/erasure journaling | Account deletion writes terminal erasure intent, then propagates deletions to dependent rows and object storage. | Roll back if terminal intent not durable; once committed, deletions are journaled and replayed after restore. |

---

## B-006 — vodozemac Key Distribution (amended v1.3-f02)

The following items supersede `docs/authority/B025/TRACK_B/B006_VODOZEMAC_KEY_DISTRIBUTION.md` for the listed clauses and add the `DB-SCHEMA-V1-FROZEN` OTK/fallback contract.

### 1. OTK state model

Canonical server states for one-time prekeys:

- `AVAILABLE` — published, not yet claimed, valid.
- `CLAIMED` — atomically assigned to exactly one claimant; consumed.
- `PUBLISHING` — client has uploaded but server has not yet ACKed durability (optional transient state; client must not mark as published before ACK).
- `EXPIRED` — older than the allowed retention window; not reusable.

State transitions:

- `PUBLISHING → AVAILABLE` after server ACK of durable persistence.
- `AVAILABLE → CLAIMED` only through an atomic claim.
- `CLAIMED` is terminal; a consumed OTK never returns to `AVAILABLE`.
- `AVAILABLE → EXPIRED` by retention/cleanup job.

### 2. Atomic claim

OTK claim is `SELECT ... FOR UPDATE SKIP LOCKED` or equivalent on a row in `AVAILABLE` state, then `UPDATE` to `CLAIMED` with `claimed_by` set to the authenticated claimant's account/device. The claim returns exactly one `AVAILABLE` public key. If none is `AVAILABLE`, the operation falls through to fallback key logic.

Race: two concurrent claims must not claim the same OTK. The first commit wins; the second re-queries. `AVAILABLE → CLAIMED` is a one-way transition enforced by state check and row lock.

### 3. OTK batch publication and ACK

- Client generates a batch of OTK public keys locally and persists them in the local Account before upload.
- Client uploads the batch to the server.
- Server durably inserts rows into `one_time_prekeys` with state `PUBLISHING`.
- Server returns an ACK.
- Client marks the local keys as `published` in the local Account only after receiving the ACK.
- Retry of the same batch is idempotent: same `otk_id`/public key combination must be accepted; same `otk_id` with a different public key is a security error and must be rejected and logged.

### 4. OTK replenishment

V1 target: client publishes new OTKs when the local `AVAILABLE` server count falls below 50% of the configured maximum `max_number_of_one_time_keys`.

This threshold is the **recommended operational threshold**, not a strict exact value. The client may replenish earlier; the server may accept the published batch at any time. The server does not enforce a specific client-side threshold, but the client must not allow the pool to reach zero under normal operation.

### 5. Fallback key lifecycle

- One fallback key per account/device is published alongside OTKs.
- Fallback key is used only when no `AVAILABLE` OTK exists for the target device.
- A fallback key may be used multiple times by design (vodozemac fallback semantics).
- When the client publishes a new fallback key, the server marks the previous fallback as `superseded_at = now` and retains it for 15 days (14-day delivery window + 24h margin).
- After 15 days the old fallback key may be removed from the server's `fallback_keys` table; object storage of any unused local material follows local retention.

### 6. OTK/fallback exhaustion

Session establishment attempts the following order:

1. If an `AVAILABLE` OTK exists, claim it and use it in the PreKey message.
2. If no OTK is `AVAILABLE` but a valid fallback key exists, use the fallback key.
3. If neither is available, the session-establishment request must fail/queue. The server returns an explicit error indicating unavailability; the client may retry later after replenishment.

No silent downgrade to plaintext or custom key agreement.

---

## B-007 — API + Wire Protocol (amended v2.0-f02)

The following items supersede `docs/authority/B025/TRACK_B/B007_API_WIRE.md` for the listed clauses and freeze the V1 endpoint inventory.

### 1. Versioning policy

V1 wire protocol is under `/v1`. Backward-incompatible changes require a new major version path (`/v2`). Servers must reject unsupported versions with a stable `unsupported_version` error. Clients must tolerate unknown response fields. Version negotiation is not dynamic; a client supporting only `/v1` calls `/v1` paths.

### 2. Endpoint inventory

All V1 endpoints are under `https://<api-host>/v1`. Admin endpoints are under a separate origin. The following endpoint classes are required.

| Class | Endpoints (contract, not implementation) | Auth | DPoP | Idempotency | Rate class |
|-------|------------------------------------------|------|------|-------------|------------|
| Registration | `POST /v1/registration/begin` (if applicable), `POST /v1/registration/validate-username`, `POST /v1/registration/validate-license`, `POST /v1/registration/submit-device-auth`, `POST /v1/registration/commit` | None / PoP for commit | No / Yes for commit | Yes (commit) | registration |
| Device Auth | `POST /v1/auth/challenge`, `POST /v1/auth/token`, `POST /v1/auth/revoke` | Device Auth proof / token | Yes | Yes (token issuance by nonce) | auth |
| License | `GET /v1/license/entitlement`, `POST /v1/license/redeem` | token | Yes | Yes (redeem) | license |
| Identity keys | `GET /v1/keys/identity/:account_id?device_id=`, `POST /v1/keys/identity` (publish), `POST /v1/keys/signed-prekey`, `POST /v1/keys/one-time-prekeys`, `POST /v1/keys/fallback-key` | token | Yes | Yes (publish) | key-dist |
| OTK claim | `POST /v1/keys/claim` | token | Yes | No (claim is stateful) | key-claim |
| Messaging | `POST /v1/messages`, `GET /v1/messages/sync` (or `/v1/sync`), `POST /v1/messages/:message_id/receipt` | token | Yes | Yes (submit) | messaging |
| Contacts / lookup | `POST /v1/contacts/requests`, `POST /v1/contacts/requests/:request_id/accept`, `POST /v1/contacts/requests/:request_id/reject`, `GET /v1/contacts`, `POST /v1/contacts/blocks` | token | Yes | Yes (request send) | social |
| Push | `POST /v1/push/token`, `DELETE /v1/push/token` | token | Yes | Yes | push |
| Attachments | `POST /v1/attachments/reserve`, `POST /v1/attachments/:attachment_id/commit`, `GET /v1/attachments/:attachment_id/download`, `POST /v1/attachments/:attachment_id/received`, `DELETE /v1/attachments/:attachment_id` | token | Yes | Yes (reserve/commit) | attachment |
| Lifecycle | `POST /v1/devices/:device_id/revoke`, `POST /v1/account/delete`, `GET /v1/account/status` | token | Yes | Yes (revoke/delete) | lifecycle |

Each endpoint row must be expanded into a per-endpoint contract with: method, path, auth required, DPoP required, account/device/entitlement state requirement, request schema reference, response schema reference, idempotency key scope, rate-limit class, privacy-sensitive fields, important errors, transactional behavior.

### 3. Idempotency

Idempotency applies to mutating endpoints.

- `Idempotency-Key` is a client-generated UUIDv4 scoped to `device_id + HTTP method + path + key`.
- Server stores the request body SHA-256 hash and a response reference for 24h.
- Replaying the same idempotency key with an identical request body returns the cached response (or a fresh response with the same outcome if idempotency semantics allow).
- Replaying with a different request body under the same key returns `409 Conflict`.
- Idempotency is an application-level duplicate-operation guard, distinct from DPoP replay protection. DPoP replay protection is a security boundary (see B-002/B-004). Both may coexist: a legitimate retry of a valid idempotent operation must use a fresh DPoP proof.

### 4. Concurrency and race semantics

The server must handle the following races with explicit, deterministic behavior:

| Race | Behavior |
|------|----------|
| Two registration commits | One wins the active-device uniqueness constraint; the other fails with a generic, anti-enumeration-safe error. |
| Two license redemptions | One wins per license code; the other fails `already_redeemed` or equivalent generic error. |
| Concurrent username assignment | Reservation/grant is checked; if both attempt to activate the same username, one wins and the other fails with `conflict`. |
| Two OTK claims | Atomic claim ensures distinct OTKs; if pool exhausted, fallback logic. |
| Duplicate message submission | Idempotency key + dedup by message_id/ciphertext hash. |
| Concurrent device revoke + authenticated operation | Revoke transaction serializes; operations after commit fail with `device_revoked`. |
| Delete + incoming message | Account deletion writes terminal intent first; subsequent message acceptance for the account is rejected. |
| License expiry/renewal race | Entitlement state is authoritative; renewal is atomic and effective from server time. |

No "last write wins" for security-critical identity state.

### 5. Error model

Stable V1 security-relevant error classes (RFC9457 problem JSON with `code` and `request_id`):

- `unauthenticated` — no or invalid access token.
- `invalid_dpop` — DPoP proof validation failed.
- `replay_detected` — DPoP jti/nonce replay.
- `authorization_denied` — authenticated but not authorized for this resource.
- `device_revoked` — device has been revoked.
- `account_suspended` — account suspended.
- `entitlement_expired` — license/entitlement expired.
- `invalid_registration_state` — registration flow out of order or grant expired.
- `idempotency_conflict` — same idempotency key with different body.
- `rate_limited` — rate limit exceeded.
- `otk_unavailable` — no OTK/fallback available.
- `resource_gone` — resource deleted or expired.
- `not_found` — generic not found (do not reveal existence where anti-enumeration applies).
- `unsupported_version` — API version not supported.

### 6. Anti-enumeration on API

The following surfaces must use uniform, existence-hiding responses:

- Username availability / user lookup (unauthenticated and authenticated).
- Registration validation (license/username).
- Contact request to non-existent or blocked user.
- License validation/redemption errors.

Where an operation is genuinely not authorized, the response must be indistinguishable from `not_found` for unprivileged callers. Timing must be normalized where practical: implement early-exit constants or cached results to avoid timing oracles.

---

## B-011 — Push + Offline Queue (amended v1.3-f02)

The following items supersede `docs/authority/B025/TRACK_B/B011_PUSH_OFFLINE.md` for the FCM token privacy contract.

### 1. FCM token threat model

The FCM token must be available to the backend in a usable form to send a push. Server-side reversible encryption of the token protects against a database-only leak without the encryption key, but it does **not** protect against a fully compromised backend that also holds the decryption key. Therefore architecture must not claim that FCM tokens are protected from the push backend itself.

### 2. FCM token controls

- Store the token encrypted at rest where practical; keep the decryption key in the secret manager, separate from the database.
- Never log the full token; redact from error output and debug UI.
- Never expose the token in admin UI by default.
- Do not use the token for analytics, device grouping, or unrelated correlation.
- Access is limited to the push delivery worker.
- Remove or replace stale tokens promptly.
- Operational access to the token is audited where infrastructure supports it.
- One active token per device; logout, device revoke, or token invalidation removes/replaces it.

---

## B-012 — Attachments (amended v1.1-f02)

The following items supersede `docs/authority/B025/TRACK_B/B012_ATTACHMENTS.md` for the attachment lifecycle.

### 1. Attachment lifecycle states

Canonical server states for an attachment:

- `RESERVED` — upload authorized, no blob yet.
- `UPLOADED` — blob uploaded to object storage, not yet linked to a message.
- `PUBLISHED` — linked to a message and available for authorized recipient fetch.
- `DELIVERED` — recipient downloaded and sent `/received` ACK.
- `EXPIRED` — message/attachment TTL reached.
- `DELETED` — user/account deletion triggered purge.
- `ORPHANED` — upload completed but message association failed; subject to cleanup.

### 2. Attachment revocation and deletion

- Device revoke does **not** automatically delete attachment blobs that may have been legitimately received by another device or that belong to a multi-recipient message. V1 is single-device per account, but attachments may have been downloaded by the recipient.
- Account deletion triggers explicit attachment purge after the erasure journal is durably written.
- Message expiry triggers attachment blob expiry after the message's retention window.
- Orphaned uploads are cleaned after 24h.
- Attachment blob deletion in object storage follows the `≤1h` target after `received` ACK or expiry.

### 3. Orphaned upload cleanup

- Upload authorized but never completed: `RESERVED` + `upload_sessions` expire after 2h (standard) / TUS session TTL.
- Completed blob but message submission fails: attachment may be `ORPHANED`; cleanup job reclaims after 24h.
- Message deleted before attachment association finalizes: same as orphaned.

---

## B-014 — Privacy / Retention / Logging (amended v1.4-f02)

The following items supersede `docs/authority/B025/TRACK_B/B014_PRIVACY_RETENTION_LOGGING.md` for backup/PITR, deletion and restore semantics.

### 1. Backup/PITR residual retention

Live database deletion and backup/PITR residual retention are explicitly separated.

- `PITR horizon`: 7 days (minimum operational recovery window). Point-in-time recovery can restore the database to any point within 7 days.
- `Base backup retention`: 30 days (full backups).
- `Object-storage backup retention`: 30 days, encrypted.

If a user-deleted account/message/attachment is restored from a backup within the PITR/base-backup window, the residual data exists until the backup ages out. Privacy documentation must state this honestly; it must not claim instant global deletion.

### 2. Erasure journal

An `erasure_journal` table records explicit deletion/erasure events for resources that must remain deleted across restores.

- On account deletion, message expiry, or attachment deletion, a journal entry is written before the live row is removed.
- On restore from PITR/base backup, a replay job applies journal entries in order to re-delete resources that were deleted after the restore point.
- Journal retention must exceed the longest backup retention (≥31 days to cover 30-day base backup). For account deletion the journal is retained until the account is permanently purged and all backups beyond the account deletion time have expired.
- Replay is idempotent; a resource that does not exist after restore is a no-op.
- Restore ordering: restore database → replay erasure journal → re-enable user traffic.

### 3. Backup access

- Backups are encrypted.
- Backup decryption capability is restricted to operational roles with human approval.
- Backup encryption keys are in the secret manager; no AI access.
- Backup restoration is auditable.

### 4. PITR restore effects

A PITR restore may resurrect data that was live at the restore point and deleted after it. The erasure journal replay is the primary defense. The privacy guarantee is: live database deletion is immediate; backup/PITR residual data is bounded by the retention windows above and is removed when backups age out or replayed by the erasure journal.

---

## B-015 — Abuse / Rate Limits (amended v1.1-f02)

The following items supersede `docs/authority/B025/TRACK_B/B015_ABUSE_RATE_LIMITS.md` for anti-enumeration, rate-limit identifiers and IP handling.

### 1. Anti-enumeration response uniformity

For registration, username/license validation, user lookup and contact request surfaces, the server must produce indistinguishable responses for:

- non-existent username/account
- blocked/inaccessible account
- existing but non-public account
- suspended/revoked account

Where exact UX needs conflict (e.g., a client needs to know a contact request was rejected vs not found), the response may carry a coarse, privacy-safe status only visible to an authenticated authorized party.

### 2. Rate-limit identifiers

Rate-limit dimensions are:

- Authenticated: `account_id`, `device_id`.
- Unauthenticated: coarse source-IP bucket with short retention (≤24h for raw IP, per B-014), hashed/pseudonymized where practical.
- Endpoint class: registration, auth, license, key-dist, messaging, social, push, attachment, lifecycle.
- Abuse signals: repeated 4xx/5xx patterns, DPoP replay attempts, invalid token attempts.

Do not create a permanent cross-service fingerprint.

### 3. IP handling

- Raw IP is not retained beyond 24h for rate-limiting or abuse purposes.
- Hashed IP identifiers, if used, are keyed with rotating keys; retention ≤24h.
- IP alone is not treated as identity.
- Hashing or pseudonymization alone does not make an IP anonymous; privacy documentation must not claim so.

---

## B-016 — Production Infrastructure (amended v1.3-f02)

The following items supersede `docs/authority/B025/TRACK_B/B016_PRODUCTION_INFRASTRUCTURE.md` for backup/restore/PITR infrastructure.

### 1. Backup and PITR infrastructure

- PostgreSQL PITR is enabled with WAL archiving.
- Base backups are taken at least daily; retention 30 days.
- Object-storage backups are encrypted and retained 30 days.
- Backup encryption keys are in the secret manager and rotated/recovered with a named owner.
- Restore testing is required before RC (release candidate) under B-022/B-023.
- A restore from backup must run erasure-journal replay before public traffic is accepted.

### 2. Backup access boundary

- Backup decryption is restricted to `admin_service` + break-glass with human authorization.
- Backup access is logged as a security event.
- No AI or worker has routine backup decryption access.

---

## ULTIMATE MAIN ARCHITECTURE — Server Trust Boundaries (amended v1.2)

The following items amend `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` §Server/Backend.

### 1. Server-side trust boundaries

V1 server-side architecture has three primary trust boundaries:

- **Public API / B-004** — receives DPoP-bound requests and produces `AuthenticatedDeviceContext`.
- **Database / B-005** — stores user data with RLS and role-based least privilege.
- **Backup/PITR / B-014 + B-016** — residual encrypted data with bounded retention and erasure-journal replay.

The push provider (FCM) and object storage are external operational dependencies. E2EE content is opaque to all server components.

### 2. B-004 ↔ B-005 boundary

B-004 may pass the `AuthenticatedDeviceContext` into the database transaction context, but it may not pass client-controlled identity values. B-005 RLS policies use the transaction-local context, not request JSON.

### 3. B-004 ↔ B-007 boundary

B-007 endpoints define the contract; B-004 controllers enforce it. Endpoint semantics, auth requirements, idempotency and error classes are authoritative in B-007.

### 4. B-005 ↔ B-006 boundary

The `crypto` schema tables (identity public keys, OTKs, fallback keys) store only public material. OTK claim state is enforced by B-005 transactions. B-006 defines the client/server lifecycle. B-005 does not interpret E2EE keys.

### 5. B-005 ↔ B-008 boundary

`messaging` schema stores ciphertext and routing metadata only. B-008 defines delivery, `DELIVERED` semantics and sync. B-005 provides durable, RLS-protected persistence.

---

## Cross-Domain Consistency Matrix

| Pair | Status | Reason |
|------|--------|--------|
| B-002 ↔ B-004 | CONSISTENT | B-004 verifies DPoP and binds tokens per B-002. |
| B-002 ↔ B-005 | CONSISTENT | Device auth keys and replay cache stored in `auth` schema; no key material persisted in B-005. |
| B-003 ↔ B-004 | CONSISTENT | Registration pipeline defined in B-004 uses B-003 identity/license rules. |
| B-003 ↔ B-005 | CONSISTENT | Account/device/entitlement schema in `core`, `licensing` matches B-003. |
| B-004 ↔ B-005 | CONSISTENT | `AuthenticatedDeviceContext` maps to DB transaction context; RLS policies use it. |
| B-004 ↔ B-007 | CONSISTENT | B-007 endpoint inventory and auth requirements implemented by B-004. |
| B-005 ↔ B-006 | CONSISTENT | `crypto` schema stores public OTK/fallback state; B-006 defines lifecycle. |
| B-005 ↔ B-008 | CONSISTENT | `messaging` schema stores ciphertext/delivery per B-008. |
| B-006 ↔ B-007 | CONSISTENT | OTK/fallback endpoints and claim semantics defined in B-007. |
| B-006 ↔ B-008 | CONSISTENT | Session-init material feeds into B-008 message Olm encryption. |
| B-008 ↔ B-012 | CONSISTENT | Attachment messages link to B-012 attachment lifecycle. |
| B-014 ↔ B-016 | CONSISTENT | Backup/PITR retention and erasure journal in B-014 implemented by B-016 infrastructure. |

---

## Milestone Security Review Flags

The following findings involve trust boundaries that must be explicitly covered by the next scheduled Security Architecture milestone review:

- `ANOX-MAINARCH-003` — server ↔ DB/RLS trust boundary: the `DB-SCHEMA-V1-FROZEN` contract is the authoritative spec, but the next Security Architecture milestone must verify that the contract maps to a reviewable RLS/role implementation.
- `ANOX-MAINARCH-007` — server ↔ backup/PITR trust boundary: the honest backup/PITR residual retention and erasure-journal contract is frozen, but the next Security Architecture milestone must verify the actual DR/restore procedure and retention.

These flags are recorded in `docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md` and `docs/workforce/registries/findings.jsonl`.

---

## Historical provenance

This V1.2 amendment does not modify the B-025 historical snapshot in `docs/authority/B025/TRACK_B/`. The B-025 snapshot files remain immutable. The `B_FREEZE_REGISTRY.md` and `AUTHORITY_INDEX.md` record the amended current versions.


