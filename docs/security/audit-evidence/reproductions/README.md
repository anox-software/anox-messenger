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

From `AUDIT-SECURITY-CRYPTO-JNI-001` (at SHA `a79166ab7e65db71ba70e3a427df2ad017dc9225`; all values are `TEMP_CURRENT_SOURCE_BUILD_EVIDENCE` / host-only — ROOT-001 still unresolved):

- **Independent temp rebuild:** `cargo ndk -t arm64-v8a -t x86_64 build --release --locked --offline` reproduced the *identical* current-source hashes (`05f3f40c…` / `c002cc42…`) — confirming the committed `.so` remains stale since `7db20fa`. Disassembly proof at offset `0x3724c`: committed `.so` emits `mov w0, #-0x2`, current-source emits `mov w0, #-0xb` (−11).
- **Evidence-method correction:** `"Output buffer too small"` is absent from *both* binaries (LTO strips unused `Display` strings); string-presence is not a valid provenance check for the −2→−11 change.
- **Identity serialization (current source):** 0 OTK 457 B; 10 → 2866 B; **20 → 5269–5287 B (> 4096)**; 50 → 12,537 B; 100 → 24,547 B; vodozemac cap 5000 → 1.23 MB. Publish removes unpublished publics (20 OTK: 5287→2878 B).
- **Session serialization (current source):** initial ≈1.0–1.2 KB; 200 ping-pong ≈2.6–2.8 KB; ≥40 skipped keys ≈8 KB; bounded max (5 chains × 40 keys) ≈29.9 KB.
- **OTK enumeration:** 20/20 index sweeps produced duplicates; worst sweep 10/20 unique; 140–146 omissions across 20 sweeps; `nth(i)` samples a fresh `HashMap` permutation per call.
- **Handle/address reuse:** host allocator returned a freed `Identity` address for the next allocation in 7/100 trials; `Identity` (408 B) and `Session` (3752 B) are different size classes (cross-type reuse 0/100 — allocator luck, not a guarantee).
- **Deserialize collapse:** `cryptoDeserialize*` return `0` for every error including `UnsupportedVersion` (−9 → 0), proven by reproduction.
- **Count/set divergence:** after `mark_keys_as_published`, stored count 20 / unpublished 0 / index 0 → −3 `InvalidSession`.
- **Host tests:** `cargo test` 17/17 pass — JNI module cfg-gated out, zero JNI evidence. JNI runtime tests: `NOT_RUN` (no approved runtime environment).

From `AUDIT-SECURITY-AUTH-DPOP-001` (at SHA `638e63a22c91ca81365bf55c8a59ec47878dd7fd`; JVM evidence only — no physical/device evidence):

- **DPoP verifier fail-open defaults:** `verify(attackerProof,"POST",uri)` → `Valid` with an attacker-generated key; same proof accepted by two default-constructed verifiers; `expectedJwkThumbprint`/`accessToken`/`expectedNonce` all default `null` (`DpopProofVerifier.kt:46-48`); `DpopProofFactory.createProof(accessToken=null, nonce=null)` mirrors the default client-side.
- **HTU collisions (harness-verified):** decoded `URI.getPath()` is signed — `/v1/a%2Fb` ≡ `/v1/a/b`; `%3F`/`%23`/`%00` decoded; double-decoding; userinfo retained in the signed claim; `:443` default port NOT elided (fail-closed interop).
- **Replay cache:** check-and-insert atomic per instance (64 threads × 200 rounds ⇒ exactly 200 accepts); two instances both accept the same `jti`; 1,000,000 unique `jti` retained with no cap; wall-clock rollback after eviction re-accepts an evicted proof (−250 s ⇒ `Valid`).
- **Malformed-input handling:** 5 JWK mutations + off-curve all → `MALFORMED`; every parse failure → `Invalid(reason)`, never throws; malleated ECDSA (n−s) → `REPLAYED_JTI` (jti identity, not bytes).
- **Keystore/DeviceAuth:** missing alias → resolver → bound ⇒ Terminal (source + instrumented test); two simultaneous `createKeyIfAbsent()` → check-then-act, `generateKeyPair` overwrites alias, StrongBox-`catch` deletes the peer's key (source); `RegistrationSessionKey.decrypt()` → `getOrCreateKey()` still creates on read.
- **Test execution:** `./gradlew --offline --no-daemon :android:testDebugUnitTest --tests 'com.anox.messenger.security.deviceauth.*' --tests 'com.anox.messenger.account.*'` → 173 executed / 173 passed (deviceauth 69, account 104). Instrumented (27) + physical: NOT_RUN.
- **Harness:** `/tmp/anox_auth_dpop_harness/` (`Harness.java`, `Size.java`) compiled against `android/build/tmp/kotlin-classes/debug` + `nimbus-jose-jwt-10.9.1` + `kotlin-stdlib-2.2.21` — 22 adversarial cases.

