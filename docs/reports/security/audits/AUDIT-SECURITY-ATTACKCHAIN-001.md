# AUDIT-SECURITY-ATTACKCHAIN-001 — FINAL REPORT

## AUDIT RESULT
`PASS_WITH_FINDINGS` (PASS does NOT unblock Product Development.)

## AUDIT
`AUDIT-SECURITY-ATTACKCHAIN-001`

## PROVIDER
Devin CLI (Cognition) session runtime

## MODEL
Claude Fable 5.1 High (runtime label as reported by the session system prompt: "You are powered by Claude Fable 5.1 High"). Effort level: not separately exposed beyond the "High" label. No fallback/routing observed. Fresh independent specialist session.

## MODEL REQUIREMENT SATISFIED
YES

## MODE
`READ_ONLY_CROSS_COMPONENT_ATTACKCHAIN_SECURITY_AUDIT`

## AUDITED SHA
`e54584903a353e98ad154d1e8f90f93ed9d7db14`

## HEAD AT END
`e54584903a353e98ad154d1e8f90f93ed9d7db14`

## ORIGIN MAIN
`e54584903a353e98ad154d1e8f90f93ed9d7db14`

## WORKING TREE
CLEAN (`git status --short` empty; `git diff --check` rc 0; branch `main`; 0 stashes)

## REPOSITORY MODIFIED
NO (temporary artifacts only under `/tmp/anox_attackchain_001/`; nothing tracked created, edited or deleted)

## REMOTE MUTATION
NONE (only `git fetch origin`)

---

## PRESERVED EVIDENCE VALIDATION
**PASS** — `python3 tools/audit/validate_security_audit_evidence_preservation.py` → `SECURITY AUDIT EVIDENCE PRESERVATION: PASS`, exit 0 (Project Memory synced to ANOX-EVENT-0048; Attackchain gate recorded as candidate/not executed).

## REPORTS REVIEWED
Complete — all eight preserved reports read in full: `AUDIT-SECURITY-ARCHITECTURE`, `AUDIT-SECURITY-CODEBASE-001`, `AUDIT-SECURITY-CODEBASE-002`, `CODEBASE-SECURITY-CONSENSUS-001`, `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`, `AUDIT-SECURITY-CRYPTO-JNI-001`, `AUDIT-SECURITY-AUTH-DPOP-001`, `AUDIT-SECURITY-ANDROID-STORAGE-001`; plus `AUDIT_EVIDENCE_INDEX.md`, `audit_registry.jsonl`, `audit_traceability.jsonl` (186 records), `evidence_hashes.json`, `reproductions/README.md`. None modified.

**Baseline continuity fact (verified):** `git diff --stat 869b99a..HEAD -- android/src crypto/ .github *.kts gradle` is **empty** — product source at `e545849` is byte-identical to the SHA audited by CODEBASE-001/002 and Consensus; the Crypto/JNI, Auth/DPoP and Android/Storage SHAs differ from HEAD only in docs/tools. Every preserved source-level finding therefore holds at this SHA without re-derivation. Committed `.so` hashes unchanged (`11a958a5…`/`ecf9fdc1…`, stale since `7db20fa`).

## AUTHORITY SOURCES
Complete — `docs/authority/AUTHORITY_INDEX.md` precedence resolved: `SECURITY_INVARIANTS_V1_1` (Inv.1/2/3/18/23/24/25/35) → V1.1/V1.2/V1.3 amendments → Track B (B-002, B-003, B-004, B-005, B-006, B-007, B-013, B-016, B-021). Key current-authority facts used: V1.2 §B-005 `device_auth_keys` has **no UNIQUE(public_key)** (only the `one_active_device_per_account` partial index on `devices(account_id)`); V1.2 §B-005.3 text: "V1 does not allow reusing an old device_id or Device Auth key" (stated, not schema-enforced → GAP-003); `identity_public_keys` "immutable; rotation is a new device/account"; endpoint table `commit`: Auth=PoP, DPoP=Yes, Idempotency=Yes; B-016 "DPoP replay … cannot be process-local"; B-006 OTK ACK by `otk_id`. Historical prompts treated as evidence only.

---

## CURRENT APPLICATION REACHABILITY
`MainActivity` renders a static greeting and constructs nothing; manifest declares no permissions (not even `INTERNET`), one exported launcher activity, `allowBackup=false`, full `dataExtractionRules`. `RegistrationOrchestrator`, `CryptoBridge`, DeviceAuth, DPoP, stores: `DEAD_OR_UNWIRED_TODAY`. `DpopProofVerifier`/`InMemoryDpopReplayCache`: `TEST_ONLY` (server-side semantics). **No attack chain is exploitable from the shipping MainActivity path at this SHA.** The only `CURRENTLY_REACHABLE` chain is the governance/artifact chain AC-012 (stale `.so` packaged in every APK). This does NOT reduce the activation-time severity of any chain below.

## THREAT ACTOR MATRIX

| Actor | Capability | Chains where this is the minimum actor |
|---|---|---|
| A0 remote unauthenticated | network only | none today; AC-003 (if B-004 verifier accepts any key, A0 + stolen token = A1) |
| A1 remote w/ stolen bearer token / captured proof / stolen 30-min grant | possesses a bearer secret, no device key | AC-003 (token), AC-004 (captured proof+token), AC-010 (grant) |
| A2 malicious/compromised anoX client | mints arbitrary proofs with own key; lies about hardware level | AC-002 (amplifier), AC-003 (with ARCH-006), AC-005 (self-rollback — no gain) |
| A3 same-account replayed device | old key/state re-registered | AC-001 variant A (same JKT, new account) |
| A4 app-private state manipulation | write/delete/rollback app files (not Keystore) | AC-001 (malicious variant), AC-005, AC-009, AC-010 stage swap |
| A5 in-process code / internal caller | direct `CryptoNative`, second `getInstance()`, `clearBinding()` | AC-006, AC-011, AC-014 reset abuse |
| A6 rooted/forensic OS | memory + files + Keystore control | AC-015, AC-005 (image restore) |
| A7 build/supply-chain | swaps/stales `.so`, unpinned toolchain | AC-012 (malicious variant; not evidenced) |
| A8 crash/power-loss/FS failure | no intent | **AC-001 (accidental variant), AC-007, AC-009, AC-005 (lost rename = rollback)** |
| A9 honest-but-buggy backend / multi-replica | mis-ported verifier, per-replica state, missing constraints | AC-002, AC-003, AC-004, AC-001 server-half, AC-010 |

## TRUST-BOUNDARY MATRIX

| Boundary | Client assumes | Server must enforce | Current contract | Chain if missing |
|---|---|---|---|---|
| client ↔ registration backend | grant is bearer for one 30-min transaction; commit idempotent; server rejects known key | registration PoP bound to registration_id+grant+nonce+JWK at submit **and** commit; idempotency on (registration_id, jkt); `device_auth_keys.public_key` UNIQUE; JKT→device_id immutable; `identity_public_keys` immutable per device | endpoint-table row only (CANDIDATE-001, GAP-002, GAP-003) | AC-001, AC-009, AC-010 |
| client ↔ auth backend | verifier binds jkt/ath/nonce; shared replay cache | mandatory jkt, mandatory ath, nonce at issuance, shared atomic replay store with monotonic/iat retention, canonical raw-path htu | B-002 prose; verifier defaults null (ROOT-008); no htu rule (ROOT-009/GAP-002) | AC-002, AC-003, AC-004 |
| client ↔ OTK backend | positional keys are stable; publish/ACK exists | otk_id-keyed storage; same otk_id≠key = security error; consumed OTK enforcement; publication epoch | B-006 v1.2 defined server-side; JNI surface lacks KeyId/publish (ROOT-005, CJ-001) | AC-005, AC-007 |
| Android app ↔ Keystore | aliases die with app data; read never creates | n/a (platform) | create-on-read in `RegistrationSessionKey.decrypt` and `initializeMasterKey` (ROOT-006); alias overwrite (CANDIDATE-002) | AC-001, AC-008, AC-011 |
| Kotlin ↔ JNI | handle = live unique object; lock is global | n/a | raw address handles, TOCTOU, per-instance lock, public `CryptoNative` (ROOT-002/003/013/014) | AC-006, AC-007 |
| native source ↔ packaged `.so` | shipped code == reviewed code | n/a (build chain) | no source→artifact gate; `.so` stale (ROOT-001/017/018) | AC-012 |
| local file ↔ local key | envelope authenticates state; presence = truth | n/a | no AAD/epoch (ROOT-011); marker plaintext; absent = first run (ROOT-007); `.bak` auto-restore (AS-CAND-002) | AC-001, AC-005, AC-009 |
| device ↔ account | one device per account; this install ↔ one account | one ACTIVE device per account (present) **and** one account per Device Auth key (absent) | partial unique index only | AC-001 variant A |
| DeviceAuth key ↔ E2EE identity | thumbprint carried through steps; server binds both to device | identity key bound to JKT+device_id at submit-identity/commit; immutable | `submitPublicIdentity(id, grant, material)` has no JKT/PoP (CANDIDATE-001) | AC-010 |

---

## SECURITY ITEM INVENTORY
**TOTAL SECURITY ITEMS CONSIDERED = 68**, derived from canonical evidence (not hard-coded): 18 Consensus Roots · 12 `ANOX-BUILDSC-CANDIDATE` · 6 `ANOX-CRYPTOJNI-CANDIDATE` · 3 `ANOX-AUTHDPOP-CANDIDATE` + 3 `ANOX-AUTHDPOP-GAP` · 2 `ANOX-ANDROIDSTORAGE-CANDIDATE` + 3 `ANOX-ANDROIDSTORAGE-GAP` · 10 `ANOX-SECURITY-ARCH-001..010` · 5 open historical (`ANOX-MAINARCH-013/018/030`, `ANOX-LEGACY-INTEGRATION-005`, `ANOX-LEGACY-B003-001`) · 5 closed-but-partial/ineffective remediations (`ANOX-LEGACY-CRYPTO-005`, `ANOX-LEGACY-INTEGRATION-001/003`, `ANOX-MAINARCH-023/031`) · 1 governance item (`CS-021`/`CODESEC2-C-017` validator lifecycle). Audit-001/002 candidates are covered through their consensus roots (21/21 + 17/17 per Consensus) and not double-counted.

## FINDING PARTICIPATION COVERAGE
```
TOTAL SECURITY ITEMS CONSIDERED = 68

MAPPED_TO_CONFIRMED_CHAIN = 29
MAPPED_TO_POTENTIAL_CHAIN = 6
STANDALONE                = 3
ENABLING_ONLY             = 14
META_ONLY                 = 9
NOT_CHAIN_RELEVANT        = 7

UNMAPPED = 0
```
(29+6+3+14+9+7 = 68.) Per-item dispositions are in the three coverage tables below.

## UNMAPPED
0

---

## ATTACK GRAPH
```
[A8 power loss | A4 file write | A6 restore | user reset]
   └─> marker ABSENT/0x00 (ROOT-007 c2)  ──┐
   └─> session EMPTY/unauth (ROOT-007 c3, ROOT-006 key-manufacture, AS-CAND-002 .bak) ─┤
                                            ├─> canStartNew()=true ──> reserve() ──> createKeyIfAbsent()
   Keystore alias SURVIVED (GAP-003 row) ───┘        │                      ├─ key present  → SAME JKT → new account   [AC-001/A]
                                                     │                      └─ key absent   → NEW key/JKT → new account [AC-001/B]
                                                     └─> server has NO public_key UNIQUE (GAP-003) → old device stays ACTIVE

[A1 stolen token] ─> attacker P-256 key ─> proof (ath optional / jkt unbound, ROOT-008) ─> verifier defaults ─> VALID   [AC-003]
[legit proof for /a%2Fb] ─> decoded htu (ROOT-009) ─> accepted for /a/b even WITH jkt ─> route confusion            [AC-002]
[valid proof+token captured] ─> replica2 / restart / clock rollback (ROOT-008 scope + CAND-003) ─> re-accepted     [AC-004]

[getInstance()×2 (ROOT-002) | CryptoNative direct (A5)] ─> unsynchronised &mut (ROOT-003) ─> destroy→realloc (ROOT-014 masks) ─> stale handle = other object ─> -1 collapse (ROOT-013) ─> wrong recovery [AC-006]
[generate 20 OTK] ─> pickle 5.27 KB > 4096 (ROOT-004) ─> -11 (or -2 on stale .so, ROOT-001) ─> LocalE2eeIdentityStepException ─> "InvalidCiphertext"/Corrupted look ─> denial / destructive-recovery input; if buffer alone raised ─> index enumeration dup/omit (ROOT-005, CJ-001) ─> server OTK set wrong [AC-007]
[old identity/session pickle restored (ROOT-011) | lost rename] ─> OTK re-publish / consumed OTK reuse / ratchet rewind [AC-005]
[wipeLocalCrypto Success (ROOT-012)] ─> DeviceAuth alias + marker + registration file survive ─> device still ACTIVE ─> FirstRun E2EE ─> new identity under old device unless server immutability [AC-008]
[commit Rejected] ─> Failed over CommitArmed while armed (AS-CAND-001) ─> permanent denial ─> only exit clearBinding() ─> feeds AC-001/A [AC-014]
[source fix merged] ─> .so not rebuilt (ROOT-001) ─> CI green (ROOT-017) ─> finding "closed" ─> runtime vulnerable [AC-012]  (already fired: MAINARCH-031)
```

