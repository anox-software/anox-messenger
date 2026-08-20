# ANOX V1 — PROMPT-005C: JNI/FFI Type Safety, Panic Containment & Release Build Validation Report

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## Important

This report documents functional verification and hardening at the implemented test level. It does **not** claim production security, independent audit, unhackability, or complete endpoint security.

---

## A. Previous Handle Architecture

`crypto/rust/src/lib.rs` previously used a single shared, untyped registry:

```rust
static ACTIVE_HANDLES: LazyLock<Mutex<HashSet<usize>>>
```

All `Identity` and `Session` raw pointer values were inserted into the same `HashSet`. `is_active(handle)` only verified that *some* live object existed at the address. `release_handle::<T>(handle)` returned a `*mut T` after removing the address, relying entirely on the JVM/Kotlin side to pass the right `jlong` into the right function.

This allowed a live `Identity` handle to be accepted by a `Session` function (and vice versa), because the shared set only knew the address, not the type. The resulting `unsafe` cast to `*mut Session` or `*mut Identity` was undefined behavior.

## B. Final Handle Architecture

The shared `ACTIVE_HANDLES` was replaced by two strictly separated registries:

```rust
static ACTIVE_IDENTITIES: LazyLock<Mutex<HashSet<usize>>>;
static ACTIVE_SESSIONS: LazyLock<Mutex<HashSet<usize>>>;
```

Each exported JNI function uses the type-appropriate registry:

| Type | Functions |
|------|-----------|
| `Identity` | `cryptoCreateIdentity`, `cryptoDestroyIdentity`, `cryptoGetCurve25519PublicKey`, `cryptoGetEd25519PublicKey`, `cryptoGenerateOneTimeKeys`, `cryptoOneTimeKeysCount`, `cryptoGetOneTimeKey`, `cryptoSerializeIdentity`, `cryptoDeserializeIdentity` |
| `Session` | `cryptoCreateOutboundSession`, `cryptoCreateInboundSession`, `cryptoEncrypt`, `cryptoDecrypt`, `cryptoDestroySession`, `cryptoSerializeSession`, `cryptoDeserializeSession` |

`Identity` functions call `is_identity_active(handle)` and cast only after validation. `Session` functions call `is_session_active(handle)`. A live `Identity` handle is therefore rejected by every `Session` function, and a live `Session` handle is rejected by every `Identity` function.

## C. Wrong-Type Handle Protection

New Android instrumentation tests prove the following do not crash and return `CryptoResult.Failure`:

- `identityHandleUsedAsSessionDecryptFails`
- `identityHandleUsedAsSessionEncryptFails`
- `sessionHandleUsedAsIdentitySerializeFails`
- `sessionHandleUsedAsIdentityPublicKeyFails`

Rust side: the handle is rejected before any `unsafe` pointer dereference. The `&*(handle as *const Identity)` or `&mut *(handle as *mut Session)` cast occurs only after the type-specific registry confirms the handle is active.

## D. Stale-Handle Protection

New tests:

- `destroyedIdentityReusedFails`
- `destroyedSessionReusedFails`

When `cryptoDestroyIdentity`/`cryptoDestroySession` are called, `release_identity`/`release_session` remove the handle from the typed registry and then `Box::from_raw` the pointer. Subsequent use of the same `jlong` is rejected because the handle is no longer in the registry.

## E. Double-Destroy Protection

New tests:

- `identityDestroyTwiceIsSafe`
- `sessionDestroyTwiceIsSafe`

`release_identity`/`release_session` return `Option<*mut T>` only the first time. The second call sees the handle already absent from the registry and returns `None`; no second `Box::from_raw` is performed. No double-free occurs.

## F. Panic Containment Review

### Current panic configuration

`crypto/rust/Cargo.toml` release profile now contains:

```toml
[profile.release]
opt-level = "s"
lto = true
panic = "abort"
```

`panic = "abort"` ensures that, in the worst case, a Rust panic aborts the process instead of unwinding across the JNI/FFI boundary. Unwinding across FFI is undefined behavior; this configuration prevents it.

### Panic sources reviewed

