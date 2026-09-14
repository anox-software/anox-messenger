# MASTER-SPECIALIST-CONSOLIDATION-001 — FINAL REPORT

## RESULT
`PASS_WITH_CONSOLIDATION_FINDINGS` — all source items accounted for; 42 security units intentionally remain OPEN pending `SECURITY-REMEDIATION-COVERAGE-GATE`. PASS does NOT unblock Product Development.

## TASK
`MASTER-SPECIALIST-CONSOLIDATION-001`
## MODE
`READ_ONLY_MASTER_SECURITY_CONSOLIDATION`
## PROVIDER
Devin CLI (Cognition) session runtime — Anthropic model
## MODEL
Claude Fable 5.1 High (runtime label per session system prompt: "You are powered by Claude Fable 5.1 High"). Effort level: not exposed beyond the "High" label. Routing/fallback: none observed. Fresh independent specialist session.
## MODEL REQUIREMENT SATISFIED
YES
## BASE SHA
`1eb773069d81ea3d12b76249c73f2f5fb0b6cae9`
## HEAD AT END
`1eb773069d81ea3d12b76249c73f2f5fb0b6cae9`
## ORIGIN MAIN
`1eb773069d81ea3d12b76249c73f2f5fb0b6cae9`
## WORKING TREE
CLEAN (`git status --short` empty; `git diff --check` rc 0; branch `main`)
## REMOTE MUTATION
NONE (only `git fetch origin`). Repository not modified. Temporary artifacts only under `/tmp/anox_master_consolidation_001/` (traceability dumps, `consolidate.py`, `model.json`) — not authoritative.

---

## PRESERVED EVIDENCE VALIDATION
**PASS** — `python3 tools/audit/validate_security_audit_evidence_preservation.py` → `SECURITY AUDIT EVIDENCE PRESERVATION: PASS`, exit 0.

## PRESERVED REPORT HASH VALIDATION
**9/9** — every report in `evidence_hashes.json` re-hashed (SHA-256 + byte length) and matched: ARCHITECTURE, CODEBASE-001, CODEBASE-002, CONSENSUS-001, BUILD-SUPPLYCHAIN-001, CRYPTO-JNI-001, AUTH-DPOP-001, ANDROID-STORAGE-001, ATTACKCHAIN-001. `HASH MISMATCHES = 0`. All nine read in full from the repository (not from chat history), plus `AUDIT_EVIDENCE_INDEX.md`, `audit_registry.jsonl`, `audit_traceability.jsonl` (245 records), `evidence_hashes.json`, `reproductions/README.md`, `docs/authority/AUTHORITY_INDEX.md`, `B025_MANDATORY_AMENDMENTS_V1_2.md` (verified: `device_auth_keys` has `public_key_pem` with **no UNIQUE**; §B-005.3 "does not allow reusing … Device Auth key" is prose only), and `docs/workforce/registries/findings.jsonl` (canonical statuses of all 26 historical/architecture findings cited below verified unchanged).

---

## SOURCE SECURITY ITEM UNIVERSE
**TOTAL SOURCE SECURITY ITEMS = 90** — derived mechanically from `audit_traceability.jsonl` + preserved reports (not assumed):

| Class | Count | Members |
|---|---|---|
| Consensus roots | 18 | ROOT-001…018 (016 REJECTED) |
| Build/Supply candidates | 12 | ANOX-BUILDSC-CANDIDATE-001…012 |
| Crypto/JNI candidates | 6 | ANOX-CRYPTOJNI-CANDIDATE-001…006 |
| Auth/DPoP candidates + gaps | 3 + 3 | CANDIDATE-001…003; GAP-001…003 |
| Android/Storage candidates + gaps | 2 + 3 | CANDIDATE-001…002; GAP-001…003 |
| Attackchains | 15 | ANOX-ATTACKCHAIN-CANDIDATE-001…015 |
| Security Architecture findings | 10 | ANOX-SECURITY-ARCH-001…010 |
| Main Architecture findings tracked by evidence | 9 | MAINARCH-005, 008, 013, 014, 018, 019, 023, 030, 031 |
| Legacy findings tracked by evidence | 7 | LEGACY-CRYPTO-005; LEGACY-INTEGRATION-001, 002, 003, 005; LEGACY-B003-001; LEGACY-ANDROIDSEC-001 |
| Governance/evidence items | 2 | CS-021/C-017 validator lifecycle; Audit-001 model deviation |

Secondary layer (not double-counted): 21 `ANOX-CODESEC-CANDIDATE` + 17 `ANOX-CODESEC2-CANDIDATE` = **38/38** traced through their consensus roots (0 without a root; CS-021/C-017 carried as the governance item; CS-102/CS-103 folded sub-items). `UNWIRED-001` is a reachability fact absorbed by ARCH-010.

## SOURCE ACCOUNTABILITY
```
TOTAL SOURCE SECURITY ITEMS = 90
ACCOUNTED FOR               = 90
UNACCOUNTED                 = 0
DUPLICATE SOURCE IDS        = 0
UNKNOWN DISPOSITION         = 0
```
Disposition distribution: DISTINCT_ROOT_CAUSE 23 · MERGE_INTO_EXISTING_ROOT 19 · ATTACKCHAIN_ONLY 14 · SUPERSEDED_BUT_TRACEABLE 12 · ARCHITECTURE_CONTRACT_GAP 9 · META_EVIDENCE_OR_BUILD_RISK 8 · REJECTED_NOT_A_FINDING 2 · ENABLING_CONDITION 2 · STANDALONE_SECURITY_ITEM 1.

### Source-item accountability table

| Source ID | Report | Type | Orig. sev | Hist. status | Current relation | Disposition → MSC |
|---|---|---|---|---|---|---|
| ROOT-001 | CONSENSUS | root | HIGH (EI CRITICAL) | ACTIVE | confirmed BUILDSC/CJ/AC-012 | DISTINCT_ROOT_CAUSE → 001 |
| ROOT-002 | CONSENSUS | root | HIGH | ACTIVE | confirmed CJ; AC-006/011 | DISTINCT → 006 |
| ROOT-003 | CONSENSUS | root | HIGH | ACTIVE | confirmed+expanded CJ; AC-006 | DISTINCT → 005 |
| ROOT-004 | CONSENSUS | root | HIGH | ACTIVE | confirmed+expanded (session) | DISTINCT → 009 |
| ROOT-005 | CONSENSUS | root | HIGH (conf. MEDIUM) | ACTIVE | confirmed+expanded | DISTINCT → 010 |
| ROOT-006 | CONSENSUS | root | MEDIUM | ACTIVE | confirmed+expanded AD/AS | DISTINCT → 014, 015 |
| ROOT-007 | CONSENSUS | root | MEDIUM | ACTIVE | confirmed+expanded (c4–c7) | DISTINCT → 016, 017, 015 |
| ROOT-008 | CONSENSUS | root | MEDIUM/HIGH@B004 | ACTIVE | confirmed+expanded | DISTINCT (split) → 021, 023 |
| ROOT-009 | CONSENSUS | root | MEDIUM | ACTIVE | confirmed+expanded | DISTINCT → 022 |
| ROOT-010 | CONSENSUS | root | LOW | ACTIVE | confirmed | DISTINCT → 030 |
| ROOT-011 | CONSENSUS | root | MEDIUM | ACTIVE | confirmed+expanded (storage) | DISTINCT (split) → 019, 020, 017 |
| ROOT-012 | CONSENSUS | root | LOW | ACTIVE | confirmed+expanded | DISTINCT (split) → 031, 032 |
| ROOT-013 | CONSENSUS | root | LOW | ACTIVE | expanded; MEDIUM proposed | DISTINCT → 007 |
| ROOT-014 | CONSENSUS | root | MEDIUM | ACTIVE | confirmed | DISTINCT → 008 |
| ROOT-015 | CONSENSUS | root | LOW | ACTIVE | confirmed; no chain | STANDALONE_SECURITY_ITEM → 035 |
| ROOT-016 | CONSENSUS | root | NONE | REJECTED | not revived (AD, AS, AC) | REJECTED_NOT_A_FINDING → 043 |
| ROOT-017 | CONSENSUS | meta root | UNKNOWN | ACTIVE | confirmed BUILDSC/AS | DISTINCT → 002 |
| ROOT-018 | CONSENSUS | umbrella | UNKNOWN | ACTIVE | confirmed+expanded BUILDSC | DISTINCT (split) → 003, 004 |
| BUILDSC-001 | BUILDSC | cand. | HIGH/EI CRITICAL | Open | confirms ROOT-001 | META_EVIDENCE_OR_BUILD_RISK → 001 |
| BUILDSC-002 | BUILDSC | cand. | HIGH | Open | confirms ROOT-017 | META → 002 |
| BUILDSC-003 | BUILDSC | cand. | HIGH | Open | prerequisite of 001 | MERGE → 001 |
| BUILDSC-004 | BUILDSC | cand. | MEDIUM | Open | ROOT-018; doc half Pre-B004 | MERGE → 003 (doc), 004 (verification) |
| BUILDSC-005 | BUILDSC | cand. | MEDIUM | Open | ROOT-018 sub-fact | MERGE → 004 |
| BUILDSC-006 | BUILDSC | cand. | MEDIUM/EI HIGH | Open | gate weakness | META → 001 |
| BUILDSC-007 | BUILDSC | cand. | MEDIUM | Open | Pre-B004 B-017-Lite | MERGE → 003 |
| BUILDSC-008 | BUILDSC | cand. | MEDIUM/EI HIGH | Open | evidence comparability | META → 001 |
| BUILDSC-009 | BUILDSC | cand. | LOW | Open | RC | MERGE → 004 |
| BUILDSC-010 | BUILDSC | cand. | LOW | Open | Pre-B004 lint | MERGE → 003 |
| BUILDSC-011 | BUILDSC | cand. | LOW | Open/DEFERRED | residual | MERGE → 004 |
| BUILDSC-012 | BUILDSC | cand. | INFO | Open/DEFERRED | "not a finding" | REJECTED_NOT_A_FINDING → 044 |
| CRYPTOJNI-001 | CJ | cand. | HIGH | Open | new root re ROOT-005 | DISTINCT → 011 |
| CRYPTOJNI-002 | CJ | cand. | MEDIUM | Open | expands ROOT-004 | DISTINCT → 012 |
| CRYPTOJNI-003 | CJ | cand. | MEDIUM | Open | expands ROOT-013 | MERGE → 007 |
| CRYPTOJNI-004 | CJ | cand. | MEDIUM | Open | new root (growth) | DISTINCT → 013 |
| CRYPTOJNI-005 | CJ | cand. | LOW | Open | expands ROOT-010 | MERGE → 030 |
| CRYPTOJNI-006 | CJ | cand. | INFO | Open | diagnostic ROOT-013 | MERGE → 007 |
| AUTHDPOP-CAND-001 | AD | cand. | MEDIUM | Open | distinct root | DISTINCT → 027 |
| AUTHDPOP-CAND-002 | AD | cand. | LOW | Open | C-014 root | DISTINCT → 029 |
| AUTHDPOP-CAND-003 | AD | cand. | LOW | Open | time source | DISTINCT → 024 |
| AUTHDPOP-GAP-001/002/003 | AD | gap | CONTRACT | Open | CHAIN_RELEVANT/CRITICAL/CRITICAL | ARCHITECTURE_CONTRACT_GAP → 025 / 026 / 028 |
| ANDROIDSTORAGE-CAND-001 | AS | cand. | LOW | Open | lifecycle contract | DISTINCT → 018 |
| ANDROIDSTORAGE-CAND-002 | AS | cand. | LOW | Open | ROOT-007 c4 | MERGE → 016 |
| ANDROIDSTORAGE-GAP-001/002/003 | AS | gap | CONTRACT | Open | CRITICAL/RELEVANT/RELEVANT | ARCHITECTURE_CONTRACT_GAP → 033 / 032 / 034 |
| AC-001…012, 014, 015 | ATTACKCHAIN | chain | H/M/M/M/M/H/M/M/L/M/M/H/L/L | Open | see §Attackchain map | ATTACKCHAIN_ONLY |
| AC-013 | ATTACKCHAIN | enabling | INFO | Open | evidence vacuum | ENABLING_CONDITION → 036 |
| SECURITY-ARCH-001 | ARCH | finding | HIGH | Open | expanded ROOT-002/003/013/014 | MERGE → 005, 006, 007, 008 |
| SECURITY-ARCH-002 | ARCH | finding | HIGH | Open | META AC-012 | META → 038 |
| SECURITY-ARCH-003 | ARCH | finding | HIGH | Open | expanded (primitives) | MERGE → 017, 014, 015, 016, 018, 027 |
| SECURITY-ARCH-004 | ARCH | finding | HIGH | Open | schema authority drift | ARCHITECTURE_CONTRACT_GAP → 040 |
| SECURITY-ARCH-005 | ARCH | finding | MEDIUM | Open | not chain relevant | ARCHITECTURE_CONTRACT_GAP → 041 |
| SECURITY-ARCH-006 | ARCH | finding | MEDIUM | Open | AC-003 potential | ARCHITECTURE_CONTRACT_GAP → 042 |
| SECURITY-ARCH-007 | ARCH | finding | MEDIUM | Open | INEFFECTIVE_REMEDIATION_SCOPE | MERGE → 014 |
| SECURITY-ARCH-008 | ARCH | finding | LOW | Open | expanded | MERGE → 007 (errors), 035 (UUID) |
| SECURITY-ARCH-009 | ARCH | finding | LOW | Open | STILL_EFFECTIVE + new root | MERGE → 031, 032 |
| SECURITY-ARCH-010 | ARCH | finding | INFO | Open | positive scope; UNWIRED-001 | SUPERSEDED_BUT_TRACEABLE → 039 (retire at B004 start) |
| MAINARCH-013 | HIST | finding | HIGH | Open | expanded; note superseded | META → 001, 003, 004 |
| MAINARCH-018 | HIST | finding | MEDIUM | Open | PHYSICAL_REVALIDATION_REQUIRED | ENABLING_CONDITION → 036 |
| MAINARCH-023 | HIST | finding | MEDIUM | Closed | PARTIALLY_EFFECTIVE | SUPERSEDED_BUT_TRACEABLE → 014 |
| MAINARCH-030 | HIST | finding | MEDIUM | Open | STILL_EFFECTIVE (Open) | MERGE → 031, 032 |
| MAINARCH-031 | HIST | finding | LOW | Closed | FALSE_CLOSURE historical instance | SUPERSEDED_BUT_TRACEABLE → 001, 037, 007 |
| MAINARCH-005 | HIST | finding | HIGH | Closed | STILL_EFFECTIVE | SUPERSEDED_BUT_TRACEABLE → 021 (conformance) |
| MAINARCH-008 | HIST | finding | HIGH | Closed | doc effective / new gaps | SUPERSEDED_BUT_TRACEABLE → 025, 026, 027 |
| MAINARCH-014 | HIST | finding | MEDIUM | Closed | NO_LONGER_APPLICABLE | SUPERSEDED_BUT_TRACEABLE → 032 (B013 revalidation) |
| MAINARCH-019 | HIST | finding | MEDIUM | Closed | STILL_EFFECTIVE | SUPERSEDED_BUT_TRACEABLE → 027, 029 (retest) |
| LEGACY-CRYPTO-005 | HIST | finding | HIGH | Closed | LATER_AUDIT_PROVES_INEFFECTIVE | SUPERSEDED_BUT_TRACEABLE → 005, 006, 037 |
| LEGACY-INTEGRATION-001 | HIST | finding | HIGH | Closed | PARTIALLY_EFFECTIVE | SUPERSEDED_BUT_TRACEABLE → 027 |
| LEGACY-INTEGRATION-002 | HIST | finding | HIGH | Closed | STILL_EFFECTIVE (blocked by 4096) | SUPERSEDED_BUT_TRACEABLE → 009, 037 |
| LEGACY-INTEGRATION-003 | HIST | finding | MEDIUM | Closed | PARTIALLY_EFFECTIVE | SUPERSEDED_BUT_TRACEABLE → 018 |
| LEGACY-INTEGRATION-005 | HIST | finding | MEDIUM | Open | NEW_ROOT_CAUSE_RELATED | MERGE → 005, 008, 037 |
| LEGACY-B003-001 | HIST | finding | LOW | Open | SAME_ROOT ROOT-015 | MERGE → 035 |
| LEGACY-ANDROIDSEC-001 | HIST | finding | HIGH | Closed | STILL_EFFECTIVE | SUPERSEDED_BUT_TRACEABLE → 014, 007 (regression retest) |
| GOV CS-021/C-017 | CODEBASE via CONSENSUS | governance | INFO | pending human | HISTORICAL_SHA_PINNED_VALIDATOR | META → 039 |
| GOV Audit-001 model deviation | CODEBASE-001 | governance | META | pending human | MODEL_DEVIATION preserved | META → 039 |

**Consensus deviations recorded explicitly:** (1) ROOT-013 severity LOW→MEDIUM adopted; (2) ROOT-008/011/012/018 SPLIT into gate-distinct units; (3) ROOT-017 given an explicit classification (was UNKNOWN); (4) CJ-CAND-001/002/004, AD-CAND-001/002/003, AS-CAND-001 recognized as distinct units (no new ROOT IDs allocated). No consensus root rewritten; earlier arbitrations otherwise confirmed.

---

## NORMALIZED MSC UNITS
**TOTAL = 44** (42 OPEN + 2 REJECTED records). Analytical IDs only — NOT permanent ROOT IDs.

## MSC UNIT TABLE

Columns: Type · Proposed consolidated severity (component / chain / evidence-integrity) · Confidence · Primary root cause · Sources · Chains · Affected code · Reachability/Activation · Gate · Fix group/session · Must-fix-together (MFT) / must-not-fix-alone (MNFA) · Chain breakers · Tests (A=automated, I=instrumented, P=physical) · Retest owners · Closure evidence · Disposition. All open units: `OPEN_PENDING_REMEDIATION_COVERAGE_GATE`; all reachability `DEAD_OR_UNWIRED_TODAY` unless stated.

