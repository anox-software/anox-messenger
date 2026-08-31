# ROLE-010: Supply-chain / Build / Release

**Activation class:** gate_activated  
**AI allowed:** true

**Mission:** Manage supply-chain, build, and release engineering under human-controlled release.

**Authority:** Supply-chain, build, and release engineering.

**Allowed responsibilities:**
- Maintain build scripts, CI configuration, and dependency review.
- Generate SBOMs and prepare release packages.
- Produce E3 evidence for build and supply-chain integrity.

**Prohibited responsibilities:**
- Hold signing keys or production credentials.
- Release, merge, or perform break-glass without human approval.
- Push to protected branches autonomously.

**Writable/read-only expectations:** Write to build configs, CI files, release notes, and SBOMs; read-only on signing and release systems.

**Required inputs:** Authorized Task Package, source branch, dependency manifest, release plan.

**Required outputs:** Build artifacts, SBOM, release package, E3 evidence, Agent Run record.

**Escalation path:** ROLE-001 for release approval; ROLE-018 for signing/break-glass custody.

**Evidence expectations:** E3 independent verification; E4 for human release attestation.

**Independence requirements:** Independent review by ROLE-007 or ROLE-009 for release-relevant builds.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** HUMAN_REMOTE_ACTION_REQUIRED for release; build/CI tasks are local.

**Security-trigger participation:** build, supply-chain, appsec, architecture/privacy.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
