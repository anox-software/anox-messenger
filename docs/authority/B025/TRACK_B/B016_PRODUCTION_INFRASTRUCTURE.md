# B-016 — Production Infrastructure
**Status:** FROZEN v1.2

- Separate DEV/STAGING/PROD with different DB/storage/Redis/FCM/secrets/hostnames/credentials; never production data in staging.
- Public API is fronted by hardened edge/reverse-proxy protection; backend origins are not directly exposed. Public SSH is closed; administrative access is through controlled private/identity-aware path.
- At least two backend instances for production availability; shared critical state such as DPoP replay, distributed abuse limits and durable jobs cannot be process-local.
- PostgreSQL/Supabase runs with encrypted transport, network restrictions, least-privilege DB roles/RLS and tested migrations/PITR/backups. Private object storage only.
- Redis/shared cache may hold only operational non-plaintext state according to classification; never E2EE private keys/message plaintext.
- Production secrets in a dedicated secret manager with per-service credentials, rotation/recovery owner and least privilege.
- Admin surface separated from user API and protected by identity-aware access plus anoX WebAuthn/hardware MFA/RBAC/step-up/CSRF protections.
- Monitoring/alerts, status endpoint/page, clock synchronization/drift monitoring, backup/restore and incident access are production requirements.
- Actual production domains/provider IDs/regions/accounts are configuration freeze evidence before RC, not hard-coded architecture secrets.
