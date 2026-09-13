# AUDIT-SECURITY-ANDROID-STORAGE-001 — FINAL REPORT

## AUDIT RESULT
**`PASS_WITH_FINDINGS`** (PASS does NOT unblock product development.)

## AUDIT
`AUDIT-SECURITY-ANDROID-STORAGE-001`

## PROVIDER
Devin CLI (Cognition) session runtime

## MODEL
Claude Fable 5.1 High (runtime label as reported by the session system prompt: "You are powered by Claude Fable 5.1 High"). No routing/fallback observed. Fresh specialist session.

## MODEL REQUIREMENT SATISFIED
YES

## MODE
`READ_ONLY_ANDROID_STORAGE_SECURITY_SPECIALIST_AUDIT`

## AUDITED SHA
`b9abeb0850a476716403d224b87a857c1147502e`

## HEAD AT END
`b9abeb0850a476716403d224b87a857c1147502e`

## ORIGIN MAIN
`b9abeb0850a476716403d224b87a857c1147502e`

## WORKING TREE
CLEAN (`git status --short` empty; `git diff --check` clean; branch `main`; 0 stashes)

## REPOSITORY MODIFIED
NO (Gradle touched only gitignored `android/build/`; harness artifacts only under `/tmp/anox_android_storage_audit/`)

## REMOTE MUTATION
NONE (only `git fetch origin`)

---

## PRESERVED EVIDENCE VALIDATION
**PASS** — `python3 tools/audit/validate_security_audit_evidence_preservation.py` → `SECURITY AUDIT EVIDENCE PRESERVATION: PASS`, exit 0. Read: `AUDIT_EVIDENCE_INDEX.md`, `audit_registry.jsonl`, `audit_traceability.jsonl`, `evidence_hashes.json`, and all seven preserved reports (ARCHITECTURE, CODEBASE-001, CODEBASE-002, CONSENSUS-001, BUILD-SUPPLYCHAIN-001, CRYPTO-JNI-001, AUTH-DPOP-001). None modified.

---

## AUTHORITY SOURCES

| Doc | Precedence | Relevant content used |
|---|---|---|
| `B025/SECURITY_INVARIANTS_V1_1.md` | 1 | Inv.1 (no recovery), 2 (one active device), 3 (loss = unrecoverable identity), 7 (Device Auth independent), 8 (Keystore P-256), 23 (**no silent identity regeneration on missing/corrupt state**), 24 (key distinctness), 25 (**private state excluded from Android/cloud backup; no recovery via restore**), 26 (no secrets in logs), 33 (tests ≠ proof), 35 (no impl without frozen spec) |
| `B025_MANDATORY_AMENDMENTS_V1_1.md` | 8 | B-003 v1.5 §3: `CommitArmed` is a client-side precondition ("local registration store, Device Auth key, and E2EE identity are prepared and **durable**"); B-013 v1.3 (expiry keeps Device Auth key) |
| `B025_MANDATORY_AMENDMENTS_V1_2.md` | 9 | `device_auth_keys` schema (no explicit UNIQUE on public key → Auth GAP-003), one-active-device partial unique index, commit race "one wins" |
| `ULTIMATE_MAIN_ARCHITECTURE_B025.md` | 7 | Local wipe offline/best-effort; uninstall/factory reset strands old account; reinstall = first run; "current file-based protected crypto state is legacy foundation and must be migrated deliberately" |
| `B002_DEVICE_AUTHENTICATION.md` v1.1 | 11 | logout keeps key; key invalidation terminal; no silent replacement |
| `B003_ACCOUNT_LICENSE.md` v1.4 | 11 | grant 256-bit/30 m; commit idempotent; crash-resume is transaction resume |
| `B009_LOCAL_DATABASE.md` v1.4 | 11 | K_STATE envelope retained; backup excluded; missing keys fail closed; wipe best-effort, no NAND erasure claim |
| `B013_LIFECYCLE.md` v1.2 | 11 | **Local wipe scope**: Device Auth key, K_DB/K_STATE wrapping material, DB/WAL/SHM, crypto state, temp, tokens; missing/corrupt K_STATE "fails closed and offers **explicit local reset/new-account path only**"; uninstall/app-data loss = first run |
| `B021_SECURITY_TEST_MATRIX.md` | 11 | mandatory classes: local envelope/Keystore corruption, crash/process-kill, backup/restore, physical GrapheneOS; emulators do not replace physical |
| `docs/current/LOCAL_KEY_STATE_LIFECYCLE_V1_FROZEN.md` | current (pre-B025 text, reconciled under B-006) | §C/§G/§J read-vs-create; §D/§K atomic write = temp+fsync+rename (no dir fsync claimed); §F "Invalidated by app data clear, uninstall"; §L fail-closed list; §M wipe; §N backup; §P best-effort FS limitation |
| `docs/current/LOCAL_DEVICE_SECURITY.md` | current | no plaintext secrets in prefs/JSON/external; wipe = cryptographic destruction + best-effort file removal; no flash-erasure claim |

**Authority observation:** the Device Auth **binding marker** and the **registration session store / `RegistrationSessionKey`** appear in **no** authority document; they exist only in the PROMPT-008 implementation report (evidence, not authority). See `ANOX-ANDROIDSTORAGE-GAP-001`.

## STORAGE SOURCE INVENTORY

Complete discovery: 49 production Kotlin files (45 `android/src/main` + 4 `crypto/android/src/main`), `AndroidManifest.xml`, `res/xml/data_extraction_rules.xml`, `android/build.gradle.kts`, `proguard-rules.pro`, `res/values/*`. Grep over `File(`, `AtomicFile`, `SharedPreferences`, `DataStore`, `SQLite`, `Room`, `filesDir`, `noBackupFilesDir`, `cacheDir`, `codeCacheDir`, `getExternal`, `AndroidKeyStore`, `KeyGenerator`, `KeyPairGenerator`, `delete(`, `renameTo`, `sync()`, `FileOutputStream`, `FileInputStream`, `RandomAccessFile`, `deleteEntry` → **6 files** touch persistent/Keystore state:

| # | File | Persistent/security state touched |
|---|---|---|
| 1 | `crypto/android/.../CryptoBridge.kt` | `anox_state_key.enc`, `anox_identity.enc`, `anox_session.enc` (filesDir); Keystore alias `anox_crypto_master_key`; `writeFileAtomic`; `wipeLocalCrypto` |
| 2 | `android/.../storage/AtomicFileWriter.kt` | temp+fsync+rename primitive (used by binding marker only; KDoc claims registration state too — stale) |
| 3 | `android/.../security/keystore/RegistrationSessionKey.kt` | Keystore alias `anox.b003.session.v1` (AES-256-GCM) |
| 4 | `android/.../security/deviceauth/FileDeviceAuthBindingStore.kt` | `anox_deviceauth_binding.state` (noBackupFilesDir) |
| 5 | `android/.../security/deviceauth/AndroidKeystoreDeviceAuthKeyManager.kt` | Keystore alias `anox.deviceauth.p256.v1` |
| 6 | `android/.../account/FileRegistrationSessionStore.kt` | `anox_registration_session.enc` (+ AndroidX `AtomicFile` `.new`/`.bak`; legacy `.state`, `.state.tmp`) (noBackupFilesDir) |

Consumers/contracts reviewed in full (24): `RegistrationOrchestrator`, `RegistrationState`, `RegistrationSessionStore`, `BinaryRegistrationStateCodec`, `RegistrationGrant`, `RegistrationSessionSecurityException`, `UuidV4`, `AccountId`, `DeviceId`, `RegistrationId`, `Username`, `DeviceAuthBindingStore`, `DeviceAuthKeyManager`, `DeviceAuthKeyStateResolver`, `DeviceAuthKeyStatus`, `HardwareSecurityLevel`, `CryptoBridgeLocalE2eeIdentityStep`, `LocalE2eeIdentityStep`, `PublicE2eeIdentityMaterial`, `RegistrationApi`, `CryptoError`, `CryptoResult`, `CryptoNative` (state bytes crossing JNI), `MainActivity` (reachability). The remaining 19 production files (DPoP/JOSE, license/entitlement value types, UI theme) were content-checked for `File|Preferences|persist|store|write|read|Log.` → zero persistence. No SharedPreferences, DataStore, SQLite/Room, cache, external storage, FileProvider, `sharedUserId`, or `android:process` anywhere. AndroidX `core:1.12.0` `AtomicFile` source extracted and reviewed (`/tmp/anox_android_storage_audit/atomicfile`).

## STORAGE TEST INVENTORY

| Suite | Kind | Tests | Storage relevance | CI |
|---|---|---|---|---|
| `FileRegistrationSessionStoreTest` | instrumented | 10 | real Keystore + noBackupFilesDir; corrupt/tamper/legacy | **NOT CI** |
| `FileDeviceAuthBindingStoreTest` | instrumented | 7 | marker persist/corrupt/truncate | **NOT CI** |
| `AndroidKeystoreDeviceAuthKeyManagerTest` | instrumented | 10 | terminal loss, unbound loss, alias | **NOT CI** |
| `CryptoInstrumentedTest` | instrumented | 39 | corrupt/empty/truncated/modified identity file, corrupted wrapped key, missing state key, wipe→FirstRun | **NOT CI** |
| `RegistrationCrashConsistencyTest` | JVM (fakes) | 12 | crash points A–J | executed |
| `RegistrationOrchestratorTest` | JVM (fakes) | 28 | state machine | executed |
| `RegistrationStateCodecTest` | JVM | 12 | round-trips, garbage, truncation, version | executed |
| `RegistrationGrantTest` / `IdentifierTest` / `DeviceAuthKeyLifecycleTest` / `CryptoErrorMappingTest` | JVM | 7/7/17/4 | grant redaction, UUID parse, resolver, error map | executed |
| Support: `AccountTestSupport.kt`, `DeviceAuthTestSupport.kt`, `RegistrationGrantGenerator.kt` | fixtures | — | fault injection (in-memory only) | — |

```
STORAGE-RELEVANT TESTS  = 153   (JVM 87 + instrumented 66)
JVM                     = 87    (CI-executed; all fakes — no real file, fsync, Keystore or crypto)
INSTRUMENTED            = 66    (never CI-executed; last known run: PROMPT-008 emulator, pre-encrypted-store)
PHYSICAL                = 0
CI-EXECUTED             = 87
```
Missing test classes (none exist anywhere): zero-length session file; session-key alias deletion then read; marker flags-byte corruption; `.new`/`.tmp` residue; `AtomicFile` rename failure; `wipeLocalCrypto` partial-failure result; rollback (old valid envelope re-accepted); commit-`Rejected`-after-arm permanent state; concurrent store instances; power-loss/dir-fsync (not JVM-testable).

## PRODUCTION FILE COVERAGE
```
ANDROID/STORAGE PRODUCTION FILES DISCOVERED = 49 (+ manifest, extraction rules, gradle, proguard)
ANDROID/STORAGE PRODUCTION FILES REVIEWED   = 49 (30 storage-relevant read in full; 19 verified persistence-free by content search)
PRODUCTION FILE COVERAGE                    = 100%
```
## TEST FILE COVERAGE
```
ANDROID/STORAGE RELEVANT TEST FILES DISCOVERED = 14
ANDROID/STORAGE RELEVANT TEST FILES REVIEWED   = 14 (3 file-store/crash suites in full; others by test bodies for storage cases + names)
TEST FILE COVERAGE                             = 100%
```

---

## STORAGE-ASSET TABLE

