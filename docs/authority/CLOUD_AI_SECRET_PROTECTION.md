# Cloud-AI Secret / Private-Key Protection

**Authority:** Binding development / security authority.
**Status:** CURRENT
**Date:** 2026-08-23

---

## Core invariant

**NO PRODUCTION USER PRIVATE KEY OR CRYPTOGRAPHIC ROOT SECRET MAY EVER BE EXPOSED TO A CLOUD-AI DEVELOPMENT ENVIRONMENT.**

Security **MUST NOT** depend on source-code secrecy.

## What cloud AI may see

- source code
- architecture
- DB schemas
- protocol specifications
- crypto integration code
- public cryptographic data
- synthetic test keys (must be obviously test-only)

## What cloud AI MUST NOT receive

Actual versions of:

- user E2EE private keys
- Identity Private Keys
- Session Keys
- Ratchet States
- Master Encryption Keys
- Recovery Seeds
- production Device private keys
- production signing private keys
- private CA / TLS root keys
- wallet seeds
- production admin master credentials
- production DB master credentials
- Supabase service-role secrets
- production HMAC / root lookup secrets
- production cloud / API master credentials
- equivalent production / root / user private secrets

## Where such secrets MUST NOT appear

- Git
- source code
- configuration committed to Git
- prompts
- screenshots
- logs
- test fixtures
- CI output
- Devin Secrets or equivalent
- cloud build environments
- generated handoff ZIPs

## Development exceptions

Development may use only:

- synthetic test secrets
- isolated DEV credentials
- isolated STAGING credentials
- least-privilege credentials
- revocable credentials
- short-lived credentials where practical

## Procedure

If a task requires an actual production / root / user private secret:

1. **STOP.**
2. Use instead:
   - synthetic test secret
   - dummy secret
   - limited DEV credential
   - architecture that avoids disclosure
3. If no safe alternative exists:
   - **SECURITY BLOCKER.**
   - Escalate to the architect.

No custom cryptographic primitive may be invented as a workaround.

## Cloud-AI secret status in output

Every security-relevant task should end with one of:

```
NO CONFIRMED CLOUD-AI SECRET EXPOSURE
```

or, if a secret is discovered:

```
RESULT: BLOCKED — CLOUD-AI SECRET EXPOSURE
```

No actual secret value may be printed.

---

## Cold-chat reconstruction quick reference

| Question | Answer |
|----------|--------|
| Are production user private keys allowed in a cloud-AI development environment? | **NO** |