**MSC-UNIT-001 — Native source↔artifact provenance chain** · BUILD_PROVENANCE · HIGH / AC-012 HIGH / **EI CRITICAL** · VERY_HIGH · no source→binary gate; hand-built `.so` committed at `7db20fa`; toolchain unpinned; local/CI strip divergence; validator provenance-blind · ROOT-001, BUILDSC-001/003/006/008, MAINARCH-013, MAINARCH-031 (fired instance), CS-003/C-001 · AC-012, AC-007 · `.github/workflows/ci.yml`, `android/src/main/jniLibs/*`, `android/build.gradle.kts`, `crypto/rust` (rust-toolchain.toml, remap/strip), `tools/security/validate_apk_contents.py` · **CURRENTLY_REACHABLE** (every APK) · PRE_B004 precondition (also NATIVE_RETEST_ACCEPTANCE, RC) · Build/Supply order 1–3 / Session S1 · MFT: pin ∧ CI cross-build ∧ reproducibility ∧ in-run hash gate ∧ validator v2 ∧ Gradle-consumes-output; MNFA: re-commit fresh `.so` without gate; rust-toolchain.toml without CI assertion · breaker: in-run hash manifest vs packaged `lib/*` · A: gate fails on committed/packaged ≠ rebuild; two clean rebuilds identical; JNI symbol parity; validator-v2 negatives (injected `.so`, wrong ABI, binary PEM) FAIL · I: existing `BufferTooSmall` instrumented tests PASS on produced binary · P: n/a · Retest: Build/Supply (+Crypto/JNI consumer) · Closure: SOURCE_DIFF + BUILD_ARTIFACT_HASH_PROOF + PROVENANCE_VERIFIED_NATIVE_RUNTIME + UNIT_TEST + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-012) + ARCHITECTURE_AUTHORITY_UPDATE (MAINARCH-013 note, `.so` policy Option C).

**MSC-UNIT-002 — Native/JNI + instrumented verification vacuum** · SECURITY_EVIDENCE_GAP · META (EI **HIGH**) / enabling AC-012, AC-013 / — · HIGH · JNI cfg-gated out of host tests; no CI cross-build; 39+27+66 instrumented tests never CI-executed; sequential "concurrent" test; test/debug OTK API in prod path · ROOT-017, BUILDSC-002, C-014/C-015/C-016 (ROOT-017 components), CS-003 · AC-012, AC-013 · `ci.yml` (emulator job arm64+x86_64), `crypto/android/src/androidTest`, `android/src/androidTest`, `crypto/rust/src/tests.rs` · CURRENT (evidence) · PRE_B004 · S1 (+AS-G) · MFT: with 001 (BUILDSC 002+006); MNFA: instrumented job packaging stale `.so` · breaker: instrumented JNI on produced binary · A: JNI symbol parity; host-testable registry tests · I: full instrumented suites both ABIs in CI, negative tests added (zero-length file, alias deletion, marker flags, residue, rollback, wipe partial, rejected-after-arm, concurrent stores) · Retest: Build/Supply + each domain · Closure: INSTRUMENTED_TEST (CI, both ABIs) + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST.

**MSC-UNIT-003 — Pre-B004 CI hygiene gates (B-017-Lite scope)** · SUPPLY_CHAIN · MEDIUM / — / — · HIGH · no advisory scan, no secret scan, no lint in CI; policy doc overclaims lockfiles · ROOT-018 (slice), BUILDSC-007, -010, -004 (doc half), MAINARCH-013 · AC-012 (enabling) · `ci.yml`, `REPOSITORY_SECURITY_POLICY.md` · PRE_B004 · S1 · MFT: doc correction with any Gradle-verification work · A: cargo-audit/OSV gate, secret-scan gate, lint gate (errors fatal) present and fail-closed on injected regressions · Retest: Build/Supply · Closure: SOURCE_DIFF + UNIT_TEST (gate negatives) + ARCHITECTURE_AUTHORITY_UPDATE (policy doc).

**MSC-UNIT-004 — Release-candidate supply-chain & release hardening** · SUPPLY_CHAIN · MEDIUM / — / — · HIGH · no Gradle verification-metadata/locking; foojay JDK unpinned/unchecksummed; embedded `/Users/<name>` paths (no remap/strip); pin-cadence absent; release unsigned/unminified, empty ProGuard (R8 would break JNI without keep) · ROOT-018, BUILDSC-004 (verification half), -005, -009, -011, CS-020/C-015, MAINARCH-013 · AC-012 (A7 variant) · Gradle files, `proguard-rules.pro`, `gradle-daemon-jvm.properties`, RUSTFLAGS · RELEASE_CANDIDATE (011 deferred) · S9 · MNFA: enabling R8 without JNI keep-rule confirmation · A: `--verify-metadata` fails on unknown artifact; cargo-deny; JDK checksum assert; remap/strip → cross-host hash identical; R8 keep test; SBOM present · Retest: Build/Supply · Closure: SOURCE_DIFF + BUILD_ARTIFACT_HASH_PROOF + UNIT_TEST + INDEPENDENT_SPECIALIST_RETEST + ARCHITECTURE_AUTHORITY_UPDATE (B-018 signing procedure; human signing).

**MSC-UNIT-005 — JNI handle identity/ownership/synchronization (slot+generation, owning lock)** · CODE_ROOT_CAUSE · HIGH / AC-006 HIGH / — · HIGH · handle = raw heap address; registry membership only; check-then-deref after unlock; unenforced `&mut` uniqueness; freed-address reuse (7/100) · ROOT-003, ARCH-001, LEGACY-INTEGRATION-005 (root never fixed), LEGACY-CRYPTO-005 (ineffective), CS-002/C-005 · AC-006 · `crypto/rust/src/lib.rs:31-116,126-255,292-344,522-544` · PRE_B004 (activates B004 multi-instance / B008 concurrency) · CJ-A / S2 · MFT: 005∧008∧007∧006; MNFA: 008 cleanup before 005 (**DO NOT FIX ROOT-014 BEFORE ROOT-003** preserved) · breaker C6 · A: host-testable slab registry unit tests (generation bump on destroy; stale generation rejected; destroy during in-flight use cannot free) · I: destroy→realloc→stale handle ⇒ `HANDLE_STALE_GENERATION`; concurrent encrypt/serialize on one handle serialized (provenance-verified `.so`) · Retest: Crypto/JNI · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-006).

**MSC-UNIT-006 — Process-global CryptoBridge singleton + CryptoNative visibility narrowing** · CODE_ROOT_CAUSE · HIGH / AC-006, AC-011 / — · HIGH · `instance` never assigned; per-instance `ReentrantLock`; public `CryptoNative` in same module; `initialize()` re-runs per call · ROOT-002, C-014 (locking component), CS-001/C-004, CS-102, LEGACY-CRYPTO-005 (inert Kotlin half) · AC-006, AC-011 · `CryptoBridge.kt:38-44,580`, `CryptoNative.kt`, module layout · PRE_B004 · CJ-E / S2 · MNFA: Kotlin singleton alone (bypass via `CryptoNative`) — closure requires 005 · breaker C6 (part) · A: `assertSame(getInstance(c), getInstance(c))`; `initialize()` runs once; `CryptoNative` not reachable from app module (compile-level) · Retest: Crypto/JNI · Closure: SOURCE_DIFF + UNIT_TEST + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-011).

**MSC-UNIT-007 — JNI error taxonomy / status channel + LocalStateStatus consumer** · CODE_ROOT_CAUSE · **MEDIUM (raised from LOW — see §ROOT-013)** / AC-006/B, AC-007 / — · HIGH · non-injective codes (−1, −3, −10, −11 overloaded; −12 unmapped); deserialize/outbound return `0` for all failures (−9 lost); `KeyError`→`KeyGenerationFailed`; NPE→`CorruptedIdentityState`; `MissingKeystore` ≡ corrupt wrapped key · ROOT-013, CJ-CAND-003, CJ-CAND-006, ARCH-008 (error half), CS-013/CS-017/C-012, MAINARCH-031 (mapping), LEGACY-ANDROIDSEC-001 (string-match in `isKeystoreOrUnwrapFailure`) · AC-006, AC-007 · `error.rs`, `lib.rs`, `CryptoError.kt`, `CryptoBridge.kt:603-661,764-777` · PRE_B004 · CJ-B + AS-C / S2 · MFT: 007∧005 (HANDLE_* codes need generation identity); 007∧015 consumer; MNFA: deserialize codes without `LocalStateStatus` consumer change · breaker C6 (part), C3 · A: error-code injectivity table test (every native condition → unique code); version bump ⇒ `UNSUPPORTED_VERSION` ≠ `Corrupted`; master-key-null ⇒ `MissingKeystore` · I: negative-path JNI tests per code on produced binary · Retest: Crypto/JNI (+Android/Storage consumer) · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST.

**MSC-UNIT-008 — Native handle lifetime / cleanup / registry bounds** · CODE_ROOT_CAUSE · MEDIUM / AC-006, AC-007, AC-015 / — · HIGH · no production destroy path; `getLocalStateStatus` leaks per call; unbounded `ACTIVE_*`; double-destroy silent success · ROOT-014, LEGACY-INTEGRATION-005, CS-012/C-016 (leak), CS-019 (registry growth) · AC-006, AC-007, AC-015 · `CryptoBridgeLocalE2eeIdentityStep.kt:61-75`, `CryptoBridge.kt:603-661`, `lib.rs:31-36` · PRE_B004 · CJ-E (**last**) / S2 · MNFA: **must not be fixed before 005** (activates wrong-object path) · breaker C14 (part) · A: every acquire has a matching destroy (`use{}`/AutoCloseable); registry size bounded/monitored; double-destroy → `HANDLE_DESTROYED` · I: leak test on produced binary · Retest: Crypto/JNI · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + INDEPENDENT_SPECIALIST_RETEST (ordered after 005 closure).

**MSC-UNIT-009 — Serialization output ABI (native-allocated output, caps, AAD hook) — Identity** · CODE_ROOT_CAUSE · HIGH / AC-007 MEDIUM, AC-005 / — · VERY_HIGH · fixed 4096-byte caller buffers vs 20-OTK pickle 5269–5287 B; heuristic `n+512/n+256` · ROOT-004, CS-004/C-002, LEGACY-INTEGRATION-002 (ordering correct but blocked) · AC-007, AC-005 · `CryptoBridge.kt:334-355,528`, `serialization.rs`, `lib.rs` · PRE_B004 (activates B004 step 3) · CJ-C / S2 · MFT: 009∧010∧011 (same call sites); MNFA: **constant increase alone = FALSE CLOSURE** · breaker C7 · A: exact-size output for 0/20/100/5000 OTK; cap enforced (2 MiB identity) · I: default-count registration step succeeds on produced binary · Retest: Crypto/JNI · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-007).

**MSC-UNIT-010 — Stable OTK KeyId surface (ordered enumeration, publish/ACK export)** · CODE_ROOT_CAUSE · HIGH / AC-007, AC-005 / — · HIGH (corroboration MEDIUM per consensus) · index over fresh `HashMap` per call (20/20 sweeps duplicated); KeyId discarded; no `mark_keys_as_published`/`unpublished`/`get(KeyId)` export · ROOT-005, C-003 · AC-007, AC-005 · `identity.rs:33-72`, `lib.rs`, `CryptoNative.kt`, `PublicE2eeIdentityMaterial.kt` · PRE_B004 · CJ-D / S2 · MFT: 009∧010∧011; MNFA: publish export without stable KeyIds · breaker C8, server S13/S14 conformance · A: enumeration == BTreeMap order, unique by (KeyId, pk); `otkMarkPublished` semantics decided (full-set or overlay) and tested · I: uploaded set == `created` KeyIds on produced binary · Retest: Crypto/JNI · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST + SYNTHETIC_BACKEND_CONFORMANCE (S13) + ATTACKCHAIN_RETEST(AC-007).

**MSC-UNIT-011 — OTK count/set semantics + discarded `OneTimeKeyGenerationResult`** · CODE_ROOT_CAUSE · HIGH / AC-007, AC-005 / — · HIGH · `stored_one_time_key_count` (all private) drives generation while enumeration reads unpublished set; `{created, removed}` discarded at `identity.rs:34` · CJ-CAND-001 · AC-007, AC-005 · `identity.rs:33-41,61-67`, `CryptoBridgeLocalE2eeIdentityStep.kt:31-52` · PRE_B004 (B006 publish) · CJ-D / S2 · MFT: with 009/010 · breaker C8 · A: `otkStoredCount`/`otkUnpublishedCount` distinct; after publish count/enumeration consistent; `removed` surfaced · I: same on produced binary · Retest: Crypto/JNI · Closure: as 010.

**MSC-UNIT-012 — Session pickle growth vs output contract** · CODE_ROOT_CAUSE · MEDIUM (HIGH at B008) / AC-005 (session variant) / — · HIGH · 8 KB at 40 skipped keys, 29.9 KB bounded max; `saveSession` failure after decrypt = unpersisted ratchet advance · CJ-CAND-002, C-002 (session) · AC-005 · `CryptoBridge.kt:528,603-661`, `session.rs` · **LATER: B008/B009** (code lands with 009 in S2; closure at B008/B009) · CJ-C / S2 (code), S7 (closure) · MNFA: separate constant for session · breaker C7 · A: 5 chains × 40 skipped ≈ 29.9 KB serializes; cap 64 KiB · I: on produced binary · Retest: Crypto/JNI · Closure: UNIT_TEST + INSTRUMENTED_TEST + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST at B008/B009.

**MSC-UNIT-013 — Unbounded OTK generation input, monotonic pickle growth, `removed`-key/replenishment handling** · CODE_ROOT_CAUSE · MEDIUM / AC-007 (potential) / — · HIGH · `count as usize` up to 2^31; unpublished set grows to 5000-cap/1.23 MB while publish unreachable; no `removed` handling · CJ-CAND-004, CS-019 (OTK count component) · AC-007 · `lib.rs:200-214`, `identity.rs` · **LATER: B006** (input cap recommended to land in S2 as hardening) · CJ-G / S2 (cap), S6 (replenishment) · A: cap test (`count > cap` ⇒ typed error); replenishment semantics vs B-006 · I: on produced binary · Retest: Crypto/JNI · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + SYNTHETIC_BACKEND_CONFORMANCE (B-006 replenishment) at B006.

**MSC-UNIT-014 — Read paths manufacture Keystore keys (create-on-read / alias overwrite / unserialized creation)** · CODE_ROOT_CAUSE · MEDIUM / AC-001 HIGH, AC-008, AC-011 / — · VERY_HIGH · `RegistrationSessionKey.decrypt()→getOrCreateKey()`; `initializeMasterKey()` on every `getInstance()`; `serialize*` for existing identity uses `getOrCreateStateKey`; non-`SecretKeyEntry` alias overwritten; `save()` encrypt outside try · ROOT-006, ARCH-007 (INEFFECTIVE_REMEDIATION_SCOPE), MAINARCH-023 (PARTIALLY_EFFECTIVE), ARCH-003, CS-005/CS-017/C-008, LEGACY-ANDROIDSEC-001 (regression watch) · AC-001, AC-008, AC-011 · `RegistrationSessionKey.kt:47-84`, `CryptoBridge.kt:38-44,73-110,133-165,337,526`, `FileRegistrationSessionStore.kt:58` · PRE_B004 · AS-A + AS-C + AD-E / S2 (CryptoBridge half) + S3 (RegistrationSessionKey half) · MFT: 014∧015∧017 (consumer semantics); MNFA: fail-on-missing-key without `currentState()/canStartNew()` change · breaker C2 · A: **enumeration test over ALL Keystore-creating call sites** (create-on-write only; read never creates; existing alias never `generateKey`); serialized creation (concurrent first-use → one key); `save()` wraps Keystore exceptions · I: delete alias with valid envelope → `load()` throws `KEY_MISSING`, alias count unchanged · P: P3 · Retest: Android/Storage + Auth/DPoP (AD-E) · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-001) + PHYSICAL(P3). **Closure requires both halves (FCP-2).**

**MSC-UNIT-015 — Storage state-failure taxonomy + first-run consumer semantics** · CODE_ROOT_CAUSE · MEDIUM / AC-001, AC-006/B / — · HIGH · `EMPTY`→`NotStarted`; `KEY_MISSING` ≡ corrupt; `UNSUPPORTED_VERSION` ≡ truncation; synthetic `Failed` → `canStartNew` true; crypto NPE→`Corrupted` · ROOT-007 c3, ROOT-006 (secondary), CS-015/CS-017/C-013, ARCH-003 · AC-001, AC-006 · `FileRegistrationSessionStore.kt:39-53`, `RegistrationSessionSecurityException.kt`, `RegistrationOrchestrator.kt:58-62,246-254`, `CryptoBridge.kt:603-661` · PRE_B004 · AS-A/AS-B (+AS-C) / S3 (+S2 crypto consumer) · MFT: with 014, 017; 007 (crypto side) · breaker C3 · A: typed `KEY_MISSING/EMPTY/UNSUPPORTED_VERSION/AUTH_FAILED/IO`; `currentState()` on each ⇒ not-first-run; zero-length file ⇒ security exception · Retest: Android/Storage · Closure: SOURCE_DIFF + UNIT_TEST + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-001).

**MSC-UNIT-016 — Durable atomic persistence primitive (dir fsync, AtomicFile replacement, `.bak`/residue policy)** · CODE_ROOT_CAUSE · MEDIUM / AC-001 (accidental), AC-009 LOW, AC-005 (lost rename) / — · HIGH · no parent-dir fsync in 3 writers; `AtomicFile.finishWrite` swallows fsync+rename failure; `.bak` auto-restore; `.new`/`.tmp` residue; `clear()` ignores results · ROOT-007 c1/c4/c6, AS-CAND-002, CS-006, ARCH-003 · AC-001, AC-009, AC-005 · `AtomicFileWriter.kt:15-26`, `CryptoBridge.writeFileAtomic:783-794`, `FileRegistrationSessionStore.kt:28-78` · PRE_B004 · AS-B / S3 (+S2 for `writeFileAtomic`) · MFT: all three writers together; MNFA: fsync in `AtomicFileWriter` while store keeps `AtomicFile.finishWrite` · breaker C4 · A: real-class temp-dir: rename failure throws; `.bak` never restored (deleted); `.new` cleaned at startup; parent-dir fsync invoked (mock FD) · I: `kill -9` between write and rename · P: P12, P13 · Retest: Android/Storage · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PHYSICAL_GRAPHENEOS_TEST(P12/P13) + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-009, AC-001).

