# AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001 — FINAL REPORT

## AUDIT RESULT
`PASS_WITH_FINDINGS`

## AUDIT
`AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`

## PROVIDER
Anthropic

## MODEL
Claude Fable 5.1 High (label as reported by the runtime: "Claude Fable 5.1 High")

## MODEL REQUIREMENT SATISFIED
YES

## MODE
`READ_ONLY_BUILD_NATIVE_PROVENANCE_SUPPLY_CHAIN_SECURITY_AUDIT`

## AUDITED SHA
`869b99acac040412a29bbaadc76342070fb2085c`

## HEAD AT END
`869b99acac040412a29bbaadc76342070fb2085c`

## ORIGIN MAIN
`869b99acac040412a29bbaadc76342070fb2085c`

## WORKING TREE
CLEAN (`git status --short` empty; `git diff --check` clean; all experimental output confined to `/tmp/anox_buildsc_*` and git-ignored `build/` dirs)

## REMOTE MUTATION
NONE (only read-only `git fetch origin` and one `git ls-remote` per pinned action repository)

---

## CONSENSUS ROOTS IN SCOPE
`ROOT-001` `ROOT-017` `ROOT-018`

## ROOT-001
**CONFIRMED and EXPANDED** — proven with byte-level evidence (see below): the committed `.so` files are bit-identical to a rebuild of the *old* Rust source (`7db20fa`), and differ from the current source in exactly the `-2 → -11` return-code sites.

## ROOT-017
**CONFIRMED** — `jni_bridge` is `#[cfg(target_os = "android")]`; host `cargo test` (local and CI) never compiles a single line of the JNI module. No CI path cross-compiles, no CI path runs instrumented tests. Additionally two committed instrumented tests (`undersizedOneTimeKeyBufferReturnsBufferTooSmall`, `undersizedCurve25519BufferReturnsBufferTooSmall`) assert `-11` and would **fail** against the packaged binary.

## ROOT-018
**CONFIRMED and EXPANDED** — new sub-facts: (a) the JDK actually running Gradle is determined by `gradle/gradle-daemon-jvm.properties` (JetBrains 21 via foojay redirect URLs, no checksum), not by the Temurin 17 that CI installs; (b) AGP cannot locate the NDK locally so native libs are packaged unstripped, while CI links the NDK into the SDK and will strip → local and CI APKs embed different native bytes; (c) `REPOSITORY_SECURITY_POLICY.md` claims "Gradle lockfiles are retained" but none exist.

---

## BUILD INVENTORY
Tracked build-related files (exact):
```
build.gradle.kts                          (AGP 8.13.2, Kotlin 2.4.10, compose plugin 2.4.10 — apply false)
android/build.gradle.kts                  (app module; ndkVersion 26.2.11394342; no externalNativeBuild; no signingConfigs)
settings.gradle.kts                       (pluginManagement google/mavenCentral/gradlePluginPortal; foojay-resolver-convention 0.10.0; FAIL_ON_PROJECT_REPOS; deps google+mavenCentral)
gradle.properties                         (AGP flags; no org.gradle.caching)
gradle/gradle-daemon-jvm.properties       (toolchainVendor=JETBRAINS, toolchainVersion=21, 10 foojay toolchainUrl redirects)
gradle/wrapper/gradle-wrapper.properties  (gradle-9.3.1-bin, distributionSha256Sum set, validateDistributionUrl=true)
gradle/wrapper/gradle-wrapper.jar         (sha256 a8451eed…46e4, 63375 B)
android/proguard-rules.pro                (template only, no project rules)
android/src/main/jniLibs/arm64-v8a/libanox_crypto.so
android/src/main/jniLibs/x86_64/libanox_crypto.so
crypto/rust/Cargo.toml                    (anox_crypto 0.1.0, cdylib+rlib; release: opt-level "s", lto=true, panic="abort")
crypto/rust/Cargo.lock                    (v4, 110 packages, 109 checksums, 100% crates.io)
.github/workflows/ci.yml                  (single workflow, 5 jobs)
tools/security/b017_lite_policy_validator.py, test_b017_lite_policy_validator.py, validate_apk_contents.py
```
NOT present: `rust-toolchain(.toml)`, `.cargo/config.toml`, `gradle/verification-metadata.xml`, `*.lockfile`, `gradle/libs.versions.toml`, `buildSrc/`, convention plugins, `deny.toml`, `supply-chain/` (cargo-vet), `.github/dependabot.yml`, CODEOWNERS, pre-commit/gitleaks config, signing configs, `local.properties` (untracked, ignored). No external binary blobs other than the two `.so` and the wrapper jar.

## NATIVE ARTIFACT INVENTORY
| ABI | SHA-256 (committed) | Size | ELF | Stripped | Build-ID | `.comment` | First/last commit |
|---|---|---|---|---|---|---|---|
| arm64-v8a | `11a958a5f8b653692fdbf189dd42fa373cff729fdfef0cc5748afc5bfd3ea6c3` | 1,206,296 | AArch64 DYN | NO (.symtab/.strtab present, no .debug_*) | none (no `.note.gnu.build-id`) | Android clang 17.0.2 (r26c), LLD 17.0.2, rustc 1.97.1 (8bab26f4f) | `7db20fa` (2026-08-19) / never changed |
| x86_64 | `ecf9fdc1e83e419f1e1b9da6e83e184f5b3dfe694ee5de13529d68fc60653c88` | 1,201,736 | x86-64 DYN | NO | none | identical | `7db20fa` / never changed |

`.note.android.ident` = API 21 (cargo-ndk default; minSdk is 26 — harmless mismatch, INFO). 17 exported `Java_com_anox_crypto_CryptoNative_*` symbols per ABI, identical sets. Exact source SHA / toolchain for the committed binaries is **not** recorded anywhere in-repo; it is only reconstructible (and was reconstructed by this audit).

