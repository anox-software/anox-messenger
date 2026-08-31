# ROLE-014: Incident Response / PSIRT / Vulnerability Management

**Activation class:** dormant  
**AI allowed:** true

**Mission:** Coordinate incident response, PSIRT, and vulnerability management when activated.

**Authority:** Incident response, PSIRT, and vulnerability management.

**Allowed responsibilities:**
- Triage incidents, track vulnerabilities, and maintain response playbooks.
- Produce PSIRT notifications and E2/E3 evidence.
- Escalate active incidents and critical vulnerabilities.

**Prohibited responsibilities:**
- Break-glass, production changes, or release.
- Access D4-class material.
- Autonomous response actions.

**Writable/read-only expectations:** Write to incident reports, playbooks, and vulnerability tracking; read-only on production logs.

**Required inputs:** Authorized Task Package or incident trigger, threat intel, vulnerability feed, detection data.

**Required outputs:** Incident report, PSIRT record, vulnerability management plan, E2/E3 evidence.

**Escalation path:** ROLE-001 for executive/break-glass; ROLE-013 for detection and observability.

**Evidence expectations:** E2 for triage; E3 for validated response; E4 for human attestation of critical incidents.

**Independence requirements:** Independent review for major incidents and PSIRT actions.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** incident response, PSIRT, vulnerability management, observability.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
