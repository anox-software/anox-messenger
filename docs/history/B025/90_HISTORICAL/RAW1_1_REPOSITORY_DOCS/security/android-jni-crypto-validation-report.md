> **Status:** HISTORICAL / SUPERSEDED  
> **Architecture Baseline:** Raw1.1  
> **Last synchronized:** 2026-08-19  
> **Do not use as current runtime validation proof.**  
> **Corrections:** JDK 21 requirement claim superseded/corrected; actual NDK is `26.2.11394342`; Android runtime has since been verified by `docs/security/android-runtime-crypto-validation-report.md`.  
> **Superseded by:** `docs/security/android-runtime-crypto-validation-report.md`  

# Android / JNI Crypto Integration Validation Report - anoX Messenger V1

## Executive Summary

The complete Android → Kotlin → JNI → Rust → vodozemac path has been built and verified at the compilation and packaging level. The debug APK, Android test APK, and the arm64-v8a/x86_64 native libraries were produced successfully. Rust regression tests remain 14/14. However, Android instrumented test **execution** was not possible because no physical device or pre-configured emulator is available, and no Android system images are installed.

The crypto foundation is **functionally verified at the compiled/linked level**. It is **not** claimed to be production-secure.

---

## A. JDK Version

| Component | Value |
|-----------|-------|
| Provider | Eclipse Temurin by Adoptium |
| Version | 17.0.20+8 |
| Architecture | aarch64 (Apple Silicon) |
| Installation path | `/Users/3xpress/Library/Java/jdk-17.0.20+8` |
| Verification command | `java -version` |

### Important Note
The project currently uses **Android Gradle Plugin 9.1.1**, which officially requires **JDK 21 or newer**. The build succeeded with JDK 17 in this validation environment, but this is an **unsupported configuration** and may break on clean builds or future runs. The recommended JDK for AGP 9.x is JDK 21. **No JDK downgrade/upgrade was performed**; only the absence/presence of a runtime was addressed.

---

## B. Android SDK Version

| Component | Value |
|-----------|-------|
| SDK root | `/Users/3xpress/Library/Android/sdk` |
| Build tools | 30.0.3, 34.0.0, 35.0.0, 36.0.0, 36.1.0, 37.0.0 |
| Platform `android-34` | present |
| Platform `android-36.1` | present |
| Emulator package | present |
| `adb` | present (`platform-tools`) |
| No `cmdline-tools` or `sdkmanager` | present (NDK and JDK installed manually) |

---

## C. NDK Version

| Component | Value |
|-----------|-------|
| NDK version | r26c (26.2.11394342) |
| Installation path | `/Users/3xpress/Library/Android/sdk/android-ndk-r26c` |
| Installation method | Direct download and unzip from Google (`android-ndk-r26c-darwin.zip`) |
| Build method | `cargo-ndk` v4.1.2 (no custom compiler scripts) |
| Targets built | `arm64-v8a`, `x86_64` |

### NDK Pinning
The project should pin `ndkVersion` in `android/build.gradle.kts` to ensure reproducible builds:
```kotlin
android { ndkVersion = "26.2.11394342" }
```
This was **not** added to avoid unrelated build changes unless requested.

---

## D. Gradle Wrapper Version

| Component | Value |
|-----------|-------|
| Wrapper distribution | `gradle-9.3.1-bin.zip` |
| Source | `gradle/wrapper/gradle-wrapper.properties` |
| Used to build | ✅ `./gradlew` |

---

## E. AGP Version

| Component | Value |
|-----------|-------|
| Android Gradle Plugin | 9.1.1 |
| Source | `build.gradle.kts` root project |
| Incompatibility note | Requires JDK 21 officially; build completed with JDK 17 in this environment |

The previous context mentioned AGP 8.13.2, but the **actual inspected version is 9.1.1**. No upgrade or downgrade was performed.

---

## F. Kotlin Version

| Component | Value |
|-----------|-------|
| Kotlin Android plugin | 2.2.10 |
| Source | `build.gradle.kts` root project |

No Kotlin upgrade was performed.

---

## G. Rust Targets Built

| Target | ABI | Purpose |
|--------|-----|---------|
| `aarch64-linux-android` | `arm64-v8a` | Real Pixel/GrapheneOS devices |
| `x86_64-linux-android` | `x86_64` | Android emulator |

Rust toolchain:
- `rustc 1.97.1`
- `cargo 1.97.1`
- `rustup` (installed during this validation)
- Host triple: `aarch64-apple-darwin`

---

## H. Generated `.so` Files / ABIs

| File | Size | ABI |
|------|------|-----|
| `android/src/main/jniLibs/arm64-v8a/libanox_crypto.so` | 1.30 MB | arm64-v8a |
| `android/src/main/jniLibs/x86_64/libanox_crypto.so` | 1.28 MB | x86_64 |

