# B-027 AI Workforce / Work-Control Governance

**Status:** FROZEN ARCHITECTURE / B027-A FOUNDATION IMPLEMENTED / B027-B RUNTIME IMPLEMENTED / B027-C INTEGRITY, AUDIT GATE, AND COLD RECOVERY IMPLEMENTED  
**Authority:** B-027 is a frozen specification under `docs/authority/B_FREEZE_REGISTRY.md`.  
**Precedence:** See `docs/authority/AUTHORITY_INDEX.md` for the canonical numbered precedence list.  

---

## A. Purpose

B-027 defines the AI workforce / work-control governance system for the anoX V1 project.  
It answers:

- WHO may work;
- WHAT task is authorized;
- WHAT role executes it;
- WHAT branch and paths are writable;
- WHAT data the AI may be exposed to;
- WHAT tools and permissions may be used;
- WHAT evidence is required;
- WHO reviews the work;
- WHAT the next gate may be.

B-027 does **not** redefine Messenger product behavior, backend service behavior, or cryptographic behavior.

---

## B. Scope

### Implemented in B027-A

- B-027 Authority document (this file);
- Workforce Runtime / Integration Contract;
- Model-Provider Policy;
- machine-readable schemas for Task Package, Finding, Decision, Agent Run, Derived Work Candidate, and Workforce State;
- deterministic Role Registry (ROLE-001 through ROLE-019);
- initial Workforce State;
- deterministic B027-A validator and adversarial tests.

### Implemented in B027-B

- State/Gate Resolver (`tools/workforce/state_gate_resolver.py`);
- Role Contracts (`docs/workforce/roles/ROLE-001.md` through `ROLE-019.md`);
- Task lifecycle engine;
- Derived Work Candidate processing;
- Prompt Registry and prompt authority;
- Communication Bus (`docs/workforce/registries/communications.jsonl`);
- finding routing and immutability rules;
- human-action boundary;
- Security Architecture Change Trigger;
- SEC-A / SEC-B / SEC-C levels;
- Legacy Code Revalidation Trigger;
- isolated legacy audit sessions;
- Final Pre-Product Architecture/Security Audit gate;
- Product-resume blocking semantics.

### Implemented in B027-C

- Final B027 integrity validator (`tools/workforce/validate_b027_integrity.py`);
- system-level adversarial tests;
- cross-component integrity graph;
- orphan-state detection;
- deadlock/livelock detection;
- responsibility ownership coverage;
- final audit plans/manifests;
- legacy audit plans/manifests;
- audit-result schema;
- final pre-product architecture/security audit gate;
- product-development block;
- Handoff and Cold Recovery integration.

---

## C. Authority boundaries

B-027 is subordinate to all higher authority listed in `docs/authority/AUTHORITY_INDEX.md`.  
Within the B-027 execution layer, the subordinate hierarchy is (highest first):

1. B-027 AI Workforce / Work-Control Governance (this document)
2. Role Contracts
3. Authorized Task Package
4. Agent Prompt
5. Agent Execution

`LOWER AUTHORITY MAY NEVER OVERRIDE HIGHER AUTHORITY.`

A Task Package cannot override a Role Contract.  
A Role Contract cannot override B-027.  
A prompt cannot override its Task Package.

---

## D. AI agents are untrusted executors, not authority

- AI agents execute work packages. They do not set architecture, security, or release policy.
- An AI suggestion, finding, log, or derived-work candidate has **no** authority to create an executable, writable task.
- Only the human Product & Security Owner, the State/Gate Resolver (implemented in B027-B), or an authorized human path may authorize work.

---

## E. Human Product & Security Owner authority

ROLE-001 / the human Product & Security Owner retains exclusive authority over:

- external remote write;
- merge;
- release approval;
- signing;
- break-glass;
- E4 evidence attestation;
- Accepted Risk decisions requiring human authority;
- any exception to B-027 invariants.

Every human exception must be recorded as a Decision and traceable to an authority reference.

---

## F. Role versus model / provider separation

`ROLE` defines authority and responsibility.  
`MODEL` or `PROVIDER` defines a replaceable execution choice (e.g., Devin, Claude, OpenAI, another provider).

