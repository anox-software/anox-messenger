> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-017 — CI/CD + Supply Chain (FROZEN v1.2).
>
# Repository Security Policy

**Status:** CURRENT  
**Scope:** ANOX V1 Git/GitHub baseline

---

## Secrets

- No passwords, API tokens, service-role keys, or database credentials are committed.
- No Android signing private keys (`.jks`, `.keystore`, `.p12`) are committed.
- No Supabase service-role key or database URL is in client source.
- No production tokens in tests.
- `local.properties`, `.env`, and `.env.*` are ignored.

## Dependencies

- `Cargo.lock` is retained in version control and all Rust builds use `--locked`.
- Gradle dependency lockfiles do **not** exist yet; Gradle dependency locking/verification is tracked as later-gate work (B-017 RC scope). Prior wording claiming retained Gradle lockfiles was incorrect.
- CI runs a fail-closed Rust advisory scan (`cargo audit`, pinned version) on every change to `crypto/rust/Cargo.lock`.
- Dependencies are pinned or versioned responsibly; all GitHub Actions `uses:` references are pinned to 40-character commit SHAs (enforced by `tools/security/b017_lite_policy_validator.py`).

## Generated artifacts

- Native `.so` libraries are **never committed**. The only accepted source of `libanox_crypto.so` is the authoritative build path `tools/security/native_build.py`, which compiles the reviewed `crypto/rust` source with the toolchain pinned in `crypto/rust/rust-toolchain.toml` (Rust 1.97.1, NDK r26c, cargo-ndk 4.1.2) for exactly `arm64-v8a` and `x86_64`.
- `android/src/main/jniLibs/` is ignored and must stay empty/absent; `android/build.gradle.kts` fails closed if a `.so` ever appears there and consumes only `build/native/jniLibs` produced by the authoritative build.
- Every authoritative build emits `build/native/native-manifest.json` binding source revision, toolchain, ABI, artifact path and SHA-256; two clean builds must produce identical hashes; `tools/security/validate_apk_contents.py` verifies the packaged `.so` bytes against that manifest inside the final APK.
- The build refuses a dirty working tree (the manifest records `source.working_tree = "clean"` and nothing else is accepted), and `native_build.py rebuild-compare` is the only writer of the `build.reproducible_build_confirmed = true` attestation, which `verify` and the APK validator require. APK member paths must be canonical (`lib/<abi>/<name>.so` exactly); any alternate spelling/casing/normalization that could hide a native library fails closed.
- GitHub Action SHA pins and their independently verified release lineage are classified in `docs/security/remediation/S1_ACTION_PIN_PROVENANCE.md`; pins are never replaced by mutable refs.
- `target/`, `build/`, `.gradle/`, and `.kotlin/` are not committed.

## Review policy

- Security-invariant changes require a pull request and explicit review.
- No direct commits to `main`.

## Release signing

- Release signing keys are stored outside the repository.
- No production keystore is uploaded to GitHub.

## Secret rotation

If a secret is accidentally exposed in the repository:

1. Immediately rotate the exposed credential.
2. Remove the secret from history.
3. Force-push is only permitted on a feature branch, never on `main`.
