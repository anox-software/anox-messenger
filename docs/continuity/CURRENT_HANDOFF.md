# CURRENT_HANDOFF — anoX V1

**Event:** `ANOX-EVENT-0054` — REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001  
**Delivery branch:** `security/remediation-s1-build-provenance-001`  
**Substantive HEAD:** `fc58414b6790c07f65d1dc9f72c019abd42efc86`  
**Main baseline:** `0f932520393feee6d479cc099f179f5766323125`  
**Effective gate:** `REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001 — ESTABLISH NATIVE BUILD PROVENANCE + EVIDENCE GATES (Ready For Remote; awaiting human merge)`

Described HEAD: fc58414b6790c07f65d1dc9f72c019abd42efc86

## Pre-merge gate

`REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001 — ESTABLISH NATIVE BUILD PROVENANCE + EVIDENCE GATES (Ready For Remote; awaiting human merge)`

- Established the trusted native build/provenance chain end to end: `crypto/rust/rust-toolchain.toml` (Rust `1.97.1`, targets `aarch64-linux-android` + `x86_64-linux-android`) → `tools/security/native_build.py` (asserts NDK `r26c` / cargo-ndk `4.1.2`; builds via `cargo ndk`; emits `build/native/native-manifest.json` binding source SHA `0f932520…`, `Cargo.lock` SHA-256, toolchain and per-ABI artifact SHA-256/size + JNI export fingerprint) → reproducibility via two clean builds (PASS) → Gradle consumes only `build/native/jniLibs` (`keepDebugSymbols`, `verifyNativeArtifacts` fail-closed, ABI filters pinned) → `tools/security/validate_apk_contents.py` v2 binds packaged `.so` hashes to the manifest (debug + release PASS) → CI `instrumented-arm64`/`instrumented-x86_64` jobs run `connectedDebugAndroidTest` on the manifest-bound artifact.
- Eliminated the committed `.so` false-closure path (`android/src/main/jniLibs/` removed from Git, git-ignored, Gradle guard rejects reintroduction).
- B-017-Lite hygiene gates live and fail-closed: `cargo audit` (0 vulns / 110 locked deps), `tools/security/secret_scan.py`, Android lint `abortOnError`, Gradle wrapper validation, `tools/security/validate_ci_pipeline.py` structural gate, all `uses:` pinned to 40-char SHAs, `contents: read` only.
- MSC-038: `tools/audit/validate_b021_verification_matrix.py` + `docs/security/remediation/msc_state.jsonl` enforce the stage chain (no IMPLEMENTED→CLOSED jump; FCP-1 provenance-bound RUNTIME_TESTED; FCP-7 retester authority separation; `--check closure` fails on unverified pre-product rows).
- Runtime evidence: `connectedDebugAndroidTest` on local `anox_api34_arm64` (API 34, arm64-v8a) — **66/66 instrumented tests PASS** on the produced manifest-bound artifact (CryptoInstrumentedTest incl. BufferTooSmall, DeviceAuth keystore, storage). x86_64: `RUNTIME_ENVIRONMENT_UNAVAILABLE` locally; CI path present.
- `tools/audit/test_s1_build_provenance.py`: 66 adversarial fail-closed tests PASS.
- `S1_SHARED_VALIDATOR_FOLLOWUP_REQUIRED` recorded: the frozen shared preservation validator is era-pinned to `ANOX-EVENT-0052` and read-only for S1; the S1-era extension (S0 `_s0_delivery_active` pattern) is required post-integration.
- No `crypto/rust/src` behavior change; no B-004/B-005 work; no MSC unit closed; 42 open MSC units; remote mutation NONE.

## Post-merge gate

`SECURITY_REMEDIATION_WAVE_1 — REMEDIATION_SESSION_S0 ∥ REMEDIATION_SESSION_S1 (S1 delivered — independent Build/Supply retest pending; S0 integration + sessions S2..S10 remain Candidate per coverage gate)`

## Preserved audit outcomes

