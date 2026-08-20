# B-004 — Backend Service Architecture
**Status:** FROZEN

- Modular monolith. Public/provider/backend/DB-storage/Android trust zones separated.
- Android → HTTPS `/v1` → anoX backend → PostgreSQL/Supabase/private storage. No direct privileged Supabase from APK.
- Pipeline: TLS → Device Auth → DPoP/replay → validation → authz → abuse/rate → business logic → repository → transaction.
- Server-derived `AuthenticatedDeviceContext` includes account/device/session/device-auth-key/entitlement/request ID. Never trust identity from JSON.
- Controller → application service → repository → DB. Parameterized SQL; allowlist dynamic identifiers.
- RLS defense in depth, runtime DB role nonprivileged, transaction boundaries explicit.
- Logs omit plaintext, token/license plaintext, DPoP proofs and full bodies. Sanitized errors; fail closed.
- Admin plane has separate authz/roles; admin can manage operational records but never decrypt chats or recover E2EE keys.
- Secrets only through environment/secret manager; DEV/STAGE/PROD separated; expand/migrate/contract DB migration approach.
- Durable jobs/queues are plaintext-free. Realtime/push are hints, not truth.
