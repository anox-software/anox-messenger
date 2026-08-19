# ANOX V1 — GIT-001: Secure Git / GitHub Baseline Report

**Status:** CURRENT  
**Report date:** 2026-08-19

---

## A. Previous Git state

No `.git` directory existed in the project root. Git was not initialized. No prior branches, commits, or remotes were present.

## B. `.gitignore` changes

The existing `.gitignore` was updated to:

- Ignore `.jks`, `.keystore`, and `.p12` files.
- Ignore `crypto/rust/target/` and all `target/` directories.
- Ignore `.kotlin/` build daemon state.
- Ignore `__MACOSX/` resource-fork directories.

Already ignored: `.DS_Store`, `.idea/`, `.gradle/`, `build/`, `local.properties`, `.env`, `*.log`, `.codeium/`.

## C. Secret audit result

No production secrets were found in the working tree.

| Checked | Result |
|---------|--------|
| `.env*` | Not present |
| `local.properties` | Present; contains only `sdk.dir` and is ignored |
| `*.jks` / `*.keystore` / `*.p12` | Not present |
| `*.pem` / `*.crt` private certificates | Not present |
| `google-services.json` | Not present |
| Hardcoded API keys / tokens | Not found |
| `BEGIN ... PRIVATE KEY` blocks | Not found |

## D. Files intentionally excluded

Generated and local files excluded from version control include:

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
| `cargo test` (crypto/rust) | **15/15 PASS** (re-run) |
| Android connected instrumentation | **35/35 PASS** (accepted from prior run) |
| `./gradlew :android:assembleRelease` | **BUILD SUCCESSFUL** (accepted from prior run) |

Note: The current macOS environment does not have a running JDK or Android emulator, so the Gradle tasks could not be re-executed during this session. The accepted baseline from the prior working environment is reported above.

## F. Baseline commit hash

```text
7db20fa4df8dc70392afd803fabaaf20c0b50d7d
```

## G. Baseline tag

```text
v1-foundation-baseline -> 7db20fa4df8dc70392afd803fabaaf20c0b50d7d
```

## H. GitHub repository result

The configured private repository is:

```text
https://github.com/anox-admin/ax-messenger.git
```

The remote was added as `origin` but the environment cannot authenticate to GitHub.

## I. Repository visibility

Cannot be verified without a GitHub access token. `curl -I https://api.github.com/repos/anox-admin/ax-messenger` returned HTTP 404 (private or missing). `git ls-remote` failed with `terminal prompts disabled`.

## J. Remote result

```text
origin	https://github.com/anox-admin/ax-messenger.git (fetch)
origin	https://github.com/anox-admin/ax-messenger.git (push)
```

## K. Branch / ruleset protection

Not configured; requires GitHub access.

## L. Secret scanning / push protection

Not configured; requires GitHub access.

## M. CI workflows created

None created because the repository is not yet connected to GitHub.

## N. CI execution result

Not executed; CI pipeline not configured.

## O. Files changed

| File | Change |
|------|--------|
| `.gitignore` | Keystore and Rust target exclusions added |
| `docs/current/GIT_DEVELOPMENT_WORKFLOW.md` | New |
| `docs/current/REPOSITORY_SECURITY_POLICY.md` | New |
| `PROJECT_STATE.md` | Updated with Git baseline status |

All other files in the baseline are the accepted current project state.

## P. Remaining Git/GitHub blockers

1. **Authentication required.** The environment has no working GitHub authentication (`gh` not installed, no MCP GitHub server, no `GITHUB_TOKEN`). Pushing to the private repository requires credentials.
2. **Repository privacy not verified** without authentication.
3. **Push not attempted** until privacy and authentication are resolved.
4. **CI pipeline, branch protection, and secret scanning** cannot be configured until the repository is reachable.

## Q. Exact recommended next engineering step

1. Provide GitHub authentication to this environment by one of these methods:
   - Install `gh` CLI and run `gh auth login` with access to the `anox-admin/ax-messenger` repository, or
   - Provide a GitHub Personal Access Token (classic) with `repo` scope and add it to the environment (for example `export GITHUB_TOKEN=...`) without pasting it into source files or logs.
2. Re-run `git ls-remote --heads origin main` to verify access.
3. Push `main` and the `v1-foundation-baseline` tag.
4. Configure branch protection, secret scanning, and the minimal Rust + Android CI workflow.
5. Then proceed with `PROMPT-007 — Device Authentication Foundation`.