**MSC-UNIT-017 — Fail-closed first-run resolver + binding-marker integrity (client half of AC-001)** · CODE_ROOT_CAUSE · MEDIUM (HIGH at B004 unless S1 frozen) / **AC-001 HIGH**, AC-014 / — · VERY_HIGH · absent/`0x00`/v1-garbage marker ⇒ unbound; no cross-check against Keystore aliases; unauthenticated 6-byte marker; public `clearBinding()`; marker rollback not detected · ROOT-007 c2/c5/c7, ROOT-011 (marker slice), CS-009/C-013, ARCH-003 · AC-001, AC-014 · `FileDeviceAuthBindingStore.kt:37-66`, `DeviceAuthKeyStateResolver.kt:20-32`, `RegistrationOrchestrator.kt:246-254` · PRE_B004 · AS-B (+AS-D marker slice) / S3 · MFT: 017∧014∧015∧016∧028(S1/S2)∧033; MNFA: marker fix without empty-file/key-missing downgrades; client resolver without server uniqueness; **ARCHITECTURE_PREREQUISITE_REQUIRED (033 first-run definition)** · breakers C1, C5 · A: resolver truth table: marker absent ∧ any anoX alias present ⇒ NOT first run (explicit reset only); HMAC-alias marker; "HMAC key missing ⇒ bound"; payload corruption fails closed · I: alias-present/marker-absent on device · P: P4, P5, P13 · Retest: Android/Storage + Auth/DPoP + Attackchain · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PHYSICAL_GRAPHENEOS_TEST + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-001 A+B).

**MSC-UNIT-018 — Armed-latch lifecycle: `RejectedAfterArm` state + reset path ordering** · CODE_ROOT_CAUSE (+LIFECYCLE_CONTRACT) · LOW / AC-014 LOW (feeds AC-001/A) / — · HIGH · `commit()` `Rejected` persists `Failed` over `CommitArmed` via direct `save` (bypasses `failStep`); transient vs permanent rejection undefined; only exit `clearBinding()` · AS-CAND-001, LEGACY-INTEGRATION-003 (PARTIALLY_EFFECTIVE), C-016 (permablock), ARCH-003 · AC-014 · `RegistrationOrchestrator.kt:216-232,302-310`, `RegistrationState.kt`, `FileDeviceAuthBindingStore.kt:58-61` · Contract PRE_B004; code B004 wiring (pull-forward into S3 recommended once 026/033 frozen) · AS-B (+AS-E reset) / S3 or S5 · MFT: rejection-class contract (026) ∧ `RejectedAfterArm` ∧ reset deletes DeviceAuth alias BEFORE marker; MNFA: clearing marker on `Rejected` alone (converts AC-014 into AC-001/A); **ARCHITECTURE_PREREQUISITE_REQUIRED** · breakers C13, S17 · A: `Rejected` after arm never overwrites `CommitArmed`; all state mutation via one guarded path (no direct `save` bypass); reset ordering test · I: marker + session end state after rejected commit · Retest: Android/Storage · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-014) + ARCHITECTURE_AUTHORITY_UPDATE.

**MSC-UNIT-019 — Local envelope AAD/type/version binding (registration, wrapped-key, crypto type tag)** · CODE_ROOT_CAUSE · MEDIUM / AC-005, AC-001 (marker slice via 017) / — · HIGH · registration envelope no AAD (version byte unauthenticated); wrapped K_STATE no AAD/version; identity vs session same key+AAD; no object type tag · ROOT-011 (registration/marker slice), C-009/CS-018 (domain separation part), CJ ROOT-011 evidence · AC-005, AC-001 · `RegistrationSessionKey.kt` (encrypt/decrypt), `CryptoBridge.wrapStateKey`, `serialization.rs:68` (CJ-C AAD hook) · PRE_B004 (before any second envelope version exists) · AS-D + CJ-C / S2 (crypto hook) + S3 (Kotlin envelopes) · MFT: with 009 (AAD hook) · breaker C12 · A: AAD = type‖version‖context; cross-type substitution fails at GCM tag; v1→v2 migration reads v1 once, `UNSUPPORTED_VERSION` distinct · Retest: Android/Storage + Crypto/JNI · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + INDEPENDENT_SPECIALIST_RETEST.

**MSC-UNIT-020 — Identity/session anti-rollback via server epoch echoed into local AAD** · CLIENT_SERVER_CONTRACT + CODE_ROOT_CAUSE · MEDIUM (HIGH at B008 without epoch) / AC-005 / — · HIGH · no freshness anywhere; AEAD authenticates, does not freshness-bind; Android has no app-accessible monotonic counter → server is the only practical V1 authority · ROOT-011 (identity/session slice), C-009/CS-018 · AC-005 · `serialization.rs`, `CryptoBridge.kt:568-585`, B-006 server (`identity_revision`, publication epoch) · **LATER: B006 (publication epoch) / B008-B009 (session)**; S15 contract entry PRE_B004 via 034 · AS-D + CJ-C/CJ-D ↔ B006 server / S6, S7 · MFT: ROOT-011 ∧ freshness source ∧ server authority; MNFA: local counter without trustworthy authority · breakers S15, S13, S14, C12 · A: old valid envelope rejected after newer epoch persisted; publish→ACK→mark→rollback→re-publish rejected by synthetic server; session rollback detected · I: rollback/AAD tests on provenance-verified `.so` · P: P12 · Retest: Crypto/JNI + Android/Storage (+backend) · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + SYNTHETIC_BACKEND_CONFORMANCE + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-005) + ARCHITECTURE_AUTHORITY_UPDATE (B-006 amendment).

**MSC-UNIT-021 — DPoP binding-by-construction (mandatory jkt/ath; typed `DpopBinding`; factory requires token)** · CODE_ROOT_CAUSE + CLIENT_SERVER_CONTRACT · MEDIUM now / **HIGH at B004** (AC-003 HIGH, cond. CRITICAL) / — · HIGH · `verify()` defaults `expectedJwkThumbprint/accessToken/expectedNonce = null`; factory mirrors; default per-instance replay cache; attacker-key proof `Valid` · ROOT-008 (binding component), ARCH-006 (attacker key passes self-report), CS-007/C-006, MAINARCH-005 (ES256 conformance) · AC-002, AC-003, AC-004 (mirror) · `DpopProofVerifier.kt:25-29,42-49,131,140,150`, `DpopProofFactory.kt:35-39` · PRE_B004 (client API); server S7/S8 at B004 · AD-B / S4 · MFT: ROOT-008 ∧ all B-004 call sites ∧ 026; MNFA: jkt at one call site while defaults remain; **mandatory ath without mandatory jkt** (harness [5]) · breakers S7 (single point for AC-003), S8, C9 · A: compile-level: `verify` cannot be invoked without a binding; attacker-key proof with correct `ath` ⇒ `KEY_BINDING_MISMATCH` on every token-bearing endpoint; factory refuses token-bearing call without token · Retest: Auth/DPoP + backend security · Closure: SOURCE_DIFF + UNIT_TEST + SYNTHETIC_BACKEND_CONFORMANCE + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-003).

**MSC-UNIT-022 — HTU/HTM canonicalization contract (raw path, port elision, no userinfo; lock-step client/server)** · CODE_ROOT_CAUSE + CLIENT_SERVER_CONTRACT · MEDIUM / AC-002 MEDIUM / — · VERY_HIGH · decoded `URI.getPath()`; `%2F/%3F/%23/%00` decoded into signed claim; double-decoding; userinfo retained; HTM unvalidated · ROOT-009, CS-008/C-007 · AC-002 · `DpopHtu.kt:29-35`, `DpopProofVerifier.kt:91`, `DpopHtuTest` · PRE_B004 (contract + client); server rule at B004 · AD-C / S4 · MFT: ROOT-009 ∧ 026 htu rule ∧ collision rows; MNFA: raw path without frozen server rule; **ARCHITECTURE_PREREQUISITE_REQUIRED** · breakers S12 (single point), C9 · A: `/v1/a%2Fb` ≠ `/v1/a/b` both directions with/without jkt; `%3F/%23/%00/%2520` rows; default-port/trailing-slash interop rows; HTM allow-list · Retest: Auth/DPoP · Closure: SOURCE_DIFF + UNIT_TEST + SYNTHETIC_BACKEND_CONFORMANCE + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-002) + ARCHITECTURE_AUTHORITY_UPDATE (B-007 htu rule).

**MSC-UNIT-023 — Replay state scope and bound (shared atomic `(jkt,jti)` store; no default cache)** · CLIENT_SERVER_CONTRACT + CODE_ROOT_CAUSE · MEDIUM / AC-004 MEDIUM / — · HIGH · per-instance in-memory cache; unbounded (1,000,000 jti retained); lost on restart · ROOT-008 (replay scope), CS-019 (replay growth), C-006 · AC-004, AC-011 · `DpopReplayCache.kt:29-57`, `InMemoryDpopReplayCache.kt`, `DpopProofVerifier.kt:27` · Contract PRE_B004; server impl B004 · AD-D / S4 (interface) + S5 (server) · MFT: 023∧024 (shared store ∧ retention source); MNFA: shared store without iat/monotonic retention · breaker S10 · A: two-verifier shared-store reject; restart persistence; per-key bound · Retest: backend security + Auth/DPoP · Closure: SOURCE_DIFF + UNIT_TEST + SYNTHETIC_BACKEND_CONFORMANCE + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-004).

**MSC-UNIT-024 — Replay retention time source (iat/monotonic; rollback-safe eviction)** · CODE_ROOT_CAUSE (SERVER_CONTRACT) · LOW / AC-004 / — · HIGH (reproduced) · wall clock shared by freshness and retention; eviction assumes monotonic insertion; rollback −250 s re-accepts evicted jti · AD-CAND-003 · AC-004 · `DpopReplayCache.kt:34-56`, `DeviceAuthClock.kt:16-18`, `DpopProofVerifier.kt:116-124,150` · Contract entry PRE_B004 (026); server impl B004 · AD-D / S4 + S5 · MFT: with 023 · breaker S11 · A: rollback −250 s ⇒ replay rejected; retention keyed by iat+tolerance or monotonic source · Retest: backend security · Closure: SOURCE_DIFF + UNIT_TEST + SYNTHETIC_BACKEND_CONFORMANCE + INDEPENDENT_SPECIALIST_RETEST.

**MSC-UNIT-025 — Nonce lifecycle contract** · ARCHITECTURE_CONTRACT_GAP · CONTRACT (CHAIN_RELEVANT AC-003/004) · HIGH · `/v1/auth/challenge` semantics, `DPoP-Nonce`, `use_dpop_nonce` retry, scope/TTL, client storage undefined · AD-GAP-001, MAINARCH-008 (new gaps) · AC-003, AC-004, AC-010 · none yet (client nonce plumbing, `DpopHtu`, `RegistrationApi`) · PRE_B004 (freeze) / B004 (impl) · AD-D / S0 (+S4 client plumbing shape) · MNFA: nonce field without server nonce state · breaker S9 · A: authority validator asserts contract presence; conformance tests once implemented · Retest: Architecture consistency · Closure: ARCHITECTURE_AUTHORITY_UPDATE + UNIT_TEST (validator) + later SYNTHETIC_BACKEND_CONFORMANCE.

**MSC-UNIT-026 — Server DPoP/registration verifier contract (umbrella)** · ARCHITECTURE_CONTRACT_GAP / SERVER_CONTRACT · CONTRACT (**CHAIN_CRITICAL**: AC-002/003/004/009/014) · HIGH · canonical htu form, replay key `(jkt,jti)`, TTL/monotonic source, mandatory ath/jkt, registration idempotency on `(registration_id, jkt)`, transient-vs-permanent rejection taxonomy absent · AD-GAP-002, MAINARCH-008 · AC-002, AC-003, AC-004, AC-009, AC-010, AC-014 · none yet · PRE_B004 (freeze) / B004 (impl) · AD-C + AD-D / S0 · breakers S4, S7, S8, S10, S11, S12, S17 · A: authority validator; conformance suite at B004 · Retest: Architecture consistency + backend security · Closure: ARCHITECTURE_AUTHORITY_UPDATE + UNIT_TEST (validator) + SYNTHETIC_BACKEND_CONFORMANCE (B004).

**MSC-UNIT-027 — Registration proof-of-possession contract + client API shape** · CODE_ROOT_CAUSE + CLIENT_SERVER_CONTRACT · MEDIUM / AC-010 MEDIUM, AC-009 / — · HIGH · PoP exists only as endpoint-table row; opaque untyped proof; JWK and proof independently supplied; `commitRegistration(id, grant)` carries no PoP/DPoP/Idempotency · AD-CAND-001, LEGACY-INTEGRATION-001 (PARTIALLY_EFFECTIVE), ARCH-003, MAINARCH-008, MAINARCH-019 (eligibility at call sites retest) · AC-010, AC-009 · `RegistrationOrchestrator.kt:46,114,167-232`, `RegistrationApi.kt:30-51` · PRE_B004 (contract + typed API); server verification B004 · AD-F (+AD-B) / S0 + S4 · MFT: 027∧028∧025; MNFA: PoP parameter without defining what it signs; **ARCHITECTURE_PREREQUISITE_REQUIRED** · breakers S5, C10 · A: typed PoP over `registration_id‖grant-hash‖nonce‖JWK‖identity-material-hash` at submit-device-auth, submit-public-identity AND commit; idempotency key present; JWK-in-proof == submitted JWK; synthetic server rejects missing PoP / second JWK · Retest: Auth/DPoP + Architecture · Closure: ARCHITECTURE_AUTHORITY_UPDATE + SOURCE_DIFF + UNIT_TEST + SYNTHETIC_BACKEND_CONFORMANCE + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-010).

**MSC-UNIT-028 — Device/JKT/account server binding invariants (schema-enforced)** · ARCHITECTURE_CONTRACT_GAP / SERVER_CONTRACT · CONTRACT (**CHAIN_CRITICAL**: server half of AC-001) · HIGH · `UNIQUE(device_auth_keys.public_key)` absent from V1.2 schema (verified); JKT→device_id immutability, known-key re-registration rejection, `identity_public_keys` immutability enforcement, device_id retention not explicit · AD-GAP-003, ARCH-004 (schema authority drift enables it) · AC-001, AC-008, AC-010, AC-014→001 · none yet (B-005 schema, B-004 pipeline) · PRE_B004 (freeze as B-spec/schema amendment) / B004+B005 (impl) · AD-F / S0 · MFT: with 017 (client resolver) — MNFA: server UNIQUE without client resolver (Variant B + denial-without-reset remain) · breakers S1, S2, S3, S16 · A: authority validator; synthetic backend: known JWK rejected; JKT→device_id immutable; second identity publication for device rejected · Retest: Architecture + backend security + Attackchain · Closure: ARCHITECTURE_AUTHORITY_UPDATE + SYNTHETIC_BACKEND_CONFORMANCE + ATTACKCHAIN_RETEST(AC-001/A, AC-010, AC-008).

**MSC-UNIT-029 — DeviceAuth key-creation race / alias overwrite / StrongBox-catch delete** · CODE_ROOT_CAUSE · LOW / AC-011, AC-010(iii) / — · HIGH · check-then-act `createKeyIfAbsent`; `generateKeyPair` overwrites alias; `catch(Exception)` deletes alias unconditionally; orchestrator unsynchronized · AD-CAND-002, C-014 (DeviceAuth component), CS-016 (catch-block delete — does NOT revive ROOT-016) · AC-011, AC-010 · `AndroidKeystoreDeviceAuthKeyManager.kt:48-57,106-118` · B004 implementation-time (NON_BLOCKING; pull-forward into S3 recommended — same pattern as 014) · AD-A / S3 or S5 · MFT: with AS-A serialized creation · breaker C2 (part) · A: concurrent `createKeyIfAbsent` ⇒ one key; StrongBox failure never deletes a pre-existing alias · I: alias-overwrite negative test · Retest: Android/Storage or Auth/DPoP · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-011).

**MSC-UNIT-030 — Best-effort zeroization / secret residency** · STANDALONE_HARDENING · LOW / AC-015 LOW / — · HIGH · pickle JSON plaintext, K_STATE copies, plaintext copies not zeroized in Rust; Kotlin `stateKey`/`out`/codec/grant never cleared; `Identity/Session::zeroize` no-op; `panic=abort` skips Drop · ROOT-010, CJ-CAND-005, CS-011/C-010, CS-019 (abort) · AC-015 · `serialization.rs:36-54`, `lib.rs:88-116`, `CryptoBridge.kt:337,340,366,526,553,622`, `FileRegistrationSessionStore.kt:51,57` · **LATER: B008/B009** · CJ-F + AS-C / S7 · MNFA: before 005 (handle redesign first) · breaker C14 · A: review-based + best-effort `fill(0)`/`zeroize` assertions; remove unused K_STATE copy at `:622` · Retest: Crypto/JNI · Closure: SOURCE_DIFF + UNIT_TEST + INDEPENDENT_SPECIALIST_RETEST (severity not inflated).

**MSC-UNIT-031 — Truthful cross-domain wipe implementation** · CODE_ROOT_CAUSE · LOW / AC-008 MEDIUM / — · HIGH · `wipeLocalCrypto` ignores delete results, returns Success; misses `.tmp/.new`, noBackupFilesDir files, DeviceAuth + session-key aliases, live handles; `clear()` ignores results; master alias recreated on next `getInstance()` (via 014) · ROOT-012, ARCH-009, MAINARCH-030, CS-010/C-011 · AC-008, AC-014 (reset) · `CryptoBridge.kt:737-754`, `FileRegistrationSessionStore.clear`, `FileDeviceAuthBindingStore`, `RegistrationSessionKey` (no delete), missing orchestrator · **LATER: B013 (+B006 S16) + FINAL_PRODUCT_GATE retest** · AS-E / S8 · MFT: orchestrator ∧ all aliases/files/residue ∧ per-item truthful result ∧ marker-last; MNFA: files without aliases (or vice versa); **ARCHITECTURE_PREREQUISITE_REQUIRED (032)** · breakers C11, S16, S18 · A: wipe enumerates 5 domains + residue + 3 aliases; partial failure reported; marker last · I: wipe + alias enumeration on device · P: wipe completeness (P17) · Retest: Android/Storage + Architecture · Closure: SOURCE_DIFF + UNIT_TEST + INSTRUMENTED_TEST + PHYSICAL_GRAPHENEOS_TEST + INDEPENDENT_SPECIALIST_RETEST + ATTACKCHAIN_RETEST(AC-008).

