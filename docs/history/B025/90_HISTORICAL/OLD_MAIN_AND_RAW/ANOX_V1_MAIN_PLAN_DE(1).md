# anoX Messenger V1 — MAIN PLAN

**Sprache:** Deutsch  
**Zweck:** Verbindlicher Gesamtentwicklungsplan vom bisherigen Projektstand bis zum V1-Endprodukt.  
**Projektmodell:** ChatGPT = Architektur/Koordination/Review, Devin = Implementierung/Test/Report, Git = Implementierungs- und Änderungshistorie.  
**Grundlage:** anoX Master Development Archive v2 AUDITED + bisherige Devin-Reports + aktuelle Architekturentscheidungen.

---

# 0. Leitprinzipien

Die Entwicklung wird nicht als ein großer „Baue die ganze App“-Prompt durchgeführt. Jeder sicherheitskritische Baustein wird einzeln geplant, implementiert, getestet und abgenommen.

Verbindlicher Ablauf:

```text
Architektur / Security Invariants
        ↓
ChatGPT definiert nächsten Arbeitsschritt
        ↓
Nummerierter Devin-Prompt
        ↓
Devin prüft echten Repository-Stand
        ↓
Implementierung
        ↓
echte Builds / Tests
        ↓
Devin-Report
        ↓
ChatGPT Architektur- und Security-Review
        ↓
PASS / FAIL
        ↓
PROJECT_STATE / FORTSCHRITT aktualisieren
        ↓
nächster Prompt
```

## Nicht verhandelbare V1-Regeln

1. Keine Account-Recovery in V1.
2. Verlust des einzigen Geräts + lokalen Crypto-States = Verlust der kryptografischen Identität.
3. Ein aktives Gerät pro Account in V1.
4. E2EE-Private-Keys verlassen das Gerät nicht.
5. Backend erhält niemals Nachrichten-Klartext.
6. Backend erhält niemals Attachment-Key im Klartext.
7. Device-Authentication ist getrennt von E2EE-Identity.
8. Key-Änderungen dürfen nicht stillschweigend vertraut werden.
9. Push enthält keinen Nachrichten-Klartext.
10. Keine selbst erfundenen kryptografischen Primitive oder Protokolle.
11. vodozemac/Olm wird nur über tatsächlich verifizierte APIs verwendet.
12. Geschützte lokale Crypto-Zustände benötigen Vertraulichkeit und Integrität/Authentizität.
13. Keine Secrets, Private Keys, Session-States, Access Tokens oder Message Plaintexts in Logs/Crash-Reports.
14. Lizenzstatus darf nicht zum E2EE-Key werden.
15. Lizenzablauf löscht keine E2EE-Identität.
16. Keine Pflicht zu Telefonnummer/E-Mail für den Kernaccount.
17. Keine unrestricted globale User-Suche in V1.
18. Kein Last Seen, globaler Online-Status oder Typing Indicator in V1.
19. Keine Third-Party Behavioral Analytics in V1.
20. Server-/DB-/Storage-/Transport-Kompromittierung allein darf korrekt implementierte E2EE-Inhalte nicht entschlüsseln können.
21. Endpoint-Kompromittierung kann durch E2EE allein nicht verhindert werden.
22. Closed Source ist eine Distributionsentscheidung, kein Sicherheitsbeweis.

---

# 1. Bereits ausgeführte Phase: Projektbasis und Architektur

## 1.1 Bestehende Android-App

Ausgangslage:
- vorhandenes Android-Projekt;
- Kotlin / Jetpack Compose;
- läuft grundsätzlich auf GrapheneOS;
- vorhandene UI war im Wesentlichen Starter-/Welcome-Zustand;
- kein funktionales Messaging;
- kein Backend;
- keine Datenbank;
- keine Authentifizierung;
- keine Crypto-Bibliothek im ursprünglichen App-Skeleton.

Entscheidung:
- Projekt wird weiterentwickelt;
- kein unnötiger kompletter Neubau als zweites Projekt.

## 1.2 Codebase-Audit

Devin hat den tatsächlichen Repository-Zustand analysiert.

Historisch gemeldete Toolchain:
- Kotlin 1.9.20
- Gradle 9.3.1
- Android Gradle Plugin 8.13.2
- compileSdk 34
- targetSdk 34
- minSdk 26
- Compose BOM 2023.10.01

Diese Werte sind historische Repository-Fakten und müssen vor Toolchain-Arbeiten erneut aus dem tatsächlichen Repo gelesen werden.

## 1.3 Architekturphase