- Changing the model or provider must not change role authority.
- A model/provider is execution metadata, not authority.
- The model provider policy is `docs/workforce/MODEL_PROVIDER_POLICY.md`.

---

## G. Task Package requirement

No writable work may be performed without an `Authorized Task Package` that records at minimum the fields defined in `docs/workforce/schemas/task-package.schema.json`.

A Task Package must declare:

- task identity and title;
- assigned role;
- start SHA;
- target branch;
- allowed and forbidden paths;
- scope, non-goals, and stop conditions;
- security classification (references existing S0–S4);
- data-egress class;
- priority;
- required evidence level;
- reviewer role where independence is required;
- remote permission;
- authority references.

Default remote permission is `NONE`.  
The schema must not silently insert security-relevant defaults.

---

## H. One active writer per writable branch

At most **one** active writable task/role may hold writer authority for the same writable branch.  
Read-only roles may operate in parallel.

The workforce state and validator must enforce this invariant.

---

## I. Writer != independent reviewer

The writer on a branch must not be the same role that performs an independent review of that branch when independence is required.

A fixer cannot solely close a critical or security finding.  
Independent closure requires appropriate reviewer/retest evidence and an authorized actor/role.

---

## J. Remote permission

Recognized remote permission values:

- `NONE` — no remote mutation by AI;
- `READ_ONLY` — AI may read remote state only;
- `HUMAN_REMOTE_ACTION_REQUIRED` — a human must perform the actual remote write.

There is no autonomous AI push permission in V1.  
There is no AI direct-main write mode.

Remote-write governance remains `HUMAN-CONTROLLED REMOTE WRITE MODE`.

---

## K. No AI signing / break-glass / D4 authority

AI may not:

- hold production signing keys;
- hold production credentials;
- hold service-role credentials;
- hold break-glass secrets;
- access D4-class material;
- perform releases, merges, or external remote writes.

D4 — Prohibited AI-secret class — includes at minimum:

- production signing keys;
- production credentials;
- service-role credentials;
- break-glass secrets;
- user plaintext;
- highly sensitive production secrets.

See `docs/workforce/MODEL_PROVIDER_POLICY.md` for the model-provider policy on D4.

---

## L. Stable identifiers

Stable identifier namespaces are:

- `ANOX-TASK-XXXXXXXXX`
- `ANOX-FINDING-XXXXXXXXX`
- `ANOX-DECISION-XXXXXXXXX`
- `ANOX-RUN-XXXXXXXXX`
- `ANOX-WORK-XXXXXXXXX`

Also maintained:

- `ROLE-001` through `ROLE-019`

Identifiers are immutable once issued.  
Deleted or closed identifiers must not be reused.

---

## M. State transitions

### Task lifecycle

```text
Candidate
→ Authorized
→ In Progress
→ Awaiting Evidence
→ Awaiting Review
→ Ready For Remote
→ Awaiting Human Remote Action
→ CI Pending
→ Ready To Merge
→ Merged
→ Closed
```

`Blocked` is an explicit exceptional state.  
Allowed transitions are machine-readable in the Task Package schema.

The State/Gate Resolver is implemented in B027-B and enforces these transitions.  
B027-A defines them and validates that schemas recognize only known values.

### Finding lifecycle

```text
Open
→ Triaged
→ Remediation In Progress
→ Ready For Retest
→ Closed
```

Additional terminal/non-normal states:

- Accepted Risk
- Deferred
- Duplicate
- Superseded

These require explicit authority/rationale fields.  
A finding must never disappear from history because it was fixed.

---

## N. Evidence levels

Canonical evidence levels:

- `E0` — assertion;
- `E1` — artifact exists;
- `E2` — locally reproducible evidence;
- `E3` — independent verification;
- `E4` — human/external attestation.

AI cannot generate E4.  
The machine schema enforces recognized values only.

---

## O. Data-egress levels

Canonical data-egress classes:

- `D0` — public;
- `D1` — internal low-sensitivity;
- `D2` — private engineering/source;
- `D3` — security-sensitive;
- `D4` — prohibited AI-secret class.

