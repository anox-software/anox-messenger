# ROLE-018: Human Release Approver / Signing / Break-glass

**Activation class:** dormant  
**AI allowed:** false

**Mission:** Provide human-only custody of release approval, signing, and break-glass.

**Authority:** Human release approval, signing, and break-glass custody. No AI execution.

**Allowed responsibilities:**
- Approve releases and perform signing.
- Execute break-glass and issue E4 attestation.
- Record Decisions for all release/signing/break-glass actions.

**Prohibited responsibilities:**
- Any AI execution or delegation to AI.
- Action without traceable authority and E4 evidence.
- Override B-027 invariants without recorded rationale.

**Writable/read-only expectations:** Remote write to release and signing systems; write to break-glass records and approvals.

**Required inputs:** Authorized Task Package, release package, build evidence, break-glass rationale.

**Required outputs:** Signed release, break-glass record, E4 attestation, Decision record.

**Escalation path:** ROLE-001 for product/security exceptions.

**Evidence expectations:** E4 for all release, signing, and break-glass actions.

**Independence requirements:** Independent of build and implementation; may be reviewed by ROLE-001 or ROLE-019.

**Data-egress ceiling:** E4 attestation applicable; D4-class secrets remain human-only.

**Remote permission ceiling:** HUMAN_REMOTE_ACTION_REQUIRED.

**Security-trigger participation:** build, release, signing, break-glass.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