Bereits festgelegt:
- Account-/Device-/E2EE-Identity-Trennung;
- Device Auth getrennt von E2EE;
- V1 Single Device;
- V1 No Recovery;
- Rust-Crypto-Layer;
- vodozemac/Olm;
- Supabase/PostgreSQL als Infrastruktur;
- eigener Backend-Service davor;
- RLS als Defense in Depth;
- E2EE Attachment-Konzept;
- Push als Wake-up;
- lokale Security;
- Threat Model;
- Message States;
- API Security;
- Metadata-Minimierung;
- Contact-/Verification-Konzept;
- License-Laufzeiten;
- Development-/Audit-Regeln.

Status: **ARCHITEKTUR-BASIS ETABLIERT**, einzelne Detailverträge sind absichtlich noch OPEN und werden vor ihrer Implementierung eingefroren.

---

# 2. Bereits ausgeführte Phase: Rust Crypto Foundation

## Ziel

Einen isolierten Rust-Crypto-Layer aufbauen, bevor Backend oder Messaging darauf aufsetzen.

## Implementiert / berichtet

- Rust-Modul `crypto/rust/`
- vodozemac 0.10.0
- JNI/native boundary
- Identity Wrapper
- Session Wrapper
- Crypto Error Model
- State Serialization
- Kotlin `CryptoNative`
- Kotlin `CryptoBridge`
- Kotlin `CryptoResult`
- Kotlin `CryptoError`
- Android-Keystore-Richtung
- Security-Dokumentation

## Erster Blocker

Die erste Version konnte den tatsächlichen vodozemac `OlmMessage`-Flow nicht korrekt verarbeiten.

Ursache laut Devin:
- falsche/ungenügende Nutzung der realen vodozemac Message-Serialization/API.

---

# 3. Bereits ausgeführte Phase: Crypto Blocker Resolution

## Änderungen

Devin hat laut Report:
- reale vodozemac `OlmMessage::to_parts` / `from_parts`-Semantik verwendet;
- `PreKeyMessage::from_bytes` verwendet;
- JNI-Grenze auf expliziten `message_type + ciphertext + length`-Flow umgestellt;
- Alice→Bob→Alice-Test geschrieben;
- Negative Tests ergänzt;
- AES-256-CBC durch AES-256-GCM ersetzt;
- Key Separation weiter abgesichert;
- JNI Checks verbessert;
- No-Recovery bestätigt.

## Ergebnis

Code war implementiert, konnte im damaligen Environment jedoch mangels Rust/Cargo nicht ausgeführt werden.

Status damals:
**IMPLEMENTED / UNVERIFIED**

---

# 4. Bereits ausgeführte Phase: Rust Crypto Validation

## Toolchain

Devin installierte:
- rustc 1.97.1
- cargo 1.97.1
- Host aarch64-apple-darwin

Kompilierte Dependencies:
- vodozemac 0.10.0
- aes-gcm 0.10.3

## Ausgeführte Tests

`cargo test`: **14/14 PASS**

Verifiziert:
- Alice → Bob Session Establishment
- Alice encrypt → Bob decrypt
- Bob encrypt → Alice decrypt
- Invalid ciphertext rejection
- Malformed message rejection
- Modified ciphertext rejection
- Wrong key material rejection
- Wrong session/message type rejection
- Crypto state serialization/restoration
- Corrupted state rejection
- authenticated AES-256-GCM state protection
- Identity Creation
- One-Time-Key Generation
- Key Separation
- No Recovery
- Secret-safe error messages

## Aktueller korrekter Status

**Rust Crypto Foundation = funktional auf Rust-Testebene verifiziert.**

Nicht behaupten:
- gesamte App ist sicher;
- Android Integration ist verifiziert;
- produktionsreif;
- unabhängig auditiert.

---

# 5. AKTUELLER SCHRITT: Android / JNI Crypto Integration

## Ziel

Vollständigen realen Pfad prüfen:

```text
Kotlin
→ CryptoBridge
→ JNI
→ Android Native .so
→ Rust
→ vodozemac
→ Ergebnis zurück nach Kotlin
```

## Muss noch durchgeführt werden

### Toolchain
- tatsächliches Gradle/AGP/Kotlin Setup aus Repo prüfen;
- passende JDK konfigurieren;
- Android SDK/NDK installieren;
- NDK-Version pinnen;
- Rust Android Targets konfigurieren;
- arm64-v8a mindestens für Pixel/GrapheneOS;
- x86_64 für Emulator, falls genutzt.

### Native Build
- Rust `.so` für Android bauen;
- `jniLibs` korrekt erzeugen/einbinden;
- Android Debug APK bauen.

