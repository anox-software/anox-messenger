> **B-025 Authority Notice**
>
> This file is an advisory summary. Canonical authority is `docs/authority/B025/TRACK_B/B013_LIFECYCLE.md` and `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md` (B-013 v1.3).

# anoX V1 — Account & Device Lifecycle

**Status:** ADVISORY — see Authority
**Architecture Baseline:** B-013
**Last synchronized:** 2026-09-02

---

V1 device and account lifecycle is governed by B-013:

- One active device per account.
- Device auth and E2EE identity are separate.
- No multi-device, no recovery.
- A lost device does not migrate its private E2EE identity to a new device.
- License expiry does not delete E2EE private keys or become an encryption key.
- License expiry enters a restricted mode with defined permitted/denied operations (see B-013 v1.3).

Current code is the implementation source of truth for the implemented subset; all future implementation must follow B-013.
