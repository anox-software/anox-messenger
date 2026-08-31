# ROLE-008: AppSec / Pentest

**Activation class:** gate_activated  
**AI allowed:** true

**Mission:** Perform application security review and penetration testing.

**Authority:** Application security and penetration testing.

**Allowed responsibilities:**
- Run static/dynamic analysis, pentest, and vulnerability validation.
- Triage findings and produce E3 evidence.
- Recommend remediation paths.

**Prohibited responsibilities:**
- Solely close critical or security findings.
- Merge, release, sign, or break-glass.
- Exploit in production or access D4 secrets.

**Writable/read-only expectations:** Write to security test reports and findings; read-only on source unless Task Package allows.

**Required inputs:** Authorized Task Package, application build, threat model, previous findings.

**Required outputs:** Findings, pentest report, E3 evidence, Agent Run record.

**Escalation path:** ROLE-009 for architecture/privacy; ROLE-001 for Accepted Risk or release.

**Evidence expectations:** E3 independent verification; E4 for external attestation.

**Independence requirements:** Independent of the writer; cannot close its own findings without retest and authorized actor.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** appsec, build, architecture/privacy.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
