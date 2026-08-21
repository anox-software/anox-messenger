# anoX Messenger V1 — Architecture Completeness Audit

**Audit date:** August 2026  
**Scope:** Available anoX conversation context through RAW1.75 + current Devin audit/crypto reports, compared against Master Development Archive v1.

## Executive conclusion

The previous ZIP correctly captured the highest-level security principles but was **not complete enough to serve as the sole engineering specification**.

The following major RAW areas were missing or materially under-specified:
- license/account activation architecture;
- registration state machine;
- account/device identifiers;
- access/refresh/session model;
- PreKey / one-time-key / fallback-key operational model;
- message states, ACK, idempotency and retry semantics;
- contact request / QR / username flow;
- detailed local-security rules;
- offline queue and push lifecycle;
- API security/abuse controls;
- metadata/privacy defaults;
- account/device lifecycle;
- the concrete logical database model discussed in RAW1.63/1.70;
- Supabase implementation boundaries;
- wire-protocol/versioning/canonicalization rules;
- crypto primitive/dependency rules;
- the full threat model;
- exact development sequence and current Devin status.

These areas are now represented in v2.

## Architecture conflicts discovered

### CONFLICT-001 — Database schema
RAW1.63 includes licenses/account_licenses, key bundles/one-time prekeys, delivery/receipts and other structures.
RAW1.70 is labeled “Final DB Schema” but omits several of these despite other accepted architecture still requiring them.

**Resolution status:** OPEN.  
Before database implementation, create one reconciled schema based on product requirements + protocol requirements. Do not blindly implement RAW1.70 as-is.

### CONFLICT-002 — Authentication/API session contract
The architecture contains:
- long-term device-authentication key;
- request signing with nonce/timestamp/body hash;
- short-lived access tokens;
- refresh mechanism.

The concepts are compatible but the exact production protocol has not been frozen.

**Resolution status:** OPEN before authentication/backend implementation.

### CONFLICT-003 — Sync endpoint shape
Earlier design uses message retrieval endpoints; later design suggests `/v1/sync`.

**Resolution status:** OPEN. Security semantics are established; exact API path/shape is not.

### CONFLICT-004 — Prekey terminology vs actual vodozemac API
Historical architecture discusses prekeys/one-time prekeys/fallback keys generically.
Implementation must use the exact actual vodozemac/Olm model, not invented Signal terminology.

**Resolution status:** MUST VERIFY against actual compiled vodozemac version/API.

## Historical completeness

The full verbatim content of every older skipped chat message and the referenced historical Raw1.0 document is not available.
This archive intentionally marks such content as HISTORICAL-MISSING rather than fabricating it.

However, RAW1.60 through RAW1.75 content visible in the current conversation has now been captured at architecture-rule level in v2.

## Current implementation truth

Latest Devin report says:
- the previous OlmMessage/session handling was rewritten using the actual vodozemac API;
- a real Alice→Bob→Alice test was written;
- negative tests were written;
- local state storage was changed from AES-256-CBC to AES-256-GCM;
- key separation/JNI checks were improved;
- no recovery was introduced.

But the Rust toolchain was unavailable, so those tests were **not executed**.

Therefore the correct current status is:

> CRYPTO FOUNDATION IMPLEMENTED/REPORTED, BUT FUNCTIONALLY UNVERIFIED.

The next accepted task is validation/build/test execution — not backend development.

## Completeness categories

### Captured as accepted V1 rules
- closed-source project direction;
- Android/GrapheneOS target;
- single active device;
- no recovery;
- no phone/e-mail requirement for core account registration;
- E2EE via Rust/vodozemac/Olm direction;
- server no message plaintext;
- E2EE private state local only;
- device authentication separate from E2EE identity;
- key verification and visible identity changes;
- client-side attachment encryption;
- push without message plaintext;
- encrypted local state;
- no Android/cloud secret backup;
- modular backend + PostgreSQL/Supabase direction;
- no direct privileged database access from app;
- metadata minimization;
- no online/last-seen/typing in V1;
- no third-party behavioral analytics;
- request validation/rate limiting/replay/idempotency requirements;
- security audit requirement before strong product security claims.

### Still open and must be finalized before relevant implementation
- exact final auth challenge/token/signature protocol;
- exact database schema reconciliation;
- exact REST/sync endpoint contract;
- exact retention periods/TTL values;
- certificate pinning decision;
- exact message payload size limits;
- exact attachment size limits;
- exact IP/security-log retention;
- exact SAS/QR verification UX and vodozemac API mapping;
- exact Android secure database/storage implementation;
- exact release/CI/supply-chain policy;
- group chats and calls (not V1 core).

## Verdict

**Master Archive v1:** good architecture summary, insufficient as sole coding specification.  
**Master Archive v2:** suitable as the authoritative architecture/workflow baseline, provided OPEN items are resolved before their implementation phase and repository state remains the source of implementation truth.
