# B-025 Mandatory Amendments V1.4 — Pre-B004 Security Contract Freeze

**Status:** FROZEN / CURRENT
**Date:** 2026-09-14
**Authority:** Human-authorized `REMEDIATION_SESSION_S0` (`SECURITY_REMEDIATION_START_AUTHORIZATION = GRANTED_BY_HUMAN_OWNER`, `HUMAN-PRE-REMEDIATION-DECISIONS-001`), executed as task `ANOX-TASK-REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001` on base `0f932520393feee6d479cc099f179f5766323125`.
**Sources:** `MASTER-SPECIALIST-CONSOLIDATION-001` (S0 unit set, SC-1…SC-14, CC-1…CC-14, SERVER_BREAKER_S1…S18), `SECURITY-REMEDIATION-COVERAGE-GATE-001` (file ownership, architecture-prerequisite matrix), `HUMAN-PRE-REMEDIATION-DECISIONS-001` (H1/H2/H3/R1).
**Supersedes:** This document is an authoritative successor amendment to specific provisions of `B025_MANDATORY_AMENDMENTS_V1_2.md` (B-004, B-005, B-006, B-007), `B025_MANDATORY_AMENDMENTS_V1_1.md` (B-003, B-013), and the B-025 snapshot items B-002 and B-009, **only for the clauses enumerated in §18**. V1.1, V1.2, V1.3 and all unamended B-025 Track B items remain in force. Where this document and any lower-precedence surface conflict on an enumerated clause, this document wins.

This is a **contract-only** freeze (`REMEDIATION_SESSION_S0`, role `ARCHITECTURE_FREEZE`). It creates **no** product code, **no** backend code, **no** SQL/schema migration, **no** CI change and **no** native artifact. `B004 = NOT_STARTED`, `B005 = NOT_STARTED`, `BACKEND = NOT_IMPLEMENTED`. Product development remains `BLOCKED_PENDING_FINAL_AUDIT`.

Machine-readable companion: `docs/authority/contracts/S0_CONTRACT_FREEZE_MANIFEST.json` (clause registry consumed by `tools/audit/validate_s0_contract_freeze.py`). The manifest never restates normative text; it only indexes the clause IDs below.

---

## 0. Scope, clause identifiers and lifecycle rule

- **[S0-000-01]** Every normative clause in this document carries a stable identifier of the form `[S0-<unit>-<nn>]`, where `<unit>` is the owning MSC unit (`018`, `020`, `022`, `025`, `026`, `027`, `028`, `032`, `033`, `034`, `040`, `042`) or `000` (framework), `017` (preserved decisions). Identifiers are assigned once and never reused for a different requirement. Retiring a clause requires an explicit superseded-by record in a later amendment, never ID reuse.
- **[S0-000-02]** This freeze owns the architecture/contract portions of the 11 **primary** S0 contract units `MSC-UNIT-018`, `020`, `025`, `026`, `027`, `028`, `032`, `033`, `034`, `040`, `042`. It additionally freezes **one supporting contract entry**, `MSC-UNIT-022` (§4, HTU/HTM canonicalization), because `MSC-UNIT-026` carries `SERVER_BREAKER_S12` and cannot be frozen without it (`MASTER-SPECIALIST-CONSOLIDATION-001` MSC-026 breaker set; `SECURITY-REMEDIATION-COVERAGE-GATE-001` architecture-prerequisite `022←026 htu`). A supporting contract entry is **not** an S0 unit: `MSC-UNIT-022` is not added to the S0 stage proposals, is not advanced in the closure state machine, is not claimed closed, and keeps its frozen primary remediation ownership (code in session S4). This freeze also consumes the already-completed Human governance decisions of `MSC-UNIT-039` (not reopened). No MSC unit outside these 11 primary units, the one supporting entry and the consumed decision record is touched.
- **[S0-000-03]** Contract lifecycle mapping (closure state machine of `MASTER-SPECIALIST-CONSOLIDATION-001`): `IMPLEMENTED = FROZEN_IN_CANONICAL_AUTHORITY` (this document), `AUTOMATED_TESTED = CONTRACT_VALIDATOR_PASS` (`validate_s0_contract_freeze.py`). No S0 unit advances to `INDEPENDENTLY_RETESTED`, `EVIDENCE_PRESERVED` or `CLOSED` by this freeze. `CLOSED_BY_S0 = 0`; `OPEN MSC UNITS = 42`.
- **[S0-000-04]** Any later implementation (B004 backend, B005 schema, S3/S4 client sessions, B006/B008/B009/B013) MUST conform to the clauses below. Per Security Invariant 35, no security-critical implementation of these areas may begin while this freeze is absent or internally contradictory.
- **[S0-000-05]** Terminology: **JWK** = the RFC 7517 public P-256 key `{"kty":"EC","crv":"P-256","x":..,"y":..}`; **JKT** = the RFC 7638 JWK thumbprint (SHA-256 over the canonical members `crv`, `kty`, `x`, `y`), base64url without padding; **public_key** = the same key as X.509 SubjectPublicKeyInfo DER bytes. JKT is a deterministic function of `public_key`; both identify the same Device Auth key.

---

## 1. B-005 — Schema authority single source of truth (MSC-UNIT-040; remediates ANOX-SECURITY-ARCH-004) — amended v1.12-f04

<!-- SCHEMA-AUTHORITY-HOME: DB-SCHEMA-V1-FROZEN -->

- **[S0-040-01]** `DB-SCHEMA-V1-FROZEN` is the **single canonical frozen schema contract** of anoX V1. Its authority home is exactly one chain: `B025_MANDATORY_AMENDMENTS_V1_2.md §B-005` (base contract) **as amended by this §1–§2 and §11** (security-relevant constraints). On any conflict inside that chain, this document wins. No other document may define, restate or vary a B-005 column, constraint, index or lifecycle rule with normative force.
- **[S0-040-02]** The following documents are **informative / superseded** for schema matters and MUST explicitly defer to `DB-SCHEMA-V1-FROZEN`: `docs/current/DATABASE_ARCHITECTURE.md`, `docs/current/BACKEND_ARCHITECTURE.md`, `docs/authority/B025/TRACK_B/B005_DATABASE_SCHEMA_RLS.md` (historical snapshot), and any RAW/history material. A statement that the schema is "not frozen" in any of these surfaces is superseded and has no normative effect.
- **[S0-040-03]** The security-relevant B-005 elements whose canonical home is this document are: `auth.device_auth_keys.public_key` / `jkt` uniqueness and lifecycle (§2), JKT / public-key identity derivation (§2), immutable `device_id` / `account_id` binding (§2), `crypto.identity_public_keys` immutability (§2), the one-active-device-per-account invariant (§2), and the publication epoch (§11). Every other B-005 clause keeps its V1.2 home.
- **[S0-040-04]** The V1.2 column `device_auth_keys.public_key_pem` is **renamed** to `device_auth_keys.public_key` (canonical binary SPKI DER, see [S0-000-05]) and a derived, stored column `device_auth_keys.jkt` is added. This is a contract rename; no SQL is created by this freeze.
- **[S0-040-05]** Any future B-005 schema amendment must be made in a successor to this document and recorded in `B_FREEZE_REGISTRY.md`; creating a second equal-precedence schema authority is prohibited (`CANONICAL CONTRACT AMBIGUITIES = 0`).
- **[S0-040-06]** MSC-UNIT-040 remains OPEN pending independent Architecture retest and evidence preservation; this freeze provides `ARCHITECTURE_AUTHORITY_UPDATE` only.

---

## 2. Device / JKT / account binding invariants (MSC-UNIT-028; SERVER_BREAKER_S1, S2, S3, S16) — B-004 / B-005

### 2.1 Global uniqueness and known-key rejection (S1)

- **[S0-028-01]** `auth.device_auth_keys.public_key` is **globally unique** across the whole table — across all accounts, all devices and **all lifecycle states including `REVOKED`**. Equivalent enforcement: `UNIQUE(device_auth_keys.public_key)` **and** `UNIQUE(device_auth_keys.jkt)`. Both constraints are mandatory contract elements of `DB-SCHEMA-V1-FROZEN`.
- **[S0-028-02]** `device_auth_keys` rows are **never deleted**. Lifecycle states of a row: `ACTIVE` → `REVOKED` (terminal). A revoked row is retained indefinitely (audit/operational retention per B-014) so that its key remains **known**.
- **[S0-028-03]** **Known-key rejection:** a registration step (`submit-device-auth`, `commit`) or any token issuance presenting a JKT that already exists in `device_auth_keys` — whether the row is `ACTIVE` or `REVOKED` — is rejected with error code `device_auth_key_reuse_rejected`, rejection class `PERMANENT` (§3.7). The rejection is returned only after the registration proof-of-possession (§6) verified, so only the legitimate key holder learns that the key is known. The server never re-binds, re-activates or "adopts" a known key.
- **[S0-028-04]** Pre-commit uniqueness: at `submit-device-auth` the server also checks the JKT against every non-expired `registration_sessions` row. Two concurrent registration sessions presenting the same JKT are resolved at commit by the one-wins rule of [S0-028-09]; the loser receives `invalid_registration_state` / `PERMANENT`.