**MSC-UNIT-032 — Wipe/logout/account-delete storage contract + explicit reset path** · ARCHITECTURE_CONTRACT_GAP / LIFECYCLE_CONTRACT · CONTRACT (CHAIN_RELEVANT AC-008/014) · HIGH · per-operation domain matrix, deletion order (marker last), truthful vs best-effort semantics, alias lifecycle (`anox.b003.session.v1` never deleted), call authority for destructive primitives, B-013 reset path · AS-GAP-002, ARCH-009, MAINARCH-030, MAINARCH-014 (license-expiry restricted flow — revalidate at B013), S18 · AC-008, AC-014 · `wipeLocalCrypto`, `deleteKeyDestructively`, `clearBinding`, `clear()` · PRE_B004 (contract) / B013 (impl) / FINAL (ROOT-012) · S0 → AS-E · A: authority validator · Retest: Architecture + Android/Storage · Closure: ARCHITECTURE_AUTHORITY_UPDATE + UNIT_TEST (validator).

**MSC-UNIT-033 — Registration-store / binding-marker / first-run authority contract** · ARCHITECTURE_CONTRACT_GAP · CONTRACT (**CHAIN_CRITICAL** AC-001/014) · HIGH · no authority defines marker states ABSENT/ARMED/BOUND/CLEARED/CORRUPT, durability incl. dir fsync, empty/corrupt/key-missing taxonomy, first-run vs Keystore-alias presence, armed-latch release, single-process assumption · AS-GAP-001 · AC-001, AC-014 · `FileDeviceAuthBindingStore.kt`, `FileRegistrationSessionStore.kt`, `RegistrationOrchestrator.kt`, `DeviceAuthKeyStateResolver.kt` · PRE_B004 (freeze) · S0 → AS-A/AS-B · MFT: with 026 (rejection classes), 028 · A: authority validator; conformance tests · Retest: Architecture consistency · Closure: ARCHITECTURE_AUTHORITY_UPDATE + UNIT_TEST (validator).

**MSC-UNIT-034 — Backup/restore/D2D/app-data-clear/reinstall/profile expected-state + anti-rollback authority contract** · ARCHITECTURE_CONTRACT_GAP · CONTRACT (CHAIN_RELEVANT AC-001 restore, AC-005, AC-013) · HIGH · expected states after `pm clear`/restore, Keystore-survival assumption, profile policy, Seedvault/D2D, server as rollback/uniqueness authority (S15) not frozen · AS-GAP-003 · AC-001, AC-005, AC-013 · manifest/extraction rules, resolver, `getLocalStateStatus` · PRE_B004 (contract) / PHYSICAL FINAL · S0 → AS-F/AS-D · MFT: with 028 (Auth GAP-003) · A: authority validator; lint disposition · P: P4, P5, P8, P10, P11 · Retest: Architecture + Physical campaign owner · Closure: ARCHITECTURE_AUTHORITY_UPDATE + PHYSICAL_GRAPHENEOS_TEST.

**MSC-UNIT-035 — UUID RFC 4122 variant validation** · STANDALONE_HARDENING · LOW / none / — · HIGH · `UuidV4.parse` checks version only; NCS-variant accepted; KDoc overclaims · ROOT-015, LEGACY-B003-001, ARCH-008 (UUID half), CS-014/C-016 (lenient) · none (standalone) · `UuidV4.kt:28,316-330` · FINAL_PRODUCT_GATE (trivially cheap; may land in S3 as hardening; matters at B004 server-response parse) · S3 (hardening) / Final closure · A: variant == 2 asserted; NCS-variant rejected; IdentifierTest rows · Retest: Android/Storage · Closure: SOURCE_DIFF + UNIT_TEST + INDEPENDENT_SPECIALIST_RETEST.

**MSC-UNIT-036 — Master Physical GrapheneOS campaign (evidence vacuum)** · PHYSICAL_VERIFICATION · META (CLOSURE_RISK_ENABLING_CONDITION) / AC-013 INFO / — · HIGH · Keystore survival, StrongBox/TEE level, backup agents, power-loss durability, file modes never measured on any binary, let alone a provenance-verified one · AC-013, MAINARCH-018, ARCH-006 (physical part), AD/AS/AC physical requirement lists · AC-013, AC-001 (resolver input), AC-008, AC-009, AC-003 (hardware level) · none · **LATER: PHYSICAL GRAPHENEOS FINAL** (prereq 001) · AS-G / S10 · MNFA: any physical run before 001 (tests stale binary) · breaker P1–P17 · P: master campaign below · Retest: Physical GrapheneOS + Build/Supply · Closure: PHYSICAL_GRAPHENEOS_TEST + BUILD_ARTIFACT_HASH_PROOF (binary used) + EVIDENCE preserved.

**MSC-UNIT-037 — Native retest revalidation set on provenance-verified binary** · SECURITY_EVIDENCE_GAP · META / AC-012 / — · VERY_HIGH · every historical native closure and all runtime native observations are provisional; `LEGACY-CRYPTO-005`, `MAINARCH-031` closures rest on source/JVM only · MAINARCH-031, LEGACY-CRYPTO-005, LEGACY-INTEGRATION-002/005, ARCH-001/008 (retest requirement), BUILDSC remediation order step 6 · AC-012 · n/a (evidence) · PRE_B004 (**NATIVE_RETEST_ACCEPTANCE**) · S10 (after S1+S2) · MNFA: retest on any non-CI-provenance binary · I: instrumented suites incl. the two `BufferTooSmall` tests, concurrency tests, handle tests on produced binary both ABIs · Retest: Crypto/JNI + Build/Supply · Closure: PROVENANCE_VERIFIED_NATIVE_RUNTIME + INSTRUMENTED_TEST + INDEPENDENT_SPECIALIST_RETEST; findings remain Closed/Open as canonical — this unit only re-establishes runtime evidence.

**MSC-UNIT-038 — Machine-enforced verification matrix / closure-evidence gate (B-021)** · SECURITY_EVIDENCE_GAP / LIFECYCLE_CONTRACT · HIGH (ARCH-002 canonical; META) / AC-012 (enabler) / — · HIGH · B-021 matrix rows NOT_RUN/UNVERIFIED do not fail closed; no validator consumes it; CS-003/CS-004 survived every green gate · ARCH-002, CS-021 alert-fatigue precursor (context) · AC-012 · `tools/audit/*` (new validator), `b021_verification_matrix.jsonl`, CI · PRE_B004 (B-004 blocking per ARCH audit) · S1 · breaker: validator fails closed on any pre_product_required row not PASS with evidence · A: validator negatives; closure-state-machine enforcement (§Closure) · Retest: Architecture + Build/Supply · Closure: SOURCE_DIFF + UNIT_TEST + ARCHITECTURE_AUTHORITY_UPDATE + INDEPENDENT_SPECIALIST_RETEST.

**MSC-UNIT-039 — Governance hygiene decisions pending Human Owner** · LIFECYCLE_CONTRACT · INFO/META / none / — · HIGH · (a) superseded SHA-pinned one-shot validators fail permanently (alert fatigue); (b) Audit-001 executed on Opus 5 Medium (MODEL_DEVIATION preserved; no Audit-001-only finding admitted without arbiter confirmation); (c) ARCH-010 positive INFO to be retired at B004 start · CS-021/C-017, Audit-001 model deviation, ARCH-010 · none · `tools/audit/*` historical validators · Human decision before remediation start (NON_BLOCKING for product security) · S0 (decision record) · Retest: Architecture (governance) · Closure: ARCHITECTURE_AUTHORITY_UPDATE (decision recorded).

**MSC-UNIT-040 — DB schema authority single source of truth (B-005)** · ARCHITECTURE_CONTRACT_GAP · CONTRACT (canonical HIGH) / AC-001 enabling / — · HIGH · `DATABASE_ARCHITECTURE.md`/`BACKEND_ARCHITECTURE.md` vs `DB-SCHEMA-V1-FROZEN` contradiction; no home for `UNIQUE(public_key)` · ARCH-004 · AC-001 (enabling) · docs only · PRE_B004 for the auth-schema portion (S1/S2 need a schema home); B005 for the rest · S0 · A: authority validator (single frozen schema source) · Retest: Architecture · Closure: ARCHITECTURE_AUTHORITY_UPDATE.

**MSC-UNIT-041 — Attachment secretstream chunked streaming / size-enforcement boundary** · ARCHITECTURE_CONTRACT_GAP · CONTRACT (canonical MEDIUM) / none / — · HIGH · SPECIFIED_NOT_IMPLEMENTED; no libsodium dependency · ARCH-005 · none · none · **LATER: B-012 attachments implementation gate** · — · A: authority validator + conformance at B012 · Retest: Architecture · Closure: ARCHITECTURE_AUTHORITY_UPDATE + later tests.

**MSC-UNIT-042 — Hardware-level trust model / attestation decision (server cannot validate self-reported StrongBox/TEE)** · ARCHITECTURE_CONTRACT_GAP · CONTRACT (canonical MEDIUM) / AC-003 potential / — · HIGH · B-002 v1.1 says no attestation V1; eligibility is client self-report; software-key attacker client passes · ARCH-006, CS-103 · AC-003, AC-013 · `AndroidKeystoreDeviceAuthKeyManager.kt:151-178` (self-report) · PRE_B004 contract decision (accept self-report with S2 key-derived identity, or require attestation); impl LATER; P1 physical · S0 · A: authority validator · P: P1 · Retest: Architecture + Physical · Closure: ARCHITECTURE_AUTHORITY_UPDATE + PHYSICAL_GRAPHENEOS_TEST(P1).

**MSC-UNIT-043 — ROOT-016 destructive Keystore deletion from catch block** · REJECTED_NOT_A_FINDING · — · REJECTED · unreachable for a bound/armed key (`Present` early return + `requireCreationAllowed`; verified by Auth, Storage, Attackchain) · ROOT-016, CS-016 · none · — · **REMAINS REJECTED — DO NOT REVIVE**. The pre-binding race is tracked separately as unit 029.

**MSC-UNIT-044 — BUILDSC-012 (cargo-ndk API 21 vs minSdk 26; duplicate crate versions; `panic="abort"`)** · REJECTED_NOT_A_FINDING · INFO · — · `panic=abort` is the safer FFI choice; document under unit 004; not a defect · BUILDSC-012, CS-019 (abort note) · none.

---

## ROOT-001 THROUGH ROOT-018 ARBITRATION

| Root | Verdict | Evidence / rationale |
|---|---|---|
| ROOT-001 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE (HIGH exploitability / **CRITICAL evidence-integrity**) | Byte-identical old-source rebuild; disassembly −0x2 vs −0xb; every native chain inherits it; AC-012 fired once. Normalized into **three dependent units** (001 provenance, 002 verification vacuum, 003/004 supply chain) — not one — because they have different closure evidence and gates; evidence-integrity criticality kept explicit, not hidden behind runtime severity. |
| ROOT-002 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE HIGH | Singleton never stored; distinct closure test (`assertSame`); MNFA singleton alone. |
| ROOT-003 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE HIGH | TOCTOU + `&mut` aliasing + 7/100 reuse; `Send+Sync` feasibility. |
| ROOT-004 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE HIGH | Identity slice Pre-B004; session dimension tracked as distinct later-gate unit 012. |
| ROOT-005 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE HIGH (corroboration MEDIUM) | vodozemac-level mechanism proven; CJ-CAND-001 kept adjacent, not merged. |
| ROOT-006 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE MEDIUM | Consumer taxonomy separated into unit 015 so closure cannot happen by fixing `decrypt` alone. |
| ROOT-007 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE MEDIUM (HIGH at B004 unless S1 frozen) | Now 7 components; normalized into durability (016) + resolver/marker (017) + taxonomy (015); AD-GAP-003 reaffirmed as server half. |
| ROOT-008 | **SPLIT_REQUIRED** (binding 021 / replay scope 023) · severity CONFIRMED_NO_CHANGE MEDIUM/HIGH@B004 | Two components with different breakers (S7 vs S10) and different retest owners. |
| ROOT-009 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE MEDIUM | Single point S12 for AC-002. |
| ROOT-010 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE LOW | Not inflated by AC-015. |
| ROOT-011 | **SPLIT_REQUIRED** (registration/marker AAD slice 019 + marker freshness in 017 — Pre-B004; identity/session anti-rollback 020 — B006/B008) · severity CONFIRMED MEDIUM | Storage specialist placed the slices at different gates; forcing one unit would either block B004 on B006 work or under-gate the marker slice. |
| ROOT-012 | **SPLIT_REQUIRED** (implementation 031 / contract 032) · CONFIRMED LOW component, chain MEDIUM | Contract half is Pre-B004 (GAP-002); implementation is B013. |
| ROOT-013 | KEEP_AS_DISTINCT_ROOT · **SEVERITY_CHANGE_PROPOSED LOW → MEDIUM** | See below. |
| ROOT-014 | KEEP_AS_DISTINCT_ROOT · CONFIRMED_NO_CHANGE MEDIUM | Ordering constraint (after ROOT-003) preserved as MNFA. |
| ROOT-015 | KEEP_AS_DISTINCT_ROOT (standalone) · CONFIRMED_NO_CHANGE LOW | No chain found by any specialist; not dropped. |
| ROOT-016 | **REJECTED_REMAINS_REJECTED** | Three later specialists re-verified the guard; no new contrary evidence. AD-CAND-002 is a pre-binding race, explicitly not a revival. |
| ROOT-017 | KEEP_AS_DISTINCT_ROOT · classification proposed below | Not merged into ROOT-001: provenance can be fixed while instrumented tests still never run. |
| ROOT-018 | **SPLIT_REQUIRED** (Pre-B004 hygiene 003 / RC controls 004) | BuildSC placed 007/010/004-doc at Pre-B004 and the rest at RC. |

## ROOT-013 SEVERITY ARBITRATION
**PROPOSED FINAL ROOT-013 SEVERITY = MEDIUM** (component). Rationale grounded in component evidence, not chain participation: (1) `cryptoDeserialize*`/`cryptoCreateOutboundSession` collapse `UnsupportedVersion`, wrong key, GCM tamper, malformed JSON and wrong type into `0` → Kotlin `CorruptedIdentityState`, which is the input to a destructive-recovery decision (Inv.23) — a control-flow fail-open, not a diagnostic nuisance; (2) stale/destroyed handle and bad argument share −1, so callers retry with stale handles (the precursor to wrong-object operation); (3) OTK-store state reported as `InvalidSession` (−3) misroutes recovery. AC-006 HIGH and AC-007 MEDIUM are not inherited; MEDIUM is the standalone component value. Consensus LOW recorded as superseded-by-later-evidence, not rewritten.

## ROOT-017 CLASSIFICATION ARBITRATION
Type `SECURITY_EVIDENCE_GAP` (meta root, unit 002). Component severity: N/A (no exploit). **Evidence-integrity severity: HIGH** (every native, storage and DeviceAuth instrumented claim is unverified; two committed tests would fail against the shipped binary; it is the enabler that let AC-012 fire once). Chain role: ENABLING (AC-012, AC-013). Gate: **PRE_B004 precondition** (native cross-build + instrumented JNI/storage/auth suites in CI on both ABIs, on a provenance-verified `.so`). Storage's `MEDIUM_ENABLING_CONDITION` for its slice is subsumed (the whole-of-system enabling condition is HIGH). Closure: INSTRUMENTED_TEST in CI + PROVENANCE_VERIFIED_NATIVE_RUNTIME + INDEPENDENT_SPECIALIST_RETEST; does not close by adding tests that run against a stale binary.

## ROOT-016
**Remains `REJECTED_NOT_A_FINDING`. DO NOT REVIVE.** No extraordinary contrary proof exists; three independent specialists verified the guard at source `:48-57`.

---

## CRYPTO/JNI CANDIDATE ARBITRATION
| Candidate | Verdict |
|---|---|
| CJ-001 OTK count/set semantics + discarded `{created,removed}` | **DISTINCT MSC UNIT (011)**; Pre-B004; must ship with 009/010. |
| CJ-002 Session pickle growth | **DISTINCT MSC UNIT (012)**, later gate B008/B009; code lands with 009 (same ABI), closure separate. |
| CJ-003 Deserialize/outbound `0` collapse | MERGE INTO ROOT-013 (unit 007) — same root (no error channel); consumer change mandatory. |
| CJ-004 Unbounded generation / growth / `removed` | **DISTINCT MSC UNIT (013)**; B006 gate; cap recommended in S2. |
| CJ-005 Transient buffers | MERGE INTO ROOT-010 (unit 030). |
| CJ-006 Mapping hygiene + invalid string heuristic | DIAGNOSTIC SUB-ITEM of unit 007; heuristic ban recorded as FCP-1. |

## AUTH/DPOP CANDIDATE ARBITRATION
| Candidate | Verdict |
|---|---|
| AD-001 Registration PoP contract/API drift | **DISTINCT MSC UNIT (027)** — distinct root (contract absent; API predates V1.2), related to ROOT-008 family only by "binding optional". |
| AD-002 DeviceAuth key creation race | **DISTINCT MSC UNIT (029)**; gives Audit-002 C-014 a concrete root; NON_BLOCKING; coordinate with unit 014 (same pattern). |
| AD-003 Wall-clock replay retention | **DISTINCT MSC UNIT (024)** — time-source root, not restated scope; MFT with 023. |

## ANDROID/STORAGE CANDIDATE ARBITRATION
| Candidate | Verdict |
|---|---|
| AS-001 Armed-latch lifecycle | **DISTINCT MSC UNIT (018)** — lifecycle-contract root (opposite direction to ROOT-007 marker semantics); not merged. |
| AS-002 AtomicFile write primitive | MERGE INTO ROOT-007 component 4 (unit 016) — same remediation (replace/guard the primitive); retains its own closure tests (rename throws; `.bak` never restored). |

