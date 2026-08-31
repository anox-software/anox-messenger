# B027-C — Final Pre-Product Architecture/Security Audit Plan

**Status:** PLAN — NOT EXECUTED  
**Branch:** `governance/b027-final-integration`  
**Date:** 2026-08-31  

---

## Status

This document is the human-readable contract for the final pre-product architecture/security audit gate. It is frozen on this branch and must not be executed until B027-C workforce integration is complete. The machine-readable source of truth is `docs/workforce/audits/final-audit-plan.json`.

---

## Authority

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B_FREEZE_REGISTRY.md`
- `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`
- `docs/workforce/MODEL_PROVIDER_POLICY.md`

---

## Scope

The final audit gate must independently assess the complete architecture and security posture of the anoX V1 project before product development (B-004/B-005) may resume. It is composed of three isolated, fresh audit sessions:

1. **AUDIT-MAIN-ARCHITECTURE** — product and system architecture.
2. **AUDIT-WORKFORCE-ARCHITECTURE** — B-027 AI workforce/work-control governance.
3. **AUDIT-SECURITY-ARCHITECTURE** — security, privacy, cryptography, and trust boundaries.

Each session is read-only, starts with no shared state, produces an `audit-result` record, and may only transition to targeted fix after a Findings Freeze.

---

## Canonicity

- The machine-readable manifest for this plan is `docs/workforce/audits/final-audit-plan.json`.
- The canonical branch is `governance/b027-final-integration`.
- The canonical repository is `/Users/3xpress/Desktop/anoX Messanger`.
- All audit results must conform to `docs/workforce/schemas/audit-result.schema.json`.
- All executed audit results are appended to `docs/workforce/registries/audits.jsonl`.
- The future master report contract is `docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md`.

Any hand-written report must reference the machine-readable manifest and schema.

---

## AUDIT-MAIN-ARCHITECTURE

**Audit ID:** `ANOX-AUDIT-MAIN-ARCH-001`

**Scope:**

- `docs/current/SYSTEM_ARCHITECTURE.md`
- `docs/current/BACKEND_ARCHITECTURE.md`
- `docs/current/DATABASE_ARCHITECTURE.md`
- `docs/current/KEY_AND_SESSION_ARCHITECTURE.md`
- `docs/current/MESSAGE_LIFECYCLE.md`
- `docs/current/API_WIRE_PROTOCOL.md`
- `docs/current/CONTACTS_AND_VERIFICATION.md`
- `docs/current/METADATA_PRIVACY.md`
- `docs/current/PUSH_OFFLINE.md`
- `docs/current/ATTACHMENTS.md`
- `docs/current/ACCOUNT_DEVICE_LIFECYCLE.md`
- `docs/current/ACCOUNT_LICENSE_REGISTRATION.md`
- `docs/current/ACCOUNT_RECOVERY_POLICY.md`
- `docs/current/SECURITY_INVARIANTS.md`
- `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md`
- `docs/authority/B025/TRACK_B/B024_FINAL_MAIN_CONSISTENCY_AUDIT.md`

**Required authorities:**

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B_FREEZE_REGISTRY.md`
- `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md`

**Required architecture domains:**

- `system`
- `backend`
- `crypto`
- `database`
- `messaging`
- `push`
- `contacts`
- `privacy`
- `api_wire`
- `attachments`
- `account_lifecycle`

**Prohibited changes during audit:**

- Product source code in `android/`, `crypto/rust/`, or `backend/`.
- CI workflow files in `.github/workflows/`.
- Higher authority documents, except B027 updates authorized by a separate task.
- Role contracts, workforce state, or schemas without an explicit B027 task.
- Signing, release, or break-glass actions.

**Output schema:** `docs/workforce/schemas/audit-result.schema.json`

**Fresh session:** yes

**Read-only:** yes

**Next gate after:** Findings Freeze

---

## AUDIT-WORKFORCE-ARCHITECTURE

**Audit ID:** `ANOX-AUDIT-WORKFORCE-ARCH-001`

**Scope:**

- `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`
- `docs/workforce/MODEL_PROVIDER_POLICY.md`
- `docs/workforce/WORKFORCE_STATE.json`
- `docs/workforce/registries/roles.json`
- `docs/workforce/roles/ROLE-001.md` through `ROLE-019.md`
- `docs/workforce/schemas/`
- `docs/workforce/registries/`
- `tools/workforce/state_gate_resolver.py`
- `tools/workforce/validate_b027a.py`
- `tools/workforce/validate_b027b.py`
- `tools/workforce/validate_b027_integrity.py`
- `tools/continuity/validate_continuity.py`
- `docs/continuity/CURRENT_HANDOFF.md`
- `docs/continuity/CURRENT_STATE.json`
- `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl`

