# Project Memory Surface Index

**Status:** CURRENT  
**Date:** 2026-08-30  
**Applies to:** PRE-B027-M2B — Project Memory / Progress Integrity V1

---

## 1. Purpose

This index defines the canonical surface classes that hold project memory and progress-integrity state. Each class is mapped to concrete files, a trust role, and the event types that must update it. Surfaces are divided into **CORE SURFACES** (authoritative live state) and **EVIDENCE SURFACES** (supporting material, audit, and recovery).

---

## 2. CORE SURFACES

### 2.1 CORE_MACHINE_HISTORY

Machine-generated, append-only historical record.

| File | Purpose |
|------|---------|
| `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` | Canonical chronological ledger of material project events. |
| `docs/continuity/CURRENT_GIT_STATE.md` | Machine-extracted Git ancestry, branch, and merge history. |
| `docs/continuity/CURRENT_STATE.json` | Machine-readable snapshot of repository, gate, and test state. |

### 2.2 CORE_HUMAN_HISTORY

Human-authored or imported historical narrative and reports.

| File | Purpose |
|------|---------|
| `docs/reports/*.md` | Human-curated project, security, and architecture reports. |
| `docs/history/B025/**/*` | Imported historical B-025 provenance and handoff material. |
| `docs/continuity/HISTORICAL_HANDOFFS/*` | Archived human handoff records. |

### 2.3 CORE_MACHINE_CURRENT

Machine-generated current-state artifacts.

| File | Purpose |
|------|---------|
| `docs/continuity/CURRENT_STATE.json` | Authoritative JSON state: heads, gates, test counts, blockers. |
| `docs/continuity/CURRENT_GIT_STATE.md` | Live Git state resolved from `git rev-parse` and `git log`. |

### 2.4 CORE_HUMAN_CURRENT

Human-curated current-state and handoff artifacts.

| File | Purpose |
|------|---------|
| `docs/continuity/CURRENT_HANDOFF.md` | Primary human handoff document. |
| `docs/continuity/CURRENT_OPEN_WORK.md` | Active work, blockers, and next engineering task. |
| `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md` | Authorized next Devin task and acceptance criteria. |
| `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md` | Product, CI, and security implementation status. |

### 2.5 AGENT_HISTORY

Agent-run and session-derived records.

| File | Purpose |
|------|---------|
| `docs/continuity/HISTORICAL_HANDOFFS/` | Per-session agent handoff snapshots. |
| `docs/current/*.md` | Agent-delivered current architecture and design documents. |
| `docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md` | Bootstrap instructions for a new agent session. |

### 2.6 CURRENT_OPERATIONAL

Operational workflow, contracts, and tooling that keep continuity running.

| File | Purpose |
|------|---------|
| `docs/continuity/HANDOFF_WORKFLOW.md` | Handoff generation and validation workflow. |
| `docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md` | Checklist for verifying a handoff package. |
| `docs/continuity/DEVIN_OUTPUT_CONTRACT.md` | Required Devin output structure and gate reporting. |
| `docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md` | Files and evidence required for a valid handoff. |
| `tools/continuity/generate_handoff.py` | Handoff package generator. |
| `tools/continuity/validate_continuity.py` | Continuity state validator. |

### 2.7 AUTHORITY

Canonical authority, governance, and freeze registry.

| File | Purpose |
|------|---------|
| `docs/authority/AUTHORITY_INDEX.md` | Canonical authority precedence. |
| `docs/authority/B_FREEZE_REGISTRY.md` | Frozen architecture and implementation gates. |
| `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` | B-026 continuity governance rules. |
| `docs/authority/B025/**/*` | B-025 track-B security and product authority. |

---

## 3. EVIDENCE SURFACES

### 3.1 EVIDENCE

Reproducible test, review, and audit artifacts.

| File | Purpose |
|------|---------|
| `tools/continuity/test_handoff_and_validator.py` | Continuity validator regression tests. |
| `tools/security/test_b017_lite_policy_validator.py` | B-017-Lite policy validator tests. |
| `docs/reports/*.md` | Reported findings, audits, and retest evidence. |
| CI logs and artifacts | Build, test, and APK content validation output. |

### 3.2 RECOVERY

Cold-start and stale-handoff recovery material.

| File | Purpose |
|------|---------|
| `docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md` | Fresh-context bootstrap instructions. |
| `tools/continuity/generate_handoff.py` | Handoff generator that produces a recoverable ZIP. |
| `tools/continuity/validate_continuity.py` | Validator that reconciles snapshot with live Git. |
| `docs/continuity/HANDOFF_WORKFLOW.md` | Recovery procedure for a dropped session. |

### 3.3 HISTORICAL_LEGACY

Legacy provenance, non-authoritative historical material.

| File | Purpose |
|------|---------|
| `docs/history/B025/**/*` | B-025 historical provenance and imported source index. |
| Legacy remotes (`anox-admin/ax-messenger`) | Historical-only provenance; never authoritative. |
| `docs/continuity/HISTORICAL_HANDOFFS/` | Superseded handoff snapshots. |

---

## 4. Event-to-Surface Update Matrix

Event taxonomy:

- **T0** — Baseline / discovery / architecture freeze / authorization event.
- **T1** — Implementation / substantive change event.
- **T2** — Review / remediation / merge / reconciliation event.
- **T3** — Gate transition / canonical merge / migration / authorization event.

| Event type | Surfaces that must be updated |
|------------|-------------------------------|
| T0 | `CORE_MACHINE_HISTORY`, `CORE_HUMAN_HISTORY`, `AUTHORITY`, `HISTORICAL_LEGACY` |
| T1 | `CORE_MACHINE_CURRENT`, `CORE_HUMAN_CURRENT`, `CURRENT_OPERATIONAL`, `EVIDENCE` |
| T2 | `AGENT_HISTORY`, `EVIDENCE`, `RECOVERY`, `CORE_MACHINE_HISTORY`, `CORE_HUMAN_HISTORY` |
| T3 | `AUTHORITY`, `CURRENT_OPERATIONAL`, `CORE_MACHINE_CURRENT`, `CORE_HUMAN_CURRENT`, `HISTORICAL_LEGACY` |

---

## 5. Update Rules

1. Every material event must produce at least one ledger row in `CORE_MACHINE_HISTORY`.
2. T1 events must update a `CORE_*_CURRENT` surface before the next T1 begins.
3. T2 and T3 events must add evidence to `EVIDENCE` or `RECOVERY`.
4. `AUTHORITY` is only updated by T0 or T3 authority/freeze events.
5. `HISTORICAL_LEGACY` is never rewritten; it is appended and marked superseded.
6. `CURRENT_OPERATIONAL` is updated whenever workflow, validation, or bootstrap tooling changes.

---

## 6. Canonical Surface Order for Cold Recovery

A fresh agent with only the handoff ZIP must read surfaces in this order:

1. `AUTHORITY` (`docs/authority/AUTHORITY_INDEX.md`)
2. `CORE_HUMAN_CURRENT` (`docs/continuity/CURRENT_HANDOFF.md`)
3. `CORE_MACHINE_CURRENT` (`docs/continuity/CURRENT_STATE.json`)
4. `CORE_MACHINE_HISTORY` (`docs/continuity/PROJECT_HISTORY_LEDGER.jsonl`)
5. `CURRENT_OPERATIONAL` (`HANDOFF_WORKFLOW.md`, `validate_continuity.py`)
6. `EVIDENCE` and `RECOVERY` as needed for verification.
