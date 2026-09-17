# REMEDIATION-S1-CANONICAL-INTEGRATION-001 — S1 Canonical Integration + Retest Findings Remediation

**Task:** `ANOX-TASK-REMEDIATION-S1-CANONICAL-INTEGRATION-001`
**Mode:** writable implementation / integration, one writer, no push / PR / merge to `main`
**Delivery branch:** `integration/s1-after-s0-001`
**Canonical `main` at task start:** `29a6643189242a47c4a79c38acd04c1eca748787`
**Canonical event:** `ANOX-EVENT-0055` (recorded by the metadata commit that follows the substantive commit described here)
**Date:** 2026-09-16

## 1. Purpose

Integrate the completed, isolated `REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001`
delivery into the current canonical `main` (which already contains the S0 contract
freeze, corrected S0 remediation, independent S0 retests, canonical S0 evidence
preservation, the Android SDK CI hotfix and the S0 integration merge), then
remediate every finding F-1…F-9 of `INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001` and
execute the confirmed shared-validator follow-up. This is not S2/S3/S4, not B004/
B005, not a redesign of S1, and it closes no MSC unit.

## 2. Immutable inputs (unchanged, un-rewritten)

| Input | SHA |
|---|---|
| Original S1 base | `0f932520393feee6d479cc099f179f5766323125` |
| Original S1 substantive | `fc58414b6790c07f65d1dc9f72c019abd42efc86` |
| Original isolated S1 final | `e32463ca71b0fec62a5f20026e6dc528f9bff30c` |
| Canonical S0 preservation | `dace1467035bf6dbfda31f336640065804d41584` |
| CI-hotfix merge | `ea838fa5803f5088a1ce39d6ac026f8295a281a6` |
| Task-start canonical `main` | `29a6643189242a47c4a79c38acd04c1eca748787` |

All eight starting invariants (branch, clean tree, HEAD == main, ancestry of
`dace1467…` and `ea838fa5…`, S1 branch == `e32463ca…`, merge-base == `0f932520…`)
were verified before modification.

## 3. Git integration (real ancestry, no rebase / squash / cherry-pick)

Integration merge `dd6e2c5d82f0777aedfea9fd7a2516cb83254fdb` — parents
`29a6643189242a47c4a79c38acd04c1eca748787` (canonical) and
`e32463ca71b0fec62a5f20026e6dc528f9bff30c` (isolated S1). Both histories preserved.

### Conflict inventory and resolution rationale

