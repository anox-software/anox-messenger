# AUDIT-SECURITY-CRYPTO-JNI-001 — FINAL REPORT

## AUDIT RESULT
`PASS_WITH_FINDINGS`

(A PASS does NOT unblock Product Development.)

## AUDIT
`AUDIT-SECURITY-CRYPTO-JNI-001`

## PROVIDER
Anthropic

## MODEL
Claude Fable 5.1 High (runtime label as reported by the session configuration). Note: the first reply in the audit session misreported the label and wrongly issued `BLOCKED — MODEL_UNAVAILABLE`; that reply was retracted before any analysis and is superseded by this report.

## MODEL REQUIREMENT SATISFIED
YES

## MODE
`READ_ONLY_CRYPTO_JNI_NATIVE_SECURITY_SPECIALIST_AUDIT`

## AUDITED SHA
`a79166ab7e65db71ba70e3a427df2ad017dc9225`

## HEAD AT END
`a79166ab7e65db71ba70e3a427df2ad017dc9225`

## ORIGIN MAIN
`a79166ab7e65db71ba70e3a427df2ad017dc9225`

## WORKING TREE
CLEAN (`git status --short` empty; `git diff --check` clean; branch `main`; no stashes)

## REPOSITORY MODIFIED
NO

## REMOTE MUTATION
NONE (only `git fetch origin`)

---

## PRESERVED EVIDENCE VALIDATION
**PASS** — `python3 tools/audit/validate_security_audit_evidence_preservation.py` → `SECURITY AUDIT EVIDENCE PRESERVATION: PASS`, exit 0 (all sections OK, Project Memory synced to ANOX-EVENT-0045, Crypto/JNI gate recorded as candidate/not executed).

## BUILD PROVENANCE LIMITATION
**Independently re-verified.** `git log 7db20fa..HEAD -- crypto/` shows Rust source changed in `342d553` (`error.rs`, `lib.rs`, `tests.rs`); committed `.so` (arm64 `11a958a5…`, x86_64 `ecf9fdc1…`) are unchanged since `7db20fa`. Disassembly proof: at identical offset `0x3724c` inside `cryptoGetCurve25519PublicKey`, the committed arm64 `.so` emits `mov w0, #-0x2` while the current-source temp build emits `mov w0, #-0xb` (−11). **All runtime-derived statements in this report are `TEMP_CURRENT_SOURCE_BUILD_EVIDENCE` or host-only evidence. Final closure of every native finding MUST be re-performed against a provenance-verified canonical binary after Build/Supply remediation (ROOT-001 unresolved).**

Additional evidence-method note: the string `"Output buffer too small"` is absent from **both** the committed `.so` and the current-source temp build (0 occurrences each; LTO strips unused `Display` strings). String-presence is therefore **not** a discriminating provenance check for the −2→−11 change; disassembly or runtime is required. This does not weaken the Build/Supply conclusion (which rested on bit-identical old-source rebuild), but the heuristic must not be reused.

---

## CRYPTO/JNI SOURCE INVENTORY

| Component | Location |
|---|---|
| JNI exports, handle registries, unsafe derefs, JNI I/O helpers | `crypto/rust/src/lib.rs` (`mod jni_bridge`, `#[cfg(target_os="android")]`, L20–545) |
| Identity wrapper (vodozemac `Account`), OTK accessors/generation/publication, pickle/unpickle, session creation | `crypto/rust/src/identity.rs` |
| Session wrapper, encrypt/decrypt, pickle/unpickle | `crypto/rust/src/session.rs` |
| Serializer (AES-256-GCM envelope `ANOX`+ver+nonce) | `crypto/rust/src/serialization.rs` |
| Native error enum + i32 ABI mapping | `crypto/rust/src/error.rs` |
| Host tests (17, no JNI) | `crypto/rust/src/tests.rs` |
| Manifest/lock (`panic="abort"`, lto, vodozemac 0.10.0, jni 0.21.1) | `crypto/rust/Cargo.toml`, `Cargo.lock` |
| Kotlin externals | `crypto/android/src/main/java/com/anox/crypto/CryptoNative.kt` |
| Bridge / singleton / lock / state key / persistence / wipe | `crypto/android/src/main/java/com/anox/crypto/CryptoBridge.kt` |
| Kotlin error mapping | `crypto/android/src/main/java/com/anox/crypto/CryptoError.kt`, `CryptoResult.kt` |
| Registration consumer of OTK material | `android/src/main/java/com/anox/messenger/account/CryptoBridgeLocalE2eeIdentityStep.kt`, `PublicE2eeIdentityMaterial.kt`, `LocalE2eeIdentityStep.kt`, `RegistrationOrchestrator.kt` (`DEFAULT_ONE_TIME_KEY_COUNT = 20`) |
| Instrumented tests (never executed in CI) | `crypto/android/src/androidTest/java/com/anox/crypto/CryptoInstrumentedTest.kt` |
| JVM error-mapping test | `android/src/test/java/com/anox/crypto/CryptoErrorMappingTest.kt` |
| Stale committed binaries | `android/src/main/jniLibs/{arm64-v8a,x86_64}/libanox_crypto.so` |

Not present anywhere: JNI export for `unpublished_one_time_keys`, `get_one_time_key(KeyId)`, `mark_keys_as_published`, fallback key, `sign`. `Device*`/`Registration*` files under `security/deviceauth` do not touch the native layer (Auth/DPoP scope).

## JNI EXPORTS
**Count: 17** (Rust `#[no_mangle]` = 17; Kotlin `external fun` = 17; temp arm64 and x86_64 dynamic symbol tables = 17 each; all four sets identical).

