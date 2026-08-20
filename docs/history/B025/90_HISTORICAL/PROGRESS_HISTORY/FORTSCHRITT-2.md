# FORTSCHRITT.md — anoX Messenger V1

**Zweck:** Aktueller, unabhängiger Entwicklungsstand inklusive Prompt-Historie, Devin-Ergebnissen und Vergleich zum MAIN PLAN.  
**Statusdatum:** August 2026  
**Regel:** „Implementiert“ ist nicht automatisch „verifiziert“. Tests zählen erst als PASS, wenn sie tatsächlich ausgeführt wurden.

---

# 1. Gesamtstatus

## Aktuelle Phase

**Phase 5 des Main Plans: Android / JNI Crypto Integration — Build/Link PASS, Runtime noch offen**

Der Rust-E2EE-Kern ist auf Rust-Testebene verifiziert.  
Der Android-Build, die nativen `.so`-Libraries und der Kotlin→JNI→Rust→vodozemac Link-Pfad wurden erfolgreich gebaut.  
Die echten Android Instrumentation Tests wurden jedoch mangels Device/Emulator noch **nicht ausgeführt**.

## Offizieller Gesamtfortschritt

### **ca. 22 % des V1-Endprodukts**

Diese Zahl ist absichtlich konservativ und gewichtet nach Engineering- und Security-Aufwand.

Sie bedeutet nicht:
- 22 % aller Codezeilen;
- 22 % aller UI-Screens;
- 22 % der Sicherheitsgarantie.

Sie bedeutet:
> Rund 22 % der für das geplante V1-Endprodukt notwendigen technischen/sicherheitskritischen Entwicklungsarbeit ist abgeschlossen oder hinreichend weit implementiert/verifiziert, um als Fortschritt zu zählen.

### Reiner sichtbarer Produktfunktionsumfang

Der nutzbare Messenger-Funktionsumfang ist deutlich niedriger, ungefähr **5–10 %**, weil Account, Backend, echte Chats, Kontakte, Push und Attachments noch nicht als integriertes Produkt existieren.

---

# 2. Gewichtetes Fortschrittsmodell

| Bereich | Gewicht am Endprodukt | Aktuell erreicht |
|---|---:|---:|
| Architektur / Master-Dokumentation | 4 % | 4 % |
| Bestehende App + Codebase Audit | 3 % | 3 % |
| Rust Crypto Foundation | 9 % | 9 % |
| Android/JNI Crypto Integration | 5 % | 3 % |
| Local Secure State / Key Lifecycle | 5 % | 2 % |
| Device Authentication | 6 % | 0 % |
| Account / License Registration | 5 % | 0 % |
| Backend Foundation | 5 % | 0 % |
| Database / Migrations / RLS | 6 % | 0 % |
| Session-init / Public Key Distribution | 4 % | 1 % |
| E2EE Message Transport / Sync | 8 % | 0 % |
| Local Message DB / Outbox | 5 % | 0 % |
| Contacts / Discovery | 4 % | 0 % |
| Key Verification | 5 % | 0 % |
| Push / Offline | 4 % | 0 % |
| Attachments | 5 % | 0 % |
| Account / Device Lifecycle | 3 % | 0 % |
| Privacy / Abuse Hardening | 5 % | 0 % |
| Integration / Security Regression | 4 % | 0 % |
| GrapheneOS + CI + Audit + Release | 5 % | 0 % |
| **Gesamt** | **100 %** | **22 %** |

Hinweis:
- One-Time-Key-Generation im Rust-Test gibt einen kleinen Vorlauf für „Session-init/Public Key Distribution“, aber kein Backend ist dafür vorhanden.
- AES-GCM, Keystore-Wrapping-Architektur, `allowBackup=false` und State-Restore-Code geben jetzt mehr Vorlauf für „Local Secure State“, aber Runtime- und Persistenztests auf Android fehlen noch.

---

# 3. Prompt- und Entwicklungs-Historie

## PROMPT-000 — Ursprüngliche Android-App-Erstellung

**Status:** HISTORISCH / exakter Wortlaut nicht vollständig verfügbar

### Ziel
Erste anoX Messenger Android-App als technische Ausgangsbasis erzeugen.

