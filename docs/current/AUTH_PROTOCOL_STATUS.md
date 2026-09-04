> **B-025 Authority Notice**
>
> This file is an advisory summary. Canonical authority is `docs/authority/B025/TRACK_B/B002_DEVICE_AUTHENTICATION.md` and `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md`.

# anoX V1 — Authentication Protocol Status

**Status:** ADVISORY — see Authority
**Architecture Baseline:** B-002
**Last synchronized:** 2026-09-02

---

V1 production authentication is governed by B-002:

- P-256 / ES256 Device Auth keypair.
- DPoP-bound access token with short lifetime.
- No refresh token.
- No Ed25519 Device Auth.
- No session-token/refresh-token mechanism.

The exact server-side contracts remain pending B-004/B-007 implementation. Until those are frozen, no code should implement a different authentication model.
