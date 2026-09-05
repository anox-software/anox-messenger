# CURRENT HANDOFF — anoX Messenger V1

Handoff version: MAINARCH-FIX-02 — SERVER / DATABASE / RLS / API / OTK / RETENTION / PRIVACY ARCHITECTURE REMEDIATION COMPLETE  
Date: 2026-09-04  
Delivery branch: `remediation/mainarch-fix-02-server-contracts`  
Described HEAD: `568c8083a3e56058fcb6e5076a7fe1ebc15c384b`  
Main baseline HEAD: `4ee8fe94c71923ae4be038fc250c9ac980ccc7c1`  
Working tree: CLEAN  
Effective gate: MAINARCH-FIX-02 — SERVER / DATABASE / RLS / API / OTK / RETENTION ARCHITECTURE REMEDIATION  
Pre-merge gate: MAINARCH-FIX-02 — SERVER / DATABASE / RLS / API / OTK / RETENTION ARCHITECTURE REMEDIATION  
Post-merge gate: MAINARCH-RETEST-02 — TARGETED DELTA RETEST OF SERVER / DATABASE / API / RETENTION ARCHITECTURE FINDINGS

---

## Project

anoX Messenger V1 — closed-source native Android/GrapheneOS messenger with vodozemac/Olm E2EE.

## Architecture authority

Authority precedence is canonical in `docs/authority/AUTHORITY_INDEX.md`.
New sessions must read that file first.

## Current repository state

- Canonical repository: `https://github.com/anox-software/anox-messenger`
- Canonical SSH remote: `git@github.com:anox-software/anox-messenger.git`
- Legacy provenance remote: `https://github.com/anox-admin/ax-messenger.git` (historical only)
- Canonical branch: `main`
- Delivery branch: `remediation/mainarch-fix-02-server-contracts`
- Current work branch: `remediation/mainarch-fix-02-server-contracts`
- Current HEAD: `568c8083a3e56058fcb6e5076a7fe1ebc15c384b`
- Main baseline HEAD: `4ee8fe94c71923ae4be038fc250c9ac980ccc7c1`
- Working tree: CLEAN
- Latest material event: `ANOX-EVENT-0031`

## Latest completed work

- `MAINARCH-FIX-02` complete.
- `B025_MANDATORY_AMENDMENTS_V1_2.md` freezes V1.2 server/DB/RLS/API/OTK/retention/privacy contracts.
- 8 findings (`ANOX-MAINARCH-003`, `007`, `008`, `009`, `010`, `015`, `016`, `017`) moved to `Ready For Retest`.
- `docs/authority/B_FREEZE_REGISTRY.md` and `docs/authority/AUTHORITY_INDEX.md` updated.
- `tools/audit/validate_mainarch_fix02.py` added.

## Current open work

- `MAINARCH-RETEST-02` — targeted delta retest of the 8 findings.

## Trust-boundary / milestone flags

- `ANOX-MAINARCH-003` (server ↔ DB/RLS) and `ANOX-MAINARCH-007` (server ↔ backup/PITR) remain flagged for the next Security Architecture milestone review.

## Product status

- `BLOCKED_PENDING_FINAL_AUDIT`.
- `B-004` backend: NOT STARTED.
- `B-005` DB/RLS: NOT STARTED.
- No Product/Rust/CI/DB/backend implementation changed.

## Next task

`MAINARCH-RETEST-02` — start only with explicit human authorization.