### 2.2 Immutable JKT → device_id → account binding (S2)

- **[S0-028-05]** `AuthenticatedDeviceContext.device_id`, `.account_id` and `.device_auth_key_id` are derived **exclusively** from the validated Device Auth key: the verifier computes the JKT of the JWK embedded in the verified DPoP proof (or registration PoP), looks up `device_auth_keys` by `jkt` with state `ACTIVE`, and takes `device_id` / `account_id` from that row. Application-supplied JSON, headers, path or query parameters MUST NOT override or supply these values (Security Invariant 19; V1.2 §B-004.2).
- **[S0-028-06]** The triple `(jkt, device_id, account_id)` in `device_auth_keys` is **immutable** after the registration commit transaction. No `UPDATE` may re-point a key to another device or account; no `UPDATE` may change a device's key. A new Device Auth key is a new device, and in V1 (one device per account, Security Invariant 2) therefore a new account.
- **[S0-028-07]** `device_id` is server-generated UUIDv4 and never reused (V1.2 §B-005.3). `devices.device_auth_key_id` → `device_auth_keys.key_id` is a `UNIQUE` foreign key: exactly one key per device, exactly one device per key.

### 2.3 One active device per account (S3)

- **[S0-028-08]** The partial unique index `one_active_device_per_account ON devices(account_id) WHERE status = 'ACTIVE'` (V1.2 §B-005.3) is retained as a mandatory `DB-SCHEMA-V1-FROZEN` element.
- **[S0-028-09]** **One wins:** concurrent registration commits for the same `account_id` (or the same JKT, [S0-028-04]) are serialized by the database; the first transaction to commit the `ACTIVE` device wins. Every other concurrent transaction fails with the uniqueness violation, rolls back completely (no partial account/device/key/identity/entitlement rows), and its registration session moves to `REJECTED` with rejection class `PERMANENT`, error `invalid_registration_state`. No last-write-wins; no application-level retry that creates a second `ACTIVE` device.
- **[S0-028-10]** A `REVOKED`/`DELETED` device never returns to `ACTIVE`. Re-activation of an account is a new B-003 registration with a new key and a new `device_id` (V1.2 §B-005.3).

### 2.4 Identity public key immutability (S16)

- **[S0-028-11]** `crypto.identity_public_keys` has `UNIQUE(account_id, device_id)` and global `UNIQUE(ed25519_public_key)` and `UNIQUE(curve25519_public_key)`. The first accepted publication for a device creates the row with `identity_revision = 1`. Any later publication for the same `(account_id, device_id)` carrying **different** identity keys is rejected with error `identity_key_immutable`, rejection class `PERMANENT`, and logged as a security event. A publication carrying **identical** keys is idempotent (same response, no write). The row is never updated or deleted while the device exists; V1 has no same-device identity rotation (B-006 v1.2).
- **[S0-028-12]** Error/disposition classes for this section: `device_auth_key_reuse_rejected` (PERMANENT), `invalid_registration_state` (PERMANENT for the losing/expired/out-of-order session), `identity_key_immutable` (PERMANENT), `authorization_denied` (PERMANENT; key valid but device not `ACTIVE`), `device_revoked` (PERMANENT). All are RFC 9457 problem responses per B-007 §5 and carry `rejection_class` (§3.7). Idempotent re-submission of an identical, already-accepted step returns the original success result (§3.1), never a rejection.

---

## 3. Server DPoP / registration verifier contract (MSC-UNIT-026; SERVER_BREAKER_S4, S7, S8, S10, S11, S12, S17) — B-002 / B-004 / B-007

There is exactly **one** canonical verifier contract. B004 implements it; the client reference verifier (`DpopProofVerifier`, session S4) mirrors it. Both must conform to every clause of §3–§5.

### 3.1 Registration idempotency (S4)

- **[S0-026-01]** Every registration step (`submit-device-auth`, `submit-public-identity`, `commit`) is idempotent on the key `(registration_id, jkt)` plus the step name. An identical re-submission (same `registration_id`, same JKT, same grant hash, same identity material hash) returns the **same authoritative result** as the first acceptance and performs no additional write.
- **[S0-026-02]** A re-submission for the same `(registration_id, jkt)` with **different** material (different grant, different JWK, different identity material) is rejected with `idempotency_conflict`, rejection class `PERMANENT`.
- **[S0-026-03]** `commit` is idempotent for the same authoritative registration: repeated commits for an already-committed `(registration_id, jkt, grant_hash)` return the original `Committed` result (`account_id`, `device_id`, `username`) and never create a second account, device, key or identity row. The B-007 `Idempotency-Key` header remains required on `commit`; server-side registration idempotency is enforced on `(registration_id, jkt)` independently of the header.

### 3.2 Mandatory JKT binding (S7)

- **[S0-026-04]** For **every** request that presents an access token (`Authorization: DPoP <token>`), the verifier MUST compute the JKT of the JWK embedded in the DPoP proof and MUST require it to equal the JKT bound to the token at issuance. Mismatch → `invalid_dpop`, reason class `KEY_BINDING_MISMATCH`, rejection class `PERMANENT`.
- **[S0-026-05]** For registration steps after `submit-device-auth`, the expected JKT is the JKT bound to the registration session; for `/v1/auth/token` it is the JKT of the `ACTIVE` `device_auth_keys` row selected by the proof's own key. There is **no** server mode, configuration flag, default parameter or code path in which JKT binding is skipped, nullable or optional. The verifier API MUST require the expected binding as a non-nullable input (safe-by-construction; FCP-5).
- **[S0-026-06]** `ath` verification (§3.3) never substitutes for JKT binding: a proof signed by an attacker-controlled key with a correct `ath` MUST be rejected on every token-bearing endpoint (breaker S7 for AC-003).

### 3.3 Mandatory `ath` (S8)

- **[S0-026-07]** Whenever a bearer/access token is presented, the DPoP proof MUST contain `ath` = base64url(SHA-256(ASCII(access_token))). Missing or mismatching `ath` → `invalid_dpop`, rejection class `PERMANENT`. Requests that present no token (`/v1/auth/challenge`, `/v1/auth/token`, registration steps) carry no `ath`; a proof carrying an unexpected `ath` on such a request is rejected.

### 3.4 Shared atomic replay store (S10)

- **[S0-026-08]** The DPoP replay store is **shared** by every verifier instance and replica of the deployment and is **atomic**: acceptance of a proof requires an insert-if-absent (`SET NX`-style / `INSERT … ON CONFLICT DO NOTHING` returning the insert outcome) keyed at minimum by `(jkt, jti)`. A proof whose key already exists → `replay_detected`.
- **[S0-026-09]** Process-local verifier memory (in-process maps, per-instance caches, default in-memory caches) is **prohibited** as the production replay store. The client-side reference verifier may use an in-memory store only in tests, and only when injected explicitly (no default replay cache; FCP-5).
- **[S0-026-10]** The store is bounded per JKT (rate/abuse limits per B-015) and its entries survive process restart for at least the retention window of §3.5.

### 3.5 Rollback-safe retention / freshness (S11)

- **[S0-026-11]** Proof freshness: `iat` must lie within ±120 s of authoritative server time (B-002). Authoritative server time is an NTP-disciplined source; a verifier that detects a backward step of its own clock beyond the tolerance MUST fail closed (reject) rather than accept.
- **[S0-026-12]** Replay retention is keyed by the proof's **`iat`** (and/or a monotonic server counter), never by wall-clock insertion time alone: an entry `(jkt, jti)` is retained until `iat + 120 s + 300 s` at minimum (≥ the freshness window plus the B-002 5-minute replay window). Eviction based on a wall clock that has been set backwards MUST NOT re-admit a previously seen `jti`; a rollback of the server clock by any amount MUST NOT shorten retention of stored entries.
- **[S0-026-13]** If the shared store is unavailable, verification fails closed (`invalid_dpop` / `TRANSIENT`); it never degrades to process-local acceptance.

### 3.6 Canonical HTU / HTM (S12)