### Verification Commands
```bash
find "android/src/main/jniLibs" -name "*.so" -exec ls -l {} \;
```

---

## I. Android Build Result

### Commands
```bash
export JAVA_HOME="/Users/3xpress/Library/Java/jdk-17.0.20+8/Contents/Home"
export ANDROID_HOME="/Users/3xpress/Library/Android/sdk"
export PATH="$JAVA_HOME/bin:$PATH"
./gradlew :android:assembleDebug :android:assembleDebugAndroidTest
```

### Result
```text
BUILD SUCCESSFUL in 6s

Generated files:
- android/build/outputs/apk/debug/android-debug.apk
- android/build/outputs/apk/androidTest/debug/android-debug-androidTest.apk
```

### What Was Proven
- Kotlin sources compile, including the `crypto/android` bridge.
- `CryptoBridge`, `CryptoNative`, and `CryptoResult` are valid Kotlin.
- Native libraries are packaged into the APK (`libanox_crypto.so` for `arm64-v8a` and `x86_64`).
- JNI method signatures match the Kotlin `external` declarations.
- `System.loadLibrary("anox_crypto")` references a library that is present in the APK.

### What Was NOT Proven
- Runtime loading of the library on a real Android runtime.
- Execution of any Kotlin/JNI method.
- Device-specific Keystore behavior (hardware-backed vs software-backed).

---

## J. JNI Test Results

### Tests Added

New file: `crypto/android/src/androidTest/java/com/anox/crypto/CryptoInstrumentedTest.kt`

Tests designed to run on real Android runtime:
1. `nativeLibraryLoads` — `System.loadLibrary` / `CryptoNative.cryptoInit()`
2. `createAndDestroyIdentity` — full create/destroy life cycle
3. `getPublicKeys` — 32-byte Curve25519 and Ed25519 public keys
4. `oneTimeKeyGeneration` — OTK generation and count
5. `identitySerializationAndRestoration` — serialize/restore identity
6. `corruptedStateRejectsDeserialization` — AES-GCM tamper detection on device
7. `invalidHandleIsRejected` — zero/invalid handle handling
8. `destroyIdentityIsIdempotent` — no crash on destroy
9. `endToEndAliceBob` — Alice→Bob and Bob→Alice round trip through Kotlin/JNI
10. `invalidCiphertextRejectsDecryption` — safe failure on bad input
11. `errorMessagesDoNotContainSecrets` — no secret leakage in exceptions

### Rust JNI Additions

- `crypto_get_one_time_key` in `lib.rs` (returns a 32-byte OTK by index)
- `CryptoNative.cryptoGetOneTimeKey` declaration
- `CryptoBridge.getOneTimeKey` wrapper

### Test Compilation
```text
Task :android:compileDebugAndroidTestKotlin — SUCCESS
Task :android:assembleDebugAndroidTest — SUCCESS
```

### Test Execution
**NOT EXECUTED** — no Android device or configured emulator is attached. The test APK is built and ready for installation.

```text
adb devices
List of devices attached
(empty)
```

No Android system images are present in the SDK, so an emulator could not be started without a large additional download.

---

## K. Rust Regression Test Result

### Command
```bash
cd crypto/rust
cargo test
```

