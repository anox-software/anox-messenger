# B027-C — Legacy Audit Plan

**Status:** PLAN — NOT EXECUTED  
**Branch:** `governance/b027-final-integration`  
**Date:** 2026-08-31  

---

## Status

This document is the human-readable contract for legacy revalidation audits. It covers the one-time final gate legacy audits and the future affected-surface policy. The machine-readable source of truth is `docs/workforce/audits/legacy-audit-plan.json`.

---

## Authority

- `docs/authority/AUTHORITY_INDEX.md`
- `docs/authority/B_FREEZE_REGISTRY.md`
- `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`

---

## Scope

The legacy audit plan defines the one-time revalidation sessions that must be satisfied before the final product gate may open, and the ongoing policy for affected-surface revalidation after the gate. Legacy audits are isolated, fresh, and read-only until a Findings Freeze is issued.

---

## One-Time Final Gate Legacy Audits

The following legacy audit sessions must each complete with an acceptable `audit-result` record before the final pre-product architecture/security audit gate may be considered satisfied.

### B-002 — Device Authentication

- **Audit ID:** `LEGACY-AUDIT-B002`
- **Scope:** Device binding, trust assumptions, and device authentication.
- **Required architecture:**
  - `docs/authority/B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md`
  - `docs/current/ACCOUNT_DEVICE_LIFECYCLE.md`
  - `docs/current/LOCAL_DEVICE_SECURITY.md`
- **Trigger domains:** `device_binding`

### B-003 — Account / License

- **Audit ID:** `LEGACY-AUDIT-B003`
- **Scope:** Registration, account lifecycle, and license management.
- **Required architecture:**
  - `docs/authority/B025/TRACK_B/B003_ACCOUNT_LICENSE.md`
  - `docs/current/ACCOUNT_LICENSE_REGISTRATION.md`
  - `docs/current/ACCOUNT_DEVICE_LIFECYCLE.md`
- **Trigger domains:** `registration`, `account`

### Crypto

- **Audit ID:** `LEGACY-AUDIT-CRYPTO`
- **Scope:** Cryptographic protocols, key handling, and E2EE assumptions.
- **Required architecture:**
  - `docs/authority/B025/TRACK_B/B006_VODOZEMAC_KEY_DISTRIBUTION.md`
  - `docs/current/KEY_AND_SESSION_ARCHITECTURE.md`
  - `docs/current/LOCAL_KEY_STATE_LIFECYCLE_V1_FROZEN.md`
- **Trigger domains:** `crypto`, `protocol`

### Android-Sec

- **Audit ID:** `LEGACY-AUDIT-ANDROID-SEC`
- **Scope:** Android local security, storage, and runtime protections.
- **Required architecture:**
  - `docs/current/LOCAL_DEVICE_SECURITY.md`
  - `docs/authority/B025/TRACK_B/B007_API_WIRE.md`
  - `docs/authority/B025/TRACK_B/B009_LOCAL_DATABASE.md`
- **Trigger domains:** `android_security`, `local_storage`

### Build

- **Audit ID:** `LEGACY-AUDIT-BUILD`
- **Scope:** Build scripts, dependency management, and supply chain integrity.
- **Required architecture:**
  - `docs/authority/B025/TRACK_B/B017_CICD_SUPPLY_CHAIN.md`
  - `docs/authority/B025/TRACK_B/B018_RELEASE_SIGNING_UPDATES.md`
  - `docs/authority/B025/TRACK_B/B023_RELEASE_DOD.md`
- **Trigger domains:** `build`, `dependency`, `supply_chain`, `supply-chain`

### Integration

- **Audit ID:** `LEGACY-AUDIT-INTEGRATION`
- **Scope:** Cross-component consistency and end-to-end integration.
- **Required architecture:**
  - `docs/authority/B025/TRACK_B/B022_INDEPENDENT_AUDIT.md`
  - `docs/authority/B025/TRACK_B/B024_FINAL_MAIN_CONSISTENCY_AUDIT.md`
  - `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md`
- **Trigger domains:** `cross_component`, `integration`

---

## Future Affected-Surface Legacy Audits

After the final product gate, any change that affects the trigger domains listed above must produce a fresh, isolated legacy audit session for each affected `audit_id`. The mapping is machine-readable in `docs/workforce/audits/legacy-audit-plan.json`.

- Only affected domains trigger revalidation.
- Unrelated changes to `docs`, `typos`, `spelling`, `comments`, `markdown`, or `formatting` must not trigger legacy revalidation.
- If a single change affects multiple legacy domains, the resolver may produce multiple distinct sessions, but must not create duplicate sessions for the same `audit_id`.
- Affected-surface legacy audits are gate-blocking until satisfied.

---

## Session Isolation

Each legacy audit is an independent session. A legacy session must not share prompt context, findings, or evidence with the final audit sessions or with other legacy sessions. The start SHA must be recorded, and the audit must be performed by a role independent of the surface under review where independence is required.

---

## No Audit Flooding

A single code change or derived work candidate must not trigger an unbounded number of audit sessions. The resolver must:

- Map each affected domain to at most one legacy `audit_id`.
- Collapse duplicate `audit_id` values for the same change.
- Ignore docs/typos/markdown/comment/spelling/formatting-only changes.
- Escalate to a `SEC-C` security reassessment only when the change is systemic or crosses multiple critical security domains.

---

## Fresh-Session Requirement

Every legacy audit session must be fresh. The auditor must start with a clean context, a recorded canonical SHA, and no shared state from previous sessions. The session is read-only until a Findings Freeze, after which targeted fixes and delta retests may be authorized. A stale or malformed SHA must be rejected.