- **[S0-026-14]** The verifier compares the proof's `htu` and `htm` to the canonical form of the request actually received, constructed per §4. The router dispatches on the **raw** request path; neither side percent-decodes before comparison.

### 3.7 Rejection taxonomy (S17)

- **[S0-026-15]** Every rejection produced by the verifier or by a registration step carries an RFC 9457 problem body with a stable `code` (B-007 §5) **and** a `rejection_class` member with exactly one of two values: `transient` — the client may retry the same registration/request with fresh proof material without changing its lifecycle state; `permanent` — the request/registration is finally refused and the client MUST NOT retry it as-is.
- **[S0-026-16]** Class assignment (frozen): `TRANSIENT` = `use_dpop_nonce`, `rate_limited`, `replay_detected` (the step may be retried with a fresh proof), server unavailability (5xx / shared-store unavailable), server-side time-skew hint. `PERMANENT` = `invalid_dpop` with `KEY_BINDING_MISMATCH`/`ath`/signature/alg failure, `invalid_registration_pop`, `invalid_registration_state` (grant expired, out-of-order step, one-wins loser), `device_auth_key_reuse_rejected`, `identity_key_immutable`, `idempotency_conflict`, `authorization_denied`, `device_revoked`, `account_suspended`, `unsupported_version`.
- **[S0-026-17]** A generic rejection without `rejection_class` is non-conformant wherever client lifecycle behaviour differs between transient and permanent outcomes (armed-registration lifecycle, §8). Anti-enumeration (B-007 §6, B-015) is preserved: `rejection_class` is returned only on authenticated/PoP-verified registration and token-bearing surfaces, never on unauthenticated lookup surfaces.

### 3.8 Baseline proof requirements (S6, retained)

- **[S0-026-18]** DPoP proofs are JWS compact serializations with header `typ = "dpop+jwt"`, `alg = "ES256"` only, and an embedded public `jwk` with `kty = "EC"`, `crv = "P-256"` and no private members; `jti` ≥ 128 random bits; claims `htm`, `htu`, `iat`, `jti`, `nonce` (§5) and `ath` (§3.3) as required. Any other `alg`, curve, `typ`, or a private JWK member → `invalid_dpop` / `PERMANENT`.

---

## 4. HTU / HTM canonicalization (MSC-UNIT-022 contract entry; SERVER_BREAKER_S12) — B-007 amended v2.1-f04

- **[S0-022-01]** Canonical `htu` = `lower(scheme) "://" lower(host) [":" port] raw_path` where: `scheme` is lowercased (`https`; `http` only in local test profiles); `host` is lowercased and MUST be ASCII (a non-ASCII or internationalized host is rejected — no IDNA mapping on either side); `port` is included **only** when present in the request and **not** the scheme default (`443` for `https`, `80` for `http`); `raw_path` is the request-target path **exactly as received, byte for byte** — percent-encoded, **not decoded**, not re-encoded, no dot-segment removal, no case folding, no trailing-slash normalization.
- **[S0-022-02]** The canonical form contains **no userinfo** (an authority component containing `@` is rejected), **no query** (`?` and everything after it is excluded from the canonical form and MUST NOT appear in `htu`), and **no fragment**. An `htu` value that contains userinfo, a query or a fragment is rejected with `invalid_dpop` / `PERMANENT`.
- **[S0-022-03]** Percent-encoding is preserved verbatim: neither client nor server decodes, normalizes or re-encodes the path before comparison, and there is **no** second decoding pass anywhere (no double-decoding). An invalid percent-triplet (e.g. `%G1`, truncated `%2`) or a raw byte outside the RFC 3986 `path` grammar → reject. The following pairs MUST remain **distinct** under this rule: `/v1/a%2Fb` vs `/v1/a/b`; `/v1/x%3Fy` vs `/v1/x?y`; `/v1/x%23y` vs `/v1/x#y`; `/v1/x%00y` vs `/v1/xy`; `/v1/x%2520y` vs `/v1/x%20y` vs `/v1/x y`.
- **[S0-022-04]** Default-port and trailing-slash rules (frozen interop rows): `https://api.example/v1/a` ≡ `https://API.EXAMPLE:443/v1/a`; `https://api.example:8443/v1/a` ≠ `https://api.example/v1/a`; `/v1/a` ≠ `/v1/a/`; an empty path is canonicalized to `/`.
- **[S0-022-05]** `htm` MUST equal the request method byte-exactly; the method MUST be one of the uppercase allow-list `GET`, `POST`, `PUT`, `DELETE`, `PATCH`. Lowercase or mixed-case methods, or methods outside the allow-list, are rejected (`invalid_dpop` / `PERMANENT`); no case normalization is applied.
- **[S0-022-06]** The client constructs `htu` from the same canonical rule over the URL it actually sends (raw encoded path; scheme/host lowercase; default port elided). The client and the server MUST implement this contract in lock-step; a client-only or server-only change to the rule is a breaking change requiring a successor amendment.

---

## 5. DPoP nonce lifecycle (MSC-UNIT-025; SERVER_BREAKER_S9) — B-002 / B-007

- **[S0-025-01]** **Nonce is required, not optional**, for the endpoint classes `registration` (`submit-device-auth`, `submit-public-identity`, `commit`), `auth` (`/v1/auth/token`, `/v1/auth/revoke`) and **every token-bearing request**. A server mode in which the nonce is optional, defaulted or skipped for these classes is prohibited. Only `/v1/auth/challenge` and the unauthenticated registration validation endpoints (`validate-username`, `validate-license`, `begin`) are exempt.
- **[S0-025-02]** **Issuance:** `POST /v1/auth/challenge` returns a fresh nonce in the response body (`nonce`) and in the `DPoP-Nonce` response header. In addition, **every** response from a nonce-required endpoint class (success or rejection) carries a fresh `DPoP-Nonce` header for the next request.
- **[S0-025-03]** **Format and binding:** the nonce is an opaque server-generated value with ≥ 128 bits of entropy (base64url, no padding), stored (or HMAC-verifiable) server-side together with its **binding scope** `(jkt, endpoint_class)` and its issue time. A nonce presented with a different JKT or a different endpoint class than it was issued for is invalid.
- **[S0-025-04]** **TTL:** 300 s from issuance. **Single use:** a nonce is consumed atomically in the shared store (§3.4) on the first successful verification; a second presentation → `replay_detected`. Consumption of the nonce and the `(jkt, jti)` replay check are both required; neither replaces the other.
- **[S0-025-05]** **Missing / expired / invalid / consumed nonce** → HTTP 401 with problem `code = "use_dpop_nonce"`, `rejection_class = "transient"`, and a fresh `DPoP-Nonce` header. On the `/v1/auth/token` endpoint the RFC 9449 `error="use_dpop_nonce"` form is returned in the `WWW-Authenticate: DPoP` challenge as well.
- **[S0-025-06]** **Client retry:** on `use_dpop_nonce` the client retries **once** with the newly issued nonce, a fresh `jti` and fresh `iat`, re-signing the proof (and, for registration steps, the registration PoP of §6). A second consecutive `use_dpop_nonce` for the same request is surfaced as a `TRANSIENT` failure to the caller; no unbounded retry loop.
- **[S0-025-07]** **Client persistence:** the current nonce is kept in process memory only; it is never written to the registration store, the binding marker, the local database or logs. After process restart the client obtains a new nonce via `/v1/auth/challenge` (or from the next `DPoP-Nonce` response) before any nonce-required request.
- **[S0-025-08]** The registration PoP (§6) binds the nonce of the step being executed; a registration step therefore always consumes exactly one nonce.

---

## 6. Registration proof-of-possession (MSC-UNIT-027 contract; SERVER_BREAKER_S5) — B-003 amended v1.6 / B-007

