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
2. prepared the exact minimum extension as a **patch** with a pinned post-change hash (below);
3. shipped the identical S1-era acceptance logic in a **separate, non-protected** validator
   `tools/audit/validate_s1_integration_evidence.py`, which imports the ratified module and runs
   every S0 protection verbatim, adding only the pinned S1-era sections;
4. shipped paired accept/reject adversarial tests (`tools/audit/test_s1_integration_evidence.py`).

Until ratification, the ratified central validator FAILS on the integrated repository **by design**
(its era pins: `LEDGER_EVENT = ANOX-EVENT-0052` chain ending at 0054, registry = 13, "no
product/CI/native changes"). This is the already-confirmed `S1_SHARED_VALIDATOR_FOLLOWUP_REQUIRED`
condition, now made precise and ready for a Human decision.

## 2. The proposed change

- **Patch:** `docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch`
- **Applies to (ratified):** `89c7358fbbe61c71c8fcde114ffc8a83aa33f52bd3fb763417e00f4131d84bb7`
- **Yields (proposed):** `03bdf7c84d7cf1eac170c8c70de582c98b001f0b582136b0ecf76c8a5d102822`
- **Integrity:** `validate_s1_integration_evidence.py` applies the patch to the ratified content in a
  scratch directory and fails if the result is not exactly the proposed hash.

Content of the extension (additive; no S0 predicate or pin is altered):

| Area | Proposed behaviour |
|---|---|
| `has_git()` | recognises a linked-worktree `.git` pointer (F-2 class defect) — never downgrades to fixture mode in a worktree |
| `S1_INTEGRATION_EVENT` | pinned: `ANOX-EVENT-0055`, type `remediation_session_integration`, task, `start_head 29a6643…`, `merged_head e32463ca…`, `merged_base 0f932520…`, report ref, branch `integration/s1-after-s0-001`, `supersedes_provisional_event = ANOX-EVENT-0054` |
| `validate_base` | when the S1 delivery is active: `lifecycle_legality.canonical_integration_delivery` (merge parents exactly (start, pinned S1 head); first-parent chain exactly [merge, substantive, metadata]; only the two pinned S1 commits integrated; metadata allowlisted) |
| `validate_registry` | 13 → **14** for exactly `SEC-AUDIT-REG-0014` (all fields pinned, report + preserved-source hashes); arbitrary growth rejected; S0 record pins unchanged |
| `validate_no_product_changes` | S1 delivery active → enumerated S1 surface allow-list; forbids `crypto/rust/src/**`, `android/src/main/java/**`, `backend/`, `supabase/`, `migrations/`, `*.sql`, `docs/authority/**`; re-asserts no tracked `.so`, `crypto/rust/src` unchanged vs S1 base, CI hotfix (`packages: 'platform-tools'`) |
| `validate_project_memory` | accepts `0055` only as direct successor of `0052 → 0053 → 0054` and only when `CURRENT_STATE` declares the S1 delivery (S0 one-time exception **not** reusable); rejects duplicate ids, the S1 original task under any id (provisional 0054 as canonical), and the S1 task under any id ≠ 0055 |

## 3. Requested Human decision (to be recorded by the Human Owner, not by this task)

If ratified, the Human Owner would — following the exact precedent of
`ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001` —

1. record `ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001` in
   `docs/workforce/registries/decisions.jsonl` with `scope = ONE_TIME_CHANGE_SPECIFIC`,
   `ratified_change = S1_INTEGRATION_LIFECYCLE_EXTENSION`, `ratified_sha256 = 03bdf7c8…`, and all
   `grants_*` flags `false`;
2. pin `03bdf7c8…` as a third authorized content in `tools/audit/validate_s0_contract_freeze.py`
   (`PROTECTED_SHARED_FILES`), with a paired adversarial test;
3. apply the patch (`git apply docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch`)
   and verify the file hash equals `03bdf7c8…`;
4. update `PINNED_TEST_COUNTS` in `tools/audit/validate_s0_evidence_preservation.py` if the central
   adversarial suite is extended with the S1-era cases (currently kept at 277 with fixture
   normalisation only).

## 4. What this proposal does NOT do

- does **not** modify the protected shared validator or the S0 contract pin;
- does **not** ratify itself, close any MSC unit, start B004/B005 or unblock the product;
- does **not** grant S1 or any session standing permission over shared governance validators;
- does **not** authorise event numbers beyond `ANOX-EVENT-0055` or registry growth beyond `SEC-AUDIT-REG-0014`.