## ARCHITECTURE GAP ARBITRATION
All six survive as **distinct contract units** — none merged behind a code fix:
AD-GAP-001 → 025 KEEP DISTINCT · AD-GAP-002 → 026 KEEP DISTINCT (umbrella; CHAIN_CRITICAL) · AD-GAP-003 → 028 KEEP DISTINCT (CHAIN_CRITICAL; tied to ARCH-004/040) · AS-GAP-001 → 033 KEEP DISTINCT (CHAIN_CRITICAL) · AS-GAP-002 → 032 KEEP DISTINCT · AS-GAP-003 → 034 KEEP DISTINCT (carries S15).

## ARCHITECTURE-FIRST CONTROL
`ARCHITECTURE_PREREQUISITE_REQUIRED` is set on: 017 (first-run definition — 033), 018 (rejection classes — 026/033), 021 (mandatory bindings — 026), 022 (htu rule — 026), 023/024 (replay key/TTL/source — 026), 025 (nonce), 027 (PoP payload — 027 contract + 028 + 025), 028 (schema home — 040), 031 (wipe contract — 032), 020 (epoch authority — 034/B-006). No code change in these units may be accepted before the corresponding contract is frozen.

---

## HISTORICAL REMEDIATION ARBITRATION

| Historical finding | Original status | Later relation | Consolidated interpretation | Remediation implication |
|---|---|---|---|---|
| ANOX-LEGACY-CRYPTO-005 | Closed | Kotlin lock inert (ROOT-002); Rust half unshipped (ROOT-001) | **INEFFECTIVE_REMEDIATION** (both mechanisms) + REQUIRES_PHYSICAL_REVALIDATION | units 005/006 fix; 037 runtime retest; not reopened here |
| ANOX-LEGACY-INTEGRATION-001 | Closed | local revalidation present; commit PoP absent (V1.2 drift) | **PARTIALLY_EFFECTIVE** | unit 027 |
| ANOX-LEGACY-INTEGRATION-002 | Closed | ordering correct; functionally blocked by 4096 | **EFFECTIVE** (ordering) + REQUIRES_PHYSICAL_REVALIDATION (never exercised at default count) | unit 009 instrumented retest; 037 |
| ANOX-LEGACY-INTEGRATION-003 | Closed | `failStep`/expiry guarded; direct `save(Failed)` on `Rejected` bypasses | **PARTIALLY_EFFECTIVE** (Pattern 3) | unit 018 |
| ANOX-LEGACY-INTEGRATION-005 | Open | registry validates membership only | never fixed — **SUPERSEDED** by ROOT-003/014 as active roots | units 005/008; 037 |
| ANOX-LEGACY-B003-001 | Open | same root as ROOT-015 | **SUPERSEDED** (same root) | unit 035 |
| ANOX-LEGACY-ANDROIDSEC-001 | Closed | string class-name matching still effective | **EFFECTIVE** | regression watch in 007/014 |
| ANOX-MAINARCH-023 | Closed | wrapped-key read paths fixed; wrapping alias created per `getInstance()`; `serialize*` getOrCreate | **PARTIALLY_EFFECTIVE** (Pattern 2) | unit 014 |
| ANOX-MAINARCH-031 | Closed | Rust half not in shipped artifact | **FALSE_CLOSURE** (artifact-level; fired AC-012 instance) | units 001, 007; 037 runtime retest |
| ANOX-SECURITY-ARCH-007 | Open | fixed in CryptoBridge deserialize paths; identical pattern in `RegistrationSessionKey.decrypt` and `initializeMasterKey` | **INEFFECTIVE_REMEDIATION_SCOPE** (Pattern 2) | unit 014 (enumeration closure) |
| ANOX-MAINARCH-013 | Open | expanded; "byte-identical rebuild" note superseded | EFFECTIVE (finding open) — supporting note SUPERSEDED | units 001/003/004 |
| ANOX-MAINARCH-018 | Open | no physical evidence; pre-rebuild evidence invalid | **REQUIRES_PHYSICAL_REVALIDATION** | unit 036 |
| ANOX-MAINARCH-030 | Open | no cross-domain wipe | still open, EFFECTIVE as finding | units 031/032 |
| ANOX-SECURITY-ARCH-009 | Open | wipe truthfulness is a distinct new root | STILL_EFFECTIVE + related new root | units 031/032 |
| ANOX-SECURITY-ARCH-003 | Open | state machine better than recorded; primitives beneath unsound | STILL_EFFECTIVE, expanded | 014/015/016/017/018/027 |
| ANOX-SECURITY-ARCH-001 | Open | TOCTOU + aliasing UB; lock inert | STILL_EFFECTIVE, expanded (severity CRITICAL was recommended by Audit-001; consolidated component HIGH retained, chain HIGH) | 005–008 |
| ANOX-SECURITY-ARCH-008 | Open | mapping enumerated; UUID variant | STILL_EFFECTIVE, expanded (MEDIUM for error half via ROOT-013) | 007, 035 |
| ANOX-MAINARCH-005 / -019 | Closed | still effective | **EFFECTIVE** | conformance retest in 021 / 027,029 |
| ANOX-MAINARCH-008 | Closed (doc) | doc effective; nonce/htu/PoP contracts absent | **PARTIALLY_EFFECTIVE** (doc layer only) | 025/026/027 |
| ANOX-MAINARCH-014 | Closed (doc) | no client impl | **SUPERSEDED** (NO_LONGER_APPLICABLE) | revalidate at B013 via 032 |
| PROMPT-008 §7 "corrupt session → NotStarted is safe" | historical prompt | superseded except empty-file remnant | **SUPERSEDED** | unit 015 |

No original closure status is rewritten by this consolidation.

## FALSE-CLOSURE PREVENTION RULES
`FALSE_CLOSURE_PREVENTION_RULES` (inputs to the Remediation Coverage Gate):
- **FCP-1 (Pattern 1 — source changed, runtime unchanged):** no unit touching `crypto/rust` or the JNI ABI may reach `IMPLEMENTED`+ without `PROVENANCE_VERIFIED_NATIVE_RUNTIME` + `BUILD_ARTIFACT_HASH_PROOF` from the same CI run; re-committing a hand-built `.so` is forbidden; the `"Output buffer too small"` string-presence heuristic is prohibited as evidence (disassembly/runtime only); no physical or instrumented result from a non-provenance-verified binary is admissible.
- **FCP-2 (Pattern 2 — equivalent path survives):** closure of any "read must not create" / "existing-only" / "fail-closed guard" unit requires an **enumeration test over all equivalent call sites** (all Keystore-creating paths: `RegistrationSessionKey.getOrCreateKey`, `initializeMasterKey`, `getOrCreateStateKey` callers, `createKeyIfAbsent`; all three atomic writers; all `save()` callers). Single-site diffs never close (ARCH-007/MAINARCH-023 precedent).
- **FCP-3 (Pattern 3 — alternate direct mutation):** state-transition guards must live at the single mutation primitive (store), not per transition; closure requires a test that no caller can persist a downgrade outside the guarded path (`RejectedAfterArm` precedent, LEGACY-INTEGRATION-003).
- **FCP-4 (Pattern 4 — component fixed, chain survives):** a chain participant may not reach `CLOSED` until every chain it participates in has `ATTACKCHAIN_RETESTED` PASS; client-half and server-half units close together or the chain stays open (AC-001: C1 ∧ S1; AC-003: C9 ∧ S7).
- **FCP-5 (default-safety):** for API-default units (021, 023) closure requires a compile-level/negative test that the insecure invocation is impossible — not a test that the secure invocation works.
- **FCP-6 (constant/lock-only fixes):** raising `4096`, adding a Kotlin lock, clearing a marker, or making `ath` mandatory alone is never closure; the coupled unit set (MFT lists) must close together.
- **FCP-7 (evidence separation):** implementer ≠ retest authority; `/tmp` artifacts are non-authoritative; runtime evidence only from CI-built, hash-manifested binaries; closure evidence preserved in the hash-bound registry before status change.
- **FCP-8 (matrix enforcement):** unit 038's validator must fail closed on any `pre_product_required` row lacking preserved evidence; a green CI is never closure evidence by itself (ARCH-002, AC-012).

---

## ATTACKCHAIN → MSC UNIT MAPPING

| Chain | Normalized units | Chain sev | Breakpoints | Gate | Whole-chain test | Retest owners |
|---|---|---|---|---|---|---|
| AC-001 | 017, 014, 015, 016, 019, 028, 033, 034 (+036 physical) | HIGH | C1 or S1 (A); C1+C3+C4 (A+B); defense in depth all three | PRE_B004 (client+contract) | commit → delete marker + empty/corrupt session + keep alias (fake) + synthetic server S1 ⇒ `reserve()` fails closed AND server rejects; Variant B still fail-closed; instrumented pm-clear-partial; P4/P5/P13 | Storage + Auth + Attackchain + Physical |
| AC-002 | 022, 021, 026 | MEDIUM | S12/C9 (single point) | PRE_B004 contract | collision rows rejected both sides ± jkt; interop rows accepted | Auth/DPoP |
| AC-003 | 021, 026, 025, 042 | HIGH (cond. CRITICAL) | **S7** (single point) + C9 | PRE_B004 contract + B004 impl | attacker-key + correct ath ⇒ `KEY_BINDING_MISMATCH` everywhere; API uncallable without binding | Auth/DPoP + backend |
| AC-004 | 023, 024, 026, 025 | MEDIUM | S10 ∧ S11 | PRE_B004 contract; server B004 | shared store two verifiers + restart + rollback −250 s rejected | backend + Auth |
| AC-005 | 020, 019, 010, 011, 009, 012, 016, 034 | MEDIUM (HIGH at B008) | S15 (+C12); S13/S14; C7/C8; C4 | LATER B006/B008 | old envelope rejected after newer epoch; publish→ACK→rollback→re-publish rejected; session rollback detected | Crypto/JNI + Storage |
| AC-006 | 005, 006, 007, 008, 015, 014 | HIGH | C6 (+C3) | PRE_B004 | instrumented: stale handle ⇒ `HANDLE_STALE_GENERATION`; concurrent ops serialized; version bump ≠ corrupted | Crypto/JNI (+Storage consumer) |
| AC-007 | 009, 010, 011, 013, 007, 001, 008 | MEDIUM | C7 ∧ C8 | PRE_B004 | default-count step succeeds; uploaded set == `created` unique; count consistent after publish | Crypto/JNI |
| AC-008 | 031, 032, 014, 028 | MEDIUM | C11 (+S16, S18) | LATER B013 + B006 + Final | wipe 5 domains + 3 aliases + residue, marker last; server revokes; second identity publication rejected | Storage + Architecture |
| AC-009 | 016, 027, 026 | LOW | C4 (+S4) | PRE_B004 | rename failure throws; planted `.bak` ignored; kill −9 matrix (P12) | Storage |
| AC-010 | 027, 029, 028, 026, 025, 019 | MEDIUM | S5 (+C10) | PRE_B004 contract | synthetic server rejects submit-identity/commit without PoP from registered JKT; second JWK rejected | Auth + Architecture |
| AC-011 | 006, 029, 014, 023 | MEDIUM | C2 ∧ C6 | PRE_B004 | `assertSame`; concurrent `createKeyIfAbsent` ⇒ one key; concurrent stores cannot both create | Crypto/JNI + Storage |
| AC-012 | 001, 002, 003, 038 | HIGH (governance) | in-run hash gate | PRE_B004 precondition (CURRENTLY_REACHABLE) | gate fails on hash mismatch; `BufferTooSmall` instrumented tests pass on produced binary | Build/Supply |
| AC-013 | 036, 002, 034 | INFO (enabling) | P1–P17 on verified binary | FINAL/PHYSICAL | campaign below | Physical + Build/Supply |
| AC-014 | 018, 033, 026, 032 | LOW | C13 ∧ S17 | PRE_B004 contract + B004 wiring | `Rejected` after arm never overwrites `CommitArmed`; reset deletes alias before marker | Storage |
| AC-015 | 030, 008 | LOW | C14 (after C6) | LATER B008/B009 | review + best-effort `fill(0)` assertions | Crypto/JNI |

`ATTACKCHAINS WITHOUT MSC UNIT = 0`.

## HIGH CHAIN CHALLENGE
- **AC-001 — HIGH_CHAIN_CONFIRMED.** Component evidence E2 valid (harness [17]–[21], [M2]–[M8]); severity justified: fail-open key-reuse across accounts violates Inv.2 and V1.2 §B-005.3 with a **non-malicious minimum actor (A8)**; existing mitigations (ARMED/BOUND marker) only work when the marker survives, which is exactly the failing precondition. Minimum breaker C1 (client) — S1 alone terminates Variant A only. Minimum MSC set: 017 + 015 + 014 + 016 (client) ∧ 028 + 033 (contract).
- **AC-003 — HIGH_CHAIN_CONFIRMED.** Mechanics E2 ([4]–[7]); `ath` alone proven insufficient; single point S7. No current mitigation. Minimum MSC set: 021 + 026 (+025 for freshness). Severity stays HIGH (requires a specific backend mistake plus token theft).
- **AC-006 — HIGH_CHAIN_CONFIRMED.** E1 source + E2 components (7/100 reuse; −9→0). Impact wrong-object crypto + destructive recovery. Type-separate registries and leak-masking do not break it (masking is exactly what ROOT-014 cleanup would remove). Minimum breaker C6; minimum set 005 + 007 + 006 + 008 (ordered), 015 consumer.
- **AC-012 — HIGH_CHAIN_CONFIRMED** (governance/evidence-integrity, CURRENTLY_REACHABLE, fired once). Existing `validate_apk_contents.py` proven bypassable; documented hash not machine-checked. Minimum breaker: in-run hash manifest; minimum set 001 (+002, 038).

## AC-003 CONDITIONAL CRITICAL OVERLAY
**Overlay remains VALID: `CONDITIONAL_CRITICAL_AT_B004_IF_VERIFIER_DEFAULTS_PORTED`; canonical severity remains HIGH.** The impact (full impersonation for token TTL, effectively unbounded via `/v1/auth/token` re-issuance) would be CRITICAL if the defaults were ported; the likelihood component (backend mistake + token theft) keeps the canonical rating HIGH. No CRITICAL is counted in the global distribution. The overlay converts to a hard CRITICAL only if B004 implementation is shown to port nullable bindings — which unit 021's compile-level test makes structurally impossible.

---

## SERVER BREAKER COVERAGE (S1–S18)

| S | Invariant | MSC unit | Gate | Chains | Synthetic/backend test |
|---|---|---|---|---|---|
| S1 | UNIQUE(`device_auth_keys.public_key`) + known-key rejection | 028 | contract PRE_B004 / impl B004+B005 | AC-001/A, AC-010, AC-014→001 | known JWK re-registration rejected |
| S2 | JKT→device_id→account immutable; context from validated key | 028 | same | AC-001/A, AC-003 | device_id derivation unique per key |
| S3 | one_active_device_per_account + "one wins" | 028 | present; conformance B004 | same-account dup | race test |
| S4 | idempotency on (registration_id, jkt); commit idempotent | 026 (+027) | contract PRE_B004 / B004 | AC-009 | replayed submit/commit idempotent |
| S5 | typed registration PoP at all three steps; JWK-in-proof == JWK | 027 | contract PRE_B004 / B004 | AC-010, AC-001 partial | reject unbound proof |
| S6 | ES256 over embedded jwk; P-256 only | 021 | baseline; conformance | baseline | alg/curve negatives |
| S7 | **mandatory jkt binding** | 021 / 026 | contract PRE_B004 / B004 | AC-003 (single point), AC-002 | attacker-key proof rejected everywhere |
| S8 | mandatory ath when token presented | 021 / 026 | same | AC-003 | missing/incorrect ath rejected |
| S9 | nonce at issuance / DPoP-Nonce / use_dpop_nonce | 025 | contract PRE_B004 / B004 | AC-003, AC-004 | nonce round-trip |
| S10 | shared atomic replay store (jkt,jti) | 023 | same | AC-004 | two replicas + restart |
| S11 | retention keyed by iat/monotonic, bounded | 024 | same | AC-004 | rollback −250 s |
| S12 | canonical raw-path htu | 022 | same | AC-002 | collision rows |
| S13 | otk_id-keyed idempotent publication; same id≠key = error | 010 (+011) | B-006 present; conformance B006 | AC-005, AC-007 | duplicate/omitted publication rejected |
| S14 | consumed-OTK enforcement (CLAIMED terminal) | 020 (+010) | B006 | AC-005 | re-claim rejected |
| S15 | publication/rollback epoch echoed to client | 020 (contract via 034) | contract PRE_B004 / B006 | AC-005 | rollback re-publish rejected |
| S16 | identity_public_keys immutability at publish | 028 | contract PRE_B004 / B006 | AC-008 | second identity for device rejected |
| S17 | rejection-class taxonomy | 026 (+018) | contract PRE_B004 / B004 | AC-014 | transient vs permanent surfaced |
| S18 | device revocation on account-delete/wipe intent | 032 | contract PRE_B004 / B013 | AC-008 | device revoked after wipe intent |

```
SERVER BREAKERS TOTAL = 18
UNASSIGNED SERVER BREAKERS = 0
```

## CLIENT BREAKER COVERAGE (C1–C14)

| C | Control | MSC unit | Fix group | Chains | Test |
|---|---|---|---|---|---|
| C1 | fail-closed first-run resolver | 017 | AS-B | AC-001, AC-014→001 | resolver truth table |
| C2 | no key creation on read; serialized creation | 014 (+029) | AS-A/AS-C/AD-E/AD-A | AC-001, AC-008, AC-011 | call-site enumeration |
| C3 | typed storage errors → not-first-run | 015 | AS-A/AS-B | AC-001, AC-006/B | taxonomy tests |
| C4 | dir fsync; AtomicFile guard; empty ⇒ exception | 016 | AS-B | AC-001, AC-009, AC-005 | real-class temp-dir |
| C5 | marker HMAC; "HMAC key missing ⇒ bound" | 017 | AS-B | AC-001 malicious | marker integrity tests |
| C6 | slot+generation handles; HANDLE_* codes; narrowed CryptoNative; singleton | 005 (+007, 006) | CJ-A/B/E | AC-006, AC-011 | instrumented stale-handle |
| C7 | native-allocated output with caps | 009 (+012) | CJ-C | AC-007, AC-005 | size tests |
| C8 | stable KeyId OTK surface | 010 (+011) | CJ-D | AC-007, AC-005 | uploaded == created |
| C9 | safe-by-construction DPoP API; raw-path htu | 021 (+022, 023) | AD-B/C/D | AC-002, AC-003, AC-004 | compile-level binding |
| C10 | typed registration PoP + idempotency key | 027 | AD-F | AC-010, AC-009 | wire-shape tests |
| C11 | truthful cross-domain wipe | 031 | AS-E | AC-008, AC-014 reset | wipe enumeration |
| C12 | local AAD type‖version‖context | 019 (+020) | AS-D/CJ-C | AC-005 | substitution fails at tag |
| C13 | RejectedAfterArm; no save(Failed) over CommitArmed | 018 | AS-B | AC-014 | transition test |
| C14 | best-effort zeroization + lifetime cleanup | 030 (+008) | CJ-F/AS-C | AC-015 | fill(0) assertions |

