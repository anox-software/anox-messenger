# B-017 — CI/CD + Supply Chain
**Status:** FROZEN v1.2

- Private repository; normal development through branch + PR + review + required checks; no force push/direct main for normal changes. B-023 requires technical branch governance before Production even if current free plan lacks it.
- CI minimum: Rust tests, Android debug/release compile, lint/static checks, secret scan, dependency/vulnerability/license checks, migration/RLS tests when present and security regression gates as they become implementable.
- GitHub Actions and external build actions must be pinned/reviewed for supply-chain risk; production release process must not fetch arbitrary “latest” crypto source. Lockfiles/checksums/verifications required.
- `Cargo.lock`, Gradle dependency locking/verification strategy, SBOM (CycloneDX target), secret scanning and provenance evidence are release artifacts.
- Production signing private key never exists in CI. CI may build unsigned/candidate artifacts; final release signing is offline/hardware-protected under B-018.
- Dependency changes to vodozemac/libsodium/SQLCipher/JOSE/WebAuthn/update/signing receive explicit security impact review and relevant tests/audit delta.
- Build/release artifacts are hash-bound and immutable; backend should deploy exact approved artifact, not rebuild source ad hoc on server.