| Function / call | Risk | Mitigation |
|-----------------|------|------------|
| `Box::into_raw` / `Box::from_raw` | Double-free or use-after-free if pointers are not tracked | Two typed registries ensure each pointer is freed at most once and only while active. |
| `CryptoSerializer::new` | `copy_from_slice` panicked if key length != 32 | Now returns `Result<Self, CryptoSerializerError::InvalidKeyLength>`. |
| `JNIEnv` array access | `get_array_length` may fail for `null`/invalid refs | All calls use `.ok()` and `.is_err()`; failures return error codes. |
| `vodozemac` calls | Could theoretically panic on malformed input | All public APIs return `Result`; invalid inputs are rejected before calling vodozemac. |

A recoverable malformed Java/Kotlin input now returns a negative error code and does not trigger a Rust panic.

### Note

Centralized `catch_unwind` at the JNI boundary was not added because `JNIEnv` is not `UnwindSafe` and because `panic = "abort"` already prevents cross-boundary unwinding. Future hardening can wrap `AssertUnwindSafe` around the Rust-only computation layer if desired.

## G. Allocation Ownership Review

### `cryptoCreateInboundSession`

The previous ordering allocated `Box::new(sess)`, registered the pointer, and then attempted `set_long_array_region`. If the JNI array write failed, the `Session` pointer was already registered and leaked.

New ordering:

1. Decrypt/create the `Session`.
2. Write `out_plaintext`.
3. `Box::into_raw(Box::new(sess))` to obtain the pointer.
4. Write the pointer into the `out_session` `JLongArray`.
5. If the JNI write fails, immediately `Box::from_raw(ptr)` to free the `Session` and return the error.
6. Only after the Java array has accepted the pointer, call `register_session(ptr)`.

This ensures every successful allocation has exactly one owner at every step and no JNI-failure path leaks a `Session`.

### `cryptoCreateOutboundSession` and `cryptoDeserializeSession`

These allocate, then immediately `register_session` only after the pointer is confirmed valid and the Java side will receive it. `cryptoCreateOutboundSession` returns the `jlong` directly to Kotlin; `cryptoDeserializeSession` returns `0` on error and frees nothing because the allocation only happens on `Ok`.

## H. Serializer Input Validation

`CryptoSerializer::new(key: &[u8])` now returns `Result<Self, CryptoSerializerError>`. It validates the key length before copying:

```rust
pub fn new(key: &[u8]) -> Result<Self, CryptoSerializerError> {
    if key.len() != 32 {
        return Err(CryptoSerializerError::InvalidKeyLength);
    }
    let mut key_array = [0u8; 32];
    key_array.copy_from_slice(key);
    Ok(Self { key: key_array })
}
```

`Identity::serialize`, `Identity::deserialize`, `Session::serialize`, and `Session::deserialize` propagate the new `Result` with `?`. Rust unit test `test_invalid_state_key_length` verifies:

- 31-byte key is rejected.
- 32-byte key is accepted.
- `Identity::serialize` with a 16-byte key is rejected.

## I. State Envelope Version Decision

The current protected-state format remains `[12-byte nonce][ciphertext + 16-byte GCM tag]` with **no explicit version byte**. Adding a version now would break the existing round-trip tests and require a migration strategy beyond the scope of this task.

**Decision:** Deferred to `PROMPT-006 — Secure Local State & Key Lifecycle Freeze`.

The lack of an explicit version is recorded as an open hardening item in `docs/reports/current-code-gap-audit.md`.

## J. Logging / Security Review

### Kotlin (`CryptoBridge.kt`)

- `Log.e(TAG, "...", e)` is used for exceptions. Exception messages and stack traces can leak internal call structure; they do not currently contain plaintext or private keys.
- `CryptoError` messages are generic (e.g., "Invalid input parameters", "Invalid ciphertext").
- `UnknownError` logs the numeric native error code, not key material.

### Rust

- No `println!`, `eprintln!`, or logging macros in `lib.rs` or `serialization.rs`.
- Error strings are generic and do not include key bytes, plaintext, or session state.

### Production guidance

Before production, `CryptoBridge.kt` `Log.e` calls should be gated by a `BuildConfig.DEBUG` flag or routed through a redacted logger so that:

- exception stack traces are not printed in release builds;
- native error codes are still available for diagnostics but not tied to user data;
- no plaintext, private key, state key, or ciphertext appears in logs.

No functional logging code was changed in this task; only the guidance was documented.