```
CLIENT BREAKERS TOTAL = 14
UNASSIGNED CLIENT BREAKERS = 0
```

---

## CROSS-GROUP DEPENDENCIES (preserved + evidence-supported additions)
Preserved: AS-A/AS-B ↔ AD-E/AD-F (AC-001) · CJ-C/CJ-D ↔ AS-D ↔ B006 server (AC-005) · CJ-B ↔ AS-C (AC-006/B) · AS-B ↔ AD-F (AC-009/014) · AS-E ↔ AD-F/B013 (AC-008) · AD-B ↔ AD-C ↔ AD-D (one DPoP contract) · Build/Supply → all CJ-* closure/retests.
Added (evidence): **Build/Supply → physical campaign and all instrumented storage/auth retests** (AC-013, MAINARCH-018) · **Contract freeze (025/026/027/028/032/033/034) → acceptance of AD-B/AD-C/AD-D/AS-B/AS-E code** (Inv.35) · **040 (schema authority) → 028** (S1/S2 need a frozen schema home; ARCH-004 enabling for AC-001) · **038 (matrix enforcement) → any unit CLOSED** (ARCH-002/AC-012) · **S3 → S4 file ordering** (`RegistrationOrchestrator.kt` touched by both storage and DPoP sessions) · **S2 owns `CryptoBridge.kt`** for the storage AS-C parts (no parallel edits).

## REMEDIATION DEPENDENCY GRAPH
Nodes are decomposed into `IMPL:` / `VERIFY:` / `ARCH:` / `PHYSICAL:` / `GATE:` so that "implement → test infrastructure → closure" relations do not form cycles (`A → B` = B must not be accepted before A):
```
IMPL:040(schema authority) → ARCH:S0-CONTRACT-FREEZE(025,026,027c,028,032,033,034,042,018c,020c)
ARCH:S0 → IMPL:017, IMPL:018, IMPL:021, IMPL:022, IMPL:023, IMPL:024, IMPL:027, IMPL:031, IMPL:020
IMPL:001(provenance) → IMPL:002(instrumented CI) → VERIFY:001, VERIFY:002, VERIFY:037
IMPL:001 → VERIFY:005/006/007/008/009/010/011/012/013 (all native closures)   IMPL:001 → VERIFY:036(physical)
IMPL:038(matrix validator) → VERIFY:* (any CLOSED)
IMPL:005 → IMPL:007 → IMPL:006 → IMPL:008 (cleanup LAST; 005 → 008 mandatory)
IMPL:009 → IMPL:010, IMPL:011, IMPL:012, IMPL:013, IMPL:019(crypto AAD hook)   IMPL:007 → IMPL:015(crypto consumer)   IMPL:005 → IMPL:030
IMPL:014 → IMPL:015 → IMPL:017 ; IMPL:016 → IMPL:017 → IMPL:018 ; IMPL:019 → IMPL:020 ; IMPL:014, IMPL:016 → IMPL:031
IMPL:017 → IMPL:027 (file overlap) ; IMPL:021 → IMPL:022, IMPL:023 → IMPL:024
IMPL:014,015,016,017,028 → VERIFY:AC-001 ; IMPL:021,026 → VERIFY:AC-003 ; IMPL:005,008 → VERIFY:AC-006 ; IMPL:001 → VERIFY:AC-012
VERIFY:AC-001, VERIFY:001 → PHYSICAL:P-CAMPAIGN → GATE:FINAL
B004 impl (S1–S12,S17 server) → VERIFY:AC-002/003/004/010 server halves ; B006 → VERIFY:AC-005 ; B013 → VERIFY:AC-008
```
Cycle check executed on the modeled graph (58 edges): **`UNRESOLVED DEPENDENCY CYCLES = 0`.** The only apparent cycle (001 needs 002's instrumented tests for closure, 002 needs 001's binary) is resolved by the IMPL/VERIFY decomposition above.

---

## PROVISIONAL LARGE FIX SESSIONS (proposals only — nothing implemented)

**S0 — CONTRACT FREEZE (Architecture)** · Objective: freeze every cross-component contract before any code that depends on it · Units: 025, 026, 027 (contract), 028, 032, 033, 034, 040 (auth-schema portion), 042 (trust decision), 018 (rejection classes/RejectedAfterArm), 020 (S15 epoch entry), 039 (human decisions recorded) · Sources: AD-GAP-001/002/003, AD-CAND-001 contract, AS-GAP-001/002/003, ARCH-004/006, S1–S18 as B-spec amendments · Chains: AC-001/002/003/004/005/008/009/010/014 · Files: `docs/authority/*` (B-spec amendment), authority validators under `tools/audit` · Prerequisites: none (parallel to S1) · Model: Claude Fable 5.1 High · SEC-B · Tests in session: authority validators asserting contract presence (fail closed) · Must NOT include: any product code, any schema SQL · Independent retest: Architecture consistency retest.

**S1 — BUILD PROVENANCE + EVIDENCE GATES (Build/Supply)** · Units: 001, 002, 003, 038 · Sources: ROOT-001/017/018 slice, BUILDSC-001/002/003/006/007/008/010/004-doc, ARCH-002, MAINARCH-013 · Chains: AC-012, AC-013 (enabler) · Files: `rust-toolchain.toml`, `ci.yml` (cross-build ×2 reproducibility, symbol parity, native manifest, emulator instrumented job arm64+x86_64, lint/audit/secret-scan gates), `android/build.gradle.kts` (jniLibs from build output; fail if committed `.so` present), `validate_apk_contents.py` v2, B-021 matrix validator, `REPOSITORY_SECURITY_POLICY.md` · Prerequisites: none · Model: Fable 5.1 High · SEC-B · Tests: gate negatives (hash mismatch, injected `.so`, wrong ABI, binary PEM); existing instrumented suites executed on the produced binary (two `BufferTooSmall` tests expected PASS — this alone re-establishes MAINARCH-031 runtime evidence) · Must NOT include: any Rust/Kotlin behaviour change in `crypto/` (so provenance repair and behaviour change are never conflated — FCP-1); no `.so` re-commit · Independent retest: Build/Supply.

**S2 — JNI ABI REVISION (Crypto/JNI + CryptoBridge persistence hygiene)** · Units: 005 → 007 → 006 → 009/010/011 (+012 code, 013 cap, 019 crypto AAD hook) → 008 last; AS-C parts of 014/015/016 (`initializeMasterKey` create-only, `serialize*` existing key, `LocalStateStatus` taxonomy, `writeFileAtomic` dir fsync/residue) · Sources: ROOT-002/003/004/005/013/014, CJ-CAND-001…004/006, ARCH-001/007(crypto)/008, LEGACY-CRYPTO-005/INTEGRATION-005 · Chains: AC-006, AC-007, AC-011, AC-005 (client half), AC-015 (prep) · Files: `crypto/rust/src/*`, `CryptoNative.kt`, `CryptoBridge.kt`, `CryptoError.kt`, `CryptoBridgeLocalE2eeIdentityStep.kt`, `CryptoInstrumentedTest.kt`, module split for `internal` visibility · Prerequisites: S1 merged (CI builds the binary the tests run on); 013 replenishment policy left to B006 · Model: Fable 5.1 High · SEC-B · Tests in session: host-testable slab registry; error-code injectivity table; `assertSame`; exact-size serialization 0/20/100/5000 OTK and 29.9 KB session; KeyId ordering/uniqueness; count/set consistency after publish; cap; instrumented stale-handle/concurrency/version tests · Must NOT include: ROOT-014 cleanup before ROOT-003; larger constant alone; publish semantics beyond the KeyId surface; any `android/src/main` storage files other than none (owned by S3) · Independent retest: Crypto/JNI on provenance-verified binary (unit 037).

**S3 — REGISTRATION / STORAGE FOUNDATION (Android/Storage + AD-E/AD-A)** · Units: 014 (RegistrationSessionKey half), 015, 016, 017, 019 (registration + wrapped-key AAD), 018 (if 026/033 frozen — recommended), 029 (recommended pull-forward), 035 (hardening) · Sources: ROOT-006/007/011 slice/015, AS-CAND-001/002, AD-CAND-002, ARCH-003, CS-005/006/009/015/017, LEGACY-INTEGRATION-003, LEGACY-B003-001 · Chains: AC-001 (client half), AC-009, AC-011, AC-014 · Files: `RegistrationSessionKey.kt`, `FileRegistrationSessionStore.kt`, `AtomicFileWriter.kt`, `FileDeviceAuthBindingStore.kt`, `DeviceAuthKeyStateResolver.kt`, `RegistrationOrchestrator.kt`, `RegistrationState.kt`, `RegistrationSessionSecurityException.kt`, `AndroidKeystoreDeviceAuthKeyManager.kt`, `UuidV4.kt`, tests · Prerequisites: S0 (033, 026 rejection classes, 028 for the AC-001 synthetic-server test); runs in parallel with S2 (disjoint files) · Model: Fable 5.1 High · SEC-B · Tests: real-class temp-dir durability; resolver truth table; typed taxonomy; Keystore-creating call-site enumeration (JVM double); concurrent creation; AC-001 whole-chain JVM with synthetic backend S1; AC-009/011/014 chain tests; instrumented negatives added for S1's emulator job · Must NOT include: wipe orchestrator (B013), server code, `CryptoBridge.kt` (S2), DPoP files (S4) · Independent retest: Android/Storage + Auth/DPoP (AD-E) + Attackchain.

**S4 — DPoP / REGISTRATION-API CLIENT HARDENING (Auth/DPoP)** · Units: 021, 022, 023 (client interface), 024 (client interface), 025 (client plumbing shape), 027 (typed API) · Sources: ROOT-008/009, AD-CAND-001/003, AD-GAP-001/002 client side, LEGACY-INTEGRATION-001, MAINARCH-005 · Chains: AC-002, AC-003, AC-004 (client mirror), AC-010, AC-009 · Files: `DpopProofVerifier.kt`, `DpopProofFactory.kt`, `DpopHtu.kt`, `DpopReplayCache.kt`, `DeviceAuthClock.kt`, `RegistrationApi.kt`, `RegistrationOrchestrator.kt:46,114` (after S3), tests · Prerequisites: S0 (026, 025, 027, 028 frozen), S3 merged · Model: Fable 5.1 High · SEC-B · Tests: compile-level non-null binding; attacker-key+ath ⇒ mismatch; collision rows; shared-store + restart + rollback; typed PoP wire shape; AC-002/003/004/010 JVM chain tests with synthetic backend · Must NOT include: server implementation; nonce state; one-site `expectedJwkThumbprint` patches · Independent retest: Auth/DPoP.

**S5 — B004 IMPLEMENTATION-TIME REQUIREMENTS (NOT a remediation session; starts only after Pre-B004 DoD)** · server S1–S12, S17; shared replay store; registration PoP verification; `AuthenticatedDeviceContext` from validated key; 018/029 code if not pulled forward; network security config before first network call · Retest: backend security + Auth/DPoP + Attackchain (AC-002/003/004/010 server halves).

**S6 — B006 OTK / ROLLBACK AUTHORITY** · Units: 013 (replenishment/`removed`), 020 (identity epoch), S13–S15 · Retest: Crypto/JNI + Storage + backend (AC-005).
**S7 — B008/B009 CRYPTO-STATE HARDENING** · Units: 012 (closure), 030, 020 (session slice) · Retest: Crypto/JNI (AC-005 session, AC-015).
**S8 — B013 WIPE / LIFECYCLE** · Units: 031, 018 reset path, S18; MAINARCH-014 revalidation · Prereq 032 frozen · Retest: Storage + Architecture (AC-008).
**S9 — RELEASE-CANDIDATE SUPPLY CHAIN** · Unit 004 (+BUILDSC-011 deferred) · Retest: Build/Supply.
**S10 — VERIFICATION CLOSURE (not a fix session)** · Units 037 (native retest set), 036 (physical campaign), whole-chain replays, legacy/architecture revalidation, fresh full-system re-audit.

## PROPOSED REMEDIATION ORDER (challenged against the DAG)
The suggested Phase 0–8 order is largely confirmed with three corrections: (a) **Phase 0 (contracts) and Phase 1 (build provenance + evidence gates) are independent and should run in parallel**, not serially; (b) **Phase 3 (registration/storage foundation, android module) does not depend on Phase 2 (JNI ABI) except for the `CryptoBridge.kt` AS-C parts, which are assigned to Phase 2 — so Phases 2 and 3 run in parallel after Phase 0/1**; (c) **ARCH-002 matrix enforcement (unit 038) belongs in Phase 1, not Phase 8**, because it is a closure control that every later closure depends on. Final order:
```
P0 S0 CONTRACT FREEZE  ∥  P1 S1 BUILD PROVENANCE + EVIDENCE GATES (incl. 038)
→ P2 S2 JNI ABI REVISION  ∥  P3 S3 REGISTRATION/STORAGE FOUNDATION
→ P4 S4 DPoP/REGISTRATION-API CLIENT HARDENING
→ P4b NATIVE RETEST ACCEPTANCE (037) + instrumented CI green on both ABIs + domain retests + Pre-B004 attackchain retests
→ PRE-B004 DEFINITION OF DONE → B004 (S5 requirements) → B006 (S6) → B008/B009 (S7) → B013 (S8)
→ RC (S9) → PHYSICAL CAMPAIGN (036) → LEGACY/ARCHITECTURE REVALIDATION → FRESH FULL-SYSTEM RE-AUDIT → FINAL OPERATIONAL ACCEPTANCE → HUMAN FINAL PRODUCT GATE
```

---

## PRE-B004 MASTER SET

### A. Architecture / Contract prerequisites (freeze, Inv.35)
025 nonce lifecycle · 026 server verifier contract (S4/S7/S8/S10/S11/S12/S17) · 027 registration PoP contract (S5) · 028 device/JKT/account binding invariants incl. UNIQUE(public_key), JKT→device_id, S16 · 032 wipe/logout/delete contract (design only) · 033 marker/session/first-run/armed-release contract · 034 backup/reinstall/profile/anti-rollback authority (S15 entry) · 040 single schema authority (auth portion) · 042 hardware-level trust decision · 018 rejection-class/RejectedAfterArm contract entry · 039 human governance decisions recorded.

### B. Build / Provenance prerequisites
001 provenance chain (pin, cross-build, reproducibility, symbol parity, manifest, Gradle consumes output, hash gate, validator v2) · 002 instrumented CI both ABIs (crypto 39 + auth 27 + storage 66 + new negatives) · 003 lint/advisory/secret-scan gates + policy-doc correction · 038 machine-enforced verification matrix.

### C. Code remediation prerequisites
005, 006, 007, 008 (ordered) · 009 (identity), 010, 011 · 014 (both halves), 015, 016, 017, 019 · 021, 022, 023 (client interface), 024 (client interface), 027 (typed client API). Recommended pull-forward (not required for DoD): 013 input cap, 018 code, 029, 035.

### D. Verification prerequisites
037 native retest set on provenance-verified binary (LEGACY-CRYPTO-005, MAINARCH-031, ARCH-001/008, LEGACY-INTEGRATION-002/005) · all required JVM + instrumented tests PASS in CI · independent domain retests (Build/Supply, Crypto/JNI, Auth/DPoP, Android/Storage) · attackchain retests AC-001 (client half + synthetic S1), AC-002, AC-003 (client + synthetic), AC-004 (client), AC-006, AC-007, AC-009, AC-010 (synthetic), AC-011, AC-012, AC-014 (contract + code if pulled forward) · architecture consistency retest of all frozen contracts.

### E. B004 implementation-time requirements (not Pre-B004 remediation)
Server enforces S1–S12, S17; shared atomic replay store with iat/monotonic retention; registration PoP verification at submit-device-auth, submit-public-identity, commit; `AuthenticatedDeviceContext` from validated key only; nonce issuance; 018 `RejectedAfterArm` code (if not pulled forward); 029 serialized key creation (if not pulled forward); network security configuration; conformance suite for units 021–028.

## PRE-B004 DEFINITION OF DONE (proposed gate criteria — NOT executed)
```
all Pre-B004 MSC units (A–D) IMPLEMENTED (code) or FROZEN (contract) as appropriate
Critical open                          = 0   (currently 0; AC-003 overlay must not have converted)
High Pre-B004 open                     = 0   (001, 005, 006, 009, 010, 011, 038)
Medium Pre-B004 open                   = 0   (003, 007, 008, 014, 015, 016, 017, 019, 021, 022, 023, 027) unless explicitly accepted by Human Owner with evidence
all architecture prerequisites (A) frozen and validator-asserted
all native runtime evidence produced from a provenance-verified, CI-built binary (001) — no hand-built .so in tree
instrumented suites PASS in CI on arm64-v8a AND x86_64 (002); JVM suites PASS
unit 037 native retest set PASS; unit 038 matrix validator PASS with no NOT_RUN pre_product_required rows
independent Pre-B004 specialist retests PASS (Build/Supply, Crypto/JNI, Auth/DPoP, Android/Storage, Architecture)
Pre-B004 attackchains broken and retested: AC-001(client+contract), 002, 003(client+contract), 004(client+contract), 006, 007, 009, 010(contract), 011, 012, 014(contract)
FCP-1..8 satisfied for every closed unit; closure state machine stages recorded
unassigned security items = 0; every LATER item carries a named gate
```

