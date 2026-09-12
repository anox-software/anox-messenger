Audit complete. Baseline reconfirmed clean at the frozen SHA. Full report follows.

---

# AUDIT RESULT

**PASS WITH FINDINGS** — with one CRITICAL artifact-provenance defect that invalidates prior native-layer closure evidence, and one HIGH defect that deterministically breaks the default registration path.

## AUDIT
`AUDIT-SECURITY-CODEBASE-001`

## ROLE
Independent read-only implementation security auditor (full existing codebase), per `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md` AI-audit role.

## PROVIDER
Anthropic

## MODEL
**Claude Opus 5 (Medium reasoning) — NOT "Claude Fable 5.1 High".**

> **MANDATORY DISCLOSURE / GOVERNANCE DEVIATION.** Section 0 required exactly `Claude Fable 5.1 High`. I cannot switch my own model and I will not enter a false model attestation into an audit record. Every technical finding below stands on its own reproducible evidence (commands, SHAs, hashes, measured byte counts). If `B027-A` role/model separation requires the named model for canonical ingest, this run must be recorded as `MODEL_DEVIATION` and re-executed in a session configured with Fable 5.1 High before the findings are frozen.

## MODE
`READ_ONLY_FULL_EXISTING_CODEBASE_SECURITY_AUDIT`

## AUDITED SHA
`869b99acac040412a29bbaadc76342070fb2085c`

## HEAD AT END
`869b99acac040412a29bbaadc76342070fb2085c`

## ORIGIN MAIN
`869b99acac040412a29bbaadc76342070fb2085c`

## WORKING TREE
**CLEAN** (`git status --short` empty; `git diff --check` empty)

## REMOTE MUTATION
**NONE** (no branch, commit, push, PR, merge, or GitHub API call)

---

## SOURCE INVENTORY

### TRACKED FILES
**396** total. By extension: `md` 217, `kt` 72, `py` 37, `xml` 18, `json` 16, `jsonl` 11, `rs` 6, `properties` 3, `kts` 3, `txt` 2, `so` 2, `yml` 1, `toml` 1, `pro` 1, `pdf` 1, `lock` 1, `jar` 1, `gitignore` 1, `bat` 1.

### PRODUCTION KOTLIN/JAVA FILES
**49** Kotlin (`android/src/main` 45 + `crypto/android/src/main` 4). **0** Java. Of these, **46 security-relevant** (3 excluded: `ui/theme/Color.kt`, `Theme.kt`, `Type.kt`).

### RUST SOURCE FILES
**6** (`crypto/rust/src/{lib,identity,session,serialization,error,tests}.rs`, 1,427 LOC total).

### JNI/NATIVE SURFACES
**17** exported JNI entry points, all in `crypto/rust/src/lib.rs::jni_bridge` (gated `#[cfg(target_os = "android")]`), declared in `crypto/android/.../CryptoNative.kt`. **2** committed prebuilt shared objects (`arm64-v8a`, `x86_64`), ELF64, **not stripped**, 17 `Java_com_anox_crypto_*` symbols each.

### BUILD/SECURITY CONFIG FILES
**11**: `build.gradle.kts`, `android/build.gradle.kts`, `settings.gradle.kts`, `gradle.properties`, `gradle/gradle-daemon-jvm.properties`, `gradle/wrapper/gradle-wrapper.properties`, `gradle/wrapper/gradle-wrapper.jar`, `android/proguard-rules.pro`, `android/src/main/AndroidManifest.xml`, `android/src/main/res/xml/data_extraction_rules.xml`, `.github/workflows/ci.yml`. Plus 3 security tooling scripts (`tools/security/*.py`).

### TEST FILES
**23** Kotlin (`android/src/test` 19, `android/src/androidTest` 3, `crypto/android/src/androidTest` 1) + `crypto/rust/src/tests.rs`.

### SECURITY-RELEVANT FILES MANUALLY REVIEWED
**46 / 46** production Kotlin, **6 / 6** Rust, **11 / 11** build-security config, **2 / 2** native binaries (hash/ABI/symbol/provenance), **1** APK (contents + embedded `.so` hash). Test sources reviewed for property-vs-presence quality.

### SECURITY-RELEVANT FILES NOT REVIEWED
**NONE.** Excluded from manual review with stated reason:
- `ui/theme/{Color,Theme,Type}.kt` — Compose colour/typography constants, no security surface, no I/O, no crypto.
- 14 launcher `mipmap`/`drawable` XML, `colors.xml`, `themes.xml` — icon/theme resources only.
- 217 `docs/**/*.md`, 37 `tools/**/*.py` governance validators — read as **authority/evidence**, not audited as product code (out of scope for a product-code audit; `tools/security/*.py` reviewed because CI depends on them).
- `gradle/wrapper/gradle-wrapper.jar` — binary; validated by CI `gradle/actions/wrapper-validation` + `distributionSha256Sum`, not decompiled.

---

## FILE-BY-FILE COVERAGE

Security relevance: **C**=critical, **H**=high, **M**=medium, **L**=low, **N**=none.

| File | Purpose | Sec. rel. | Reviewed | Findings |
|---|---|---|---|---|
| `crypto/rust/src/lib.rs` | JNI bridge, handle registry | C | YES | CS-002, CS-013, CS-011, CS-019 |
| `crypto/rust/src/identity.rs` | vodozemac Account wrapper | C | YES | CS-011 (empty `Zeroize`/`Drop`), unwired APIs |
| `crypto/rust/src/session.rs` | vodozemac Session wrapper | C | YES | CS-011 (empty `Zeroize`/`Drop`), unwired APIs |
| `crypto/rust/src/serialization.rs` | AES-256-GCM state envelope | C | YES | CS-011, CS-018 |
| `crypto/rust/src/error.rs` | error→i32 mapping | H | YES | CS-013 |
| `crypto/rust/src/tests.rs` | Rust unit tests | M | YES | JNI layer uncovered; 1 warning |
| `crypto/rust/Cargo.toml` | deps, `panic="abort"` | H | YES | CS-019 (abort-on-panic) |
| `crypto/rust/Cargo.lock` | pinned deps | M | YES | none |
| `crypto/android/.../CryptoBridge.kt` | safe wrapper, K_STATE, persistence, wipe | C | YES | **CS-001**, CS-004, CS-010, CS-011, CS-017, CS-006 |
| `crypto/android/.../CryptoNative.kt` | JNI declarations | C | YES | CS-102 (public bypass surface) |
| `crypto/android/.../CryptoError.kt` | code→exception mapping | H | YES | CS-013 |
| `crypto/android/.../CryptoResult.kt` | result monad | L | YES | none |
| `android/.../MainActivity.kt` | sole app entry point | C | YES | **UNWIRED-001** (no security wiring at all) |
| `android/.../account/RegistrationOrchestrator.kt` | B-003 state machine | C | YES | CS-004, CS-006, CS-005 |
| `android/.../account/CryptoBridgeLocalE2eeIdentityStep.kt` | E2EE identity/OTK step | C | YES | **CS-004**, CS-012 |
| `android/.../account/LocalE2eeIdentityStep.kt` | boundary interface | M | YES | none |
| `android/.../account/FileRegistrationSessionStore.kt` | encrypted session store | H | YES | CS-015, CS-011, CS-006 |
| `android/.../account/RegistrationSessionStore.kt` | interface + in-memory impl | M | YES | none |
| `android/.../account/BinaryRegistrationStateCodec.kt` | versioned binary codec | H | YES | none (bounds-checked, fail-closed) |
| `android/.../account/RegistrationState.kt` | state hierarchy | H | YES | none |
| `android/.../account/RegistrationGrant.kt` | 256-bit grant holder | H | YES | none (`toString` redacted) |
| `android/.../account/RegistrationApi.kt` | network contract | M | YES | `NOT_IMPLEMENTED` (B-004) |
| `android/.../account/RegistrationSessionSecurityException.kt` | fail-closed signal | M | YES | none |
| `android/.../account/UuidV4.kt` | identifier validation | M | YES | **CS-014** |
| `android/.../account/{AccountId,DeviceId,RegistrationId}.kt` | typed IDs | M | YES | inherit CS-014 |
| `android/.../account/LicenseCode.kt` | license shape validation | M | YES | none (`toString` redacted) |
| `android/.../account/LicenseDuration.kt` | duration enum | L | YES | none |
| `android/.../account/Username.kt` | username validation | M | YES | none |
| `android/.../account/{Account,Device,Entitlement}State.kt` | server state enums | M | YES | none |
| `android/.../account/Entitlement.kt`, `EntitlementRenewal.kt` | entitlement logic | M | YES | none |
| `android/.../account/PublicE2eeIdentityMaterial.kt` | public-only material | H | YES | none (public keys only) |
| `android/.../deviceauth/AndroidKeystoreDeviceAuthKeyManager.kt` | P-256 Keystore key | C | YES | **CS-016**, CS-103 |
| `android/.../deviceauth/DeviceAuthKeyStateResolver.kt` | terminal-loss decision | C | YES | none (correct fail-closed) |
| `android/.../deviceauth/DeviceAuthKeyStatus.kt` | lifecycle states | H | YES | none |
| `android/.../deviceauth/HardwareSecurityLevel.kt` | eligibility policy | H | YES | none (`UNKNOWN`→ineligible ✓) |
| `android/.../deviceauth/DeviceAuthKeyManager.kt` | interface | H | YES | contract contradicted by CS-016 |
| `android/.../deviceauth/DeviceAuthSigner.kt` | opaque signing boundary | C | YES | none (no private bytes) |
| `android/.../deviceauth/DeviceAuthBindingStore.kt` | interface + in-memory | C | YES | CS-009 (`clearBinding` bypass) |
| `android/.../deviceauth/FileDeviceAuthBindingStore.kt` | durable guard | C | YES | **CS-009**, CS-006 |
| `android/.../deviceauth/DpopProofVerifier.kt` | RFC9449 verification | C | YES | **CS-007** |
| `android/.../deviceauth/DpopProofFactory.kt` | proof minting | H | YES | none |
| `android/.../deviceauth/DpopHtu.kt` | htu canonicalisation | H | YES | **CS-008** |
| `android/.../deviceauth/DpopReplayCache.kt` | replay protection | H | YES | CS-007, CS-019 |
| `android/.../deviceauth/DpopVerificationResult.kt` | rejection reasons | M | YES | none |
| `android/.../deviceauth/JtiGenerator.kt` | CSPRNG jti | H | YES | length-only check (false assurance) |
| `android/.../deviceauth/DeviceAuthAccessTokenContract.kt` | token/ath contract | H | YES | none material |
| `android/.../deviceauth/DeviceAuthClock.kt` | injectable wall clock | M | YES | see TIME section |
| `android/.../keystore/RegistrationSessionKey.kt` | AES-256-GCM session key | C | YES | **CS-005** |
| `android/.../storage/AtomicFileWriter.kt` | temp+rename write | C | YES | **CS-006** |
| `android/src/main/AndroidManifest.xml` | components/backup | H | YES | none material |
| `android/src/main/res/xml/data_extraction_rules.xml` | backup exclusion | H | YES | none (fail-closed ✓) |
| `android/build.gradle.kts` | build config | H | YES | **CS-020** |
| `build.gradle.kts`, `settings.gradle.kts` | plugins/repos | M | YES | none (`FAIL_ON_PROJECT_REPOS` ✓) |
| `android/proguard-rules.pro` | shrink rules | M | YES | CS-020 (empty; no JNI `-keep`) |
| `.github/workflows/ci.yml` | CI pipeline | C | YES | **CS-003** |
| `tools/security/validate_apk_contents.py` | APK gate | H | YES | CS-003 (no provenance check) |
| `tools/security/b017_lite_policy_validator.py` | supply-chain gate | H | YES | none |
| `jniLibs/{arm64-v8a,x86_64}/libanox_crypto.so` | shipped native | C | YES | **CS-003** |
| `android/src/test/**` (19), `androidTest/**` (4) | tests | H | YES | see TEST sections |
| `ui/theme/{Color,Theme,Type}.kt` | Compose theme | N | **NO** | Rationale: colour/typography constants only; no I/O, crypto, persistence, IPC or state. |
| 17 `res/**` icon/theme XML | resources | N | **NO** | Rationale: launcher icons/colours/strings; no security semantics. `data_extraction_rules.xml` reviewed separately. |
| `gradle/wrapper/gradle-wrapper.jar` | wrapper binary | M | **NO** (not decompiled) | Rationale: integrity delegated to `distributionSha256Sum` + CI `wrapper-validation`; hash-gated, not source-auditable. |

---

## AUTHORITY PRECEDENCE
Resolved from `docs/authority/AUTHORITY_INDEX.md` (canonical, self-declared tie-breaker):
1. `B025/SECURITY_INVARIANTS_V1_1.md` → 2. `B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` → 3. `B_FREEZE_REGISTRY.md` → 4. `CLOUD_AI_SECRET_PROTECTION.md` → 5. `DEVELOPMENT_SECURITY_WORKFLOW_V1.md` → 6. `GITHUB_REMOTE_ACTIVITY_SAFETY.md` → 7. `B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` → 8. `B025_MANDATORY_AMENDMENTS_V1_1` → 9. `V1_2` → 10. `V1_3` → 11. `B025/TRACK_B/B0xx_*` (amended items superseded) → 12. `B027_AI_WORKFORCE_GOVERNANCE.md` → 13. `docs/history/**` (provenance only).

## IMPLEMENTATION-vs-ARCHITECTURE RESULT
**PARTIAL** — the specified *decision logic* is largely implemented and genuinely fail-closed; the specified *enforcement, wiring, artifact provenance and memory-safety serialisation* are not.

## FALSE ASSURANCE RISKS
1. **`CryptoBridge` `getInstance` is not a singleton.** `instance` is never assigned (`CryptoBridge.kt:39-44`); `cryptoLock` is a per-instance `ReentrantLock` (`:580`). The commit `342d553` claim "serialize CryptoBridge identity/session operations with a ReentrantLock" is **inert**. Comments assert serialisation that the runtime cannot provide.
2. **Shipped `.so` ≠ audited Rust.** The binary predates the LEGACY-FIX-01 remediation. Every "closed" native finding and all physical/instrumented evidence gathered on-device tested a *different* binary than the reviewed source.
3. **`impl Zeroize for Identity` / `for Session` have empty bodies**, and `impl Drop` bodies are comments only (`identity.rs:161-172`, `session.rs:101-112`). A validator or reviewer grepping for "Zeroize implemented" gets a true positive with zero effect.
4. **`cargo test` never compiles the JNI bridge.** `mod jni_bridge` is `#[cfg(target_os = "android")]`; the canonical Rust test command runs on the host. CI runs `cargo test --locked` on `ubuntu-latest`. The entire 17-function security boundary is **never compiled or tested by any automated gate**.
5. **`CryptoInstrumentedTest.kt` (39 tests) is the only test touching real JNI — and CI has no emulator step.** The single test suite that could have caught CS-003 and CS-004 never runs automatically.
6. **`DpopProofVerifier` KDoc says "`jti` at least 128 random bits"; the code checks `jti.length >= 22`.** Presence of length, not entropy.
7. **`DpopReplayCache`/`DeviceAuthAccessTokenContract`/`RegistrationApi` KDocs say "a production deployment supplies…".** Caller discipline documented in prose, enforced nowhere; the *default* argument is the insecure one.
8. **`DeviceAuthKeyManager.deleteKeyDestructively()` KDoc: "never called implicitly by any recovery, retry or error-handling path"** — called from `catch (e: Exception)` at `AndroidKeystoreDeviceAuthKeyManager.kt:114`.
9. **`UuidV4` KDoc claims "RFC 4122 variant 1, version 4"** — only `version()` is checked.
10. **`FileRegistrationSessionStore` KDoc: "returns `NotStarted` only when no file exists"** — a zero-byte file also returns `NotStarted`.
11. **`AtomicFileWriter`/`writeFileAtomic`/`AtomicFile` named/documented "atomic" and "durably arms"** — no parent-directory `fsync`, so the rename is not crash-durable.
12. **Android Lint's one security-adjacent warning (`StaticFieldLeak` on `CryptoBridge`) is a false positive *only because* of CS-001** — the static field is never populated. The signal pointing at the defect was inverted into a non-issue.
13. **All governance validators are green while the shipped artifact does not match the source.** Green validators certify document/registry consistency, not code or binary correctness.