### Bekannter Output
- Android-Projekt vorhanden.
- App startet.
- GrapheneOS-Ausführung grundsätzlich möglich.
- Späterer Audit zeigte: im Kern Starter-/Welcome-App.

### Main-Plan-Zuordnung
- Phase 1: Projektbasis

### Bewertung
**Teilweise abgeschlossen.**
Die App war eine Basis, aber noch kein Messenger.

---

## PROMPT-001 — Existing Codebase Audit

**Status:** AUSGEFÜHRT  
**Exakter ursprünglicher Wortlaut:** im aktuellen Kontext nicht vollständig erhalten.

### Ziel
Tatsächlichen Zustand des vorhandenen Projekts feststellen, statt Architektur auf angenommene vorhandene Features aufzubauen.

### Devin Output — Kernaussagen
Repository bestand im Wesentlichen aus:
- `android` Modul
- leerem `backend`
- leerem `tests`
- `com.anox.messenger`
- `MainActivity.kt`
- Compose Theme

Gemeldete Toolchain:
- Kotlin 1.9.20
- Gradle 9.3.1
- AGP 8.13.2
- compileSdk 34
- targetSdk 34
- minSdk 26
- Compose BOM 2023.10.01

Nicht vorhanden:
- Crypto
- Networking
- Datenbank
- Supabase
- Authentication
- Messaging
- Persistence
- echte Tests

### Main-Plan-Zuordnung
Phase 1 / Projektbasis und Audit.

### ChatGPT Review
Audit wurde akzeptiert.
Entscheidung:
- vorhandenes Projekt weiterverwenden;
- tatsächliche Messenger-Layer kontrolliert aufbauen;
- Crypto Foundation vor Backend/Messaging.

### Status
**PASS / abgeschlossen.**

---

## PROMPT-002 — Crypto Foundation

**Status:** AUSGEFÜHRT  
**Exakter Wortlaut:** nicht vollständig als historischer Originaltext erhalten; Aufgabeninhalt ist erhalten.

### Ziel
Isolierten kryptografischen Foundation-Layer auf Basis der realen vodozemac API aufbauen.

### Vorgaben
- vorhandenes Android-Projekt nicht ersetzen;
- Rust crypto module;
- vodozemac prüfen;
- narrow JNI/API boundary;
- E2EE identity getrennt von device auth/session tokens;
- Android Keystore/storage architecture;
- sichere serialisierte State-Behandlung;
- safe errors;
- echte Crypto Tests;
- kein Backend;
- kein Messaging;
- kein Push;
- keine Attachments;
- kein Recovery;
- keine erfundenen APIs.

### Devin Output
Gemeldet:
- vodozemac 0.10.0
- `crypto/rust/`
- JNI Interface mit 16 Crypto-Funktionen
- `error.rs`
- `identity.rs`
- `session.rs`
- `serialization.rs`
- Kotlin:
  - `CryptoNative.kt`
  - `CryptoError.kt`
  - `CryptoResult.kt`
  - `CryptoBridge.kt`
- Security Docs

Lokale State Protection damals:
- AES-256-CBC

### Kritischer Output
**Olm Session Decryption funktionierte nicht.**

Ursache:
vodozemac Message Format/API nicht korrekt verarbeitet.

### ChatGPT Review
Nicht als fertig akzeptiert.

Zusätzlich erkannt:
AES-256-CBC ohne authentifizierte Integrität ist für diesen Zweck nicht ausreichend.

### Main-Plan-Zuordnung
Phase 2: Rust Crypto Foundation.

### Status
**FAIL / Blocker entdeckt → Reparaturprompt erforderlich.**

---

## PROMPT-003 — Resolve Crypto Foundation Blockers

**Status:** AUSGEFÜHRT

### Ziel
Crypto Foundation korrigieren, ohne Backend/Messaging vorzuziehen.

### Prompt-Vorgaben
- echte vodozemac 0.10.0 `OlmMessage` API untersuchen;
- keine manuell erfundene Message Parser-Logik;
- Alice→Bob Roundtrip;
- Bob→Alice Antwort;
- Negative Tests;
- AES-CBC Review;
- falls keine Authentizität: etablierte AEAD verwenden;
- keine Recovery;
- Key Separation;
- JNI safety;
- Docs aktualisieren;
- bei inkompatibler API stoppen statt Workaround erfinden.

