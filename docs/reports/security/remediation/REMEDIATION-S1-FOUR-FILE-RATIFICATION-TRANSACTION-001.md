# REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001

**Task:** `ANOX-TASK-REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001`
**Authority:** `ANOX-DECISION-S1-FOUR-FILE-RATIFICATION-AUTHORIZATION-001`
(`HUMAN-DECISION-S1-FOUR-FILE-RATIFICATION-AUTHORIZATION-001`, recorded verbatim in
`docs/reports/security/decisions/S1-FOUR-FILE-RATIFICATION-AUTHORIZATION-001.md`)
**Mode:** `FINAL BOUNDED PRE-RATIFICATION CORRECTION`
**Start head:** `10cc68c442bc67be03d863ad20e29e4dfcb0bd51`
**Branch:** `integration/s1-after-s0-001`
**Canonical event:** unchanged — `ANOX-EVENT-0055` remains the latest material event
**Resolves:** retest S1-004 `B-6` (blocking), `N-13`, `N-14`, and the related
post-ratification fixture/test failures
**Shared Validator status:** still a **PROPOSAL**. NOT Human-ratified.
**Independent verification:** **NO** — authored by the same agent that produced retest S1-004.

## 1. The defect being fixed (B-6)

The previous package (`87cd5e202325…` + `c305c21c9405…`) was verifiable but
**structurally uncommittable**. Applying it makes
`tools/audit/validate_security_audit_evidence_preservation.py` a *third* content,
while the frozen S0 contract (`tools/audit/validate_s0_contract_freeze.py`, F-03)
pinned it to exactly two. The deadlock had no authorized exit:

| Attempted repair | Outcome |
|---|---|
| `R1` = 2 package paths | S0 contract FAILS (`content 87cd5e2023… is neither the pre-S0 baseline nor a Human-ratified change`) |
| `R1` = 2 package paths + the S0 contract | Rejected by the central **and** S1 validators: `must change exactly [2 paths], changed [3 paths]` |
| metadata `R2` | `validate_s0_contract_freeze.py` / `test_s0_contract_freeze.py` are not in `METADATA_ALLOWLIST` |

## 2. The fix — one atomic four-path transaction

`R1` now changes **exactly** four paths (no fifth is ever admissible):

| # | Path | Pre-image | Post-image (pinned) |
|---|---|---|---|
| 1 | `tools/audit/validate_security_audit_evidence_preservation.py` | `89c7358fbbe61c71…` | `859e834e06876e34efbdaf9f209005c86d0562b54237f602c45f110bc72a6148` |
| 2 | `tools/audit/test_security_audit_evidence_preservation.py` | `b69dbb3546eae50a…` | `c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462` |
| 3 | `tools/audit/validate_s0_contract_freeze.py` | `5077558321dcc6e3…` | `7dbcaf60d7ba4dab1124e2af035eea64a8847a6d7942a6316229eb2bf645d5b4` |
| 4 | `tools/audit/test_s0_contract_freeze.py` | `6590a218b11bce51…` | `d22034e61257f3d13588b402b49eba2396ee2b5b9a736774e9a6522ee037f13a` |

File 2's post-image is unchanged by construction (same era migration); it is a
genuine member of the transaction because it differs from its ratified baseline
`b69dbb35…`. No cosmetic edit was made anywhere to manufacture a new hash.

### 2.1 No fixed point

File 3 pins the post-images of files **1, 2 and 4** — never its own. A digest
cannot be pinned inside the file it describes. File 3's own post-image is bound
from three independent directions instead:

- `tools/audit/validate_s1_integration_evidence.py` pins all four post-images and
  is deliberately **not** part of the transaction;
- `R1`'s exact changed-path set;
- the Human ratification record, which must pin all four (and which must pin the
  *live* content of file 3, checked against the live digest).

### 2.2 S0 contract successor — no general future permission

The successor admits exactly one further content for the protected validator,
under `ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001`, gated by
`_s1_integration_ratification()`:

- the three externally pinnable post-images must match exactly;
- in a Git context `_s1_ratification_transaction()` must prove `R1` structurally:
  a single-parent commit changing exactly the four paths and producing exactly
  the pinned post-images, with **at most one** following commit (the metadata
  `R2`), which may not touch `POST_R1_FORBIDDEN_PREFIXES`;
- the Human decision record is validated with the same discipline as F-01 and the
  S0 preservation ratification **whenever it is present**
  (`ONE_TIME_CHANGE_SPECIFIC`, `is_human_authority`, all `grants_*` false, all four
  digests exact — including file 3's, checked against the *live* content — and the
  canonical record file present);
