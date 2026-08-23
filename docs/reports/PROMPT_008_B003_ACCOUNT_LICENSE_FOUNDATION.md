# PROMPT-008 — B-003 Account / License Foundation

**Date:** 2026-08-22
**Branch:** `feature/b003-account-license-foundation`
**Baseline:** `main @ 0785b6001f816f5a6520951dd9a8c5a4af9af4c2`
**Authority:** current B-025 + B-026
**Type:** implementation (client domain/state foundation only)

---

## 1. Scope

Implements the minimum B-003 Account/License client foundation: strongly typed domain values,
the frozen account/device/entitlement state model, the registration transaction state machine,
narrow API contracts for the future B-004 backend, a persistent Device Auth binding store (a
gap explicitly left open by PROMPT-007), and persistent, crash-resumable registration-session
storage.

**In scope:** username/license/UUID validation, account/device/entitlement states, license
duration enum, registration grant model, registration state machine, narrow
`RegistrationApi`/`LocalE2eeIdentityStep` interfaces, persistent local storage for the Device
Auth binding marker and registration session, integration with the existing B-002 Device Auth
boundary and the existing E2EE (`CryptoBridge`) public API.

**Explicitly out of scope and NOT implemented:** B-004 backend (real HTTP stack, token issuance,
server persistence), B-005 database/RLS, any privileged Supabase/PostgreSQL access from the
APK, license generation (server responsibility), the server HMAC lookup algorithm or its secret,
account recovery, device replacement/multi-device, a 365-day standard license, a general
one-week V1 trial.

## 2. Files added / changed

### Added — `android/src/main/java/com/anox/messenger/account/`

| File | Responsibility |
|---|---|
| `UuidV4.kt` | Shared UUIDv4 parse/validate helper |
| `AccountId.kt` / `DeviceId.kt` / `RegistrationId.kt` | Server-issued identifier value types |
| `Username.kt` | B-003 username syntax validation |
| `LicenseCode.kt` | License code structural validator, secret-safe |
| `LicenseDuration.kt` | Frozen 30/90/180-day standard durations |
| `AccountState.kt` / `DeviceState.kt` / `EntitlementState.kt` | Frozen state enums |
| `Entitlement.kt` | Server-reported entitlement snapshot |
| `EntitlementRenewal.kt` | Non-authoritative renewal preview (server-time input only) |
| `RegistrationGrant.kt` | Opaque 256-bit grant wrapper + foundation/test generator |
| `RegistrationState.kt` | Registration transaction state machine (sealed) |
| `PublicE2eeIdentityMaterial.kt` | Public-only E2EE material shape for the API boundary |
| `LocalE2eeIdentityStep.kt` | Narrow E2EE-creation boundary interface |
| `CryptoBridgeLocalE2eeIdentityStep.kt` | Implementation calling existing `CryptoBridge` API |
| `RegistrationApi.kt` | Narrow B-004 network contract + result types |
| `RegistrationSessionStore.kt` | Session-resume storage interface + in-memory implementation |
| `FileRegistrationSessionStore.kt` | Persistent, no-backup, crash-resumable session storage |
| `RegistrationOrchestrator.kt` | Drives the registration state machine |

### Added — `android/src/main/java/com/anox/messenger/security/deviceauth/`

| File | Responsibility |
|---|---|
| `FileDeviceAuthBindingStore.kt` | Persistent, no-backup, fail-closed Device Auth binding marker |

### Added — `android/src/main/java/com/anox/messenger/storage/`

| File | Responsibility |
|---|---|
| `AtomicFileWriter.kt` | Shared atomic write-then-rename helper |

### Added — tests

- `android/src/test/java/com/anox/messenger/account/`: `AccountTestSupport.kt`,
  `UsernameTest.kt`, `IdentifierTest.kt`, `LicenseCodeTest.kt`, `LicenseDurationTest.kt`,
  `EntitlementRenewalTest.kt`, `RegistrationGrantTest.kt`,
  `AccountDeviceEntitlementStateTest.kt`, `RegistrationStateCodecTest.kt`,
  `RegistrationOrchestratorTest.kt`
- `android/src/androidTest/java/com/anox/messenger/security/deviceauth/FileDeviceAuthBindingStoreTest.kt`
- `android/src/androidTest/java/com/anox/messenger/account/FileRegistrationSessionStoreTest.kt`

### Not changed

`crypto/rust/**`, `CryptoNative.kt`, `CryptoBridge.kt` (called, not modified),
`AndroidManifest.xml`, `android/build.gradle.kts` dependency list, Gradle/Kotlin/NDK/AGP/Compose
versions, native `.so` files, `docs/authority/`, the B-002 Device Auth security model.

## 3. Account model