### Devin Output
Behoben/gemeldet:
1. `OlmMessage::to_parts/from_parts`
2. `PreKeyMessage::from_bytes`
3. JNI boundary mit `(message_type, ciphertext, length)`
4. Alice→Bob→Alice Test geschrieben
5. Negative Tests geschrieben
6. AES-256-CBC → AES-256-GCM
7. No Recovery bestätigt
8. Key Separation bestätigt
9. JNI Null/bounds/error/resource Handling verbessert

### Kritischer verbleibender Blocker
Rust/Cargo fehlte im Environment.

Tests waren geschrieben, aber **nicht ausgeführt**.

### ChatGPT Review
Codeverbesserung akzeptiert, aber Foundation weiterhin nicht verifiziert.

### Main-Plan-Zuordnung
Phase 3: Crypto Blocker Resolution.

### Status
**IMPLEMENTED / UNVERIFIED.**

---

## PROMPT-004 — Crypto Foundation Validation

**Status:** AUSGEFÜHRT UND BESTANDEN AUF RUST-EBENE

### Ziel
Nicht weitere Features bauen, sondern vorhandenen Crypto-Code tatsächlich kompilieren und testen.

### Prompt-Vorgaben
- Rust Toolchain installieren;
- `cargo test`;
- tatsächliche Resultate liefern;
- Fehler korrigieren;
- Rust Crypto Roundtrip;
- Negative Tests;
- AES-GCM Validation;
- JNI Boundary Review;
- Android Build versuchen;
- GrapheneOS Smoke Test falls möglich;
- keine falschen Security Claims.

### Devin Output

Installiert:
- `rustc 1.97.1`
- `cargo 1.97.1`
- Host: `aarch64-apple-darwin`

Dependencies tatsächlich kompiliert:
- `vodozemac 0.10.0`
- `aes-gcm 0.10.3`

### Cargo Test

**14 / 14 PASS**

Tests:
- `test_error_messages_no_secrets`
- `test_authenticated_encryption`
- `test_identity_creation`
- `test_corrupted_serialized_state`
- `test_key_separation`
- `test_no_recovery_mechanism`
- `test_wrong_key_material`
- `test_malformed_message`
- `test_invalid_ciphertext`
- `test_one_time_key_generation`
- `test_serialization_restoration`
- `test_modified_ciphertext`
- `test_wrong_session_message_type`
- `test_alice_bob_full_flow`

### Zusätzlich korrigierte reale Compile/API-Probleme
- `Session` name conflict
- vodozemac key imports
- `Ed25519PublicKey::as_bytes()`
- `[u8;32]` handling
- CryptoError mapping
- `DeserializeOwned`
- unused imports/warnings

### Nicht verifiziert
- Android NDK nicht installiert
- Java Runtime fehlte
- Android Gradle Build nicht ausführbar
- kein Emulator/Gerät
- GrapheneOS smoke test nicht ausgeführt

### ChatGPT Review
Akzeptierte Aussage:

**Rust Crypto Foundation = FUNCTIONALLY VERIFIED AT RUST TEST LEVEL.**

Nicht akzeptiert:
„full crypto foundation is secure / production secure“.

### Main-Plan-Zuordnung
Phase 4: Rust Crypto Validation.

### Status
**PASS auf Rust-Ebene.**

---

## PROMPT-005 — Android / JNI Crypto Integration Validation

**Status:** AUSGEFÜHRT / TEILWEISE BESTANDEN  
**Main-Plan-Zuordnung:** Phase 5 — Android / JNI Crypto Integration

### Ziel
Den realen Android→Kotlin→JNI→Rust→vodozemac Pfad bauen, paketieren und so weit wie im Environment möglich verifizieren.

### Tatsächlich festgestellte Toolchain

- JDK: Temurin 17.0.20+8
- Android SDK: `/Users/3xpress/Library/Android/sdk`
- NDK: r26c / 26.2.11394342
- Gradle Wrapper: 9.3.1
- AGP: **9.1.1**
- Kotlin: **2.2.10**
- compileSdk: 34
- targetSdk: 34
- minSdk: 26
- Rust: 1.97.1
- cargo: 1.97.1
- cargo-ndk: 4.1.2
- vodozemac: 0.10.0
- aes-gcm: 0.10.3