| File | Resolution | Rationale |
|---|---|---|
| `PROJECT_STATE.md`, `docs/continuity/CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, `CURRENT_IMPLEMENTATION_STATE.md`, `CURRENT_NEXT_DEVIN_TASK.md`, `CURRENT_OPEN_WORK.md`, `CURRENT_STATE.json`, `PROJECT_MEMORY_SURFACE_INDEX.md`, `docs/workforce/WORKFORCE_STATE.json` | canonical S0 side | current-state surfaces: canonical S0 authority wins over stale isolated S1 metadata; re-synchronised for `ANOX-EVENT-0055` in the metadata commit |
| `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` | canonical S0 side | the isolated S1 line claimed `ANOX-EVENT-0054`, which canonical `main` owns for S0 evidence preservation; admitting it would duplicate a canonical event id. The provisional line remains preserved in the original S1 commits. |
| `FORTSCHRITT.md` | both, chronological | append-style log; the S1 section is kept as history and explicitly annotated **provisional / NONCANONICAL**; its `ANOX_EVENT` marker is demoted so continuity tooling cannot parse it as canonical |
| `docs/workforce/registries/tasks.jsonl` | union | the genuine S1 task record is intended registry growth |
| `.github/workflows/ci.yml` | auto-merge + semantic fix | S1's pipeline retained; the canonical CI hotfix (`packages: 'platform-tools'`) applied to S1's two new instrumented jobs (`'platform-tools emulator'`); string `tools platform-tools` absent |

No S1 security implementation file conflicted.

## 4. Event collision

Isolated S1 provisionally used `ANOX-EVENT-0054`. Canonical `main` assigned
`ANOX-EVENT-0054` to `SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001`.
The provisional identity is **NONCANONICAL**. Canonical ledger inspected: 54 events,
no duplicates, last = `0054` → next legal id **`ANOX-EVENT-0055`** (assigned to this
integration by the metadata commit; `supersedes_provisional_event = ANOX-EVENT-0054`).
Original S1 commits were not rewritten to pretend another event was used.

## 5. Findings remediation (INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001)

| ID | Disposition | Implementation |
|---|---|---|
| F-1 MEDIUM | **FIXED** | `validate_apk_contents.py`: every member path must be canonical (no `./`, `/`, `//`, `.`/`..` segments, backslash, NUL, control chars); any member that could denote a native library under any casing/spelling (`LIB/`, `.SO`, `.so.1`, `.so` outside `lib/`) must be exactly `lib/<abi>/<name>.so` or fails; exact duplicate entries and case-folded collisions fail. 13 adversarial tests. |
| F-2 MEDIUM | **FIXED** | `validate_s1_build_provenance.py`: `resolve_git_dir()` accepts a `.git` directory or a linked-worktree `gitdir:` pointer (relative/absolute, HEAD + commondir validated) and fails closed on missing/malformed/invalid/non-repository context; the Rust behavior-scope check is never silently skipped (CLI always enforces). Central validator `has_git()` likewise recognises worktrees. 12 tests incl. real linked worktree. |
| F-3 MEDIUM | **FIXED** | `validate_b021_verification_matrix.py`: exact FCP-1 — `RUNTIME_TESTED=PASS` on provenance units requires a structured `provenance` object with **both** `build_artifact_hash_proof` (manifest ref, `reproducible_build_confirmed=true`, per-ABI SHA-256 for exactly `{arm64-v8a, x86_64}`) and `provenance_verified_native_runtime` (per-ABI PASS, ≥1 test, 0 failures, `artifact_sha256` equal to the hash proof = same-run, evidence ref, authority). Token/filename matching removed. Consequence: MSC-UNIT-001/002 `RUNTIME_TESTED` truthfully downgraded to `PENDING` (arm64-only, implementer-run partial evidence retained). 11 tests. |
| F-4 LOW/MED | **FIXED** | `validate_ci_pipeline.py`: parses `needs:` and enforces the required edge set (`native-build ← rust, gradle-wrapper-validation`; `android-debug/-release/instrumented-* ← native-build`, …), transitive descent from `native-build`, exact artifact name `native-artifacts-${{ github.sha }}` into `build/native`, mandatory `native_build.py verify` on every consumer **before** any Gradle step, no `continue-on-error`/`if:` on those steps, no consumer rebuilding natively, producer order check-toolchain → build → rebuild-compare → verify → upload with `if-no-files-found: error`. `ci.yml`: `android-release` gains the missing re-verify step and an explicit `needs: native-build`. 12 mutation tests. |
| F-5 LOW | **FIXED (option A — authoritative)** | `native_build.py`: `rebuild-compare` performs two clean builds and a **three-way** compare against the primary manifest; only on success does it write `build.reproducible_build_confirmed = true` plus a `reproducibility` attestation (`method`, `builds=2`, `build_ids`, `per_abi_sha256`). `build` writes `false`. `verify` and the APK validator fail unless the attestation is exactly `True` and its per-ABI hashes equal the artifact hashes. 10 tests. |
| F-6 LOW | **FIXED** | `secret_scan.py`: binary files scanned in the byte domain (PEM markers, AWS/GitHub/Slack/Supabase tokens) instead of skipped; indented/quoted PEM headers followed by a base64 body detected (`pem_private_key_indented`) while bare marker literals in tool source stay clean; oversize files remain a reported failure. `validate_apk_contents.py`: oversize members fail (not skipped), compression-ratio bomb guard, total-uncompressed and member-count bounds. 13 tests. |
| F-7 LOW | **FIXED (fail closed)** | `native_build.py`: `build`, `rebuild-compare` and `write_manifest` refuse a dirty tree (tracked modifications, staged changes, untracked non-ignored files); the manifest records `source.working_tree` and `verify`/APK validation reject anything but `"clean"`, and `verify` re-checks the live tree. No dirty-encoding form is introduced (no authority approval for one). 11 real-git tests. |
| F-8 INFO | **DOCUMENTED, PINS UNCHANGED** | `docs/security/remediation/S1_ACTION_PIN_PROVENANCE.md`: all 8 external pins remain full SHAs; 7 have verified release lineage; `dtolnay/rust-toolchain@4360b525…` is `PIN_IMMUTABLE` + `PIN_PROVENANCE_UNVERIFIED` (official repo resolves; no tag; branch force-moved). No stronger provenance fabricated; no mutable refs introduced. |
| F-9 LOW | **FIXED** | `validate_b021_verification_matrix.py`: every stage record must be present (omission = fail); a PASS stage requires every earlier stage present and PASS (or `NOT_APPLICABLE` only when not required); `IMPLEMENTED/AUTOMATED_TESTED/INDEPENDENTLY_RETESTED/EVIDENCE_PRESERVED/CLOSED` always required; `recorded_by`/`recorded_at` mandatory for PASS; FCP-7 compares normalised authorities, rejects missing `recorded_by`, whitespace/case variants and implementer-prefixed aliases. 14 tests. |

