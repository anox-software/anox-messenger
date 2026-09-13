# AUDIT EVIDENCE INDEX — Security Hardening Audit Preservation

**Preservation tasks:** `SECURITY-AUDIT-EVIDENCE-PRESERVATION-001` (`ANOX-EVENT-0045`), `SECURITY-AUDIT-EVIDENCE-PRESERVATION-002` (`ANOX-EVENT-0046`), `SECURITY-AUDIT-EVIDENCE-PRESERVATION-003` (`ANOX-EVENT-0047`)
**Audit base SHA:** `869b99acac040412a29bbaadc76342070fb2085c` (Security Hardening wave audits); `a79166ab7e65db71ba70e3a427df2ad017dc9225` (`AUDIT-SECURITY-CRYPTO-JNI-001`); `638e63a22c91ca81365bf55c8a59ec47878dd7fd` (`AUDIT-SECURITY-AUTH-DPOP-001`)
**Purpose:** repository-contained, hash-verifiable preservation of completed audit evidence. **No security finding is fixed, closed, re-severitied, merged, or reinterpreted by this task.** Nothing here is a re-run of a completed audit.

## Preserved original reports (immutable evidence)

| Audit | Path | SHA-256 | Result | Model (actual) | Candidates |
|---|---|---|---|---|---|
| `AUDIT-SECURITY-ARCHITECTURE` (`ANOX-AUDIT-SECURITY-ARCH-001`) | `docs/reports/security/audits/AUDIT-SECURITY-ARCHITECTURE.md` | `da230ac1a3f623eba559c31641e52ffd2fc5487502d4c6ad2ccbbc1f9eb6dfe6` | PASS_WITH_FINDINGS | Claude Opus 5 High | 11 local (0C/5H/3M/2L/1I) → 10 canonical `ANOX-SECURITY-ARCH-*` |
| `AUDIT-SECURITY-CODEBASE-001` | `docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md` | `122d0aae9c1b64d060010092bea77f4d9c3466c5df2d10ccf56955bc4987f153` | PASS_WITH_FINDINGS | Claude Opus 5 Medium (requested: Fable 5.1 High — MODEL_DEVIATION disclosed, pending human disposition) | 21 (`ANOX-CODESEC-CANDIDATE-001..021` / `CS-001..021`; 1C/3H/8M/7L/2I) |
| `AUDIT-SECURITY-CODEBASE-002` (blind) | `docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-002.md` | `2ce279637bea62c79ced6614318c1fe79fcdc1b30b33519aeb7b2d426d4c09d5` | PASS_WITH_FINDINGS | Claude Fable 5.1 High | 17 (`ANOX-CODESEC2-CANDIDATE-001..017`; 0C/3H/6M/6L/2I) |
| `CODEBASE-SECURITY-CONSENSUS-001` | `docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md` | `66ea13d75982e83fdb9b316f3b95c0aef4b1fae9604d5e6457abb33e40898f8c` | PASS (final) | Claude Opus 5 High | 21/21 + 17/17 → 18 normalized Consensus Roots |
| `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001` | `docs/reports/security/audits/AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001.md` | `6afdd091d64ec9a30d40f8ba4e0fbe73bfb4812f105993bdbb42b49895acda1a` | PASS_WITH_FINDINGS | Claude Fable 5.1 High | 12 (`ANOX-BUILDSC-CANDIDATE-001..012`; 0C exploitability/3H/5M/3L/1I; 001 EVIDENCE_INTEGRITY=CRITICAL) |
| `AUDIT-SECURITY-CRYPTO-JNI-001` (specialist) | `docs/reports/security/audits/AUDIT-SECURITY-CRYPTO-JNI-001.md` | `c7367e3419b709d9675b16ddcf1fee23fd114283482523ee036be99e4ecc836b` | PASS_WITH_FINDINGS | Claude Fable 5.1 High (requirement SATISFIED; first-reply mislabel retracted before analysis) | 6 (`ANOX-CRYPTOJNI-CANDIDATE-001..006`; 0C/1H/3M/1L/1I) + 6 consensus roots confirmed/expanded |
| `AUDIT-SECURITY-AUTH-DPOP-001` (specialist) | `docs/reports/security/audits/AUDIT-SECURITY-AUTH-DPOP-001.md` | `57516d7d47e56447b7ab7a91aadaa2b7c3acdeda71e572b2b4366d2a6526b18e` | PASS_WITH_FINDINGS | Claude Fable 5.1 High (requirement SATISFIED) via Devin CLI (Cognition) session runtime | 3 (`ANOX-AUTHDPOP-CANDIDATE-001..003`; 0C/0H/1M/2L/0I) + 3 architecture gaps (`ANOX-AUTHDPOP-GAP-001..003`) + 4 consensus roots confirmed (008/009 expanded) |

