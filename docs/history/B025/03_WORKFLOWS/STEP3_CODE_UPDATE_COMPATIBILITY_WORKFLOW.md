# STEP 3 — Code Update Compatibility Workflow

## Recommendation first

**Yes, an update pass is necessary before new feature work — but primarily as a controlled compatibility/documentation synchronization, not as a blanket rewrite of working crypto code.** The repository predates B-002…B-024 and contains stale current docs (for example old Ed25519 Device Auth and OPEN items now frozen). Current implemented code is limited mainly to crypto/JNI/local protected state; static inspection did not reveal a reason to replace that foundation wholesale. The correct goal is to prove which parts remain compliant and change only real conflicts.

## Phase 0 — Freeze the workspace

Create no code yet. Record branch, HEAD, remote, `git status`, diff, toolchain files, Cargo/Gradle lock state and latest CI. If working tree is dirty, classify each difference before continuing. ZIP permission-bit artifacts do not count as functional code changes.

## Phase 1 — Load authority

Read Security Invariants, B Freeze Registry, Ultimate MAIN and B-002…B-014 first because they can affect existing foundation behavior. Historical Raw docs are evidence only.

## Phase 2 — Inventory existing implementation

Map every existing source file to responsibility: Android UI/manifest, Gradle/toolchain, Kotlin crypto bridge, JNI exports, Rust identity/session/serialization/errors/tests, local state wrapper, native `.so`, CI, docs. Record which B-spec each current file touches.

## Phase 3 — Build a traceability matrix

For every frozen requirement that can affect existing code, assign one status:

- `COMPLIANT`: code matches current rule.
- `DOC_ONLY`: implementation is not wrong, but repository docs/comments/config guidance are stale.
- `UPDATE_REQUIRED`: existing behavior directly conflicts with current frozen rule.
- `MISSING_FEATURE`: feature does not exist yet; do not modify unrelated foundation just to “prepare” it.
- `UNVERIFIED`: behavior appears compatible but needs actual build/runtime/negative/crash test.

At minimum check: no recovery paths; one-device assumptions; E2EE private state local; vodozemac API use; no custom crypto; key separation; state envelope/version/AAD; atomic persistence; fail-closed missing/corrupt state; JNI wrong/stale handles; logging; Android backup config; old Ed25519 Device Auth references; refresh-token references; QR/KEY_CHANGED semantics in docs; push/attachment/open-decision docs; CI dependency/action pinning.

## Phase 4 — Compare current code to post-B024 amendments

Specific compatibility questions:

1. Does any current code implement Device Auth? If no, there is no Ed25519 code migration; update only stale docs and later implement P-256 cleanly.
2. Does any current code permit same-device E2EE identity replacement/reverification? If yes, block it; if absent, no change.
3. Does current crypto/JNI create custom SAS/QR logic? If absent, do not add it until B-010 implementation.
4. Does current state layer silently regenerate identity on missing/corrupt state? It must not.
5. Does current local state depend on recovery/cloud backup? It must not.
6. Will B-009 SQLCipher require moving current identity/session envelope files? Treat as a later explicit migration; do not delete current working state before migration exists/tests pass.
7. Does any existing log/error expose plaintext/private state? Fix immediately if found.
8. Do current Cargo dependencies/actions fetch floating/uncontrolled crypto/tooling? Record for B-017 hardening.

## Phase 5 — Decide update scope

Create a review report before editing. Prefer three separate categories/PRs:

A. `B025-DOCSYNC`: update stale current docs, START/README/OPEN items/state to the new authority. No functional code changes.

B. `B025-COMPAT`: only if actual implemented foundation conflicts with B-025. Security-critical code changes must be small and test-backed.

C. Future feature PRs: Device Auth, account/license, backend, etc. Do not mix them into the compatibility PR.

If no code conflict exists, explicitly record `CODE_COMPATIBILITY = PASS / NO FOUNDATION CHANGE REQUIRED`; do not manufacture changes.

## Phase 6 — Test any changed foundation

Run Rust test suite, Android build, connected instrumentation, release compile, and targeted new regression tests for every modified security behavior. On real/physical GrapheneOS when the change affects Keystore/runtime assumptions. Never call unavailable tests PASS.

## Phase 7 — Review gate

Before merge, verify diff against Security Invariants and relevant B-specs. Confirm no recovery/multi-device/custom crypto/identity migration path was introduced, no toolchain drift occurred unintentionally, and docs no longer point agents to superseded architecture.

## Output of STEP 3

Produce `B025_CODE_COMPATIBILITY_REPORT.md` with exact commit, files inspected, matrix, tests run, findings, required changes, unchanged components and next approved Git action.
