# anoX V1 Development Security Workflow

**Authority:** Additive development-governance authority under B-026.
**Status:** CURRENT
**Date:** 2026-08-23

---

## Scope

This document governs the *development process* and *AI-assisted workflow* for anoX Messenger V1.

It does **NOT** supersede B-025 frozen product and security semantics. If any workflow rule in this document conflicts with a B-025 product/security requirement, B-025 wins and the conflict must be escalated to the architect.

## Authority precedence

The canonical authority precedence is `docs/authority/AUTHORITY_INDEX.md`. This document is an
additive current authority under that index. In case of any apparent conflict, `AUTHORITY_INDEX.md`
is the winner.

---

## S0–S4 Security Classification

Every change should identify a security class. The class determines workflow depth.

### S0 — Low security relevance

Examples:
- UI / copy
- visual assets
- ordinary non-security documentation

Default workflow:
- implementation
- tests / CI
- PR
- merge after normal gates

### S1 — Normal business logic

Examples:
- ordinary domain/business logic
- features without meaningful trust-boundary or cryptographic impact

Default workflow:
- implementation
- tests / CI
- normal review
- PR
- merge

### S2 — Security critical

Examples:
- authentication, authorization
- Device Auth
- account/device binding
- licensing
- RLS
- E2EE
- cryptographic state, keys
- SQLCipher, secure local storage
- replay prevention, nonce handling
- sessions, lifecycle
- signing / updates
- sensitive persistence

Current architect decision:

A separate paid Frontier/Opus-class audit is **NOT** mandatory for every individual S2 implementation PR during normal V1 development.

Normal S2 flow:
- implementation
- strong automated tests
- adversarial / negative tests
- CI / security gates
- PR
- repair all known merge-blocking defects
- merge after required gates pass

Important:
- Security-sensitive AI-generated code is **NOT** automatically considered fully security-audited merely because it builds, tests pass, CI is green, or it was merged.
- Known **HIGH** or **CRITICAL** security defects **MUST NOT** be knowingly deferred until the final V1 audit.
- A known HIGH/CRITICAL defect remains an immediate merge blocker.

### S3 — Integration security checkpoint

Triggered after approximately 3–5 tightly coupled security subsystems are implemented.

Focus on:
- trust-boundary interaction
- crash consistency
- state synchronization
- concurrency
- replay
- authorization
- lifecycle transitions
- fail-open / fail-closed behavior
- end-to-end DEV behavior
- fault injection

A paid Frontier full-repository audit is **NOT** mandatory at every S3 checkpoint.

First expected S3 slice:
- B-002 Device Authentication
- B-003 Account/License
- B-004 Backend
- B-005 Database / RLS

### S4 — Release security

After **functional V1** is complete:

1. Freeze an auditable V1 baseline.
2. Perform multiple **READ-ONLY** AI security-audit passes.
3. Use Claude Code or the strongest suitable model available at that future time.
4. Record findings individually.
5. Remediate findings through small traceable branches / PRs.
6. Add regression tests.
7. Run full B-021 security gates.
8. Perform physical GrapheneOS testing.
9. Verify TEE / StrongBox behavior on supported hardware.
10. Perform independent external human security / cryptography audit.
11. Remediate findings.
12. Retest.
13. B-023 Production GO / NO-GO.

AI does **NOT** replace the external human audit.

---

## Future AI security audit strategy

After functional V1, the preferred strategy is **READ-ONLY** audits first.

Separate passes may include:
- Architecture / trust boundaries
- E2EE / vodozemac
- Authentication
- Device Authentication
- Account / License
- Backend
- PostgreSQL / Supabase / RLS
- Android Keystore
- Local storage
- Network security
- IPC / permissions
- Logging
- Crash handling
- Concurrency / race conditions
- Replay
- Metadata / privacy
- Supply chain
- Account lifecycle
- Signing / updates
- OWASP MASVS / MASWE / MASTG

Remediation strategy for a finding:

```
security finding
→ tracked issue
→ small fix branch
→ regression test
→ PR
→ verification
→ merge
```

Do **NOT** encode:

```
"rewrite the complete application for maximum security"
```

as an accepted remediation strategy.

---

## GitHub as security ledger

From this governance migration onward, `main` is treated as protected history.

Normal repository flow:

```
branch
→ implementation
→ tests
→ CI
→ PR
→ merge
```

Rules:
- No normal feature or governance direct push to `main`.
- No force push to `main`.
- Security changes must remain traceable.
- Post-merge continuity updates must also use a reviewable branch / PR flow.

Historical direct pushes are recorded as historical behavior, not the future rule.

Do **NOT** rewrite Git history.

If repository hosting does not currently technically enforce all branch protections:

```
MANUAL GOVERNANCE ENFORCEMENT REQUIRED
```

Do not falsely claim server-side GitHub protection exists.

---

## GitHub remote activity safety

All AI-assisted and human-assisted Git/GitHub remote activity is governed by
`docs/authority/GITHUB_REMOTE_ACTIVITY_SAFETY.md`.

Key hard invariant:

```text
NO RAPID REPETITIVE REMOTE AUTOMATION
```

Remote-write authority is explicit and never assumed. After the controlled migration to the new
GitHub environment, AI initially operates in `HUMAN-CONTROLLED REMOTE WRITE MODE`. AI may not
autonomously push, create remote PRs, poll GitHub in tight loops, or cycle credentials. Account
migration and credential reconfiguration are explicit human-controlled workflows.

This is governance only; account migration is a separate controlled workflow.

---

## Prompt / model-selection governance

The recommended Devin/AI model is communicated **OUTSIDE** the actual implementation prompt.

The project prompt itself should normally **NOT** contain:
- `RECOMMENDED MODEL`
- `Recommended Devin model`
- `use Opus`
- `use SWE`
- `use Frontier`
- model pricing / quota instructions

unless the architect explicitly requests model information inside the prompt.

Reason:
- prevents stale model names from becoming project authority
- reduces unnecessary prompt context
- model availability changes over time

Do not encode a specific current AI model as permanent authority.

---

## Security baseline tag rule

After functional V1 and before large security audits, create an immutable auditable release / security baseline tag.

Example naming:

```
v1.0.0-security-baseline
```

Do **NOT** create that tag now. It is a future release governance action.

---

## B-017-Lite timing

The next hardening milestone **after** this governance task is merged and **before** B-004 / B-005 implementation:

```
B-017-Lite
```

Expected scope:
- Android lint / static analysis
- repository secret scanning
- diff-aware secret scanning
- history-aware secret scanning where practical
- `cargo audit`
- dependency vulnerability scanning
- OSV or equivalent advisory checks
- dependency locking / verification improvements
- GitHub Actions immutable SHA pinning where practical
- CI hardening
- Android instrumentation CI where technically reliable
- supply-chain evidence foundation

Full SBOM and complete B-017 release evidence can remain part of later full B-017 completion.

Do **NOT** implement B-017-Lite in this task.

---

## Cold-chat reconstruction quick reference

These one-line answers are provided so a brand-new session can determine the current governance without previous chat memory.

| Question | Answer |
|----------|--------|
| What is S0–S4? | S0 low relevance, S1 normal business logic, S2 security critical, S3 integration checkpoint, S4 release security. Defined above. |
| Are per-PR Frontier/Opus audits mandatory during normal V1 development? | **NO** |
| What happens to known HIGH/CRITICAL security findings? | **THEY REMAIN IMMEDIATE MERGE BLOCKERS** |
| When does B-017-Lite occur? | **AFTER GOVERNANCE/HANDOFF HARDENING, BEFORE B-004/B-005** |
| When does the full READ-ONLY AI audit occur? | **AFTER FUNCTIONAL V1** |
| Is an external human audit still required? | **YES** |
| Is `main` PR-only under the new governance? | **YES** |
| Should model recommendations be embedded inside Devin prompts? | **NO** |
|| Is AI remote-write authority assumed? | **NO** — `REMOTE WRITE AUTHORITY IS EXPLICIT, NEVER ASSUMED`; see `GITHUB_REMOTE_ACTIVITY_SAFETY.md` |
