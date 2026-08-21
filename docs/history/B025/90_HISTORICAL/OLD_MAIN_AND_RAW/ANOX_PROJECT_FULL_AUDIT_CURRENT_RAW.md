# anoX Messenger — Vollständiger Projekt-Audit gegen aktuelle RAW-/Master-Architektur

**Audit-Datum:** 19.08.2026  
**Geprüfte Quelle:** vollständiger hochgeladener Projektordner `anoX Messanger.zip`  
**Aktuelle Architektur-Baseline:** konsolidierte RAW1.60–RAW1.75-Entscheidungen + aktueller anoX Master Development Archive / Main Plan / Security Invariants  
**Wichtig:** Es wird bewusst **keine neue erfundene RAW-Nummer** vergeben.

---

# 1. Umfang des Scans

Im ZIP wurden insgesamt **10.121 Dateien** gefunden.

Ein großer Teil davon besteht aus erzeugten Build-/Compiler-Artefakten:
- Rust `target/`
- Gradle Build Outputs
- `.o`, `.rlib`, `.rmeta`
- Android Build Outputs
- Cache-/Indexdateien
- `__MACOSX`

Diese Binär-/Cache-Artefakte wurden inventarisiert, aber nicht wie Quellcode semantisch bewertet.

Vollständig geprüft wurden die relevanten:
- Kotlin-Dateien
- Rust-Dateien
- Gradle/Kotlin-Builddateien
- AndroidManifest
- Cargo.toml / Cargo.lock-Struktur
- Testcode
- `.gitignore`
- Projektstruktur
- alle **21 Markdown-Dokumente**

Nach Ausschluss generierter Build-/Cache-Verzeichnisse blieben rund **125 relevante Quell-/Konfigurations-/Dokumentationsdateien**.

---

# 2. Tatsächlicher Code-Stand

## Android-App

Vorhanden:
- Kotlin / Jetpack Compose
- `MainActivity.kt`
- Theme-Dateien
- App startet als Minimal-/Welcome-App
- keine echte Messenger-UI
- keine Navigation
- keine Kontakte
- kein Login/Registration
- kein Chat
- kein Messaging Repository
- kein lokales Message-DB-Modell

## Backend

`backend/` ist leer.

Nicht implementiert:
- API
- Auth
- Account
- License
- Message Routing
- Key Distribution
- Contacts
- Attachments
- Push
- Database access

## Tests

Das zentrale Root-`tests/`-Verzeichnis ist leer.

Vorhanden sind:
- Rust Crypto Tests
- Android Crypto Instrumentation Tests

## Tatsächliche Build-Konfiguration

Im Repository aktuell:
- AGP: **9.1.1**
- Kotlin: **2.2.10**
- Gradle Wrapper: **9.3.1**
- compileSdk: **34**
- targetSdk: **34**
- minSdk: **26**
- Java/Kotlin JVM Target: **17**
- NDK ist aktuell bereits explizit gepinnt:
  `26.2.11394342`

Das widerspricht dem älteren `android-jni-crypto-validation-report.md`, der noch behauptet, `ndkVersion` sei nicht gesetzt.

## Rust Crypto

Vorhanden:
- vodozemac `0.10.0`
- aes-gcm `0.10.3`
- JNI `0.21.1`
- zeroize `1.8`
- `Cargo.lock`
- Identity Wrapper
- Session Wrapper
- One-Time-Key Funktionen
- AES-256-GCM State Serialization
- Android JNI Bridge

Aus unserem letzten verifizierten Devin-Report:
- `cargo test`: **14/14 PASS**

Aktueller Code entspricht grundsätzlich diesem Stand.

---

# 3. Sehr wichtige Code-Funde

Diese Punkte bedeuten **nicht**, dass die bisherige Rust-Crypto-Arbeit wertlos ist. Sie sind konkrete Integrations-/Safety-Punkte, die vor der endgültigen Crypto-Abnahme behoben bzw. real getestet werden müssen.

## CODE-CRITICAL-001 — Raw Pointer Handles / Use-after-free-Risiko

`crypto/rust/src/lib.rs` nutzt u.a.:

```text
Box::into_raw(...)
Box::from_raw(...)
unsafe { &*(handle as *const Identity) }
unsafe { &mut *(handle as *mut Session) }
```

