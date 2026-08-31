# ROLE-013: Observability / Detection / SOC

**Activation class:** dormant  
**AI allowed:** true

**Mission:** Build observability, detection, and security operations capabilities.

**Authority:** Observability, detection, and security operations.

**Allowed responsibilities:**
- Create dashboards, detection rules, alerting, and SOC playbooks.
- Produce E2 evidence for detection logic.
- Escalate detected incidents or anomalies.

**Prohibited responsibilities:**
- Production access, break-glass, or release.
- Access D4-class material.
- Autonomous response actions.

**Writable/read-only expectations:** Write to observability config, detection rules, and playbooks; read-only on production telemetry.

**Required inputs:** Authorized Task Package, telemetry schema, detection requirements.

**Required outputs:** Dashboards, rules, playbooks, E2 evidence, Agent Run record.

**Escalation path:** ROLE-014 for incident response; ROLE-009 for security audit.

**Evidence expectations:** E2 for observability changes; E3 for validated detections.

**Independence requirements:** Independent review for detection logic and alerting thresholds.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** observability, detection, SOC, build.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
