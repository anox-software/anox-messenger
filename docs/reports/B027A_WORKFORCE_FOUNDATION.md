# B027-A — AI Workforce / Work-Control Governance Foundation

**Status:** IMPLEMENTED  
**Date:** 2026-08-31  
**Branch:** `governance/b027-workforce-foundation`  
**Start SHA:** `69c1d9b9f7605d5d96e0bc1add3d05ecbc82ee1b`  

## Summary

B027-A establishes the executable foundation of the B-027 AI Workforce / Work-Control Governance system.

## Implemented

- `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md` — B-027 Authority.
- `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md` — Runtime / Integration Contract.
- `docs/workforce/MODEL_PROVIDER_POLICY.md` — Model / Provider Policy.
- `docs/workforce/schemas/` — machine schemas for Task Package, Finding, Decision, Run, Derived Work, and Workforce State.
- `docs/workforce/registries/` — Role Registry, plus tasks, findings, decisions, runs, and derived-work registries.
- `docs/workforce/WORKFORCE_STATE.json` — canonical current workforce state.
- `tools/workforce/validate_b027a.py` — deterministic B027-A validator.
- `tools/workforce/test_b027a.py` — adversarial tests.
- `tools/continuity/validate_continuity.py` — extended to call the B027-A validator.

## Deferred

- State/Gate Resolver (B027-B).
- Full per-role contracts (B027-B).
- Task/Prompt/Communication runtime (B027-B).
- Cold Recovery integration (B027-C).

## Findings

None. All adversarial tests pass.

## Evidence

- B027-A validator: PASS
- B027-A adversarial tests: 20/20 PASS
- Continuity tests: to be run after metadata sync

## Authority

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B_FREEZE_REGISTRY.md`
- `docs/reports/PRE_B027_WORKFORCE_ARCHITECTURE_FREEZE.md`

## Next

B027-B — State/Gate Resolver + Role Contracts + Task/Prompt/Communication runtime.
