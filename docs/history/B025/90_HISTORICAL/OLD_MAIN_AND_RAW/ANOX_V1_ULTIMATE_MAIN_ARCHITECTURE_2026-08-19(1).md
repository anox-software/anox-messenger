# anoX Messenger V1 — ULTIMATE MAIN ARCHITECTURE

**Status:** AUTHORITATIVE V1 BASELINE  
**Stand:** 19.08.2026  
**Zweck:** Oberste technische und produktbezogene V1-Referenz bis zur Release-Entwicklung.  
**Wichtig:** Diese Datei ist ein Architekturvertrag, kein Versprechen, dass jede Detailentscheidung bereits endgültig eingefroren ist.

## 1. Source-of-Truth-Regel

Bei Widersprüchen gilt:
1. Diese MAIN Architecture + ausdrücklich akzeptierte spätere ADRs/Architecture Decisions.
2. Tatsächlich implementierter Code und tatsächlich ausgeführte Tests für den Implementierungsstatus.
3. Aktuelle `docs/current/`-Dokumentation, soweit sie 1–2 nicht widerspricht.
4. Historische RAW-/Raw1.1-Dokumente nur als Kontext.

Eine bindende Security-Regel darf niemals stillschweigend durch einen Coding-Agent geändert werden.
Jede Änderung braucht eine explizite Architecture Decision mit Begründung, Sicherheitsauswirkung und Migration.

## 2. Was bereits feststeht

### Produkt
- Closed-source Android Messenger; GrapheneOS ist primäres V1-Ziel.
- Bestehende anoX-Android-App wird weiterentwickelt.
- V1-Kern: sichere 1:1-Kommunikation.
- anoX Support Chat ist fester Produktbestandteil.
- Keine Behauptung „unhackbar“ oder „metadata-free“.
- Vor starken kommerziellen Security-Claims ist unabhängige Prüfung/Audit erforderlich.

### Account, Identitäten und Gerät
- `account_id`: zufällig, nicht sequenziell.
- `device_id`: zufällig, nicht sequenziell.
- Account, Gerät, öffentlicher Username/Kontakt-Identifier und E2EE-Identität sind getrennte Konzepte.
- Keine verpflichtende Telefonnummer oder E-Mail.
- Username/öffentlicher Identifier + QR-Kontaktaufnahme.
- Kein unbeschränktes globales User-Verzeichnis; Anti-Enumeration.
- V1: exakt ein aktives Gerät pro Account.
- Multi-Device ist nicht V1.

### Recovery
V1 hat absichtlich KEIN Recovery:
- kein Seed / Recovery Phrase
- kein Recovery Code
- kein Recovery Device
- kein Social Recovery
- kein Server-Backup privater E2EE-Schlüssel
- kein Cloud-Restore privater E2EE-Zustände
- kein versteckter Recovery Master Key

Verlust des einzigen Geräts und lokalen Crypto-States bedeutet: alte kryptografische Identität nicht wiederherstellbar.

### Lizenz
Standard V1:
- 1 Monat
- 3 Monate
- 6 Monate

Lizenzstatus ist strikt von E2EE getrennt. Lizenzdaten sind niemals Schlüsselmaterial.
1 Jahr/12 Monate ist keine aktuelle bindende V1-Laufzeit.

### E2EE
Architektur:
Android/Kotlin → schmale Crypto-Schnittstelle → JNI/native → Rust → vodozemac/Olm.

- vodozemac/Olm ist die aktuelle V1-1:1-E2EE-Richtung.
- Kein OpenPGP als zusätzliche normale Chat-Verschlüsselung.
- libsignal ist nicht die gewählte V1-Implementierung.
- Keine selbst erfundene Kryptografie.
- Keine selbst erfundenen Ratchets, DH/KDF/AEAD/MAC/RNG/Safety-Number-Protokolle.
- Konkrete Session-/Prekey-Semantik folgt der tatsächlich verwendeten vodozemac-API.
- Private E2EE-Identität und Session/Ratchet-State bleiben lokal.
- Server verarbeitet/speichert keine Nachrichten-Klartexte.

### Key Separation
Getrennt bleiben:
1. E2EE Identity/Private State
2. Olm Session/Ratchet State
3. lokaler State-Protection-Key
4. Device-Authentication-Key
5. Access/Refresh/Session Tokens
6. Attachment Encryption Keys

