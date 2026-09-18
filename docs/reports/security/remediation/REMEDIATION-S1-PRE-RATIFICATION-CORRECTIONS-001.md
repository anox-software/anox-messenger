# REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001

**Task:** `ANOX-TASK-REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001`
**Authorization:** `ANOX-DECISION-S1-PRE-RATIFICATION-CORRECTIONS-AUTHORIZATION-001`
(Human Product & Security Owner; exactly one change-specific correction pass)
**Branch:** `integration/s1-after-s0-001` (extends the recorded S1 delivery by the
authorized correction pair `[D1 substantive, D2 metadata]`)
**Status:** PRE-RATIFICATION CORRECTION — Shared Validator extension remains a
**proposal**; B-1 (S0-validator ownership deviation) remains **unresolved** pending
explicit Human disposition; nothing herein closes MSC units, starts B004/B005,
rewrites canonical history, or authorises push/merge.

## 1. Scope exercised (exactly the authorized surface)

| Authorized edit | Change |
|---|---|
| `tools/audit/validate_s0_contract_freeze.py` | Git-context detection now resolves a linked-worktree `.git` pointer file (real `.git` dir **or** well-formed `gitdir:` pointer to an existing Git dir) and fails closed on absent/malformed/dangling metadata instead of silently `SKIP`ping the S0 scope gate (retest finding N-1). No forbidden/pinned set, era range, or protected-file predicate altered. |
| `tools/audit/validate_s0_evidence_preservation.py` | No code change required this pass (era-precision already verified non-weakening). `PINNED_TEST_COUNTS["test_s0_contract_freeze.py"]` 98 → 100 for the two paired worktree tests. |
| Paired tests | `test_s0_contract_freeze.py` +2 worktree cases (valid `gitdir:` pointer executes the gate; malformed pointer fails closed). `test_s1_integration_evidence.py` +7 (authorized correction-pair accept/reject topology cases + subtle patch-tamper case). `test_s1_retest_remediation.py` +7 (escaped-PEM scan cases; consumer soft-fail cases). `test_security_audit_evidence_preservation.py` is **not** modified in place — its migration ships inside the ratification patch. |
| S1-owned files | `tools/security/secret_scan.py` (N-3: single-line `\n`-escaped PEM detection), `tools/security/validate_ci_pipeline.py` (N-4: shell soft-fail `||`/`; exit` detection on consumer download/verify/Gradle steps), `docs/current/REPOSITORY_SECURITY_POLICY.md` (N-2: attestation trust-boundary wording), `tools/audit/lifecycle_legality.py` + `tools/audit/validate_s1_integration_evidence.py` (authorized correction-pair delivery proof), ratification patch + proposal record (B-2), registry record, this report. |

## 2. Findings disposition

- **B-2 — RESOLVED (package complete):** the ratification patch now covers both
  `validate_security_audit_evidence_preservation.py` and its paired suite
  `test_security_audit_evidence_preservation.py`. Simulated application yields exactly
  `e52f626a46f27af59b51acf2af20ec6762ab71f8c1e35239e6c59f70182af1f8` (validator) and
  `c305c21c9405454067721efe7c8d0395e99aed9e6870cf49e3daedb4a3552462` (suite), and the
  post-application suite runs **277/277 OK** (era migration only — no assertion
  weakened, no negative case dropped, count unchanged).
- **B-1 — UNRESOLVED BY DESIGN:** this pass records the previously verified
  non-weakening S0-validator edits under explicit Human authorization, but the
  ownership deviation itself still requires the final Human ratification decision.
- **N-1 — FIXED:** S0 scope gate executes in linked worktrees and fails closed on
  malformed Git metadata.
- **N-2 — DOCUMENTED:** policy wording now states the attestation is a self-asserted
  manifest (unsigned); the cryptographic limitation is disclosed, not eliminated.
- **N-3 — FIXED:** escaped-newline PEM (`\\n`-joined key body) is detected.
- **N-4 — FIXED:** shell soft-fail masking on consumer download/verify/Gradle steps
  is rejected; legitimate `&&` chains still accepted.
- **N-5 — DOCUMENTED (cannot be rewritten):** sealed `ANOX-EVENT-0055` recorded
  `test_s1_integration_evidence: 53`; the suite is now 68 tests (authorized paired
  additions). Canonical events are immutable, so the sealed figure stays; the
  truthful current count is recorded in `CURRENT_STATE` / continuity metadata.
- **N-6 — FIXED:** proposal wording distinguishes ratified vs proposed validator
  content.
- **N-7 — UNCHANGED (pre-existing, central-validator-mitigated):** prior-record
  protection binds hash shape; the central validator binds the value.

## 3. Delivery topology

Pinned original delivery preserved: merge `dd6e2c5d82f0` + substantive
`ea20aaaf330c` + metadata `573c5f58b91a`. The correction pair appends exactly
`[D1, D2]` where D1 is bound to `CURRENT_STATE.described_head` and D2 touches only
`METADATA_ALLOWLIST` paths. `canonical_integration_delivery` accepts the 5-commit
shape only while `CURRENT_STATE.current_task` is the authorized correction task;
every other shape (missing authorization, wrong pins, extra commits, non-metadata
D2) is rejected — see `test_410`–`test_415`.

## 4. Verification summary

- `test_s1_integration_evidence` 68/68 · `test_s1_retest_remediation` 101/101 ·
  `test_s0_contract_freeze` 100/100 · `test_s0_evidence_preservation` 40/40 ·
  `test_security_audit_evidence_preservation` 277/277 (pre- and post-application)
- Proposal simulation: patch applies cleanly to both ratified files; post hashes exact.
- Escaped-PEM probe: detected; source-literal false positives: none.
- Consumer soft-fail probes: `|| true`, `; echo`, `; exit 0` rejected; `&&` accepted.
- MSC: 42 open / 0 closed; SECURITY_REMEDIATION IN_PROGRESS; B004/B005 NOT_STARTED;
  product BLOCKED_PENDING_FINAL_AUDIT. `docs/authority/*` untouched.

## 5. Explicit non-goals (per authorization)

No ratification recorded, no MSC closure, no B004/B005 work, no `docs/authority/*`
change, no history rewrite, no push/merge. An independent retest of this branch is
required before any final ratification or push decision.