### JNI Tests
Mindestens:
- Native Library lädt;
- Identity Creation über Kotlin/JNI;
- Public Key Export;
- State Serialize;
- State Restore;
- corrupted input fails safely;
- native errors sauber nach Kotlin;
- handles/resources sauber zerstörbar;
- falsche/ungültige Handles fail safe;
- kein Private-Key-Leak in UI/Logs.

### End-to-End via Android Boundary
- Alice→Bob→Alice nicht direkt Rust-only, sondern über Kotlin/JNI.

### AES-GCM Review
Prüfen:
- Key Herkunft;
- Keystore-Wrapping/Protection;
- Nonce/IV Generation;
- Nonce uniqueness;
- Tag handling;
- state versioning;
- corrupted state behavior.

### GrapheneOS
Wenn Gerät vorhanden:
- APK installieren;
- native library laden;
- Crypto initialisieren;
- State speichern;
- App neu starten;
- State wiederherstellen.

## Abnahme

Erst wenn relevante Android/JNI Tests tatsächlich PASS sind:

**CRYPTO FOUNDATION V1 = ACCEPTED**

---

# 6. Phase: Secure Local State & Key Lifecycle Freeze

Diese Phase finalisiert, was lokal dauerhaft gespeichert wird.

## Zu implementieren/finalisieren

- E2EE Identity State
- Olm Session State
- One-Time-/Session-Init Material entsprechend realer vodozemac API
- Local State Protection Key
- Device Auth Private Key
- Access/Refresh Tokens getrennt
- encrypted local DB key
- lifecycle/versioning der serialisierten Crypto States
- schema/version migrations lokaler Crypto-Daten
- secure deletion / crypto erase
- no cloud backup
- no auto restore
- uninstall/clear-data Verhalten
- logout != identity wipe

## Wichtig

Keine erfundenen PreKey/Signal-Strukturen. Tatsächliche vodozemac/Olm API ist Source of Truth.

---

# 7. Phase: Device Authentication Protocol einfrieren

Vor Backend-Code muss der exakte Vertrag beschlossen werden.

## Architektur-Richtung

Separate Device-Auth Keypair:
- Ed25519-Richtung
- private local
- public server-side

Request Authentication berücksichtigt:
- method
- path
- timestamp
- nonce/request ID
- body hash
- signature/canonical bytes

Zusätzlich vorgesehen:
- short-lived access token
- revocable refresh/session mechanism

## Noch OPEN

Exakt definieren:
- Challenge/Registration Flow
- Token lifetime
- refresh rotation
- session revocation
- nonce/freshness window
- canonical serialization
- key rotation
- compromised token behavior
- device revocation semantics

## Output

`AUTH-PROTOCOL-V1-FROZEN.md` + ADR.

Danach erst implementieren.

---

# 8. Phase: Account + License Registration

## Account

- random `account_id`
- random `device_id`
- keine Pflicht-Telefonnummer
- keine Pflicht-E-Mail
- one active device
- no recovery

## License

V1-Laufzeiten:
- 1 Monat
- 3 Monate
- 6 Monate

Historisch zusätzlich vorgesehen:
- 1-Woche-Testlizenz für berechtigte Admin-/Support-Accounts

Falls die 1-Woche-Testlizenz weiterhin Produktanforderung ist, muss sie im finalen License-ADR explizit bestätigt bleiben.

## Grundregeln

- License != Crypto Identity
- License expiry löscht keine Keys
- License expiry sperrt/limitiert Produktzugriff gemäß finalem Product Flow
- Lizenzcodes nicht sequenziell/leicht erratbar
- Server autoritativ für Aktivierung/Status
- vor Ablauf Benutzerhinweis
- Export von Kontakten vor Ablauf kann empfohlen werden

## Registration State

```text
NEW
→ LICENSE_CHECK
→ ACCOUNT_CREATE
→ DEVICE_AUTH_KEY_SETUP
→ E2EE_KEY_SETUP
→ PUBLIC SESSION-INIT MATERIAL UPLOAD
→ SESSION AUTH
→ ACTIVE
```

Fehlgeschlagene partielle Registrierung darf keine unsicheren halbaktiven Accounts erzeugen.

---

# 9. Phase: Backend Foundation

## Architektur

Modularer Monolith, keine unnötigen Microservices.

Logische Module:
- Account / Identity
- License
- Device Authentication
- Device Management
- Key Distribution
- Messaging
- Delivery / Sync
- Contacts
- Attachments
- Push
- Abuse / Security
- Account Lifecycle

## Backend-Regeln

- TLS
- keine DB-Service-Role Keys in App
- keine Server Secrets in APK/Git/Logs
- server-side authorization
- strict validation
- rate limiting
- replay checks
- object-level authorization
- standardized errors
- protocol versioning