A Task Package must declare the maximum allowed egress class.  
D4 may not be assigned to AI roles.

---

## P. Priority levels

Canonical priority levels:

- `P0` — active critical incident / immediate release stop;
- `P1` — current gate/milestone blocker;
- `P2` — normal planned work;
- `P3` — backlog / optimization / deferred.

Priority is separate from security severity (S0–S4) and data-egress class (D0–D4).

---

## Q. Security classification

B-027 does **not** redefine S0–S4.  
Task Packages reference the existing S0–S4 classification from higher authority.

---

## R. Finding persistence and evidence

A finding must contain at minimum the fields in `docs/workforce/schemas/finding.schema.json`.

A severity downgrade requires:

- rationale;
- evidence;
- authorized actor/role;
- decision or audit event.

A closed finding requires closure actor and closure evidence.  
Severity downgrade cannot silently overwrite history.

---

## S. Decision record

Decisions are append-only historical facts.  
A later decision may supersede, not erase, an earlier one.  
Decision records follow `docs/workforce/schemas/decision.schema.json`.

---

## T. Agent Run record

Agent run records follow `docs/workforce/schemas/run.schema.json`.  
They do not store full prompts or full transcripts.  
They record evidence produced, remote mutation, and the model/provider used.

---

## U. Derived Work non-authorization

A `Derived Work Candidate` is a suggestion.  
It is explicitly `NON-AUTHORIZED` until the State/Gate Resolver (implemented in B027-B) or an authorized human path evaluates and accepts it.  
The resolver evaluates Derived Work Candidates against role authority and workforce state.  
An AI may suggest work; an AI suggestion must not create an executable authorized task.

---

## V. Deterministic resolver and fail-closed behavior

The deterministic State/Gate Resolver is implemented in B027-B (`tools/workforce/state_gate_resolver.py`).  
It remains fail-closed:

- `UNKNOWN OR AMBIGUOUS GATE STATE = BLOCKED`;
- unauthorized task, state transition, path, data-egress, or remote-permission request is rejected with a deterministic reason code;
- all remote write remains human-controlled.

---

## W. Cold Recovery requirement

B027-C implements workforce Cold Recovery.  
A fresh context with only the handoff package must be able to determine at minimum:

- canonical repository;
- handoff snapshot SHA;
- highest authority;
- workforce authority and Role Registry;
- active roles;
- active/non-closed tasks;
- open/non-closed findings;
- active decisions;
- current gate;
- Human-Controlled Remote Write Mode;
- next authorized action.

---

## X. Human override and exception traceability

Any human override of B-027 invariants must be recorded as a Decision with:

- decision_id;
- authority_actor (human role);
- decision and rationale;
- authority references;
- evidence references;
- timestamp.

No override is valid without traceability.

---

## Y. References

- Canonical precedence: `docs/authority/AUTHORITY_INDEX.md`
- Freeze registry: `docs/authority/B_FREEZE_REGISTRY.md`
- Runtime contract: `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`
- Model provider policy: `docs/workforce/MODEL_PROVIDER_POLICY.md`
- Role registry: `docs/workforce/registries/roles.json`
- Role contracts: `docs/workforce/roles/`
- Workforce state: `docs/workforce/WORKFORCE_STATE.json`
- Schemas: `docs/workforce/schemas/`
- B027-A validator: `tools/workforce/validate_b027a.py`
- State/Gate Resolver: `tools/workforce/state_gate_resolver.py`
- B027-B validator: `tools/workforce/validate_b027b.py`
- B027-C integrity validator: `tools/workforce/validate_b027_integrity.py`
- Final Audit Plan: `docs/workforce/audits/FINAL_AUDIT_PLAN.md`
- Legacy Audit Plan: `docs/workforce/audits/LEGACY_AUDIT_PLAN.md`
- Audit Result Schema: `docs/workforce/schemas/audit-result.schema.json`

---

## Z. Version

