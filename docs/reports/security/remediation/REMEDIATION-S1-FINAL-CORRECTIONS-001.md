# REMEDIATION-S1-FINAL-CORRECTIONS-001

**Task:** `ANOX-TASK-REMEDIATION-S1-FINAL-CORRECTIONS-001`
**Authorization:** `ANOX-DECISION-S1-FINAL-CORRECTION-AUTHORIZATION-001`
(`HUMAN-DECISION-S1-FINAL-CORRECTION-AUTHORIZATION-001`, Human Product & Security
Owner; `ONE_TIME_CHANGE_SPECIFIC`; recorded verbatim in
`docs/reports/security/decisions/S1-FINAL-CORRECTION-AUTHORIZATION-001.md`)
**Branch:** `integration/s1-after-s0-001`
**Authorized start head:** `f08749e2e5ec45e76b1ea98c5c999e4679be3ffe`
**Remediates:** `TARGETED-INDEPENDENT-PRE-RATIFICATION-RETEST-S1-002`
(B-3, B-4, B-5, N-8, N-9; B-1 Human-ratified)

> **NOT INDEPENDENTLY VERIFIED.** This pass was implemented by the same agent that
> produced `TARGETED-INDEPENDENT-PRE-RATIFICATION-RETEST-S1-002`. Independence is
> therefore reduced exactly as in the B-1 pattern. An independent retest by a
> session that did not author this pair is required before any ratification or
> push. This limitation is recorded in the Human decision record, the task record
> and `CURRENT_STATE`.

## 1. Findings disposition

| Finding | Status | Change |
|---|---|---|
| **B-1** | `HUMAN_RATIFIED` | Ratified by the Human Owner for the already reviewed S1 integration/correction scope only, on the independent non-weakening finding. No general or future S0-validator permission. The S0-owned validators are **not** further modified by this pass. |
| **B-3** | FIXED | `decisions.jsonl`: the genuine Human decision is recorded with valid `authority_refs`; the prior agent-generated record is corrected to state its true provenance (`is_human_authority: false`, `AGENT_ASSERTED_…`, `superseded_by`) and given `authority_refs`. One active writer restored: the two predecessor tasks on this branch move `Ready For Remote → Awaiting Human Remote Action` (the documented successor state; `write_window: CLOSED`), leaving this task as the sole active writer; `WORKFORCE_STATE.current_writer` / `authorized_tasks` updated to match. |
| **B-4** | FIXED | `decisions.jsonl` is delivered in the **substantive** commit, so the metadata commit touches only paths in the continuity `METADATA_ONLY_ALLOWLIST`. The stale `pre_merge_state.current_gate` is synchronised with `CURRENT_STATE.pre_merge_gate` so the Continuity/Workforce effective-gate agreement holds and `__EFFECTIVE_GATE__` resolves. No allowlist was widened. |
| **B-5** | FIXED | `test_91` now uses `git rev-parse --absolute-git-dir` and asserts the pointer is absolute. `test_s0_contract_freeze` is **100/100 in a normal clone** as well as in a linked worktree. |
| **N-8** | FIXED | `validate_ci_pipeline` inspects the `run:` script of mandatory download/verify/Gradle steps and rejects `set +e`, explicit `exit 0`, and a trailing no-op success builtin (`true` / `:`), in addition to `||` / `;` / `continue-on-error` / `if:`. `&&` chaining and `set -euo pipefail` remain legal. A body-extraction bug that silently dropped the **first** line of a block scalar was fixed and pinned by a regression test. |
| **N-9** | FIXED (bounded) + disclosed | Every delivered correction pair is now pinned by SHA in `CONSUMED_CORRECTION_PAIRS`; the pre-ratification pair `0d1549d12d02` / `f08749e2e5ec` is CONSUMED and can no longer be replaced, rewritten or reused. At most one further pair is accepted, only while the authorized correction task is declared; a second unpinned pair is rejected outright. |
| **N-10 / N-11** | UNCHANGED (LOW) | `.git`-absent trees still SKIP the S0 scope gate (fixture mode, required by the adversarial harness); the `;` rule stays deliberately broad. Both fail closed or are pre-existing. |
| **N-7** | UNCHANGED | Pre-existing; central-validator-mitigated. |

## 2. N-9 residual trust boundary (disclosed, not solved)

The trailing correction pair **cannot** be bound cryptographically by an in-repo
validator: the commit that carries the pin is authored inside the same pass, so an
actor who authors the pair can also author its declaration. What this pass does
achieve is that the slot is no longer *standing* — it is single-use and every
consumed pair is immutable.

To close the residual gap, the Human Owner should either require signed
commits/tags, or record the final substantive SHA and promote it into
`CONSUMED_CORRECTION_PAIRS` in a follow-up decision. This is stated plainly in the
validator docstring rather than implied to be solved.

