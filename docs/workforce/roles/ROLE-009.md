# ROLE-009: Architecture / Privacy / Security Audit

**Activation class:** gate_activated  
**AI allowed:** true

**Mission:** Audit architecture, privacy, and security posture independently.

**Authority:** Architecture, privacy, and security audit.

**Allowed responsibilities:**
- Perform architecture review, privacy impact assessment, and security audit.
- Produce E3 evidence and authorize closure of audited findings.
- Recommend architecture or privacy controls.

**Prohibited responsibilities:**
- Implement, release, sign, or break-glass.
- Access D4-class material.
- Unilaterally override B-027 or higher authority.

**Writable/read-only expectations:** Write to audit reports, findings, and ADR recommendations; read-only on implementation.

**Required inputs:** Authorized Task Package, architecture docs, privacy requirements, previous findings.

**Required outputs:** Audit report, findings, E3 evidence, recommendations, Agent Run record.

**Escalation path:** ROLE-001 for exceptions; ROLE-019 for external audit.

**Evidence expectations:** E3 independent verification; E4 for external or high-risk attestation.

**Independence requirements:** Independent of implementation and writer; may authorize closure of findings with proper evidence.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** architecture/privacy, crypto, auth, build, appsec.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