| # | Export | Handle | Mutation | Error contract | Unsafe deref |
|---|---|---|---|---|---|
| 1 | `cryptoInit` | – | none | always `1` | – |
| 2 | `cryptoCreateIdentity` | → Identity | alloc+register | never fails (ptr) | – |
| 3 | `cryptoDestroyIdentity` | Identity | remove+free | void; silent no-op | `Box::from_raw` |
| 4 | `cryptoGetCurve25519PublicKey` | Identity | none | −1/−3/−11/−10/−12 | `&*` |
| 5 | `cryptoGetEd25519PublicKey` | Identity | none | same | `&*` |
| 6 | `cryptoGenerateOneTimeKeys` | Identity | **mutates** | −1 / `CryptoError` | `&mut *` |
| 7 | `cryptoOneTimeKeysCount` | Identity | none | −1 | `&*` |
| 8 | `cryptoGetOneTimeKey` | Identity | none | −1/−3(not found!)/−11 | `&*` |
| 9 | `cryptoSerializeIdentity` | Identity | none | −1/−3/−11/`CryptoError` | `&*` |
| 10 | `cryptoDeserializeIdentity` | → Identity | alloc+register | **0 on any error** | – |
| 11 | `cryptoCreateOutboundSession` | Identity → Session | alloc+register | **0 on any error** | `&*` |
| 12 | `cryptoCreateInboundSession` | Identity **mut** → Session | consumes OTK, alloc | −1/−3/−11/`CryptoError` | `&mut *` |
| 13 | `cryptoEncrypt` | Session | **mutates ratchet** | −1/−3/−11/`CryptoError` | `&mut *` |
| 14 | `cryptoDecrypt` | Session | **mutates ratchet** | same | `&mut *` |
| 15 | `cryptoDestroySession` | Session | remove+free | void; silent no-op | `Box::from_raw` |
| 16 | `cryptoSerializeSession` | Session | none | −1/−3/−11/`CryptoError` | `&*` |
| 17 | `cryptoDeserializeSession` | → Session | alloc+register | **0 on any error** | – |

Thread-safety requirement (actual): every handle-taking export requires external mutual exclusion per object *and* across destroy; none is enforced natively. Lifetime requirement: caller must never pass a handle after destroy; not enforceable natively (see below).

## UNSAFE RUST INVENTORY
14 `unsafe` blocks, all in `lib.rs`:

| Lines | Form | Invariant relied upon | Enforced in Rust? | Delegated to Kotlin? | Concurrent violation possible? | Consequence |
|---|---|---|---|---|---|---|
| 143, 481 | `Box::from_raw(ptr)` after registry `remove` | no other reference alive; ptr came from `into_raw` | registry membership only | yes | **yes** (another thread may be inside `&mut *`) | UAF / double-free avoided only for *second* destroy; use-during-destroy = UB |
| 166, 191, 225, 247, 272, 327, 502 | `&*(h as *const T)` | object alive for whole call; no `&mut` concurrently | **no** (check released lock before deref) | yes | **yes** | stale read, UAF, wrong-object read (after reuse) |
| 209, 359, 411, 450 | `&mut *(h as *mut T)` | unique reference | **no** | yes | **yes** — two callers get two `&mut T` | Rust aliasing UB; ratchet/OTK-store corruption (integrity), key reuse (confidentiality) |
| 387 | `Box::from_raw` on set_long_array_region failure | fresh, unregistered | yes | – | no | none (correct) |

Also `handle as *mut Identity` casts of arbitrary `jlong`: a forged value not in the registry is rejected (membership), but a forged value that *is* in the registry (guessable after leak/reuse) is dereferenced.

## TEMP CURRENT-SOURCE BUILD
Source SHA `a79166ab…`; rustc 1.97.1 (8bab26f4f); cargo 1.97.1; cargo-ndk 4.1.2; NDK 26.2.11394342 (r26c); `cargo ndk -t arm64-v8a -t x86_64 build --release --locked --offline`; target dir `/tmp/anox_crypto_jni_ndk_target`; output `/tmp/anox_crypto_jni_ndk_out`. Both ABIs compiled successfully. Not copied into tracked `jniLibs`.

## TEMP BINARY HASHES
- arm64-v8a: `05f3f40cd4122ddd4286c513470f8bb6cdf54ca69b4c1879e53cb6a8ba22d7a2` (1,206,312 B)
- x86_64: `c002cc420813f3b8473be7aa82eb0af334bd73e6847cd1c893ce500845dfe798` (1,201,736 B)
- Host reproduction binary: `/tmp/anox_crypto_jni_repro/target/release/anox_crypto_jni_repro` (host aarch64-apple-darwin, links `anox_crypto` rlib by path + vodozemac 0.10.0 from the same `Cargo.lock`).

## HOST RUST TESTS
`cargo test --locked --offline` (target `/tmp/anox_crypto_jni_host`): **17 passed, 0 failed, 0 ignored**. JNI module not compiled (cfg gate) — zero JNI evidence from this run.

## JNI RUNTIME TESTS
`NOT_RUN — NO APPROVED RUNTIME ENVIRONMENT`. An AVD (`anox_api34_arm64`) exists but is not running, no device attached, and Gradle would package the **stale committed** `.so` for instrumented tests; substituting the temp binary would mutate tracked files. Not performed.

---

## ROOT-002
**CONFIRMED** — HIGH.
`CryptoBridge.kt:38-44`: `instance ?: synchronized(this) { instance ?: CryptoBridge(...).also { it.initialize() } }` — `instance` is **never assigned**. Every `getInstance()` call constructs a new bridge, re-runs `initialize()` (native init + Keystore alias check), and owns a distinct `cryptoLock = ReentrantLock()` (L580). The "global" lock is per-instance; two callers holding different bridges serialize nothing. `@Volatile`/double-checked pattern is decorative.

## ROOT-003
**CONFIRMED and EXPANDED** — HIGH.
Confirmed: handle = raw heap address (`Box::into_raw(...) as jlong`, L131-133), registry is `HashSet<usize>` of addresses, pattern is check-under-lock → release → deref (`is_identity_active` L44-49 then `&mut *` L209), so TOCTOU is real; `&mut T` constructed per call with no uniqueness enforcement.
Expanded: (a) `Identity` and `Session` are auto `Send + Sync` (no `Rc`/`RefCell`/`unsafe impl` in vodozemac) — so a `Mutex<T>`-owning registry is directly implementable; (b) host allocator immediately reused a freed `Identity` address in **7/100** trials (same size class, 408 B) — on Android scudo same-size-class reuse is likely at least as frequent; cross-type reuse was 0/100 on host because `Identity`(408 B) and `Session`(3752 B) are different size classes — this is allocator luck, not a guarantee, and the separate registries only reject *type* confusion, not *instance* confusion.

