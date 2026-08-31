# Project Memory / Progress Integrity Reconstruction V1

**Status:** CURRENT  
**Date:** 2026-08-30  
**Task:** PRE-B027-M2B  

---

## 1. M2A discovery source

M2A discovered that the canonical merge lifecycle (CML) and pre-B-027 events were described in human handoff files but were not recorded in a single, machine-readable chronological ledger. Specific gaps:

- PR #3 and PR #4 canonical merge events were not eventized.
- `POST-PR3 FAILURE` (validator could not classify a two-parent merge) had been observed but not recorded as a material blocker.
- M1R1, M1R2, and M1R3 remediation states were collapsed in `CURRENT_HANDOFF.md`.
- The `B-027 AUTHORIZED` gate transition was implied but not explicit.

Sources used for reconstruction:

- `docs/continuity/CURRENT_HANDOFF.md`
- `docs/continuity/CURRENT_GIT_STATE.md`
- `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md`
- `docs/continuity/CURRENT_STATE.json`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/reports/PRE_B027_WORKFORCE_ARCHITECTURE_FREEZE.md`
- `docs/reports/B017_LITE_CI_SUPPLY_CHAIN_SECURITY.md`
- `docs/reports/PROMPT_008_B003_ACCOUNT_LICENSE_FOUNDATION.md`
- `docs/authority/B_FREEZE_REGISTRY.md`

---

## 2. Reconstruction rules

- One ledger row per material event.
- A material event changes a gate, a finding state, a canonical head, test counts, or authority.
- `start_head` / `end_head` / `merge_head` follow the `described_head` semantics defined in PRE-B027-0.
- `gate_after` is the next gate that must pass, not the gate that was just closed.
- Findings use canonical IDs and lifecycle states: `discovered`, `remediated`, `fix_ready`, `closed`.
- Status vocabulary is closed: `closed`, `complete`, `remediated`, `fix_ready`, `merged`, `authorized`, `discovered`, `abandoned`, `in_progress`.
- Do not infer independent review PASS; only record states that can be evidenced.
- Preserve `__M2B_SUBSTANTIVE_HEAD__` until the task produces its first substantive commit.

---

## 3. Corrected CML chronology

The corrected chronological ledger (ANOX-EVENT-0001 through ANOX-EVENT-0022) includes:

1. PROMPT-008D — CommitArmed closure (2026-08-23).
2. PROMPT-008 MERGE — B-003 to main (2026-08-23).
3. PROMPT-009 — Development Security Governance (2026-08-23).
4. PROMPT-009R/R2/R3 — governance remediation chain (2026-08-28).
5. PROMPT-010 — GitHub Remote Activity Safety Governance (2026-08-28).
6. PROMPT-010R1 — remote activity finding remediation (2026-08-28).
7. REMOTE-MIGRATION-SYNC-001 — new GitHub main reconciliation (2026-08-29).
8. B-017-Lite — CI/Supply-Chain Security Foundation (2026-08-29).
9. PRE-B027-0 — B-027 architecture / continuity semantics freeze (2026-08-29).
10. PRE-B027-0R — review finding remediation (2026-08-29).
11. PRE-B027-0R2 — merge-commit payload visibility fix (2026-08-30).
12. PR #3 canonical merge — PRE-B027-0R2 to main (2026-08-30).
13. POST-PR3 FAILURE — validator two-parent merge deficiency (2026-08-30).
14. PRE-B027-M1R — Initial Canonical Merge Lifecycle (2026-08-30).
15. M1R1, M1R2, M1R3 — CML remediations (2026-08-30).
16. PR #4 canonical merge — CML V1 to main (2026-08-30).
17. B-027 AUTHORIZED — effective gate transition (2026-08-30).
18. PRE-B027-M2B — Project Memory / Progress Integrity V1 (2026-08-30).

Total: **22 events** in `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl`.

---

## 4. Missing events restored

Before M2A, **zero** of these events existed in a unified chronological machine ledger. The reconstruction restores the full pre-B-027, CML, and B-027 authorization lineage.

- **22** material events added.
- All pre-B-027 and CML events now have stable `ANOX-EVENT-` IDs.
- All canonical merge heads are recorded.

---

## 5. Contradictions resolved

- `POST-PR3 FAILURE` is recorded as a material `blocker` event with `status: abandoned` and `end_head: 2ee3f9d...`, not silently omitted.
- `PRE-B027-M1R` now correctly starts at the PR #3 merge head (`3e127c7...`).
- M1R1, M1R2, M1R3 are now distinct events with separate finding sets.
- `B-027 AUTHORIZED` is a separate `gate_transition` event rather than an implied state.
- `PRE-B027-M2B` uses the placeholder `__M2B_SUBSTANTIVE_HEAD__` to avoid inventing a commit SHA.

---

## 6. Facts intentionally not claimed

This reconstruction does **not** claim any of the following:

- `PRE-B027-M1R3 INDEPENDENT DELTA REVIEW PASS`.
- `PRE-B027-M1R3` has been merged to `main` on GitHub (it is on `governance/canonical-merge-lifecycle-v1` at `cb1bc3d...` and awaits review).
- PR #4 has been created or merged on GitHub (the ledger models the intended canonical merge target).
- The `B-027 AI WORKFORCE IMPLEMENTATION` gate is complete.
- Any B-027 runtime files have been created.

---

## 7. New memory model

M2B introduces the Project Memory Surface Index and the canonical Project History Ledger. The model:

- distinguishes `CORE SURFACES` from `EVIDENCE SURFACES`;
- defines 10 surface classes and the files that instantiate them;
- provides an `Event-to-surface update matrix` mapping T0–T3 events to the surfaces that must be updated;
- makes the continuity history machine-readable and auditable;
- keeps `CURRENT_HANDOFF.md` and `CURRENT_STATE.json` as the human and machine current-state surfaces;
- uses the ledger as the single chronological source of truth for material events.

---

## 8. Next gate

`B-027 AI WORKFORCE IMPLEMENTATION` is the authorized next gate after `B-027 AUTHORIZED`. No B-027 runtime files are implemented until that gate is explicitly authorized.
