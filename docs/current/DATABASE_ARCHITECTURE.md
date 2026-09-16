> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-005 — Database Schema + RLS (FROZEN v1.12-f04) / B-009 — Local Messenger Database (FROZEN v1.5-f04).
>
> **Schema authority notice (DEFERS-TO: DB-SCHEMA-V1-FROZEN).** This document is **informative** for schema matters.
> The single canonical frozen schema contract is `DB-SCHEMA-V1-FROZEN`: `docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md §B-005`
> as amended by `docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md §1–§2, §11` (see `docs/authority/AUTHORITY_INDEX.md`).
> Nothing in this file defines, restates or varies a column, constraint, index or lifecycle rule with normative force.
>
# anoX V1 — Database Architecture

**Status:** CURRENT (informative; defers to DB-SCHEMA-V1-FROZEN)
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated
**Last synchronized:** 2026-09-14

---

## 1. Status

The V1 logical schema **is frozen** as `DB-SCHEMA-V1-FROZEN` (authority home: `B025_MANDATORY_AMENDMENTS_V1_2.md §B-005` as amended by `B025_MANDATORY_AMENDMENTS_V1_4.md §1–§2, §11`). The earlier statement in this file that the schema was not yet frozen is **superseded** (`ANOX-SECURITY-ARCH-004`, `MSC-UNIT-040`). Migrations/SQL are still `NOT_STARTED` (B-005 `implementation_state = NOT_STARTED`); a frozen contract is not a deployed schema.

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
