# B-017-Lite — CI / Supply-Chain Security Foundation

**Date:** 2026-08-29
**Branch:** `security/b017-lite-supply-chain-foundation`

---

## 1. Threat being reduced

- Mutable GitHub Action references.
- Overbroad `GITHUB_TOKEN` permissions in CI.
- Dangerous workflow triggers such as `pull_request_target` and `workflow_run`.
- Gradle wrapper substitution in transit.
- Dynamic/changing Android/Gradle dependencies and insecure repositories.
- Unreviewed `Cargo.lock` handling or unpinned Rust Git dependencies.
- Wrapper JAR tampering (a committed, executable artifact).
- Evidence loss from obsolete CI runs on `main`.

B-017-Lite does not claim to fully secure the supply chain. It establishes a deterministic, fail-closed, reviewable foundation.

## 2. Controls implemented

### 2.1 GitHub Actions hardening

- Workflow default `permissions: contents: read`.
- No job is granted any `GITHUB_TOKEN` write scope.
- All `uses:` references in `.github/workflows/ci.yml` are pinned to full 40-character commit SHAs.
- Human-readable version comments are retained.
- Provenance for the pinned SHAs was established with `git ls-remote` and verified commits API calls:

| Action | Pin | Comment |
|---|---|---|
| `actions/checkout` | `11d5960a326750d5838078e36cf38b85af677262` | v4, lightweight tag |
| `actions/setup-java` | `cf277c60eb25467037889841efdb72551f06f6c3` | v4, lightweight tag |
| `dtolnay/rust-toolchain` | `4360b52568e2003a75bf9bc1d59f33a8e3fc893c` | stable branch tip, immutable commit |
| `android-actions/setup-android` | `40fd30fb8d7440372e1316f5d1809ec01dcd3699` | v4.0.1, lightweight tag |
| `nttld/setup-ndk` | `afb4c9964b521afb97c864b7d40b11e6911bd410` | v1.5.0, peeled annotated-tag commit |
| `actions/upload-artifact` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | v4, lightweight tag |
| `gradle/wrapper-validation-action` | `56b90f209b02bf6d1deae490e9ef18b21a389cd4` | v1.1.0, peeled annotated-tag commit |

- No `pull_request_target`, `workflow_run`, `workflow_dispatch`, or other privileged triggers.
- `concurrency` is scoped to `${{ github.workflow }}-${{ github.ref }}`; `cancel-in-progress` is disabled for `refs/heads/main` to preserve gate evidence for every mainline commit.
- `set -euo pipefail` is used in multi-line shell steps.
- APK lookup uses `find ... -print -quit` to avoid a `find | head` SIGPIPE under `pipefail`.

### 2.2 Android / Gradle hardening

- `gradle/wrapper/gradle-wrapper.properties` contains `distributionSha256Sum` for the Gradle 9.3.1 distribution; the value was verified against `https://services.gradle.org/distributions/gradle-9.3.1-bin.zip.sha256`.
- CI runs `gradle/wrapper-validation-action` before any `./gradlew` invocation. This validates the committed `gradle-wrapper.jar` against Gradle's published wrapper checksums.
- No `+`, `latest.release`, `latest.integration`, `SNAPSHOT`, or Maven version ranges in dependency declarations.
- No `allowInsecureProtocol = true`, no HTTP repositories, no `mavenLocal()`, no `jcenter()`.
- `settings.gradle.kts` restricts repositories to `google()`, `mavenCentral()`, and `gradlePluginPortal()` under `FAIL_ON_PROJECT_REPOS`.
- Full `gradle/verification-metadata.xml` remains deferred.

### 2.3 Rust / Cargo hardening

- `crypto/rust/Cargo.lock` is committed and not ignored.
- CI runs `cargo test --locked`.
- No wildcard (`*`, `1.*`) or range dependency versions.
- No unpinned or branch/tag Git dependencies.
- `tools/security/b017_lite_policy_validator.py` enforces the above and is itself tested.

### 2.4 B-017-Lite policy validator

`tools/security/b017_lite_policy_validator.py`:

- Deterministic, zero-dependency, no credentials, fail-closed.
- CI-integrated as a required gate.
- Workflow checks:
  - inspect `*.yml` and `*.yaml`;
  - deny `pull_request_target` and `workflow_run` in block, inline, and list forms;
  - deny any `permissions: write` scope at workflow or job level (deny by default);
  - deny `permissions: write-all`;
  - require external `uses:` to be pinned to a 40-character commit SHA (or a SHA-digest Docker image);
  - flag mutable `docker://image:tag` references.
- Gradle checks:
  - `distributionSha256Sum` and `validateDistributionUrl=true` in wrapper properties;
  - no `+`, `1.+`, `1.*`, `latest.release`, `latest.integration`, `SNAPSHOT`, or Maven ranges;
  - no `mavenLocal()`, `jcenter()`, `allowInsecureProtocol=true`;
  - only HTTPS and only allow-listed repository hosts;
  - `FAIL_ON_PROJECT_REPOS` in `settings.gradle`/`settings.gradle.kts`.
