# FINAL PRE-PRODUCT WORKFORCE ARCHITECTURE AUDIT

**Audit:** `AUDIT-WORKFORCE-ARCHITECTURE`  
**Audit ID:** `ANOX-AUDIT-WORKFORCE-ARCH-001`  
**Model:** `Devin SWE-1.7 Max`  
**Provider:** `Cognition`  
**Canonical base / end SHA:** `d5f76ba9dfdb332ac5f70b769c57b3f0ae6122b8`  
**Mode:** `READ-ONLY INDEPENDENT WORKFORCE ARCHITECTURE AUDIT`  
**Repository modified:** `NO`  
**Remote mutation:** `NONE`  
**Result:** `PASS WITH FINDINGS`  
**Status after freeze:** `COMPLETE_WITH_FINDINGS`  

---

## Executive summary

The B-027 AI Workforce / Work-Control Governance system was audited on the frozen canonical base `d5f76ba`.  The audit confirms that the workforce architecture is internally coherent, fail-closed, recoverable, auditable, and safe enough to govern future Product development, subject to the canonical findings recorded here.

The repository can deterministically answer:

- who may act — the 19 role contracts and `registries/roles.json`;
- which role they act as — role registry and task package `role_id`;
- what they may modify — `allowed_paths`/`forbidden_paths` in task packages and the state/gate resolver;
- what they may not modify — forbidden paths, product code for governance tasks, D4-class data, human-only actions;
- which branch they may write — branch tied to the authorized task package;
- who reviews them — `reviewer_role` with independence enforced;
- what evidence is required — `required_evidence` and run records;
- what security/data classification applies — `security_class`, `data_egress`, `priority`;
- whether remote mutation is permitted — `remote_permission` enum, AI remote write prohibited;
- which task state transitions are legal — `state_gate_resolver.py` `TRANSITION_RULES`;
- which finding transitions are legal — `lifecycle_legality.py` and finding schema;
- what the next authorized gate is — `WORKFORCE_STATE.json` and `CURRENT_STATE.json`;
- when Security reassessment is required — `evaluate_security_trigger` (SEC-A/B/C);
- when Legacy revalidation is required — `resolve_legacy_revalidation`;
- when Human action is mandatory — `HUMAN_ACTIONS` and human-only roles;
- how state is reconstructed after context loss — Project Memory surfaces, handoff archive, `CURRENT_CHAT_BOOTSTRAP_PROMPT.md`.

The core B027-A/B/C validators pass.  The state/gate resolver blocks the adversarial cases in its unit tests.  The 19 role contracts are complete.  The authority precedence chain is clear.  Human-only remote actions are enforced.

The audit produced six local candidates.  After root-cause deduplication three are promoted to canonical Workforce findings; two are merged into the same root cause; one is a scope decision item.

---

## Authority precedence

Resolved from `docs/authority/AUTHORITY_INDEX.md` (highest first):

1. `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
2. `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
3. `docs/authority/B_FREEZE_REGISTRY.md`
4. `docs/authority/CLOUD_AI_SECRET_PROTECTION.md`
5. `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`
6. `docs/authority/GITHUB_REMOTE_ACTIVITY_SAFETY.md`
7. `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md`
8. `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md`
9. `docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md`
10. `docs/authority/B025_MANDATORY_AMENDMENTS_V1_3.md`
11. `docs/authority/B025/TRACK_B/B0xx_*.md`
12. `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`

B027 is the lowest layer; its internal execution hierarchy is `B027 Governance → Role Contract → Authorized Task Package → Agent Prompt → Agent Execution`.

---

## 19-role model