`AccountId`, `DeviceId`, `RegistrationId` are value types wrapping `java.util.UUID`. Each has a
private constructor and a single companion factory `parse(raw: String): X?` that validates the
UUID is syntactically valid **and** version 4; non-v4 UUIDs and malformed strings are rejected.
There is no generator method on any of the three types: the client never manufactures a
canonical account/device/registration identifier.

`AccountState` = `{ACTIVE, SUSPENDED, REVOKED, DELETED}`, `DeviceState` = `{ACTIVE, REVOKED}`,
`EntitlementState` = `{ACTIVE, EXPIRED, REVOKED}` — exactly the frozen sets, server-authoritative
always; the client never derives these locally.

`Username.validate(raw)` returns a sealed `UsernameValidation` (`Valid`/`Invalid` with a reason).
Validation is against the exact input; an invalid username (e.g. containing uppercase letters)
is rejected outright and never silently lowercased. No reserved-name list is implemented because
the current authority does not enumerate one; server-side validation remains authoritative.

## 4. License model

`LicenseCode.parse(raw)` validates only the external shape `anox-XXXX-XXXX-XXXX` (uppercase
alphanumeric, 4-4-4 grouping). **Assumption/limitation:** the current authority specifies "12
unambiguous CSPRNG-generated characters" but does not enumerate which characters are excluded as
ambiguous; rather than inventing an unspecified exclusion alphabet, the validator checks only the
gross structural shape. This should be tightened once the exact server-side alphabet is frozen.
`LicenseCode` never has a generation method — license generation is exclusively a server
responsibility — and its `toString()` is overridden to never print the plaintext value.

`LicenseDuration` is an enum with exactly `DAYS_30(30)`, `DAYS_90(90)`, `DAYS_180(180)`. Tests
explicitly prove no `365`-day or `7`-day (one-week trial) value exists.

No HMAC lookup algorithm or server secret is implemented or embedded anywhere in this branch.

## 5. Registration flow

`RegistrationState` is a sealed class: `NotStarted -> Reserved -> DeviceAuthRegistered ->
PublicIdentityUploaded -> Committed`, plus `Expired` and `Failed` terminal-ish states. No state
represents account recovery or device replacement (enforced by an exhaustive `when` in tests
with no `else` branch, so an added recovery/replacement state would fail to compile until
explicitly named and handled).

`RegistrationOrchestrator` exposes one method per flow step (`reserve`, `registerDeviceAuth`,
`uploadPublicIdentity`, `commit`) plus `currentState()` and `abandon()`. Each step:
1. requires the correct prior state (skipping a step fails closed to `Failed`, never silently
   advances);
2. persists its resulting state via `RegistrationSessionStore` **before** returning, so a
   crash/process death is resumable by simply reconstructing the orchestrator against the same
   store and calling the next step;
3. never calls `DeviceAuthBindingStore.markBound()` except from exactly one place: immediately
   after `commit()` observes `CommitResult.Committed`.

A local (non-authoritative) staleness check against the registration grant's 30-minute TTL uses
an injectable `Instant` parameter, never the bare device clock implicitly — this is a UX
optimization only; the server remains the actual arbiter of grant validity.

## 6. Device Auth binding

