> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-003 — Account + License (FROZEN v1.4).
>
# anoX V1 — Account, License & Registration

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Account Identity

- `account_id` is random and non-sequential.
- `account_id` is not a password and not an E2EE key.
- Public username/handle and QR/contact identifier may be used for addressing.
- No unrestricted global user directory.
- Username change does **not** imply E2EE identity-key change.

## 2. Device Identity

- `device_id` is random and non-sequential.
- V1 supports one active device per account.
- Device authentication is separate from E2EE identity.
- Device revocation must prevent API authentication and new push/message delivery.

## 3. License

**Current binding standard durations:**
- 1 month
- 3 months
- 6 months

1-year plans are **not** current binding V1 offerings.

License status controls product/service access. License expiry:
- must not delete E2EE private keys;
- must not become the encryption key;
- gates product/service access according to the final product flow.

## 4. Registration

- No phone/email mandatory for V1 identity.
- Account creation creates a new random `account_id` and a new local E2EE identity.
- Device registration pairs the device with the account using the device-auth key and tokens.

## 5. Recovery

**V1 has no account or crypto recovery.** A new device creates a new V1 cryptographic identity. Pending messages are not routed to a new identity.
