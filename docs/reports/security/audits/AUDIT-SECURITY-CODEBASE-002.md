Preserving the blind findings snapshot to `/tmp` before any canonical-findings comparison.

# AUDIT-SECURITY-CODEBASE-002 — FINAL REPORT

## AUDIT RESULT
**PASS WITH FINDINGS** (0 CRITICAL, 3 HIGH, 6 MEDIUM, 6 LOW, 2 INFO). Product remains blocked regardless.

## AUDIT
AUDIT-SECURITY-CODEBASE-002

## PROVIDER
Anthropic

## MODEL
Claude Fable 5.1 High

## MODEL REQUIREMENT SATISFIED
YES

## BLINDNESS PRESERVED
YES

## BLINDNESS COMPROMISE
NONE. No `AUDIT-SECURITY-CODEBASE-001` report exists as a tracked, untracked or ignored file in the repository (searched `codebase|CODESEC|AUDIT-SECURITY`). Files carrying canonical `ANOX-SECURITY-ARCH-*` content (`findings.jsonl`, `FINAL_PRE_PRODUCT_SECURITY_ARCHITECTURE_AUDIT.md`, continuity/state docs, `validate_security_architecture_findings_freeze.py`) were not opened until after the blind checkpoint; in Phase E only `findings.jsonl` entries were read. One incidental exposure: the `validate_mainarch_fix03.py` validator output printed the ARCH-001 audit's *provider/model metadata* (not findings). Blind checkpoint preserved at `/tmp/anox_audit2/BLIND_CHECKPOINT_CODESEC2.md`.

## MODE
READ_ONLY_BLIND_INDEPENDENT_FULL_CODEBASE_SECURITY_AUDIT

## AUDITED SHA
`869b99acac040412a29bbaadc76342070fb2085c`

## HEAD AT END
`869b99acac040412a29bbaadc76342070fb2085c`

## ORIGIN MAIN
`869b99acac040412a29bbaadc76342070fb2085c`

## WORKING TREE
CLEAN (`git status --short` empty, `git diff --check` rc=0; only gitignored `android/build`, `.gradle`, `build/` touched by builds)

## REMOTE MUTATION
NONE

---

## SOURCE INVENTORY
396 tracked files. Implementation/security surface: `android/src/main` Kotlin 45 · `android/src/test` Kotlin 19 · `android/src/androidTest` Kotlin 3 · `crypto/android/src/main` Kotlin 4 · `crypto/android/src/androidTest` Kotlin 1 · Rust `crypto/rust/src` 6 (+`Cargo.toml`, `Cargo.lock` 110 packages / 109 checksums) · Gradle `.kts` 3 (+`gradle.properties`, wrapper) · workflows 1 · `tools/**/*.py` 37 (security 3) · Manifest 1 · res XML 17 · committed binaries 3 (`jniLibs/arm64-v8a/libanox_crypto.so` sha256 `11a958a5…6a6c3`, `jniLibs/x86_64/libanox_crypto.so` `ecf9fdc1…53c88`, `gradle-wrapper.jar`) · Java 0 · shell 0. No JNI C/C++; JNI is Rust `#[cfg(target_os="android")]`.

## SECURITY FILE REVIEW COVERAGE
All 50 production `.kt` files, 6 `.rs` files, Manifest, `data_extraction_rules.xml`, 3 `.kts`, `gradle.properties`, `proguard-rules.pro`, wrapper properties, `ci.yml`, `tools/security/*` (3), both `.so` (symbol/disassembly) — **REVIEWED**. UI theme (3 files), launcher resources (14), `tools/audit|continuity|workforce/*.py` (34) — NOT_REVIEWED — no security relevance / governance tooling only (validators were executed, not source-reviewed).

## FILE-BY-FILE COVERAGE

