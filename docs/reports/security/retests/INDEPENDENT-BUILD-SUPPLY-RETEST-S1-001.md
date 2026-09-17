# INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001 — Independent Security Retest of REMEDIATION-SESSION-S1

**Result:** `PASS_WITH_FINDINGS`
**Mode:** `READ_ONLY_INDEPENDENT_BUILD_SUPPLY_RETEST` (no file changes, no commits, no remote mutation)
**Retest authority:** fresh independent session — Claude Opus 5 (Medium) — distinct from the implementing session (Devin SWE-2 Max). FCP-7 respected.
**Date:** 2026-09-15
**Preserved by:** `REMEDIATION-S1-CANONICAL-INTEGRATION-001` (the retest itself was delivered as session output; this file is its repository-preserved record).

## Target

| Item | Value |
|---|---|
| S1 base | `0f932520393feee6d479cc099f179f5766323125` |
| S1 substantive | `fc58414b6790c07f65d1dc9f72c019abd42efc86` |
| S1 final head | `e32463ca71b0fec62a5f20026e6dc528f9bff30c` |
| Two-commit topology | PASS (metadata commit is direct child of substantive) |
| Retest worktree | `/Users/3xpress/Desktop/anoX-s1-retest`, detached at S1 final head, clean |

## Independent reproduction (not taken from the implementer's report)

