# HUMAN-DECISION-S1-FOUR-FILE-RATIFICATION-AUTHORIZATION-001

**Classification:** `HUMAN_AUTHORIZED_CHANGE_SPECIFIC_FOUR_FILE_RATIFICATION_TRANSACTION`
**Authority actor:** Human Product & Security Owner
**Decision id:** `ANOX-DECISION-S1-FOUR-FILE-RATIFICATION-AUTHORIZATION-001`
**Scope:** `ONE_TIME_CHANGE_SPECIFIC`
**Authorizes task:** `ANOX-TASK-REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001`
**Start head:** `10cc68c442bc67be03d863ad20e29e4dfcb0bd51`

> **Provenance limitation — stated plainly.** This document and the paired
> `decisions.jsonl` record are an agent transcription of a Human instruction. No
> commit in this delivery is cryptographically signed and no signed tag anchors
> it, so `is_human_authority: true` is a recorded declaration, **not**
> cryptographic Human provenance. Any reviewer must treat it as such.

## 1. Why this authorization exists

`TARGETED-INDEPENDENT-FINAL-RATIFICATION-RETEST-S1-004` returned
`RATIFICATION_NOT_COMMITTABLE` with one blocking finding:

- **B-6 (HIGH)** — at committed `R1` (and `R1+R2`) the central validator, its
  277-case suite, the S1 integration validator and S0 preservation all PASSED,
  but the **frozen S0 contract FAILED**, because
  `tools/audit/validate_s0_contract_freeze.py` (F-03) pinned the protected
  central validator to only two Human-ratified contents. Applying the package
  makes it a third. There was no authorized repair path:
  - an `R1` that also carried the S0 contract pin was rejected by both
    validators — *"ratification commit R1 must change exactly [2 paths], changed
    [3 paths]"*;
  - a metadata-only `R2` may not touch `tools/**`.
  Consequently `test_s0_contract_freeze` fell to 98/100 and the S1 suite to
  78/84 after ratification.

Two non-blocking findings were also recorded: **N-13** (a blanket substitution
left four current surfaces stating that the *current* proposal is "SUPERSEDED,
never ratify") and **N-14** (stale task/commit attribution in
`CURRENT_NEXT_DEVIN_TASK.md` and `CURRENT_OPEN_WORK.md`).

## 2. What is authorized

Exactly one further change-specific correction pass from
`10cc68c442bc67be03d863ad20e29e4dfcb0bd51`, to:

1. regenerate the ratification package as **ONE atomic transaction over exactly
   four paths**, so that a single `R1` commit can carry both the protected
   validator and the S0 contract that pins it:
   - `tools/audit/validate_security_audit_evidence_preservation.py`
   - `tools/audit/test_security_audit_evidence_preservation.py`
   - `tools/audit/validate_s0_contract_freeze.py`
   - `tools/audit/test_s0_contract_freeze.py`
   **No fifth path.**
2. admit in the S0 contract exactly **one** further authorized content for the
   protected shared validator, era-gated to the authorized transaction, with
   **no general future successor permission**;
3. bind the transaction pre-ratification in the S1-owned machinery (four paths,
   four post-images, historical consumed correction pairs, the optional
   metadata-only `R2` tail);
4. promote the frozen pair `[4b31f680613651772d6006c2d47d1f6ccd1bb837,
   10cc68c442bc67be03d863ad20e29e4dfcb0bd51]` into the consumed correction
   history so it can never be substituted;
5. correct the identified post-tail S1 tests (including `test_511`) so they pass
   in **both** legitimate eras without weakening any assertion;
6. repair N-13 / N-14 on current surfaces without rewriting historical evidence.

## 3. What is NOT authorized

This decision grants **NO**:

- change to `docs/authority/**`; no weakening of any S0 protection;
- history rewrite, rebase, squash, or change to `ANOX-EVENT-0055`;
- general or future successor permission for any
  `PROTECTED_SHARED_GOVERNANCE_FILE` — exactly one hash, one four-path set, one
  decision id;
- further correction pairs or ratification tails beyond this one pass;
- `S2`/`S3`/`S4` authority, `B004`/`B005` start, product development;
- MSC closure (must remain 42 open / 0 closed);
- `push`, `PR`, `merge`;
- **self-ratification.** The shared-validator package remains a PROPOSAL. The
  implementing agent may not record
  `ANOX-DECISION-S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-001`.

## 4. Required post-conditions

The delivery is only acceptable if, in a fresh disposable clone, a simulated
committed `R1` (exactly the four paths) satisfies **simultaneously**: central
validator PASS, central suite 277/277, **S0 contract validator PASS**, **S0
contract suite 100/100**, S0 preservation PASS, S1 integration validator PASS,
S1 integration suite full green — and the subsequent metadata-only `R2` keeps all
of those plus B027-A/B/integrity and continuity live.

Verification by the implementing agent is **NOT** independent verification.