| ID | Role | Activation | Write | Remote | Human-only? | Bootstrap |
|----|------|------------|-------|--------|-------------|-----------|
| ROLE-001 | Human Product & Security Owner | active | human remote write | HUMAN_REMOTE_ACTION_REQUIRED | YES | COMPLETE |
| ROLE-002 | Chief Architect / Technical Governance | active | governance paths | NONE | NO | COMPLETE |
| ROLE-003 | Engineering & Continuity Manager / Workforce Orchestrator | active | governance/continuity | NONE | NO | COMPLETE |
| ROLE-004 | Core Implementation Engineer | active | allowed branch paths | NONE | NO | COMPLETE |
| ROLE-005 | Crypto / Protocol | gate_activated | crypto paths | NONE | NO | COMPLETE |
| ROLE-006 | Product / Security UX | dormant | product/UX paths | NONE | NO | COMPLETE |
| ROLE-007 | Independent QA / Adversarial Test | gate_activated | test artifacts | NONE | NO | COMPLETE |
| ROLE-008 | AppSec / Pentest | gate_activated | security test reports | NONE | NO | COMPLETE |
| ROLE-009 | Architecture / Privacy / Security Audit | gate_activated | audit reports | NONE | NO | COMPLETE |
| ROLE-010 | Supply-chain / Build / Release | gate_activated | build/CI paths | HUMAN_REMOTE_ACTION_REQUIRED | NO | COMPLETE |
| ROLE-011 | Maintenance / Update / Compatibility | dormant | maintenance paths | NONE | NO | COMPLETE |
| ROLE-012 | Platform / SRE / DR | dormant | SRE paths | NONE | NO | COMPLETE |
| ROLE-013 | Observability / Detection / SOC | dormant | observability paths | NONE | NO | COMPLETE |
| ROLE-014 | Incident Response / PSIRT / Vulnerability Management | dormant | incident paths | NONE | NO | COMPLETE |
| ROLE-015 | Abuse / Fraud / Trust & Safety | dormant | trust/safety paths | NONE | NO | COMPLETE |
| ROLE-016 | Technical Support / Bug Intake | dormant | support paths | NONE | NO | COMPLETE |
| ROLE-017 | Data Protection / Legal / Compliance | dormant | compliance paths | NONE | NO | COMPLETE |
| ROLE-018 | Human Release Approver / Signing / Break-glass | dormant | release/signing | HUMAN_REMOTE_ACTION_REQUIRED | YES | COMPLETE |
| ROLE-019 | Independent External Security / Crypto Auditor | dormant | external audit reports | NONE | NO | COMPLETE |

Activation classes, human-only status, and role/model/provider separation are consistent across the role registry and role contracts.

---

## Control matrix

| Control | Authority | Implementation | Enforcement | Adversarial test | Result |
|---------|-----------|----------------|-------------|------------------|--------|
| Role separation | B027 + contracts | 19 role contracts, role registry | validator-enforced | title/provider conflation | PASS |
| Human authority | B027 + ROLE-001/018 | `check_human_action_boundary` | deterministic | AI merge/push/E4/D4 | PASS |
| Task authorization | B027 + resolver | `authorize_task`, schema | deterministic | unknown role, dormant, missing fields | PASS |
| Task lifecycle | B027 + resolver | `TRANSITION_RULES` | deterministic | illegal transitions, AI self-auth | PASS |
| One active writer | B027 + resolver | `check_one_active_writer` | deterministic | duplicate writer, writer=reviewer | PASS |
| Branch authorization | B027 + resolver | start_sha, branch field | deterministic | start_sha mismatch | PASS |
| Path scope | B027 + resolver | `check_path_enforcement` | deterministic, not normalizing | `../` not covered | **FINDING** |
| Remote permission | B027 + schema | enum NONE/READ_ONLY/HUMAN... | schema/resolver | AI_WRITE, HUMAN_REMOTE for AI | PASS |
| GitHub human boundary | B027 + resolver | `HUMAN_ACTIONS` | deterministic | AI push/merge/release | PASS |
| Evidence / D4 / E4 | B027 + schema | E0-E4, D0-D4 | schema/resolver | E5, AI E4 | PASS |
| Security reassessment | B027 + resolver | `evaluate_security_trigger` | deterministic | docs not triggering, crypto → SEC-C | PASS |
| Legacy revalidation | B027 + resolver | `resolve_legacy_revalidation` | deterministic | unrelated domains, duplicate sessions | PASS |
| Final product gate | B027 + resolver | `resolve_final_product_gate` | deterministic | missing human/legacy/retest | PASS |
| Two-commit delivery | B027 + legacy validator | `git rev-list --count` | validator-enforced | counts merge as 3rd commit | **FINDING** |
| Project Memory | B026 + B027 | ledger, `CURRENT_STATE`, handoff | validator-enforced | duplicate event, stale gate | **FINDING** |
| Cold recovery | B027-C | `validate_continuity --mode archive` | validator-enforced | stale handoff gate | PARTIAL |
| Bootstrap | B027 + `CURRENT_CHAT_BOOTSTRAP_PROMPT.md` | authority-first read-only | documented | fresh session reconstruction | PASS |

---

## Bootstrap and cold-recovery status