| File | Purpose | Security relevance | Reviewed | Findings |
|---|---|---|---|---|
| `crypto/rust/src/lib.rs` | JNI bridge, handle registries | HIGH | REVIEWED | C-005, C-012, C-010 |
| `crypto/rust/src/identity.rs` | vodozemac Account wrapper | HIGH | REVIEWED | C-003, C-010 |
| `crypto/rust/src/session.rs` | Olm Session wrapper | HIGH | REVIEWED | C-010 |
| `crypto/rust/src/serialization.rs` | AES-256-GCM envelope | HIGH | REVIEWED | C-009, C-010 |
| `crypto/rust/src/error.rs` | error codes | MED | REVIEWED | C-012 |
| `crypto/rust/src/tests.rs` | host tests | MED | REVIEWED | false-assurance note |
| `crypto/rust/Cargo.toml/.lock` | deps | MED | REVIEWED | — |
| `crypto/android/.../CryptoNative.kt` | public JNI externs | HIGH | REVIEWED | C-005 |
| `crypto/android/.../CryptoBridge.kt` | K_STATE, persistence, lock | HIGH | REVIEWED | C-002, C-004, C-008, C-011, C-016 |
| `crypto/android/.../CryptoError.kt` / `CryptoResult.kt` | error mapping | MED | REVIEWED | C-012 |
| `crypto/android/.../CryptoInstrumentedTest.kt` | device tests | MED | REVIEWED | false-assurance note |
| `account/RegistrationOrchestrator.kt` | B-003 state machine | HIGH | REVIEWED | C-014, C-016 |
| `account/RegistrationState.kt` | state hierarchy | MED | REVIEWED | — |
| `account/FileRegistrationSessionStore.kt` | encrypted session store | HIGH | REVIEWED | C-013, C-014 |
| `account/BinaryRegistrationStateCodec.kt` | codec | MED | REVIEWED | C-013 (minor) |
| `account/RegistrationGrant.kt` | grant holder | MED | REVIEWED | C-010 (String) |
| `account/CryptoBridgeLocalE2eeIdentityStep.kt` | E2EE public material | HIGH | REVIEWED | C-002, C-003, C-016 |
| `account/LocalE2eeIdentityStep.kt`, `PublicE2eeIdentityMaterial.kt`, `RegistrationApi.kt`, `RegistrationSessionStore.kt`, `RegistrationSessionSecurityException.kt` | contracts | MED | REVIEWED | C-003 (no key ids) |
| `account/UuidV4.kt`, `AccountId/DeviceId/RegistrationId.kt` | identifiers | LOW | REVIEWED | lenient `UUID.fromString` (INFO) |
| `account/Username.kt`, `LicenseCode.kt`, `LicenseDuration.kt`, `Entitlement*.kt`, `AccountState.kt`, `DeviceState.kt` | value types | LOW | REVIEWED | — |
| `security/keystore/RegistrationSessionKey.kt` | Keystore AES key | HIGH | REVIEWED | C-008, C-009 |
| `security/deviceauth/AndroidKeystoreDeviceAuthKeyManager.kt` | P-256 key lifecycle | HIGH | REVIEWED | C-014 |
| `DeviceAuthKeyManager.kt`, `DeviceAuthKeyStateResolver.kt`, `DeviceAuthKeyStatus.kt`, `HardwareSecurityLevel.kt` | lifecycle logic | HIGH | REVIEWED | — (sound) |
| `DeviceAuthBindingStore.kt`, `FileDeviceAuthBindingStore.kt` | binding marker | HIGH | REVIEWED | C-013 |
| `storage/AtomicFileWriter.kt` | atomic write | MED | REVIEWED | no dir fsync (durability note) |
| `DpopProofVerifier.kt` | DPoP verify | HIGH | REVIEWED | C-006 |
| `DpopHtu.kt` | htu normalization | HIGH | REVIEWED | C-007 |
| `DpopProofFactory.kt`, `DpopReplayCache.kt`, `DpopVerificationResult.kt`, `JtiGenerator.kt`, `DeviceAuthClock.kt`, `DeviceAuthSigner.kt`, `DeviceAuthAccessTokenContract.kt` | DPoP support | MED-HIGH | REVIEWED | C-006 |
| `MainActivity.kt` | Hello-world UI | LOW | REVIEWED | nothing wired |
| `AndroidManifest.xml`, `data_extraction_rules.xml` | attack surface / backup | HIGH | REVIEWED | — (sound) |
| `android/build.gradle.kts`, root `.kts`, `settings.gradle.kts`, `gradle.properties`, wrapper | build | MED | REVIEWED | C-015 |
| `proguard-rules.pro` | R8 (minify disabled) | LOW | REVIEWED | — |
| `.github/workflows/ci.yml` | CI | HIGH | REVIEWED | C-001, C-015 |
| `tools/security/validate_apk_contents.py`, `b017_lite_policy_validator.py` | supply-chain tooling | MED | REVIEWED | C-015 (text-suffix scan only) |
| `jniLibs/*/libanox_crypto.so` (×2) | shipped native | HIGH | REVIEWED (nm/readelf/objdump) | C-001 |
| JVM tests (19 files, 177 tests) | assurance | MED | REVIEWED (names/structure + key tests) | false-assurance notes |
| androidTest (3 app + 1 crypto files) | assurance | MED | REVIEWED | not runnable here |
| `ui/theme/*.kt` (3), launcher res (14) | UI | none | NOT_REVIEWED — no security relevance | — |
| `tools/audit|continuity|workforce/*.py` (34) | governance | none (code) | NOT_REVIEWED — executed only | C-017 |

---

## BLIND FINDINGS SNAPSHOT
### TOTAL — 17
### CRITICAL — none
### HIGH — CANDIDATE-001, CANDIDATE-002, CANDIDATE-003
### MEDIUM — CANDIDATE-004, -005, -006, -007, -008, -009
### LOW — CANDIDATE-010, -011, -012, -013, -014, -015
### INFO — CANDIDATE-016, -017

---

## INDEPENDENT FINDINGS TABLE

