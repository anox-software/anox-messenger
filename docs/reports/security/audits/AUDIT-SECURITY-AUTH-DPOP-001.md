# AUDIT-SECURITY-AUTH-DPOP-001 — FINAL REPORT

## AUDIT RESULT
**`PASS_WITH_FINDINGS`**

## AUDIT
`AUDIT-SECURITY-AUTH-DPOP-001`

## PROVIDER
Devin CLI (Cognition) session runtime

## MODEL
Claude Fable 5.1 High (as reported by the session system prompt: "You are powered by Claude Fable 5.1 High"). No routing/fallback observed.

## MODEL REQUIREMENT SATISFIED
YES

## MODE
`READ_ONLY_DEVICE_AUTH_DPOP_SECURITY_SPECIALIST_AUDIT`

## AUDITED SHA
`638e63a22c91ca81365bf55c8a59ec47878dd7fd`

## HEAD AT END
`638e63a22c91ca81365bf55c8a59ec47878dd7fd`

## ORIGIN MAIN
`638e63a22c91ca81365bf55c8a59ec47878dd7fd`

## WORKING TREE
CLEAN (`git status --short` empty; `git diff --check` clean; branch `main`)

## REPOSITORY MODIFIED
NO (only gitignored `android/build/` touched by the Gradle test run; temp harness under `/tmp/anox_auth_dpop_harness/`)

## REMOTE MUTATION
NONE

---

## PRESERVED EVIDENCE VALIDATION
**PASS** — `python3 tools/audit/validate_security_audit_evidence_preservation.py` → `SECURITY AUDIT EVIDENCE PRESERVATION: PASS`. All six preserved reports, `AUDIT_EVIDENCE_INDEX.md`, `audit_registry.jsonl`, `audit_traceability.jsonl`, `evidence_hashes.json` read. None modified.

---

## AUTHORITY SOURCES

| Doc | Precedence | Relevant content |
|---|---|---|
| `B025/SECURITY_INVARIANTS_V1_1.md` | 1 | Inv. 2 (one active device), 7 (Device Auth independent), 8 (P-256/ES256 + RFC9449 DPoP), 18 (DPoP replay controls), 23 (no silent regeneration), 24 (key distinctness), 25 (no backup recovery), 26 (no secrets in logs), 33 (tests ≠ proof) |
| `B025_MANDATORY_AMENDMENTS_V1_2.md` | 9 | B-004 pipeline (PoP → replay → token binding), `AuthenticatedDeviceContext` (`device_id` bound to Device Auth key), `auth` schema (`device_auth_keys`, `access_tokens`, `replay_cache`, `nonces`), endpoint table (`/v1/registration/submit-device-auth` DPoP=No; `/v1/registration/commit` Auth=PoP, DPoP=Yes, Idempotency=Yes; `/v1/auth/challenge|token|revoke` DPoP=Yes), race table (two commits → one wins), error classes `invalid_dpop`/`replay_detected`, logging bans DPoP proofs |
| `B025_MANDATORY_AMENDMENTS_V1_1.md` | 8 | B-003 v1.5: `CommitArmed` is client-side only; server relies on grant + Device Auth PoP + atomic commit |
| `B002_DEVICE_AUTHENTICATION.md` (FROZEN v1.1) | 11 | P-256/ES256 Keystore, non-exportable, StrongBox preferred/TEE ok/software fails; no attestation V1; DPoP `jti≥128b`, `iat±120s`, shared replay cache 5m; token 256-bit/SHA-256 stored/15m/no refresh; fresh nonce at issuance; logout keeps key; key loss terminal |
| `B003_ACCOUNT_LICENSE.md` v1.4 (+V1.1) | 11 | server UUIDv4 ids, one active device DB-enforced, registration sequence with PoP, grant 256-bit/30m, commit idempotent |
| `B007_API_WIRE.md` v1.9 | 11 | RFC9449 `htu` semantics; `iat` numeric; retry uses fresh DPoP proof |
| `B004_BACKEND_SERVICE_ARCHITECTURE.md`, `B016` | 11 | server derives identity; replay state cannot be process-local |
| `ULTIMATE_MAIN_ARCHITECTURE_B025.md` §Device Authentication / §Lifecycle | 7 | reinstall = new account; logout keeps key; no re-binding after loss |
| `B021_SECURITY_TEST_MATRIX.md` | 11 | Device Auth nonce/DPoP/token binding/replay/key invalidation mandatory test classes |

Historical prompts (PROMPT-007/008C) referenced in KDoc are treated as evidence, not authority.

## B002 / DEVICEAUTH SOURCE INVENTORY

Production (`android/src/main/java/com/anox/messenger/…`), all reviewed in full:

| # | File | Role |
|---|---|---|
| 1 | `security/deviceauth/AndroidKeystoreDeviceAuthKeyManager.kt` | Keystore P-256 key lifecycle, signer |
| 2 | `security/deviceauth/DeviceAuthKeyManager.kt` | interface/contract |
| 3 | `security/deviceauth/DeviceAuthKeyStateResolver.kt` | pure terminal-loss decision |
| 4 | `security/deviceauth/DeviceAuthKeyStatus.kt` | states + exceptions |
| 5 | `security/deviceauth/HardwareSecurityLevel.kt` | eligibility policy |
| 6 | `security/deviceauth/DeviceAuthSigner.kt` | JWK + opaque JWS signer + JKT |
| 7 | `security/deviceauth/DeviceAuthBindingStore.kt` | bound/armed marker interface + in-memory |
| 8 | `security/deviceauth/FileDeviceAuthBindingStore.kt` | persistent marker |
| 9 | `security/deviceauth/DpopProofFactory.kt` | proof creation |
| 10 | `security/deviceauth/DpopProofVerifier.kt` | proof verification |
| 11 | `security/deviceauth/DpopHtu.kt` | `htu` canonicalization |
| 12 | `security/deviceauth/DpopReplayCache.kt` | replay interface + in-memory impl |
| 13 | `security/deviceauth/DpopVerificationResult.kt` | error taxonomy |
| 14 | `security/deviceauth/JtiGenerator.kt` | CSPRNG jti |
| 15 | `security/deviceauth/DeviceAuthClock.kt` | wall clock |
| 16 | `security/deviceauth/DeviceAuthAccessTokenContract.kt` | token/`ath` contract + test-scope generator |
| 17 | `security/keystore/RegistrationSessionKey.kt` | AES-GCM Keystore key for registration session |
| 18 | `account/RegistrationOrchestrator.kt` | registration state machine, Device Auth call sites |
| 19 | `account/RegistrationApi.kt` | network contract (no impl) |
| 20 | `account/RegistrationState.kt` | states incl. `deviceAuthJwkThumbprint` |
| 21 | `account/RegistrationSessionStore.kt` | store interface + in-memory |
| 22 | `account/FileRegistrationSessionStore.kt` | encrypted store |
| 23 | `account/BinaryRegistrationStateCodec.kt` | codec (grant, thumbprint) |
| 24 | `account/RegistrationGrant.kt` | grant (redacted toString) |
| 25 | `account/RegistrationSessionSecurityException.kt` | error |
| 26 | `account/DeviceId.kt`, `RegistrationId.kt`, `UuidV4.kt` | server-issued ids |
| 27 | `storage/AtomicFileWriter.kt` | marker write path |
| 28 | `account/CryptoBridgeLocalE2eeIdentityStep.kt`, `LocalE2eeIdentityStep.kt` | adjacent step (reviewed for binding only) |
| 29 | `MainActivity.kt` | reachability check (greeting screen only) |
| — | `android/build.gradle.kts` | `com.nimbusds:nimbus-jose-jwt:10.9.1` pinned; minSdk 26 |

Call-site search (`okhttp|HttpURLConnection|Retrofit|ktor|<Class>(`) in `src/main`: **zero** construction sites for any DeviceAuth/DPoP/Registration class outside their own declarations. No HTTP stack exists.

## TEST INVENTORY

| Suite | Kind | Tests | CI |
|---|---|---|---|
| `DpopProofVerifierTest` | JVM | 32 | executed (`:android:testDebugUnitTest`) |
| `DeviceAuthKeyLifecycleTest` | JVM | 17 | executed |
| `DpopHtuTest` | JVM | 7 | executed |
| `DeviceAuthAccessTokenContractTest` | JVM | 7 | executed |
| `InMemoryDpopReplayCacheTest` | JVM | 6 | executed |
| `RegistrationOrchestratorTest` | JVM | 28 | executed |
| `RegistrationCrashConsistencyTest` | JVM | 12 | executed |
| `RegistrationStateCodecTest` | JVM | 12 | executed |
| `RegistrationGrantTest` | JVM | 7 | executed |
| `AndroidKeystoreDeviceAuthKeyManagerTest` | instrumented | 10 | **NOT CI-executed** |
| `FileDeviceAuthBindingStoreTest` | instrumented | 7 | **NOT CI-executed** |
| `FileRegistrationSessionStoreTest` | instrumented | 10 | **NOT CI-executed** |
| Support: `DeviceAuthTestSupport.kt`, `AccountTestSupport.kt`, `RegistrationGrantGenerator.kt` | fixtures | — | — |

```
TOTAL AUTH/DEVICEAUTH TESTS = 155  (69 deviceauth-package + 59 registration-related + 27 instrumented)
JVM              = 128
INSTRUMENTED     = 27
PHYSICAL         = 0
CI-EXECUTED      = 128  (ci.yml runs only ./gradlew :android:testDebugUnitTest; no connectedAndroidTest)
NOT-CI-EXECUTED  = 27
```
Replay-concurrency tests: 0. HTU adversarial tests: 0 (7 happy-path only). Keystore tests: instrumented only. Hardware tests: 0 (instrumented suite explicitly refuses to assert StrongBox/TEE).

## B002 PRODUCTION FILE COVERAGE
```
B002 PRODUCTION FILES DISCOVERED = 29 (17 deviceauth + 1 keystore + 10 account/storage + MainActivity)
B002 PRODUCTION FILES REVIEWED   = 29
B002 PRODUCTION FILE COVERAGE    = 100%
```
## B002 TEST FILE COVERAGE
```
B002 RELEVANT TEST FILES DISCOVERED = 14 (9 JVM suites/fixtures in deviceauth+account relevant to auth, 3 instrumented, 2 support)
B002 RELEVANT TEST FILES REVIEWED   = 14
B002 TEST FILE COVERAGE             = 100%
```

---

## ARCHITECTURE-TO-CODE COVERAGE MATRIX