## STATE-MACHINE ATTACK GRAPH
Nodes: `FIRST_RUN`, `RESERVED`, `DEVICE_AUTH_REGISTERED`, `PUBLIC_IDENTITY_UPLOADED`, `COMMIT_ARMED`, `COMMITTED`, `FAILED`, `EXPIRED`, marker `ABSENT`/`ARMED`/`BOUND`/`CLEARED(0x00)`/`CORRUPT`, `KEY_MISSING`, `STATE_MISSING`, `STATE_CORRUPT`, `ROLLED_BACK`, `TERMINAL_KEY_LOSS`, `STUCK_ARMED`.

| From → To | Class | Trigger | Evidence |
|---|---|---|---|
| FIRST_RUN → RESERVED → DEVICE_AUTH_REGISTERED → PUBLIC_IDENTITY_UPLOADED → COMMIT_ARMED(+marker ARMED) → COMMITTED(+marker BOUND) → session cleared | normal | steps 1–4 | harness [16] |
| RESERVED/DAR/PIU → EXPIRED | normal failure | grant TTL, not armed | source `expiredOrNull` |
| any in-progress → (returned) FAILED, durable unchanged | normal failure | `failStep` refuses overwrite | source `:302-310` |
| COMMIT_ARMED → FAILED **persisted** while marker ARMED | **security-relevant unexpected** | `CommitResult.Rejected` direct `save` | harness [23]; AS-CAND-001 |
| STUCK_ARMED + key loss → TERMINAL_KEY_LOSS | fail-closed | | harness [25] |
| BOUND + key loss → TERMINAL_KEY_LOSS; canStartNew=false | fail-closed (control) | | harness [22] |
| BOUND → ABSENT/CLEARED | **security-relevant unexpected** | lost rename (A8), delete (A4), `clearBinding()` (A5), restore | marker harness [M2][M3][M5][M6] |
| COMMITTED(cleared) + marker ABSENT + session STATE_MISSING/EMPTY/STATE_CORRUPT(→synthetic FAILED) → FIRST_RUN semantics → RESERVED (new account) | **fail-open** | AC-001 | harness [17]–[21] |
| key PRESENT + marker ABSENT → `Present` (no cross-check) | fail-open resolver input | | marker harness [M8] |
| BOUND → ARMED(0x02) rollback | still blocks creation; commit cannot resume → denial | | [M4] |
| structural marker corruption → (T,T) | fail-closed | | [M7] |
| any → ROLLED_BACK (older valid envelope accepted) | security-relevant | no AAD/epoch | ROOT-011 (preserved) |

---

## ATTACKCHAIN CANDIDATES

### TOTAL
15

### CRITICAL
0 — (AC-003 carries `CONDITIONAL_CRITICAL_AT_B004_IF_VERIFIER_DEFAULTS_PORTED`; not rated CRITICAL because it requires a specific future backend mistake plus token theft)

### HIGH
4 — `ANOX-ATTACKCHAIN-CANDIDATE-001`, `-003`, `-006`, `-012`

### MEDIUM
7 — `-002`, `-004`, `-005`, `-007`, `-008`, `-010`, `-011`

### LOW
3 — `-009`, `-014`, `-015`

### INFO
1 — `-013`

---

## ATTACKCHAIN TABLE

| Chain | Severity | Confidence | Evidence | Attacker (min) | Activation | Components | Impact | Chain breaker (any one) | Gate |
|---|---|---|---|---|---|---|---|---|---|
| AC-001 Local state loss → re-registration / one key, two accounts | HIGH | HIGH | E2 | A8 (accidental) / A4 | B004 | ROOT-007, ROOT-006, AD-GAP-003, ROOT-011(marker), AS-CAND-002, AS-GAP-001/003, ARCH-003/007 | FAIL_OPEN_SECURITY + STATE_DIVERGENCE (Inv.2/23 lifecycle; key→device ambiguity) | server `public_key` UNIQUE (variant A); first-run resolver cross-check (A+B); marker+session durability | PRE-B004 |
| AC-002 htu collision × unbound verifier | MEDIUM | HIGH | E2 | A2/A9 | B004 | ROOT-009, ROOT-008, AD-GAP-002 | FAIL_OPEN (route confusion) / FAIL_CLOSED interop | canonical raw-path htu contract | PRE-B004 contract |
| AC-003 Stolen bearer + optional ath/jkt | HIGH (cond. CRITICAL) | HIGH | E2 | A1 + A9 | B004 | ROOT-008, AD-GAP-002, AD-GAP-001, ARCH-006 | FAIL_OPEN_SECURITY (full impersonation for token TTL) | **mandatory jkt binding** (ath alone does NOT break it — harness [5]) | PRE-B004 contract + B004 impl |
| AC-004 Replay across replicas/restart/rollback | MEDIUM | HIGH | E2 | A1 (captured proof+token) / A9 | B004 backend | ROOT-008 scope, AD-CAND-003, AD-GAP-002, AD-GAP-001, B-016 | FAIL_OPEN (bounded re-execution of same method+URI, body unbound) | shared atomic replay store + iat/monotonic retention; nonce | PRE-B004 contract |
| AC-005 OTK/session rollback + enumeration duplicates | MEDIUM | HIGH | E1 (+E2 preserved components) | A4/A6/A8 | B006/B008 | ROOT-011, ROOT-005, CJ-CAND-001, CJ-CAND-002, ROOT-004 | CONFIDENTIALITY (message-key reuse at B008) + INTEGRITY (one-time property) + STATE_DIVERGENCE | server OTK/publication epoch + consumed-OTK enforcement; AAD/type/epoch; KeyId surface | B006/B008 |
| AC-006 JNI stale handle / wrong object / error collapse → wrong recovery | HIGH | HIGH | E1 (+E2 preserved 7/100 reuse) | A5 or none (multi-thread B008) | B004 (multi-instance) / B008 (concurrency) | ROOT-002, ROOT-003, ROOT-013, ROOT-014, CJ-CAND-003, ROOT-006(crypto), ARCH-001, LEGACY-INTEGRATION-005 | INTEGRITY + CONFIDENTIALITY (UB, key reuse, wrong identity) + FALSE destructive recovery | slot+generation handles with owning lock; typed HANDLE_*/version errors + consumer | PRE-B004 |
| AC-007 4096 + default OTK count → deterministic failure misreported | MEDIUM | VERY_HIGH | E2 (preserved measurements; source unchanged) | none (A8-class reliability) | B004 | ROOT-004, ROOT-005, CJ-CAND-001, CJ-CAND-004, ROOT-013/CJ-CAND-003, ROOT-001(-2), ROOT-014 | FAIL_CLOSED_DENIAL + STATE_DIVERGENCE (leaked OTK material; if buffer raised alone → duplicate upload) | dynamic native-allocated output + KeyId OTK surface, together | PRE-B004 |
| AC-008 Partial wipe leaves authenticatable device | MEDIUM | HIGH | E1 | none (user action) / A8 | B013 (+B006) | ROOT-012, AS-GAP-002, ROOT-006(master alias), ARCH-009, MAINARCH-030, MAINARCH-023 | INTEGRITY/lifecycle (device ACTIVE, FirstRun E2EE → silent identity replacement unless server immutability) + false "wiped" UX | cross-domain wipe (marker last, truthful) + server `identity_public_keys` immutability | B013 / Final |
| AC-009 AtomicFile swallowed rename / `.bak` → step replay same grant | LOW | HIGH | E2 (preserved) | A8/A4 | B004 | AS-CAND-002, ROOT-007, AD-GAP-002 | STATE_DIVERGENCE bounded by idempotency + grant TTL | check rename result; forbid `.bak` restore; idempotency on (registration_id, jkt) | PRE-B004 |
| AC-010 Registration transaction hijack (bearer grant, no PoP at submit-identity/commit, stage key swap) | MEDIUM | MEDIUM | E1/E2 (wire shape [26][27]) | A1 (stolen grant) / A9 | B004 | AD-CAND-001, AD-CAND-002, AD-GAP-003, ROOT-011(reg), ARCH-003, LEGACY-INTEGRATION-001 | INTEGRITY (attacker E2EE identity bound to victim device) / denial | typed PoP at submit-identity and commit binding JWK+registration_id+grant+nonce; identity↔JKT binding | PRE-B004 contract |
| AC-011 Multi-instance security-domain split | MEDIUM | HIGH | E1 | A5 / none (wiring) | B004 | ROOT-002, AD-CAND-002, ROOT-006(creation race), per-instance `@Synchronized`, ROOT-008 per-instance | STATE_DIVERGENCE feeding AC-001 (unauthenticable envelope) and AC-006 | process-wide singletons + serialized key creation + alias-existence check | PRE-B004 |
| AC-012 Build false closure | HIGH | VERY_HIGH | E2 (preserved; fired: MAINARCH-031) | none / A7 | CURRENTLY_REACHABLE | ROOT-001, ROOT-017, ROOT-018, BUILDSC-001/002/003/006/008, ARCH-002, MAINARCH-013/031, LEGACY-CRYPTO-005 | FALSE_CLOSURE (`SECURITY_FIX_DECLARED_CLOSED_WHILE_RUNTIME_REMAINS_VULNERABLE`) | CI native cross-build + in-run hash gate + instrumented JNI on provenance-verified `.so` | PRE-B004 |
| AC-013 Physical evidence vacuum | INFO | HIGH | E0 (by definition) | none | FINAL/PHYSICAL | ROOT-017, MAINARCH-018, ARCH-006, AS-GAP-003, BUILDSC-002 | FALSE_CLOSURE risk (Keystore-survival/StrongBox assumptions unproven) | physical campaign P1–P14 on provenance-verified binary | FINAL |
| AC-014 Armed-latch denial → forced reset → AC-001 | LOW | HIGH | E2 | none (server Rejected) | B004 | AS-CAND-001, AS-GAP-001, AD-GAP-002, LEGACY-INTEGRATION-003 | FAIL_CLOSED_DENIAL; enabler of AC-001/A via `clearBinding()` | rejection-class contract + `RejectedAfterArm` state + reset path clearing marker last | PRE-B004 contract |
| AC-015 Secret residency | LOW | HIGH | E1 | A6/A5 | B004 volume / B008 | ROOT-010, CJ-CAND-005, ROOT-014, CS-019 abort | CONFIDENTIALITY only with memory disclosure | best-effort zeroization + handle lifetime cleanup (after CJ-A) | B008/B009 |

---

## CHAIN DETAILS