### Devin Output

#### Native Android Libraries
Erfolgreich gebaut:
- `android/src/main/jniLibs/arm64-v8a/libanox_crypto.so`
- `android/src/main/jniLibs/x86_64/libanox_crypto.so`

#### Android Build
**PASS**

Erzeugt:
- `android-debug.apk`
- `android-debug-androidTest.apk`

Damit ist nachgewiesen:
- Kotlin-Code kompiliert;
- JNI/Native-Library wird korrekt paketiert;
- Rust/vodozemac wird in den Android Build gelinkt.

#### Rust Regression
`cargo test`: **14/14 PASS**

#### Instrumentation Tests
`CryptoInstrumentedTest.kt` wurde implementiert und kompiliert.

Enthaltene reale, nicht gemockte Tests:
- native library load
- identity create/destroy
- public key export
- one-time-key generation
- identity serialize/deserialize
- corrupted-state rejection
- invalid handle rejection
- Alice↔Bob through Kotlin/JNI
- invalid ciphertext rejection
- secret-safe error messages

**Ausführung:** NICHT ERFOLGT.

Grund:
- kein Android Device;
- kein Emulator;
- keine System Images installiert.

#### AES-256-GCM / Local State Review
Gemeldet:
- AES-256-GCM via `aes-gcm` 0.10.3
- 12-Byte Nonce
- Nonce via `getrandom`
- 16-Byte Tag
- Format `[nonce][ciphertext+tag]`
- 32-Byte State Key
- State Key durch non-extractable Android-Keystore-Key gewrappt
- wrapped key file: `anox_state_key.enc`
- corrupted ciphertext → Auth Failure → kein Plaintext

Review-Präzisierung:
Ein zufälliger 96-Bit-GCM-Nonce hat bei sicherem RNG und begrenztem Volumen eine sehr geringe Kollisionswahrscheinlichkeit, aber nicht „kein Risiko“.

#### Android Keystore
Gemeldet:
- Keystore Master Key non-extractable
- AES-256-GCM
- State Key via `SecureRandom`
- E2EE Identity bleibt in Rust-serialisiertem State und wird mit State Key geschützt
- Private E2EE Keys nicht an UI/Server exportiert
- `allowBackup=false`
- uninstall zerstört Keystore Key und wrapped key file

#### GrapheneOS
**UNVERIFIED**

Kein verbundenes Gerät.

### Geänderte Dateien

- `android/build.gradle.kts`
- `android/src/main/AndroidManifest.xml`
- `crypto/rust/src/lib.rs`
- `crypto/rust/src/identity.rs`
- `crypto/android/src/main/java/com/anox/crypto/CryptoBridge.kt`
- `crypto/android/src/main/java/com/anox/crypto/CryptoNative.kt`
- `crypto/android/src/main/java/com/anox/crypto/CryptoResult.kt`
- `crypto/android/src/androidTest/java/com/anox/crypto/CryptoInstrumentedTest.kt`
- `android/src/main/jniLibs/`
- `docs/security/android-jni-crypto-validation-report.md`

### ChatGPT Review

**PASS:**
- Rust regression weiterhin 14/14.
- Native Libraries für arm64-v8a/x86_64 gebaut.
- Android Debug + Test APK bauen erfolgreich.
- Kotlin/JNI/Rust/vodozemac Link- und Packaging-Pfad verifiziert.
- Instrumentation Tests real geschrieben und kompilierbar.
- AES-GCM + Keystore-Architektur wesentlich plausibler als ursprünglicher CBC-Ansatz.
- No-Recovery-Regel erhalten.

**NOCH NICHT PASS:**
- Android Runtime Instrumentation Tests wurden nicht ausgeführt.
- GrapheneOS Crypto Runtime wurde nicht getestet.
- NDK-Version ist noch nicht explizit gepinnt/normalisiert.
- Persistenz/Restart-Verhalten wurde nicht auf Android Runtime bewiesen.

### Korrektur zu Devins Toolchain-Aussage