- **Authoritative native build executed twice** on the retest host (NDK r26c `26.2.11394342`, rustc 1.97.1, cargo-ndk 4.1.2; separate `CARGO_TARGET_DIR`s; output under `/tmp`).
- `arm64-v8a` = `c854de2587ec1bd6387f39770feeabf24bf6cf2b729911c5ba57f5e4d8bd7b57` (both builds; `cmp` byte-identical; equals S1's recorded hash).
- `x86_64` = `77a404b2bd6f13ce50b4360f439bd09e6cff6f6d8233557fe89c195fa33d85e2` (both builds; byte-identical; equals S1's recorded hash).
- **17 JNI exports per ABI** read from the produced binaries with `llvm-nm`; sets identical across ABIs and equal to the 17 Kotlin `external fun` declarations. Missing-symbol and foreign-surface mutations both fail closed.
- `cargo audit`: **110 crate dependencies, 0 vulnerabilities** (reproduces S1).
- `native_build.py verify`: 12/12 mutations fail closed (foreign `.so`, missing ABI, stray `.so`, extra ABI, tampered hash, wrong `repo_sha`, tampered `Cargo.lock` hash, unpinned channel, dropped ABI, tampered JNI fingerprint, absent manifest, malformed manifest).
- `validate_apk_contents.py` v2: 10/12 mutations fail closed (missing lib, wrong ELF machine, extra ABI, injected `.so`, stale hash, PEM in assets, PEM inside `.so`, forbidden governance path, `.jks`, duplicate ZIP entry, missing `--native-manifest`).
- Committed-`.so` bypass: 0 tracked `.so` at HEAD; injected committed `.so` → static gate FAIL; `.gitignore` covers `android/src/main/jniLibs/`; Gradle `verifyNativeArtifacts` gates every `package*` task. **AC-012_MINIMUM_BREAKER = PASS** (full AC-012 not declared closed).
- Rust behavioral scope: `crypto/rust/src/**` diff vs S1 base = **empty** (`NATIVE_BEHAVIOR_SOURCE_CHANGED = NO`).
- S1 adversarial suite: 66/66 PASS. Quality: **56/66 meaningful fail-closed mutations** — 7 controls by design; 3 deficient (`test_24` tautological; `test_46`/`test_47` non-discriminating — control already yields 5 blockers); 2 weak (`test_22` stubbed oracle; `test_23` never invokes `rebuild-compare`).
- Central validator `tools/audit/validate_security_audit_evidence_preservation.py`: S1 diff = **NONE** (blob `b61723a9…` identical). Its 3 failures are structural-era mismatches (pre-remediation `BASE_SHA`, "no product/build changes" assumption, `LEDGER_EVENT = ANOX-EVENT-0052` pin) — **`S1_SHARED_VALIDATOR_FOLLOWUP_REQUIRED = CONFIRMED`**, not corrupt S1 evidence.
- Continuity: `validate_continuity` live = PASS in a real clone with correct branch topology; archive = PASS; B027-A/B/integrity = PASS. Handoff zip SHA-256 `b9ba8aea3b072ebb1140c2725f23ef7b4fdf89bf59c721551f7817ae049f239e` matches (isolated S1 artefact; superseded by post-S0 integration).
- Runtime: **ARM64 not independently reproduced** (no JRE / Android SDK / emulator on retest host); **X86_64 = `PENDING_REAL_CI_OR_INDEPENDENT_RUNTIME_EVIDENCE`**.

## Findings

| ID | Severity | Finding |
|---|---|---|
| F-1 | MEDIUM | APK validator path-normalization bypass: an extra foreign `.so` stored as `./lib/<abi>/x.so` or `LIB/<abi>/x.so` is invisible to the ABI/hash/ELF inventory (`startswith("lib/")`), validator returns PASS. Secret-marker scan still covers such members. |
| F-2 | MEDIUM | `validate_s1_build_provenance.py` guards the Rust behavior-scope check with `.git.is_dir()`; in a linked worktree the check is silently skipped while the gate reports PASS. |
| F-3 | MEDIUM | FCP-1 enforced by `any()` over a regex alternation that also matches *filenames*; `MSC-UNIT-001.RUNTIME_TESTED` satisfied FCP-1 solely because its evidence path contained `PROVENANCE_VERIFIED_NATIVE_RUNTIME`. Contract requires BUILD_ARTIFACT_HASH_PROOF **+** PROVENANCE_VERIFIED_NATIVE_RUNTIME, same-run. |
| F-4 | LOW/MEDIUM | `validate_ci_pipeline.py` never inspects `needs:`; lineage graph unenforced. `android-release` lacked the `native_build.py verify` re-verification step present on every other consumer. |
| F-5 | LOW | `reproducible_build_confirmed` always `null`; never set, never checked — decorative. |
| F-6 | LOW | `secret_scan.py` skips any file with a NUL in its first 2048 bytes; line-anchored PEM misses indented keys; `validate_apk_contents.py` silently skips members > 64 MiB. |
| F-7 | LOW | `write_manifest` stamps `git rev-parse HEAD` without checking working-tree cleanliness — a dirty tree yields an unqualified clean SHA claim. |
| F-8 | INFO | `PIN_PROVENANCE_UNVERIFIED` for `dtolnay/rust-toolchain@4360b525…` (official repo resolves; no tag; `diverged` from force-moved `stable`). All other 7 pins resolve to exact official release tags. Pins must stay SHA-based. |
| F-9 | LOW | B-021 stage ordering `continue`s over absent intermediate stage records (e.g. `INDEPENDENTLY_RETESTED=PASS` accepted with `RUNTIME_TESTED` omitted); FCP-7 compares `recorded_by` by exact equality and tolerates a missing field. |

## MSC status established by this retest

`INDEPENDENTLY_RETESTED = PASS` for the applicable static / build-provenance / automated S1 evidence of MSC-UNIT-001/002/003/038. **No unit CLOSED. No `EVIDENCE_PRESERVED`. No independent native runtime evidence for either ABI.** Global: `OPEN_MSC = 42`, `SECURITY_REMEDIATION = IN_PROGRESS`, `B004/B005 = NOT_STARTED`, `PRODUCT = BLOCKED_PENDING_FINAL_AUDIT`.

## Integration blocker stated by the retest

S1 was **not directly merge-ready**: required sequence S0 corrected → S0 retest → S0 evidence preservation → S0 merge → integrate S1 onto new main → authorized shared-validator era extension → regenerate S1 metadata → rerun gates → targeted integration retest → preserve/merge S1. This sequence is executed by `REMEDIATION-S1-CANONICAL-INTEGRATION-001`.
