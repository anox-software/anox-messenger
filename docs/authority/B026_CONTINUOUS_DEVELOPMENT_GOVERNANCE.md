# B-026 — Continuous Development Governance and Chat Handoff System

**Status:** FROZEN  
**Date:** 2026-08-20

---

## Purpose

Establish a permanent, repository-based continuity system for anoX Messenger so that development is independent of any individual ChatGPT conversation, Devin session, developer computer, or AI provider.

B-026 is a governance specification. It does not modify B-002…B-025 product or security semantics.

---

## Mandatory post-task governance

Every future Devin implementation task MUST update, before declaring `PASS`:

1. `PROJECT_STATE.md`
2. `FORTSCHRITT.md`
3. `DEVIN_PROMPT_OUTPUT_ARCHIV.md`

Where relevant it MUST ALSO update:

4. Security / validation reports
5. Architecture compatibility reports
6. Migrations / schema documentation
7. Test evidence
8. Current continuity state in `docs/continuity/`

A task that has not updated required governance files must report:

`BLOCKED — GOVERNANCE UPDATE INCOMPLETE`

---

## PROJECT_STATE.md contract

`PROJECT_STATE.md` must always answer:

- current date
- repository, branch, current HEAD
- current milestone and architecture authority version
- what is implemented, partial, missing, verified, and unverified
- active blockers, CI status, physical-device status
- last completed engineering task, next approved gate
- next proposed Devin task
- current known architecture deviations and release blockers

It must not record intended future implementation as already implemented.

---

## FORTSCHRITT.md contract

`FORTSCHRITT.md` is chronological. Every Devin task must append:

- TASK ID, date, starting HEAD, branch, objective
- architecture references
- files changed
- implementation summary
- tests actually run with PASS / FAIL / NOT RUN / UNVERIFIED
- CI, security invariants, blockers
- commits, PR, merge status, final HEAD if merged
- next gate

Historical entries must never be silently rewritten. Corrections must be new entries.

---

## DEVIN PROMPT / OUTPUT ARCHIVE contract

`DEVIN_PROMPT_OUTPUT_ARCHIV.md` must record for every future task:

- TASK ID
- prompt version / title
- short purpose
- architecture authority used
- execution summary
- files changed
- test result
- commit(s)
- PR
- final result
- next recommended step

The complete prompt does not have to be duplicated indefinitely if it is stored as a separate versioned prompt file; in that case record its path and hash.

Never store tokens, passwords, private keys, license plaintext, or production secrets.

---

## Structured Devin final output standard

`docs/continuity/DEVIN_OUTPUT_CONTRACT.md` defines the final-output sections. Every future Devin task must end with:

A. TASK  
B. BASELINE  
C. BRANCH  
D. FILES CHANGED  
E. IMPLEMENTATION  
F. TESTS ACTUALLY RUN  
G. TESTS NOT RUN / UNVERIFIED  
H. SECURITY INVARIANTS  
I. PROJECT_STATE UPDATE  
J. FORTSCHRITT UPDATE  
K. DEVIN ARCHIVE UPDATE  
L. COMMITS  
M. PR  
N. CI  
O. BLOCKERS  
P. ARCHITECTURE IMPACT  
Q. NEXT RECOMMENDED GATE  

And exactly one of:

`RESULT: PASS — READY FOR ARCHITECT REVIEW`  
`RESULT: BLOCKED — ARCHITECT DECISION REQUIRED`

---

## Continuity directory

`docs/continuity/` is the repository handoff and continuity authority. It contains the files listed in `docs/continuity/AUTHORITY_INDEX.md`.

## Authority versioning rule

- `docs/authority/B025/` is the immutable historical snapshot of the B-025 architecture handoff.
- `docs/authority/B_FREEZE_REGISTRY.md` is the current registry of frozen specifications B-001…B-026.
- New B IDs are appended to the current registry; the historical B-025 snapshot is not rewritten.

---

## Handoff workflow

The frozen lifecycle is:

Chat A becomes slow / context too large  
→ finish current Devin task  
→ ensure clean / documented state  
→ update `PROJECT_STATE`, `FORTSCHRITT`, `DEVIN_PROMPT_OUTPUT_ARCHIV`  
→ update `docs/continuity/CURRENT_HANDOFF.md`  
→ generate handoff package  
→ new ChatGPT chat  
→ upload package / provide repository  
→ run read-only bootstrap  
→ bootstrap `PASS`  
→ handoff acceptance review  
→ Chat A becomes archive  
→ development continues only in Chat B

Never switch chats in the middle of an undocumented partially completed implementation task unless an emergency handoff explicitly records that state.

---

## Handoff readiness gate

`docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md` defines the required checks. Only when all are `PASS`:

`HANDOFF READINESS = PASS`

---

## Handoff retention and performance policy

A handoff ZIP is a local artifact. It is **not** committed to Git and is **not** automatically generated after every normal Devin task.

### Normal task rule

For every normal Devin task, update:

1. `PROJECT_STATE.md`
2. `FORTSCHRITT.md`
3. `DEVIN_PROMPT_OUTPUT_ARCHIV.md`

Update other `docs/continuity/` files only when their represented state actually changed. Run the task-specific required validation. Do **not** generate a handoff ZIP unless the task explicitly requests one.

### When to generate a handoff ZIP

A handoff ZIP may be generated only when:

- a ChatGPT chat handoff is actually requested;
- an explicitly defined architecture or release milestone is reached;
- the architect or user explicitly requests one;
- a recovery or emergency handoff is required.

The expensive full handoff/parity/cold-bootstrap process is therefore event-driven, not mandatory after every task.

### ZIP retention and cleanup

- Generated ZIPs stay under `artifacts/handoff/` and are excluded from Git by `.gitignore`.
- After a successor handoff has:
  - validated `PASS`,
  - passed integrity verification, and
  - (for a real chat migration) successfully bootstrapped in the successor chat,
  older intermediate or test handoff ZIPs may be deleted locally.
- Milestone handoffs are preserved only when explicitly required.
- Git history, authority files, `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`, and historical provenance remain the durable development record.

---

## APK content / secret leakage release gate

### Architecture principle

**Repository content is not APK content.** The following are repository/governance-only and must never appear in the distributed Android APK:

- `docs/authority/`
- `docs/continuity/`
- `docs/history/`
- `docs/reports/` unless deliberately converted to runtime-safe product data by a future explicit architecture decision
- `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- `MAIN_PLAN_DE.md`
- generated handoff ZIPs and `ANOX_HANDOFF_*` artifacts
- `GIT_SNAPSHOT.txt`, `CURRENT_HANDOFF.md`, `CURRENT_GIT_STATE.md`, `CURRENT_STATE.json`
- historical RAW material and historical Devin outputs
- audit working files
- `.git/` and Git metadata
- `.env`, `.env.*`, `local.properties`, `*.jks`, `*.keystore`, `*.p12`, `*.pfx`, `*.pem`, `*.key`

These files are not removed from the repository; they are simply forbidden from the APK package.

### Security principle

The anoX security model must not depend on APK secrecy. Assume an attacker can unzip, decompile, inspect resources, native libraries, and the manifest. Therefore the APK must never embed production private keys, signing keys, backend credentials, database passwords, service-role secrets, API tokens, admin credentials, recovery secrets, E2EE private keys, or license-generation secrets.

### Validation rule

APK content validation is a mandatory release/security gate. `tools/security/validate_apk_contents.py` inspects the final APK and fails closed if any forbidden repository/governance artifact or obvious secret marker is found. This is a validation and detection tool, not a claim that reverse engineering is prevented.

### Release gate status values

- `PASS` — validator found no forbidden items and no obvious secret markers in the exact APK artifact.
- `FAIL` — forbidden items or secret markers found; release blocked.
- `NOT RUN` — validator was not executed.
- `UNVERIFIED` — no APK artifact was available for inspection.

A debug APK `PASS` is useful CI regression evidence but is not automatically the final production-release artifact attestation. At final release, B-023 must validate the exact signed/shipping APK again.

### Authority references

This rule complements the frozen B-017 (CI/CD + Supply Chain), B-018 (Release Signing + Secure Updates), and B-023 (V1 Release Definition of Done) specifications without modifying their security semantics.

---

## Handoff package generator

`tools/continuity/generate_handoff.py` (Python 3 standard library only, no network) builds:

`artifacts/handoff/ANOX_HANDOFF_<YYYY-MM-DD>_<short-head>.zip`

The package contains at minimum:

- `docs/authority` current frozen architecture
- `docs/continuity`
- `PROJECT_STATE.md`
- `FORTSCHRITT.md`
- `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- `MAIN_PLAN_DE.md`
- relevant current reports
- selected historical indexes / provenance
- Git metadata snapshot
- file manifest
- SHA-256 manifest

