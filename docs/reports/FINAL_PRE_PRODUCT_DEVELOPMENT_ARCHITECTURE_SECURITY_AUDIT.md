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