- B027-A foundation: implemented as deterministic schemas, registries, state, and tests.
- B027-B runtime: State/Gate Resolver, Role Contracts, Task lifecycle engine, Derived Work processing, Prompt Registry, Communication Bus, security and legacy triggers, and final product gate semantics.
- B027-C integrity, audit gate, and cold recovery: implemented; includes the final B027 integrity validator, system-level adversarial tests, cross-component integrity graph, orphan-state and deadlock/livelock detection, responsibility ownership coverage, final/legacy audit plans/manifests, audit-result schema, final pre-product architecture/security audit gate, product-development block, and Handoff/Cold Recovery integration.

---

## AA. Security Architecture Reassessment Trigger

Material architecture changes affecting security trigger a mandatory, deterministic reassessment candidate.  
The resolver (`evaluate_security_trigger` in `tools/workforce/state_gate_resolver.py`) creates a candidate and assigns the minimum sufficient audit level when affected domains are not limited to docs, typos, spelling, comments, markdown, or formatting.

---

## AB. Security audit levels (SEC-A / SEC-B / SEC-C)

The resolver assigns the minimum sufficient level and records the rationale:

- `SEC-A` — localized delta review;
- `SEC-B` — domain-wide review (e.g., auth, crypto, backend, RLS, Android security, build/release);
- `SEC-C` — full review for critical or multiple security domains, including security invariants, trust boundaries, cryptography, E2EE, key lifecycle, the State/Gate Resolver, and role permissions.

---

## AC. Final Pre-Product Architecture/Security Audit

B027-C implemented the final pre-product architecture/security audit gate. The gate is opened by three isolated, read-only, fresh audit sessions with no shared prompt state, no stale findings, and no shared working-tree edits:

1. `ANOX-AUDIT-MAIN-ARCH-001` — product and system architecture.
2. `ANOX-AUDIT-WORKFORCE-ARCH-001` — B-027 workforce/work-control governance architecture.
3. `ANOX-AUDIT-SECURITY-ARCH-001` — security, privacy, cryptography, and trust boundaries.

Each session:
- starts from a recorded canonical SHA;
- is independent of the implementation role where independence is required;
- produces an `audit-result` record conforming to `docs/workforce/schemas/audit-result.schema.json`;
- appends that record to `docs/workforce/registries/audits.jsonl`.

The canonical fail-closed workflow is:

```text
Read-Only Audit
→ Findings Freeze
→ Targeted Fix (authorized, no scope expansion)
→ Targeted Delta Retest (new evidence against frozen findings)
→ Systemic Re-audit (only if required)
→ Human Final Gate
```

Product-resume requirements for B-004/B-005 include:
- all three final audit sessions produce `PASS` or `PARTIAL` with no `FAIL` or `BLOCKED`;
- all required legacy audits are satisfied;
- no open `CRITICAL` or `HIGH` findings remain;
- every targeted fix has completed delta retest with new evidence;
- every `systemic_reaudit_required: true` flag is cleared by a fresh systemic re-audit;
- a human Product & Security Owner decision records the final gate in `docs/workforce/registries/decisions.jsonl`;
- the State/Gate Resolver returns a non-`BLOCKED` machine decision for the product gate.

---

## AD. Legacy Code Revalidation

A Legacy Code Revalidation Trigger creates one or more isolated legacy audit sessions for affected surfaces.  
The resolver (`resolve_legacy_revalidation`) maps changed domains to legacy audit scopes and produces separate, fresh audit sessions.  
Audit output is recorded and must be satisfied before the final product gate can pass.

---

## AE. Product Development Block

`PRODUCT_DEVELOPMENT_BLOCKED_PENDING_FINAL_AUDIT` is the fail-closed product gate. B027-C workforce work may continue, but B-004 and B-005 product development remains blocked until the final pre-product architecture/security audit conditions are satisfied and the Human Final Gate is recorded.

`B027 IMPLEMENTATION COMPLETE` is the runtime/workforce milestone produced by a passing run of `tools/workforce/validate_b027_integrity.py`. It is distinct from `FINAL PRE-PRODUCT AUDIT COMPLETE`, which is the human-gated product-resume condition. `B027 IMPLEMENTATION COMPLETE` does not, by itself, unblock product development.