## TOOLCHAIN INVENTORY
Local: rustc/cargo 1.97.1 (stable-aarch64-apple-darwin, targets aarch64-linux-android + x86_64-linux-android installed), cargo-ndk 4.1.2, NDK 26.2.11394342 (r26c) at non-standard path `$SDK/android-ndk-r26c`, build-tools 34.0.0, JBR 21.0.9 (Android Studio) used as Gradle daemon JVM, Gradle 9.3.1.
CI: `dtolnay/rust-toolchain@4360b5…` = **floating `stable`** channel; Temurin 17 installed but daemon JVM criteria demand JetBrains 21 → auto-provisioned download at build time; NDK r26c via `nttld/setup-ndk`; no cargo-ndk, no Android targets installed, no cross-compilation.

## DEPENDENCY INVENTORY
Cargo: 8 direct (vodozemac 0.10.0, serde 1.0, serde_json 1.0, thiserror 1.0, zeroize 1.8, aes-gcm 0.10.3, getrandom 0.2, jni 0.21.1); 110 locked packages, all `registry+https://github.com/rust-lang/crates.io-index`, no git/path/patch/registry overrides. Duplicate versions: jni-sys, syn, thiserror, thiserror-impl, windows-sys (INFO). Proc-macro/build-script crates in graph: proc-macro2, quote, syn, serde_derive, thiserror-impl, zeroize_derive, jni-sys-macros; build.rs-bearing: libc, getrandom, serde etc. (standard). No project `build.rs`.
Gradle: all direct versions fixed (compose-bom 2023.10.01, core-ktx 1.12.0, nimbus-jose-jwt 10.9.1, junit 4.13.2, androidx.test 1.5.x, espresso 3.5.1); no `+`/latest/SNAPSHOT/ranges. Transitives unlocked and unverified.

## CI INVENTORY
`ci.yml`: triggers `push:main`, `pull_request:main`; workflow `permissions: contents: read`; concurrency group per ref. Jobs: `supply-chain-policy` → `gradle-wrapper-validation`, `rust` (cargo test --locked, host only) → `android-debug` (JDK17, SDK, NDK r26c, testDebugUnitTest, assembleDebug, validate_apk_contents) → `android-release` (assembleRelease unsigned, validate_apk_contents). Only artifact uploaded: unit-test HTML report. **No APK/.so artifact, no hashes, no provenance, no lint, no instrumented tests, no native build, no vulnerability scan.**

---

## SOURCE ↔ COMMITTED .SO
**`SOURCE_MATCHES_COMMITTED_BINARY = NO`** for both ABIs — proven three ways:
1. Rebuild of **current** source (`869b99a`) → arm64 `05f3f40cd4122ddd4286c513470f8bb6cdf54ca69b4c1879e53cb6a8ba22d7a2` (1,206,312 B), x86_64 `c002cc420813f3b8473be7aa82eb0af334bd73e6847cd1c893ce500845dfe798` ≠ committed.
2. Rebuild of **old** source (`git archive 7db20fa crypto/rust`, same Cargo.lock sha `a0a8b49f…`) → **exactly** the committed hashes `11a958a5…` / `ecf9fdc1…` for both ABIs.
3. Disassembly of `cryptoGetCurve25519PublicKey` (arm64): committed `mov w0, #-0x2`; rebuilt `mov w0, #-0xb`. Only `.text` differs (+8 bytes arm64; same size x86_64).
Divergence class = **A (source divergence)** — the 8 `-2 → -11` (`BufferTooSmall`) changes from LEGACY-FIX-01 (`342d553`, 2026-09-06). Toolchain metadata (`.comment`) is identical between committed and rebuilt.

## COMMITTED .SO ↔ APK
**IDENTICAL locally** (debug and release-unsigned APK both embed `11a958a5…` / `ecf9fdc1…`, unstripped). Gradle **copies committed jniLibs**; it does not compile Rust and obtains nothing elsewhere. Caveat: AGP printed `Unable to strip the following libraries, packaging them as they are: libanox_crypto.so` because the NDK is not at `$SDK/ndk/26.2.11394342`. In CI (`link-to-sdk: true`) AGP will strip → **CI APK native bytes ≠ repo `.so` ≠ local APK** (hash drift; inference from configuration — CI log not observable locally).

## CURRENT SOURCE REBUILD
SUCCESS for both ABIs. Exact command (from `crypto/rust`, `ANDROID_NDK_HOME=$SDK/android-ndk-r26c`):
`CARGO_TARGET_DIR=/tmp/… cargo ndk -t arm64-v8a -t x86_64 -o /tmp/… build --release --locked --offline`
cargo-ndk 4.1.2, rustc/cargo 1.97.1, NDK 26.2.11394342, triples aarch64-linux-android / x86_64-linux-android. No tracked file mutated.

## REPRODUCIBILITY
**`BIT_REPRODUCIBLE`** — two clean builds in separate target dirs produced identical SHA-256 for both ABIs; additionally the old-source rebuild reproduced the 22-day-old committed binaries byte-for-byte. Reproducibility on this host/toolchain is excellent; cross-host reproducibility is *not* established (see embedded paths).

## ABI PARITY
PASS — same source, same Cargo.lock, same profile, same features, identical 17-symbol export set, identical `.comment` metadata across arm64-v8a and x86_64.

## JNI SYMBOL PARITY
PASS — Rust `#[no_mangle]` set (17) == committed exports (17, both ABIs) == rebuilt exports (17) == `CryptoNative.kt` `external fun` set (17). No stale/missing/extra exports. Contract is intact; the **behaviour** behind 8 of those symbols is stale.

## EMBEDDED PATHS
48 strings of `/Users/<developer-username>/.cargo/registry/src/index.crates.io-…/<crate>/…` in each binary (vodozemac, bytes, serde_json, sha2, rand, curve25519-dalek, …) plus `/rustc/8bab26f4f…/library/std/...` (stable-toolchain paths, not privacy-relevant). Project files appear as relative `src/lib.rs`, `src/serialization.rs`. Impact: **privacy LOW** (leaks local username, no secrets); **reproducibility MEDIUM** (any other build host produces a different hash unless `--remap-path-prefix` or `trim-paths` is used — this is why the byte-identical result here is host-specific); **debug LOW** (symtab present, no DWARF). `strip`/`remap-path-prefix` should be required for release artifacts.

