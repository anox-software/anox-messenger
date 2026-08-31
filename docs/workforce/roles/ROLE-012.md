# ROLE-012: Platform / SRE / DR

**Activation class:** dormant  
**AI allowed:** true

**Mission:** Perform platform engineering, site reliability, and disaster recovery preparation.

**Authority:** Platform engineering, site reliability, and disaster recovery.

**Allowed responsibilities:**
- Maintain platform configs, SRE runbooks, DR plans, and monitoring.
- Produce E2/E3 evidence for platform and DR readiness.
- Escalate security or production impact.

**Prohibited responsibilities:**
- Hold production credentials or break-glass secrets.
- Release or remote write to production.
- Access D4-class material.

**Writable/read-only expectations:** Write to platform docs, IaC, and runbooks; read-only on production state.

**Required inputs:** Authorized Task Package, platform architecture, SLO/DR requirements.

**Required outputs:** Platform configs, runbooks, DR plan, E2/E3 evidence, Agent Run record.

**Escalation path:** ROLE-009 for security/privacy; ROLE-001 for production exceptions.

**Evidence expectations:** E2 for platform changes; E3 for DR validation.

**Independence requirements:** Independent review for production-impacting changes.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** build, appsec, architecture/privacy, observability.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
