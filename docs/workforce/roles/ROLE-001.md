# ROLE-001: Human Product & Security Owner

**Activation class:** active  
**AI allowed:** false

**Mission:** Retain ultimate human authority over product direction, security posture, release, and exceptions.

**Authority:** Product and security authority; human-controlled remote write, merge, release, signing, break-glass, E4 attestation, and Accepted Risk decisions.

**Allowed responsibilities:**
- Authorize, approve, or reject Task Packages, releases, and exceptions.
- Perform human-controlled remote writes, merges, and break-glass actions.
- Issue E4 attestation and Accepted Risk decisions.
- Delegate authority to named roles via recorded Decision.

**Prohibited responsibilities:**
- Delegate authority without a traceable Decision.
- Override B-027 invariants without evidence.
- Allow AI to perform signing, break-glass, or release.

**Writable/read-only expectations:** Human remote write allowed to protected branches, release artifacts, signing systems, and break-glass records.

**Required inputs:** Authorized Task Package or break-glass rationale; Workforce State; current SHA; authority reference.

**Required outputs:** Decision record; E4 attestation; merge/release log; break-glass record.

**Escalation path:** No higher authority within B-027; record Decision and cite higher authority (`docs/authority/AUTHORITY_INDEX.md`) if needed.

**Evidence expectations:** E4 for attestation and exceptions; E3 for delegated approvals.

**Independence requirements:** Decisions may be reviewed by ROLE-009 / ROLE-019; writer and reviewer must differ where independence is required.

**Data-egress ceiling:** E4 attestation applicable; D4-class secrets remain prohibited for AI.

**Remote permission ceiling:** Human remote write.

**Security-trigger participation:** All security triggers (crypto, auth, build, appsec, architecture/privacy, release, break-glass, incident response, compliance).

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
