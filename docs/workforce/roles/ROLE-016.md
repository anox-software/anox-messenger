# ROLE-016: Technical Support / Bug Intake

**Activation class:** dormant  
**AI allowed:** true

**Mission:** Triage technical support issues and bug reports when activated.

**Authority:** Technical support and bug intake.

**Allowed responsibilities:**
- Provide support responses and reproduce reported issues.
- Triage and route bugs to engineering.
- Produce E1/E2 evidence for reproduced issues.

**Prohibited responsibilities:**
- Code changes, release, break-glass, or production access.
- Access D4-class material.
- Make security or architecture decisions.

**Writable/read-only expectations:** Write to support docs, bug reports, and triage notes; read-only on source.

**Required inputs:** Authorized Task Package, support ticket, bug report, non-sensitive logs.

**Required outputs:** Triage notes, reproduction steps, bug/finding record, E1/E2 evidence.

**Escalation path:** ROLE-008/009 for security issues; ROLE-004 for engineering fix.

**Evidence expectations:** E1 for intake; E2 for reproduced issues.

**Independence requirements:** Intake role; does not close findings.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** appsec, bug intake.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
