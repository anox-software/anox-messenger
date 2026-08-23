# PROMPT-009 — Development Security Governance / Handoff Hardening

**Date:** 2026-08-23  
**Branch:** `governance/development-security-handoff-v1`  
**Starting baseline:** `main` @ `881c85ec726d8a32eb84b00955b6b9db7912fe1e`  
**Status:** Governance / handoff security hardening; no product feature changes.

---

## Purpose

B-002 and B-003 client foundations are merged. This task permanently encodes the architect's updated development security rules into the repository and every future anoX handoff ZIP. No product subsystem (B-004, B-005, B-017-Lite, etc.) is implemented here.

---

## Product architecture status

**UNCHANGED.** B-025 frozen product / security semantics were not modified. No B-002–B-025 semantics were redesigned.

---

## Files changed

New authority:

- `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`
- `docs/authority/CLOUD_AI_SECRET_PROTECTION.md`

Updated:

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md`
- `docs/continuity/DEVIN_OUTPUT_CONTRACT.md`
- `docs/continuity/CURRENT_STATE.json`
- `docs/continuity/CURRENT_GIT_STATE.md`
- `docs/continuity/CURRENT_HANDOFF.md`
- `docs/continuity/CURRENT_OPEN_WORK.md`
- `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md`
- `PROJECT_STATE.md`
- `FORTSCHRITT.md`
- `tools/continuity/generate_handoff.py`
- `tools/continuity/validate_continuity.py`
- `tools/continuity/test_handoff_and_validator.py` (new)

---

## New development-security authority

`DEVELOPMENT_SECURITY_WORKFLOW_V1.md` establishes:

- B-025 product security invariants retain precedence.
- S0–S4 security classification with workflow depth per class.
- S2: no mandatory per-PR Frontier/Opus audit during normal V1 development, but known HIGH/CRITICAL findings remain immediate merge blockers.
- S3: integration security checkpoints after 3–5 coupled subsystems; first expected slice is B-002 + B-003 + B-004 + B-005.
- S4: release security workflow including READ-ONLY AI audits, physical GrapheneOS/TEE testing, and a mandatory external human audit.

---

## Cloud-AI secret authority

`CLOUD_AI_SECRET_PROTECTION.md` codifies:

- NO production user private key or cryptographic root secret may ever be exposed to a cloud-AI environment.
- Explicit allow and deny lists for what cloud AI may / may not see.
- STOP procedure when a real secret is required.
- No custom crypto primitive as a workaround.

---

## S0–S4 summary

| Class | Examples | Audit depth |
|-------|----------|-------------|
| S0 | UI, copy, visual work | implementation → tests → CI → PR |
| S1 | ordinary business logic | implementation → tests → review → PR |
| S2 | Device Auth, E2EE, keys, licensing | strong tests, adversarial tests, CI, PR, no HIGH/CRITICAL deferral |
| S3 | integration of 3–5 security subsystems | trust-boundary, crash consistency, replay, fail-open/closed testing |
| S4 | release | freeze baseline, READ-ONLY AI audits, physical hardware tests, human audit, B-023 GO/NO-GO |

---

## V1 AI security-audit timing

READ-ONLY AI audits occur **AFTER FUNCTIONAL V1**. Findings are remediated through small traceable branches / PRs. AI does **not** replace the external human audit.

---

## GitHub / main governance

- `main` is a security ledger.
- Normal flow: branch → implementation → tests → CI → PR → merge.
- No direct feature/governance push to `main`.
- No force push to `main`.
- If server-side branch protections are not technically enforced: **MANUAL GOVERNANCE ENFORCEMENT REQUIRED**.

---

## B-017-Lite timing

B-017-Lite runs **AFTER this governance task is merged and BEFORE B-004/B-005 implementation**. It covers lint, secret scanning, dependency advisories, CI hardening, and supply-chain evidence foundation. It is **not** implemented in this task.

---

## Authority index changes

`AUTHORITY_INDEX.md` now lists `CLOUD_AI_SECRET_PROTECTION.md` and `DEVELOPMENT_SECURITY_WORKFLOW_V1.md` with explicit precedence below B-025 and B-026.

---

## Bootstrap changes

`CURRENT_CHAT_BOOTSTRAP_PROMPT.md` now requires reading the new governance documents and answering the 15 reconstruction questions before starting work.

---

## Devin output contract changes

`DEVIN_OUTPUT_CONTRACT.md` now requires:

- `SECURITY CLASS: S0 / S1 / S2 / S3 / S4`
- `CLOUD-AI SECRET STATUS`
- `IMPLEMENTED / VERIFIED / PARTIAL / MISSING / UNVERIFIED`
- No model recommendation field.

---

## Handoff generator changes

`generate_handoff.py` now performs a MINIMUM secret-preflight:

- rejects `.env`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `*.p8`, etc.
- rejects filenames with `service-account`, `private-key`, `database-dump` markers.
- rejects files containing private-key PEM markers.
- reports only category, relative path, and reason; never prints the secret content.

B-017-Lite will add stronger maintained scanning later.

---

## Continuity validator changes

`validate_continuity.py` now:

- requires `CLOUD_AI_SECRET_PROTECTION.md` and `DEVELOPMENT_SECURITY_WORKFLOW_V1.md`.
- checks `CURRENT_HANDOFF.md` / `CURRENT_GIT_STATE.md` baseline consistency.
- checks `CURRENT_GIT_STATE.md` handoff branch vs live.
- detects stale current-state phrases (e.g., `~27%`, "Device Authentication has not started").
- checks `CURRENT_NEXT_DEVIN_TASK.md` does not still list PROMPT-008 as active without MERGED.

---

## Current-state synchronization

All current-state surfaces now record:

- `main` @ `881c85ec726d8a32eb84b00955b6b9db7912fe1e`
- B-002 and B-003 MERGED FOUNDATION
- active branch `governance/development-security-handoff-v1`
- next gate `DEVELOPMENT SECURITY GOVERNANCE / HANDOFF HARDENING`
- missing/unverified: B-004, B-005, physical GrapheneOS, StrongBox/TEE, final human audit, production GO/NO-GO

---

## Tests

Added `tools/continuity/test_handoff_and_validator.py` covering:

A. new governance files required by validation  
B. `CURRENT_HANDOFF.md` required  
C. handoff includes new governance  
D. handoff excludes `.git/`  
E. handoff includes `CURRENT_CHAT_BOOTSTRAP_PROMPT.md`  
F. `.env` style file blocks handoff  
G. private-key PEM marker blocks handoff  
H. key/high-risk filename blocks handoff  
I. secret contents not printed in error output  
J. bootstrap references new governance  
K. validator catches inconsistent current-state  
L. historical entries do not falsely fail validation  

Result: **12/12 PASS**.

---

## Generated handoff ZIP

- `ANOX_HANDOFF_2026-08-23_881c85ec726d.zip`
- FILE COUNT: 311
- SHA-256: `14c202f7bd8901d5d2390ac105e889e3db4bf74d981a48eab9b3d2d6e6742cf5`
- `EMERGENCY_DIRTY` because the working tree had uncommitted PROMPT-009 changes at the time of generation.
- Forbidden artifacts (`.git/`, `.env`, `*.pem`, `*.key`, etc.): **absent**
- Required files (authority, bootstrap, continuity): **present**

---

## Cold-chat recovery test

A new session can answer all 15 required questions from the handoff ZIP alone:

1. Frozen product architecture: `B025/SECURITY_INVARIANTS_V1_1.md` — **PASS**
2. Current main truth: `CURRENT_GIT_STATE.md` / `CURRENT_STATE.json` — **PASS**
3. B-002 merged: `CURRENT_IMPLEMENTATION_STATE.md` — **PASS**
4. B-003 merged: `CURRENT_IMPLEMENTATION_STATE.md` — **PASS**
5. What comes next: `CURRENT_NEXT_DEVIN_TASK.md` — **PASS**
6. S0–S4: `DEVELOPMENT_SECURITY_WORKFLOW_V1.md` — **PASS**
7. Per-PR Frontier audits mandatory? **NO** — **PASS**
8. HIGH/CRITICAL findings? **THEY REMAIN IMMEDIATE MERGE BLOCKERS** — **PASS**
9. Cloud-AI invariant: `CLOUD_AI_SECRET_PROTECTION.md` — **PASS**
10. Production user private keys in Cloud AI? **NO** — **PASS**
11. B-017-Lite timing? **AFTER GOVERNANCE/HANDOFF HARDENING, BEFORE B-004/B-005** — **PASS**
12. Full READ-ONLY AI audit? **AFTER FUNCTIONAL V1** — **PASS**
13. External human audit required? **YES** — **PASS**
14. `main` PR-only? **YES** — **PASS**
15. Model recommendations in Devin prompt? **NO** — **PASS**

Overall: **PASS**.

---

## Limitations

- The handoff ZIP was generated as an emergency/dirty handoff because the working tree was not yet committed.
- B-017-Lite is defined but not implemented.
- B-004, B-005, and B-017 full remain out of scope.
- Physical GrapheneOS / StrongBox / TEE behavior remains unverified.

---

## Next gate

**B-017-Lite CI / Secret / Supply-Chain Hardening**

B-004 **MUST NOT** start before that gate is completed.