---

## BASELINE VALIDATORS

| Validator | Exit | Result |
|---|---|---|
| `tools/continuity/validate_continuity.py --mode live` | 0 | **PASS** — memory freshness + live git verification, `ANOX-EVENT-0044` |
| `tools/audit/validate_security_architecture_findings_freeze.py` | 0 | **PASS** — no product/CI/SQL changes; report exists; memory synced |
| `tools/audit/validate_workforce_retest_closure_ingest.py` | **1** | **FAIL** (4 FAIL lines) — `ANOX-TASK-SECURITY-ARCH-001 not Candidate`; `WORKFORCE_STATE next_phase not AUDIT-SECURITY-ARCHITECTURE`; `CURRENT_STATE post_merge_gate not AUDIT-SECURITY-ARCHITECTURE`. **Assessment: stale one-shot post-merge assertion, superseded by `SECURITY-ARCHITECTURE-FINDINGS-FREEZE-001`. Fails closed (correct), not in CI. Recorded as CS-021 (INFO).** |
| `tools/workforce/validate_b027a.py` | 0 | **PASS** — role/model separation, secret scan |
| `tools/workforce/validate_b027b.py` | 0 | **PASS** — 58/58 resolver tests |
| `tools/workforce/validate_b027_integrity.py` | 0 | **PASS** — `PRODUCT_DEVELOPMENT: BLOCKED_PENDING_FINAL_AUDIT` |
| `tools/security/b017_lite_policy_validator.py` | 0 | **PASS** — no dangerous triggers, no token write perms, wrapper SHA pinned, no dynamic Gradle deps, `Cargo.lock` present |

Per §96: no code finding below is downgraded on the strength of green validators.

## RUST TESTS
`cd crypto/rust && CARGO_TARGET_DIR=/tmp/anox_codesec_cargo_target cargo test --locked --offline`
**17 passed, 0 failed, 0 ignored, 0 filtered.** 1 compiler warning (`unused_variable: bob_otk_bytes`, `tests.rs:136`).
**Coverage caveat:** 0 of 17 exercise `jni_bridge` (host target excludes it).

## JVM SECURITY TESTS
`./gradlew :android:testDebugUnitTest --offline --rerun-tasks` (JDK: Android Studio JBR 21) — **BUILD SUCCESSFUL**.
**16 suites, 177 tests, 0 failures, 0 errors, 0 skipped.**
`CryptoErrorMappingTest` 4 · `AccountDeviceEntitlementStateTest` 3 · `EntitlementRenewalTest` 7 · `IdentifierTest` 7 · `LicenseCodeTest` 10 · `LicenseDurationTest` 6 · `RegistrationCrashConsistencyTest` 12 · `RegistrationGrantTest` 7 · `RegistrationOrchestratorTest` 28 · `RegistrationStateCodecTest` 12 · `UsernameTest` 12 · `DeviceAuthAccessTokenContractTest` 7 · `DeviceAuthKeyLifecycleTest` 17 · `DpopHtuTest` 7 · `DpopProofVerifierTest` 32 · `InMemoryDpopReplayCacheTest` 6.
**Coverage caveat:** **zero** JVM unit tests for `CryptoBridge` itself.