| Asset | File / Alias | Contains | Conf. | Integ. | Avail. | Lifetime | Backup allowed? | Owner |
|---|---|---|---|---|---|---|---|---|
| Device Auth private key | Keystore `anox.deviceauth.p256.v1` | P-256 private (non-exportable) | HIGH | HIGH | terminal on loss once armed/bound | install; never rotated | N/A (Keystore) | `AndroidKeystoreDeviceAuthKeyManager` |
| RegistrationSessionKey | Keystore `anox.b003.session.v1` | AES-256-GCM | HIGH | HIGH | needed only during 30 m transaction | **unbounded; never deleted** | N/A | `RegistrationSessionKey` |
| K_STATE master (wrapping) key | Keystore `anox_crypto_master_key` | AES-256-GCM | HIGH | HIGH | identity lifetime | recreated on every `getInstance()` if absent | N/A | `CryptoBridge` |
| K_STATE (wrapped) | `filesDir/anox_state_key.enc` (28+ B: IV‖ct‖tag, **no AAD**) | wrapped 32-B key | HIGH | HIGH (GCM) | identity lifetime | install | **NO** (manifest rules; not in noBackupFilesDir) | `CryptoBridge` |
| E2EE identity state | `filesDir/anox_identity.enc` (`ANOX`‖0x01‖nonce‖ct) | all private Olm keys + OTKs | HIGH | HIGH (GCM, AAD magic‖ver) | HIGH (no recovery) | install | **NO** | `CryptoBridge` |
| Olm session state | `filesDir/anox_session.enc` | ratchet | HIGH | HIGH | HIGH | B-008+ | **NO** | `CryptoBridge` |
| Registration session | `noBackupFilesDir/anox_registration_session.enc` (0x01‖IV‖ct‖tag, **no AAD**) | state tag, registration_id, **grant plaintext inside envelope**, expiry, username, JKT; or account_id/device_id (transient) | HIGH (grant) | HIGH (GCM) | resume only | ≤ commit (then `clear()`) | NO (noBackup + rules) | `FileRegistrationSessionStore` |
| Device Auth binding marker | `noBackupFilesDir/anox_deviceauth_binding.state` (6 B `ANXB`‖ver‖flags, **plaintext, unauthenticated**) | bound/armed flags | none | **required but absent** | **HIGH** (anchors terminal-loss invariant) | must outlive Keystore key | NO | `FileDeviceAuthBindingStore` |
| Grant | inside session envelope / memory (`String`) | 256-bit bearer | HIGH | — | — | 30 m | NO | codec/store |
| JKT | inside session envelope | public | none | MED | — | transaction | NO | codec |
| device_id / account_id | `Committed` state — **persisted then immediately cleared** | public UUIDs | none | — | not retained | transient | NO | orchestrator |
| Username | inside session envelope; `Failed.reason` text | identifier | LOW | — | — | transaction | NO | codec |
| Temp residue | `*.enc.tmp` (crypto, filesDir), `anox_registration_session.enc.new`/`.bak` (AtomicFile), `anox_deviceauth_binding.state.tmp` | **ciphertext only** (marker tmp = flags) | as parent | — | never authoritative (`.bak` exception below) | until next write | NO | writers |
| Legacy plaintext | `anox_registration_session.state`(.tmp) | PROMPT-008C plaintext grant | HIGH | — | — | deleted best-effort on load(absent)/clear only | NO | `FileRegistrationSessionStore` |
| Access token | none persisted (B-004 absent) | — | — | — | — | — | — | — |
| Cache / SharedPreferences / DB | **none exist** | — | — | — | — | — | — | — |

---

## ARCHITECTURE-TO-CODE COVERAGE MATRIX

| # | Requirement | Authority | Existing code | Test | Runtime/physical proof | Status | Finding |
|---|---|---|---|---|---|---|---|
| 1 | No silent identity regeneration on missing/corrupt state | Inv.23, LKSL §J | `getLocalStateStatus` 6-way; `createAndPersistFirstIdentity` refuses if file exists; `deserialize*` use `getExistingStateKey` | inst. `missingStateKeyPreventsDeserializeButDoesNotCreateOne`, `corruptedIdentityFileFailsToLoad` (not CI) | none | IMPLEMENTED_NOT_VERIFIED | — |
| 2 | Read paths must not create K_STATE/master key | Inv.23, LKSL §C, ARCH-007 | deserialize paths fixed; **`initializeMasterKey()` runs on every `getInstance()` and creates the alias whenever absent, including when `anox_state_key.enc` exists**; `serializeIdentity/Session` (write for existing identity) use `getOrCreateStateKey` | none | none | IMPLEMENTATION_DRIFT | ROOT-006 CONFIRMED |
| 3 | RegistrationSessionKey read must not create | Inv.23 (by analogy), Auth handoff | `decrypt()` → `getOrCreateKey()` → `generateKey()` (`RegistrationSessionKey.kt:58,63-69`) | none (inst. tests never delete alias) | none | IMPLEMENTATION_DRIFT | ROOT-006 CONFIRMED |
| 4 | K_STATE / Device Auth / session-key / E2EE distinct | Inv.24 | 3 distinct aliases; E2EE not in Keystore | inst. name-check only | physical | IMPLEMENTED_AND_VERIFIED (source) | — |
| 5 | Protected state AEAD, versioned, fail-closed parse | LKSL §E/§L, B-009 | Rust envelope (Crypto audit); Kotlin `unwrapStateKey` min-size check | inst. 6 corruption tests (not CI) | none | IMPLEMENTED_NOT_VERIFIED | — |
| 6 | Registration grant never plaintext on disk | B-003, PROMPT-008 | GCM-sealed; legacy plaintext files deleted best-effort | inst. `persistedGrantIsNotPlaintext` (not CI) | none | IMPLEMENTED_NOT_VERIFIED | — |
| 7 | Atomic (non-torn) writes | LKSL §D/§K | `writeFileAtomic`, `AtomicFileWriter` (fsync+rename, throw on rename fail); AndroidX `AtomicFile` (fsync+rename, **errors swallowed**) | none real | harness: `finishWrite` returns normally on rename failure | PARTIALLY_IMPLEMENTED | ROOT-007 EXPANDED / CANDIDATE-002 |
| 8 | Durable commit of armed state before remote call | B-003 v1.5 §3, orchestrator KDoc | file fsync yes; **no parent-directory fsync** in all 3 writers | none | none (physical/power-loss) | PARTIALLY_IMPLEMENTED | ROOT-007 CONFIRMED |
| 9 | Missing marker ≠ first run when other security state exists | Inv.23/B-002 (derived) | absent → `(false,false)`; no cross-check against Keystore aliases or session file | none | none | IMPLEMENTATION_DRIFT (fail-open on absence) | ROOT-007 CONFIRMED |
| 10 | Corrupt marker fails closed | PROMPT-008 §6 (design), Inv.23 | structural corruption → `(true,true)`; **flags-byte / v1-garbage / unknown-bit corruption → unbound** | inst. 3 tests (structural only) | harness state map | PARTIALLY_IMPLEMENTED | ROOT-007 EXPANDED |
| 11 | Zero-length / truncated session file fails closed | Inv.23 | `envelope.isEmpty() → NotStarted` (`:44`); truncated/garbage → security exception | inst. corrupt/tamper; **no empty test** | harness (`readFully` → len 0) | IMPLEMENTATION_DRIFT | ROOT-007 CONFIRMED |
| 12 | Storage error taxonomy distinguishes security states | Inv.23, B-013 | `NOT_FOUND`→NotStarted; `EMPTY`→NotStarted; read/auth/parse → one `RegistrationSessionSecurityException`; `KEY_MISSING` indistinguishable (key recreated); crypto: `MissingStateKey` distinct, `MissingKeystore` ≡ corrupt wrapped key, NPE→`CorruptedIdentityState` | JVM error-map 4 | — | PARTIALLY_IMPLEMENTED | ROOT-006/013 CONFIRMED |
| 13 | Rollback of protected state detected | Inv.23 (integrity/authenticity), ROOT-011 | no counter/epoch anywhere; marker unauthenticated; `.bak` auto-restore | none | harness `.bak` → readFully returns planted bytes | MISSING | ROOT-011 CONFIRMED+EXPANDED |
| 14 | Envelope version authenticated | LKSL §E (crypto: yes) | crypto: AAD magic‖ver ✓; registration: **no AAD; version byte unauthenticated**; wrapped-key: no AAD | — | — | PARTIALLY_IMPLEMENTED | ROOT-011 EXPANDED |
| 15 | Domain separation across object types | Inv.24 (derived) | distinct keys per domain ✓; identity vs session same key/AAD (Crypto audit); registration single type | — | — | PARTIALLY_IMPLEMENTED | ROOT-011 (adjacent) |
| 16 | Private state excluded from backup/D2D | Inv.25, B-009, LKSL §N | `allowBackup=false`; `dataExtractionRules` exclude all domains for cloud + device-transfer; registration/marker in `noBackupFilesDir`; crypto in `filesDir` | none | none | IMPLEMENTED_NOT_VERIFIED / PHYSICAL_VERIFICATION_REQUIRED | GAP-003 |
| 17 | Reinstall/app-data-clear = first run, old account stranded | ULTIMATE §Lifecycle, B-013, LKSL §F | code assumes Keystore aliases die with app data; no code path handles "key survives, marker gone" (→ same JKT reused) | inst. `unboundKeyLossIsTreatedAsFirstRun` | none | PHYSICAL_VERIFICATION_REQUIRED + SERVER_PREREQUISITE (JKT uniqueness) | GAP-003 (+Auth GAP-003) |
| 18 | Local wipe deletes Device Auth key, K_STATE wrapping material, crypto state, temp, tokens; offline; best-effort | B-013, ULTIMATE, LKSL §M | only `wipeLocalCrypto` (3 crypto files + master alias; ignores results; no temp; no marker/session/aliases); primitives `deleteKeyDestructively`, `clearBinding`, `clear()` scattered | inst. `firstRunStatusIsDetected` (wipe→FirstRun) | none | NOT_APPLICABLE_YET (B-013 orchestrator) + IMPLEMENTATION_DRIFT (wipe truthfulness) | ROOT-012 CONFIRMED+EXPANDED / GAP-002 |
| 19 | Wipe reports truthful result | B-009 "best-effort" (must be stated) | `wipeLocalCrypto` returns Success unconditionally after `deleteEntry` | none | — | IMPLEMENTATION_DRIFT | ROOT-012 |
| 20 | Logout preserves Device Auth key, E2EE, DB | B-002, B-013 | no logout flow | — | — | NOT_APPLICABLE_YET | GAP-002 |
| 21 | Account deletion forces local wipe after server erasure intent | B-013 | none | — | — | NOT_APPLICABLE_YET | GAP-002 |
| 22 | Missing/corrupt K_STATE fails closed and offers explicit local reset path | B-013 | fail-closed ✓ (`MissingStateKey`/`MissingKeystore`/`Corrupted…`); **no reset path** | inst. | — | PARTIALLY_IMPLEMENTED | GAP-001/002 |
| 23 | Armed installation has an authoritative release/reset path | B-013 (reset path), B-003 v1.5 §3 | `commit()` `Rejected` → `Failed` **overwrites `CommitArmed`** while marker stays armed; only exit = public `clearBinding()` | JVM `rejected commit does not bind` (asserts not-bound only) | — | IMPLEMENTATION_DRIFT + ARCHITECTURE_GAP | CANDIDATE-001 / GAP-001 |
| 24 | CommitArmed session must not be downgraded while armed | LEGACY-INTEGRATION-003, `RegistrationState` KDoc | `failStep` ✓, `expiredOrNull` ✓; **direct `save(Failed)` at `:224-226` bypasses** | JVM `failStep cannot overwrite armed session` | — | PARTIALLY_IMPLEMENTED | CANDIDATE-001 |
| 25 | Terminal key loss never regenerates key | B-002 | resolver + marker (`Present` early return; `requireCreationAllowed`) | JVM 17 + inst. 10 | marker durability physical | IMPLEMENTED_AND_VERIFIED (logic) / marker → ROOT-007 | — |
| 26 | Keystore alias collision handled fail-closed | Inv.23 (derived) | `RegistrationSessionKey`: non-`SecretKeyEntry` → `generateKey()` **overwrites**; Device Auth: wrong-type → `as? PrivateKey` null → absent → `generateKeyPair()` overwrites | none | none | IMPLEMENTATION_DRIFT | ROOT-006 EXPANDED (Auth CANDIDATE-002 adjacent) |
| 27 | Key creation serialized | derived | none; check-then-act in both key classes | none | none | MISSING | Auth CANDIDATE-002 / ROOT-006 |
| 28 | Store writes serialized globally | LKSL §O ("single ReentrantLock") | `@Synchronized` per instance; `CryptoBridge` lock per instance (ROOT-002); fixed `.tmp`/`.new` names | none | — | IMPLEMENTATION_DRIFT | ROOT-002 (Crypto), noted |
| 29 | Single process | B-009 "single process/locks" | no `android:process`; no `sharedUserId` | — | — | IMPLEMENTED_AND_VERIFIED (manifest) | — |
| 30 | App-private file permissions | LOCAL_DEVICE_SECURITY §2 | `File(dir, const)` only; no `MODE_WORLD_*`, chmod, external, FileProvider; mode bits inherited from sandbox umask | none | **mode bits require instrumented/physical check** | IMPLEMENTED_NOT_VERIFIED | — |
| 31 | No plaintext secrets in prefs/JSON/external | LOCAL_DEVICE_SECURITY §2 | none used | — | — | IMPLEMENTED_AND_VERIFIED | — |
| 32 | Temp files never authoritative | derived | `.tmp` never read ✓; `.new` deleted on read when base exists ✓; **`.bak` auto-renamed over base on read/write** | none | harness | PARTIALLY_IMPLEMENTED | CANDIDATE-002 |
| 33 | Temp residue cleanup | LOCAL_DEVICE_SECURITY "short-lived" | only legacy `.state.tmp`; no `.enc.tmp`/`.new` cleanup; wipe ignores them | inst. checks `.tmp` not `.new` | — | PARTIALLY_IMPLEMENTED | ROOT-012 EXPANDED |
| 34 | Bounded codec / file reads | derived (local DoS) | strings ≤16 KB ✓; negative/oversize length rejected ✓; whole-file reads unbounded | JVM codec 12 | harness | IMPLEMENTED (codec) / MISSING (file size) | not a finding (app-UID writer only) |
| 35 | Persisted UUIDs validated (syntax, version, variant) | B-003, UuidV4 KDoc | version only | JVM 7 | harness: NCS-variant `…-0123-…` accepted | IMPLEMENTATION_DRIFT | ROOT-015 CONFIRMED |
| 36 | Transient secret copies cleared (best-effort) | Inv.4/26 spirit, ROOT-010 | K_STATE `ByteArray` never cleared (`:337,366,526,553,622` incl. **unused copy at `:622`**); codec plaintext arrays; grant `String` | none | — | MISSING (best-effort) | ROOT-010 CONFIRMED |
| 37 | No secrets in logs/exception text | Inv.26 | `CryptoBridge` `Log.e` static + exception objects; `AtomicFile` logs absolute paths; grant redacted | JVM grant test | — | IMPLEMENTED_AND_VERIFIED | — |
| 38 | Storage filenames leak no identifiers | derived | constant names | — | — | IMPLEMENTED_AND_VERIFIED | — |
| 39 | Committed ids durably retained locally | GAP (Auth GAP-003) | `Committed` saved then `clear()` | JVM G | — | ARCHITECTURE_GAP (recorded by Auth audit) | — |
| 40 | Profile/user isolation policy | none | none assumed | — | physical | PHYSICAL_VERIFICATION_REQUIRED + ARCHITECTURE_GAP | GAP-003 |
| 41 | Instrumented storage tests executed in CI | B-021, ROOT-017 | `ci.yml` runs only `testDebugUnitTest` | 66 inst. never run in CI | — | MISSING | ROOT-017 CONFIRMED |
| 42 | Physical GrapheneOS storage/Keystore evidence | B-021, ULTIMATE | none | — | none | PHYSICAL_VERIFICATION_REQUIRED | ROOT-017 / MAINARCH-018 |