## K. Rust Test Results

Command:

```bash
cd crypto/rust && cargo test
```

Result:

```text
test result: ok. 15 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

New test: `test_invalid_state_key_length`.

## L. Android Connected Test Results

Command:

```bash
./gradlew :android:clean :android:connectedDebugAndroidTest
```

Result:

```text
Starting 27 tests on anox_api34_arm64(AVD) - 14
Finished 27 tests on anox_api34_arm64(AVD) - 14
BUILD SUCCESSFUL
```

The 19 previous tests remain; 8 new tests were added:

- `identityHandleUsedAsSessionDecryptFails`
- `identityHandleUsedAsSessionEncryptFails`
- `sessionHandleUsedAsIdentitySerializeFails`
- `sessionHandleUsedAsIdentityPublicKeyFails`
- `destroyedIdentityReusedFails`
- `destroyedSessionReusedFails`
- `identityDestroyTwiceIsSafe`
- `sessionDestroyTwiceIsSafe`

No existing test was deleted.

## M. Release Build Result

Command:

```bash
./gradlew :android:assembleRelease
```

Result:

```text
BUILD SUCCESSFUL
```

Output:

```text
android/build/outputs/apk/release/android-release-unsigned.apk
  lib/arm64-v8a/libanox_crypto.so
  lib/x86_64/libanox_crypto.so
```

Notes:

- The APK is **unsigned**. A full distributable release would require a release signing config.
- Native libraries are packaged for both `arm64-v8a` and `x86_64`.
- `stripReleaseDebugSymbols` reported `Unable to strip libanox_crypto.so` and packaged it as-is. This did not block the build.
- No `panic = "abort"` runtime issue; release `.so` was built with `panic = "abort"`.

## N. GrapheneOS Status

No physical Pixel running GrapheneOS was available.

```text
GRAPHENEOS CRYPTO RUNTIME: UNVERIFIED
```

## O. Files Changed

| File | Change |
|------|--------|
| `crypto/rust/src/lib.rs` | Replaced shared untyped handle registry with `ACTIVE_IDENTITIES` and `ACTIVE_SESSIONS`; fixed `cryptoCreateInboundSession` ownership ordering. |
| `crypto/rust/src/serialization.rs` | `CryptoSerializer::new` now returns `Result` and validates 32-byte key length. |
| `crypto/rust/src/identity.rs` | Propagated `CryptoSerializer::new` `Result` with `?`. |
| `crypto/rust/src/session.rs` | Propagated `CryptoSerializer::new` `Result` with `?`. |
| `crypto/rust/src/tests.rs` | Added `test_invalid_state_key_length`; updated `CryptoSerializer::new` usage. |
| `crypto/rust/Cargo.toml` | Added `panic = "abort"` to release profile. |
| `crypto/android/src/androidTest/java/com/anox/crypto/CryptoInstrumentedTest.kt` | Added 8 new wrong-type/stale/double-destroy tests. |
| `android/src/main/jniLibs/arm64-v8a/libanox_crypto.so` | Rebuilt with release profile and typed handle registry. |
| `android/src/main/jniLibs/x86_64/libanox_crypto.so` | Rebuilt with release profile and typed handle registry. |

## P. Remaining Blockers

None. Rust `cargo test` and Android connected tests both pass after the hardening changes.

## Q. Exact Recommended Next Step

1. Configure a release signing configuration and run `:android:assembleRelease` on a CI agent to confirm the signed APK packaging pipeline.
2. Conduct an independent security review of the Rust/JNI boundary.
3. Only after the review, begin `PROMPT-006 — Secure Local State & Key Lifecycle Freeze` (envelope versioning, local DB, etc.).

---

## Conclusion

The anoX Rust crypto foundation and Android/JNI runtime boundary are functionally verified and memory-safety hardened at the implemented test level:

- wrong-type handles fail safely;
- stale handles fail safely;
- double-destroy is safe;
- no raw pointer is dereferenced before type validation;
- `panic = "abort"` prevents cross-boundary unwinding;
- `CryptoSerializer::new` no longer panics on bad key length;
- the `cryptoCreateInboundSession` leak path is closed;
- release build produces an APK with both native libraries;
- Rust: 15/15 PASS;
- Android: 27/27 PASS.