It must NOT include:

- `.git` object database
- `build/`, `.gradle/`, `target/`
- `local.properties`
- keystores, `.jks`, `.p12`, `.keystore`
- `.env` or environment files
- production credentials
- Android build caches
- large generated build artifacts

---

## Git snapshot in package

The generator records a text snapshot with:

```
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
git tag --list
recent relevant log
```

If the working tree is dirty, the generator must either `FAIL` or clearly produce `EMERGENCY / DIRTY HANDOFF` with the exact changed files.

---

## Validation script

`tools/continuity/validate_continuity.py` (Python standard library only) validates presence and basic consistency of:

- `PROJECT_STATE.md`
- `FORTSCHRITT.md`
- `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- authority files
- continuity files

and checks Git cleanliness. It returns non-zero on handoff readiness failure.

---

## Historical handoffs

`docs/continuity/HISTORICAL_HANDOFFS/` contains lightweight metadata/index files referencing previous handoff generations. Generated ZIPs normally remain local artifacts; do not commit large ZIPs to Git unless explicitly required by a later architecture decision.

---

## Upload requirements

Preferred future handoff workflow:

- **UPLOAD A:** latest generated `ANOX_HANDOFF_*.zip`
- **UPLOAD B:** latest repository snapshot only if direct repository access is unavailable

If the new AI can directly inspect the current repository, the handoff package plus repository access is sufficient.

---

## Bootstrap prompt contract

`docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md` must instruct a new ChatGPT conversation to:

- inventory supplied anoX files
- read current authority
- read `PROJECT_STATE`, `FORTSCHRITT`, `CURRENT_HANDOFF`
- inspect the repository and Git state
- distinguish target truth from implementation truth
- treat historical RAW as history only
- never invent Raw1.0
- never modify code in the first bootstrap pass
- return a read-only bootstrap audit
- state `PASS` or `BLOCKED`

It must not contain a hard-coded Git HEAD. Instead, it must direct the AI to read `docs/continuity/CURRENT_GIT_STATE.md` and actual repository state.

---

## No product source changes

B-026 implementations must not modify:

- `crypto/rust` source
- JNI layer
- `CryptoNative.kt` / `CryptoBridge.kt`
- Android manifest security architecture
- Gradle / Kotlin / NDK versions
- native libraries
- application features
- backend code

---

## Canonical merge lifecycle rule

A reviewed and approved delivery payload is NOT a new merge payload.

### Authority

`tools/continuity/validate_continuity.py` is the canonical enforcement of this rule. It must distinguish:

1. **Reviewed delivery tail** — changes between the described checkpoint and the reviewed delivery branch head.
2. **Merge resolution** — changes introduced between the reviewed delivery head and the final canonical merge result.
3. **Post-merge canonical tail** — any commits after the canonical integration merge.

A normal clean merge into `main` has an empty merge-resolution range. The merge result must equal the reviewed delivery result, or differ only in explicitly allowlisted metadata.

### Failure semantics

- Any Product, CI, Authority, Tool/Validator, Rust/Crypto, B0xx spec, or security report change introduced only through merge resolution fails closed.
- Deletion of substantive content during merge resolution fails closed.
- Unknown or ambiguous merge topologies fail closed.
- Squash, rebase, octopus, and rewritten delivery lineage are not supported by V1.

### Branch separation

The continuity state must declare both `canonical_branch` and `delivery_branch`. The runtime branch is derived from Git. The effective next gate is determined by verified lifecycle state, not by a manually edited `current_gate` prediction.

- Runtime `delivery_branch` → effective gate is `pre_merge_gate`.
- Runtime `canonical_branch` with a verified canonical integration merge → effective gate is `post_merge_gate`.

This rule is frozen as B-026 lifecycle invariant.

---

## Canonical base-drift policy

### V1 rule

For Canonical Merge Lifecycle V1, the canonical integration base must not have advanced with **substantive** work after the reviewed delivery branch was created.

- A `canonical_parent` that is not an ancestor of the `delivery_parent` indicates the canonical branch has diverged since the delivery lineage was established.
- The validator compares the merge base between the canonical parent and the delivery parent against the canonical parent.
- If the drift contains only metadata-only changes (per the fail-closed `METADATA_ONLY_ALLOWLIST`), the merge may proceed and is recorded as `metadata-only canonical base drift accepted`.
- If the drift contains Product, CI, Authority, Tool/Validator, or unknown path changes, the merge is:

`MERGE BLOCKED — SUBSTANTIVE CANONICAL BASE DRIFT — RESYNCHRONIZATION REQUIRED`

### Resynchronization workflow

When substantive canonical drift is detected:

1. STOP the final merge.
2. Record the delivery branch as stale against the current canonical base.
3. Create a controlled resynchronization branch from the latest canonical `main`.
4. Merge the reviewed delivery payload into the resynchronization branch (do not rebase/squash and silently reuse the old review).
5. Establish a new substantive checkpoint representing the reconciled state.
6. Update `described_head` to that already-existing checkpoint through the finite metadata-sync commit model.
7. Rerun the full relevant test suite.
8. Obtain a focused independent Delta Review because the reviewed code ancestry changed.
9. Only after the Delta Review passes may the controlled human PR/merge resume.

### Review-approval invalidation

`OLD REVIEW APPROVAL != APPROVAL OF RESYNCHRONIZED DELIVERY`

Any substantive synchronization changes the reviewed object. The old review or approval cannot be reused for the resynchronized delivery.

### Authorized canonical base

Where the continuity state records `latest_merge_to_baseline`, that value represents the canonical base the reviewed delivery assumed. The canonical parent in the final `--no-ff` merge must be that base or a metadata-only descendant of it. Substantial divergence from that base triggers the resynchronization workflow.

### Multiple canonical merges

If the lifecycle validator identifies more than one qualifying two-parent canonical integration merge for the same `described_head`, the topology is **ambiguous** and the result is:

`FAIL — AMBIGUOUS/MULTIPLE CANONICAL INTEGRATION MERGES`

Only a single clean `--no-ff` integration merge is supported per lifecycle task. Later merges must be represented by a new `described_head` in a new lifecycle task.

---

## Archive trust model

### Internal archive integrity

A generated handoff ZIP contains an internal SHA-256 manifest that protects against accidental or partial tampering after generation. The archive validator cross-checks lifecycle fields (canonical branch, delivery branch, described head, handoff branch, handoff head, working tree, current/effective gate) across `CURRENT_STATE.json`, `CURRENT_HANDOFF.md`, `CURRENT_GIT_STATE.md`, and `GIT_SNAPSHOT.txt`.

A partial rewrite of one surface without a matching rewrite of all cross-checked surfaces FAILS archive validation.

### Archive authenticity

A self-contained unsigned ZIP with an internal manifest is **NOT cryptographically authenticated**. An attacker who controls the archive contents and the manifest can rewrite both coherently and recompute the manifest.

Authenticity requires a trust anchor outside the archive, such as:

- a trusted externally stored SHA-256 digest,
- a detached digital signature,
- or a human-controlled release/signing mechanism.

`tools/continuity/generate_handoff.py` emits the final ZIP SHA-256 as `HANDOFF_SHA256: <digest>` so that an external trust anchor can record it. If the attacker also controls the external channel storing the digest, authenticity is still not established.

Cold recovery from a handoff ZIP may reconstruct internal project state with `ARCHIVE INTERNAL VALIDATION = PASS`, but it MUST report `ARCHIVE AUTHENTICITY = UNVERIFIED — NO EXTERNAL TRUST ANCHOR PROVIDED` unless a trusted external anchor is supplied.

This is a trust-level distinction, not a reason to make ordinary Handoff unusable.
