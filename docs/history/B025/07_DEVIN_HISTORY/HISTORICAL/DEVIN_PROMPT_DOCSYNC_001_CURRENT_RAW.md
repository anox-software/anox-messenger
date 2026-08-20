# DEVIN PROMPT — DOCSYNC-001
# anoX V1 Current RAW Architecture & Documentation Synchronization

```text
ANOX V1 — DOCSYNC-001
FULL PROJECT DOCUMENTATION SYNCHRONIZATION TO CURRENT ARCHITECTURE

OBJECTIVE

Synchronize EVERY architecture, security, specification, status, decision,
README, and changelog Markdown document in the existing anoX Messenger repository
with the current accepted V1 architecture.

This is a DOCUMENTATION / ARCHITECTURE SYNCHRONIZATION task.

DO NOT implement new product features.
DO NOT implement backend.
DO NOT implement account registration.
DO NOT implement messaging.
DO NOT implement push.
DO NOT implement attachments.
DO NOT redesign the crypto code in this task.

The purpose is to ensure that no future coding agent can accidentally read an old
Raw1.1 document and implement superseded requirements such as recovery,
multi-device, libsignal, OpenPGP, server-trusted verification, or old push rules.

==================================================
0. SOURCE OF TRUTH / STATUS MODEL
==================================================

The repository currently contains many documents labeled:

Raw1.1

These are NOT the current authoritative architecture.

The current authoritative baseline is the consolidated anoX V1 architecture
from RAW1.60 through RAW1.75 plus the current Master Architecture decisions.

DO NOT invent a new RAW version number.

Use status headers such as:

Status: CURRENT
Architecture Baseline: RAW1.60–RAW1.75 consolidated
Last synchronized: 2026-08-19

or:

Status: HISTORICAL / SUPERSEDED
Do not use as current implementation specification.
Superseded by: <current file>

Historical reports must not be rewritten to falsely claim tests that did not run.

==================================================
1. CURRENT BINDING V1 ARCHITECTURE
==================================================

Treat the following as binding unless explicitly marked OPEN.

-------------------------
PRODUCT / DISTRIBUTION
-------------------------

- anoX Messenger is a closed-source project.
- Android / GrapheneOS is the primary V1 target.
- Existing Android project must be evolved, not recreated as an unrelated app.
- V1 core is 1:1 secure messaging.
- anoX Support chat is a product requirement and should be pinned/clearly available.
- Do not claim that anoX is "unhackable".
- Strong security claims require independent review/audit.

-------------------------
ACCOUNT / USER IDENTITY
-------------------------

- Internal `account_id` is random and non-sequential.
- `device_id` is random and non-sequential.
- Account identity, device identity, public username/contact identifier,
  and E2EE identity are separate concepts.
- No mandatory telephone number.
- No mandatory e-mail address.
- Usernames/public handles may be used for contact addressing.
- QR/contact identifiers are supported conceptually.
- There is no unrestricted global user directory in V1.
- Protect against account/username enumeration.
- Username change does NOT imply E2EE identity-key change.
- `account_id` is not a password and not an E2EE key.

-------------------------
DEVICE MODEL
-------------------------

- V1 supports ONE active device per account.
- Multi-device is NOT a V1 feature.
- Do not document 5-device/10-device limits as current architecture.
- Do not document device-addition sync flows as V1.
- Device authentication is separate from E2EE identity.
- Device revocation must prevent API authentication and new push/message delivery.
- A lost device does not migrate its old private E2EE identity to a new device.

-------------------------
RECOVERY
-------------------------

V1 HAS NO ACCOUNT OR CRYPTO RECOVERY.

Explicitly prohibited in V1:
- recovery seed
- recovery phrase
- recovery code
- encrypted server private-key backup
- recovery device
- social recovery
- multi-device recovery
- hidden master recovery key
- cloud restoration of E2EE private state

If the only device and local crypto state are permanently lost:
the old cryptographic identity/account cannot be restored in V1.

A new device creates a new V1 cryptographic identity/account.

Do not silently route old pending messages to a new identity.

-------------------------
LICENSE MODEL
-------------------------

Current binding standard license durations:
- 1 month
- 3 months
- 6 months

Do not document 1-year as a current plan.

A historical 1-week admin/support trial concept existed but must NOT be treated
as a general binding V1 license unless a future explicit ADR confirms it.

License status is separate from cryptographic identity.

License expiry:
- must not delete E2EE private keys;
- must not become the encryption key;
- controls product/service access according to final product flow.

-------------------------
CRYPTO / E2EE
-------------------------

Current direction:
Android/Kotlin
→ narrow crypto interface
→ JNI/native boundary
→ Rust
→ vodozemac/Olm

Binding:
- vodozemac/Olm is the V1 1:1 E2EE direction.
- Do NOT use OpenPGP as an additional normal-chat encryption layer.
- libsignal is NOT the selected current E2EE library.
- Do NOT invent a custom Double Ratchet.
- Do NOT invent custom DH, KDF, AEAD, MAC, signatures, RNG, safety numbers,
  key hierarchy, or vodozemac APIs.
- Actual vodozemac API is source of truth for concrete session-init/prekey behavior.
- Private E2EE identity state stays local.
- Private Olm session/ratchet state stays local.
- Public session-initialization material may be stored/distributed by the server.
- Fallback/one-time-key terminology must be mapped to the actual vodozemac API,
  not Signal terminology invented by documentation.

Current implemented/reported dependency state:
- vodozemac 0.10.0
- aes-gcm 0.10.3
- Rust cargo test: 14/14 PASS

This is functional test evidence, NOT proof of production security.

-------------------------
KEY SEPARATION
-------------------------

Keep distinct:
1. E2EE identity/private state
2. Olm session/ratchet state
3. local state-protection key
4. device-authentication key
5. access/refresh/session tokens
6. future attachment encryption key

Do not collapse them into one generic master key.

-------------------------
LOCAL CRYPTO STORAGE
-------------------------

Current implementation direction:
- Android Keystore non-extractable master/wrapping key
- random 32-byte local state-protection key
- AES-256-GCM authenticated protection of serialized Rust/vodozemac state
- `allowBackup=false`
- no V1 cloud private-state restore

Current serialization format has no explicit version byte.
This is an OPEN/HARDENING item and must be documented, not silently claimed solved.

Do not claim arbitrary vodozemac objects are stored directly as Keystore keys.

-------------------------
KEY VERIFICATION
-------------------------

Verification is required.

Contact relationship state and trust state are distinct.

Accepted contact != verified contact.

Local trust states should conceptually include:
- UNKNOWN / UNVERIFIED
- VERIFIED
- KEY_CHANGED / SECURITY_CHANGE

A verified E2EE identity changing:
VERIFIED
→ KEY_CHANGED / UNVERIFIED
→ user warning
→ explicit re-verification
→ VERIFIED

Never silently preserve VERIFIED trust across a new identity.

SAS and/or QR are the V1 verification UX direction,
but use established vodozemac/Matrix verification semantics/APIs.

Do NOT invent:
- custom cryptographic safety-number algorithms
- custom fingerprint protocols
- custom QR cryptographic binding

The server is NOT the final trust authority.

-------------------------
DEVICE AUTHENTICATION
-------------------------

Device authentication is separate from E2EE.

Current direction:
- Ed25519 device-auth keypair
- private device-auth key local
- public key server-side
- short-lived access/session concept
- revocable refresh/session mechanism
- request freshness/replay protection

Historical design requires binding signed requests conceptually to:
- method
- path
- timestamp/freshness
- nonce/request ID
- body hash
- canonical deterministic bytes

IMPORTANT:
The exact production auth/token/challenge/signature contract is still OPEN.
Do not invent the final protocol in documentation.

-------------------------
MESSAGE LIFECYCLE
-------------------------

Conceptual states:
- COMPOSING
- ENCRYPTING
- QUEUED
- SENT
- DELIVERED
- READ (optional)
- FAILED
- RETRY

Meanings:
- SENT = backend accepted/persisted ciphertext.
- DELIVERED = recipient device received encrypted message.
- READ = optional receipt.

Sender flow:
plaintext local
→ CryptoService
→ vodozemac encrypt
→ encrypted outbox
→ authenticated API
→ server persists ciphertext
→ ACK
→ SENT

Recipient:
sync/fetch ciphertext
→ local dedup
→ local decrypt
→ local protected storage/UI

Requirements:
- random globally unique `message_id`
- retry uses same logical message ID
- deduplication/idempotency
- replay handling
- manipulated ciphertext fails safely
- server timestamp is not cryptographic truth
- push is not delivery truth

Privacy defaults:
- no typing indicator in V1
- no global online status
- no last seen

Read receipts may be optional/user-configurable.

-------------------------
CONTACTS / DISCOVERY
-------------------------

- username/public identifier and QR/contact identifier direction
- contact requests
- accept/reject/block
- no unrestricted global directory
- anti-enumeration controls
- local nicknames stay local where possible
- accepted != verified

-------------------------
PUSH / OFFLINE
-------------------------

Push is wake-up only.

Push payload must NOT contain:
- message plaintext
- message preview
- attachment plaintext
- E2EE keys

Push provider is not a trust source.

Push may be:
- delayed
- lost
- duplicated

Message sync must work independently of push.

Provider/transport selection is NOT fully frozen.
Do NOT state UnifiedPush+FCM fallback as the current binding architecture.

Push tokens:
- separate from E2EE/device auth
- can rotate
- revoked with device

Offline recipient:
- backend may temporarily queue ciphertext
- exact TTL remains OPEN

-------------------------
ATTACHMENTS
-------------------------

Do not send large files as ordinary Olm message bodies.

V1 direction:
file
→ local metadata minimization where appropriate
→ random attachment key
→ local authenticated encryption
→ encrypted blob storage

Attachment key + sensitive metadata are transported inside E2EE message payload.

Backend must not receive:
- attachment plaintext
- attachment key in plaintext

XChaCha20-Poly1305 is the planned attachment AEAD direction
IF supported by the final established maintained Rust library.

Do not document it as implemented.

Generate thumbnails locally where possible.
Do not claim perfect metadata anonymity.

-------------------------
BACKEND / SUPABASE
-------------------------

Architecture:
Android
→ authenticated HTTPS API
→ anoX backend/service layer
→ Supabase/PostgreSQL infrastructure

Supabase is infrastructure, NOT:
- E2EE key vault
- cryptographic trust authority
- recovery authority
- message plaintext processor

V1 backend style:
modular monolith, not premature microservices.

Logical modules:
- account/identity
- license
- auth/device
- keys/session-init
- contacts
- messaging
- delivery/sync
- attachments
- push
- abuse/security
- account lifecycle

Never ship in APK/Git/logs:
- service-role key
- DB password
- backend secrets
- provider secrets

Postgres RLS is defense in depth, not a replacement for backend authorization.

Use migrations.
Separate dev/staging/prod.

-------------------------
DATABASE
-------------------------

Final DB schema is NOT frozen.

There is an explicit historical conflict:
RAW1.63 contained more license/prekey/delivery/receipt structures.
RAW1.70 was called "final" but omitted some still-required domains.

Therefore DO NOT present RAW1.70 as final current schema.

Logical domains discussed:
- accounts
- devices
- licenses
- account_licenses
- identity/public key material
- device_auth_keys
- sessions
- one-time/session-init public material
- contacts
- conversations
- conversation_members
- messages
- message_queue/delivery
- receipts
- attachments
- push registrations
- security events
- rate limits

Never store:
- message plaintext
- E2EE private keys
- private session state
- attachment plaintext
- recovery secrets

A future DB-SCHEMA-V1-FROZEN decision is required before migrations.

-------------------------
WIRE / API
-------------------------

REST/HTTPS `/v1` direction.

API version and cryptographic/wire protocol version are separate.

Outer envelope contains only server-required operational data.

Sensitive semantic metadata should be inside encrypted payload when the server
does not need it.

Sender identity should be derived/validated from authenticated device context,
not blindly accepted from JSON.

Cursor-based sync/pagination direction.

Exact endpoint names and final `/sync` contract remain OPEN.

Standardized minimal error model.
No internal SQL/stack trace leakage.

-------------------------
API SECURITY / ABUSE
-------------------------

Required:
TLS
→ device auth
→ freshness/replay checks
→ validation
→ authorization
→ rate limits/abuse controls
→ business logic
→ DB/RLS

Requirements:
- object-level authorization
- nonce/request ID
- timestamp/freshness
- idempotency
- request/body size limits
- attachment quotas
- concurrency limits
- timeouts
- contact spam controls
- auth/license brute-force controls
- anti-enumeration
- parameterized queries/safe ORM

Certificate pinning is OPEN.
Do NOT state it as mandatory V1 architecture.

Do NOT require dummy traffic as an implemented V1 feature.

-------------------------
LOCAL DEVICE SECURITY
-------------------------

Protect:
- E2EE identity
- Olm sessions
- device auth key
- local DB
- contacts
- encrypted outbox
- attachment material

Rules:
- no plaintext secrets in SharedPreferences/JSON/external storage
- neutral lock-screen notifications
- no plaintext push
- screenshot/recent-app protection where appropriate
- clipboard minimization
- app lock / biometric authorization may be used
- biometric is NOT E2EE key
- no cloud backup of E2EE private state
- sensitive temp files short-lived
- production logs privacy-minimal

Logout != delete.

Wipe/delete:
- revoke sessions/server state as appropriate
- cryptographically destroy local protection material
- remove local encrypted DB/temp/cache as practical

Do not claim guaranteed physical flash erasure.

-------------------------
METADATA / PRIVACY
-------------------------

Do NOT market V1 as metadata-free.

Backend/infrastructure may observe:
- account/device IDs
- routing/conversation relationship
- timestamps
- ciphertext size
- delivery state
- IP at infrastructure layer
- push provider/token timing metadata

Defaults:
- no last seen
- no global online
- no typing
- no behavioral analytics
- no phonebook upload
- local contact/chat names local where possible

IP/security logs:
purpose-limited and minimized.
Exact retention remains OPEN.

Padding/timing obfuscation/sealed-sender-like routing are future options,
not current V1 promises.

-------------------------
SUPPORT ACCOUNT
-------------------------

Binding product requirements:
- anoX Support chat exists / is pinned or clearly fixed in the app UX.
- Support chat uses the same E2EE content-protection principles.
- Support/admin has no universal decryption bypass.
- Support staff must not receive user private E2EE keys.

NOT currently frozen:
- support virtual-device architecture
- HA/load balancing model
- support key backup
- special retention
- ticket-system integration
- server-signed support trust model

Do not present those as binding V1 cryptographic architecture.

-------------------------
THREAT MODEL
-------------------------

Must include:
- DB dump
- full backend compromise
- network MITM
- initial key substitution
- later identity replacement
- replay
- ciphertext manipulation
- server deletion/blocking/reordering
- stolen device
- endpoint compromise
- push provider
- object storage leak
- DoS/flooding
- enumeration
- metadata analysis
- malicious APK/client
- supply-chain compromise
- insider/admin

Security limitation:
A compromised endpoint may expose plaintext because plaintext exists locally
before encryption / after decryption.

E2EE does not guarantee availability or metadata anonymity.

-------------------------
SUPPLY CHAIN / TESTING
-------------------------

Requirements:
- pinned/controlled dependencies
- lockfiles
- secret scanning
- dependency/security scanning
- SBOM before release
- signing/provenance
- negative security tests
- DB dump no-plaintext test
- revoked device denied test
- identity-change warning test
- malformed/modified ciphertext safe failure
- independent external security/crypto audit before strong commercial claims

==================================================
2. CURRENT IMPLEMENTATION STATUS — MUST BE REFLECTED
==================================================

Actual repository state currently includes:

Android:
- AGP 9.1.1
- Kotlin 2.2.10
- Gradle Wrapper 9.3.1
- compileSdk 34
- targetSdk 34
- minSdk 26
- Java/Kotlin target 17
- `ndkVersion = "26.2.11394342"` IS CURRENTLY PRESENT

Crypto:
- vodozemac 0.10.0
- aes-gcm 0.10.3
- Rust crypto module
- JNI bridge
- Android CryptoBridge
- Android Keystore state-key wrapping
- `allowBackup=false`
- arm64-v8a `libanox_crypto.so`
- x86_64 `libanox_crypto.so`
- Rust `cargo test`: latest verified report 14/14 PASS
- Android APK/test APK build/link path previously PASS
- Android runtime instrumentation remains UNVERIFIED
- GrapheneOS runtime remains UNVERIFIED

Product:
- MainActivity is still minimal
- backend directory is empty
- root tests directory is empty
- no production account/auth
- no database
- no messaging transport
- no real chat UI
- no contacts
- no push
- no attachments

Overall project weighted progress remains approximately 22%.

==================================================
3. CODE GAPS FOUND BY REPOSITORY AUDIT
==================================================

DO NOT FIX THESE IN THIS DOCSYNC TASK.

Document them in:
`docs/reports/current-code-gap-audit.md`

Include at minimum:

CODE-CRITICAL-001
Raw pointer JNI handles:
`Box::into_raw`, `Box::from_raw`, direct pointer dereference from Kotlin Long.
Potential use-after-free/double-free/type-confusion after destruction.

CODE-CRITICAL-002
Some Android negative tests pass Identity handles to APIs expecting Session handles.
Because both are untyped Long handles, this can cause native type confusion / UB.

CODE-HIGH-003
No centralized panic containment around JNI extern boundary.

CODE-MEDIUM-004
Potential session pointer leak in inbound-session JNI error path after allocation.

CODE-MEDIUM-005
Serialized crypto state currently has no explicit version byte/envelope version.

CODE-MEDIUM-006
`CryptoSerializer::new()` assumes a 32-byte key and can panic if misused.

CODE-MEDIUM-007
Production logging still uses `Log.e(..., exception)` and requires later redaction/hardening review.

CODE-MEDIUM-008
`destroyAllCrypto()` currently deletes the Keystore entry but does not itself remove all
wrapped/local/future DB/temp artifacts.

CODE-INFO-009
Instrumentation tests exist but runtime execution is still unverified.

CODE-INFO-010
NDK is already pinned in actual code, so older docs saying "NDK not pinned" are stale.

Do not claim these issues are fixed.

==================================================
4. FILE-BY-FILE REQUIRED DOCUMENTATION ACTIONS
==================================================

Review EVERY `.md` in the repository.

Required explicit actions:

1. `README.md`
   REWRITE to current architecture/status.
   Remove Raw1.1/current-crypto-not-implemented claims.
   Do not claim GitHub remote is configured unless verified.

2. `CHANGELOG.md`
   UPDATE Unreleased with:
   - Rust/vodozemac foundation
   - OlmMessage fix
   - AES-CBC → AES-GCM
   - 14/14 Rust tests
   - Android JNI build/link
   - Keystore wrapping
   - allowBackup=false
   - native ABIs
   - instrumentation tests written
   - runtime still unverified
   - current known JNI safety gap recorded

3. `docs/architecture/key-architecture.md`
   COMPLETELY REWRITE as current vodozemac-based key/state architecture.
   Remove Signal-like invented key hierarchy, backup, recovery, multi-device.

4. `docs/decisions/open-decisions.md`
   COMPLETELY REWRITE.
   Close decisions already decided.
   Keep only genuinely OPEN architecture decisions.

5. `docs/security/account-recovery.md`
   Preserve old analysis only as HISTORICAL/SUPERSEDED.
   Move historical content to `docs/history/raw1.1/account-recovery-analysis.md`
   if appropriate.
   Create current V1 no-recovery spec.

6. `docs/security/android-jni-crypto-validation-report.md`
   Keep as historical report/evidence.
   Add a corrections header:
   - JDK21 requirement claim is superseded/corrected by current project review.
   - current repo has `ndkVersion = "26.2.11394342"`.
   - Android runtime remains unverified.
   - do not rewrite old test execution as PASS.

7. `docs/security/crypto-foundation-completion-report.md`
   Keep as HISTORICAL DEVIN REPORT.
   Add header linking to later Rust validation.
   Do not use as canonical architecture.

8. `docs/security/crypto-foundation-security-review.md`
   Mark historical/current-status boundary.
   Remove ambiguity that old CBC is current.
   Point to current AES-GCM state.

9. `docs/security/crypto-foundation-validation-report.md`
   Preserve as evidence that Rust tests were 14/14 PASS.
   Add current status header:
   Rust verified at implemented test level; Android runtime still pending.

10. `docs/security/cryptography-comparison.md`
    Mark/move as SUPERSEDED historical decision input.
    Current decision = vodozemac/Olm.
    libsignal/OpenPGP are not current implementation choices.

11. `docs/security/cryptography-status.md`
    COMPLETELY REWRITE to current implementation state.

12. `docs/security/device-loss-scenarios.md`
    COMPLETELY REWRITE for one-device/no-recovery V1.

13. `docs/security/metadata-analysis.md`
    UPDATE to current metadata-minimization model.
    Remove broad "zero-knowledge"/metadata-elimination claims.

14. `docs/security/push-notifications.md`
    UPDATE.
    Provider choice is not frozen.
    Push = wake-up only / no plaintext.

15. `docs/security/security-requirements.md`
    COMPLETELY REWRITE.
    This is a critical authoritative file.
    Remove:
    - key backup requirement
    - multi-device requirements
    - recovery codes
    - account recovery
    - mandatory certificate pinning
    - dummy traffic requirement
    - secure E2EE-key backup/recovery
    Replace with current Security Invariants and V1 requirements.

16. `docs/security/server-trust-model.md`
    UPDATE from broad "zero-knowledge" branding to precise:
    server untrusted for content; metadata remains visible; availability not guaranteed.

17. `docs/security/threat-model.md`
    REWRITE/EXPAND to current RAW1.75 threat model.

18. `docs/specifications/device-identity.md`
    COMPLETELY REWRITE:
    one active device; no add-device/multi-device sync; random device_id;
    device auth separate; no phone/email requirement.

19. `docs/specifications/public-key-verification.md`
    COMPLETELY REWRITE:
    established SAS/QR semantics; local trust states; no custom safety-number protocol;
    no blind "mark trusted" across identity change.

20. `docs/specifications/support-account.md`
    REWRITE to only current binding support product/security requirements.
    Mark operational support HA/key-backup/ticket details OPEN rather than binding.

21. `docs/specifications/user-identity.md`
    COMPLETELY REWRITE:
    random account_id; username/public identifier separate; QR;
    no global directory; no phone/email; account/device/E2EE separation.

==================================================
5. CREATE MISSING CURRENT CANONICAL DOCS
==================================================

Create:

`docs/current/SYSTEM_ARCHITECTURE.md`
`docs/current/SECURITY_INVARIANTS.md`
`docs/current/ACCOUNT_LICENSE_REGISTRATION.md`
`docs/current/KEY_AND_SESSION_ARCHITECTURE.md`
`docs/current/LOCAL_DEVICE_SECURITY.md`
`docs/current/AUTH_PROTOCOL_STATUS.md`
`docs/current/API_WIRE_PROTOCOL.md`
`docs/current/MESSAGE_LIFECYCLE.md`
`docs/current/CONTACTS_AND_VERIFICATION.md`
`docs/current/PUSH_OFFLINE.md`
`docs/current/ATTACHMENTS.md`
`docs/current/METADATA_PRIVACY.md`
`docs/current/ACCOUNT_DEVICE_LIFECYCLE.md`
`docs/current/BACKEND_ARCHITECTURE.md`
`docs/current/DATABASE_ARCHITECTURE.md`
`docs/current/THREAT_MODEL.md`
`docs/current/OPEN_ARCHITECTURE_ITEMS.md`

Also create or update at project root:

`PROJECT_STATE.md`

Do not fabricate exact historic prompts in this task.

If `FORTSCHRITT.md`, `MAIN_PLAN_DE.md`, or `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
are not currently in the repository, create placeholders that clearly state:

"Canonical version is maintained by ChatGPT coordination and must be imported/
updated from the current Master Development Archive."

Do NOT invent missing historical prompt wording.

==================================================
6. DOCUMENT STATUS / DISCOVERY RULE
==================================================

Every current architecture file must clearly identify itself as CURRENT.

Every historical analysis/report must clearly state that it is:
HISTORICAL or SUPERSEDED.

Create:
`docs/README.md`

It must explain:

Implementation truth:
repository code + executed tests

Architecture truth:
`docs/current/` + current Security Invariants + accepted ADRs

Historical docs:
`docs/history/`

Reports:
historical evidence, not automatically current requirements

Future coding agents MUST NOT treat Raw1.1 historical docs as current.

==================================================
7. DO NOT ERASE HISTORY
==================================================

Do not simply delete old architectural reasoning.

Move clearly obsolete analyses to:
`docs/history/raw1.1/`

Preserve:
- original context
- old recommendation
- why superseded
- current replacement link

Historical Devin validation reports should remain intact enough to preserve evidence.

Do not change an old report from "NOT EXECUTED" to "PASS".

==================================================
8. CROSS-DOCUMENT CONSISTENCY CHECK
==================================================

After updates, search the entire repository documentation for:

Raw1.1
recovery
recovery code
multi-device
5 devices
10 devices
libsignal
OpenPGP
PGP
FCM fallback
UnifiedPush default
key backup
server-signed identity trust
certificate pinning MUST
dummy traffic MUST
JDK 21 required
NDK not pinned
security mechanisms not implemented
initial foundation only