Die JNI-Grenze behandelt Native Pointer direkt als Kotlin-`Long`.

Problem:
Nach `cryptoDestroyIdentity()` / `cryptoDestroySession()` bleibt der alte numerische `Long` auf Kotlin-Seite weiterhin existent.

Ein späterer Zugriff kann einen bereits freigegebenen Pointer dereferenzieren.

Das kann zu:
- Use-after-free
- Double free
- Speicherfehler
- Prozessabsturz
- Undefined Behavior

führen.

Der vorhandene Instrumentation-Test `destroyedHandleDoesNotCrash()` soll genau diesen Bereich testen, wurde aber bisher nicht ausgeführt.

**Bewertung:** KRITISCH VOR ENDGÜLTIGER JNI-ABNAHME.

Mögliche spätere Architektur:
- validierte Handle Registry
- opaque generation-counted handles
- sichere Ownership-Schicht

Die konkrete Lösung darf nicht im Dokumentations-Sync erfunden werden; dafür folgt ein separater Code-/Safety-Task.

---

## CODE-CRITICAL-002 — Instrumentation Tests besitzen Type-Confusion-Risiko

In `CryptoInstrumentedTest.kt` werden in mehreren Negative Tests `Identity`-Handles an `bridge.decrypt(...)` übergeben, obwohl dort ein `Session`-Handle erwartet wird.

Beispiele:
- `invalidCiphertextRejectsDecryption`
- `invalidMessageTypeRejectsDecryption`
- `malformedMessageRejectsDecryption`

Da Identity und Session beide als untypisierte `Long`-Pointer transportiert werden, kann der native Code den falschen Rust-Typ dereferenzieren.

Das ist ein weiterer Beleg, dass rohe Pointer-Handles an der Kotlin/JNI-Grenze zu schwach typisiert sind.

**Bewertung:** KRITISCH VOR AUSFÜHRUNG DER KOMPLETTEN RUNTIME-SUITE.

---

## CODE-HIGH-003 — Kein expliziter Panic-Containment-Wrapper an JNI

Die `extern "system"` JNI-Funktionen besitzen keinen zentralen Panic-/FFI-Safety-Wrapper.

Unsere Architektur fordert:
- kein Panic über JNI-Grenze
- kontrollierte Fehler
- kein Secret Leak

Vor finaler Abnahme muss überprüft werden, wie unerwartete Rust-Panics an dieser Boundary behandelt werden.

---

## CODE-MEDIUM-004 — Session-Leak bei seltenem JNI-Output-Fehler möglich

Bei `cryptoCreateInboundSession()` wird ein Session-Pointer via `Box::into_raw()` erzeugt, bevor sicher feststeht, dass der Pointer erfolgreich in `out_session` geschrieben werden kann.

Scheitert der JNI-Array-Write, kann der erzeugte Pointer nicht mehr zurückgeholt werden.

**Bewertung:** Memory-Leak Edge Case.

---

## CODE-MEDIUM-005 — Crypto State Format besitzt keine explizite Version

`serialization.rs` speichert:

```text
[12 byte nonce][ciphertext + GCM tag]
```

Der aktuelle Validation Report bestätigt ebenfalls:
`Versioning: Single format (V1); no version byte currently.`

Unsere aktuelle Architektur verlangt eine sichere **versionierte** Persistenz, damit spätere Crypto-/Schema-Upgrades nicht stillschweigend inkompatibel werden.

**Bewertung:** Muss spätestens bei `Secure Local State & Key Lifecycle Freeze` gelöst werden.

---

## CODE-MEDIUM-006 — `CryptoSerializer::new()` validiert Key-Länge nicht selbst

Intern wird `copy_from_slice(key)` auf `[u8; 32]` ausgeführt.

Die heutigen Identity-/Session-Caller prüfen die Länge vorher, aber die öffentliche Konstruktorfunktion selbst ist nicht fail-safe.

Kein akuter JNI-Exploit über die heutigen geprüften Call Paths, aber API-Härtung ist sinnvoll.

---

## CODE-MEDIUM-007 — Production Logging noch nicht final

`CryptoBridge.kt` nutzt mehrfach:

```text
Log.e(TAG, "...", e)
```

Der Text enthält aktuell keine bewusst ausgegebenen Secrets, aber unsere V1-Regeln verlangen für Production:
- minimale Logs
- keine Tokens
- keine privaten Keys
- keine Session-States
- keine Message Plaintexts
- keine sensitiven Exception-Details

Vor Release muss Logging zentral redaktiert/hardening-fähig werden.

---

## CODE-MEDIUM-008 — `destroyAllCrypto()` ist derzeit enger als sein Name

Aktuell löscht `destroyAllCrypto()` primär den Keystore-Eintrag.

Es löscht nicht explizit:
- `anox_state_key.enc`
- zukünftige verschlüsselte lokale DB
- Temp Attachments
- Caches
- weitere gespeicherte Crypto-State-Dateien

Das Löschen des Keystore-Key kann als Crypto-Erase bereits entscheidend sein, aber die Methode darf nicht als vollständiger Wipe aller lokalen Artefakte überinterpretiert werden.

---

## CODE-INFO-009 — Android Runtime noch nicht verifiziert

Instrumentation Tests sind vorhanden und kompilieren.

Sie wurden nach dem letzten verifizierten Report noch **nicht auf Emulator/Device ausgeführt**.

Der aktuelle Code enthält zusätzliche Tests:
- Persistence Roundtrip
- Fresh Nonce
- Corrupted Wrapped State Key
- State-Key Stability

Diese zusätzlichen Tests ändern den Status nicht:
**geschrieben ≠ ausgeführt**.

---

## CODE-INFO-010 — NDK ist bereits gepinnt

`android/build.gradle.kts` enthält aktuell:

```kotlin
ndkVersion = "26.2.11394342"
```

Damit ist der alte Dokumentations-Blocker „NDK not pinned“ im hochgeladenen Projekt bereits überholt.

---

# 4. Git-/Repository-Hygiene

`.gitignore` ist für die kommende GitHub-Anbindung noch nicht vollständig.

Gefunden:
- Rust `target/` ist nicht explizit ignoriert.
- `.kotlin/` ist nicht explizit ignoriert.
- Keystore-Patterns (`*.jks`, `*.keystore`) sind nur auskommentiert.
- `google-services.json` ist nur auskommentiert.
- Native `.so` liegen aktuell im Source Tree.

Für spätere GitHub-/CI-Phase muss entschieden werden:
- Native Binaries reproduzierbar im CI erzeugen statt manuell versionieren?
- `target/` / lokale Build Artefakte ausschließen
- Secrets konsequent blockieren
- keine Signing Keys in Git

Im Scan wurden **keine offensichtlichen API Keys/Passwörter/Tokens** in den relevanten Quell-/Konfigurationsdateien gefunden.

---

# 5. Vergleich mit `FORTSCHRITT.md`

Unser bisheriger koordinierter Stand von ca. **22 %** bleibt als konservativer Gesamtfortschritt plausibel.

Bestätigt:
- Rust Crypto existiert.
- 14/14 Rust Tests waren zuletzt ausgeführt und PASS.
- Android `.so` vorhanden.
- arm64-v8a + x86_64 vorhanden.
- Android Build/JNI Packaging vorhanden.
- Backend/DB/Auth/Messaging fehlen weiterhin.

Korrektur zum bisherigen Fortschrittsdokument:
- **NDK ist im hochgeladenen Repo bereits gepinnt.**

Neu durch statischen Repo-Audit erkannt:
- Raw-Pointer-Handle-Safety ist noch kritischer als bisher dokumentiert.
- Einige Android Negative Tests sind wegen untypisierter Handles selbst potenziell gefährlich.
- Persistenztests existieren als Code, sind aber nicht als echter Process-Restart verifiziert.

Der Prozentstand wird deswegen **nicht erhöht**.

---

# 6. Markdown-Dokumente — Datei-für-Datei-Audit

## 1. `README.md`

**Status:** KRITISCH VERALTET

Probleme:
- Architecture Version `Raw1.1`
- sagt, Crypto sei nicht implementiert
- sagt „No security mechanisms should be considered implemented“
- „initial foundation setup / Arbeitsschritt 1“
- behauptet GitHub Hosting, obwohl dies aus dem ZIP nicht verifiziert werden kann