---

## RUST TOOLCHAIN PINNING
NONE. No `rust-toolchain.toml`. CI uses `dtolnay/rust-toolchain` pinned to an action commit that installs the **floating `stable`** channel — rustc version drifts with every Rust release (6-weekly). Local happens to be 1.97.1 which matches the committed binaries. Impact: reproducibility HIGH-risk over time; security MEDIUM (unreviewed compiler upgrades silently change shipped code).

## NDK PINNING
Partially. `ndkVersion = "26.2.11394342"` in Gradle and `r26c` in CI are the same release (good), but (a) Gradle never uses the NDK for compilation, only for stripping; (b) CI installs it but **never builds Rust with it** — false-assurance evidence; (c) cargo-ndk resolves NDK from `ANDROID_NDK_HOME` ad hoc; nothing binds the Rust cross-build to this version.

## CARGO LOCK / VERIFICATION
Cargo.lock committed, v4, 109/110 checksums (only the root crate lacks one — normal), `--locked` enforced in CI, `--locked --offline` works. No git/path deps. **No cargo-audit / cargo-deny / cargo-vet / cargo-auditable**; no license or banned-crate policy; duplicate-version drift undetected. Cargo transitive changes ARE detectable (lockfile diff + checksums) — materially stronger than Gradle.

## GRADLE VERSION PINNING
Direct plugin and dependency versions are fixed; no dynamic versions (validator + manual review agree). Transitive graph is **not** locked (no `*.lockfile`, no `dependencyLocking`).

## GRADLE DEPENDENCY VERIFICATION
**ABSENT.** No `gradle/verification-metadata.xml`. Versions pinned ≠ artifacts verified: downloaded jars/aars/plugins are trusted on TLS + repository integrity alone; a compromised or substituted artifact at the same coordinates would be invisible. Transitive changes are not detectable.

## GRADLE REPOSITORY TRUST
`google()` + `mavenCentral()` for deps, `+ gradlePluginPortal()` for plugins, `FAIL_ON_PROJECT_REPOS`, all HTTPS, no mavenLocal/flatDir/jcenter. No `content {}` filters (so a Google-coordinated artifact could theoretically resolve from Maven Central and vice-versa — realistic risk LOW given both are first-party registries). Dependency-confusion risk: LOW.

## WRAPPER TRUST
GOOD. `distributionSha256Sum` present, `validateDistributionUrl=true`, wrapper JAR committed and validated in CI by `gradle/actions/wrapper-validation` (SHA-pinned, resolves to v6.3.0). This is the strongest link in the Gradle chain — but it only covers Gradle itself, not dependencies.

## JDK / FOOJAY
`gradle/gradle-daemon-jvm.properties` mandates JetBrains Runtime 21 with 10 foojay `disco/v3.0/ids/<id>/redirect` URLs (TLS-only, **no checksum**, opaque redirect IDs). CI's `setup-java temurin 17` is therefore **not the JVM that runs Gradle**; Gradle auto-provisions JBR 21 at build time from a third-party redirect (`org.gradle.java.installations.auto-download` default true). Locally the Android Studio JBR satisfied the criteria (no download; daemon log confirms `Android Studio.app/Contents/jbr`). For release builds the JDK must be frozen to an exact vendor+version+checksum (or vendored/immutable image), and `compileOptions` (17) vs daemon (21) alignment documented.

---

## GITHUB ACTIONS
| Action | Ref | Resolves to (ls-remote, read-only) | Perms/creds |
|---|---|---|---|
| actions/checkout | `11d5960a…` | v4 / v4.4.0 | GITHUB_TOKEN read |
| gradle/actions/wrapper-validation | `9c971963…` | v6.3.0 (peeled) | none |
| dtolnay/rust-toolchain | `4360b525…` | **no longer a ref tip** (former `stable` branch tip; immutable commit) — installs floating `stable` Rust | none |
| actions/setup-java | `cf277c60…` | v4 / v4.9.1 | none |
| android-actions/setup-android | `40fd30fb…` | v4.0.1 | none |
| nttld/setup-ndk | `afb4c996…` | v1.5.0 (peeled) | actions/cache (local-cache) |
| actions/upload-artifact | `ea165f8d…` | v4 / v4.6.2 | GITHUB_TOKEN read |
All 7 third-party actions are 40-char SHA-pinned — satisfies Authority. Pin aging is unmanaged (no Dependabot/Renovate config in repo).

## WORKFLOW TRIGGERS
`push: [main]`, `pull_request: [main]` only. No `pull_request_target`, `workflow_run`, `workflow_call`, `workflow_dispatch`, `schedule`. No secrets referenced anywhere. No dangerous combination. PASS.

## TOKEN PERMISSIONS
Workflow-level `permissions: contents: read`; no job-level escalation; no `secrets.*`/`env.*` echoes. Least privilege PASS.

## REMOTE CONFIGURATION
`REMOTE_CONFIGURATION_UNVERIFIED` — branch protection/rulesets, required checks, GitHub secret scanning, Dependabot alerts, artifact attestation settings are not observable locally and were not queried.

## BUILD CACHE TRUST
Gradle build cache disabled; no `actions/cache` for Gradle/Cargo; only `nttld/setup-ndk local-cache: true` (NDK zip in actions cache). Poisoning surface: LOW. No artifact verification protects the cached NDK beyond the action's own logic (unverified).

---

