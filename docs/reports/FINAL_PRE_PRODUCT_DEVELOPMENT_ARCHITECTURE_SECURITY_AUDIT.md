# FINAL PRE-PRODUCT DEVELOPMENT ARCHITECTURE / SECURITY AUDIT

**Master Report Contract:** This document aggregates the three final pre-product audit sessions and the six required legacy audits.
**Status:** IN PROGRESS — AUDIT 1 (MAIN ARCHITECTURE) COMPLETE
**Date:** 2026-08-31
**Canonical Repository:** `https://github.com/anox-software/anox-messenger`

---

## Required Audit Sessions

| Audit ID | Title | Status | Output |
|---|---|---|---|
| `AUDIT-MAIN-ARCHITECTURE` | AUDIT-MAIN-ARCHITECTURE | COMPLETE — PASS WITH FINDINGS | This section |
| `AUDIT-WORKFORCE-ARCHITECTURE` | B-027 workforce/work-control governance | NOT EXECUTED | — |
| `AUDIT-SECURITY-ARCHITECTURE` | Security, privacy, cryptography, trust boundaries | NOT EXECUTED | — |

**Required Legacy Audits:** `LEGACY-AUDIT-B002`, `LEGACY-AUDIT-B003`, `LEGACY-AUDIT-CRYPTO`, `LEGACY-AUDIT-ANDROID-SEC`, `LEGACY-AUDIT-BUILD`, `LEGACY-AUDIT-INTEGRATION` — all NOT EXECUTED.

**Product-Resume Block:** Product development for B-004/B-005 remains `BLOCKED_PENDING_FINAL_AUDIT` until all final/legacy audits pass, all blocking findings are closed, and the human final gate is recorded.

---

# AUDIT 1 — MAIN ARCHITECTURE

## EXECUTIVE RESULT

**PASS WITH FINDINGS**

No CRITICAL finding. 13 HIGH findings block affected-domain product implementation and the final product gate until remediated or explicitly risk-accepted by the human owner. The frozen architecture core (invariants, one-device/no-recovery model, E2EE trust model, push wake-only model) is internally coherent; the dominant defect classes are **fractured source of truth**, **frozen-authority ambiguity**, and **unspecified server-side enforcement contracts** for not-yet-built B-004/B-005/B-007 surfaces.

## CANONICAL SHA