| # | Requirement / invariant | Authority | Existing implementation | Tests | Runtime evidence | Status | Finding |
|---|---|---|---|---|---|---|---|
| 1 | Device key P-256/ES256 in Android Keystore | B-002, Inv.8 | `AndroidKeystoreDeviceAuthKeyManager.generateKey`: `EC`/`secp256r1`, `PURPOSE_SIGN|VERIFY`, `DIGEST_SHA256` | inst. `firstRunCreatesP256Key` | JVM harness confirms ES256/64-byte sig with JCA key | IMPLEMENTED_NOT_VERIFIED (CI); instrumented test exists but not run | — |
| 2 | Hardware-backed requirement (TEE min.) | B-002 | `resolveHardwareSecurityLevel` via `KeyInfo.securityLevel` (API31+) / `isInsideSecureHardware`; `UNKNOWN`→ineligible | JVM `DeviceAuthKeyLifecycleTest` (policy) | none physical | PHYSICAL_VERIFICATION_REQUIRED | ANOX-MAINARCH-018 |
| 3 | StrongBox preferred, TEE fallback | B-002 | `setIsStrongBoxBacked(true)` API≥28; `catch(Exception)`→delete alias→TEE | none | none | IMPLEMENTED_NOT_VERIFIED + PHYSICAL | CANDIDATE-002 (race), ANOX-MAINARCH-018 |
| 4 | Software-only fails production registration | B-002 | `RegistrationOrchestrator.registerDeviceAuth` :105 + `validateDeviceAuthForCommit` :323 | JVM 4 tests | — | IMPLEMENTED_AND_VERIFIED | (LEGACY-019 still effective) |
| 5 | Private key non-exportable | B-002, Inv.4 | Keystore-generated; `ECDSASigner(PrivateKey, Curve)`; JWK via `toPublicJWK()` | inst. `privateKeyIsNotExportable`; JVM `signer never exposes private key` | harness: header JWK has no `d` | IMPLEMENTED_AND_VERIFIED (source) / PHYSICAL for Keystore semantics | — |
| 6 | No per-use biometric | B-002 | `setUserAuthenticationRequired(false)` | — | — | IMPLEMENTED_NOT_VERIFIED | — |
| 7 | Key attestation not mandatory V1 | B-002 | absent | — | — | NOT_APPLICABLE_YET (server cannot validate client claim → ANOX-SECURITY-ARCH-006 Open) | — |
| 8 | Device identifier = server UUIDv4 bound to Device Auth key | B-003, V1.2 §2 | `DeviceId` parse-only; thumbprint carried in `RegistrationState`; **no local binding of device_id↔JKT after commit** (Committed cleared) | JVM | — | PARTIALLY_IMPLEMENTED (server-side binding SERVER_PREREQUISITE) | GAP-003 |
| 9 | One-device-only | Inv.2, B-003 | client: `canStartNew` + binding marker; no client enforcement possible | JVM | — | NOT_APPLICABLE_YET on client / SERVER_PREREQUISITE (DB unique constraint) | GAP-003 |
| 10 | Registration PoP (submit-device-auth) | B-003 | `createDeviceAuthProof: (RegistrationId)->String` opaque lambda; `RegistrationApi.registerDeviceAuth(…, publicJwk, dpopProof)` | JVM forwards fake string | — | **IMPLEMENTATION_DRIFT / ARCHITECTURE_GAP** (proof content unspecified; not bound to grant/nonce/JWK) | CANDIDATE-001 |
| 11 | Commit requires PoP + DPoP + Idempotency | V1.2 §2 endpoint table | `commitRegistration(registrationId, grant)` — **no proof, no idempotency key** | JVM | — | **IMPLEMENTATION_DRIFT** | CANDIDATE-001 |
| 12 | DPoP header `typ=dpop+jwt`, `alg=ES256`, `jwk` | RFC9449/B-002 | `DpopProofFactory` :41–44; verifier :59–75 | JVM | harness header `{"typ":"dpop+jwt","alg":"ES256","jwk":{…}}` | IMPLEMENTED_AND_VERIFIED | — |
| 13 | JKT = RFC7638 thumbprint | B-002/RFC | Nimbus `computeThumbprint()` | JVM | harness: manual RFC7638 canonical JSON `{"crv","kty","x","y"}` SHA-256 b64url == Nimbus | IMPLEMENTED_AND_VERIFIED | — |
| 14 | `jti` ≥128 random bits | B-002 | `SecureRandomJtiGenerator` 16 B → 22 chars; verifier length-only check | JVM 25 unique | harness 100k unique | IMPLEMENTED_AND_VERIFIED (generation); verifier check is length-only (info) | — |
| 15 | `iat` numeric seconds, ±120 s | B-002, B-007 | factory `Date(now*1000)`; verifier `issueTime.time/1000` vs `±120` | JVM | harness edges −121/−120/+120/+121 correct | IMPLEMENTED_AND_VERIFIED | — |
| 16 | `htm` binding | RFC9449 | `uppercase()` both sides, equality | JVM | harness: no method validation (`""`, `"P O S T\n"` accepted) | IMPLEMENTED_AND_VERIFIED (equality) / lacks validation | ROOT-009 EXPANDED (info) |
| 17 | `htu` RFC9449 semantics | B-007, B-002 | `DpopHtu.normalize` = lower(scheme)+"://"+lower(authority)+**decoded** `URI.getPath()` | 7 happy-path | harness: 8 collisions | IMPLEMENTATION_DRIFT | ROOT-009 CONFIRMED+EXPANDED |
| 18 | Nonce (fresh at issuance; `/v1/auth/challenge`) | B-002, V1.2 | optional claim; no client nonce acquisition/storage/`DPoP-Nonce` handling | JVM nonce path | — | PARTIALLY_IMPLEMENTED (claim) / MISSING (lifecycle) | GAP-001, ROOT-008 |
| 19 | `ath` when token present | B-002/RFC §4.3 | `accessTokenHash` = b64url(SHA-256(ASCII)); optional by default | JVM | harness: verify w/o token ⇒ Valid | IMPLEMENTED (correct hash) / OPTIONAL_BY_IMPLEMENTATION | ROOT-008 CONFIRMED |
| 20 | Key binding `jkt` check | B-002 "token bound to key" | `expectedJwkThumbprint: String? = null` | JVM | harness: attacker key Valid with defaults | OPTIONAL_BY_IMPLEMENTATION | ROOT-008 CONFIRMED |
| 21 | Replay protection, shared cache 5 m | B-002, B-016 | `InMemoryDpopReplayCache` per-instance, jti-keyed, 300 s | JVM 6 | harness: 2 instances both accept | PARTIALLY_IMPLEMENTED (foundation) / SERVER_PREREQUISITE | ROOT-008 CONFIRMED |
| 22 | Proof uniqueness | Inv.18 | jti-based, not byte-based | — | harness: malleated sig (n−s) ⇒ `REPLAYED_JTI` | IMPLEMENTED_AND_VERIFIED | — |
| 23 | Replay TTL covers freshness window | derived | 300 s ≥ 120+120 s, same clock | JVM | harness proves + clock-rollback counterexample | IMPLEMENTED_AND_VERIFIED (same monotonic assumption) / drift under wall-clock rollback | CANDIDATE-003 |
| 24 | Replay check-and-insert atomicity | Inv.18 | `@Synchronized recordIfAbsent` | none | harness 200×64 threads ⇒ exactly 200 accepts | IMPLEMENTED_AND_VERIFIED (per instance) | — |
| 25 | Replay memory bound | — | none | none | harness 1,000,000 entries retained | MISSING (server-side concern) | ROOT-008 (C-019 component) |
| 26 | HTTP URI canonicalization contract client↔server | B-007 | client lossy; no server | — | — | MISSING | ROOT-009 |
| 27 | Key deletion only explicit | B-002 | `deleteKeyDestructively()` public; called from StrongBox `catch` | — | — | PARTIALLY_IMPLEMENTED | ROOT-007 (public API) / CANDIDATE-002 |
| 28 | Reinstall = first run, no recovery | ULTIMATE §Lifecycle | absent key+absent marker ⇒ `AbsentNotBound` | JVM | — | IMPLEMENTED_NOT_VERIFIED; Keystore-survives-data-clear semantics PHYSICAL | GAP-003 (server JKT uniqueness) |
| 29 | Logout keeps key; wipe deletes | B-002, ULTIMATE | no logout/wipe orchestrator; primitives exist | JVM logout-style test (no-op) | — | NOT_APPLICABLE_YET | storage handoff |
| 30 | Clock handling | B-002 | `System.currentTimeMillis()` wall clock everywhere | JVM injectable | — | IMPLEMENTED; verifier-side monotonic requirement unspecified | CANDIDATE-003 |
| 31 | Malformed-proof behaviour | RFC | every parse failure → `Invalid(reason)`; never throws | JVM 32 | harness: 5 JWK mutations + off-curve all `MALFORMED` | IMPLEMENTED_AND_VERIFIED | — |
| 32 | Missing-binding behaviour | B-002 | defaults null ⇒ skipped | JVM (only positive) | harness | IMPLEMENTATION_DRIFT (fail-open default) | ROOT-008 |
| 33 | Signing failure | — | Nimbus `JOSEException` propagates from `createProof` (unchecked) | none | — | IMPLEMENTED_NOT_VERIFIED (fail-closed by exception) | — |
| 34 | Keystore failure | — | `loadPrivateKeyOrNull` maps `KeyPermanentlyInvalidated`/`Unrecoverable` → absent; other exceptions propagate | inst. | — | IMPLEMENTED_NOT_VERIFIED | — |
| 35 | RegistrationSessionKey lifecycle (read must not create) | Inv.23, ROOT-006 | `decrypt()`→`getOrCreateKey()` **still creates on read** | none (inst. tests don't delete alias) | — | IMPLEMENTATION_DRIFT | ROOT-006 CONFIRMED (unchanged) |
| 36 | Key separation | Inv.24 | 3 aliases distinct; E2EE not in Keystore | inst. alias test (name-based) | — | IMPLEMENTED_AND_VERIFIED (source) | — |
| 37 | Terminal key loss, no silent replacement | B-002 | `DeviceAuthKeyStateResolver` + marker | JVM 17 + inst. | — | IMPLEMENTED_AND_VERIFIED (logic) / marker durability → ROOT-007 | — |
| 38 | Device Auth re-validated before arming | LEGACY-INTEGRATION-001 | `validateDeviceAuthForCommit` | JVM 4 | — | IMPLEMENTED_AND_VERIFIED | — |
| 39 | No secrets in logs/exceptions | Inv.26 | zero `Log.*`; `RegistrationGrant.toString` redacted; exceptions carry status/thumbprint only | JVM grant test | grep | IMPLEMENTED_AND_VERIFIED | — |
| 40 | Future backend verifier assumptions documented | B-004 | KDoc only | — | — | MISSING (contract) | GAP-002 |

## ARCHITECTURE COVERAGE SUMMARY
```
TOTAL CURRENT AUTH REQUIREMENTS   = 40

IMPLEMENTED_AND_VERIFIED          = 15
IMPLEMENTED_NOT_VERIFIED          = 7
PARTIALLY_IMPLEMENTED             = 6
IMPLEMENTATION_DRIFT              = 6
MISSING                           = 3
NOT_APPLICABLE_YET                = 3
PHYSICAL_VERIFICATION_REQUIRED    = 2 (rows 2,3 primary; rows 1,5,28 carry secondary PHYSICAL qualifier)
UNMAPPED                          = 0
```
(Rows with dual classification counted once under their primary status; 15+7+6+6+3+3=40.)

## UNMAPPED REQUIREMENTS
0.

---

## CURRENT RUNTIME REACHABILITY

| Component | Class |
|---|---|
| `MainActivity` | CURRENTLY_REACHABLE (greeting screen; constructs nothing) |
| `AndroidKeystoreDeviceAuthKeyManager`, `FileDeviceAuthBindingStore`, `FileRegistrationSessionStore`, `RegistrationSessionKey`, `RegistrationOrchestrator`, `DpopProofFactory`, `DeviceAuthSigner` | DEAD_OR_UNWIRED today → ACTIVATES_AT_B004 (first network/registration wiring) |
| `DpopProofVerifier`, `InMemoryDpopReplayCache`, `DeviceAuthAccessTokenGenerator`, `InMemory*` stores | TEST_ONLY (verifier semantics belong server-side; activation = B-004 backend, if this code is ported/reused) |
| `RegistrationApi` | interface only; ACTIVATES_AT_B004 |
| Logout/wipe/revoke flows | ACTIVATES_AT_LATER_GATE (B-013 lifecycle) |

Severity below is **not** reduced for unwiring; activation point is B-004 for every item unless stated.

---

## ROOT-008
**CONFIRMED** (and EXPANDED on the client side).

- Prior Consensus severity: MEDIUM now / HIGH at B-004.
- Specialist proposed severity: **MEDIUM now / HIGH at B-004** (unchanged; consolidation not required).
- Confidence: HIGH.
- Exact evidence at this SHA: `DpopProofVerifier.kt:46-48` defaults `expectedJwkThumbprint = null`, `accessToken = null`, `expectedNonce = null`; `:27` per-instance `InMemoryDpopReplayCache()`; harness: `verify(attackerProof,"POST",uri)` → `Valid(jwkThumbprint=pnoDEd…)` with an attacker-generated key; same proof accepted by verifier A **and** verifier B; two default-constructed verifiers both accept the same proof; 1,000,000 unique `jti` retained with no cap. **Expansion:** the client `DpopProofFactory.createProof(method, uri, accessToken = null, nonce = null)` (`:38-39`) mirrors the fail-open default — a B-004 client call site can mint a token-bearing request without `ath` by omission. Replay-cache statement "scoped per instance" is exactly correct; "optional by default" is exactly correct.

## ROOT-009
**CONFIRMED** and **EXPANDED**.

- Prior severity: MEDIUM. Specialist proposed: **MEDIUM** (no change; B-004 blocker stands). Confidence: VERY_HIGH.
- Exact evidence (`DpopHtu.kt:29,34` — `uri.path` decoded, `authority.lowercase()`), harness collisions on the real class: `a%2Fb ≡ a/b`, `a%2fb ≡ a/b`, `%61ccount ≡ account`, `x%2F..%2Fadmin ≡ x/../admin`, `%2e%2e/admin ≡ ../admin`, `r%C3%A9s ≡ rés`; **new**: `%3F`/`%23` decode to literal `?`/`#` inside `htu` (`/v1/a?b`, `/v1/a#b`), `%00` decodes to a NUL byte inside the signed claim, `a%2520b` → `a%20b` (double-decoding hazard vs. a server that decodes once), userinfo (`alice:pw@`) retained and lowercased inside a signed, transmitted JWT. Fail-closed mismatches (interop, not bypass): `:443` vs default port, `//` not collapsed, `..` not resolved, trailing slash, IPv6 textual forms, punycode vs Unicode host. Fail-closed on `%zz`, spaces, missing authority, `file:` — correct.

---

## DEVICE KEY VERDICT
`KeyPairGenerator("EC","AndroidKeyStore")`, `ECGenParameterSpec("secp256r1")`, purposes `SIGN|VERIFY`, digest SHA-256, `setUserAuthenticationRequired(false)`, StrongBox requested on API ≥ 28, alias `anox.deviceauth.p256.v1`; no invalidation policy set (`setInvalidatedByBiometricEnrollment` irrelevant with user-auth off); no attestation challenge; created lazily by `createKeyIfAbsent()` at registration step 2. Matches B-002 in source. **Creation is check-then-act and `generateKeyPair()` silently overwrites an existing alias** (CANDIDATE-002).

## KEYSTORE VERDICT
SOURCE_VERIFIABLE: private key never leaves Keystore (handle only; Nimbus `ECDSASigner(PrivateKey, Curve)`); public key via certificate; `KeyPermanentlyInvalidatedException`/`UnrecoverableKeyException` → treated as absent → resolver decides; alias distinct from `anox_crypto_master_key` and `anox.b003.session.v1`; delete only via public `deleteKeyDestructively()` and the StrongBox `catch` block. PHYSICAL_DEVICE_VERIFICATION_REQUIRED: actual hardware level, StrongBox fallback behaviour, key survival across app-data-clear/reinstall/profile switch, invalidation semantics on GrapheneOS Pixel.

## STRONGBOX VERDICT
**Preferred with silent fallback** (`catch (e: Exception)` → `deleteKeyDestructively()` → TEE). Consistent with B-002 ("preferred, TEE accepted"). No signal is surfaced that the fallback occurred (reported level is truthful afterwards). Hardware-backed security is **not claimed** by this audit — physical proof required (ANOX-MAINARCH-018).

## KEY ATTESTATION
Not required by B-002 v1.1 ("no mandatory remote attestation V1"); not implemented; no attestation challenge in the `KeyGenParameterSpec`. No new finding. Consequence recorded under ANOX-SECURITY-ARCH-006 (server cannot validate StrongBox/TEE claim) — SERVER_PREREQUISITE/architecture decision, not a client defect.

## DEVICE IDENTIFIER BINDING
The device is cryptographically represented by the **P-256 public key / JKT** only. `device_id` is server-issued (`DeviceId.parse` only), returned at commit, and **discarded locally** (`Committed` persisted then `sessionStore.clear()`); the binding marker stores only two flag bits. The JKT is carried through `DeviceAuthRegistered → PublicIdentityUploaded → CommitArmed` and re-derived at commit (`validateDeviceAuthForCommit`). Registration `submitPublicIdentity` and `commitRegistration` carry **no** JKT/PoP; `registerDeviceAuth` transmits `publicJwk` and `dpopProof` as two independent parameters — binding between them depends entirely on the (unspecified) server verifier extracting `jwk` from the proof and comparing. `device_id A + key B + JKT C + registration_id D` are bound only server-side, by a contract that does not yet exist below the endpoint-table level (CANDIDATE-001 / GAP-003).

## ONE-DEVICE-ONLY VERDICT
Client-enforced: only "this installation will not start a second registration while bound/armed" (`canStartNew`) — this is a *local* guard against self-rebinding, not the invariant. Server-required (architectural, B-003/B-005/V1.2 §4): `UNIQUE(account_id) WHERE status=ACTIVE` on `devices`, `UNIQUE(public_key)` on `device_auth_keys` (rejects a surviving Keystore key re-registering under a new account after marker loss), commit race "one wins". Currently impossible until backend. No false client-only claim is made by the code (KDoc explicitly says DB-enforced).

---

## KEY-SEPARATION TABLE

| Key | Purpose | Algorithm | Storage | Lifetime | Exportable | Bound to |
|---|---|---|---|---|---|---|
| Device Auth private | DPoP / PoP signing | EC P-256, ES256 | AndroidKeyStore `anox.deviceauth.p256.v1` (StrongBox→TEE) | installation; terminal on loss once bound/armed | NO (handle only) | binding marker (flags), server device record (future) |
| Device Auth public / JWK / JKT | key identity | P-256 point / RFC7638 SHA-256 | derived from Keystore cert; JKT in encrypted session state | same | public | registration state thumbprint; server `device_auth_keys` (future) |
| `RegistrationSessionKey` | seal registration session file | AES-256-GCM, 96-bit IV, 128-bit tag | AndroidKeyStore `anox.b003.session.v1` | created on first encrypt **or first decrypt** (ROOT-006); never rotated/deleted | NO | nothing (no AAD, version byte outside AAD) |
| `K_STATE` (CryptoBridge) | wrap E2EE state | AES-GCM | AndroidKeyStore `anox_crypto_master_key` + `anox_state_key.enc` | out of scope (Crypto/JNI audit) | NO | — |
| E2EE identity (Curve25519/Ed25519) | Olm | vodozemac | native, K_STATE-wrapped file | — | private never exported | account/device (server, future) |
| Registration grant | 256-bit bearer for one transaction | random | inside AES-GCM session envelope / memory | 30 m | plaintext inside sealed file | registration_id |
| Access token | bearer + `ath` | 256-bit random (server, future) | memory-only preferred | 15 m | n/a | jkt/session (server) |

No key is reused across domains. Separation holds in source. Keystore-level distinctness is on-device only (instrumented test checks alias *names*).

## REGISTRATION SESSION KEY
Generation: `KeyGenerator("AES","AndroidKeyStore")`, 256-bit, GCM, no padding, no user auth — inside `getOrCreateKey()`. Entropy: Keystore CSPRNG. Storage: Keystore only. Lifetime: unbounded (never deleted, even after `Committed`/`clear()`); scope: process-independent, per-app-uid. Persistence: Keystore. Recreation: whenever `getEntry(alias)` is not a `SecretKeyEntry` — including alias-type collision (then `generateKey()` **overwrites** the alias). Concurrency: no synchronization; two instances' first use race → second `generateKey` overwrites the first → the first's ciphertext becomes unauthenticable → `RegistrationSessionSecurityException` → synthetic `Failed` → restart allowed if not armed. Wipe: none. Relation to DeviceAuth: none cryptographically (correct); it protects the JKT/grant state the orchestrator relies on. Relation to K_STATE: separate alias (correct). Relation to DPoP: none.

## REGISTRATION SESSION KEY CREATION SEMANTICS
`decrypt()` (a read path, invoked by `FileRegistrationSessionStore.load()` → `RegistrationOrchestrator.currentState()`) calls `getOrCreateKey()` → **creates a new key when missing**, then fails GCM authentication with the wrong key. Net effect: a read (`currentState()`) silently changes Keystore security state and permanently converts a recoverable "key missing" condition into "envelope unauthenticable + new key exists". **ROOT-006 CONFIRMED, unchanged since Audit-001/002.** No getter rotates or destroys it. Cross-reference: ANOX-SECURITY-ARCH-007 was fixed in `CryptoBridge` but this identical anti-pattern remains (INEFFECTIVE_REMEDIATION scope-wise).

---

## DPOP HEADER
Exact generated header (harness, real `DpopProofFactory`):
`{"typ":"dpop+jwt","alg":"ES256","jwk":{"kty":"EC","crv":"P-256","x":"<43 b64url>","y":"<43 b64url>"}}` — public-only; Nimbus refuses private JWK in header (tested). Verifier: `typ` exact, `alg` ES256 only (alg=none/HS256 rejected), `jwk` present, EC, P-256, not private.

## DPOP CLAIMS

| Claim | Factory | Verifier | Classification |
|---|---|---|---|
| `jti` | always, 16 random bytes b64url | required, length ≥ 22 only | REQUIRED |
| `htm` | always, `uppercase()` | required, equality with `httpMethod.uppercase()` | REQUIRED (no method validation) |
| `htu` | always, `DpopHtu.normalize` | required, equality with normalized observed URI | REQUIRED (lossy canonicalization) |
| `iat` | always, seconds | required, ±120 s | REQUIRED |
| `nonce` | only if `nonce != null` | only if `expectedNonce != null` | OPTIONAL_BY_IMPLEMENTATION_ONLY (architecture: required at token issuance) |
| `ath` | only if `accessToken != null` | only if `accessToken != null` | OPTIONAL_BY_IMPLEMENTATION_ONLY (RFC §4.3 / B-002: required whenever a token is presented) |
| `jkt` binding | n/a | only if `expectedJwkThumbprint != null` | OPTIONAL_BY_IMPLEMENTATION_ONLY (architecture: token bound to key) |

Payload example: `{"htm":"POST","htu":"https://api.test/v1/res","iat":1760000000,"jti":"oiBRjhaSMDTwgebn9gnZ9A"}`.

## SECURE-DEFAULTS TABLE

| Default | Location | Classification |
|---|---|---|
| `expectedJwkThumbprint = null` | `DpopProofVerifier.verify` | **FAIL_OPEN** / UNSAFE_AT_B004 |
| `accessToken = null` (verifier) | same | **FAIL_OPEN** when a token is actually presented / UNSAFE_AT_B004 |
| `expectedNonce = null` | same | CONTEXT_DEPENDENT (FAIL_OPEN at token issuance) |
| `replayCache = InMemoryDpopReplayCache()` | verifier ctor | **FAIL_OPEN** across instances / UNSAFE_AT_B004 |
| `clock = SystemDeviceAuthClock` | factory/verifier/cache | CONTEXT_DEPENDENT (wall clock; see CANDIDATE-003) |
| `iatToleranceSeconds = 120` | verifier | SAFE (frozen) |
| `windowSeconds = 300` | cache | SAFE (frozen) |
| `accessToken = null`, `nonce = null` | `DpopProofFactory.createProof` | CONTEXT_DEPENDENT → UNSAFE_AT_B004 for token-bearing calls |
| `keyAlias = DEFAULT_KEY_ALIAS` | key manager | SAFE |
| `key = RegistrationSessionKey()` | `FileRegistrationSessionStore` | SAFE (alias) / creation semantics → ROOT-006 |
| `signer()` performs no eligibility check | key manager | CONTEXT_DEPENDENT (registration gates eligibility; a future direct auth call site would not) |
| HTTP method unvalidated | factory/verifier | CONTEXT_DEPENDENT (server sees real method) |

Answer to §24: **Yes** — production code can generate a syntactically valid, signed, insufficiently bound proof (`createProof(m, u)` without `ath` while sending `Authorization: DPoP <token>`), and the co-located verifier will accept it with its defaults.

## JWK VERDICT
Correct: `kty=EC`, `crv=P-256`, `x`/`y` base64url no padding, fixed 32-byte coordinates (harness found a key whose BigInteger `y` was 31 bytes → JWK still 32/32), public-only, private material structurally excluded by Nimbus + explicit `isPrivate` check.

## JKT VERDICT
Correct: Nimbus `computeThumbprint()` == manual RFC7638 (`{"crv":"P-256","kty":"EC","x":…,"y":…}` lexicographic, UTF-8, SHA-256, base64url no padding). Deterministic; no general serializer involved. Client (`DeviceAuthSigner.jwkThumbprint()`) and verifier (`ecKey.computeThumbprint()`) use the same routine.

## ES256 SIGNATURE VERDICT
Nimbus transcodes DER → fixed 64-byte `R||S` (harness: 64 bytes, first byte ≠ 0x30; raw JCA re-verification over the exact `BASE64URL(header).BASE64URL(payload)` bytes = true). Serialize-after-sign returns the same bytes (`SignedJWT.serialize()` uses the signed parts). Leading-zero R/S handled by library. **Keystore-provider DER path is instrumented-only, not CI-executed.**

---

## HTM VERDICT
`uppercase()` (Kotlin, locale-invariant) on both sides; no allow-list; empty string and arbitrary strings accepted (`""`→`htm:""`, `"p o s t\n"`→`"P O S T\n"`). Mismatch → `HTM_MISMATCH`. No security consequence server-side (method comes from the HTTP layer) — INFO, folded into the ROOT-009 canonicalization contract.

## HTU VERDICT
IMPLEMENTATION_DRIFT vs "RFC9449 `htu` semantics": decoded path, no default-port elision, no dot-segment/duplicate-slash normalization, userinfo retained, IDNA not normalized, `%2F`/`%3F`/`%23`/`%00` decoded into the signed claim. ROOT-009 CONFIRMED+EXPANDED. Fail-closed on syntactically invalid input.

## HTU COLLISION TESTS
See ROOT-009 above (8 COLLIDE rows, 12 distinct/fail-closed rows, 7 single-value probes) — executed against the real compiled `DpopHtu` class.

## CLIENT/SERVER CANONICALIZATION CONTRACT
No backend exists; **no contract is defined**. Required future verifier contract (to be frozen before B-004): compare `htu` against `lower(scheme) "://" lower(host) [":" port if non-default] rawPath` where `rawPath` is the request-target path **as received, percent-encoding preserved** (RFC 3986 §6.2.2.1 case-normalize hex digits and §6.2.2.2 decode only unreserved characters), no userinfo, no query/fragment, IDNA A-label host. Client canonicalization is currently **lossy** (`CLASSIFY: LOSSY_DECODING`) and must change in lock-step (MUST-FIX-TOGETHER).

---

## JTI VERDICT
`SecureRandom`, 128 bits, base64url no padding, 22 chars; 100 000 unique in harness; fresh per proof; no persistence; `FixedJtiGenerator` is test-only. Verifier accepts any ≥22-char string (22 spaces → Valid) — length is not entropy; unfixable server-side, INFO only.

## IAT / CLOCK VERDICT
`System.currentTimeMillis()`; seconds; UTC epoch; ±120 s enforced on both edges (verified). Same wall clock drives replay-cache eviction: **eviction after 300 s followed by verifier wall-clock rollback ≥ 60 s makes an evicted proof valid again** (harness: rollback −250 s → `Valid`). Client-side `iat` skew vs server is a normal DPoP `use_dpop_nonce`/`invalid_dpop` retry concern — no client clock-error handling exists yet (GAP-001).

## NONCE VERDICT
Claim supported end-to-end when supplied; **no nonce lifecycle on the client** (no `DPoP-Nonce` header capture, no storage/rotation, no `use_dpop_nonce` retry), no server nonce state anywhere. B-002 requires fresh nonce at token issuance and V1.2 defines `/v1/auth/challenge`. Classified GAP-001 (architecture/contract gap + B-004 activation hazard), verifier optionality is ROOT-008.

## ATH VERDICT
Correct hash (`base64url(SHA-256(ASCII(token)))`, 43 chars); constant-time compare; **optional by default** (ROOT-008). At B-004 every `Authorization: DPoP` request MUST make `ath` mandatory (RFC 9449 §4.3 step 12). `US_ASCII` encoding is lossy for non-ASCII tokens — not a finding (tokens are base64url).

---

## REPLAY CACHE
One implementation: `InMemoryDpopReplayCache` — owned per `DpopProofVerifier` instance (default ctor creates a private one); key = `jti` only; TTL 300 s from *record time*; no max entries; eviction = head-scan on insertion order (correct only if record timestamps are monotonic); `@Synchronized`; not persisted.

## REPLAY SCOPE
Per object instance, per process. Two verifiers each accept the same proof once (proved). Not per-user/device/JKT/endpoint: the same `jti` string from a different key or for a different endpoint is denied globally within one cache (harness) — acceptable given 128-bit random `jti` (not exploitable for denial), and consistent with RFC 9449 "SHOULD track jti (optionally with jkt)". ROOT-008 scope statement CONFIRMED.

## REPLAY ATOMICITY
`recordIfAbsent` is atomic per instance (200 rounds × 64 threads → exactly 200 accepts). The historical concern "check-then-insert non-atomic" is **CONTRADICTED for a single instance**; the real defect is scope, not atomicity.

## REPLAY TTL
Record lifetime (300 s) ≥ freshness window (240 s total) under a single monotonic clock: verified (`t=299` → `IAT_STALE`, not replay-window dependent; `t=300` evicted but `IAT_STALE`). Invariant **holds only while the verifier clock never moves backwards** (CANDIDATE-003).

## REPLAY PROCESS-RESTART LIMITATION
Nothing survives restart. This cache is a local/test foundation; authoritative replay enforcement MUST live server-side in shared storage (B-016 "cannot be process-local"). Android process persistence is irrelevant to server security and is not claimed.

---

## BACKEND-ABSENCE SECURITY LIMITATION
No token issuance, no session store, no nonce store, no replay store, no device registry, no HTTP transport, no server verifier exist. Every "verify" property proven here is proven for a **client-module copy of verifier logic** and constitutes zero enforcement against a malicious client. Trust boundary: CLIENT CREATES PROOF ↔ SERVER VALIDATES PROOF; client self-validation is not authentication.

## REQUIRED SERVER ENFORCEMENT
1. ES256 signature over embedded `jwk`; reject non-P-256, private material, alg≠ES256.
2. `jkt` binding: proof key thumbprint == `device_auth_keys.public_key` thumbprint bound to token/session/device — **mandatory, not optional**.
3. Device ownership: `AuthenticatedDeviceContext.device_id` derived from validated key, never from JSON.
4. Account/device record: `devices` ACTIVE uniqueness per account; `device_auth_keys.public_key` UNIQUE globally (prevents surviving-Keystore-key rebind after local marker loss); terminal on revoke.
5. One-device-only: DB constraint + commit race "one wins" (V1.2 §4).
6. `htm` equality; `htu` per the canonical contract above (raw-path compare).
7. `iat` ±120 s using a monotonic-safe server clock; reject missing/non-numeric.
8. `jti` replay: shared store keyed `(jti)` or `(jkt, jti)`, TTL ≥ 300 s and ≥ freshness window, atomic `SET NX`-style insert, bounded (per-key rate limit) and evicted by insertion time from a monotonic source.
9. Nonce: issue at `/v1/auth/challenge` and via `DPoP-Nonce` header, bind to (device/jkt, endpoint class), single-use/short TTL, `use_dpop_nonce` error class.
10. `ath` mandatory on every `Authorization: DPoP` request; token hash lookup only.
11. Entitlement/device status/revocation checks after PoP (pipeline order V1.2 §1).
12. Registration PoP: bind proof to `registration_id` + grant + fresh nonce; compare `jwk` in proof == submitted `publicJwk`; PoP again at commit.

## BACKEND CONTRACT GAPS

| Required future server invariant | Client dependency | Defined in architecture? | Implementation status | Class |
|---|---|---|---|---|
| Registration PoP payload/binding (what the `submit-device-auth` proof signs; nonce; grant binding) | `createDeviceAuthProof` lambda shape, `registerDeviceAuth(publicJwk, dpopProof)` | Only "with PoP" (B-003); table says DPoP=No for submit-device-auth, PoP+DPoP=Yes for commit (V1.2) | not implemented; **client drifts** | CURRENT_CLIENT_DEFECT + ARCHITECTURE_GAP (CANDIDATE-001) |
| PoP + DPoP + Idempotency-Key at `/v1/registration/commit` | `commitRegistration(id, grant)` has neither | YES (V1.2 §2) | client lacks | CURRENT_CLIENT_DEFECT (CANDIDATE-001) |
| Shared replay store, TTL, atomicity, bound | none | YES (B-002/B-016) | absent | SERVER_PREREQUISITE (ROOT-008) |
| Mandatory jkt/ath/nonce checks | verifier defaults | YES (B-002) | optional in client copy | SERVER_PREREQUISITE + client verifier defect (ROOT-008) |
| `htu` canonical form | `DpopHtu` | "RFC9449 semantics" only | undefined | ARCHITECTURE_GAP (ROOT-009 coupling) |
| Nonce challenge lifecycle (`/v1/auth/challenge`, `DPoP-Nonce`, `use_dpop_nonce`) | no client handling | endpoint named only | absent | ARCHITECTURE_GAP (GAP-001) |
| `device_auth_keys.public_key` UNIQUE; JKT→device_id binding; rejection of re-registration of a known key | none possible | implied by one-device; not explicit | absent | SERVER_PREREQUISITE (GAP-003) |
| Monotonic clock for replay eviction | none | not stated | absent | SERVER_PREREQUISITE (CANDIDATE-003) |
| Hardware-level assertion trust model (no attestation) | `HardwareSecurityLevel` self-report | B-002 says no attestation | server cannot verify | SERVER_PREREQUISITE / ANOX-SECURITY-ARCH-006 |

---

## REGISTRATION FLOW
```
App (B-004 caller, not yet existing)
→ RegistrationOrchestrator.reserve(username, license)          [state Reserved; grant sealed by RegistrationSessionKey]
→ registerDeviceAuth()
    ├ currentState()  → FileRegistrationSessionStore.load() → RegistrationSessionKey.decrypt() [creates key if missing — ROOT-006]
    ├ status(): key? marker? → TerminalKeyLoss ⇒ Failed (session preserved)
    ├ createKeyIfAbsent() → generateKey(StrongBox → catch → deleteEntry → TEE)   [security state created]
    ├ signer() → JWK/JKT
    ├ isProductionEligible() gate (client-only)
    ├ proof = createDeviceAuthProof(registrationId)  [opaque; content unspecified — CANDIDATE-001]
    ├ api.registerDeviceAuth(id, grant, publicJwk, proof)  [future backend]
    └ Accepted ⇒ DeviceAuthRegistered(thumbprint) saved; Rejected ⇒ Failed saved (grant discarded)
→ uploadPublicIdentity() → CryptoBridge (E2EE) → api.submitPublicIdentity(id, grant, material)  [no JKT/PoP]
→ commit()
    ├ validateDeviceAuthForCommit(thumbprint)  [key present, eligible, same JKT]
    ├ sessionStore.save(CommitArmed)  → fail ⇒ Failed (session unchanged)
    ├ bindingStore.markArmed()        → fail ⇒ Failed (CommitArmed durable; no downgrade — LEGACY-INTEGRATION-003 fix)
    ├ api.commitRegistration(id, grant)  [no PoP/DPoP/Idempotency-Key — drift vs V1.2]
    ├ exception ⇒ Failed, armed stays (retry same key)
    ├ Committed ⇒ markBound() → save(Committed) → clear()   [device_id discarded locally]
    └ Rejected ⇒ Failed saved; installation remains armed forever (documented; storage handoff)
```
Security-state creation/change points: Keystore EC key (step 2), RegistrationSessionKey (any load/save), binding marker (arm/bound), session file (every step).

## PARTIAL-FAILURE ANALYSIS
- Key created, server never reached → unbound key persists; reused on retry (JKT stable) — correct.
- RegistrationSessionKey created, envelope lost/corrupt → `Failed` synthetic; new registration allowed unless armed/bound → new Device Auth key **only if** the old one is absent (else same key reused). Combined with marker loss this is ROOT-007 (storage).
- Proof created, request "sent", server accepted `submit-device-auth`, client sees exception → state stays `Reserved` (exception propagates uncaught); retry re-submits **same JWK** with a new proof — server must be idempotent on `(registration_id, jkt)`. Not specified (GAP-002).
- Server committed, client died before `markBound` → armed ⇒ retry `commit()` with same grant; server must be idempotent (B-003 "commit is idempotent"). Local persistence failure after `markBound` → bound marker already durable — correct ordering.
- `Rejected` at commit after arming → permanently armed, no new registration possible on this installation without explicit local reset (`clearBinding`). Known (C-016 Audit-002 / storage).

## RETRY SEMANTICS
Per authority: reuse device key and JKT (yes — same alias), reuse registration grant for idempotent retry (V1.2 §DB races: "Idempotent retry uses same registration grant") — **client discards the grant on any `Rejected`** (state → `Failed`), forcing a new reservation; fresh `jti` per attempt (yes); new nonce per attempt (undefined — GAP-001); new server registration session only after `Expired`/`Failed`. Transient-vs-permanent rejection is indistinguishable in `RegistrationApi` (single `Rejected(reason)`), so retry policy is `ARCHITECTURE_GAP` (GAP-002). Not invented here.

---

## LOGGING / SECRET EXPOSURE
No `Log.*`/`println`/`printStackTrace`/Timber in `android/src/main`. `RegistrationGrant.toString()` redacted; data-class `toString` of states embeds it redacted. Exceptions contain: hardware level, thumbprints (public), registration/device UUIDs, usernames, constant messages; never grant, token, proof, or key bytes. `RegistrationSessionSecurityException` wraps `cause` (e.g., `AEADBadTagException`) — no secret content. `DpopRejectionReason` enum is log-safe. Crash-report risk: `RegistrationState.Failed(reason)` strings persist server-supplied `reason` text into the encrypted store only.

## ERROR TAXONOMY
Distinguishable: `MALFORMED`, `INVALID_TYP`, `UNSUPPORTED_ALG`, `INVALID_JWK`, `PRIVATE_KEY_IN_JWK`, `INVALID_SIGNATURE`, `KEY_BINDING_MISMATCH`, `HTM_MISMATCH`, `HTU_MISMATCH`, `MISSING_IAT`, `IAT_STALE`, `IAT_FUTURE`, `INVALID_JTI`, `REPLAYED_JTI`, `MISSING_ATH`, `ATH_MISMATCH`, `MISSING_NONCE`, `NONCE_MISMATCH`; `DeviceAuthTerminalStateException`, `DeviceAuthNotProductionEligibleException`, `RegistrationSessionSecurityException`, `IllegalArgumentException` (bad URI). Not distinguishable: "key unavailable" vs "Keystore failure" (both → absent → resolver), malformed-URI vs wrong-URI (`HTU_MISMATCH` covers both), signing failure (raw `JOSEException`), Keystore alias-type collision, RegistrationSessionKey missing vs corrupt envelope (both → "could not be authenticated"). Server-only classes (`nonce required`, revocation) correctly not modelled yet.

## FAIL-CLOSED BEHAVIOR
Fail-closed: all verifier paths return `Invalid`; `DpopHtu` throws on invalid input; `createProof` throws on signing failure (no `runCatching`); marker corrupt ⇒ bound+armed; `failStep` never downgrades in-progress state; `UNKNOWN` hardware ⇒ ineligible. Fail-open: verifier/factory optional bindings (ROOT-008); `decrypt()` creates key (ROOT-006); empty session file ⇒ `NotStarted` and absent marker ⇒ unbound (ROOT-007, storage); StrongBox `catch(Exception)` deletes alias then retries (CANDIDATE-002). No path yields a *weaker but still generated* proof except by caller omission.

## DIRECT API BYPASS
All classes are Kotlin-public within `:android`. Any caller can: construct `DpopProofFactory` with a non-Keystore `DeviceAuthSigner` (server cannot detect without attestation — ARCH-006); call `keyManager.signer()` without `isProductionEligible()`; call `deleteKeyDestructively()`/`clearBinding()`; construct `DpopProofVerifier()` with defaults. The fundamental verifier API is **not safe by construction** (ROOT-008) — analogous to the prior native-bypass finding. The key-manager API *is* safe by construction for terminal loss (guard inside `createKeyIfAbsent`, not only in the orchestrator).

---

## TEST EXECUTION
```
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"   (OpenJDK 21.0.9)
./gradlew --offline --no-daemon :android:testDebugUnitTest \
    --tests 'com.anox.messenger.security.deviceauth.*' --tests 'com.anox.messenger.account.*'
BUILD SUCCESSFUL in 17s
Executed 173  Passed 173  Failed 0  Errors 0  Skipped 0   (deviceauth 69, account 104; timestamps 2026-09-12T08:18Z)
```
Instrumented (27) and hardware/StrongBox: **NOT_RUN** (no device/emulator authorized). No results fabricated.

Harness (`/tmp/anox_auth_dpop_harness/Harness.java`, `Size.java`) compiled against `android/build/tmp/kotlin-classes/debug` + `nimbus-jose-jwt-10.9.1` + `kotlin-stdlib-2.2.21`; output preserved at `/tmp/anox_auth_dpop_harness/out.txt`.

## ADVERSARIAL ANALYSIS

| # | Case | Result |
|---|---|---|
| 1 | same JTI twice, one verifier | 2nd → `REPLAYED_JTI` ✓ |
| 2 | same JTI through two cache instances | both accept ✗ (ROOT-008) |
| 3 | 64 threads × 200 rounds same JTI | exactly 200 accepts ✓ atomic |
| 4 | missing `htu` claim | `HTU_MISMATCH` ✓ (existing test) |
| 5 | missing `htm` | `HTM_MISMATCH` ✓ |
| 6 | wrong HTU / wrong host | `HTU_MISMATCH` ✓ |
| 7 | encoded-path variants | `a%2Fb` proof accepted for `/a/b` ✗ (ROOT-009); `%3F`,`%23`,`%00` decoded ✗ |
| 8 | default-port variant `:443` | `HTU_MISMATCH` (fail-closed interop) |
| 9 | method case / arbitrary / empty | case-insensitive ✓; `""` and `"P O S T\n"` accepted (info) |
| 10 | IAT −121 / +121 | `IAT_STALE` / `IAT_FUTURE` ✓; ±120 accepted ✓ |
| 11 | verifier clock rollback after eviction | evicted proof **accepted again** ✗ (CANDIDATE-003) |
| 12 | malformed JWK (short x, y=x, P-384, RSA, extra byte, off-curve y=0) | all `MALFORMED` ✓ |
| 13 | leading-zero coordinate / ECDSA R‖S | JWK 32/32 ✓; signature 64 B ✓; JCA re-verify ✓; malleated (n−s) → `REPLAYED_JTI` (jti identity, not bytes) ✓ |
| 14 | signing failure | `JOSEException` propagates; no fallback (source) ✓ |
| 15 | missing Keystore alias | `loadPrivateKeyOrNull`→null→resolver; bound ⇒ Terminal (source + inst. test) ✓ |
| 16 | RegistrationSessionKey missing during read | **key created on read**, envelope then unauthenticable (source) ✗ ROOT-006 |
| 17 | process restart replay state | cache lost; server prerequisite (source) |
| 18 | two simultaneous `createKeyIfAbsent()` | check-then-act; `generateKeyPair` overwrites alias; StrongBox-catch deletes peer's key (source) ✗ CANDIDATE-002 |
| 19 | minimal `verify()` with attacker key | `Valid` ✗ ROOT-008; with `expectedJkt` → `KEY_BINDING_MISMATCH` ✓ |
| 20 | replay cache 1,000,000 unique jti | all retained, no cap (ROOT-008 C-019) |
| 21 | proof carries unexpected nonce | accepted when `expectedNonce=null` (RFC-consistent) |
| 22 | jti = 22 spaces | accepted (length-only; INFO) |

## SECURITY PROPERTY MATRIX

| Property | Architecture | Source enforcement | JVM proof | Instrumented | Physical | Server | Status |
|---|---|---|---|---|---|---|---|
| Private key non-exportability | B-002 | Keystore handle only | partial (JWK no `d`) | `privateKeyIsNotExportable` (not CI) | required | n/a | SOURCE_VERIFIED / PHYSICAL_PENDING |
| Hardware backing (TEE) | B-002 | `KeyInfo` policy | policy only | consistency only | **required** | cannot verify (no attestation) | PHYSICAL_VERIFICATION_REQUIRED |
| StrongBox | preferred | requested + fallback | none | none | required | n/a | PHYSICAL_VERIFICATION_REQUIRED |
| JKT correctness | RFC7638 | Nimbus | harness ✓ | — | — | must recompute | VERIFIED |
| JOSE signature correctness | ES256 | Nimbus transcoding | harness ✓ (JCA key) | `keystoreBackedProofVerifiesEndToEnd` (not CI) | Keystore DER path | must verify | VERIFIED (JVM) / INSTRUMENTED_PENDING |
| HTM binding | RFC | equality | ✓ | — | — | required | VERIFIED (weak validation) |
| HTU binding | RFC9449 | lossy | 7 happy | — | — | contract missing | DRIFT (ROOT-009) |
| JTI uniqueness | ≥128 b | CSPRNG | ✓ | — | — | replay store | VERIFIED |
| IAT freshness | ±120 s | ✓ | ✓ | — | — | required | VERIFIED |
| Replay prevention | shared 5 m | per-instance | ✓ per instance | — | — | **required** | FOUNDATION_ONLY (ROOT-008) |
| Nonce binding | fresh at issuance | optional | ✓ when supplied | — | — | required | GAP |
| ATH binding | when token | optional | ✓ when supplied | — | — | required mandatory | FAIL_OPEN_DEFAULT (ROOT-008) |
| One-device-only | Inv.2 | local guard only | ✓ local | — | — | **required** | SERVER_PREREQUISITE |
| Device/account binding | V1.2 | JKT in state only | ✓ | — | — | required | SERVER_PREREQUISITE + CANDIDATE-001 |
| RegistrationSessionKey lifecycle | Inv.23 | create-on-read | none | none delete alias | — | n/a | DRIFT (ROOT-006) |
| Terminal loss / no regeneration | B-002 | resolver + marker | ✓ 17 | ✓ 7+10 (not CI) | marker durability | server device record | VERIFIED (logic) / ROOT-007 for durability |

## PHYSICAL EVIDENCE REQUIREMENTS

| Requirement | Procedure (defensive, high level) |
|---|---|
| StrongBox key on GrapheneOS Pixel | Install debug build on a StrongBox-capable Pixel running GrapheneOS; run `AndroidKeystoreDeviceAuthKeyManagerTest`; record `KeyInfo.securityLevel == STRONGBOX`; repeat on non-StrongBox device and confirm TEE fallback with `Present(TRUSTED_EXECUTION_ENVIRONMENT)`. |
| Non-exportability | On device, assert `privateKey.encoded == null`, `KeyFactory.getKeySpec(.., ECPrivateKeySpec)` throws. |
| Keystore DER→JOSE on real provider | Run `keystoreBackedProofVerifiesEndToEnd` on device; additionally verify proof with an independent verifier (e.g., server-side lib) to exclude Nimbus self-consistency. |
| Key survival across app-data-clear / reinstall / OS update | Create key + mark bound; `pm clear`; observe status; reinstall; observe; confirm `AbsentNotBound` only when both key and marker are gone; record any case where key survives but marker does not (drives server JKT-uniqueness requirement). |
| Work/secondary profile isolation | Install in second user profile; confirm separate alias namespace and separate `noBackupFilesDir`. |
| Invalidation semantics | With `setUserAuthenticationRequired(false)` no biometric invalidation expected; confirm on lock-screen removal/change. |
| Wall-clock behaviour | Change device time ±10 min; confirm proofs rejected server-side and that nonce/retry path (once defined) recovers. |

---

## HISTORICAL FINDING REVALIDATION

| Historical finding | Historical status | Current relation | Current evidence | Action |
|---|---|---|---|---|
| `ANOX-LEGACY-INTEGRATION-001` (key not re-verified before arm/commit) | Closed (LEGACY-FIX-01) | **PARTIALLY_EFFECTIVE** | `validateDeviceAuthForCommit` present and tested (4 tests); but the finding's own note "commitRegistration API takes no new Device Auth proof" was **not** remediated and now conflicts with V1.2 §2 (PoP+DPoP at commit) | keep Closed; relate to CANDIDATE-001 |
| `ANOX-LEGACY-INTEGRATION-003` (CommitArmed vs armed flag divergence) | Closed | STILL_EFFECTIVE | `expiredOrNull` returns null for `CommitArmed`; `canStartNew` excludes it; tests `commitArmed …` ×3 pass | none |
| `ANOX-MAINARCH-019` (eligibility not enforced at call site) | Closed | STILL_EFFECTIVE | enforced at `:105` and `:323`; 4 JVM tests | none |
| `ANOX-MAINARCH-008` (server DPoP trust delegated to B-004) | Closed (doc remediation) | STILL_EFFECTIVE (doc) / RELATED_NEW_ROOT_CAUSE | V1.2 defines schema/pipeline; nonce/htu/registration-PoP contracts still absent → GAP-001/002, CANDIDATE-001 | keep Closed; gaps tracked separately |
| `ANOX-MAINARCH-018` (StrongBox physical) | Open | PHYSICAL_REVALIDATION_REQUIRED | no physical evidence at this SHA | unchanged |
| `ANOX-SECURITY-ARCH-006` (no server validation of hardware level) | Open | STILL_EFFECTIVE (Open) | no attestation; self-reported level | unchanged; SERVER_PREREQUISITE |
| `ANOX-SECURITY-ARCH-003` (registration fail-closed gaps) | Open | RELATED_NEW_ROOT_CAUSE | CANDIDATE-001 (PoP contract), GAP-002 (retry) | expand at consolidation |
| `ANOX-SECURITY-ARCH-007` (getOrCreateStateKey) | Open | INEFFECTIVE_REMEDIATION (scope) | fixed in `CryptoBridge`; identical pattern remains in `RegistrationSessionKey.decrypt` | ROOT-006 |
| `ANOX-SECURITY-ARCH-008` / `ANOX-LEGACY-B003-001` (UUID variant) | Open | STILL_EFFECTIVE (Open) | `UuidV4.parse` checks version only | ROOT-015, unchanged |
| `ANOX-MAINARCH-014` (restricted Device-Auth flow) | Closed (doc) | NO_LONGER_APPLICABLE to client code | no client implementation yet | none |
| Consensus `ROOT-006` | ACTIVE MEDIUM | CONFIRMED (+ creation-race expansion) | `RegistrationSessionKey.kt:58,63-69` unchanged | storage handoff |
| Consensus `ROOT-007` | ACTIVE MEDIUM | CONFIRMED (adjacent) | `FileRegistrationSessionStore.kt:44`, marker absent ⇒ unbound, `clearBinding` public | storage handoff |
| Consensus `ROOT-008` | ACTIVE MEDIUM/HIGH@B004 | CONFIRMED + EXPANDED | see §ROOT-008 | no re-severity |
| Consensus `ROOT-009` | ACTIVE MEDIUM | CONFIRMED + EXPANDED | see §ROOT-009 | no re-severity |
| Consensus `ROOT-016` | REJECTED | **NOT revived** | CANDIDATE-002 concerns a *pre-binding* concurrent-creation race, not destruction of a bound key; the `Present` early-return guard still protects bound keys | remains rejected |
| Audit-002 `C-014` (concurrency gaps) | ACCOUNTED_FOR (ROOT-002/017, derived) | RELATED_NEW_ROOT_CAUSE | CANDIDATE-002 gives it a concrete DeviceAuth root cause | consolidation |
| Audit-001 `CS-019` replay-cache growth | ROOT-008 component | CONFIRMED | 1,000,000 entries retained | none |

## INEFFECTIVE HISTORICAL REMEDIATIONS
- `ANOX-SECURITY-ARCH-007` remediation not applied to `RegistrationSessionKey` (ROOT-006 persists).
- `ANOX-LEGACY-INTEGRATION-001` remediation addressed local revalidation only; commit-step PoP absence persists (now a V1.2 drift).

## STILL-EFFECTIVE HISTORICAL REMEDIATIONS
`ANOX-LEGACY-INTEGRATION-003`, `ANOX-MAINARCH-019`, `ANOX-MAINARCH-005` (P-256/ES256 direction implemented), `ANOX-MAINARCH-008` (documentation layer).

---

## AUDIT-LOCAL FINDINGS

### TOTAL
3 candidates + 3 architecture gaps

### CRITICAL
0

### HIGH
0

### MEDIUM
1 — `ANOX-AUTHDPOP-CANDIDATE-001`

### LOW
2 — `ANOX-AUTHDPOP-CANDIDATE-002`, `ANOX-AUTHDPOP-CANDIDATE-003`

### INFO
0 candidates (INFO observations folded into ROOT-009 expansion: HTM validation, length-only jti, US_ASCII `ath`)

---

## FINDINGS TABLE

| Candidate | Severity | Confidence | Root cause | Authority | Exact evidence | Consensus relation | Historical relation | Reachability | Activation | Blocks | Fix group | Retest |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **ANOX-AUTHDPOP-CANDIDATE-001** — Registration proof-of-possession contract undefined and client API drifts from V1.2 (no PoP/DPoP/Idempotency at commit; opaque untyped registration proof; JWK and proof independently supplied) | MEDIUM | HIGH | Registration PoP wire contract exists only as an endpoint-table row; client shaped before V1.2 | V1.2 §2 endpoint table (`commit`: Auth=PoP, DPoP=Yes, Idempotency=Yes), V1.1 B-003 §3, B-003 v1.4 | `RegistrationOrchestrator.kt:46` `createDeviceAuthProof: (RegistrationId) -> String`; `:114`; `RegistrationApi.kt:30-35,48-51`; tests forward literal `"fake-dpop-proof-for-…"` | RELATED to ROOT-008 family (binding optional), distinct root cause | PARTIALLY_EFFECTIVE `ANOX-LEGACY-INTEGRATION-001`; expands `ANOX-SECURITY-ARCH-003` | DEAD_OR_UNWIRED | B-004 registration endpoints | **B004 = YES** (contract must be frozen before implementation) | AD-F (+AD-B) | JVM: orchestrator supplies typed proof bound to registration_id+grant+nonce+JWK at submit **and** commit; contract doc validator |
| **ANOX-AUTHDPOP-CANDIDATE-002** — Device Auth key creation not serialized; `generateKeyPair()` overwrites existing alias; StrongBox-fallback `catch(Exception)` deletes alias unconditionally | LOW | HIGH | check-then-act in `createKeyIfAbsent` + Keystore alias overwrite semantics | B-002 (no silent key replacement), Inv.23 | `AndroidKeystoreDeviceAuthKeyManager.kt:48-57,106-118`; no lock; `RegistrationOrchestrator` unsynchronized | RELATED_NEW_ROOT_CAUSE for Audit-002 C-014 (ACCOUNTED_FOR, ROOT-002 family); **does not revive ROOT-016** (pre-binding only; bound keys still guarded) | C-014 | DEAD_OR_UNWIRED | B-004 (any concurrent caller) | B004 = NO (NON_BLOCKING; fix with AD-A) | AD-A | JVM: injectable Keystore double with concurrent `createKeyIfAbsent`; instrumented alias-overwrite test |
| **ANOX-AUTHDPOP-CANDIDATE-003** — Replay-cache eviction and `iat` freshness share a wall clock; verifier clock rollback after eviction re-enables replay; eviction algorithm assumes monotonic insertion timestamps | LOW | HIGH (reproduced) | time-source design: wall clock used for both freshness and retention | B-002 (replay cache 5 m), Inv.18 | `InMemoryDpopReplayCache.kt:38-56`, `DeviceAuthClock.kt:17`; harness rollback −250 s ⇒ `Valid` for previously-consumed jti | ADJACENT to ROOT-008 (scope) — distinct root cause (time source), not restated | none | TEST_ONLY (server-side risk) | B-004 backend verifier if this design is ported | B004 = NO (SERVER_PREREQUISITE; must be in verifier contract) | AD-D | JVM: rollback test; server verifier uses monotonic retention or iat-based expiry |

Architecture gaps (not client defects, must enter the coverage gate):

| Gap | Statement | Gate |
|---|---|---|
| `ANOX-AUTHDPOP-GAP-001` | Nonce lifecycle unspecified: `/v1/auth/challenge` semantics, `DPoP-Nonce` header, `use_dpop_nonce` retry, nonce scope/TTL, client storage — nothing on client, nothing in contract | PRE-B004 (contract), B-004 (impl) |
| `ANOX-AUTHDPOP-GAP-002` | Server verifier contract absent: canonical `htu` form, replay key `(jkt,jti)` vs `jti`, TTL/monotonic source, mandatory `ath`/`jkt`, registration PoP idempotency on `(registration_id, jkt)`, transient-vs-permanent rejection classes for client retry | PRE-B004 |
| `ANOX-AUTHDPOP-GAP-003` | Device/JKT/account server binding invariants not explicit: `device_auth_keys.public_key` UNIQUE, JKT→`device_id` immutability, rejection of known-key re-registration after local marker loss, `device_id` not retained locally | PRE-B004 (schema/contract) |

## NEW ROOT-CAUSE CANDIDATES
`ANOX-AUTHDPOP-CANDIDATE-001`, `-002`, `-003`.

## CONFIRMED CONSENSUS ROOTS
`ROOT-006` (unchanged at this SHA), `ROOT-007` (adjacent components present), `ROOT-008`, `ROOT-009`.

## EXPANDED CONSENSUS ROOTS
`ROOT-008` (client factory defaults mirror verifier defaults; default-ctor verifiers share nothing), `ROOT-009` (`%3F`/`%23`/`%00` decoding, double-decoding, userinfo in signed claim, HTM unvalidated as part of the same canonicalization-contract gap), `ROOT-006` (RegistrationSessionKey first-use creation race / alias-type overwrite).

## CONTRADICTED CONSENSUS ROOTS
None. (Sub-claim contradicted: replay check-and-insert **is** atomic per instance; the defect is scope only.)

## REJECTED / NOT FINDINGS
- jti-only replay key causing cross-key denial — not exploitable (128-bit random jti); RFC-consistent.
- Length-only `jti` check — entropy unverifiable by any verifier; INFO.
- `ath` US_ASCII lossiness — tokens are base64url ASCII.
- Unexpected `nonce` accepted when none expected — RFC-consistent.
- Key attestation absence — not required by B-002 v1.1.
- Keystore deletion from StrongBox `catch` as destruction of a **bound** key — remains ROOT-016 REJECTED (guard verified).
- `signer()` lacking eligibility gate — hardware level cannot change after creation; registration gate suffices.

---

## PRE-B004 AUTH/DPOP BLOCKERS
Consensus roots: `ROOT-006`, `ROOT-007`, `ROOT-008`, `ROOT-009` (all already in the 12-root set).
New: `ANOX-AUTHDPOP-CANDIDATE-001`.
Architecture gaps: `ANOX-AUTHDPOP-GAP-001`, `GAP-002`, `GAP-003` (contracts must be frozen before B-004 implementation starts; Inv. 35).

## LATER-GATE AUTH/DPOP ITEMS
- `ANOX-AUTHDPOP-CANDIDATE-002` — fix inside AD-A during B-004 Device-Auth wiring; activation requires a concurrent caller, which does not exist until B-004 (NON_BLOCKING).
- `ANOX-AUTHDPOP-CANDIDATE-003` — server verifier implementation gate (B-004 backend); recorded in GAP-002 contract now.
- Physical StrongBox/TEE/Keystore semantics (`ANOX-MAINARCH-018`) — Final Product Gate on provenance-verified binary.
- Logout/wipe/revoke Device-Auth behaviour — B-013 lifecycle gate.
- Instrumented DeviceAuth suites in CI — ROOT-017 track.

## MUST-FIX-TOGETHER
1. **ROOT-008 ∧ all B-004 DPoP call sites ∧ GAP-002**: make `jkt`/`ath`/replay-cache constructor-mandatory (no defaults) *and* update every factory/verifier call site *and* freeze the server contract.
2. **Replay-cache ownership ∧ atomicity ∧ time source (ROOT-008 ∧ CANDIDATE-003)**: shared store + atomic insert + monotonic/iat-based retention in one change.
3. **ROOT-009 ∧ GAP-002 canonical `htu`**: client `DpopHtu` (raw path, port elision, no userinfo) and server comparison rule change in lock-step; `DpopHtuTest` gains the collision rows.
4. **ROOT-006 ∧ consumer error handling**: split `RegistrationSessionKey` into existing-only read / create-on-write *and* make `FileRegistrationSessionStore.load` distinguish "key missing" (terminal/audit) from "envelope corrupt"; together with ROOT-007 three components.
5. **CANDIDATE-001 ∧ GAP-003 ∧ GAP-001**: registration PoP payload (registration_id + grant hash + nonce + JWK) at submit **and** commit, idempotency key, server binding of JKT→device_id — one contract.
6. **CANDIDATE-002 ∧ AD-A**: serialize key creation, never `generateKeyPair` on an existing alias, StrongBox failure must not delete an entry it did not create.

## MUST-NOT-FIX-ALONE
- Passing `expectedJwkThumbprint` at one call site while `verify()` keeps nullable defaults → false closure of ROOT-008.
- Making the replay cache global/shared while leaving wall-clock retention (CANDIDATE-003) → replay after clock adjustment.
- Changing `DpopHtu` to raw path without freezing the server rule → fail-closed outage or new collisions.
- Adding client-only one-device/JKT checks without `device_auth_keys` uniqueness → false enforcement.
- Adding a `nonce` field/plumbing without server nonce state/`use_dpop_nonce` → dead field, false coverage.
- Adding a PoP parameter to `commitRegistration` without defining what it signs → untestable contract.

## PROPOSED REMEDIATION GROUPS
- **AD-A** Device-key lifecycle: serialized `createKeyIfAbsent`, alias-existence check before generation, StrongBox fallback without unconditional delete, eligibility signalled on fallback (CANDIDATE-002).
- **AD-B** DPoP proof contract: mandatory bindings by type (`DpopBinding(jkt, tokenHash?, nonce?)` non-null where required), factory requires token for token-bearing requests, no default replay cache (ROOT-008).
- **AD-C** HTU/HTM canonicalization contract + tests (ROOT-009, GAP-002 part).
- **AD-D** Replay/JTI/time/nonce: shared store interface with `(jkt, jti)` key, monotonic/iat retention, nonce lifecycle (CANDIDATE-003, GAP-001, ROOT-008 scope).
- **AD-E** RegistrationSessionKey lifecycle: existing-only read path, explicit key-missing exception, coordinated with ROOT-007 storage fixes (ROOT-006).
- **AD-F** Device/account/JKT/server-binding contract: registration PoP at submit+commit, idempotency, JKT uniqueness, device_id retention policy (CANDIDATE-001, GAP-003).

## REQUIRED REMEDIATION ORDER
Contracts first (AD-C rule, AD-D nonce/replay spec, AD-F PoP spec → freeze as B-spec amendment) → AD-B (API hardening, compiles call sites) → AD-C client change → AD-D client plumbing → AD-E with ROOT-007 storage group → AD-A → independent retest (JVM adversarial suite incl. collision rows, two-verifier replay, rollback, concurrency) → instrumented Keystore suite in CI → physical StrongBox campaign on provenance-verified binary.

---

## SEC-A
AD-A, AD-C, AD-E (component-local corrections, no trust-boundary change).

## SEC-B
AD-B, AD-D, AD-F (API-contract and cross-component changes touching the client↔server security contract; no systemic redesign).

## SEC-C REQUIRED
**NO** — the frozen trust model (Keystore-bound non-exportable P-256, DPoP, server-derived identity, no recovery) is correct; defects are contract completeness and default-safety, not invariant redesign.

## ARCHITECTURE VERDICT
**`COMPONENT_INTERNAL_REDESIGN_ONLY`** — verifier/factory API must become safe-by-construction, canonicalization and registration PoP contracts must be written, replay design must specify scope/time source; the B-002/B-004 trust boundary itself stands.

---

## ANDROID/STORAGE HANDOFF
ROOT-006 (`RegistrationSessionKey` create-on-read + first-use race), ROOT-007 (empty session file ⇒ `NotStarted`, absent marker ⇒ unbound, no directory fsync in `AtomicFileWriter`/`AtomicFile`, `clearBinding()`/`deleteKeyDestructively()` public), permanently-armed installation after commit `Rejected`, wipe/logout primitives and `.tmp` residue, Keystore survival vs app-data-clear/reinstall/profile (physical), anti-rollback of session envelope (version byte outside AAD).

## ATTACKCHAIN HANDOFF
- HTU decoded-path collision (ROOT-009) × unbound verifier default (ROOT-008) → proof minted for one route accepted for another, by any key.
- Optional `ath` (ROOT-008) × stolen bearer token → token replay without key possession.
- Per-instance replay cache (ROOT-008) × multi-replica backend (B-016) × wall-clock rollback (CANDIDATE-003) → bounded replay windows.
- Marker loss (ROOT-007) × RegistrationSessionKey regeneration (ROOT-006) × missing JKT-uniqueness (GAP-003) → second key bound to a new account while the old key/account survive server-side.
- Concurrent key creation (CANDIDATE-002) × registration PoP not re-checked at commit (CANDIDATE-001) → JKT submitted ≠ key present at commit (currently caught client-side only).

---

## REMEDIATION COVERAGE METADATA

**ANOX-AUTHDPOP-CANDIDATE-001**
SOURCE: AUDIT-SECURITY-AUTH-DPOP-001 · ROOT_CAUSE: registration PoP contract undefined; client API predates V1.2 · AFFECTED_CODE: `RegistrationOrchestrator.kt:46,114`, `RegistrationApi.kt:30-51`, `RegistrationOrchestratorTest.kt`, `RegistrationCrashConsistencyTest.kt` · AFFECTED_ARCHITECTURE: V1.2 §2 endpoint table, B-003 v1.5, B-002 · FIX_GROUP: AD-F (+AD-B) · PRE_B004_OR_LATER: PRE_B004 · REQUIRED_TEST: typed PoP bound to registration_id/grant/nonce/JWK at submit and commit; idempotency key present; JWK-in-proof == submitted JWK · INDEPENDENT_RETEST_OWNER: next AUTH/DPoP retest session (not the implementer) · DEPENDENCIES: GAP-001, GAP-003, ROOT-008 · DISPOSITION: OPEN_PENDING_CONSOLIDATION

**ANOX-AUTHDPOP-CANDIDATE-002**
SOURCE: AUDIT-SECURITY-AUTH-DPOP-001 · ROOT_CAUSE: non-serialized check-then-act key creation + alias overwrite + unconditional delete in StrongBox fallback · AFFECTED_CODE: `AndroidKeystoreDeviceAuthKeyManager.kt:48-57,106-118` · AFFECTED_ARCHITECTURE: B-002 (no silent replacement), Inv.23 · FIX_GROUP: AD-A · PRE_B004_OR_LATER: LATER (fix within B-004 Device-Auth wiring; NON_BLOCKING) · REQUIRED_TEST: concurrent `createKeyIfAbsent` yields one key; StrongBox failure never deletes a pre-existing alias; instrumented alias-overwrite negative test · INDEPENDENT_RETEST_OWNER: ANDROID/STORAGE or AUTH retest session · DEPENDENCIES: C-014 (Audit-002), ROOT-017 (instrumented CI) · DISPOSITION: OPEN_PENDING_CONSOLIDATION

**ANOX-AUTHDPOP-CANDIDATE-003**
SOURCE: AUDIT-SECURITY-AUTH-DPOP-001 · ROOT_CAUSE: wall clock shared by freshness and retention; insertion-order eviction assumes monotonic time · AFFECTED_CODE: `DpopReplayCache.kt:34-56`, `DeviceAuthClock.kt:16-18`, `DpopProofVerifier.kt:116-124,150` · AFFECTED_ARCHITECTURE: B-002 replay cache 5 m, Inv.18, B-016 shared state · FIX_GROUP: AD-D · PRE_B004_OR_LATER: LATER (B-004 backend verifier; contract entry in GAP-002 PRE_B004) · REQUIRED_TEST: rollback test (evicted jti rejected after −250 s), retention keyed by `iat`+tolerance or monotonic source · INDEPENDENT_RETEST_OWNER: backend security retest · DEPENDENCIES: ROOT-008 scope fix · DISPOSITION: OPEN_PENDING_CONSOLIDATION

**ANOX-AUTHDPOP-GAP-001 / GAP-002 / GAP-003**
SOURCE: AUDIT-SECURITY-AUTH-DPOP-001 · ROOT_CAUSE: contract absent below endpoint-table level · AFFECTED_CODE: none yet (client nonce plumbing / `DpopHtu` / `RegistrationApi` will be affected) · AFFECTED_ARCHITECTURE: B-002, B-004 (V1.2 §1–§5), B-005 auth schema, B-007 · FIX_GROUP: AD-D / AD-C+AD-D / AD-F · PRE_B004_OR_LATER: PRE_B004 (contract freeze) · REQUIRED_TEST: authority validator asserting contract presence; conformance tests once implemented · INDEPENDENT_RETEST_OWNER: architecture consistency retest · DEPENDENCIES: ROOT-008, ROOT-009, CANDIDATE-001/003 · DISPOSITION: OPEN_PENDING_CONSOLIDATION

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
`PRESERVE AUDIT-SECURITY-AUTH-DPOP-001 → AUDIT-SECURITY-ANDROID-STORAGE-001 → PRESERVE → AUDIT-SECURITY-ATTACKCHAIN-001 → PRESERVE → MASTER SPECIALIST CONSOLIDATION → SECURITY-REMEDIATION-COVERAGE-GATE (100% assignment) → LARGE DEPENDENCY-SAFE REMEDIATION SESSIONS → INDEPENDENT RETESTS → LEGACY/ARCHITECTURE REVALIDATION → FRESH FULL-SYSTEM SECURITY RE-AUDIT → OPERATIONAL ACCEPTANCE → HUMAN FINAL GATE → ONLY THEN B004`

```
HEAD        = 638e63a22c91ca81365bf55c8a59ec47878dd7fd
origin/main = 638e63a22c91ca81365bf55c8a59ec47878dd7fd
working tree = CLEAN · branches/commits/push/PR/merge = NONE · remote mutation = NONE
findings / docs / registries / Project Memory mutation = NONE · fixes implemented = NONE
```

`AUDIT-SECURITY-AUTH-DPOP-001` — COMPLETE. `PASS_WITH_FINDINGS`. STOP.