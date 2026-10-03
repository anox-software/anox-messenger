# B-028 — Scalable Governance Architecture

**Status:** CURRENT (additive governance track; foundation delivered under `ANOX-DECISION-B028-SCALABLE-GOVERNANCE-FOUNDATION-001`)
**Date:** 2026-10-02

---

## Purpose

Make the B-026/B-027 governance system scale with codebase growth. Today every material state transition requires a purpose-built, event- or hash-pinned validator and a human-ratified extension; every session ships a bespoke adversarial suite; the `CURRENT_*` surfaces are synchronized by hand; and audit depth is uniform regardless of risk. The C-01/R09 sequence demonstrated the cost: one validator authority correction required five governance deliveries.

B-028 replaces one-off machinery with deterministic, manifest-driven state-transition machinery while preserving every existing security guarantee: fail-closed validation, append-only registries, writer/reviewer separation, the human remote/merge boundary, D4 prohibition, and byte-exact evidence pinning.

B-028 is a governance specification. It modifies no B-002…B-025 product or security semantics and does not weaken B-026/B-027.

---

## Core principle

```text
VERIFY TRANSITIONS BY CONSTRUCTION — PIN ARTIFACTS, NOT HISTORY.
```

- **Evidence artifacts** remain pinned by SHA-256 (`docs/security/audit-evidence/evidence_hashes.json` model). Artifact pins are immutable.
- **State transitions** are verified structurally: sequence integrity, hash-chained lineage, schema conformance, authorized scope, and legal-transition rules — never by pinning a validator to one exact historical path.
- **Authority reads are provenance-anchored**: authorization for a delivery is resolved from canonical records that predate the delivery's writable surface (the C-01/R09 rule), generalized to every registry consumed by B-028 tooling.

---

## Components

### A. Session manifests — sessions become data, not code

A remediation/audit session is described by a manifest under `docs/workforce/sessions/<session-id>.json` conforming to `docs/workforce/schemas/session.schema.json`:

- `session_id`, `security_class`, `authorized_task_id`
- `covered_units` — MSC unit / finding identifiers the session claims to cover
- `artifacts` — `[{path, sha256}]` pinned evidence files
- `required_retests` — per-unit evidence level and binding (`independent_retest` | `ci_verdict`)
- `provenance` — `{base_sha, delivery_branch}` anchoring the session to canonical lineage

New session ⇒ new manifest file ⇒ generic ingest. No new validator is written per session.

### B. `tools/continuity/seal_event.py` — hash-chained event sealing

- Appends a `PROJECT_HISTORY_LEDGER.jsonl` event deterministically from canonical merge/checkpoint metadata: `event_id`, `date`, `type`, `task`, `summary`, `status`, `start_head`, `end_head`, `merge_head`, `gate_after`, `findings`, `tests`, `refs`, `evidence`.
- Each record carries `prev_event_hash` = SHA-256 of the canonicalized previous record. The chain is verifiable in **archive mode without Git**; tampering, gaps, duplicates, and reordered events fail closed.
- `seal_event.py --verify` performs standalone chain verification; `--seal` performs the append (human-invoked at merge time only).
- Cutover is explicit: the first hash-chained record references the last historically pinned event (`ANOX-EVENT-0066`) as its `prev_event_hash` anchor. Historical validators remain authoritative for all events before the cutover; no historical record is rewritten.

### C. `tools/continuity/render_surfaces.py` — single-source surface rendering

- `CURRENT_GIT_STATE.md` and the other `CURRENT_*` surfaces contain deterministic fields (canonical base, delivery branch, described head, gates, runtime placeholders).
- The renderer resolves the placeholder set already consumed by `generate_handoff.py` (`__EFFECTIVE_GATE__`, `__HANDOFF_BRANCH__`, `__HANDOFF_HEAD__`, `__WORKING_TREE__`, `__CANONICAL_BASE__`, `__DESCRIBED_HEAD__`, `__DELIVERY_BRANCH__`, `__LATEST_EVENT__`, `__PRE_MERGE_GATE__`, `__POST_MERGE_GATE__`) from `CURRENT_STATE.json` + `WORKFORCE_STATE.json` + live Git.
- `--check` (dual-run drift mode): fails if a surface's deterministic fields diverge from rendered truth. `--write`: rewrites deterministically.
- Unresolved markers and unparsable source JSON fail closed. Prose sections remain human-authored; only deterministic fields are rendered.

### D. `test_map.jsonl` + `tools/audit/ingest_ci_verdict.py` — CI-bound retest evidence

- `docs/workforce/registries/test_map.jsonl` binds `{msc_unit | finding_id → [test_refs], ci_jobs[], map_version}`.
- A CI verdict record `{verdict_id, commit_sha, run_id, workflow, job, map_version, result, units[]}` is admissible only when bound to a canonical commit SHA, an identifiable CI run/job, and the current test-map version. Locally produced output is not canonical CI evidence and cannot satisfy `ci_verdict` requirements.
- Records append to `docs/workforce/registries/ci_verdicts.jsonl`; `--verify` re-checks any record offline.

### E. `tools/workforce/risk_classifier.py` + `domain_tiers.json` — deterministic audit depth

