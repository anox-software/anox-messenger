> **B-025 Authority Notice**
>
> This file is an advisory summary. Canonical authority is `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md` (Security Invariants 1–3) and `docs/authority/B025/TRACK_B/B013_LIFECYCLE.md` / `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md#B-013`.

# anoX V1 — Account & Crypto Recovery Policy

**Status:** ADVISORY — see Authority
**Architecture Baseline:** B-013
**Last synchronized:** 2026-09-02

---

## 1. Invariant

**V1 has no account or cryptographic recovery.**

## 2. Prohibited Mechanisms

The following are explicitly prohibited in V1:
- recovery seed / phrase / code
- encrypted server private-key backup
- recovery device
- social recovery
- multi-device recovery
- hidden master recovery key
- cloud restoration of E2EE private state

## 3. Device Loss

If the only device and local crypto state are permanently lost:
- the old cryptographic identity/account cannot be restored;
- a new device creates a new V1 cryptographic identity;
- pending messages are not routed to the new identity.

## 4. New Device

A new device registration creates:
- a new random `account_id` (if a new account is desired);
- a new random `device_id`;
- a new local E2EE identity (vodozemac account);
- a new device-auth keypair.

## 5. Historical Analysis

Earlier analysis comparing recovery models is preserved as historical/superseded in `docs/security/account-recovery.md`.