## ARCHITECTURE COVERAGE SUMMARY
```
TOTAL ANDROID/STORAGE REQUIREMENTS = 42
IMPLEMENTED_AND_VERIFIED           = 6    (4, 25, 29, 31, 37, 38)
IMPLEMENTED_NOT_VERIFIED           = 5    (1, 5, 6, 16*, 30)
PARTIALLY_IMPLEMENTED              = 10   (7, 10, 12, 14, 15, 22, 24, 32, 33, 34)
IMPLEMENTATION_DRIFT               = 10   (2, 3, 9, 11, 19, 23, 26, 28, 35, 36→MISSING counted below)
MISSING                            = 4    (13, 27, 36, 41)
NOT_APPLICABLE_YET                 = 3    (18, 20, 21)
PHYSICAL_VERIFICATION_REQUIRED     = 3    (17, 40, 42)  (*16 secondary physical)
SERVER_PREREQUISITE                = 0 primary (17 secondary)
ARCHITECTURE_GAP (primary)         = 1    (39)
UNMAPPED                           = 0
```
(6+5+10+10+4+3+3+1 = 42; rows with dual classification counted once under primary.)

## UNMAPPED
0.

---

## MANIFEST / BACKUP POLICY
`AndroidManifest.xml`: `android:allowBackup="false"`, `android:dataExtractionRules="@xml/data_extraction_rules"`, no `fullBackupContent`, no backup agent, one exported launcher activity, no permissions/services/receivers/providers, no `android:process`, no `sharedUserId`, no `usesCleartextTraffic`, `debuggable` only in debug variant (AGP default). `data_extraction_rules.xml`: `<cloud-backup>` and `<device-transfer>` each exclude `root, file, database, sharedpref, external, device_root, device_file, device_database, device_sharedpref` with `path="."`. Static verdict: API 26–30 → `allowBackup=false` disables full backup and adb backup for release; API 31+ → rules exclude both cloud and D2D (correct, since `allowBackup=false` alone does not govern D2D on API 31+). `noBackupFilesDir` additionally excludes registration/marker regardless. **Debug builds are `debuggable` → `run-as`/`adb backup` can extract app-private files (ciphertext) — debug-only, not a production exposure.** Whether GrapheneOS/Seedvault/OEM agents honor these rules: PHYSICAL_VERIFICATION_REQUIRED. No security asset is backup-eligible by configuration; the crypto state's reliance on manifest rules (rather than `noBackupFilesDir`) is a defense-in-depth observation, not drift (LKSL §D specifies `filesDir`).

## FILE LOCATION POLICY
`filesDir`: `anox_state_key.enc`, `anox_identity.enc`, `anox_session.enc` (+ `.tmp`). `noBackupFilesDir`: `anox_registration_session.enc` (+ `.new`/`.bak`), `anox_deviceauth_binding.state` (+ `.tmp`), legacy `.state`/`.state.tmp`. Keystore: 3 aliases. Nothing in cache, external, databases, SharedPreferences. All paths constructed as `File(dir, CONSTANT)` — traversal structurally impossible.

## FILE PERMISSIONS
All files created via `FileOutputStream` in app-private directories; no `MODE_WORLD_*`, no `chmod`/`setReadable`, no `sharedUserId`, no FileProvider/content URI, no external storage. Effective mode bits (expected 0600 under the zygote umask 077) are **not asserted anywhere** → INSTRUMENTED/PHYSICAL verification recommended. Root/compromised OS is outside the threat model and not claimed to be resisted.

---

## ROOT-006
**CONFIRMED (with minor expansion).**
- Prior Consensus severity: MEDIUM. Specialist proposed: **MEDIUM** (unchanged). Confidence: VERY_HIGH.
- Exact evidence: `RegistrationSessionKey.kt:47-61` `decrypt()` → `:63-69` `getOrCreateKey()` → `:71-84` `generateKey()` (creates and, if the alias holds a non-`SecretKeyEntry`, **overwrites**). Invoked by `FileRegistrationSessionStore.load():47` ← `RegistrationOrchestrator.currentState():59` — every state read. `CryptoBridge.kt:38-44` `getInstance()` never caches → `:50-65` `initialize()` → `:73-101` `initializeMasterKey()` creates `anox_crypto_master_key` whenever absent, including when `anox_state_key.enc` exists (read/status entry path manufactures the wrapping key, converting "master key missing" into "wrapped key unauthenticable + replacement exists" → reported as `MissingKeystore`). `:106-110` `getMasterKey()` `as SecretKey` NPE on null → not matched by `isKeystoreOrUnwrapFailure` → `CorruptedIdentityState`. `serializeIdentity:337`/`serializeSession:526` use `getOrCreateStateKey()` for an existing identity (split-brain K_STATE if wrapped file lost while a handle is live). Expansion: `FileRegistrationSessionStore.save():58` calls `key.encrypt()` **outside** the try → Keystore exceptions escape unwrapped (not `RegistrationSessionSecurityException`), inconsistent with `load()`.
- Reachability: DEAD_OR_UNWIRED today; ACTIVATES_AT_B004 (first `currentState()`).
- Pre-B004: **YES**. Coupling: MUST fix with ROOT-007 (consumer semantics) and the storage error taxonomy (AS-A); Auth AD-E.

## ROOT-007
**CONFIRMED and EXPANDED.**
- Prior severity: MEDIUM ("highest-priority MEDIUM; HIGH the moment a server accepts a second binding"). Specialist proposed: **MEDIUM now / HIGH at B-004 unless server JKT uniqueness (Auth GAP-003) is frozen first** — same conditional as consensus; no re-severity. Confidence: VERY_HIGH.
- Confirmed components: (1) no parent-directory fsync in `AtomicFileWriter.kt:15-26`, `CryptoBridge.writeFileAtomic:783-794`, AndroidX `AtomicFile.finishWrite` (only `getFD().sync()` on the file); (2) absent marker → `(false,false)` (`FileDeviceAuthBindingStore.kt:38`) → `AbsentNotBound`; (3) zero-length session file → `NotStarted` (`FileRegistrationSessionStore.kt:44`), contradicting the class KDoc (":16 returns NotStarted only when no file exists").
- **Expansion (harness-proven on the real classes):** (4) `AtomicFile.finishWrite()` swallows fsync **and rename** failure (`Log.e` only) → `save()` returns normally while the base file still holds the previous state (`.new` left behind) — a "durably armed" claim can be false without any exception (see CANDIDATE-002); (5) marker fail-closed holds only for **structural** corruption (size≠6, bad magic, unknown version): v2 flags with bits 0/1 clear (e.g. `0x00`, `0x04`) → unbound; **v1 garbage flags (`0x03`, `0xff`) → unbound**; single-bit flips of `0x03` still block (`0x02`/`0x01`), but a two-bit zeroing is fail-open; (6) `AtomicFile.openRead()/startWrite()` auto-rename a sibling `anox_registration_session.enc.bak` over the live file — a stale/planted `.bak` becomes authoritative; (7) `markArmed()` from an absent marker writes `0x02` (armed, not bound) — correct; from a corrupt marker writes `0x03` (heals to bound) — correct direction.
- Chain (unchanged from consensus, revalidated line-by-line): power loss/`pm`-level truncation ⇒ marker absent **and/or** session file empty/unauthenticable ⇒ `canStartNew(Failed|NotStarted)` true ⇒ `createKeyIfAbsent()` allowed ⇒ **second Device Auth key on an installation whose commit may have succeeded**. Additional first-run cross-check is absent: marker missing while `anox.deviceauth.p256.v1` / `anox.b003.session.v1` / `anox_crypto_master_key` exist is still treated as first run.
- Pre-B004: **YES** (all components together, plus CANDIDATE-002).

## ROOT-010
**CONFIRMED (Android side, no severity change).** Prior LOW; proposed **LOW**. Evidence: K_STATE returned as `ByteArray` and never cleared at `CryptoBridge.kt:337,366,526,553`; **`:622` unwraps K_STATE into an unused local** (a second copy per status call); codec plaintext `ByteArray` (contains grant) at `FileRegistrationSessionStore.kt:51,57` never cleared; grant held as immutable `String`; `decrypt()` outputs never cleared. Only best-effort `fill(0)` is achievable on the JVM; no false guarantee should be made. Gate: B008/B009 (unchanged). Fix group AS-C / CJ-F.

## ROOT-011
**CONFIRMED and EXPANDED (storage/rollback side).** Prior MEDIUM; proposed **MEDIUM** (unchanged). Evidence: no generation/epoch anywhere; identity/session envelopes accept any older valid ciphertext (Crypto audit); **registration envelope has no AAD at all** (`RegistrationSessionKey.encrypt/decrypt` never call `updateAAD`; the version byte is outside authentication — Auth audit note **verified**); wrapped-key envelope (`wrapStateKey`) has no AAD; binding marker is plaintext with no freshness — restoring an old `0x02`/`0x00` marker or deleting it rolls the terminal-loss anchor backwards; `.bak` sibling substitution (harness). Concrete consequences per object: identity → OTK re-publication/double consumption, rewound ratchets (B-008+); registration → step replay bounded by server idempotency, **no new grant exposure** (same grant); marker → `BOUND→ARMED` still blocks, `BOUND→absent/0x00` fails open (ROOT-007). Realistic vector today = app-UID writer or image-level restore (backup excluded by config) → matches consensus B008/B009 gating for identity; **the marker/registration rollback pieces belong to the Pre-B004 ROOT-007 fix set**.

## ROOT-012
**CONFIRMED and EXPANDED (wipe side).** Prior LOW; proposed **LOW** (unchanged; coupling raised — see GAP-002). Evidence: `wipeLocalCrypto():737-754` deletes alias first (correct order) then three `File.delete()` with ignored results → `CryptoResult.success` unconditionally; no `.tmp` cleanup; live handles untouched; scope excludes `noBackupFilesDir` state, `anox.b003.session.v1`, Device Auth alias. Expansion: `FileRegistrationSessionStore.clear()` → `AtomicFile.delete()` ignores all three delete results; `deleteLegacyArtifacts()` best-effort by contract; `RegistrationSessionKey` alias is **never** deleted (unbounded lifetime); no `.new` cleanup; **no cross-domain wipe/logout/delete orchestrator exists** (B-013 NOT_IMPLEMENTED). Gate: B008/B009 + Final Product Gate (unchanged), design contract Pre-B013.