## ROOT-004
**CONFIRMED and EXPANDED** — HIGH.
Identity: 0 OTK = 457 B; 10 = 2866 B; **20 = 5269–5287 B (> 4096)**; 50 = 12,537 B; 100 = 24,547 B (~240 B/OTK). With `DEFAULT_ONE_TIME_KEY_COUNT = 20`, `saveIdentity` inside `ensurePublicIdentityMaterial` (L44-47) fails with −11 deterministically at B-004 activation.
Expanded to Session: initial ≈ 1.0–1.2 KB; after 200 ping-pong ≈ 2.6–2.8 KB; with **≥ 40 skipped message keys ≈ 8.0 KB**; worst case (5 receiving chains × 40 skipped keys) **≈ 29.9 KB** bounded by vodozemac constants. `serializeSession` 4096 (L528) fails for any offline-receiver scenario. Also `encrypt` output `plaintext.size + 512` and `decrypt` `ciphertext.size + 256` are heuristics; Olm overhead is currently within them but this is not a contract.

## ROOT-005
**CONFIRMED and EXPANDED** — HIGH.
Mechanism proven at vodozemac source level: `Account::one_time_keys()` (`account/mod.rs:356`) builds a **fresh `HashMap`** from the internal ordered `BTreeMap` on **every call**; `Identity::get_one_time_key_by_index` calls it per index → `nth(i)` samples a different random permutation each call. Reproduction (20 OTK, 20 sweeps of index 0..19): duplicates in **20/20 sweeps**, worst **10/20 unique**, 140–146 omissions total, index 0 returned 12–13 distinct keys across sweeps. KeyId (`KeyId(u64)`, monotonic counter, base64 11 chars) is discarded at `identity.rs:61-67` and never crosses JNI. `mark_keys_as_published`, `unpublished_one_time_keys`, `get_one_time_key(KeyId)` have no JNI export. `OneTimeKeyGenerationResult { created, removed }` is discarded (`identity.rs:34`) — the `created` vector is exactly the upload set the wrapper needs, and `removed` is the only signal that published private keys were evicted.

## ROOT-013
**CONFIRMED and EXPANDED** — final severity **MEDIUM** (raised from LOW; justification below). New collisions found: (a) `cryptoGetOneTimeKey` returns **−3 `InvalidSession`** for "index out of range / no unpublished keys" (L253) — an OTK-store condition is reported as a session error; (b) `cryptoDeserialize*` return `0` for **all** failures, so `UnsupportedVersion` (−9), `InvalidInput` (bad key length), GCM auth failure, malformed JSON, and wrong-type pickle all collapse into Kotlin `DeserializationFailed` → `LocalStateStatus.CorruptedIdentityState`; a future envelope-version bump is indistinguishable from tampering and feeds the wipe/recovery decision path; (c) −3 is reused for JNI array-length/region failures; (d) −1 is reused for "handle inactive/stale" and "bad input". These are control-flow ambiguities, not merely diagnostic.

## ROOT-014
**CONFIRMED** — MEDIUM. Nothing in Kotlin production code destroys the identity handle returned by `resolveIdentityHandle()`; `getLocalStateStatus` deserializes a new Identity on every call (L624) and `LocalStateStatus.IdentityReady` leaks it if the caller does not destroy; registry sets grow monotonically. Coupling reasoning (§8) independently verified: today leaks mean freed addresses are rarely reused → the stale-handle→wrong-object path is mostly dormant; adding cleanup first would activate it.

## ROOT-010 / ROOT-011 ADJACENT FINDINGS
- **ROOT-010 (zeroization), crypto-specific expansion (LOW):** vodozemac zeroizes secret key types (`Curve25519SecretKey(Box<StaticSecret>)`, root/chain/message keys). anoX transient buffers are **not** zeroized: plaintext JSON pickle `Vec<u8>` in `CryptoSerializer::serialize` (contains all private keys) and `decrypt` output; K_STATE copies in `read_byte_array` (two copies: `Vec<i8>` + `Vec<u8>`); plaintext/ciphertext copies in `to_i8_vec`. `Identity::zeroize`/`Drop` are no-ops (acceptable — inner types zeroize). `AccountPickle`/`SessionPickle` are not `ZeroizeOnDrop` (their inner secret fields are). Kotlin: `stateKey` ByteArray and `out` buffers are never cleared (best-effort only possible).
- **ROOT-011 (domain separation), CONFIRMED, no expansion:** Identity and Session envelopes are byte-identical in header (`41 4E 4F 58 01`), same K_STATE, same AAD (`"ANOX"||0x01`), no object-type discriminator, no generation/counter. Cross-type substitution tested both directions → **parse failure (−6)**, not silent acceptance, because serde requires distinct fields. Rollback (old valid pickle) is accepted by the crypto layer — no freshness field exists. Prerequisite for anti-rollback lives in Android/Storage scope.

---

## HANDLE SAFETY VERDICT
**UNSOUND.** (1) handle is literally a heap address; (2) typed only by which `HashSet` it is in — no type tag in the value; (3) no generation; (4) old handle can equal a new allocation (7/100 host); (5) Identity/Session spaces collide numerically, guarded only by separate sets; (6) null (0) handled; (7) forged arbitrary `jlong` is rejected iff not in the set — forging a currently-live address is accepted; (8) double-destroy is a silent no-op (not detectable by caller); (9) stale use detectable only until the address is reallocated; (10) yes — a stale handle becomes "valid" again for a *different* object after allocator reuse.

## RUST ALIASING VERDICT
**VIOLATED BY DESIGN.** Two Java threads calling any two of {`cryptoGenerateOneTimeKeys`, `cryptoCreateInboundSession`} on one identity, or {`cryptoEncrypt`, `cryptoDecrypt`} on one session, each construct `&mut T` to the same object with no exclusion. Even `&T` + `&mut T` (e.g. `cryptoSerializeIdentity` during `cryptoGenerateOneTimeKeys`) is UB. Reachable via: multiple `CryptoBridge` instances (ROOT-002), direct `CryptoNative` calls, or one bridge from two threads holding different bridges.

## CONCURRENCY VERDICT
No native synchronization exists around object use; registries' `Mutex` protects only the set. Kotlin `ReentrantLock` is per-instance and thus ineffective globally. `panic = "abort"` means a poisoned-lock `unwrap()` (`lock().unwrap()`) would abort the process rather than unwind — memory-safe, but a DoS/secret-cleanup concern only if a panic occurs while holding the lock (no panic site found inside the critical sections).

## STALE HANDLE / ADDRESS REUSE
Feasible; currently masked by leaks; consequence = operating on / freeing a different live object (wrong-object encrypt/decrypt = confidentiality + integrity failure; wrong-object destroy = UAF for the legitimate holder). Minimum Rust-side invariant: **identity ≠ address; validity check and use must occur while holding an owning lock; destruction must be impossible while any use is in flight.**

