# AUDIT EVIDENCE INDEX — Security Hardening Audit Preservation

**Preservation task:** `SECURITY-AUDIT-EVIDENCE-PRESERVATION-001`
**Event:** `ANOX-EVENT-0045`
**Audit base SHA:** `869b99acac040412a29bbaadc76342070fb2085c` (all Security Hardening wave audits)
**Purpose:** repository-contained, hash-verifiable preservation of completed audit evidence. **No security finding is fixed, closed, re-severitied, merged, or reinterpreted by this task.** Nothing here is a re-run of a completed audit.

## Preserved original reports (immutable evidence)

| Audit | Path | SHA-256 | Result | Model (actual) | Candidates |
|---|---|---|---|---|---|
| `AUDIT-SECURITY-ARCHITECTURE` (`ANOX-AUDIT-SECURITY-ARCH-001`) | `docs/reports/security/audits/AUDIT-SECURITY-ARCHITECTURE.md` | `da230ac1a3f623eba559c31641e52ffd2fc5487502d4c6ad2ccbbc1f9eb6dfe6` | PASS_WITH_FINDINGS | Claude Opus 5 High | 11 local (0C/5H/3M/2L/1I) → 10 canonical `ANOX-SECURITY-ARCH-*` |
| `AUDIT-SECURITY-CODEBASE-001` | `docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md` | `122d0aae9c1b64d060010092bea77f4d9c3466c5df2d10ccf56955bc4987f153` | PASS_WITH_FINDINGS | Claude Opus 5 Medium (requested: Fable 5.1 High — MODEL_DEVIATION disclosed, pending human disposition) | 21 (`ANOX-CODESEC-CANDIDATE-001..021` / `CS-001..021`; 1C/3H/8M/7L/2I) |
| `AUDIT-SECURITY-CODEBASE-002` (blind) | `docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-002.md` | `2ce279637bea62c79ced6614318c1fe79fcdc1b30b33519aeb7b2d426d4c09d5` | PASS_WITH_FINDINGS | Claude Fable 5.1 High | 17 (`ANOX-CODESEC2-CANDIDATE-001..017`; 0C/3H/6M/6L/2I) |
| `CODEBASE-SECURITY-CONSENSUS-001` | `docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md` | `66ea13d75982e83fdb9b316f3b95c0aef4b1fae9604d5e6457abb33e40898f8c` | PASS (final) | Claude Opus 5 High | 21/21 + 17/17 → 18 normalized Consensus Roots |
| `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001` | `docs/reports/security/audits/AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001.md` | `6afdd091d64ec9a30d40f8ba4e0fbe73bfb4812f105993bdbb42b49895acda1a` | PASS_WITH_FINDINGS | Claude Fable 5.1 High | 12 (`ANOX-BUILDSC-CANDIDATE-001..012`; 0C exploitability/3H/5M/3L/1I; 001 EVIDENCE_INTEGRITY=CRITICAL) |

`SOURCE_PRESENT = YES` for all five. Sources: the architecture report is the already-canonical repository file (identical bytes also remain at `docs/reports/FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT.md`); the other four are human-supplied files preserved byte-exact (no normalization; see `evidence_hashes.json`).

## Registry layer (structured interpretation — NOT the reports)

- `audit_registry.jsonl` — one record per audit (model attribution, SHA, result, candidate counts, blindness, lifecycle state).
- `audit_traceability.jsonl` — per-candidate consensus mappings (21/21 + 17/17), 18 consensus roots, 12 Build/Supply candidates, gate sets, historical relations, governance items.
- `evidence_hashes.json` — report SHA-256s + preserved reproduced native-artifact/APK hash evidence.
- `reproductions/README.md` — reproduced-evidence provenance and boundaries.

This directory is the **single canonical audit-evidence registry** for the Security Hardening wave. `docs/workforce/registries/audits.jsonl` remains the separate workforce-run registry and is not duplicated here; it records `ANOX-AUDIT-SECURITY-ARCH-001` as a workforce-run record — different layer, not a competing evidence registry.

## Consensus outcome (from CODEBASE-SECURITY-CONSENSUS-001)

