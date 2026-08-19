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

No GitHub integration was available in the current environment. `gh` CLI is not installed and no MCP GitHub server is configured.

The repository identifier must be provided before the remote can be added.

## I. Repository visibility

Not yet verified (no remote configured).

## J. Remote result

```text
(no remotes configured)
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

1. **GitHub repository identifier needed.** Please provide the exact owner and repository name (e.g. `your-org/anoX-Messenger`) or the full HTTPS/SSH URL.
2. **Authentication setup.** Confirm that the environment has a working `gh` CLI, a PAT, or an MCP GitHub integration with push access.
3. **CI pipeline.** Add `.github/workflows/ci.yml` after the repository is connected.
4. **Branch protection / ruleset.** Configure after pushing `main` to GitHub.

## Q. Exact recommended next engineering step

1. Provide the exact private GitHub repository identifier.
2. Add the remote and push `main` and the `v1-foundation-baseline` tag.
3. Configure branch protection, secret scanning, and the minimal Rust + Android CI workflow.
4. Then proceed with `PROMPT-007 — Device Authentication Foundation`.