`SOURCE_PRESENT = YES` for all seven. Sources: the architecture report is the already-canonical repository file (identical bytes also remain at `docs/reports/FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT.md`); the codebase/consensus/build-supply reports are human-supplied files preserved byte-exact; the Crypto/JNI and Auth/DPoP reports are byte-exact final report bodies emitted by the authorized specialist audit sessions (no normalization; see `evidence_hashes.json`).

## Registry layer (structured interpretation — NOT the reports)

- `audit_registry.jsonl` — one record per audit (model attribution, SHA, result, candidate counts, blindness, lifecycle state).
- `audit_traceability.jsonl` — per-candidate consensus mappings (21/21 + 17/17), 18 consensus roots, 12 Build/Supply candidates, 6 Crypto/JNI + 3 Auth/DPoP specialist candidates, 3 Auth/DPoP architecture gaps, gate sets, historical relations/revalidation, governance items.
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

## Crypto/JNI specialist audit outcome (AUDIT-SECURITY-CRYPTO-JNI-001)

- Result: `PASS_WITH_FINDINGS` at audited SHA `a79166ab7e65db71ba70e3a427df2ad017dc9225`; 6 audit-local candidates `ANOX-CRYPTOJNI-CANDIDATE-001..006` (0C/1H/3M/1L/1I).
- Consensus roots: `ROOT-002`, `ROOT-014` **CONFIRMED**; `ROOT-003`, `ROOT-004`, `ROOT-005`, `ROOT-010`, `ROOT-013` **CONFIRMED_AND_EXPANDED**; `ROOT-011` confirmed (adjacent, no expansion). No new root IDs assigned; candidates only.
- `ROOT-013` severity overlay `LOW → MEDIUM (proposed)` recorded as `PENDING_SPECIALIST_CONSOLIDATION` — consensus severity not overwritten.
- **JNI ABI revision required** (`JNI_ABI_REVISION=YES`, verdict `COMPONENT_INTERNAL_REDESIGN_ONLY`, SEC-C not required): slot+generation handles with owning locks; disjoint error taxonomy incl. `HANDLE_*` family; native-allocated output buffers; KeyId-based OTK surface with publication/ACK support.
- Measured evidence (temporary, current-source only): Identity pickle 20 OTK = 5269–5287 B > 4096 fixed buffer; Session ≈ 29.9 KB bounded max; OTK index enumeration duplicated in 20/20 sweeps (worst 10/20 unique); same-size-class handle address reuse 7/100 host trials; independent temp rebuild reproduced identical current-source hashes (`05f3f40c…`/`c002cc42…`) — committed `.so` still stale (ROOT-001 unresolved).
- Evidence-method correction recorded: string-presence heuristic is not discriminating (LTO strips `"Output buffer too small"` in both binaries); use disassembly/runtime.
- Host `cargo test` 17/17 pass (JNI cfg-gated out); JNI runtime tests `NOT_RUN` (no approved runtime environment).
- Pre-B004 Crypto/JNI gate set (8): `ROOT-002, 003, 004, 005, 013, 014, CANDIDATE-001, CANDIDATE-003`. B008/B009 gate set (5): `CANDIDATE-002, 004, 005, ROOT-010, ROOT-011`. Final-gate: native retests on provenance-verified binary, instrumented-JNI CI (ROOT-017), CANDIDATE-006 hygiene.

## Auth/DPoP specialist audit outcome (AUDIT-SECURITY-AUTH-DPOP-001)