## CI COVERAGE MATRIX
| Security property | CI job | Actually executed? | Artifact covered? |
|---|---|---|---|
| Governance validators (B-017-Lite policy) | supply-chain-policy | YES | n/a |
| Wrapper JAR integrity | gradle-wrapper-validation | YES | wrapper only |
| Rust host unit tests | rust | YES (17 tests) | **not the shipped binary; JNI module not compiled** |
| Android native Rust cross-build | — | **NO** | — |
| JNI symbol contract check | — | NO | — |
| Kotlin/JVM unit tests | android-debug | YES (177) | dex only |
| Android lint | — | **NO** (manual only) | — |
| assembleDebug | android-debug | YES | packages stale committed `.so` |
| assembleRelease (unsigned) | android-release | YES | same |
| APK content validation | both android jobs | YES | filename/text-suffix scan only |
| Native `.so` hash/provenance | — | NO | — |
| Instrumented / emulator JNI tests | — | NO | — |
| Physical device tests | — | NO | — |
| Dependency vulnerability / license scan (Cargo or Gradle) | — | NO | — |
| Secret scanning (repo/diff/history/artifact) | — | NO (validator scans APK text members only) | partial |
| SBOM / provenance attestation | — | NO | — |

## RUST HOST TEST RESULT
`cargo test --locked --offline` (target `/tmp/anox_buildsc_rust_host`): **17 passed, 0 failed**, 1 warning (`unused variable bob_otk_bytes`). JNI bridge not compiled on host.

## ANDROID NATIVE CROSS-BUILD
SUCCESS ×2 (current source) + ×1 (old source), both ABIs, `--locked --offline`. See hashes above.

## JVM TEST RESULT
`:android:testDebugUnitTest --offline --rerun-tasks`: **177 passed, 0 failures, 0 errors, 0 skipped**.

## LINT RESULT
`:android:lintDebug --offline`: **0 errors, 8 warnings** (OldTargetApi, GradleDependency, DataExtractionRules, ObsoleteSdkInt, StaticFieldLeak, UnusedResources, MonochromeLauncherIcon×2). Not in CI.

## INSTRUMENTED/JNI TEST STATUS
`NOT_RUN` in CI and not executed by this audit. `CryptoInstrumentedTest` (39 tests) + 27 tests in `android/src/androidTest`. Two tests assert `-11` and **cannot pass against the committed binary** (returns `-2`). Last recorded execution was at the 2026-08-19 baseline, arm64 only, against the baseline `.so`; x86_64 has **never** been executed.

## DEBUG APK
Built offline: `android-debug.apk` sha256 `f202c5e17a24b68bf3c741de0a7d5b5f88cbede2fb0ec7a6744ff2daa357379d`, debuggable, native-code arm64-v8a+x86_64, validator PASS.

## RELEASE APK
Built offline with `--rerun-tasks`: `android-release-unsigned.apk` sha256 `7207548704d74e6b3e36438993cf08443fa828e39960d2cf5e8e75b5d1182dad`, **unsigned** (no META-INF signature), not debuggable, `allowBackup=false`, `dataExtractionRules` set, minify disabled, same unstripped `.so`, validator PASS.

---

## APK VALIDATOR CAPABILITY
`validate_apk_contents.py` checks: forbidden path regexes (docs/governance files, `.env`, `.jks/.keystore/.p12/.pfx/.pem/.key` **by filename**), 4 PEM header markers in members with text-like suffixes ≤1 MiB, and prints inventory (dex count, native lib list, manifest/resources presence). It does **not** verify: ABI set, expected `.so` names/count, `.so` hashes/provenance, dex contents, assets, resources, native binary strings, credentials/tokens, debuggable flag, package id, permissions.
**Empirical bypass test (in `/tmp`, copy of the debug APK):** injected `lib/arm64-v8a/libinjected.so` containing a PEM marker, `assets/creds.bin` containing PEM + AKIA-style marker, and an extra `lib/armeabi-v7a/` directory with a wrong-arch binary → **RESULT: PASS**. It is a filename/text scanner, not a binary or provenance validator.

## SECRET SCANNING
No repo-level secret scanner (no gitleaks/trufflehog/pre-commit/CI step). History scan for secret-like filenames: none ever added. PEM markers in tracked files: only scanner patterns and a truncated dummy test fixture (`tools/audit/validate_mainarch_fix03.py`, `tools/continuity/generate_handoff.py`, `tools/continuity/test_handoff_and_validator.py:349`, `tools/security/validate_apk_contents.py`) — no exposure. `validate_b027a.py` performs a governance secret scan (PASS). False-negative classes: binary members, non-text suffixes, base64/JSON-embedded keys, API tokens, history.

## NATIVE PROVENANCE VALIDATION
ABSENT. Nothing records or checks source SHA, toolchain, or `.so` hash at any stage.

## SOURCE→ARTIFACT BINDING
ABSENT. The only binding today is this audit's manual reconstruction.

---

## SUPPLY-CHAIN THREAT TABLE
| Threat actor / source | Current exposure | Existing control | Gap |
|---|---|---|---|
| Stale developer artifact | **REALISED** (committed `.so` = old source) | none | no rebuild/hash gate |
| Accidental developer drift | REALISED (same) | none | same |
| Malicious contributor swapping `.so` | HIGH (PR review of binary is impossible) | human PR review | no source↔binary check |
| Compromised crates.io dependency | MEDIUM | Cargo.lock checksums, --locked | no audit/vet/deny |
| Compromised Maven artifact | MEDIUM | pinned versions, TLS | no verification-metadata |
| Compromised upstream JDK (foojay redirect) | MEDIUM | TLS | no checksum, vendor drift |
| Floating Rust toolchain | MEDIUM | none | no rust-toolchain.toml |
| Malicious GitHub Action | LOW | 40-char SHA pins, read-only token | no pin-update review cadence |
| Compromised CI runner | LOW today (no secrets, no release artifacts) | read-only token | future release path undefined |
| Compromised build cache | LOW | almost no caching | NDK cache unverified |
| Release operator error | N/A (no release pipeline) | Authority (human-only signing) | not yet implemented — correctly deferred |

