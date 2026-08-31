# ROLE-004: Core Implementation Engineer

**Activation class:** active  
**AI allowed:** true

**Mission:** Implement authorized product and tooling tasks within an assigned Task Package.

**Authority:** Implementation of authorized product and tooling tasks within a Task Package.

**Allowed responsibilities:**
- Write code, tests, and tooling in allowed paths.
- Run local builds and unit tests.
- Produce E2 evidence and propose findings.
- Request review or escalate blockers.

**Prohibited responsibilities:**
- Remote write, merge, release, signing, break-glass.
- Access D4-class material or production secrets.
- Write outside allowed paths or override architecture/security decisions.

**Writable/read-only expectations:** Write to allowed branch paths only; read-only elsewhere unless Task Package specifies.

**Required inputs:** Authorized Task Package, start SHA, allowed/forbidden paths, evidence requirement, security classification.

**Required outputs:** Code changes, tests, E2 evidence, Agent Run record, findings if discovered.

**Escalation path:** ROLE-002 for architecture; ROLE-007/008 for security findings; ROLE-001 for exceptions.

**Evidence expectations:** E2 locally reproducible evidence; E3 after independent review for security-relevant changes.

**Independence requirements:** Writer on a branch; cannot be independent reviewer of the same branch.

**Data-egress ceiling:** D0-D3.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** crypto, auth, build, appsec, architecture/privacy (only as directed by Task Package and reviewed).

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