Devin meldete:
> AGP 9.1.1 erfordert JDK 21.

Review gegen offizielle Android-Kompatibilitätsangaben:
**AGP 9.1.1 verwendet JDK 17 als Minimum und Default.**

JDK 17 ist daher **kein Blocker**.

### NDK

AGP 9.1.1 verwendet standardmäßig NDK `28.2.13676358`.

Aktuell wurde erfolgreich mit r26c gebaut.

Die NDK-Version muss jetzt:
- explizit gepinnt und begründet werden, oder
- kontrolliert auf eine aktuelle unterstützte Version normalisiert und erneut getestet werden.

### Akzeptierter Status

**Android/JNI BUILD + LINK = VERIFIED**

**Android/JNI RUNTIME = UNVERIFIED**

**GrapheneOS RUNTIME = UNVERIFIED**

**Crypto Foundation V1 insgesamt = NOCH NICHT ENDGÜLTIG ABGENOMMEN**

---

## PROMPT-005B — Android Runtime Crypto Validation & Toolchain Normalization

**Status:** NÄCHSTER FESTGELEGTER ARBEITSSCHRITT

### Ziel
Die bereits kompilierten echten Android/JNI-Tests tatsächlich auf einer Android Runtime ausführen, State-Persistenz verifizieren und die NDK-Konfiguration reproduzierbar machen.

### Muss erreicht werden
- Android Emulator oder reales Gerät verfügbar machen;
- `connectedDebugAndroidTest` tatsächlich ausführen;
- alle realen `CryptoInstrumentedTest` Tests PASS;
- Alice↔Bob über Kotlin/JNI zur Laufzeit PASS;
- State Save → Restart/Recreate → Restore PASS;
- corrupted state runtime failure PASS;
- invalid handle/error runtime failure PASS;
- keine Secret-Leaks;
- NDK-Version explizit pinnen bzw. kontrolliert normalisieren;
- Rust 14/14 Regression weiterhin PASS.

### GrapheneOS
Wenn ein Pixel/GrapheneOS-Gerät verfügbar ist:
- gleichen Smoke-/Runtime-Test durchführen.

Wenn nicht:
- GrapheneOS weiterhin als **UNVERIFIED**, aber nicht fälschlich als allgemeinen Android-JNI-Blocker deklarieren.

### Abnahme
Wenn Android Runtime PASS:
- Android/JNI Crypto Runtime kann akzeptiert werden.
- GrapheneOS-spezifischer Smoke Test bleibt als Plattformtest offen, falls kein physisches Gerät verfügbar ist.
- Danach kann `PROMPT-006 — Secure Local State & Key Lifecycle Freeze` beginnen.

### Status
**PENDING.**

---

# 4. Noch nicht erzeugte zukünftige Prompt-Serie

Die folgenden Prompt-IDs sind Plan-IDs. Der genaue Prompt wird erst unmittelbar vor dem Schritt von ChatGPT erzeugt, damit er auf dem tatsächlichen Repo-Stand basiert.

## PROMPT-006 — Secure Local State & Key Lifecycle Freeze
Status: GEPLANT

## PROMPT-007 — Device Authentication Protocol Freeze & Implementation
Status: GEPLANT

## PROMPT-008 — Account + License Registration
Status: GEPLANT

## PROMPT-009 — Backend Foundation
Status: GEPLANT

## PROMPT-010 — DB Schema Reconciliation / Migrations / RLS
Status: GEPLANT

## PROMPT-011 — Public Session-init / Key Distribution
Status: GEPLANT

## PROMPT-012 — 1:1 E2EE Message Transport / Sync
Status: GEPLANT

## PROMPT-013 — Local Encrypted Message DB / Outbox
Status: GEPLANT

## PROMPT-014 — Contact Discovery / Requests / Blocking
Status: GEPLANT

## PROMPT-015 — Key Verification / Identity Change UX
Status: GEPLANT

## PROMPT-016 — Push / Offline Delivery
Status: GEPLANT

## PROMPT-017 — Encrypted Attachments
Status: GEPLANT

## PROMPT-018 — Account / Device Lifecycle
Status: GEPLANT

## PROMPT-019 — Privacy / Local Security Hardening
Status: GEPLANT