## FALSE ASSURANCE RISKS
1. **CI installs NDK r26c in both Android jobs but never compiles Rust** — creates the impression of a native build.
2. **"Rust crypto tests" green ≠ JNI compiled** — `jni_bridge` is cfg-gated out on the host; a JNI compile error would pass CI.
3. **APK validator PASS ≠ native provenance OK** — proven by bypass test and by stale `.so` passing.
4. **`REPOSITORY_SECURITY_POLICY.md` claims Gradle lockfiles are retained** — none exist.
5. **Committed Cargo.lock ≠ vulnerability/license verification** — no scanning.
6. **Wrapper validation ≠ dependency verification** — covers only the Gradle distribution.
7. **`setup-java temurin 17` ≠ JVM used** — daemon runs JBR 21 auto-downloaded via foojay.
8. **Release APK job exists ≠ release security** — unsigned, unstripped-locally/stripped-in-CI, no hash record, no provenance.
9. **Historical byte-identical rebuild claim (BUILD-001 / MAINARCH-013 note)** — was true at `f245dc4`, is now stale evidence because source moved at `342d553`.
10. **Instrumented tests assert current-source behaviour but were never run post-fix** — the test suite would fail against the shipped binary.

---

## AUDIT-LOCAL FINDINGS

### TOTAL
12

### CRITICAL
0 exploitability-critical (EVIDENCE_INTEGRITY = CRITICAL on 001)

### HIGH
3 — `ANOX-BUILDSC-CANDIDATE-001`, `-002`, `-003`

### MEDIUM
5 — `ANOX-BUILDSC-CANDIDATE-004`, `-005`, `-006`, `-007`, `-008`

### LOW
3 — `ANOX-BUILDSC-CANDIDATE-009`, `-010`, `-011`

### INFO
1 — `ANOX-BUILDSC-CANDIDATE-012`

## FINDINGS TABLE
| Candidate | Severity | Evidence integrity | Root cause | Exact evidence | Consensus relation | Reachability | Blocks | Reassessment |
|---|---|---|---|---|---|---|---|---|
| **001** Committed `.so` built from `7db20fa`, not current source; APK ships pre-FIX-01 native behaviour (`-2` instead of `-11`) | HIGH | **CRITICAL** | No source→binary gate; binaries hand-built and committed | old-source rebuild == committed hashes byte-for-byte; current-source rebuild differs; disasm `#-0x2` vs `#-0xb`; `CryptoError.fromCode(-2)=InvalidCiphertext` | CONFIRMS ROOT-001; EXPANDS ANOX-MAINARCH-013 (Open) | Runtime: buffer-too-small mislabelled (MAINARCH-031 Rust half effectively unshipped); all native retest evidence invalid | BLOCKS_NATIVE_RETEST_ACCEPTANCE; BLOCKS_PRE_B004 (by dependency: hardening-phase native fixes cannot be accepted); BLOCKS_RELEASE_CANDIDATE | Re-verify after provenance fix with two clean rebuilds + APK extraction |
| **002** No CI path compiles or executes JNI code (host cfg-gate; no cross-build; no instrumented run) | HIGH | HIGH | Verification vacuum | `#[cfg(target_os="android")] mod jni_bridge`; ci.yml has no cargo-ndk/connectedAndroidTest; 2 instrumented tests would fail vs committed `.so` | CONFIRMS ROOT-017 | Any JNI regression ships undetected | BLOCKS_PRE_B004 (Authority: "Android instrumentation CI where technically reliable" is B-017-Lite pre-B004 scope); BLOCKS_RELEASE_CANDIDATE | After native CI gate exists |
| **003** Rust toolchain floats (`stable`), no `rust-toolchain.toml`; NDK installed in CI but unused for Rust; cargo-ndk absent from CI | HIGH | HIGH | Toolchain not project-pinned | ci.yml L49; no rust-toolchain file; `.comment` shows 1.97.1 only by coincidence with local | CONFIRMS ROOT-018; EXPANDS MAINARCH-013 | Reproducibility breaks on next Rust release | BLOCKS_PRE_B004 (prerequisite of 001 remediation) | With 001 |
| **004** Gradle artifacts unverified (no verification-metadata.xml, no lockfiles); `REPOSITORY_SECURITY_POLICY.md` falsely claims Gradle lockfiles exist | MEDIUM | MEDIUM | Deferred B017-DEF-001 + stale doc | absence of file; policy L24 | CONFIRMS ROOT-018; confirms B017-DEF-001 | Compromised Maven artifact undetectable | BLOCKS_RELEASE_CANDIDATE (Authority "Lockfiles/checksums/verifications required" for release); doc correction PRE_B004 | — |
| **005** JDK provenance: daemon JVM auto-provisioned from foojay redirect URLs, no checksum; CI's Temurin 17 is not the executing JVM | MEDIUM | MEDIUM | Gradle 9 daemon-JVM criteria + foojay | `gradle-daemon-jvm.properties`; ci.yml L65-69; local daemon log | EXPANDS ROOT-018 (new sub-fact) | Build-time download of unverified runtime | BLOCKS_RELEASE_CANDIDATE | — |
| **006** APK validator is filename/text-only; passes injected `.so`, wrong ABI, PEM in binary/asset; no `.so` identity/hash check | MEDIUM | HIGH | Validator scope | `/tmp` bypass test PASS | CONFIRMS ROOT-018/ROOT-001 (gate weakness) | Malicious/stale native member passes CI | BLOCKS_NATIVE_RETEST_ACCEPTANCE (as evidence gate); BLOCKS_RELEASE_CANDIDATE | — |
| **007** No vulnerability/advisory scanning (cargo-audit/OSV/Gradle) and no repo secret scanning in CI | MEDIUM | MEDIUM | B-017-Lite scope not completed | ci.yml; no tooling in repo | CONFIRMS ROOT-018; confirms B017-DEF-002 | Known-vuln crate/jar ships undetected | BLOCKS_PRE_B004 (Authority lists `cargo audit`, OSV, secret scanning as pre-B004 B-017-Lite scope; B-021 rows B017-002/004 are `pre_product_required` and `NOT_RUN`) | — |
| **008** Local vs CI native packaging divergence (AGP strip fails locally, succeeds in CI) → APK `.so` hashes differ by environment | MEDIUM | HIGH | NDK path/lookup inconsistency; no explicit strip policy | Gradle warning "Unable to strip…"; CI `link-to-sdk: true` | EXPANDS ROOT-001 (evidence comparability) | Evidence gathered locally ≠ CI artifact | BLOCKS_NATIVE_RETEST_ACCEPTANCE | Confirm with CI artifact hash once emitted |
| **009** Embedded `/Users/<username>/.cargo/registry/...` paths (48/binary); no `remap-path-prefix`/strip | LOW | — | Default rustc path embedding | `strings` output | Genuinely new (minor) | Username leak; cross-host non-reproducibility | BLOCKS_RELEASE_CANDIDATE | — |
| **010** Android lint not in CI (manual only; 0 errors / 8 warnings today) | LOW | — | B-017-Lite scope gap | ci.yml | CONFIRMS ROOT-018 | Static-analysis regressions unseen | BLOCKS_PRE_B004 per Authority B-017-Lite scope (low effort) | — |
| **011** No action-pin update cadence / Dependabot; `dtolnay/rust-toolchain` pin is a detached former-branch-tip | LOW | — | B017 residual | ls-remote result | confirms B-017-Lite residual | Pin aging | NON_BLOCKING / DEFERRED_FUTURE_SCOPE | — |
| **012** cargo-ndk default platform API 21 vs minSdk 26; duplicate crate versions; `panic="abort"` | INFO | — | Defaults | `.note.android.ident`; Cargo.lock | Not a finding | none | NON_BLOCKING | — |

