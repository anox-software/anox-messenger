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
| `cargo test` (crypto/rust) | **15/15 PASS** (re-run in GIT-001 session) |
| Android connected instrumentation | **35/35 PASS** (accepted from prior run) |
| `./gradlew :android:assembleRelease` | **BUILD SUCCESSFUL** (accepted from prior run) |

The Gradle build could not be re-run in the local macOS session because no JDK/Android emulator is present.

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

Tooling:

- `actions/checkout@v4`
- `dtolnay/rust-toolchain@stable`
- `actions/setup-java@v4` (Temurin 17)
- `android-actions/setup-android@v4.0.1`
- `nttld/setup-ndk@v1.5.0` (r26c)

No secrets are embedded in the workflow.

## N. CI execution result

| Run | Commit | Result |
|-----|--------|--------|
| `32309069013` | `42521af` (CI workflow add) | `failure` — could not resolve `org.jetbrains.kotlin.plugin.compose:1.9.20` |
| `32309477433` | `f08f16e` (add compose plugin version) | `failure` — `org/gradle/api/internal/HasConvention` with Kotlin 1.9.20 on Gradle 9.3.1 |
| `32309829334` | `b894058` (use `composeOptions.kotlinCompilerExtensionVersion = 1.5.4`) | `failure` — same `HasConvention` Gradle 9 / Kotlin 1.9.20 incompatibility |

Final run `32309829334`:

- **Rust crypto tests:** PASS
- **Android debug build:** FAIL — `org/gradle/api/internal/HasConvention` / `BuildFlowService` error
- **Android release compile smoke:** skipped (depends on debug)

**Root cause:** Kotlin Gradle Plugin 1.9.20 is not compatible with Gradle 9.3.1 (convention APIs were removed in Gradle 9.0). The repository needs either a Gradle downgrade to 8.x or a Kotlin/AGP upgrade to the 2.2.x / 9.x line.

## O. Files changed

| File | Change |
|------|--------|
| `.gitignore` | Hardened |
| `build.gradle.kts` | Compose plugin version attempted, then reverted to correct 1.9.20 setup |
| `android/build.gradle.kts` | Removed incompatible `plugin.compose`; added `composeOptions.kotlinCompilerExtensionVersion = "1.5.4"` |
| `docs/current/GIT_DEVELOPMENT_WORKFLOW.md` | New |
| `docs/current/REPOSITORY_SECURITY_POLICY.md` | New |
| `PROJECT_STATE.md` | Updated |
| `FORTSCHRITT.md` | Updated |
| `DEVIN_PROMPT_OUTPUT_ARCHIV.md` | Updated with GIT-001 summary |
| `docs/reports/git-github-baseline-report.md` | This report |

## P. Remaining blockers

1. **CI Android build failing** due to Kotlin 1.9.20 / Gradle 9.3.1 incompatibility. Requires a deliberate build-tooling alignment decision.
2. **Branch protection / ruleset** unavailable on the free private GitHub plan.
3. **Secret scanning / push protection** unavailable on the free private GitHub plan.

## Q. Exact recommended next engineering step

1. Decide the build-tooling alignment:
   - **Option A (minimal change):** Downgrade the Gradle wrapper to a version compatible with the existing AGP 8.13.2 + Kotlin 1.9.20 (e.g. 8.13.x).
   - **Option B (baseline alignment):** Upgrade to AGP 9.1.1 + Kotlin 2.2.10 + `org.jetbrains.kotlin.plugin.compose` and remove `composeOptions`.
2. After CI is green, optionally set `Rust crypto tests` as a required status check (if plan allows) and add branch protection.
3. Then proceed with `PROMPT-007 — Device Authentication Foundation`.
