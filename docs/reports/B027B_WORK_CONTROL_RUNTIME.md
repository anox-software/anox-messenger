# B027-B — State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime

**Status:** IMPLEMENTED  
**Date:** 2026-08-31  
**Branch:** `governance/b027-work-control-runtime`  
**Start SHA:** `38b619e55082086989bb0713cad42c4c53be14ab`  

## Summary

B027-B turns the B027-A static governance foundation into deterministic work-control behavior.

## Implemented

- `tools/workforce/state_gate_resolver.py` — deterministic, fail-closed State/Gate Resolver.
- `tools/workforce/validate_b027b.py` — B027-B validator and 48 adversarial tests.
- `docs/workforce/roles/ROLE-001.md` through `ROLE-019.md` — canonical per-role contracts.
- `docs/workforce/schemas/prompt.schema.json` and `docs/workforce/schemas/communication.schema.json`.
- `docs/workforce/registries/prompts.jsonl` and `docs/workforce/registries/communications.jsonl`.
- Task lifecycle enforcement.
- Derived Work Candidate processing.
- Finding routing and immutability rules.
- Human-action boundary.
- Security Architecture Change Trigger and SEC-A/B/C levels.
- Legacy Code Revalidation Trigger and separate-session policy.
- Final Pre-Product Architecture/Security Audit gate contract.
- Product-resume blocking semantics.
- Integration with `tools/continuity/validate_continuity.py`.

## Deferred

- B027-C — Cold Recovery and handoff integration.
- Product features (B-004/B-005).
- Final architecture/security/legacy audits.

## Findings

None. All adversarial tests pass.

## Evidence

- B027-A validator: PASS
- B027-A adversarial tests: 20/20 PASS
- B027-B validator: PASS
- B027-B adversarial tests: 48/48 PASS
- Continuity regression: 171/171 PASS
- B017-Lite policy validator: 35/35 PASS
- Rust tests: 15/15 PASS
- `git diff --check`: clean

## Authority

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`
- `docs/workforce/MODEL_PROVIDER_POLICY.md`

## Next

B027-C — Integrity Validator + Adversarial System Tests + Handoff + Cold Recovery + Final B027 Integration.
