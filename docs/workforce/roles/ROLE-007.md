# ROLE-007: Independent QA / Adversarial Test

**Activation class:** gate_activated  
**AI allowed:** true

**Mission:** Perform independent quality and adversarial testing, distinct from the writer.

**Authority:** Independent quality and adversarial testing. Must be independent of the writer when required.

**Allowed responsibilities:**
- Create and execute test plans, including adversarial and fuzz testing.
- Retest findings after remediation.
- Produce E3 evidence for test results.
- Report defects and security observations.

**Prohibited responsibilities:**
- Implement fixes or merge code.
- Release, sign, or break-glass.
- Access D4-class material.

**Writable/read-only expectations:** Write to test artifacts and reports; read-only on code under test unless Task Package allows.

**Required inputs:** Authorized Task Package, implementation branch, test plan, findings to retest.

**Required outputs:** Test results, E3 evidence, findings, retest report, Agent Run record.

**Escalation path:** ROLE-008 for security findings; ROLE-001 for release blockers.

**Evidence expectations:** E3 independent verification; E4 for human/external attestation where required.

**Independence requirements:** Must be independent of the writer on the same branch; cannot review its own tests.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** build, appsec, architecture/privacy (adversarial testing).

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
