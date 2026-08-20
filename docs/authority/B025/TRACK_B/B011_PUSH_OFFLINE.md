# B-011 — Push + Offline Queue
**Status:** FROZEN v1.2

- Primary V1 push transport: FCM HTTP v1, but optional for core messaging. GrapheneOS can use sandboxed Google Play without Google account for reliable wakeups; anoX still functions without it.
- Push = wake only; `/v1/sync` authoritative. Payload conceptually exactly `{ "v":"1", "type":"sync" }` with no message/sender/conversation/account/device IDs, plaintext, preview, attachment metadata, E2EE keys or license.
- Data message; use high priority only for user-visible timely activity; collapse key `anox_sync`; provider TTL 5m.
- Do not show “new secure message” before sync proves there is a message. Post-sync local notification is privacy-first and has no sender/content by default.
- anoX ciphertext queue TTL 14d. Provider queue/acceptance never changes message state.
- FCM token is sensitive operational secret; register through authenticated DPoP endpoint, server stores encrypted reversible token + hash, one active token/device, rotation replace; never full-token logs/admin display.
- Invalid provider token disables registration. Logout disables/removes push; device revoke/wipe removes. Entitlement expiry may retain registration but stops normal message wakeups.
- No-Play fallback: app open/resume/manual refresh plus conservative WorkManager periodic best-effort (Android minimum ~15m) and network reconnect triggers where practical. No aggressive polling, permanent background websocket, permanent FGS/wakelock V1.
- Backend DB commit → durable push job → worker send. Provider failure never affects durable ciphertext. Transient retry bounded within wake TTL; invalid token is permanent failure.
- No Firebase Analytics/topics/device groups/BigQuery metrics by default.
