# PROMPT-007 — B-002 Device Authentication Foundation

**Date:** 2026-08-21
**Branch:** `feature/b002-device-auth-foundation`
**Baseline:** `main @ 33440823f3d2a785202ca1828e4bf9c71b175008`
**Authority:** current B-025 + B-026
**Type:** implementation (client foundation only)

---

## 1. Scope

Implements the minimum production-oriented client foundation for **B-002 Device
Authentication**. This is a foundation task, not a full B-002 delivery.

**In scope:** Android Keystore Device Auth key handling, P-256/ES256 signing, hardware
security classification and production-eligibility policy, public-key representation,
RFC9449 DPoP proof creation, a testable DPoP verification boundary, the frozen
nonce/`jti`/`iat`/`ath` semantics, fail-closed key-loss handling, and tests.

**Out of scope and NOT implemented:** B-003 account/license registration, B-004 production
backend, B-005 DB/RLS, token issuance/persistence/revocation, shared production replay
cache, device registry, entitlement enforcement, messaging, `/sync`, contacts, SAS, push,
attachments, SQLCipher DB, multi-device, recovery, refresh tokens, remote attestation,
certificate pinning.

## 2. Files added / changed

### Added — `android/src/main/java/com/anox/messenger/security/deviceauth/`

| File | Responsibility |
|---|---|
| `HardwareSecurityLevel.kt` | StrongBox / TEE / Software / Unknown + production-eligibility policy |
| `DeviceAuthKeyStatus.kt` | Key lifecycle states and terminal-state exceptions |
| `DeviceAuthKeyStateResolver.kt` | Pure, Android-free lifecycle decision logic |
| `DeviceAuthKeyManager.kt` | Key lifecycle contract |
| `AndroidKeystoreDeviceAuthKeyManager.kt` | Android Keystore implementation |
| `DeviceAuthBindingStore.kt` | Bound-marker abstraction + in-memory implementation |
| `DeviceAuthSigner.kt` | Public JWK + opaque JOSE signing capability |
| `DeviceAuthClock.kt` | Injectable clock |
| `JtiGenerator.kt` | CSPRNG `jti` generation (128-bit minimum) |
| `DpopHtu.kt` | RFC9449 `htu` normalisation |
| `DpopProofFactory.kt` | RFC9449 DPoP proof creation |
| `DpopProofVerifier.kt` | Verification boundary |
| `DpopVerificationResult.kt` | Result + safe rejection reasons |
| `DpopReplayCache.kt` | Replay interface + in-memory 5-minute implementation |
| `DeviceAuthAccessTokenContract.kt` | Frozen token contract + `ath` computation |

### Added — tests

- `android/src/test/java/.../DeviceAuthTestSupport.kt`
- `android/src/test/java/.../DpopProofVerifierTest.kt`
- `android/src/test/java/.../DeviceAuthKeyLifecycleTest.kt`
- `android/src/test/java/.../DeviceAuthAccessTokenContractTest.kt`
- `android/src/test/java/.../DpopHtuTest.kt`
- `android/src/test/java/.../InMemoryDpopReplayCacheTest.kt`
- `android/src/androidTest/java/.../AndroidKeystoreDeviceAuthKeyManagerTest.kt`

### Changed

- `android/build.gradle.kts` — pinned `com.nimbusds:nimbus-jose-jwt:10.9.1`; explicit
  `test` / `androidTest` source dirs.
- `.github/workflows/ci.yml` — added `:android:testDebugUnitTest` plus report upload.

### Not changed

`crypto/rust/**`, `CryptoNative.kt`, `CryptoBridge.kt`, `AndroidManifest.xml`, `MainActivity.kt`,
Compose theme, native `.so`, AGP `8.13.2`, KGP `2.4.10`, Compose `2.4.10`, Gradle `9.3.1`,
NDK `26.2.11394342`, vodozemac `0.10.0`, `K_STATE`, `[ANOX][0x01]` envelope.

## 3. Device Auth key lifecycle

States resolved by `DeviceAuthKeyStateResolver`:

| Key present | Previously bound | State | Creation allowed |
|---|---|---|---|
| no | no | `AbsentNotBound` | yes (first run) |
| yes | any | `Present(level)` | no-op, key reused |
| no | yes | `TerminalKeyLoss` | **refused** |

