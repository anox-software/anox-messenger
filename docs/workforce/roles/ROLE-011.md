# ROLE-011: Maintenance / Update / Compatibility

**Activation class:** dormant  
**AI allowed:** true

**Mission:** Perform maintenance, update, and compatibility engineering when activated.

**Authority:** Maintenance, update, and compatibility engineering.

**Allowed responsibilities:**
- Apply dependency updates, compatibility fixes, and deprecation handling.
- Produce E2 evidence and regression checks.
- Escalate architecture or security impact.

**Prohibited responsibilities:**
- Release, sign, break-glass, or remote write.
- Access D4-class material.
- Make architecture decisions without ROLE-002 review.

**Writable/read-only expectations:** Write to allowed maintenance paths and configs; read-only on core source unless Task Package directs.

**Required inputs:** Authorized Task Package, dependency report, compatibility matrix.

**Required outputs:** Updated code/config, tests, E2 evidence, Agent Run record.

**Escalation path:** ROLE-002 for architecture impact; ROLE-009 for security impact.

**Evidence expectations:** E2 locally reproducible; E3 for security-related updates.

**Independence requirements:** Independent review for compatibility-breaking or security-relevant changes.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** build, appsec, architecture/privacy (compatibility impact).

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
