# Git / GitHub Development Workflow

**Status:** CURRENT  
**Scope:** ANOX V1 repository governance

---

## 1. Main branch is integration state

The `main` branch represents the current accepted architecture and passing baseline. Merges into `main` require a pull request and passing relevant checks.

## 2. One branch per substantive task

Each Devin/Claude prompt or substantial engineering task gets its own branch.

Examples:

- `devin/device-auth`
- `devin/account-license`
- `devin/backend-foundation`
- `devin/message-transport`

A branch is created from the latest `main` and merged through a PR.

## 3. Run tests before merge

Before opening a PR and before merge:

```bash
cd crypto/rust && cargo test
./gradlew :android:connectedDebugAndroidTest
./gradlew :android:assembleRelease
```

Connected device tests may remain optional until CI provides a safe emulator pipeline.

## 4. Architecture / security changes require ADR review

Changes that modify security invariants, crypto boundaries, key lifecycle, or protocol contracts require an architecture decision record and explicit review.

## 5. Failed tasks are not merged just because code compiles

A feature branch is only merged when it satisfies its acceptance criteria, including passing tests and documentation updates.

## 6. No force-push to `main`

Force-pushing, history rewriting, or destructive operations on `main` are not allowed.

## 7. Each accepted prompt maps to a commit / PR

The prompt ID and a short summary should be included in the commit/PR description to maintain traceability.