## PROMPT-020 — API Abuse / Rate / Security Controls
Status: GEPLANT

## PROMPT-021 — Full Integration & Security Regression Suite
Status: GEPLANT

## PROMPT-022 — GrapheneOS End-to-End Validation
Status: GEPLANT

## PROMPT-023 — GitHub / CI / Supply Chain Hardening
Status: GEPLANT

## PROMPT-024 — External Audit Preparation
Status: GEPLANT

## PROMPT-025 — V1 Release Candidate Stabilization
Status: GEPLANT

Wichtig:
Die Nummerierung ist eine Steuerungsstruktur, kein Zwang, dass jede Phase exakt einen einzigen Devin-Prompt benötigt. Große Phasen können in mehrere Unterprompts aufgeteilt werden, z. B. `PROMPT-012A`, `012B`, `012C`.

---

# 5. Aktuelle Blocker

## Kritischer Blocker

Android/JNI **Runtime-Tests** noch nicht ausgeführt.

Bereits vorhanden:
- JDK 17
- Android SDK
- NDK r26c
- Rust Android `.so`
- Android Debug APK
- Android Test APK
- kompilierte Instrumentation Tests

Noch benötigt:
- Emulator/System Image oder reales Android-Gerät
- tatsächliche Ausführung von `connectedDebugAndroidTest`
- Restart/Persistenz-Runtime-Test
- NDK-Version pinnen/normalisieren
- optional sofortiger GrapheneOS Smoke Test auf physischem Pixel

## Spätere Architektur-Blocker

Vor Device Auth:
- finaler Auth/Token/Request-Signing-Vertrag einfrieren.

Vor Datenbank:
- RAW1.63 vs RAW1.70 Schema-Konflikt auflösen.

Vor Key Distribution:
- konkrete reale vodozemac Session-init/one-time/fallback API verifizieren.

Vor Production:
- TTL/Retention-Werte;
- Rate Limits;
- Attachment Limits;
- IP Security Log Retention;
- Certificate Pinning Entscheidung;
- Release Signing/Supply Chain;
- externer Audit.

---

# 6. Fortschritt nach Statusart

## Architektur
**hoch / weitgehend definiert**

Die meisten großen V1-Sicherheits- und Produktentscheidungen sind bekannt.
Einige konkrete Wire/Auth/DB Parameter sind bewusst offen.

## Crypto Rust
**sehr weit / funktional getestet**

14/14 Rust Tests PASS.

## Android Crypto Integration
**teilweise verifiziert**

Build/Link/Packaging sind PASS.  
Runtime-Instrumentation ist noch UNVERIFIED.

## Backend
**0 % implementiert**

## Datenbank
**0 % final implementiert**

## Account/Auth
**0 % produktiv implementiert**

## Messaging
**0 % als echtes Client↔Server↔Client Produkt implementiert**

## Contacts/Verification
**0 % produktiv implementiert**

## Push
**0 % produktiv implementiert**

## Attachments
**0 % produktiv implementiert**

## Production Security/CI/Audit
**frühe Planung vorhanden, Implementierung überwiegend offen**

---

# 7. Nächste Aktion

**PROMPT-005B — Android Runtime Crypto Validation & Toolchain Normalization ausführen.**

Danach:
1. vollständigen Devin Output speichern;
2. tatsächliche Instrumentation-Testresultate prüfen;
3. Android/JNI Runtime PASS/FAIL festlegen;
4. GrapheneOS-Status separat dokumentieren;
5. `FORTSCHRITT.md` erneut aktualisieren;
6. Prozentwert neu berechnen;
7. bei PASS anschließend PROMPT-006 erzeugen.

---

# 8. Regel für zukünftige Updates dieser Datei

Nach jedem Devin-Task eintragen:

```text
PROMPT-ID:
Datum:
Ziel:
Architektur-Referenzen:
Security Invariants:
Devin Änderungen:
Dateien:
Build:
Tests:
PASS/FAIL:
Blocker:
ChatGPT Review:
Akzeptierter Status:
Git Commit/PR:
Nächster Prompt:
```

Die Datei muss immer den realen Repository-/Teststand widerspiegeln und darf keine ungetestete Implementierung als abgeschlossen zählen.
