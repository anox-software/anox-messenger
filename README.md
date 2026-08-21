> **B-025 Architecture Authority Notice**
>
> B-025 is the current architecture authority. See `docs/authority/B025/` for the complete handoff package. This file may still contain pre-B-025 text.
>
# anoX Messenger

A security-oriented native messenger application for Android and GrapheneOS.

**Current architecture baseline:** B-025
**Last synchronized:** 2026-08-20

---

## Status

- Rust crypto foundation implemented and passing: `cargo test` **15/15 PASS** (current CI and historical local runs).
- Android connected instrumentation **35/35 PASS** (historical, not re-run in CI due to no emulator).
- Core backend, account/auth, messaging, contacts, push, and attachments are **not yet implemented**.

This project is closed-source. Do not claim it is "unhackable" or production-secure without independent review.

## Technologies

- Native Android (Kotlin)
- Gradle 9.3.1
- Jetpack Compose
- Rust crypto crate (`anox_crypto`)
- vodozemac 0.10.0
- aes-gcm 0.10.3
- NDK r26c (`26.2.11394342`)

## Project Structure

```text
anox-messenger/
├── android/            # Native Android application
├── backend/            # Backend services (placeholder)
├── crypto/             # Rust crypto crate + Kotlin crypto bridge
├── docs/               # Documentation
│   ├── current/        # Current canonical architecture
│   ├── history/raw1.1/ # Historical/superseded documents
│   ├── security/       # Security reports and validation evidence
│   ├── architecture/   # Historical architecture docs
│   ├── specifications/ # Technical specifications
│   ├── decisions/      # Decision records
│   └── reports/        # Audit and sync reports
└── .gitignore
```

## Build Commands

```bash
./gradlew build
./gradlew :android:connectedDebugAndroidTest
```

## Important Documents

- `docs/current/SECURITY_INVARIANTS.md`
- `docs/current/SYSTEM_ARCHITECTURE.md`
- `docs/reports/current-code-gap-audit.md`
- `docs/reports/documentation-raw-sync-report.md`