## LATER-GATE MASTER SET
| Gate | MSC units | Notes |
|---|---|---|
| **B006** | 013 (replenishment/`removed`), 020 (identity epoch, S13–S15), 010/011 server conformance | AC-005 identity leg |
| **B008/B009** | 012 (session sizing closure), 030 (zeroization), 020 (session rollback detection) | AC-005 session leg, AC-015 |
| **B012** | 041 (attachments) | not chain relevant |
| **B013** | 031 (wipe implementation), 018 reset path, S18; MAINARCH-014 revalidation | AC-008, AC-014 |
| **RELEASE CANDIDATE** | 004 (verification-metadata, locking, cargo-deny, JDK freeze, remap/strip, SBOM, attestation, R8 keep, signing procedure; BUILDSC-011 deferred) | AC-012 A7 variant |
| **PHYSICAL GRAPHENEOS FINAL** | 036 (P1–P17), 034 physical half, 042 P1, MAINARCH-018 | prereq 001 |
| **FINAL PRODUCT GATE / OPERATIONAL ACCEPTANCE** | 035 (ROOT-015), 031 retest (ROOT-012), whole-chain final replay set, fresh full-system re-audit, retest of all Pre-B004 units on provenance-verified binary, ARCH-010 retirement | — |
| **Human decision (pre-remediation)** | 039 | governance only |
`LATER ITEMS WITHOUT NAMED GATE = 0`.

---

## CLOSURE EVIDENCE STANDARD
Allowed classes: SOURCE_DIFF · UNIT_TEST · INSTRUMENTED_TEST · PROVENANCE_VERIFIED_NATIVE_RUNTIME · SYNTHETIC_BACKEND_CONFORMANCE · INDEPENDENT_SPECIALIST_RETEST · ATTACKCHAIN_RETEST · PHYSICAL_GRAPHENEOS_TEST · ARCHITECTURE_AUTHORITY_UPDATE · BUILD_ARTIFACT_HASH_PROOF. Minimum per type: CODE_ROOT_CAUSE → SOURCE_DIFF + UNIT_TEST + INDEPENDENT_SPECIALIST_RETEST (+INSTRUMENTED/PROVENANCE if native or Keystore/file-system; +ATTACKCHAIN_RETEST if chain participant; +PHYSICAL if listed) · ARCHITECTURE_CONTRACT_GAP / SERVER_CONTRACT / CLIENT_SERVER_CONTRACT → ARCHITECTURE_AUTHORITY_UPDATE + validator UNIT_TEST (+SYNTHETIC_BACKEND_CONFORMANCE when implemented) · BUILD_PROVENANCE / SUPPLY_CHAIN → SOURCE_DIFF + BUILD_ARTIFACT_HASH_PROOF + gate negatives + INDEPENDENT_SPECIALIST_RETEST · SECURITY_EVIDENCE_GAP → INSTRUMENTED_TEST in CI + PROVENANCE_VERIFIED_NATIVE_RUNTIME · PHYSICAL_VERIFICATION → PHYSICAL_GRAPHENEOS_TEST + BUILD_ARTIFACT_HASH_PROOF of the tested binary. **A finding cannot close solely because code changed.** Per-unit requirements are listed in the MSC table.

## CLOSURE STATE MACHINE
```
FOUND → CONSOLIDATED → ASSIGNED → IMPLEMENTED → AUTOMATED_TESTED → RUNTIME_TESTED [if native/Keystore/FS; else NOT_APPLICABLE]
→ INDEPENDENTLY_RETESTED → ATTACKCHAIN_RETESTED [if chain participant; else NOT_APPLICABLE]
→ PHYSICAL_VERIFIED [if unit lists P-items; else NOT_APPLICABLE] → EVIDENCE_PRESERVED (hash-bound registry) → CLOSED
```
Rules: no silent jumps; `NOT_APPLICABLE` must be declared per unit at ASSIGNED time and confirmed by the retest owner; contract units use IMPLEMENTED = "frozen in authority", AUTOMATED_TESTED = "validator asserts presence", RUNTIME_TESTED = conformance at implementation gate; a unit regresses to IMPLEMENTED if its ATTACKCHAIN_RETEST fails; unit 038's validator enforces stage ordering (FCP-8).

## INDEPENDENT RETEST MATRIX
| Owner | Units |
|---|---|
| Build/Supply | 001, 002, 003, 004, 037, 038 (shared), 036 (binary provenance) |
| Crypto/JNI | 005, 006, 007, 008, 009, 010, 011, 012, 013, 019 (hook), 020, 030, 037 |
| Auth/DPoP | 014 (AD-E), 017 (shared), 021, 022, 023, 024, 025, 026, 027, 029 |
| Android/Storage | 014, 015, 016, 017, 018, 019, 020 (shared), 029, 031, 032, 035, 036 (P-campaign design) |
| Attackchain | AC-001/003/006/012 mandatory; AC-005/008/010; recommended set; cross-domain units 017, 021, 028 |
| Architecture | 025, 026, 027, 028, 032, 033, 034, 038, 039, 040, 041, 042; contract-freeze consistency |
| Physical GrapheneOS | 036, 034, 042 (P1), 016 (P12/P13), 017 (P4/P5/P13), 014 (P3), 031 (P17) |
| Backend security (at B004+) | 021, 023, 024, 026, 028 server halves |
The implementer of a session is never the sole retest authority for its units.

## WHOLE-CHAIN RETESTS
Mandatory final replay: **AC-001, AC-003, AC-006, AC-012, AC-005, AC-008, AC-010**. Recommended: AC-002, AC-004, AC-007, AC-011, AC-014. Component-tested + physical: AC-009 (P12), AC-013 (campaign), AC-015. All 14 synthesis tests from the Attackchain report retained verbatim as the chain-test inventory; chain tests are never replaced by component unit tests. Native-participating chains only on a provenance-verified binary.

## FINAL FULL-SYSTEM REAUDIT SET
All 42 open units re-verified on a provenance-verified binary; mandatory chain replay set above; legacy/architecture revalidation of the 26 historical/architecture findings (table above) with no status rewrite outside the canonical freeze process; Auth 40/40 and Storage 42/42 architecture matrices re-scored; physical campaign results; fresh independent full-system security audit (new SHA) before Final Operational Acceptance.

---

## MASTER PHYSICAL CAMPAIGN (deduplicated; prerequisite: PROVENANCE_VERIFIED_BINARY from unit 001)
| # | Requirement | Feeds |
|---|---|---|
| P1 | StrongBox/TEE level for all 3 aliases (`KeyInfo.securityLevel`; never SOFTWARE; TEE fallback observed on non-StrongBox device) | 042, MAINARCH-018, AC-003 |
| P2 | DeviceAuth non-exportability (`privateKey.encoded == null`; `getKeySpec` throws) | B-002 |
| P3 | RegistrationSessionKey create-on-read (delete alias with valid session; `load()`; alias inventory) — expected after fix: `KEY_MISSING`, no alias created | 014 |
| P4 | `pm clear` from bound state → all aliases/files absent → `AbsentNotBound`; **record any alias survival** | 017, 034, AC-001 |
| P5 | uninstall/reinstall (as P4) | 017, 034 |
| P6 | reboot — bound state unchanged | 016 |
| P7 | OS update — bound state unchanged | 034 |
| P8 | secondary/work profile isolation; profile deletion leaves Owner unaffected | 034 |
| P9 | Keystore invalidation on lock-screen change/removal (none expected; user-auth off) | B-002 |
| P10 | backup/restore Seedvault incl. D2D-style option — no anoX file restored | 034, AC-001 restore |
| P11 | device-to-device transfer — no files | 034 |
| P12 | abrupt process kill (`kill -9`) during commit between `save(CommitArmed)`/`markArmed`/remote — resume matrix | 016, AC-009, AC-005 |
| P13 | power-loss durability after `markArmed()` returns (repeat N×) — marker present every time | 016, 017, AC-001 |
| P14 | file mode bits — `stat` all anoX files/dirs 0600/0700 | LOCAL_DEVICE_SECURITY |
| P15 | Keystore DER→JOSE ES256 on real provider verified by an **independent** verifier (exclude Nimbus self-consistency) | 021 |
| P16 | wall-clock ±10 min — server rejection and nonce/retry recovery; replay/rollback assumptions | 024, 025, AC-004 |
| P17 | wipe/logout/delete completeness — alias enumeration + residue after wipe; `status()`; server revocation | 031, AC-008 |

---

## ARCHITECTURE COVERAGE
```
Auth/DeviceAuth requirements:   40 / 40 mapped   UNMAPPED = 0
Android/Storage requirements:   42 / 42 mapped   UNMAPPED = 0
```
Every finding referenced by a matrix row (ROOT-002/006/007/008/009/010/011/012/013/015/017, AD-CAND-001/002/003, AD-GAP-001/002/003, AS-CAND-001/002, AS-GAP-001/002/003, ARCH-003/006, MAINARCH-018/019, ROOT-016 note) has an MSC owner; rows scored IMPLEMENTED_AND_VERIFIED carry no finding and need no unit. All 10 `ANOX-SECURITY-ARCH-*` and all 9 tracked `ANOX-MAINARCH-*` have dispositions.
## ARCHITECTURE FINDING COVERAGE LOSS
**0**

## LEGACY CODE/FINDING COVERAGE
| Legacy area | Historical finding(s) | Normalized unit(s) | Gate | Retest |
|---|---|---|---|---|
| B002 DeviceAuth | MAINARCH-005, -019, -008, -014; ARCH-006; AD-CAND-002 | 021, 027, 029, 042, 025/026, 032 | PRE_B004 / B004 / B013 | Auth/DPoP; Architecture |
| B003 Registration | LEGACY-INTEGRATION-001/-003; LEGACY-B003-001; ARCH-003 | 027, 018, 035, 014–017 | PRE_B004 (+B004 wiring; Final for 035) | Auth + Storage + Attackchain |
| CryptoBridge | LEGACY-CRYPTO-005 (Kotlin half); MAINARCH-023; ARCH-007; LEGACY-ANDROIDSEC-001 | 006, 014, 007 | PRE_B004 | Crypto/JNI + Storage |
| Rust/JNI | LEGACY-CRYPTO-005 (Rust half); LEGACY-INTEGRATION-005; MAINARCH-031; ARCH-001/-008 | 005, 007, 008, 009, 037 | PRE_B004 + NATIVE_RETEST_ACCEPTANCE | Crypto/JNI on verified binary |
| Local persistence | ARCH-009; MAINARCH-030; LEGACY-INTEGRATION-002 | 016, 019, 031, 032, 009 | PRE_B004 / B013 / Final | Storage |
| DeviceAuth binding (marker) | ARCH-003 (CS-009); AS-CAND-001 | 017, 018, 033 | PRE_B004 | Storage + Attackchain |
| RegistrationSessionKey | ARCH-007 (scope); ROOT-006 | 014, 015, 019 | PRE_B004 | Storage + Auth |
| Historical native artifact remediation | MAINARCH-013; MAINARCH-031; LEGACY-CRYPTO-005 | 001, 002, 037, 038 | PRE_B004 precondition | Build/Supply |
## LEGACY FINDINGS WITHOUT CURRENT OWNER
**0**

---

## PROPOSED MASTER SEVERITY DISTRIBUTION (per MSC unit, component severity; overlays noted)
```
CRITICAL      = 0   (evidence-integrity CRITICAL overlay on 001; AC-003 conditional overlay — neither counted as a CRITICAL unit)
HIGH          = 7   (001, 005, 006, 009, 010, 011, 038)
MEDIUM        = 16  (003, 004, 007, 008, 012, 013, 014, 015, 016, 017, 019, 020, 021, 022, 023, 027)
LOW           = 6   (018, 024, 029, 030, 031, 035)
INFO/META     = 4   (002 [EI HIGH], 036, 037, 039)
CONTRACT_GAPS = 9   (025, 026, 028, 032, 033, 034, 040, 041, 042)
REJECTED      = 2   (043 ROOT-016, 044 BUILDSC-012)
TOTAL         = 44  (OPEN = 42)
```
Per-unit COMPONENT / CHAIN / EVIDENCE-INTEGRITY / GATE-PRIORITY are distinguished in the MSC table; no LOW component was inflated by chain membership (018, 024, 029, 030, 031 stay LOW despite AC-014/004/011/015/008), and no HIGH-chain breaker was under-prioritized (017 and 021 carry gate-priority HIGH at MEDIUM component severity).

## ARCHITECTURE VERDICT
**`CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED`** — confirmed. The four HIGH chains and most MEDIUM chains terminate only when client controls and server invariants are specified together (AC-001: C1 ∧ S1/S2; AC-003: C9 ∧ S7; AC-010: C10 ∧ S5; AC-005: C12 ∧ S15), and today those invariants exist only as prose or endpoint-table rows (verified: no UNIQUE on `device_auth_keys.public_key`). The specialists' `COMPONENT_INTERNAL_REDESIGN_ONLY` verdicts are true within each component and are subsumed. Not `TRUST_BOUNDARY_REDESIGN_REQUIRED`: all nine trust boundaries are correctly placed; their contracts are incomplete.

## SEC-C REQUIRED
**NO.** The frozen trust model (Keystore-bound non-exportable keys, AEAD-protected local state, server-derived identity, DPoP, no recovery, one device, backup exclusion) is valid; every chain is broken by completing contracts inside that model plus component-internal redesigns (JNI ABI, storage primitives, safe-by-construction DPoP API, build trust chain). Escalation trigger preserved: if S1/S2/S5/S7 cannot be frozen as binding server invariants before B004, AC-001/AC-003/AC-010 would leave the one-device and DPoP invariants dependent on unspecified server behaviour — a systemic invariant gap requiring SEC-C.

## MASTER SECURITY RISK SUMMARY
- **Strongest current risk:** AC-012 — the packaged native runtime is provably not the reviewed source (CURRENTLY_REACHABLE in every APK); it has already produced one false closure.
- **Strongest future B004 risk:** AC-001 (fail-open re-registration with a non-malicious minimum actor) and AC-003 (DPoP nullified if verifier defaults are ported).
- **Strongest native risk:** AC-006 — raw-address handles + aliased `&mut` + error collapse → wrong-object crypto and destructive recovery, currently masked only by leaks.
- **Strongest storage risk:** ROOT-006/007 composition — a read that manufactures keys plus a non-durable, unauthenticated marker whose absence means "first run".
- **Strongest lifecycle risk:** AC-008/AC-014 — partial wipe leaves an authenticatable device; the only reset path today recreates the AC-001/A entry.
- **Strongest false-closure risk:** any native fix accepted from source/JVM review (Pattern 1), any single-site read/create fix (Pattern 2), and raising `4096` alone.
- **Strongest later B008/B009 risk:** AC-005 — rollback without epoch → OTK re-publication and Olm message-key reuse; session pickle exceeds the fixed buffer in normal offline operation.
- **Strongest physical uncertainty:** Keystore alias survival across `pm clear`/reinstall/profile (AC-001 resolver input) and StrongBox/TEE level — never measured on any provenance-verified binary.

---

## CONSOLIDATED SERVER SECURITY CONTRACT (deduplicated; NOT implemented)
| # | Rule | Source | MSC | Chains |
|---|---|---|---|---|
| SC-1 | Registration: typed PoP signed by the Device Auth key over `registration_id‖grant-hash‖nonce‖JWK‖identity-material-hash` at submit-device-auth, submit-public-identity and commit; JWK-in-proof == submitted JWK; second JWK per registration_id rejected | S5, AD-CAND-001 | 027 | AC-010, AC-001 |
| SC-2 | Registration idempotency on `(registration_id, jkt)`; commit idempotent with same grant | S4 | 026, 027 | AC-009 |
| SC-3 | DeviceAuth: `UNIQUE(device_auth_keys.public_key)` global; re-registration of a JWK bound to any ACTIVE/REVOKED device rejected; `one_active_device_per_account` + "one wins" | S1, S3 | 028 | AC-001/A, AC-010, AC-014→001 |
| SC-4 | JKT → device_id → account immutable; `AuthenticatedDeviceContext.device_id` derived from the validated key only, never from JSON | S2 | 028 | AC-001/A, AC-003 |
| SC-5 | Identity key: `identity_public_keys` immutable per device, enforced at publish | S16 | 028 | AC-008 |
| SC-6 | DPoP: ES256 over embedded P-256 `jwk`; **jkt binding mandatory** for every token-bearing request; **ath mandatory** whenever a token is presented; htm equality; iat ±120 s | S6, S7, S8 | 021, 026 | AC-003, AC-002 |
| SC-7 | Nonce: issued at `/v1/auth/challenge` and via `DPoP-Nonce`; bound to (jkt, endpoint class); single-use/short TTL; `use_dpop_nonce` error class | S9 | 025 | AC-003, AC-004 |
| SC-8 | Replay: shared atomic store keyed `(jkt, jti)`, `SET NX`-style insert, TTL ≥ 300 s and ≥ freshness window, retention keyed by **iat/monotonic source**, bounded per key | S10, S11 | 023, 024, 026 | AC-004 |
| SC-9 | HTU: compare `lower(scheme)://lower(host)[:non-default port]rawPath` (RFC 3986 §6.2.2 only), no userinfo/query/fragment; router matches raw path | S12 | 022, 026 | AC-002 |
| SC-10 | OTK: `otk_id`-keyed idempotent publication; same `otk_id` ≠ key = security error; duplicate public key under two ids rejected; consumed OTK (`CLAIMED`) terminal | S13, S14 | 010, 011, 020 | AC-005, AC-007 |
| SC-11 | Rollback/epoch: monotonic `identity_revision`/publication epoch echoed to client for local AAD binding | S15 | 020, 034 | AC-005 |
| SC-12 | Rejection-class taxonomy: transient vs permanent surfaced to client for armed-latch release | S17 | 026, 018 | AC-014 |
| SC-13 | Wipe/revocation lifecycle: device revoked on account-delete/wipe intent; logout keeps key; revocation terminal | S18 | 032, 031 | AC-008 |
| SC-14 | Hardware level: self-reported StrongBox/TEE is not trusted for authorization; identity derives from the key (SC-4); attestation decision recorded | ARCH-006 | 042 | AC-003 |

