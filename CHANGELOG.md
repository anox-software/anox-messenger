# Changelog

All notable changes to the anoX Messenger project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## B-025 Authority Notice

- The current architecture authority is **B-025** (`docs/authority/B025/`).
- Open architecture items are now tracked in `docs/current/OPEN_ARCHITECTURE_ITEMS.md` and `docs/authority/B025/IMPLEMENTATION_GAP_MATRIX.md`.
- The historical entries below are retained for context.

## [Unreleased]

### Added
- Rust crypto crate (`anox_crypto`) wrapping vodozemac 0.10.0.
- AES-256-GCM local state protection using Android Keystore-wrapped state key.
- JNI bridge between Kotlin and Rust.
- Android CryptoBridge (`CryptoBridge.kt`, `CryptoNative.kt`, `CryptoError.kt`).
- `allowBackup=false` in `AndroidManifest.xml` to prevent cloud restoration of E2EE state.
- `arm64-v8a` and `x86_64` native libraries (`libanox_crypto.so`).
- Android instrumentation test suite covering identity, keys, encryption, Keystore wrapping, persistence, and error safety.

### Changed
- Crypto state protection moved from AES-CBC concept to AES-256-GCM authenticated encryption.
- `OlmMessage` / message handling aligned with actual vodozemac Olm API.

### Security
- E2EE identity and session state stay on-device.
- Private E2EE state never crosses the JNI boundary.
- Active-handle registry prevents double-free and use-after-free in the JNI bridge.

### Verified
- Rust `cargo test`: **14/14 PASS**.
- Android `:android:connectedDebugAndroidTest`: **19/19 PASS** on `anox_api34_arm64` emulator (API 34).
- GrapheneOS runtime: **UNVERIFIED** (no physical device available).

### Known Open Items
- Final DB schema not frozen.
- Backend/account/auth/messaging/contacts/push/attachments not implemented.
- Certificate pinning, exact auth/token contract, and push provider selection remain open.
- See `docs/current/OPEN_ARCHITECTURE_ITEMS.md` and `docs/reports/current-code-gap-audit.md`.
