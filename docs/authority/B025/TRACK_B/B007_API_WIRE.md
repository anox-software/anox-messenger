# B-007 — API + Wire Protocol
**Status:** FROZEN v1.9

- HTTPS `/v1`; admin plane separate origin. snake_case UTF-8 JSON. Successful responses typed/direct.
- UUIDv4 lowercase external IDs; RFC3339 UTC timestamps; DPoP `iat` numeric; JSON binary base64url-no-padding unless external standard says otherwise.
- Reject unknown request fields; clients tolerate unknown response fields. No secrets in query parameters.
- Server UUIDv4 `X-Request-ID`.
- DPoP uses RFC9449 `htu` semantics and B-002 proof requirements.
- Registration/license/auth/account/device/entitlement/crypto/contact/message/sync/receipt/push/attachment endpoints follow frozen domain specs. No global user search, GraphQL privilege bypass or direct privileged Supabase.
- Contact API supports requests, accept/reject/cancel, contacts, invites, blocks.
- Attachment API: create, commit, download capability, received ACK and delete only where lifecycle permits.
- Pagination default 50/max100.
- `Idempotency-Key`: UUIDv4; scope device+method+route+key; generic retention 24h; SHA-256 exact request-body fingerprint; changed body under same key = 409; retry uses fresh DPoP proof.
- RFC9457 problem JSON with stable code + request_id, anti-enumeration-safe errors.
- Global JSON body cap 256 KiB; attachments go to object storage.
- Sync cursor: random 32-byte opaque base64url token, hash server-side, bound to account/device, 30d lifetime; safe replay of older valid cursor after client crash.