| Candidate | Sev | Root cause | Evidence | Reachability | Impact | Blocks | Reassess | Specialist |
|---|---|---|---|---|---|---|---|---|
| ANOX-CODESEC2-CANDIDATE-001 | HIGH | Committed `.so` binaries are stale vs. frozen Rust source; no native build in CI; no provenance | `.so` last changed at `7db20fa` (2026-08-19); `lib.rs`/`error.rs` changed at `342d553` (2026-09-06). Disassembly of committed arm64 `cryptoGetCurve25519PublicKey`: `cmp w8,#0x20 → mov w0,#-0x2`; x86_64 `movl $0xfffffffe`. Rebuild from HEAD (cargo-ndk, `/tmp`): `mov w0,#-0xb`. Debug APK ships the stale hashes. Binary embeds `/Users/<dev>/.cargo/registry/...` paths. | CURRENTLY_REACHABLE (every APK built at this SHA) | Audited source ≠ shipped code; `BufferTooSmall` surfaces as `InvalidCiphertext`; instrumented tests expecting `-11` would fail on shipped binary; invalidates source-based native evidence | BLOCKS_PRE_B004_HARDENING, BLOCKS_RELEASE_CANDIDATE | SEC-B | BUILD-SUPPLYCHAIN |
| CANDIDATE-002 | HIGH | Fixed 4096-byte serialize buffers (`CryptoBridge.kt:340,528`) | `/tmp` proof against frozen crate: identity 0 OTK=459 B, 5=1671 B, **20=5277 B**, 50=12571 B, 100=24673 B; session after 39 skipped msgs=**6438 B**. `DEFAULT_ONE_TIME_KEY_COUNT=20` → `saveIdentity` in `CryptoBridgeLocalE2eeIdentityStep:44` fails deterministically → step 3 can never succeed with defaults. | PUBLIC_BUT_UNWIRED (deterministic on B-004 wiring); LATENT_UNTIL_B008 for sessions | Registration foundation non-functional at defaults; session persistence failure after decrypt → unpersisted ratchet advance / stale state reload | BLOCKS_B004, BLOCKS_B008_B009 | SEC-B | CRYPTO-JNI |
| CANDIDATE-003 | HIGH | OTK enumeration by index over a per-call `HashMap` (`identity.rs:61`, vodozemac `one_time_keys()` collects into fresh `HashMap`) | `/tmp` proof: 20/20 index sweeps had duplicates; one sweep yielded 12 unique of 20; two sweeps differ in order. `PublicE2eeIdentityMaterial` carries raw keys only (no `KeyId`); `mark_keys_as_published`/fallback keys not exposed via JNI. | PUBLIC_BUT_UNWIRED | Uploaded OTK set has duplicates and omissions; B-006 "same key id ≠ value is security error", publish-after-ACK and OTK claim semantics are not implementable on this JNI surface | BLOCKS_B004, BLOCKS_B008_B009 | SEC-B | CRYPTO-JNI |
| CANDIDATE-004 | MEDIUM | `CryptoBridge.getInstance` never assigns `instance` (`CryptoBridge.kt:38-44`) | Every call constructs a new bridge with its own `cryptoLock`; the documented "single ReentrantLock serializes all state ops" (LOCAL_KEY_STATE_LIFECYCLE §D/§O) does not hold across callers; `stateKeyDeterministicWrap` test asserts key equality, not identity | LATENT (single caller today) | Makes C-005 JNI races reachable once ≥2 components hold a bridge; concurrent atomic writes to same `.tmp` name | BLOCKS_B008_B009 | SEC-B | CRYPTO-JNI |
| CANDIDATE-005 | MEDIUM | JNI handle registry: check (`is_*_active`) and raw deref (`&*`, `&mut *`) not under one lock; `&mut` from `jlong` without exclusivity; freed-address reuse → wrong object; `CryptoNative` is `public object` | `lib.rs:156-166,206-209,359,411,450`; registries are `HashSet<usize>` protecting only membership; `CryptoInstrumentedTest:657,669` call `CryptoNative` directly | LATENT (guarded only by Kotlin lock, which C-004 undermines) | UAF/double-`&mut` UB, ratchet corruption under concurrency; bypass of "only via CryptoBridge" comment | BLOCKS_B008_B009 | SEC-B | CRYPTO-JNI |
| CANDIDATE-006 | MEDIUM | `DpopProofVerifier.verify` defaults `expectedJwkThumbprint/accessToken/expectedNonce = null`; replay cache per-instance in-memory keyed by `jti` only | `DpopProofVerifier.kt:42-49,150`; `InMemoryDpopReplayCache` unbounded within window, wall-clock based | TEST_ONLY / FUTURE_INTEGRATION_SURFACE | Minimal call accepts any self-signed proof for the method/URI with no key/token/nonce binding; caller discipline required for B-004 | BLOCKS_B004 | SEC-A | AUTH-DPOP |
| CANDIDATE-007 | MEDIUM | `DpopHtu.normalize` uses decoded `URI.getPath()` and lowercases full authority | `/tmp` JVM proof: `/v1/a%2Fb`≡`/v1/a/b`; `/v1/x%2F..%2Fadmin`≡`/v1/x/../admin`; `%61ccount`≡`account`; `Alice@`→`alice@`; `:443` not equalized; `//v1` not collapsed | TEST_ONLY / FUTURE | `htu` attests a weaker URI than the request; encoded-slash/traversal collisions if server routing differs | BLOCKS_B004 | SEC-A | AUTH-DPOP |
| CANDIDATE-008 | MEDIUM | Read/decrypt paths manufacture keys; Keystore-failure misclassification | `RegistrationSessionKey.decrypt→getOrCreateKey` (`:58,63`); `CryptoBridge.initialize→initializeMasterKey` creates master key even when `anox_state_key.enc` exists; `serializeIdentity/serializeSession` (writes for *existing* identity) call `getOrCreateStateKey` → split-brain K_STATE if wrapped key file missing; `isKeystoreOrUnwrapFailure`: `AEADBadTagException` (corrupt wrapped key) → `MissingKeystore`, null master key → NPE → `CorruptedIdentityState`; `getLocalStateStatus:622` unwraps key twice, result unused | LATENT | Violates §24 read-vs-create; wrong recovery decision by future UI | BLOCKS_B008_B009 | SEC-B | ANDROID-STORAGE |
| CANDIDATE-009 | MEDIUM | No rollback/freshness or domain separation in protected-state envelopes | `serialization.rs:68`: AAD constant `"ANOX"+0x01`; identity & session share K_STATE and AAD; `RegistrationSessionKey` version byte outside AAD; no counter/generation | LATENT_UNTIL_B008_B009 | Old valid `anox_session.enc` can be swapped back → ratchet/message-key reuse; cross-type confusion prevented only by serde shape | BLOCKS_B008_B009 | SEC-B | CRYPTO-JNI |
| CANDIDATE-010 | LOW | Zeroization is nominal | `identity.rs:161-172`, `session.rs:101-112` empty `Drop`/`Zeroize`; `serialization.rs:36,50` plaintext pickle `Vec` not zeroized; `lib.rs:96-101` `Vec<i8>`/`Vec<u8>` key copies not zeroized; Kotlin `key`/`stateKey` `ByteArray` never filled; grant is `String` | LATENT | Secret residue in heap; comments claim protection stronger than delivered | NON_BLOCKING | SEC-A | CRYPTO-JNI |
| CANDIDATE-011 | LOW | `wipeLocalCrypto` ignores `delete()` results, misses `*.tmp`, does not destroy live handles, always succeeds; Keystore alias deleted first | `CryptoBridge.kt:737-754` | PUBLIC_BUT_UNWIRED | Misleading success; residual `.enc.tmp` may hold latest ciphertext | BLOCKS_FINAL_PRODUCT_GATE | SEC-A | ANDROID-STORAGE |
| CANDIDATE-012 | LOW | Error-semantic collapse across JNI | deserialize returns `0` for all failures (UnsupportedVersion lost); `-3` JNI failure ≡ `InvalidSession`; `-10` array-length failure ≡ `KeyError`→`KeyGenerationFailed`; `-12` unmapped; stale handle → `InvalidInput` | LATENT | Wrong recovery branch | NON_BLOCKING | SEC-A | CRYPTO-JNI |
| CANDIDATE-013 | LOW | Fail-open edges in local guards | `FileRegistrationSessionStore.load:44` empty file → `NotStarted` (not security exception); binding marker unauthenticated, **missing** file = unbound while corrupt = bound; `clearBinding()`/`deleteKeyDestructively()` public & unguarded; codec ignores trailing bytes | LATENT | Local-file attacker downgrades pre-armed registration; design accepted for marker but inconsistent with "corrupt = bound" | NON_BLOCKING | SEC-A | ANDROID-STORAGE |
| CANDIDATE-014 | LOW | Concurrency gaps in registration/deviceauth | `RegistrationOrchestrator` unsynchronized; `createKeyIfAbsent` check-then-act may regenerate alias; `@Synchronized` per-instance stores; test "I concurrent or double commit" is sequential | LATENT | State-machine double-save/alias overwrite under concurrent callers | NON_BLOCKING | SEC-A | ATTACKCHAIN |
| CANDIDATE-015 | LOW | Supply-chain gaps vs B-017 | No `gradle/verification-metadata.xml` or lockfile; foojay JDK auto-download; `dtolnay/rust-toolchain` floating `stable`; no lint or instrumented tests in CI; APK validator scans text suffixes only (would not catch secrets in `.so`/`.dex`) | RELEASE_ONLY | Non-reproducible builds; B-017 "lockfiles/verification required" unmet | BLOCKS_RELEASE_CANDIDATE | SEC-A | BUILD-SUPPLYCHAIN |
| CANDIDATE-016 | INFO | Misc. | `commit()` saves `Committed` then `clear()`s it → account/device ids not durably retained by foundation; commit `Rejected` after `markArmed` permanently blocks re-registration on the install; `resolveIdentityHandle` leaks native handles; debug APK adds exported `PreviewActivity`/`ComponentActivity`/`ProfileInstallReceiver`; `Log.e(..., e)` may include file paths; `getOneTimeKey` documented "test/debug" but used in production path; `UUID.fromString` lenient | mixed | — | NON_BLOCKING | SEC-A | ANDROID-STORAGE |
| CANDIDATE-017 | INFO | Historical validators fail by lifecycle | `validate_mainarch_fix03` (provider-field trigger), `validate_workforce_retest_closure_ingest`, `retest02/03`, `workforce_fix01/02`, `legacy_retest01`, `continuity_sync_fix01` exit 1 expecting superseded gates | governance | HISTORICAL_VALIDATOR_LIFECYCLE_MISMATCH, not code insecurity | NON_BLOCKING | — | — |