From `AUDIT-SECURITY-ANDROID-STORAGE-001` (at SHA `b9abeb0850a476716403d224b87a857c1147502e`; JVM + source-review evidence only — no physical/device evidence):

- **Marker state map (harness-verified, 16 states + 8 single-bit flips):** structural corruption (size≠6 / bad magic / unknown version) fails closed `(T,T)`; payload-level corruption fails **open** — v1 garbage flags (`0x03`, `0xff`) and v2 `0x00`/`0x04` → unbound; single-bit flips of `0x03` still block. Absence is interpreted as first run, not unknown state (ROOT-007).
- **AndroidX `AtomicFile` (core:1.12.0) behaviours:** `finishWrite()` returns normally on fsync **and** rename failure (`Log.e` only) leaving `.new` residue; `openRead()`/`startWrite()` auto-rename a sibling `.bak` over the live file (planted `.bak` → returned by `readFully`); `delete()` results ignored by `clear()` (CANDIDATE-002).
- **Empty file semantics:** zero-length registration session file → `readFully` len 0 → `NotStarted` (first-run downgrade; `FileRegistrationSessionStore.kt:44`).
- **Codec bounds:** empty/1-byte/version-2/unknown-tag/truncated/negative/`0x7fffffff`/16385-length inputs all → null; trailing bytes ignored; tag relabel among identical-layout states accepted; empty grant accepted; NCS-variant UUID accepted (ROOT-015); malformed UTF-8 username rejected; 16384-B reason accepted, 16385 rejected.
- **Create-on-read (source):** `RegistrationSessionKey.decrypt()` → `getOrCreateKey()` → `generateKey()`; `CryptoBridge.initializeMasterKey()` recreates `anox_crypto_master_key` on every `getInstance()` including status/read paths (ROOT-006 CONFIRMED + expansion).
- **Wipe truthfulness (source):** `wipeLocalCrypto()` returns `Success` after ignored `File.delete()` results; `clear()` ignores all `AtomicFile.delete()` results; `anox.b003.session.v1` alias never deleted; no cross-domain wipe orchestrator (ROOT-012 EXPANDED, GAP-002).
- **Test execution:** `./gradlew --offline --no-daemon :android:testDebugUnitTest --tests 'com.anox.messenger.account.*' --tests 'com.anox.messenger.security.deviceauth.*' --tests 'com.anox.crypto.*'` → 177 executed / 177 passed (account 104, deviceauth 69, crypto error-map 4). Instrumented (66) + physical: NOT_RUN.
- **Harness:** `/tmp/anox_android_storage_audit/harness/` (`Harness.java`) compiled against `android/build/tmp/kotlin-classes/debug` + `kotlin-stdlib-2.2.21` + `androidx.core:core:1.12.0` `AtomicFile` source with stub `Context`/`Log`; `/tmp/anox_android_storage_audit/atomicfile/` held the extracted library source.

From `AUDIT-SECURITY-ATTACKCHAIN-001` (at SHA `e54584903a353e98ad154d1e8f90f93ed9d7db14`; production classes compiled from unchanged source + repo JVM test doubles — no device/emulator authorized):

