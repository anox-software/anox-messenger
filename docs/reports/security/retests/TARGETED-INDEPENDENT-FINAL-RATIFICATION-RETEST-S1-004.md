# TARGETED-INDEPENDENT-FINAL-RATIFICATION-RETEST-S1-004

**Mode:** `READ_ONLY_FINAL_RATIFICATION_TECHNICAL_VERIFICATION` (no repository mutation)
**Target head:** `10cc68c442bc67be03d863ad20e29e4dfcb0bd51`
**Reviewed delivery:** `REMEDIATION-S1-RATIFICATION-TAIL-CORRECTION-001` (`4b31f680613651772d6006c2d47d1f6ccd1bb837` + `10cc68c442bc67be03d863ad20e29e4dfcb0bd51`)
**Result:** `RATIFICATION_NOT_COMMITTABLE` — 1 blocking finding, 2 non-blocking
**Repository modified:** NO
**Session:** new non-authoring session (did not implement `REMEDIATION-S1-FINAL-CORRECTIONS-001` or `REMEDIATION-S1-RATIFICATION-TAIL-CORRECTION-001`)

## 1. Verified good

- **Topology exact:** `M dd6e2c5d → C1 ea20aaaf → C2 573c5f58 → [0d1549d1, f08749e2] → [a79e3b3d, 4319daca] → [4b31f680, 10cc68c4]` (9 first-parent commits); merge parents `(29a6643…, e32463ca…)`; `e32463ca ← fc58414b ← 0f932520` intact; no rewrite, squash or rebase.
- **Deterministic regeneration:** `89c7358f…`/`b69dbb35…` → `87cd5e2023…`/`c305c21c…`, byte-exact, reproduced independently.
- **All pre-ratification gates PASS at target head:** B027-A/B/integrity, continuity live, S0 contract validator + 100/100, S0 preservation + 40/40, S1 integration validator + 84/84, S1 remediation 107/107, S1 build provenance 66/66, central suite 277/277, CI structural, secret scan, B021, B017-Lite (35/35), `git diff --check` clean. The ratified central validator FAILS pre-ratification by design (era pins: 0052-chain, 13 records, no product/CI/native).
- **Consumed correction pairs pinned in both validators;** omit / substitute pair 1 / substitute pair 2 / reorder / insert-alternate all rejected with exact reasons (trees replayed verbatim as new SHAs).
- **Era-awareness coherent both directions:** baseline+no-tail PASS, successor+tail PASS, successor-without-tail FAIL, baseline-after-tail FAIL, arbitrary third hash / tampered successor / fake second ratification FAIL.
- **Unauthorized append matrix — all rejected:** arbitrary substantive, arbitrary metadata, fake third correction pair, R1 missing a package path, R1 with an extra path, S2 task reusing S1 authority, and every post-tail append.
- **Stage-aware `described_head`:** correct pre-ratification; `R1` requires no metadata it cannot modify; `R2` must advance it to `R1` exactly (stale value and missing `ratification_decision_id` both rejected).
- **State unchanged:** MSC 42 open / 0 closed; B004/B005 `NOT_STARTED`; product `BLOCKED_PENDING_FINAL_AUDIT`.

## 2. BLOCKER B-6 (HIGH) — committed R1/R2 breaks the frozen S0 contract

Simulated `R1` (`bacaf195…`, exactly the two package paths, post-images exact) and
metadata `R2` (`bcf8ba30…`) in a disposable clone:

| Gate | at R1 | at R1+R2 |
|---|---|---|
| Central validator | PASS | PASS |
| Central 277-suite | 277/277 | 277/277 |
| S1 integration validator | PASS | PASS |
| S0 preservation | PASS | PASS (40/40) |
| B027-A / B / integrity | — | PASS / PASS / PASS |
| Continuity live | FAIL (expected: tail not yet described) | PASS |
| **S0 contract validator** | **FAIL** | **FAIL** |
| S0 contract suite | 98/100 | 98/100 |
| S1 integration suite | — | 78/84 |

Root cause: `validate_s0_contract_freeze.py::PROTECTED_SHARED_FILES` admits only
`756141b3…` and `89c7358f…`; the package makes the protected file `87cd5e2023…`:

> `…content 87cd5e202325f192… is neither the pre-S0 baseline nor a Human-ratified change … a new Human ratification is required`

No authorized commit could repair it: an `R1` that also changed
`validate_s0_contract_freeze.py` was rejected by **both** validators
(*"must change exactly [2 paths], changed [3 paths]"*), and
`validate_s0_contract_freeze.py` / `test_s0_contract_freeze.py` are not in
`METADATA_ALLOWLIST`, so `R2` could not either. Collateral failures with the same
root cause: `test_00_baseline_passes`, `test_91…`,
`test_511_s0_scope_live_repo_passes_with_s1_integrated` and 5 fixture-era S1 tests.

This is the same *class* of defect as S1-003 BLOCKER-1, relocated from the
delivery-shape rule to the S0 contract pin.

## 3. Non-blocking

- **N-13 (MEDIUM)** — inverted supersession text. A blanket substitution left
  `CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, `PROJECT_STATE.md` and
  `CURRENT_OPEN_WORK.md` reading *"87cd5e202325… (supersedes e52f… and d03e…) …
  SUPERSEDED, never ratify"* — i.e. the current proposal presented as
  never-ratifiable.
- **N-14 (LOW)** — stale attribution: `CURRENT_NEXT_DEVIN_TASK.md` and
  `CURRENT_OPEN_WORK.md` attributed the pair `4b31f6806136` + metadata to
  `REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001` (actually
  `0d1549d1`/`f08749e2`) and still named an obsolete next task.
- **Observation (by design, disclosed)** — the central validator cannot
  authenticate its own content: at R1-with-tampered-successor it self-reports
  PASS. The non-protected S1 validator and the S0 contract catch it.
- **Provenance limitation** — every commit in the chain is unsigned
  (`%G? = N`, author `Test <test@anox.software>`); `is_human_authority: true` is a
  self-declaration, not cryptographic Human provenance.

## 4. Required remedy (as specified to the Human)

Make the ratification ONE atomic four-path transaction so the S0 contract pin and
its paired adversarial coverage travel inside `R1`; keep both pinned test counts
(277 and 100) exact; make the era-sensitive S1 tests pass in both eras; fix
N-13/N-14.

## 5. Disposition

Cleared by `REMEDIATION-S1-FOUR-FILE-RATIFICATION-TRANSACTION-001` under
`ANOX-DECISION-S1-FOUR-FILE-RATIFICATION-AUTHORIZATION-001`.
`87cd5e202325…` is **superseded by the four-file package and must never be
ratified**, alongside `e52f626a46f2…` and `d03e539a49e9…`.