## ANDROID LINT
`./gradlew :android:lintDebug --offline` — **BUILD SUCCESSFUL**. **0 errors / 0 fatal, 7 warnings (8 issue instances).**
`StaticFieldLeak` (CryptoBridge.kt) · `DataExtractionRules` (API 31+ note) · `OldTargetApi` · `GradleDependency` (compileSdk 36 available) · `ObsoleteSdkInt` (v26 folder) · `UnusedResources` (`R.string.app_name`) · `MonochromeLauncherIcon` ×2.
**Security-relevant:** only `StaticFieldLeak`, and it is a false positive *because of* CS-001 (see False Assurance #12). **Lint detected none of the 21 findings.**

## DEBUG BUILD
`./gradlew :android:assembleDebug --offline` — **PASS**. `tools/security/validate_apk_contents.py` on the produced APK — **PASS** (5 dex, 2 native libs, 0 forbidden members, 0 secret markers). Embedded `.so` SHA-256 verified byte-identical to the repo blobs.

## PHYSICAL DEVICE TESTS
`NOT_RUN — PHYSICAL DEVICE / EMULATOR REQUIRED`. No GrapheneOS/StrongBox claim is made. `ANOX-MAINARCH-018` remains governed separately. **Additional caveat: because of CS-003, any physical evidence gathered before a native rebuild tested the stale binary and must be re-collected.**

---

## EXISTING SECURITY ARCH FINDINGS REVIEW

| ID | Reproduced? | Exact code evidence | Severity still justified? | Additional impact |
|---|---|---|---|---|
| **ARCH-001** HIGH — native handle concurrency/lifecycle not fail-closed | **YES, expanded** | `lib.rs:44-49,69-74` release the registry mutex before `lib.rs:166,191,209,225,247,272,327,359,411,450,502` raw-deref; `lib.rs:142-147,480-485` free via `Box::from_raw` with no use-barrier; registry keys are reusable heap addresses | **YES — raise to CRITICAL** on remediation ordering. Root cause is deeper than "does not deterministically fail": it is a **TOCTOU + `&mut` aliasing** defect, i.e. Rust UB, not merely a missing check | Kotlin-side compensating lock is **inert** (CS-001), so nothing serialises it; `mark_keys_as_published`/`unpublished_one_time_keys`/`get_one_time_key`/`session_id`/`has_received_message` have **no JNI export and no caller** (dead security surface) |
| **ARCH-002** HIGH — B-021 matrix gate not machine-enforced | **YES (governance)** | No validator in `tools/**` consumes `b021_verification_matrix.jsonl`; CI runs only `b017_lite_policy_validator.py` | **YES** | This audit is direct proof of consequence: CS-003 and CS-004 survived every green gate |
| **ARCH-003** HIGH — Registration/AccountKeyManager fail-closed gaps | **PARTIALLY — much better than described, with 3 concrete new gaps** | `RegistrationOrchestrator.kt:88-112,181-185,196-209,246-254,302-310` implement genuine fail-closed pre-auth/device-auth/thumbprint revalidation and non-destructive `failStep`; **gaps:** CS-005 (`RegistrationSessionKey.kt:65-70`), CS-006 (`AtomicFileWriter.kt:17-25`), CS-015 (`FileRegistrationSessionStore.kt:47`) | **YES, HIGH** | Reclassify from "not documented" to "documented and implemented, but the *durability* and *key-existence* primitives underneath are unsound" |
| **ARCH-004** HIGH — DB schema authority contradiction | **N/A to code** | No SQL/DB code exists at this SHA | YES (doc-level) | `DESIGN_ONLY_NOT_IMPLEMENTED` |
| **ARCH-005** MEDIUM — attachment secretstream not operational | **YES** | No libsodium/secretstream dependency in `Cargo.toml`; no attachment code | YES | `DESIGN_ONLY_NOT_IMPLEMENTED` |
| **ARCH-006** MEDIUM — StrongBox/TEE eligibility lacks server validation | **YES** | `AndroidKeystoreDeviceAuthKeyManager.kt:59-63,151-178` client-side only; no attestation-certificate parsing anywhere | YES | `UNKNOWN`→ineligible is correctly fail-closed; but **no key attestation is requested or verified at all** — client self-assertion only, unverifiable by a future server |
| **ARCH-007** MEDIUM — `getOrCreateStateKey`/K_STATE handle lifecycle not fail-closed | **PARTIALLY — remediated in source, but expanded** | `CryptoBridge.kt:133-165` correctly splits `getOrCreateStateKey` (create paths) from `getExistingStateKey` (read paths); read paths at `:366,553,622` use existing-only ✓ | **Lower to LOW for the original root cause; but CS-005 is the same defect, unfixed, in `RegistrationSessionKey`** | The identical anti-pattern was fixed in `CryptoBridge` and left in place in `RegistrationSessionKey.decrypt()` → `getOrCreateKey()`. Remediation was not applied consistently across the codebase |
| **ARCH-008** LOW — `CryptoError.fromCode` non-injective + `UuidV4` non-canonical | **YES, both, with exact evidence** | `error.rs:40-55` vs `lib.rs:106,109,114,161,244,253,370` — `-3`, `-10`, `-11` each carry two distinct meanings; `-12` unmapped → `UnknownError`; `-1` = both `InvalidInput` and inactive/null handle. `UuidV4.kt:323-330` has no `variant()` check | **Raise to MEDIUM** — "stale/invalid native handle" is indistinguishable from "invalid input", which defeats diagnosis of the ARCH-001 class at runtime | Compounded by CS-003: the shipped binary returns the **pre-remediation** `-2` (`InvalidCiphertext`) for buffer overflow |
| **ARCH-009** LOW — WAL/SHM + backup scope of `wipeLocalCrypto` | **YES, expanded** | `CryptoBridge.kt:737-754`: master key deleted first ✓, then 3 `File.delete()` calls whose **return values are ignored** → `CryptoResult.success` on failed deletion; `.tmp` siblings never removed; registration-session and device-auth binding files (in `noBackupFilesDir`) out of scope | **Raise to MEDIUM** | New evidence: the fail-open success return (CS-010) is a distinct defect from the WAL/SHM scope gap |
| **ARCH-010** INFO — B-004/B-005 correctly NOT_STARTED | **YES, confirmed and strengthened** | `RegistrationApi.kt` is interface-only; no HTTP client, no `INTERNET` permission in the manifest; `MainActivity.kt` wires nothing | YES | **Strengthened well beyond the recorded scope: not just B-004/B-005 — the *entire implemented security subsystem* is unwired from the application runtime.** See UNWIRED-001 |

## CLOSED FINDING REGRESSIONS
**`ANOX-LEGACY-CRYPTO-005` — `REGRESSION_OF_CLOSED_FINDING` (two independent mechanisms):**
1. The Kotlin remediation shipped in `342d553` ("serialize CryptoBridge identity/session operations with a ReentrantLock") is **functionally inert** because `getInstance` never stores the singleton → every caller gets a private lock (CS-001).
2. The Rust remediation shipped in `342d553` (`-2` → `-11`, `CryptoError::BufferTooSmall`) **is not present in the shipped binary**, which was built at `7db20fa` and never rebuilt (CS-003).

**`ANOX-LEGACY-INTEGRATION-005`** (native handle lifecycle) — root cause **not regressed but never actually fixed**: the registry added at `7db20fa` validates handle *membership* only, which cannot prevent destroy-racing-use or address reuse (CS-002).

No other closed finding overlaps audited code; per §82 no mechanical re-audit was performed and nothing was reopened in the repository.

---

## CRYPTOBRIDGE SINGLETON

**DEFECTIVE — the singleton does not exist. `CONFIRMS`/`EXPANDS ANOX-SECURITY-ARCH-001` + `REGRESSION_OF_CLOSED ANOX-LEGACY-CRYPTO-005`.**

```kotlin
// CryptoBridge.kt:38-44
fun getInstance(context: Context): CryptoBridge {
    return instance ?: synchronized(this) {
        instance ?: CryptoBridge(context.applicationContext).also {
            it.initialize()            // <-- result is NEVER assigned to `instance`
        }
    }
}
// CryptoBridge.kt:580
private val cryptoLock = ReentrantLock()   // <-- per-INSTANCE, not companion
```

- Singleton construction: **works**. Singleton **storage: absent** — `instance` remains `null` forever.
- All product callers share the same instance: **NO.** Every `getInstance()` returns a fresh object.
- Locking globally effective: **NO.** Two callers hold two different `ReentrantLock`s and can enter `cryptoEncrypt` on the *same* `session: Long` concurrently.
- Lower-level bypass: **YES.** `object CryptoNative` is public with 17 public `external fun`; nothing is `internal` or `private`. `CryptoBridge` is not the only path.
- **Additional consequences beyond concurrency (§70):** `initialize()` + `initializeMasterKey()` re-run on every call (repeated `KeyStore.load`/`containsAlias`); two instances write the **same** `.tmp` path (`filesDir/anox_identity.enc.tmp`) in `writeFileAtomic` → interleaved writes then rename → corrupt protected identity; each instance can independently `getOrCreateStateKey()`; the `@Volatile` static never holds a `Context`, which is why Lint's `StaticFieldLeak` is a benign false positive.

## KOTLIN CONCURRENCY

**Locks present, one of them ineffective; the rest are correct but instance-scoped.**

| Construct | Location | Actual resource protected | Verdict |
|---|---|---|---|
| `ReentrantLock cryptoLock` | `CryptoBridge.kt:580` | *intended*: native handles + K_STATE + state files. *actual*: **nothing shared** | **INEFFECTIVE** (CS-001) |
| `synchronized(this)` | `CryptoBridge.kt:39` | companion object during construction | correct but pointless (no store) |
| `@Volatile instance` | `CryptoBridge.kt:32-33` | — | never written |
| `@Synchronized` ×3 | `FileRegistrationSessionStore.kt:38,58,74` | the `AtomicFile` + Keystore ops | correct, **instance-scoped** |
| `@Synchronized` ×4 | `FileDeviceAuthBindingStore.kt:30,33,48,53,58` | marker file read-modify-write | correct, **instance-scoped**; `markArmed()` is read-then-write, atomic only within one instance |
| `@Synchronized` | `DpopReplayCache.kt:38` | `LinkedHashMap seen` | correct |
| `@Volatile` ×2 | `DeviceAuthBindingStore.kt:65,68` | in-memory flags | correct |
| `@Volatile` | `RegistrationSessionStore.kt:36` | in-memory state | correct |

No coroutines, no callbacks, no futures, no `Executor` in production code. **`RegistrationOrchestrator` has no synchronisation whatsoever** — it is single-threaded by assumption, undocumented and unenforced; two concurrent `reserve()` calls could both pass `check(canStartNew(...))`.

## RUST FFI SOUNDNESS

**UNSOUND under concurrent access.** 20 `unsafe` sites, all raw-pointer dereferences or `Box::from_raw`/`into_raw`.

Per §16, for the representative class (`lib.rs:206-213`, `408-411`, `447-450`):
1. **Required invariant:** the `jlong` is a live, uniquely-owned `*mut Identity`/`*mut Session`, and no other `&`/`&mut` to it exists for the reference's lifetime.
2. **Who establishes it:** nobody. The JVM caller supplies an arbitrary `Long`.
3. **Runtime verification:** only set-membership (`is_identity_active` / `is_session_active`) — and **the mutex is released before the dereference**.
4. **Concurrent violation:** **YES.** Two JVM threads calling `cryptoEncrypt(sameSession, …)` each create `&mut *(session as *mut Session)` → two live `&mut` aliases → immediate UB. Nothing in Rust serialises this; the Kotlin lock that was supposed to is inert (CS-001).
5. **Stale-handle violation:** **YES.** `cryptoDestroyIdentity` removes the key and `Box::from_raw` frees. A subsequent `Box::into_raw(Box::new(Identity::new()))` may receive the *same heap address*, re-inserting it into `ACTIVE_IDENTITIES`. A stale `Long` retained by Kotlin then passes `is_identity_active` and operates on a **different identity**. Cross-*type* confusion is correctly prevented by the two separate sets; same-type confusion is not.
6. **Kotlin violation:** **YES.** `CryptoNative` is fully public; any code can pass any `Long`.

Positive: `cryptoCreateInboundSession` (`lib.rs:381-392`) correctly registers the handle *after* the JVM array write succeeds and frees on failure — a genuinely careful leak-avoidance. `read_byte_array`/`write_byte_array` bounds-check via `get_array_length` before every copy. `panic = "abort"` (release) prevents unwinding across `extern "system"` — but note the shipped `.so` was not built by any verifiable pipeline, so the profile actually used is unproven.

## NATIVE HANDLE LIFECYCLE

```
Identity:  Box::new ─► Box::into_raw ─► register_identity(HashSet<usize>)
           ─► [use: 8 JNI fns, unsafe deref AFTER releasing registry lock]
           ─► serialize (immutable borrow)
           ─► cryptoDestroyIdentity ─► release_identity (remove from set)
                                    ─► Box::from_raw ─► drop ─► free
Session:   identical, via ACTIVE_SESSIONS
```
- **Owner:** ambiguous. Rust owns the allocation; the JVM owns the only reference, as an untyped `Long`.
- **Lifetime:** until an explicit `cryptoDestroy*`. There is **no finaliser, no `Cleaner`, no `AutoCloseable`, no `try/finally`, no `use {}`** anywhere.
- **Cleanup trigger:** manual only. **No production code calls `destroyIdentity`/`destroySession`** — `CryptoBridgeLocalE2eeIdentityStep.resolveIdentityHandle()` acquires a handle and never releases it, and `getLocalStateStatus()` deserialises a **fresh** native `Identity` on every call (CS-012).
- **Duplicate destruction:** silently no-ops (`release_*` returns `None`) and `CryptoBridge.destroyIdentity` returns `CryptoResult.success(Unit)` → double-destroy is indistinguishable from success.
- **Stale handle:** rejected only if the address was not reused (see above).
- **Address reuse:** exploitable within a type.
- **Process teardown:** no `Drop` runs; no zeroisation of native secrets on exit.
- **Exception during teardown:** `destroy*` is wrapped in `try/catch(Exception)` returning `CryptoFailure`; the native object is already freed, so the handle is dangling but the JVM keeps the `Long`.

Interaction with `ANOX-LEGACY-INTEGRATION-005` / `ARCH-001`: the registry is a **necessary but insufficient** mitigation; it was closed/hardened as if membership-checking were the fix.

## USE-AFTER-FREE / DOUBLE-FREE

| Scenario | Possible? | Basis |
|---|---|---|
| Use after destroy (single-threaded) | **NO** | `release_*` removes from the set before freeing; a later call returns `-1`/`0` |
| Destroy racing use | **YES** | `is_*_active` releases the mutex, then dereferences (`lib.rs:156→166`, `408→411`, `447→450`) |
| Double destroy | **NO (memory)** | Set removal is atomic; second call no-ops. Reported as success (diagnostic defect) |
| Stale `Long` reused after address reuse | **YES** | Registry keys are raw heap addresses; `Box::from_raw` frees, allocator may reissue |
| Wrong object type as handle | **NO** | `ACTIVE_IDENTITIES` and `ACTIVE_SESSIONS` are separate — a genuine, effective control |
| Identity handle used as session handle | **NO** | Same as above |
| Pointer truncation / sign conversion | **NO (as shipped)** | Only `arm64-v8a`/`x86_64` (64-bit) are built; `usize == jlong` width. **A future 32-bit ABI would truncate `handle as usize`** |
| Concurrent registry mutation | **NO** | `Mutex<HashSet<usize>>` correctly serialises the set itself |

**Reproduction status:** the aliasing/TOCTOU defect is proven by construction from the source; a live UAF repro requires the Android target (`#[cfg(target_os = "android")]` + JNI + emulator). I built out-of-tree `/tmp` probes for the two claims that were empirically decidable on the host (buffer sizing, htu canonicalisation) and did not fabricate an on-device repro. **Routed to `AUDIT-SECURITY-CRYPTO-JNI-001` with an emulator/ASAN repro as a required deliverable.**

## CRYPTO MUTABILITY / RATCHET

Mutating operations: `generate_one_time_keys` (`&mut`), `create_inbound_session` (`&mut`), `Session::encrypt` (`&mut`), `Session::decrypt` (`&mut`). `mark_keys_as_published` (`&mut`) exists but is **unreachable — no JNI export, no caller**.

Two concurrent operations on one handle can produce: **aliased `&mut` — YES** (UB); **lost ratchet updates — YES**; **duplicate message keys — YES** (two `encrypt` calls observing the same chain index ⇒ keystream/counter reuse in the Olm ratchet); **state rollback — YES**; **corrupted serialised state — YES** (`serialize` takes `&*` while another thread holds `&mut`); **UB — YES**.

Additional: because `mark_keys_as_published` is never invoked, `account.one_time_keys()` never transitions keys out of the unpublished set — OTK replenishment/rotation for B-006 is **specified but structurally unreachable**.

## ZEROIZATION

**Weakest area of the implementation. `impl Zeroize` exists and does nothing.**

| Secret | Location | Status |
|---|---|---|
| Pickled `Account`/`Session` JSON (all private identity keys, all OTK secrets, full ratchet state) | `serialization.rs:36` `serde_json::to_vec(data)` | **NO ZEROIZATION** — plain `Vec<u8>` dropped |
| Decrypted pickle on load | `serialization.rs:53,120` | **NO ZEROIZATION** |
| K_STATE 32 bytes crossing JNI | `lib.rs:268,302,498,532` `read_byte_array` → `Vec<u8>` | **NO ZEROIZATION** |
| K_STATE in JVM | `CryptoBridge.kt:133,156` returns `ByteArray`; callers at `:337,366,526,553,622` never clear | **GC-MANAGED / UNCONTROLLED** |
| Olm plaintext out-buffers | `CryptoBridge.kt:431,446,489,495` `ByteArray` + `copyOfRange` (duplicates the plaintext) | **GC-MANAGED / UNCONTROLLED** |
| 256-bit registration grant (cleartext codec payload) | `FileRegistrationSessionStore.kt:60,50`; `BinaryRegistrationStateCodec.encode/decode` | **NO ZEROIZATION** |
| `CryptoSerializer.key` | `serialization.rs:124-128` `Drop` → `self.key.zeroize()` | **STRONG** ✓ (the only real one) |
| `Identity` / `Session` | `identity.rs:161-172`, `session.rs:101-112` — empty `Drop`, empty `Zeroize` | **NONE** (comments only). vodozemac does zeroise its own internals, but the wrapper's declared `Zeroize` contract is a no-op |

## SERIALIZATION

**Cryptographically sound envelope; fail-closed parsing; no rollback resistance.**

Format: `[4 magic "ANOX"][1 version 0x01][12 nonce][ct+16 tag]`, AES-256-GCM, AAD = `magic‖version`, nonce from `getrandom`. Reviewed `serialization.rs:34-121`.

| Input | Behaviour | Verdict |
|---|---|---|
| Malformed / unknown / missing / duplicate JSON fields | GCM tag verifies first; only self-produced JSON reaches serde | **FAIL_CLOSED** |
| < 33 bytes | `InvalidCiphertext` | **FAIL_CLOSED** |
| Bad magic | `InvalidEnvelope` | **FAIL_CLOSED** |
| Wrong version | `UnsupportedVersion` → distinct `-9` | **FAIL_CLOSED** ✓ |
| Corrupted ciphertext / flipped bit | `DecryptionError` | **FAIL_CLOSED** |
| Attacker-modified file | AAD+tag reject | **FAIL_CLOSED** |
| Cross-type state (session pickle as account) | GCM passes (same K_STATE), serde rejects → `-6` | **FAIL_CLOSED** |
| **Older valid ciphertext replayed (rollback)** | **ACCEPTED** — no epoch/generation counter in the envelope or AAD | **FAIL_OPEN** (CS-018) |
| Nonce reuse | 96-bit random per write, fixed key; birthday bound ~2⁴⁸ writes | acceptable, INFO |

Parse failure can **not** silently create a new identity: `getLocalStateStatus` distinguishes `FirstRun` / `WipedState` / `MissingStateKey` / `CorruptedIdentityState` / `MissingKeystore`, `deserializeIdentity` uses `getExistingStateKey`, and `createAndPersistFirstIdentity` refuses if the file exists. **The no-recovery invariant holds here.**

## LOCAL STATE ATOMICITY

**All three writers are "atomic" against torn content but NOT crash-durable.**

`CryptoBridge.writeFileAtomic` (`:783-794`), `AtomicFileWriter.write` (`:17-25`): `write` → `flush` → `fd.sync()` → `renameTo` → on failure `delete` + throw. `FileRegistrationSessionStore` uses AndroidX `AtomicFile` (`startWrite`/`finishWrite`/`failWrite`, `.bak`-based).

- Temp write: ✓ · file fsync: ✓ · rename: ✓ · **parent-directory fsync: ✗ (all three)**
- Crash windows: (a) before `fd.sync()` → tmp discarded, previous state intact ✓; (b) after `fd.sync()` before `rename` → stale `.tmp` left behind (never cleaned; not covered by `wipeLocalCrypto`) ✓-ish; (c) **after `rename`, before the filesystem journals the directory entry → the rename is lost while the caller has already returned success** ✗ — this is CS-006 and it directly undermines `markArmed()`.
- Overwrite semantics: `renameTo` replaces; old content unrecoverable ✓.
- Permissions: `filesDir` / `noBackupFilesDir`, default `0600`-equivalent app-private; **no explicit permission hardening and no verification** — inherited from the Android sandbox.
- **Concurrency:** `CryptoBridge` instances share the `.tmp` path (CS-001 consequence) → interleaved writers.

---

## REGISTRATION STATE MACHINE

Derived from `RegistrationOrchestrator.kt` (not from docs). 8 states, 8 tags in the codec (note tag ordering: `COMMIT_ARMED = 7`, `FAILED = 6`).

```
NotStarted ──reserve()[canStartNew ∧ ¬bound ∧ ¬armed]──► Reserved            [save]
Reserved ──registerDeviceAuth()[¬TerminalKeyLoss ∧ isProductionEligible ∧ ¬grantExpired]──► DeviceAuthRegistered [save]
DeviceAuthRegistered ──uploadPublicIdentity()[¬expired; OTKs generated AND persisted first]──► PublicIdentityUploaded [save]
PublicIdentityUploaded ──commit()[revalidate thumbprint+eligibility]──► CommitArmed [save] ──► markArmed() [durable] ──► POST commit
CommitArmed ──Committed──► markBound() [durable, BEFORE state save] ──► Committed [save] ──► sessionStore.clear()
CommitArmed ──retry commit()──► CommitArmed (idempotent; expiry checks suppressed)
{Reserved, DeviceAuthRegistered, PublicIdentityUploaded} ──grant TTL──► Expired [save]
any non-terminal ──error──► Failed (persisted ONLY from NotStarted/Failed)
Committed ── terminal, never overwritten
```

**Illegal state skipping: NONE FOUND.** Every step re-reads durable state via `currentState()` and hard-casts to the single legal predecessor (`as? X ?: return failStep(...)`). `failStep` (`:302-310`) refuses to overwrite terminal *or* resumable states — evidence preservation is genuinely implemented. `expiredOrNull` (`:256-288`) correctly suppresses expiry once armed/bound, preventing a clock-driven downgrade. `canStartNew` (`:246-254`) consults the binding store first. **This is the strongest subsystem in the codebase.**

Weaknesses: no concurrency guard on the orchestrator; `RegistrationApi` is unimplemented so idempotency is an assumption; step 3 is currently guaranteed to fail (CS-004).

## REGISTRATION CRASH SAFETY

| Crash point | Durable outcome | Verdict |
|---|---|---|
| Before server call | previous state | SAFE |
| After server response, before persist | server reserved/registered, client one step behind; step re-derives from durable state and re-issues | SAFE (server idempotency assumed) |
| Before local persistence | previous state | SAFE |
| After local persistence | resumable | SAFE |
| **Before OTK mutation** | identity unchanged | SAFE |
| **After OTK mutation, before persist** | **explicitly guarded**: `CryptoBridgeLocalE2eeIdentityStep.kt:41-47` persists the identity *before* returning public OTK material — correct, and correctly commented | **SAFE BY DESIGN** (but currently always fails, CS-004) |
| **Before commit (post-`markArmed`)** | `isArmed` ⇒ key loss terminal, expiry suppressed, retry safe | SAFE **iff `markArmed` is durable — it is not** (CS-006) |
| After commit, before acknowledgement | `markBound()` precedes `Committed` save (`:218-222`) — deliberate and correct ordering | SAFE |
| **`markArmed()` rename lost to power failure** | marker absent ⇒ `AbsentNotBound` ⇒ replacement Device Auth key permitted for a possibly-committed account | **UNSAFE — CS-006** |
| **Keystore session key lost** | `decrypt` silently mints a new key, tag fails, `Failed`, `canStartNew` true unless the marker survived | **UNSAFE — CS-005 + CS-006 chain** |

Can restart produce: duplicate device — **YES**, only via the CS-005 + CS-006 chain; lost identity — **NO**; mismatched identity/device — **NO** (thumbprint revalidated at `:318-343`); half-registered account — **NO** locally; unrecoverable ambiguity — **NO** (corrupt marker ⇒ bound+armed, correct direction).

## DEVICE AUTH KEY LIFECYCLE

Generation `KeyPairGenerator("EC","AndroidKeyStore")`, P-256/secp256r1, `PURPOSE_SIGN|VERIFY`, `DIGEST_SHA256`, `setUserAuthenticationRequired(false)`, `setIsStrongBoxBacked(true)` on API ≥ 28 with fallback. Alias `anox.deviceauth.p256.v1` — verified distinct from `anox_crypto_master_key` (K_STATE) and `anox.b003.session.v1`. Public export via certificate → `ECKey.toPublicJWK()`; **private key never leaves the Keystore, never crosses JNI, never serialised.**

- Existing alias: `createKeyIfAbsent` returns early on `Present` — no silent replacement ✓
- Failed creation: **`catch (Exception) { deleteKeyDestructively() }`** at `:113-115` — contract violation, CS-016
- Replacement: gated by `requireCreationAllowed` → throws on `TerminalKeyLoss` ✓
- Deletion: `deleteKeyDestructively()` public, **no production caller** ✓ (but reachable API)
- **Key/device/account disagreement:** prevented at commit by thumbprint revalidation (`:336-340`) ✓. **But CS-009**: the binding marker that anchors the whole invariant is an unauthenticated 6-byte file — delete it and `TerminalKeyLoss` collapses to `AbsentNotBound`.
- **No key attestation** is requested or verified (relevant to ARCH-006).

## KEYSTORE FAIL-CLOSED

| Condition | Behaviour | Verdict |
|---|---|---|
| Unavailable hardware | `isInsideSecureHardware=false` → `SOFTWARE` → ineligible | **FAIL_CLOSED** ✓ |
| StrongBox unavailable | caught → TEE fallback (B-002 permits TEE) | **FAIL_CLOSED** (with CS-016 side effect) |
| `KeyInfo` retrieval failure | `catch → UNKNOWN` → ineligible | **FAIL_CLOSED** ✓ |
| API 26–30 (no `securityLevel`) | boolean → conservatively TEE, never StrongBox | **FAIL_CLOSED** ✓ |
| Invalidated key | `KeyPermanentlyInvalidatedException` → null → `TerminalKeyLoss` if bound/armed | **FAIL_CLOSED** ✓ |
| Missing alias | null → `AbsentNotBound` or `TerminalKeyLoss` | **FAIL_CLOSED** ✓ |
| Corrupted binding marker | `(true,true)` = bound+armed | **FAIL_CLOSED** ✓ |
| **Deleted binding marker** | `(false,false)` = never bound | **FAIL_OPEN** (CS-009) |
| Security level unknown | `UNKNOWN.isProductionEligible == false` | **FAIL_CLOSED** ✓ |
| **K_STATE master key missing** | `keyStore.getKey(...) as SecretKey` on null → NPE; `isKeystoreOrUnwrapFailure` does not match NPE → reported as `CorruptedIdentityState`, not `MissingKeystore` | **FAIL_CLOSED but MISCLASSIFIED** (CS-017) |
| **Registration session key missing** | `decrypt` → `getOrCreateKey()` **creates a new key**, then tag fails | **AMBIGUOUS / key-manufacturing** (CS-005) |

Verified in implementation, not comments. `HardwareSecurityLevel.UNKNOWN → ineligible` is the single best fail-closed decision in the codebase.

## DEVICE AUTH ↔ E2EE BINDING

**Correct.** Domain separation is real and verified: three distinct Keystore aliases; the E2EE identity is **not** in the Keystore (native, K_STATE-wrapped); `PublicE2eeIdentityMaterial` carries only public Curve25519/Ed25519/OTK bytes. Wrong-E2EE-to-right-DeviceAuth binding is prevented because `uploadPublicIdentity` requires the `DeviceAuthRegistered` predecessor carrying the thumbprint, and `commit` re-derives the live thumbprint and compares. `DeviceAuthKeyStatus.TerminalKeyLoss` explicitly documents that local E2EE state must **not** be deleted — and no code deletes it. No key reuse across domains found.

---

## DPoP VERIFICATION SEQUENCE

Exact order (`DpopProofVerifier.verify`, `:51-154`):
1. `SignedJWT.parse` → `MALFORMED`
2. `typ == "dpop+jwt"` → `INVALID_TYP`
3. `alg == ES256` → `UNSUPPORTED_ALG`
4. `header.getJWK()` present → `INVALID_JWK`
5. `!jwk.isPrivate` → `PRIVATE_KEY_IN_JWK`
6. cast `ECKey`, `curve == P_256` → `INVALID_JWK`
7. **`signedJwt.verify(ECDSAVerifier(ecKey))`** → `INVALID_SIGNATURE`
8. `computeThumbprint()` (RFC7638)
9. **`expectedJwkThumbprint != null` → constant-time compare** → `KEY_BINDING_MISMATCH` ← *conditional*
10. claims parse → `MALFORMED`
11. `htm == httpMethod.uppercase()` → `HTM_MISMATCH`
12. `htu == DpopHtu.normalize(targetUri)` → `HTU_MISMATCH`
13. `iat` present → `MISSING_IAT`; `iat ≥ now−120` → `IAT_STALE`; `iat ≤ now+120` → `IAT_FUTURE`
14. `jti` non-empty ∧ `length ≥ 22` → `INVALID_JTI`
15. **`accessToken != null` → `ath` present ∧ constant-time == SHA-256(token)** → `MISSING_ATH`/`ATH_MISMATCH` ← *conditional*
16. **`expectedNonce != null` → `nonce` present ∧ constant-time ==** → `MISSING_NONCE`/`NONCE_MISMATCH` ← *conditional*
17. `replayCache.recordIfAbsent(jti)` → `REPLAYED_JTI`

**Mandatory:** 1–8, 10–14, 17. **Optional (caller-controlled, default off):** 9, 15, 16. Ordering is correct — signature before claims, replay recorded **last** so a rejected proof does not burn a `jti` (explicitly tested).

## DPoP CALL-SITE SAFETY
**There is no caller.** `grep` over `android/src/main` + `crypto/android/src/main` finds **zero** construction sites for `DpopProofVerifier` and **zero** invocations of `.verify(`. The only callers are `DpopProofVerifierTest` (32 tests) — which do supply thumbprint, `ath`, nonce and a shared clock. Reachability: `PUBLIC_BUT_CURRENTLY_UNWIRED` / `FUTURE_INTEGRATION_SURFACE`. Assessed independently as a misuse surface: see CS-007.

## DPoP FAIL-OPEN DEFAULTS
```kotlin
class DpopProofVerifier(
    clock: DeviceAuthClock = SystemDeviceAuthClock,
    replayCache: DpopReplayCache = InMemoryDpopReplayCache(),   // fresh per verifier
    iatToleranceSeconds: Long = 120L)
fun verify(proof, httpMethod, targetUri,
    expectedJwkThumbprint: String? = null,   // ⇒ NO key binding
    accessToken: String? = null,             // ⇒ NO ath binding
    expectedNonce: String? = null)           // ⇒ NO nonce
```
`verify(proof, "POST", uri)` — the **simplest and most natural B-004 invocation** — returns `Valid` for a proof signed with an **attacker-generated P-256 key**, with no token binding, no nonce, and replay state private to that verifier instance. RFC9449 §4.3 requires `ath` verification whenever a proof accompanies an access token; here omission is the default. `AMBIGUOUS→FAIL_OPEN`.

## DPoP KEY CONFUSION

| Proof signed / presented with | Accepted? | Reason |
|---|---|---|
| Attacker-generated P-256 key, `expectedJwkThumbprint = null` | **ACCEPTED** | step 9 skipped; step 7 verifies the proof against its own embedded `jwk` |
| Attacker-generated key, thumbprint supplied | REJECTED | `KEY_BINDING_MISMATCH` (constant-time) |
| Wrong account key / wrong device key | REJECTED **iff** thumbprint supplied; otherwise ACCEPTED | same |
| Different endpoint | REJECTED | `HTU_MISMATCH` — **unless the two paths collide under CS-008** (`/a%2Fb` vs `/a/b`, `/%61dmin` vs `/admin`) |
| Different HTTP method | REJECTED | `HTM_MISMATCH`, uppercase-normalised both sides |
| Different access token | REJECTED **iff** `accessToken` passed; otherwise **not checked at all** | step 15 conditional |
| Missing nonce | REJECTED **iff** `expectedNonce` passed | step 16 conditional |
| Stale/future `iat` (>120 s) | REJECTED | `IAT_STALE`/`IAT_FUTURE` |
| Reused `jti` | REJECTED | `REPLAYED_JTI` — **within one cache instance / one process only** |
| RS256/HS256/`alg:none` | REJECTED | step 3 |
| Private key in `jwk` header | REJECTED | step 5, plus Nimbus refuses to build it |
| `typ` missing or wrong | REJECTED | step 2 |

## DPoP HTU

`DpopHtu.normalize` = `scheme.lowercase() + "://" + authority.lowercase() + uri.path`. **`uri.path` is `URI.getPath()` — percent-DECODED.** Empirically verified on JBR 21:

| Input | Output | Class |
|---|---|---|
| `https://api.test/v1/a%2Fb` | `https://api.test/v1/a/b` | **FAIL-OPEN — collides with the next row** |
| `https://api.test/v1/a/b` | `https://api.test/v1/a/b` | (collision partner) |
| `https://api.test/v1/%61dmin` | `https://api.test/v1/admin` | **FAIL-OPEN — collides with the next row** |
| `https://api.test/v1/admin` | `https://api.test/v1/admin` | (collision partner) |
| `https://api.test:443/v1/a` | `https://api.test:443/v1/a` | FAIL-CLOSED (interop): default port not elided |
| `https://api.test/v1/../admin` | `https://api.test/v1/../admin` | FAIL-CLOSED: `..` not resolved |
| `https://api.test//v1/a` | `https://api.test//v1/a` | FAIL-CLOSED: duplicate slash kept |
| `https://User:Pass@api.test/v1/a` | `https://user:pass@api.test/v1/a` | **LOW: userinfo retained and lowercased into a signed, transmitted JWT** |
| `https://api.test` (empty path) | `https://api.test` | AMBIGUOUS: not normalised to `/` |
| `https://[::1]:8443/v1/a` | `https://[::1]:8443/v1/a` | correct |
| `https://api.test/v1/a%zz` | `URISyntaxException` → `IllegalArgumentException` → `HTU_MISMATCH` | FAIL-CLOSED ✓ |
| `https://api.test/v1/caf%C3%A9` | `https://api.test/v1/café` | decoded — encoding-dependent |
| uppercase host / query / fragment | correctly lowercased / stripped | correct ✓ |

Fix: `getRawPath()` + explicit default-port elision + RFC3986 §6.2.2 path normalisation. Test gap: `DpopHtuTest` (7 tests) covers none of the failing rows.

## DPoP REPLAY CACHE
`InMemoryDpopReplayCache` — key: **`jti` alone** (not `(jti, jkt)`); expiry: 5 min (frozen ✓); clock: injectable, wall-clock in production; scope: **single instance, single process**; **max size: NONE**; eviction: head-scan with `break` on first non-expired entry — correct because insertion order is monotonic in time; concurrency: `@Synchronized`, correct; restart: **entire cache lost — every `jti` becomes replayable once**.
**No server-level replay protection is claimed or provided.** For a multi-instance B-004 backend this in-process cache provides **no** cross-instance protection; the KDoc says so, and nothing enforces it. `recordIfAbsent` is the correct atomic primitive for a future distributed implementation.

---

## ANDROID MANIFEST / COMPONENTS

| Property | Value | Verdict |
|---|---|---|
| Components | exactly **1**: `.MainActivity` | minimal ✓ |
| `MainActivity` exported | `true` with `MAIN`/`LAUNCHER` | required; no extras read, no URI handling, `onCreate` only calls `setContent` — **no reachable sensitive operation** ✓ |
| Services / Receivers / Providers | **none** | ✓ |
| Deep links / non-launcher intent filters | **none** (`extractDeepLinksDebug` produced nothing) | ✓ |
| Permissions | **none declared** — not even `INTERNET` | ✓ and corroborates ARCH-010 |
| `allowBackup` | `false` (explicit) | ✓ |
| `dataExtractionRules` | `@xml/data_extraction_rules` | ✓ |
| `usesCleartextTraffic` | not declared → **default `false`** for `targetSdk 34` | ✓ (implicit — should be made explicit before B-004) |
| `networkSecurityConfig` | absent | acceptable now; **required before B-004** (no pinning) |
| `debuggable` | not declared → build-type controlled | ✓ |
| `MainActivity` explicit `taskAffinity`/`excludeFromRecents`/`FLAG_SECURE` | absent | not yet needed (no sensitive UI) |

**Attack surface at this SHA: one launcher activity that renders a static string. Proven, not assumed.**

## BACKUP / DATA EXTRACTION
Static conclusion, defence in depth is correct:
- **API 26–30:** `allowBackup="false"` disables full-app cloud backup. `dataExtractionRules` is ignored (Lint confirms). ✓
- **API 31–34:** `dataExtractionRules` excludes `root`, `file`, `database`, `sharedpref`, `external` and all `device_*` domains from **both** `<cloud-backup>` and `<device-transfer>`. ✓
- `noBackupFilesDir` additionally used for the registration session store and the Device Auth binding marker — excluded regardless of rules. ✓
- K_STATE wrapped key, protected identity and session live in `filesDir` — covered by both mechanisms, and the wrapping key is a non-extractable Keystore key that is never backed up regardless. ✓
- Physical verification of actual backup behaviour across API levels: **NOT_RUN — device required.**

## LOCAL STORAGE
All sensitive writes use app-private internal storage: `context.filesDir` (`anox_state_key.enc`, `anox_identity.enc`, `anox_session.enc`) and `context.noBackupFilesDir` (`anox_registration_session.enc`, `anox_deviceauth_binding.state`). **No** external storage, **no** `MODE_WORLD_*`, **no** cache dir, **no** shared storage, **no** `FileProvider`, **no** content URI export, **no** caller-supplied absolute paths. All `File` construction is `File(dir, constantName)` — path traversal is structurally impossible. No explicit permission hardening; sandbox-inherited.

## WIPE
`CryptoBridge.wipeLocalCrypto()` (`:737-754`) — ordering is **correct**: `keyStore.deleteEntry(MASTER_KEY_ALIAS)` first (rendering the wrapped K_STATE and therefore all protected state permanently undecryptable), then `anox_state_key.enc`, `anox_identity.enc`, `anox_session.enc`.
Gaps: `File.delete()` return values **ignored** → `CryptoResult.success` on failed deletion (CS-010); `.tmp` siblings not removed; registration-session and binding-marker files out of scope; no `.wal`/`.shm` (no SQLCipher yet — `DESIGN_ONLY_NOT_IMPLEMENTED`, ARCH-009/MAINARCH-030). Practical impact bounded by the correct key-first ordering.

## LOGGING / SECRET LEAKAGE
**28 logging calls in the entire product, all in `CryptoBridge.kt`** (25×`Log.e`, 2×`Log.w`, 1×`Log.i`). Enumerated individually: every message is a fixed English string plus a `Throwable`. **No** key material, **no** plaintext, **no** ciphertext, **no** token, **no** grant, **no** native handle value, **no** filesystem path, **no** account/device/user ID is logged. `RegistrationGrant.toString()` → `"RegistrationGrant(***, …)"`; `LicenseCode.toString()` → `"LicenseCode(***)"`. `CryptoError` messages are fixed strings; Rust error strings never cross JNI (only `i32`). Rust `test_error_messages_no_secrets` passes.
Residual: no debug/release gating (`isMinifyEnabled=false`, no `-assumenosideeffects` for `Log`) → all 28 remain in release; attached `Throwable`s may carry platform-internal detail. **LOW.** `Failed(reason)` strings embed a Device Auth thumbprint (`:338`) — a public key hash, not a secret.

---

## UNWIRED SECURITY CODE

**UNWIRED-001 — the single most important reachability fact of this audit.**

`MainActivity.kt` is the only application entry point. Its entire body is `setContent { AnoxMessengerTheme { Surface { Greeting("anoX Messenger") } } }`. It constructs **nothing**. A `grep` for every security type across `android/src/main` + `crypto/android/src/main` returns only declarations, KDoc references, and the classes' own definitions — **no production instantiation of any of:**

`CryptoBridge.getInstance` · `CryptoBridgeLocalE2eeIdentityStep` · `RegistrationOrchestrator` · `FileRegistrationSessionStore` · `RegistrationSessionKey` · `AndroidKeystoreDeviceAuthKeyManager` · `FileDeviceAuthBindingStore` · `DpopProofFactory` · `DpopProofVerifier` · `InMemoryDpopReplayCache` · `SecureRandomJtiGenerator` · `DeviceAuthAccessTokenGenerator` · `AtomicFileWriter`.

Also unreachable at the native layer (no JNI export, no caller): `Identity::mark_keys_as_published`, `Identity::unpublished_one_time_keys`, `Identity::get_one_time_key(KeyId)`, `Session::session_id`, `Session::has_received_message`, `CryptoSerializer::zeroize`, `Identity/Session::zeroize`.
Never called by production code: `CryptoBridge.destroyIdentity`, `destroySession`, `wipeLocalCrypto`, `destroyAllCrypto`, `loadSession`, `saveSession`, `deserializeSession`, `encrypt`, `decrypt`, `createOutboundSession`, `createInboundSession`; `DeviceAuthBindingStore.clearBinding`; `DeviceAuthKeyManager.deleteKeyDestructively` (except CS-016).

**A secure component that is never called does not secure the product.** Conversely, this is why every finding below is latent rather than exploitable today.

## SAFE-WRAPPER BYPASS SURFACES

```
[any Kotlin code] ──► CryptoNative (public object, 17 public external fun) ──► JNI ──► unsafe deref
                 └──► CryptoBridge (intended sole path: lock + validation + K_STATE)
```
- `object CryptoNative` and all 17 `external fun` are **public**; nothing is `internal`, `private`, or module-restricted. `crypto/android/src/main/java` is compiled directly into the `:android` source set, so there is not even a module boundary.
- Bypassing `CryptoBridge` skips: the (inert) lock, the 32-byte size checks, `getExistingStateKey` vs `getOrCreateStateKey` separation, error translation, and buffer sizing.
- `CryptoBridge` itself leaks raw native pointers to callers as `Long`, so even the "safe" API hands out the primitive needed to bypass it.
- `getOrCreateStateKey`/`getExistingStateKey` are `internal` — reachable from anywhere in the same module, i.e. all of `:android`.
- `DeviceAuthBindingStore.clearBinding()` and `DeviceAuthKeyManager.deleteKeyDestructively()` are public interface members that defeat B-002 terminal-loss semantics.
Classification: `PUBLIC_BUT_CURRENTLY_UNWIRED` today; **high B-004 integration risk**.

## TODO/FIXME SECURITY ITEMS
**NONE.** Grep for `TODO|FIXME|HACK|XXX|STUB|placeholder|not implemented` across all production Kotlin and Rust returns only three legitimate, accurate scope statements (`DpopReplayCache.kt:26`, `DeviceAuthAccessTokenContract.kt:12`, `LicenseCode.kt:6`) declaring B-004 boundaries. No finding raised. Code hygiene here is genuinely good.

## SECURITY TEST FALSE-ASSURANCE RISKS
1. **The JNI bridge is never compiled by any automated gate** — `#[cfg(target_os = "android")]` + host-target `cargo test` (local and CI). 0/17 Rust tests reach it.
2. **`CryptoInstrumentedTest` (39 tests) is the only test that loads the real `.so` — and CI has no emulator job.** This suite would have caught CS-004 immediately.
3. **`CryptoBridge` has zero JVM unit tests.** CS-001 is a four-line, trivially unit-testable defect (`assertSame(getInstance(c), getInstance(c))`) that no test asserts.
4. **No test asserts the `.so` corresponds to the Rust source.** `validate_apk_contents.py` checks for forbidden docs and PEM markers only — no hash, no rebuild, no reproducibility.
5. **`RegistrationOrchestratorTest` (28) and `RegistrationCrashConsistencyTest` (12) use in-memory fakes** for the session store, binding store and E2EE step. They prove the *state machine*; they cannot and do not prove durability (CS-006), Keystore behaviour (CS-005) or real crypto sizing (CS-004).
6. **`DpopProofVerifierTest` (32) is genuinely adversarial** (wrong key, wrong method, wrong URI, wrong host, stale/future/missing `iat`, replay, tampered payload, private JWK, wrong `typ`, non-ES256, missing/wrong `ath`, missing/wrong nonce, `jti` not consumed on failure) — **but no test documents the danger of the default invocation**, i.e. that omitting `expectedJwkThumbprint` accepts an attacker's key.
7. **`DpopHtuTest` (7) tests only the passing cases.** No `%2F`, no `%61`, no `:443`, no `..`, no `//`, no userinfo, no IPv6, no empty path.
8. **`Zeroize` implementations are asserted by no test** — because they do nothing.

---

## IMPLEMENTATION SECURITY BOUNDARY TABLE

| Boundary | Enforcement layer | Bypass path | Failure mode | Verdict |
|---|---|---|---|---|
| Kotlin → JNI | `CryptoBridge` (locking + size + key-path checks) | **`CryptoNative` public object** | inert lock; raw `Long` handles exposed | **INEFFECTIVE** (CS-001, CS-102) |
| Native handle registry | `Mutex<HashSet<usize>>` membership check | TOCTOU after unlock; heap-address reuse | `&mut` aliasing (UB), UAF-on-race | **UNSOUND** (CS-002) |
| K_STATE read vs create | `getExistingStateKey` / `getOrCreateStateKey` split | `internal` visibility; module-wide | correct at every read site | **EFFECTIVE** ✓ |
| Registration session key | `RegistrationSessionKey` | `decrypt → getOrCreateKey` | silently mints a key on a read path | **FAIL-OPEN key manufacture** (CS-005) |
| Device Auth → registration | `status()` + `isProductionEligible()` + thumbprint revalidation | — | fails closed at every step | **EFFECTIVE** ✓ |
| Terminal-key-loss guard | `DeviceAuthKeyStateResolver` + binding marker | **delete the marker file**; `clearBinding()` | `TerminalKeyLoss` → `AbsentNotBound` | **CONDITIONALLY EFFECTIVE** (CS-009) |
| Keystore → local binding | `HardwareSecurityLevel` policy (`UNKNOWN`→ineligible) | — | fails closed | **EFFECTIVE** ✓ |
| Local state → persistence | temp+fsync+rename ×3 | — | rename not durable (no dir fsync) | **PARTIAL** (CS-006) |
| Protected-state confidentiality/integrity | AES-256-GCM + magic/version AAD | — | no epoch ⇒ rollback accepted | **PARTIAL** (CS-018) |
| Private-key non-export | Keystore (device auth) / native-only (E2EE) | — | no export API anywhere | **EFFECTIVE** ✓ |
| Verifier API → future server | `DpopProofVerifier.verify` | **default args** disable jkt/ath/nonce | attacker-key proof accepted | **FAIL-OPEN BY DEFAULT** (CS-007) |
| htu target binding | `DpopHtu.normalize` | decoded-path collisions | cross-endpoint proof reuse | **PARTIAL** (CS-008) |
| Replay protection | `InMemoryDpopReplayCache` | per-instance, per-process, unbounded | reset on restart; no cross-instance | **FOUNDATION ONLY** |
| Source → shipped binary | *(nothing)* | — | stale artifact ships | **ABSENT** (CS-003) |
| App attack surface | manifest, 1 launcher activity, 0 permissions | — | nothing reachable | **EFFECTIVE (by absence)** ✓ |

## IMPLEMENTATION-vs-ARCHITECTURE MATRIX

| Security requirement | Authority | Implementation | Actual behaviour | Match |
|---|---|---|---|---|
| E2EE private keys never leave native memory | SI-4, B-006 | `crypto/rust`, `PublicE2eeIdentityMaterial` | public material only crosses; no export API | **MATCH** |
| No account recovery / no key export / no seed | SI (no-recovery), B-002/B-003 | whole codebase | no backup, seed, mnemonic, export or admin path exists | **MATCH** |
| Local state encrypted with authenticated encryption | SI, B-009 | `serialization.rs` | AES-256-GCM + AAD, versioned, fail-closed | **MATCH** (rollback gap → PARTIAL) |
| K_STATE distinct from Device Auth key and E2EE identity | SI-24, B-002 | 3 distinct aliases + native identity | verified distinct, no reuse | **MATCH** |
| Device Auth key non-exportable, StrongBox pref / TEE ok / software rejected | B-002 v1.1 | `AndroidKeystoreDeviceAuthKeyManager`, `HardwareSecurityLevel` | correct, `UNKNOWN`→ineligible | **MATCH** (no attestation → PARTIAL) |
| Device Auth key loss is terminal; no silent replacement | B-002 v1.1 | `DeviceAuthKeyStateResolver`, binding store | logic correct; anchor file unauthenticated + non-durable | **PARTIAL** |
| DPoP RFC9449: ES256, jti ≥128 bits, iat ±120 s, 5-min replay window | B-002 v1.1 | `DpopProofFactory`/`Verifier`/`ReplayCache`/`JtiGenerator` | all parameters correct; bindings optional; cache in-process | **PARTIAL** |
| Shared server-side DPoP replay cache | B-002 v1.1 | interface only | in-process impl, documented as non-production | **NOT_IMPLEMENTED** |
| Access token: opaque 256-bit, server stores SHA-256, 15-min TTL, no refresh | B-002 v1.1 | `DeviceAuthAccessTokenContract` | contract constants + `ath`/hash helpers; no issuance | **NOT_IMPLEMENTED** (contract MATCH) |
| Registration is one atomic transaction, resumable, never recovery | B-003 v1.4 | `RegistrationOrchestrator` + codec + encrypted store | state machine correct and genuinely fail-closed | **MATCH** (durability → PARTIAL) |
| OTK private state persisted before public upload | B-003/B-006 | `CryptoBridgeLocalE2eeIdentityStep:41-47` | ordering correct — **but always fails at the default count** | **CONTRADICTION** (CS-004) |
| OTK publication tracking / replenishment | B-006 | `mark_keys_as_published` in Rust | **no JNI export, no caller** | **UNWIRED** |
| Grant: 256-bit, 30-min TTL, never plaintext on disk, never logged | B-003 v1.4 | `RegistrationGrant`, `RegistrationSessionKey`, codec | redacted `toString`, GCM-sealed, legacy plaintext files deleted | **MATCH** |
| Identifiers are server-issued UUIDv4, client validates only | B-003 v1.4 | `UuidV4`, `AccountId`/`DeviceId`/`RegistrationId` | version checked, **variant not** | **PARTIAL** (CS-014) |
| Serialised crypto state concurrency-safe | SI, B-006/B-009 | `ReentrantLock` + Rust registry | lock inert; registry TOCTOU; `&mut` aliasing | **CONTRADICTION** (CS-001, CS-002) |
| Secret material zeroised | SI, B-009 | `impl Zeroize` ×3 | 1 real (`CryptoSerializer`), 2 empty; pickle/K_STATE/grant buffers never cleared | **CONTRADICTION** |
| No private app data in cloud backup or D2D transfer | B-025 | manifest + `data_extraction_rules` + `noBackupFilesDir` | fail-closed on all domains, both channels | **MATCH** (physical verification pending) |
| Reproducible, provenance-verified native artifact | B-017 / B-018 | *(nothing)* | prebuilt `.so`, one commit, never rebuilt, stale vs source | **CONTRADICTION** (CS-003) |
| B-021 pre-product verification matrix machine-enforced | Amendments V1_3 | no validator | not enforced | **NOT_IMPLEMENTED** (ARCH-002) |
| Local database / SQLCipher / WAL wipe | B-009 | none | no DB code at this SHA | **NOT_IMPLEMENTED** |
| Attachment secretstream + size bounds | B-012 | none | no libsodium dependency | **NOT_IMPLEMENTED** (ARCH-005) |
| Backend service / DB schema / RLS | B-004, B-005 | interfaces only | correctly absent | **NOT_IMPLEMENTED** ✓ (ARCH-010) |
| Release signing / minification | B-018 | `isMinifyEnabled=false`, no signingConfig | unsigned, unshrunk | **NOT_IMPLEMENTED** |

## SECURITY INVARIANT TEST MAPPING

| Invariant | Code | Test | Property actually proven | Gap |
|---|---|---|---|---|
| E2EE private keys never leave native | `identity.rs`, `PublicE2eeIdentityMaterial` | `test_no_recovery_mechanism`, `test_key_separation` | no export API exists; keys differ across domains | none material |
| No recovery / no export | whole codebase | `test_no_recovery_mechanism` + manual API sweep | **genuinely proven** | none |
| Authenticated local state | `serialization.rs` | `test_authenticated_encryption`, `test_modified_ciphertext`, `test_corrupted_serialized_state`, `test_wrong_key_material`, `test_invalid_ciphertext` | tamper/wrong-key/corruption all rejected | **no rollback (older-valid-ciphertext) test** → CS-018 |
| Version/envelope fail-closed | `serialization.rs:94-102` | `test_invalid_state_key_length`, `test_buffer_too_small_error_code` | magic/version/length rejection | **`-11` asserted in source but the shipped binary returns `-2`** → CS-003 |
| Key domain separation | 3 aliases + native | `test_key_separation`, `DeviceAuthKeyLifecycleTest` | distinctness | Keystore aliases only verified on-device |
| Device Auth terminal loss | `DeviceAuthKeyStateResolver` | `DeviceAuthKeyLifecycleTest` (17) | resolver truth table + creation guard — **strong** | marker **durability** and **integrity** untested → CS-006, CS-009 |
| StrongBox/TEE eligibility | `HardwareSecurityLevel` | `DeviceAuthKeyLifecycleTest` | `UNKNOWN`/`SOFTWARE` ineligible | real `KeyInfo` path is `androidTest` only, never run in CI |
| DPoP claim validation | `DpopProofVerifier` | `DpopProofVerifierTest` (32) | **the security property, adversarially** | **no test on insecure defaults** → CS-007 |
| htu binding | `DpopHtu` | `DpopHtuTest` (7) | happy paths only | `%2F`, `%61`, `:443`, `..`, `//`, userinfo → CS-008 |
| jti entropy | `SecureRandomJtiGenerator` | `each proof uses a fresh jti`, `short jti is rejected` | freshness + min length | entropy **cannot** be verified; KDoc overclaims |
| Replay window | `InMemoryDpopReplayCache` | `InMemoryDpopReplayCacheTest` (6) | in-window reject, post-window accept | process-restart and unbounded-growth untested |
| Registration atomicity / resume | `RegistrationOrchestrator` | `RegistrationOrchestratorTest` (28), `RegistrationCrashConsistencyTest` (12) | transition legality, non-destructive failure, armed-state protection — **strong** | fakes only: no fsync, no Keystore, no real crypto |
| Session state codec robustness | `BinaryRegistrationStateCodec` | `RegistrationStateCodecTest` (12) | length bounds, unknown tags, round-trip | zero-length-file downgrade untested → CS-015 |
| Identifier canonicality | `UuidV4` | `IdentifierTest` (7) | version-4 acceptance | **variant untested and unimplemented** → CS-014 |
| Error mapping non-secret | `CryptoError` | `CryptoErrorMappingTest` (4), `test_error_messages_no_secrets` | no secrets in messages | **injectivity untested** → CS-013 |
| Concurrency safety of crypto state | `cryptoLock`, Rust registry | **NONE** | — | **TOTAL GAP** → CS-001, CS-002 |
| Zeroisation | `impl Zeroize` ×3 | **NONE** | — | **TOTAL GAP** → CS-011 |
| Native handle lifecycle | Rust registry | `CryptoInstrumentedTest` (never run in CI) | — | **TOTAL GAP** → CS-002, CS-012 |
| Artifact provenance | **none** | **NONE** | — | **TOTAL GAP** → CS-003 |
| B-008/B-009/B-010/B-011/B-012 invariants | — | — | — | `NOT_IMPLEMENTED` (not a test gap) |

---

## NEW CODESEC CANDIDATES
**21** — `ANOX-CODESEC-CANDIDATE-001` … `-021` (audit-local only; canonical registry untouched).

## CRITICAL
**1** — `-003`

## HIGH
**3** — `-001`, `-002`, `-004`

## MEDIUM
**8** — `-005`, `-006`, `-007`, `-008`, `-009`, `-010`, `-011`, `-012`

## LOW
**7** — `-013`, `-014`, `-015`, `-016`, `-017`, `-018`, `-019`

## INFO
**2** — `-020`, `-021`

---

## NEW FINDINGS TABLE

| Candidate | Sev | Root cause | Exact code evidence | Reachability | Security impact | Existing finding relation | Blocks | Reassessment | Specialist |
|---|---|---|---|---|---|---|---|---|---|
| **CS-003** | **CRITICAL** | No build step produces the shipped native library; prebuilt `.so` committed once and never rebuilt after the Rust source changed | `git log -- android/src/main/jniLibs` → **only** `7db20fa` (Aug 19); `git log 7db20fa..HEAD -- crypto/rust` → `342d553` (Sep 6) changed `lib.rs` (8× `-2`→`-11`) and `error.rs` (+`BufferTooSmall`); `git show 7db20fa:crypto/rust/src/lib.rs` has `-2` at lines 164,189,245,280,375,423,462,510 and no `-11` in `error.rs`; APK `.so` sha256 `11a958a5…`/`ecf9fdc1…` = repo blobs exactly; `ci.yml` has **no** cargo/cargo-ndk/cross step (NDK is installed and unused); `validate_apk_contents.py` performs no provenance check | **CURRENTLY_REACHABLE** — true of every APK built today | The audited source is not the executing code. LEGACY-FIX-01's Rust remediation is absent at runtime: a buffer overflow returns `-2` → `InvalidCiphertext` instead of `-11` → `BufferTooSmall`, misdiagnosing a sizing bug as state corruption. Every closed native finding and all on-device evidence tested a different binary. Unauditable 1.2 MB binary in the trust base | `REGRESSION_OF_CLOSED_FINDING` (`ANOX-LEGACY-CRYPTO-005`) + `EXPANDS ANOX-MAINARCH-013` | `BLOCKS_PRE_B004_HARDENING`, `BLOCKS_B004`, `BLOCKS_FINAL_PRODUCT_GATE`, `BLOCKS_RELEASE_CANDIDATE`, `BLOCKS_PRODUCTION_RELEASE` | **SEC-B** (crypto/JNI + supply chain) | CRYPTO/JNI + BUILD/SUPPLYCHAIN |
| **CS-001** | HIGH | `getInstance` never assigns `instance`; `cryptoLock` is per-instance | `CryptoBridge.kt:32-33,38-44,580` | `PUBLIC_BUT_CURRENTLY_UNWIRED` (no production caller) | Every documented serialisation guarantee is void. Enables CS-002's `&mut` aliasing and concurrent writes to the shared `.tmp` path; `initialize()`+Keystore re-run per call | `EXPANDS ARCH-001`, `EXPANDS ARCH-007`, `REGRESSION_OF_CLOSED ANOX-LEGACY-CRYPTO-005` | `BLOCKS_PRE_B004_HARDENING`, `BLOCKS_B004`, `BLOCKS_B008_B009` | **SEC-A** | CRYPTO/JNI |
| **CS-002** | HIGH | Registry mutex released before raw deref; membership ≠ exclusivity; freed heap addresses are reusable registry keys | `lib.rs:44-49,69-74` vs `:166,191,209,225,247,272,327,359,411,450,502`; free at `:142-147,480-485` | `PUBLIC_BUT_CURRENTLY_UNWIRED` (native reachable only via unwired Kotlin) | Concurrent `&mut` aliasing = Rust UB; destroy-racing-use = UAF; stale handle after address reuse = wrong-object operation. Ratchet: lost updates, duplicate message keys, state rollback, corrupted pickles | `CONFIRMS`/`EXPANDS ARCH-001`; `ANOX-LEGACY-INTEGRATION-005` root cause never actually fixed | `BLOCKS_PRE_B004_HARDENING`, `BLOCKS_B004`, `BLOCKS_B008_B009` | **SEC-B** (crypto/JNI domain) | CRYPTO/JNI + ATTACKCHAIN |
| **CS-004** | HIGH | Hard-coded 4096-byte serialisation buffer < actual pickle size at the default OTK count | `CryptoBridge.kt:340,528` `ByteArray(4096)`; `RegistrationOrchestrator.kt:352` `DEFAULT_ONE_TIME_KEY_COUNT = 20`; `CryptoBridgeLocalE2eeIdentityStep.kt:35-48`. **Measured out-of-tree (`/tmp`, unmodified crate):** 0 OTK→463 B, 10→2850, **15→4045 (last fit)**, **16→4305 (first fail)**, 20→**5280**, 50→12546, 100→24582 | `PUBLIC_BUT_CURRENTLY_UNWIRED`, but it is the **default path** the moment step 3 is wired | `uploadPublicIdentity` deterministically fails at the frozen default. OTK private material is generated in native memory and cannot be persisted; the handle leaks; retry re-generates. With CS-003 the runtime code is `-2 InvalidCiphertext`, so a sizing bug presents as cryptographic state corruption — a dangerous input to any recovery decision | **NEW** (contradicts the B-003/B-006 OTK-persist requirement) | `BLOCKS_PRE_B004_HARDENING`, `BLOCKS_B004`, `BLOCKS_B008_B009` | **SEC-A** | CRYPTO/JNI |
| **CS-005** | MEDIUM | Read path manufactures a Keystore key | `RegistrationSessionKey.kt:56-70` — `decrypt()` → `getOrCreateKey()` → `generateKey()`; contrast the deliberately split `CryptoBridge.kt:133-165` | `PUBLIC_BUT_CURRENTLY_UNWIRED` | After Keystore loss the session envelope becomes permanently unauthenticable **and** a new key silently exists; the failure is generic, so `currentState()`→`Failed`→`canStartNew` true unless the binding marker survived. The exact anti-pattern ARCH-007 fixed in `CryptoBridge`, left unfixed here | `EXPANDS ARCH-007`, `EXPANDS ARCH-003` | `BLOCKS_PRE_B004_HARDENING`, `BLOCKS_B004` | **SEC-A** | ANDROID/STORAGE |
| **CS-006** | MEDIUM | No parent-directory `fsync` after `rename` in any of the three "atomic" writers | `AtomicFileWriter.kt:17-25`; `CryptoBridge.kt:783-794`; AndroidX `AtomicFile.finishWrite` via `FileRegistrationSessionStore.kt:67` | `PUBLIC_BUT_CURRENTLY_UNWIRED` | `RegistrationOrchestrator.kt:203-209` documents `markArmed()` as durable arming before the remote call. A power failure shortly after can lose the rename → marker absent → `AbsentNotBound` → replacement Device Auth key permitted for a possibly-committed account, the exact outcome B-002 forbids | `EXPANDS ARCH-003` | `BLOCKS_PRE_B004_HARDENING`, `BLOCKS_B004` | **SEC-A** | ANDROID/STORAGE |
| **CS-007** | MEDIUM | Security-critical bindings are optional parameters defaulting to "off" | `DpopProofVerifier.kt:25-29,42-49,91,131,140` | `PUBLIC_BUT_CURRENTLY_UNWIRED` / `FUTURE_INTEGRATION_SURFACE` (no production caller) | `verify(proof, method, uri)` accepts a proof signed by any attacker-generated P-256 key, with no `ath` (contra RFC9449 §4.3) and no nonce, using a verifier-private replay cache. The easiest B-004 invocation is a complete authentication bypass. Enforced only by KDoc | **NEW** (adjacent to `ARCH-003`) | `BLOCKS_B004` | **SEC-A** | AUTH/DPoP |
| **CS-008** | MEDIUM | `URI.getPath()` returns the percent-decoded path, collapsing distinct targets | `DpopHtu.kt:34` (`uri.path`, should be `rawPath`). **Empirically verified (JBR 21):** `/v1/a%2Fb` → `/v1/a/b`; `/v1/%61dmin` → `/v1/admin`; `:443` not elided; `..`/`//` unresolved; userinfo retained and lowercased | `PUBLIC_BUT_CURRENTLY_UNWIRED` | Two distinct endpoints the server distinguishes normalise to one `htu` → a proof minted for one target is accepted for another. Also: default-port and path-form mismatches cause fail-closed interop breakage; credentials in a URI end up inside a signed, transmitted JWT | **NEW** | `BLOCKS_B004` | AUTH/DPoP |
| **CS-009** | MEDIUM | The anchor of the B-002 terminal-loss invariant is an unauthenticated 6-byte file, and `clearBinding()` is public API | `FileDeviceAuthBindingStore.kt:29,40-45,59-66` (magic+version+flags, no MAC); `DeviceAuthBindingStore.kt:54` | `PUBLIC_BUT_CURRENTLY_UNWIRED` | Correctly fail-closed on **corruption** (`(true,true)`), but **deletion** yields `(false,false)` → `TerminalKeyLoss` collapses to `AbsentNotBound` → replacement key creation permitted. `clearBinding()` gives any future caller the same bypass. Design tension acknowledged: the marker must survive Keystore loss, so it cannot be MAC'd by a key that may also be gone — a dedicated HMAC key plus "HMAC key missing ⇒ treat as bound" is the fail-closed resolution | `EXPANDS ARCH-003`; interacts with `ARCH-006` | `BLOCKS_B004` | **SEC-A** | ANDROID/STORAGE |
| **CS-010** | MEDIUM | `File.delete()` return values ignored; `.tmp` and sibling state files out of wipe scope | `CryptoBridge.kt:737-754` | `PUBLIC_BUT_CURRENTLY_UNWIRED` | `wipeLocalCrypto` returns `Success` even when protected identity/session deletion failed. `.tmp` artifacts from interrupted writes, and the registration-session / binding-marker files, are never removed. Impact bounded because the Keystore master key is deleted first | `CONFIRMS`/`EXPANDS ARCH-009`; joint with `ANOX-MAINARCH-030` | `BLOCKS_B008_B009`, `BLOCKS_FINAL_PRODUCT_GATE` | **SEC-A** | ANDROID/STORAGE |
| **CS-011** | MEDIUM | Declared zeroisation is a no-op; every intermediate secret buffer is left to `drop`/GC | `identity.rs:161-172` and `session.rs:101-112` (empty `Drop` + empty `Zeroize`); `serialization.rs:36,53,120` (pickle JSON never cleared); `lib.rs:268,302,498,532` (K_STATE `Vec<u8>` never cleared); `CryptoBridge.kt:133,156,337,366,431,446,489,495,622` (`ByteArray` never cleared); `FileRegistrationSessionStore.kt:50,60` (grant plaintext never cleared) | `PUBLIC_BUT_CURRENTLY_UNWIRED` | Full private identity, all OTK secrets, complete ratchet state, K_STATE and the 256-bit grant persist in freed native heap and in the JVM heap until GC — recoverable via heap dump, core dump, `.hprof`, or swap. Contradicts the explicit `Zeroize` contract. `CryptoSerializer` is the sole correct implementation | **NEW** | `BLOCKS_B008_B009`, `BLOCKS_FINAL_PRODUCT_GATE` | **SEC-B** (crypto domain) | CRYPTO/JNI |
| **CS-012** | MEDIUM | No owner destroys native handles; unbounded registry | `CryptoBridgeLocalE2eeIdentityStep.kt:61-75` (handle acquired, never destroyed); `CryptoBridge.kt:603-638` (`getLocalStateStatus` deserialises a fresh `Identity` per call); no `Cleaner`/`AutoCloseable`/`finally` anywhere; `lib.rs:31-36` sets grow only on explicit destroy | `PUBLIC_BUT_CURRENTLY_UNWIRED` | Every `ensurePublicIdentityMaterial`/`getLocalStateStatus` call leaks one `Box<Identity>` plus a permanent registry entry. Private key material stays resident for process lifetime, extending the CS-011 exposure window and growing the address space that CS-002's reuse hazard operates over | `EXPANDS ARCH-001`, `ANOX-LEGACY-INTEGRATION-005` | `BLOCKS_PRE_B004_HARDENING`, `BLOCKS_B004` | **SEC-A** | CRYPTO/JNI |
| **CS-013** | LOW | Native→JVM error codes are not injective | `error.rs:40-55` vs `lib.rs:106,109,114,161,244,253,370,459` — `-1`={`InvalidInput`, null/inactive handle}, `-3`={`InvalidSession`, `get_array_length` failure}, `-10`={`KeyError`, JNI length failure}, `-11`={`BufferTooSmall`, out-of-space}, `-12` unmapped→`UnknownError`; `CryptoError.kt:26-41` | `PUBLIC_BUT_CURRENTLY_UNWIRED` | "Stale/invalid native handle" is indistinguishable from "invalid input", defeating runtime diagnosis of the ARCH-001 defect class and any future automated detection | `CONFIRMS ARCH-008` (recommend raising ARCH-008 to MEDIUM) | `BLOCKS_B004` | **SEC-A** | CRYPTO/JNI |
| **CS-014** | LOW | RFC 4122 variant not validated despite an explicit KDoc claim | `UuidV4.kt:316,323-330` — `uuid.version() == 4` only, no `uuid.variant() == 2` | `PUBLIC_BUT_CURRENTLY_UNWIRED` | Non-canonical UUIDs (e.g. NCS variant with version nibble 4) are accepted, widening the identifier space beyond what the server issues; KDoc asserts a check that does not exist | `CONFIRMS ARCH-008` | `BLOCKS_B004` | **SEC-A** | AUTH/DPoP |
| **CS-015** | LOW | Zero-length file mapped to a clean initial state | `FileRegistrationSessionStore.kt:47` `if (envelope.isEmpty()) return RegistrationState.NotStarted` — contradicts the class KDoc "returns `NotStarted` only when no file exists" | `PUBLIC_BUT_CURRENTLY_UNWIRED` | Truncating the session file to 0 bytes downgrades state without raising `RegistrationSessionSecurityException`. Partly mitigated by the binding store, itself weakened by CS-009 | **NEW** | `BLOCKS_B004` | **SEC-A** | ANDROID/STORAGE |
| **CS-016** | LOW | Destructive Keystore deletion invoked from a `catch` block, contradicting the interface contract | `AndroidKeystoreDeviceAuthKeyManager.kt:110-116` calls `deleteKeyDestructively()`; `DeviceAuthKeyManager.kt:44-52` states it is "never called implicitly by any recovery, retry or error-handling path" | `REACHABLE_CURRENT_PRODUCT_PATH` within the class, but **cannot destroy a bound key** (guarded by the early `Present` return and `requireCreationAllowed`) | No exploitable path today; a latent hazard if `createKeyIfAbsent`'s guards are refactored during B-004. The broad `catch (Exception)` also silently downgrades StrongBox→TEE with no signal | **NEW** | `NON_BLOCKING` (fix with B-004 device-auth work) | **SEC-A** | ANDROID/STORAGE |
| **CS-017** | LOW | Initialisation failures swallowed; Keystore-loss misclassified | `CryptoBridge.kt:50-65,73-101` (`catch` + `Log` + continue); `:106-110` `keyStore.getKey(...) as SecretKey` NPEs on a missing alias; `:764-768` `isKeystoreOrUnwrapFailure` does not match NPE → `:635` `CorruptedIdentityState` instead of `MissingKeystore` | `PUBLIC_BUT_CURRENTLY_UNWIRED` | A usable-looking bridge is returned after `cryptoInit()` or master-key generation failed. A missing wrapping key is reported as *corrupted identity state* — a materially different and more alarming diagnosis that could drive an unnecessary destructive recovery | **NEW** (adjacent `ARCH-008` masking class) | `BLOCKS_B004` | **SEC-A** | CRYPTO/JNI + ANDROID/STORAGE |
| **CS-018** | LOW | No state generation/epoch in the protected-state envelope | `serialization.rs:68,76-82,110` — AAD = `magic‖format-version` only; no counter, no monotonic epoch, no external anti-rollback anchor | `PUBLIC_BUT_CURRENTLY_UNWIRED` | An older, valid ciphertext under the same K_STATE authenticates successfully → identity/session/OTK/ratchet rollback (replayed OTKs, rewound ratchet). Requires app-UID file write or an image-level restore | **NEW** | `BLOCKS_B008_B009` | **SEC-B** (crypto domain) | CRYPTO/JNI + ATTACKCHAIN |
| **CS-019** | LOW | Unbounded, attacker-influenced resource allocation; abort-on-panic | `lib.rs:206-213` (`count` up to `Int.MAX_VALUE`); `DpopReplayCache.kt:35` (no size cap); `lib.rs:31-36` (unbounded sets, cf. CS-012); `Cargo.toml:22` `panic = "abort"` | `PUBLIC_BUT_CURRENTLY_UNWIRED` | Any Rust panic or allocation failure aborts the whole process, skipping all `Drop`/zeroisation. The replay cache grows with valid-signature request volume — and under CS-007's default, "valid" includes attacker-keyed proofs | **NEW** | `BLOCKS_B004` (replay cache), else `NON_BLOCKING` | **SEC-A** | AUTH/DPoP + CRYPTO/JNI |
| **CS-020** | INFO | Release build unhardened and unsigned; ProGuard file effectively empty | `android/build.gradle.kts:24-32` (`isMinifyEnabled = false`, no `signingConfig`, no `debug` block); `proguard-rules.pro` (comments only, no `-keep`, no `Log` stripping) | `RELEASE_ONLY` | Full class/method names and all 28 `Log` calls ship in release. **Critically: with no `-keep class com.anox.crypto.CryptoNative`, enabling R8 later will rename the class and silently break `Java_com_anox_crypto_CryptoNative_*` symbol resolution at runtime** | **NEW**; B-018 `NOT_IMPLEMENTED` | `BLOCKS_RELEASE_CANDIDATE`, `BLOCKS_PRODUCTION_RELEASE` | **SEC-A** | BUILD/SUPPLYCHAIN |
| **CS-021** | INFO | Superseded one-shot governance validator retained in the prescribed baseline set | `tools/audit/validate_workforce_retest_closure_ingest.py` → **exit 1** at this SHA (`ANOX-TASK-SECURITY-ARCH-001 not Candidate`; `next_phase`/`post_merge_gate` not `AUDIT-SECURITY-ARCHITECTURE`) | `CURRENTLY_REACHABLE` (governance tooling) | Fails **closed** (correct) and is not in CI, but it will fail permanently, training operators to ignore a red validator — a classic alert-fatigue precursor. Recommend marking it historical/pinned-to-SHA | **NEW** (governance hygiene) | `NON_BLOCKING` | **SEC-A** | — |

*(Two bypass surfaces referenced above are recorded as sub-items rather than separate candidates, to respect §93 duplicate control: **CS-102** = `CryptoNative` fully public (folded into CS-001/CS-002 remediation); **CS-103** = no Keystore key attestation requested or verified (folded into `ARCH-006`).)*

## CONFIRMED EXISTING FINDINGS
`ANOX-SECURITY-ARCH-001` · `ANOX-SECURITY-ARCH-002` · `ANOX-SECURITY-ARCH-005` · `ANOX-SECURITY-ARCH-006` · `ANOX-SECURITY-ARCH-008` · `ANOX-SECURITY-ARCH-009` · `ANOX-SECURITY-ARCH-010`

## EXPANDED EXISTING FINDINGS
- **`ANOX-SECURITY-ARCH-001`** — root cause is a **TOCTOU + `&mut` aliasing** unsoundness (Rust UB), not a missing fail-closed check; the Kotlin compensating lock is **inert** (CS-001); handle leak and unbounded registry (CS-012); dead native security surface (`mark_keys_as_published` et al.). *Recommend severity CRITICAL.*
- **`ANOX-SECURITY-ARCH-003`** — the state machine is materially **better** than recorded (genuinely fail-closed, evidence-preserving, thumbprint-revalidating); the real gaps are the primitives beneath it: CS-005 (key manufacture on a read path), CS-006 (arming is not crash-durable), CS-009 (guard is unauthenticated and deletable), CS-015 (zero-length downgrade).
- **`ANOX-SECURITY-ARCH-007`** — the original K_STATE root cause **is remediated** in `CryptoBridge` (recommend LOW); the identical defect **persists unfixed** in `RegistrationSessionKey.decrypt()` (CS-005). Remediation was not applied consistently.
- **`ANOX-SECURITY-ARCH-008`** — exact non-injective code mapping enumerated (`-1`/`-3`/`-10`/`-11` overloaded, `-12` unmapped) plus the missing `UuidV4.variant()` check. *Recommend severity MEDIUM.*
- **`ANOX-SECURITY-ARCH-009`** — new distinct defect: `wipeLocalCrypto` returns **success on failed deletion**; `.tmp` and sibling `noBackupFilesDir` state files out of scope. *Recommend severity MEDIUM.*
- **`ANOX-SECURITY-ARCH-010`** — strengthened far beyond its recorded scope: **the entire implemented security subsystem is unwired from the application runtime** (UNWIRED-001), not merely B-004/B-005.
- **`ANOX-MAINARCH-013`** — expanded with code-level proof: exact commit divergence, byte-identical stale APK payload, absent CI native build, provenance-blind APK validator (CS-003).

## NOT REPRODUCIBLE EXISTING FINDINGS
**NONE.** No canonical `ANOX-SECURITY-ARCH-*` finding was found to be a false positive.
Classified `DESIGN_ONLY_NOT_IMPLEMENTED` (no code exists to reproduce against, correctly so): `ANOX-SECURITY-ARCH-004` (DB schema), `ANOX-SECURITY-ARCH-005` (attachment secretstream).

---

## ATTACK / FAILURE CHAINS

**AC-1 — Audited-source ≠ executing-code (evidence-integrity collapse).**
`ci.yml` has no native build step → `.so` frozen at `7db20fa` → `342d553` changes `lib.rs`/`error.rs` → APK ships the stale blob → a buffer overflow returns `-2` (`InvalidCiphertext`) instead of `-11` (`BufferTooSmall`) → every closed native finding, every instrumented test result, and all physical evidence describe a binary that is not the reviewed source.
→ **`CURRENTLY_REACHABLE`**

**AC-2 — Inert lock → Rust UB → ratchet compromise.**
`getInstance` never stores the singleton (CS-001) → N instances, N private locks → two threads enter `cryptoEncrypt(sameSession)` → registry check passes, mutex released, both take `&mut *Session` (CS-002) → aliased `&mut` (UB), lost ratchet updates, **duplicate message keys / keystream reuse**, corrupted pickle.
→ **`LATENT_UNTIL_B008_B009`** (requires messaging + concurrent use; blocked today by UNWIRED-001)

**AC-3 — Handle destruction + address reuse → wrong-identity operation.**
`destroyIdentity` → `release_identity` → `Box::from_raw` frees → allocator reissues the address to a new `Identity` → the address re-enters `ACTIVE_IDENTITIES` → a stale `Long` retained by Kotlin (guaranteed retained: nothing destroys handles, CS-012) passes `is_identity_active` → serialise/OTK/session operations execute against a **different identity**. Diagnosis is impossible because `-1` conflates "inactive handle" with "invalid input" (CS-013).
→ **`LATENT_UNTIL_B004`**

**AC-4 — Default OTK count bricks registration and misreports as corruption.**
`uploadPublicIdentity` → `ensurePublicIdentityMaterial(20)` → `generateOneTimeKeys(20)` mutates native state → `saveIdentity` → `serializeIdentity` with `ByteArray(4096)` vs a **measured 5280-byte** pickle → overflow → with CS-003 the runtime returns `-2` → `InvalidCiphertext` → `LocalE2eeIdentityStepException` → `failStep`. OTK private material exists only in leaked native memory (CS-012); retry regenerates and leaks again. A future recovery handler reading "invalid ciphertext / corrupted state" could reasonably decide to wipe.
→ **`LATENT_UNTIL_B004`** (but the defect is present and default today)

**AC-5 — DPoP default binding omission → full authentication bypass.**
B-004 calls `verify(proof, method, uri)` (the simplest overload) → `expectedJwkThumbprint == null` → step 9 skipped → an attacker generates a P-256 key, mints a syntactically perfect proof, self-signs → signature verifies against the embedded `jwk` → `ath` unchecked (`accessToken == null`) → nonce unchecked → `Valid`. Amplifier: each such proof also inserts into the **unbounded** in-process replay cache (CS-019).
→ **`LATENT_UNTIL_B004`**

**AC-6 — htu collision → cross-endpoint proof reuse.**
`normalize` decodes the path (CS-008) → a proof minted for `/v1/a%2Fb` presents an `htu` of `/v1/a/b` → the server's observed target `/v1/a/b` normalises identically → step 12 passes → the proof is accepted for an endpoint it was never issued for. Aggravated by AC-5 (no key binding to constrain who minted it).
→ **`LATENT_UNTIL_B004`**

**AC-7 — Replay cache scope → replay across restarts and instances.**
`InMemoryDpopReplayCache` is per-instance, per-process, non-persistent → a backend restart or a second replica makes every `jti` in the window replayable exactly once per instance. Documented in KDoc; enforced nowhere.
→ **`LATENT_UNTIL_B004`**

**AC-8 — Non-durable arming + key-manufacturing read path → duplicate device binding.**
`markArmed()` returns success but the rename is not directory-fsynced (CS-006) → power failure → marker absent → `isArmed == false`, `isBound == false`. In parallel/independently, `RegistrationSessionKey.decrypt` mints a fresh key on Keystore loss (CS-005) → session unauthenticable → `currentState()` → `Failed` → `canStartNew(Failed) == true` (marker gone) → a **new** Device Auth key is generated and bound while the server may already hold a committed account for the previous key. This is precisely the outcome B-002's terminal-loss invariant exists to prevent.
→ **`LATENT_UNTIL_B004`**

**AC-9 — Binding-marker deletion → invariant reset.**
An app-UID-capable or rooted actor (or a device-image restore) deletes `anox_deviceauth_binding.state` (CS-009) → `(false,false)` → `TerminalKeyLoss` → `AbsentNotBound` → replacement key creation allowed. `clearBinding()` offers the same effect as a public API call.
→ **`LATENT_UNTIL_B004`**

**AC-10 — Local state rollback.**
No epoch in the envelope (CS-018) → an older valid `anox_identity.enc`/`anox_session.enc` under the same K_STATE authenticates → OTK reuse and ratchet rewind. Requires app-UID file write; not remotely reachable.
→ **`LATENT_UNTIL_B008_B009`**

**AC-11 — Secret residency + abort-on-panic → heap-dump disclosure.**
Pickle JSON, K_STATE and grant plaintext are never zeroised (CS-011), handles are never destroyed so secrets stay resident for process lifetime (CS-012), and `panic = "abort"` skips all `Drop` on teardown (CS-019) → a heap dump, core dump, `.hprof` or swap page can yield the complete private identity and full ratchet state.
→ **`LATENT_UNTIL_B004`** for volume; the code defect exists today

**AC-12 — Test false assurance → gate progression.**
`cargo test` never compiles the JNI bridge; `CryptoInstrumentedTest` never runs in CI; `CryptoBridge` has no unit test; `validate_apk_contents.py` checks no provenance; ARCH-002's matrix gate is unenforced → 17 Rust + 177 JVM tests pass, lint is clean, all validators (bar one stale one) are green → CS-001, CS-003 and CS-004 pass every gate. **This chain already fired: it is why these defects reached a frozen main.**
→ **`CURRENTLY_REACHABLE`**

**AC-13 — Release minification enabling breaks JNI silently.**
`isMinifyEnabled = false` today with an empty ProGuard file (CS-020) → a future B-018 release-hardening flip to `true` renames `com.anox.crypto.CryptoNative` → `Java_com_anox_crypto_CryptoNative_*` no longer resolves → `UnsatisfiedLinkError` at first crypto use, in release builds only.
→ **`RELEASE_ONLY`**

*No chain requiring an unreachable precondition has been asserted. In particular: no remote attack chain exists at this SHA, because the app declares no permissions (not even `INTERNET`), exposes one launcher activity that renders a static string, and wires none of the security code.*

---

## BLOCKS PRE-B004 HARDENING
`CS-003`, `CS-001`, `CS-002`, `CS-004`, `CS-005`, `CS-006`, `CS-012`

## BLOCKS B004
`CS-003`, `CS-001`, `CS-002`, `CS-004`, `CS-005`, `CS-006`, `CS-007`, `CS-008`, `CS-009`, `CS-012`, `CS-013`, `CS-014`, `CS-015`, `CS-017`, `CS-019`

## BLOCKS B008/B009
`CS-001`, `CS-002`, `CS-004`, `CS-010`, `CS-011`, `CS-018`

## BLOCKS FINAL PRODUCT GATE
`CS-003`, `CS-010`, `CS-011`, plus resolution of `UNWIRED-001` and `ANOX-SECURITY-ARCH-002`

## BLOCKS RELEASE CANDIDATE
`CS-003`, `CS-020`

## BLOCKS PRODUCTION RELEASE
`CS-003`, `CS-020`

## NON-BLOCKING
`CS-016`, `CS-021`

## PHYSICAL_EVIDENCE_REQUIRED
`CS-002` (on-device/emulator UAF + ASAN repro), `CS-004` (on-device confirmation of the `-2` vs `-11` runtime code), `CS-005`, `CS-006`, `CS-009`, `CS-016`, `CS-017` (real Android Keystore + power-loss behaviour), and `ANOX-SECURITY-ARCH-006` / `ANOX-MAINARCH-018` (StrongBox/TEE).

---

## SEC-A FOLLOW-UP
`CS-001`, `CS-004`, `CS-005`, `CS-006`, `CS-007`, `CS-009`, `CS-010`, `CS-012`, `CS-013`, `CS-014`, `CS-015`, `CS-016`, `CS-017`, `CS-019`, `CS-020`, `CS-021`

## SEC-B FOLLOW-UP
- **Crypto / JNI / native-handle domain** — `CS-002`, `CS-011`, `CS-018` (+ `ARCH-001`). Any change to the handle-ownership model or zeroisation touches every native call site and must be re-audited as a domain.
- **Build / supply-chain / artifact-provenance domain** — `CS-003`. Introducing a reproducible native build changes the trust base of every prior native conclusion; a domain re-audit must re-verify all closed native findings against the newly built binary.

## SEC-C REQUIRED
**NO.**
Justification: no finding requires architectural redesign. CS-001 is a missing assignment. CS-002 requires moving serialisation inside Rust (per-object locks or `Arc<Mutex<_>>` handles with generation-tagged IDs) — a contained, well-understood change within the existing boundary. CS-003 requires adding a `cargo-ndk` job plus an artifact-hash gate. CS-004 is a buffer-sizing fix (two-call size query or a length-returning API). The frozen architecture, trust boundaries and invariants are **not** invalidated; the implementation and pipeline are.
**Escalation trigger to SEC-C:** if the CS-002 remediation changes the handle-ownership model such that Kotlin no longer holds raw pointers (e.g. an opaque generation-tagged handle table), **or** if a rebuilt native binary invalidates any previously closed `ANOX-LEGACY-CRYPTO-*` / `ANOX-LEGACY-INTEGRATION-*` conclusion, SEC-C becomes mandatory.

---

## SPECIALIST REVIEW ROUTING

### CRYPTO/JNI (`AUDIT-SECURITY-CRYPTO-JNI-001`)
`CS-001`, `CS-002`, `CS-003`, `CS-004`, `CS-011`, `CS-012`, `CS-013`, `CS-017`, `CS-018`, `CS-019`, `CS-102`, + `ARCH-001`, `ARCH-007`, `ARCH-008`.
**Required deliverables:** an emulator/ASAN use-after-free and `&mut`-aliasing reproduction; an exact-size serialisation contract; a native handle-ownership redesign proposal; a zeroisation audit of every secret buffer.

### AUTH/DPoP (`AUDIT-SECURITY-AUTH-DPOP-001`)
`CS-007`, `CS-008`, `CS-014`, `CS-019` (replay cache), + `ARCH-006`, `CS-103`.
**Required deliverables:** make `jkt`/`ath`/`nonce` mandatory (no insecure default); `getRawPath()` + RFC3986 §6.2.2 + default-port elision; a distributed replay-cache contract; a Keystore key-attestation verification design.

### ANDROID/STORAGE (`AUDIT-SECURITY-ANDROID-STORAGE-001`)
`CS-005`, `CS-006`, `CS-009`, `CS-010`, `CS-015`, `CS-016`, `CS-017`, + `ARCH-003`, `ARCH-009`.
**Required deliverables:** directory-`fsync` durability for all three writers; existing-only key retrieval everywhere; an integrity-protected, fail-closed binding marker; complete wipe scope with verified deletion.

### BUILD/SUPPLYCHAIN (`AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`)
`CS-003`, `CS-020`, `CS-021`, + `ARCH-002`, `ANOX-MAINARCH-013`.
**Required deliverables:** reproducible `cargo-ndk` native build in CI; artifact-hash / source-provenance gate in `validate_apk_contents.py`; Gradle dependency verification metadata; ProGuard JNI `-keep` rules; release signing; a B-021 matrix validator that fails closed.

### ATTACKCHAIN (`AUDIT-SECURITY-ATTACKCHAIN-001`)
`AC-1` … `AC-13`, with emphasis on `AC-1`, `AC-2`, `AC-4`, `AC-5`, `AC-8`, `AC-12`, and on the reachability transition the moment `MainActivity` wires the subsystem.

---

## SECURITY CODEBASE VERDICT

**1. Is the existing implementation safe enough to build additional product code on top of before remediation?**
**No.** Not because it is exploitable today — it demonstrably is not (see UNWIRED-001) — but because three foundation properties that B-004 will immediately depend on are **absent while appearing present**: (a) the shipped native binary is not the audited source (CS-003), so no native conclusion is trustworthy; (b) crypto-state serialisation does not exist despite a lock that looks like it does (CS-001 + CS-002); (c) the default E2EE identity-persistence path deterministically fails at the frozen default OTK count (CS-004), and fails with a *misleading* error. Building B-004 on this foundation would inherit a false verification baseline and would surface CS-004 as the first runtime symptom of the first real registration attempt.

**2. Which foundation defects should be corrected before B-004?**
`CS-003` (reproducible native build + artifact provenance gate — **do this first**, because every other native fix is unverifiable until the pipeline can prove what ships), `CS-001` (one-line assignment; then decide whether the lock belongs in Kotlin at all), `CS-002` (move serialisation into Rust; replace raw-pointer registry keys with generation-tagged handles), `CS-004` (exact-size serialisation contract), `CS-005`, `CS-006`, `CS-012`. Then, before wiring DPoP: `CS-007`, `CS-008`, `CS-009`.

**3. Which defects should deliberately wait until specialist audits finish?**
`CS-002`, `CS-011`, `CS-018` — all three touch the native handle-ownership and secret-lifetime model. A hasty fix (e.g. bolting another Kotlin lock on) would repeat exactly the mistake CS-001 represents: a control that looks correct and does nothing. These need `AUDIT-SECURITY-CRYPTO-JNI-001`'s ASAN reproduction and an agreed ownership design first. Likewise `CS-007`/`CS-008` should be resolved as one coherent DPoP contract under `AUDIT-SECURITY-AUTH-DPOP-001`, not patched parameter by parameter.

**4. Which previously "secure" controls are currently ineffective or only apparently secure?**
- `CryptoBridge.cryptoLock` — **inert**; the LEGACY-FIX-01 locking remediation serialises nothing.
- The LEGACY-FIX-01 Rust error remediation (`-11`/`BufferTooSmall`) — **not in the shipped binary**.
- `impl Zeroize for Identity` / `for Session` and both `Drop` impls — **empty bodies**.
- The native handle registry — validates membership, cannot prevent destroy-racing-use or address reuse.
- `RegistrationSessionKey` — the read/create split that was fixed in `CryptoBridge` was never applied here.
- "Atomic"/"durably arms" file writes — not crash-durable (no directory `fsync`).
- `DpopProofVerifier` key/token/nonce binding — present but **off by default**.
- `DpopHtu` canonicalisation — collapses distinct endpoints.
- The Device Auth binding marker — the anchor of the terminal-loss invariant is unauthenticated and deletable.
- `wipeLocalCrypto` — reports success on failed deletion.
- `UuidV4` variant validation — claimed, absent.
- `cargo test` / CI as assurance for the JNI layer — **never compiles it**.

**5. Which security properties are genuinely enforced by current code?**
- No account recovery, no key export, no seed/mnemonic, no admin restoration — verified by exhaustive API sweep, not by test alone.
- E2EE private key material never crosses the JNI boundary; only public Curve25519/Ed25519/OTK bytes do.
- Device Auth private key is non-extractable, `PURPOSE_SIGN` only, and never returned as bytes.
- Genuine key-domain separation across three distinct Keystore aliases plus native-only E2EE identity, with no reuse.
- `HardwareSecurityLevel.UNKNOWN` → not production eligible — absence of proof is never read as presence of protection.
- Authenticated protected-state encryption (AES-256-GCM, AAD-bound magic/version) with fail-closed rejection of every malformed, truncated, tampered, wrong-key, wrong-version and cross-type input.
- `getExistingStateKey` vs `getOrCreateStateKey` separation, correctly applied at all `CryptoBridge` read paths.
- The B-003 registration state machine: no illegal transition, terminal states never overwritten, resumable evidence never destroyed by transient failure, Device Auth thumbprint revalidated before irreversible arming, `markBound()` ordered before the `Committed` save, expiry suppressed once armed.
- Corrupt binding marker and unknown marker version → treated as bound+armed (correct fail-closed direction).
- Length-prefixed, bounds-checked, version-gated registration state codec.
- Secret redaction discipline: `RegistrationGrant`/`LicenseCode` `toString()`, zero secrets across all 28 logging calls, legacy plaintext session artifacts actively deleted.
- Backup/D2D exclusion, defence-in-depth across API 26–34, plus `noBackupFilesDir`.
- Minimal attack surface: one launcher activity, zero permissions, zero services/receivers/providers/deep links.
- Separate identity and session handle registries — effective type-confusion prevention.
- CI supply-chain hygiene: SHA-pinned actions, no dangerous triggers, read-only token, wrapper SHA validation, no dynamic Gradle versions.

**6. Which properties exist only in specification?**
Shared server-side DPoP replay cache; access-token issuance/persistence/revocation; server-side proof-of-factory-state and production-eligibility enforcement; Keystore key attestation; OTK publication tracking and replenishment (`mark_keys_as_published` exists in Rust and is unreachable); attachment secretstream and size bounds (B-012); local database / SQLCipher / WAL wipe (B-009); backend service and DB schema/RLS (B-004/B-005); release signing and minification (B-018); machine-enforced B-021 verification matrix; reproducible, provenance-verified native artifacts; and — most consequentially — **every implemented mechanism's actual invocation**, since nothing is wired to the application.

**7. Does any finding require architectural redesign?**
**No.** All 21 candidates are implementation or pipeline defects. The closest to structural is CS-002, which needs the native handle-ownership *model* revised (Rust-side per-object locking, generation-tagged handle IDs instead of raw addresses) — a redesign of a component's internals, not of the frozen architecture, trust boundaries, or security invariants. The specified security model is sound; the implementation under-delivers it and the pipeline cannot prove what it delivers.

**8. Is SEC-C required?**
**NO** — with the two escalation triggers stated in the SEC-C section above.

---

## PRODUCT DEVELOPMENT
`BLOCKED_PENDING_FINAL_AUDIT`

## B004
`NOT_STARTED`

## B005
`NOT_STARTED`

## SECURITY HARDENING PHASE
`IN_PROGRESS`

## FINAL OPERATIONAL ACCEPTANCE
`PENDING`

## HUMAN FINAL PRODUCT GATE
`NOT_EXECUTED`

## REPOSITORY MODIFIED
`NO` — no tracked file created, edited, or deleted; no branch, commit, push, PR, or merge; no registry, findings, tasks, runs, audits, Project Memory, or Authority mutation. Temporary artifacts were confined to `/tmp` (`/tmp/anox_codesec_cargo_target`, `/tmp/anox_probe`, `/tmp/anox_probe_target`, `/tmp/anox_htu`). Ignored build output produced by the permitted commands: `android/build/`, `build/`, `.gradle/` (all `.gitignore`d; reported separately per §98, not tracked mutation).

## BASELINE RECONFIRMED
**PASS** — `HEAD = origin/main = 869b99acac040412a29bbaadc76342070fb2085c`; `git status --short` empty; `git diff --check` empty.

---

## NEXT ACTION

`PRESERVE CODEBASE AUDIT → CANONICAL FINDINGS FREEZE LATER → CONTINUE SPECIALIST CLAUDE REVIEW WAVE → CONSOLIDATE ROOT CAUSES → HUMAN-APPROVED FOUNDATION REMEDIATION`

No emergency implementation is prescribed. `CS-003` is CRITICAL but not an active exploitation risk — it is an **evidence-integrity** defect. Its only urgent consequence is procedural, and it should be recorded now: **until a reproducible native build exists, no native-layer finding may be closed and no physical/instrumented evidence may be accepted**, because such evidence would test a binary that provably differs from the reviewed source. I recommend the Human Product & Security Owner treat that as an interim governance constraint rather than as a trigger for immediate code change.

Recommended specialist order (unchanged, and well-matched to the routing above):
1. `AUDIT-SECURITY-CRYPTO-JNI-001`
2. `AUDIT-SECURITY-AUTH-DPOP-001`
3. `AUDIT-SECURITY-ANDROID-STORAGE-001`
4. `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`
5. `AUDIT-SECURITY-ATTACKCHAIN-001`

One sequencing note offered for the Owner's judgement, not acted upon: `CS-003` routes primarily to specialist **4**, which is scheduled last. Since specialists 1–3 will produce native-layer conclusions that cannot be validated against the shipped artifact until `CS-003` is fixed, the Owner may wish to either promote the build/supply-chain review or authorise the native-build remediation as an isolated, independently-reviewed change ahead of the wave.

**Two items require your explicit decision before findings freeze:**
1. **Model deviation** — this run executed on Claude Opus 5 Medium, not Claude Fable 5.1 High. Confirm whether to accept it as `MODEL_DEVIATION` or re-run.
2. **`CS-021`** — `tools/audit/validate_workforce_retest_closure_ingest.py` now fails permanently at main and is listed in the §95 baseline validator set. Confirm whether it should be marked historical/SHA-pinned.

**STOP.**