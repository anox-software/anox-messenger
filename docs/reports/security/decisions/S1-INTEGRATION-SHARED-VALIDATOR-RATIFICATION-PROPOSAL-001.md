# S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-PROPOSAL-001

**Classification:** `HUMAN_RATIFICATION_PROPOSAL` — **NOT a decision, NOT a ratification, NOT executed**
**Prepared by:** `REMEDIATION-S1-CANONICAL-INTEGRATION-001` (`ANOX-TASK-REMEDIATION-S1-CANONICAL-INTEGRATION-001`)
**Decision authority required:** Human Product & Security Owner
**Date prepared:** 2026-09-16

## 1. Why a proposal and not a change

`tools/audit/validate_security_audit_evidence_preservation.py` is a
`PROTECTED_SHARED_GOVERNANCE_FILE`. The frozen S0 contract
(`tools/audit/validate_s0_contract_freeze.py`, F-03) pins its content to exactly the
two Human-ratified contents:

| Ratified change | Decision | SHA-256 |
|---|---|---|
| `S0_SUCCESSOR_EVENT_SUPPORT` | `ANOX-DECISION-S0-F01-RATIFICATION-001` | `756141b378a19e3e30c225e1e158bbcd61d6d0b7dc921a3f4fe591c81e497b80` |
| `S0_PRESERVATION_LIFECYCLE_EXTENSION` | `ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001` | `89c7358fbbe61c71c8fcde114ffc8a83aa33f52bd3fb763417e00f4131d84bb7` (current) |

Both ratifications record `scope = ONE_TIME_CHANGE_SPECIFIC`, `grants_s1_permission = false`,
`grants_future_sessions = false`, `grants_future_event_numbers = false`, and state that any other
content "is an unauthorized modification … a new Human ratification is required".

The S1 integration task was instructed to create the minimum canonical S1-era extension of this
validator. Doing so **in place** would (a) fail the frozen S0 contract, (b) require the task to
either forge a Human ratification or re-pin the S0 contract itself — both of which would silently
weaken S0 authority. Neither is permitted. The task therefore:

1. left the protected file **byte-identical** to the ratified content `89c7358f…`;
2. prepared the exact minimum extension as a **patch** with pinned post-change hashes covering both
   the validator and its paired adversarial test suite (below);
3. shipped the identical S1-era acceptance logic in a **separate, non-protected** validator
   `tools/audit/validate_s1_integration_evidence.py`, which imports the ratified module and runs
   every S0 protection verbatim, adding only the pinned S1-era sections;
4. shipped paired accept/reject adversarial tests (`tools/audit/test_s1_integration_evidence.py`).

