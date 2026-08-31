# ANOX Workforce Runtime / Integration Contract

**Status:** B027-B RUNTIME  
**Authority:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`  

This contract defines how the B-027 workforce runtime entities interact.  
It is an engineering and runtime contract, subordinate to the B-027 Authority.

---

## A. Precedence chain

The runtime precedence chain is (highest first):

```text
Higher Authority (AUTHORITY_INDEX.md, invariants, freeze registry, etc.)
→ B027 AI Workforce / Work-Control Governance
→ Role Contract
→ Authorized Task Package
→ Agent Prompt
→ Agent Execution
```

A lower layer must never override a higher layer.  
A prompt cannot grant permissions not present in its Task Package.  
A Task Package cannot override the assigned Role Contract.  
A Role Contract cannot override B-027.

---

## B. Entities

### Authority

The canonical B-027 Authority in `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md` and the higher authority it references.  
Authority defines what is permitted, prohibited, and deferred.

### Role Contract

Per-role contracts are now implemented in `docs/workforce/roles/` (`ROLE-001.md` through `ROLE-019.md`).  
Each contract defines:

- role identity and authority;
- allowed and prohibited responsibilities;
- allowed task types;
- allowed data-egress classes;
- allowed tools and paths;
- writable/read-only expectations;
- review, independence, and evidence requirements;
- remote permission ceiling and security-trigger participation.

### Task Package

The machine-readable work package defined by `docs/workforce/schemas/task-package.schema.json`.  
A Task Package must be `Authorized` before execution.  
The B027-A validator checks structural validity; the B027-B resolver authorizes state transitions.

### State

The canonical machine state in `docs/workforce/WORKFORCE_STATE.json`.  
It contains only current pointers and active items, not full history.  
Full history lives in the registries under `docs/workforce/registries/`.

### Evidence

Evidence levels E0–E4 are defined by B-027.  
The required evidence for a task is declared in its Task Package.  
Evidence is recorded in the Agent Run record and may be referenced by Findings and Decisions.

### Findings

A Finding is a discovered issue, risk, or observation.  
Findings follow `docs/workforce/schemas/finding.schema.json`.  
Findings are persistent and cannot silently disappear.  
Closure requires evidence and an authorized actor.

### Decisions

A Decision is an append-only historical record of an authority decision.  
Decisions follow `docs/workforce/schemas/decision.schema.json`.  
Decisions may supersede earlier decisions but never erase them.

### Prompt

The concrete prompt given to an agent for a specific Task Package.  
A prompt is derived from the Task Package and must not exceed its authority.  
Prompts are not stored in the Agent Run record.

### Agent Run

An Agent Run is an execution record.  
It follows `docs/workforce/schemas/run.schema.json`.  
It records what task was executed, by which role, using which model/provider, the result, and the evidence produced.

### Prompt Registry

The machine-readable prompt authority and registry in `docs/workforce/registries/prompts.jsonl` (schema `docs/workforce/schemas/prompt.schema.json`).  
It records canonical prompts, their authority references, and assigned roles.  
A concrete prompt must derive from an Authorized Task Package and must not exceed its authority.

### Communication Bus

The machine-readable communication registry in `docs/workforce/registries/communications.jsonl` (schema `docs/workforce/schemas/communication.schema.json`).  
It records directed messages between roles, findings, decisions, and task events.  
The bus is append-only and preserves finding immutability and routing.

### State/Gate Resolver

The deterministic fail-closed resolver implemented in `tools/workforce/state_gate_resolver.py`.  
It evaluates Candidate Task Packages, state transitions, Derived Work Candidates, path enforcement, one-active-writer, human-action boundaries, security triggers, legacy revalidation, and the final product gate.

---

## C. Runtime flow

### B027-A (foundation only)

1. A human or the future resolver produces a Candidate Task Package.
2. The B027-A validator checks the Task Package for required fields, valid roles, valid enums, and prohibited assignments.
3. The Task Package is NOT yet executable.  
   In B027-A, no automated authorization or state resolution occurs.
4. Findings, Decisions, and Run records may be recorded for B027-A itself.

### B027-B runtime

1. The State/Gate Resolver evaluates the Candidate Task Package against the current Workforce State, Role Contract, and active gates.
2. If the resolver authorizes it, the Task Package status becomes `Authorized`.
3. The authorized role receives a concrete prompt from the Prompt Registry or derived directly from the Task Package; the prompt must not exceed Task Package authority.
4. Task state transitions are resolved by the State/Gate Resolver; only permitted actors may advance the task through the lifecycle.
5. The agent executes the task within allowed paths, data-egress class, and remote permission.
6. Findings are routed and recorded on the Communication Bus; they are immutable and cannot silently disappear.
7. The agent produces evidence and returns to `Awaiting Evidence` / `Awaiting Review`.
8. The resolver enforces the human-action boundary for remote push, merge, release, signing, break-glass, E4, and D4-class actions.
9. Security Architecture Change Triggers create reassessment candidates with SEC-A, SEC-B, or SEC-C levels; the rationale and affected domain are recorded.
10. Legacy Code Revalidation Triggers create isolated, fresh legacy audit sessions for affected surfaces.
11. An independent reviewer (where required) reviews and may require retest.
12. Only after human-controlled remote action may the result be merged.
13. The final pre-product architecture/security audit gate remains closed until all blocking findings, legacy audits, and final audit conditions are satisfied.

---

## D. Integration with Project Memory / Continuity

Every material workforce event is recorded in:

- `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` (canonical machine history);
- `FORTSCHRITT.md` (human history with `<!-- ANOX_EVENT: ... -->` markers).

The B027-A validator is called by `tools/continuity/validate_continuity.py` in live mode.  
It ensures the workforce foundation is structurally and semantically consistent.

---

## E. Fail-closed defaults

- Unknown role → FAIL.
- Unknown task state → FAIL.
- Unknown evidence, egress, or priority level → FAIL.
- Missing authority references → FAIL.
- D4 assignment to an AI role → FAIL.
- AI remote-write permission → FAIL.
- Writer and independent reviewer are the same role where independence is required → FAIL.
- Two writers on the same branch → FAIL.
- Derived Work marked `Authorized` directly → FAIL.
- Unknown or ambiguous gate → BLOCKED.

### Resolver reason codes

The State/Gate Resolver returns a deterministic reason string for every BLOCKED or FAIL result.  
Examples include `unknown_role`, `unknown_current_state`, `invalid_state_transition`, `unauthorized_actor`, `unauthorized_path`, `active_writer_conflict`, `d4_for_ai`, `data_egress_exceeds_role_ceiling`, `remote_permission_exceeds_role_ceiling`, `ai_cannot_perform_human_action`, `ai_self_authorization`, `human_action_required`, and `ci_not_passing`.  
The authoritative list and logic are in `tools/workforce/state_gate_resolver.py`.

---

## F. References

- B027 Authority: `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- Model provider policy: `docs/workforce/MODEL_PROVIDER_POLICY.md`
- Role registry: `docs/workforce/registries/roles.json`
- Role contracts: `docs/workforce/roles/`
- Workforce state: `docs/workforce/WORKFORCE_STATE.json`
- Schemas: `docs/workforce/schemas/`
- Prompt registry: `docs/workforce/registries/prompts.jsonl`
- Communication registry: `docs/workforce/registries/communications.jsonl`
- B027-A validator: `tools/workforce/validate_b027a.py`
- State/Gate Resolver: `tools/workforce/state_gate_resolver.py`
- B027-B validator: `tools/workforce/validate_b027b.py`