---

## EXISTING CANONICAL FINDINGS COMPARISON

| CODESEC2 candidate | Relation | Canonical ID | Same root cause? | New evidence |
|---|---|---|---|---|
| 001 | NEW_ROOT_CAUSE | — | No | Stale binaries proven by disassembly + rebuild |
| 002 | NEW_ROOT_CAUSE | — | No | Measured sizes vs 4096 |
| 003 | NEW_ROOT_CAUSE | — | No | HashMap nondeterminism reproduction |
| 004 | EXPANDS_CANONICAL_FINDING | ANOX-SECURITY-ARCH-001 | Partially (concurrency) | Broken singleton = lock identity mismatch |
| 005 | CONFIRMS_CANONICAL_FINDING | ANOX-SECURITY-ARCH-001 | Yes | Exact TOCTOU sites, public `CryptoNative` bypass |
| 006 | PARTIAL_OVERLAP | ANOX-SECURITY-ARCH-003 | Partly (B-004 fail-closed points) | Default-parameter behavior |
| 007 | NEW_ROOT_CAUSE | — | No | HTU collision table |
| 008 | EXPANDS_CANONICAL_FINDING | ANOX-SECURITY-ARCH-007 | Yes (K_STATE) | Adds `RegistrationSessionKey.decrypt`, `initializeMasterKey`, misclassification |
| 009 | NEW_ROOT_CAUSE | — | No | Rollback/AAD analysis |
| 010 | NEW_ROOT_CAUSE | — | No | Empty Zeroize impls |
| 011 | PARTIAL_OVERLAP | ANOX-SECURITY-ARCH-009 / ANOX-MAINARCH-030 | Partly | `.tmp`, ignored results, live handles |
| 012 | CONFIRMS_CANONICAL_FINDING | ANOX-SECURITY-ARCH-008 | Yes | JNI code collisions `-3/-10/-12`, deserialize→0 |
| 013 | PARTIAL_OVERLAP | ANOX-SECURITY-ARCH-003 | Partly | Empty-file downgrade |
| 014 | PARTIAL_OVERLAP | ANOX-SECURITY-ARCH-001/003 | Partly | Sequential "concurrent" test |
| 015 | NEW_ROOT_CAUSE | — | No | Missing Gradle verification, floating toolchain |
| 016 (handle leak) | CONFIRMS_CANONICAL_FINDING | ANOX-LEGACY-INTEGRATION-005 | Yes | — |
| 017 | NEW (governance INFO) | — | — | — |

