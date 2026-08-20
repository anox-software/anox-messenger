# anoX V1 — Project State

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## Implementation Status

| Component | Status |
|-----------|--------|
| Rust crypto crate (`anox_crypto`) | `cargo test` **15/15 PASS** |
| Android project build + APK packaging | **PASS** locally (accepted from prior environment) |
| Android connected instrumentation | **35/35 PASS** (accepted from prior environment; NOT run in CI) |
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
| Git/GitHub baseline | Remote connected; `main` + tag pushed; CI created; Rust CI green; **Android CI blocked by toolchain incompatibility** |

## Actual Toolchain (source of truth from checked-in files)

- AGP `8.13.2` — `build.gradle.kts` line 3
- Kotlin `1.9.20` — `build.gradle.kts` line 4
- Gradle Wrapper `9.3.1` — `gradle/wrapper/gradle-wrapper.properties` line 3
- JDK `17`
- NDK `26.2.11394342` (r26c)
- Rust `1.97.1`
- `cargo-ndk` `4.1.2`
- `compileSdk`/`targetSdk` `34`, `minSdk` `26`

## Toolchain Reconciliation

Earlier documents claimed `AGP 9.1.1` and `Kotlin 2.2.10`. Those values do not exist in any checked-in build file. The first commit (`7db20fa`) already contained `AGP 8.13.2`, `KGP 1.9.20`, and Gradle Wrapper `9.3.1`.

**No supported Gradle 8.x wrapper exists for `AGP 8.13.2` + `KGP 1.9.20`:**

- AGP 8.13.2 requires Gradle `≥ 8.13`.
- KGP 1.9.20 supports Gradle `6.8.3 – 8.1.1`.

These ranges do not overlap. A wrapper-only fix is impossible. The Android CI failure is not caused by a missing wrapper version; it is caused by a mismatched toolchain that requires either an AGP/Kotlin downgrade or a planned AGP/Kotlin upgrade.

## Architecture Highlights

- One active device per account in V1.
- No account or crypto recovery.
- vodozemac/Olm is the E2EE direction.
- No OpenPGP, no libsignal, no custom Double Ratchet.
- Device auth (Ed25519) separate from E2EE identity.
- Supabase/PostgreSQL as backend infrastructure, not a trust/recovery authority.

## Open Items

- Decide and execute a toolchain-alignment strategy to make Android CI green.
- Branch protection and GitHub secret scanning are unavailable on the free private plan.
- See `docs/current/OPEN_ARCHITECTURE_ITEMS.md`.

## Historical Context

Older Raw1.1 documents are in `docs/history/raw1.1/` and must not be used as current requirements.

## Next Engineering Task

A dedicated `PROMPT-TOOLCHAIN-ALIGNMENT` to choose between:

1. Downgrading AGP/Kotlin/Gradle to a mutually compatible set, or
2. Upgrading to the intended AGP 9.1.1 / Kotlin 2.2.10 / Gradle 9.3.1 baseline.

After the toolchain is aligned, proceed with `PROMPT-007 — Device Authentication Foundation` following an independent security review.
