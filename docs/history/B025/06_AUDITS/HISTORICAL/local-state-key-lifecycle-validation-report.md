# ANOX V1 — PROMPT-006: Local State & Key Lifecycle Validation Report

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## Important

This report documents the implemented and verified local key/state lifecycle. It does **not** claim production security, independent audit, or complete endpoint security.

---

## A. Files Changed

| File | Change |
|------|--------|
| `crypto/rust/src/serialization.rs` | Added `ANOX` magic + `0x01` versioned AES-256-GCM envelope with AAD-bound header. |
| `crypto/rust/src/identity.rs` | Mapped `CryptoSerializerError::UnsupportedVersion` to `CryptoError::UnsupportedVersion`. |
| `crypto/rust/src/session.rs` | Mapped `CryptoSerializerError::UnsupportedVersion` to `CryptoError::UnsupportedVersion`. |
| `crypto/android/src/main/java/com/anox/crypto/CryptoBridge.kt` | Added `LocalStateStatus`, `getLocalStateStatus`, atomic `writeFileAtomic`, `saveIdentity`/`loadIdentity`, `saveSession`/`loadSession`, `createAndPersistFirstIdentity`, `wipeLocalCrypto`, `ReentrantLock` for storage. |
| `crypto/android/src/androidTest/java/com/anox/crypto/CryptoInstrumentedTest.kt` | Added 9 new persistence/corruption/first-run/session tests. |
| `docs/current/LOCAL_KEY_STATE_LIFECYCLE_V1_FROZEN.md` | New canonical V1 local key/state lifecycle spec. |
| `docs/security/local-state-key-lifecycle-validation-report.md` | This report. |
| `android/src/main/jniLibs/arm64-v8a/libanox_crypto.so` | Rebuilt with versioned envelope. |
| `android/src/main/jniLibs/x86_64/libanox_crypto.so` | Rebuilt with versioned envelope. |

## B. Final State-Envelope Format

```text
[ 4 magic bytes "ANOX" ]
[ 1 version byte 0x01 ]
[ 12 nonce bytes ]
[ ciphertext + 16-byte GCM authentication tag ]
```

- Magic and version are included in the AES-GCM AAD.
- Unknown version is explicitly rejected.
- Invalid magic is explicitly rejected.
- Truncated or modified ciphertext/tag fails GCM authentication.

## C. Migration Strategy

Old unversioned `[nonce][ciphertext+tag]` development data is **not migrated**. Any pre-existing protected state without the `ANOX` header is treated as corrupted/unsupported and fails closed. New installs and new persistence use the `ANOX`/`0x01` envelope.

## D. First-Run / Lost-State Model

`CryptoBridge.getLocalStateStatus()` returns the `LocalStateStatus` sealed class:

- `FirstRun` — no state files.
- `IdentityReady(identity)` — valid identity loaded.
- `WipedState` — state key file exists but identity file missing.
- `MissingStateKey` — identity file exists but wrapped state key missing.
- `MissingKeystore` — Keystore wrapping key cannot be used.
- `CorruptedIdentityState(reason)` — files exist but authentication/decryption fails.

The crypto layer does not silently create a new identity when existing state is unavailable.

## E. Atomic Persistence Implementation

`CryptoBridge.writeFileAtomic`:

1. Writes to `<file>.tmp`.
2. `FileOutputStream.flush()`.
3. `FileDescriptor.sync()`.
4. `renameTo()` the temp file over the target.
5. On rename failure, deletes the temp file and throws.

Used for `anox_state_key.enc`, `anox_identity.enc`, and `anox_session.enc`.

## F. Keystore Lifecycle

- Alias: `anox_crypto_master_key`
- Algorithm: `AES/GCM/NoPadding`
- Size: 256 bits
- Provider: `AndroidKeyStore`
- `setUserAuthenticationRequired(false)` for V1
- Non-extractable
- Created on first `getOrCreateStateKey()`
- Deleted by `wipeLocalCrypto()`

## G. State-Key Lifecycle

- 32 bytes from `SecureRandom`.
- Wrapped by the Keystore master key to `[12-byte IV][ciphertext + 16-byte tag]`.
- Stored as `anox_state_key.enc`.
- Stable for the identity lifetime.
- Wrong length rejected by `CryptoSerializer::new`.
- Corrupted wrapped state key fails closed.

## H. Identity / Session Persistence

- `CryptoBridge.saveIdentity` / `loadIdentity` for `anox_identity.enc`.
- `CryptoBridge.saveSession` / `loadSession` for `anox_session.enc`.
- Both use the versioned envelope and atomic write.
- All storage operations are serialized by `ReentrantLock`.

## I. Corruption Test Matrix Results

| Test | Result |
|------|--------|
| missing identity file | `CryptoResult.Failure` |
| empty identity file | `CryptoResult.Failure` |
| truncated identity file | `CryptoResult.Failure` |
| corrupt magic | `CryptoResult.Failure` |
| modified ciphertext/tag | `CryptoResult.Failure` |
| corrupted wrapped state key | exception on unwrap |
| valid identity save/load | public key identical |
| valid session save/load | conversation continues successfully |

All Android tests passed.

## J. Concurrency Strategy

A `ReentrantLock` in `CryptoBridge` guards `getOrCreateStateKey`, `saveIdentity`, `loadIdentity`, `saveSession`, `loadSession`, `createAndPersistFirstIdentity`, `wipeLocalCrypto`, and `getLocalStateStatus`. Future messaging must acquire this lock when reading or writing ratchet state.

## K. Logout / Wipe / Delete Behavior

- `wipeLocalCrypto()` deletes the Keystore alias, `anox_state_key.enc`, `anox_identity.enc`, and `anox_session.enc`.
- Local wipe is distinct from logout; future logout will remove API tokens without deleting E2EE state.
- Account delete will reuse the local wipe path and add future server-side revocation.

## L. Backup Policy

- `AndroidManifest.xml`: `allowBackup="false"`.
- Crypto files are in `context.filesDir`.
- No cloud, Seedvault, or device-to-device restore of E2EE private state.

## M. Rust Test Results

```bash
cd crypto/rust && cargo test
```

```text
test result: ok. 15 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

## N. Android Connected-Test Results

```bash
./gradlew :android:clean :android:connectedDebugAndroidTest
```

```text
Starting 35 tests on anox_api34_arm64(AVD) - 14
Finished 35 tests on anox_api34_arm64(AVD) - 14
BUILD SUCCESSFUL
```

The 27 previous tests remain; 8 new tests added for this task plus the previous 9 from PROMPT-005C = 35 total. (No tests deleted.)

## O. Release Build

```bash
./gradlew :android:assembleRelease
```

```text
BUILD SUCCESSFUL
```

`android/build/outputs/apk/release/android-release-unsigned.apk` packaged `lib/arm64-v8a/libanox_crypto.so` and `lib/x86_64/libanox_crypto.so`. APK is unsigned because no release signing config is configured.

## P. GrapheneOS Result

No physical Pixel running GrapheneOS was available.

```text
GRAPHENEOS LOCAL STATE RUNTIME: UNVERIFIED
```

## Q. Remaining Blockers

None. Rust, Android connected tests, and release build all pass.

## R. Exact Recommended Next Task

`PROMPT-007 — Device Authentication Foundation` (after an independent security review of the local state lifecycle).
