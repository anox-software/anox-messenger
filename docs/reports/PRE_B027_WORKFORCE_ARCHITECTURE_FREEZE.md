# PRE-B027-0 — AI Workforce / Work-Control Governance Architecture Freeze

**Status:** PRE-FROZEN / APPROVED for implementation
**Date:** 2026-08-29
**Branch:** `governance/pre-b027-continuity-reconciliation`
**Applies to:** B-027 V1 implementation and all subsequent Workforce runtime work

---

## A. Purpose

This document captures the approved PRE-B027-A/B/C/D architecture for B-027 — AI Workforce / Work-Control Governance. It does **not** implement the Workforce runtime. Its purpose is to freeze the authority, security, evidence, data-egress, priority, and implementation-order models that the later B-027 implementation must follow.

After this freeze is accepted, `B-027 IMPLEMENTATION = AUTHORIZED`. No further architecture-planning gate is required.

---

## B. Frozen B-027 Purpose

B-027 is:

`AI Workforce / Work-Control Governance`

It defines:

- WHO may work
- WHAT task is authorized
- WHAT role executes it
- WHAT branch/path is writable
- WHAT data may be exposed
- WHAT tools may be used
- WHAT evidence is required
- WHO reviews
- WHAT next gate may occur

B-027 does **not** redefine Messenger product behavior.

---

## C. Frozen Authority Position

Canonical authority precedence is defined only in `docs/authority/AUTHORITY_INDEX.md`.
This document must not duplicate or redefine the full numbered precedence list.

Within the B-027 execution layer the subordinate hierarchy is (highest first):

1. B-027 AI Workforce / Work-Control Governance
2. Role Contracts
3. Task Packages
4. concrete Agent / Devin prompts
5. historical / superseded / legacy material

B-027 is subordinate to all higher authority defined by `docs/authority/AUTHORITY_INDEX.md`.

Invariant:

`LOWER AUTHORITY MAY NEVER OVERRIDE HIGHER AUTHORITY`

---

## D. Frozen 19 Roles

Stable IDs:

| ID | Role | Status |
|----|------|--------|
| ROLE-001 | Product & Security Owner | active |
| ROLE-002 | Chief Architect / Technical Governance | active |
| ROLE-003 | Engineering & Continuity Manager / Workforce Orchestrator | active |
| ROLE-004 | Core Implementation Engineer | active |
| ROLE-005 | Crypto & Protocol Specialist | dormant |
| ROLE-006 | Product & Security UX Engineer | dormant |
| ROLE-007 | Independent QA & Adversarial Test Operator | dormant |
| ROLE-008 | AppSec & Penetration Security Operator | dormant |
| ROLE-009 | Architecture / Privacy / Security-Compliance Auditor | dormant |
| ROLE-010 | Supply-Chain / Build / Release Security Operator | dormant |
| ROLE-011 | Maintenance / Update / Compatibility Operator | dormant |
| ROLE-012 | Platform / SRE / Disaster Recovery | dormant |
| ROLE-013 | Observability / Detection / SOC | dormant |
| ROLE-014 | Incident Response / PSIRT / Vulnerability Management | dormant |
| ROLE-015 | Abuse / Fraud / Trust & Safety | dormant |
| ROLE-016 | Technical Support / Bug Intake | dormant |
| ROLE-017 | Data Protection / Legal / Compliance Owner | dormant |
| ROLE-018 | Human Release Approver / Signing & Break-Glass Custodian | dormant |
| ROLE-019 | Independent External Security & Crypto Auditor | dormant |

Only ROLE-001 through ROLE-004 are initially active. Other roles are gate-activated or on-demand.

### Role ≠ Model

A role is a stable workforce identity/capability. A model/provider is a replaceable
runtime assignment. For example:

`ROLE-008 = AppSec & Penetration Security Operator`

not:

`ROLE-008 = Claude / Devin`

The Model/Provider Matrix determines which models/providers may be assigned to which
roles. Changing a model or provider does not renumber, rename, or redefine a role.

---

## E. Frozen Security Principles

- `WRITER != INDEPENDENT REVIEWER`
- `ONE WRITABLE BRANCH = ONE ACTIVE WRITER AUTHORITY`
- `HUMAN-CONTROLLED REMOTE WRITE MODE`
- `NO RAPID REPETITIVE REMOTE AUTOMATION`
- `HANDOFF SNAPSHOT != LIVE SOURCE`
- `UNKNOWN OR AMBIGUOUS GATE STATE = BLOCKED`
- `D4 AI ACCESS = PROHIBITED`

AI may not possess production signing keys or activate Break-Glass. ROLE-003 is an Orchestrator, not a Superuser.

### Finding Security

1. Findings cannot silently disappear.
2. Persistent Finding records must remain audit-traceable.
3. A fixer cannot solely close an independent Finding.
4. Independent closure requires appropriate reviewer/retest evidence.
5. Severity downgrade requires:
   - rationale,
   - evidence,
   - authorized actor/role,
   - audit event.
