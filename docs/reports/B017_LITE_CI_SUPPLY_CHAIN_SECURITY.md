# B-017-Lite — CI / Supply-Chain Security Foundation

**Date:** 2026-08-29  
**Branch:** `security/b017-lite-supply-chain-foundation`  
**Task:** Implement the B-017-Lite CI and supply-chain hardening foundation.

---

## 1. Threat being reduced

The main supply-chain and CI risks targeted by B-017-Lite are:

- **Mutable GitHub Action references** (`@v4`, `@stable`) that can be silently retargeted to a different commit after a workflow is written.
- **Overbroad workflow token permissions** that grant the default `GITHUB_TOKEN` more access than the CI job needs.
- **Dangerous workflow triggers** (`pull_request_target`, privileged `workflow_run`) that can execute untrusted code with repository secrets or write access.
- **Gradle wrapper substitution** by an attacker who can replace the wrapper distribution in transit.
- **Dynamic or changing Android/Gradle dependencies** (`+`, `latest.release`, `SNAPSHOT`) that make builds non-reproducible and allow malicious updates.
- **Insecure HTTP repositories or `allowInsecureProtocol`** that enable downgrade / package interception.
- **Unreviewed local repositories (`mavenLocal()`)** that can leak attacker-controlled artifacts into the build.
- **Unlocked Rust `Cargo.lock` or wildcard dependencies** that allow dependency graph drift between CI and developer builds.

B-017-Lite does not claim to eliminate these risks entirely. It establishes a deterministic, fail-closed foundation that can be expanded in later B-017 work.

---

## 2. Controls implemented

### 2.1 GitHub Actions hardening

- **Least-privilege `GITHUB_TOKEN` permissions.**
  - Workflow top-level: `permissions: contents: read`.
  - `android-debug` job that uploads artifacts: explicit `permissions: contents: read, actions: write`.
  - No `pull-requests: write`, `issues: write`, `packages: write`, or `contents: write` is granted.

- **Immutable action references.**
  - All `uses:` references in `.github/workflows/ci.yml` are pinned to full 40-character commit SHAs.
  - The human-readable version tag is retained in an adjacent comment, e.g. `actions/checkout@11d5960... # v4`.
  - Provenance for the pinned SHAs was established with `git ls-remote` against the canonical action repositories:
    - `actions/checkout` v4 → `11d5960a326750d5838078e36cf38b85af677262`
    - `actions/setup-java` v4 → `cf277c60eb25467037889841efdb72551f06f6c3`
    - `dtolnay/rust-toolchain` stable branch → `4360b52568e2003a75bf9bc1d59f33a8e3fc893c`
    - `android-actions/setup-android` v4.0.1 → `40fd30fb8d7440372e1316f5d1809ec01dcd3699`
    - `nttld/setup-ndk` v1.5.0 → `1e00e161fa5fe726a48dfe290a9549362c9621fc`
    - `actions/upload-artifact` v4 → `ea165f8d65b6e75b540449e92b4886f43607fa02`

- **Dangerous triggers removed.**
  - The existing `push` and `pull_request` triggers are preserved.
  - `pull_request_target` and `workflow_run` are not introduced.

- **Bounded concurrency.**
  - `concurrency: group: ${{ github.workflow }}-${{ github.ref }}; cancel-in-progress: true` prevents obsolete runs from piling up.

- **Shell safety.**
  - Inline Bash steps now begin with `set -euo pipefail` where appropriate.

### 2.2 Android / Gradle hardening

- **Gradle wrapper SHA-256 verification.**
  - Added `distributionSha256Sum=b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06` to `gradle/wrapper/gradle-wrapper.properties`.
  - The checksum was obtained from the authoritative source `https://services.gradle.org/distributions/gradle-9.3.1-bin.zip.sha256`.
  - `validateDistributionUrl=true` was already present and is retained.

- **Dependency declaration hygiene confirmed.**
  - No `+`, `latest.release`, `latest.integration`, or `SNAPSHOT` versions are present in Gradle build files.
  - No `allowInsecureProtocol = true` or HTTP repositories are present.
  - Repository sources are restricted to `google()`, `mavenCentral()`, and `gradlePluginPortal()` with `FAIL_ON_PROJECT_REPOS`.
  - `mavenLocal()` is not used.

- **No `gradle/verification-metadata.xml` introduced.**
  - Full cryptographic Gradle artifact verification was not feasible to bootstrap safely within B-017-Lite. It is deferred to later B-017 hardening.

### 2.3 Rust / Cargo hardening

- **Locked dependency resolution in CI.**
  - CI now runs `cargo test --locked` to enforce `Cargo.lock`.
  - `cargo generate-lockfile --locked` is run in the policy job to detect an out-of-date `Cargo.lock`.

- **`Cargo.lock` is present and not ignored.**
  - Existing `crypto/rust/Cargo.lock` is committed.
  - `.gitignore` does not ignore `Cargo.lock`.

- **No wildcard or floating Git dependencies.**
  - `Cargo.toml` dependencies are exact versions or compatible version requirements that are resolved through `Cargo.lock`.

