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
