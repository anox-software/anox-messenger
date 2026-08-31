# CURRENT NEXT DEVIN TASK

**Status:** AUTHORIZED — START WHEN HUMAN ASSIGNS
**Task ID:** `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT` (`AUDIT-MAIN-ARCHITECTURE`)
**Date:** 2026-08-31

---

## Purpose

Conduct the final pre-product architecture and security audit for the B027 workforce runtime and
all merged governance and implementation surfaces before any product engineering resumes.

B027-C is complete at `176cebca7a693282de09f0ea08169c6d1f485dff` on
`governance/b027-final-integration`. All B027-A, B027-B, B027-C, continuity, B017, and Rust
validation suites PASS. Product engineering is blocked pending this audit.

## Preconditions satisfied

- B-027 architecture is frozen and implementation-authorized.
- B027-A governance foundation is merged to `main` at `38b619e55082086989bb0713cad42c4c53be14ab`.
- B027-B state/gate resolver, role contracts, prompt/communication runtime is merged to `main` at
  `aca7a8364a89423173440997ac01865c63552ca0`.
- B027-C integrity validator, adversarial system tests, handoff, cold recovery, and final
  integration is implemented and validated at `176cebca7a693282de09f0ea08169c6d1f485dff`.
- 19 roles, evidence/egress/priority models, and role-versus-model distinction are defined.
- Canonical Merge Lifecycle V1 is merged to `main`.
- Human-Controlled Remote Write Mode is in effect.
- Project Memory / Progress Integrity V1 ledger, surface index, and validator checks are active.
- All test suites pass: B027-A 20/20, B027-B 48/48, B027-C PASS, continuity 171/171,
  B017-Lite policy validator 35/35, Rust 15/15.

## Scope of the next task

- Independently review the final pre-product architecture and security posture documented in
  `docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md` and
  `docs/reports/B027C_FINAL_INTEGRATION.md`.
- Verify `docs/workforce/audits/FINAL_AUDIT_PLAN.md`,
  `docs/workforce/audits/LEGACY_AUDIT_PLAN.md`, and
  `docs/workforce/schemas/audit-result.schema.json`.
- Confirm the `do-not-touch` foundation list, B-025/B-026/B-027 authority, and security invariants
  remain intact.
- Confirm no product/CI/dependency changes occurred beyond B027 governance and tooling.
- Record the audit as `ANOX-EVENT-0028` when authorized.
- Maintain `WRITER != INDEPENDENT REVIEWER`, `D4` prohibition, no AI remote-write, and
  fail-closed authorization.
- Do not implement product features or resume B-004/B-005 engineering until the audit is complete
  and the next gate is explicitly authorized.

## Out of scope

- Product features (B-004 backend, B-005 database/RLS, messaging, etc.).
- Pushing, PR creation, or remote automation.
- Any implementation work beyond the audit itself.

## Next authorized sequence

1. Human assigns and scopes the `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT` session
   (`AUDIT-MAIN-ARCHITECTURE`).
2. Review all B027-C materials and merged B027-A/B surfaces.
3. Record findings and audit result in the ledger and `FORTSCHRITT.md`.
4. Human authorizes the next product engineering gate.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
