# B-018 — Release Signing + Secure Updates
**Status:** FROZEN

- Android release signing key `K_APK_RELEASE` is hardware protected/offline from CI, with controlled backups and tested recovery rehearsal.
- Existing installations must only accept updates signed by the production app signer; wrong signer/tampered package must fail. Signer fingerprint is release evidence.
- Update metadata is separately signed (JWS) with version/artifact hash/size/minimum compatibility as frozen by implementation spec; valid metadata accepted, tampered/wrong-key rejected and rollback detected.
- Direct APK distribution is canonical V1 path unless explicitly changed; download/install/update flow tested on supported GrapheneOS/Android.
- Exact RC source commit, APK/backend hashes, schema/IaC revision, SBOM and metadata are frozen. Post-audit security-sensitive changes require delta review/audit.
- Signing recovery rehearsal must actually restore backup and sign a test artifact; possession of an unused backup is not sufficient.
- Release rollback keeps database compatibility; do not rely on destructive DB downgrade.
