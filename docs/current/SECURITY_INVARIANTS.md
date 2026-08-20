# anoX Messenger V1 — Security Invariants v1.1

**Status:** CURRENT / BINDING
**Change control:** explicit problem → ADR → security impact → B-spec version bump → tests/migrations/docs update. No silent agent changes.

1. V1 has no account or crypto recovery secret, recovery device, social recovery, server private-key backup or cloud restoration of private E2EE state.
2. V1 has exactly one active device per account; no device-add/replacement flow to an existing account.
3. Loss/wipe/uninstall/factory reset that destroys the only private state means the old cryptographic identity is not recoverable.
4. E2EE private identity and Olm session/ratchet state never leave the endpoint as plaintext/private material.
5. Backend, DB, storage and push providers do not receive message plaintext.
6. Attachment encryption keys never reach backend/object storage as plaintext.
7. Device Authentication is independent from E2EE identity, account/license and local state-protection keys.
8. Device Authentication V1 uses P-256/ES256 Keystore keys and RFC9449-style DPoP; old Ed25519 Device Auth direction is superseded.
9. License state/code is not cryptographic identity or E2EE key material; expiry does not delete local E2EE identity/history.
10. No custom cryptographic primitives, ratchets, DH/KDF/AEAD/MAC/RNG/signature or verification constructions when established library/protocol behavior exists.
11. Actual compiled vodozemac API is the source of truth for Olm session behavior.
12. Contact acceptance is not cryptographic verification.
13. Same active `account_id + device_id` E2EE identity change becomes `KEY_CHANGED`; sending/session establishment is blocked. No “accept changed key” shortcut in V1.
14. Contact QR is discovery/invite only. V1 cryptographic peer verification is SAS using established vodozemac/Matrix SAS-v1 semantics.
15. Push is wake-only and carries no plaintext, preview, E2EE key, sender/conversation/message identifier or sensitive attachment metadata.
16. `/sync` is message-state truth; push/realtime/timestamps are not delivery/read truth.
17. `SENT`, `DELIVERED` and `READ` follow the frozen B-008 semantics; recipient durable decrypt/persistence precedes delivery ACK.
18. Duplicate/replayed API operations/messages must be safe through DPoP replay controls, idempotency and message dedup/replay handling.
19. Sender/account/device object identity is derived from authenticated server context, not trusted from client JSON.
20. No unrestricted global user directory or prefix/autocomplete lookup; anti-enumeration is mandatory.
21. No third-party behavioral analytics, phonebook upload, global online/last-seen/typing by default in V1.
22. V1 is not metadata-free; security/product copy must not claim zero metadata or “unhackable”.
23. Local protected crypto state requires confidentiality and integrity/authenticity; no silent identity regeneration on missing/corrupt state.
24. `K_STATE`, SQLCipher `K_DB`, Device Auth key, E2EE private state, access/session credentials and attachment keys remain distinct.
25. Private state is excluded from Android/cloud backup; no recovery path may be introduced by backup/restore.
26. No secrets, private keys, Olm state, access tokens, license plaintext, message plaintext or attachment keys in logs/crash reports.
27. Supabase/PostgreSQL is infrastructure, not crypto trust authority, recovery authority or E2EE key vault.
28. RLS is defense in depth and never substitutes backend object-level authorization.
29. Service-role/DB/provider/release-signing secrets are never stored in APK, Git, prompts or ordinary logs.
30. Attachment V1 uses separately keyed authenticated streaming encryption; large files are not normal Olm bodies.
31. Certificate pinning and dummy traffic are not mandatory V1 controls; introducing them later requires review/ADR.
32. Endpoint compromise may expose endpoint plaintext; GrapheneOS compatibility does not make endpoint compromise impossible.
33. Passing application tests is not proof of production cryptographic security.
34. Independent security/crypto review is required before strong commercial security claims and before Production V1 according to B-022/B-023.
35. No security-critical implementation begins when its required current freeze/spec is absent or internally contradictory.