- Final result: `PASS`; no remaining technical disputes.
- 18 normalized Consensus Roots `ROOT-001..018`. HIGH foundation roots: `ROOT-001` (EVIDENCE_INTEGRITY=CRITICAL), `ROOT-002`, `ROOT-003`, `ROOT-004`, `ROOT-005`.
- `ROOT-005` is `SINGLE_AUDIT_CONFIRMED_BY_ARBITER` — Audit-002-sourced only; **no Audit-001 source candidate exists and none may be fabricated**.
- `ROOT-016` is `REJECTED / NOT_A_FINDING` — must never be promoted to a real finding.
- `Audit-001 C-019` (unbounded resource allocation / panic-abort) exists and splits across `ROOT-008` + `ROOT-014`.
- Finalized Pre-B004 root set (12): `ROOT-001, 002, 003, 004, 005, 006, 007, 008, 009, 013, 014, 017`.
- B008/B009 set (3): `ROOT-010, 011, 012`. Final Product Gate (2): `ROOT-012, 015` + retest of all Pre-B004 roots on a provenance-verified binary. Release Candidate: `ROOT-018` + supply-chain/release controls.

## Build/Supply audit outcome (AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001)

- `ANOX-BUILDSC-CANDIDATE-001`: committed `.so` proven byte-identical to a rebuild of old Rust source at `7db20fa` — **EVIDENCE_INTEGRITY = CRITICAL**.
- Reproduced hashes: committed arm64 `11a958a5…`, x86_64 `ecf9fdc1…`; current-source rebuild arm64 `05f3f40c…`, x86_64 `c002cc42…`; debug APK `f202c5e1…`; release unsigned APK `72075487…` (full values in `evidence_hashes.json`).
- Pre-B004 blockers: `001` (by dependency), `002`, `003`, `007`, `010`, doc-correction half of `004`.
- Native-retest acceptance blockers: `001`, `006`, `008` (+ `002` as enabling condition).
- Release-candidate blockers: `001`–`010`. Deferred: `011`, `012`.
- Remediation order: toolchain pinning → CI native cross-build + reproducibility + JNI symbol test + native manifest → Gradle consumes build output / committed `.so` transition → instrumented JNI CI → lint/audit/secret-scan + policy-doc fix → native retests on provenance-verified binary → RC controls → human signing.

## Historical relations preserved (no rewrites)

- `ANOX-LEGACY-CRYPTO-005` — remains **Closed**; relationship `LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION` (Kotlin `cryptoLock` inert via CS-001/C-004; native concurrency never exercised on a current-source binary; `EVIDENCE_REVALIDATION_REQUIRED_AFTER_PROVENANCE_FIX`). **Not reopened.**
- `ANOX-LEGACY-INTEGRATION-005` — remains **Open**; relationship `NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING` (ROOT-003/ROOT-014).
- `ANOX-MAINARCH-031` — remains **Closed**; Rust half of its fix is not in the shipped artifact (flagged for consolidation, not reopened here).
- `ANOX-MAINARCH-013` — remains **Open**, expanded; its "byte-identical rebuild" note is superseded.
- `ANOX-MAINARCH-018` — **PHYSICAL_VERIFICATION_REQUIRED** unchanged; pre-rebuild physical evidence must be re-collected.
- `ANOX-SECURITY-ARCH-001/008` — Open, expanded by this wave; retest requires provenance-verified binary.
- `ANOX-LEGACY-B003-001` — Open; same root-cause family as `ROOT-015`.
- Historical validator lifecycle mismatches (`CS-021` / `ANOX-CODESEC2-CANDIDATE-017`) are `GOVERNANCE_ONLY` / `HISTORICAL_SHA_PINNED_VALIDATOR`, not product-security failures; pending human decision.

## Lifecycle state (unchanged by this task)

- Product Development: `BLOCKED_PENDING_FINAL_AUDIT`
- B-004: `NOT_STARTED` · B-005: `NOT_STARTED`
- Next gate: `AUDIT-SECURITY-CRYPTO-JNI-001` — **CANDIDATE / NOT_EXECUTED** (then AUTH/DPOP, ANDROID/STORAGE, ATTACKCHAIN specialists; then consolidation, remediation sessions, independent retests; only then B-004)

## Validator

`tools/audit/validate_security_audit_evidence_preservation.py` — fail-closed on altered/deleted/incomplete evidence or invalid lifecycle state. Adversarial tests: `tools/audit/test_security_audit_evidence_preservation.py`.