`createKeyIfAbsent()` is idempotent and throws `DeviceAuthTerminalStateException` on
`TerminalKeyLoss`. A permanently invalidated or missing key entry is detected via
`KeyPermanentlyInvalidatedException` / `UnrecoverableKeyException` and reported as absent, at
which point the bound marker decides first-run vs terminal.

Terminal loss consequences, per B-002:
- old-account network access is permanently lost;
- no replacement key is generated;
- no re-binding of a new key to the old account;
- local E2EE identity and local protected state are **not** touched;
- only an explicit destructive local reset (`clearBinding()`) permits a brand new key, which
  means a new account from scratch, not recovery.

Key deletion exists only as `deleteKeyDestructively()` and is never invoked from a recovery,
retry or error-handling path.

## 4. Hardware security policy

| Level | Production eligible |
|---|---|
| `STRONGBOX` | yes (preferred) |
| `TRUSTED_EXECUTION_ENVIRONMENT` | yes (B-002 permits TEE fallback) |
| `SOFTWARE` | **no** |
| `UNKNOWN` | **no** (fail closed) |

StrongBox is requested on API 28+ and falls back to TEE on failure. Detection:

- **API 31+** — exact `KeyInfo.getSecurityLevel()`.
- **API 26–30** — only `isInsideSecureHardware()` exists, so a hardware-backed key is
  conservatively reported as TEE even when it was actually generated in StrongBox.
  **StrongBox is never claimed without platform proof.** Both levels are production eligible,
  so this conservatism costs no functionality.

## 5. Public key representation

Only a **public-only** `ECKey` JWK (`kty=EC`, `crv=P-256`, `x`, `y`) is exposed, plus its
RFC7638 SHA-256 thumbprint (`jkt`) used for token/key binding. `DeviceAuthSigner` has no
method returning private key bytes; the Android Keystore `PrivateKey` handle also returns
`null` from `getEncoded()`.

## 6. DPoP implementation

**Library:** `com.nimbusds:nimbus-jose-jwt:10.9.1`, pinned.

Justification: no cryptographic primitive is hand-rolled, and the ES256 DER-to-JOSE
signature transcoding required by RFC7518 is a standards detail that must not be
re-implemented. Nimbus is the reference Java/Android JOSE library; it is Apache-2.0, compiled
to Java 7 bytecode, ships shaded JSON, and treats BouncyCastle/Tink as optional, so it is
safe at `minSdk 26`. Critically, `ECDSASigner(PrivateKey, Curve)` is explicitly intended for
EC keys in stores that do not expose private key parameters, which is exactly the Android
Keystore case. Version `10.9.1` was published 2026-05-31, well beyond a 7-day vetting window.
No AGP/Kotlin/Compose/Gradle/NDK change was needed to accommodate it.

**Proof header:** `typ=dpop+jwt`, `alg=ES256`, `jwk` = public Device Auth JWK.
**Proof claims:** `jti`, `htm`, `htu`, `iat`, plus `ath` when token-bound and `nonce` when
supplied.

`htu` is normalised identically on both sides by stripping query and fragment and lowercasing
scheme and authority.

## 7. Frozen parameters implemented

| Parameter | Value | Location |
|---|---|---|
| `jti` entropy | 128 bits (CSPRNG) | `SecureRandomJtiGenerator` |
| `iat` acceptance | ±120 s | `DpopProofVerifier` |
| Replay window | 5 minutes | `InMemoryDpopReplayCache` |
| Signature alg | ES256 only | `DpopProofVerifier` |
| Token entropy | 256 bits opaque | `DeviceAuthAccessTokenContract` |
| Server storage | SHA-256 only | `serverStoredTokenHash` |
| Token TTL | 15 minutes | `TOKEN_TTL_SECONDS` |
| Refresh token | none | `REFRESH_TOKEN_SUPPORTED = false` |

## 8. Verification boundary and replay model

`DpopProofVerifier` validates, in order: parse, `typ`, `alg`, `jwk` presence/curve/public-only,
signature, `jkt` key binding, `htm`, `htu`, `iat` window, `jti` minimum entropy, `ath`,
`nonce`, then replay. Replay is checked **last** so a proof failing any earlier check does not
consume a `jti` slot.

`ath` and `nonce` are compared with `MessageDigest.isEqual`.

**Explicit limitation:** `InMemoryDpopReplayCache` is single-process and in-memory. It proves
the 5-minute semantics and is not, and is not presented as, the production shared cache that
B-002 requires. A production backend must supply a distributed `DpopReplayCache`.