## HANDLE LIFETIME
No RAII on Kotlin side, no `Cleaner`/`finalize`, no ownership transfer semantics documented. `getLocalStateStatus` allocates an Identity per call. Instrumented tests leak on assertion failure paths. Unbounded registry growth (local misuse class).

## CRYPTOBRIDGE SINGLETON
Broken as described (ROOT-002). Additional: `initialize()` swallows all exceptions and continues; `createAndPersistFirstIdentity` → `createIdentity` → `serializeIdentity` re-enter the same `ReentrantLock` (fine) but the identity is **not destroyed** if `serializeIdentity`/`writeFileAtomic` throw (leak on failure path, L652-654).

## CRYPTONATIVE BYPASS
`object CryptoNative` is **public** in package `com.anox.crypto`, compiled into the **same Gradle module** (`:android`, via `srcDir("../crypto/android/src/main/java")`). Any code in the app can call it directly; the instrumented tests already do (`CryptoNative.cryptoGetOneTimeKey(...)`). Kotlin `internal` would not help across the same module for app code; eventual remediation must (a) move native layer into its own Gradle module with `internal` visibility, or (b) make the native ABI itself safe so bypass is not a security boundary. **(b) is mandatory regardless; (a) is defense-in-depth.**

---

## SERIALIZATION CONTRACT
Caller-allocated fixed `byte[]`; native returns written length or −11. Fixed buffers: `serializeIdentity` 4096, `serializeSession` 4096, `encrypt` `n+512`, `decrypt` `n+256`, `createInboundSession` `n+256`, public keys 32 (correct). Length conversions: `data.len() as jint` (usize→i32, safe for these sizes); `get_array_length as usize` (jsize≥0, safe). No allocation cap on input side (`read_byte_array` allocates `len` twice for any input the JVM hands over — bounded by JVM array limits; local-caller class only).

## IDENTITY SERIALIZATION MEASUREMENT
0→457 B, 1→689 B, 5→1632 B, 10→2866 B, **20→5269/5287 B**, 50→12,537 B, 100→24,547 B, 500→122 KB, 1000→244 KB, **5000 (vodozemac private cap)→1.23 MB**. After `mark_keys_as_published` the unpublished public set is dropped from the pickle (20 OTK: 5287→2878 B). Because publish is not exported, the unpublished set (and pickle) only grows until the 5000 cap.

## SESSION SERIALIZATION MEASUREMENT
Outbound initial 1014–1031 B; inbound initial 1171–1177 B; 200 ping-pong rounds 2573–2847 B; ≥40 skipped keys ≈ 7.99–8.08 KB; **5 receiving chains × 40 skipped ≈ 29.85 KB (bounded max)**. vodozemac `MAX_MESSAGE_KEYS=40`, `MAX_RECEIVING_CHAINS=5`, `MAX_MESSAGE_GAP=2000` (decrypt after 2999 skips → `InvalidCiphertext`, expected).

## RECOMMENDED SERIALIZATION ABI
**Option D — native returns Java `byte[]` (`JByteArray`) allocated by Rust via `env.byte_array_from_slice`, `null` on error with error code delivered through a side channel (e.g. `IntArray(1)` out-param or a thrown typed exception).** Rationale: single pass, exact size, no magic constants, no retry loop, JNI allocation failure surfaces as a pending `OutOfMemoryError` which must be checked (`env.exception_check()`) and mapped. Add a native hard cap (e.g. 2 MiB for Identity, 64 KiB for Session — both ≥ measured maxima) to bound DoS. Reject A (magic growth), B (retry doubles work + still needs a cap), C (two calls = two pickles of secret state + TOCTOU on size), E (ByteBuffer adds lifetime complexity), F (over-engineering for V1).

---

## OTK ENUMERATION
Numeric positional index over a freshly materialized `HashMap` per call — **invalid by construction**; ordering is `RandomState`-seeded and differs between calls within the same process. The internal store (`unpublished_public_keys: BTreeMap<KeyId,_>`) *is* deterministically ordered by KeyId, so a correct API is trivially available (`iter()` over the BTreeMap order or return the map with KeyIds).

## OTK DUPLICATION / OMISSION
Measured 20 OTK / 20 sweeps: duplicates 20/20 sweeps; unique per sweep 10–14 (worst 10/20); omissions 140–146 total. A registration payload built by `ensurePublicIdentityMaterial(20)` would contain ~6–10 duplicate public keys and omit ~6–10 generated private keys from the server forever (they remain locally, never claimable). Index ≥ unpublished count → −3.

## OTK KEY-ID CONTRACT
Required public structure: `{ key_id: KeyId(u64, base64 11-char, monotonic per Account), public_key: Curve25519 32 B }`, ordered by `key_id`, unique by both fields. Server storage keyed by `(account_id, device_id, otk_id)`; ACK identity = list of `otk_id`; idempotent retry = same `(otk_id, public_key)` accepted, same `otk_id` with different key = security error (matches B-006 amended v1.3-f02 §3). Replay of an upload batch is harmless if keyed by `otk_id`. Duplicate upload of one public key under two ids must be rejected server-side (defense against the current enumeration bug class).

## OTK PUBLICATION / ACK
JNI currently exposes **none** of: unpublished retrieval with ids, get-by-KeyId, mark-as-published. Kotlin can only fetch positional public keys and can never mark anything published. The B-006 flow `generate → persist → upload (KeyId+key) → ACK → mark exactly accepted ids published → persist` is **not implementable** with the current ABI. Additionally vodozemac's `mark_keys_as_published()` marks **all** unpublished keys — "mark exactly accepted IDs" requires either (a) uploading exactly the full unpublished set per batch and treating partial ACK as retry-until-complete, or (b) a wrapper-side published-set overlay persisted in the anoX envelope. This design gap must be decided in CJ-D; it is a vodozemac API constraint, not a bug.

## OTK COUNT SEMANTICS
`stored_one_time_key_count()` = **all private OTKs** (published + unpublished; decremented on inbound-session consumption). `one_time_keys()` = **unpublished only**. Proven: after publish, `stored=20, unpublished=0, index0=None(−3)`; after +5 gen, `stored=25, unpublished=5`. `CryptoBridgeLocalE2eeIdentityStep` compares the stored count against `oneTimeKeyCount` then enumerates the *unpublished* set by index — different sets. Today they coincide only because publish is never called; the moment publication exists, the step will under-generate and then fail with `InvalidSession` (−3) on enumeration.

