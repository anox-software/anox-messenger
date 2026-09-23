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

> ### SUPERSESSION NOTICE — three earlier revisions must NEVER be ratified
>
> | Revision | Validator post-image | Status |
> |---|---|---|
> | 1 | `e52f626a46f27af5…` | **SUPERSEDED — NEVER RATIFY** (valid only for the pre-final-correction topology) |
> | 2 | `d03e539a49e9126e…` | **SUPERSEDED — NOT COMMITTABLE — NEVER RATIFY** (technically verified but structurally not committable: committing it makes the chain 8/9 while the shape rule admitted only 5 or 7) |
> | 3 | `87cd5e202325f192…` | **SUPERSEDED BY THE NEW FOUR-FILE PACKAGE — NEVER RATIFY** (admitted the tail, but only over two paths, so committing it broke the frozen S0 contract with no authorized repair path — retest S1-004 blocking finding B-6) |
> | 4 | `64fc3ffb3dc67bd0…` | **CURRENT PROPOSAL** (atomic four-file ratification transaction) |
>
> Revision 2's defect was found by
> `TARGETED-INDEPENDENT-RATIFICATION-COMMITTABILITY-RETEST-S1-003`, which committed
> the package in a disposable clone and observed the would-be-ratified validator
> reject its own repository. Revision 3's defect was found the same way by
> `TARGETED-INDEPENDENT-FINAL-RATIFICATION-RETEST-S1-004`: the central validator and
> the S1 validator both passed at committed R1/R2, but
> `tools/audit/validate_s0_contract_freeze.py` pinned the protected validator to only
> two authorized contents, and neither a two-path R1 (which may not touch the S0
> contract) nor a metadata-only R2 (which may not touch `tools/**`) could repair it.
>
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

### The ratification is ONE atomic four-path transaction (R1)

`R1` must change **exactly** these four paths — no fewer, no fifth:

| # | Path | Pre-image | Post-image (**pinned**) |
|---|---|---|---|
| 1 | `tools/audit/validate_security_audit_evidence_preservation.py` | `89c7358fbbe61c71…` | `859e834e06876e34efbdaf9f209005c86d0562b54237f602c45f110bc72a6148` |
| 2 | `tools/audit/test_security_audit_evidence_preservation.py` | `b69dbb3546eae50a…` | `c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462` |
| 3 | `tools/audit/validate_s0_contract_freeze.py` | `5077558321dcc6e3…` | `7dbcaf60d7ba4dab1124e2af035eea64a8847a6d7942a6316229eb2bf645d5b4` |
| 4 | `tools/audit/test_s0_contract_freeze.py` | `6590a218b11bce51…` | `d22034e61257f3d13588b402b49eba2396ee2b5b9a736774e9a6522ee037f13a` |

File 3 is the frozen S0 contract that content-pins file 1; file 4 is its paired
adversarial suite. Files 1+2 alone were uncommittable (B-6). All four move in the
same commit or the ratification does not happen.

**No fixed point:** file 3 pins the post-images of files 1, 2 and 4, but never its
own — a digest cannot be pinned inside the file it describes. File 3's own
post-image is pinned externally by `tools/audit/validate_s1_integration_evidence.py`
(which is deliberately **not** part of the transaction) and by the Human
ratification record, and structurally by R1's exact changed-path set.

- **Patch:** `docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch`
- **Integrity:** `validate_s1_integration_evidence.py` copies all four pre-images into a
  scratch directory, applies the patch, and fails unless the changed path set is exactly the
  four paths and every one of the four results is exactly its pinned post-image.
- **Atomicity:** the same validator refuses any half-applied state — all four files must sit
  in the same era (all pre-images or all post-images).
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

1. apply the patch and commit it as **R1**, changing exactly the four package paths
   (this commit *is* the act of ratification);
2. commit the required metadata synchronisation **R2** (metadata allow-list only), which
   advances `described_head` to R1 and records
   `ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001` in
   `docs/workforce/registries/decisions.jsonl` with `scope = ONE_TIME_CHANGE_SPECIFIC`,
   `ratified_change = S1_INTEGRATION_LIFECYCLE_EXTENSION`, `ratified_files` = the four paths,
   `ratified_sha256` pinning all four post-images, and all `grants_*` flags `false`;
3. no separate follow-up is needed to pin the new content in the S0 contract: that pin, and its
   paired adversarial coverage, are *inside* R1 (files 3 and 4). This is what makes the package
   committable at all;
4. verify the four post-images equal `64fc3ffb…`, `c305c21c…`, `058e8ec0…`, `d22034e6…`;
5. no `PINNED_TEST_COUNTS` update is needed: the central paired suite stays at exactly **277** and
   the S0 contract paired suite stays at exactly **100** (era migration and strengthened
   assertions only — no assertion weakened, no negative case dropped). Both must show full
   green before and after R1/R2.

## 4. What this proposal does NOT do

- does **not** modify the protected shared validator or the S0 contract pin;
- does **not** ratify itself, close any MSC unit, start B004/B005 or unblock the product;
- does **not** grant S1 or any session standing permission over shared governance validators;
- does **not** authorise event numbers beyond `ANOX-EVENT-0055` or registry growth beyond `SEC-AUDIT-REG-0014`;
- does **not** create any general future-successor permission for the protected shared validator:
  the S0 contract admits exactly one further content (`64fc3ffb…`), under exactly one decision id,
  over exactly one four-path set. Any other content remains a hard failure requiring a new Human
  ratification.