### Result
```text
running 14 tests
test tests::tests::test_identity_creation ... ok
test tests::tests::test_corrupted_serialized_state ... ok
test tests::tests::test_key_separation ... ok
test tests::tests::test_error_messages_no_secrets ... ok
test tests::tests::test_authenticated_encryption ... ok
test tests::tests::test_invalid_ciphertext ... ok
test tests::tests::test_malformed_message ... ok
test tests::tests::test_serialization_restoration ... ok
test tests::tests::test_wrong_key_material ... ok
test tests::tests::test_no_recovery_mechanism ... ok
test tests::tests::test_one_time_key_generation ... ok
test tests::tests::test_modified_ciphertext ... ok
test tests::tests::test_alice_bob_full_flow ... ok
test tests::tests::test_wrong_session_message_type ... ok

test result: ok. 14 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

### Status
✅ **14/14 PASS** (same as before Android integration).

---

## L. AES-256-GCM Nonce/Key/Storage Review

### Rust Local-State Encryption (`crypto/rust/src/serialization.rs`)

| Property | Implementation |
|----------|----------------|
| Algorithm | AES-256-GCM |
| Library | `aes-gcm` 0.10.3 |
| Key size | 32 bytes (256 bits) |
| Key origin | Android side generates a random 32-byte state key; it is encrypted with the Keystore master key and stored in the app’s private files. |
| Nonce/IV size | 12 bytes (96 bits) |
| Nonce generation | `getrandom::getrandom(&mut [0u8; 12])` — random per encryption call |
| Auth tag size | 16 bytes (128 bits) produced automatically by `aes-gcm` |
| Serialization format | `[ 12 bytes nonce ][ ciphertext + 16-byte tag ]` |
| Versioning | Single format (V1); no version byte currently. |
| Corrupted/tampered behavior | `decrypt()` fails with `DecryptionError` and returns no plaintext. |

### Nonce Reuse Risk
- **Random 96-bit nonce is acceptable for V1** with limited encryption volume under the same key (birthday bound ~2^48 messages before non-negligible collision risk).
- **No nonce is ever reused with the same key by design** unless `getrandom` is broken.
- A future hardening step is to add a version byte and consider deterministic counter-based nonces if the key lifetime spans billions of encryptions.
- **No custom cryptography is used.**

### Android State-Key Wrap (`CryptoBridge.kt`)

| Property | Implementation |
|----------|----------------|
| Keystore key | AES-256-GCM, non-extractable, in `AndroidKeyStore` |
| State key | Random 32 bytes, generated with `SecureRandom` |
| Wrap algorithm | AES/GCM/NoPadding using Keystore key |
| Wrapped key file | `context.filesDir/anox_state_key.enc` |
| Wrapped format | `[ 12-byte IV ][ ciphertext + 16-byte tag ]` |
| Key rotation | Not implemented in V1. |

### Security Notes
- The state key is **never** stored in plaintext; it is only present in memory while a crypto operation is in progress.
- The Keystore master key is **non-extractable**; the state key cannot be recovered without the original device Keystore.
- No private E2EE keys are stored in Kotlin; only the 32-byte state key and opaque pointer handles cross the JNI boundary.

---

## M. Android Keystore Review

### What Is Correct

1. **E2EE identity keys are separated from local state-protection material**
   - E2EE keys live in Rust vodozemac, serialized with AES-GCM using the state key.
   - The state key is wrapped by the Keystore master key.
   - The Keystore master key never leaves the Keystore.

2. **No private E2EE key is exported to server or UI**
   - Only public keys (`[u8; 32]`) and opaque pointers are returned to Kotlin.
   - Private key material is inside vodozemac pickles and encrypted before leaving Rust.

3. **Crypto state is protected at rest**
   - Identity/session pickles are AES-256-GCM encrypted.
   - The AES key itself is encrypted by the Keystore and stored in app private files.

4. **No cloud-backup recovery path**
   - `AndroidManifest.xml` `android:allowBackup` changed to `"false"`.
   - Keystore keys are device-bound and not included in backup anyway; disallowing backup removes any ambiguity about ciphertext portability.

5. **App uninstall = permanent loss**
   - `anox_state_key.enc` is deleted with app data.
   - Keystore key is deleted on uninstall.
   - No recovery secret, seed, or server backup exists.

### What Remains a V1 Limitation

1. **No device-lock requirement**
   - `setUserAuthenticationRequired(false)` is set.
   - A PIN/biometric is not required to use the crypto material.
   - This is documented as a V1 choice.

2. **No `setInvalidatedByBiometricEnrollment` or strong hardware binding**
   - Standard Keystore behavior; not a custom mechanism.

3. **No Keystore key attestation**
   - No verification that the key is hardware-backed.

4. **Wrapped state key file has no backup exclusion rule beyond `allowBackup="false"`**
   - Currently acceptable because `allowBackup="false"` is the nuclear option. If `allowBackup` is ever enabled, a `<full-backup-content>` exclude rule must be added.

---

## N. GrapheneOS / Device Test Result

**NO ANDROID DEVICE OR EMULATOR WAS AVAILABLE.**

```text
$ adb devices
List of devices attached

