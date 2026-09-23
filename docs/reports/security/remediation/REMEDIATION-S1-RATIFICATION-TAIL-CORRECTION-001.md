# REMEDIATION-S1-RATIFICATION-TAIL-CORRECTION-001

**Task:** `ANOX-TASK-REMEDIATION-S1-RATIFICATION-TAIL-CORRECTION-001`
**Authorization:** `ANOX-DECISION-S1-RATIFICATION-TAIL-CORRECTION-AUTHORIZATION-001`
(`HUMAN-DECISION-S1-RATIFICATION-TAIL-CORRECTION-AUTHORIZATION-001`; Human Product
& Security Owner; `ONE_TIME_CHANGE_SPECIFIC`; verbatim in
`docs/reports/security/decisions/S1-RATIFICATION-TAIL-CORRECTION-AUTHORIZATION-001.md`)
**Authorized start head:** `4319dacaa7ac94405e8b72fe23effb6e733ab898`
**Remediates:** `TARGETED-INDEPENDENT-RATIFICATION-COMMITTABILITY-RETEST-S1-003`
(BLOCKER-1, BLOCKER-2, N-12)

> **NOT INDEPENDENTLY VERIFIED · NOT HUMAN-RATIFIED.** Implemented and checked by
> the same agent that produced retests S1-002 and S1-003. The regenerated package
> `87cd5e2023…` is a **proposal only**. Targeted independent re-verification by a
> non-authoring session — repeating the committed R1 and R1+R2 simulation — is
> required before Human ratification.

## 1. Package revisions

| Rev | Validator post-image | Paired tests | Status |
|---|---|---|---|
| 1 | `e52f626a46f27af5…` | `c305c21c9405…` | **SUPERSEDED — never ratify** (pre-final-correction topology only) |
| 2 | `d03e539a49e9126e…` | `c305c21c9405…` | **SUPERSEDED — never ratify** (structurally not committable) |
| 3 | **`87cd5e202325f1921954fc3a6e23999f987fc65d65bb13652ae34473001fbecd`** | **`c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462`** | **CURRENT PROPOSAL** |

Applies to the unchanged Human-ratified baseline
`89c7358fbbe61c71…` / `b69dbb3546eae50a…`.

**Disclosure on the paired-tests hash:** `c305c21c9405…` is *unchanged* across all
three revisions. The paired suite performs the same era migration and stays pinned
at **277** tests (`PINNED_TEST_COUNTS`), which this pass is not authorized to
change. Only the validator post-image is new. New coverage for the ratification
tail was therefore added to the S1-owned suite
(`test_s1_integration_evidence.py`, 75 → **84**) rather than padded into the
pinned central suite.

## 2. BLOCKER-1 — non-circular ratification tail

The delivery proof now admits, on top of a completed delivery, **at most**:

- **R1** — the Human-ratification application: parent must be the completed
  delivery tip, and it must change **exactly**
  `tools/audit/validate_security_audit_evidence_preservation.py` and
  `tools/audit/test_security_audit_evidence_preservation.py`; the resulting
  contents are fixed by hashes already recorded in evidence.
- **R2** — the required metadata synchronisation: child of R1, restricted to
  `METADATA_ALLOWLIST`, and it must advance `described_head` to R1.

Nothing beyond R1/R2 is accepted, so this is **not** a generic append slot. No
validator ever needs to know its own future commit SHA.

**Tail detection is signature-based, not arithmetic.** Counting alone is
ambiguous — with two consumed pairs a 9-commit chain could be *"2 consumed + an
open correction pair"* or *"1 consumed + R1 + R2"*. The tail is identified by R1's
exact changed-path set, and a commit that touches the package but not exactly is
reported precisely instead of degrading into a generic shape error.

Because R1 may not touch metadata, the `described_head` binding is stage-aware:
at R1 the pre-ratification pointer still holds; at R2 it must equal R1.

## 3. BLOCKER-2 — pre-ratification vs ratified successor

`validate_s1_integration_evidence.py` now admits **exactly two** contents and
never conflates them: `CENTRAL_RATIFIED_SHA256` (`PRE_RATIFICATION`) and
`CENTRAL_PROPOSED_SHA256` (`RATIFIED_SUCCESSOR_APPLIED`). Any other content is a
hard fail. Coherence is enforced both ways:

- successor content present **without** an authorized tail → FAIL
- tail present **without** the exact successor content → FAIL
- completed `R1R2` tail without `CURRENT_STATE.ratification_decision_id ==
  ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001` → FAIL

## 4. D1'/D2' substitution closed

`[a79e3b3db9b441fd81b5f76f6804f90eb44bb36b, 4319dacaa7ac94405e8b72fe23effb6e733ab898]`
is promoted into `CONSUMED_CORRECTION_PAIRS` in both the S1 validator and the
proposed central validator. Both pairs are now pinned by SHA; substitution of
either is rejected. The residual disclosed in S1-002/S1-003 is closed for
`D1'/D2'`; only this pass's own pair remains bound by `described_head` until a
future decision promotes it.

## 5. N-12

Stale `e52f626a46f2…` references in `CURRENT_HANDOFF.md`,
`CURRENT_NEXT_DEVIN_TASK.md` and `CURRENT_OPEN_WORK.md` now name the current
proposal and mark the two superseded revisions.

## 6. Non-goals honoured

`docs/authority/*` untouched · S0 protections not weakened · no history rewrite ·
`ANOX-EVENT-0055` unchanged (this pass is a **NON-EVENT**) · MSC 42 open / 0
closed · `B004`/`B005` `NOT_STARTED` · no product development · Shared Validator
remains a **proposal** · **no push, PR or merge** · **no self-ratification**.
