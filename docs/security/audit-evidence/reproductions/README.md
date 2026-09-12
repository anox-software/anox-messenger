# Reproduced Audit Evidence — Provenance and Boundaries

This directory records the *reproduced* evidence reported by the completed Security Hardening audits. It is evidence about what the audits proved, not remediation and not a re-run.

## What the audits reproduced (all at SHA `869b99acac040412a29bbaadc76342070fb2085c`)

From `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`:

- **Stale native artifact proof:** committed `libanox_crypto.so` (arm64-v8a `11a958a5…`, x86_64 `ecf9fdc1…`) are byte-identical to a rebuild of the Rust source at `7db20fa` (rustc 1.97.1, NDK r26c, cargo-ndk 4.1.2, release profile). A rebuild of the audited source produces different hashes (`05f3f40c…` / `c002cc42…`) and different behaviour (`-11` `BufferTooSmall` vs shipped `-2` `InvalidCiphertext` on 8 JNI functions).
- **APK hashes:** debug `f202c5e1…`, release unsigned `72075487…`.
- **Validator bypass test:** the APK content validator passed a deliberately injected `.so`, a wrong ABI member, and a PEM marker inside a binary/asset — proving filename/text-suffix-only scope.
- **Toolchain facts:** `stable` Rust toolchain unpinned; no `rust-toolchain.toml`; NDK installed in CI but unused for Rust builds; Gradle daemon JVM auto-provisioned via foojay without checksum.

From `AUDIT-SECURITY-CODEBASE-001` / `AUDIT-SECURITY-CODEBASE-002`:

- **Serialization overflow measurements:** identity pickle = 459 B (0 OTK), 1671 B (5), **5277–5280 B (20 = default)**, 12546–12571 B (50), 24582–24673 B (100); session after 39 skipped messages = 6438 B — all exceed the fixed 4096-byte buffers.
- **OTK enumeration nondeterminism:** 20/20 index sweeps produced duplicates; one sweep yielded 12 unique of 20; order differs per call.
- **DPoP/htu collisions (JVM-verified):** `/v1/a%2Fb` ≡ `/v1/a/b`; `/v1/%61dmin` ≡ `/v1/admin`; userinfo retained+lowercased; `:443` not elided; `..`/`//` unresolved.
- **`getInstance` defect:** four-line defect (`instance` never assigned) — no JVM test asserts singleton identity.
- **Concurrency:** `RegistrationOrchestratorTest`/`RegistrationCrashConsistencyTest` use in-memory fakes; the only suite touching real JNI (`CryptoInstrumentedTest`, 39 tests) never runs in CI (no emulator job).

## Authoritative locations

The authoritative evidence is:

1. The preserved report bodies in `docs/reports/security/audits/` (hash-bound in `../evidence_hashes.json`).
2. The structured mappings in `../audit_traceability.jsonl` and `../audit_registry.jsonl`.

**`/tmp` artifacts are NOT authoritative.** Paths such as `/tmp/anox_buildsc_out_1/`, `/tmp/anox_audit2/`, and `/tmp` proof scripts were audit-run artifacts; they are transient, unowned by this repository, and are deliberately not copied in as evidence. Their *results* are preserved inside the reports themselves; only the recorded hash values are carried into `../evidence_hashes.json`.

## Boundary

- No finding is remediated here.
- No audit was re-run for this preservation task; reproduced values are transcribed from the preserved reports.
- `BLIND_CHECKPOINT_CODESEC2.md` (in `/tmp`) is a checkpoint summary only — it is not the Audit-002 report and is not preserved.
- Any future retest must execute against a provenance-verified binary (see `ANOX-BUILDSC-CANDIDATE-001` and the `NATIVE_RETEST_ACCEPTANCE_BLOCKERS` gate set).