- `AUDIT-SECURITY-CODEBASE-001`: PASS_WITH_FINDINGS; 21 candidates (1C/3H/8M/7L/2I); actual model Claude Opus 5 Medium (MODEL_DEVIATION vs requested Fable 5.1 High — accepted by HUMAN_DECISION_H2 with preserved rationale).
- `AUDIT-SECURITY-CODEBASE-002` (blind): PASS_WITH_FINDINGS; 17 candidates (0C/3H/6M/6L/2I); Claude Fable 5.1 High.
- `CODEBASE-SECURITY-CONSENSUS-001`: PASS; 18 normalized roots; `ROOT-005` single-audit/arbiter-confirmed; `ROOT-016` NOT_A_FINDING; Pre-B004 set = 12 roots.
- `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`: PASS_WITH_FINDINGS; 12 candidates; `ANOX-BUILDSC-CANDIDATE-001` EVIDENCE_INTEGRITY=CRITICAL (committed `.so` stale vs source `7db20fa`) — **the S1 provenance chain removes this bypass path; retest pending**.
- `AUDIT-SECURITY-CRYPTO-JNI-001` (specialist): PASS_WITH_FINDINGS at `a79166ab`; 6 candidates (0C/1H/3M/1L/1I); `JNI_ABI_REVISION=YES`; verdict `COMPONENT_INTERNAL_REDESIGN_ONLY`; Pre-B004 Crypto/JNI gate set = 8 members; ROOT-013 canonical `MEDIUM` (OPEN).
- `AUDIT-SECURITY-AUTH-DPOP-001` (specialist): PASS_WITH_FINDINGS at `638e63a2`; 3 candidates (0C/0H/1M/2L/0I) + 3 architecture gaps; B-002 29/29 production + 14/14 test files; 40 requirements, 0 unmapped; 173/173 focused tests pass; physical verification still required; verdict `COMPONENT_INTERNAL_REDESIGN_ONLY`, SEC-C not required.
- `AUDIT-SECURITY-ANDROID-STORAGE-001` (specialist): PASS_WITH_FINDINGS at `b9abeb08`; 2 candidates (0C/0H/0M/2L/0I) + 3 architecture gaps; 49/49 production + 14/14 test files; 42 requirements, 0 unmapped; 177/177 focused tests pass; physical verification still required; verdict `COMPONENT_INTERNAL_REDESIGN_ONLY`, SEC-C not required.
- `AUDIT-SECURITY-ATTACKCHAIN-001` (specialist): PASS_WITH_FINDINGS at `e5458490`; 15 chains (0C/4H/7M/3L/1I; HIGH = AC-001/003/006/012; AC-003 `CONDITIONAL_CRITICAL_AT_B004_IF_VERIFIER_DEFAULTS_PORTED` overlay only); evidence E2=8/E1=6/E0=1; 68 security items, UNMAPPED=0; verdict `CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED`, SEC-C not required; 13 rejected hypotheses; final re-audit mandatory = AC-001/003/006/012 + AC-005/008/010.
- `MASTER-SPECIALIST-CONSOLIDATION-001` (consolidation): PASS_WITH_CONSOLIDATION_FINDINGS at `1eb773069d81`; 90/90 source items accounted; 44 `MSC_UNIT_001..044` (42 OPEN + 2 REJECTED); verdict `CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED`; SEC-C not required.
- `SECURITY-REMEDIATION-COVERAGE-GATE-001` (coverage gate): PASS at `610ed0833753`; 42/42 OPEN `MSC_UNIT_*` covered; dependency cycles 0; parallel-writer collisions 0; `FCP_1..8` enforced; false-closure A–F blocked; `SC/CC 14/14`; `PHYSICAL_P1..P17` assigned 17/17, executed 0; retest owners 42/42; DoD unowned 0.
- `HUMAN-PRE-REMEDIATION-DECISIONS-001` (human governance decision record): `DECIDED — REMEDIATION_WAVE_1_AUTHORIZED` at `9e585468d081`; H1/H2/H3/R1 decided by Human Product & Security Owner; `SECURITY_REMEDIATION_START_AUTHORIZATION = GRANTED_BY_HUMAN_OWNER` for first wave `S0 ∥ S1`; authorization is not execution.
- `REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001`: IMPLEMENTED at `0f932520393f` (substantive `fc58414b6790`); MSC-001/002/003/038 `IMPLEMENTED+AUTOMATED_TESTED`, MSC-001/002 additionally `RUNTIME_TESTED` (arm64, provenance-bound); `INDEPENDENTLY_RETESTED` pending; 0 units closed.

## Open product findings

- `ANOX-MAINARCH-013`, `ANOX-MAINARCH-018` (`PHYSICAL_VERIFICATION_REQUIRED`), `ANOX-MAINARCH-030`, `ANOX-LEGACY-INTEGRATION-005`, `ANOX-LEGACY-B003-001`
- `ANOX-SECURITY-ARCH-001`..`010` (Open; 001..004 are B-004 blockers; `ANOX-SECURITY-ARCH-010` scheduled trigger `RETIRE_AT_B004_START` — stays Open/INFO until B004 start)
- Active consensus roots `ROOT-001`..`ROOT-015`, `ROOT-017`, `ROOT-018` (`ROOT-013` canonical severity `MEDIUM`, remains OPEN) + `ANOX-CRYPTOJNI-CANDIDATE-001..006` + `ANOX-AUTHDPOP-CANDIDATE-001..003` + `ANOX-AUTHDPOP-GAP-001..003` + `ANOX-ANDROIDSTORAGE-CANDIDATE-001..002` + `ANOX-ANDROIDSTORAGE-GAP-001..003` + `ANOX-ATTACKCHAIN-CANDIDATE-001..015` + consolidated `MSC_UNIT_001..042` open units (see `docs/security/audit-evidence/audit_traceability.jsonl`)

## Product state

- `PRODUCT_DEVELOPMENT = BLOCKED_PENDING_FINAL_AUDIT`
- `B004 = NOT_STARTED`
- `B005 = NOT_STARTED`
- `SECURITY-REMEDIATION-COVERAGE-GATE = EXECUTED_AND_PRESERVED (PASS — coverage only, NOT a remediation authorization)`
- `HUMAN_PRE_REMEDIATION_DECISIONS_AND_AUTHORIZATION = EXECUTED_AND_PRESERVED (decided; SECURITY_REMEDIATION_START_AUTHORIZATION = GRANTED_BY_HUMAN_OWNER)`
- `SECURITY REMEDIATION = IN_PROGRESS (REMEDIATION_SESSION_S1 delivered — IMPLEMENTED_PENDING_INDEPENDENT_BUILD_SUPPLY_RETEST; REMEDIATION_SESSION_S0 completed on its separate branch per human orchestration)`
- `SECURITY_REMEDIATION_WAVE_1 (REMEDIATION_SESSION_S0 ∥ S1) = IN_PROGRESS`
- `FINAL-OPERATIONAL-HANDOFF-BOOTSTRAP-ACCEPTANCE = PENDING / NOT_EXECUTED`
- `Human final product gate = NOT_EXECUTED`