`AUDIT_CANONICAL_SHA = 0a4910eab1a92622383721100879cda46f924ca0` (canonical `main`, PR #8 merge; B027-A/B/C ancestral; working tree CLEAN; local == origin/main)

## MODE

**READ-ONLY.** No file, commit, branch, or remote mutation during the audit itself.

## AUTHORITY PRECEDENCE

PASS — `docs/authority/AUTHORITY_INDEX.md` defines a single numbered precedence; validators confirm no competing list. However the index itself carries stale B-027 status (finding 002) and is undermined by `docs/README.md` routing (finding 004).

## TOTAL FINDINGS

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 13 |
| MEDIUM | 17 |
| LOW | 5 |
| INFO | 1 |
| **Total** | **36** |

## BLOCKING FINDINGS

All HIGH findings block product implementation in their affected domains and the Final Pre-Product Gate:

`ANOX-MAINARCH-001, -002, -003, -004, -005, -006, -007, -008, -009, -010, -011, -012, -013`

Most immediately blocking for the first product task (B-004 backend): **001, 003, 008, 009, 010**.

## ARCHITECTURE COVERAGE

| Domain | Status |
|---|---|
| System/client architecture (B-001, ULTIMATE) | REVIEWED |
| B-002 Device Authentication | REVIEWED |
| B-003 Account/License | REVIEWED |
| B-004 Backend | REVIEWED (spec only; no implementation) |
| B-005 Database/RLS | REVIEWED (spec only) |
| B-006 Crypto/Key Distribution | REVIEWED (incl. Rust/JNI source) |
| B-007 API/Wire | REVIEWED (spec only) |
| B-008 Messaging/Sync | REVIEWED (spec only) |
| B-009 Local Database | REVIEWED (spec + foundation) |
| B-010 Contacts/Verification | REVIEWED (spec only) |
| B-011 Push/Offline | REVIEWED |
| B-012 Attachments | REVIEWED |
| B-013 Lifecycle | REVIEWED |
| B-014 Privacy/Retention/Logging | REVIEWED |
| B-015 Abuse/Rate-Limits | REVIEWED |
| B-016 Production Infrastructure | REVIEWED (spec only) |
| B-017 Build/Supply Chain | REVIEWED (incl. CI) |
| B-018 Release/Signing/Updates | REVIEWED (spec only) |
| B-019 Operations/IR | REVIEWED (spec only) |
| B-020 Product/Security UX | REVIEWED |
| B-021 Security Test Matrix | REVIEWED |
| B-022/B-023 Audit/Release DoD | REVIEWED |
| B-024+ Final consistency / freeze | REVIEWED |
| Cross-domain contracts | REVIEWED |
| Physical GrapheneOS/StrongBox runtime | NOT REVIEWABLE — no physical evidence in repo |
| Production Supabase/infrastructure config | NOT REVIEWABLE — no IaC exists |
| Runtime execution of Rust/Android tests | NOT REVIEWABLE — historical PASS accepted as recorded |

## CROSS-DOMAIN CONSISTENCY

**RESULT: FINDINGS.** Core frozen architecture is consistent; seams with unbuilt server surfaces are the dominant defect class. Verified non-findings include: E2EE plaintext boundary, no-recovery/one-device, key separation, DPoP parameters, backup exclusion, protected-state envelope, B017-Lite controls.

## SECURITY INVARIANT CONSISTENCY

**PASS WITH FINDINGS.** The 35 invariants are internally consistent. Defects: no traceability/enforcement matrix (011); duplicate in `docs/current/` is a drift channel (032); B-003 line 4 conflicts with no-phone/email posture (001).

## STATE MACHINE CONSISTENCY

**FINDINGS.** Account/device/entitlement states defined; license-expiry restricted-mode transitions undefined (014). Registration crash-resume defined; server concurrency contract missing (009). Message lifecycle states diverge between B-008 and `MESSAGE_LIFECYCLE.md` (022). Contact trust naming diverges (021). OTK claim transition unmodeled (010). Local crypto state is correctly ordered in `getLocalStateStatus`; `getOrCreateStateKey()` on read paths can silently mint a new K_STATE (023).

## TRUST BOUNDARIES

**FINDINGS.** Documented boundaries consistent with Invariants 5–7, 27–29. Gaps: RLS/role scope (003), FCM token reversibility (016), AI/CI/model-provider boundary not in MAIN trust description (028), committed `.so` provenance (013).

## PRIVACY MODEL

**PASS WITH FINDINGS.** No message plaintext at server/push consistent. Not metadata-free correctly disclaimed. B-003 wording could mandate phone/email (001). Deletion targets frozen but backup/PITR not reconciled (007). Push is wake-only. Anti-enumeration mandatory but mechanism not specified (017).

## FAILURE MODES

**FINDINGS.** Defined: registration crash-resume, fail-closed local state. Undefined: license expiry (014), attachment cleanup (015), backend-unavailable races (009), OTK double-claim (010), restore-from-backup vs erasure journal (007).

## GRAPHENEOS ASSUMPTIONS

**PASS WITH FINDINGS.** No security guarantees misattributed to GrapheneOS. Physical GrapheneOS/StrongBox test is a release hard gate currently UNVERIFIED (018).

## SERVER COMPROMISE MODEL

**PASS WITH FINDINGS.** No plaintext/message keys/attachment keys at server. Metadata/availability/account manipulation remains possible. Rollback detection, OTK withholding, backup resurrection are gaps (007/010).

## DEVICE COMPROMISE MODEL

**PASS.** No-recovery/no-backup posture consistent; one hygiene defect (023).

## SOURCE-OF-TRUTH / STALE DOCS

**FINDINGS (dominant defect class).** See 002, 004, 005, 006, 032, 034, 035. Superseded docs in active paths still describe prohibited architectures.

## IMPLEMENTATION-ARCHITECTURE DRIFT

**FINDINGS.** Foundation code is faithful. Drift/gaps: 008, 010, 019, 023, 029, 030, 031. B-004–B-016 are documentation-only (expected).

## TESTABILITY GAPS

**FINDINGS.** 011 (no invariant traceability), 026 (no B-021 test IDs), 018 (physical unverified).

---

## FINDINGS

Format: **ID | Severity | Class** — Title. Evidence → Consequence → Required fix → flags.

### HIGH

**ANOX-MAINARCH-001 | HIGH | CONTRADICTION / MISSING SPECIFICATION** — Frozen B-003 line "No password, mandatory email/phone/SMS" contradicts the no-phone/email identity model. Evidence: `docs/authority/B025/TRACK_B/B003_ACCOUNT_LICENSE.md:4` vs `docs/current/ACCOUNT_LICENSE_REGISTRATION.md:47`. Consequence: B-004 implementer could build mandatory PII collection. Fix: ADR + B-003 version bump rewording to "No password; no mandatory email/phone/SMS." Code affected: NO. Legacy: LEGACY-AUDIT-B003. Trust-boundary: NO. Re-audit: NO.

**ANOX-MAINARCH-002 | HIGH | SOURCE-OF-TRUTH DUPLICATION** — B-027 status contradictory across `B_FREEZE_REGISTRY.md:46`, `AUTHORITY_INDEX.md:18,36`, and `B027_AI_WORKFORCE_GOVERNANCE.md:3`. Consequence: fresh session resolving from registry would use wrong B-027 status/location. Fix: update registry row and AUTHORITY_INDEX. Code affected: NO. Re-audit: NO.

**ANOX-MAINARCH-003 | HIGH | CONTRADICTION / MISSING SPECIFICATION / TRUST-BOUNDARY DEFECT** — B-005 "FROZEN v1.10" vs `DATABASE_ARCHITECTURE.md:18` "NOT frozen"; no RLS/role model, DPoP context propagation, service-role usage. Consequence: B-004/B-005 implementation would start against contradictory/insufficient spec; RLS may be disabled by service role. Fix: produce DB-SCHEMA-V1-FROZEN with tables, constraints, RLS, role matrix. Trust-boundary change: YES. Systemic re-audit: YES.

**ANOX-MAINARCH-004 | HIGH | SOURCE-OF-TRUTH DUPLICATION** — `docs/README.md` routes agents to `docs/current/` as source of truth, bypassing `AUTHORITY_INDEX.md`. Consequence: fresh agent lands on partially stale files. Fix: rewrite README routing; correct history path. Re-audit: NO.

**ANOX-MAINARCH-005 | HIGH | STALE CURRENT DOCUMENTATION** — `docs/current/AUTH_PROTOCOL_STATUS.md` and `ACCOUNT_DEVICE_LIFECYCLE.md:21` still describe Ed25519/refresh-token auth, contradicting B-002 P-256/ES256 DPoP. Fix: reconcile from B-002. Legacy: LEGACY-AUDIT-B002.

**ANOX-MAINARCH-006 | HIGH | STALE CURRENT DOCUMENTATION / CONTRADICTION** — Superseded docs outside `docs/history/` carry prohibited architectures (recovery, multi-device, key backup, UnifiedPush-default, zero-knowledge, custom verification). Fix: relocate to `docs/history/` or strip to stubs.

**ANOX-MAINARCH-007 | HIGH | TRUST-BOUNDARY DEFECT / PRIVACY DEFECT** — Backup/PITR retention not reconciled with B-014 deletion targets; deleted data may be resurrected. Fix: specify PITR/backup retention <= deletion targets or documented exception. Trust-boundary: YES. Systemic re-audit: YES.

**ANOX-MAINARCH-008 | HIGH | SECURITY DEFECT (by absence)** — Server-side DPoP replay cache, token issuance, revocation, device registry, one-active-device enforcement delegated to unbuilt B-004. Fix: B-004 task package must enumerate these as stop conditions. Legacy: LEGACY-AUDIT-B002/B003/INTEGRATION.

**ANOX-MAINARCH-009 | HIGH | MISSING SPECIFICATION** — B-007 has no endpoint inventory, per-endpoint authorization, idempotency, or race semantics. Fix: freeze `/v1` endpoint inventory before B-004. Legacy: LEGACY-AUDIT-INTEGRATION.

**ANOX-MAINARCH-010 | HIGH | IMPLEMENTATION-ARCHITECTURE DRIFT / STATE-MACHINE DEFECT** — B-006 OTK/fallback lifecycle (publish-ACK, fallback, 15-day retention, ~50% replenish, atomic claim) unmodeled. Fix: specify DB claim model + extend Rust/JNI using vodozemac. Legacy: LEGACY-AUDIT-CRYPTO.

**ANOX-MAINARCH-011 | HIGH | TESTABILITY GAP** — 35 binding invariants have no traceability to validators/tests. Fix: create invariant->verifier traceability matrix.

**ANOX-MAINARCH-012 | HIGH | CONTRADICTION** — B-022 vs B027-C final-audit gate criteria differ (named human reviewers + Medium blocking vs fresh AI sessions + CRITICAL/HIGH only). Fix: ADR distinguishing B027-C internal gate from B-022 release gate.

**ANOX-MAINARCH-013 | HIGH | TRUST-BOUNDARY DEFECT** — Full B-017 controls deferred; committed `.so` binaries have no CI provenance. Fix: track full-B-017; add `cargo-ndk` CI build or remove committed `.so`. Trust-boundary: YES. Legacy: LEGACY-AUDIT-BUILD.

### MEDIUM

**ANOX-MAINARCH-014** — License-expiry restricted Device Auth flow undefined.
**ANOX-MAINARCH-015** — Attachment blob cleanup on device revocation/account deletion unspecified.
**ANOX-MAINARCH-016** — FCM token reversible encryption overclaims protection.
**ANOX-MAINARCH-017** — Anti-enumeration / privacy network signals not operationally specified.
**ANOX-MAINARCH-018** — GrapheneOS/StrongBox physical verification unverified and release-gated.
**ANOX-MAINARCH-019** — `isProductionEligible()` unenforced at client registration call site.
**ANOX-MAINARCH-020** — License code alphabet and reserved username list unspecified.
**ANOX-MAINARCH-021** — Contact trust-state naming and `KEY_CHANGED` transitions undefined.
**ANOX-MAINARCH-022** — `MESSAGE_LIFECYCLE.md` adds unfrozen states and weakens durable-commit rule.
**ANOX-MAINARCH-023** — `CryptoBridge.getOrCreateStateKey()` on read paths may silently persist fresh K_STATE; the refuted claim that `MissingStateKey` was unreachable is corrected.
**ANOX-MAINARCH-024** — B-018/B-019 release signing and operations artifacts aspirational.
**ANOX-MAINARCH-025** — B-020 omits UX requirements for license/irreversible/update-trust flows.
**ANOX-MAINARCH-026** — B-021 lacks test IDs and traceability.
**ANOX-MAINARCH-027** — GitHub Free plan branch protection unenforceable assumption.
**ANOX-MAINARCH-028** — B-027 AI/CI/model-provider trust boundary not integrated into MAIN trust model.
**ANOX-MAINARCH-029** — `CommitArmed`/`isArmed` unratified in frozen B-003.
**ANOX-MAINARCH-030** — `wipeLocalCrypto` scope and single-session persistence diverge from B-009.

### LOW

**ANOX-MAINARCH-031** — `CryptoError.fromCode(-11)` mislabels Rust buffer-too-small error.
**ANOX-MAINARCH-032** — Verbatim duplicate authority docs in `docs/current/` are drift channels.
**ANOX-MAINARCH-033** — Stale crypto-foundation review describes K_STATE derivation incorrectly.
**ANOX-MAINARCH-034** — Residual OPEN markers in current docs conflict with frozen B-014/B-011/B-012.
**ANOX-MAINARCH-035** — `docs/README.md` references non-existent `docs/history/raw1.1/`.

### INFO

**ANOX-MAINARCH-036** — B-004 through B-016 remain documentation-only as expected pre-product; recorded to prevent mistaking architecture PASS for product readiness.

---

## LEGACY AUDIT IMPACT

| Legacy session | Must investigate |
|---|---|
| LEGACY-AUDIT-B002 | 001, 005, 008, 018, 019 |
| LEGACY-AUDIT-B003 | 001, 020, 029 |
| LEGACY-AUDIT-CRYPTO | 010, 023, 030, 031 |
| LEGACY-AUDIT-ANDROID-SEC | 018, 023, backup-exclusion regression |
| LEGACY-AUDIT-BUILD | 013, 027 |
| LEGACY-AUDIT-INTEGRATION | 008, 009, 010 |

## REQUIRED FIX ORDER

1. 002 + 004 + 035 (authority routing correctness)
2. 005 + 006 + 022 + 032 + 034 (stale/duplicate doc reconciliation)
3. 001 (B-003 ADR/version bump)
4. 012 (audit-gate ADR)
5. 003 → 009 → 010, then 017/014/015/016/020/021
6. 011 + 026 (traceability matrix)
7. 023/019/031/030 (code findings through later code/Legacy workflow)
8. 013/024/025/027/028 (release/build/boundary)
9. 007 coordinated with DB/infra design
10. 018/036 remain verification/implementation-state items.

## TRUST-BOUNDARY CHANGES REQUIRED

- 003: server ↔ DB/RLS
- 007: server ↔ backup
- 013: source ↔ artifact
- 024: signing/release custody (when defined)

## SYSTEMIC RE-AUDIT REQUIREMENT

- **YES:** 003, 007
- **NO:** all others

## TARGETED RETEST PLAN

- Stale docs: doc-consistency validator
- B-003: client unit tests + B-003 text review
- DB/API/OTK: schema/API validators + B-021 classes at B-004/B-005
- Backup/DR: B-021 backup/DR test class
- DPoP: B-004 integration tests
- Traceability: matrix completeness
- Audit gate: B-022/FINAL_AUDIT_PLAN diff review
- Build: CI artifact hash check
- Code: targeted Android/Rust unit tests

## VERIFIED NON-FINDINGS

- E2EE plaintext boundary maintained.
- No-recovery / one-device model consistent.
- Key separation (Device Auth / K_STATE / E2EE / license) correct in code.
- DPoP parameters consistent with B-002.
- Backup exclusion present.
- Protected-state envelope AES-256-GCM correct.
- B017-Lite controls validated.
- Marketing guardrails explicit.
- License separate from crypto identity.

## LIMITATIONS

- Physical StrongBox/TEE/GrapheneOS: INSUFFICIENT REPOSITORY EVIDENCE.
- Rust/Gradle tests not executed in session; historical PASS accepted.
- Production infrastructure/IaC absent; B-016 spec-only.
- Rust source reviewed statically.
- One explorer claim (unreachable MissingStateKey) was refuted and narrowed to finding 023.

## REPOSITORY MODIFIED

**NO** during the read-only audit. This Findings Freeze task modifies only governance/audit registry/continuity metadata, not product architecture or code.

## REMOTE MUTATION

**NONE.**

## NEXT STEP

`FREEZE MAIN ARCHITECTURE FINDINGS → HUMAN REVIEW → MAINARCH-FIX-01 — AUTHORITY / SOURCE-OF-TRUTH / B003 / AUDIT-GATE ARCHITECTURE REMEDIATION`


---

## MAINARCH-FIX-01 — Targeted architecture / source-of-truth remediation

**Status:** COMPLETE — verified by MAINARCH-RETEST-01
**Branch:** `remediation/mainarch-fix-01-authority-source-truth`
**Amendment:** `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md`
**Targeted findings (17):**

- HIGH: ANOX-MAINARCH-001, 002, 004, 005, 006, 012
- MEDIUM: ANOX-MAINARCH-014, 020, 021, 022, 025, 028, 029
- LOW: ANOX-MAINARCH-032, 033, 034, 035

**Verification:** All 17 findings Closed by MAINARCH-RETEST-01 PASS at `fd1fbddbddcba7d8705f7a76318856ad56dafb19`.

**Summary of changes:**

- Created `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md` as the current B-025 amendment surface (B-003 v1.5, B-008 v1.6, B-010 v1.3, B-013 v1.3, B-020 v1.2, B-022 v1.1, B-025 ULTIMATE development/AI trust boundary).
- Updated `docs/authority/B_FREEZE_REGISTRY.md` to record the amended versions and the completed B-027 status.
- Updated `docs/authority/AUTHORITY_INDEX.md` to include the amendment file in precedence and to reflect B-027 A/B/C implemented.
- Updated `docs/README.md` to route all sessions first to `docs/authority/AUTHORITY_INDEX.md` and removed `docs/current/**` as unconditional architecture source of truth.
- Updated `docs/current/AUTH_PROTOCOL_STATUS.md`, `ACCOUNT_DEVICE_LIFECYCLE.md`, `MESSAGE_LIFECYCLE.md`, `ACCOUNT_LICENSE_REGISTRATION.md`, `CONTACTS_AND_VERIFICATION.md`, `METADATA_PRIVACY.md`, `PUSH_OFFLINE.md`, `ATTACHMENTS.md` to point to current Authority and remove stale OPEN markers.
- Converted `docs/current/SECURITY_INVARIANTS.md`, `SYSTEM_ARCHITECTURE.md`, `OPEN_ARCHITECTURE_ITEMS.md` from duplicate normative bodies to pointers.
- Updated superseded historical documents (`docs/security/account-recovery.md`, `push-notifications.md`, `device-loss-scenarios.md`, `docs/architecture/key-architecture.md`, `docs/specifications/public-key-verification.md`, `docs/security/crypto-foundation-security-review.md`) with current Authority pointers.
- Updated `docs/current/ACCOUNT_RECOVERY_POLICY.md` to reference canonical sources and fixed the broken `docs/history/raw1.1/` reference.
- Created `tools/audit/validate_mainarch_fix01.py` to deterministically validate the remediation.
- Updated `docs/workforce/registries/findings.jsonl` so the 17 targeted findings are `Ready For Retest` with remediation notes.

**Product impact:** NONE. No Product code, Rust, JNI, backend, DB, CI, or workflow was changed.

**Product development state:** `BLOCKED_PENDING_FINAL_AUDIT` (unchanged).

**Next task:** `MAINARCH-FIX-02 — SERVER / DATABASE / RLS / API / OTK / RETENTION ARCHITECTURE REMEDIATION`.

---

## MAINARCH-RETEST-01 — Targeted delta retest of FIX-01 findings

**Status:** PASS
**Mode:** READ-ONLY TARGETED DELTA RETEST
**Canonical retest SHA:** `fd1fbddbddcba7d8705f7a76318856ad56dafb19`
**FIX-01 canonical merge SHA:** `fd1fbddbddcba7d8705f7a76318856ad56dafb19`
**Original audit SHA:** `0a4910eab1a92622383721100879cda46f924ca0`
**Model:** Devin SWE-1.7
**Retested findings:** 17
**Pass — Remediated:** 17/17
**Failures:** 0
**Regressions:** 0
**Not Reviewable:** 0

**Findings verified and Closed:**

- HIGH: ANOX-MAINARCH-001, 002, 004, 005, 006, 012
- MEDIUM: ANOX-MAINARCH-014, 020, 021, 022, 025, 028, 029
- LOW: ANOX-MAINARCH-032, 033, 034, 035

**Summary:**

Deterministic targeted retest confirms the MAINARCH-FIX-01 authority/source-of-truth/B003/state-machine/audit-gate remediation removed the original defects for the 17 findings. Severities were preserved. No product, Rust, backend, database, or CI changes were introduced. No material regression was found. No new independent architecture/security audit is required for this retest/closure.

**Product development state:** `BLOCKED_PENDING_FINAL_AUDIT` (unchanged).

**Next task:** `MAINARCH-FIX-02 — SERVER / DATABASE / RLS / API / OTK / RETENTION ARCHITECTURE REMEDIATION`.

---

## MAINARCH-FIX-02 — Server / database / RLS / API / OTK / retention / privacy architecture remediation

**Status:** COMPLETE — verified by MAINARCH-RETEST-02 (8 findings Closed)
**Branch:** `remediation/mainarch-fix-02-server-contracts`
**Amendment:** `docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md`
**Targeted findings (8):**

- HIGH: ANOX-MAINARCH-003, 007, 008, 009, 010
- MEDIUM: ANOX-MAINARCH-015, 016, 017

**Summary of changes:**

- Created `docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md` as the authoritative V1.2 architecture amendment, freezing `DB-SCHEMA-V1-FROZEN` and the server-facing security contracts.
- Updated `docs/authority/B_FREEZE_REGISTRY.md` to record amended versions for B-004, B-005, B-006, B-007, B-011, B-012, B-014, B-015, B-016.
- Updated `docs/authority/AUTHORITY_INDEX.md` precedence to include the V1.2 amendment.
- Defined B-005 DB/RLS contract: entity table, ownership, security-sensitive fields, retention, one-active-device DB enforcement, authenticated DB context, RLS policies, server role matrix, explicit `service_role` policy, security-critical transaction boundaries.
- Defined B-004 backend contract: request pipeline, `AuthenticatedDeviceContext`, service/repository layering, logging, admin/worker planes, secret handling.
- Defined B-002/B-004 Device Auth server contract: DPoP verification obligations, shared replay cache with fail-closed semantics, access-token binding/lifetime/no-refresh, revocation semantics.
- Defined B-007 V1 endpoint inventory with auth/authz, idempotency, concurrency/race, versioning, and stable error model.
- Defined B-006 OTK/fallback lifecycle: `AVAILABLE → CLAIMED` atomic claim, batch publication ACK, replenishment threshold, fallback 15-day retention, OTK exhaustion behavior.
- Defined B-014/B-016 backup/PITR/erasure-journal contract with honest residual retention bounds (PITR 7d, base backup 30d, object backup 30d) and restore ordering.
- Defined B-012 attachment lifecycle, orphaned-upload cleanup, and device/account deletion purge semantics.
- Defined B-011 FCM-token privacy contract with realistic threat model (backend recoverable) and logging/admin restrictions.
- Defined B-015 anti-enumeration, rate-limit identifiers, and IP-handling contract (raw IP ≤24h, no permanent fingerprint).
- Added cross-domain consistency matrix and milestone security-review flags for ANOX-MAINARCH-003 and ANOX-MAINARCH-007.
- Created `tools/audit/validate_mainarch_fix02.py` targeted validator.
- Updated `docs/workforce/registries/findings.jsonl` so the 8 targeted findings are `Ready For Retest` with remediation refs; no findings Closed.

**Product impact:** NONE. No Product code, Rust, JNI, backend, DB, CI, or workflow was changed.

**Product development state:** `BLOCKED_PENDING_FINAL_AUDIT` (unchanged).

**Trust-boundary / Security milestone flags:** ANOX-MAINARCH-003 (server ↔ DB/RLS) and ANOX-MAINARCH-007 (server ↔ backup/PITR) are deferred to the next scheduled Security Architecture milestone review as required by B027 policy. No immediate Claude security audit is triggered.

**Next task:** `MAINARCH-RETEST-02 — TARGETED DELTA RETEST OF SERVER / DATABASE / API / RETENTION ARCHITECTURE FINDINGS`.

---

## MAINARCH-RETEST-02 — Targeted delta retest of FIX-02 findings

**Status:** PASS
**Mode:** READ-ONLY TARGETED DELTA RETEST
**Canonical retest SHA:** `739ea1c36c3d6f8eedb9a315fc6fba5173a82289`
**FIX-02 canonical merge SHA:** `739ea1c36c3d6f8eedb9a315fc6fba5173a82289`
**Original audit SHA:** `0a4910eab1a92622383721100879cda46f924ca0`
**Model:** Devin SWE-1.7 Max
**Retested findings:** 8
**Pass — Remediated:** 8/8
**Failures:** 0
**Regressions:** 0
**Not Reviewable:** 0
**Claude used:** NO

**Findings verified and Closed:**

- HIGH: ANOX-MAINARCH-003, 007, 008, 009, 010
- MEDIUM: ANOX-MAINARCH-015, 016, 017

**Summary:**

Independent read-only targeted delta retest confirms the MAINARCH-FIX-02 server/database/RLS/API/OTK/retention/privacy remediation removed the original material defects for the 8 findings: `DB-SCHEMA-V1-FROZEN` provides an implementable entity/RLS/role/transaction contract; the B-002/B-004 Device Auth server contract (DPoP, shared replay cache, token binding, no refresh) is complete and consistent; the B-007 `/v1` inventory, idempotency, concurrency, error model and versioning are deterministic; the B-006 OTK/fallback lifecycle is vodozemac-compatible with atomic claim and explicit replenishment threshold; B-014/B-016 honestly separate live deletion from bounded backup/PITR residual retention with erasure-journal replay; B-012 attachment lifecycle and B-011 FCM-token threat model are truthful; B-015 anti-enumeration and rate-limit/IP handling are operationally specified. Severities preserved. No product, Rust, backend, SQL, or CI changes. No material regression found. No Claude audit executed or required now.

**Retest observations (non-blocking, not new findings):**

- `docs/current/DATABASE_ARCHITECTURE.md` retains historical advisory wording ("Final DB schema is NOT frozen") but explicitly subordinates itself to canonical Authority; not an authoritative contradiction.
- B-012/V1.2 correctly distinguish server-visible ciphertext metadata (size/hash) from hidden plaintext-side metadata (key/filename/MIME/plaintext size); no impossible privacy claim is made.

**Milestone security review coverage still pending:** ANOX-MAINARCH-003 (server ↔ DB/RLS trust boundary) and ANOX-MAINARCH-007 (server ↔ backup/PITR trust boundary) are Closed as *architecture remediation verified*; their modified trust boundaries remain scheduled for the next Security Architecture milestone review. This is not a Security Architecture Audit PASS.

**MAIN finding totals after closure:** Closed = 25, Remaining = 11 (ANOX-MAINARCH-011, 013, 018, 019, 023, 024, 026, 027, 030, 031, 036).

**Product development state:** `BLOCKED_PENDING_FINAL_AUDIT` (unchanged).

**Next task:** `MAINARCH-FIX-03 — TRACEABILITY / TEST MATRIX / RELEASE-GOVERNANCE ARCHITECTURE REMEDIATION`.

---

## MAINARCH-FIX-03 — Traceability / test matrix / release-governance / implementation-readiness remediation

**Status:** COMPLETE — verified by MAINARCH-RETEST-03 (5 findings Closed)
**Branch:** `remediation/mainarch-fix-03-traceability-release-governance`
**Substantive commit:** recorded in `docs/continuity/CURRENT_STATE.json` (`described_head`)
**Amendment:** `docs/authority/B025_MANDATORY_AMENDMENTS_V1_3.md`
**Validators:** `tools/audit/validate_mainarch_fix03.py` + `tools/audit/test_mainarch_fix03.py`

**Targeted findings (exactly 5):**

- HIGH: `ANOX-MAINARCH-011`
- MEDIUM: `ANOX-MAINARCH-024`, `ANOX-MAINARCH-026`, `ANOX-MAINARCH-027`
- INFO: `ANOX-MAINARCH-036`

**Explicitly untouched (later sessions):** `ANOX-MAINARCH-013`, `ANOX-MAINARCH-018`, `ANOX-MAINARCH-019`, `ANOX-MAINARCH-023`, `ANOX-MAINARCH-030`, `ANOX-MAINARCH-031` — remain `Open`, unchanged.

### Deliverables

1. **Security Invariant Traceability (011):** canonical machine registry `docs/workforce/registries/security_invariant_traceability.jsonl` (35 rows, `INV-01`…`INV-35`) + human-readable `docs/security/SECURITY_INVARIANT_TRACEABILITY.md`. The canonical invariant text remains `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`; traceability rows reference, never restate it. Dimensional state fields (`implementation_state`, `automated_state`, `physical_state`, `external_state`) keep `SPECIFIED` / `IMPLEMENTED` / `TESTED` / `PHYSICALLY_VERIFIED` / `EXTERNALLY_VERIFIED` permanently distinct; evidence states map to B-027 E0–E4 without redefining them. Specification is never recorded as implementation or verification.
2. **B-021 verification architecture (026):** machine matrix `docs/workforce/registries/b021_verification_matrix.jsonl` — 150 stable test IDs (`ANOX-TEST-B0NN-MMM`, `ANOX-TEST-INV-NN`), nine execution classes (`REPO_STATIC`, `JVM_UNIT`, `RUST`, `ANDROID_EMULATOR`, `PHYSICAL_GRAPHENEOS`, `BACKEND_INTEGRATION`, `INFRA_DR`, `HUMAN_RELEASE_PROCEDURE`, `INDEPENDENT_AUDIT`), result model `PASS/FAIL/NOT_RUN/BLOCKED/NOT_APPLICABLE/UNVERIFIED` where `NOT_RUN`/`BLOCKED`/`UNVERIFIED` never count as PASS. All B-002…B-020 domains plus all 35 invariants covered; B-017 and B-020 have explicit rows; physical GrapheneOS/StrongBox rows are explicitly `UNVERIFIED`/`PHYSICAL_VERIFICATION_REQUIRED` (emulator evidence may not substitute). Pre-product gate and B-022/B-023 release gate are distinct consumers with different blocking rules.
3. **Release/signing/update/incident governance (024):** V1.3 §B-018 defines `K_APK_RELEASE` custody (human-only `ROLE-018`, AI/D4 prohibition, human-controlled signing, hash-bound artifact, recorded approval evidence, signing distinct from build), signing-environment requirements (isolation, least privilege, backup/recovery rehearsal, revocation/compromise, emergency rotation — no secrets or locations chosen), a deterministic update/downgrade trust state machine (`UPDATE_ACCEPT` … `ROLLBACK_AUTHORIZED`), and a human-gated emergency release path that can never let an incident self-authorize an AI release. V1.3 §B-019 defines the canonical incident/PSIRT artifact contract (vulnerability intake, `security.txt`, role-bound security contact, severity/triage, containment, credential/key compromise, malicious release, backend compromise, disclosure coordination, emergency update, post-incident review) bound to `ROLE-013/014/009/018/001/015/012` without duplicating role definitions.
4. **Branch-protection release gate (027):** V1.3 §B-023 records the honest current state — GitHub Free private repository has **no** server-side branch protection; the human-controlled remote workflow is a development-phase compensating control only. Deterministic release requirement: before RC/B-023 authorization, verified server-side protection OR an explicit recorded `ROLE-001` human decision approving an equivalent control (none exists; none fabricated). No GitHub configuration was changed. `HUMAN DECISION REQUIRED: NO` at this stage — technical protection is the default requirement; a decision is only needed if the project ever intends to release without it.
5. **Implementation-readiness state model (036):** three independent machine-checkable axes (`architecture_state`, `implementation_state`, `release_readiness`) in `docs/workforce/registries/implementation_readiness.json`. `B-004`/`B-005` = `FROZEN` + `NOT_STARTED` + `NOT_RELEASE_READY`. Architecture PASS is not implementation readiness.

### Finding lifecycle

All five targeted findings moved `Open` → `Ready For Retest` with remediation notes and evidence refs in `docs/workforce/registries/findings.jsonl`. **No finding was Closed by this task** (`CLOSED BY THIS TASK: NONE`); closure requires independent retest evidence under `MAINARCH-RETEST-03`.

### Milestone security review flags

`ANOX-MAINARCH-003` (server↔DB/RLS) and `ANOX-MAINARCH-007` (server↔backup/PITR) remain flagged; `ANOX-MAINARCH-024` is newly flagged (signing/release custody + incident-response trust boundary defined for the first time in V1.3).

### Constraints observed

No product code, Rust, Android, backend, SQL, Supabase, messaging, Device Auth, crypto, or `.so` changes. No CI workflow changes. No signing keys created or imported. No secrets touched. No GitHub repository/configuration changes. No remote mutation (no push, PR, merge, or polling). Architecture documentation is not product implementation. Product development remains `BLOCKED_PENDING_FINAL_AUDIT`. **CLAUDE AUDIT TRIGGERED: NO.**

### Validation

`tools/audit/validate_mainarch_fix03.py` enforces all remediation checks deterministically; `tools/audit/test_mainarch_fix03.py` provides targeted adversarial regression tests. See `docs/continuity/CURRENT_STATE.json` for the recorded validation set and commit pointers.

## MAINARCH-RETEST-03 — Targeted delta retest of FIX-03 findings

**Status:** PASS
**Mode:** READ-ONLY TARGETED DELTA RETEST
**Canonical retest SHA:** `88ea18c9b7078c376ee027d0cacc4d4f147ebbf5`
**FIX-03 canonical merge SHA:** `88ea18c9b7078c376ee027d0cacc4d4f147ebbf5` (substantive `4573b64dcc997aaaee8e81675a871201627d454e` + metadata `c81ed78aee82eabc816d858e03e01231f5b28461`)
**Original audit SHA:** `0a4910eab1a92622383721100879cda46f924ca0`
**Model:** Devin SWE-1.7 Max
**Retested findings:** 5
**Pass — Remediated:** 5/5
**Failures:** 0
**Regressions:** 0
**Not Reviewable:** 0
**Claude used:** NO

**Findings verified and Closed:**

- HIGH: ANOX-MAINARCH-011
- MEDIUM: ANOX-MAINARCH-024, ANOX-MAINARCH-026, ANOX-MAINARCH-027
- INFO: ANOX-MAINARCH-036

**Summary:**

Independent read-only targeted delta retest confirms the MAINARCH-FIX-03 traceability / test-matrix / release-governance / implementation-readiness remediation removed the original material defects for the 5 findings: all 35 Security Invariants are deterministically traced to authoritative source, domains, enforcement surfaces, verification IDs and evidence state with an explicitly non-collapsible spec/implementation/verification model; the B-021 matrix provides 150 unique stable test IDs covering B-002…B-020, B-021 self-check and all invariants with honest result semantics (NOT_RUN/BLOCKED/UNVERIFIED never count as PASS) and nine execution classes including physical GrapheneOS and independent audit; release signing is bound to human-only `ROLE-018`/`K_APK_RELEASE` with D4 secret prohibition, hash-bound artifacts, an 8-state update/downgrade trust machine and a human-gated emergency path; the B-019 incident/PSIRT artifact contract is defined role-bound without fabricated contacts; the B-023 branch-protection record is honest (no server-side protection exists today) with a deterministic release gate requiring verified enforcement or an explicit recorded `ROLE-001` decision; and the implementation-readiness registry separates architecture/implementation/release-readiness axes with B-004/B-005 recorded FROZEN + NOT_STARTED. Severities preserved. No product, Rust, backend, SQL, or CI changes. No material regression found. No Claude audit executed or required now.

**Validator observations (recorded, hardened in MAINARCH-RETEST-03-INGEST):**

- Release-governance checks were substring-based — semantics verified by manual inspection; deterministic cross-references added.
- Invariant `verification_ids` were not cross-validated for existence in the B-021 matrix — deterministic cross-check added.
- Worktree-vs-main scope/secret scan was inert post-merge — replaced by pinned base/substantive/metadata/merge SHA verification.

**Milestone security review coverage still pending:** ANOX-MAINARCH-003 (server ↔ DB/RLS), ANOX-MAINARCH-007 (server ↔ backup/PITR) and ANOX-MAINARCH-024 (signing/release custody + incident-response trust boundary) are Closed as *architecture remediation verified*; their trust boundaries remain scheduled (`PENDING`) for the next Security Architecture milestone review. This is not a Security Architecture Audit PASS.

**MAIN finding totals after closure:** Closed = 30, Remaining = 6 (ANOX-MAINARCH-013, 018, 019, 023, 030, 031). **MAIN ARCHITECTURE AUDIT = COMPLETE; MAIN ARCHITECTURE REMEDIATION PHASE = COMPLETE.** The remaining six findings are specialized Legacy / Build / Hardware verification items; `ANOX-MAINARCH-018` remains `PHYSICAL_VERIFICATION_REQUIRED`.

**Product development state:** `BLOCKED_PENDING_FINAL_AUDIT` (unchanged). Final Pre-Product Audit remains IN PROGRESS (AUDIT-WORKFORCE-ARCHITECTURE, AUDIT-SECURITY-ARCHITECTURE and the six legacy audits not executed).

**Next task:** first required specialized session per canonical `docs/workforce/audits/legacy-audit-plan.json` — `LEGACY-AUDIT-B002` (Legacy / Build / Hardware verification phase), pending human authorization.
## LEGACY-AUDIT-SET-FREEZE — Six-Session Legacy Audit Consolidation

**Status:** COMPLETE
**Mode:** READ-ONLY LEGACY FINDINGS FREEZE
**Canonical base SHA:** `f245dc429a9e4bd10f51692eb452d03ccb9a6749`
**Ending SHA (all six audits):** `f245dc429a9e4bd10f51692eb452d03ccb9a6749`
**Model:** `Devin SWE-1.7 Max`
**Run:** `ANOX-RUN-LEGACYFREEZE0001`
**Result:** PASS WITH FINDINGS
**Repository modified:** NO
**Remote mutation:** NONE
**Claude audit triggered:** NO

### Legacy audit set completion

All six canonical legacy audits were executed on the frozen base SHA:

1. `LEGACY-AUDIT-B002` — Device Authentication
2. `LEGACY-AUDIT-B003` — Account / License / Registration
3. `LEGACY-AUDIT-CRYPTO` — Cryptography / vodozemac / JNI
4. `LEGACY-AUDIT-ANDROID-SEC` — Android local security
5. `LEGACY-AUDIT-BUILD` — Build / supply chain / native artifacts
6. `LEGACY-AUDIT-INTEGRATION` — Cross-domain integration

**Set state:** 6 / 6 COMPLETE

### Existing MAIN findings revalidated

The six remaining Open MAIN findings were revalidated and remain Open:

- `ANOX-MAINARCH-013` — build/provenance (Class D)
- `ANOX-MAINARCH-018` — physical GrapheneOS/StrongBox verification (Class E, `PHYSICAL_VERIFICATION_REQUIRED`)
- `ANOX-MAINARCH-019` — Device Auth production eligibility not enforced (Class A)
- `ANOX-MAINARCH-023` — K_STATE read-path silent recreation (Class A)
- `ANOX-MAINARCH-030` — B-009/B-013 wipe/session persistence (Class C)
- `ANOX-MAINARCH-031` — JNI output-buffer error mapping (Class A)

### Promoted canonical Legacy findings

7 audit-local candidates were promoted to canonical Open findings:

- `ANOX-LEGACY-ANDROIDSEC-001` — API 26–32 KeyStoreException crash (HIGH, Class A)
- `ANOX-LEGACY-CRYPTO-005` — unsafe concurrent `&mut` native Identity/Session access (HIGH, Class A)
- `ANOX-LEGACY-INTEGRATION-001` — Device Auth key not re-verified before commit (HIGH, Class A)
- `ANOX-LEGACY-INTEGRATION-002` — OTK private state not persisted after generation (HIGH, Class A)
- `ANOX-LEGACY-INTEGRATION-003` — `CommitArmed` / binding-store divergence (MEDIUM, Class A)
- `ANOX-LEGACY-INTEGRATION-005` — native Identity handle leak (MEDIUM, Class F)
- `ANOX-LEGACY-B003-001` — UUIDv4 variant not verified (LOW, Class F)

### Candidate disposition summary

| Disposition | Count | Items |
|---|---|---|
| `PROMOTE_CANONICAL` | 7 | ANOX-LEGACY-B003-001, ANOX-LEGACY-CRYPTO-005, ANOX-LEGACY-ANDROIDSEC-001, ANOX-LEGACY-INTEGRATION-001, ANOX-LEGACY-INTEGRATION-002, ANOX-LEGACY-INTEGRATION-003, ANOX-LEGACY-INTEGRATION-005 |
| `MERGE_INTO_EXISTING` | 5 | ANOX-LEGACY-CRYPTO-001, ANOX-LEGACY-CRYPTO-002, ANOX-LEGACY-CRYPTO-003, ANOX-LEGACY-CRYPTO-004, ANOX-LEGACY-BUILD-001 |
| `DEFER_AS_FUTURE_WORK` | 3 | ANOX-LEGACY-B002-002, ANOX-LEGACY-CRYPTO-006, ANOX-LEGACY-CRYPTO-007 |
| `VERIFICATION_GAP_ONLY` | 1 | ANOX-LEGACY-CRYPTO-008 |
| `DOCUMENTATION_CLEANUP` | 1 | ANOX-LEGACY-B002-001 |
| `NOT_A_FINDING` | 2 | ANOX-LEGACY-BUILD-002, ANOX-LEGACY-INTEGRATION-006 |
| `REQUIRES_SCOPE_DECISION` | 1 | ANOX-LEGACY-INTEGRATION-004 |

### MAINARCH-030 current-vs-future decomposition

`ANOX-MAINARCH-030` is resolved as **Class C** (implement with B-008/B-009/B-013). The current `wipeLocalCrypto()` correctly removes the currently existing file-based crypto state. DB/WAL/SHM/attachments/temp, `preferred_session_id`, and per-peer session persistence are future Product implementation items, not current foundation defects.

### INTEGRATION-004 32-bit ABI scope decision

`ANOX-LEGACY-INTEGRATION-004` (missing 32-bit ABI `.so` artifacts) is **not auto-promoted**. `minSdk=26` is an API-level declaration, not a supported-CPU promise. The frozen product boundary names GrapheneOS (64-bit Pixel) as the primary V1 target. A human/scope decision is required before this becomes a release or build finding.

### Pre-B004 foundation blockers (Class A)

ANOX-MAINARCH-019, ANOX-MAINARCH-023, ANOX-MAINARCH-031, ANOX-LEGACY-ANDROIDSEC-001, ANOX-LEGACY-CRYPTO-005, ANOX-LEGACY-INTEGRATION-001, ANOX-LEGACY-INTEGRATION-002, ANOX-LEGACY-INTEGRATION-003

### Release blockers

ANOX-MAINARCH-013, ANOX-MAINARCH-018, ANOX-LEGACY-ANDROIDSEC-001

### Physical verification blockers

ANOX-MAINARCH-018

### Milestone security-review flags (preserved)

ANOX-MAINARCH-003, ANOX-MAINARCH-007, ANOX-MAINARCH-024

### Product development state

`BLOCKED_PENDING_FINAL_AUDIT` (unchanged). The next authorized task is `ANOX-TASK-LEGACYFIX01` — dependency-sorted remediation of the Class-A legacy blockers.

### Constraints observed

No product code, Rust, Android, backend, SQL, Supabase, messaging, Device Auth, crypto, or `.so` changes. No CI workflow changes. No signing keys created or imported. No secrets touched. No GitHub repository/configuration changes. No remote mutation. **CLAUDE AUDIT TRIGGERED: NO.**

### Consolidation artifacts

- `docs/workforce/registries/findings.jsonl` — existing Open MAIN findings updated; 7 canonical Legacy findings appended.
- `docs/workforce/registries/audits.jsonl` — 6 legacy audit records appended.
- `docs/workforce/schemas/audit-result.schema.json` — `PASS_WITH_FINDINGS` added to result enum.
- `docs/workforce/WORKFORCE_STATE.json` — legacy audit set 6/6 complete; next task recorded.
- `docs/reports/FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md` — full consolidation report.
- `tools/audit/consolidate_legacy_audit_set.py` — this one-time ingest script.
- `tools/audit/validate_legacy_audit_consolidation.py` — consolidation validator plus adversarial tests.