- **[S0-027-01]** Registration PoP is a **typed** structure `RegistrationPoP v1`: a JWS compact serialization with protected header `typ = "anox-reg-pop+jwt"`, `alg = "ES256"`, embedded public `jwk` (P-256, no private members), signed by the **Device Auth private key** — the same key whose JWK is submitted at `submit-device-auth`. No other signer (E2EE identity key, session key, server key) is acceptable. An opaque, untyped `proof` field is **not** a conformant contract.
- **[S0-027-02]** Payload claims (all required): `v` = `1`; `phase` ∈ {`submit_device_auth`, `submit_public_identity`, `commit`}; `registration_id` (UUIDv4); `grant_hash` = base64url(SHA-256(grant bytes)); `nonce` (§5); `jkt` = RFC 7638 thumbprint of the embedded `jwk`; `identity_material_hash` (below); `htu` and `htm` of the step endpoint in canonical form (§4); `iat`; `jti` (≥ 128 bits). The signed context therefore binds `registration_id ‖ grant-hash ‖ nonce ‖ DeviceAuth JWK ‖ identity-material-hash` plus phase, endpoint and freshness — enough to prevent substitution of any component.
- **[S0-027-03]** **Deterministic encoding:** `identity_material_hash` = base64url(SHA-256(`"anox.reg.identity.v1"` ‖ `0x00` ‖ `ed25519_public_key` (32 raw bytes) ‖ `curve25519_public_key` (32 raw bytes))). For `phase = submit_device_auth` (identity not yet published) the value is base64url(SHA-256(`"anox.reg.identity.v1"` ‖ `0x00`)) — the fixed empty-material hash. The header `typ` value provides domain separation from DPoP proofs (`dpop+jwt`); a `dpop+jwt` MUST never be accepted as a registration PoP and vice versa.
- **[S0-027-04]** **PoP is required at all three security-relevant phases:** `submit-device-auth`, `submit-public-identity` and `commit`. A phase request without a PoP, with a PoP whose `phase` does not match the endpoint, or whose `htu`/`htm` do not match the request → `invalid_registration_pop` / `PERMANENT`.
- **[S0-027-05]** **JWK equality:** the embedded `jwk` MUST be byte-canonically equal (RFC 7638 members) to the JWK submitted in the `submit-device-auth` body, and its thumbprint MUST equal the payload `jkt`. From `submit-device-auth` onward the registration session binds that JKT; a PoP or proof with a **different** JWK for the same `registration_id` → `invalid_registration_pop` / `PERMANENT`, and the session moves to `REJECTED`. A second JWK per `registration_id` is never accepted.
- **[S0-027-06]** **Replay / idempotency relation:** the PoP `jti` is single-use in the shared `(jkt, jti)` store (§3.4); the bound `nonce` is single-use (§5). An identical logical step re-submission uses a **fresh** PoP (new nonce, jti, iat) and is idempotent on `(registration_id, jkt)` per §3.1 — same outcome, no duplicate write.
- **[S0-027-07]** **Failure taxonomy:** `invalid_registration_pop` (signature/alg/typ/claims/JWK-equality/phase mismatch — `PERMANENT`); `use_dpop_nonce` (`TRANSIENT`); `replay_detected` (`TRANSIENT` for the step, the proof itself is dead); `device_auth_key_reuse_rejected` (`PERMANENT`, §2.1); `invalid_registration_state` (`PERMANENT`); `idempotency_conflict` (`PERMANENT`). The typed client API (session S4) MUST carry the PoP, the nonce and the idempotency key explicitly on `submitDeviceAuth`, `submitPublicIdentity` and `commitRegistration`; an API shape that accepts an un-typed proof or omits any of them is non-conformant (CC-10).
- **[S0-027-08]** The PoP remains tied to the authoritative Device Auth identity: the server derives the registration's device identity from the PoP's validated key (§2.2), never from JSON fields, so AC-010 (proof/key substitution) is broken at S5 together with C10.

---

## 7. Registration store / binding marker / first-run contract (MSC-UNIT-033) — B-003 amended v1.6 / B-009 / B-013

### 7.1 Canonical binding-marker states

- **[S0-033-01]** The Device Auth binding marker (`anox_deviceauth_binding.state` in `noBackupFilesDir`) has exactly these canonical states: `ABSENT` (no marker file), `ARMED` (pre-commit latch set; registration `CommitArmed` durably persisted), `BOUND` (server commit observed; device identity bound), `EXPLICIT_RESET` (transient state during the explicit reset path of [S0-018-05]/§9 — the marker is removed **last**; a marker that reads `EXPLICIT_RESET` on start means an interrupted reset and is treated as `BOUND`), `CORRUPT` (marker file present but fails authentication, version or parse checks).
- **[S0-033-02]** The marker is **authenticated**: versioned payload (`version ‖ state ‖ jkt ‖ armed_at ‖ bound_at`) with an HMAC-SHA-256 tag under a dedicated Keystore alias `anox.deviceauth.marker.hmac.v1`. An unauthenticated 6-byte flag is non-conformant. If the marker file is present but the HMAC alias is **missing**, the resolver treats the marker as `BOUND` (fail closed: "HMAC key missing ⇒ bound"). An invalid tag ⇒ `CORRUPT`.
- **[S0-033-03]** Marker transitions are `ABSENT → ARMED → BOUND` and `{ARMED, BOUND, CORRUPT} → EXPLICIT_RESET → ABSENT` only. `ARMED`/`BOUND` never revert to `ABSENT` except through the explicit reset path. `clearBinding()`/destructive primitives are not public API (CC-5); all marker mutation goes through one guarded store primitive (FCP-3).

### 7.2 First-run resolver (security-critical)

- **[S0-033-04]** First run is resolved by the following truth table and no other rule: (a) marker `BOUND` or `ARMED` ⇒ **NOT FIRST RUN**; (b) marker `CORRUPT` ⇒ **NOT FIRST RUN**, fail closed, explicit recovery-reset path only; (c) marker `ABSENT` **AND any relevant anoX Keystore alias or local state indicates prior initialization** ⇒ **NOT FIRST RUN**, fail closed, explicit recovery-reset path only; (d) marker `ABSENT` AND no alias AND no state/residue file ⇒ **FIRST RUN** (`AbsentNotBound`).
- **[S0-033-05]** "Relevant anoX Keystore alias/state" for rule (c) is the closed set: aliases `anox.deviceauth.p256.v1`, `anox.b003.session.v1`, `anox_crypto_master_key`, `anox_db_wrap_v1`, `anox.deviceauth.marker.hmac.v1`; files `anox_registration_session.enc`, `anox_registration_session.state` (legacy), `anox_state_key.enc`, `anox_identity.enc`, `anox_session.enc`, the SQLCipher database and its `-wal`/`-shm`, and any residue file of [S0-033-08]. Adding an alias or file to the product adds it to this set in a successor amendment.
- **[S0-033-06]** The resolver never creates a Keystore key, a file or a marker (CC-1: no create-on-read). `docs/current/LOCAL_KEY_STATE_LIFECYCLE_V1_FROZEN.md §J` ("`FirstRun` — no state files") is informative and is refined by [S0-033-04]–[S0-033-05]; where they differ, this section wins.

### 7.3 Registration-store failure taxonomy

- **[S0-033-07]** `FileRegistrationSessionStore` load outcomes are **typed** and closed: `EMPTY` (zero-length file), `TRUNCATED` (file shorter than the envelope header/tag), `AUTH_FAILED` (AES-GCM tag invalid / corrupt ciphertext), `KEY_MISSING` (Keystore alias `anox.b003.session.v1` absent while a file exists), `UNSUPPORTED_VERSION`, `MARKER_CORRUPT`, `MARKER_HMAC_KEY_MISSING`, `IO_FAILURE`. **Every** one of these is consumed as **NOT FIRST RUN** and surfaces as a typed `RegistrationSessionSecurityException`; **none** maps to `NotStarted`, `Failed`, or "can start new". The historical rule "corrupt session → `NotStarted` is safe" (PROMPT-008 §7) is superseded.
- **[S0-033-08]** **Residue files** (`*.tmp`, `*.new`, `*.bak`, legacy `anox_registration_session.state`, `anox_registration_session.state.tmp`) indicate prior initialization for rule (c). A `.bak` file is **never** auto-restored; residue is removed only by the explicit reset path or by a startup cleanup that runs strictly **after** the first-run resolver has evaluated it.

### 7.4 Durability, ordering and process model

- **[S0-033-09]** Every writer of registration state, marker or crypto state uses: write temp file → flush → `fsync` file → atomic rename → `fsync` parent directory; the rename result is checked and a failure is surfaced (never swallowed). `markArmed()` and `markBound()` return only after the marker is durable.
- **[S0-033-10]** Frozen commit ordering: registration store `CommitArmed` persisted → marker `ARMED` → remote `commit` (§6) → registration store `Committed` persisted → marker `BOUND`. A crash between any two steps resumes into the last durable state; it is transaction resume, never account recovery (B-003 v1.5 §3).
- **[S0-033-11]** **Single-process assumption:** the registration store, marker store and crypto state stores are accessed from exactly one process; in-process access is serialized. Concurrent multi-process access is a defect, not a supported mode. The stores fail closed on any evidence of concurrent mutation (e.g. unexpected temp file, changed inode).

---

## 8. Armed-latch lifecycle: `RejectedAfterArm` (MSC-UNIT-018 contract; CLIENT_BREAKER_C13, SERVER_BREAKER_S17) — B-003 amended v1.6