Additional: the three deficient S1 adversarial tests identified by the retest
(`test_24` tautological, `test_46`/`test_47` non-discriminating) were rewritten to
exercise the real gates with a zero-blocker control; `test_23` now exercises the
attestation writer. Fixtures updated for the stricter manifest schema.

## 6. Shared-validator follow-up (`S1_SHARED_VALIDATOR_FOLLOWUP_REQUIRED = CONFIRMED`) — governance-compliant form

**Constraint discovered during execution.** `tools/audit/validate_security_audit_evidence_preservation.py`
is a `PROTECTED_SHARED_GOVERNANCE_FILE`: the frozen S0 contract (`validate_s0_contract_freeze.py`
F-03) pins its content to exactly the two Human-ratified hashes and states that any other content
"is an unauthorized modification — a new Human ratification is required"; both ratifications record
`grants_s1_permission = false` and `grants_future_sessions = false`. Modifying the file in place would
fail the S0 contract freeze, and the only ways to make it pass (forging a Human decision or re-pinning
the S0 contract) would silently weaken S0 authority. Neither was done. The protected file is
**byte-identical to the ratified content `89c7358f…`**.

The follow-up is therefore delivered as:

1. **The exact minimum S1-era extension, preserved as a tamper-evident ratification proposal**
   (`docs/reports/security/decisions/S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-PROPOSAL-001.md`
   + `docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch`; applies to
   `89c7358f…`; the resulting post-change SHA-256 is pinned in the proposal record and in
   `tools/audit/validate_s1_integration_evidence.py` — not repeated here to avoid a hash cycle).
   It is a proposal, not a decision; only the Human Owner may ratify (precedent:
   `ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001`).
2. **`tools/audit/validate_s1_integration_evidence.py`** — a separate, non-protected validator that
   imports the ratified central module unmodified (refusing to run on any other hash), executes every
   era-agnostic S0 protection **verbatim**, runs the ratified S0 registry checks on the 13-record view,
   and adds only the pinned S1-era sections:
   - accepts **only** `ANOX-EVENT-0055` with pinned `type`/`task`/`start_head`/`merged_head`/`ref`/
     `supersedes_provisional_event`, and only as the direct successor of `0052 → 0053 → 0054`;
   - rejects duplicate ids, skipped ids, any event carrying the isolated S1 task (provisional `0054`
     as canonical), the S1 task under any id ≠ `0055`, and `0055` without `CURRENT_STATE` declaring
     the S1 delivery (S0 one-time exception **not** reusable);
   - topology proof `lifecycle_legality.canonical_integration_delivery`: first-parent chain above
     `29a6643…` exactly [merge, substantive, metadata]; merge parents exactly (`29a6643…`, `e32463ca…`);
     only the two pinned S1 commits integrated; metadata commit allowlisted;
   - scope: enumerated S1 surface allow-list; `crypto/rust/src/**`, `android/src/main/java/**`,
     `backend/`, `supabase/`, `migrations/`, `*.sql`, `docs/authority/**` rejected; protected shared
     validator must be unchanged; no tracked `.so`; CI hotfix invariant enforced;
   - registry `13 → 14` for exactly `SEC-AUDIT-REG-0014` (pinned fields, report + preserved-source
     hashes); arbitrary growth rejected;
   - ratification-proposal integrity (patch applies to ratified content and yields the pinned hash).