### Lokaler Schutz
- Android Keystore als nicht exportierbarer Wrapping-Key.
- zufälliger 32-Byte State-Protection-Key.
- AES-256-GCM für authentifizierten Schutz serialisierter Crypto-Zustände.
- `allowBackup=false`.
- kein V1 Cloud-Restore privater Crypto-Zustände.
- Keine sensitiven Klartext-Secrets in SharedPreferences/JSON/External Storage.

### Verification
- Kontakt akzeptiert ≠ kryptografisch verifiziert.
- Zustände: UNVERIFIED → VERIFIED; bei Identity-Wechsel → KEY_CHANGED/UNVERIFIED → explizite Re-Verifikation.
- Keine stille Übernahme von VERIFIED bei neuem Identity Key.
- SAS/QR auf etablierten vodozemac/Matrix-Semantiken; kein eigenes Safety-Number-Protokoll.
- Server ist nicht finale Trust Authority.

### Messaging
Konzeptionell:
COMPOSING → ENCRYPTING → QUEUED → SENT → DELIVERED → READ(optional), plus FAILED/RETRY.

- zufällige globale `message_id`
- Retry behält logische Message-ID
- Idempotenz/Deduplizierung/Replay-Schutz
- manipuliertes Ciphertext muss sicher fehlschlagen
- SENT = Backend akzeptiert/persistiert Ciphertext
- DELIVERED = Empfängergerät hat verschlüsselte Nachricht erhalten
- Push ist nicht Delivery-Wahrheit
- kein Typing, global Online oder Last Seen standardmäßig in V1

### Kontakte
- Username/Identifier und QR
- Contact Request / Accept / Reject / Block
- Anti-Enumeration
- lokale Nicknames lokal, soweit möglich
- Kontaktstatus und Truststatus getrennt

### Push
- Wake-up only.
- Kein Plaintext, Preview, Attachment-Plaintext oder E2EE-Key im Push.
- Sync funktioniert unabhängig von Push.
- Provider ist noch nicht eingefroren.
- Push-Token ist getrennt von E2EE und Device Auth.

### Attachments
- Datei lokal mit zufälligem Attachment-Key authentifiziert verschlüsseln.
- Server/Object Storage erhält nur verschlüsselten Blob.
- Attachment-Key + sensitive Metadaten innerhalb E2EE-Nachricht.
- XChaCha20-Poly1305 ist geplante Richtung, aber erst nach finaler Library-Entscheidung bindend/implementiert.

### Backend
Android → authenticated HTTPS API → anoX Backend/Service Layer → Supabase/PostgreSQL.

- Supabase ist Infrastruktur, nicht Trust Authority, Recovery Authority oder E2EE-Key-Vault.
- V1: modularer Monolith, keine unnötigen Microservices.
- RLS = Defense in Depth, nicht Ersatz für Backend Authorization.
- dev/staging/prod getrennt.
- Service Role Key, DB Passwords und Backend Secrets niemals im APK/Git/Client.

### API Security
TLS → Device Auth → Freshness/Replay → Validation → Authorization → Rate Limits/Abuse → Business Logic → DB/RLS.

Pflicht:
- Object-Level Authorization
- Nonce/Request-ID
- Freshness/Timestamp
- Idempotency
- Größen-/Quota-/Concurrency-/Timeout-Limits
- Spam/Bruteforce/Enumeration-Schutz
- sichere parameterisierte DB-Zugriffe
- keine SQL-/Stacktrace-/Secret-Leaks

### Datenschutz / Metadaten
V1 ist nicht metadata-free.
Infrastruktur kann u.a. Account/Device IDs, Routingbeziehungen, Timing, Ciphertext-Größe, Delivery-State, IP und Push-Metadaten sehen.
Kein Behavioral Analytics, Phonebook Upload, Last Seen, global Online oder Typing standardmäßig.
Retention wird minimiert; konkrete Zeiten werden vor Production eingefroren.

### Support
- Support Chat vorhanden/gepinnt bzw. klar fest.
- gleicher E2EE-Content-Schutz.
- kein Universal-Decryption-Bypass.
- Support erhält niemals User-E2EE-Private-Keys.

### Threat Model / Supply Chain
Abdecken: DB Dump, Backend-Kompromittierung, MITM, Key Substitution/Change, Replay, Manipulation, Reordering/Deletion, verlorenes Gerät, Endpoint Compromise, Push Provider, Storage Leak, DoS, Enumeration, Metadata Analysis, malicious client/APK, Supply Chain, Insider/Admin.
Vor Release: Dependency/Secret Scanning, Lockfiles, SBOM, Signing/Provenance, negative Security Tests, GrapheneOS Tests und unabhängiger Security/Crypto Review.

## 3. Noch NICHT endgültig eingefrorene Entscheidungen

