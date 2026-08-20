# B-022 — Independent Security Audit
**Status:** FROZEN

Mandatory before commercial Production V1. At least two independent named reviewers collectively covering applied crypto/E2EE, Android, Rust/JNI, backend/API/Postgres/infra/supply-chain. White-box primary plus grey/black-box testing.

Scope includes architecture/trust, Android/local security, JNI/Rust/vodozemac, SAS, attachment secretstream, Device Auth/DPoP, registration/license, backend/API/RLS, messaging/sync, contacts, lifecycle/no-recovery, privacy/retention, push/no-Google, infra/admin, CI/supply-chain, signing/updates, backup/DR/operations.

Audit is bound to exact commit/APK/backend/schema/IaC/spec versions. Critical/High and core-security Medium findings block release. Remediation status is not independently VERIFIED until auditor retest. Architecture-changing fixes require ADR + spec version bump + tests + retest. Public audit summary is required for strong commercial security claims; do not claim OWASP/NIST/GrapheneOS certification merely from using those standards/test methods.