---

# 10. Phase: Datenbank-Schema einfrieren

Vor Implementierung muss Konflikt RAW1.63 vs RAW1.70 aufgelöst werden.

## Benötigte logische Domänen

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

## Datenbank-Invarianten

Nie speichern:
- Message Plaintext
- E2EE Private Keys
- Session Private State
- Attachment Plaintext
- Recovery Secret

## Umsetzung

- SQL Migrations
- random IDs
- FK Constraints
- unique constraints
- partial unique active-device constraint
- indexes
- RLS
- least privilege
- dev/staging/prod separation
- migration tests

Output:
`DB-SCHEMA-V1-FROZEN.md`

---

# 11. Phase: Public Key / Session Initialization Distribution

## Ziel

Offline Session Establishment ermöglichen.

Server bekommt ausschließlich öffentliches Material, das die tatsächliche vodozemac/Olm Session Initialization benötigt.

## Implementieren

- public identity material upload
- one-time/session-init public material upload
- fetch flow
- consume/replenish semantics
- fallback semantics nur falls echte vodozemac API dies vorsieht
- authorization
- rate limits
- anti-enumeration
- identity version/change tracking

Private Counterparts bleiben local.

---

# 12. Phase: 1:1 E2EE Messaging Transport

## Send Flow

```text
Compose plaintext locally
→ CryptoService encrypt
→ encrypted outbox
→ authenticated API
→ backend validates
→ ciphertext persisted
→ ACK
→ SENT
```

## Receive Flow

```text
sync/fetch
→ ciphertext
→ local dedup
→ CryptoService decrypt
→ local encrypted DB
→ UI plaintext
```

## Message States

- COMPOSING
- ENCRYPTING
- QUEUED
- SENT
- DELIVERED
- READ optional
- FAILED
- RETRY

## Regeln

- random unique `message_id`
- same retry = same logical message ID
- conflicting same ID rejected
- no server plaintext
- sender derived from auth context
- server timestamps not cryptographic truth
- cursor sync
- malformed ciphertext fail safe

---

# 13. Phase: Local Encrypted Messaging Database & Outbox

Implementieren:
- encrypted message storage
- encrypted contact data where needed
- local conversation state
- encrypted outbox
- retry state
- delivery/read state
- migration/versioning
- no plaintext DB
- no plaintext search indexes that leak content
- app restart persistence
- crash-safe retry

Test:
- DB dump enthält keine Message Plaintexts.

---

# 14. Phase: Contacts / Discovery

## Funktionen

- username/contact identifier
- QR contact exchange
- contact request
- accept
- reject
- block
- unblock

## Regeln

- username != account ID != device ID != crypto identity
- keine unrestricted global directory
- protection against enumeration
- local nickname stays local where possible
- accepted != verified

---

# 15. Phase: Key Verification

## Trust States

- UNKNOWN / UNVERIFIED
- VERIFIED
- KEY_CHANGED / SECURITY_CHANGE

## Funktionen

- SAS und/oder QR gemäß etabliertem vodozemac/Matrix-Mechanismus
- verification events local
- server transportiert höchstens Protokollnachrichten
- server ist nicht Trust Authority

## Identity Change

```text
VERIFIED
→ new identity key observed
→ KEY_CHANGED / UNVERIFIED
→ warning
→ manual reverification
→ VERIFIED
```

Nie neue Identity automatisch als vorher verified übernehmen.

---

# 16. Phase: Push & Offline Messaging

## Push

- wake-up only
- no plaintext
- no sender/message preview in provider payload
- opaque event
- duplicate tolerant
- push failure darf Message nicht verlieren

## Offline Queue

- ciphertext server-side temporary queue
- TTL
- delivered deletion eligibility
- sync works without push

## Push Token

- distinct from crypto/device auth
- rotate/update
- revoke with device

---

# 17. Phase: Attachments

## Flow

```text
File local
→ metadata minimization
→ random attachment key
→ local authenticated encryption
→ encrypted blob upload
→ attachment key + sensitive metadata inside E2EE message
```

## Architektur-Richtung

XChaCha20-Poly1305, sofern in der final ausgewählten gepflegten Rust-Library sauber unterstützt.

## Server sieht nicht

- attachment plaintext
- attachment key
- original filename where not needed
- sensitive MIME metadata where not needed

## Zusätzlich

- local thumbnails
- EXIF/metadata stripping where appropriate
- temp file cleanup
- attachment size limits
- quotas
- no auto execution

---

# 18. Phase: Account / Device Lifecycle