Muss aktualisiert werden auf:
- aktuelle konsolidierte RAW-Baseline
- Rust Crypto 14/14 PASS
- Android Build/Link PASS
- Android Runtime noch UNVERIFIED
- ca. 22 % V1 Fortschritt
- Backend/Messaging noch nicht implementiert

---

## 2. `CHANGELOG.md`

**Status:** KRITISCH VERALTET

Aktuell endet es bei:
`No security mechanisms implemented yet (Architecture Raw1.1)`

Fehlt:
- Rust/vodozemac Foundation
- OlmMessage Fix
- AES-CBC → AES-GCM
- Rust 14/14
- JNI/Android Build
- Android Keystore
- allowBackup=false
- `.so` Builds
- Instrumentation Tests
- bekannte noch offene Runtime-/Handle-Safety-Punkte

---

## 3. `docs/architecture/key-architecture.md`

**Status:** KRITISCH / MUSS KOMPLETT NEU GEFASST WERDEN

Veraltet/falsch:
- eigene Signal-artige Key-Hierarchy
- Signed Prekeys als selbst definierte Architektur
- eigenes Root/Chain/Message-Key-Modell
- direkte Festlegung AES/ChaCha für Message Keys
- optionales Identity-Key Backup
- Key Recovery
- Multi-Device Sync
- Device Signed Prekeys
- libsodium/TweetNaCl als Implementierungsplan

Aktuell bindend:
- vodozemac/Olm ist E2EE Source of Truth
- keine selbst definierte Ratchet-/Key-Hierarchy
- E2EE Identity / Olm Session / Local State Key / Device Auth Key / API Tokens getrennt
- Private E2EE State lokal
- Android Keystore schützt Local State Key
- AES-256-GCM schützt serialisierten Crypto State
- No Recovery
- Single Device
- Device Auth separat, Ed25519-Richtung
- Attachment Key separat geplant

---

## 4. `docs/decisions/open-decisions.md`

**Status:** EXTREM VERALTET

Viele längst entschiedene Themen stehen noch als OPEN:
- Recovery
- Anzahl Geräte
- E2EE Library
- Multi-Device
- PGP/libsignal
- Backup
- Push Default/Fallback
- Key Algorithm intern
- Signed Prekey Rotation

Muss ersetzt werden durch nur **wirklich offene** Punkte.

Aktuell tatsächlich OPEN:
- finaler Device-Auth/Access-/Refresh-/Request-Signing-Vertrag
- RAW1.63/RAW1.70 DB-Schema-Reconciliation
- exakte Sync/API-Endpunkte
- exakte TTL/Retention-Werte
- API/Attachment Size Limits
- Rate-Limit-Werte
- IP-/Security-Log-Retention
- Certificate Pinning Entscheidung
- finaler SAS/QR-vodozemac-UX/API-Mapping
- finale lokale verschlüsselte DB-Library
- Push Provider/Transport-Implementierung
- CI/SBOM/Release-Signing Details
- externe Audit-Planung

---

## 5. `docs/security/account-recovery.md`

**Status:** DIREKTER WIDERSPRUCH ZUR V1-ARCHITEKTUR

Dokument empfiehlt:
- Multi-Device Recovery
- Recovery Code
- Hybrid Recovery

Aktuell bindend:
**V1 besitzt KEINE Recovery.**

Muss:
- entweder nach `docs/history/raw1.1/` verschoben und als SUPERSEDED markiert werden
- oder in eine aktuelle No-Recovery-Spezifikation umgeschrieben werden

Empfehlung:
Historische Analyse archivieren + neue aktuelle Datei erstellen.

---

## 6. `docs/security/android-jni-crypto-validation-report.md`

**Status:** HISTORISCHER REPORT MIT VERALTETEN FAKTEN

Korrekt erhalten:
- Android Build/Packaging PASS
- Rust 14/14
- Instrumentation nicht ausgeführt
- GrapheneOS UNVERIFIED

Veraltet:
- behauptet JDK 17 sei für AGP 9.1.1 unsupported / JDK21 erforderlich
- behauptet NDK sei nicht gepinnt
- beschreibt einen älteren Testbestand
- empfiehlt ggf. Downgrade auf AGP 8.x ohne aktuellen Architekturgrund

