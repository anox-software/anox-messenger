# B-002 — Device Authentication
**Status:** FROZEN v1.1

- Device Auth is independent from E2EE, account identity and license.
- P-256 / ES256 Android Keystore private key; non-exportable; StrongBox preferred, TEE fallback accepted in production; software-only fails production registration.
- No per-use biometric requirement and no mandatory remote attestation V1.
- RFC9449-style DPoP rather than custom request signatures.
- Opaque 256-bit access token; server stores SHA-256 only; TTL 15 minutes; no refresh token.
- Token issuance uses fresh nonce. Protected requests use `Authorization: DPoP <token>` plus DPoP proof with `jti`, `htm`, `htu`, `iat`, `ath` as applicable.
- `jti`: at least 128 random bits; `iat` acceptance ±120s; shared replay cache 5m.
- Token bound to session/device/key. Access token memory-only preferred.
- Logout revokes session/token but keeps E2EE and Device Auth key. Device revoke blocks authentication.
- Device Auth key invalidation is terminal for old-account network access in V1; do not silently generate replacement key.
- Expired entitlement may use restricted Device-Auth+nonce flow for renewal/security operations, not normal messaging.
