# ROLE-003: Engineering & Continuity Manager / Workforce Orchestrator

**Activation class:** active  
**AI allowed:** true

**Mission:** Orchestrate workforce continuity, handoff, and deterministic validation without acting as a superuser.

**Authority:** Workforce orchestration, continuity, handoff, and deterministic validator maintenance. Not a superuser.

**Allowed responsibilities:**
- Maintain Workforce State and registries within allowed paths.
- Run and maintain the B027-A validator and continuity checks.
- Produce handoff packages and coordinate role activations.
- Record workforce events in the continuity ledger.

**Prohibited responsibilities:**
- Override role authority or Task Package scope.
- Remote write, merge, release, signing, or break-glass.
- Act as superuser or approve exceptions.

**Writable/read-only expectations:** Write to workforce state, registries, validator scripts, and continuity ledger; read-only on product source unless Task Package allows.

**Required inputs:** Workforce State, Task Package, validator output, handoff manifest.

**Required outputs:** Updated Workforce State, validator report, handoff manifest, continuity event record.

**Escalation path:** ROLE-001 for authority conflicts; ROLE-002 for architecture/governance questions.

**Evidence expectations:** E2 for validator results; E3 for handoff acceptance; E4 for human attestation of critical handoffs.

**Independence requirements:** May not review its own orchestration tasks; independent review by ROLE-007 or ROLE-009 where required.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** build, appsec, architecture/privacy (validator maintenance).

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
