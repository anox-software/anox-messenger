# STEP 4 — Git Closure + Resume Development Workflow

## Important correction

The old plan said Git/TOOLCHAIN were still pending. The uploaded repository now proves a newer state: `main` is `c076528e26e5e3ed05b4d0aeed794894f1f78b5e`; PR #1/TOOLCHAIN-001 is merged; the repo records post-merge main CI run `32344459447` as green. Therefore do **not** reopen or redo TOOLCHAIN-001 merely because an older FORTSCHRITT says it is pending.

## A. Verify current Git evidence

1. Fresh clone or actual working project, not a ZIP-only pseudo-worktree when possible.
2. `git status --short --branch`.
3. `git rev-parse HEAD` and `git rev-parse origin/main`.
4. `git log --oneline --decorate -20`.
5. Verify PR #1 merge commits and current toolchain files.
6. Verify latest CI associated with current main. If newer than the archived run, use newer evidence.
7. Re-run tests locally where environment allows. Mark unavailable connected/GrapheneOS tests UNVERIFIED, never PASS-by-assumption.

Expected archived baseline: `main == origin/main == c076528e26e5e3ed05b4d0aeed794894f1f78b5e`.

## B. Apply B-025 compatibility synchronization

Create a dedicated branch, e.g. `architecture/b025-main-sync`. First commit should be documentation/authority synchronization only. If STEP 3 found a real existing-code conflict, address it in a separate commit or PR with explicit B-spec references and regression tests.

Do not mix Device Authentication implementation into the B-025 synchronization PR.

## C. PR and CI

Open PR to `main`. Require the current available checks: Rust tests, Android debug build, Android release compile smoke, plus any newly added doc/schema/static/security checks. Review diff for secrets and security-invariant changes. If a security invariant would change, stop: the PR requires ADR/spec change, not ordinary implementation review.

## D. Merge and close Git baseline

After green checks/review, merge. Record merge commit and post-merge CI. Confirm clean `main`, `origin/main`, no unexpected untracked secrets/build artifacts. Update `PROJECT_STATE.md`, `FORTSCHRITT.md`, prompt/output archive and B-025 compatibility report.

Recommended optional tag after successful synchronization: `v1-b025-architecture-baseline`. Tag only the verified post-merge commit; do not move the existing `v1-foundation-baseline` tag.

Current plan limitations (branch protection/secret scanning unavailable on free private plan) remain tracked as B-017/B-023 Production gates; they do not require repeating the already completed Git baseline today.

## E. Resume product engineering

Only now start the next product gate:

`PROMPT-007 — Device Authentication Foundation`

Target must implement B-002, not the old repository docs:

- Android Keystore P-256 / ES256 private key.
- Hardware-backed production policy (StrongBox preferred, TEE fallback; software-only rejection in production path).
- RFC9449-style DPoP proof creation/verification contract.
- Opaque 256-bit access token, 15m TTL, hash-only server storage, no refresh token.
- Fresh nonce, jti replay protection, iat ±120s, token/key/device binding.
- No E2EE changes, no recovery, no account-device replacement.

Before writing PROMPT-007 code, inspect the actual latest repo after B-025 merge and define exact files/modules and STOP conditions.

## F. Continue dependency order

After Device Auth is implemented and accepted, proceed in this order unless a new ADR changes dependency logic:

Device Auth → Account/License Registration → Backend Foundation → DB/RLS → vodozemac public session-init distribution → Messaging/Sync → SQLCipher local messenger DB/outbox → Contacts → SAS Verification → Push/Offline → Attachments → Lifecycle → Privacy/Retention → Abuse → Production infra/supply-chain/signing/ops → full security matrix → independent audit → Release DoD.

After every agent task update FORTSCHRITT with objective, B-specs, files, tests actually run, PASS/FAIL/UNVERIFIED, blockers, review result, commit/PR and exact next task.