## CONSOLIDATED CLIENT SECURITY CONTRACT (deduplicated)
| # | Rule | MSC | Chains |
|---|---|---|---|
| CC-1 | Key lifecycle: no Keystore key creation on any read/status path; create-on-write only; never `generateKey` on an existing alias; creation serialized; alias-type collision fails closed | 014, 029 | AC-001, AC-008, AC-011 |
| CC-2 | JNI handles: opaque `(slot, generation)` never a memory address; check+use under one owning `Arc<Mutex<T>>` scope; destroy cannot race use; double-destroy/stale/wrong-type return disjoint `HANDLE_*` codes; one process-wide bridge; `CryptoNative` not app-reachable | 005, 006, 007, 008 | AC-006, AC-011 |
| CC-3 | Serialization: native-allocated exact-size output with hard caps (identity 2 MiB, session 64 KiB); AAD = magic‖version‖object_type‖context; `UNSUPPORTED_VERSION` distinct | 009, 012, 019 | AC-007, AC-005 |
| CC-4 | OTK surface: `{KeyId, pk}` ordered by KeyId, unique; `created/removed` surfaced; stored vs unpublished counts distinct; mark-published semantics per B-006; input `count ≤ cap` | 010, 011, 013 | AC-007, AC-005 |
| CC-5 | DeviceAuth: P-256 non-exportable, StrongBox preferred/TEE ok/software fails; terminal loss never regenerates; destructive primitives not public API | 029, 017, 032 | AC-001, AC-014 |
| CC-6 | DPoP API: non-null `DpopBinding(jkt, tokenHash?, nonce?)`; factory requires token for token-bearing calls; no default replay cache; raw-path htu; HTM allow-list | 021, 022, 023 | AC-002, AC-003, AC-004 |
| CC-7 | First-run resolver: marker absent ∧ any anoX alias present ⇒ NOT first run ⇒ fail closed (explicit reset only); marker HMAC-protected with "HMAC key missing ⇒ bound"; payload corruption fails closed | 017 | AC-001, AC-014 |
| CC-8 | Registration persistence: typed `KEY_MISSING/EMPTY/UNSUPPORTED_VERSION/AUTH_FAILED/IO`; all consumed as not-first-run; empty file is a security exception; all state mutation through one guarded path; `RejectedAfterArm` explicit | 015, 018 | AC-001, AC-014 |
| CC-9 | Durability: file fsync + parent-directory fsync in every writer; rename result checked; `.bak` never restored; `.new/.tmp` residue policy at startup | 016 | AC-001, AC-009, AC-005 |
| CC-10 | Rollback: local envelopes bind type‖version‖context; server epoch echoed into AAD when available; no local counter presented as anti-rollback | 019, 020 | AC-005 |
| CC-11 | Wipe: cross-domain orchestrator; per-item truthful results; order alias-first, marker-last; all 3 aliases + 5 domains + residue; logout keeps key | 031, 032 | AC-008, AC-014 |
| CC-12 | Error taxonomy: injective native→JVM codes; version ≠ corruption ≠ key-missing ≠ stale-handle; recovery decisions never made on collapsed codes | 007, 015 | AC-006, AC-007 |
| CC-13 | Secrets: best-effort zeroization of pickle/K_STATE/grant buffers; handles released deterministically | 030, 008 | AC-015 |
| CC-14 | Identifiers: UUIDv4 version AND variant validated | 035 | — |

---

## MASTER FIX COVERAGE PRECURSOR

| MSC | Source IDs (primary) | Sev | Gate | Session | Code | Architecture | Tests | Runtime | Physical | Retest owner | Chains |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | ROOT-001; BUILDSC-001/003/006/008; MAINARCH-013/031 | HIGH (EI CRIT) | PRE_B004 | S1 | ci.yml, jniLibs, gradle, rust-toolchain, validator | B-017/B-021 policy | gate negatives, parity, repro | instrumented on produced .so | — | Build/Supply | 012, 007 |
| 002 | ROOT-017; BUILDSC-002 | META (EI HIGH) | PRE_B004 | S1 | ci.yml, androidTest | B-021 | negatives added | instrumented CI both ABIs | — | Build/Supply + domains | 012, 013 |
| 003 | ROOT-018 slice; BUILDSC-007/010/004-doc | MEDIUM | PRE_B004 | S1 | ci.yml, policy doc | B-017-Lite | gate negatives | — | — | Build/Supply | 012 |
| 004 | ROOT-018; BUILDSC-004/005/009/011; CS-020 | MEDIUM | RC | S9 | gradle, proguard, RUSTFLAGS | B-017/B-018 | verify-metadata, R8 keep, SBOM | — | — | Build/Supply | 012 |
| 005 | ROOT-003; ARCH-001; LEG-INT-005 | HIGH | PRE_B004 | S2 | lib.rs | Inv.23 | host registry tests | stale-handle instrumented | — | Crypto/JNI | 006 |
| 006 | ROOT-002; CS-102 | HIGH | PRE_B004 | S2 | CryptoBridge.kt:38-44,580; CryptoNative.kt | LKSL §O | assertSame; visibility | — | — | Crypto/JNI | 006, 011 |
| 007 | ROOT-013; CJ-003/006; ARCH-008 | MEDIUM | PRE_B004 | S2 | error.rs, lib.rs, CryptoError.kt, CryptoBridge.kt | Inv.23 | injectivity table | negative-path JNI | — | Crypto/JNI + Storage | 006, 007 |
| 008 | ROOT-014; LEG-INT-005; CS-019 | MEDIUM | PRE_B004 (after 005) | S2 | LocalE2eeIdentityStep, CryptoBridge, lib.rs | — | acquire/release pairing | leak test | — | Crypto/JNI | 006, 007, 015 |
| 009 | ROOT-004; CS-004 | HIGH | PRE_B004 | S2 | CryptoBridge.kt:334-355; serialization.rs; lib.rs | B-006 | size tests | default-count step | — | Crypto/JNI | 007, 005 |
| 010 | ROOT-005 | HIGH | PRE_B004 | S2 | identity.rs, lib.rs, CryptoNative.kt | B-006 v1.2 | ordering/uniqueness | uploaded==created | — | Crypto/JNI | 007, 005 |
| 011 | CJ-001 | HIGH | PRE_B004 | S2 | identity.rs:33-67; LocalE2eeIdentityStep:31-52 | B-006 | count/set consistency | same | — | Crypto/JNI | 007, 005 |
| 012 | CJ-002 | MEDIUM | B008/B009 | S2 code / S7 close | CryptoBridge.kt:528; session.rs | B-008 | 29.9 KB test | on produced .so | — | Crypto/JNI | 005 |
| 013 | CJ-004; CS-019 | MEDIUM | B006 | S2 cap / S6 | lib.rs:200-214; identity.rs | B-006 replenishment | cap; removed handling | on produced .so | — | Crypto/JNI | 007 |
| 014 | ROOT-006; ARCH-007; MAINARCH-023; CS-005/017 | MEDIUM | PRE_B004 | S2+S3 | RegistrationSessionKey.kt; CryptoBridge.kt:73-165,337,526 | Inv.23; LKSL §C/§G | call-site enumeration; serialized creation | alias tests | P3 | Storage + Auth | 001, 008, 011 |
| 015 | ROOT-007 c3; ROOT-006 sec.; CS-015/017 | MEDIUM | PRE_B004 | S3 (+S2) | FileRegistrationSessionStore:39-53; Orchestrator:58-62,246-254 | GAP-001 | taxonomy tests | — | — | Storage | 001, 006 |
| 016 | ROOT-007 c1/c4/c6; AS-CAND-002; CS-006 | MEDIUM | PRE_B004 | S3 (+S2 writer) | AtomicFileWriter; writeFileAtomic; FileRegistrationSessionStore | B-003 v1.5 §3 | temp-dir real-class | kill -9 | P12, P13 | Storage | 001, 009, 005 |
| 017 | ROOT-007 c2/c5/c7; ROOT-011 marker; CS-009 | MEDIUM (HIGH@B004) | PRE_B004 | S3 | FileDeviceAuthBindingStore; Resolver; Orchestrator:246-254 | GAP-001 (033) | resolver truth table; HMAC marker | alias-present/marker-absent | P4, P5, P13 | Storage + Auth + Attackchain | 001, 014 |
| 018 | AS-CAND-001; LEG-INT-003 | LOW | contract PRE_B004 / code B004 | S3 or S5 | Orchestrator:216-232,302-310; RegistrationState | 026/033 | transition + reset order | end-state | — | Storage | 014 |
| 019 | ROOT-011 reg. slice; C-009 | MEDIUM | PRE_B004 | S2+S3 | RegistrationSessionKey enc/dec; wrapStateKey; serialization.rs | Inv.24 | AAD tests | instrumented | — | Storage + Crypto/JNI | 005, 001 |
| 020 | ROOT-011 id/session; CS-018 | MEDIUM | B006/B008 | S6, S7 | serialization.rs; CryptoBridge; B-006 server | 034 (S15) | rollback tests | instrumented | P12 | Crypto/JNI + Storage + backend | 005 |
| 021 | ROOT-008 binding; ARCH-006; CS-007 | MEDIUM (HIGH@B004) | PRE_B004 client / B004 server | S4 (+S5) | DpopProofVerifier; DpopProofFactory | 026 | compile-level binding | — | P15 | Auth + backend | 002, 003, 004 |
| 022 | ROOT-009; CS-008 | MEDIUM | PRE_B004 | S4 | DpopHtu.kt; DpopHtuTest | 026 (htu rule) | collision rows | — | — | Auth | 002 |
| 023 | ROOT-008 scope; CS-019 | MEDIUM | contract PRE_B004 / B004 | S4 (+S5) | DpopReplayCache; verifier ctor | 026 | two-verifier; restart | — | — | backend + Auth | 004, 011 |
| 024 | AD-CAND-003 | LOW | contract PRE_B004 / B004 | S4 (+S5) | DpopReplayCache:34-56; DeviceAuthClock | 026 | rollback −250 s | — | P16 | backend | 004 |
| 025 | AD-GAP-001 | CONTRACT | PRE_B004 / B004 | S0 (+S4) | N/A (contract) | B-002/B-004/B-007 | validator | conformance B004 | P16 | Architecture | 003, 004, 010 |
| 026 | AD-GAP-002 | CONTRACT | PRE_B004 / B004 | S0 | N/A | B-002/B-004/B-016 | validator | conformance B004 | — | Architecture + backend | 002, 003, 004, 009, 010, 014 |
| 027 | AD-CAND-001; LEG-INT-001 | MEDIUM | PRE_B004 / B004 server | S0 + S4 | RegistrationApi:30-51; Orchestrator:46,114 | V1.2 §2 endpoint table | typed PoP wire tests | conformance | — | Auth + Architecture | 010, 009 |
| 028 | AD-GAP-003; ARCH-004 | CONTRACT | PRE_B004 / B004+B005 | S0 | N/A (schema amendment) | V1.2 B-005 | validator; synthetic S1/S2/S16 | conformance | — | Architecture + backend + Attackchain | 001, 008, 010, 014 |
| 029 | AD-CAND-002; C-014 | LOW | B004 impl (pull-forward S3) | S3/S5 | AndroidKeystoreDeviceAuthKeyManager:48-57,106-118 | B-002 | concurrent creation | alias overwrite | — | Storage/Auth | 011, 010 |
| 030 | ROOT-010; CJ-005; CS-011 | LOW | B008/B009 | S7 | serialization.rs; lib.rs; CryptoBridge; store | B-009 | fill(0) assertions | — | — | Crypto/JNI | 015 |
| 031 | ROOT-012; ARCH-009; MAINARCH-030; CS-010 | LOW | B013 + Final | S8 | CryptoBridge:737-754; stores; new orchestrator | 032 | wipe enumeration | device wipe | P17 | Storage + Architecture | 008, 014 |
| 032 | AS-GAP-002 | CONTRACT | PRE_B004 / B013 / Final | S0 | N/A | B-013/B-009 | validator | — | P4/P5 | Architecture + Storage | 008, 014 |
| 033 | AS-GAP-001 | CONTRACT | PRE_B004 | S0 | N/A | B-003 v1.5/B-002/B-013 | validator | — | — | Architecture | 001, 014 |
| 034 | AS-GAP-003 | CONTRACT | PRE_B004 / Physical | S0 | N/A (manifest rules later) | Inv.25/B-013/B-021 | validator | — | P4,P5,P8,P10,P11 | Architecture + Physical | 001, 005, 013 |
| 035 | ROOT-015; LEG-B003-001 | LOW | Final (hardening S3) | S3 | UuidV4.kt:28,316-330 | B-003 | variant tests | — | — | Storage | — |
| 036 | AC-013; MAINARCH-018 | META | Physical Final | S10 | N/A | B-021 physical rows | — | — | P1–P17 | Physical + Build/Supply | 013, 001, 008, 003 |
| 037 | MAINARCH-031; LEG-CRYPTO-005; LEG-INT-002/005 | META | PRE_B004 (native retest acceptance) | S10 | N/A (evidence) | — | — | instrumented on verified .so | — | Crypto/JNI + Build/Supply | 012 |
| 038 | ARCH-002 | HIGH (META) | PRE_B004 | S1 | tools/audit validator | B-021 V1.3 | validator negatives | — | — | Architecture + Build/Supply | 012 |
| 039 | CS-021/C-017; model deviation; ARCH-010 | INFO | human decision | S0 | tools/audit historical validators | B-027 | — | — | — | Architecture | — |
| 040 | ARCH-004 | CONTRACT | PRE_B004 (auth) / B005 | S0 | N/A | DB-SCHEMA-V1 | validator | — | — | Architecture | 001 (enabling) |
| 041 | ARCH-005 | CONTRACT | B012 | — | N/A | B-012 | validator | — | — | Architecture | — |
| 042 | ARCH-006; CS-103 | CONTRACT | PRE_B004 decision / Physical | S0 | N/A (self-report code unchanged) | B-002 v1.1 | validator | — | P1 | Architecture + Physical | 003, 013 |

```
OPEN MSC UNITS               = 42
UNASSIGNED FIX SESSION       = 0   (041 is gate-owned by B012; 036/037 are verification sessions S10)
MISSING AFFECTED CODE        = 0   (contract/meta units explicitly N/A)
MISSING ARCHITECTURE OWNER   = 0
MISSING REQUIRED TEST        = 0
MISSING RETEST OWNER         = 0
UNKNOWN GATE                 = 0
```

## MASTER CONSOLIDATION QUALITY GATES
```
SOURCE ITEMS UNACCOUNTED         = 0
MSC UNITS WITHOUT SOURCE         = 0
ATTACKCHAINS WITHOUT MSC UNIT    = 0
SERVER BREAKERS UNASSIGNED       = 0
CLIENT BREAKERS UNASSIGNED       = 0
ARCHITECTURE GAPS LOST           = 0   (6/6 distinct contract units)
LEGACY FINDINGS WITHOUT OWNER    = 0
PRE-B004 ITEMS WITHOUT GATE      = 0
LATER ITEMS WITHOUT NAMED GATE   = 0
MSC UNITS WITHOUT TEST PLAN      = 0
MSC UNITS WITHOUT RETEST OWNER   = 0
UNKNOWN DISPOSITIONS             = 0
SILENTLY DROPPED                 = 0
UNRESOLVED DEPENDENCY CYCLES     = 0
```
(All counts machine-checked from `audit_traceability.jsonl` via `/tmp/anox_master_consolidation_001/consolidate.py`; temporary artifact, not authoritative.)

## CONSOLIDATION FINDINGS (why not a clean PASS)
1. 42 security units remain OPEN by design (`OPEN_PENDING_REMEDIATION_COVERAGE_GATE`).
2. Severity deviation from Consensus proposed: ROOT-013 LOW → MEDIUM (requires human acceptance at coverage gate).
3. ROOT-017 classified (was UNKNOWN): SECURITY_EVIDENCE_GAP, evidence-integrity HIGH, Pre-B004 precondition.
4. Four roots proposed for SPLIT (008, 011, 012, 018) across gates; seven specialist candidates recognized as distinct units without new ROOT IDs.
5. Remediation order corrected: contracts ∥ build provenance; JNI ABI ∥ storage foundation; ARCH-002 matrix enforcement moved to Phase 1.
6. One evidence-method prohibition (string-presence heuristic) elevated to a coverage-gate rule (FCP-1).
7. Two governance items (validator lifecycle, Audit-001 model deviation) still await Human Owner disposition (unit 039).

## EVIDENCE LIMITATIONS
This consolidation is analytical and read-only: no build, test, harness or device run was executed; all measurements are transcribed from the hash-verified preserved reports; server behaviour remains modelled (no B004 backend exists); `/tmp` artifacts of this session are working notes, not evidence.

---

## SECURITY HARDENING STATUS
`IN_PROGRESS`
## PRODUCT DEVELOPMENT
`BLOCKED_PENDING_FINAL_AUDIT`
## B004
`NOT_STARTED`
## B005
`NOT_STARTED`
## SECURITY REMEDIATION
`NOT_STARTED`
## SECURITY-REMEDIATION-COVERAGE-GATE
`NOT_EXECUTED` (this report is its input; it is NOT reported as passed)
## FINAL OPERATIONAL ACCEPTANCE
`PENDING / NOT_EXECUTED`
## HUMAN FINAL PRODUCT GATE
`NOT_EXECUTED`

## END REPOSITORY CHECK
```
HEAD        = 1eb773069d81ea3d12b76249c73f2f5fb0b6cae9
origin/main = 1eb773069d81ea3d12b76249c73f2f5fb0b6cae9
working tree = CLEAN (git status --short empty; git diff --check rc 0; branch main)
branches / commits / push / PR / merge = NONE · remote mutation = NONE
findings / docs / registries / Project Memory / Consensus mutation = NONE · permanent ROOT IDs allocated = NONE · fixes implemented = NONE
temp artifacts = /tmp/anox_master_consolidation_001/ only
```

## NEXT ACTION
`PRESERVE / FREEZE MASTER-SPECIALIST-CONSOLIDATION-001 → MERGE → SECURITY-REMEDIATION-COVERAGE-GATE → ONLY AFTER 100% COVERAGE START LARGE DEPENDENCY-SAFE REMEDIATION SESSIONS`

`MASTER-SPECIALIST-CONSOLIDATION-001` — COMPLETE. `PASS_WITH_CONSOLIDATION_FINDINGS`. STOP.