## ROOT-015
**CONFIRMED.** Prior LOW; proposed **LOW**. Evidence: `UuidV4.kt:28` checks `version()==4` only; harness: `RegistrationId.parse("12345678-1234-4123-0123-123456789abc")` (NCS variant) accepted. Storage relevance: codec decode consumes only self-written, AEAD-authenticated data → **no local security consequence**; matters only at the server-response parse boundary (B-004). No re-severity; Final Product Gate unchanged.

## ROOT-017
**CONFIRMED (storage-specific).** Prior severity: UNKNOWN in registry (meta root). Specialist proposed: **MEDIUM (enabling condition)** for the storage slice. Evidence: 66 instrumented storage/Keystore tests exist, none executed in CI (`ci.yml:89` runs only `testDebugUnitTest`); last known execution was a PROMPT-008 emulator run **before** the encrypted session store existed; all 87 CI-executed storage tests use in-memory fakes (no fsync, Keystore, real file, or crypto); zero tests for zero-length file, alias deletion, flags corruption, residue, rollback, wipe partial failure, rejected-after-arm; zero physical evidence. Pre-B004 (unchanged).

---

## REGISTRATION SESSION KEY
`KeyGenerator("AES","AndroidKeyStore")`, 256-bit, GCM/NoPadding, `setUserAuthenticationRequired(false)`, alias `anox.b003.session.v1`; created lazily inside `getOrCreateKey()` on first `encrypt` **or first `decrypt`**; no caching (Keystore `getEntry` per operation); never rotated; never deleted (survives `clear()`, `Committed`, and any wipe); no AAD; envelope `0x01‖IV(12)‖ct‖tag(16)`; `decrypt` size check `<13` (comment says "at least a tag" but 13–28 bytes pass the check and fail only at GCM — harmless).

## CREATE-ON-READ
**YES** — `decrypt()` → `getOrCreateKey()` → `generateKey()`. Sequence when key is missing and an envelope exists: read → alias absent → new key K′ generated → GCM under K′ fails → `AEADBadTagException` → `RegistrationSessionSecurityException("could not be authenticated")` → `currentState()` synthetic `Failed` → `canStartNew` true unless marker armed/bound. Net: a read permanently converts recoverable "key missing" into "envelope unauthenticable + replacement key exists", and the caller cannot distinguish key-missing from corrupt. **ROOT-006 CONFIRMED.**

## KEY CREATION CONCURRENCY
Source-level race is real: `getEntry` (check) and `generateKey` (act) are unsynchronized; each `FileRegistrationSessionStore` owns its own default `RegistrationSessionKey()`; multiple stores/orchestrators may exist. Android Keystore semantics: generating into an existing alias **replaces** the entry (documented `KeyGenParameterSpec` behaviour) — so A's K1 can be replaced by B's K2 after A encrypted under K1 → A's envelope unauthenticable at next read. Physical feasibility on a real provider not demonstrated here (no runtime); classified SOURCE_RACE_CONFIRMED / PROVIDER_BEHAVIOUR_DOCUMENTED / PHYSICAL_NOT_TESTED. Reachable only with a concurrent caller (B-004).

## ALIAS COLLISION
`RegistrationSessionKey`: alias present but not `SecretKeyEntry` (wrong type) → `generateKey()` **overwrites** the foreign entry; inaccessible/`UnrecoverableKeyException` from `getEntry` propagates → wrapped by `load()` (fail-closed) but escapes `save()` raw. Device Auth: wrong-type alias → `as? PrivateKey` = null → treated as absent → `AbsentNotBound` (if no marker) → `generateKeyPair()` overwrites (Auth CANDIDATE-002 territory; not duplicated). Neither class fails closed on alias-type collision.

---

## REGISTRATION SESSION STORE
`load()`: base absent → delete legacy artifacts → `NotStarted`; read failure → security exception; **empty → `NotStarted`**; decrypt failure (any exception incl. Keystore) → security exception; codec null → security exception. `save()`: encode → encrypt (**outside try**) → `startWrite` (may rename `.bak`→base) → write → flush → `finishWrite` (fsync+rename, **errors swallowed**) ; exceptions → `failWrite` + security exception. `clear()`: `AtomicFile.delete()` (base, `.new`, `.bak`; results ignored) + legacy cleanup. State transitions: exactly the orchestrator's; `NotStarted` is also encodable (`0x01 0x00`) though never saved by production code. Crash during first write: `.new` present, base absent → `NotStarted` + ciphertext residue (not authoritative). Crash after `finishWrite` rename before directory durability → previous state reappears (no dir fsync).

## BINDING STORE
Actual state model (harness map): `ABSENT→(F,F)`; `v2 0x00→(F,F)` (explicit clear — **indistinguishable from never-bound**); `v2 0x01→(T,F)` (only via legacy v1 or corruption); `v2 0x02→(F,T)` ARMED; `v2 0x03→(T,T)` BOUND; `v2 other bits→bitwise` (0x04→(F,F)); `v1 0x01→(T,F)`; **`v1 ≠0x01→(F,F)`**; size≠6 / bad magic / unknown version / unreadable → `(T,T)` CORRUPT-FAIL-CLOSED. Absence is interpreted as **FIRST RUN**, not as an unknown state — this is the security-critical asymmetry (ROOT-007). No MAC, no Keystore binding, no cross-check with other security state.

## EMPTY FILE SEMANTICS
Verified: `FileRegistrationSessionStore.kt:44` maps a 0-byte file to `NotStarted`; harness confirms `AtomicFile.readFully()` returns length 0 for an empty base. A crash/truncation (or app-UID writer) can therefore downgrade `Reserved…CommitArmed` to first-run **iff** the marker is also absent/zeroed; with an armed/bound marker `canStartNew` still blocks. Crypto side: empty identity file → `deserialize` fails → `CorruptedIdentityState` (fail-closed, inst. test exists).

## CORRUPTION TAXONOMY
Distinguished today — registration: `NOT_FOUND`(→NotStarted), `EMPTY`(→NotStarted, **wrong**), everything else → one exception type with message text (`read` / `authenticate` / `malformed`); **not distinguished:** `KEY_MISSING` vs `AUTHENTICATION_FAILED` (key recreated), `UNSUPPORTED_VERSION` vs truncation (both `IllegalStateException`→authenticate), `IO_FAILURE` vs `PERMISSION_FAILURE`, `ROLLBACK` (undetectable). Crypto: `FirstRun/WipedState/MissingStateKey/MissingKeystore/CorruptedIdentityState` distinguished; **`MissingKeystore` ≡ corrupted wrapped-key file ≡ master key replaced**; master key null → NPE → `CorruptedIdentityState`; deserialize `0` collapse (Crypto CANDIDATE-003). Marker: `CORRUPT(structural)→bound`, `CORRUPT(payload)→parsed`. Security-relevant collapses: EMPTY→first-run; KEY_MISSING→corrupt(+key created); marker payload corruption→unbound.

---

## ATOMIC FILE DURABILITY
Three writers. `AtomicFileWriter`/`writeFileAtomic`: write → flush → `fd.sync()` → `renameTo` (throws on failure, deletes tmp). AndroidX `AtomicFile`: write → `finishWrite` (fsync **logged on failure**, rename **logged on failure**). None fsyncs the parent directory. Content is never torn; **commit is not crash-durable and, for the registration store, not truthfully reported.**

## FILE FSYNC
Present in all three (`FileDescriptor.sync()`); failure throws in the two custom writers; **swallowed** in `AtomicFile`.

## DIRECTORY FSYNC
**Absent in all three.** On ext4/f2fs a `rename()` may be lost on power failure until the directory entry is journaled; the caller has already returned "durably armed". ROOT-007 component 1 CONFIRMED.

## TEMP FILE RESIDUE
`.enc.tmp` (crypto, fixed name, ciphertext) left after exception between sync and rename or during write; `anox_registration_session.enc.new` (ciphertext) left after crash before `finishWrite` or after swallowed rename failure; `anox_deviceauth_binding.state.tmp` (flags) left on write exception; legacy plaintext `.state`/`.state.tmp` removed only on load-when-absent/clear. Startup handling: none; `.tmp` never read (safe); `.new` deleted on next `openRead` only if base exists (safe); **`.bak` is auto-restored over the base (unsafe policy inherited from the library)**. `wipeLocalCrypto` does not remove any residue.

## CROSS-FILE TRANSACTIONALITY
None (5 domains: session file, marker, Device Auth alias, session-key alias, identity/K_STATE). The orchestrator relies on ordering (`save(CommitArmed)` → `markArmed` → remote → `markBound` → `save(Committed)` → `clear`). Ordering is correct in direction; durability of each step is the weak point (ROOT-007), and the `Rejected` branch persists `Failed` over `CommitArmed` (CANDIDATE-001).

## CRASH STATE MATRIX

| SESSION | MARKER | DEVICE KEY | IDENTITY | Current behaviour | Class |
|---|---|---|---|---|---|
| CommitArmed | absent (rename lost) | present | present | `canStartNew` false (state not startable); `commit()` resumes; expiry suppressed by state | fail-closed (state-side) |
| CommitArmed | absent | **absent** | present | `AbsentNotBound`; `validateDeviceAuthForCommit` → Invalid → `Failed` returned (not persisted) → stuck, **no new key while session survives** | fail-closed (denial) |
| empty/unauth (`Failed`) | absent | absent | present | `canStartNew(Failed)` **true** → `reserve` → new key | **FAIL-OPEN (ROOT-007 chain)** |
| empty/unauth | armed/bound | absent | present | `TerminalKeyLoss`; `canStartNew` false | fail-closed |
| Failed (Rejected path) | armed | present | present | permanently armed; `reserve` blocked; `commit()` fails (state not resumable); only `clearBinding()` exits | fail-closed **denial** (CANDIDATE-001/GAP-001) |
| missing (`clear()` done) | bound | present | present | steady state after success | correct |
| missing | bound | **absent** | present | `TerminalKeyLoss` (terminal, correct); E2EE untouched | correct |
| missing | absent | **present** (Keystore survived, files gone) | absent | `AbsentNotBound`?? no — `Present` → `createKeyIfAbsent` no-op → **same JKT re-registered under a new account** | SERVER_PREREQUISITE (Auth GAP-003) |
| any | bound | present | **absent** (identity deleted, K_STATE present) | `WipedState` → step 3 throws (fail-closed) | fail-closed |
| any | bound | present | files present, master alias gone | `getInstance` recreates alias → unwrap fails → `MissingKeystore` → step throws | fail-closed (misleading label) |
| PublicIdentityUploaded (save(CommitArmed) silently failed) | armed | present | present | resume re-runs `commit()`: save → arm → remote (idempotent) | bounded by server idempotency |
| Reserved (rolled back) | armed | present | present | `registerDeviceAuth()` re-submits same JWK with same grant → server idempotency on `(registration_id, jkt)` required (Auth GAP-002) | SERVER_PREREQUISITE |

---

## CRYPTO IDENTITY STORAGE
Path `filesDir/anox_identity.enc`; envelope `ANOX‖0x01‖nonce‖GCM(ct)` with AAD `ANOX‖0x01`, key = K_STATE (Rust); written via `writeFileAtomic` (fixed `.tmp`, no dir fsync); loaded via `loadIdentity`/`getLocalStateStatus` → `deserializeIdentity` with `getExistingStateKey()` (read never creates ✓); missing file + present K_STATE → `WipedState` (fail-closed); both absent → `FirstRun` (documented wipe/first-run semantics); zero-length/truncated/modified → `CorruptedIdentityState` (inst. tests). Backup: excluded by manifest rules only. Wipe: `wipeLocalCrypto`. Rollback: undetectable.

## K_STATE STORAGE
Representation: 32 random bytes (`SecureRandom`), wrapped `IV(12)‖GCM(ct‖tag)` under Keystore `anox_crypto_master_key` (no AAD), persisted `filesDir/anox_state_key.enc` via `writeFileAtomic`. Created only in `getOrCreateStateKey()` (create/serialize paths). Read via `getExistingStateKey()` (deserialize/status) — **verified: read/status paths do not generate a replacement K_STATE** (MAINARCH-023 remediation effective for the wrapped key). **The master (wrapping) alias, however, is created by `initialize()` on every `getInstance()`** — the wrapping-key half of the invariant is not read-safe. Memory: `ByteArray` copies never cleared (incl. unused copy `:622`). Concurrency: per-instance lock only (ROOT-002).

