# B028-SCALABLE-GOVERNANCE-FOUNDATION-001 — Human Decision Record

**Decision ID:** `ANOX-DECISION-B028-SCALABLE-GOVERNANCE-FOUNDATION-001`
**Authority actor:** Human Product & Security Owner
**Classification:** `HUMAN_AUTHORIZED_PROGRAM_FOUNDATION`
**Scope:** `PROGRAM_FOUNDATION` (B-028 additive governance track)
**Date:** 2026-10-02
**Status:** Recorded

## Decision

The Human Product & Security Owner authorizes exactly one bounded governance delivery — `ANOX-TASK-B028-SCALABLE-GOVERNANCE-FOUNDATION-001` on branch `governance/b028-foundation-001` from canonical main `32c729ceb6991447698c7ec8deee7278e36d333d` — to establish the **B-028 Scalable Governance** architecture as an additive authority track and deliver its generic foundation tooling in **non-enforcing advisory mode**.

## What is authorized

1. `docs/authority/B028_SCALABLE_GOVERNANCE.md` — the design authority (transitions verified by construction; artifacts remain hash-pinned).
2. Registration in `B_FREEZE_REGISTRY.md` and `AUTHORITY_INDEX.md` as an additive governance track.
3. New data surfaces: `docs/workforce/schemas/session.schema.json`, `docs/workforce/registries/domain_tiers.json` (protected classification table), `test_map.jsonl`, `ci_verdicts.jsonl`, first `prompts.jsonl` activation record.
4. New deterministic, fail-closed tools, all advisory until cutover:
   - `tools/continuity/seal_event.py` — hash-chained ledger sealing (`prev_event_hash`; archive-mode verifiable)
   - `tools/continuity/render_surfaces.py` — deterministic surface rendering + `--check` drift gate
   - `tools/audit/validate_session_evidence.py` — generic manifest-driven session evidence ingest
   - `tools/audit/ingest_ci_verdict.py` — canonical CI verdict binding (SHA + run id + job + map version)
   - `tools/workforce/risk_classifier.py` — `tier = max(severity, domain)`; CONTROL_SURFACE → SEC-C; unknown → SEC-C
   - `tools/workforce/next_step.py` — deterministic authorized-bundle resolver (B027-D core, read-only)
   - `tools/audit/validate_prompt.py` — prompt-registry scope enforcement
5. `docs/workforce/coordination/CHATGPT_COORDINATOR_RULES.md` — canonical, version-pinned home of the external coordinator rules (previously unversioned outside the repository).
6. `ANOX-TASK-B028-DUAL-RUN-CUTOVER-001` registered as **Candidate** (`start_sha NOT YET BOUND`) — the future dual-run/cutover gate.

## What is NOT authorized

- Product, crypto, Android, backend, schema, migration, or CI-workflow changes.
- Finding or MSC closure; severity mutation; historical evidence or validator rewrite/deletion.
- A new canonical ledger event append (no `seal_event.py` execution against the canonical ledger).
- Activation or cutover of any B-028 component to acceptance authority — each requires a **separate** recorded human decision after clean dual-run parity.
- `state_gate_resolver.py` modification; resolver integration is a later stage.
- Push, PR, real merge, release, or signing action. Remote mutation `NONE`.

## Rationale

Governance cost currently scales with ceremony instead of risk: one pinned validator per event and bespoke adversarial suites per session (the C-01/R09 correction alone required five governance deliveries). B-028 verifies transitions by construction — sessions become data, events become hash-chained, surfaces become rendered, audit depth becomes computed — while keeping every existing guarantee: fail-closed validation, append-only registries, writer/reviewer separation, human merge boundary, and byte-exact evidence pinning.

## Cutover requirement

Each B-028 component becomes the acceptance authority only through a separate recorded human decision after clean dual-run parity against the historical pinned validators. Historical validators remain authoritative and preserved; retirement follows the H1 pattern (withdrawn from active acceptance, never deleted).

## Evidence

- Adversarial suites: `test_seal_event.py` (19), `test_render_surfaces.py` (10), `test_session_evidence.py` (19), `test_ingest_ci_verdict.py` (16), `test_validate_prompt.py` (16), `test_risk_classifier.py` (10), `test_next_step.py` (8) — 98 tests.
- Registry records: `decisions.jsonl` (`ANOX-DECISION-B028-SCALABLE-GOVERNANCE-FOUNDATION-001`), `tasks.jsonl` (foundation task + cutover candidate), `prompts.jsonl` (`ANOX-PROMPT-B028F001`).