### 2.4 B-017-Lite policy validator

Created `tools/security/b017_lite_policy_validator.py` and `tools/security/test_b017_lite_policy_validator.py`.

The validator is:

- deterministic;
- locally runnable without credentials;
- fail-closed;
- integrated into CI as a required gate;
- tested with PASS and FAIL cases.

Checks performed:

- `.github/workflows/*.yml`
  - all `uses:` refs are pinned to full 40-char SHA (with optional comment);
  - no `pull_request_target` or `workflow_run` triggers;
  - explicit `permissions` block is present;
  - no overbroad `contents`, `issues`, `pull-requests`, or `packages` write permissions.
- `gradle/wrapper/gradle-wrapper.properties`
  - `distributionSha256Sum` is present;
  - `validateDistributionUrl=true` is present.
- Gradle files
  - no dynamic/changing versions (`+`, `latest.release`, `latest.integration`, `SNAPSHOT`);
  - no insecure HTTP repositories;
  - no `allowInsecureProtocol = true`;
  - no `mavenLocal()`;
  - no unexpected repositories in `settings.gradle.kts`.
- Rust
  - `Cargo.lock` exists and is not ignored;
  - no `*` dependency versions;
  - no branch/tag Git dependencies.

---

## 3. Files affected

- `.github/workflows/ci.yml`
- `gradle/wrapper/gradle-wrapper.properties`
- `tools/security/b017_lite_policy_validator.py`
- `tools/security/test_b017_lite_policy_validator.py`
- `docs/reports/B017_LITE_CI_SUPPLY_CHAIN_SECURITY.md`
- Continuity/current-state surfaces (updated separately)

No product source, cryptography, or architectural files were changed.

---

## 4. CI gate list

The resulting CI enforces, in order:

1. **B-017-Lite supply-chain policy** (`tools/security/b017_lite_policy_validator.py`)
2. **Cargo.lock freshness check** (`cargo generate-lockfile --locked`)
3. **Rust crypto tests** (`cargo test --locked`)
4. **JVM unit tests** (`./gradlew :android:testDebugUnitTest`)
5. **Android debug build + APK content validation**
6. **Android release compile smoke + APK content validation**

---

## 5. Residual risks

- **GitHub Free plan:** private repositories cannot use server-side Rulesets or mandatory branch protection. This is a known platform constraint. B-017-Lite relies on repository-controlled CI hardening and cannot replace server-side enforcement.
- **No `gradle/verification-metadata.xml`:** full cryptographic artifact verification for all Gradle dependencies is not yet in place.
- **Action pin aging:** pinned commit SHAs will age. A future hardening task must define a controlled cadence for reviewing and updating action versions.
- **CI secrets surface:** B-017-Lite added no secrets. The residual risk is that existing workflow steps that install SDK/NDK via remote network fetches must be trusted at their pinned commit SHAs.
- **Human-controlled remote write remains in effect.** No AI remote push/merge is permitted.

---

## 6. What B-017-Lite does NOT guarantee

- It does not guarantee the supply chain is attack-proof.
- It does not replace a paid GitHub plan or server-side branch protection.
- It does not provide full reproducible-build evidence or SBOM generation.
- It does not audit the transitive dependency trees for every known vulnerability.
- It does not implement release signing or artifact provenance chains.

---

## 7. Future full B-017 / release-security work

- Generate and review `gradle/verification-metadata.xml` with cryptographic hashes for all Gradle artifacts.
- Introduce Cargo `cargo-vet` or `cargo-deny` policy for Rust crates.
- Add SBOM generation and artifact provenance attestation.
- Implement release signing and signing-key governance.
- Establish a controlled cadence for updating pinned GitHub Actions and verifying their new SHAs.
- Add periodic audit of dependency diffs in lockfiles.

---

## 8. Validation performed

- `python3 tools/security/b017_lite_policy_validator.py` → PASS
- `python3 -m unittest tools/security/test_b017_lite_policy_validator.py -v` → 9/9 PASS
- `git diff --check` → PASS
- `python3 tools/continuity/test_handoff_and_validator.py` → 24 tests PASS (expected)
- `python3 tools/continuity/validate_continuity.py --mode live` → expected PASS after continuity surfaces are reconciled

---

## 9. Open findings / deferred hardening

| ID | Item | Severity | Deferral reason |
|---|---|---|---|
| B017-DEF-001 | Full `gradle/verification-metadata.xml` with SHA-256 for all Gradle artifacts | MEDIUM | Requires controlled bootstrap and independent review; not feasible within B-017-Lite scope. |
| B017-DEF-002 | `cargo-vet` or `cargo-deny` Rust supply-chain audit | MEDIUM | Requires crate-level policy curation and review; deferred to full B-017. |
| B017-DEF-003 | SBOM / artifact provenance | LOW | Release evidence gate, not Lite. |
| B017-DEF-004 | Server-side branch protection | LOW | Blocked by GitHub Free plan; not a repository defect. |