## K_STATE KEY LOSS
`encrypted state + wrapped key present, master alias missing` → next `getInstance()` recreates the alias → `unwrapStateKey` → `AEADBadTagException` → `MissingKeystore` (terminal-looking, fail-closed, **but the reported label hides that a replacement wrapping key now exists**); if alias creation itself fails → `getMasterKey()` NPE → `CorruptedIdentityState` (misclassified). `wrapped key file missing, identity present` → `MissingStateKey` (correct, no regeneration). Architecture (B-013) expects fail-closed + explicit reset path: fail-closed ✓, reset path ✗ (GAP-002). No silent regeneration of K_STATE or identity ✓.

---

## BACKUP
Configuration excludes every anoX security file from cloud backup and D2D on API 31+, and from full backup on API 26–30; registration/marker additionally in `noBackupFilesDir`. Enumerated restore outcomes if an agent ignored rules: identity/K_STATE ciphertext without matching master alias → `MissingKeystore` (denial, not disclosure); registration ciphertext without `anox.b003.session.v1` → unauthenticable → `Failed` (+ROOT-006 key creation); **marker restored while key absent → `TerminalKeyLoss` (denial)**; marker absent while Keystore key survived → same-JKT re-registration (server prerequisite). No confidentiality loss from ciphertext-only restore; **denial/terminal states are the realistic risk**, plus the ROOT-007 fail-open if only the marker is lost.

## DEVICE-TO-DEVICE TRANSFER
`<device-transfer>` excludes all domains (API 31+); API 26–30 D2D uses the full-backup path disabled by `allowBackup=false`. Architecture expectation: Inv.25 + ULTIMATE "one device / reinstall = new account" imply exclusion, but **no authority text names D2D/Seedvault/profile explicitly** → `ARCHITECTURE_GAP` (GAP-003), current configuration is consistent with the implied policy.

## APP DATA CLEAR
Expected (`pm clear`): `filesDir` + `noBackupFilesDir` emptied; AOSP `clearApplicationUserData` also clears the UID's Keystore entries (`clearKeystoreData`) → consistent first run (all 5 domains absent). LKSL §F states this expectation. **Not verified physically.** Worst-case inconsistent combinations: (a) Keystore entries survive → Device Auth `Present`, marker absent → old JKT re-registered under a new account (needs server `device_auth_keys.public_key` UNIQUE — Auth GAP-003); RegistrationSessionKey survives → harmless; master alias survives → harmless (new K_STATE). (b) Files survive, keys gone → `MissingKeystore`/`TerminalKeyLoss` denial states with no reset path (GAP-002).

## UNINSTALL / REINSTALL
Code assumes reinstall = first run (all state gone). Architecture agrees (ULTIMATE §Lifecycle, B-013). Dependencies made explicit: (1) Keystore entries deleted on uninstall (platform behaviour, PHYSICAL); (2) no backup restore re-injects files (config ✓, PHYSICAL); (3) **server-side uniqueness of Device Auth public key / one-active-device** rejects a surviving key rebinding — SERVER_PREREQUISITE, not yet in V1.2 schema text (Auth GAP-003, reaffirmed).