- **Baseline continuity:** `git diff 869b99a..e545849` over `android/src`, `crypto/`, `.github`, `*.kts`, `gradle` is empty — product source byte-identical to the consensus-audited SHA; committed `.so` unchanged and stale since `7db20fa`.
- **DPoP composition harness (Harness.java, 27 cases):** `/v1/a%2Fb` proof validated against `/v1/a/b` (decoded-path collision survives correct JKT binding — AC-002); attacker-generated proof + stolen token accepted when `jkt`/`ath` optional (AC-003; mandatory `ath` alone proven insufficient); same proof re-accepted across independent cache instances, after restart, and after −250 s wall-clock rollback (AC-004); marker loss + session loss ⇒ `canStartNew=true`, surviving alias re-binds same JKT to a new account, absent alias generates new key (AC-001 A/B); `CommitArmed` + `Rejected` persists `Failed` while marker ARMED, `canStartNew=false` (AC-014); registration wire carries `jwk` and `proof` independently (proof unbound) and `commitRegistration` has no PoP/DPoP/idempotency (AC-010).
- **Marker harness (MarkerHarness.java, 9 cases):** valid bound marker bytes `414e58420203…` → `bound=true armed=true`; absent → first-run semantics; `clearBinding()` bytes `414e58420200` equivalent to absent; rollback to `0x02` ARMED blocks creation; rollback to zero flags and v1-garbage payload fail **open**; structural corruption fails **closed**; surviving alias + absent marker → resolver `Present` (fresh first-run input — AC-001 Variant A precondition).
- **Native measurements:** preserved from `AUDIT-SECURITY-CRYPTO-JNI-001` (`TEMP_CURRENT_SOURCE_BUILD_EVIDENCE`) — session pickle 7196→29923 B over 8 chains; identity 500 OTK = 122391 B / 1000 = 244483 B / 5000 = 1228738 B; stored=5000 unpublished=5000.
- **Instrumented + physical:** `NOT_RUN` (no device/emulator authorized; no results fabricated). `AC-013` physical evidence vacuum recorded as CLOSURE_RISK_ENABLING_CONDITION (P1–P14 campaign required on a provenance-verified binary).
- **Harness:** `/tmp/anox_attackchain_001/` (`Harness.java`, `MarkerHarness.java`, `out.txt`, `marker_out.txt`, `METHOD.txt`, `traceability_extract.txt`) compiled against `android/build/tmp/kotlin-classes/{debug,debugUnitTest}` + `nimbus-jose-jwt-10.9.1` + `kotlin-stdlib-2.2.21` — 36 benign composition cases; **not authoritative**, results preserved in the report only.

From `MASTER-SPECIALIST-CONSOLIDATION-001` (at base SHA `1eb773069d81ea3d12b76249c73f2f5fb0b6cae9`; analytical read-only consolidation — no build, test, harness or device run executed):

- All runtime measurements and native observations carried by the consolidation are **transcribed** from the nine hash-verified preserved reports above; the consolidation produced no new empirical evidence.
- `/tmp/anox_master_consolidation_001/` (the consolidation's analytical scratch builder) is **not authoritative** and not preserved; its outputs exist only inside the preserved report.
- The consolidation's machine-readable layer (`msc_*` records in `../audit_traceability.jsonl`) is preserved evidence of the consolidation's conclusions — it is not itself remediation evidence.

## Authoritative locations

The authoritative evidence is:

1. The preserved report bodies in `docs/reports/security/audits/` and the Master Consolidation report in `docs/reports/security/consolidation/` (hash-bound in `../evidence_hashes.json`).
2. The structured mappings in `../audit_traceability.jsonl` and `../audit_registry.jsonl`.

**`/tmp` artifacts are NOT authoritative.** Paths such as `/tmp/anox_buildsc_out_1/`, `/tmp/anox_audit2/`, `/tmp/anox_crypto_jni_*/` (host target, repro crate, cargo-ndk output), `/tmp/anox_auth_dpop_harness/` (Auth/DPoP adversarial harness), `/tmp/anox_android_storage_audit/` (AtomicFile extracted source + adversarial harness), `/tmp/anox_attackchain_001/` (Attackchain composition + marker harnesses), and `/tmp` proof scripts were audit-run artifacts; they are transient, unowned by this repository, and are deliberately not copied in as evidence. Their *results* are preserved inside the reports themselves; only the recorded hash values are carried into `../evidence_hashes.json`.

## Boundary

- No finding is remediated here.
- No audit was re-run for this preservation task; reproduced values are transcribed from the preserved reports.
- `BLIND_CHECKPOINT_CODESEC2.md` (in `/tmp`) is a checkpoint summary only — it is not the Audit-002 report and is not preserved.
- Any future retest must execute against a provenance-verified binary (see `ANOX-BUILDSC-CANDIDATE-001` and the `NATIVE_RETEST_ACCEPTANCE_BLOCKERS` gate set).