**Required authorities:**

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B_FREEZE_REGISTRY.md`
- `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`

**Required architecture domains:**

- `workforce`
- `governance`
- `resolver`
- `continuity`
- `role_permissions`
- `state_gate_resolver`

**Prohibited changes during audit:**

- Direct changes to role authority or role contracts without an authorized task.
- D4-class material or AI access to production secrets.
- Autonomous remote write, merge, or release.
- Product code changes outside workforce tooling.
- Higher authority documents.

**Output schema:** `docs/workforce/schemas/audit-result.schema.json`

**Fresh session:** yes

**Read-only:** yes

**Next gate after:** Findings Freeze

---

## AUDIT-SECURITY-ARCHITECTURE

**Audit ID:** `ANOX-AUDIT-SECURITY-ARCH-001`

**Scope:**

- `docs/current/SECURITY_REQUIREMENTS.md`
- `docs/current/SECURITY_INVARIANTS.md`
- `docs/current/THREAT_MODEL.md`
- `docs/current/LOCAL_DEVICE_SECURITY.md`
- `docs/current/LOCAL_KEY_STATE_LIFECYCLE_V1_FROZEN.md`
- `docs/current/KEY_AND_SESSION_ARCHITECTURE.md`
- `docs/current/API_WIRE_PROTOCOL.md`
- `docs/current/DATABASE_ARCHITECTURE.md`
- `docs/current/METADATA_PRIVACY.md`
- `docs/current/MESSAGE_LIFECYCLE.md`
- `docs/current/ACCOUNT_DEVICE_LIFECYCLE.md`
- `docs/current/ACCOUNT_LICENSE_REGISTRATION.md`
- `docs/current/ACCOUNT_RECOVERY_POLICY.md`
- `docs/current/AUTH_PROTOCOL_STATUS.md`
- `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
- `docs/authority/B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md`
- `docs/authority/B025/TRACK_B/B003_ACCOUNT_LICENSE.md`
- `docs/authority/B025/TRACK_B/B006_VODOZEMAC_KEY_DISTRIBUTION.md`
- `docs/authority/B025/TRACK_B/B017_CICD_SUPPLY_CHAIN.md`
- `docs/authority/B025/TRACK_B/B021_SECURITY_TEST_MATRIX.md`

**Required authorities:**

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B_FREEZE_REGISTRY.md`
- `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`

**Required architecture domains:**

- `security_invariants`
- `trust_boundaries`
- `cryptography`
- `e2ee`
- `key_lifecycle`
- `auth`
- `rls`
- `android_security`
- `build_release`
- `supply_chain`
- `privacy`

**Prohibited changes during audit:**

- Product code in `android/`, `crypto/rust/`, or `backend/`.
- CI workflow files.
- Higher authority documents.
- Signing, release, or break-glass actions.
- D4-class access by any AI role.

**Output schema:** `docs/workforce/schemas/audit-result.schema.json`

**Fresh session:** yes

**Read-only:** yes

**Next gate after:** Findings Freeze

---

## Fresh-Session Requirement

Each audit session must start from a fresh context with no shared prompt state, no stale findings, and a clean working tree or a read-only branch clone. The audit role must not be the same role that implemented the surface under audit where independence is required. The start SHA must be an ancestor of or equal to the current HEAD and must be recorded in the audit result.

---

## Audit Workflow

The canonical workflow for every final audit session is fail-closed and sequential:

1. **Read-Only** — The auditor examines the canonical architecture surfaces and the higher authority chain. No changes are permitted.
2. **Findings Freeze** — The auditor records all findings using the `ANOX-FINDING-XXXXXXXXX` namespace and produces an audit result. The set of findings is frozen.
3. **Targeted Fix** — Only after Findings Freeze may an authorized task target the accepted findings. Fixes must not expand scope.
4. **Targeted Delta Retest** — The fix is retested against the frozen findings. New evidence is recorded.
5. **Systemic Re-audit if required** — If the fix reveals systemic impact or the audit result marked `systemic_reaudit_required: true`, a fresh, isolated systemic re-audit is authorized.
6. **Human Final Gate** — A human Product & Security Owner decision records that the audit is accepted, all blocking findings are closed, and product-resume conditions are met.

No audit session may advance directly to product-resume without the Human Final Gate.

---

## Finding Namespaces

- `ANOX-FINDING-XXXXXXXXX` — canonical findings, governed by `docs/workforce/schemas/finding.schema.json`.
- `ANOX-AUDIT-XXXXXXXXX` — audit session identity and audit result records.
- `LEGACY-AUDIT-*` — legacy revalidation session identifiers.

Findings discovered during an audit must be cross-referenced by `finding_ids` in the audit result. Duplicate or conflicting finding identifiers for the same scope are not permitted.

---

## Output Schema

All audit output, both final and legacy, must conform to:

`docs/workforce/schemas/audit-result.schema.json`

Executed results are appended to:

`docs/workforce/registries/audits.jsonl`

---

## Product-Resume Block

Product development for B-004/B-005 remains blocked until all of the following conditions are satisfied and recorded:

- All three final audit sessions produce `PASS` or `PARTIAL` with no `FAIL` or `BLOCKED`.
- All required legacy audits are satisfied.
- No open `CRITICAL` or `HIGH` findings remain.
- All targeted fixes have completed delta retest with new evidence.
- Any `systemic_reaudit_required` flag has been cleared by a fresh systemic re-audit.
- A human final gate decision is recorded in `docs/workforce/registries/decisions.jsonl`.
- The machine decision from `tools/workforce/state_gate_resolver.py` is not `BLOCKED`.

The fail-closed gate name is `PRODUCT_DEVELOPMENT_BLOCKED_PENDING_FINAL_AUDIT`.
