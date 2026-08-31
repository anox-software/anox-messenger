# B-027 AI Workforce / Work-Control Governance

**Status:** FROZEN ARCHITECTURE / B027-A FOUNDATION IMPLEMENTED  
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

### Frozen architecture (not yet implemented runtime)

- State/Gate Resolver execution engine;
- automated Derived Work authorization;
- full per-role contract activation;
- communication bus execution;
- per-role prompt contracts.

### Deferred to B027-B

- State/Gate Resolver;
- per-role contracts (ROLE-001 through ROLE-019);
- task/prompt/communication runtime.

### Deferred to B027-C

- Cold Recovery integration;
- workforce handoff manifest extension;
- stale-handoff retest.

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
- Only the human Product & Security Owner, the State/Gate Resolver (when implemented), or an authorized human path may authorize work.

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

The State/Gate Resolver (B027-B) will enforce these transitions.  
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
It is explicitly `NON-AUTHORIZED` until accepted by the future State/Gate Resolver or an authorized human path.  
An AI may suggest work; an AI suggestion must not create an executable authorized task.

---

## V. Deterministic resolver and fail-closed behavior

A deterministic State/Gate Resolver is required for B027-B.  
Until it is implemented:

- `UNKNOWN OR AMBIGUOUS GATE STATE = BLOCKED`;
- no runtime automated authorization occurs;
- all remote write remains human-controlled.

---

## W. Cold Recovery requirement

B-027-C will implement workforce Cold Recovery.  
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
- Workforce state: `docs/workforce/WORKFORCE_STATE.json`
- Schemas: `docs/workforce/schemas/`
- B027-A validator: `tools/workforce/validate_b027a.py`

---

## Z. Version

- B027-A foundation: implemented as deterministic schemas, registries, state, and tests.
- B027-B: State/Gate Resolver + Role Contracts + Task/Prompt/Communication runtime.
- B027-C: Cold Recovery and handoff integration.