6. Normal remediation sequence:

`FINDING → TARGETED FIX → DELTA RETEST → CLOSURE`

---

## F. Frozen Cost / Review Rule

One full independent security review per Security Gate.

After findings:

`TARGETED FIX → DELTA RETEST`

Do not repeat a full audit unless:

- architecture changes
- trust boundary changes
- systemic finding
- new security domain
- reviewer explicitly requires it

---

## G. Frozen State Design

Future B-027 canonical state will use JSON.

Planned canonical categories:

- Roles
- Tasks
- Findings
- Decisions
- Agent Runs
- Derived Work
- Gate State
- Model/Provider Matrix

Stable IDs:

- `ANOX-TASK-XXXXXX`
- `ANOX-FINDING-XXXXXX`
- `ANOX-DECISION-XXXXXX`
- `ANOX-RUN-XXXXXX`
- `ANOX-WORK-XXXXXX`

No actual Workforce directories or files are created by this freeze.

### Gate Resolver

The Gate Resolver is deterministic, fail-closed, and operates on structured canonical inputs.

- `UNKNOWN OR AMBIGUOUS GATE STATE = BLOCKED`
- A Derived Work Candidate cannot self-authorize.
- Findings, logs, or support input cannot directly cause writable execution.
- Only the Authority + Resolver path can produce an authorized executable Task.

---

## H. Frozen Evidence Model

| Level | Meaning | Gate-closing |
|-------|---------|--------------|
| E0 | Agent assertion only | No |
| E1 | Artifact-linked evidence | Partial |
| E2 | Reproducible local execution evidence | Partial |
| E3 | Independent verification such as CI or independent reviewer | Yes |
| E4 | Human/external controlled attestation | Yes |

AI cannot self-generate E4.

---

## I. Frozen Data-Egress Model

| Class | Meaning | AI access |
|-------|---------|-----------|
| D0 | Public | Prohibited by default |
| D1 | Internal low-sensitivity | Prohibited by default |
| D2 | Private engineering/source | Prohibited by default |
| D3 | Security-sensitive | Prohibited by default |
| D4 | Prohibited AI secret class | **PROHIBITED** |

Examples of D4:

- Production signing keys
- production credentials
- service-role secrets
- Break-Glass secrets
- recovery secrets
- user plaintext
- highly sensitive production-user data

Default:

`AI ACCESS = PROHIBITED`

---

## J. Frozen Priority Model

- P0 — active critical incident / immediate release stop
- P1 — current gate/milestone blocker
- P2 — normal planned work
- P3 — backlog / optimization / deferred

P0–P3 are separate from existing S0–S4 Security Class and D0–D4 Data Class.

---

## K. Frozen Handoff Requirement

B-027 Definition of Done requires Handoff integration. Future Handoff must contain/validate:

- Workforce Authority
- Role Registry
- Runtime Contract
- mandatory Workforce schemas
- active Tasks
- non-closed Findings
- active Decisions
- current Gate State
- Model/Provider Matrix
- Remote Write Mode
- Workforce Bootstrap
- per-role bootstraps
- integrity/hash information

Cold Recovery requirement:

`FRESH CONTEXT + ONLY HANDOFF ZIP + NO PRIOR CHAT MEMORY`

must be able to determine at minimum:

- canonical repository
- Handoff snapshot SHA
- highest Authority
- Workforce Authority
- its Role / Role Registry
- active Roles
- active/non-closed Tasks
- open/non-closed Findings
- active Decisions
- current Gate
- Human-Controlled Remote Write Mode
- next authorized action

It must also understand `HANDOFF SNAPSHOT != LIVE SOURCE` and reconcile with live Git
before writable work.

---

## L. Frozen B-027 Implementation Order

1. Authority Integration + Architecture + ERIC
2. Schemas + Registries
3. Task / Finding / Decision / Run / Derived Work State
4. Evidence + Data Egress + Priority + Tool Permissions
5. deterministic fail-closed Gate Resolver
6. ROLE-001 through ROLE-019 contracts
7. Prompt Contracts + Communication + Bootstraps
8. Workforce Validator + tests
9. Handoff Generator / Manifest / Validator integration
10. Cold Recovery + stale-Handoff tests
11. independent B-027 Security Review

---

## M. Continuity / HEAD Semantics

The repository now uses three distinct HEAD concepts:

1. `described_head` — the substantive Git commit whose project state the tracked continuity metadata describes.
2. `live_head` — the runtime `git rev-parse HEAD`, never stored as authoritative.
3. `handoff_snapshot_head` — the external Handoff ZIP manifest value, recorded after a Git commit exists.

`described_head` may be an ancestor of `live_head` only when every intermediate change is on the explicit metadata-only allowlist. This breaks the previous self-referential `baseline_head == live HEAD` invariant that required a tracked file to store its own commit SHA.

---

## N. Next Gate

`PRE-B027-0 FOCUSED INDEPENDENT REVIEW`

After that review and controlled human merge:

`B-027 IMPLEMENTATION AUTHORIZED`