`FileDeviceAuthBindingStore` (in `security.deviceauth`, alongside the interface it implements)
closes the gap PROMPT-007 explicitly left open ("`DeviceAuthBindingStore` has only an in-memory
implementation"). It stores a single small marker file under `Context.getNoBackupFilesDir()`:
- absent file -> not bound (legitimate first run);
- valid marker -> the stored flag;
- **unreadable or corrupt file -> fails closed to `bound = true`.** This is the safe direction
  here: `isBound() == true` only ever blocks new-key creation
  (`DeviceAuthKeyStateResolver.requireCreationAllowed`) and can never cause a silent Device Auth
  key replacement for what might in fact be an already-bound installation.

`RegistrationOrchestrator` is the only caller of `markBound()`, and only after a successful
commit.

## 7. Local persistence

Both `FileDeviceAuthBindingStore` and `FileRegistrationSessionStore` write under
`Context.getNoBackupFilesDir()`, which Android excludes from classic backup and
device-to-device transfer independent of `dataExtractionRules`. This is on top of the existing
app-wide `android:allowBackup="false"` and `dataExtractionRules` (which already exclude the
entire private storage root, `domain="root"`); no manifest or `data_extraction_rules.xml` change
was needed or made.

Both use a shared `AtomicFileWriter` (write-temp-then-rename), mirroring the pattern already
used internally by `CryptoBridge`, without depending on or modifying it.

The registration session file uses a minimal, dependency-free `key=value` text format (no JSON
library was introduced). A corrupt/unparseable session file fails closed to
`RegistrationState.NotStarted` — the opposite direction from the binding store, because there is
no equivalent security asymmetry here: an unreadable in-progress registration simply restarts
cleanly, and the corresponding server-side reservation is separately released once the grant's
TTL elapses server-side.

## 8. Secret handling

- `LicenseCode.toString()` never prints the plaintext value.
- `RegistrationGrant.toString()` never prints the grant value.
- Neither type is ever logged anywhere in the new code (verified by inspection: no `Log.*`,
  `println`, or `System.out` calls exist in the new files).
- The registration grant is held only in memory / the narrow session-resume file; it is never
  placed in `SharedPreferences`, crash reports, or treated as a refresh token or recovery
  credential.
- `PublicE2eeIdentityMaterial` carries only public key bytes; `LocalE2eeIdentityStep` never
  reads or exposes private key material from `CryptoBridge`.
- No server HMAC secret, Supabase service-role credential, or other production secret is present
  anywhere in this branch.

## 9. Server / database boundary (explicit, per instructions)

No production infrastructure was provisioned. `RegistrationApi` is a plain interface with no
HTTP client, no fake Supabase/PostgreSQL implementation, and no privileged credentials. The
expected future topology remains:

```
Android -> authenticated HTTPS /v1 -> anoX backend (B-004) -> PostgreSQL/Supabase/private storage (B-005)
```

B-004 will introduce the real anoX backend service and decide the actual threading/network
model for `RegistrationApi`. B-005 will introduce the real PostgreSQL/Supabase schema,
constraints (including DB-enforced one-active-device-per-account) and RLS. Neither exists yet;
this branch does not simulate them.

## 10. Tests actually run

| Command | Result |
|---|---|
| `cargo test` (crypto/rust) | 15/15 PASS |
| `./gradlew :android:testDebugUnitTest` | **146/146 PASS**, 0 failures, 0 errors (77 new B-003 tests + 69 pre-existing B-002 tests, unchanged) |
| `./gradlew :android:connectedDebugAndroidTest` | **58/58 PASS**, 0 failures, 0 errors, on a real Android emulator (`anox_api34_arm64`, API 34) — see note below |
| `./gradlew :android:assembleDebug` | PASS |
| `./gradlew :android:assembleRelease` | PASS |
| `validate_apk_contents.py` on fresh debug APK | PASS (0 forbidden, 0 secret markers) |
| `validate_apk_contents.py` on fresh release APK | PASS (0 forbidden, 0 secret markers) |
| `git diff --check` | PASS |
| `python3 tools/continuity/validate_continuity.py` | PASS (after governance sync, see below) |

**Note on instrumentation:** an Android emulator was unexpectedly available in this environment.
Running `connectedDebugAndroidTest` executed all instrumentation suites, including
`AndroidKeystoreDeviceAuthKeyManagerTest` (B-002, PROMPT-007), which had never been executed in
CI or in any prior review. All 10 of its tests passed on the emulator, in addition to 35
pre-existing `CryptoInstrumentedTest` tests, 7 new `FileDeviceAuthBindingStoreTest` tests, and 6
new `FileRegistrationSessionStoreTest` tests. **This is still an emulator, not a physical
device, and not GrapheneOS**, so it does not constitute physical StrongBox/TEE or GrapheneOS
verification; those remain UNVERIFIED. It does, however, upgrade "Android Keystore
instrumentation: NOT RUN" to "run and passing on an emulator" for both B-002 and the new B-003
persistence classes.

## 11. Tests NOT run / UNVERIFIED

- Physical hardware-backed StrongBox/TEE Device Auth key behaviour: UNVERIFIED (emulator only).
- GrapheneOS physical-device behaviour: UNVERIFIED.
- Any real B-004 network integration: not applicable, B-004 does not exist.
- Server-side one-active-device-per-account DB enforcement (B-005): not applicable, does not
  exist yet.

## 12. CI

No CI workflow change was required; the existing `.github/workflows/ci.yml` `Run JVM unit tests`
step already executes the entire `android/src/test/java` tree, including the new
`com.anox.messenger.account` package, without modification. Instrumentation remains not runnable
in CI (no emulator there); this is unchanged from PROMPT-007.

## 13. Limitations and future B-004/B-005 requirements

- `RegistrationApi` has no real implementation; a future B-004 task must implement it against
  the actual `/v1` endpoints and decide the threading/coroutines model.
- `LicenseCode`'s structural validator uses a placeholder-safe uppercase-alphanumeric charset
  assumption pending the exact "unambiguous" character set definition from a future B-003
  clarification or B-004 implementation.
- One-active-device-per-account is only representable (`DeviceState`), not enforced; real
  enforcement is DB-level under B-005.
- `RegistrationOrchestrator`'s one-time-key upload count (`DEFAULT_ONE_TIME_KEY_COUNT = 20`) is
  a foundation placeholder; the real value is a future B-004/B-005 product decision.
- No UI/ViewModel wiring exists yet (matching the same "foundation, not wired into MainActivity"
  pattern PROMPT-007 used for B-002).