## NEW ROOT CAUSES NOT IN CANONICAL FINDINGS
C-001 (stale native artifacts / no provenance), C-002 (4096-byte buffers), C-003 (nondeterministic OTK enumeration, no key ids, no publish path), C-004 (broken singleton), C-007 (HTU decoded-path collisions), C-009 (rollback/domain separation), C-010 (nominal zeroization), C-015 (Gradle verification/toolchain pinning).

## CANONICAL FINDINGS NOT INDEPENDENTLY REPRODUCED
ARCH-002 (B-021 matrix enforcement — governance, outside code scope of this audit), ARCH-004 (doc contradiction — not code), ARCH-005 (attachments — consistent: no attachment code exists, but not "reproduced" as a defect), ARCH-006 (server-side eligibility — consistent: only client-side `isProductionEligible` exists), ARCH-010 (positive INFO). Not treated as false positives.

---

## FALSE ASSURANCE RISKS
1. `CryptoErrorMappingTest` + Rust `test_buffer_too_small_error_code` prove a mapping table, not that the *shipped* binary emits `-11` (it emits `-2`).
2. `RegistrationOrchestratorTest`/`RegistrationCrashConsistencyTest` use `FakeLocalE2eeIdentityStep`; `CryptoBridgeLocalE2eeIdentityStep` has zero tests — C-002/C-003 are invisible to the suite.
3. Instrumented tests use 1–5 OTKs; default flow uses 20 (fails).
4. `stateKeyDeterministicWrap` obtains two bridges and compares keys, masking that they are different instances/locks.
5. Test "I concurrent or double commit invocation" is sequential.
6. `Zeroize`/`Drop` impls on `Identity`/`Session` are empty with "handles its own zeroization" comments.
7. `CryptoBridge` header comment "ONLY way Android code should interact with cryptography" — `CryptoNative` is public and used directly by tests.
8. `test_error_messages_no_secrets` checks for the word "key" in a too-short-buffer error only.
9. LOCAL_KEY_STATE_LIFECYCLE §O "single ReentrantLock serializes" — not true (C-004).
10. CI `android-debug` sets up NDK r26c but never builds Rust for Android; the packaged `.so` is whatever is committed.

## REACHABILITY SUMMARY
`MainActivity` is a greeting screen; nothing else is wired. `CryptoBridge`, `RegistrationOrchestrator`, DeviceAuth, DPoP: PUBLIC_BUT_UNWIRED / FUTURE_INTEGRATION_SURFACE. `DpopProofVerifier`, `InMemoryDpopReplayCache`, `DeviceAuthAccessTokenGenerator`, `InMemory*` stores: TEST_ONLY. Stale `.so`: CURRENTLY_REACHABLE artifact defect (packaged, not executed by any user flow). No DEAD_CODE beyond `mark_keys_as_published`/`unpublished_one_time_keys`/`session_id`/`has_received_message` (Rust-only, no JNI).

## CURRENTLY REACHABLE DEFECTS
C-001 (artifact provenance). No remotely reachable runtime defect at this SHA.

## LATENT PRE-B004 DEFECTS
C-002, C-003, C-004, C-005, C-008, C-013, C-014.

## LATENT B008/B009 DEFECTS
C-002 (sessions), C-004, C-005, C-009, C-011, C-012.