- **[S0-018-01]** The client registration state machine gains the canonical state `RejectedAfterArm(registrationId, jkt, rejectionClass, code)` reached **only** from `CommitArmed` when the remote `commit` returns a rejection (§3.7). `Rejected` MUST NOT be persisted as `Failed`, `NotStarted` or any state that permits a fresh registration while the marker is `ARMED`.
- **[S0-018-02]** **Transient rejection** (`rejection_class = transient`): the state becomes `RejectedAfterArm(transient)`; the marker stays `ARMED`; the client MAY retry `commit` with the **same** `registration_id`, grant and Device Auth identity (fresh PoP/nonce) until the grant TTL elapses. Retry success → `Committed` → marker `BOUND`.
- **[S0-018-03]** **Permanent rejection** (`rejection_class = permanent`, or grant expiry while armed): the state becomes `RejectedAfterArm(permanent)`; the marker stays `ARMED`; **no** retry and **no** fresh registration is permitted from this state. The only exits are (i) a later successful idempotent commit response for the same authoritative registration (§3.1) or (ii) the **explicit reset path** of [S0-018-05].
- **[S0-018-04]** **Armed-state persistence:** `RejectedAfterArm` is durably persisted through the same guarded store primitive as every other state; the guard lives at the store (FCP-3): no caller can persist a downgrade from `CommitArmed`/`RejectedAfterArm` to a lower state (`Failed`, `NotStarted`, `Reserved`, …) outside the explicit reset path. Direct `save()` bypasses are non-conformant.
- **[S0-018-05]** **Explicit reset contract (deletion order):** the reset is an explicit, user-confirmed, destructive action. Frozen order: (1) if reachable, best-effort server notification/abandonment of the registration (never a precondition); (2) destroy the Device Auth key alias `anox.deviceauth.p256.v1`; (3) delete the registration session file and all residue, then destroy `anox.b003.session.v1`; (4) delete any locally created E2EE identity/session/state-key material created during the registration; (5) set marker `EXPLICIT_RESET`, then delete the marker file **last**, then destroy `anox.deviceauth.marker.hmac.v1`. The Device Auth alias is always deleted **before** the marker so that an interrupted reset leaves the resolver fail-closed (AC-001/A is never re-created).
- **[S0-018-06]** **Release conditions:** the armed latch is released only by `BOUND` (successful commit) or by completion of step (5) of [S0-018-05]. Silent release on `Rejected`, on grant expiry, on process restart or on `Failed` is prohibited. Code for this state lands in session S3 (or B004 wiring); this freeze is contract only.

---

## 9. Wipe / logout / account-delete / reset / revocation domain matrix (MSC-UNIT-032; SERVER_BREAKER_S18, CLIENT_BREAKER_C11) — B-013 amended v1.4 / B-009

### 9.1 Per-operation domain matrix

Legend: **R** = retained · **D** = deleted locally (truthful, per-item result) · **V** = revoked/terminal on server · **I** = remotely invalidated (best effort when reachable; local outcome never depends on it) · **—** = not applicable.

- **[S0-032-01]** Operations are distinguished exactly as: `logout` (network-session termination), `local wipe` (user-initiated local destruction), `account deletion` (strong authenticated destructive action), `explicit reset` (registration abandonment, [S0-018-05]), `device revocation` (server-side terminal revoke, initiated by the account holder or operations), `license-expiry restricted flow` (entitlement `EXPIRED`).

| Domain | logout | local wipe | account deletion | explicit reset | device revocation | license expiry |
|---|---|---|---|---|---|---|
| Device Auth alias `anox.deviceauth.p256.v1` | R | D | D | D | R (key useless; no regeneration) | R |
| RegistrationSession alias `anox.b003.session.v1` | R | D | D | D | R | R |
| Crypto-state aliases `anox_crypto_master_key`, `anox_db_wrap_v1` | R | D | D | D (only material created during registration) | R | R |
| Marker HMAC alias `anox.deviceauth.marker.hmac.v1` | R | D (last) | D (last) | D (last) | R | R |
| Identity / session files `anox_identity.enc`, `anox_session.enc`, `anox_state_key.enc` | R | D | D | D (registration-created only) | R | R |
| Registration session file + residue | R | D | D | D | R | R |
| Local DB (`-wal`/`-shm`), encrypted attachments, temp files | R | D | D | — | R | R |
| Binding marker `anox_deviceauth_binding.state` | R | D (last) | D (last) | D (last) | R | R |
| Live native handles (identity/session) | R | D (destroy before file deletion) | D | D | R | R |
| Access token / session (memory) | D + I | D + I | D + I | — | I | R (server rejects service actions) |
| Push registration | I | I | I | — | I | R |
| Server `devices` row | R (`ACTIVE`) | V (wipe intent → `REVOKED`, best effort) | V (`REVOKED`, then account `DELETED`) | — (registration not committed) | V | R (`ACTIVE`, entitlement `EXPIRED`) |
| Server sessions/tokens | V | V | V | — | V | R |

- **[S0-032-02]** **Logout keeps the key:** logout revokes access token/session and push registration only; Device Auth key, E2EE identity/sessions, local DB and marker are retained (B-002, B-013 v1.2). Re-authentication on the same device uses the existing Device Auth key.
- **[S0-032-03]** **Device revocation is terminal** (`ACTIVE → REVOKED`, S18): the server rejects all further authentication for the key; the client never silently generates a replacement key; the `device_auth_keys` row is retained (§2.1) so the key stays known.
- **[S0-032-04]** **Account deletion** writes the terminal erasure intent durably server-side first, revokes device/sessions/push, purges queued server data per B-014, then forces the local wipe of this matrix (B-013 v1.2). Remote steps are `I`/`V`; the local wipe still completes offline.
- **[S0-032-05]** **License expiry restricted flow** retains every local domain (B-013 v1.3 §1); no deletion, no key rotation; renewal preserves all bindings.

### 9.2 Truthful outcomes and deletion ordering

- **[S0-032-06]** Destructive operations produce **truthful per-item outcomes**: each domain reports `DELETED`, `NOT_PRESENT`, or `FAILED(reason)`; the aggregate result is `Success` only if every required domain is `DELETED` or `NOT_PRESENT`. Ignoring `delete()` return values or reporting `Success` on partial failure is non-conformant. No NAND physical-erasure claim is made (B-009).
- **[S0-032-07]** **Frozen deletion order** for `local wipe` / `account deletion`: (1) stop workers/notifications; (2) best-effort remote revoke + push removal when reachable (never blocking); (3) close the local DB and destroy live native handles; (4) delete identity/session/state-key files, DB/WAL/SHM, attachments, temp/residue; (5) destroy aliases `anox.b003.session.v1`, `anox_crypto_master_key`, `anox_db_wrap_v1`, then `anox.deviceauth.p256.v1`; (6) set marker `EXPLICIT_RESET`, delete the marker file **last**, then destroy `anox.deviceauth.marker.hmac.v1`. The marker/binding state is never removed early; a wipe interrupted before step (6) leaves the resolver fail-closed (AC-001 not re-created). The order for `explicit reset` is [S0-018-05].
- **[S0-032-08]** Destructive primitives (`deleteKeyDestructively`, `clearBinding`, `clear()`, `wipeLocalCrypto`) are callable only from the single wipe/reset orchestrator (CC-5, CC-11); they are not public API for feature code. Implementation lands in B013 (S8); this freeze is contract only.

---

## 10. Backup / restore / reinstall / profile / rollback expected-state contract (MSC-UNIT-034; carries SERVER_BREAKER_S15) — B-013 / B-009 / Security Invariant 25

### 10.1 Assumption classes

- **[S0-034-01]** Every statement about Android Keystore or file survival is classified as exactly one of: **CONTRACTUAL** (the product MUST behave this way regardless of platform behaviour), **PHYSICAL_TEST_DEPENDENT** (platform behaviour that MUST be measured in the GrapheneOS physical campaign `PHYSICAL_P4`, `P5`, `P7`, `P8`, `P10`, `P11` on a provenance-verified binary before it may be relied upon), or **PROHIBITED_ASSUMPTION** (MUST NOT be assumed by any code path or document).
- **[S0-034-02]** **PROHIBITED_ASSUMPTIONS:** that Keystore aliases are deleted by app-data clear, uninstall or profile deletion; that no anoX file can ever be restored by a backup agent; that StrongBox is present; that the local clock or any local counter is monotonic across rollback; that a restored file set is fresh. **CONTRACTUAL:** the first-run resolver of §7.2 fails closed whenever any alias or file indicates prior initialization; private state is excluded from every backup transport (`allowBackup="false"`, `noBackupFilesDir`, no backup rules); Keystore keys are non-exportable and never restorable; the server is the sole freshness/uniqueness authority (§10.3).

