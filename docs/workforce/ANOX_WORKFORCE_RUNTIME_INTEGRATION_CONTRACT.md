# ANOX Workforce Runtime / Integration Contract

**Status:** B027-A FOUNDATION  
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

A per-role contract (to be implemented in B027-B) that defines:

- role identity and authority;
- allowed task types;
- allowed data-egress classes;
- allowed tools and paths;
- review and evidence requirements.

In B027-A, only the Role Registry and activation classes are implemented.  
Full per-role contracts are B027-B.

### Task Package

The machine-readable work package defined by `docs/workforce/schemas/task-package.schema.json`.  
A Task Package must be `Authorized` before execution.  
The B027-A validator checks structural validity; the B027-B resolver will authorize state transitions.

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

---

## C. Runtime flow

### B027-A (foundation only)

1. A human or the future resolver produces a Candidate Task Package.
2. The B027-A validator checks the Task Package for required fields, valid roles, valid enums, and prohibited assignments.
3. The Task Package is NOT yet executable.  
   In B027-A, no automated authorization or state resolution occurs.
4. Findings, Decisions, and Run records may be recorded for B027-A itself.

### B027-B (future)

1. The State/Gate Resolver evaluates the Candidate against the current Workforce State, Role Contract, and active gates.
2. If the resolver authorizes it, the Task Package status becomes `Authorized`.
3. The authorized role receives a concrete prompt derived from the Task Package.
4. The agent executes the task within allowed paths, data-egress class, and remote permission.
5. The agent produces evidence and returns to `Awaiting Evidence` / `Awaiting Review`.
6. An independent reviewer (where required) reviews and may require retest.
7. Only after human-controlled remote action may the result be merged.

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

---

## F. References

- B027 Authority: `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- Model provider policy: `docs/workforce/MODEL_PROVIDER_POLICY.md`
- Role registry: `docs/workforce/registries/roles.json`
- Workforce state: `docs/workforce/WORKFORCE_STATE.json`
- Schemas: `docs/workforce/schemas/`
- B027-A validator: `tools/workforce/validate_b027a.py`