Diese Punkte dürfen NICHT von einem Coding-Agent eigenmächtig entschieden werden:
- exakter Device-Auth Challenge/Token/Request-Signing-Vertrag
- finales PostgreSQL/Supabase-Schema und RLS
- genaue REST-Endpunkte und `/sync` Wire-Struktur
- Push-Provider/Transport
- Offline-Ciphertext-TTL
- finale Attachment-Crypto-Library/Formatdetails
- Certificate Pinning ja/nein
- konkrete Metadata/IP/Security-Log Retention
- Support HA/Key-Continuity/Ticket-Integration
- lokales verschlüsseltes Message-DB-Design/Library
- Crypto-State Envelope/Migrationsstrategie
- Production Signing/Release/Update-Mechanismus

Für jeden Punkt wird vor Implementierung eine explizite ADR/FREEZE-Entscheidung erstellt.

## 4. Aktueller Implementierungsstand

Verifiziert:
- Android Projekt vorhanden.
- Rust/vodozemac Crypto Foundation vorhanden.
- AES-GCM State Protection + Android Keystore vorhanden.
- Rust Tests zuletzt 14/14 PASS.
- Android Connected Runtime Tests zuletzt 19/19 PASS.
- arm64-v8a + x86_64 Native Libraries vorhanden.
- NDK r26c gepinnt.
- DOCSYNC-001 abgeschlossen.

Noch offen/zu härten:
- JNI wrong-type Handle Safety.
- Panic Containment/FFI Ownership Review.
- Release Build Smoke.
- GrapheneOS Crypto Runtime.
- State Envelope Versioning/Lifecycle.

Noch nicht produktiv implementiert:
- Supabase Connection
- Backend
- PostgreSQL/RLS
- Account Registration
- License Activation
- Device Authentication
- API Tokens/Request Auth
- Network Messaging/Sync
- Chat UI
- Contacts
- Verification UX
- Push
- Attachments
- Production Lifecycle/Revocation/Delete
- Production CI/CD/Audit

Gewichteter Entwicklungsstand: ca. 24 %.

## 5. Verbindliche Entwicklungsreihenfolge

1. DOCSYNC/Governance — abgeschlossen.
2. PROMPT-005C: JNI/FFI Type Safety + Panic/Ownership + Release Smoke.
3. PROMPT-006: Secure Local State & Key Lifecycle Freeze.
4. Device Authentication Protocol FREEZE + Implementierung.
5. Account/Lizenz-Flow.
6. Backend API Foundation.
7. DB-SCHEMA-V1-FROZEN + Migrationen/RLS.
8. Public Session-Init/Key Distribution.
9. 1:1 Encrypted Message Transport/Sync.
10. Encrypted Local Message DB + Outbox.
11. Contacts/Discovery.
12. Key Verification / Security-Change UX.
13. Push/Offline.
14. Attachments.
15. Device/Account Revoke/Delete Lifecycle.
16. Metadata/Privacy Defaults.
17. Abuse/Rate/Security Logging.
18. Vollständige Integration/Security Regression.
19. GrapheneOS Hardening.
20. CI/CD/Supply Chain.
21. Independent Audit Preparation + Fixes.
22. Release Candidate / V1 Release Gate.

## 6. Änderungsregel

Diese Datei darf bis V1 als Ultimatum/Architecture Contract verwendet werden — ABER nicht als unveränderliches Dogma.

Änderungen sind erlaubt, wenn neue Erkenntnisse, Library-Limitierungen, Security Reviews oder Tests zeigen, dass eine Entscheidung verbessert werden muss. Dann gilt:
1. Problem dokumentieren.
2. Alternative analysieren.
3. Security-/Privacy-/Compatibility-Auswirkung bewerten.
4. ADR erstellen.
5. MAIN Architecture explizit aktualisieren.
6. betroffene Tests/Dokumentation/Code migrieren.

Keine stillen Änderungen durch Devin, Claude Code, Windsurf oder einen anderen Agenten.

## 7. Definition of Done für V1

V1 ist erst fertig, wenn die bindenden Funktionen implementiert, Security Invariants nachweisbar getestet, offene Architekturentscheidungen eingefroren, GrapheneOS-End-to-End-Tests bestanden, Secrets/Dependencies/Supply Chain geprüft, Release-Build/Signing/Update-Prozess validiert und ein unabhängiger Security Review durchgeführt sowie kritische Findings behoben wurden.

**Golden Rule:** Implementierungsfortschritt darf die Sicherheitsarchitektur nicht stillschweigend verändern.