Until ratification, the ratified central validator FAILS on the integrated repository **by design**
(its era pins: `LEDGER_EVENT = ANOX-EVENT-0052` chain ending at 0054, registry = 13, "no
product/CI/native changes"). This is the already-confirmed `S1_SHARED_VALIDATOR_FOLLOWUP_REQUIRED`
condition, now made precise and ready for a Human decision.

## 2. The proposed change

> ### SUPERSESSION NOTICE — do not reuse the previous hashes
>
> An earlier revision of this package proposed
> `e52f626a46f27af59b51acf2af20ec6762ab71f8c1e35239e6c59f70182af1f8` (validator)
> with `c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462` (paired
> suite). **`e52f626a46f2…` is SUPERSEDED and must never be ratified.** It was
> valid *only* for the pre-final-correction topology
> `[M, C1, C2, D1, D2]`: it hardcoded
> `ANOX-TASK-REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001` as the sole
> correction task and a 3-or-5-commit chain, so on the corrected tree it fails on
> the very repository it governs (`expected exactly 2 task-authored commits above
> base, found 20`; `CURRENT_STATE does not declare the S1 integration delivery`).
>
> The independent retest `TARGETED-INDEPENDENT-PRE-RATIFICATION-RETEST-S1-002`
> verified `e52f626a46f2…` against `f08749e2` — that verification does **not**
> carry over to the current package. The paired-suite post-image
> `c305c21c9405…` is byte-identical in both revisions; only the validator
> post-image changed.
>
> The current package was regenerated deterministically from the committed final
> correction history by `REMEDIATION-S1-FINAL-CORRECTIONS-001` and is verified by
> its **authoring** agent only. It is **NOT self-ratified** and requires targeted
> independent re-verification before Human ratification.

- **Patch:** `docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch`
- **Applies to (ratified):** `validate_security_audit_evidence_preservation.py` @
  `89c7358fbbe61c71c8fcde114ffc8a83aa33f52bd3fb763417e00f4131d84bb7` and its paired adversarial
  suite `test_security_audit_evidence_preservation.py` @ `b69dbb3546eae50a82a322373a9b064ca976906cb4028f2a57a185d6de48c1d6`
- **Yields (proposed):** validator `d03e539a49e9126e92b0fdc31fb5c8e424a6e7e82c98cf954881e99e6edbed74`;
  paired test suite `c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462`
- **Integrity:** `validate_s1_integration_evidence.py` applies the patch to both ratified files in a
  scratch directory and fails if either result is not exactly the proposed hash.
- **Post-application test state:** the paired suite update migrates the fixture era and the era-
  sensitive expected messages so the full **277/277** central adversarial suite passes against the
  proposed validator (verified by simulated application during
  `REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001`). The suite stays at 277 tests — no assertion is
  weakened and no negative case is dropped; only era-pinned fixtures/needles move to the S1 era.

Content of the extension (additive; no S0 predicate or pin is altered):

| Area | Proposed behaviour |
|---|---|
| `has_git()` | recognises a linked-worktree `.git` pointer (F-2 class defect) — never downgrades to fixture mode in a worktree |
| `S1_INTEGRATION_EVENT` | pinned: `ANOX-EVENT-0055`, type `remediation_session_integration`, task, `start_head 29a6643…`, `merged_head e32463ca…`, `merged_base 0f932520…`, report ref, branch `integration/s1-after-s0-001`, `supersedes_provisional_event = ANOX-EVENT-0054` |
| `validate_base` | when the S1 delivery is active: `lifecycle_legality.canonical_integration_delivery` (merge parents exactly (start, pinned S1 head); first-parent chain exactly [merge, substantive, metadata]; only the two pinned S1 commits integrated; metadata allowlisted). Optionally, exactly one **authorized pre-ratification correction pair** `[D1, D2]` may follow — D1 pinned via `described_head`, D2 metadata-allowlisted — and only when `CURRENT_STATE` declares the Human-authorized correction task `ANOX-TASK-REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001`; unauthorized or malformed correction chains are rejected |
| `validate_registry` | 13 → **14** for exactly `SEC-AUDIT-REG-0014` (all fields pinned, report + preserved-source hashes); arbitrary growth rejected; S0 record pins unchanged |
| `validate_no_product_changes` | S1 delivery active → enumerated S1 surface allow-list; forbids `crypto/rust/src/**`, `android/src/main/java/**`, `backend/`, `supabase/`, `migrations/`, `*.sql`, `docs/authority/**`; re-asserts no tracked `.so`, `crypto/rust/src` unchanged vs S1 base, CI hotfix (`packages: 'platform-tools'`) |
| `validate_project_memory` | accepts `0055` only as direct successor of `0052 → 0053 → 0054` and only when `CURRENT_STATE` declares the S1 delivery (S0 one-time exception **not** reusable); rejects duplicate ids, the S1 original task under any id (provisional 0054 as canonical), and the S1 task under any id ≠ 0055 |

## 3. Requested Human decision (to be recorded by the Human Owner, not by this task)

If ratified, the Human Owner would — following the exact precedent of
`ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001` —

1. record `ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001` in
   `docs/workforce/registries/decisions.jsonl` with `scope = ONE_TIME_CHANGE_SPECIFIC`,
   `ratified_change = S1_INTEGRATION_LIFECYCLE_EXTENSION`, `ratified_sha256 = d03e539a…`, and all
   `grants_*` flags `false`;
2. pin `d03e539a…` as a third authorized content in `tools/audit/validate_s0_contract_freeze.py`
   (`PROTECTED_SHARED_FILES`), with a paired adversarial test;
3. apply the patch (`git apply docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch`)
   and verify the validator hash equals `d03e539a…` and the paired suite hash equals `c305c21c…`;
4. no `PINNED_TEST_COUNTS` update is needed: the paired suite update keeps the count at exactly 277
   (era migration only, no added/removed assertions); re-running it must show 277/277 OK.

## 4. What this proposal does NOT do

- does **not** modify the protected shared validator or the S0 contract pin;
- does **not** ratify itself, close any MSC unit, start B004/B005 or unblock the product;
- does **not** grant S1 or any session standing permission over shared governance validators;
- does **not** authorise event numbers beyond `ANOX-EVENT-0055` or registry growth beyond `SEC-AUDIT-REG-0014`.
