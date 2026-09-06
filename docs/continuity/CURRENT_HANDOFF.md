# CURRENT HANDOFF — anoX Messenger V1

Handoff version: LEGACY-FIX-01 — FOUNDATION STATE / REGISTRATION / CRYPTO SAFETY REMEDIATION
Date: 2026-09-06
Delivery branch: `remediation/legacy-fix-01-foundation-safety`
Described HEAD: `342d55386f1bd7ea1531fc70e0e0f14fca0f279f`
Main baseline HEAD: `785e9a574fbbe072c454d8515a9a05022c282c46`
Working tree: CLEAN
Effective gate: LEGACY-FIX-01 — FOUNDATION STATE / REGISTRATION / CRYPTO SAFETY REMEDIATION
Pre-merge gate: LEGACY-FIX-01 — FOUNDATION STATE / REGISTRATION / CRYPTO SAFETY REMEDIATION
Post-merge gate: LEGACY-RETEST-01 — TARGETED DELTA RETEST OF FOUNDATION SAFETY REMEDIATION

---

## Project

anoX Messenger V1 — closed-source native Android/GrapheneOS messenger with vodozemac/Olm E2EE.

## Architecture authority

Authority precedence is canonical in `docs/authority/AUTHORITY_INDEX.md`.
New sessions must read that file first.

## Current repository state

- Canonical repository: `https://github.com/anox-software/anox-messenger`
- Canonical SSH remote: `git@github.com:anox-software/anox-messenger.git`
- Legacy provenance remote: `https://github.com/anox-admin/ax-messenger.git` (historical only)
- Canonical branch: `main`
- Delivery branch: `remediation/legacy-fix-01-foundation-safety`
- Current work branch: `remediation/legacy-fix-01-foundation-safety`
- Current HEAD: `342d55386f1bd7ea1531fc70e0e0f14fca0f279f`
- Main baseline HEAD: `785e9a574fbbe072c454d8515a9a05022c282c46`
- Working tree: CLEAN
- Latest material event: `ANOX-EVENT-0036`

## Latest completed work

- `LEGACY-FIX-01` PASS: 8 Class-A findings moved to Ready For Retest.
- Device Auth production eligibility enforced; identity revalidated before commit; CommitArmed/binding divergence fail-closed.
- K_STATE read/create split and atomic write implemented.
- API 26–32-safe Keystore exception classification.
- JNI buffer error domain and Crypto concurrency protection.
- OTK durability: identity persisted before public OTK material returned.
- JVM unit tests 177/0; Rust tests 17/0; Android lint 0 errors; instrumentation NOT_RUN.
- B027 integrity and continuity live validation PASS.

## Current open work

- `LEGACY-RETEST-01 — TARGETED DELTA RETEST OF FOUNDATION SAFETY REMEDIATION` — pending human authorization.

## Trust-boundary / milestone flags

- `ANOX-MAINARCH-003`, `007`, `024` remain `PENDING` milestone Security Architecture review.

## Product status

- `BLOCKED_PENDING_FINAL_AUDIT`.
- `B-004` backend: NOT_STARTED.
- `B-005` DB/RLS: NOT_STARTED.
- `ANOX-MAINARCH-018` physical verification remains `PHYSICAL_VERIFICATION_REQUIRED`.

## Next task

`LEGACY-RETEST-01` — targeted retest of foundation safety remediation; start only with explicit human authorization.
