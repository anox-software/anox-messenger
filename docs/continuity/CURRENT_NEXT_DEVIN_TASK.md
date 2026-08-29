# CURRENT NEXT DEVIN TASK

**Status:** AWAITING REVIEW RETEST
**Task ID:** `B-017-Lite-R1 — Review finding remediation`
**Date:** 2026-08-29

---

## Purpose

B-017-Lite has been implemented on `security/b017-lite-supply-chain-foundation`. The next gate is
an independent security review of the CI and supply-chain hardening before it can be merged.

## Preconditions satisfied

- `PROMPT-009` / `PROMPT-010` governance is merged to `main`.
- `main` HEAD is `043e87480b3c00bed2cbce6b24bf24a7dfc5d7ff`.
- Repository is `anox-software/anox-messenger`.
- `GITHUB_REMOTE_ACTIVITY_SAFETY.md` is binding.
- Remote-write authority remains `HUMAN-CONTROLLED REMOTE WRITE MODE`.
- `.github/workflows/ci.yml` is pinned and hardened.
- `gradle/wrapper/gradle-wrapper.properties` has `distributionSha256Sum`.
- `tools/security/b017_lite_policy_validator.py` and its tests are implemented.
- `docs/reports/B017_LITE_CI_SUPPLY_CHAIN_SECURITY.md` is created.

## Scope of the next task

- Independently review `.github/workflows/ci.yml` for least privilege, immutable action SHAs,
  dangerous triggers, and concurrency.
- Independently review `gradle/wrapper/gradle-wrapper.properties` for checksum provenance.
- Independently review `tools/security/b017_lite_policy_validator.py` for correctness and
  completeness.
- Independently review `docs/reports/B017_LITE_CI_SUPPLY_CHAIN_SECURITY.md` for threat, controls,
  residual risks, and deferred work.
- Run `python3 tools/security/b017_lite_policy_validator.py` and confirm PASS.
- Run `python3 -m unittest tools/security/test_b017_lite_policy_validator.py` and confirm PASS.
- Run `python3 tools/continuity/test_handoff_and_validator.py` and confirm 24 tests PASS.
- Run `python3 tools/continuity/validate_continuity.py --mode live` and confirm PASS.
- Run `git diff --check` and confirm PASS.
- If all checks pass, declare `B-017-Lite` ready for merge.

## Out of scope

- GitHub account/repository migration (already complete).
- Credential or remote URL configuration.
- Pushing, PR creation, or remote automation.
- B-027 Workforce implementation.
- B-004 backend implementation.
- B-005 database/RLS implementation.
- Any Messenger product code change.

## Next authorized sequence after this review

1. If review PASS, preserve the clean local branch.
2. Human-controlled remote actions: create PR, merge to `main`.
3. Synchronize `main` continuity surfaces and generate a fresh canonical handoff.
4. Authorize `B-027` or remaining product engineering according to architecture authority.

## Remote safety

No autonomous push, merge, PR creation, credential cycling, or rapid GitHub API polling.
All remote mutations remain human-controlled unless explicit governance changes this mode.