## RELEASE-ONLY DEFECTS
C-015; debug-only exported components (C-016) disappear in release; release has `isMinifyEnabled=false`, unsigned.

---

## KOTLIN CONCURRENCY
`CryptoBridge`: DCL pattern with `@Volatile instance` but **no assignment** → N instances, N locks (C-004). `cryptoLock` covers all bridge ops of one instance only. `FileRegistrationSessionStore`/`FileDeviceAuthBindingStore`: `@Synchronized` per instance; two instances on the same file are not mutually excluded. `RegistrationOrchestrator`: no synchronization; steps are check-then-act on `currentState()`. `AndroidKeystoreDeviceAuthKeyManager.createKeyIfAbsent`: check-then-act; `generateKeyPair` on existing alias overwrites. `InMemoryDpopReplayCache`: `@Synchronized` correct per instance. `AtomicFileWriter`/`writeFileAtomic`: fixed `.tmp` name — safe only under a shared lock.

## RUST/JNI SOUNDNESS
17 exported `Java_com_anox_crypto_CryptoNative_*` symbols; all other symbols hidden. `unsafe` sites: `lib.rs:144,166,191,209,225,247,272,327,359,388,411,450,482,502` — every deref is a raw `jlong→*const/*mut` cast after a membership check under a `Mutex<HashSet<usize>>` that is released before the deref; no exclusivity for `&mut` (generate OTKs, inbound session, encrypt, decrypt); no generation counter → freed address reuse revalidates a stale handle as a *different* live object of the same type; cross-type confusion prevented by separate sets. Destroy: `Box::from_raw` after atomic remove → double-free prevented; race-to-destroy vs in-flight use **not** prevented. Input validation: 32-byte key/peer-key checks present; `count < 0` and `index < 0` rejected; message type restricted to `{0,1}`; output-capacity checks present. `read_byte_array` allocates caller-sized `Vec`. JNI module compiles for `aarch64-linux-android` (verified) but is **not** compiled or tested by host `cargo test`. Pointer width: `usize`↔`jlong` fine on 64-bit ABIs only (arm64/x86_64 shipped).

## NATIVE ARTIFACT PROVENANCE
**Not tied to source — provably divergent.** Committed `.so` (both ABIs) built 2026-08-19 from pre-`342d553` source (returns `-2` where HEAD returns `-11`). No tracked build script; CI never builds native; no reproducible-build or signature evidence; binaries embed developer home paths; APK repackages the committed hashes unchanged. NDK ident note: r26c.

## CRYPTO STATE
Mutable state (`Account`, `Session`) is mutated through `&mut` derived from JNI longs; overlap of encrypt/decrypt/OTK-generation/inbound-creation on the same handle is only prevented by `cryptoLock` of a single `CryptoBridge` instance — undermined by C-004 and bypassable via public `CryptoNative`. Ratchet implication: overlapping `&mut` = UB and potential chain corruption; failed `saveSession` (C-002) after a successful decrypt leaves advanced state unpersisted.

## ZEROIZATION
`CryptoSerializer.key` zeroized on drop (real). `Identity`/`Session` `Zeroize`/`Drop` are no-ops (delegated to vodozemac, which zeroizes its own secret types). Not zeroized: plaintext pickle JSON (`serialize`), decrypted JSON (`deserialize`), `key_bytes`/`buf` Vecs in JNI helpers, Kotlin `key`/`stateKey` ByteArrays, unused `stateKey` in `getLocalStateStatus`, grant `String`.

## SERIALIZATION
Envelope `[ANOX][0x01][12B nonce][GCM ct+tag]`, AES-256-GCM, random 96-bit nonce via `getrandom`, AAD = magic+version. Correct fail-closed on short/magic/version/tag. Weaknesses: no domain tag (identity vs session), no anti-rollback, output buffers 4096 fixed on Kotlin side (C-002), JNI deserialize collapses all errors to `0`, JSON (serde) as inner format → sizes grow ~245 B per OTK; vodozemac stores up to 5000 private OTKs → unbounded growth.

## LOCAL STATE DURABILITY
`writeFileAtomic`/`AtomicFileWriter`: write→flush→`fd.sync()`→`renameTo`; no directory fsync (rename durability not guaranteed across power loss; content is never torn). `AtomicFile` (AndroidX) used for registration session: fsync + rename, `.new` cleanup on read. Crash windows: state key created and wrapped file written before identity file — crash between leaves `WipedState` (correct). `wipeLocalCrypto`: Keystore alias deleted first; partial failures reported as success.

## REGISTRATION STATE MACHINE
Graph from code: `NotStarted/Expired/Failed →reserve→ Reserved →registerDeviceAuth→ DeviceAuthRegistered →uploadPublicIdentity→ PublicIdentityUploaded →commit→ CommitArmed(persist)→markArmed→remote→ Committed(save→clear→NotStarted on disk)`; `Expired` from Reserved/DeviceAuthRegistered/PublicIdentityUploaded when grant TTL passed and not armed/bound; `Failed` persisted only from NotStarted/Failed. Step skipping is rejected. `failStep` never overwrites in-progress/terminal states. Durable outcome of success is the binding marker only; `Committed` ids are cleared immediately (C-016). Rejected commit after arming → permanently armed installation (C-016). Unreadable store → synthetic `Failed` → new registration allowed if not armed/bound.

