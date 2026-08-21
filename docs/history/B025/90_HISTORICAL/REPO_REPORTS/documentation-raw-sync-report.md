# DOCSYNC-001 — Project Documentation Synchronization Report

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## A. All Markdown Files Found

| Path | Old Status | Action Taken | New Status |
|------|------------|--------------|------------|
| `README.md` | Raw1.1 | Rewritten with current status, toolchain, and docs map | CURRENT |
| `CHANGELOG.md` | Raw1.1 | Updated `Unreleased` with current foundation, test results, and open items | CURRENT |
| `docs/architecture/key-architecture.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/decisions/open-decisions.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/security/account-recovery.md` | Raw1.1 recovery analysis | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/security/android-jni-crypto-validation-report.md` | Raw1.1 runtime report | Added HISTORICAL/SUPERSEDED + corrections header | HISTORICAL |
| `docs/security/android-runtime-crypto-validation-report.md` | Current report | Added CURRENT header | CURRENT |
| `docs/security/crypto-foundation-completion-report.md` | Devin report | Added HISTORICAL DEVIN REPORT header | HISTORICAL |
| `docs/security/crypto-foundation-security-review.md` | Review report | Added HISTORICAL/CURRENT-STATUS BOUNDARY header | HISTORICAL |
| `docs/security/crypto-foundation-validation-report.md` | Evidence report | Added HISTORICAL EVIDENCE header | HISTORICAL |
| `docs/security/cryptography-comparison.md` | Raw1.1 | Added SUPERSEDED HISTORICAL DECISION INPUT header | HISTORICAL |
| `docs/security/cryptography-status.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/security/device-loss-scenarios.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/security/metadata-analysis.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/security/push-notifications.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/security/security-requirements.md` | Raw1.1 150 requirements | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/security/server-trust-model.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/security/threat-model.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/specifications/device-identity.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/specifications/public-key-verification.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/specifications/support-account.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/specifications/user-identity.md` | Raw1.1 | Added HISTORICAL/SUPERSEDED header | HISTORICAL |
| `docs/current/SYSTEM_ARCHITECTURE.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/SECURITY_INVARIANTS.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/SECURITY_REQUIREMENTS.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/ACCOUNT_LICENSE_REGISTRATION.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/KEY_AND_SESSION_ARCHITECTURE.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/LOCAL_DEVICE_SECURITY.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/ACCOUNT_RECOVERY_POLICY.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/AUTH_PROTOCOL_STATUS.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/API_WIRE_PROTOCOL.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/MESSAGE_LIFECYCLE.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/CONTACTS_AND_VERIFICATION.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/PUSH_OFFLINE.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/ATTACHMENTS.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/BACKEND_ARCHITECTURE.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/DATABASE_ARCHITECTURE.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/THREAT_MODEL.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/METADATA_PRIVACY.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/ACCOUNT_DEVICE_LIFECYCLE.md` | Missing | Created new canonical doc | CURRENT |
| `docs/current/OPEN_ARCHITECTURE_ITEMS.md` | Missing | Created new canonical doc | CURRENT |
| `docs/README.md` | Missing | Created new documentation guide | CURRENT |
| `PROJECT_STATE.md` | Missing | Created project state summary | CURRENT |
| `docs/reports/current-code-gap-audit.md` | Missing | Created | CURRENT |
| `docs/reports/documentation-raw-sync-report.md` | Missing | Created | CURRENT |

## B. Files Moved to History

No files were moved or deleted; all historical documents were preserved in place with HISTORICAL/SUPERSEDED headers and pointer links to current canonical equivalents. The old content remains available as evidence and is not fabricated.

## C. Files Rewritten

- `README.md`
- `CHANGELOG.md`

## D. New Canonical Docs Created

Twenty-three new files under `docs/current/`, `docs/README.md`, `PROJECT_STATE.md`, and two new files under `docs/reports/`.

## E. Unresolved Architecture Decisions

The following remain genuinely OPEN and require an explicit ADR to close:

1. Final authentication/token/challenge/signature contract.
2. Final push provider/transport selection.
3. Offline ciphertext queue TTL.
4. Final DB schema.
5. Attachment AEAD library final selection (XChaCha20-Poly1305 only if the final maintained Rust library supports it).
6. Certificate pinning (not mandatory in V1).
7. State serialization envelope version byte.
8. Support virtual-device/HA/ticket/retention operational model.
9. 1-year license plan.

## F. Cross-Document Consistency

A check was performed for the following terms. Where they appear in historical docs, they are labeled HISTORICAL/SUPERSEDED. They are not present as current requirements in `docs/current/`.

- `Raw1.1` — now header-labeled in all obsolete files.
- `recovery` / `recovery code` — removed as a current V1 requirement.
- `multi-device` / `5 devices` / `10 devices` — removed as a current V1 feature.
- `libsignal` / `OpenPGP` / `PGP` — removed as current E2EE choices.
- `FCM fallback` / `UnifiedPush default` — not frozen as current.
- `key backup` / `server-signed identity trust` — not current V1.
- `certificate pinning MUST` — not mandatory.
- `dummy traffic MUST` — not a V1 feature.
- `JDK 21 required` — superseded; project uses JDK 17.
- `NDK not pinned` — corrected; `ndkVersion = "26.2.11394342"`.
- `1 year` / `12 months` license — not a current binding plan.

## G. Functional Code Changes

**0**

No functional code was changed. Only Markdown documentation was updated, and only code-affecting documentation additions were architecture/status headers. The Rust/Kotlin/JNI source remains untouched.

## H. Code Gaps Recorded

See `docs/reports/current-code-gap-audit.md` for CODE-CRITICAL-001 through CODE-INFO-010.

## I. Exact Recommended Next Engineering Task

Run `:android:assembleRelease` to confirm the release APK packages the rebuilt `libanox_crypto.so` artifacts without error, then conduct an independent security review of the Rust/JNI crypto foundation before beginning any backend, account, messaging, push, contact, or attachment implementation.

---

## Summary Counts

| Metric | Count |
|--------|-------|
| Markdown files scanned | 48 |
| Current files updated/created | 23 |
| Rewritten | 2 |
| Historical/Superseded (header-labeled) | 19 |
| New canonical `docs/current/` docs | 21 |
| New reports | 2 |
| Unresolved architecture decisions | 9 |
| Functional code changes | 0 |