3. Paired accept/reject adversarial tests in `tools/audit/test_s1_integration_evidence.py`.
4. The ratified central adversarial suite stays at its S0-pinned **277** tests; its fixtures are
   normalised to the S0 era (S1 event/record stripped in `setUp`) so every S0 protection is exercised
   unchanged on the integrated tree.
5. `tools/audit/validate_s0_evidence_preservation.py`: one explicit, documented change — the S1 record
   `SEC-AUDIT-REG-0014` is not an S0 "prior" record (the 12-prior-record protection is unchanged).

**Consequence stated plainly:** the ratified central validator FAILS on the integrated repository
(era pins) **until the Human Owner ratifies the proposal**; the S1 integration validator PASSES and
carries every S0 protection. This is the designed behaviour of a protected governance file.

## 7. S0 / CI invariants after integration

S0 contract freeze PASS · S0 evidence preservation PASS · S0 correction/retest evidence
preserved (registry `SEC-AUDIT-REG-0013` unchanged) · `dace1467…` ancestor of HEAD ·
CI hotfix present in all four `setup-android` steps · `tools platform-tools` absent.

**Two explicit (non-silent) era-precision corrections to S0-owned validators were required**
for these results to hold in a real clone (both validators skipped their Git checks inside the
linked worktree — the F-2 pattern — and only revealed the era conflation in a scratch clone):

| Validator | Before | After | Why this is not a weakening |
|---|---|---|---|
| `validate_s0_contract_freeze.py` F-02 scope | `git diff <S0 base>` vs **HEAD**: any later delivery touching S1-owned/product paths retro-fails S0 | `git diff <S0 base> <pinned corrected S0 final head 0be57335…>`; the final head is newly pinned and must be a HEAD ancestor descending from the base; protected-shared-file content is still checked at **HEAD** | S0's contract is about S0's own changes; the identical forbidden set is applied to S0's complete pinned range, plus a new lineage pin; later deliveries are governed by their own scope gates (S1: `validate_s1_integration_evidence.py`) |
| `validate_s0_evidence_preservation.py` §ledger | `ANOX-EVENT-0054` must be the **last** ledger event; `latest_material_event_id == 0054` | 0054 exactly once at chain position `0052 → 0053 → 0054`; every later id strictly ascending and legal; **no S0 task may be re-recorded after preservation**; `latest_material_event_id` must equal the last ledger event | preservation is a sealed chain position, not a freeze of all future history; re-opening S0 is now rejected explicitly |

S0 adversarial suites keep their pinned counts (98 / 40); the paired tests for these corrections live
in `tools/audit/test_s1_integration_evidence.py` (`S0EraPrecisionTests`).

## 8. MSC / product state

| Unit | Before (isolated S1) | After (this task) |
|---|---|---|
| MSC-UNIT-001 | IMPLEMENTED, AUTOMATED_TESTED, RUNTIME_TESTED=PASS (arm64 only, implementer) | IMPLEMENTED, AUTOMATED_TESTED PASS; **RUNTIME_TESTED = PENDING** (exact FCP-1: x86_64 absent, arm64 not independent); INDEPENDENTLY_RETESTED PENDING |
| MSC-UNIT-002 | same as 001 | same as 001 |
| MSC-UNIT-003 | IMPLEMENTED, AUTOMATED_TESTED | unchanged; INDEPENDENTLY_RETESTED PENDING |
| MSC-UNIT-038 | IMPLEMENTED, AUTOMATED_TESTED | unchanged; INDEPENDENTLY_RETESTED PENDING |

`GLOBAL_OPEN_MSC = 42` · `MSC_CLOSED = 0` · `SECURITY_REMEDIATION = IN_PROGRESS` ·
`B004 = NOT_STARTED` · `B005 = NOT_STARTED` · `PRODUCT = BLOCKED_PENDING_FINAL_AUDIT`.
FCP-7: `INDEPENDENTLY_RETESTED` stays PENDING — the remediated surfaces require a
targeted independent integration retest by a non-implementing authority.
x86_64 runtime: `PENDING_REAL_CI_OR_INDEPENDENT_RUNTIME_EVIDENCE`.

## 9. Next recommended gate

`TARGETED-INDEPENDENT-INTEGRATION-RETEST-S1-001` on this branch head (fresh
independent session), then human merge of `integration/s1-after-s0-001` to `main`.
