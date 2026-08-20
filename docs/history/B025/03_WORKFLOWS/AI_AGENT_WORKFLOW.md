# AI-Agnostic Development Workflow

For Devin, Claude Code, Windsurf or another coding agent:

1. Inspect actual repo first.
2. State exact authority specs/security invariants for the task.
3. Define scope exclusions and STOP conditions.
4. Create branch/PR-sized change, not architecture rewrite.
5. Implement using real library APIs; never invent crypto APIs.
6. Add/update tests that prove the intended behavior and negative/fail-closed cases.
7. Run tests; mark anything not executed UNVERIFIED.
8. Return exact files changed, commands/tests/results, security implications, blockers, commit/PR.
9. ChatGPT/human reviews against frozen architecture before acceptance.
10. Update PROJECT_STATE/FORTSCHRITT/history only after review.

No agent may silently change frozen security architecture, claim production security from unit tests, add recovery/multi-device, or make historical documents current again.
