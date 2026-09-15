# REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001 — Task Report

Session: `REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001`
Branch: `security/remediation-s1-build-provenance-001`
Base SHA: `0f932520393feee6d479cc099f179f5766323125`
Units: MSC-UNIT-001, MSC-UNIT-002, MSC-UNIT-003, MSC-UNIT-038

## What S1 built

Trusted chain implemented end to end:

```
reviewed crypto/rust source
→ crypto/rust/rust-toolchain.toml pin (Rust 1.97.1 + Android targets)
→ tools/security/native_build.py (cargo-ndk 4.1.2, NDK r26c asserted)
→ build/native/jniLibs/{arm64-v8a,x86_64}/libanox_crypto.so
→ build/native/native-manifest.json (source SHA + Cargo.lock + toolchain
   + per-ABI SHA-256/size + JNI fingerprint)
→ Gradle consumes ONLY that output (committed .so bypass removed;
   keepDebugSymbols => packaged bytes identical; verifyNativeArtifacts
   task fails closed if artifacts missing or committed .so reappears)
→ tools/security/validate_apk_contents.py v2 binds every packaged .so
   hash to the manifest, enforces the exact ABI set and ELF machine,
   scans all members for secret markers
→ CI instrumented jobs (arm64 on macos-14, x86_64 on KVM ubuntu) run
   connectedDebugAndroidTest against that same artifact and re-bind the
   tested APK to the manifest
```

## Verified evidence

- `native_build.py build` → PASS; arm64 `c854de25…`, x86_64 `77a404b2…`
- `native_build.py rebuild-compare` → PASS (two clean builds identical)
- `native_build.py verify` → PASS (hashes, ABI set, JNI fingerprint)
- `validate_apk_contents.py` debug APK → PASS; release APK → PASS
- `cargo test --locked` → 17 tests PASS
- `cargo audit` (0.22.2) → 0 vulnerabilities / 110 locked deps
- `./gradlew :android:testDebugUnitTest` → 16 test classes, 0 failures
- `./gradlew :android:lintDebug` → PASS (abortOnError)
- `./gradlew :android:connectedDebugAndroidTest` on `anox_api34_arm64`
  (API 34, arm64-v8a) → **66 instrumented tests, 0 failures**, covering
  CryptoInstrumentedTest (JNI surface incl. BufferTooSmall), DeviceAuth
  keystore tests, binding-store and registration storage tests — executed
  against the manifest-bound produced artifact
  (PROVENANCE_VERIFIED_NATIVE_RUNTIME, arm64).
- `validate_ci_pipeline.py` → 23 gate requirements + 8 required jobs PASS
- `secret_scan.py` → PASS (0 findings)
- `validate_b021_verification_matrix.py --check integrity` → PASS;
  `--check closure` correctly FAILS (5 pre_product_required rows still
  NOT_RUN — honest blockers, not auto-greened)
- `validate_s1_build_provenance.py --check static` → PASS
- `tools/audit/test_s1_build_provenance.py` → 66 adversarial tests PASS
- `b017_lite_policy_validator.py` → PASS (all `uses:` SHA-pinned)

## x86_64 runtime

`RUNTIME_ENVIRONMENT_UNAVAILABLE` locally — no x86_64 system image on this
host. The executable path exists in CI (`instrumented-x86_64` job).
Independent Build/Supply retest must produce the x86_64 runtime evidence.

## S1_SHARED_VALIDATOR_FOLLOWUP_REQUIRED

`tools/audit/validate_security_audit_evidence_preservation.py` is frozen
read-only for S1 (parallel-writer collision guard vs S0). Two of its checks
are era-pinned to the previous delivery and cannot pass on this branch:

1. `validate_project_memory` requires the last ledger event to be exactly
   `ANOX-EVENT-0052`. Recording S1's material event (required by canonical
   continuity) necessarily advances the ledger past that pin.
2. `validate_no_product_changes` fails on any diff vs `BASE_SHA` touching
   `android/`, `crypto/rust/`, `.github/workflows/` — precisely the
   surfaces this session is authorized and required to remediate, and
   `validate_base` pins the previous two-commit topology.

Required follow-up (post-integration, not by S1): extend the shared
validator with S1-era handling — the same pattern S0 used
(`_s0_delivery_active`) — recognizing the S1 delivery branch, its ledger
event, and the S1-authorized build/provenance surfaces as the new baseline
for `validate_no_product_changes`.

All other canonical validators unaffected by era pins were run and pass.

## Scope honesty

- `crypto/rust/src/**` behavior diff vs base: NONE (verified; the static
  gate enforces it).
- No B-004/B-005 implementation; no product behavior change.
- No MSC unit CLOSED; INDEPENDENTLY_RETESTED remains PENDING for all four
  units. Global open MSC units: 42.
- Remote mutation: NONE.
