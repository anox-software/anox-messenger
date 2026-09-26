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

- `Cargo.lock` is retained in version control and all Rust builds run with `--locked`.
- Dependencies are pinned or versioned responsibly.
- Rust toolchain, Android NDK, and cargo-ndk are pinned exactly
  (`crypto/rust/rust-toolchain.toml`; asserted by `tools/security/native_build.py check-toolchain`).

## Generated artifacts

- Native `.so` libraries are NEVER committed. The authoritative producer is
  `tools/security/native_build.py` (cargo-ndk, `--locked`, deterministic path
  remapping), which emits `build/native/jniLibs/{arm64-v8a,x86_64}/libanox_crypto.so`
  plus `build/native/native-manifest.json` binding source SHA, Cargo.lock hash,
  toolchain, per-artifact SHA-256 and the JNI export fingerprint.
- A two-clean-build reproducibility attestation (`native_build.py rebuild-compare`)
  is required before any manifest is accepted; APKs are bound to the manifest by
  `tools/security/validate_apk_contents.py --native-manifest` (hash + ABI + ELF
  machine match + ACTUAL packaged-binary JNI export surface vs source, anchored
  to an expected source SHA, fail-closed).
- Gradle never packages unverified native input: every `merge*JniLibFolders` /
  `merge*NativeLibs` / `strip*Symbols` / `package*` / `bundle*` task depends on
  `verifyNativeArtifacts`, an `Exec` of `native_build.py verify` (fail-closed);
  `src/main/jniLibs` is not a jniLibs source (`setSrcDirs` replaces the default).
- Packaged APK members (binary members included) are scanned for private-key
  markers AND the same material token classes as the repository secret scan
  (AWS / GitHub / Slack / Supabase keys, generic `*_secret`/`service_role_key`
  assignments). This is byte-pattern scanning of members, not entropy analysis.
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