## NEW ROOT CAUSES
None warranted. 005, 008, 009 are new *sub-facts* of ROOT-018/ROOT-001, not new roots.

## CONFIRMED CONSENSUS ROOTS
ROOT-001, ROOT-017, ROOT-018 — all confirmed with independent evidence.

## EXPANDED CONSENSUS ROOTS
ROOT-001 (proof of exact origin commit + behavioural delta + local/CI packaging drift); ROOT-018 (JDK/foojay executing-JVM fact; stale policy doc claim; validator bypass).

## REJECTED / NOT FINDINGS
- GitHub Actions pinning, triggers, token permissions — compliant.
- Gradle wrapper trust — compliant.
- Repository allow-list / FAIL_ON_PROJECT_REPOS — compliant.
- Cargo.lock hygiene — compliant.
- Signing absent — `NOT_IMPLEMENTED — CORRECTLY DEFERRED`; no key material in repo or history.
- R8/JNI renaming — `isMinifyEnabled=false`; AGP default `proguard-android-optimize.txt` already contains `-keepclasseswithmembernames class * { native <methods>; }`, so enabling R8 later would **not** break static JNI lookup as long as the default file stays referenced. Release-only watch item; not a finding.
- `panic="abort"` at JNI boundary — Rust panics abort the whole process instead of unwinding across FFI (which is UB). This is the *safer* choice for memory safety; consequences are availability (process kill) and no in-Rust secret cleanup on panic (Android process death clears memory anyway). Acceptable; document.
- Duplicate crate versions — normal for the ecosystem; INFO.
- `validate_mainarch_fix03.py` FAIL (structured "Claude provider" trigger fires on later audits) — `HISTORICAL_SHA_PINNED_VALIDATOR_CANDIDATE`, out of this audit's scope, not a build/supply-chain failure.

---

## PRE-B004 BLOCKERS
`ANOX-BUILDSC-CANDIDATE-001` (by dependency), `-002`, `-003`, `-007`, `-010`, doc-correction half of `-004`

## NATIVE-RETEST ACCEPTANCE BLOCKERS
`ANOX-BUILDSC-CANDIDATE-001`, `-006`, `-008` (and `-002` as enabling condition)

## RELEASE-CANDIDATE BLOCKERS
`ANOX-BUILDSC-CANDIDATE-001`, `-002`, `-003`, `-004`, `-005`, `-006`, `-007`, `-008`, `-009`, `-010`

## PRODUCTION BLOCKERS
All of the above plus B-018 human signing/update controls (already governed; not new findings) and SBOM (`ANOX-TEST-B017-003`, release_required).

## DEFERRED / FUTURE
`ANOX-BUILDSC-CANDIDATE-011`, `-012`; SBOM/CycloneDX; SLSA-level attestation beyond hash manifest; server-side branch protection (plan-dependent, UNVERIFIED).

---

## HISTORICAL B017 STATUS
| Historical claim | Status now |
|---|---|
| All `uses:` SHA-pinned, read-only token, no dangerous triggers | **VALID** |
| Wrapper SHA + wrapper-validation gate | **VALID** |
| Cargo.lock + `--locked` | **VALID** |
| "No dynamic Gradle versions" | **VALID** (direct deps) |
| B017-DEF-001 verification-metadata deferred | **STILL OPEN → now RELEASE-BLOCKING** (Authority text) |
| B017-DEF-002 cargo-vet/deny deferred | **STILL OPEN; cargo-audit/OSV are pre-B004 per DEVELOPMENT_SECURITY_WORKFLOW** → **PARTIAL** (Lite report deferred what Authority lists as Lite scope) |
| B017-DEF-003 SBOM/provenance LOW | **SUPERSEDED in part**: `.so` provenance is now proven broken (EVIDENCE_INTEGRITY CRITICAL); SBOM itself remains release scope |
| B017-DEF-004 branch protection | UNVERIFIED (remote) |
| MAINARCH-013 note "byte-for-byte identical rebuild" | **SUPERSEDED** — true for `f245dc4`, false since `342d553` |
| `REPOSITORY_SECURITY_POLICY.md` "Gradle lockfiles retained" | **INEFFECTIVE / INACCURATE** |

