# ANOX V1 — GIT-001: Secure Git / GitHub Baseline Report

**Status:** CURRENT  
**Report date:** 2026-08-19

---

## A. Previous Git state

No `.git` directory existed in the project root when GIT-001 started. Git was not initialized. No prior branches, commits, or remotes were present.

## B. `.gitignore` changes

The `.gitignore` was hardened to:

- Ignore `.jks`, `.keystore`, and `.p12` files.
- Ignore `crypto/rust/target/` and all `target/` directories.
- Ignore `.kotlin/` build daemon state.
- Ignore `__MACOSX/` resource-fork directories.

Already ignored: `.DS_Store`, `.idea/`, `.gradle/`, `build/`, `local.properties`, `.env`, `*.log`, `.codeium/`.

## C. Secret audit result

No production secrets were found in the working tree at baseline.

| Checked | Result |
|---------|--------|
| `.env*` | Not present |
| `local.properties` | Present; contains only `sdk.dir` and is ignored |
| `*.jks` / `*.keystore` / `*.p12` | Not present |
| `*.pem` / `*.crt` private certificates | Not present |
| `google-services.json` | Not present |
| Hardcoded API keys / tokens | Not found |
| `BEGIN ... PRIVATE KEY` blocks | Not found |

Post-push `git ls-tree` confirmed no `local.properties`, `.env`, `.jks`, `.keystore`, `.p12`, build caches, `crypto/rust/target/`, or private PEM files were pushed.

## D. Files intentionally excluded

- `local.properties`
- `android/build/`
- `crypto/rust/target/`
- `.gradle/`
- `.idea/`
- `.kotlin/`
- `.DS_Store`
- signing key files

## E. Baseline test results

| Test | Result |
|------|--------|
| `cargo test` (crypto/rust) | **15/15 PASS** (re-run in GIT-001C session) |
| Android connected instrumentation | **35/35 PASS** (accepted from prior run; not re-run in CI) |
| `./gradlew :android:assembleRelease` | **BUILD SUCCESSFUL** (accepted from prior run; CI not yet green) |

## F. Baseline commit hash

```text
7db20fa4df8dc70392afd803fabaaf20c0b50d7d
```

## G. Baseline tag

```text
v1-foundation-baseline -> 7db20fa4df8dc70392afd803fabaaf20c0b50d7d
```

## H. GitHub repository result

```text
https://github.com/anox-admin/ax-messenger.git
```

- Remote added as `origin`.
- `main` pushed.
- `v1-foundation-baseline` tag pushed.

## I. Repository visibility

Verified as **PRIVATE** via the GitHub REST API.

## J. Remote result

```text
origin	https://github.com/anox-admin/ax-messenger.git (fetch)
origin	https://github.com/anox-admin/ax-messenger.git (push)
```

## K. Branch / ruleset protection

GitHub returned `403: Upgrade to GitHub Pro or make this repository public to enable this feature.` for both the branch protection and ruleset APIs.

**Branch protection / ruleset: UNAVAILABLE** on the current free private plan.

## L. Secret scanning / push protection

GitHub did not expose `security_and_analysis` settings for this repository.

**Secret scanning / push protection: UNAVAILABLE** on the current plan.

## M. CI workflow created

Created `.github/workflows/ci.yml` with three jobs:

1. `Rust crypto tests` — `cargo test` in `crypto/rust`
2. `Android debug build` — `./gradlew :android:assembleDebug`
3. `Android release compile smoke` — `./gradlew :android:assembleRelease`

## N. CI execution result and toolchain reconciliation

### Actual source of truth (from checked-in files)

| File | Setting | Value | Lines |
|------|---------|-------|-------|
| `build.gradle.kts` | AGP | `8.13.2` | 3 |
| `build.gradle.kts` | KGP | `1.9.20` | 4 |
| `android/build.gradle.kts` | `compileSdk` / `targetSdk` | `34` | 8, 13 |
| `android/build.gradle.kts` | `minSdk` | `26` | 12 |
| `android/build.gradle.kts` | `ndkVersion` | `26.2.11394342` | 16 |
| `android/build.gradle.kts` | `kotlinCompilerExtensionVersion` | `1.5.4` | 47–48 |
| `gradle/wrapper/gradle-wrapper.properties` | Gradle Wrapper | `9.3.1` | 3 |

