> **B-025 Authority Notice**
>
> This file is an advisory summary. Canonical authority is `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md#B-010` (B-010 v1.3) and `docs/authority/B025/TRACK_B/B010_CONTACTS_VERIFICATION.md` (v1.2 historical snapshot).

# anoX V1 — Contacts & Public-Key Verification

**Status:** ADVISORY — see Authority
**Architecture Baseline:** B-010 v1.3
**Last synchronized:** 2026-09-02

---

## 1. Contacts

- Contacts are addressed by username / public handle or QR/contact identifier.
- Contact requests with accept/reject/block.
- No unrestricted global user directory.
- Anti-enumeration controls.
- Local nicknames stay local where possible.
- Accepted contact ≠ verified contact.

## 2. Durable Trust States

| State | Meaning |
|-------|---------|
| `UNKNOWN` | No trust decision recorded. |
| `UNVERIFIED` | Contact exists but not verified. |
| `VERIFIED` | Safety number/QR verified by both sides. |
| `KEY_CHANGED` | Contact's long-term identity key changed; send blocked until re-verification. |
| `BLOCKED` | Contact or conversation blocked. |

`VERIFYING` and `SECURITY_CHANGE` are transient UI/process descriptors, not canonical durable states.

## 3. Verification

- SAS and/or QR are the V1 verification UX direction.
- Use established vodozemac/Matrix verification semantics and APIs.
- **Do not** invent custom safety-number algorithms, custom fingerprint protocols, or custom QR cryptographic binding.
- The server is **not** the final trust authority.

## 4. Identity Change

A verified E2EE identity changing must:
1. Transition to `KEY_CHANGED`.
2. Show a user warning.
3. Require explicit re-verification.
4. Only then return to `VERIFIED`.

Never silently preserve `VERIFIED` across a new identity.