- Rust checks:
  - `Cargo.lock` present and not ignored;
  - no `*` or `[` version values in dependency sections;
  - no `git = "..."` without `rev = "..."`.

**Known limitations (documented):** the offline validator cannot distinguish a 40-character annotated-tag object from a 40-character commit. The implementation already repinned `nttld/setup-ndk` to the peeled commit. Any new annotated-tag pin is a provenance defect that must be caught by independent review, not by this offline tool.

## 3. Files affected

- `.github/workflows/ci.yml`
- `gradle/wrapper/gradle-wrapper.properties`
- `tools/security/b017_lite_policy_validator.py`
- `tools/security/test_b017_lite_policy_validator.py`
- `docs/reports/B017_LITE_CI_SUPPLY_CHAIN_SECURITY.md`
- Continuity/current-state surfaces (updated separately)

No product source, cryptography, or architectural files were changed.

## 4. CI gate list

1. **B-017-Lite supply-chain policy** (`tools/security/b017_lite_policy_validator.py`)
2. **Gradle wrapper JAR validation** (`gradle/wrapper-validation-action`)
3. **Rust crypto tests** (`cargo test --locked`)
4. **JVM unit tests** (`./gradlew :android:testDebugUnitTest`)
5. **Android debug build and APK content validation**
6. **Android release compile smoke and APK content validation**

Note: `cargo generate-lockfile --locked` is **not** used because it is not a reliable offline freshness check. Locked build and test (`cargo test --locked`) is the real enforcement.

## 5. Residual risks

- **GitHub Free plan:** private repositories cannot use server-side Rulesets or mandatory branch protection. This is a known platform constraint.
- **No `gradle/verification-metadata.xml`:** full cryptographic artifact verification for all Gradle dependencies is not yet in place.
- **Action pin aging:** pinned SHAs will age. A future hardening task must define a controlled review cadence.
- **Offline validator limitation:** cannot verify whether a 40-character SHA is a tag object or a commit. Independent SHA provenance review remains required.
- **Human-controlled remote write remains in effect.** No AI remote push/merge is permitted.

## 6. What B-017-Lite does NOT guarantee

- Fully attack-proof supply chain.
- Server-side branch protection on GitHub Free.
- Full reproducible-build evidence or SBOM generation.
- Audit of every transitive dependency for every known vulnerability.
- Release signing or artifact provenance attestation.

## 7. Future full B-017 / release-security work

- Generate and review `gradle/verification-metadata.xml`.
- Introduce `cargo-vet` or `cargo-deny`.
- Add SBOM and artifact provenance.
- Release signing and signing-key governance.
- Controlled action-pin update cadence.

## 8. Validation performed

- `python3 tools/security/b017_lite_policy_validator.py` → PASS
- `python3 -m unittest tools.security.test_b017_lite_policy_validator` → **21/21 PASS** (includes the 18 independent-review regression cases)
- `cd crypto/rust && cargo test --locked` → 15/15 PASS
- `python3 tools/continuity/test_handoff_and_validator.py` → 24 PASS
- `python3 tools/continuity/validate_continuity.py --mode live` → PASS
- `git diff --check main...HEAD` → PASS (the two Markdown hard-break lines are intentional)

## 9. Review findings remediated

| Finding | Status | Evidence |
|---|---|---|
| ANOX-B017REV-001 | CLOSED | no `actions: write`; `grep -c 'write' .github/workflows/ci.yml` returns 0 |
| ANOX-B017REV-002 | CLOSED | 21/21 validator tests PASS, including 18 adversarial bypasses now rejected |
| ANOX-B017REV-003 | CLOSED | report CI gate list matches actual `.github/workflows/ci.yml`; false `generate-lockfile` claim removed |
| ANOX-B017REV-004 | CLOSED | `nttld/setup-ndk` repinned to peeled commit `afb4c996…`; commits API verified |
| ANOX-B017REV-005 | CLOSED | `gradle/wrapper-validation-action` added as required gate before `./gradlew` |
| ANOX-B017REV-006 | CLOSED | `cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}` |
| ANOX-B017REV-007 | CLOSED | APK lookups use `find ... -print -quit` |

## 10. Open findings / deferred hardening

| ID | Item | Severity | Status |
|---|---|---|---|
| B017-DEF-001 | Full `gradle/verification-metadata.xml` | MEDIUM | Deferred to full B-017 |
| B017-DEF-002 | `cargo-vet`/`cargo-deny` | MEDIUM | Deferred to full B-017 |
| B017-DEF-003 | SBOM / artifact provenance | LOW | Deferred to release B-017 |
| B017-DEF-004 | Server-side branch protection | LOW | Blocked by GitHub Free plan |