- a record that is present but weakened, widened or forged fails;
- every historical S0 fail-closed protection is preserved: the pre-S0 baseline
  still fails, and any other content still fails with *"a new Human ratification
  is required"*.

### 2.2.1 Disclosed residual — and why "hardening" it would re-break the package

The decision record is deliberately **not mandatory inside the authorized tail**.
An earlier draft of this correction made it mandatory at `R2`, and the committed
simulation immediately reproduced the B-6 class of defect:

> `FAIL delivery tail 748f789ffe7f..7f7ab55c820c contains non-metadata-only paths:`
> `  - docs/workforce/registries/decisions.jsonl`

Because `R1` is restricted to the four package paths and cannot touch registries,
`R2` is restricted to metadata, and
`tools/continuity/validate_continuity.py::METADATA_ONLY_ALLOWLIST` does **not**
contain `docs/workforce/registries/decisions.jsonl` (it lists `runs`, `tasks` and
`findings` only), an `R2` carrying the record fails continuity live. Requiring it
would have made the package uncommittable again.

Resolution: the Human's *act* of ratification is the `R1` commit itself, proven
structurally; `CURRENT_STATE.ratification_decision_id` — which **is**
metadata-allowlisted and **is** required at the `R1+R2` stage by
`validate_s1_integration_evidence.py` — carries the declared decision id inside the
tail; and the full registry record is a later, separate governance commit outside
this delivery's authority. This residual is stated in the code itself so a future
pass does not re-introduce the deadlock.

In fixture mode (no `.git`) only content identity is checkable — the same
limitation the scope gate already discloses. Neither concession widens *which*
content is admissible.

### 2.3 Pinned test counts preserved

`PINNED_TEST_COUNTS` is untouched: the central paired suite stays at exactly
**277** `def test_` and the S0 contract paired suite at exactly **100**. Coverage
for the new pin was added *inside* existing tests (`test_52` now rejects tampering
of any pinned package member in the successor era; `test_91` now requires the
successor to have been admitted by the **structural** proof, never by identity
alone), not by padding the count. No assertion was weakened and no negative case
was dropped.

## 3. Era-aware S1 tests

`test_s1_integration_evidence.py` gained an `era()` helper that reads the era from
content, and the five era-sensitive tests now assert the malformed state that is
actually reachable in each era:

| Test | pre-ratification | post-ratification |
|---|---|---|
| `test_300` | `awaiting Human ratification` | `ratified four-file transaction matches the pinned proposal exactly` |
| `test_350` | patch tamper rejected | tampered live `test_security…` rejected (`half-applied`) |
| `test_350b` | subtle patch tamper rejected | tampered live `test_s0_contract_freeze` rejected |
| `test_351` | patch missing rejected | tampered live `validate_s0_contract_freeze` rejected |
| `test_352` | **each** of the four post-images missing from the record rejected | missing package member rejected |
| `test_511` | S0 scope PASS on the live repo | S0 scope PASS on the live repo (now genuinely reachable) |

`load_central()` additionally refuses any **half-applied** package: all four files
must sit in the same era, and the three superseded revisions (`e52f626a46f2…`,
`d03e539a49e9…`, `87cd5e202325…`) are rejected by name.

## 4. N-13 / N-14

- **N-13** — the four current surfaces that stated the *current* proposal was
  "SUPERSEDED, never ratify" now state the truth: `e52f…` SUPERSEDED / NEVER
  RATIFY; `d03e…` SUPERSEDED / NOT COMMITTABLE / NEVER RATIFY; `87cd…` SUPERSEDED
  BY THE FOUR-FILE PACKAGE / NEVER RATIFY; the four new hashes are the CURRENT
  PROPOSAL.
- **N-14** — `CURRENT_NEXT_DEVIN_TASK.md` and `CURRENT_OPEN_WORK.md` now attribute
  each correction pair to the task that actually authored it and name the correct
  next task.
- Historical evidence (`FORTSCHRITT.md` history lines, prior retest and
  remediation reports, the ledger) is **not** rewritten.

## 5. Not done / explicitly out of scope

No S1 security re-opening (F1-F9, architecture, crypto, Android/storage, MSC
units). No `docs/authority/**` change. No history rewrite. `ANOX-EVENT-0055`
unchanged. MSC 42 open / 0 closed. B004/B005 `NOT_STARTED`. Product
`BLOCKED_PENDING_FINAL_AUDIT`. No push, no PR, no merge, **no self-ratification** —
`ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001` is deliberately
absent from `decisions.jsonl`.