Aktuell:
- im Repo ist NDK bereits gepinnt
- JDK17 war in unserem Review kein aktueller Blocker
- Testcode ist inzwischen umfangreicher
- Runtime weiterhin UNVERIFIED

Report als historischen Evidence-Report behalten, aber mit **Corrections/Superseded Header** versehen.

---

## 7. `docs/security/crypto-foundation-completion-report.md`

**Status:** HISTORISCH / TEILWEISE ÜBERHOLT

Wertvoll als Devin-Arbeitsreport.

Muss klar markieren:
- Blocker Resolution war Zwischenstand
- Tests waren zu diesem Zeitpunkt noch nicht ausgeführt
- anschließend `crypto-foundation-validation-report.md` mit 14/14 PASS
- nicht als Current Architecture verwenden

Nicht löschen.

---

## 8. `docs/security/crypto-foundation-security-review.md`

**Status:** HISTORISCH + TEILWEISE VERALTET

Enthält:
- Raw1.1
- alte CBC-Historie
- frühere Blocker
- zum Teil überholte API-Beschreibungen
- Fallback-/Prekey-Terminologie

Muss:
- als historischer Security Review markiert werden
- Current Status oben ergänzen
- aktuelle AES-GCM-/14/14-/Android-Unverified-Lage referenzieren
- nicht als aktuelle Key Architecture dienen

---

## 9. `docs/security/crypto-foundation-validation-report.md`

**Status:** WEITGEHEND GÜLTIGER HISTORISCHER EVIDENCE-REPORT

Behalten:
- Rust toolchain
- vodozemac 0.10.0
- aes-gcm 0.10.3
- 14/14 PASS

Ergänzen:
- Status = Rust-Test-Level Verified
- nicht Production-Security
- nachfolgender Android/JNI Build existiert
- Runtime noch offen

---

## 10. `docs/security/cryptography-comparison.md`

**Status:** SUPERSEDED DECISION INPUT

Veraltet:
- E2EE Library noch offen
- libsignal als Kandidat
- Multi-Device als gewünschtes Requirement
- PGP/Hybrid weiterhin als aktive Alternativen

Aktuelle Entscheidung:
- vodozemac/Olm
- Rust Wrapper
- kein PGP-Layer für normale Chats
- Single Device V1

Sollte nach History/Decisions verschoben oder deutlich `SUPERSEDED` markiert werden.

---

## 11. `docs/security/cryptography-status.md`

**Status:** KRITISCH VERALTET

Muss komplett ersetzt werden durch:
- vodozemac 0.10.0
- AES-GCM state protection
- Rust 14/14 PASS
- Android native build/link PASS
- Android runtime UNVERIFIED
- GrapheneOS runtime UNVERIFIED
- kein Backend/Messaging

---

## 12. `docs/security/device-loss-scenarios.md`

**Status:** DIREKTER V1-WIDERSPRUCH

Enthält:
- Account Recovery
- Multi-device Redundancy
- Recovery API
- Key recovery/rotation flow

Aktuell:
- Device verloren + lokaler State weg = Account/Identity verloren
- kein Multi-device
- kein Recovery
- neues Gerät = neue V1 Identity/Account
- alte Identity nicht still migrieren
- alte verifizierte Kontakte müssen neue Identity als KEY_CHANGED behandeln
- wie Lost-Device Remote-Revocation ohne vorhandenes Credential ausgelöst wird, ist ein separat zu finalisierendes Account/Auth-Policy-Thema; nicht erfinden

Komplett aktualisieren.

---

## 13. `docs/security/metadata-analysis.md`

**Status:** TEILWEISE GUT, ABER RAW1.1 / ÜBERTRIEBENE CLAIMS

Veraltet:
- „zero-knowledge“ als pauschale Bezeichnung
- Aussagen wie vollständige Eliminierung bestimmter Metadaten
- nicht an aktuelle Backend-/Privacy-Regeln gekoppelt