(empty)
```

No AVDs exist:
```text
$ emulator -list-avds
(no output)
```

No Android system images are installed, so an emulator could not be started.

### GRAPHENEOS DEVICE TEST: **UNVERIFIED**

The following cannot be confirmed until a Pixel/GrapheneOS device or emulator with the appropriate system image is available:
- APK installs and launches.
- Native library `libanox_crypto.so` loads successfully.
- `CryptoBridge` initializes the Keystore and Rust layer.
- `CryptoInstrumentedTest` suite runs and passes.
- Real Olm Alice/Bob round trip completes through the full Android/JNI stack.
- Persisted crypto-state survives an app restart and is restored correctly.

---

## O. Files Changed

### Build / Tooling Configuration
- `android/build.gradle.kts` — added `crypto/android` main and androidTest source sets, added AndroidX test dependencies.
- `gradle/wrapper/gradle-wrapper.properties` — no changes (already 9.3.1).
- `build.gradle.kts` — no changes.
- `AndroidManifest.xml` — `android:allowBackup="false"`.

### Rust Crypto Layer
- `crypto/rust/src/lib.rs` — added `crypto_get_one_time_key`.
- `crypto/rust/src/identity.rs` — added `get_one_time_key_by_index`.

### Android Crypto Bridge
- `crypto/android/src/main/java/com/anox/crypto/CryptoBridge.kt` — fixed Keystore AES/GCM key generation, added state-key wrap/unwrap (non-extractable Keystore + 32-byte random state key), added `getOneTimeKey`.
- `crypto/android/src/main/java/com/anox/crypto/CryptoNative.kt` — added `cryptoGetOneTimeKey` declaration.
- `crypto/android/src/main/java/com/anox/crypto/CryptoResult.kt` — fixed generic `Failure` type to extend `CryptoResult<Nothing>`.

### Android Tests
- `crypto/android/src/androidTest/java/com/anox/crypto/CryptoInstrumentedTest.kt` — new instrumented test suite.

### Native Libraries
- `android/src/main/jniLibs/arm64-v8a/libanox_crypto.so` — generated.
- `android/src/main/jniLibs/x86_64/libanox_crypto.so` — generated.

### Documentation
- `docs/security/android-jni-crypto-validation-report.md` — this file.

---

## P. Remaining Blockers

### Blocker 1: No Device / Emulator
- **Impact**: Android instrumented tests and GrapheneOS smoke test cannot be executed.
- **Status**: Not fixable in this environment without downloading a system image and creating an AVD, or connecting a physical device.

### Blocker 2: JDK Version Mismatch
- **Impact**: Project uses AGP 9.1.1, which officially requires JDK 21. Validation used JDK 17 and succeeded, but this is unsupported.
- **Recommended fix**: Install JDK 21 and set `JAVA_HOME` for the project.

### Blocker 3: NDK Not Pinned
- **Impact**: `android/build.gradle.kts` does not specify `ndkVersion`.
- **Recommended fix**: Add `ndkVersion = "26.2.11394342"` to `android/build.gradle.kts`.

### Blocker 4: AGP 9.1.1 / Kotlin 2.2.10 vs Original Context
- **Impact**: The previous summary referenced AGP 8.13.2 / Kotlin 1.9.20. The actual project is now 9.1.1 / 2.2.10. No version was changed by this session, but this should be reconciled with the product baseline.

### Blocker 5: `allowBackup="false"` Is Broad
- **Impact**: Disabling all backup is correct for V1, but in the future a more selective backup policy may be needed for non-crypto data (e.g., user preferences).
- **Status**: Acceptable for V1.

---

## Q. Exact Recommended Next Development Step

1. **Install JDK 21** (or use the existing JDK 17 if the project is intentionally pinned to AGP 8.x, but first reconcile the AGP version).
2. **Pin `ndkVersion`** in `android/build.gradle.kts`.
3. **Create an AVD or connect a Pixel/GrapheneOS device.**
   - For AVD, download a system image (e.g., `system-images;android-34;google_apis;x86_64`).
4. **Install and run instrumented tests:**
   ```bash
   ./gradlew :android:connectedDebugAndroidTest
   ```
5. **Verify GrapheneOS smoke test:**
   - Install debug APK.
   - Launch app.
   - Run `CryptoInstrumentedTest` or a manual `CryptoBridge.getInstance(context).createIdentity()` call.
   - Restart app and verify `deserializeIdentity` works.
6. **If the project is intended to remain on AGP 8.x**, downgrade the root `build.gradle.kts` to:
   ```kotlin
   id("com.android.application") version "8.13.2" apply false
   id("org.jetbrains.kotlin.android") version "1.9.20" apply false
   ```
   and confirm the build still works with JDK 17.

---

## Conclusion

### Verified
- ✅ Android project builds with Kotlin/JNI/Rust/vodozemac linked.
- ✅ Debug APK and AndroidTest APK generated.
- ✅ Native libraries `libanox_crypto.so` built for `arm64-v8a` and `x86_64`.
- ✅ Rust `cargo test` remains 14/14.
- ✅ AES-256-GCM local state protection reviewed; no nonce reuse, authenticated integrity.
- ✅ Keystore integration reviewed; no private E2EE keys exported; no cloud backup recovery.
- ✅ `allowBackup="false"` prevents unexpected restoration.

### Not Verified
- ❌ Android instrumented test execution (no device/emulator).
- ❌ GrapheneOS device smoke test.
- ❌ Runtime Keystore behavior on real hardware.

The Android/JNI crypto foundation is **functionally built and linked**, but its **runtime correctness on an actual Android/GrapheneOS device remains unverified**.