## PROFILE ISOLATION
Source makes no profile assumptions; Android scopes app data and Keystore per user/UID, so Owner/secondary/work profiles are separate installations (each may hold its own account — consistent with Inv.2 since they are distinct devices from the server's view). Architecture is silent → GAP-003. GrapheneOS secondary-user deletion behaviour: PHYSICAL.

---

## ROLLBACK
No persisted security object has freshness: identity/session (no epoch), registration (no AAD, no counter), marker (plaintext flags), wrapped key (no AAD). AEAD detects **tampering, not rollback**. Vectors: app-UID writer, image/backup restore (excluded by config), `.bak` sibling (library behaviour), power-loss rename loss (effectively a rollback to the previous version — ROOT-007).

## IDENTITY ROLLBACK
Old valid pickle accepted → unpublished OTK set reappears (duplicate publication), consumed OTKs re-consumable (one-time property broken for those keys), sessions rewound → message-key reuse. Activation: B-006 publication / B-008 messaging (server-side OTK bookkeeping is the only current mitigation). B008/B009 gate (consensus) stands.

## REGISTRATION ROLLBACK
Restoring `Reserved`/`DeviceAuthRegistered`/`PublicIdentityUploaded` over `CommitArmed` → step replay with the **same** grant/JWK (server idempotency dependent; no new grant exposure); restoring `Failed`/`Expired`/`NotStarted` → blocked by an armed/bound marker, **fail-open if marker also rolled back**; restoring `CommitArmed` over `Failed(Rejected)` → retry of an already-rejected commit (server must re-reject); restoring `Committed` → decoded and treated as terminal (harmless: `canStartNew` false). Grant TTL (30 m) bounds most replay windows; `CommitArmed` suppresses expiry deliberately.

## BINDING MARKER ROLLBACK
`BOUND(0x03)→ARMED(0x02)`: still blocks creation, but `commit()` cannot resume (session cleared) → denial. `BOUND→0x00/absent`: **fail-open** (ROOT-007). `BOUND→v1 0x01`: bound, not armed — fine. Consequence hinges entirely on server uniqueness.

## ANTI-ROLLBACK REQUIREMENT
Conceptual assessment (no implementation): Keystore-protected counter — Android offers no app-accessible monotonic/rollback-resistant counter; a Keystore-authenticated counter *file* is itself rollback-able → insufficient alone. Server monotonic epoch — available from B-004; server already knows committed device/key and (B-006) published/consumed OTK ids → **the practical V1 authority**. Persisted sequence number — only useful as tamper evidence, not rollback resistance. Hardware RPMB — not exposed to apps; do not require. **Minimum practical V1:** (1) server as authority for device/key uniqueness and OTK/publication state; (2) local **first-run cross-check**: marker absent **and** any anoX Keystore alias present ⇒ not first run ⇒ fail closed (require explicit reset) — cheap, closes the marker-deletion fail-open without a trusted counter; (3) AAD/type/version binding on all local envelopes so rollback at least cannot be combined with substitution; (4) keep backup exclusion. Defer hardware-backed counters.

---

## ENVELOPE VERSION / AAD
Crypto envelope: version inside AAD ✓ (`-9` distinct in Rust, collapsed to `0` at JNI — Crypto CANDIDATE-003). Registration envelope: version byte **outside** authentication, **no AAD** (verified: no `updateAAD`); unsupported version → `IllegalStateException` → security exception (fail-closed); downgrade impossible today (single version), possible once v2 exists unless v1 is refused. Wrapped K_STATE: no version, no AAD. Marker: version byte plaintext; unknown version → fail-closed `(T,T)` ✓.

## DOMAIN SEPARATION
Three keys for three domains ✓ (cross-domain substitution fails at GCM). Within K_STATE: identity vs session share key + AAD (parse-failure only — Crypto audit). Within RegistrationSessionKey: single object type; codec type tag inside the authenticated payload; **structurally identical states (`DeviceAuthRegistered`/`PublicIdentityUploaded`/`CommitArmed`) are interchangeable by tag byte** — only relevant to a key-holder, so not a finding (harness evidence only).

## PATH BINDING
None of the envelopes bind filename/path. Registration → identity path: fails (different key). Identity → session: parse failure (Crypto). `.bak` → live: **accepted by design of `AtomicFile`** (harness). Distinguished: cryptographic separation (keys) vs format-accident separation (parse) vs none (`.bak`).

---

## WIPE INVENTORY

| Function | Objects | Delete API | Result checked? | Failure propagated? | Remaining aliases | Remaining files | Remaining tmp |
|---|---|---|---|---|---|---|---|
| `CryptoBridge.wipeLocalCrypto()` | master alias; `anox_state_key.enc`, `anox_identity.enc`, `anox_session.enc` | `deleteEntry`, `File.delete()`×3 | alias: exception only; files: **NO** | alias exception → `CryptoFailure`; files: **never** | `anox.b003.session.v1`, `anox.deviceauth.p256.v1`; master alias **recreated by next `getInstance()`** | registration, marker, any custom-named identity/session files | all `.tmp` |
| `CryptoBridge.destroyAllCrypto()` | = wipeLocalCrypto | — | — | — | same | same | same |
| `AndroidKeystoreDeviceAuthKeyManager.deleteKeyDestructively()` | Device Auth alias | `containsAlias`+`deleteEntry` | exception only | YES (throws) | others | marker stays → `TerminalKeyLoss` | — |
| `FileDeviceAuthBindingStore.clearBinding()` | marker → writes `0x00` | write (not delete) | YES (throws on rename fail) | YES | — | file remains (harmless) | `.tmp` on exception |
| `FileRegistrationSessionStore.clear()` | base, `.new`, `.bak`, legacy ×2 | `AtomicFile.delete()`, `File.delete()` | **NO** | **NO** | session key alias never deleted | — | `.new` if delete fails |
| RegistrationSessionKey deletion | — | **does not exist** | — | — | alias permanent | — | — |
| Temp cleanup | — | **does not exist** (except legacy `.state.tmp`) | — | — | — | — | all |
| Cross-domain wipe / logout / account-delete | — | **NOT_IMPLEMENTED** | — | — | — | — | — |

## WIPE SUCCESS SEMANTICS
`wipeLocalCrypto` returns `Success` after partial or total file-deletion failure (only Keystore exceptions fail it). `clear()` returns void with all results ignored. No contract states "best-effort" for these methods (B-009 says wipe is best-effort for the *user-facing* operation; a primitive silently reporting success is still untruthful for the caller that must decide whether to show "wiped").

## WIPE ORDER
Current `wipeLocalCrypto`: key → files (cryptographic erasure first → correct for confidentiality; crash after `deleteEntry` leaves files that read as `MissingKeystore` until re-wipe — fail-closed denial). Recommended full-reset order (design only): stop workers → delete Device Auth alias → delete master alias → delete K_STATE/identity/session/registration files + residue → delete session-key alias → **clear marker last** (a crash before the last step leaves `TerminalKeyLoss`, the safe direction; clearing the marker first while the Device Auth key still exists would allow same-JKT re-registration).

## SECURE DELETE LIMITATION
Cryptographic erasure = Keystore alias deletion (renders ciphertext permanently undecryptable; strongest available); logical file deletion = unlink (data remains on flash until GC/TRIM); memory clearing = best-effort only on JVM; physical flash remanence cannot be guaranteed from app code (B-009 "no NAND physical-erasure claim" — correctly stated in authority; code makes no such claim).

## LOGOUT / WIPE / DELETE MATRIX

| Operation | DeviceAuth key | Binding marker | Registration state | K_STATE (+master) | E2EE identity | Session state |
|---|---|---|---|---|---|---|
| Logout (B-002/B-013: keep everything, revoke network) | keep | keep | n/a (cleared at commit) | keep | keep | keep — **NOT_IMPLEMENTED** |
| Local wipe / reset (B-013) | delete | **must clear (unspecified)** | delete + residue | delete both | delete | delete — **NOT_IMPLEMENTED**; only `wipeLocalCrypto` covers K_STATE/identity/session |
| Account delete (B-013: server erasure intent → local wipe) | delete | clear | delete | delete | delete | delete — **NOT_IMPLEMENTED** |
| Uninstall / pm clear | platform | platform | platform | platform | platform | platform — PHYSICAL |

---

## CONCURRENCY
Per-instance `@Synchronized` (both file stores); per-instance `ReentrantLock` (`CryptoBridge`, broken singleton — ROOT-002); `RegistrationOrchestrator` unsynchronized (check-then-act on `currentState()`); Keystore creation check-then-act in both key classes. Races: read-while-rename is safe (rename atomic); two saves from two instances interleave on fixed `.new`/`.tmp` names → torn temp → rename of a partially written temp possible → corrupt file (marker: fail-closed `(T,T)`; session: security exception + ROOT-006); `clear` during `save` → `.new` orphan or resurrected state; wipe during load → `MissingKeystore`.

## MULTI-INSTANCE
Yes — all stores/managers are plain classes with public constructors and no factory; instance locks do not serialize globally. Same pattern as `CryptoBridge` (ROOT-002) and Device Auth (Auth CANDIDATE-002). Activation: B-004 wiring.

## MULTI-PROCESS
Single process (no `android:process`, no `sharedUserId`); no file locks used and none needed today. Code silently assumes one process (no `FileLock`); acceptable, should be stated in the storage contract (GAP-001).

---

## CODEC REVIEW
`BinaryRegistrationStateCodec`: version byte checked; 8 tags, unknown → null; every string length-prefixed, bounded `0..16384` (negative/oversize rejected — harness); `readFully` → EOF → null; UUIDs re-parsed (version only); username re-validated; grant **not** validated (empty accepted); expiry any long; **trailing bytes ignored**; malformed UTF-8 → replacement chars… harness shows null because the username re-validation rejects — but `Failed.reason`/thumbprint fields would accept replacement chars silently (benign); `decode` catches all exceptions → null (single failure class). All payloads are AEAD-authenticated before decode, so untrusted-server text cannot cause a silent downgrade — **but the codec is not the guard; the AEAD key is**, and ROOT-006 weakens key semantics. Tag ordering (`COMMIT_ARMED=7`, `FAILED=6`) cosmetic.

## UUID VALIDATION
Syntax (`UUID.fromString`, lenient on segment lengths — `1-2-4-8-a` rejected only because version ≠ 4), version 4 ✓, **variant not checked** (NCS-variant accepted — harness). ROOT-015 CONFIRMED; no storage-boundary consequence.

## FILE SIZE BOUNDS
Codec strings ≤16 KB ✓. Whole-file reads unbounded: `readFully()`, `readBytes()` (identity → also two native copies). Local DoS only via app-UID writer → not a finding (recorded as REJECTED with reasoning).

---

## PLAINTEXT-AT-REST SEARCH
Grant: inside GCM envelope only (legacy plaintext `.state` deleted best-effort; dev-era only). Tokens: none persisted. Identity/session keys: encrypted (Rust). Usernames/JKT/registration id: inside envelope; also in `Failed.reason` strings (inside envelope) and in exception messages returned to callers (public identifiers, Inv.26-compliant). Marker flags: plaintext by design (non-secret). K_STATE: wrapped. **No plaintext secret at rest found.**

## STORAGE METADATA EXPOSURE
Filenames constant, reveal only that anoX is installed and whether a registration/binding exists (file presence/size: marker 6 B; session file size correlates weakly with state); `.new`/`.tmp` presence reveals interrupted writes. Within app-private storage; forensic relevance only. `AtomicFile`/`writeFileAtomic` exception text includes absolute paths (no identifiers).

---

## TEST EXECUTION
```
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
./gradlew --offline --no-daemon :android:testDebugUnitTest \
  --tests 'com.anox.messenger.account.*' --tests 'com.anox.messenger.security.deviceauth.*' --tests 'com.anox.crypto.*'
BUILD SUCCESSFUL in 13s
Executed 177  Passed 177  Failed 0  Errors 0  Skipped 0   (timestamps 2026-09-13T15:56Z)
  account 104 (crash 12, orchestrator 28, codec 12, grant 7, identifiers 7, username 12, license 10, duration 6, renewal 7, states 3)
  deviceauth 69, crypto error-map 4
```
Harness (`/tmp/anox_android_storage_audit/harness/Harness.java` compiled against `android/build/tmp/kotlin-classes/debug` + `kotlin-stdlib-2.2.21` + `androidx.core:core:1.12.0` with stub `android.content.Context`/`android.util.Log`; output `out.txt`): marker 16-state map + 8 single-bit flips; `clearBinding` bytes vs absent; `AtomicFileWriter` rename-failure (throws, no residue ✓); **`AtomicFile.finishWrite` returns normally on rename failure with `.new` residue**; **`.bak` planted → `readFully` returns planted bytes**; empty base → len 0; `.new`+no base → FileNotFound with residue; codec: empty/1-byte/version-2/unknown tags/truncation/negative/`0x7fffffff`/16385 lengths all → null; trailing bytes accepted; tag relabel among identical-layout states accepted; empty grant accepted; UUID NCS-variant accepted; malformed UTF-8 username rejected; 16384-byte reason encodes, 16385 rejected.

## INSTRUMENTED TESTS
`NOT_RUN — NO APPROVED RUNTIME ENVIRONMENT` (`adb devices`: none; no emulator started; destructive Keystore tests not launched). 66 instrumented tests exist; would run against the **stale committed `.so`** (ROOT-001).

## PHYSICAL TESTS
`NOT_RUN`. No GrapheneOS device. Nothing claimed.

---

## PHYSICAL GRAPHENEOS CAMPAIGN

| # | Requirement | Procedure (defensive, high-level) | Expected |
|---|---|---|---|
| P1 | StrongBox/TEE level for all 3 aliases | run instrumented suites on GrapheneOS Pixel; record `KeyInfo.securityLevel` for Device Auth; confirm AES aliases are hardware-backed | `STRONGBOX` or `TEE`; never `SOFTWARE` |
| P2 | Device Auth non-exportability | `privateKey.encoded == null`; `getKeySpec(ECPrivateKeySpec)` throws | pass |
| P3 | RegistrationSessionKey storage & create-on-read | delete alias with a valid session file present; call `load()`; inspect aliases | today: key recreated (ROOT-006 physical confirmation) |
| P4 | `pm clear` | bind (marker 0x03, 3 aliases, files) → `pm clear` → enumerate aliases + files → `status()` | all absent → `AbsentNotBound`; **record any alias survival** |
| P5 | uninstall/reinstall | same as P4 via `pm uninstall`/install | same |
| P6 | reboot | bound state → reboot → status | unchanged |
| P7 | OS update | bound → OTA → status | unchanged |
| P8 | secondary profile | install in second user; verify separate dirs + aliases; delete profile; verify Owner unaffected | isolation |
| P9 | Keystore invalidation | lock-screen change/removal, credential reset | no invalidation (user-auth off) |
| P10 | backup/restore (Seedvault, D2D) | enable Seedvault (incl. "D2D"-style option); backup; restore on same/different device/new profile; enumerate files | **no anoX file restored** |
| P11 | device-to-device transfer | Pixel setup transfer | no files |
| P12 | abrupt process kill during commit | `kill -9` between `save(CommitArmed)`/`markArmed`/remote (instrumented hooks) | resume matrix above |
| P13 | power-loss durability (where safely reproducible) | battery pull / forced reboot immediately after `markArmed()` returns; repeat N× | marker present every time (today: expect occasional loss without dir fsync) |
| P14 | file mode bits | `stat` all anoX files/dirs | 0600 / 0700 |

## BACKUP/RESTORE PHYSICAL MATRIX

| Asset | backup created? | restore same device | restore different device | reinstall | new profile |
|---|---|---|---|---|---|
| Device Auth alias | never (Keystore) | absent unless survived | absent | absent | absent |
| RegistrationSessionKey alias | never | absent | absent | absent | absent |
| master alias | never | absent | absent | absent | absent |
| `anox_state_key.enc` / identity / session | **must be NO** | if present → `MissingKeystore` | same | same | same |
| registration file | NO (noBackup) | if present → unauthenticable → ROOT-006 | same | same | same |
| marker | NO (noBackup) | if present w/o key → `TerminalKeyLoss` | same | same | same |
| Expected end state | — | FirstRun/AbsentNotBound | same | same | same |

---

## HISTORICAL FINDING REVALIDATION

| Finding | Historical status | Current relation | Evidence | Action |
|---|---|---|---|---|
| `ANOX-SECURITY-ARCH-003` (registration fail-closed gaps) | Open | STILL_EFFECTIVE (Open) + RELATED_NEW_ROOT_CAUSE | primitives beneath the state machine unsound (ROOT-006/007); `Rejected`-after-arm bypasses `failStep` (CANDIDATE-001) | expand at consolidation |
| `ANOX-SECURITY-ARCH-007` (K_STATE getOrCreate lifecycle) | Open | **INEFFECTIVE_REMEDIATION_SCOPE** | deserialize paths fixed; `initializeMasterKey()` still creates on ctor/status path; identical pattern in `RegistrationSessionKey.decrypt` | ROOT-006 |
| `ANOX-MAINARCH-023` (read paths persist fresh K_STATE) | Closed | **PARTIALLY_EFFECTIVE** | wrapped K_STATE never created on read ✓ (inst. test); wrapping alias created on every `getInstance()`; `serialize*` still `getOrCreate` | keep Closed; relate to ROOT-006 |
| `ANOX-SECURITY-ARCH-008` (error masking / UUID) | Open | STILL_EFFECTIVE (Open) | NPE→`CorruptedIdentityState`; variant unchecked | ROOT-013/015 |
| `ANOX-SECURITY-ARCH-009` (wipe scope WAL/SHM/backup) | Open | STILL_EFFECTIVE (Open) + RELATED_NEW_ROOT_CAUSE | wipe ignores results, misses residue/noBackup files/aliases | ROOT-012 / GAP-002 |
| `ANOX-MAINARCH-030` (wipeLocalCrypto scope vs B-009) | Open | STILL_EFFECTIVE (Open) | no cross-domain wipe exists | GAP-002 |
| `ANOX-MAINARCH-018` (GrapheneOS physical) | Open | PHYSICAL_REVALIDATION_REQUIRED | none at this SHA | campaign above |
| `ANOX-LEGACY-INTEGRATION-002` (identity persisted before OTK) | Closed | STILL_EFFECTIVE (ordering) / RELATED_NEW_ROOT_CAUSE | `saveIdentity` before returning OTKs (`:41-47`) ✓; functionally blocked by ROOT-004 (4096) | none here |
| `ANOX-LEGACY-INTEGRATION-003` (CommitArmed vs armed divergence) | Closed | **PARTIALLY_EFFECTIVE** | `failStep`/`expiredOrNull` protect CommitArmed ✓; `commit()` `Rejected` branch persists `Failed` over `CommitArmed` while armed (`:224-226`) | CANDIDATE-001 |
| `ANOX-LEGACY-ANDROIDSEC-001` (KeyStoreException API-33 class ref) | Closed | STILL_EFFECTIVE | string class-name matching `:764-777` | none |
| `ANOX-LEGACY-B003-001` (UUID variant) | Open | SUPERSEDED_BY/SAME ROOT ROOT-015 | harness | unchanged |
| PROMPT-008 §7 design claim "corrupt session → NotStarted is safe" | historical prompt (evidence) | NO_LONGER_APPLICABLE (superseded by encrypted store + security exception) — **except the empty-file remnant** | `:44` | ROOT-007 |
| Consensus `ROOT-006` | ACTIVE MEDIUM | CONFIRMED | above | Pre-B004 |
| Consensus `ROOT-007` | ACTIVE MEDIUM | CONFIRMED + EXPANDED (4 new components) | above | Pre-B004 |
| Consensus `ROOT-010` | ACTIVE LOW | CONFIRMED | above | B008/B009 |
| Consensus `ROOT-011` | ACTIVE MEDIUM | CONFIRMED + EXPANDED (registration/marker side) | above | B008/B009 + Pre-B004 slice |
| Consensus `ROOT-012` | ACTIVE LOW | CONFIRMED + EXPANDED | above | B008/B009 / final gate |
| Consensus `ROOT-015` | ACTIVE LOW | CONFIRMED | harness | final gate |
| Consensus `ROOT-017` | ACTIVE (UNKNOWN sev) | CONFIRMED | 66 inst. not CI; 0 physical | Pre-B004 |
| Consensus `ROOT-016` | REJECTED | **NOT revived** — `deleteKeyDestructively` from StrongBox catch cannot reach a bound key (`Present` early return) | — | remains rejected |
| Audit-002 `C-016` INFO items (Committed-then-clear; Rejected permablock; `.tmp`) | ACCOUNTED_FOR (bundle) | RELATED_NEW_ROOT_CAUSE | Rejected permablock now CANDIDATE-001 | consolidation |
| Auth `ANOX-AUTHDPOP-CANDIDATE-002` | Open | ADJACENT (alias overwrite semantics shared with RegistrationSessionKey) | — | AD-A/AS-A coordination |
| Auth `ANOX-AUTHDPOP-GAP-003` | Open | **REAFFIRMED as the server half of ROOT-007** | matrix row "key survived, files gone" | Pre-B004 |

## INEFFECTIVE HISTORICAL REMEDIATIONS
- `ANOX-SECURITY-ARCH-007` / `ANOX-MAINARCH-023`: read-vs-create split applied to the wrapped K_STATE only; wrapping-alias creation in `initialize()` and `RegistrationSessionKey.decrypt()` untouched (ROOT-006).
- `ANOX-LEGACY-INTEGRATION-003`: guard covers `failStep`/expiry but not the direct `save(Failed)` on `Rejected` (CANDIDATE-001).

## STILL-EFFECTIVE HISTORICAL REMEDIATIONS
`ANOX-LEGACY-ANDROIDSEC-001`; `ANOX-LEGACY-INTEGRATION-002` (ordering); `ANOX-MAINARCH-023` (wrapped-key read paths); LEGACY plaintext-session removal (PROMPT-008C→encrypted store); marker structural fail-closed; `createAndPersistFirstIdentity` refuse-if-exists; `WipedState`/`MissingStateKey` distinctions.

---

## AUDIT-LOCAL FINDINGS

### TOTAL
2 candidates + 3 architecture gaps (+ 7 consensus roots confirmed/expanded without new IDs)

### CRITICAL
0

### HIGH
0

### MEDIUM
0

### LOW
2 — `ANOX-ANDROIDSTORAGE-CANDIDATE-001`, `ANOX-ANDROIDSTORAGE-CANDIDATE-002`

### INFO
0 (INFO observations folded into root expansions: unused K_STATE copy `:622`, `save()` unwrapped encrypt exceptions, stale `AtomicFileWriter` KDoc, session-key alias never deleted, trailing codec bytes)

---

## ARCHITECTURE GAPS

| Gap | Statement | Gate |
|---|---|---|
| `ANOX-ANDROIDSTORAGE-GAP-001` | **No authority defines the registration-session store or the Device Auth binding marker** (states `ABSENT/ARMED/BOUND/CLEARED/CORRUPT`, durability requirement incl. directory fsync, empty/corrupt/key-missing taxonomy, first-run definition vs Keystore-alias presence, armed-latch release semantics after an authoritative commit rejection, single-process assumption). B-003 v1.5 §3 says the guard "may be made explicit" and B-013 requires an "explicit local reset path" — neither is specified. | PRE-B004 (contract freeze) |
| `ANOX-ANDROIDSTORAGE-GAP-002` | **Local wipe / logout / account-delete storage contract absent at implementation level**: which of the 5 domains + marker + residue each operation touches, deletion order (marker last), truthful vs best-effort result semantics per primitive, alias lifecycle (`anox.b003.session.v1` never deleted), who may call `clearBinding()`/`deleteKeyDestructively()`/`wipeLocalCrypto()`. | PRE-B004 (contract), B-013 (impl), Final gate (ROOT-012) |
| `ANOX-ANDROIDSTORAGE-GAP-003` | **Backup/restore/D2D/app-data-clear/reinstall/profile expected-state contract and anti-rollback authority unspecified**: Inv.25 + ULTIMATE imply exclusion and first-run-on-reinstall, but no authority states expected states after `pm clear`/restore, the Keystore-survival assumption, profile policy, Seedvault/D2D explicitly, or that the **server is the rollback/uniqueness authority** (ties to Auth GAP-003). | PRE-B004 (contract), physical final gate |

---

## FINDINGS TABLE

| Candidate | Severity | Confidence | Root cause | Authority | Evidence | Consensus relation | Historical relation | Reachability | Activation | Gate | Fix group | Retest |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **ANOX-ANDROIDSTORAGE-CANDIDATE-001** — `commit()` on `CommitResult.Rejected` persists `Failed` over `CommitArmed` while the armed marker remains set; installation becomes permanently armed with no resumable evidence and no reset path; contradicts `RegistrationState`/orchestrator KDoc | LOW (fail-closed denial, not bypass) | HIGH | one-way armed latch + direct `sessionStore.save(next)` bypassing `failStep`; transient-vs-permanent rejection undefined | B-003 v1.5 §3 (client precondition), B-013 (explicit reset path), B-003 (commit idempotent; retry uses same grant) | `RegistrationOrchestrator.kt:216-226`, `:302-310` (failStep contract), `FileDeviceAuthBindingStore.kt:58-61` (only exit); JVM test `rejected commit does not bind` asserts only `!isBound` | RELATED to ROOT-007 marker semantics (opposite direction); distinct root cause (lifecycle contract) | Audit-002 C-016 INFO sub-item; `ANOX-LEGACY-INTEGRATION-003` PARTIALLY_EFFECTIVE | DEAD_OR_UNWIRED | B-004 (first real `Rejected`) | **PRE-B004 = YES (contract via GAP-001/Auth GAP-002); code fix in AS-B** | AS-B | JVM: `Rejected` after arm preserves `CommitArmed` or transitions to an explicit terminal `RejectedAfterArm` state; reset path test; instrumented marker + session end state |
| **ANOX-ANDROIDSTORAGE-CANDIDATE-002** — `FileRegistrationSessionStore` delegates durability to AndroidX `AtomicFile`, whose `finishWrite()` swallows fsync **and rename** failures (`Log.e` only), leaves `.new` residue, and auto-restores any sibling `.bak` over the live file; `save()` therefore reports success without a committed write and `clear()` ignores delete results | LOW (bounded by the throwing marker writer + server idempotency; grant not exposed) | HIGH (harness-reproduced on `core:1.12.0`) | error-swallowing library primitive used for a security-state write path | B-003 v1.5 §3 "durable"; Inv.23 | `FileRegistrationSessionStore.kt:59-71,76`; `androidx/core/util/AtomicFile.java` `finishWrite`/`rename`/`openRead`/`delete`; harness: rename failure → normal return, `.new` present; `.bak` planted → returned by `readFully` | **EXPANDS ROOT-007 (component 4)**; distinct primitive-level mechanism recorded separately for coverage-gate tracking | Audit-001 CS-006 adjacent (dir fsync) | DEAD_OR_UNWIRED | B-004 | PRE-B004 = YES (inside ROOT-007 set) | AS-B | JVM (real class, temp dir): rename failure → exception; `.bak` ignored/deleted; `.new` cleaned on startup; instrumented same |

## NEW ROOT-CAUSE CANDIDATES
`ANOX-ANDROIDSTORAGE-CANDIDATE-001` (armed-latch lifecycle), `ANOX-ANDROIDSTORAGE-CANDIDATE-002` (error-swallowing write primitive / `.bak` policy).

## CONFIRMED CONSENSUS ROOTS
`ROOT-006`, `ROOT-007`, `ROOT-010`, `ROOT-011`, `ROOT-012`, `ROOT-015`, `ROOT-017`.

## EXPANDED CONSENSUS ROOTS
`ROOT-007` (AtomicFile swallowed errors; marker payload-level fail-open incl. v1 garbage; `.bak` auto-restore; no Keystore-presence first-run cross-check), `ROOT-011` (registration envelope no AAD/version unauthenticated; marker rollback; `.bak` substitution), `ROOT-012` (`clear()` ignores results; no cross-domain wipe; session-key alias never deleted; `.new` residue), `ROOT-006` (`save()` unwrapped Keystore exceptions; alias-type overwrite).

## CONTRADICTED CONSENSUS ROOTS
None. (Sub-claims refined: marker "corrupt ⇒ bound" is true only for structural corruption; single-bit flips of `0x03` still block; wrapped-K_STATE read paths do **not** create — only the wrapping alias and the session key do.)

## REJECTED / NOT FINDINGS
- Unbounded whole-file reads (local DoS) — requires app-UID writer ≡ device compromise; no security consequence beyond crash.
- Codec tag relabel among identical-layout states / trailing bytes — inside AEAD; a key-holder can rewrite anything anyway.
- Legacy plaintext `.state` deletion only on absent-base/clear — PROMPT-008C dev-era artifact; no production install.
- Crypto state in `filesDir` rather than `noBackupFilesDir` — matches LKSL §D; manifest rules exclude it; defense-in-depth suggestion only.
- `wipeLocalCrypto` key-first ordering — correct direction, not a finding.
- `deleteKeyDestructively` from StrongBox `catch` destroying a bound key — ROOT-016 remains REJECTED (guard verified).
- Debug-build `adb backup`/`run-as` extraction — debuggable only; ciphertext only.
- Marker `clearBinding()` writing `0x00` instead of deleting — semantically equal to absent; harmless.

---

## PRE-B004 STORAGE BLOCKERS
Consensus roots: `ROOT-006`, `ROOT-007` (all 4+ components), `ROOT-017` (storage instrumented CI), plus the **registration/marker slice of `ROOT-011`** (AAD/version binding, marker freshness cross-check) because it is inseparable from the ROOT-007 fix.
Candidates: `ANOX-ANDROIDSTORAGE-CANDIDATE-002` (with ROOT-007); `ANOX-ANDROIDSTORAGE-CANDIDATE-001` contract half.
Gaps: `ANOX-ANDROIDSTORAGE-GAP-001`, `GAP-002` (contract), `GAP-003` (contract) — must be frozen before B-004 implementation (Inv.35). Server prerequisite reaffirmed: Auth `GAP-003` JKT/device uniqueness.

## LATER-GATE STORAGE ITEMS
- `ROOT-010` Android best-effort clearing → B008/B009 (AS-C/CJ-F); no exploit path before messaging.
- `ROOT-011` identity/session anti-rollback mechanism (server epoch + AAD hook) → B008/B009 with CJ-C.
- `ROOT-012` wipe truthfulness + residue + cross-domain wipe implementation → B-013 lifecycle + Final Product Gate (design contract is Pre-B004 via GAP-002).
- `ROOT-015` → Final Product Gate (unchanged; no storage consequence).
- `CANDIDATE-001` code change → AS-B during B-004 registration wiring (after GAP-001 freeze).
- Physical GrapheneOS campaign P1–P14 → Final gate on a provenance-verified binary (ROOT-001).

---

## MUST-FIX-TOGETHER
1. **ROOT-006 ∧ ROOT-007 ∧ `RegistrationSessionStore` consumer**: existing-only `decrypt` + explicit `KEY_MISSING`/`EMPTY`/`UNSUPPORTED_VERSION` exceptions + `currentState()`/`canStartNew()` treating them as not-first-run + marker cross-check — changing any one alone shifts the fail-open elsewhere.
2. **Marker durability ∧ registration-state durability ∧ crash-state resolver**: dir fsync in all writers + `AtomicFile` replacement/result checking (CANDIDATE-002) + a single resolver that derives "first run" from *all* of {marker, session file, Keystore aliases}.
3. **ROOT-011 rollback ∧ freshness source ∧ server authority**: AAD/type/version binding on local envelopes + server device/key uniqueness + OTK/publication epoch (B-006) — local AAD alone does not stop rollback; server alone does not stop local substitution.
4. **ROOT-012 wipe ∧ all aliases/files/residue ∧ truthful result**: wipe must enumerate every domain incl. `noBackupFilesDir` files, `.tmp`/`.new`, all three aliases, marker-last ordering, and return a per-item result.
5. **Backup exclusion ∧ reinstall behaviour ∧ one-device server uniqueness** (GAP-003 ∧ Auth GAP-003): the client's first-run assumption is only safe if the server rejects a surviving key.
6. **CANDIDATE-001 ∧ GAP-001 ∧ Auth GAP-002**: armed-latch release needs the rejection-class contract before code changes.

## MUST-NOT-FIX-ALONE
- Making `decrypt` fail on missing key without changing `currentState()`/`canStartNew()` → still synthetic `Failed` → still startable → false closure of ROOT-006.
- Adding file fsync/dir fsync to `AtomicFileWriter` while the registration store keeps `AtomicFile.finishWrite` → arming still not truthfully durable.
- Deleting files while leaving Keystore aliases (or vice versa) in a "wipe" → inconsistent terminal states (`MissingKeystore`/`TerminalKeyLoss`) with no reset path.
- Deleting keys and returning success despite leftover state → false "wiped" UX.
- Adding a local rollback counter without a trustworthy authority → false anti-rollback.
- Moving one file to `noBackupFilesDir` while other authoritative state stays manifest-rule-dependent → inconsistent restore states.
- Fixing the marker (MAC/cross-check) without fixing the empty-file and key-missing session-store downgrades → chain remains via the session path.
- Clearing the armed marker on `Rejected` without a server rejection-class contract → re-enables key creation after a possibly-transient rejection.

## REMEDIATION GROUPS
- **AS-A** RegistrationSessionKey lifecycle + storage error taxonomy: existing-only read, create-on-write only, no alias overwrite, serialized creation, typed exceptions (`KEY_MISSING`, `EMPTY`, `UNSUPPORTED_VERSION`, `AUTH_FAILED`, `IO`), `save()` wrapping; coordinates with Auth AD-E/AD-A. (ROOT-006, ROOT-006 expansion)
- **AS-B** Marker + registration-state crash consistency: dir fsync in all writers; replace/guard `AtomicFile` (check rename, forbid `.bak` restore, startup residue policy); empty-file → security exception; first-run resolver with Keystore-alias cross-check; marker payload integrity (dedicated Keystore HMAC alias, "HMAC key missing ⇒ bound") ; `Rejected`-after-arm state. (ROOT-007, CANDIDATE-001/002)
- **AS-C** Crypto identity/K_STATE persistence: `initializeMasterKey` only on create paths; `serialize*` for existing identity uses existing key; status taxonomy (NPE → `MissingKeystore`, corrupt-wrapped-key distinct); best-effort `fill(0)`; residue cleanup; coordinates with CJ-B/CJ-E. (ROOT-006 crypto component, ROOT-010, ROOT-013 consumer)
- **AS-D** Rollback/domain/version architecture: AAD = type‖version‖(context) for registration and wrapped-key envelopes; crypto AAD hook (CJ-C); server epoch/uniqueness as authority; marker freshness policy. (ROOT-011)
- **AS-E** Wipe/logout/delete semantics: cross-domain wipe orchestrator, ordering (marker last), per-item results, alias lifecycle incl. `anox.b003.session.v1`, residue cleanup, visibility narrowing of destructive primitives. (ROOT-012, GAP-002)
- **AS-F** Backup/restore/profile/D2D policy: freeze expected-state contract (GAP-003), optional move of crypto files to `noBackupFilesDir`, lint `DataExtractionRules` warning disposition.
- **AS-G** Verification: instrumented storage suites in CI on emulator (both ABIs, provenance-verified `.so`), new negative tests listed above, physical GrapheneOS campaign P1–P14. (ROOT-017)

## REQUIRED REMEDIATION ORDER
1. Freeze contracts: GAP-001 (marker/session/first-run/armed release), GAP-002 (wipe/logout/delete), GAP-003 (backup/reinstall/profile/anti-rollback authority) + Auth GAP-002/003 as B-spec amendment.
2. AS-A explicit read-vs-create + typed error taxonomy (client + `CryptoBridge` init path).
3. AS-B crash-consistent transition design + first-run resolver (consumes AS-A exceptions).
4. AS-B file + directory durability, `AtomicFile` replacement, residue policy.
5. AS-B marker/state coupling (integrity + cross-check) + CANDIDATE-001 state.
6. AS-D envelope AAD/version binding (client side) — before any second envelope version exists.
7. AS-F backup/device-transfer rules and file-location decision.
8. AS-E wipe semantics (needs AS-A/AS-B taxonomy and AS-D alias list).
9. AS-D rollback authority (server epoch) with B-004/B-006.
10. AS-G tests (JVM negative suite, instrumented CI).
11. Physical verification on provenance-verified binary (ROOT-001 prerequisite).

---

## SEC-A
AS-A, AS-C, AS-F (component-local corrections; no trust-boundary change).

## SEC-B
AS-B, AS-D, AS-E (cross-component state-transition/contract changes touching client↔server authority and lifecycle; no systemic redesign), AS-G (CI/physical evidence infrastructure).

## SEC-C REQUIRED
**NO** — the local trust model (Keystore-bound non-exportable keys, AEAD-protected state, no recovery, backup exclusion, server-authoritative binding) is correct; the defects are unsound primitives, missing contracts, and untruthful durability/wipe semantics inside that model.

## ARCHITECTURE VERDICT
**`COMPONENT_INTERNAL_REDESIGN_ONLY`** — the storage layer needs a coherent local-state contract (first-run definition, error taxonomy, durability, wipe) and a first-run resolver across the five domains, but the boundary (device-private files + Keystore + server authority) stands. Not `LOCAL_STATE_ARCHITECTURE_REDESIGN`: no new storage technology, key hierarchy, or trust anchor is required; B-009 migration of the file envelope into SQLCipher is already planned and unaffected.

---

## ATTACKCHAIN HANDOFF
- **Marker loss (ROOT-007) × RegistrationSessionKey regeneration (ROOT-006) × missing server JKT uniqueness (Auth GAP-003)** → second Device Auth key bound to a new account while the first account/key remain server-side; local first-run resolver never consults surviving Keystore aliases.
- **Rollback (ROOT-011) × OTK/session state** → old identity pickle re-publishes/re-consumes OTKs; combined with ROOT-005 enumeration duplicates at B-006.
- **Partial wipe (ROOT-012) × stale credentials** → `wipeLocalCrypto` "success" while registration file / Device Auth key / marker remain → device still authenticates (key kept) or is stuck terminal; account-delete UX shows "wiped".
- **Restored backup × missing Keystore key** → `MissingKeystore`/`TerminalKeyLoss` denial with no reset path (GAP-002) → user forced to `pm clear` → first run → new account (intended) — but if only the marker restored and key survived: same-JKT rebind.
- **Crash consistency × re-registration** → `save(CommitArmed)` swallowed rename (CANDIDATE-002) + `markArmed` durable + server committed + crash → resume re-runs commit (idempotency dependency, Auth GAP-002).
- **Key/file mismatch × fail-open first-run classification** → alias-type collision overwrite (ROOT-006 expansion / Auth CANDIDATE-002) → old envelope unauthenticable → `Failed` → startable if marker also gone.
- **`.bak` substitution × registration replay** → planted old envelope becomes live on next read → step replay with same grant (server idempotency).

---

## REMEDIATION COVERAGE METADATA

**ANOX-ANDROIDSTORAGE-CANDIDATE-001**
SOURCE: AUDIT-SECURITY-ANDROID-STORAGE-001 · ROOT_CAUSE: armed marker is a one-way latch; `commit()` `Rejected` branch persists `Failed` over `CommitArmed` via direct `save` (bypasses `failStep`); no authoritative release/reset contract · AFFECTED_CODE: `RegistrationOrchestrator.kt:216-232,302-310`, `FileDeviceAuthBindingStore.kt:58-61`, `RegistrationState.kt` (KDoc), `RegistrationOrchestratorTest.kt:129-138` · AFFECTED_ARCHITECTURE: B-003 v1.5 §3, B-013 (reset path), Auth GAP-002 (rejection classes) · FIX_GROUP: AS-B (+GAP-001) · PRE_B004_OR_LATER: PRE_B004 (contract) / B-004 wiring (code) · REQUIRED_TEST: JVM — `Rejected` after arm never overwrites `CommitArmed` or transitions to explicit `RejectedAfterArm`; permanent-vs-transient rejection handling; explicit reset path clears marker last · RUNTIME_TEST: instrumented end-state of marker + session file after rejected commit · PHYSICAL_TEST: none · INDEPENDENT_RETEST_OWNER: next ANDROID/STORAGE retest session (not implementer) · DEPENDENCIES: GAP-001, Auth GAP-002, ROOT-007 set · DISPOSITION: OPEN_PENDING_CONSOLIDATION

**ANOX-ANDROIDSTORAGE-CANDIDATE-002**
SOURCE: AUDIT-SECURITY-ANDROID-STORAGE-001 · ROOT_CAUSE: AndroidX `AtomicFile.finishWrite()` swallows fsync/rename failures; `.bak` auto-restore; `.new` residue; `delete()` results ignored · AFFECTED_CODE: `FileRegistrationSessionStore.kt:28-31,39-44,59-71,74-78`; `androidx.core:core:1.12.0` `AtomicFile` · AFFECTED_ARCHITECTURE: B-003 v1.5 §3 "durable", Inv.23 · FIX_GROUP: AS-B (ROOT-007 component 4) · PRE_B004_OR_LATER: PRE_B004 · REQUIRED_TEST: JVM real-class temp-dir tests — rename failure throws; `.bak` never restored; `.new` cleaned at startup; parent-dir fsync invoked (mock FD) · RUNTIME_TEST: instrumented same + `kill -9` between write and rename · PHYSICAL_TEST: P12/P13 · INDEPENDENT_RETEST_OWNER: ANDROID/STORAGE retest session · DEPENDENCIES: ROOT-007 (dir fsync), ROOT-006 (taxonomy) · DISPOSITION: OPEN_PENDING_CONSOLIDATION

**ANOX-ANDROIDSTORAGE-GAP-001**
SOURCE: AUDIT-SECURITY-ANDROID-STORAGE-001 · ROOT_CAUSE: binding marker / registration store exist only as PROMPT-008 implementation artifacts; no authority contract · AFFECTED_CODE: `FileDeviceAuthBindingStore.kt`, `FileRegistrationSessionStore.kt`, `RegistrationOrchestrator.kt`, `DeviceAuthKeyStateResolver.kt` · AFFECTED_ARCHITECTURE: B-003 v1.5 §3, B-002, B-013, Inv.23/35 · FIX_GROUP: contract freeze → AS-A/AS-B · PRE_B004_OR_LATER: PRE_B004 · REQUIRED_TEST: authority validator asserting contract presence; conformance tests once implemented · RUNTIME_TEST: — · PHYSICAL_TEST: — · INDEPENDENT_RETEST_OWNER: architecture consistency retest · DEPENDENCIES: Auth GAP-002/003 · DISPOSITION: OPEN_PENDING_CONSOLIDATION

**ANOX-ANDROIDSTORAGE-GAP-002**
SOURCE: AUDIT-SECURITY-ANDROID-STORAGE-001 · ROOT_CAUSE: B-013 wipe/logout/delete not decomposed into per-domain storage operations, order, result semantics, alias lifecycle, call authority · AFFECTED_CODE: `CryptoBridge.wipeLocalCrypto`, `deleteKeyDestructively`, `clearBinding`, `clear()`, (missing) orchestrator · AFFECTED_ARCHITECTURE: B-013, B-009, LOCAL_DEVICE_SECURITY §4, LKSL §M · FIX_GROUP: contract → AS-E · PRE_B004_OR_LATER: PRE_B004 (contract) / B-013 (impl) / Final gate (ROOT-012) · REQUIRED_TEST: wipe enumerates all domains; partial failure reported; marker cleared last; residue removed · RUNTIME_TEST: instrumented wipe + alias enumeration · PHYSICAL_TEST: P4/P5 · INDEPENDENT_RETEST_OWNER: ANDROID/STORAGE retest · DEPENDENCIES: ROOT-012, ANOX-MAINARCH-030, ARCH-009 · DISPOSITION: OPEN_PENDING_CONSOLIDATION

**ANOX-ANDROIDSTORAGE-GAP-003**
SOURCE: AUDIT-SECURITY-ANDROID-STORAGE-001 · ROOT_CAUSE: expected local states after `pm clear`/reinstall/restore/D2D/profile and the Keystore-survival + first-run assumptions, plus the anti-rollback authority (server), are implied but not frozen · AFFECTED_CODE: manifest/extraction rules, `DeviceAuthKeyStateResolver`, `CryptoBridge.getLocalStateStatus`, future first-run resolver · AFFECTED_ARCHITECTURE: Inv.25, ULTIMATE §Lifecycle, B-013, B-021 backup/restore + physical rows, Auth GAP-003 · FIX_GROUP: contract → AS-F/AS-D · PRE_B004_OR_LATER: PRE_B004 (contract) / Final gate (physical) · REQUIRED_TEST: authority validator; lint disposition · RUNTIME_TEST: — · PHYSICAL_TEST: P4, P5, P8, P10, P11 · INDEPENDENT_RETEST_OWNER: physical campaign owner + architecture retest · DEPENDENCIES: ROOT-007, ROOT-011, Auth GAP-003 · DISPOSITION: OPEN_PENDING_CONSOLIDATION

**Consensus-root expansions recorded (no new IDs):** ROOT-006 (`save()` unwrapped exceptions; alias-type overwrite; `initializeMasterKey` per `getInstance`) → AS-A/AS-C; ROOT-007 components 4–7 → AS-B; ROOT-011 registration/marker side → AS-D; ROOT-012 scope → AS-E; ROOT-010 `:622` unused copy → AS-C; ROOT-017 storage inst. deficit → AS-G. Each inherits the parent root's gate; retest owner = ANDROID/STORAGE retest session.

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

---

## NEXT ACTION
`PRESERVE AUDIT-SECURITY-ANDROID-STORAGE-001 → AUDIT-SECURITY-ATTACKCHAIN-001 → PRESERVE → MASTER SPECIALIST CONSOLIDATION → SECURITY-REMEDIATION-COVERAGE-GATE → LARGE DEPENDENCY-SAFE REMEDIATION → INDEPENDENT RETESTS → LEGACY/ARCHITECTURE REVALIDATION → FRESH FULL-SYSTEM RE-AUDIT → OPERATIONAL ACCEPTANCE → HUMAN FINAL GATE → ONLY THEN B004`

```
HEAD        = b9abeb0850a476716403d224b87a857c1147502e
origin/main = b9abeb0850a476716403d224b87a857c1147502e
working tree = CLEAN (git status --short empty; git diff --check clean; branch main)
branches / commits / push / PR / merge = NONE · remote mutation = NONE
findings / docs / registries / Project Memory mutation = NONE · fixes implemented = NONE
temp artifacts = /tmp/anox_android_storage_audit/{atomicfile,harness} only
```

`AUDIT-SECURITY-ANDROID-STORAGE-001` — COMPLETE. `PASS_WITH_FINDINGS`. STOP.
