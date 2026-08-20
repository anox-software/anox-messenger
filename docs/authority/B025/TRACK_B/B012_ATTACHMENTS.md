# B-012 — Attachment Encryption + Storage
**Status:** FROZEN

- Crypto: libsodium `crypto_secretstream_xchacha20poly1305`, through Rust/native. Initial selected integration: libsodium-rs 0.2.4 plus pinned transitive/source dependency. If Android arm64/x86_64 build/runtime fails, STOP; do not silently substitute primitive.
- Fresh independent 256-bit attachment key per send; no derivation/reuse/convergent encryption/dedup.
- Limits: 1 attachment/message; plaintext 1 byte–100MiB; fixed plaintext chunk 1MiB; ciphertext cap 101MiB.
- Blob format: secretstream header + authenticated chunks; nonfinal `TAG_MESSAGE`, final `TAG_FINAL`; strict final/EOF/truncation/reorder/corruption failure. SHA-256 exact ciphertext blob.
- E2EE descriptor contains attachment_id, crypto_version=1, key, ciphertext hash/size, plaintext size, filename, MIME. Server never sees key/filename/MIME/plaintext size/hash.
- Filename max 255 UTF-8 bytes and never internal path; MIME max 127 ASCII and untrusted. No auto-execute.
- Sender encrypts source to app-private encrypted temp, hashes exact blob, uploads private storage, commits, then sends E2EE attachment message and atomically publishes linkage. Retry upload reuses exact encrypted blob; no whole-file RAM buffering.
- Signed upload capability 2h. Small upload standard; >6MiB TUS resumable. No upsert/overwrite after publish.
- Recipient signed download URL 5m after exact authorization; verify bytes/hash/secretstream/final/plaintext size before durable local encrypted storage. Then idempotent `/received` ACK for server cleanup, not sender read status.
- Retention: unpublished max24h; published+undelivered follows message 14d; after message delivered but blob not received max additional14d; after received ACK or message expiry delete server blob ≤1h.
- No server thumbnails/OCR/malware scan/dedup. User explicit Save As decrypts via SAF; external open may expose plaintext by user action. Temp plaintext short-lived/best-effort delete.
