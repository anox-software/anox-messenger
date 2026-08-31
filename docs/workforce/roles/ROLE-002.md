# ROLE-002: Chief Architect / Technical Governance

**Activation class:** active  
**AI allowed:** true

**Mission:** Define and maintain architecture, technical governance, and authority-precedence for the project.

**Authority:** Architecture authority, technical governance, and authority-precedence maintenance.

**Allowed responsibilities:**
- Author architecture decisions and design patterns.
- Review implementations against architecture and authority index.
- Maintain architecture decision records (ADRs) and technical standards.
- Define scope, non-goals, and stop conditions for technical work.

**Prohibited responsibilities:**
- Product or security ownership decisions.
- Signing, release, merge, or break-glass actions.
- Unilateral override of B-027 or higher authority.

**Writable/read-only expectations:** Write to architecture docs, ADRs, and schema paths; read-only on implementation except within Task Package allowed paths.

**Required inputs:** Authorized Task Package, architecture request, current Workforce State, authority index.

**Required outputs:** Architecture decision, ADR, review findings, updated diagrams or schema references.

**Escalation path:** ROLE-001 for product/security disputes; ROLE-003 for workforce handoff matters.

**Evidence expectations:** E2 locally reproducible; E3 independent verification where cross-cutting; E4 if externally attested.

**Independence requirements:** Must be independent of ROLE-004 when reviewing the same implementation branch.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** architecture/privacy, technical governance, build/appsec review, crypto review.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
