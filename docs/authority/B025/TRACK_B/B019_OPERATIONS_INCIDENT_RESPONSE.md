# B-019 — Operations + Incident Response
**Status:** FROZEN

- Production has named primary/secondary on-call and out-of-band communication, at least two authorized security operators and two SUPER_ADMIN-capable owners, each with approved physical FIDO2 keys.
- Admin uses layered identity-aware access + independent hardware MFA + anoX WebAuthn + RBAC + step-up + CSRF defenses. Shared admin password is not acceptable.
- Break-glass procedure exists, is tightly controlled/audited and rehearsed before production.
- Mandatory runbooks include DB compromise, backend/node compromise, GitHub/supply-chain compromise, signing incident, secret rotation, privacy breach, backup restore, disaster recovery, provider outage and account/data erasure reconciliation.
- Alerts must prove delivery for backend/DB/Redis/backup/security spikes. Status page should remain communicative during backend failure.
- Backups encrypted; integrity checks and full restore rehearsal required. Restore procedure must replay terminal erasure journal/retention reconciliation to prevent resurrection of deleted data.
- Account deletion terminal intent is written durably before primary DB delete transaction; operational recovery must finish deletion after crash/restore.
- Vulnerability disclosure contact/policy and `security.txt` are production requirements. Serious audit/incident findings use immediate escalation and evidence preservation without logging user plaintext/private keys.