- Result: `PASS_WITH_FINDINGS` at audited SHA `638e63a22c91ca81365bf55c8a59ec47878dd7fd`; 3 audit-local candidates `ANOX-AUTHDPOP-CANDIDATE-001..003` (0C/0H/1M/2L/0I) + 3 architecture gaps `ANOX-AUTHDPOP-GAP-001..003`.
- Coverage: B-002 production files 29/29 (100%); relevant test files 14/14 (100%); architecture coverage matrix 40 requirements, 0 unmapped (15 IMPLEMENTED_AND_VERIFIED / 7 IMPLEMENTED_NOT_VERIFIED / 6 PARTIALLY_IMPLEMENTED / 6 IMPLEMENTATION_DRIFT / 3 MISSING / 3 NOT_APPLICABLE_YET / 2 PHYSICAL_VERIFICATION_REQUIRED).
- Test counts are distinct: focused relevant test inventory = 155 (JVM 128, instrumented 27, physical 0, CI-executed 128); actual audit execution = 173/173 PASS (deviceauth 69 + account 104). Instrumented + physical NOT_RUN.
- Consensus roots: `ROOT-006`, `ROOT-007` CONFIRMED; `ROOT-008`, `ROOT-009` CONFIRMED_AND_EXPANDED. `ROOT-016` remains REJECTED (CANDIDATE-002 is a pre-binding race, not destruction of a bound key). No new root IDs assigned; no re-severity.
- Pre-B004 set: `ROOT-006`, `ROOT-007`, `ROOT-008`, `ROOT-009` (already in the 12-root set) + `ANOX-AUTHDPOP-CANDIDATE-001` + `ANOX-AUTHDPOP-GAP-001/002/003` (contract freeze before B-004 implementation).
- Later-gate items: `CANDIDATE-002` (AD-A, NON_BLOCKING), `CANDIDATE-003` (B-004 backend verifier; contract entry in GAP-002), `ANOX-MAINARCH-018` physical, logout/wipe/revoke (B-013), instrumented CI (ROOT-017).
- Remediation groups `AD-A`..`AD-F`; SEC verdict: `COMPONENT_INTERNAL_REDESIGN_ONLY`, SEC-C **not** required. Fix-coupling (MUST_FIX_TOGETHER / MUST_NOT_FIX_ALONE) recorded.
- Historical revalidation preserved: `ANOX-LEGACY-INTEGRATION-001` PARTIALLY_EFFECTIVE (Closed, not reopened); `ANOX-SECURITY-ARCH-007` INEFFECTIVE_REMEDIATION_SCOPE (RegistrationSessionKey create-on-read persists → ROOT-006); `ANOX-SECURITY-ARCH-003` expanded; `ANOX-MAINARCH-018` PHYSICAL_REVALIDATION_REQUIRED unchanged.
- Handoffs recorded: `ANDROID/STORAGE` (ROOT-006/007 + persisted-binding durability) and `ATTACKCHAIN` (5 chained combinations) — both remain CANDIDATE / NOT_EXECUTED.

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
- `AUDIT-SECURITY-CRYPTO-JNI-001`: **EXECUTED + PRESERVED** (`ANOX-EVENT-0046`) — PASS does NOT unblock product development.
- `AUDIT-SECURITY-AUTH-DPOP-001`: **EXECUTED + PRESERVED** (`ANOX-EVENT-0047`) — PASS does NOT unblock product development.
- Next gate: `AUDIT-SECURITY-ANDROID-STORAGE-001` — **CANDIDATE / NOT_EXECUTED** (then ATTACKCHAIN specialist; then consolidation, remediation sessions, independent retests; only then B-004)

## Validator

`tools/audit/validate_security_audit_evidence_preservation.py` — fail-closed on altered/deleted/incomplete evidence or invalid lifecycle state; extended under PRESERVATION-002 to cover the Crypto/JNI report, candidates, provenance limitation, temp-build evidence, ABI-revision record, and under PRESERVATION-003 to cover the Auth/DPoP report, candidates/gaps, consensus relations, coverage/test evidence, remediation coverage, handoffs, and the Android/Storage not-executed gate. Adversarial tests: `tools/audit/test_security_audit_evidence_preservation.py`.
