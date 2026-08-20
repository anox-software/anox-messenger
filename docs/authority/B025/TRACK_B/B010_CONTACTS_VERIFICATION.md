# B-010 — Contacts + Verification
**Status:** FROZEN v1.2

- Relationship state, trust state, username and cryptographic identity are separate.
- Relationship request states PENDING/ACCEPTED/REJECTED/CANCELLED/EXPIRED; trust UNVERIFIED/VERIFIED/KEY_CHANGED; VERIFYING transient.
- Accepting contact does not verify identity. Unverified contacts may E2EE message with visible trust status.
- Discovery: exact username or contact QR only; no directory/prefix/autocomplete/phonebook. Create request may return generic 202 to hide existence/block.
- Contact QR URI concept `anox://contact/v1/<192-bit base64url token>`; token hash server-side; discovery only, not cryptographic proof.
- Verification: vodozemac SAS using Matrix SAS-v1 cryptographic semantics. Seven emoji default with decimal fallback; verification transaction UUID; expiration 10m; fresh SAS object. No custom KDF/commitment/MAC/SAS derivation; use established vodozemac/Matrix behavior including required canonicalization.
- Verification controls are hidden anoX E2EE traffic; this does not claim Matrix wire compatibility.
- Same active account/device identity mismatch => KEY_CHANGED + send/session-init blocked; no accept-changed/reverify-under-same-device shortcut.
- New account/device after loss is new contact/identity and must be re-added/reverified.
- Blocked pair cannot request/claim/message/verify; generic unavailable behavior; undelivered ciphertext purge ≤1h. If exact original identity later unblocked, local verification may remain.
- Contact export/import transfers public identifier/nickname only, never verification/session/private keys.