### ANOX-ATTACKCHAIN-CANDIDATE-001
**TITLE:** Local security-state loss/mismatch permits a second registration while the previous server device remains ACTIVE (same key → two accounts, or new key → orphaned account)
**CHAIN_SEVERITY:** HIGH (`COMPONENT_FINDING_SEVERITY`: ROOT-007 MEDIUM, ROOT-006 MEDIUM, GAP-003 contract) · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E2 (this audit: orchestrator+marker harness [16]–[22], [M2][M3][M5][M6][M8]; preserved: empty-file→NotStarted, AtomicFile, create-on-read)
**ATTACKER_CLASS:** A8 minimum (no attacker: power loss during arming or session write); A4 malicious variant; A6 restore variant; A3 outcome.
**CURRENT_REACHABILITY:** DEAD_OR_UNWIRED_TODAY · **ACTIVATION_GATE:** ACTIVATES_AT_B004
**ENTRY_CONDITION:** marker `ABSENT`/`0x00`/v1-garbage **and** session file absent/empty/unauthenticable (or `Failed`), after a commit that may have succeeded server-side.
**PREREQUISITES:** (a) any of: lost `rename()` (no dir fsync), `AtomicFile.finishWrite` swallowed failure, app-UID delete, `clearBinding()` call, restore/`pm clear`-partial; (b) session downgrade: empty file → `NotStarted`, or key missing → `decrypt()` mints new key → unauthenticable → synthetic `Failed`; (c) server lacks `device_auth_keys.public_key` UNIQUE / known-key rejection.
**COMPONENT_FINDINGS:** ROOT-007 (c1–c7), ROOT-006, ROOT-011 (marker/registration slice), AS-CAND-002, ARCH-003, ARCH-007, ARCH-004 (schema authority drift), MAINARCH-018 (Keystore survival unproven).
**ARCHITECTURE_GAPS:** AD-GAP-003 (CHAIN_CRITICAL), AS-GAP-001 (CHAIN_CRITICAL), AS-GAP-003 (CHAIN_RELEVANT).
**STATE TRANSITIONS:** `COMMITTED(cleared)+BOUND` → [loss] → `marker ABSENT` + `session NotStarted/Failed` → `canStartNew=true` [17] → `reserve` → `registerDeviceAuth` → **variant A** key survived: `status()=Present` (no cross-check, [M8]) → same JKT submitted for a **new** account [18][19]; **variant B** key gone: `AbsentNotBound` → new key generated [20][21].
**FINAL IMPACT:** Variant A: one Device Auth public key bound to two `device_id`s in two accounts → V1.2 §2 `AuthenticatedDeviceContext.device_id` "bound to the validated Device Auth key" becomes **ambiguous** (authorization identity derivation non-unique) — violates V1.2 §B-005.3 "does not allow reusing … Device Auth key". Variant B: old account stays ACTIVE with an unreachable device (no revocation path), user silently on a new account; consistent with no-recovery but not with truthful lifecycle. Both: `one_active_device_per_account` does **not** block (different accounts).
**CURRENT MITIGATIONS:** marker `ARMED`/`BOUND` present ⇒ `TerminalKeyLoss` [22]; structural marker corruption fails closed [M7]; `failStep` never downgrades in-progress state; grant TTL irrelevant (new reservation).
**FUTURE_SERVER_MITIGATIONS:** `UNIQUE(device_auth_keys.public_key)` global; reject `submit-device-auth` with a JWK already bound to an ACTIVE device; JKT→device_id immutable — terminates **variant A only** (converts it to FAIL_CLOSED_DENIAL needing a reset path). Variant B is indistinguishable server-side from a legitimate new device → remains a local lifecycle failure.
**CHAIN BREAKPOINTS:** breaks if ANY ONE of: (1) server `public_key` UNIQUE + known-key rejection [variant A]; (2) client first-run resolver: marker absent ∧ any anoX Keystore alias present ⇒ NOT first run ⇒ fail closed (explicit reset only) [A+B]; (3) marker integrity (HMAC alias; "HMAC key missing ⇒ bound") + dir fsync + `AtomicFile` replacement + empty-file ⇒ security exception + existing-only `decrypt` with `KEY_MISSING` treated as not-first-run [A+B, accidental variant]. Defense-in-depth available: (1)+(2)+(3) are independent. **Not** SINGLE_POINT.
**MUST_FIX_TOGETHER:** ROOT-006 ∧ ROOT-007 (all components) ∧ consumer semantics (`currentState`/`canStartNew`) ∧ AD-GAP-003 server contract ∧ AS-GAP-001 contract. `CROSS_GROUP_FIX_DEPENDENCY`: AS-A/AS-B ↔ AD-E/AD-F.
**FIX GROUPS:** AS-A, AS-B, AS-D (marker slice), AD-E, AD-F.
**REQUIRED_TEST:** JVM: delete marker + keep DeviceAuth alias (fake) + old server device ACTIVE (synthetic backend with public_key uniqueness) ⇒ `reserve()`/`registerDeviceAuth()` rejected locally (resolver) **and** server-side; instrumented: `pm clear`-partial simulation; physical P4/P5/P13.
**INDEPENDENT_RETEST_OWNER:** Android/Storage + Auth/DPoP + Attackchain (cross-domain).
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-002
**TITLE:** Decoded-path `htu` collision × unbound verifier default → proof intended for one route validates for another
**CHAIN_SEVERITY:** MEDIUM · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E2 (harness [1]–[3])
**ATTACKER_CLASS:** A9 (server routes distinguish `%2F`) with A2/A1 proof source; **note:** harness [1] proves the collision survives jkt binding — a *legitimate device's* proof for `/v1/a%2Fb` is `VALID` for `/v1/a/b`; attacker key adds nothing once ROOT-008 is present [2] and is rejected once jkt is bound [3].
**CURRENT_REACHABILITY:** TEST_ONLY/UNWIRED · **ACTIVATION_GATE:** B004 (server verifier)
**ENTRY_CONDITION:** server verifier compares against decoded path (ports current `DpopHtu`) and exposes two routes that differ only under percent-decoding.
**PREREQUISITES:** verifier mirrors `URI.getPath()`; a proof (captured or self-minted) for the colliding route; V1 endpoint inventory has fixed paths with UUID params, so a real collision additionally requires a router that decodes before matching — realistic-but-specific.
**COMPONENT_FINDINGS:** ROOT-009, ROOT-008. **GAPS:** AD-GAP-002 (canonical htu rule absent — CHAIN_CRITICAL for this chain).
**FINAL IMPACT:** FAIL_OPEN cross-endpoint proof reuse (bounded to same method + iat window + jti); with ROOT-008 defaults the impact collapses into AC-003. Interop fail-closed rows (`:443`, `..`, `//`) are availability, not bypass.
**CURRENT MITIGATIONS:** signature, htm, iat ±120 s, jti replay (per instance).
**FUTURE_SERVER_MITIGATIONS:** compare `lower(scheme)://lower(host)[:non-default port]rawPath` (RFC 3986 §6.2.2 only), no userinfo; router matches raw path.
**CHAIN BREAKPOINTS:** canonical raw-path htu contract frozen and applied on both sides in lock-step (**SINGLE_POINT_OF_SECURITY_FAILURE** for the route-confusion property; jkt binding does not help).
**MUST_FIX_TOGETHER:** ROOT-009 ∧ AD-GAP-002 (client `DpopHtu` + server rule + `DpopHtuTest` collision rows).
**FIX GROUPS:** AD-C (+AD-B).
**REQUIRED_TEST:** proof for `/v1/a%2Fb` rejected for `/v1/a/b` (and vice-versa) with and without jkt; `%3F/%23/%00/%2520` rows; default-port and trailing-slash interop rows.
**INDEPENDENT_RETEST_OWNER:** Auth/DPoP.
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-003
**TITLE:** Stolen bearer token + optional `ath` + optional `jkt` → attacker-generated proof accepted (DPoP nullified)
**CHAIN_SEVERITY:** HIGH, `CONDITIONAL_CRITICAL_AT_B004_IF_VERIFIER_DEFAULTS_PORTED` · **CONFIDENCE:** HIGH (mechanics) / MEDIUM (likelihood of the backend mistake) · **EVIDENCE_LEVEL:** E2 (harness [4]–[7])
**ATTACKER_CLASS:** A1 (token) + A9 (verifier with defaults). ARCH-006 lets an A2 software-key client pass eligibility self-report — no attestation to stop the attacker key.
**CURRENT_REACHABILITY:** TEST_ONLY · **ACTIVATION_GATE:** B004
**ENTRY_CONDITION:** B-004 verifier ports/mirrors `DpopProofVerifier.verify(proof, method, uri)` with `expectedJwkThumbprint=null` (and/or `accessToken=null`); `DpopProofFactory.createProof(m,u)` mirrors the omission client-side.
**PREREQUISITES:** token theft (15-min TTL, memory-only, SHA-256 stored server-side; exposure via compromised client/log/edge) **and** the default-argument mistake. Fresh nonce absent (GAP-001) removes the one server-controlled freshness input.
**COMPONENT_FINDINGS:** ROOT-008 (jkt/ath optional, factory mirror), ARCH-006. **GAPS:** AD-GAP-002 (mandatory bindings unspecified — CHAIN_CRITICAL), AD-GAP-001 (nonce — CHAIN_RELEVANT).
**STATE TRANSITIONS:** attacker P-256 key → proof (with or without `ath`) → signature verifies against embedded jwk → step 9 skipped → `Valid` [4]; **making `ath` mandatory alone does not help**: attacker computes `ath` for the stolen token → `Valid` [5]; only expected-jkt rejects [6]; `ath` mandatory only blocks a proof that omits it [7].
**FINAL IMPACT:** FAIL_OPEN_SECURITY — full account impersonation for token lifetime; `/v1/auth/token` re-issuance also passes under the same defaults → effectively unbounded. Blast radius per victim token.
**CURRENT MITIGATIONS:** none in the verifier by default; only KDoc prose; iat window; per-instance replay (irrelevant to a fresh attacker proof).
**FUTURE_SERVER_MITIGATIONS:** jkt derived from `device_auth_keys` bound to the token/session and **required**; `ath` required whenever a token is presented; nonce at issuance; `AuthenticatedDeviceContext` from validated key only.
**CHAIN BREAKPOINTS:** **mandatory jkt binding is the single control that terminates this chain** (`SINGLE_POINT_OF_SECURITY_FAILURE`); `ath` is necessary for token binding but insufficient alone; a safe-by-construction API (non-null `DpopBinding(jkt, tokenHash?, nonce?)`) prevents the omission by type.
**MUST_FIX_TOGETHER:** ROOT-008 ∧ all B-004 call sites ∧ AD-GAP-002 ∧ AD-GAP-001 (nonce state). MUST_NOT_FIX_ALONE: passing jkt at one site while defaults remain.
**FIX GROUPS:** AD-B, AD-D, AD-F(server derivation).
**REQUIRED_TEST:** attacker-key proof with correct `ath` for a valid token ⇒ `KEY_BINDING_MISMATCH` on every token-bearing endpoint; compile-time test that `verify` cannot be invoked without a binding; synthetic backend conformance suite.
**INDEPENDENT_RETEST_OWNER:** Auth/DPoP + backend security retest.
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-004
**TITLE:** Replay across per-instance caches, replicas, process restart and wall-clock rollback
**CHAIN_SEVERITY:** MEDIUM · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E2 (harness [8]–[15])
**ATTACKER_CLASS:** A1 (captured full request: proof + token) / A9 (replicas, restart, clock).
**CURRENT_REACHABILITY:** TEST_ONLY · **ACTIVATION_GATE:** B004 backend (only if this design is ported; B-016 already forbids process-local replay state).
**ENTRY_CONDITION:** replay cache not shared **or** shared but wall-clock retention.
**PREREQUISITES:** variants are independent — (i) two replicas [10]; (ii) restart [11]; (iii) clock rollback ≥ 60 s after eviction [15]; each alone suffices. Attacker must hold a proof still inside the ±120 s iat window (except rollback, which re-opens the window).
**COMPONENT_FINDINGS:** ROOT-008 (scope), AD-CAND-003 (time source). **GAPS:** AD-GAP-002 (replay key/TTL/source), AD-GAP-001 (nonce would add server freshness).
**FINAL IMPACT:** FAIL_OPEN bounded re-execution of the same method+URI; DPoP does not bind the body, so a replayed proof+token can carry a different body to the same endpoint (idempotency keys mitigate mutating endpoints only when the attacker cannot choose a fresh key — they can). Not credential theft.
**CURRENT MITIGATIONS:** shared cache with two verifiers rejects [12][13] (proves the fix works); atomic `recordIfAbsent` per instance; iat window.
**FUTURE_SERVER_MITIGATIONS:** shared atomic store keyed `(jkt, jti)`, TTL ≥ 300 s from **iat** (or monotonic source), bounded per key; server nonce.
**CHAIN BREAKPOINTS:** shared store ∧ iat/monotonic retention (fixing scope alone re-enables the rollback variant — MUST_NOT_FIX_ALONE).
**FIX GROUPS:** AD-D.
**REQUIRED_TEST:** two-verifier shared-store reject; restart persistence; rollback −250 s rejected; per-key bound.
**INDEPENDENT_RETEST_OWNER:** backend security retest (Auth/DPoP for contract).
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-005
**TITLE:** Protected-state rollback × OTK lifecycle → OTK re-publication, consumed-OTK reuse, ratchet rewind
**CHAIN_SEVERITY:** MEDIUM (HIGH at B008 if no server epoch) · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E1 (source at this SHA) + E2 preserved components (rollback acceptance, enumeration dup 20/20, stored/unpublished divergence, session 8–29.9 KB)
**ATTACKER_CLASS:** A4/A6 (older valid `anox_identity.enc`/`anox_session.enc` written back); A8 variant: lost `rename()` after `saveIdentity`/`saveSession` **is** a rollback to the previous version; CJ-CAND-002 variant: `saveSession` fails (>4096) after a successful decrypt → unpersisted ratchet advance → same effect on reload.
**CURRENT_REACHABILITY:** UNWIRED · **ACTIVATION_GATE:** B006 (publication) / B008-B009 (messaging)
**COMPONENT_FINDINGS:** ROOT-011, ROOT-005, CJ-CAND-001, CJ-CAND-002, ROOT-004, ROOT-007(c1 lost rename), MAINARCH-023 (adjacent). **GAPS:** AS-GAP-003 (server as rollback authority not frozen).
**STATE TRANSITIONS:** identity pickle N (OTKs published, marked — once export exists) → rollback to pickle N-1 → unpublished set reappears → re-publication of already-published publics (duplicate `otk_id`/same key = idempotent-OK, but a *consumed* OTK's private half is back → second inbound session on a "one-time" key) → **and** with ROOT-005 index enumeration the re-upload set is itself nondeterministic (dup/omit) → server/client divergence. Session rollback → chain index reused → message-key reuse.
**FINAL IMPACT:** INTEGRITY (one-time property broken; server bookkeeping divergent) at B006; CONFIDENTIALITY (Olm message-key reuse) at B008. No new grant/credential exposure.
**CURRENT MITIGATIONS:** AEAD stops tampering (not rollback); backup exclusion; server `CLAIMED` is terminal (B-006) — blocks server-side re-claim but not client-side re-acceptance of an inbound PreKey for a rolled-back OTK.
**FUTURE_SERVER_MITIGATIONS:** OTK/publication epoch; `otk_id` keyed idempotent publication; consumed-OTK enforcement; identity_revision monotonic.
**CHAIN BREAKPOINTS:** ANY ONE of: server publication/consumption epoch echoed into local AAD (AS-D + CJ-C); local envelope generation counter anchored to a trusted source (none available on Android alone — insufficient alone); durable writes (dir fsync) + dynamic buffers remove the *accidental* rollback variants.
**MUST_FIX_TOGETHER:** ROOT-011 ∧ freshness source ∧ server authority; ROOT-004 ∧ ROOT-005 ∧ CJ-CAND-001. `CROSS_GROUP_FIX_DEPENDENCY`: CJ-C/CJ-D ↔ AS-D ↔ B-006 server.
**FIX GROUPS:** CJ-C, CJ-D, AS-D, AS-B (durability).
**REQUIRED_TEST:** old valid identity envelope rejected after a newer epoch was persisted; publish→ACK→mark→rollback→re-publish attempt rejected by synthetic server; session rollback detection.
**INDEPENDENT_RETEST_OWNER:** Crypto/JNI + Android/Storage.
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-006
**TITLE:** JNI false state — stale/reused handle, aliased `&mut`, error collapse → wrong-object crypto and incorrect recovery
**CHAIN_SEVERITY:** HIGH · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E1 (source at this SHA; `lib.rs:44-49→209`, `CryptoBridge.kt:38-44,580`) + E2 preserved (7/100 same-size-class address reuse; deserialize −9→0)
**ATTACKER_CLASS:** A5 (any second component calling `getInstance()` or `CryptoNative` directly) or **none** (a multi-threaded B-008 pipeline).
**CURRENT_REACHABILITY:** UNWIRED · **ACTIVATION_GATE:** B004 (multi-instance: `RegistrationOrchestrator` + any status/UI caller each get a distinct bridge) / B008 (true concurrency)
**COMPONENT_FINDINGS:** ROOT-002, ROOT-003, ROOT-013, ROOT-014, CJ-CAND-003, CJ-CAND-006, ROOT-006 (split-brain K_STATE in `serialize*`), ARCH-001, ARCH-008, LEGACY-INTEGRATION-005.
**STATE TRANSITIONS:** variant A (Sequence A/C): bridge B1/B2 with locks L1/L2 → T1 `generateOneTimeKeys(h)` ∥ T2 `saveIdentity(h)` → aliased `&mut`/`&` → torn pickle or UB; or `destroy(h1)` → realloc → `h2==h1` → `createInboundSession(h1)` consumes identity-2's OTK / `destroy(h1)` frees identity-2 under another caller; stale use returns `-1 InvalidInput` (ROOT-013) → caller retries with the stale handle. **ROOT-014 leaks currently mask this**: fixing the leak first activates it. Variant B (error collapse): `cryptoDeserialize*` returns `0` for `UnsupportedVersion`/wrong key/tamper → `CorruptedIdentityState` → a future recovery handler wipes/regenerates → **fail-open destructive recovery** (Inv.23).
**FINAL IMPACT:** INTEGRITY + CONFIDENTIALITY (wrong identity/session, message-key reuse), AVAILABILITY (abort), FALSE state to the lifecycle layer.
**CURRENT MITIGATIONS:** separate type registries (type confusion blocked); leaks mask reuse; single caller today.
**CHAIN BREAKPOINTS:** slot+generation handles with owning `Arc<Mutex<T>>` (check+use in one scope) **and** disjoint `HANDLE_*`/`UNSUPPORTED_VERSION` codes consumed by `LocalStateStatus`; singleton alone is insufficient (bypass via `CryptoNative`).
**MUST_FIX_TOGETHER:** ROOT-003 ∧ ROOT-014 ∧ ROOT-013 ∧ ROOT-002; CJ-CAND-003 ∧ ROOT-013 ∧ ROOT-006 consumer. MUST_NOT_FIX_ALONE: leak cleanup first; Kotlin singleton alone.
**FIX GROUPS:** CJ-A, CJ-B, CJ-E (cleanup last), AS-C (consumer).
**REQUIRED_TEST:** instrumented (provenance-verified `.so`): stale handle after destroy+realloc ⇒ `HANDLE_STALE_GENERATION`; concurrent encrypt/serialize on one handle serialized; version bump ⇒ `UNSUPPORTED_VERSION` not `Corrupted`.
**INDEPENDENT_RETEST_OWNER:** Crypto/JNI (+Android/Storage for consumer).
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-007
**TITLE:** 4096-byte buffer × default 20 OTKs × stale `.so` → deterministic registration failure that looks like tampering; buffer-only fix → duplicate/omitted OTK upload
**CHAIN_SEVERITY:** MEDIUM (component ROOT-004 HIGH not inherited: end impact is denial + divergence, not bypass) · **CONFIDENCE:** VERY_HIGH · **EVIDENCE_LEVEL:** E2 (preserved: 20 OTK = 5269–5287 B; 20/20 sweeps duplicated; `-2` in shipped binary by disassembly; source byte-identical at this SHA)
**ATTACKER_CLASS:** none (reliability, A8-class).
**CURRENT_REACHABILITY:** UNWIRED (default path) · **ACTIVATION_GATE:** B004 step 3
**COMPONENT_FINDINGS:** ROOT-004, ROOT-005, CJ-CAND-001, CJ-CAND-004, ROOT-013/CJ-CAND-003, ROOT-001 (runtime `-2 InvalidCiphertext`), ROOT-014 (leaked handle with 20 private OTKs), LEGACY-INTEGRATION-002 (ordering correct but blocked).
**STATE TRANSITIONS:** `uploadPublicIdentity` → `ensurePublicIdentityMaterial(20)` → generate → `saveIdentity` → >4096 → `-11` (source) / `-2` (shipped) → `LocalE2eeIdentityStepException("InvalidCiphertext")` → `failStep` (durable state preserved) → retry regenerates + leaks again. If only the constant is raised: `oneTimeKeysCount` (stored) vs index over *unpublished* set → ~6–10 duplicates, ~6–10 omitted → server stores duplicates or dedups; after any publish, count/set diverge → `-3 InvalidSession`.
**FINAL IMPACT:** FAIL_CLOSED_DENIAL (B-004 cannot complete at defaults) + STATE_DIVERGENCE + misleading "corruption" signal into the same recovery path as AC-006/B. Not fail-open.
**CURRENT MITIGATIONS:** identity persisted before OTKs returned; `failStep` preserves state.
**CHAIN BREAKPOINTS:** dynamic native-allocated output **together with** KeyId-ordered OTK export + `created/removed` handling; constant increase alone is a false closure.
**FIX GROUPS:** CJ-C, CJ-D, CJ-G; ROOT-001 first so the retest is meaningful.
**REQUIRED_TEST:** instrumented default-count registration step succeeds; uploaded set = exactly `created` KeyIds, unique; count semantics equal after publish.
**INDEPENDENT_RETEST_OWNER:** Crypto/JNI.
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-008
**TITLE:** Partial "wipe" leaves an authenticatable device and an E2EE first-run → false wiped UX / silent identity replacement risk
**CHAIN_SEVERITY:** MEDIUM · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E1 (source `CryptoBridge.kt:737-754`, no orchestrator; `getLocalStateStatus` → `FirstRun` after wipe; `createAndPersistFirstIdentity` on FirstRun)
**ATTACKER_CLASS:** none (user-initiated wipe/account-delete) / A8.
**CURRENT_REACHABILITY:** UNWIRED · **ACTIVATION_GATE:** B013 (wipe/logout/delete) + B006 (identity publication)
**COMPONENT_FINDINGS:** ROOT-012, ROOT-006 (master alias recreated on next `getInstance()`), ARCH-009, MAINARCH-030, MAINARCH-023 (adjacent). **GAPS:** AS-GAP-002 (CHAIN_RELEVANT).
**STATE TRANSITIONS:** `wipeLocalCrypto()` → master alias deleted (crypto erasure ✓) → three `delete()` results ignored → `Success` → DeviceAuth alias, marker `BOUND`, registration file, `anox.b003.session.v1`, `.tmp` all survive → device still ACTIVE server-side and can still sign DPoP → E2EE state now `FirstRun` → any later identity step creates a **new** E2EE identity under the old device unless the server enforces `identity_public_keys` immutability; if identity deleted but K_STATE file survives → `WipedState` denial; master alias silently recreated → `MissingKeystore` label hides that a replacement wrapping key exists.
**FINAL IMPACT:** INTEGRITY/lifecycle: user believes wiped, device remains authenticatable; potential NO-RECOVERY violation (silent identity replacement inside the same account) if server immutability is not enforced; confidentiality preserved (key-first ordering). Account-delete UX may misreport.
**CURRENT MITIGATIONS:** key-first ordering; V1.2 `identity_public_keys` "immutable" (contract, not implemented).
**CHAIN BREAKPOINTS:** ANY ONE of: cross-domain wipe orchestrator with per-item truthful results and marker-last ordering + all three aliases; server rejects a second identity publication for an existing device (immutability) — the latter breaks only the identity-replacement leg, not the false-UX leg.
**FIX GROUPS:** AS-E, AS-C, AD-F (server binding).
**REQUIRED_TEST:** wipe enumerates 5 domains + residue + 3 aliases; partial failure reported; after wipe `status()`=`AbsentNotBound` and server device revoked; synthetic server rejects new identity for existing device.
**INDEPENDENT_RETEST_OWNER:** Android/Storage (+Architecture for B-013 contract).
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-009
**TITLE:** `AtomicFile` swallowed rename / stale `.bak` auto-restore → registration step replay with the same grant
**CHAIN_SEVERITY:** LOW · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E2 (preserved harness on `core:1.12.0`)
**ATTACKER_CLASS:** A8 / A4 (planted `.bak`).
**ACTIVATION_GATE:** B004 · **COMPONENT_FINDINGS:** AS-CAND-002, ROOT-007 (c1, c4, c6), AD-CAND-001 (no PoP at commit). **GAPS:** AD-GAP-002 (idempotency on `(registration_id, jkt)`).
**STATE TRANSITIONS:** `save(CommitArmed)` returns although base still holds `PublicIdentityUploaded` → `markArmed` durable → remote commit → crash → resume from `PublicIdentityUploaded` → `commit()` again (same grant) → server must be idempotent; `.bak` with `Reserved` planted → next `load()` returns it → `registerDeviceAuth()` re-submits the same JWK.
**FINAL IMPACT:** STATE_DIVERGENCE bounded by server idempotency and 30-min grant TTL; no new grant exposure; server idempotency *prevents duplicate effects* but does **not** break the divergence itself — only truthful local durability does.
**CHAIN BREAKPOINTS:** check `finishWrite`/rename result (throw); never restore `.bak`; dir fsync; server idempotency on `(registration_id, jkt)` for `submit-device-auth` and commit.
**FIX GROUPS:** AS-B, AD-F.
**REQUIRED_TEST:** real-class temp-dir: rename failure throws; planted `.bak` ignored/deleted; `kill -9` matrix (P12).
**INDEPENDENT_RETEST_OWNER:** Android/Storage.
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-010
**TITLE:** Registration transaction hijack — bearer grant with no PoP at submit-identity/commit, untyped registration proof, stage key swap
**CHAIN_SEVERITY:** MEDIUM · **CONFIDENCE:** MEDIUM (server contract undefined) · **EVIDENCE_LEVEL:** E1 + E2 for wire shape (harness [26][27]: proof is an opaque string not bound to JWK/grant; `commitRegistration(id, grant)` carries no PoP/DPoP/Idempotency; `submitPublicIdentity(id, grant, material)` carries no JKT/PoP)
**ATTACKER_CLASS:** A1 holding the 30-min registration grant (theft via compromised client/edge; TLS assumed intact) / A9.
**ACTIVATION_GATE:** B004 · **COMPONENT_FINDINGS:** AD-CAND-001, AD-CAND-002, ROOT-011 (registration rollback to `Reserved`), ARCH-003, LEGACY-INTEGRATION-001 (commit PoP absence persists). **GAPS:** AD-GAP-003, AD-GAP-002, AD-GAP-001.
**STATE TRANSITIONS:** (i) grant holder calls `submitPublicIdentity(registration_id, grant, attackerMaterial)` after the victim's `registerDeviceAuth` → server binds attacker E2EE identity to victim's Device Auth key/device → victim's contacts encrypt to the attacker; (ii) grant holder calls `commit` first → victim's `commit()` idempotent retry; (iii) stage swap: state rolled back to `Reserved` (A4) + alias overwritten (AD-CAND-002) → second `submit-device-auth` with JWK₂ for the same `registration_id` → server behaviour undefined (last-write? reject?). Local `validateDeviceAuthForCommit` blocks *in-state* thumbprint drift but not (i)/(ii) and not a rolled-back state without a thumbprint.
**FINAL IMPACT:** INTEGRITY — DeviceAuth↔E2EE binding controlled by whoever holds the grant; server-side binding contract "exists only as an endpoint-table row".
**CURRENT MITIGATIONS:** grant 256-bit, TTL 30 min, sealed at rest, redacted; thumbprint revalidation at commit (local); `one_active_device` index.
**CHAIN BREAKPOINTS:** typed PoP signed by the Device Auth key over `registration_id‖grant-hash‖nonce‖JWK‖identity-material-hash` at `submit-device-auth`, `submit-public-identity` **and** `commit`; server compares JWK-in-proof == submitted JWK; idempotency on `(registration_id, jkt)`; reject a second JWK for a `registration_id`.
**MUST_FIX_TOGETHER:** AD-CAND-001 ∧ AD-GAP-003 ∧ AD-GAP-001; AD-CAND-002 ∧ AD-A.
**FIX GROUPS:** AD-F, AD-B, AD-A.
**REQUIRED_TEST:** synthetic backend rejects `submit-public-identity` without PoP from the registered JKT; rejects second JWK per registration_id; commit without PoP rejected.
**INDEPENDENT_RETEST_OWNER:** Auth/DPoP + Architecture.
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-011
**TITLE:** Multiple object instances → multiple security domains that were designed as one (singleton pattern)
**CHAIN_SEVERITY:** MEDIUM · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E1 (source: `CryptoBridge.getInstance` never assigns; `RegistrationSessionKey`/`FileRegistrationSessionStore`/`FileDeviceAuthBindingStore`/`AndroidKeystoreDeviceAuthKeyManager` public constructors, per-instance `@Synchronized`; `InMemoryDpopReplayCache` per verifier)
**ATTACKER_CLASS:** A5 or none (two wiring paths).
**ACTIVATION_GATE:** B004 · **COMPONENT_FINDINGS:** ROOT-002, AD-CAND-002, ROOT-006 (creation race/alias overwrite), ROOT-008 (per-instance cache), Audit-002 C-014 (via ROOT-002).
**Assessment (§43):** **one architecture pattern, multiple roots** — the shared pattern is "instance-local lock/cache/creation for a process-global invariant", but the roots differ in consequence (native UB vs Keystore alias overwrite vs replay scope) and must remain distinct.
**STATE TRANSITIONS:** two `FileRegistrationSessionStore` → two `RegistrationSessionKey` → first-use race → K₂ replaces K₁ → envelope under K₁ unauthenticable → synthetic `Failed` → **AC-001 entry**; two `createKeyIfAbsent()` → alias overwritten between steps → thumbprint mismatch → denial; two bridges → AC-006.
**FINAL IMPACT:** STATE_DIVERGENCE / denial; enabler for AC-001 and AC-006.
**CHAIN BREAKPOINTS:** process-wide singletons (DI-owned) + serialized key creation with alias-existence check + no `generateKey` on existing alias.
**FIX GROUPS:** CJ-E, AD-A, AS-A.
**REQUIRED_TEST:** `assertSame(getInstance(c), getInstance(c))`; concurrent `createKeyIfAbsent` yields one key; concurrent store instances cannot both create.
**INDEPENDENT_RETEST_OWNER:** Crypto/JNI + Android/Storage.
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-012
**TITLE:** Build false closure — source remediated, `.so` stale, source-only retest, CI green
**CHAIN_SEVERITY:** HIGH (governance/evidence-integrity; not a runtime attacker chain) · **CONFIDENCE:** VERY_HIGH · **EVIDENCE_LEVEL:** E2 (preserved: committed `.so` == old-source rebuild byte-for-byte; `-2` vs `-11` disassembly; validator bypass) · **already fired once:** `ANOX-MAINARCH-031` closed at source level while runtime remained pre-fix; `ANOX-LEGACY-CRYPTO-005` Kotlin half inert (ROOT-002) and Rust half unshipped.
**ATTACKER_CLASS:** none required; A7 malicious variant (a swapped `.so` passes `validate_apk_contents.py`) is possible but **not evidenced** — no malicious event is asserted.
**CURRENT_REACHABILITY:** CURRENTLY_REACHABLE (every APK).
**COMPONENT_FINDINGS:** ROOT-001, ROOT-017, ROOT-018, BUILDSC-001/002/003/006/008, ARCH-002 (matrix not machine-enforced), MAINARCH-013, MAINARCH-031, LEGACY-CRYPTO-005, CS-021 (alert fatigue precursor).
**Composition answer (§14):** YES — ROOT-003/004/005/013/014 remediations can be "closed" from source/JVM review while the APK executes old native behaviour; an independent retest inspecting source would agree. Classification: `META_EVIDENCE_ISSUE / SECURITY_ENABLING_CONDITION`, formally `FALSE_CLOSURE_CHAIN`.
**FINAL IMPACT:** `SECURITY_FIX_DECLARED_CLOSED_WHILE_RUNTIME_REMAINS_VULNERABLE`; every native chain (AC-005/006/007) inherits this until broken.
**CHAIN BREAKPOINTS:** CI cross-build from pinned toolchain + in-run hash manifest compared to packaged `lib/*` (never read from repo) + JNI symbol parity + instrumented JNI on the produced binary; Gradle consumes build output. Re-committing a fresh `.so` alone is the same failure mode (MUST_NOT_FIX_ALONE).
**FIX GROUPS:** Build/Supply remediation order 1–4 (precondition to CJ-*).
**REQUIRED_TEST:** gate fails when committed/packaged hash ≠ rebuild; the two `BufferTooSmall` instrumented tests pass on the produced binary.
**INDEPENDENT_RETEST_OWNER:** Build/Supply.
**DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-013
**TITLE:** Physical evidence vacuum (Keystore survival, StrongBox/TEE, backup agents, power-loss) — enabling condition, not an attack chain
**CHAIN_SEVERITY:** INFO · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E0 (by nature) · **ATTACKER_CLASS:** none · **ACTIVATION:** FINAL_RELEASE_ONLY / PHYSICAL_ONLY
**COMPONENT_FINDINGS:** ROOT-017, MAINARCH-018, ARCH-006, BUILDSC-002. **GAPS:** AS-GAP-003.
**Assessment (§61):** `CLOSURE_RISK_ENABLING_CONDITION` — AC-001 (Keystore-alias survival across `pm clear`/reinstall), AC-008 (alias enumeration), AC-003/ARCH-006 (self-reported hardware level) and AC-009 (P12/P13 power loss) all rest on device behaviour no evidence has measured on a provenance-verified binary. Not forced into an exploit chain.
**CHAIN BREAKPOINTS:** P1–P14 executed on a provenance-verified binary after ROOT-001.
**RETEST OWNER:** Physical GrapheneOS + Build/Supply. **DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-014
**TITLE:** Armed-latch permanent denial after authoritative `Rejected` → only exit is `clearBinding()` → feeds AC-001 variant A
**CHAIN_SEVERITY:** LOW (denial; enabler) · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E2 (harness [23]–[25]: `Failed` persisted, armed=true, `canStartNew=false`, retry impossible, key loss ⇒ `TerminalKeyLoss`)
**ATTACKER_CLASS:** none (server rejects; transient vs permanent indistinguishable). **ACTIVATION:** B004 first real `Rejected`.
**COMPONENT_FINDINGS:** AS-CAND-001, LEGACY-INTEGRATION-003 (partial), ARCH-003. **GAPS:** AS-GAP-001, AD-GAP-002 (rejection classes), AS-GAP-002 (reset path).
**FINAL IMPACT:** FAIL_CLOSED_DENIAL; no authorization bypass confirmed. Chain relevance: the inevitable "reset" UX (`clearBinding()` while the Device Auth alias survives) is exactly the AC-001/A entry with the *same JKT* — a reset that does not delete the alias last recreates the fail-open.
**CHAIN BREAKPOINTS:** rejection-class contract + explicit `RejectedAfterArm` state (no `save(Failed)` over `CommitArmed`) + reset path that deletes the Device Auth alias **before** clearing the marker; clearing the marker on `Rejected` alone re-enables key creation after a transient rejection (MUST_NOT_FIX_ALONE).
**FIX GROUPS:** AS-B, AS-E, AD-F. **RETEST OWNER:** Android/Storage. **DISPOSITION:** OPEN_PENDING_CONSOLIDATION

### ANOX-ATTACKCHAIN-CANDIDATE-015
**TITLE:** Secret residency (pickle JSON, K_STATE copies, grant, leaked handles, abort-on-panic) → heap/core disclosure
**CHAIN_SEVERITY:** LOW · **CONFIDENCE:** HIGH · **EVIDENCE_LEVEL:** E1 · **ATTACKER_CLASS:** A6 (memory/core/hprof) or A5 · **ACTIVATION:** B004 volume / B008
**COMPONENT_FINDINGS:** ROOT-010, CJ-CAND-005, ROOT-014 (lifetime), CS-019 (`panic=abort` skips Drop). **Assessment (§35):** relevant only with process-memory disclosure; no standalone chain; severity not inflated. **BREAKPOINTS:** best-effort zeroization + handle lifetime cleanup (after CJ-A). **FIX GROUPS:** CJ-F, AS-C. **RETEST OWNER:** Crypto/JNI. **DISPOSITION:** OPEN_PENDING_CONSOLIDATION

---

## REQUIRED CHAIN — ROOT-006 + ROOT-007 + AUTH GAP-003
**CONFIRMED — AC-001, HIGH, E2.** Same key or new key: **both** (variant A same JKT when the Keystore alias survives — harness [18]; variant B new key when the alias is gone — [21]). Exact states required: marker absent/`0x00`/v1-garbage **∧** session absent/empty/unauthenticable(→`Failed`) [17]; with the marker armed/bound the chain is blocked ([22]). Server uniqueness fully breaks **variant A only** and converts it to local denial requiring a reset path; **variant B remains** (indistinguishable from a legitimate new device) → impact then = denial-plus-orphaned-ACTIVE-account, i.e. lifecycle/integrity, not authorization bypass. Accidental (A8) and malicious (A4) variants share the sequence and are recorded as one chain.

## REQUIRED CHAIN — ROOT-008 + ROOT-009
**CONFIRMED — AC-002, MEDIUM, E2.** A proof intended for `/v1/a%2Fb` validates against `/v1/a/b` under current verifier semantics — **even with jkt binding** ([1]); with an attacker key and defaults ([2]) the result is dominated by ROOT-008. Necessary verifier mistakes: decoded-path comparison **and** a router that decodes before matching. Server canonicalization mismatch in the other direction (`:443`, `..`, `//`) is interoperability (fail-closed), not authorization. Activation B004; no external bypass procedure derived.

## REQUIRED CHAIN — STOLEN TOKEN + OPTIONAL ATH/JKT
**CONFIRMED — AC-003, HIGH (`CONDITIONAL_CRITICAL_AT_B004_IF_VERIFIER_DEFAULTS_PORTED`), E2.** A server mirroring current defaults accepts an attacker-generated proof for a stolen synthetic token ([4]); **mandatory `ath` alone does not break the chain** — the attacker computes `ath` over the stolen token ([5]); **mandatory jkt binding does** ([6]). `SINGLE_POINT_OF_SECURITY_FAILURE` = jkt binding. Synthetic tokens only; no real tokens obtained or used.

## REQUIRED CHAIN — REPLAY ACROSS INSTANCES/REPLICAS
**CONFIRMED — AC-004, MEDIUM, E2.** Three independent variants, none requiring the others: second replica ([10]), process restart ([11]), wall-clock rollback after eviction ([15]). A shared cache alone terminates the first two ([12][13]) but not the third; iat/monotonic retention is also required. Server contract hazard (B-016) unless the design is ported.

## REQUIRED CHAIN — ROOT-005 + ROOT-011
**CONFIRMED (E1 at this SHA; component behaviours E2-preserved) — AC-005, MEDIUM (HIGH at B008 without server epoch).** Rolled-back identity pickle re-exposes an unpublished set and consumed private OTKs; combined with index enumeration the re-upload set is nondeterministic; session rollback rewinds the ratchet. Lost `rename()` and failed `saveSession` (>4096) are non-malicious variants. B006 terminators: `otk_id`-keyed idempotent publication, consumed-OTK enforcement, publication epoch echoed into local AAD.

## REQUIRED CHAIN — ROOT-003 + ROOT-013 + ROOT-014 + ROOT-002
**CONFIRMED (E1; E2-preserved 7/100 reuse) — AC-006, HIGH.** Stale handle accepted after realloc → wrong object; `-1` collapse hides it; deserialize `0` collapse routes version bumps into `CorruptedIdentityState` → incorrect (potentially destructive) recovery. Multi-instance (ROOT-002) or direct `CryptoNative` makes it reachable without true concurrency at B004; concurrency at B008. Leaks currently mask address reuse — fixing ROOT-014 first activates the chain. No memory-corruption exploit developed.

## REQUIRED CHAIN — ROOT-004 + ROOT-005
**CONFIRMED — AC-007, MEDIUM, E2 (preserved measurements; source unchanged).** Exact current failure point: `saveIdentity` inside `ensurePublicIdentityMaterial(20)` (`CryptoBridge.kt:340` `ByteArray(4096)` vs 5269–5287 B) → `-11` in source / `-2 InvalidCiphertext` in the shipped binary. Result: **denial only** at this SHA (state preserved by `failStep`; identity with 20 unpersisted private OTKs leaked in native memory; retry regenerates). Not fail-open. Raising the constant alone converts it into OTK publication inconsistency (duplicates/omissions).

## REQUIRED CHAIN — ROOT-012 PARTIAL WIPE
**CONFIRMED (E1) — AC-008, MEDIUM.** After `wipeLocalCrypto()` → `Success`: Device Auth alias, `BOUND` marker, registration state and session-key alias survive; old authentication **can continue** (key kept); E2EE identity disappears (`FirstRun`) while Device Auth survives; server still recognizes the device; user is not stuck (unless K_STATE file survives → `WipedState`); account-delete UX **could** be misleading. Confidentiality impact: none (key-first). Lifecycle/integrity impact: yes, including a NO-RECOVERY hazard (new E2EE identity under the old device) unless the server enforces identity immutability.

## REQUIRED CHAIN — ANDROIDSTORAGE-CANDIDATE-002 COMMIT DURABILITY
**CONFIRMED (E2 preserved) — AC-009, LOW.** Server idempotency **prevents duplicate effects** but does **not** break the state divergence (client resumes from a stale step; `.bak` makes an old envelope live). Fail-open re-registration does **not** result from this chain alone (marker armed blocks `canStartNew`); it is replay/divergence bounded by the same grant and TTL.

## REQUIRED CHAIN — ROOT-001 FALSE CLOSURE
**CONFIRMED — AC-012, HIGH (governance), E2 preserved, CURRENTLY_REACHABLE, `FALSE_CLOSURE_CHAIN`.** A remediation can pass all source/JVM review while the released APK executes vulnerable native behaviour — it already did (`ANOX-MAINARCH-031`). No malicious actor required; none evidenced.

---

## ONE-DEVICE-ONLY ANALYSIS
Violations / apparent violations of `ONE ACTIVE DEVICE` (Inv.2):

| Path | Client guard today | Server guard today (V1.2) | Residual |
|---|---|---|---|
| local marker loss (A8/A4) | none once absent ([M2]) | `one_active_device_per_account` — **does not apply** (new account) | AC-001 |
| surviving DeviceAuth alias, files gone | `Present` → reuse ([M8][18]) | no `public_key` UNIQUE | AC-001/A: one key, two accounts |
| new DeviceAuth key after loss | `AbsentNotBound` → create ([21]) | legitimate new device | AC-001/B: orphaned ACTIVE device |
| re-registration inside same account | `canStartNew` false while bound | index blocks second ACTIVE | correct |
| backend race (two commits) | n/a | "one wins" | correct if implemented |
| missing JKT/public-key uniqueness | n/a | **absent** (GAP-003) | AC-001/A, AC-010 |
| commit idempotency | retry same grant | contract row only | AC-009 |
| forced reset via `clearBinding()` | public API | none | AC-014 → AC-001/A |

**Minimum server constraints making all client-side local-loss paths harmless:** (1) `UNIQUE(device_auth_keys.public_key)` globally + reject `submit-device-auth` for a JWK bound to any ACTIVE or REVOKED device (V1.2 §B-005.3 text made schema-enforced); (2) JKT→`device_id` immutable; (3) `identity_public_keys` immutability per device enforced at publication; (4) registration idempotency on `(registration_id, jkt)`; (5) typed PoP at submit and commit. With (1)–(5), every AC-001 path degrades to **local denial** (variant B still yields an orphaned ACTIVE device → requires a revocation/expiry policy, not a security control).

## NO-RECOVERY ANALYSIS
Unintentional recovery-like outcomes found: (a) **silent identity recreation** — AC-008 (`FirstRun` after partial wipe → `createAndPersistFirstIdentity` under a live device) unless server identity immutability; (b) **rebind of old credentials** — AC-001/A (surviving Device Auth key rebinds to a *new* account; not the old one — consistent with "denial requiring a new account", but the key reuse itself violates V1.2 §B-005.3); (c) **restore-based recovery** — none: ciphertext-only restore without Keystore yields `MissingKeystore`/`TerminalKeyLoss` (denial), never decryption; marker-only restore → `TerminalKeyLoss`; (d) **server-side account continuation with new local identity** — possible only via (a). Verdict: the no-recovery invariant holds for confidentiality; it is at risk for *identity continuity* in AC-008 and for *key reuse* in AC-001/A until the server constraints above exist.

## DEVICEAUTH ↔ E2EE BINDING
Client: JKT carried through `DeviceAuthRegistered → PublicIdentityUploaded → CommitArmed` and re-derived at commit — genuinely effective **locally**. Wire: `submitPublicIdentity(registrationId, grant, material)` and `commitRegistration(registrationId, grant)` carry **no JKT, no PoP, no idempotency key**; `registerDeviceAuth` carries JWK and an opaque proof string independently ([26][27]). Server contract binding `JKT + device_id + account_id + E2EE identity key` exists only as V1.2 table rows (`devices.device_auth_key_id`, `identity_public_keys` per device) with no PoP rule → **architecture gap relation recorded (AD-CAND-001 / AD-GAP-003), no semantics invented.** Component swap is possible for a grant holder (AC-010).

---

## SERVER CONTRACT CHAIN BREAKERS

| # | Server invariant | Breaks | Status in authority |
|---|---|---|---|
| S1 | `UNIQUE(device_auth_keys.public_key)` + known-key re-registration rejection | AC-001/A, AC-010, AC-014→001 | text only (V1.2 §B-005.3); schema lacks it — GAP-003 |
| S2 | JKT→device_id→account immutable binding; `AuthenticatedDeviceContext` from validated key only | AC-001/A, AC-003 | V1.2 §B-004.2 (context) partially |
| S3 | `one_active_device_per_account` partial index + "one wins" | same-account duplicates only | present |
| S4 | Registration idempotency on `(registration_id, jkt)`; commit idempotent | AC-009 effects | B-003 prose; GAP-002 |
| S5 | Typed registration PoP at submit-device-auth, submit-public-identity, commit (JWK-in-proof == JWK) | AC-010, AC-001 (partial) | endpoint-table row only — CAND-001 |
| S6 | ES256 signature over embedded jwk; P-256 only | baseline | B-002 |
| S7 | **Mandatory jkt binding** for every token-bearing request | AC-003 (single point), AC-002 (attacker-key leg) | B-002 prose; verifier optional |
| S8 | Mandatory `ath` when token presented | AC-003 (necessary, insufficient) | RFC 9449 §4.3; B-002 |
| S9 | Nonce at issuance / `DPoP-Nonce` / `use_dpop_nonce` | AC-003, AC-004 (freshness) | endpoint named only — GAP-001 |
| S10 | Shared atomic replay store `(jkt, jti)` | AC-004 (replica/restart) | B-016 "cannot be process-local" |
| S11 | Replay retention keyed by iat/monotonic source, bounded | AC-004 (rollback) | absent — CAND-003 |
| S12 | Canonical raw-path htu contract | AC-002 | absent — GAP-002 |
| S13 | OTK `otk_id`-keyed idempotent publication; same id ≠ key = security error | AC-005, AC-007 | B-006 v1.2 present |
| S14 | Consumed OTK enforcement (`CLAIMED` terminal) | AC-005 (server side) | B-006 present |
| S15 | Publication/rollback epoch (identity_revision monotonic, echoed to client) | AC-005 | absent — AS-GAP-003 |
| S16 | `identity_public_keys` immutability enforced at publish | AC-008 identity-replacement leg | V1.2 text "immutable" |
| S17 | Rejection-class taxonomy (transient vs permanent) | AC-014 | absent — GAP-002 |
| S18 | Device revocation on account-delete/wipe intent | AC-008 lifecycle leg | B-013 |

## CLIENT CONTRACT CHAIN BREAKERS

| # | Client control | Breaks |
|---|---|---|
| C1 | Fail-closed first-run resolver over {marker, session file, all anoX Keystore aliases}: absent marker ∧ any alias present ⇒ not first run | AC-001 (A+B), AC-014→001 |
| C2 | No key creation on read (`RegistrationSessionKey`, `initializeMasterKey`, `serialize*` for existing identity); create-on-write only; never `generateKey` on an existing alias; serialized creation | AC-001 entry, AC-008 label, AC-011 |
| C3 | Typed storage errors (`KEY_MISSING`, `EMPTY`, `UNSUPPORTED_VERSION`, `AUTH_FAILED`, `IO`) consumed by `currentState`/`canStartNew` as not-first-run | AC-001, AC-006/B |
| C4 | Directory fsync in all writers; replace/guard `AtomicFile` (check rename, forbid `.bak`, residue policy); empty file ⇒ security exception | AC-001 accidental, AC-009, AC-005 lost-rename |
| C5 | Marker integrity (dedicated HMAC alias; "HMAC key missing ⇒ bound") | AC-001 malicious |
| C6 | Slot+generation JNI handles with owning lock; `HANDLE_*` + `UNSUPPORTED_VERSION` codes; module-narrowed `CryptoNative`; process-wide singleton | AC-006, AC-011 |
| C7 | Dynamic native-allocated output with caps | AC-007, AC-005 (session variant) |
| C8 | Stable KeyId OTK surface (`created/removed`, unpublished-with-ids, mark-published) | AC-007, AC-005 |
| C9 | Safe-by-construction DPoP API: non-null `DpopBinding(jkt, tokenHash?, nonce?)`; factory requires token for token-bearing calls; no default replay cache; raw-path `DpopHtu` | AC-002, AC-003, AC-004 (client mirror) |
| C10 | Typed registration PoP at submit and commit + idempotency key | AC-010, AC-009 |
| C11 | Truthful cross-domain wipe (per-item results, marker last, all aliases, residue) | AC-008, AC-014 reset |
| C12 | Local AAD = type‖version‖context on registration and wrapped-key envelopes; crypto AAD hook | AC-005 (with S15) |
| C13 | `RejectedAfterArm` state; no `save(Failed)` over `CommitArmed` | AC-014 |
| C14 | Best-effort zeroization + handle lifetime cleanup (after C6) | AC-015 |

---

## PRE-B004 ATTACKCHAIN BLOCKERS

### CODE
AC-001 client half (C1–C5; AS-A/AS-B/AD-E), AC-006 + AC-007 (merged JNI ABI revision CJ-A/B/C/D/E; C6–C8), AC-011 (singletons + serialized creation; CJ-E/AD-A/AS-A), AC-012 (native build chain: pin, cross-build, hash gate, validator v2, instrumented JNI — precondition for accepting any native fix), AC-002/AC-003/AC-004 client-side API hardening (C9; AD-B/AD-C/AD-D client plumbing), AC-009 (C4).

### CONTRACT
Freeze before B-004 implementation (Inv.35): AD-GAP-003 (S1, S2, S16), AD-GAP-002 (S7, S8, S10, S11, S12, S17, S4), AD-GAP-001 (S9), AD-CAND-001 (S5), AS-GAP-001 (marker/session/first-run/armed-release contract), AS-GAP-002 (wipe/logout/delete contract), AS-GAP-003 (backup/reinstall/anti-rollback authority — S15).

### IMPLEMENTATION REQUIREMENTS
Inside B-004: server enforces S1–S12 and S17; shared replay store; registration PoP verification; `AuthenticatedDeviceContext` from validated key; AC-014 code change (`RejectedAfterArm`) during registration wiring after GAP-001 freeze; AD-CAND-002 fix inside Device-Auth wiring.

## LATER-GATE ATTACKCHAINS
- **AC-005** — B006 (publication/ACK/epoch, S13–S15) and B008/B009 (session rollback, CJ-CAND-002); reason: no publication or messaging exists to rewind.
- **AC-008** — B013 (wipe/logout/delete implementation) + B006 (S16) + Final gate (ROOT-012 retest); contract half is Pre-B004 via AS-GAP-002.
- **AC-015** — B008/B009 (CJ-F/AS-C); no exploit path before messaging volume.
- **AC-013** — Final/physical only, on a provenance-verified binary (ROOT-001 prerequisite).
- **AC-004 server half** — B004 backend implementation gate (contract entry Pre-B004).

---

## REJECTED CHAINS

| Hypothesis | Reason rejected | Mitigation that stops it | Evidence |
|---|---|---|---|
| Cross-type pickle substitution (session as identity) yields wrong-type object | serde shape rejects → `-6` | field-shape mismatch (accidental, but effective) | Crypto/JNI preserved |
| Remote exploitation of any chain at this SHA | no network code, no permissions, one static Activity | absence of surface | manifest + `MainActivity` |
| Remote manipulation of app-private files without local compromise | Android sandbox; no exported providers/services | platform sandbox | manifest |
| Structural marker corruption → unbound | fails closed `(T,T)` | `parse()` null ⇒ bound+armed | [M7] |
| ROOT-016 revival: StrongBox `catch` destroys a bound key | `Present` early return + `requireCreationAllowed` guard | source `:48-57` | Auth/Storage revalidation; **remains REJECTED** |
| jti-only replay key → cross-key denial | 128-bit random jti; RFC-consistent | entropy | Auth preserved |
| HTU collision as a **standalone** V1 authorization bypass | frozen endpoint inventory has fixed paths + UUIDv4 params; needs a decoding router; a self-minted proof gains nothing for its own key | — (kept only as composition amplifier in AC-002) | V1.2 §B-007.2 |
| Registration-state rollback exposes a new grant | same grant, same TTL | grant scope | Storage preserved |
| Backup/restore → confidentiality loss | ciphertext only; Keystore never backed up; `allowBackup=false` + rules + `noBackupFilesDir` | Keystore binding | Storage preserved; physical pending |
| `one_active_device_per_account` prevents AC-001 | index is per `account_id`; AC-001 registers a **new** account | — (insufficient, not a mitigation) | V1.2 §B-005.3 |
| Malicious `.so` supply-chain event already occurred | origin commit and toolchain fully reconstructed; stale, not foreign | — | Build/Supply preserved |
| Two `getInstance()` callers corrupt `.tmp` today | single caller today; folded into AC-011/AC-006 as activation-time | unwired | source |
| Grant theft via logs | no `Log` outside `CryptoBridge`; grant redacted | redaction discipline | Auth/Storage preserved |
| Enabling R8 breaks JNI symbols | AGP default keep rule retains native methods | default proguard file | Build/Supply preserved |

---

## ROOT COVERAGE TABLE

| Root | Chain(s) | Disposition | Enabler/Standalone/Later | Notes |
|---|---|---|---|---|
| ROOT-001 | AC-012 (core), AC-007 (-2 runtime) | META_EVIDENCE_ISSUE | enabler of every native closure | PRE-B004 precondition |
| ROOT-002 | AC-006, AC-011 | PARTICIPATES_IN_CONFIRMED_CHAIN | | |
| ROOT-003 | AC-006 | CONFIRMED | | |
| ROOT-004 | AC-007, AC-005 | CONFIRMED | | |
| ROOT-005 | AC-007, AC-005 | CONFIRMED | | |
| ROOT-006 | AC-001, AC-011, AC-008 | CONFIRMED | | |
| ROOT-007 | AC-001, AC-009 | CONFIRMED | | hub |
| ROOT-008 | AC-002, AC-003, AC-004 | CONFIRMED | | |
| ROOT-009 | AC-002 | CONFIRMED | | |
| ROOT-010 | AC-015 | PARTICIPATES_IN_POTENTIAL_CHAIN | later B008 | |
| ROOT-011 | AC-005, AC-001 (marker) | CONFIRMED | later B006/B008 (identity); Pre-B004 slice | |
| ROOT-012 | AC-008 | CONFIRMED | later B013/Final | |
| ROOT-013 | AC-006, AC-007 | CONFIRMED | | severity overlay stays PENDING |
| ROOT-014 | AC-006, AC-007, AC-015 | CONFIRMED | | fix after ROOT-003 |
| ROOT-015 | — | STANDALONE_SECURITY_ISSUE | Final gate | no composition found |
| ROOT-016 | — | NOT_CHAIN_RELEVANT | — | REJECTED; not promoted |
| ROOT-017 | AC-012, AC-013 | ENABLING_CONDITION_ONLY | | |
| ROOT-018 | AC-012 | META_EVIDENCE_ISSUE | RC | umbrella |

## SPECIALIST CANDIDATE COVERAGE TABLE

| Candidate | Chain(s) | Disposition |
|---|---|---|
| BUILDSC-001 | AC-012 | META_EVIDENCE_ISSUE |
| BUILDSC-002 | AC-012, AC-013 | ENABLING_CONDITION_ONLY |
| BUILDSC-003 | AC-012 | ENABLING_CONDITION_ONLY |
| BUILDSC-004 | AC-012 (doc claim) | META_EVIDENCE_ISSUE |
| BUILDSC-005 | (A7 supply) | ENABLING_CONDITION_ONLY |
| BUILDSC-006 | AC-012 | ENABLING_CONDITION_ONLY |
| BUILDSC-007 | — | STANDALONE_SECURITY_ISSUE |
| BUILDSC-008 | AC-012 | ENABLING_CONDITION_ONLY |
| BUILDSC-009 | — | NOT_CHAIN_RELEVANT |
| BUILDSC-010 | — | NOT_CHAIN_RELEVANT |
| BUILDSC-011 | — | NOT_CHAIN_RELEVANT |
| BUILDSC-012 | — | NOT_CHAIN_RELEVANT |
| CRYPTOJNI-001 | AC-007, AC-005 | PARTICIPATES_IN_CONFIRMED_CHAIN |
| CRYPTOJNI-002 | AC-005 (session variant) | PARTICIPATES_IN_POTENTIAL_CHAIN |
| CRYPTOJNI-003 | AC-006/B, AC-007 | PARTICIPATES_IN_CONFIRMED_CHAIN |
| CRYPTOJNI-004 | AC-007 (growth) | PARTICIPATES_IN_POTENTIAL_CHAIN |
| CRYPTOJNI-005 | AC-015 | PARTICIPATES_IN_POTENTIAL_CHAIN |
| CRYPTOJNI-006 | AC-006 (diagnostic) | ENABLING_CONDITION_ONLY |
| AUTHDPOP-CANDIDATE-001 | AC-010, AC-009 | PARTICIPATES_IN_CONFIRMED_CHAIN |
| AUTHDPOP-CANDIDATE-002 | AC-011, AC-010 | PARTICIPATES_IN_CONFIRMED_CHAIN |
| AUTHDPOP-CANDIDATE-003 | AC-004 | PARTICIPATES_IN_CONFIRMED_CHAIN |
| ANDROIDSTORAGE-CANDIDATE-001 | AC-014 (→AC-001) | PARTICIPATES_IN_CONFIRMED_CHAIN |
| ANDROIDSTORAGE-CANDIDATE-002 | AC-009, AC-001 (`.bak`) | PARTICIPATES_IN_CONFIRMED_CHAIN |

Historical/architecture items: ARCH-001 CONFIRMED (AC-006); ARCH-002 META (AC-012); ARCH-003 CONFIRMED (AC-001/010/014); ARCH-004 ENABLING (schema-authority drift for S1/S2); ARCH-005 NOT_CHAIN_RELEVANT; ARCH-006 POTENTIAL (AC-003); ARCH-007 CONFIRMED (AC-001 via ROOT-006); ARCH-008 CONFIRMED (AC-006/007); ARCH-009 CONFIRMED (AC-008); ARCH-010 NOT_CHAIN_RELEVANT; MAINARCH-013 META (AC-012); MAINARCH-018 ENABLING (AC-013/001); MAINARCH-030 CONFIRMED (AC-008); LEGACY-INTEGRATION-005 CONFIRMED (AC-006); LEGACY-B003-001 STANDALONE; LEGACY-CRYPTO-005 META (AC-012 example); LEGACY-INTEGRATION-001 CONFIRMED (AC-010); LEGACY-INTEGRATION-003 CONFIRMED (AC-014); MAINARCH-023 POTENTIAL (AC-008/006); MAINARCH-031 META (AC-012 fired instance); CS-021/C-017 META.

## ARCHITECTURE GAP COVERAGE TABLE

| Gap | Chains | Class |
|---|---|---|
| AUTHDPOP-GAP-001 (nonce) | AC-003, AC-004 | CHAIN_RELEVANT — ENABLING_CONDITION_ONLY |
| AUTHDPOP-GAP-002 (verifier contract) | AC-002, AC-003, AC-004, AC-009, AC-014 | **CHAIN_CRITICAL** — ENABLING_CONDITION_ONLY |
| AUTHDPOP-GAP-003 (JKT/device/account binding) | AC-001 (server half), AC-010, AC-008 | **CHAIN_CRITICAL** — PARTICIPATES_IN_CONFIRMED_CHAIN |
| ANDROIDSTORAGE-GAP-001 (marker/session contract) | AC-001, AC-014 | **CHAIN_CRITICAL** — ENABLING_CONDITION_ONLY |
| ANDROIDSTORAGE-GAP-002 (wipe contract) | AC-008, AC-014 | CHAIN_RELEVANT — ENABLING_CONDITION_ONLY |
| ANDROIDSTORAGE-GAP-003 (backup/reinstall/anti-rollback authority) | AC-001 (restore variants), AC-005, AC-013 | CHAIN_RELEVANT — ENABLING_CONDITION_ONLY |

---

## CROSS-GROUP FIX DEPENDENCIES
`CROSS_GROUP_FIX_DEPENDENCY` recorded for: **AS-A/AS-B ↔ AD-E/AD-F** (AC-001: client resolver + server uniqueness), **CJ-C/CJ-D ↔ AS-D ↔ B-006 server** (AC-005 epoch/AAD/KeyId), **CJ-B ↔ AS-C** (AC-006/B error channel + consumer), **AS-B ↔ AD-F** (AC-009/AC-014 idempotency + rejection classes), **AS-E ↔ AD-F/B-013** (AC-008 wipe + revocation + identity immutability), **AD-B ↔ AD-C ↔ AD-D** (AC-002/003/004 one DPoP contract), **Build/Supply → all CJ-\*** (AC-012 precondition). Existing groupings are not proven unsafe; no regrouping proposed.

## MASTER REMEDIATION PRECURSOR MATRIX

| Chain | Components | Fix groups | Must fix together | Minimum breaking control | Retest domains |
|---|---|---|---|---|---|
| AC-001 | ROOT-006/007/011m, AS-CAND-002, GAP-003, AS-GAP-001/003 | AS-A, AS-B, AS-D, AD-E, AD-F | all ROOT-007 components ∧ ROOT-006 ∧ consumer ∧ S1/S2 | C1 (client) or S1 (server, variant A) | Storage, Auth, Attackchain, Physical |
| AC-002 | ROOT-009, ROOT-008, GAP-002 | AD-C (+AD-B) | client htu ∧ server rule | S12/C9 | Auth |
| AC-003 | ROOT-008, GAP-002, GAP-001, ARCH-006 | AD-B, AD-D | all call sites ∧ contract | **S7 mandatory jkt** | Auth, backend |
| AC-004 | ROOT-008 scope, AD-CAND-003, GAP-001/002 | AD-D | shared store ∧ retention source | S10 ∧ S11 | backend, Auth |
| AC-005 | ROOT-011, ROOT-005, CJ-001/002, ROOT-004 | CJ-C, CJ-D, AS-D, AS-B | AAD ∧ epoch ∧ KeyId ∧ durability | S15 (+C12) | Crypto/JNI, Storage |
| AC-006 | ROOT-002/003/013/014, CJ-003/006, ROOT-006c | CJ-A, CJ-B, CJ-E, AS-C | ROOT-003∧014∧013∧002; CJ-003∧consumer | C6 | Crypto/JNI (instrumented on verified `.so`) |
| AC-007 | ROOT-004/005, CJ-001/004, ROOT-013, ROOT-001 | CJ-C, CJ-D, CJ-G | buffer ∧ KeyId surface | C7 ∧ C8 | Crypto/JNI |
| AC-008 | ROOT-012, ROOT-006m, GAP-002s, ARCH-009, MAINARCH-030 | AS-E, AS-C, AD-F | wipe ∧ aliases ∧ marker-last ∧ S16 | C11 (+S16) | Storage, Architecture |
| AC-009 | AS-CAND-002, ROOT-007, GAP-002 | AS-B, AD-F | rename check ∧ `.bak` ∧ idempotency | C4 | Storage |
| AC-010 | AD-CAND-001/002, GAP-003, ROOT-011r | AD-F, AD-B, AD-A | PoP ∧ uniqueness ∧ nonce | S5 | Auth, Architecture |
| AC-011 | ROOT-002, AD-CAND-002, ROOT-006 race | CJ-E, AD-A, AS-A | singleton ∧ serialized creation | C2 ∧ C6 | Crypto/JNI, Storage |
| AC-012 | ROOT-001/017/018, BUILDSC-001/002/003/006/008, ARCH-002 | Build/Supply 1–4 | pin ∧ cross-build ∧ hash gate ∧ instrumented | in-run hash gate | Build/Supply |
| AC-013 | ROOT-017, MAINARCH-018, AS-GAP-003 | AS-G | after ROOT-001 | P1–P14 | Physical |
| AC-014 | AS-CAND-001, AS-GAP-001, GAP-002 | AS-B, AS-E, AD-F | state ∧ rejection classes ∧ reset order | C13 ∧ S17 | Storage |
| AC-015 | ROOT-010, CJ-005, ROOT-014 | CJ-F, AS-C | after CJ-A | C14 | Crypto/JNI |

## MUST-FIX-TOGETHER ACROSS DOMAINS
1. AC-001: Storage (AS-A/AS-B) ∧ Auth (AD-E/AD-F) ∧ server schema (S1/S2) ∧ contracts (AS-GAP-001, AD-GAP-003).
2. AC-005: Crypto (CJ-C/CJ-D) ∧ Storage (AS-D) ∧ B-006 server (S13–S15).
3. AC-006/B & AC-007: Crypto (CJ-B/CJ-C/CJ-D) ∧ Storage consumer (AS-C) ∧ Build/Supply (ROOT-001) for retest validity.
4. AC-003/002/004: Auth client API (AD-B/AD-C/AD-D) ∧ server contract (GAP-002/001) ∧ B-004 implementation.
5. AC-008/AC-014: Storage (AS-E/AS-B) ∧ Auth/server (AD-F, S16–S18) ∧ B-013 contract.

## MUST-NOT-FIX-ALONE ACROSS DOMAINS
- Server `public_key` UNIQUE without the client first-run resolver → variant B and denial-without-reset remain; client resolver without server uniqueness → variant A survives a `pm clear`/reinstall where the alias survives (physical unknown).
- Marker HMAC/cross-check without fixing empty-file and key-missing session downgrades → chain re-enters via the session path.
- Shared replay store without iat/monotonic retention → AC-004 rollback variant survives.
- Mandatory `ath` without mandatory jkt → AC-003 survives (proven [5]).
- Raising the 4096 constant without the KeyId surface → AC-007 becomes duplicate upload.
- ROOT-014 handle cleanup before ROOT-003 → AC-006 activates.
- Clearing the armed marker on `Rejected` without rejection classes and alias-first reset → AC-014 converts into AC-001/A.
- Re-committing a rebuilt `.so` without the CI hash gate → AC-012 repeats.
- Wipe deleting files but not aliases (or vice-versa) → AC-008 inconsistent terminal states.

---

## TEST REQUIREMENT SYNTHESIS
Whole-chain regression tests (synthetic backend permitted later; JVM-first):
1. **AC-001:** commit → delete marker + empty/corrupt session + keep DeviceAuth alias (fake Keystore double) + synthetic server with S1 → `reserve()` throws (resolver) and server rejects known JWK; variant B (alias gone) → resolver still fails closed (aliases `anox.b003.session.v1`/master present) ⇒ explicit reset required. Instrumented: same on device; physical P4/P5/P13.
2. **AC-002:** collision rows rejected with and without jkt on both client and synthetic server; interop rows accepted after canonicalization.
3. **AC-003:** attacker-key proof with correct `ath` for a valid token ⇒ `KEY_BINDING_MISMATCH` on all token-bearing endpoints; API cannot be called without a binding (compile-level).
4. **AC-004:** shared store across two verifier instances + restart persistence + rollback −250 s ⇒ replay rejected.
5. **AC-005:** old identity envelope rejected after newer epoch; publish→ACK→mark→rollback→re-publish rejected by synthetic server; session rollback detected.
6. **AC-006:** instrumented: destroy → realloc → stale handle ⇒ `HANDLE_STALE_GENERATION`; concurrent encrypt/serialize serialized; version bump ⇒ `UNSUPPORTED_VERSION` ≠ corrupted.
7. **AC-007:** instrumented default-count step succeeds; uploaded set == `created` KeyIds, unique; count/enumeration equal after publish.
8. **AC-008:** wipe touches 5 domains + 3 aliases + residue, marker last, per-item result; server device revoked; second identity publication for the same device rejected.
9. **AC-009:** rename failure throws; planted `.bak` ignored; `kill -9` matrix (P12).
10. **AC-010:** synthetic server rejects submit-public-identity/commit without PoP from the registered JKT; second JWK per registration_id rejected.
11. **AC-011:** `assertSame(getInstance, getInstance)`; concurrent `createKeyIfAbsent` → one key; concurrent stores cannot both create.
12. **AC-012:** gate fails on committed/packaged hash ≠ rebuild; `BufferTooSmall` instrumented tests pass on the produced binary.
13. **AC-014:** `Rejected` after arm never overwrites `CommitArmed`; reset deletes alias before marker.
14. **AC-015:** review-based + best-effort `fill(0)` assertions.

## INDEPENDENT RETEST OWNERS
AC-001 Storage + Auth + Attackchain + Physical · AC-002/003 Auth/DPoP (+backend) · AC-004 backend + Auth · AC-005 Crypto/JNI + Storage · AC-006/007 Crypto/JNI · AC-008 Storage + Architecture · AC-009 Storage · AC-010 Auth + Architecture · AC-011 Crypto/JNI + Storage · AC-012 Build/Supply · AC-013 Physical GrapheneOS + Build/Supply · AC-014 Storage · AC-015 Crypto/JNI. None may be the implementer.

## FINAL FULL-SYSTEM REAUDIT CHAINS
Mandatory replay after all remediation: **AC-001, AC-003, AC-006, AC-012** (HIGH) plus chains crossing ≥3 trust boundaries: **AC-005, AC-008, AC-010**; recommended: AC-002, AC-004, AC-007, AC-011, AC-014 (feeds AC-001). All on a provenance-verified binary.

---

## EVIDENCE LIMITATIONS
No chain exceeds E2. Harness results (`/tmp/anox_attackchain_001/harness/out.txt`, `marker_out.txt`, `METHOD.txt`) use production classes compiled from the unchanged source plus the repository's own JVM test doubles (`FakeRegistrationApi`, `FakeDeviceAuthKeyManager`, `InMemory*` stores, `MutableTestClock`); the server side is modelled, not implemented; `/tmp` artifacts are **not authoritative** — results are transcribed here. `RegistrationSessionKey` create-on-read and empty-file downgrade rely on preserved E2 evidence (Keystore not available on the JVM). No exploit, credential tooling, or third-party traffic was produced.

## PHYSICAL EVIDENCE LIMITATIONS
No device/emulator authorized; instrumented (66 storage + 27 auth + 39 crypto) and physical tests `NOT_RUN`. Keystore survival across `pm clear`/reinstall/profile, StrongBox/TEE level, real power-loss rename durability, backup-agent behaviour and file mode bits remain unmeasured (AC-013). Any physical run before ROOT-001 remediation tests the stale binary.

## SERVER-ABSENCE LIMITATIONS
No B-004 backend, token issuance, nonce store, replay store, device registry or schema exists. All "server accepts/rejects" statements are derived from V1.2 contract text and the verifier semantics of the client-module copy; AC-002/003/004 therefore describe **future backend hazards** (E2 for mechanics, E0 for the backend's eventual behaviour) and are gated as contract-freeze items, not asserted as live vulnerabilities.

---

## SEC-A
Component-local: CJ-F/CJ-G (AC-015, AC-007 caps), AS-A/AS-C/AS-F, AD-A/AD-C/AD-E, Build/Supply 010/011/012/009 hygiene.

## SEC-B
Cross-component contract/API changes without trust-boundary redesign: merged CJ-A+B+C+D+E ABI revision (AC-006/007), AS-B/AS-D/AS-E (AC-001/005/008/009/014), AD-B/AD-D/AD-F (AC-002/003/004/010), Build/Supply trust-chain redesign (AC-012), server-side S1–S18 as B-spec amendments.

## SEC-C REQUIRED
**NO.** Every chain is broken by completing contracts inside the frozen trust model (Keystore-bound non-exportable keys, server-derived identity, DPoP, no recovery, one device) plus component-internal redesigns already proposed by the specialists. No chain requires moving a trust boundary or introducing a new trust anchor. Escalation trigger: if S1/S2/S5/S7 cannot be frozen as binding server invariants before B-004, AC-001/AC-003/AC-010 would leave the one-device and DPoP invariants dependent on unspecified server behaviour — that would be a systemic invariant gap.

## ARCHITECTURE VERDICT
**`CROSS_COMPONENT_CONTRACT_HARDENING_REQUIRED`** — stronger than "component fixes only" because the four HIGH chains and most MEDIUM chains terminate **only** when client controls and server invariants are specified together (AC-001: resolver + `public_key` UNIQUE; AC-003: mandatory jkt binding across client API and server pipeline; AC-010: typed PoP on both ends; AC-005: epoch echoed into local AAD), and today several of those invariants exist only as prose or endpoint-table rows. Not `TRUST_BOUNDARY_REDESIGN_REQUIRED`: boundaries are correctly placed; their contracts are incomplete.

---

## MASTER CONSOLIDATION HANDOFF
- Chain IDs: `ANOX-ATTACKCHAIN-CANDIDATE-001..015` (audit-local; no ROOT IDs allocated; no canonical finding mutated).
- Component IDs referenced: ROOT-001..018 (016 REJECTED, untouched); BUILDSC-001..012; CRYPTOJNI-001..006; AUTHDPOP-CANDIDATE-001..003; AUTHDPOP-GAP-001..003; ANDROIDSTORAGE-CANDIDATE-001..002; ANDROIDSTORAGE-GAP-001..003; ARCH-001..010; MAINARCH-013/018/023/030/031; LEGACY-CRYPTO-005; LEGACY-INTEGRATION-001/003/005; LEGACY-B003-001; CS-021/C-017.
- Severity: 0C / 4H (001, 003, 006, 012) / 7M / 3L / 1I; AC-003 conditional CRITICAL flag; ROOT-013 overlay untouched (PENDING).
- Evidence: E2 = AC-001/002/003/004/007/009/012/014; E1 = AC-005/006/008/010/011/015; E0 = AC-013.
- Chain breakpoints: S1–S18 / C1–C14 tables; single points: AC-003 (S7), AC-002 (S12).
- Fix-group dependencies: precursor matrix + cross-group list above.
- Gates: PRE-B004 code/contract/implementation sets; later-gate set.
- Required tests: synthesis items 1–14.
- Rejected chains: 13 recorded with reasons.
- Coverage: 68 items, UNMAPPED = 0.

## REMEDIATION COVERAGE HANDOFF
For each of AC-001..015 the record above supplies: SOURCE (`AUDIT-SECURITY-ATTACKCHAIN-001`), CHAIN_ID, COMPONENT_FINDINGS, ROOT_CAUSE_COMPOSITION (state transitions), AFFECTED_CODE (`RegistrationOrchestrator.kt:58-62,167-232,246-254`; `FileRegistrationSessionStore.kt:35-53,56-72`; `RegistrationSessionKey.kt:47-69`; `FileDeviceAuthBindingStore.kt:37-45,58-61`; `DeviceAuthKeyStateResolver.kt:20-32`; `AndroidKeystoreDeviceAuthKeyManager.kt:48-57,106-118`; `DpopProofVerifier.kt:25-29,42-49,91,131,140,150`; `DpopHtu.kt:29-35`; `DpopReplayCache.kt:29-57`; `DpopProofFactory.kt:35-39`; `RegistrationApi.kt:30-51`; `CryptoBridge.kt:38-44,73-101,133-165,334-355,580,603-661,737-754,783-794`; `CryptoBridgeLocalE2eeIdentityStep.kt:19-75`; `lib.rs:31-116,126-255,292-344,522-544`; `identity.rs:33-72`; `ci.yml`; `jniLibs/*`), AFFECTED_ARCHITECTURE (Inv.1/2/3/18/23/24/25/35; B-002; B-003 v1.5; V1.2 §B-004.1-2, §B-005.2-3, §B-006.3, §B-007.2-5; B-013; B-016; B-021), FIX_GROUPS, PRE_B004_OR_LATER, CHAIN_BREAKPOINTS, REQUIRED_TEST / RUNTIME_TEST (instrumented items) / PHYSICAL_TEST (P1–P14 mapping), RETEST_OWNERS, DEPENDENCIES, DISPOSITION = `OPEN_PENDING_CONSOLIDATION` for all 15 (none rejected as a chain; AC-013 is an enabling condition, kept for coverage-gate tracking).

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
`PRESERVE AUDIT-SECURITY-ATTACKCHAIN-001 → MERGE → MASTER SPECIALIST CONSOLIDATION → SECURITY-REMEDIATION-COVERAGE-GATE WITH 100% ASSIGNMENT → LARGE DEPENDENCY-SAFE REMEDIATION SESSIONS → INDEPENDENT DOMAIN RETESTS → CROSS-DOMAIN ATTACKCHAIN RETEST → LEGACY/ARCHITECTURE REVALIDATION → FRESH FULL-SYSTEM SECURITY RE-AUDIT → PHYSICAL GRAPHENEOS EVIDENCE → FINAL OPERATIONAL ACCEPTANCE → HUMAN FINAL PRODUCT GATE → ONLY THEN B004`

```
HEAD        = e54584903a353e98ad154d1e8f90f93ed9d7db14
origin/main = e54584903a353e98ad154d1e8f90f93ed9d7db14
working tree = CLEAN (git status --short empty; git diff --check rc 0; branch main; 0 stashes)
branches / commits / push / PR / merge = NONE · remote mutation = NONE
findings / docs / registries / Project Memory mutation = NONE · fixes implemented = NONE
temp artifacts = /tmp/anox_attackchain_001/{harness,METHOD.txt,traceability_extract.txt} only
```

`AUDIT-SECURITY-ATTACKCHAIN-001` — COMPLETE. `PASS_WITH_FINDINGS`. STOP.