## LEGACY NATIVE FINDING EVIDENCE STATUS
`EVIDENCE_REVALIDATION_REQUIRED_AFTER_PROVENANCE_FIX` for:
- **`ANOX-LEGACY-CRYPTO-005`** (Closed) — fix is Kotlin-side (`cryptoLock`), so it *is* in the APK dex; but closure rests on source review + JVM tests with instrumentation `NOT_RUN`. Native concurrency behaviour has never been exercised on a current-source binary. Closure not contradicted; runtime evidence must be re-established.
- **`ANOX-MAINARCH-031`** (Closed) — **the Rust half of the fix is not in the shipped artifact.** Runtime behaviour today = pre-fix (`-2 → InvalidCiphertext`). Closure was source-level correct but artifact-level false. Do not reopen here; flag for consolidation.
- **`ANOX-SECURITY-ARCH-001`, `ANOX-LEGACY-INTEGRATION-005`, `ANOX-SECURITY-ARCH-008`** (Open) — any future retest must run against a provenance-verified binary; existing native observations are provisional.
- **`ANOX-MAINARCH-013`** (Open) — expanded, not closed; its "identical rebuild" supporting note is stale.
- Historical runtime reports (`android-runtime-crypto-validation-report.md`, baseline Aug-19) remain valid *for the baseline binary only*; x86_64 was never runtime-tested.

---

## RECOMMENDED .SO POLICY
**Option C** — CI builds the canonical per-ABI `.so` from source on every PR/main run; Gradle consumes the CI-built output (or a local build produced by the same pinned recipe), and the release pipeline consumes the immutable CI artifact. Rationale: Option A keeps un-reviewable binaries in Git and depends on cross-host reproducibility (currently blocked by embedded `/Users/...` paths); Option B alone leaves no immutable artifact for release binding. C gives auditability (hash manifest per run), eliminates stale-artifact risk, keeps offline dev builds possible via the pinned recipe, and aligns with B-017 "artifacts are hash-bound and immutable". Transitional step acceptable: keep committed `.so` **only** while a CI gate fails if `sha256(committed) != sha256(CI rebuild)`; remove them once Gradle consumes the build output directly.

## REQUIRED FUTURE NATIVE BUILD CHAIN
```
git SHA (checked out, clean)
→ rust-toolchain.toml (exact rustc, profile, targets aarch64/x86_64-linux-android, components)
→ Cargo.lock --locked --offline (vendored or checksum-verified registry)
→ pinned NDK 26.2.11394342 resolved from one canonical variable, version asserted
→ pinned cargo-ndk version
→ RUSTFLAGS --remap-path-prefix (or trim-paths) + explicit strip policy
→ clean per-ABI release build ×2 (separate target dirs) → hashes must be equal
→ JNI symbol contract test (nm exports == Rust #[no_mangle] set == CryptoNative.kt externals)
→ native-manifest.json {git_sha, rustc, cargo-ndk, ndk, cargo_lock_sha256, per-ABI sha256+size, build_id}
→ Gradle APK build consumes that exact output dir (jniLibs.srcDir = build output; fail if src/main/jniLibs exists)
→ extract APK lib/*/ → sha256 == manifest (post-strip hash also recorded)
→ JVM tests → lint (errors fatal) → instrumented JNI tests on emulator (arm64 + x86_64)
→ APK security validator v2 (ABI set, expected .so names/hashes, debuggable, packageId, binary marker scan)
→ upload {APK, native-manifest, SBOM later} as CI artifact; record digest in evidence
→ Human release gate / K_APK_RELEASE signing (offline) with pre/post hash record
```

## REQUIRED HASH / PROVENANCE SCHEME
Minimum for V1: **A + B combination** — a machine-generated native/APK hash manifest produced *in the same CI run* that built the binaries (not committed, not hand-editable), plus GitHub's build provenance attestation (or equivalent signed statement) over the manifest and APK, binding them to `github.sha` and the workflow file. Full SLSA/D (independently signed build manifest) is FUTURE_SCOPE. Anti-tamper property: expected hashes are never read from the repository; they are derived in-run and compared against the packaged bytes, so editing an "expected hash" file beside a malicious binary cannot satisfy the gate.

## REQUIRED TOOLCHAIN PINNING
`rust-toolchain.toml` (channel = exact version, e.g. "1.97.1", targets, components); cargo-ndk exact version (install with `--locked --version`); NDK exact revision asserted from `source.properties`; JDK exact vendor+version with checksum (drop foojay redirect for release; align daemon 21 vs compile 17 intentionally); Gradle already pinned; build-tools/platform pinned (already 34.0.0 / android-34).

## REQUIRED DEPENDENCY VERIFICATION
Pre-B004: `cargo audit` (or OSV) in CI; lint in CI; repo secret scan in CI; correct the lockfile claim in `REPOSITORY_SECURITY_POLICY.md`. Pre-RC: `gradle/verification-metadata.xml` (sha256 + PGP where available) with `--verify-metadata` failing on unknown artifacts; Gradle dependency locking; `cargo deny` (advisories, licenses, bans, sources); `cargo vet` optional; SBOM (CycloneDX) for both ecosystems; action-pin review cadence.

## REQUIRED CI GATES
1. native-build gate (chain above, fails on hash mismatch or symbol drift); 2. JNI instrumented gate (emulator, both ABIs); 3. lint gate (errors fatal); 4. advisory gate (cargo-audit/OSV); 5. secret-scan gate; 6. APK validator v2 gate; 7. artifact upload + provenance attestation; 8. (RC) verification-metadata gate; 9. (RC) SBOM gate.

## REQUIRED APK VERIFICATION
packageId = `com.anox.messenger`; `debuggable=false` for release; `allowBackup=false` + dataExtractionRules present; ABI set exactly {arm64-v8a, x86_64}; exactly one `libanox_crypto.so` per ABI with hash == native manifest; no other `.so`; no forbidden files; binary-wide marker scan (all members, not suffix-based); permissions list == expected; exported components == expected; versionCode/Name == release record; signing state (unsigned pre-signing, production-signer post-signing, fingerprint recorded); provenance manifest digest recorded.

