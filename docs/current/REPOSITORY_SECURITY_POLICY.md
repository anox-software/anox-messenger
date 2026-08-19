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

- `Cargo.lock` and Gradle lockfiles are retained in version control.
- Dependencies are pinned or versioned responsibly.

## Generated artifacts

- Native `.so` libraries are currently committed because the project does not yet have a reproducible `cargo-ndk` CI pipeline.
- When a CI build pipeline is added, native artifacts should be produced in CI and removed from the repository.
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
