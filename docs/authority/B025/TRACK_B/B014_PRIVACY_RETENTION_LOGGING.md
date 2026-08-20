# B-014 — Privacy / Retention / Logging
**Status:** FROZEN v1.3

- Do not claim metadata-free. Server/provider may observe identifiers, routing relationships, timing, ciphertext size, delivery state, IP and push token/timing metadata.
- No third-party behavioral analytics, phonebook upload, global online/last seen/typing by default.
- Message ciphertext: undelivered max14d; after DELIVERED server ciphertext deletion target ≤1h; expired ciphertext ≤1h.
- Attachment retention follows B-012 lifecycle; after received ACK or expiry delete encrypted server blob ≤1h.
- Previous Olm fallback key retention: 15d to cover 14d delivery window + 24h safety margin.
- Ordinary anoX raw IP/request logging is minimized; current policy target for raw IP under anoX control is ≤24h. Never claim that Cloudflare/FCM/other providers necessarily share the same deletion clock.
- Push tokens are operational secrets stored encrypted+hashed; never ordinary logs. Old invalid registrations/jobs are cleaned under operational retention.
- Security/admin audit events may be retained longer where needed for incident/security/accountability but must exclude plaintext/private crypto/token/license secrets and have explicit production retention owners/jobs.
- Backups contain only server-side data already permitted by the trust model; never E2EE private keys/message plaintext. Erasure/deletion journal is replayed after restore so deleted accounts cannot resurrect.
- Retention must be enforced by tested jobs, not only policy text. Production privacy/provider/legal review remains a release gate.

**Recoverability note:** This export preserves the numerical retention values visible in current accepted evidence. If a future implementation needs a finer per-log-category duration not stated here, recover the original B-014 source or create a new explicit ADR/freeze; do not invent one from historical Raw docs.