### 10.2 Expected security state per scenario

- **[S0-034-03]** Android app-data clear (`pm clear`): CONTRACTUAL — all anoX files gone; if any Keystore alias survives (PHYSICAL_TEST_DEPENDENT, `P4`), the resolver yields NOT FIRST RUN → explicit reset only; the server keeps the old device `ACTIVE` until revoked and rejects re-registration of the surviving key (§2.1). Expected client state after clear with no surviving alias: `AbsentNotBound` (first run, new account required — old identity unrecoverable, Security Invariant 3).
- **[S0-034-04]** Uninstall / reinstall: identical to [S0-034-03] (`P5`). Uninstall never transfers or recovers the account.
- **[S0-034-05]** Backup / restore (Google cloud backup, Seedvault-style local/USB backup, device-to-device transfer): CONTRACTUAL — no anoX private file, marker or registration store is included in any backup; if a backup agent nevertheless restores an anoX file, the resolver treats it as prior initialization (NOT FIRST RUN, fail closed) and the server rejects stale state via §10.3; Keystore keys never travel. Observation of the actual agents is PHYSICAL_TEST_DEPENDENT (`P10`, `P11`). No recovery path may be created by any restore (Security Invariant 25).
- **[S0-034-06]** Owner vs secondary / work profile: each Android user/profile has its own app sandbox and Keystore namespace → each profile instance is an **independent device** and therefore an independent account in V1; the Owner profile is unaffected by secondary/work profile installation or deletion (PHYSICAL_TEST_DEPENDENT, `P8`). Profile deletion behaves as uninstall for that profile ([S0-034-04]).
- **[S0-034-07]** OS update: bound state unchanged; no re-registration, no key regeneration (PHYSICAL_TEST_DEPENDENT, `P7`). Keystore key invalidation by the platform is treated as terminal Device Auth loss (B-002) — never silent regeneration.
- **[S0-034-08]** Rollback scenarios (older file set restored over newer state; snapshot/restore of the sandbox): local AEAD authenticates but cannot prove freshness; the client MUST bind the server publication epoch (§11) into local envelope AAD once available and MUST treat an epoch mismatch as a security anomaly requiring reconcile — never as normal operation. A local counter is not an anti-rollback authority (PROHIBITED_ASSUMPTION).

### 10.3 Server authority role (S15 carrier)

- **[S0-034-09]** The server is the **authoritative** source for (a) Device Auth key uniqueness and device binding (§2), (b) freshness/anti-rollback of published key material via the publication epoch (§11), and (c) OTK consumption state (`CLAIMED` terminal, B-006). No client-local mechanism may claim these roles. This clause is the `SERVER_BREAKER_S15` authority entry consumed by MSC-UNIT-020 (§11).
- **[S0-034-10]** No physical test is executed by this freeze; `PHYSICAL_P1…P17 = NOT_EXECUTED`. Physical results are admissible only from a provenance-verified, CI-built binary (FCP-1, MSC-UNIT-001/036).

---

## 11. Server publication / identity revision epoch (MSC-UNIT-020 contract entry; SERVER_BREAKER_S15) — B-006 amended v1.4-f04 / B-005

