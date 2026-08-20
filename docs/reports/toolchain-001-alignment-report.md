# TOOLCHAIN-001 — Android Toolchain Alignment Report

**Status:** CURRENT  
**Branch:** `toolchain-001/android-toolchain-alignment`  
**Pull Request:** https://github.com/anox-admin/ax-messenger/pull/1  
**Report date:** 2026-08-20

---

## 1. Objective

Repair the checked-in Android build-toolchain inconsistency and restore green Android CI without introducing application functionality, Device Authentication, or cryptographic changes.

## 2. Actual source of truth before changes

| Setting | Value | Source file | Line(s) |
|---------|-------|-------------|---------|
| AGP | `8.13.2` | `build.gradle.kts` | 3 |
| KGP | `1.9.20` | `build.gradle.kts` | 4 |
| Gradle Wrapper | `9.3.1` | `gradle/wrapper/gradle-wrapper.properties` | 3 |
| `compileSdk` | `34` | `android/build.gradle.kts` | 8 |
| `targetSdk` | `34` | `android/build.gradle.kts` | 13 |
| `minSdk` | `26` | `android/build.gradle.kts` | 12 |
| `ndkVersion` | `26.2.11394342` | `android/build.gradle.kts` | 16 |
| Compose compiler config | `kotlinCompilerExtensionVersion = "1.5.4"` | `android/build.gradle.kts` | 47–48 |

## 3. Historical discrepancy

Earlier `PROJECT_STATE.md` and `FORTSCHRITT.md` listed `AGP 9.1.1` and `Kotlin 2.2.10`. Git history shows these values were never present in `build.gradle.kts` or `android/build.gradle.kts`.

The first baseline commit `7db20fa` already contained `AGP 8.13.2`, `KGP 1.9.20`, and the Gradle `9.3.1` wrapper. The `9.1.1` / `2.2.10` values came from the original user task description, not from the repository itself.

## 4. Incompatibility identified

`AGP 8.13.2` requires Gradle `≥ 8.13`, while `KGP 1.9.20` only supports Gradle `≤ 8.1.1`. No single Gradle version satisfies both, so a wrapper-only fix was impossible.

## 5. Selected target toolchain

The lowest-risk, mutually supported modern combination that preserves AGP `8.13.2` and Gradle `9.3.1` is:

| Component | Final version | Rationale |
|-----------|---------------|-----------|
| AGP | `8.13.2` | Unchanged; supports `compileSdk 34` and Gradle `≥ 8.13`. |
| Gradle Wrapper | `9.3.1` | Unchanged; within KGP `2.4.10` and AGP `8.13.2` support ranges. |
| KGP | `2.4.10` | Authoritative compatibility: Gradle `7.6.3–9.5.0`, AGP `8.5.2–9.1.0`. |
| Compose compiler plugin | `2.4.10` | Bundled/controlled by `org.jetbrains.kotlin.plugin.compose`. |
| JDK | `17` | Unchanged; required by AGP 8.x. |
| `compileSdk` / `targetSdk` | `34` | Unchanged. |
| `minSdk` | `26` | Unchanged. |
| NDK | `26.2.11394342` | Unchanged. |

No `compileSdk`, `targetSdk`, `minSdk`, or NDK changes were needed.

## 6. Changes applied

### `build.gradle.kts`

- Upgraded `org.jetbrains.kotlin.android` from `1.9.20` to `2.4.10`.
- Added `org.jetbrains.kotlin.plugin.compose` version `2.4.10` with `apply false`.

### `android/build.gradle.kts`

- Added `org.jetbrains.kotlin.plugin.compose` plugin.
- Removed deprecated `kotlinOptions { jvmTarget = "17" }`.
- Removed `composeOptions { kotlinCompilerExtensionVersion = "1.5.4" }`.
- Added top-level:

```kotlin
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}
```

## 7. What was not changed

- Application source code
- Rust crypto crate (`anox_crypto`) and JNI bindings
- E2EE / local-state architecture
- `compileSdk`, `targetSdk`, `minSdk`, `NDK`
- `.so` native libraries: `arm64-v8a/libanox_crypto.so` and `x86_64/libanox_crypto.so`
- Security invariants (no recovery, one device, local-only keys)

## 8. Local testing

| Test | Command | Result |
|------|---------|--------|
| Rust crypto tests | `cd crypto/rust && cargo test` | **15/15 PASS** |

The local macOS environment does not have a JDK/Android SDK, so `./gradlew` builds could not be executed locally. CI was used for Android build validation.

## 9. GitHub Actions CI

Workflow: `anoX V1 CI`  
Run: `32342258423`  
URL: https://github.com/anox-admin/ax-messenger/actions/runs/32342258423

| Job | Result |
|-----|--------|
| `Rust crypto tests` | **PASS** |
| `Android debug build` | **PASS** |
| `Android release compile smoke` | **PASS** |

All three required jobs passed.

## 10. Connected Android instrumentation

The GitHub Actions environment does not provide an Android emulator, so the existing 35 connected Android instrumentation tests were **NOT RUN IN CI**. The historical `35/35 PASS` evidence from the prior local environment remains accepted.

## 11. Regression inspection

- `git diff main..HEAD --stat` shows only `build.gradle.kts` and `android/build.gradle.kts` changed.
- Native libraries `android/src/main/jniLibs/{arm64-v8a,x86_64}/libanox_crypto.so` are unchanged.
- No `local.properties`, `.env`, secrets, or build artifacts were committed.

## 12. Remaining items

- Branch protection and secret scanning are unavailable on the free private GitHub plan (same as GIT-001).
- After review, merge `toolchain-001/android-toolchain-alignment` to `main`.
- No functional product feature was introduced; functional progress remains at approximately 27%.

## 13. Recommended next step

1. Review and merge PR #1.
2. Update `main` branch `PROJECT_STATE.md` / `FORTSCHRITT.md` to reflect green CI.
3. Proceed with `PROMPT-007 — Device Authentication Foundation` after an independent security review.
