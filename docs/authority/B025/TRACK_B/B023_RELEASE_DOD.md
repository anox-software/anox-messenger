# B-023 — V1 Release Definition of Done
**Status:** FROZEN v1.1

Production release is GO/NO-GO. A build compiling is not a release. All V1 scope, production backend/DB/infra, security controls, migration/retention jobs, tests, audit, signing/update path, operations and legal/privacy readiness must be complete for the exact artifact set.

Hard gates include: security-critical architecture opens=0; protected/green `main`; current toolchain/Android target release review; Device Auth hardware-backed production behavior; complete registration/license; backend authz/RLS; message/verification/push/attachment/lifecycle semantics; retention/abuse jobs; no hidden recovery; no behavioral analytics; supply-chain controls/SBOM; offline hardware release signing and recovery rehearsal; physical GrapheneOS matrix including no-Google mode; admin hardware MFA and at least two operators; on-call/runbooks/break-glass; backup restore and pre-release DR exercise; B-021 required tests all PASS; B-022 final audit/retest with no unresolved Critical/High/core-security Medium; evidence-backed privacy/marketing claims only.

Release evidence binds exact commit, signed APK hash/signer, backend artifact, migrations, IaC, SBOM, security test report, audit references, GrapheneOS/DR/signing-recovery reports and human GO approvals. AI alone cannot approve Production.
