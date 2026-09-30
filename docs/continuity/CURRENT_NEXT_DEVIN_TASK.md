# CURRENT_NEXT_DEVIN_TASK — anoX V1

## S2-C01 pre-authorization anchor — S2-C01-PREAUTHORIZATION-001 (2026-09-30)

**Delivery:** `governance/s2-c01-preauthorization-001`, canonical base `02179ecd34fde81a0cc8866a09653cab8ff40f38` (verified `main` = `origin/main`; PR #40 merge).
**Decision:** `ANOX-DECISION-S2-C01-PREAUTHORIZATION-001` — Human Product & Security Owner, ONE_TIME_CHANGE_SPECIFIC, recorded in `docs/workforce/registries/decisions.jsonl`.
**Anchor:** `ANOX-TASK-S2-CORRECTION-001` is canonically registered in `docs/workforce/registries/tasks.jsonl` on this delivery, binding `remediation/s2-correction-001`, `start_sha 02179ecd…` and its reviewed allowed/forbidden path scope. This is the non-self-mintable pre-delivery authorization anchor required to close review finding C-01/R09.
**Next task:** the authorized C-01 correction on `remediation/s2-correction-001` — bind the protected-Rust authorization in `tools/audit/validate_s1_build_provenance.py` to this pre-delivery canonical evidence. Effective only after this governance delivery passes review and the Human remote/merge gate to `main`. No implementation, no validator change, no remote mutation here.
**Event:** `ANOX-EVENT-0054` remains the last sealed canonical event. This record does not append an event.

The S2 scope freeze below remains the canonical scope-freeze record from `S2-BOOTSTRAP-LIFETIME-GOVERNANCE-AND-SCOPE-FREEZE-001` (merged via PR #40). It is derived planning/continuity metadata, not a competing security Authority or a mutation of preserved audits/findings. Security semantics defer to `docs/authority/AUTHORITY_INDEX.md` and its indexed Authorities (including V1.4 for S0 contracts).

## S2 scope freeze — S2-BOOTSTRAP-LIFETIME-GOVERNANCE-AND-SCOPE-FREEZE-001

**S2_SCOPE_SELECTION = FROZEN — REPOSITORY_VERIFIED** (2026-09-27).
**Verification base:** `cb9aee039bd2816c38c11a5e9084be56aa8cde15`, verified clean `main` = `origin/main`, normal PR #38/#39 merges in ancestry.
**Delivery:** `remediation/s2-lifetime-and-scope-001`; governance checkpoint `60f42b0ac99c62e71a0bacd69a294a7eb2bc3c3a` (merged via PR #40 at `02179ecd34fde81a0cc8866a09653cab8ff40f38`).
**Event:** `ANOX-EVENT-0054` remains the last sealed canonical event. This freeze does not append an event or relabel the historical event as S2.

## Selection and execution boundaries

Primary S2 implementation units: **MSC_UNIT_005, 006, 007, 008, 009, 010, 011**.
Additional explicitly assigned S2 slices: **012 code, 013 input cap, 014 CryptoBridge half, 015 crypto consumer, 016 CryptoBridge writeFileAtomic, 019 crypto AAD hook**. These are 13 OPEN MSC records touched by the planned S2 code scope, not 13 units authorized for closure. The other halves and later closure gates are excluded below.

Selection comes from the verified Master report §PROVISIONAL LARGE FIX SESSIONS / S2 and the verified Coverage Gate §EXECUTION SESSION COVERAGE / S2 plus §FILE OWNERSHIP, not numeric ordering. Required order: **005 → 007 → 006 → 009/010/011 (+012 code, 013 cap, 019 hook; AS-C 014/015/016) → 008 LAST**. The coupling groups 005∧006∧007∧008 and 009∧010∧011 remain intact. Cleanup must not precede safe handle identity/ownership. No larger-buffer-constant-only or singleton-only closure.

S0 contract evidence is preserved and merged at `29a6643189242a47c4a79c38acd04c1eca748787`; targeted correction retest PASS_WITH_FINDINGS, zero merge blockers, two residual LOW follow-ups. S1 implementation is COMPLETE/MERGED at `2dc6b7453ef292c30f32c02e0eb213e1ef5496cb` (PR #38), integrated delivery `3ed46b717172d512f75672c83d58327a52ac3c61`; post-S1 continuity merged at the verification base (PR #39). The S1 build/provenance infrastructure exists; x86_64 instrumented CI is recorded EXECUTED_AND_PASS. **ARM64 remains UNVERIFIED_PENDING_REAL_ARM64_RUNTIME**. The four S1 stage-overlay records still have pending runtime/retest/preservation/closure stages; no missing evidence is promoted by this freeze. Before implementation/acceptance, the new task must bind its fresh canonical start SHA, verify the required S1 CI-built source/hash/artifact evidence and independent predecessor retest/preservation gates. This scope record is not proof those runtime/closure prerequisites passed and is not a Product gate waiver.

S2 owns `crypto/rust/src/*`, the CryptoBridge/CryptoNative/CryptoError implementation and its focused crypto tests, `CryptoBridgeLocalE2eeIdentityStep.kt`, `CryptoInstrumentedTest.kt`, and the canonical module/visibility split contemplated by the Coverage Gate. Resolve exact current paths in the implementation task. S2 does not own other Android registration/storage or DPoP files; no backend/Supabase/SQL, B004/B005, S3/S4 or physical campaign implementation is authorized here. The later task must bind any module-split build-file edits explicitly; a conceptual module split is not blanket build/CI authority. S2/S3 file ownership is disjoint; S3 consumes the typed crypto surface without writing CryptoBridge. S3 → S4 remains sequential for RegistrationOrchestrator.

Current path existence was checked (not a new code audit): `crypto/android/src/main/java/com/anox/crypto/CryptoBridge.kt`, `CryptoNative.kt` and `CryptoError.kt` in that directory; `android/src/main/java/com/anox/messenger/account/CryptoBridgeLocalE2eeIdentityStep.kt`; `crypto/android/src/androidTest/java/com/anox/crypto/CryptoInstrumentedTest.kt`. The affected `android/src/main/java/com/anox/messenger/account/PublicE2eeIdentityMaterial.kt` also exists; MASTER 010 lists it as affected, while GATE limits Android writes to the identity step. Affected-code traceability is not writable-path authority: any necessary edit to that DTO must be explicitly resolved in the next Human-authorized task rather than silently broadening the frozen file partition.

## Verified source-report inventory

Canonical registry: `docs/security/audit-evidence/audit_registry.jsonl`; index: `docs/security/audit-evidence/AUDIT_EVIDENCE_INDEX.md`. Each report below exists and its recomputed SHA-256 **equals** the registered value shown (expected = actual, PASS). Hashes are byte-level verification, not new audit execution. Source labels in the matrix resolve to these paths and sections.

| Label | Registry audit/artifact | Report path | Expected = actual SHA-256 |
|---|---|---|---|
| ARCH | ANOX-AUDIT-SECURITY-ARCH-001 | docs/reports/security/audits/AUDIT-SECURITY-ARCHITECTURE.md | da230ac1a3f623eba559c31641e52ffd2fc5487502d4c6ad2ccbbc1f9eb6dfe6 |
| A1 | AUDIT-SECURITY-CODEBASE-001 | docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md | 122d0aae9c1b64d060010092bea77f4d9c3466c5df2d10ccf56955bc4987f153 |
| A2 | AUDIT-SECURITY-CODEBASE-002 | docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-002.md | 2ce279637bea62c79ced6614318c1fe79fcdc1b30b33519aeb7b2d426d4c09d5 |
| CONS | CODEBASE-SECURITY-CONSENSUS-001 | docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md | 66ea13d75982e83fdb9b316f3b95c0aef4b1fae9604d5e6457abb33e40898f8c |
| BUILD | AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001 | docs/reports/security/audits/AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001.md | 6afdd091d64ec9a30d40f8ba4e0fbe73bfb4812f105993bdbb42b49895acda1a |
| CJ | AUDIT-SECURITY-CRYPTO-JNI-001 | docs/reports/security/audits/AUDIT-SECURITY-CRYPTO-JNI-001.md | c7367e3419b709d9675b16ddcf1fee23fd114283482523ee036be99e4ecc836b |
| AD | AUDIT-SECURITY-AUTH-DPOP-001 | docs/reports/security/audits/AUDIT-SECURITY-AUTH-DPOP-001.md | 57516d7d47e56447b7ab7a91aadaa2b7c3acdeda71e572b2b4366d2a6526b18e |
| AS | AUDIT-SECURITY-ANDROID-STORAGE-001 | docs/reports/security/audits/AUDIT-SECURITY-ANDROID-STORAGE-001.md | 7532877dd14b97011d19f0b07a79bb50e529e4130feb0226c242b60d3e995720 |
| AC | AUDIT-SECURITY-ATTACKCHAIN-001 | docs/reports/security/audits/AUDIT-SECURITY-ATTACKCHAIN-001.md | a4feac55f49066647ec0c1665c40deab581115da4b102e81eb6742e72b80ca9e |
| MASTER | MASTER-SPECIALIST-CONSOLIDATION-001 / SEC-AUDIT-REG-0010 | docs/reports/security/consolidation/MASTER-SPECIALIST-CONSOLIDATION-001.md | a22c779833e6334067405ebd158f1cbadeee5dc51d9b7795c31ef12758060b00 |
| GATE | SECURITY-REMEDIATION-COVERAGE-GATE-001 / SEC-AUDIT-REG-0011 | docs/reports/security/gates/SECURITY-REMEDIATION-COVERAGE-GATE-001.md | 175aa756fa1a260311c3d8b3c3680aa26de38d58bd2d8ebb782320cc27e2b27e |
| HUMAN | HUMAN-PRE-REMEDIATION-DECISIONS-001 / SEC-AUDIT-REG-0012 | docs/reports/security/decisions/HUMAN-PRE-REMEDIATION-DECISIONS-001.md | d558471dee257b80540e0bc21d2204470402ab9f44234a7e8e0208dc96ef2b13 |
| S0 | SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001 / SEC-AUDIT-REG-0013 | docs/reports/security/remediation/SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001.md | 995b4006c96ee53646c78fe93e70ea5d79d99d5a7eab565f997f513a8d3868f8 |

Nested `preserved_sources` in SEC-AUDIT-REG-0013 also rehashed PASS: implementation/correction `docs/reports/security/remediation/REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md` = `19cb339f398c4bd9b702a1442ea21d0bf96ffc57ed97ff351d9b49c1eed9484a`; first retest `docs/reports/security/retests/INDEPENDENT-ARCHITECTURE-RETEST-S0-001.md` = `fb2f4b8cb83b6b812dfb3656d9f6b1b0c2541b8f9b1af22c55787422e4fa5d29` (Human-authorized reconstruction, not original verbatim evidence); targeted retest `docs/reports/security/retests/TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001.md` = `67cb2c152c234397fe94259207492263200123db6acd07e2d97f80ecb5d5b951`.

## Canonical cross-check conventions and supersession

- Finding registry: `docs/workforce/registries/findings.jsonl` (56 records: 41 Closed, 15 Open). Selected architecture references ARCH-001/003/007/008 are canonical `ANOX-SECURITY-ARCH-*` records, still Open at HIGH/HIGH/MEDIUM/LOW respectively; no severity is changed here. `ANOX-LEGACY-INTEGRATION-005` remains Open/MEDIUM.
- Traceability: `docs/security/audit-evidence/audit_traceability.jsonl`. Canonical consensus/candidate findings live in its `consensus_root`, specialist-candidate and `msc_source_item` layers; no nonexistent workforce finding ID is invented for a ROOT or specialist candidate. Each MSC selection resolves its `msc_unit` by `msc_unit_id`, its `gate_coverage_unit` by `msc_unit`, and the GATE execution-session/file-ownership records. MASTER §MSC UNIT TABLE and GATE §42-ROW OPEN MSC COVERAGE MATRIX were compared with those records.
- MSC universe: 44 `msc_unit` records = 42 OPEN_PENDING_REMEDIATION_COVERAGE_GATE + 2 REJECTED_NOT_A_FINDING. `docs/security/remediation/msc_state.jsonl` is an overlay containing only 001/002/003/038. All 13 selected records have **no stage overlay and remain OPEN; implementation NOT_STARTED**. Underscore/hyphen spellings denote the same numbered unit per the existing MSC validator, not newly allocated IDs.
- Every selected source label below has SHA PASS in the inventory above. A1 references mean its §NEW FINDINGS TABLE; A2 references mean its §INDEPENDENT FINDINGS TABLE; CJ candidates mean §FINDINGS TABLE; AS ROOT sections and §FINDINGS TABLE provide the named expansions. CONS §§2–5 preserves normalization/arbitration; MASTER §MSC UNIT TABLE gives the complete source→unit chain; GATE's S2 row and file partition resolve placement.
- `ROOT-013` historical LOW and CJ/MASTER MEDIUM proposals are superseded by HUMAN §R1 / `ANOX-DECISION-HUMANPREREMEDIATION001` / `canonical_severity_transition` at ANOX-EVENT-0052: current MEDIUM, OPEN. ARCH-008 stays LOW/Open; these are distinct records, not conflicting severities.
- CONS arbitration supersedes A2's lower severity/later activation of ROOT-002/003/006 and A1's unsupported escalation recommendations. ROOT-005 is A2-only plus arbiter/specialist confirmation; **no direct A1 candidate exists**.
- Closed historical findings (LEGACY-CRYPTO-005, LEGACY-ANDROIDSEC-001, LEGACY-INTEGRATION-002, MAINARCH-023/031) remain Closed. Later source reports establish ineffective/partial remediation or related current roots; MASTER §HISTORICAL REMEDIATION ARBITRATION and current finding notes preserve those relations without reopening history.
- GATE §42-row resolutions explicitly treats 005's machine `architecture_prerequisites` 007/008 as code coupling, not missing S0 contracts. GATE session/file partition resolves shared-unit ownership. Later code/closure splits for 012/013 and 014/015/016/019 are intentional, not permission to promote later milestones.
- HUMAN H2 accepts A1's disclosed model deviation; H1 retires the named one-shot validators but not security controls; H3 keeps ARCH-010 Open/INFO until B004 start. Protected S0 shared-validator decisions are one-time and grant no new event numbers. All historical evidence remains unchanged.

## Per-unit finding cross-check matrix

All entries below inherit the exact registry paths, current OPEN/no-overlay state, source SHA PASS and source-section conventions above. Dependency numbers refer to MSC_UNIT records; dependencies inside S2 are ordered work, not already completed fixes. MFT = must fix together; MNFA = must not fix alone. Empty physical requirements mean none for that unit, not waiver of a coupled unit's physical campaign.

### MSC_UNIT_005 — JNI handle identity/ownership/synchronization (slot+generation, owning lock)

- Severity HIGH; root ROOT-003 (ACTIVE). Sources: ROOT-003, ANOX-SECURITY-ARCH-001, ANOX-LEGACY-INTEGRATION-005, ANOX-LEGACY-CRYPTO-005, A1 CS-002, A2 C-005; ARCH §Final canonical finding set; CJ §ROOT-003 / HANDLE SAFETY VERDICT. Raw-address identity, check-then-deref, aliasing and address reuse are the normalized root.
- Architecture/code: Inv.23; `crypto/rust/src/lib.rs` handle registry/use/destroy. Fix group CJ-A. Placement: MASTER S2; GATE row 005 S2 order 1. Activation PRE_B004 (B004 multi-instance / B008 concurrency).
- Dependency 001: infrastructure merged, native acceptance evidence still required. MFT 005∧008∧007∧006; MNFA cleanup 008 before safe 005. 007/008 are coupling requirements, not S0 prerequisites (GATE resolution).
- Automated: host-testable slab registry, generation bump, stale rejection, no free during in-flight use. Instrumented: destroy/reallocate/stale → HANDLE_STALE_GENERATION; concurrent encrypt/serialize serialized on provenance-verified binary. Physical: none.
- Independent retest: Crypto/JNI separate session via 037; closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-006), with preserved hash-bound evidence/FCP stages.

### MSC_UNIT_006 — Process-global CryptoBridge singleton + CryptoNative visibility narrowing

- Severity HIGH; root ROOT-002 (ACTIVE). Sources: ROOT-002, A2 C-014 (locking component), A1 CS-001/CS-102, A2 C-004, ANOX-LEGACY-CRYPTO-005; CJ §ROOT-002 / CRYPTOBRIDGE SINGLETON / CRYPTONATIVE BYPASS. Unassigned singleton produces per-instance locks and repeated initialization.
- Architecture/code: LKSL §O; `CryptoBridge.kt`, `CryptoNative.kt`, module layout. Group CJ-E; MASTER S2 / GATE 006 S2 order 3; PRE_B004.
- Dependency 005 OPEN/planned first; coupled 005/007/008 group. MNFA singleton-only fix while direct native bypass remains unsafe; closure requires 005.
- Automated: assertSame on getInstance, initialize once, compile-level app-module CryptoNative invisibility. Instrumented: no separate requirement, provenance/runtime through 005. Physical: none.
- Retest Crypto/JNI; closure SOURCE_DIFF + UNIT_TEST + INDEPENDENT_SPECIALIST_RETEST + AC-011 attackchain retest, coupled provenance evidence and all required FCP stages.

### MSC_UNIT_007 — JNI error taxonomy / status channel + LocalStateStatus consumer

- Severity MEDIUM; ROOT-013 current MEDIUM/OPEN by HUMAN R1. Sources: ROOT-013, ANOX-CRYPTOJNI-CANDIDATE-003/006, ANOX-SECURITY-ARCH-008, A1 CS-013/017, A2 C-012, ANOX-MAINARCH-031, ANOX-LEGACY-ANDROIDSEC-001; CJ §ROOT-013 / ERROR MAPPING TABLE / candidates 003/006; AS §CORRUPTION TAXONOMY. Non-injective codes and pointer-or-zero lose security-relevant failure classes.
- Architecture/code: Inv.23; `error.rs`, `lib.rs`, `CryptoError.kt`, `CryptoBridge.kt` LocalStateStatus/error classification. Groups CJ-B/AS-C; MASTER S2 / GATE 007 S2 order 2; PRE_B004.
- Dependency 005 OPEN/planned first. MFT 007∧005 and 007∧015 consumer. MNFA deserialize codes without consumer change; no string-presence provenance heuristic.
- Automated: injective native-condition/code table, unsupported-version distinct from corruption, missing master key → MissingKeystore. Instrumented: negative JNI path per code on verified binary. Physical: none.
- Retest Crypto/JNI + Android/Storage consumer; closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST; GATE additionally requires AC-006 part/chain stage. No mutation of ARCH-008 severity.

### MSC_UNIT_008 — Native handle lifetime / cleanup / registry bounds

- Severity MEDIUM; ROOT-014 ACTIVE. Sources: ROOT-014, ANOX-LEGACY-INTEGRATION-005, A1 CS-012/019, A2 C-016 leak sub-item; CJ §ROOT-014 / HANDLE LIFETIME. No production destroy path, status-call leaks, unbounded registries, silent double destroy.
- Code: `CryptoBridgeLocalE2eeIdentityStep.kt`, `CryptoBridge.kt`, `lib.rs` registry. Group CJ-E; MASTER/GATE S2 **LAST**; PRE_B004 after 005.
- Dependency 005 OPEN. MFT group 005/006/007/008; MNFA cleanup before 005 (activates wrong-object reuse). Independent verification of 005 precedes cleanup acceptance; coupled FCP-6 closure remains required.
- Automated: every acquire matched by destroy, use/AutoCloseable behavior, bounded/monitored registry, double destroy → HANDLE_DESTROYED. Instrumented: leak/cleanup on produced binary. Physical: none.
- Retest Crypto/JNI; closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + independent specialist retest ordered after 005 verification; GATE requires provenance-bound runtime and AC-006 chain stage. No isolated closure.

### MSC_UNIT_009 — Serialization output ABI (native-allocated output, caps, AAD hook) — Identity

- Severity HIGH; ROOT-004 ACTIVE. Sources: ROOT-004, A1 CS-004, A2 C-002, ANOX-LEGACY-INTEGRATION-002; CJ §ROOT-004 / IDENTITY SERIALIZATION MEASUREMENT / RECOMMENDED SERIALIZATION ABI. Fixed 4096-byte/heuristic output buffers fail default 20-OTK pickle size.
- Architecture/code: B-006; `CryptoBridge.kt`, `serialization.rs`, `lib.rs`. Group CJ-C; MASTER/GATE S2 order 4; PRE_B004, B004 step 3 activation.
- Dependency 001 infrastructure merged, runtime evidence still gated. MFT 009∧010∧011; MNFA constant increase alone (FCP-6). Provides 012 code and 019 hook.
- Automated: exact-size 0/20/100/5000 OTK serialization, 2 MiB identity cap. Instrumented: default-count registration step succeeds on produced binary. Physical: none.
- Retest Crypto/JNI; closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + independent specialist retest + AC-007, preserved under FCP stages.

### MSC_UNIT_010 — Stable OTK KeyId surface (ordered enumeration, publish/ACK export)

- Severity HIGH; ROOT-005 ACTIVE (single-audit/arbiter-confirmed). Sources: ROOT-005, A2 C-003; CONS §Roots with no dedicated Audit-001 candidate; CJ §ROOT-005 / OTK KEY-ID CONTRACT / OTK PUBLICATION / ACK. Fresh HashMap per positional lookup drops KeyId and duplicates/omits keys; no fabricated A1 source.
- Architecture/code: B-006 otk_id ACK; `identity.rs`, `lib.rs`, `CryptoNative.kt`, PublicE2eeIdentityMaterial surface (implementation task must bind allowed consumer paths). Group CJ-D; MASTER/GATE S2 order 5; PRE_B004 code, B006 conformance.
- Dependency 009 OPEN/planned first; MFT 009∧010∧011; MNFA publication export without stable KeyIds. S2 owns the KeyId surface, not backend publication/replenishment policy beyond it.
- Automated: deterministic KeyId order and (KeyId, public key) uniqueness; test the approved full-set/overlay publication-surface semantics, never invent a policy choice beyond scope. Instrumented: uploaded set equals created KeyIds. Physical: none. Synthetic backend S13 conformance remains B006.
- Retest Crypto/JNI; closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + independent specialist retest + SYNTHETIC_BACKEND_CONFORMANCE(S13) + AC-007. Later server conformance is not completed in S2.

### MSC_UNIT_011 — OTK count/set semantics + discarded OneTimeKeyGenerationResult

- Severity HIGH; source ANOX-CRYPTOJNI-CANDIDATE-001 (distinct count/set root related to ROOT-005), CJ §FINDINGS TABLE 001 / OTK COUNT SEMANTICS. Stored private count drives unpublished enumeration; created/removed result discarded.
- Architecture/code: B-006; `identity.rs`, `CryptoBridgeLocalE2eeIdentityStep.kt`. Group CJ-D; MASTER/GATE S2 order 5; PRE_B004, B006 publication conformance later.
- Dependency 010 OPEN/planned first; MFT with 009/010; no separate MNFA beyond this coupling.
- Automated: stored/unpublished counts distinct, after-publication enumeration/count consistency, removed results surfaced. Instrumented: same on produced binary. Physical: none. B006 conformance remains later.
- Retest Crypto/JNI; closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + independent specialist retest + AC-007; MASTER says closure as 010 and GATE binds B006 conformance, so no server-conformance waiver from the shorter derived evidence list.

### MSC_UNIT_012 — Session pickle growth vs output contract (S2 CODE ONLY)

- Severity MEDIUM, conditional HIGH at B008 (no escalation now). Sources ANOX-CRYPTOJNI-CANDIDATE-002, A2 C-002 session dimension; CJ §SESSION SERIALIZATION MEASUREMENT / candidate 002. Approximately 29.9 KB bounded maximum exceeds fixed buffer; persistence failure can leave ratchet advance unrecorded.
- Architecture/code B008/B009; `CryptoBridge.kt`, `session.rs`; CJ-C. MASTER S2(code)+S7(closure); GATE 012 primary S7 explicitly states code S2. Activation/closure LATER_B008_B009.
- Dependency 009 OPEN; code lands with common ABI; MNFA separate session constant. Do not implement B008/B009 features.
- Automated: five chains ×40 skipped keys serialize (~29.9 KB), 64 KiB cap. Instrumented: same on verified binary. Physical: none.
- Retest Crypto/JNI; closure at B008/B009 requires UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + independent specialist retest and AC-005 session chain per GATE. S2 code does not advance later closure.

### MSC_UNIT_013 — Unbounded OTK generation input / replenishment (S2 CAP ONLY)

- Severity MEDIUM; sources ANOX-CRYPTOJNI-CANDIDATE-004, A1 CS-019 OTK-count component; CJ §PANIC BOUNDARY / candidate 004. Unbounded native count and persistent growth; removed-key/replenishment handling is distinct later work.
- Architecture/code B-006 replenishment; `lib.rs`, `identity.rs`; CJ-G. MASTER S2(cap)+S6(replenishment), GATE S2 cap explicitly included; activation/closure LATER_B006. This is the recorded recommended cap pull-forward, not promotion of the complete B006 unit.
- Dependency 010 OPEN; no additional MFT/MNFA field. No replenishment/removed-key policy implementation beyond 011's surfaced result.
- Automated: count above cap → typed error. Instrumented cap on produced binary. Physical: none. Replenishment semantics + synthetic backend remain B006.
- Retest Crypto/JNI; full closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + SYNTHETIC_BACKEND_CONFORMANCE(B006), provenance/independent/chain stages per GATE; remains OPEN through this bootstrap.

### MSC_UNIT_014 — Read paths manufacture Keystore keys (S2 CRYPTOBRIDGE HALF ONLY)

- Severity MEDIUM; ROOT-006 ACTIVE. Sources ROOT-006, ANOX-SECURITY-ARCH-007/003, ANOX-MAINARCH-023, A1 CS-005/017, A2 C-008, ANOX-LEGACY-ANDROIDSEC-001; AS §ROOT-006 / K_STATE STORAGE / CREATE-ON-READ. Master alias creation on bridge read/initialization and existing-identity serialize paths manufacture keys.
- Architecture Inv.23/LKSL C/G; S2 code only `CryptoBridge.kt` init/master/existing-state-key paths; RegistrationSessionKey/store half excluded to S3. Groups AS-A/AS-C/AD-E. MASTER split plus GATE 014 primary S3/secondary S2 and exclusive CryptoBridge ownership; PRE_B004.
- Dependencies 015/017 OPEN (coupled acceptance, not a cycle per IMPL/VERIFY DAG). MFT 014∧015∧017; MNFA missing-key fail-closed without first-run consumer semantics; FCP-2 closure needs both halves.
- Automated: enumerate all Keystore-creating paths, reads do not create, existing aliases never regenerate, concurrent first-use one key; S3 save-exception wrapper remains S3. Instrumented: delete alias with valid envelope → KEY_MISSING, unchanged alias inventory. Physical P3 required at physical gate, NOT_EXECUTED.
- Retest Android/Storage + Auth/DPoP; closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + independent specialist retest + AC-001 + PHYSICAL(P3). S2 half cannot close the unit.

### MSC_UNIT_015 — Storage state-failure taxonomy + first-run consumer semantics (S2 CRYPTO CONSUMER ONLY)

- Severity MEDIUM; ROOT-007 plus ROOT-006 ACTIVE. Sources ROOT-007/006, A1 CS-015/017, A2 C-013, ANOX-SECURITY-ARCH-003; AS §CORRUPTION TAXONOMY and CJ §ROOT-013. Crypto missing-key/version errors collapse into corruption; registration empty-file/first-run downgrade is S3.
- Architecture store/first-run contract (033); S2 code `CryptoBridge.kt` LocalStateStatus only, AS-C consumer of CJ-B. MASTER S3(+S2 consumer), GATE session S2 AS-C slice; primary S3 retained; PRE_B004.
- Dependencies 014/007 OPEN; MFT 014/017 and 007 crypto consumer; no independent MNFA beyond coupled consumer semantics.
- Automated: typed KEY_MISSING/EMPTY/UNSUPPORTED_VERSION/AUTH_FAILED/IO; crypto status distinctions in S2; registration currentState not-first-run and empty-file exception tests in S3. Separate instrumented/physical requirement N/A for this unit per GATE; 007 retains JNI runtime tests.
- Retest Android/Storage with Crypto/JNI consumer coordination; closure SOURCE_DIFF + UNIT_TEST + independent specialist retest + AC-001. No S3 registration edits or isolated closure.

### MSC_UNIT_016 — Durable atomic persistence primitive (S2 writeFileAtomic ONLY)

- Severity MEDIUM; ROOT-007 ACTIVE. Sources ROOT-007, ANOX-ANDROIDSTORAGE-CANDIDATE-002, A1 CS-006, ANOX-SECURITY-ARCH-003; AS §ATOMIC FILE DURABILITY / DIRECTORY FSYNC / TEMP FILE RESIDUE / candidate 002. Three writers lack directory durability; registration AtomicFile also swallows failures/restores .bak.
- Architecture B-003 durable-write contract; S2 code `CryptoBridge.writeFileAtomic` only; AS-B/AS-C partition. MASTER S3(+S2 writer) and GATE S2 AS-C 016/exclusive CryptoBridge; primary S3 retained; PRE_B004.
- No standalone dependency field. MFT all three writers; MNFA fixing AtomicFileWriter while registration store keeps error-swallowing AtomicFile. S3 owns other writers; no false complete-durability claim from one slice.
- Automated real-class temp-dir rename-failure, residue handling and directory fsync tests; .bak/no auto-restore tests apply to S3 store. Instrumented kill-between-write/rename. Physical P12/P13 required, NOT_EXECUTED.
- Retest Android/Storage; closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PHYSICAL(P12/P13) + independent specialist retest + AC-009/AC-001. S2 slice alone cannot close.

### MSC_UNIT_019 — Local envelope AAD/type/version binding (S2 CRYPTO HOOK ONLY)

- Severity MEDIUM; ROOT-011 ACTIVE. Sources ROOT-011, A2 C-009, A1 CS-018; CJ §STATE DOMAIN SEPARATION / CRYPTO-LAYER ANTI-ROLLBACK and AS §ROOT-011 / AS-D. Common AAD lacks object type/context; local authenticated format is not an anti-rollback authority.
- Architecture Inv.24; S2 `serialization.rs`/common ABI AAD hook with 009; RegistrationSessionKey/Kotlin-envelope work remains S3's planned half under the file partition (S3 must not write CryptoBridge). Groups AS-D/CJ-C. MASTER split and GATE 019 primary S3/secondary S2; PRE_B004 before a second envelope version.
- Dependency 009 OPEN; MFT AAD hook with 009; no other MNFA field. No server epoch or B006/B008 anti-rollback implementation. If an implementation needs a shared-file change outside the recorded partition, STOP for a bounded task/ownership decision rather than extending S2 silently.
- Automated type/version/context AAD, cross-type substitution fails authentication, supported v1 migration versus unsupported version distinct. GATE requires instrumented AAD-hook test on verified binary (the derived unit's empty instrumented field is not a waiver). Physical: none.
- Retest Android/Storage + Crypto/JNI; closure SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + independent specialist retest, provenance runtime per GATE, and coupled-unit acceptance. Local AAD alone cannot close rollback chain AC-005.

## Adjacent exclusions (all obligations retained)

| Unit(s) | Excluded from S2 | Canonical reason / owner |
|---|---|---|
| 001/002/003/038 | Reimplementing S1, changing CI/provenance gates, or claiming closure | S1 implementation merged; stage overlay still awaits required runtime/independent retest/preservation evidence; 038 gates all closures |
| 004 | RC supply chain, signing/minification/SBOM | S9 / RELEASE_CANDIDATE |
| 012 | Session-feature implementation and closure | S7 at B008/B009; only common output-ABI code is in S2 |
| 013 | Replenishment/removed-key policy | S6 at B006; only cap slice in S2 |
| 014/015/016 | RegistrationSessionKey, stores, AtomicFileWriter, first-run registration consumer | S3; S2 owns only named CryptoBridge parts; MFT closure remains cross-session |
| 017/018/029/035 | Resolver/marker, RejectedAfterArm code, DeviceAuth race, UUID hardening | S3 primary (018/029 contingency S5); 018 contract already S0; 035 closure at final gate |
| 019 | Registration/Kotlin-envelope implementation outside S2 hook and assigned CryptoBridge partition | S3 planned half; no blanket shared-file permission |
| 020 | Server publication epoch / anti-rollback | S6 identity/B006, S7 session/B008; S0 contract entry only completed |
| 021/022/023/024/027 | DPoP, replay/clock interfaces, typed Registration API | S4 client after S3; B004/S5 server remains later |
| 025/026/028/032/033/034/040/042 (and 018c/020c/027c) | New contract or backend/schema implementation | S0 contracts frozen/retested; B004/B005/B006/B013/physical halves retain original named gates |
| 030 | Zeroization hardening | S7 / B008/B009; AS-C label does not pull all CJ-F work into S2 |
| 031 | Cross-domain wipe/reset orchestrator | S8 / B013 and final retest |
| 036 | PHYSICAL_P1..P17 | S10 physical campaign on provenance-verified binary; NOT_EXECUTED |
| 037 | Independent native retest execution/acceptance | S10 verification-only after S1+S2; independent Crypto/JNI + Build/Supply owners, not the S2 implementer |
| 039 | Reopening decided Human governance packet | H1/H2/H3/R1 decided; status/closure not changed here |
| 041 | Attachment secretstream boundary | B012_GATE |
| 043/044 | Any remediation or reopening | ROOT-016 / BUILDSC-012 REJECTED_NOT_A_FINDING; traceability only |
| S1CRC-R-003 / R-009 | Foreign-export inventory / protected shared-validator extension | Recorded deferred/non-blocking follow-ups, not S2 remediation scope |
| B027-D | Employee runtime router | DEFERRED_UNTIL_ALL_CURRENT_FINDINGS_CLOSED |

## Acceptance and next action

No findings/MSC units closed; no severity or protected evidence changed. All 42 MSC units remain OPEN, zero CLOSED. B004/B005, actual S2/S3/S4 remediation and physical campaign remain NOT_STARTED/NOT_EXECUTED. Product BLOCKED_PENDING_FINAL_AUDIT, ARM64 UNVERIFIED_PENDING_REAL_ARM64_RUNTIME, B027-D deferred, ledger tail ANOX-EVENT-0054. No full handoff requested/generated.

Next is **S2-IMPLEMENTATION-001**, using this exact scope, the canonical Authority chain and a fresh authorized task package after governance/scope delivery acceptance. Bind and verify predecessor/provenance evidence before execution; preserve all runtime, independent retest, chain, physical and evidence-preservation requirements. This bootstrap neither implements remediation nor grants push/PR/merge or Product-resume authority.
