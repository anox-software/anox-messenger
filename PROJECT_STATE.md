# anoX V1 — Project State

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## Implementation Status

| Component | Status |
|-----------|--------|
| Rust crypto crate (`anox_crypto`) | `cargo test` **15/15 PASS** |
| Android project build + APK packaging | PASS (debug + release APK) |
| Android connected instrumentation | **35/35 PASS** on arm64 emulator API 34 |
| JNI bridge (vodozemac 0.10.0, aes-gcm 0.10.3) | PASS at implemented test level |
| Android Keystore state-key wrapping | PASS at implemented test level |
| Versioned protected state envelope | PASS at implemented test level |
| Atomic local persistence | PASS at implemented test level |
| MainActivity / UI | Minimal placeholder only |
| Backend code | Empty / not implemented |
| Database | Not implemented |
| Account/auth registration | Not implemented |
| Real chat UI | Not implemented |
| Contacts | Not implemented |
| Push | Not implemented |
| Attachments | Not implemented |
| Git/GitHub baseline | Local repository, baseline, and origin remote configured; GitHub authentication pending before push |

## Toolchain

- AGP `9.1.1`
- Kotlin `2.2.10`
- Gradle Wrapper `9.3.1`
- JDK 17
- NDK `26.2.11394342` (r26c)
- Rust `1.97.1`
- `cargo-ndk` `4.1.2`
- `compileSdk`/`targetSdk` `34`, `minSdk` `26`

## Architecture Highlights

- One active device per account in V1.
- No account or crypto recovery.
- vodozemac/Olm is the E2EE direction.
- No OpenPGP, no libsignal, no custom Double Ratchet.
- Device auth (Ed25519) separate from E2EE identity.
- Supabase/PostgreSQL as backend infrastructure, not a trust/recovery authority.

## Open Items

See `docs/current/OPEN_ARCHITECTURE_ITEMS.md`.

## Historical Context

Older Raw1.1 documents are in `docs/history/raw1.1/` and must not be used as current requirements.

## Next Engineering Task

Connect the local repository to the private GitHub repository, then proceed to `PROMPT-007 — Device Authentication Foundation` after an independent security review.