| Item | Status |
|------|--------|
| Role-specific bootstrap | COMPLETE |
| Workforce bootstrap | PARTIAL — schemas, resolver, contracts, and validators complete; stale state and handoff gate still open |
| Project-wide bootstrap | PARTIAL — live repo is reconstructable; handoff-only archive failed at the freeze base and must be revalidated after remediation |
| Handoff recovery | EXPECTED OPEN FINDING — archive-mode validation failed at `d5f76ba` because `CURRENT_HANDOFF.md` and `CURRENT_GIT_STATE.md` carried the previous effective gate |
| Cold recovery | PARTIAL — live repository + `CURRENT_STATE.json` works; handoff-only path blocked by 002 |
| Final operational handoff / bootstrap / employee cold-boot acceptance gate | REQUIRED AS DERIVED WORK — recorded as `ANOX-WORK-FINAL-HANDOFF-ACCEPTANCE-001`; must be satisfied before the human final product gate |
| Autonomous 19-agent employee runtime | NOT IMPLEMENTED and NOT REQUIRED at this stage |

---

## Source candidates and dispositions

| Candidate | Severity | Disposition | Rationale |
|-----------|----------|-------------|-----------|
| `ANOX-WORKFORCE-AUDIT-001` | MEDIUM | **PROMOTE_CANONICAL** | The legacy retest ingest validator counts the post-merge Human merge commit as a third commit, contradicting the intended two-commit *task-authored* delivery contract (interpretation A).  Remediation: make the validator merge-aware. |
| `ANOX-WORKFORCE-AUDIT-002` | MEDIUM | **PROMOTE_CANONICAL** | `CURRENT_HANDOFF.md` and `CURRENT_GIT_STATE.md` retained the previous `LEGACY-RETEST-01-INGEST` effective gate after the Human merge; `GIT_SNAPSHOT.txt` resolved the new gate to `AUDIT-WORKFORCE-ARCHITECTURE`, causing archive/cold-recovery validation to fail.  This is a post-merge continuity synchronization defect. |
| `ANOX-WORKFORCE-AUDIT-003` | (merged) | **MERGE_INTO_EXISTING: ANOX-WORKFORCE-AUDIT-002** | `WORKFORCE_STATE.json` `current_gate` and `current_writer` are stale for the same root cause: post-merge current-state synchronization was incomplete.  Same control surface; no separate remediation. |
| `ANOX-WORKFORCE-AUDIT-004` | (merged) | **MERGE_INTO_EXISTING: ANOX-WORKFORCE-AUDIT-002** | `ANOX-TASK-WORKFORCEARCH001` `start_sha` is stale (pre-merge base) because the Candidate was not rebound after the Human merge.  A Candidate with a stale `start_sha` is fail-closed — the resolver will block authorization until it is rebound — but it is still a symptom of the same post-merge synchronization root cause. |
| `ANOX-WORKFORCE-AUDIT-005` | MEDIUM | **PROMOTE_CANONICAL** | `state_gate_resolver.py` `_path_allowed()` does not normalize `..` segments.  A manual probe shows `docs/workforce/../backend/x.py` is accepted against an allowed path of `docs/workforce/`.  The canonical path-enforcement primitive should fail closed even when `changed_paths` are not pre-normalized Git diff output.  Reaching the resolver with an unnormalized path is possible because `check_path_enforcement` is callable both from `authorize_task` and as a resolver CLI operation. |
| `ANOX-WORKFORCE-AUDIT-006` | LOW/INFO | **REQUIRES_SCOPE_DECISION** | Python `fnmatch.fnmatch` makes a single `*` match across directory separators, so `docs/workforce/*` matches `docs/workforce/deep/sub/x.py`.  Existing task packages use `**` for recursion, but B027/Authority does not explicitly define whether `*` means one component or recursive.  The schema and runtime contract need an explicit path-scope semantics decision before any single-`*` task package is authorized. |

### Final canonical finding set

| ID | Title | Severity | Status | Blocking class |
|----|-------|----------|--------|----------------|
| `ANOX-WORKFORCE-AUDIT-001` | Legacy retest ingest validator miscounts Human merge commit as task-authored third commit | MEDIUM | Open | **BLOCKS CONTINUED FINAL-AUDIT WORK** |
| `ANOX-WORKFORCE-AUDIT-002` | Post-merge continuity and Workforce state synchronization incomplete (stale handoff gate, `WORKFORCE_STATE` pointers, stale Candidate `start_sha`) | MEDIUM | Open | **BLOCKS CONTINUED FINAL-AUDIT PROGRESSION** |
| `ANOX-WORKFORCE-AUDIT-005` | `state_gate_resolver.py` path enforcement does not normalize `..` segments, allowing path escape | MEDIUM | Open | NON-BLOCKING |

`ANOX-WORKFORCE-AUDIT-003` and `ANOX-WORKFORCE-AUDIT-004` are recorded as merged into `ANOX-WORKFORCE-AUDIT-002`.  `ANOX-WORKFORCE-AUDIT-006` is a scope decision item, not a canonical finding.

