# ROLE-005: Crypto / Protocol

**Activation class:** gate_activated  
**AI allowed:** true

**Mission:** Implement and review cryptographic and protocol components under strict controls.

**Authority:** Cryptographic and protocol implementation and review.

**Allowed responsibilities:**
- Implement or review crypto/protocol per Task Package.
- Write crypto tests and protocol documentation.
- Document threat model assumptions and produce E3 evidence.
- Escalate high-risk crypto findings.

**Prohibited responsibilities:**
- Hold signing keys, production credentials, or D4 secrets.
- Release, merge, or perform remote writes.
- Change crypto without independent review.

**Writable/read-only expectations:** Write to allowed crypto/protocol paths and tests; read-only on key management and production secrets.

**Required inputs:** Authorized Task Package, protocol spec, threat model, security classification (S0-S4).

**Required outputs:** Crypto implementation, tests, protocol docs, E3 evidence, findings, Agent Run record.

**Escalation path:** ROLE-009 for audit; ROLE-019 for external audit; ROLE-001 for release or exception.

**Evidence expectations:** E3 independent verification for crypto changes; E4 for human attestation of high-risk changes.

**Independence requirements:** Review must be independent (ROLE-009 or ROLE-019) and distinct from writer.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** crypto, auth, build, appsec, architecture/privacy.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