Aktuell:
- Server sieht unvermeidbare Routing-/Operations-Metadaten
- keine Behauptung „metadata free“
- IP technisch sichtbar
- kurze/purpose-limited Logging-Policy
- keine Third-Party Behavioral Analytics
- kein last seen/online/typing
- local nicknames/chat names wo möglich
- future padding/timing privacy = future, nicht V1 Claim

---

## 14. `docs/security/push-notifications.md`

**Status:** ARCHITEKTUR-EMPFEHLUNG VERALTET

Aktuell empfiehlt Dokument:
- UnifiedPush primary
- FCM fallback

Aktueller V1-Kern ist provider-agnostisch:
- Push = wake-up only
- kein Message Plaintext
- kein Message Preview
- tatsächliche Ciphertexts per anoX API/sync
- Push darf verloren/dupliziert werden
- Push Token separat
- GrapheneOS-Kompatibilität wichtig
- konkreter Provider/Transport ist noch nicht final

Dokument komplett aktualisieren; alte Provideranalyse kann History bleiben.

---

## 15. `docs/security/security-requirements.md`

**Status:** KRITISCH — MUSS KOMPLETT NEU SYNCHRONISIERT WERDEN

Enthält viele direkte Widersprüche:
- optionales Key Backup
- Device Addition / Multi-Device
- Multi-Device Requirement
- Account Recovery
- Recovery Codes
- Multi-Device Recovery
- Secure Backup/Recovery Pflicht
- mandatory Certificate Pinning
- Dummy Traffic als Pflicht
- „all key operations must be logged“ zu breit und potenziell gefährlich

Muss durch aktuelle Security Invariants + V1 Requirements ersetzt werden.

---

## 16. `docs/security/server-trust-model.md`

**Status:** TEILWEISE RICHTIG, ABER BEGRIFFLICH ZU STARK

Richtig:
- Server darf Message Plaintext nicht sehen
- Private Keys nicht serverseitig

Zu aktualisieren:
- „Zero Knowledge“ nicht als pauschales Versprechen
- Server kennt Routing-/Timing-/Account-/Device-Metadaten
- Server kann Availability angreifen
- Server kann Key Substitution versuchen
- Verification ist local/end-device Trust
- Server ist nicht Recovery-/Crypto-Trust-Authority
- Supabase ist Infrastruktur, nicht Crypto Authority

---

## 17. `docs/security/threat-model.md`

**Status:** GRUNDLAGE GUT, ABER RAW1.1 / NICHT RAW1.75-VOLLSTÄNDIG

Muss ergänzen/ändern:
- full backend compromise
- initial key substitution
- later identity replacement
- malicious APK
- supply chain
- push provider
- object storage
- insider/admin
- replay/idempotency
- ciphertext modification
- server deletion/blocking/availability
- endpoint compromise limitation
- keine pauschale mandatory Certificate Pinning-Aussage
- Padding nicht als verpflichtendes V1-Feature

---

## 18. `docs/specifications/device-identity.md`

**Status:** EXTREM VERALTET

Aktuell basiert Dokument auf:
- User mit 3 Devices
- Add Device QR
- E-Mail/Phone Verification
- 5 Devices
- Desktop/Web
- Multi-Device Sync
- Device replacement with continuity

Aktuelle V1:
- genau ein aktives Gerät
- random `device_id`
- Account Identity ≠ Device Identity ≠ E2EE Identity
- Device Auth Key separat
- keine Telefon/E-Mail-Pflicht
- verlorenes Gerät wird nicht auf neues Gerät migriert
- neues Gerät = neue Identity/Account in V1
- revocation blocks API/push
- Multi-device ist future, nicht V1

Komplett neu schreiben.

---

## 19. `docs/specifications/public-key-verification.md`

**Status:** TEILWEISE VERALTET / CUSTOM-CRYPTO-RISIKO

Aktuell enthält es selbst definierte:
- SHA-256 Fingerprint-Spezifikation
- eigene Safety-Number-Konstruktion
- eigene QR-Payload
- „Mark as Trusted“
- Grace Period

Aktuelle Architektur:
- Verification required
- accepted contact != verified contact
- local states:
  - UNKNOWN/UNVERIFIED
  - VERIFIED
  - KEY_CHANGED
- Identity Change:
  VERIFIED → KEY_CHANGED/UNVERIFIED
