> **Status:** CURRENT  
> **Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
> **Last synchronized:** 2026-08-19  

# ANOX V1 — Android Runtime Crypto Validation Report

**Scope:** Runtime validation of the Rust/JNI crypto bridge, NDK/toolchain reproducibility, and selected Android Keystore/AES-GCM behavior on an Apple-Silicon Android emulator. This report supersedes any earlier draft that claimed runtime verification without actual passing connected tests.

**Important:** This report documents functional verification at the implemented test level. It does **not** claim production security, audit completion, unhackability, or complete endpoint security.

---

## A. Exact Final Toolchain

| Component | Value | Source of truth |
|-----------|-------|-----------------|
| AGP | `8.13.2` | `build.gradle.kts` top-level plugin version |
| Kotlin Android plugin | `1.9.20` | `build.gradle.kts` top-level plugin version |
| Gradle Wrapper | `9.3.1` | `gradle/wrapper/gradle-wrapper.properties` |
| JDK | Eclipse Temurin `17.0.20+8` | `JAVA_HOME` / `java -version` output |
| `compileSdk` | `34` | `android/build.gradle.kts` |
| `minSdk` | `26` | `android/build.gradle.kts` |
| `targetSdk` | `34` | `android/build.gradle.kts` |
| Rust toolchain | `rustc 1.97.1`, `cargo 1.97.1` | `rustc --version` / `cargo --version` |
| `cargo-ndk` | `4.1.2` | `cargo ndk --version` |
| Android host target | `aarch64-apple-darwin` | `rustc -vV` host triple |
| Android build targets | `arm64-v8a`, `x86_64` | `cargo ndk -t` invocation |
| Android SDK | `/Users/3xpress/Library/Android/sdk` | `ANDROID_HOME` |
| NDK | `26.2.11394342` (r26c) | `android/build.gradle.kts` `ndkVersion` / `ANDROID_NDK_HOME` |

## B. Exact Pinned NDK Version and Reason

NDK `26.2.11394342` (r26c) is pinned in `android/build.gradle.kts`:

```kotlin
defaultConfig {
    ndkVersion = "26.2.11394342"
    ...
}
```

The installed NDK at `$ANDROID_HOME/android-ndk-r26c` is used by `cargo-ndk` for the Rust cross-compilation and by the Android Gradle Plugin for native builds. This version was chosen because:

1. It is already installed and working with the current Rust `aarch64-linux-android` and `x86_64-linux-android` targets.
2. It produces `libanox_crypto.so` artifacts for both `arm64-v8a` and `x86_64` that are packaged and successfully executed in the connected Android tests.
3. It is the r26c LTS release with compatible LLVM/Clang for `vodozemac 0.10.0` and `aes-gcm 0.10.3`.

**Compatibility note:** Future Android Gradle Plugin or Rust NDK support may require moving to NDK r27/r28. Any upgrade must be explicit, pinned, and re-validated by `cargo test` plus `:android:connectedDebugAndroidTest`.

## C. Emulator / Device Model

| Item | Value |
|------|-------|
| AVD name | `anox_api34_arm64` |
| Device skin | `pixel_7` (Google) |
| System image | `Google APIs`, Android `14.0` (`UpsideDownCake`) |
| ABI | `google_apis/arm64-v8a` |
| AVD path | `/Users/3xpress/.android/avd/anox_api34_arm64.avd` |

## D. Android API Level

`34` (Android 14 / UpsideDownCake).

## E. ABI

`arm64-v8a` (emulated on Apple Silicon). `x86_64` libraries were also built but not executed because the emulator is ARM64.

## F. Exact Instrumentation Command

From the repository root (`/Users/3xpress/Desktop/anoX Messanger`):

```bash
export JAVA_HOME="/Users/3xpress/Library/Java/jdk-17.0.20+8/Contents/Home"
export ANDROID_HOME="/Users/3xpress/Library/Android/sdk"
export PATH="$JAVA_HOME/bin:$PATH"
./gradlew :android:connectedDebugAndroidTest
```

