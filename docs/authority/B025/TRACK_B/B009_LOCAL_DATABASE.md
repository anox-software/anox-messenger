# B-009 — Local Messenger Database
**Status:** FROZEN v1.4

- Android/Kotlin → Room 2.8.4 → SQLCipher for Android 4.17.x → encrypted SQLite. No plaintext Room DB, JSON persistence or external-storage secrets.
- Two protection layers: SQLCipher for entire messenger DB + existing AES-GCM versioned envelope for serialized vodozemac Account/Session state.
- `K_DB` random 256-bit, independent from `K_STATE`, Device Auth, E2EE and attachment keys; wrap under dedicated Keystore AES-GCM alias `anox_db_wrap_v1`. No biometric user-auth requirement for routine background operation.
- Standard SQLCipher settings/WAL encryption; no custom PRAGMAs without ADR. Backup excluded.
- Local tables cover account/device, E2EE identity/session/preferred session, contacts/trust, conversations/messages, encrypted outbox, pending receipts, sync cursor/events, dedup/replay, attachments, security metadata.
- DB is authoritative local application state; in-memory objects are working copies. Single process/locks serialize crypto mutation.
- Critical outgoing/incoming/prekey operations use one durable DB transaction per frozen B-008 rules.
- `preferred_session_id` persisted per peer device. Valid preferred session is used outbound; new inbound PreKey does not silently replace it. Missing/corrupt preferred state does not trial-decrypt/randomly select another session.
- Normal local plaintext message content may live inside SQLCipher; do not add homemade row crypto/FTS leakage.
- Missing DB/Keystore/state keys or corruption fail closed; no silent destructive migration/new identity. Schema export and migration tests required.
- Logout/expiry preserve local DB/keys; wipe deletes wrappers/DB/WAL/SHM/state/encrypted attachment/temp best-effort; no NAND physical-erasure claim.