For every match:
- determine whether it is historical context;
- if historical, label it clearly;
- if current/binding, remove or correct it.

Also search for contradictory license durations:
- 1 year / 12 months must not remain as current binding V1 plan.
- current standard plans: 1, 3, 6 months.

==================================================
9. NO CODE FEATURE CHANGES
==================================================

This task is documentation synchronization.

Do NOT:
- redesign JNI
- fix pointer handles
- modify vodozemac integration
- implement auth
- implement backend
- implement DB
- implement messaging
- implement recovery
- change cryptographic primitives
- upgrade dependencies

You MAY update code comments only if they contain clearly obsolete architectural claims,
but do not alter runtime behavior.

==================================================
10. DELIVERABLE
==================================================

Create:
`docs/reports/documentation-raw-sync-report.md`

Report:

A. every Markdown file found
B. old status
C. action taken
D. new status
E. files moved to history
F. files rewritten
G. new current canonical docs created
H. remaining architecture OPEN items
I. contradictions that could not be resolved without a new architecture decision
J. confirmation that no functional code was changed
K. code gaps recorded in `current-code-gap-audit.md`
L. exact recommended next engineering task

Also output a concise terminal summary:

DOCUMENTATION SYNC:
- files scanned: X
- current files: X
- rewritten: X
- historical/superseded: X
- new canonical docs: X
- unresolved architecture decisions: X
- functional code changes: 0

==================================================
11. ACCEPTANCE CRITERIA
==================================================

PASS only if:

- all project Markdown files were reviewed;
- no unlabeled Raw1.1 file can be mistaken for current architecture;
- V1 no-recovery is consistent everywhere current;
- V1 one-device is consistent everywhere current;
- vodozemac is consistently the current E2EE direction;
- OpenPGP/libsignal are historical only;
- current security requirements no longer require recovery/multi-device;
- current push docs do not falsely freeze UnifiedPush/FCM;
- current identity docs match random account_id/device_id + username/QR separation;
- current server model accurately admits metadata;
- current DB docs explicitly state schema is not frozen;
- current Auth docs explicitly state final signing/token contract is still OPEN;
- current project status reflects Rust 14/14 + Android build/link + runtime unverified;
- historical reports retain truthful original test status;
- no functional code was changed.

After this DOCSYNC task, STOP.

Do not begin the next code task automatically.
```
