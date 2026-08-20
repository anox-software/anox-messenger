> **B-025 Authority Notice**
>
> B-025 is the current architecture authority for this repository.
> This file may still contain pre-B-025 text that has not yet been fully reconciled.
> The canonical B-025 package is at `docs/authority/B025/`.
> Relevant frozen Track-B item: B-022 — Independent Security Audit (FROZEN).
>
# anoX V1 — Threat Model

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## 1. Scope

This threat model covers the V1 architecture: native Android app, JNI/Rust crypto, authenticated API, and Supabase/PostgreSQL backend.

## 2. Threats

| Threat | V1 Mitigation |
|--------|---------------|
| DB dump | E2EE; server stores ciphertext only. |
| Full backend compromise | Ciphertext-only; no plaintext or E2EE keys on server. |
| Network MITM | TLS + device-auth. |
| Initial key substitution | Public-key verification / trust states. |
| Later identity replacement | `KEY_CHANGED` warning + re-verification. |
| Replay | Freshness / nonce / request ID. |
| Ciphertext manipulation | vodozemac authentication fails safely. |
| Server deletion/blocking/reordering | Sync and idempotency; availability not cryptographically guaranteed. |
| Stolen device | No recovery; device revocation prevents future delivery. |
| Endpoint compromise | A compromised endpoint can expose local plaintext. E2EE does not prevent this. |
| Push provider abuse | Push is wake-up only; no content. |
| Object storage leak | Attachments are encrypted locally. |
| DoS/flooding | Rate limits, size limits, abuse controls. |
| Enumeration | Anti-enumeration on contacts/usernames. |
| Metadata analysis | Metadata is visible; privacy defaults minimize it. |
| Malicious APK/client | Server-side auth and validation; cannot forge valid ciphertext. |
| Supply-chain compromise | Pinned dependencies, lockfiles, SBOM, signing. |
| Insider/admin | RLS + backend authorization; no plaintext access. |

## 3. Limitations

- A compromised endpoint may expose plaintext because plaintext exists locally before encryption and after decryption.
- E2EE does not guarantee availability or metadata anonymity.
