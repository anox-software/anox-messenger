# anoX V1 — Contacts & Public-Key Verification

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Contacts

- Contacts are addressed by username / public handle or QR/contact identifier.
- Contact requests with accept/reject/block.
- No unrestricted global user directory.
- Anti-enumeration controls.
- Local nicknames stay local where possible.
- Accepted contact ≠ verified contact.

## 2. Trust States

| State | Meaning |
|-------|---------|
| `UNKNOWN` / `UNVERIFIED` | No verification performed. |
| `VERIFIED` | Identity has been verified by the user. |
| `KEY_CHANGED` / `SECURITY_CHANGE` | The verified identity has changed; user warning; explicit re-verification required. |

## 3. Verification

- SAS and/or QR are the V1 verification UX direction.
- Use established vodozemac/Matrix verification semantics and APIs.
- **Do not** invent custom safety-number algorithms, custom fingerprint protocols, or custom QR cryptographic binding.
- The server is **not** the final trust authority.

## 4. Identity Change

A verified E2EE identity changing must:
1. Transition to `KEY_CHANGED` / `UNVERIFIED`.
2. Show a user warning.
3. Require explicit re-verification.
4. Only then return to `VERIFIED`.

Never silently preserve `VERIFIED` across a new identity.