- keine automatische Vertrauensübernahme
- SAS/QR über etablierte vodozemac/Matrix Semantik, keine hausgemachte kryptografische Verification
- Server ist nicht Trust Authority

Komplett aktualisieren.

---

## 20. `docs/specifications/support-account.md`

**Status:** TEILWEISE PRODUKTANFORDERUNG, VIELE NICHT BESCHLOSSENE DETAILS

Aktuell bindend:
- anoX Support Chat soll im Produkt vorhanden/angeheftet sein
- Support-Kommunikation nutzt denselben E2EE-Grundschutz
- Support hat keinen universellen Decryption-/Admin-Bypass

Nicht bindend bzw. aktuell nicht final beschlossen:
- server-signed Support Identity
- Virtual Device
- Load Balancing
- verschlüsseltes Support-Key-Backup
- Ticket System
- besondere Retention
- eigene spezielle Ratchet-/Prekey-Regeln
- „no metadata access“ als absolute Aussage

Dokument auf minimal akzeptierte V1-Anforderungen reduzieren.
Operational Support Backend später separat designen.

---

## 21. `docs/specifications/user-identity.md`

**Status:** KRITISCH VERALTET

Aktuell definiert:
- spezielles `AX-...` anoX-ID Format
- 58.5 Bit Human-readable ID
- Server-signed mapping
- ID persistent across device changes
- alte Identity kann bei neuem Gerät weiterlaufen

Aktuelle V1:
- random internal `account_id`
- random `device_id`
- Username/public handle als getrenntes Konzept
- QR/contact identifier
- kein unrestricted global directory
- Account ID ≠ Username ≠ Device ID ≠ E2EE Identity
- Username Change != Key Change
- keine Phone-/Email-Pflicht
- Lost Device = kein Account-/Crypto-Restore

Komplett neu schreiben.

---

# 7. Wichtige aktuelle Architekturdateien fehlen im Projekt vollständig

Im hochgeladenen Projekt fehlen die konsolidierten aktuellen Master-Dokumente.

Es sollten mindestens hinzugefügt werden:

```text
docs/current/
├── SYSTEM_ARCHITECTURE.md
├── SECURITY_INVARIANTS.md
├── ACCOUNT_LICENSE_REGISTRATION.md
├── KEY_AND_SESSION_ARCHITECTURE.md
├── LOCAL_DEVICE_SECURITY.md
├── AUTH_PROTOCOL_STATUS.md
├── API_WIRE_PROTOCOL.md
├── MESSAGE_LIFECYCLE.md
├── CONTACTS_AND_VERIFICATION.md
├── PUSH_OFFLINE.md
├── ATTACHMENTS.md
├── METADATA_PRIVACY.md
├── ACCOUNT_DEVICE_LIFECYCLE.md
├── BACKEND_ARCHITECTURE.md
├── DATABASE_ARCHITECTURE.md
├── THREAT_MODEL.md
└── OPEN_ARCHITECTURE_ITEMS.md
```

Zusätzlich root/projektsteuernd:

```text
MAIN_PLAN_DE.md
FORTSCHRITT.md
DEVIN_PROMPT_OUTPUT_ARCHIV.md
PROJECT_STATE.md
```

Und historische Dokumente:

```text
docs/history/raw1.1/
```

---

# 8. Aktuelle bindende Architektur — Kurzfassung

## Produkt
- Closed Source
- Android / GrapheneOS
- V1 1:1 Messenger
- Support Chat angeheftet
- kein „unhackable“-Claim

## Account
- random `account_id`
- random `device_id`
- keine Telefon-/E-Mail-Pflicht
- Username + QR/contact identifier
- kein unrestricted global directory
- 1 aktives Device

## License
Bindende aktuellen Laufzeiten:
- 1 Monat
- 3 Monate
- 6 Monate

1-Woche-Testlizenz = historisches Konzept / nicht als aktuelle allgemeine V1-Regel behandeln, bis explizit erneut bestätigt.

1 Jahr = superseded.

License != Crypto Identity.
Expiry löscht keine Private Keys.

## Recovery
- keine Recovery
- kein Seed
- kein Recovery Code
- kein Server Private-Key Backup
- kein Multi-device Recovery
- Device verloren = Identity verloren