- `tier = max(severity_tier, domain_tier)` where `domain_tier` is derived from the union of a task's declared `allowed_paths` and the paths actually changed. Any declared-vs-actual mismatch beyond metadata allowlists fails closed.
- `docs/workforce/registries/domain_tiers.json` is the frozen classification table:

| Domain | Example globs | Tier | Required evidence |
|---|---|---|---|
| `CONTROL_SURFACE` | `tools/audit/**`, `tools/continuity/**`, `tools/workforce/**`, `tools/security/**`, `.github/**` | SEC-C | E3 + independent review |
| `TRUST_BOUNDARY` | `crypto/**`, `**/*.rs`, keystore/auth/JNI surfaces | SEC-B | E3 |
| `CODE` | `android/**`, other source | SEC-B | E2 (CI verdict) |
| `DOCS_ONLY` | `docs/**`, registries, surfaces | SEC-A | E1 |
| `UNKNOWN` | unmatched | SEC-C | E3 (fail closed) |

- `domain_tiers.json` is itself `CONTROL_SURFACE`: every change to it is highest-tier and human-authorized.
- Severity overlay: `LOW`/`MEDIUM` findings may close on canonical CI verdicts + review legality; `HIGH`/`CRITICAL` always require a fresh independent retest session ingested via the generic session path. CI verdicts never satisfy HIGH/CRITICAL requirements. Over-evidencing (independent retest for LOW) is permitted but recorded as `over_evidence`.

### F. Coordinator binding — deterministic next step, narrated externally

- `tools/workforce/next_step.py` resolves the authorized next work bundle from `WORKFORCE_STATE.json` + `tasks.jsonl` (current writer, authorized tasks, candidates) and emits it as machine-readable JSON. It is the deterministic core of task selection; no model judgment is required to identify *what is authorized*.
- `tools/audit/validate_prompt.py` validates a `prompts.jsonl` record against its task package: task exists and is delivery-authorized, `role_id`/`branch`/`start_sha` agree, `allowed_paths ⊆ task.allowed_paths`, `data_egress ≤ task.data_egress`, `remote_permission ≤ task.remote_permission`, no model selection embedded in prompt content, `prompt_id` unique.
- `docs/workforce/coordination/CHATGPT_COORDINATOR_RULES.md` is the canonical home of the external coordinator rules (previously unversioned outside the repository). The coordinator narrates, prioritizes, and formats prompts; it does not derive authority. Its rules are pinned by repository version, not by chat memory.

---

## Layered model

```text
Human Owner (ROLE-001) — merge, seal, ratify
Generators    — seal_event.py · render_surfaces.py
Resolver      — state_gate_resolver.py · risk_classifier.py
Generic ingest— validate_session_evidence.py · ingest_ci_verdict.py · validate_prompt.py
Registries    — append-only JSONL (unchanged semantics)
Evidence      — byte-exact hash-pinned artifacts (unchanged semantics)
```

## Protected core

The generic machinery is itself `CONTROL_SURFACE`: `seal_event.py`, `render_surfaces.py`, `validate_session_evidence.py`, `ingest_ci_verdict.py`, `validate_prompt.py`, `risk_classifier.py`, `next_step.py`, `domain_tiers.json`, `session.schema.json`, and any resolver integration. Changes are SEC-C, require independent review and human ratification. Generic inputs (manifests, test-map rows, CI verdicts, prompts) are data and do not require ratified code changes.

## Dual-run and cutover rule

- New generic components run alongside the historical pinned validators (`dual-run`). Any divergence between generic and pinned verdicts is a blocker, never silently resolved.
- Cutover per component requires a recorded human decision (`ONE_TIME_CHANGE_SPECIFIC` or program-scoped ratification). Historical validators and evidence remain preserved and authoritative for their era; retirement follows the H1 pattern — withdrawn from active acceptance, never deleted.
- Until a cutover decision exists, pinned validators remain the acceptance authority; B-028 tools are advisory/enforcement-ready.

## Non-goals

- No product, crypto, Android, backend, schema, migration, or CI-workflow change.
- No MSC/finding closure, no severity mutation, no historical evidence rewrite.
- No remote mutation; no push, PR, merge, release, or signing authority.
- No weakening of existing validators; no removal of human gates.
- No B027-D employee runtime router enforcement (remains deferred until current findings close; `next_step.py` is read-only resolution, not routing authority).

## Relation to existing authority

- **B-026** — handoff/continuity lifecycle, output contract, merge lifecycle: unchanged. B-028 tools render/seal within B-026's rules.
- **B-027** — workforce roles, task packages, registries: unchanged. B-028 adds data surfaces (session manifests, test map, CI verdicts, prompts) consumed under the same task-package authority.
- **C-01/R09 lesson** — provenance-anchored authority reads are the generalization of the canonical-merge-base anchor established by `ANOX-DECISION-S2-C01-PREAUTHORIZATION-001`.
- **`DEVELOPMENT_SECURITY_WORKFLOW_V1.md`** — delivery lifecycle and merge-safe invariant: unchanged; B-028 components are validated by the same delivery pipeline.
