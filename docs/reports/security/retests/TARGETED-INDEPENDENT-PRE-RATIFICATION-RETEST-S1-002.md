# TARGETED-INDEPENDENT-PRE-RATIFICATION-RETEST-S1-002

**Mode:** `READ_ONLY_INDEPENDENT_SECURITY_RETEST` (no repository mutation)
**Target head:** `f08749e2e5ec45e76b1ea98c5c999e4679be3ffe`
**Branch:** `integration/s1-after-s0-001`
**Reviewed delivery:** `REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001`
(correction pair `0d1549d12d02` + `f08749e2e5ec`)
**Predecessor retest:** `TARGETED-INDEPENDENT-INTEGRATION-RETEST-S1-001`
**Result:** `FAIL` — 4 merge blockers, 5 non-blocking findings
**Repository modified:** NO

## 1. Topology — PASS (exact)

`[M dd6e2c5d] → C1 ea20aaaf → C2 573c5f58 → D1 0d1549d1 → D2 f08749e2`; `M`
retains its original parents `29a6643189…` / `e32463ca71…`; `dace146`, `ea838fa`,
`fc58414`, `e32463ca` all remain ancestors; no rewrite, squash or rebase.
`origin/main` unchanged at `29a6643189…`; the integration branch is absent from
the remote.

## 2. Merge blockers

| ID | Severity | Finding |
|---|---|---|
| **B-1** | HIGH | Human authority for the S0-owned validator edits was **not** independently demonstrated. `ANOX-DECISION-S1-PRE-RATIFICATION-CORRECTIONS-AUTHORIZATION-001` first appears in the very commits it authorizes (`git log -S` → only `0d1549d`, `f08749e`), has no dedicated decision report, no `authority_refs`, unsigned commits authored `Test <test@anox.software>`. Contrast the genuine `ANOX-DECISION-HUMANPREREMEDIATION001` (own governance branch → PR #33 → decision report). |
| **B-3** | HIGH | B027 governance regression: `validate_b027a` / `b027b` / `b027_integrity` PASS at `C2`, FAIL at HEAD — (a) the new decision record is missing required `authority_refs`; (b) `multiple active writers on branch integration/s1-after-s0-001`. |
| **B-4** | MEDIUM | `validate_continuity --mode live` PASS at `C2`, FAIL at HEAD: `delivery tail 0d1549d12d02..f08749e2e5ec contains non-metadata-only paths: docs/workforce/registries/decisions.jsonl`; `__EFFECTIVE_GATE__` consequently unresolvable. |
| **B-5** | MEDIUM | `test_s0_contract_freeze` is **99/100** in any normal clone: `test_91` derives its pointer from `git rev-parse --git-dir`, which returns a relative `.git` outside a linked worktree; the validator resolves it against the fixture root and rejects it. The claimed "100/100" held only in the implementer's worktree. `PINNED_TEST_COUNTS` counts tests, not passes. |

## 3. Resolved / truthful

- **B-2 — RESOLVED.** Package covers both files; applying it yields exactly
  `e52f626a46f2…` (validator) and `c305c21c9405…` (paired suite); post-application
  central validator **PASS** and suite **277/277**. All 17 adversarial probes fail
  closed (duplicate/missing/reordered/skipped events, provisional 0054 as
  canonical, arbitrary registry growth, REG-0014 repurposed, S2/S3/S4
  authorization, B004/B005 advancement, MSC closure, authority mutation, product
  source mutation, tracked `.so`, CI-hotfix rollback). Malformed patch, tampered
  pre-images and a subtle tamper that still applies cleanly are all rejected by
  post-image hash mismatch.
- **N-1 FIXED** (validator): scope gate executes in a real linked worktree and in
  a normal clone; malformed/dangling/NUL/two-line/non-git-dir pointers all fail
  closed. **N-2 TRUTHFUL**, **N-3 FIXED**, **N-5 TRUTHFULLY HANDLED** (ledger blob
  byte-identical `054dcc85…`; sealed `0055` still records `53`; discrepancy
  disclosed), **N-6 FIXED**.
- **S0 regression — NONE.** `docs/authority/**` unchanged; forbidden prefixes and
  `AUTHORIZED_S0_BASE_SHA` unchanged; protected shared files still checked at
  current content. All S0 authority probes fail closed.
- **Test-count deltas genuine.** 98→100, 61→68, 94→101 = 16 new functions, no
  duplicates, no skips; mutation testing killed 15/16 (the 16th is `test_91`,
  red at baseline — B-5).

## 4. Non-blocking findings

| ID | Severity | Finding |
|---|---|---|
| **N-7** | carried | Prior-record protection binds hash shape; the central validator binds the value. |
| **N-8** | MEDIUM | N-4 incomplete: multiline `run:` blocks masking the mandatory verify/download/Gradle exit status are not detected — `set +e`, trailing `exit 0`, trailing `true`, swallowing subshell all PASS. `&&` correctly accepted. |
| **N-9** | MEDIUM | The correction-delivery proof grants a standing, reusable 2-commit append slot. `D1` is pinned nowhere; it is bound only to the agent-writable `CURRENT_STATE.described_head`, and `correction_task` is a validator constant. Demonstrated: a replacement pair carrying an extra unauthorized change to `tools/security/secret_scan.py` was accepted. |
| **N-10** | LOW | A `.git`-absent tree still SKIPs the S0 scope gate ("fixture mode"), so an exported tree passes without scope enforcement. |
| **N-11** | LOW | `SOFTFAIL_RUN = \|\||;` rejects any `;` in a mandatory step — fails closed (safe) but brittle. |

## 5. State verified unchanged

`GLOBAL_OPEN_MSC = 42`; `MSC_CLOSED = 0`; `MSC-UNIT-001/002 RUNTIME_TESTED =
PENDING` under exact FCP-1 (arm64 `IMPLEMENTER_ONLY_NOT_INDEPENDENT`, x86_64
`PENDING_REAL_CI_OR_INDEPENDENT_RUNTIME_EVIDENCE`); `B004`/`B005 NOT_STARTED`;
`PRODUCT = BLOCKED_PENDING_FINAL_AUDIT`.

Runtime/Android instrumented evidence: **NOT_RUN** — no `adb`/`emulator`,
`ANDROID_HOME` unset, no device or KVM host. No PASS inferred.

## 6. Disposition

`RATIFICATION_TECHNICALLY_SAFE` for the two-file Shared Validator **package**;
**not** safe to execute ratification on this head while the branch's own
governance gates are red. B-1 requires Human disposition.

Cleared by `REMEDIATION-S1-FINAL-CORRECTIONS-001` under
`ANOX-DECISION-S1-FINAL-CORRECTION-AUTHORIZATION-001`: B-1 Human-ratified;
B-3/B-4/B-5/N-8/N-9 remediated. That correction pass was implemented by the same
agent that produced this retest and is therefore **not independently verified**.