## E2EE
- Rust
- vodozemac/Olm
- keine Custom Ratchets
- private E2EE state local
- server only public material + ciphertext
- One-Time/Session-init Material nur gemäß realer vodozemac API

## Verification
- required
- accepted != verified
- UNKNOWN/UNVERIFIED
- VERIFIED
- KEY_CHANGED
- SAS/QR etablierte Semantik
- kein Server Trust Authority

## Device Auth
- separat von E2EE
- Ed25519-Richtung
- private local
- exact Token/Signing Protocol noch OPEN

## Message
- local plaintext
- encrypt local
- encrypted outbox
- server ciphertext
- ACK => SENT
- recipient receive => DELIVERED
- READ optional
- retry/idempotency
- random message_id
- no typing/last seen/online

## Backend
- eigener modularer Backend Layer
- Supabase/Postgres Infrastruktur
- kein Service Role Secret in APK
- RLS defense in depth
- migrations
- dev/staging/prod

## DB
Final Schema noch NICHT eingefroren.
RAW1.63/RAW1.70 müssen reconciled werden.

## Attachments
- local encryption
- separate random attachment key
- encrypted blob storage
- key + sensitive metadata inside E2EE payload
- XChaCha20-Poly1305 direction, wenn etablierte gepflegte Library final bestätigt

## Push
- wake-up only
- no plaintext
- no preview
- provider not trust source
- sync must work even if push fails

## Local Security
- AES-256-GCM current state protection
- Android Keystore wrapping
- no cloud backup
- no recovery
- encrypted local DB planned
- privacy-safe logs
- temp-file cleanup
- app lock/biometric may authorize access, not E2EE identity

## Metadata
- no metadata-free claim
- routing/timing/device/account metadata unavoidable
- no behavioral analytics
- no last seen/online/typing
- local labels local where possible

## Security
- replay protection
- object-level authorization
- rate limits
- anti-enumeration
- request sizes/timeouts/concurrency
- dependency pinning
- SBOM/audit before strong commercial security claims

---

# 9. Aktueller Code-Fortschritt gegenüber Endprodukt

**Gesamtfortschritt bleibt ca. 22 %.**

Warum nicht höher:
- Crypto Rust ist stark vorangekommen.
- Android Build/Link ist vorhanden.
- Aber Android Runtime/JNI Safety ist noch nicht abgenommen.
- Backend 0 %
- produktive DB 0 %
- Auth 0 %
- Account/License 0 %
- Messaging Transport 0 %
- Chat UI 0 %
- Contacts 0 %
- Verification UI 0 %
- Push 0 %
- Attachments 0 %
- Production Hardening/Audit überwiegend offen.

---

# 10. Empfohlene nächste Reihenfolge

## Jetzt zuerst
**DOCSYNC-001**
Alle Projekt-Markdowns auf aktuelle Architektur bringen und veraltete Raw1.1-Inhalte als historische Dokumente isolieren.

Warum zuerst:
Devin darf bei späteren Coding-Tasks nicht zufällig eine alte `Raw1.1`-Datei lesen und daraus Recovery/Multi-Device/libsignal/FCM/etc. implementieren.

## Danach
Nicht direkt Backend.

Zuerst Crypto/JNI Safety & Runtime:
- Raw Handle / type safety
- Android instrumentation runtime
- persistence/restart
- GrapheneOS smoke test

Dann erst Main Plan weiter.

---

# 11. Audit-Endergebnis

## Dokumentation
**NICHT synchron.**
Die Mehrheit der bindend formulierten Projekt-Dokumentation ist Raw1.1 und für aktuelle Implementierungs-Prompts gefährlich.

## Code
Der tatsächliche Code ist deutlich weiter als README/CHANGELOG behaupten, aber noch im Crypto-Foundation-/Integration-Stadium.

## Wichtigstes Risiko
Nicht die 14/14 Rust Tests, sondern die **untypisierte Raw-Pointer-JNI-Handle-Schicht** ist aktuell der wichtigste neu erkannte Code-Sicherheitsbereich.

## Handlung
DOCSYNC-001 ausführen, danach aktuellen Crypto Runtime/Safety Task fortsetzen.