---

## ERROR MAPPING TABLE

| Rust error / native condition | Native code | Kotlin meaning | Information lost? |
|---|---|---|---|
| `InvalidInput` | −1 | `InvalidInput` | collides with inactive/stale/null handle (−1), `count<0`, `index<0`, key length ≠32, unreadable array, bad message_type |
| Handle null / not in registry | −1 | `InvalidInput` | **yes** — stale handle indistinguishable from bad argument |
| `InvalidCiphertext` (Olm decrypt fail, `from_parts` fail, MAX_GAP exceeded) | −2 | `InvalidCiphertext` | ok |
| `InvalidSession` | −3 | `InvalidSession` | never produced by wrapper for a session condition |
| JNI `get_array_length`/`set_*_region` failure | −3 | `InvalidSession` | **yes** |
| OTK index out of range / no unpublished keys | −3 | `InvalidSession` | **yes** — OTK-store state reported as session error |
| `SessionCreationFailed` | −4 | `SessionCreationFailed` | ok (inbound only; outbound returns 0) |
| `SerializationError(_)` | −5 | `SerializationFailed` | detail string dropped (fine) |
| `DeserializationError(_)` (GCM auth fail, bad magic, too short, JSON, wrong type) | −6 | `DeserializationFailed` | detail dropped; **never crosses JNI** (deserialize returns 0) |
| `StateCorrupted` | −7 | `StateCorrupted` | never produced |
| `CryptoFailure` (outbound session, encrypt) | −8 | `CryptoFailure` | outbound returns 0 instead |
| `UnsupportedVersion` | −9 | `UnsupportedVersion` | **never crosses JNI** (deserialize returns 0) |
| `KeyError(_)` (bad Curve25519 bytes) | −10 | `KeyGenerationFailed` | **mismapped meaning**; also collides with JNI `get_array_length(out)` failure in `write_byte_array` (−10) |
| `BufferTooSmall` / out too small | −11 | `BufferTooSmall` | ok |
| `set_byte_array_region` failure | −12 | `UnknownError(-12)` | unmapped |
| `cryptoDeserialize*`, `cryptoCreateOutboundSession` any error | `0L` | `DeserializationFailed` / `CryptoFailure` | **all discrimination lost** |

## SECURITY-RELEVANT ERROR COLLISIONS
1. Version-bump vs tamper vs wrong key → all `DeserializationFailed` → `CorruptedIdentityState` (destructive-recovery decision input). 2. Stale/destroyed handle vs bad argument (−1) → callers may retry with the same stale handle; masks UAF-precursor. 3. OTK exhaustion/publication state vs `InvalidSession` (−3) → wrong recovery domain. 4. `KeyError` → `KeyGenerationFailed` → caller may regenerate identity for what was a *peer* key problem. Purely diagnostic: −5/−6 string loss, −12 unmapped.

## STALE-HANDLE ERROR DESIGN
Native codes (conceptual): `HANDLE_NULL`, `HANDLE_UNKNOWN` (never issued), `HANDLE_STALE_GENERATION` (slot reused), `HANDLE_WRONG_TYPE` (type tag mismatch), `HANDLE_DESTROYED` (slot empty, generation matches). Exposing these to Kotlin is safe (no secret content) and useful: `DESTROYED`/`STALE` must be treated as a **programming-error class** (fail closed, log security event, never retry); `WRONG_TYPE`/`UNKNOWN` indicate corruption or misuse (abort operation). Do not collapse into `InvalidInput`.

---

## ZEROIZATION
Effective Rust-side: vodozemac secret types. Missing (best-effort achievable in Rust): pickle plaintext JSON `Vec<u8>` (serialize & decrypt paths), K_STATE copies in `read_byte_array`, message plaintext copies in `to_i8_vec`/`from_i8_slice`. Impossible guarantees: Kotlin `ByteArray` copies of K_STATE (`getOrCreateStateKey` result), `out` buffers, `copyOfRange` results — GC may move/copy; only best-effort `fill(0)` is possible and should be done. vodozemac's own encrypted pickle (`AccountPickle::encrypt`) exists but is unused; anoX's envelope is an acceptable alternative.

## STATE DOMAIN SEPARATION
Absent (same key, same AAD `"ANOX"||0x01`, no type byte). Practical effect today = parse failure (−6). Recommendation for CJ-C ABI revision: AAD = `magic || version || object_type || (future) generation`, so substitution fails at GCM tag rather than at JSON parse and cannot be confused with corruption once error codes are split.

## CRYPTO-LAYER ANTI-ROLLBACK
Format provides: nothing (random nonce only). Lacks: generation/monotonic counter, epoch, freshness binding. Prerequisites (Android/Storage scope): a trusted monotonic store (Keystore-bound counter or file with tamper evidence) whose value is included in AAD and checked on load. Crypto layer must expose an AAD/context input for this; it does not today.