---

## Evidence for promoted findings

### ANOX-WORKFORCE-AUDIT-001

```text
$ python3 tools/audit/validate_legacy_retest01_ingest.py
...
FAIL Expected exactly 2 commits on ingest branch, found 3
```

The branch `audit/legacy-retest-01-ingest` contains exactly two task-authored commits (`f50dc79` substantive, `0f5c62a` metadata).  The third commit is the Human-created merge commit `d5f76ba` on `main`.  The validator uses `git rev-list --count {RETEST_BASE_SHA}..HEAD`, which includes the merge.

### ANOX-WORKFORCE-AUDIT-002

```text
$ python3 tools/continuity/validate_continuity.py --mode archive
...
FAIL docs/continuity/CURRENT_HANDOFF.md effective gate LEGACY-RETEST-01-INGEST ...
FAIL docs/continuity/CURRENT_GIT_STATE.md effective gate LEGACY-RETEST-01-INGEST ...
```

`CURRENT_STATE.json` resolved the post-merge effective gate to `AUDIT-WORKFORCE-ARCHITECTURE`, while the human-readable handoff surfaces retained `LEGACY-RETEST-01-INGEST`.

### ANOX-WORKFORCE-AUDIT-005

```text
$ python3 - <<'PY'
import tools.workforce.state_gate_resolver as sgr
r = sgr.check_path_enforcement(
    ["docs/workforce/../backend/x.py"],
    {"task_id": "T", "allowed_paths": ["docs/workforce/"], "forbidden_paths": []}
)
print(r)
PY
{'result': 'ALLOWED', 'reason': 'paths_allowed', 'unauthorized_paths': []}
```

The resolver accepts the `..` segment and would allow a write outside the intended scope.  Git diff output is normally normalized, but the resolver is also exposed as a generic authorization primitive and may receive unnormalized input.

---

## Final operational handoff acceptance requirement

A derived work candidate `ANOX-WORK-FINAL-HANDOFF-ACCEPTANCE-001` is recorded.  Before the product final gate opens the project must demonstrate, without chat history:

1. project-wide bootstrap;
2. complete Workforce bootstrap;
3. all 19 role contracts;
4. representative role-specific fresh-session boots;
5. handoff-only recovery;
6. archive validation PASS;
7. cold recovery PASS;
8. current findings and next authorized task resolvable;
9. Authority precedence and Human remote boundary;
10. Security reassessment and Legacy revalidation rules;
11. fail-closed behavior on stale/mismatched state.

This gate must precede the Human Final Product Gate.

---

## Remediation candidate

`ANOX-TASK-WORKFORCEFIX01` — `WORKFORCE-FIX-01 — WORKFORCE GOVERNANCE / CONTINUITY HARDENING`

- **Role:** `ROLE-003` (Engineering & Continuity Manager / Workforce Orchestrator), reviewer `ROLE-002` (Chief Architect)
- **Branch:** `remediation/workforce-fix-01`
- **Remote permission:** `NONE`
- **Product code:** forbidden
- **Scope:**
  - update `validate_legacy_retest01_ingest.py` to distinguish task-authored branch commits from Human merge commits;
  - add post-merge current-state synchronization (continuity surfaces + `WORKFORCE_STATE.json`) to `WORKFORCE-FIX-01` delivery checklist;
  - normalize `..` segments and document wildcard semantics in `state_gate_resolver.py`;
  - update `ANOX-TASK-WORKFORCEARCH001` `start_sha` if still needed when authorized.

---

## Next canonical gate

After `WORKFORCE-FIX-01` is complete, reviewed, and the blocking Workforce findings are closed, the next gate is the third required Final Pre-Product audit:

`AUDIT-SECURITY-ARCHITECTURE` (`ANOX-AUDIT-SECURITY-ARCH-001`)

It is **NOT** authorized until the Workforce blocking findings (`ANOX-WORKFORCE-AUDIT-001`, `ANOX-WORKFORCE-AUDIT-002`) are closed and the Workforce bootstrap/handoff acceptance evidence is satisfactory.

---

## Product state

- **Product development:** `BLOCKED_PENDING_FINAL_AUDIT`
- **B004 backend:** `NOT_STARTED`
- **B005 DB/RLS:** `NOT_STARTED`
- **Existing product findings unchanged:** `ANOX-MAINARCH-013`, `ANOX-MAINARCH-018`, `ANOX-MAINARCH-030`, `ANOX-LEGACY-INTEGRATION-005`, `ANOX-LEGACY-B003-001`
- **Claude / external audit trigger:** `NO`
- **Remote mutation performed by this audit:** `NONE`