### Historical discrepancy

Previous documentation claimed `AGP 9.1.1` and `Kotlin 2.2.10`. Those values never appeared in the checked-in build files. The initial baseline commit `7db20fa` already contained `AGP 8.13.2`, `KGP 1.9.20`, and the Gradle 9.3.1 wrapper. The discrepancy came from earlier `PROJECT_STATE.md` entries that were written from the user's task description rather than from `build.gradle.kts` / `gradle-wrapper.properties`.

### Incompatibility

No supported Gradle 8.x wrapper exists for the **actual** checked-in toolchain:

- **AGP 8.13.2** requires **Gradle 8.13** minimum.¹
- **Kotlin Gradle Plugin 1.9.20** is fully compatible with **Gradle 6.8.3 through 8.1.1**.²

There is no Gradle version that satisfies both `≥ 8.13` and `≤ 8.1.1`.

### CI runs

| Run | Commit | Result |
|-----|--------|--------|
| `32309069013` | `42521af` (CI workflow add) | `failure` — could not resolve `org.jetbrains.kotlin.plugin.compose:1.9.20` |
| `32309477433` | `f08f16e` (compose plugin version) | `failure` — `org/gradle/api/internal/HasConvention` (Gradle 9 / KGP 1.9.20) |
| `32309829334` | `b894058` (use `composeOptions`) | `failure` — same Gradle 9 / KGP 1.9.20 incompatibility |

Final run `32309829334`:

- **Rust crypto tests:** PASS
- **Android debug build:** FAIL (toolchain incompatibility)
- **Android release compile smoke:** skipped

Because no compatible Gradle 8.x wrapper exists for the actual `AGP 8.13.2` + `KGP 1.9.20` combination, the CI Android build cannot be fixed by wrapper changes alone.

## O. Files changed

| File | Change |
|------|--------|
| `.gitignore` | Hardened |
| `build.gradle.kts` | Compose plugin version attempted, then reverted to KGP 1.9.20 setup |
| `android/build.gradle.kts` | Removed incompatible `plugin.compose`; added `composeOptions.kotlinCompilerExtensionVersion = "1.5.4"` |
| `.github/workflows/ci.yml` | Minimal CI workflow |
| `docs/current/GIT_DEVELOPMENT_WORKFLOW.md` | New |
| `docs/current/REPOSITORY_SECURITY_POLICY.md` | New |
| `PROJECT_STATE.md` | Updated |
| `FORTSCHRITT.md` | Updated |
| `DEVIN_PROMPT_OUTPUT_ARCHIV.md` | Updated with GIT-001 summary |
| `docs/reports/git-github-baseline-report.md` | This report |

## P. Remaining blockers

1. **Toolchain incompatibility:** `AGP 8.13.2` and `KGP 1.9.20` cannot be reconciled with any single Gradle wrapper version. The checked-in build files need either an AGP/Kotlin downgrade or a dedicated Toolchain Modernization task.
2. **Branch protection / ruleset** unavailable on the free private GitHub plan.
3. **Secret scanning / push protection** unavailable on the free private GitHub plan.

## Q. Exact recommended next engineering step

1. **Option A (lowest-risk, given current KGP):** Downgrade `AGP` to a `KGP 1.9.20`-compatible version (e.g. AGP 8.1.x) and Gradle wrapper to 8.1.1, then run a full regression.
2. **Option B (baseline modernization):** Upgrade `KGP` to `2.2.10` and `AGP` to `9.1.1`, keep Gradle 9.3.1, and replace `composeOptions` with the new Compose compiler plugin. This requires a dedicated `PROMPT-TOOLCHAIN-UPGRADE` with full device/emulator regression.
3. **Do not apply either** without the user choosing, because both change build tooling beyond the scope of GIT-001.

---

¹ Source: Android Gradle Plugin 8.x/9.x compatibility — `https://developer.android.com/build/releases/about-agp`  
² Source: Kotlin 1.9.20 Gradle compatibility — `https://kotlinlang.org/docs/whatsnew1920.html`