Single-test debugging used the same command with `-Pandroid.testInstrumentationRunnerArguments.class=com.anox.crypto.CryptoInstrumentedTest#getOneTimeKey`.

## G. Exact Executed Tests and PASS/FAIL Counts

Command result:

```text
Starting 19 tests on anox_api34_arm64(AVD) - 14
Finished 19 tests on anox_api34_arm64(AVD) - 14
BUILD SUCCESSFUL
```

XML test result file (`TEST-anox_api34_arm64(AVD) - 14-_android-.xml`):

| Metric | Value |
|--------|-------|
| tests | 19 |
| failures | 0 |
| errors | 0 |
| skipped | 0 |

All `com.anox.crypto.CryptoInstrumentedTest` methods passed:

- `oneTimeKeyGeneration`
- `invalidHandleIsRejected`
- `missingStateFailsSafely`
- `invalidCiphertextRejectsDecryption`
- `getOneTimeKey`
- `invalidMessageTypeRejectsDecryption`
- `endToEndAliceBob`
- `nativeLibraryLoads`
- `destroyedHandleDoesNotCrash`
- `corruptedWrappedStateKeyFails`
- `createAndDestroyIdentity`
- `stateEncryptionUsesFreshNonces`
- `corruptedStateRejectsDeserialization`
- `malformedMessageRejectsDecryption`
- `identitySerializationAndRestoration`
- `persistenceRoundTrip`
- `getPublicKeys`
- `errorMessagesDoNotContainSecrets`
- `stateKeyDeterministicWrap`

## H. Alice ↔ Bob Kotlin/JNI Runtime Result

`endToEndAliceBob` **PASS**.

The Kotlin test creates Alice and Bob identities, generates Bob one-time keys through the `CryptoBridge`, retrieves a one-time key by index through JNI, creates an outbound Olm/PreKey session from Alice to Bob via `cryptoCreateOutboundSession`, encrypts a message via `cryptoEncrypt`, and decrypts it via `cryptoDecrypt`. The round-trip plaintext matched the original `ByteArray` and the message type `0` (PreKey) was produced on first encrypt.

## I. Persistence / Restart Result

`persistenceRoundTrip` and `identitySerializationAndRestoration` **PASS**.

- Identity is created and public keys captured.
- `CryptoBridge.serializeIdentity` wraps the identity pickle through JNI with a fresh AES-GCM encryption using the separately wrapped state key.
- Identity is destroyed and a new handle is obtained by `deserializeIdentity` from the encrypted bytes.
- The restored identity reproduces the same Curve25519 and Ed25519 public key bytes.
- No recovery path is exposed; `allowBackup="false"` is set in `AndroidManifest.xml`.

## J. AES-256-GCM Runtime Result

`stateEncryptionUsesFreshNonces` and `corruptedStateRejectsDeserialization` **PASS**.

- `stateEncryptionUsesFreshNonces` serializes the same identity twice and confirms the two ciphertexts are different, proving a fresh nonce is used per call.
- `corruptedStateRejectsDeserialization` flips a byte in the serialized blob and confirms the deserialization returns an authentication failure instead of any plaintext.

The Rust `CryptoSerializer` produces `[12-byte nonce][ciphertext + 16-byte GCM tag]` and rejects tampered or wrong-key inputs.

## K. Nonce-Generation Review

- Nonce is `12` bytes, generated with `getrandom` per `aes-gcm 0.10.3` `Aes256Gcm::new_randomized_nonce`.
- `stateEncryptionUsesFreshNonces` empirically confirms nonces are not repeated across two serializations of the same identity.
- `CryptoSerializer::zeroize` zeroizes the state key on drop.

## L. Android Keystore Runtime Result

`stateKeyDeterministicWrap` and `corruptedWrappedStateKeyFails` **PASS**.

