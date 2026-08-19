# anoX V1 — Database Architecture

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Status

**Final DB schema is NOT frozen.** A future `DB-SCHEMA-V1-FROZEN` decision is required before migrations.

## 2. Logical Domains

- accounts
- devices
- licenses
- account_licenses
- identity / public key material
- device_auth_keys
- sessions
- one-time / session-init public material
- contacts
- conversations
- conversation_members
- messages
- message_queue / delivery
- receipts
- attachments
- push registrations
- security events
- rate limits

## 3. Never Store

- message plaintext
- E2EE private keys
- private session state
- attachment plaintext
- recovery secrets

## 4. Postgres RLS

- Defense in depth.
- Not a replacement for backend authorization.

## 5. Conflict Note

There is an explicit historical conflict: RAW1.63 contained more license/prekey/delivery/receipt structures; RAW1.70 was called "final" but omitted some still-required domains. Therefore RAW1.70 must **not** be treated as the final current schema.
