# B-006 — vodozemac Key Distribution
**Status:** FROZEN v1.2

- vodozemac 0.10.0/Olm V1 direction; no custom PreKey/ratchet construction.
- E2EE identity exposes vodozemac public Ed25519/Curve25519 identity keys; private state local only.
- `identity_revision=1`; no same-device identity replacement/rotation in V1.
- Generate/publish OTKs toward `max_number_of_one_time_keys`; initial batch plus fallback.
- Publish durability: persist Account with generated keys → upload public keys → backend ACK → `mark_keys_as_published` → persist updated Account. Never mark before ACK.
- Identical retry is idempotent; same key id with different public value is a security error.
- OTK claim is atomic AVAILABLE→CLAIMED; authorized accepted/nonblocked contacts only.
- Fallback used only when no OTK. Retain previous fallback key 15 days (14-day delivery window + 24h margin).
- Replenish OTK pool when below ~50% toward max.
- Reuse valid sessions; session id not secret; session mutation serialized. Same active device identity mismatch is rejected/security anomaly.