- The Keystore master key is generated with `KeyGenParameterSpec.Builder(AES/GCM/NoPadding, 256, ENCRYPT/DECRYPT, no user auth)` in `AndroidKeyStore`.
- The 32-byte state key is generated by `SecureRandom`, then wrapped by the non-extractable Keystore key.
- Wrapped format: `[12-byte IV][ciphertext + GCM tag]`.
- `corruptedWrappedStateKeyFails` flips a byte in the wrapped file and confirms `getOrCreateStateKey` fails without exposing the state key.

## M. JNI Safety Result

- `nativeLibraryLoads` **PASS**: `System.loadLibrary("anox_crypto")` succeeds.
- `invalidHandleIsRejected` **PASS**: operations with `0` or unknown handles return `InvalidInput` rather than crashing.
- `destroyedHandleDoesNotCrash` **PASS**: `cryptoDestroyIdentity` removes the handle from a global active-handle set; subsequent use returns an error and the memory is freed only once.
- `getPublicKeys` and `getOneTimeKey` **PASS**: `JByteArray` is passed by value as required by `jni 0.21.1`; `get_array_length` and `set_byte_array_region` succeed.
- No secrets or private key material are returned in error strings (`errorMessagesDoNotContainSecrets` **PASS**).

**Important fix applied:** The original `lib.rs` used `&JByteArray`, `&JClass`, and `&mut JNIEnv` in `extern "system"` functions, which is an ABI mismatch with `jni 0.21.1`. These were corrected to the `jni 0.21.1` convention: `mut env: JNIEnv<'local>`, `class: JClass<'local>`, and `out: JByteArray<'local>` passed by value. This resolved all `UnsatisfiedLinkError`/InvalidSession symptoms.

## N. Rust `cargo test` Result

Command:

```bash
cd crypto/rust && cargo test
```

Result:

```text
test result: ok. 14 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

All 14 Rust crypto unit tests pass after the Android bridge changes.

## O. Android Build Result

- `:android:assembleDebug` and `:android:connectedDebugAndroidTest` build successfully.
- `lib/arm64-v8a/libanox_crypto.so` and `lib/x86_64/libanox_crypto.so` are packaged in the debug APK.
- Native libraries are built in `release` profile (`opt-level = "s"`, `lto = true`) for size and the runtime suite still passes.

## P. GrapheneOS Result

No supported physical Pixel running GrapheneOS was available during this validation.

```text
GRAPHENEOS CRYPTO RUNTIME: UNVERIFIED
```

## Q. Files Changed

| File | Change |
|------|--------|
| `crypto/rust/src/lib.rs` | Re-implemented the `jni 0.21.1` bridge using by-value `JNIEnv`/`JClass`/`JByteArray` parameters; added global active-handle tracking to prevent use-after-free and double-free; added `write_byte_array`/`read_byte_array` helpers. |
| `crypto/rust/src/identity.rs` | Fixed `get_one_time_key_by_index` to iterate the account's one-time key map. |
| `crypto/android/src/androidTest/java/com/anox/crypto/CryptoInstrumentedTest.kt` | Hardened `corruptedWrappedStateKeyFails` to restore the wrapped state key in a `finally` block and avoid poisoning other tests. |
| `android/src/main/jniLibs/arm64-v8a/libanox_crypto.so` | Rebuilt from the corrected Rust source (release profile). |
| `android/src/main/jniLibs/x86_64/libanox_crypto.so` | Rebuilt from the corrected Rust source (release profile). |

## R. Remaining Blockers

None. The Rust unit suite and the connected Android instrumentation suite both pass.

## S. Exact Recommended Next Step

1. Run `:android:assembleRelease` to confirm the release APK packages the rebuilt `libanox_crypto.so` artifacts without error.
2. Conduct an independent security review of the Rust crypto foundation and the JNI boundary.
3. Only after the above review, and within the explicit scope, begin work on backend, account registration, messaging, push, attachments, multi-device, or recovery.

---

**Conclusion:** Rust crypto and Android/JNI runtime integration are functionally verified at the implemented test level.
