# B-013 — Account / Device / Local-State Lifecycle
**Status:** FROZEN v1.2

Distinguish app lock, network logout, entitlement expiry, suspension, device revoke, local wipe/reset, account deletion, lost/stolen device, uninstall/reinstall and Keystore/DB corruption.

- App lock/biometric is local access control only; failed attempts do not rotate/revoke E2EE or wipe automatically.
- Logout is network-session termination only: revoke access token/session/push registration, preserve Device Auth key, E2EE identity/sessions, SQLCipher DB/history/contacts. Re-auth on same device uses Device Auth.
- Entitlement expiry preserves local state/history; normal messaging/sync/contact/attachment operations are restricted while renewal/status/security operations remain available through restricted Device Auth flow. Pending server ciphertext continues only until normal TTL.
- Account SUSPENDED is reversible; REVOKED/DELETED terminal. Device ACTIVE→REVOKED terminal. Effective precedence: DELETED > REVOKED > SUSPENDED > entitlement expired > active.
- Device revoke prevents new auth/push/delivery; in one-device V1 revoking sole device strands old account. No replacement device binding.
- Local wipe always works offline: stop workers/notifications; attempt authenticated server revoke/push removal when reachable; close DB; delete Device Auth key, K_DB/K_STATE wrapping material, DB/WAL/SHM, crypto state, encrypted attachments/temp/tokens. Do not make local deletion depend on server response.
- Lost/stolen device has no account/crypto recovery. Support may handle a security report/administrative suspension under operations policy but may not transfer identity/keys/username trust.
- Uninstall/factory reset/app-data loss starts first-run on reinstall and strands old account because Keystore/private state is gone.
- DeviceAuth invalidation prevents network auth but may leave locally decryptable history if DB keys remain; no silent new DeviceAuth under old account. Missing/corrupt K_DB/K_STATE fails closed and offers explicit local reset/new-account path only.
- Account deletion requires strong authenticated destructive action, writes terminal erasure intent durably before DB deletion, revokes sessions/device/push, purges server queued data per retention, then forces local wipe. No delete-for-everyone of recipient local copies.