- **[S0-020-01]** The server maintains, per `(account_id, device_id)`, an authoritative **monotonic** integer `publication_epoch` (starting at `0` before any publication) alongside the immutable `identity_revision` (`1` in V1). `publication_epoch` is stored in `DB-SCHEMA-V1-FROZEN` (`crypto.identity_public_keys.publication_epoch`) and is incremented **only by the server**, inside the same transaction that accepts a state-changing key-distribution operation.
- **[S0-020-02]** **When it changes:** on every accepted OTK batch publication (`POST /v1/keys/one-time-prekeys`), fallback-key publication, signed-prekey publication, and on each server-side transition that consumes published material (`AVAILABLE → CLAIMED` batches, expiry cleanup). Idempotent re-publication of an identical batch does **not** increment it.
- **[S0-020-03]** **How the client receives it:** every key-distribution response and `GET /v1/account/status` returns `publication_epoch` (and `identity_revision`). The client persists the received epoch only **after** the server ACK, together with `mark_keys_as_published` (B-006 §3), inside the same durable local transaction.
- **[S0-020-04]** **Local binding:** the client binds the last acknowledged `publication_epoch` (and `identity_revision`) into the AAD of the local identity envelope, and the corresponding session-state epoch into session envelopes (CC-10, CC-3); the AAD is `magic ‖ version ‖ object_type ‖ context ‖ epoch`. An envelope authenticated under an older epoch than the one the client last acknowledged is **stale**.
- **[S0-020-05]** **Stale re-publication:** every publication request carries `expected_epoch` (the client's last acknowledged value). If `expected_epoch < server publication_epoch`, the server rejects with `stale_publication_epoch`, rejection class `PERMANENT` for that batch, and returns the current epoch; the client MUST reconcile (fetch status, discard OTKs the server reports `CLAIMED`/unknown, re-derive the unpublished set) before any new publication. If `expected_epoch > server publication_epoch` the server has been rolled back (restore); the server logs a security event, refuses publication (`stale_publication_epoch`) and the condition requires operator reconciliation — never silent acceptance.
- **[S0-020-06]** **Behaviour on client rollback:** on load, a local epoch lower than the server's current epoch means the local state predates acknowledged publications; the client MUST NOT use or re-publish OTKs from that state and MUST run the reconcile of [S0-020-05]. This is the S15 breaker for AC-005 (OTK re-publication / Olm key reuse after rollback).
- **[S0-020-07]** No anti-rollback code is created by this freeze. Implementation: B006 (identity/OTK leg, session S6) and B008/B009 (session leg, S7). `identity_revision` remains `1` — no same-device identity rotation in V1.

---

## 12. Hardware-level trust / attestation decision (MSC-UNIT-042; SC-14; remediates ANOX-SECURITY-ARCH-006) — B-002 amended v1.2-f04

- **[S0-042-01]** **Decision:** V1 does **NOT** require remote hardware attestation (B-002 v1.1 preserved). No attestation backend, attestation certificate-chain verifier or attestation root store is introduced by this freeze; introducing one is a B-002 v2 candidate requiring an ADR and a successor amendment.
- **[S0-042-02]** **Identity derives from validated key material only:** Device Auth identity (JKT → `device_id` → `account_id`, §2.2) is established by proof-of-possession of the P-256 key. The client-reported hardware level is **never** an input to authentication, authorization, entitlement, `AuthenticatedDeviceContext`, RLS context or any server-side trust decision.
- **[S0-042-03]** **Client-reported informational data:** the client MAY report `security_level_reported ∈ {STRONGBOX, TEE, SOFTWARE}` (from `KeyInfo.securityLevel`) at `submit-device-auth`. The server stores it as **informational** (telemetry / support / physical-campaign correlation) and MUST NOT treat it as a fact about the key; it MUST NOT reject or privilege a registration based on it. Self-reported StrongBox is not a server authorization fact.
- **[S0-042-04]** **Client policy (unchanged, restated for one home):** StrongBox **preferred**; TEE **acceptable** in production (canonical V1 policy, B-002 v1.1); `SOFTWARE` fails production registration **client-side** (the key is destroyed before any submission; a pre-existing bound alias is never deleted by this check — MSC-UNIT-029). Software-key rejection is a client integrity control, not a server-verifiable one.
- **[S0-042-05]** **Residual risk (accepted, documented):** an attacker-controlled client may register with a software-backed or exported key; because identity derives from possession of that key (§2.2) and JKT binding is mandatory (§3.2), the impact is confined to the attacker's own account/device; it does not enable impersonation of honest devices (AC-003 remains broken at S7). Honest devices retain non-exportability; physical verification of the honest-device level is `PHYSICAL_P1` (`NOT_EXECUTED`).

---

## 13. Server security contract authority map (SC-1 … SC-14)

- **[S0-000-06]** Every rule of the consolidated server security contract has exactly **one** canonical authority home in this document (clauses listed) plus the retained base clauses it references. `SERVER CONTRACT RULES = 14`, `AMBIGUOUS = 0`, `CONTRADICTORY = 0`.

| SC | Rule (summary — normative text lives in the clauses) | Authority home (clauses) | Retained base |
|---|---|---|---|
| SC-1 | Typed registration PoP at all three phases; JWK-in-proof == submitted JWK; second JWK rejected | [S0-027-01]–[S0-027-08] | B-003 v1.5 §3 |
| SC-2 | Registration idempotency on `(registration_id, jkt)`; commit idempotent | [S0-026-01]–[S0-026-03] | B-007 v2.0-f02 §3 |
| SC-3 | `UNIQUE(device_auth_keys.public_key)` global; known-key rejection; one active device + one wins | [S0-028-01]–[S0-028-04], [S0-028-08]–[S0-028-10] | V1.2 §B-005.3 |
| SC-4 | JKT → device_id → account immutable; context from validated key only | [S0-028-05]–[S0-028-07] | V1.2 §B-004.2, §B-005.4 |
| SC-5 | `identity_public_keys` immutable per device, enforced at publish | [S0-028-11] | V1.2 §B-005.2 |
| SC-6 | ES256/P-256 proof; jkt binding mandatory; ath mandatory; htm equality; iat ±120 s | [S0-026-04]–[S0-026-07], [S0-026-11], [S0-026-18] | B-002 v1.1 |
| SC-7 | Nonce issuance / `DPoP-Nonce` / `(jkt, endpoint class)` / single-use / `use_dpop_nonce` | [S0-025-01]–[S0-025-08] | B-002 v1.1, B-007 §2 |
| SC-8 | Shared atomic `(jkt, jti)` replay store; iat/monotonic retention; bounded | [S0-026-08]–[S0-026-13] | B-002 v1.1 |
| SC-9 | Canonical raw-path HTU; no userinfo/query/fragment; router matches raw path | [S0-022-01]–[S0-022-06], [S0-026-14] | B-007 v1.9 |
| SC-10 | `otk_id`-keyed idempotent publication; same id ≠ key = error; `CLAIMED` terminal | V1.2 §B-006.1–§B-006.3 (retained; epoch coupling [S0-020-02]) | V1.2 §B-006 |
| SC-11 | Monotonic publication epoch echoed to client for local AAD binding | [S0-020-01]–[S0-020-07], [S0-034-09] | V1.2 §B-006 |
| SC-12 | Rejection-class taxonomy transient vs permanent for armed-latch release | [S0-026-15]–[S0-026-17], [S0-018-02]–[S0-018-03] | B-007 §5 |
| SC-13 | Device revoked on account-delete/wipe intent; logout keeps key; revocation terminal | [S0-032-01]–[S0-032-07] | B-013 v1.2, B-002 v1.1 |
| SC-14 | Self-reported hardware level not trusted for authorization; identity from key; attestation decision | [S0-042-01]–[S0-042-05] | B-002 v1.1 |

---

## 14. Client security contract authority map (CC-1 … CC-14)

- **[S0-000-07]** S0 implements no client code. Each client contract rule has a known **authority owner that is an `AUTHORITY_INDEX.md`-indexed normative document** so that sessions S2/S3/S4/S7/S8 receive unambiguous normative requirements. `CLIENT CONTRACT RULES = 14`, `AUTHORITY OWNER KNOWN = 14`.
- **[S0-000-15]** **Evidence is not authority.** `MASTER-SPECIALIST-CONSOLIDATION-001` and `SECURITY-REMEDIATION-COVERAGE-GATE-001` are hash-preserved **traceability / evidence** artefacts under `docs/reports/security/`; they are not listed in `AUTHORITY_INDEX.md` and therefore **may never be cited as the normative authority home** of a contract rule. Where a rule's detailed requirement text appears only in that evidence, the normative owner is the authority-indexed document it derives from, and the consolidation reference is recorded as `traceability` only. Requirements whose detailed design is fixed at implementation time (e.g. the CC-2 JNI handle representation, owned by `MSC-UNIT-005`/`006`/`007`/`008` in session S2) are **not** frozen by this document and gain no S0 contract.

| CC | Rule (summary) | Authority owner (normative, authority-indexed) | Traceability (evidence, non-normative) | Implementing session |
|---|---|---|---|---|
| CC-1 | No Keystore key creation on read/status paths; create-on-write; serialized creation | [S0-033-06]; Security Invariant 23 | `LOCAL_KEY_STATE_LIFECYCLE_V1_FROZEN.md §C/§G` (informative) | S2 (CryptoBridge half), S3 |
| CC-2 | Opaque `(slot, generation)` JNI handles; owning lock; `HANDLE_*` codes; one bridge; `CryptoNative` not app-reachable | Security Invariant 23 (integrity of local crypto state; no silent regeneration) + Security Invariant 24 (key separation) + `B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` (**narrow** Kotlin→JNI→Rust interface boundary) | `MASTER-SPECIALIST-CONSOLIDATION-001` CC-2 — the concrete handle representation is a **code** requirement of `MSC-UNIT-005/006/007/008`, fixed at S2 implementation time and **not** frozen by this document ([S0-000-15]) | S2 |
| CC-3 | Native-allocated exact-size output with caps; AAD `magic ‖ version ‖ object_type ‖ context` (+ epoch) | [S0-020-04]; Security Invariant 24; B-009 v1.4 | — | S2, S3 |
| CC-4 | Stable `{KeyId, pk}` OTK surface; counts distinct; mark-published per B-006 | V1.2 §B-006.3 | — | S2 (+B006) |
| CC-5 | DeviceAuth P-256 non-exportable; StrongBox preferred/TEE ok/software fails; terminal loss never regenerates; destructive primitives not public | [S0-042-04], [S0-033-03], [S0-032-08]; B-002 v1.1 | — | S3 |
| CC-6 | Non-null `DpopBinding`; factory requires token; no default replay cache; raw-path htu; HTM allow-list | [S0-026-05], [S0-026-09], [S0-022-01]–[S0-022-06] | — | S4 |
| CC-7 | First-run resolver truth table; HMAC marker; "HMAC key missing ⇒ bound"; corruption fails closed | [S0-033-01]–[S0-033-06] | — | S3 |
| CC-8 | Typed store failure taxonomy consumed as not-first-run; empty file = security exception; one guarded mutation path; `RejectedAfterArm` | [S0-033-07]–[S0-033-08], [S0-018-01]–[S0-018-06] | — | S3 |
| CC-9 | fsync file + parent dir in every writer; rename checked; `.bak` never restored; residue policy | [S0-033-08]–[S0-033-09] | — | S3 (+S2 `writeFileAtomic`) |
| CC-10 | Local envelopes bind type‖version‖context; server epoch echoed into AAD; no local counter as anti-rollback | [S0-020-04]–[S0-020-06], [S0-034-08] | — | S3 (+S6/S7) |
| CC-11 | Cross-domain wipe orchestrator; truthful per-item results; alias-first, marker-last; logout keeps key | [S0-032-01]–[S0-032-08] | — | S8 (B013) |
| CC-12 | Injective native→JVM error codes; version ≠ corruption ≠ key-missing ≠ stale-handle | [S0-033-07] (typed, disjoint store-failure classes) + Security Invariant 23 | `MASTER-SPECIALIST-CONSOLIDATION-001` CC-12 — the native-side `HANDLE_*`/error-code table is a **code** requirement of `MSC-UNIT-007` (S2), not frozen here ([S0-000-15]) | S2, S3 |
| CC-13 | Best-effort zeroization; deterministic handle release | Security Invariant 26; B-009 v1.4 | — | S7 |
| CC-14 | UUIDv4 version AND variant validated | B-003 v1.5 §2 (identifier rules); B-007 v1.9 (lowercase UUIDv4) | — | S3 |

---

## 15. Server breaker authority map (SERVER_BREAKER_S1 … S18)

- **[S0-000-08]** `SERVER BREAKERS TOTAL = 18`; each has one authority status recorded here. Breakers whose contract is frozen by this document are `FROZEN_IN_AUTHORITY`; breakers already frozen in V1.2 are `RETAINED_V1_2`; all remain `IMPLEMENTATION = NOT_STARTED`.

| S | Invariant | Authority clauses | Status |
|---|---|---|---|
| S1 | Global unique `device_auth_keys.public_key` + known-key rejection | [S0-028-01]–[S0-028-04] | FROZEN_IN_AUTHORITY |
| S2 | JKT → device_id → account immutable; context from validated key | [S0-028-05]–[S0-028-07] | FROZEN_IN_AUTHORITY |
| S3 | One active device per account; one wins | [S0-028-08]–[S0-028-10] | FROZEN_IN_AUTHORITY |
| S4 | Idempotency on `(registration_id, jkt)`; commit idempotent | [S0-026-01]–[S0-026-03] | FROZEN_IN_AUTHORITY |
| S5 | Typed registration PoP at all three phases; JWK equality | [S0-027-01]–[S0-027-08] | FROZEN_IN_AUTHORITY |
| S6 | ES256 over embedded jwk; P-256 only | [S0-026-18] | RETAINED_V1_2 (B-002 v1.1) |
| S7 | Mandatory jkt binding | [S0-026-04]–[S0-026-06] | FROZEN_IN_AUTHORITY |
| S8 | Mandatory ath when token presented | [S0-026-07] | FROZEN_IN_AUTHORITY |
| S9 | Nonce lifecycle | [S0-025-01]–[S0-025-08] | FROZEN_IN_AUTHORITY |
| S10 | Shared atomic `(jkt, jti)` replay store | [S0-026-08]–[S0-026-10] | FROZEN_IN_AUTHORITY |
| S11 | Rollback-safe iat/monotonic retention | [S0-026-11]–[S0-026-13] | FROZEN_IN_AUTHORITY |
| S12 | Canonical raw-path htu | [S0-022-01]–[S0-022-06], [S0-026-14] | FROZEN_IN_AUTHORITY |
| S13 | `otk_id`-keyed idempotent publication | V1.2 §B-006.3 | RETAINED_V1_2 |
| S14 | Consumed-OTK enforcement (`CLAIMED` terminal) | V1.2 §B-006.1–§B-006.2 | RETAINED_V1_2 |
| S15 | Publication/rollback epoch echoed to client | [S0-020-01]–[S0-020-07], [S0-034-09] | FROZEN_IN_AUTHORITY |
| S16 | `identity_public_keys` immutability at publish | [S0-028-11] | FROZEN_IN_AUTHORITY |
| S17 | Rejection-class taxonomy | [S0-026-15]–[S0-026-17] | FROZEN_IN_AUTHORITY |
| S18 | Device revocation on account-delete / wipe intent | [S0-032-03]–[S0-032-04], [S0-032-07] | FROZEN_IN_AUTHORITY |

---

## 16. Attackchain contract coverage

- **[S0-000-09]** The frozen contracts preserve the breakers required for `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`, `AC-008`, `AC-009`, `AC-010`, `AC-014` as follows. **AC-001:** server uniqueness alone (S1) is **not** accepted as the breaker; the contract retains the client resolver defence (C1, §7.2) **and** the server binding defence (S1/S2, §2); both halves are required (FCP-4). **AC-002:** S12/C9 (§4). **AC-003:** **mandatory JKT binding (S7, §3.2) is the single point; `ath` alone is insufficient** ([S0-026-06]) plus C9 and nonce freshness (§5). **AC-004:** S10 ∧ S11 (§3.4–§3.5) with nonce (§5). **AC-005:** S15 (§11) with C12 (CC-10). **AC-008:** C11 + S16 + S18 (§9, [S0-028-11]). **AC-009:** S4 (§3.1) with C4 (CC-9). **AC-010:** S5 — the registration PoP stays tied to the authoritative DeviceAuth identity ([S0-027-08]) with C10. **AC-014:** C13 ∧ S17 (§8, §3.7).

---

## 17. Preserved governance decisions (not altered by this freeze)

- **[S0-017-01]** `ROOT-013` canonical severity is `MEDIUM` (ratified by `HUMAN_DECISION_R1`) and the finding remains `OPEN`. S0 does not remediate ROOT-013 and does not alter its severity.
- **[S0-017-02]** `ROOT-016` remains `REJECTED_NOT_A_FINDING` — **DO NOT REVIVE**. Nothing in §7–§9 (Device Auth lifecycle, reset, wipe wording) revives it; the separate pre-binding key-creation race remains `MSC-UNIT-029`.
- **[S0-017-03]** `ANOX-SECURITY-ARCH-010` remains `OPEN` / `INFO` with trigger `RETIRE_AT_B004_START` (`HUMAN_DECISION_H3`). It is **not** retired by S0; B004 has not started.
- **[S0-017-04]** `MSC-UNIT-039` (Human governance decisions) is consumed as decided in `HUMAN-PRE-REMEDIATION-DECISIONS-001` and is not reopened.

---

## 18. Precedence and superseded provisions

- **[S0-000-10]** This document takes precedence immediately after `B025_MANDATORY_AMENDMENTS_V1_3.md` in `AUTHORITY_INDEX.md` and above every `B025/TRACK_B/*` snapshot item, `docs/current/*` document and historical material. It supersedes **only** the following enumerated provisions; everything else in V1.1/V1.2/V1.3 and the unamended B-025 items remains in force.

| Superseded provision | Superseding clauses |
|---|---|
| V1.2 §B-005.2 row `device_auth_keys` (`public_key_pem`, no uniqueness) | §1, [S0-028-01]–[S0-028-03], [S0-040-04] |
| V1.2 §B-005.2 row `identity_public_keys` (immutability without enforcement rule; no epoch) | [S0-028-11], [S0-020-01] |
| V1.2 §B-005.3 (one active device — race semantics "generic error") | [S0-028-08]–[S0-028-10], [S0-026-15]–[S0-026-16] |
| V1.2 §B-004.2 (`AuthenticatedDeviceContext` derivation source) | [S0-028-05] |
| V1.2 §B-007.2 Registration row (`None / PoP for commit`, DPoP `No / Yes for commit`) | [S0-027-04], [S0-025-01] |
| V1.2 §B-007.4 row "Two registration commits" | [S0-028-09] |
| V1.2 §B-007.5 error model (extended by `rejection_class` and new codes) | [S0-026-15]–[S0-026-17], [S0-028-12], [S0-027-07], [S0-020-05] |
| V1.2 §B-006.3 (publication ACK — extended by epoch) | [S0-020-02]–[S0-020-05] |
| V1.1 §B-003.3 `CommitArmed` semantics (extended by armed-latch lifecycle) | §7.1, §7.4, §8 |
| V1.1 §B-013.1 (restricted mode — domain matrix column) | [S0-032-05] |
| B-002 v1.1 nonce / `htu` / replay bullets (made exact) | §3, §4, §5 |
| B-002 v1.1 "no mandatory remote attestation V1" (decision recorded with residual risk) | §12 |
| B-009 v1.4 / B-013 v1.2 wipe bullets (made a per-operation matrix with order) | §9 |
| `docs/current/DATABASE_ARCHITECTURE.md` §1, `docs/current/BACKEND_ARCHITECTURE.md` §4 "schema not frozen" | [S0-040-02] |
| `docs/current/LOCAL_KEY_STATE_LIFECYCLE_V1_FROZEN.md` §J first-run definition | [S0-033-06] |
| PROMPT-008 §7 "corrupt session → NotStarted is safe" | [S0-033-07] |

- **[S0-000-11]** Contract version: `S0-CONTRACT-FREEZE v1` (this document). Future agents determine the current contract by `AUTHORITY_INDEX.md` → this file → the manifest; older documents listed in the table above are informative for the superseded provisions.

---

## 19. What this freeze does not do

- **[S0-000-12]** `B004 = NOT_STARTED`; `B005 = NOT_STARTED`; `BACKEND = NOT_IMPLEMENTED`; `S1 = NOT_EXECUTED_BY_THIS_TASK` (authorized, parallel); `S2 = NOT_STARTED`; `S3 = NOT_STARTED`; `S4 = NOT_STARTED`. No SQL, no Kotlin, no Rust, no CI, no manifest and no native artifact is changed. Build/provenance policy items relevant to S1 (MSC-UNIT-001/002/003/038) are referenced as authority dependencies only and are not implemented here.
- **[S0-000-13]** MSC unit stages proposed by S0 (subject to independent Architecture retest): `025, 026, 027c, 028, 032, 033, 034, 040, 042, 018c, 020c` → `IMPLEMENTED (FROZEN_IN_AUTHORITY)` → `AUTOMATED_TESTED (CONTRACT_VALIDATOR_PASS)`. None reaches `INDEPENDENTLY_RETESTED`, `EVIDENCE_PRESERVED` or `CLOSED`. `FULLY CLOSED MSC UNITS = 0`; `OPEN MSC UNITS = 42`.
- **[S0-000-14]** Next required action: `INDEPENDENT ARCHITECTURE RETEST OF S0 → PRESERVE/FREEZE S0 REMEDIATION EVIDENCE → MERGE`. Dependent sessions S3/S4 MUST NOT start before that gate is satisfied.

---

## Historical provenance

This V1.4 amendment does not modify the B-025 historical snapshot in `docs/authority/B025/`. The snapshot files remain immutable provenance. `B_FREEZE_REGISTRY.md` and `AUTHORITY_INDEX.md` record the amended current versions.