Likewise `DpopProofVerifier` is a protocol/policy boundary, not the B-004 backend: it does not
issue tokens, own sessions, consult a device registry or enforce entitlement. The interface
boundary for the future restricted expired-entitlement renewal flow is preserved by keeping
token/session/entitlement decisions entirely outside this subsystem.

## 9. Token binding behaviour

`ath = base64url(SHA-256(ASCII(access_token)))` per RFC9449. When a caller presents an access
token, a proof lacking `ath` is rejected (`MISSING_ATH`) and a mismatching `ath` is rejected
(`ATH_MISMATCH`). The plaintext token is never a legitimate stored server value;
`serverStoredTokenHash` returns the digest. `DeviceAuthAccessTokenGenerator` is CSPRNG-backed
and explicitly foundation/test scoped.

## 10. Tests

### Positive
P-256/ES256 key works; public key verifies signatures; private material never exposed
(`isPrivate == false`, no `d`, `toECPrivateKey() == null`, Keystore `getEncoded() == null`);
StrongBox/TEE accepted; valid proof accepted; `ath` binding correct; nonce path works; fresh
unique `jti`; `iat` accepted inside the window; `htu` query/fragment ignored; key binding
matches; idempotent key creation.

### Negative
wrong `htm`; wrong `htu`; different host; stale `iat`; future `iat`; missing `iat`; duplicate
`jti`; exact proof replay; short `jti`; wrong key binding; corrupted signature; spliced/tampered
payload; malformed proof; wrong `typ`; missing `typ`; non-ES256 (HS256 algorithm-confusion
attempt); missing `jwk`; private key in `jwk` header; missing `ath`; wrong `ath`; missing
`nonce`; wrong `nonce`; software-only rejected for production; `UNKNOWN` hardware fails closed;
terminal key loss does not silently regenerate; failed verification does not consume `jti`.

### Two correctness issues found and fixed while writing tests
1. Nimbus `JWSHeader.Builder.jwk()` throws `IllegalArgumentException("The JWK must be public")`
   and `JWSHeader.parse` routes `jwk` through `parsePublicJWK`. A private-JWK proof therefore
   cannot be built normally and is rejected at parse time as `MALFORMED`. The test now builds
   it by raw header surgery and asserts it is never accepted; the verifier's explicit
   `PRIVATE_KEY_IN_JWK` check is retained as defence in depth.
2. Tampering the final base64url character of a 64-byte ECDSA signature is unreliable, because
   that character carries 4 bits that decoding discards. Signature corruption now flips a byte
   inside `r`.

## 11. Known limitations / remaining B-002 work

- No production backend: token issuance, storage, session binding, device revocation and the
  shared replay cache are B-004.
- No account registration or device binding call: B-003. `DeviceAuthBindingStore` is currently
  in-memory only; a persistent implementation is required before real binding.
- Restricted expired-entitlement renewal flow is not implemented; only the boundary is preserved.
- No remote attestation (not required in V1).
- `isProductionEligible()` is computed but not yet enforced at a registration call site,
  because no registration call site exists yet.
- StrongBox cannot be distinguished from TEE below API 31.

## 12. Verification status

| Item | Status |
|---|---|
| JVM unit tests (Device Auth) | see CI on PR #4 |
| Rust crypto tests | unchanged, run in CI |
| Android debug build | run in CI |
| Android release compile smoke | run in CI |
| Debug/release APK content gate | run in CI |
| Android instrumentation (real Keystore) | **NOT RUN** in CI — no emulator |
| Physical hardware-backed StrongBox behaviour | **UNVERIFIED** |
| GrapheneOS physical-device Device Auth | **UNVERIFIED** |

Passing these tests is not proof of production cryptographic security. Independent security
review remains required per Security Invariants 33 and 34.

## 13. Security invariants

No file under `docs/authority/` was modified. No frozen invariant was changed or required
changing. Relevant invariants upheld: 7 (independence), 8 (P-256/ES256 + DPoP, no Ed25519),
10 (no custom primitives), 24 (key separation), 26 (no secrets in logs), 29 (no secrets in APK),
33/34 (no production security claim without independent review).

Rejection reasons are enumerated values carrying no secret material, so they are safe to log.
No private key, access token or `ath` preimage is logged anywhere in the subsystem.
