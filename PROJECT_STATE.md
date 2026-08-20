# anoX V1 — Project State

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-20

---

## Implementation Status

| Component | Status |
|-----------|--------|
| Rust crypto crate (`anox_crypto`) | `cargo test` **15/15 PASS** |
| Android project build + APK packaging | **PASS** locally and in CI (`assembleDebug` + `assembleRelease`) |
| Android connected instrumentation | **35/35 PASS** (accepted from prior environment; **NOT RUN IN CI**) |
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
| Git/GitHub baseline | **FULL PASS** — remote connected; `main` + tag pushed; CI green on `main` |

## Actual Toolchain (source of truth from checked-in files)

- AGP `8.13.2` — `build.gradle.kts` line 3
- KGP `2.4.10` — `build.gradle.kts` line 4
- Compose compiler plugin `2.4.10` — `build.gradle.kts` line 5
- Gradle Wrapper `9.3.1` — `gradle/wrapper/gradle-wrapper.properties` line 3
- JDK `17`
- NDK `26.2.11394342` (r26c)
- Rust `1.97.1`
- `cargo-ndk` `4.1.2`
- `compileSdk`/`targetSdk` `34`, `minSdk` `26`

## Toolchain Reconciliation

Earlier documentation incorrectly listed `AGP 9.1.1` and `Kotlin 2.2.10`. Those values never appeared in `build.gradle.kts`, `android/build.gradle.kts`, or `gradle-wrapper.properties`. The first commit `7db20fa` already used `AGP 8.13.2`, `KGP 1.9.20`, and Gradle `9.3.1`.

The previous `KGP 1.9.20` was incompatible with Gradle `9.3.1` and `AGP 8.13.2` because `KGP 1.9.20` only supports Gradle `≤ 8.1.1` while `AGP 8.13.2` requires Gradle `≥ 8.13`.

TOOLCHAIN-001 fixed this by:

- Upgrading `KGP` to `2.4.10` (officially supports Gradle `7.6.3–9.5.0` and AGP `8.5.2–9.1.0`).
- Adding the new `org.jetbrains.kotlin.plugin.compose` plugin `2.4.10`.
- Removing `composeOptions.kotlinCompilerExtensionVersion`.
- Replacing `kotlinOptions { jvmTarget = "17" }` with the `compilerOptions` DSL.

`compileSdk`, `targetSdk`, `minSdk`, and `NDK` were **not** changed.

## Architecture Highlights

- One active device per account in V1.
- No account or crypto recovery.
- vodozemac/Olm is the E2EE direction.
- No OpenPGP, no libsignal, no custom Double Ratchet.
- Device auth (Ed25519) separate from E2EE identity.
- Supabase/PostgreSQL as backend infrastructure, not a trust/recovery authority.

## Open Items

- Branch protection and GitHub secret scanning remain unavailable on the free private plan.
- See `docs/current/OPEN_ARCHITECTURE_ITEMS.md`.

## Historical Context

Older Raw1.1 documents are in `docs/history/raw1.1/` and must not be used as current requirements.

## Next Engineering Task

1. Proceed with `PROMPT-007 — Device Authentication Foundation` after an independent security review.