## PANIC BOUNDARY
Reachable panics from JNI: `ACTIVE_*.lock().unwrap()` on poisoned mutex (only after a prior panic — none found in critical sections); `vec![0i8; len]` allocation failure (abort). `count as usize` for `cryptoGenerateOneTimeKeys(i32::MAX)` → vodozemac generates up to 2^31 keys (each ~100+ B + evictions beyond 5000) → minutes of CPU — **local-misuse DoS, no cap**. No `unwrap`/`expect`/indexing on untrusted data in wrapper (serializer bounds-checks before slicing). With `panic="abort"`: no FFI unwinding UB; abort = process death = availability loss + no zeroization of in-flight buffers (vodozemac Drop won't run). Not misclassified as unwinding.

## RESOURCE EXHAUSTION
Classified separately: (1) **local trusted-caller misuse**: unbounded `cryptoGenerateOneTimeKeys(count)`; unbounded registry growth via repeated create/deserialize without destroy; `getLocalStateStatus` allocating per call. (2) **Remote-triggerable (future B-008)**: skipped-key storage is bounded by vodozemac (40×5) — fine; pre-key message length unbounded before `PreKeyMessage::from_bytes` (allocates 2 copies) — bound at Kotlin/wire layer required. (3) **Unbounded persistent growth**: Identity pickle grows ~240 B/OTK up to 1.2 MB because publish is unreachable — resolved by CJ-D.

---

## TEST COVERAGE MATRIX

| Security property | Host Rust | JVM | Instrumented JNI | Current-source temporary proof | Missing evidence |
|---|---|---|---|---|---|
| handle creation | – | – | written, never run | compile+symbol only | runtime on canonical binary |
| invalid handle | – | – | `destroyedIdentityReusedFails` (never run) | source analysis | runtime |
| stale handle after reuse | – | – | – | host reuse 7/100 | Android allocator repro |
| destroy | – | – | written, never run | – | runtime |
| concurrent use | – | – | – | static UB proof | any test |
| concurrent destroy | – | – | – | static | any test |
| serialization too small | `-11` mapping only | `fromCode(-11)` | 2 tests, never run | disassembly −0xb | runtime |
| Identity serialize default OTK (20) | – | – | – | **5269–5287 B** | instrumented failing test |
| Session serialization growth | – | – | – | **8 KB / 29.9 KB** | instrumented |
| OTK enumeration | – | – | – | **20/20 sweeps dup** | instrumented |
| OTK KeyId | – | – | – | KeyId lost at `identity.rs:61` | any |
| publication | Rust test 3 calls `mark_keys_as_published` (no JNI) | – | – | count/unpublished divergence proven | JNI export absent |
| error mapping | 1 test | 4 tests | – | full table above | negative-path JNI tests |
| double destroy | – | – | 2 tests, never run | source: silent no-op | runtime |
| resource bounds | – | – | – | 5000-cap, 1.2 MB | any |

## FALSE ASSURANCE RISKS
1. Kotlin `ReentrantLock` appears global — it is per-instance and the singleton never caches. 2. `ACTIVE_*` sets appear to own handles — they are membership bookkeeping; ownership/lifetime/identity are absent. 3. Host `cargo test` 17/17 PASS is quoted as crypto verified — 0 JNI lines compiled. 4. Handle leaks appear to "prevent UAF" — they mask address reuse. 5. `getOneTimeKey(index)` appears deterministic — it is a fresh random permutation per call. 6. `oneTimeKeysCount` appears to describe the enumerated set — different sets (stored vs unpublished). 7. `CryptoError` sealed class appears typed — five distinct native conditions share −1, three share −3, deserialize collapses all to 0. 8. Instrumented tests exist and look thorough — never executed in CI and would run against the stale binary. 9. `"Output buffer too small"` string absence in a binary appears to prove old source — the string is absent in current-source builds too. 10. `Identity: Zeroize` impl appears to zeroize — it is a documented no-op (acceptable but misleading).

## FAILURE INTERLEAVINGS
- **A** — `getInstance(ctx)` ×2 → bridges B1,B2 with locks L1,L2 → T1: `B1.generateOneTimeKeys(h)` (`&mut Identity`) ∥ T2: `B2.saveIdentity(h)` (`&Identity` → `pickle()` iterating BTreeMaps being inserted into) → UB; realistic outcome: torn pickle persisted or crash. Also T1/T2 both `encrypt(s)` → duplicate ratchet index → **message-key reuse** (confidentiality).
- **B** — T_A: `is_identity_active(h)` true → lock released → T_B: `cryptoDestroyIdentity(h)` removes+frees → T_A: `&*(h)` → UAF read of freed `Account` (secret material may still be resident, or reallocated page).
- **C** — T_A destroys `h1` → allocator returns same address to `cryptoDeserializeIdentity` (h2 == h1 numerically) → registry re-inserts → T_C still holding `h1` calls `cryptoCreateInboundSession(h1, …)` → consumes an OTK of **identity 2** and returns a session bound to the wrong identity; or `cryptoDestroyIdentity(h1)` frees identity 2 under T_B's feet.
- **D** — `ensurePublicIdentityMaterial(20)`: FirstRun → create+persist (457 B OK) → `generateOneTimeKeys(20)` → `saveIdentity` → native computes 5.27 KB > 4096 → −11 → `LocalE2eeIdentityStepException` → registration cannot proceed; identity left with 20 unpersisted private OTKs in memory (leaked handle).
- **E** — Same step with buffer fixed: 20 × `getOneTimeKey(i)` → ~13 unique keys, ~7 duplicates uploaded, ~7 private keys never published; server rejects or stores duplicates; later peer claims a duplicate → two peers receive the same "one-time" key → inbound session for the second fails (OTK already consumed) or, if the server dedups, ~35 % of generated capacity is dead weight.

---

## AUDIT-LOCAL FINDINGS

### TOTAL
6 new candidates (plus 6 Consensus roots CONFIRMED/EXPANDED without new IDs per §57).

### CRITICAL
0

### HIGH
1 — `ANOX-CRYPTOJNI-CANDIDATE-001`

### MEDIUM
3 — `ANOX-CRYPTOJNI-CANDIDATE-002`, `-003`, `-004`

### LOW
1 — `ANOX-CRYPTOJNI-CANDIDATE-005`

### INFO
1 — `ANOX-CRYPTOJNI-CANDIDATE-006`

## FINDINGS TABLE

| Candidate | Severity | Confidence | Root cause | Exact evidence | Consensus relation | Current reachability | Activation | Blocks | Reassessment |
|---|---|---|---|---|---|---|---|---|---|
| **001** OTK count semantics mismatch: `stored_one_time_key_count` (all private) drives generation while enumeration reads the *unpublished* set; publication and `OneTimeKeyGenerationResult{created,removed}` discarded | HIGH | HIGH | Wrapper conflates two vodozemac sets; ignores generation result | `identity.rs:33-41,61-67`; `CryptoBridgeLocalE2eeIdentityStep.kt:31-52`; repro R3 (`stored=20, unpublished=0, idx0=None`) | NEW_ROOT_CAUSE related to ROOT-005 (distinct: count/set semantics vs ordering) | Not reachable (no product caller) | ACTIVATES_AT_B004 (step) / B006 publish | B004: YES | Instrumented test proving count/enumeration equality after publish |
| **002** Session pickle exceeds 4096 (8 KB with 40 skipped keys, 29.9 KB max) — 4096 fails in normal offline-receiver operation | MEDIUM (HIGH at B-008) | HIGH | Same fixed-buffer contract applied to a state with 7× larger bounded max | `CryptoBridge.kt:528`; repro R4 | EXPANDS ROOT-004 (Session dimension) | Not reachable | ACTIVATES_AT_B008/B009 | B004: NO (fold into CJ-C anyway) ; B008: YES | Measure against canonical binary |
| **003** Deserialize/outbound-session ABI returns `0` for every failure — `UnsupportedVersion`, wrong key, GCM tamper, malformed JSON, wrong type indistinguishable; feeds `CorruptedIdentityState` | MEDIUM | HIGH | Pointer-or-zero return shape has no error channel | `lib.rs:292-314,317-344,522-544`; repro R5 (−9 → 0) | EXPANDS ROOT-013 (security-relevant control-flow) ; secondary ROOT-006 | Not reachable | ACTIVATES_AT_B004 | B004: YES (within CJ-B) | Negative-path instrumented tests per code |
| **004** `cryptoGenerateOneTimeKeys(count)` unbounded (`count as usize`, up to 2^31) and identity pickle grows ~240 B/OTK to 1.23 MB at vodozemac cap; no wrapper cap, no `removed` handling | MEDIUM | HIGH | No native input bound; publish unreachable so unpublished set only grows | `lib.rs:200-214`; repro (5000→1.23 MB) | NEW (local-misuse DoS + persistent growth); touches ROOT-014 growth theme | Not reachable | ACTIVATES_AT_B004 (trusted caller) | B004: NO (justify: trusted caller passes 20) → B008/B009 | Cap test |
| **005** Transient secret buffers not zeroized in Rust (pickle JSON plaintext, K_STATE copies, plaintext copies) and Kotlin K_STATE/out buffers never cleared | LOW | HIGH | Wrapper relies on vodozemac zeroization only | `serialization.rs:36-40,50-54`; `lib.rs:88-116`; `CryptoBridge.kt:337,340` | EXPANDS ROOT-010 (crypto-specific) | Not reachable | ACTIVATES_AT_B004 | B004: NO | Code review after CJ-F |
| **006** `KeyError` (−10) mapped to Kotlin `KeyGenerationFailed`; −10 also returned for JNI array-length failure; −12 unmapped; OTK-not-found → −3 `InvalidSession`; string-presence provenance heuristic invalid | INFO | HIGH | Mapping table drift | `error.rs:52`, `CryptoError.kt:37`, `lib.rs:106,114,253` | EXPANDS ROOT-013 (diagnostic) | – | – | NO | Table review in CJ-B |

## NEW ROOT CAUSES
- CANDIDATE-001 (OTK set-semantics conflation + discarded generation result).
- CANDIDATE-004 (unbounded OTK generation input / persistent pickle growth).

## CONFIRMED CONSENSUS ROOTS
ROOT-002, ROOT-014, ROOT-011 (adjacent, no expansion).

## EXPANDED CONSENSUS ROOTS
ROOT-003 (Send+Sync feasibility; same-size-class reuse evidence), ROOT-004 (Session dimension, bounded maxima), ROOT-005 (vodozemac-level mechanism; `created`/`removed` discard; "mark exactly accepted" constraint), ROOT-013 (raised to MEDIUM: deserialize-collapse + −3/−1 collisions are control-flow relevant), ROOT-010 (crypto-specific transient buffers).

## REJECTED / NOT FINDINGS
- Cross-type pickle substitution as a confidentiality/integrity break — results in parse failure; recorded as ROOT-011 evidence only.
- FFI unwinding UB — `panic="abort"`; not a finding.
- JNI local-reference exhaustion — no loops creating local refs; `JNIEnv` never cached; per-call env used on the calling thread; not a finding.
- Integer wraparound in `jint→usize` casts — all guarded by `< 0` checks or non-negative `jsize`; not a finding (bound issue is CANDIDATE-004, not overflow).
- Ed25519/Curve25519 retrieval — 32-byte checks correct, −11 present in current source (8 sites), type separation by distinct functions; no finding.
- vodozemac 0.10.0 API misuse (cryptographic) — `create_outbound/inbound_session` with `SessionConfig::version_1()`, `PreKeyMessage::from_bytes`, `OlmMessage::from_parts`, pickle/from_pickle all used as intended. Assumptions **not** guaranteed by vodozemac and currently relied on: HashMap iteration order (none — and it is not), `stored_count == unpublished_count` (false once publish exists).

---

## PRE-B004 CRYPTO/JNI BLOCKERS
ROOT-002, ROOT-003, ROOT-004 (Identity), ROOT-005, ROOT-013, ROOT-014, **CANDIDATE-001**, **CANDIDATE-003** — all delivered as one ABI revision (CJ-A/B/C/D/E merged). Prerequisite: ROOT-001 canonical provenance so the retest is meaningful.

## B008/B009 CRYPTO/JNI BLOCKERS
CANDIDATE-002 (Session sizing — but the dynamic ABI from CJ-C already removes it; verify), CANDIDATE-004 (cap + `removed` handling + replenishment semantics), CANDIDATE-005 / ROOT-010 (zeroization), ROOT-011 domain tag + anti-rollback AAD hook (crypto side), session concurrency contract for B-008 message pipeline.

## FINAL-GATE ITEMS
Re-execution of every native retest against the provenance-verified canonical `.so`; instrumented-JNI suite in CI (ROOT-017); CANDIDATE-006 table hygiene.

---

## REQUIRED JNI ABI REVISION
**YES** — `JNI_ABI_REVISION`. Handle semantics, return shapes (pointer-or-zero), output-buffer contract, and OTK surface all change; a compatible patch is not possible.

## PROPOSED NEW ABI CONTRACT
Conceptual (no code):
- **Handles**: opaque `jlong` = `(slot_index: u32, generation: u32)`; type encoded by separate slot tables (Identity table, Session table) *and* a type nibble in the handle for early rejection. Never a memory address.
- **Registry**: per-type `Mutex<Slab<Slot { generation, object: Arc<Mutex<T>> }>>`. Lookup = lock table → verify generation → clone `Arc` → unlock table → lock object → operate → unlock. Destroy = lock table → verify generation → take `Arc`, bump generation → unlock table → drop `Arc` (object freed when last in-flight user finishes). Check+use are therefore within one object-lock scope; destroy cannot race a use into UAF.
- **Returns**: every function returns `jint` status (0 success, negative typed code including `HANDLE_*` family); handles and byte outputs via out-params or a native-allocated `byte[]` return with status in an `IntArray(1)`.
- **Serialization**: native-allocated `byte[]` (Option D), hard caps, AAD = `magic||version||object_type||context`.
- **OTK surface**: `otkGenerate(identity, count≤cap) → created [(KeyId, pk)] + removed [pk]`; `otkUnpublished(identity) → [(KeyId, pk)]` in KeyId order; `otkMarkPublished(identity, [KeyId])` (implemented per vodozemac constraint decided in CJ-D); `otkStoredCount`, `otkUnpublishedCount` as distinct calls.
- **Error taxonomy**: disjoint code ranges for handle errors, input errors, crypto errors, state-format errors, JNI/platform errors.
- **Versioning**: envelope version bump only if AAD layout changes; migration = read v1 with old AAD once, write v2 — deserialize must return `UNSUPPORTED_VERSION` distinctly.

## REMEDIATION GROUPS
- **CJ-A+B+C+D+E (merged, one ABI revision)**: handle identity/ownership/synchronization; error semantics; serialization ABI; OTK KeyId/publication/count; Kotlin singleton fix + `CryptoNative` visibility narrowing (module split) + handle lifetime cleanup **last** within the group.
- **CJ-F**: zeroization of transient buffers (Rust + Kotlin best-effort), can follow.
- **CJ-G** (new): input caps (`count`, message length) and `removed`-key handling with B-006 replenishment semantics.

## ITEMS THAT MUST BE FIXED TOGETHER
- ROOT-003 + ROOT-014: cleanup activates reuse unless identity/ownership is fixed first (independently verified: 7/100 immediate host reuse).
- ROOT-003 + ROOT-013: stale/destroyed handle codes only make sense once generation identity exists; without them stale use stays `InvalidInput`.
- ROOT-004 + ROOT-005 + CANDIDATE-001: the OTK export surface and the serialize shape change the same Kotlin call sites and the same identity-step; fixing one and leaving the other yields a payload that either fails to persist or uploads duplicates.
- ROOT-002 + ROOT-003: singleton alone does not make aliasing sound (direct `CryptoNative` callers, tests); native lock alone leaves repeated `initialize()`.
- CANDIDATE-003 + ROOT-013 + ROOT-006: deserialize error channel must land together with the `LocalStateStatus` consumer so version≠corruption.

## ITEMS THAT MUST NOT BE FIXED ALONE
- Handle-leak cleanup alone → **worsens risk** (activates wrong-object path).
- Kotlin singleton alone → false closure (ABI remains unsound under bypass/tests).
- Larger buffer constant alone → false closure (Session 29.9 KB; Identity 1.2 MB cap) and hides the missing publication export.
- OTK publication export without stable KeyIds / `created` vector → duplicates and omissions persist; ACK cannot name keys.
- Deserialize error codes alone without `LocalStateStatus` consumer change → codes computed then collapsed again in Kotlin.

## REQUIRED REMEDIATION ORDER
1. ROOT-001 provenance + native CI (Build/Supply) — precondition for accepting any native evidence.
2. CJ-A: slot+generation registry with owning `Arc<Mutex<T>>` and in-scope check+use.
3. CJ-B: error taxonomy including handle family and deserialize status channel.
4. CJ-C: native-allocated output + caps + AAD type tag.
5. CJ-D: OTK KeyId surface, counts, publish, `created/removed`.
6. CJ-E: Kotlin singleton assignment, module/visibility narrowing, `LocalStateStatus` consumer rewrite, **then** handle lifetime cleanup (ROOT-014) last.
7. CJ-F/G afterwards; independent retest of all on canonical binary.

---

## SEC-A
CJ-F (zeroization of transients), CANDIDATE-006 mapping hygiene, CJ-G caps.

## SEC-B
Merged CJ-A+B+C+D+E ABI revision (component-internal to `crypto/rust` + `crypto/android` + one Kotlin consumer; changes the JNI ABI but not system trust boundaries).

## SEC-C REQUIRED
**NO**. Unsafe Rust redesign stays inside the crypto component; no trust boundary, server contract, or invariant changes.

## ARCHITECTURE VERDICT
`COMPONENT_INTERNAL_REDESIGN_ONLY` — the Kotlin↔JNI contract must be rewritten, but the component boundary, vodozemac choice, envelope approach (AES-GCM over pickle under Keystore-wrapped K_STATE) and the B-006 flow all stand. This matches the Consensus verdict; no escalation to `CRYPTO_JNI_BOUNDARY_REDESIGN` is warranted because the boundary (Kotlin app ↔ native crypto) is correctly placed — only its ABI is unsound.

---

## AUTH/DPOP HANDOFF
None of the above. Note for that audit: Device Auth (P-256 Keystore) and `RegistrationSessionKey` are independent of `K_STATE`; verify key-separation claims in `RegistrationSessionKey.kt:16`.

## ANDROID/STORAGE HANDOFF
Anti-rollback trusted counter and its inclusion in the crypto AAD hook; `getLocalStateStatus` wipe/recovery decision consuming collapsed errors (consumer side of CANDIDATE-003); `writeFileAtomic` durability (ROOT-007) for `anox_identity.enc`; best-effort clearing of Kotlin `ByteArray` secrets; Keystore master-key lifecycle in `wipeLocalCrypto`.

## ATTACKCHAIN HANDOFF
Sequence E (duplicate OTK upload → server-side dedup/claim behaviour) and the "server holds OTKs whose private half was evicted (`removed`)" path once B-006 publication exists; message-key reuse via Sequence A under a multi-threaded B-008 pipeline.

---

## PRODUCT DEVELOPMENT
`BLOCKED_PENDING_FINAL_AUDIT`

## B004
`NOT_STARTED`

## B005
`NOT_STARTED`

## SECURITY HARDENING PHASE
`IN_PROGRESS`

## FINAL OPERATIONAL ACCEPTANCE
`PENDING / NOT_EXECUTED`

## HUMAN FINAL PRODUCT GATE
`NOT_EXECUTED`

---

## NEXT ACTION
`PRESERVE AUDIT-SECURITY-CRYPTO-JNI-001 → RUN AUDIT-SECURITY-AUTH-DPOP-001 → RUN AUDIT-SECURITY-ANDROID-STORAGE-001 → RUN AUDIT-SECURITY-ATTACKCHAIN-001 → CONSOLIDATE SPECIALIST FINDINGS → LARGE DEPENDENCY-SAFE REMEDIATION SESSIONS → INDEPENDENT RETESTS → ONLY THEN B004`

Temporary artifacts left in `/tmp/anox_crypto_jni_*` only (host target, repro crate, NDK target/output with the hashes above). No tracked file was created or modified; no branch, commit, push, PR, or merge.

STOP.
