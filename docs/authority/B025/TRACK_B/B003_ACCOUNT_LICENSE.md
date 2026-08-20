# B-003 — Account + License
**Status:** FROZEN v1.4

- No password, mandatory email/phone/SMS.
- `account_id` and `device_id`: server UUIDv4; one active device DB-enforced.
- Username: lowercase ASCII `[a-z0-9_.]`, 3–32; reserved system names; no directory.
- V1 username is immutable after successful activation; previously activated usernames are not automatically reused.
- Standard licenses: 30/90/180 days. One-year superseded; historical one-week trial is not a general V1 license.
- License code: `anox-XXXX-XXXX-XXXX`, 12 unambiguous CSPRNG characters. Plaintext shown once; canonical lookup is versioned HMAC-SHA-256 under server secret lookup key.
- Registration: reserve license+username → registration session/grant → register Device Auth with PoP → create E2EE locally → upload public E2EE material → atomic final commit account/device/key bindings/entitlement redemption.
- Registration id UUIDv4; registration grant 256-bit/hash-only; grant TTL 30m. Abandoned reservation is released.
- Account states: ACTIVE/SUSPENDED/REVOKED/DELETED. Device ACTIVE/REVOKED. Entitlement ACTIVE/EXPIRED/REVOKED.
- Renewal extends from existing expiry if active; expired renewal starts from current server time. Renewal preserves identities.
- Commit is idempotent; crash-resume before commit is transaction resume, not account recovery.