## 3. Shared Validator ratification package REGENERATED (disclosed)

The previously pinned package (`e52f626a46f2…`) **hardcoded** the pre-ratification
correction task id and a 3-or-5-commit chain, and did not enumerate the new
evidence surfaces. Empirically demonstrated before regeneration: applying the
pinned package to the corrected tree makes the would-be-ratified validator fail on
the very tree it governs (`expected exactly 2 task-authored commits above base,
found 20`; `CURRENT_STATE does not declare the S1 integration delivery`). Since any
correction pass necessarily adds a commit pair, the old package was **unratifiable
in practice**.

Regenerated under `ANOX-DECISION-S1-FINAL-CORRECTION-AUTHORIZATION-001`:

| Artifact | Before | After |
|---|---|---|
| Proposed validator post-image | `e52f626a46f27af5…` | **`d03e539a49e9126e…`** |
| Proposed paired-suite post-image | `c305c21c94054540…` | `c305c21c94054540…` (**unchanged**) |
| Applies to (ratified) | `89c7358fbbe61c71…` | `89c7358fbbe61c71…` (unchanged) |

Changes inside the proposed validator: accept any recorded correction task; pass
`S1_CONSUMED_CORRECTION_PAIRS` to the topology proof; accept every consumed
metadata head; enumerate the three final-correction evidence surfaces.

**Deliberate design choice — pins were NOT delegated to a shared module.** The
delivery-shape pins remain duplicated between the Human-ratified central validator
(authoritative) and `validate_s1_integration_evidence.py`. Collapsing them into
`tools/audit/lifecycle_legality.py` would have been more convenient, but that file
is S1-writable, so the S1 session could then widen the acceptance criteria of the
validator meant to constrain it — a weakening the authorization forbids. Instead
the duplication is made safe: `validate_no_pin_drift` fails closed if any
duplicated pin differs, or if an S1-side allowed path is not allowed by the
ratified validator. Pre-ratification the ratified file carries no S1 constants and
the gate is a documented no-op that arms automatically on ratification.

> **This regenerated package was verified by the authoring agent, NOT
> independently.** Retest `TARGETED-INDEPENDENT-PRE-RATIFICATION-RETEST-S1-002`
> verified `e52f626a46f2…`; it did not verify `d03e539a49e9…`. The independent
> retest must re-verify the package from scratch.

## 4. Delivery topology

```
29a6643189… ─┐
             ├─ M dd6e2c5d ── C1 ea20aaaf ── C2 573c5f58 ── D1 0d1549d1 ── D2 f08749e2 ── D1' ── D2'
e32463ca71… ─┘                                              └── CONSUMED (pinned) ──┘   └ this pass ┘
```

`M`/`C1`/`C2` pinned and immutable; `[0d1549d1, f08749e2]` pinned as consumed;
`D1'` bound to `CURRENT_STATE.described_head`; `D2'` restricted to metadata
allowlists. No history rewritten; `ANOX-EVENT-0055` remains the latest material
event (this pass is a **NON-EVENT**); the ledger is untouched.

## 5. Verification

- `validate_b027a` / `validate_b027b` / `validate_b027_integrity` — PASS
- `validate_continuity --mode live` — PASS in a real clone
- `validate_s0_contract_freeze` PASS · `test_s0_contract_freeze` **100/100 in a normal clone**
- `validate_s0_evidence_preservation` PASS · `test_s0_evidence_preservation` 40/40
- `validate_s1_integration_evidence` PASS · `test_s1_integration_evidence` **75/75**
- `test_s1_retest_remediation` **107/107** · `test_s1_build_provenance` 66/66
- `validate_security_audit_evidence_preservation` FAILS **by design** pre-ratification;
  `test_security_audit_evidence_preservation` 277/277
- Regenerated package: applies to ratified `89c7358fbbe6…` yielding exactly
  `d03e539a49e9…` + `c305c21c9405…`; post-application central validator PASS and
  suite 277/277; all adversarial probes fail closed
- `validate_ci_pipeline`, `secret_scan`, `validate_b021_verification_matrix`,
  `validate_s1_build_provenance`, `b017_lite_policy_validator` — PASS
- `cargo test --locked` 17/17 · `cargo audit` 0 vulnerabilities · `git diff --check` clean
- Mutation-tested: reverting each fix turns its paired tests red

## 6. Non-goals honoured

`docs/authority/*` untouched; S0 protections not weakened (no S0-owned validator
modified by this pass beyond the already-ratified scope); no history rewrite; MSC
42 open / 0 closed; `B004`/`B005` `NOT_STARTED`; Shared Validator remains a
**proposal**; `PRODUCT = BLOCKED_PENDING_FINAL_AUDIT`; **no push, PR or merge**.