## DEVICE AUTH
P-256/`secp256r1`, `PURPOSE_SIGN|VERIFY`, SHA-256, `setUserAuthenticationRequired(false)`, StrongBox attempted on API 28+ with TEE fallback; eligibility from `KeyInfo.securityLevel` (API 31+) or `isInsideSecureHardware`; `UNKNOWN`/`SOFTWARE` fail closed. Private key never exported: `ECDSASigner(PrivateKey, Curve)`, public JWK via `toPublicJWK()`. Alias `anox.deviceauth.p256.v1` distinct from `anox_crypto_master_key` and `anox.b003.session.v1`. Terminal loss logic (`DeviceAuthKeyStateResolver`) is correct and pure. Gaps: `deleteKeyDestructively` public/unguarded; check-then-act creation (C-014); StrongBox failure path deletes alias then falls back (safe only because guarded by `Present` early return).

## DPoP
Verified: `typ=dpop+jwt`, `alg=ES256` only, embedded public `jwk` (private → reject), P-256 curve, signature via Nimbus `ECDSAVerifier`, RFC7638 thumbprint compared constant-time, `htm` uppercase equality, `htu` normalized equality, `iat` ±120 s, `jti` ≥22 chars, `ath` = base64url(SHA-256(token)) when token given, `nonce` when expected, replay recorded last. Optional (caller-controlled): key binding, `ath`, `nonce` — all skipped in the smallest call (C-006). HTU: decoded path collisions (C-007). Replay: per-instance in-memory, jti-keyed, wall-clock, unbounded within 5 min (documented as non-production). Token contract constants match B-002 (256-bit, 15 min, no refresh).

## ANDROID
Manifest: `allowBackup=false`, `dataExtractionRules` excluding all domains for cloud+D2D, single exported launcher `MainActivity`, no permissions, no services/receivers/providers/deep links declared, cleartext not enabled (targetSdk 34 default). Debug APK merges exported `PreviewActivity`, `ComponentActivity`, `ProfileInstallReceiver` (debug deps) and is `debuggable` — release differs. Sensitive files under `filesDir` (crypto) and `noBackupFilesDir` (registration/binding). Backup posture: sound for API 26–34 statically; no device evidence.

## LOGGING
All 28 `Log.*` calls are in `CryptoBridge.kt`, static messages plus exception objects; no key/token/grant/ciphertext logging found; exception text may include absolute file paths (`Atomic rename failed for …`). `RegistrationGrant`/`LicenseCode` redact `toString`; `Failed.reason` strings embed `$current` state (grant redacted) and usernames.

## BUILD/CI
CI: pinned action SHAs, `permissions: contents: read`, B-017-Lite validator, wrapper validation, host `cargo test --locked`, JVM unit tests, `assembleDebug`/`assembleRelease`, APK content validator. Missing: native build from source, lint, instrumented tests, Gradle dependency verification/locking, SBOM, toolchain pinning (Rust `stable`, foojay JDK). Release: minify off, unsigned, no signing config (expected pre-B-018).

---

## RUST TESTS
`cargo test --locked --offline` with `CARGO_TARGET_DIR=/tmp/anox_audit2/target`: **17 passed, 0 failed, 0 ignored** (host; JNI module excluded by `cfg`). Android cross-compile of HEAD via `cargo ndk -t arm64-v8a build --release`: **success** (sha256 `05f3f40c…d7a2`, ≠ committed).

## JVM TESTS
`./gradlew --offline :android:testDebugUnitTest --rerun-tasks`: **177 tests, 0 failures, 0 errors, 0 skipped**.

## LINT
`:android:lintDebug`: **0 errors, 8 warnings** — OldTargetApi, GradleDependency (compileSdk 36 available), DataExtractionRules (no `fullBackupContent` for API<31 — mitigated by `allowBackup=false`), ObsoleteSdkInt, StaticFieldLeak (`CryptoBridge.instance`), UnusedResources, MonochromeLauncherIcon ×2. None security-critical.

## DEBUG BUILD
`:android:assembleDebug` success. `android-debug.apk` sha256 `f202c5e1…379d`; `native-code: arm64-v8a, x86_64`; packaged `.so` hashes identical to committed (stale) binaries; `validate_apk_contents.py` PASS; 9 dex files; `debuggable=true`, `allowBackup=false`.

## PHYSICAL TESTS
NOT_RUN — PHYSICAL DEVICE / EMULATOR REQUIRED (39 crypto + 27 app instrumented tests not executed).

---

## ATTACK CHAINS
1. **Artifact/evidence chain (CURRENTLY_REACHABLE):** source review + host tests pass → CI packages stale `.so` → shipped behavior differs from audited source (C-001, C-015). Consequence: any conclusion about native behavior drawn from source is unverified for the artifact.
2. **Registration foundation failure (LATENT_UNTIL_B004):** wire `RegistrationOrchestrator` with defaults → `generateOneTimeKeys(20)` → `saveIdentity` `-11`/`-2` → step 3 fails forever (C-002); if buffer were raised, index enumeration uploads duplicate/missing OTKs without ids (C-003) → server-side OTK claims unusable or ambiguous.
3. **Native memory-safety chain (LATENT_UNTIL_B008_B009):** second component calls `CryptoBridge.getInstance` → distinct lock (C-004) → concurrent encrypt/save/destroy on same handle → check/use race or aliased `&mut` (C-005) → UB/ratchet corruption; reachable earlier via public `CryptoNative`.
4. **State rollback chain (LATENT_UNTIL_B008_B009):** local attacker/backup-restore-like copy of old `anox_session.enc` → accepted (C-009) → message-key reuse; K_STATE regeneration by write path after wrapped-key loss (C-008) → mixed-key state.
5. **DPoP integration chain (LATENT_UNTIL_B004):** backend uses minimal `verify()` (C-006) → any key holder passes; encoded-slash route mismatch (C-007).

