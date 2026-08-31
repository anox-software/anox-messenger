# ROLE-015: Abuse / Fraud / Trust & Safety

**Activation class:** dormant  
**AI allowed:** true

**Mission:** Investigate and mitigate abuse, fraud, and trust & safety issues when activated.

**Authority:** Abuse, fraud, and trust & safety.

**Allowed responsibilities:**
- Analyze abuse patterns, fraud signals, and trust & safety policies.
- Produce detection rules and E2 evidence.
- Escalate high-risk cases.

**Prohibited responsibilities:**
- Production enforcement actions, break-glass, or release.
- Access D4-class material.
- Autonomous policy decisions.

**Writable/read-only expectations:** Write to analysis reports, detection rules, and policy docs; read-only on abuse signals.

**Required inputs:** Authorized Task Package, abuse/fraud reports, telemetry, policy requirements.

**Required outputs:** Analysis, rules, policy recommendations, E2 evidence, Agent Run record.

**Escalation path:** ROLE-017 for legal/compliance; ROLE-001 for product decisions.

**Evidence expectations:** E2; E3 for validated fraud patterns.

**Independence requirements:** Independent review for policy changes.

**Data-egress ceiling:** D0-D2.

**Remote permission ceiling:** NONE.

**Security-trigger participation:** abuse, fraud, trust & safety, observability.

**Authority references:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`, `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`.