---

## ITEMS THAT MUST BE FIXED TOGETHER
- 001 + 003 + 008 (native build pinning, CI cross-build, strip/remap policy, hash gate) — fixing one without the others recreates drift.
- 002 + 006 (instrumented JNI CI + validator v2) — a rebuilt binary without runtime tests, or tests without a validated artifact, leaves the evidence gap open.
- 004 doc correction with any Gradle verification work (avoid re-introducing overclaim).

## ITEMS THAT MUST NOT BE FIXED ALONE
- Re-committing freshly built `.so` files to "fix" the hash mismatch **without** the CI gate — this is the exact failure mode already observed and would falsely close ROOT-001.
- Adding `rust-toolchain.toml` without asserting it in CI (silent divergence).
- Enabling R8 without the JNI keep-rule confirmation.

## REMEDIATION ORDER
1. Pin toolchains (rust-toolchain.toml, cargo-ndk, NDK assert, remap/strip policy).
2. CI native cross-build + reproducibility check + JNI symbol test + native manifest.
3. Gradle consumes build output; remove/transition committed `.so`; APK hash gate; validator v2.
4. Instrumented JNI tests in CI (emulator, arm64 + x86_64).
5. Lint, cargo-audit/OSV, secret scanning in CI; fix policy doc.
6. Re-run native retests for CRYPTO-005 / MAINARCH-031 / SECARCH-001 / INTEGRATION-005 against the provenance-verified binary.
7. (RC) verification-metadata, dependency locking, cargo-deny, JDK freeze, SBOM, provenance attestation.
8. (Release) human signing procedure per B-018 V1.3.

---

## RETEST REQUIREMENTS AFTER REMEDIATION
- Two clean native rebuilds from the fixed SHA on CI and on one independent host → identical per-ABI hashes (after remap-path-prefix) or documented, diagnosed differences.
- Per-ABI hash manifest present; APK `lib/*` hashes == manifest (pre- and post-strip recorded).
- JNI symbol parity: exports == source == Kotlin externals, both ABIs.
- Rust host tests PASS; Android cross-build PASS; **instrumented JNI suite PASS on arm64 and x86_64** including the two `BufferTooSmall` tests.
- Validator v2 negative tests (injected `.so`, wrong ABI, binary PEM) → FAIL as expected.
- Revalidation of ANOX-LEGACY-CRYPTO-005, ANOX-MAINARCH-031 (runtime), and any Open native/JNI finding against the verified binary.
- Lint 0 errors; cargo-audit clean or accepted advisories recorded.

## SEC-A
010 (lint in CI), 011 (pin cadence), 012 (INFO), documentation correction in 004, 009 (remap/strip flags).

## SEC-B
001, 002, 003, 005, 006, 007, 008, and the Gradle-verification half of 004 — these change how trust is established for the shipped native artifact and its evidence chain, but do not change the product's trust architecture.

## SEC-C REQUIRED
**NO.** Trigger that would escalate: discovery that a committed binary was ever built from *non-repository* source or with an unrecorded toolchain; or a decision to move signing/provenance into an automated pipeline contrary to B-018. Neither is the case (origin commit and toolchain were fully reconstructed).

## ARCHITECTURAL REDESIGN
`BUILD_TRUST_CHAIN_REDESIGN` — the build/evidence pipeline must be redesigned; product architecture (crypto layer, JNI contract, Kotlin bridge) needs no redesign from this audit's findings.

---

## CRYPTO/JNI SPECIALIST HANDOFF
Verified facts the next audit may rely on:
- Audited source SHA: `869b99acac040412a29bbaadc76342070fb2085c`.
- **No committed or packaged binary represents current source.** Committed/APK `.so` (both ABIs) == source at `7db20fa4df8dc70392afd803fabaaf20c0b50d7d` built with rustc 1.97.1 + NDK r26c + cargo-ndk 4.1.2, release profile, current Cargo.lock. They return `-2` where current source returns `-11` (8 JNI functions); everything else is expected to be behaviourally identical (only `.text` differs, +8 bytes arm64) but this is inferred, not proven per-function.
- Current-source binaries **can** be produced: `/tmp/anox_buildsc_out_1/{arm64-v8a,x86_64}/libanox_crypto.so` (sha `05f3f40c…` / `c002cc42…`), bit-reproducible on this host. These are audit artifacts only — not authoritative, not in the tree.
- JNI source compiles for Android for both ABIs with `--locked --offline`; 17-symbol contract matches `CryptoNative.kt` exactly.
- Host `cargo test` exercises **zero** JNI code. `CryptoInstrumentedTest` reflects current-source expectations and has **not** been executed against any current-source binary; two tests would fail against the committed binary.
- What Crypto/JNI may inspect with confidence: Rust source, Kotlin bridge source, JNI contract, host-testable logic. What remains provisional: any runtime/artifact claim (handle lifecycle, concurrency, error mapping at runtime) until executed against a provenance-verified build. Recommended: if runtime probing is needed, build from source into `/tmp` with the exact command above and state the hash used; do not treat the committed `.so` as evidence of current behaviour.

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
`PENDING / NOT_EXECUTED`

## HUMAN FINAL PRODUCT GATE
`NOT_EXECUTED`

## REPOSITORY MODIFIED
NO

## BASELINE RECONFIRMED
PASS (`HEAD` = `origin/main` = `869b99acac040412a29bbaadc76342070fb2085c`, branch `main`, working tree clean, `git diff --check` clean)

---

## NEXT ACTION
`PRESERVE BUILD/SUPPLY AUDIT → NO FIX YET → RUN AUDIT-SECURITY-CRYPTO-JNI-001 → RUN AUTH/DPOP + ANDROID/STORAGE + ATTACKCHAIN SPECIALISTS → CONSOLIDATE ALL SPECIALIST FINDINGS → LARGE DEPENDENCY-SAFE REMEDIATION SESSIONS → INDEPENDENT RETESTS → ONLY THEN B004`

STOP.