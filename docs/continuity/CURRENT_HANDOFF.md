# CURRENT HANDOFF — anoX Messenger V1

Handoff version: `WORKFORCE-FIX-01 — WORKFORCE GOVERNANCE / CONTINUITY HARDENING`
Date: 2026-09-07
Delivery branch: `remediation/workforce-fix-01-governance-continuity`
Described HEAD: `3cc663e00a23e6a0cc342d3ad941a8e926772cd6`
Main baseline HEAD: `7eede96b3830a9b4a49e43494b60d4163c1e5cb3`
Working tree: `CLEAN`
Effective gate: `WORKFORCE-FIX-01 — WORKFORCE GOVERNANCE / CONTINUITY HARDENING (Ready For Remote; awaiting human merge)`
Pre-merge gate: `WORKFORCE-FIX-01 — WORKFORCE GOVERNANCE / CONTINUITY HARDENING (Ready For Remote; awaiting human merge)`
Post-merge gate: `WORKFORCE-RETEST-01 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST (Candidate, pending human authorization)`

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
- Delivery branch: `remediation/workforce-fix-01-governance-continuity`
- Current work branch: `remediation/workforce-fix-01-governance-continuity`
- Current HEAD: `3cc663e00a23e6a0cc342d3ad941a8e926772cd6`
- Main baseline HEAD: `7eede96b3830a9b4a49e43494b60d4163c1e5cb3`
- Working tree: `CLEAN`
- Latest material event: `ANOX-EVENT-0039`

## Latest completed work

- `WORKFORCE-FIX-01` (`ANOX-TASK-WORKFORCEFIX01`) remediated to `Ready For Remote`: three canonical Workforce findings (`ANOX-WORKFORCE-AUDIT-001`, `002`, `005`) moved to `Ready For Retest`.
- Merge-aware canonical two-commit delivery validator implemented in `tools/audit/lifecycle_legality.py`; `validate_legacy_retest01_ingest.py` and `validate_workforce_audit_findings_freeze.py` now distinguish task-authored commits from Human merge commits and exclude later `main` history.
- Post-merge continuity/Workforce-state synchronization hardened: `WORKFORCE_STATE.json` carries `pre_merge_state` and `post_merge_state` blocks; `state_gate_resolver.py` derives effective current writer and gate deterministically after canonical merge; no third post-merge bookkeeping commit required.
- `tools/workforce/state_gate_resolver.py` path normalization hardened: `..`, multi-level traversal, root escape, POSIX/Windows/UNC absolute paths rejected; `.` components and duplicate separators normalized; single-component `*` and double `**` wildcard semantics preserved.
- `FINAL-OPERATIONAL-HANDOFF-BOOTSTRAP-ACCEPTANCE` gate defined as `NOT_EXECUTED/PENDING`; final product gate now depends on it.
- `ANOX-TASK-WORKFORCERETEST01` recorded as `Candidate` with unbound `start_sha` (`NOT YET BOUND — HUMAN SUPPLIES POST-MERGE MAIN SHA`).
- New `tools/audit/validate_workforce_fix01.py` + `tools/audit/test_workforce_fix01.py` (17 tests) added.
- B027-A/B/C integrity, legacy retest ingest, and new fix validator PASS.

## Current open work

- `ANOX-TASK-WORKFORCEFIX01` — Workforce Governance / Continuity Hardening — `Ready For Remote`; awaits human merge.
- `ANOX-TASK-WORKFORCERETEST01` — Candidate; start only on explicit human authorization and a fresh post-merge `main` SHA.
- `ANOX-MAINARCH-018` physical GrapheneOS/StrongBox verification (`PHYSICAL_VERIFICATION_REQUIRED`).
- Milestone Security Architecture review for `ANOX-MAINARCH-003`, `007`, `024`.
- `ANOX-WORK-FINAL-HANDOFF-ACCEPTANCE-001` — final operational handoff/bootstrap/employee cold-boot acceptance gate.

## Trust-boundary / milestone flags

- `ANOX-MAINARCH-003`, `007`, `024` remain `PENDING` milestone Security Architecture review.
- `ANOX-MAINARCH-018` physical GrapheneOS/StrongBox verification remains `PHYSICAL_VERIFICATION_REQUIRED`.

## Product status

- `BLOCKED_PENDING_FINAL_AUDIT`.
- `B-004` backend: `NOT_STARTED`.
- `B-005` DB/RLS: `NOT_STARTED`.

## Next task

`WORKFORCE-RETEST-01` (`ANOX-TASK-WORKFORCERETEST01`) — Independent Targeted Workforce Governance Delta Retest — Candidate, pending human authorization. Scope: verify merge-aware validator, post-merge effective state, path authorization, final operational acceptance gate, and archive/cold recovery. No product code; no Security Architecture audit; remote `NONE`.