## BLOCKS PRE-B004 HARDENING
C-001.
## BLOCKS B004
C-002, C-003, C-006, C-007.
## BLOCKS B008/B009
C-002, C-004, C-005, C-008, C-009.
## BLOCKS FINAL PRODUCT GATE
C-011.
## BLOCKS RELEASE CANDIDATE
C-001, C-015.
## BLOCKS PRODUCTION RELEASE
None beyond the above (all upstream).
## NON-BLOCKING
C-010, C-012, C-013, C-014, C-016, C-017.

---

## SEC-A FOLLOW-UP
C-006, C-007, C-010, C-011, C-012, C-013, C-014, C-015, C-016.
## SEC-B FOLLOW-UP
C-001, C-002, C-003, C-004, C-005, C-008, C-009.
## SEC-C REQUIRED
NO
## ARCHITECTURAL REDESIGN REQUIRED
NO. No finding contradicts the frozen trust model (Keystore-bound K_STATE, non-exportable Device Auth key, DPoP, no-recovery). Component-internal redesign **is** needed: (a) JNI ownership model (generation-tagged handles or per-object locking, non-public `CryptoNative`), (b) key-id-bearing OTK export and publish/ACK path, (c) dynamic/size-negotiated serialization buffers, (d) envelope domain separation + anti-rollback, (e) reproducible native build in CI.

---

## SPECIALIST ROUTING
### BUILD / NATIVE PROVENANCE
C-001, C-015 → `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`
### CRYPTO / JNI
C-002, C-003, C-004, C-005, C-009, C-010, C-012 → `AUDIT-SECURITY-CRYPTO-JNI-001`
### AUTH / DPoP
C-006, C-007 → `AUDIT-SECURITY-AUTH-DPOP-001`
### ANDROID / STORAGE
C-008, C-011, C-013, C-016 → `AUDIT-SECURITY-ANDROID-STORAGE-001`
### ATTACK CHAIN
Chains 1–5, C-014 → `AUDIT-SECURITY-ATTACKCHAIN-001`

---

## SECURITY VERDICT
1. **Safe to extend before remediation?** No. C-001 breaks the source↔artifact link; C-002/C-003 mean the E2EE-registration step cannot work as written; C-004/C-005 make the native layer unsafe under any second caller.
2. **Strongest foundation blockers:** stale/unprovenanced native binaries (C-001); 4096-byte serialization ceiling (C-002); nondeterministic, id-less OTK export with no publish path (C-003); non-functional singleton lock (C-004).
3. **Genuinely effective:** AES-256-GCM envelope integrity/fail-closed parsing; Keystore-wrapped K_STATE with read-vs-create split in load paths; Device Auth key lifecycle resolver (terminal-loss never regenerates); P-256/ES256 non-exportable signer; DPoP claim validation when all bindings are supplied; registration step ordering and `failStep`/armed-guard logic; `allowBackup=false` + full `dataExtractionRules`; no-recovery (no export/seed/restore API; identity undecryptable without device Keystore); pinned CI actions; grant/license `toString` redaction.
4. **Only appear effective:** "single lock" serialization; JNI handle validity (check≠use); `Zeroize` impls; "CryptoBridge is the only way"; error-code contract tests; concurrency test naming; APK secret scan (text suffixes only).
5. **Entirely unwired/spec-only:** B-004 network, token issuance, server replay cache, OTK publish/ACK/`mark_keys_as_published`, fallback keys, B-008/B-009 messaging & SQLCipher, attachments, push, SAS, server-side eligibility/PoP checks, release signing.
6. **Remotely exploitable at this SHA?** No. No network code exists; runtime attack surface is one launcher Activity.
7. **Architectural redesign?** No — component-internal redesign as listed above.
8. **SEC-C required?** No.

---

## PRODUCT DEVELOPMENT
BLOCKED_PENDING_FINAL_AUDIT
## B004
NOT_STARTED
## B005
NOT_STARTED
## SECURITY HARDENING PHASE
IN_PROGRESS
## FINAL OPERATIONAL ACCEPTANCE
PENDING / NOT_EXECUTED
## HUMAN FINAL PRODUCT GATE
NOT_EXECUTED
## REPOSITORY MODIFIED
NO (all builds/proofs in gitignored dirs or `/tmp/anox_audit2`)
## BASELINE RECONFIRMED
PASS

---

## NEXT ACTION
`PRESERVE BLIND CODEBASE AUDIT 002 → RETURN REPORT TO HUMAN → NO FINDINGS FREEZE YET → NO REMEDIATION YET → PERFORM INDEPENDENT AUDIT-001 ↔ AUDIT-002 CONSENSUS ANALYSIS`

STOP.