Implementieren:
- logout
- session revoke
- device revoke
- account delete
- local wipe
- username change
- identity change
- license expiry
- lost device state

## Regeln

Logout:
- server session revoked
- long-term identity remains local

Delete:
- authenticated confirmation
- sessions/device revoked
- server data deletion per policy
- local cryptographic wipe

Lost device:
- no recovery
- new account/new identity

Old pending messages:
- never silently redirect to new identity.

---

# 19. Phase: Privacy / Metadata / Local UX Hardening

Implementieren:
- neutral notification defaults
- sensitive recent-app preview protection
- screenshot protection where useful
- clipboard minimization
- app lock
- biometric authorization where appropriate
- no last seen
- no typing
- no global online
- local nicknames
- temp file discipline
- privacy-safe logs

Open policy values finalisieren:
- IP retention
- message TTL
- attachment TTL
- security event retention

---

# 20. Phase: API Abuse & Security Controls

Implementieren/testen:
- rate limits
- body size limits
- attachment quotas
- concurrency limits
- timeouts
- contact spam control
- license/auth brute force controls
- user enumeration resistance
- safe error model
- parameterized DB access
- replay rejection
- revoked device denial
- malformed request rejection

Keine serverseitige Content-Moderation auf Message Plaintext, da E2EE.

---

# 21. Phase: Vollständige Integration- und Security-Tests

Pflichtfälle:
- DB dump no plaintext
- backend compromise model
- revoked device cannot authenticate
- identity change warning
- modified ciphertext fails
- wrong session fails
- replay fails
- duplicate ID dedup
- offline retry
- push duplicate
- push failure recovery
- attachment blob storage compromise
- corrupted local state
- uninstall/clear data behavior
- license expiry behavior
- account deletion
- contact enumeration resistance
- API object authorization
- rate limits
- malicious attachment handling

---

# 22. Phase: GrapheneOS End-to-End Validation

Auf echten unterstützten Pixel-Geräten:
- Installation
- registration
- crypto initialization
- send/receive
- restart persistence
- offline
- push
- attachment
- lock/wipe
- screenshot/privacy
- revoke/delete
- performance/battery
- update behavior

GrapheneOS ist Zielplattform, aber keine Sicherheitsgarantie für fehlerhaften App-Code.

---

# 23. Phase: GitHub / CI / Supply Chain

## Repository

Private GitHub Repository.

Speichern:
- Code
- Master Archive
- Prompts
- Devin Reports
- ADRs
- CURRENT_STATE
- CHANGELOG
- Tests
- migrations

## Workflow

Devin arbeitet über Branch/PR.

Main:
- protected
- PR required
- passing checks required

CI:
- `cargo test`
- Android build
- Android/JNI tests
- lint/static analysis
- dependency scan
- secret scan
- migration tests

Secrets:
- GitHub Secrets/Environments
- niemals Repository/Prompt/Logs

Supply Chain:
- pinned dependencies
- Cargo.lock / Gradle lock strategy
- SBOM
- dependency/license review
- release signing
- provenance

---

# 24. Phase: Security Audit Preparation

Vor externem Audit:
- Architektur frozen
- threat model current
- SBOM
- build instructions
- reproducible test procedure
- crypto boundary docs
- key lifecycle
- API contract
- DB schema
- security invariants
- known limitations
- test evidence
- dependency inventory
- release signing process

Dann unabhängiger Security/Crypto-Audit.

---

# 25. Phase: V1 Release Candidate

Erst nach bestandenen internen Tests und Audit-Fixes.

V1 Release Candidate muss mindestens können:
- Account + License
- Single Device
- 1:1 E2EE
- Contact request
- QR/username exchange
- Key Verification
- Offline encrypted messaging
- delivery/read optional
- Push without plaintext
- Encrypted attachments
- revoke/delete
- local secure storage
- GrapheneOS operation
- production backend
- rate/abuse protections
- migrations
- CI/release pipeline

Nicht automatisch V1:
- recovery
- multi-device
- group chat
- calls
- presence/typing
- global directory

---

# 26. Definition „Fertig“

anoX V1 gilt technisch nicht als fertig, wenn nur:
- APK startet;
- Nachrichten gesendet werden;
- Crypto Unit Tests bestehen.

Fertig bedeutet:
1. definierter V1 Scope vollständig;
2. alle kritischen Security Invariants umgesetzt;
3. echte End-to-End Tests erfolgreich;
4. GrapheneOS validiert;
5. Backend/DB/Client Security Tests erfolgreich;
6. keine bekannten kritischen Blocker;
7. Release Pipeline;
8. externer Review/Audit vor starken kommerziellen Security Claims.
