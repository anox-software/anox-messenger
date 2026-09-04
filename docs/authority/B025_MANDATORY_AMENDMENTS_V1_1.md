# B-025 Mandatory Amendments V1.1

**Status:** FROZEN / CURRENT  
**Date:** 2026-09-02  
**Authority:** Human-authorized `MAINARCH-FIX-01` architecture remediation.  
**Supersedes:** Specific provisions in `docs/authority/B025/TRACK_B/` B-003 v1.4, B-008 v1.5, B-010 v1.2, B-013 v1.2, B-020 v1.1, B-022, and `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` as detailed below.  

This document is the authoritative successor for the enumerated provisions. All other B-025 content remains in force without change. Historical B-025 snapshot files are not rewritten.

---

## B-003 — Account + License (amended v1.5)

The following items supersede `docs/authority/B025/TRACK_B/B003_ACCOUNT_LICENSE.md` v1.4 for the clauses listed.

### 1. Identity / PII

V1 identity model is:

- **No password.**
- **No mandatory email, phone number, or SMS identity requirement.**

Email/phone/SMS may be supported as optional non-identity contact/notification channels if explicitly added by a future, separately authorized track item. They are not required for account creation, activation, or license ownership in V1.

### 2. Username and license code policy

Username contract:

- Lowercase ASCII `[a-z0-9_.]`, length 3–32.
- Reserved system names are maintained by server policy.
- Client validation is advisory only; server is the authoritative accept/reject authority.
- Client and server must share the documented syntax/length rules to prevent avoidable divergence.
- V1 username is immutable after successful activation.

License code contract:

- Format `anox-XXXX-XXXX-XXXX`.
- 12 unambiguous CSPRNG characters drawn from the unambiguous uppercase alphanumeric alphabet excluding visually confusable characters (server-defined canonical alphabet; client implements the same alphabet as a sync requirement, not a policy override).
- Plaintext shown once.
- Canonical lookup is versioned HMAC-SHA-256 under a server secret lookup key.

### 3. CommitArmed semantics

`CommitArmed` / `isArmed` is a **client-side safety precondition** for the final registration commit. It is not a wire protocol message or a server-enforced contract.

- Client must be in a state where the local registration store, Device Auth key, and E2EE identity are prepared and durable.
- Server must not rely on `CommitArmed` as a protocol state; server relies on the committed grant, Device Auth proof-of-possession, and final atomic commit evidence.
- The guard may be made explicit in the B-003 client state machine as a pre-commit readiness gate.

---

## B-008 — Messaging + Sync (amended v1.6)

The following items supersede `docs/authority/B025/TRACK_B/B008_MESSAGING_SYNC.md` v1.5 for the clauses listed.

### 1. Message lifecycle states

Canonical protocol states are:

- `QUEUED` — encrypted message is in local outbox, not yet accepted by server.
- `SENT` — server accepted and persisted the ciphertext.
- `DELIVERED` — recipient device received the message **and** completed the durable atomic commit of changed Olm state, message, dedup/replay, and conversation state as required by B-008.
- `READ` — optional E2EE read receipt.

`COMPOSING`, `ENCRYPTING`, `FAILED`, and `RETRY` are **UI/client process states**, not canonical protocol states. They may appear in client UX but must not be persisted as canonical message states.

`DELIVERED` is not merely "received by device"; it requires the recipient-side durable commit/ack specified in B-008 v1.5 §11.

---

## B-010 — Contacts + Verification (amended v1.3)

The following items supersede `docs/authority/B025/TRACK_B/B010_CONTACTS_VERIFICATION.md` v1.2 for the clauses listed.

### 1. Durable contact trust states

Canonical durable states:

- `UNKNOWN` — no trust decision recorded (first interaction or reset).
- `UNVERIFIED` — contact exists but no verified safety number/QR.
- `VERIFIED` — safety number/QR verified by both sides.
- `KEY_CHANGED` — contact's long-term identity key changed since last verification; send blocked until re-verification unless explicitly downgraded by user.
- `BLOCKED` — contact or conversation blocked.

Transient UI/process states:

- `VERIFYING` — in-progress verification flow, not a durable state.

`SECURITY_CHANGE` and similar are not canonical states; they are events or UI descriptors for `KEY_CHANGED`.

### 2. State transitions

- new contact → `UNKNOWN`
- manual verification accepted → `VERIFIED`
- verified contact key changes → `KEY_CHANGED`
- user re-verifies → `VERIFIED`
- user fails/dismisses verification → `UNVERIFIED` or `KEY_CHANGED` retained
- user blocks → `BLOCKED`
- user unblocks → previous durable state (`UNKNOWN`/`UNVERIFIED`/`KEY_CHANGED`)
- delete and re-add → `UNKNOWN` unless prior verification is restored by an explicit re-verification event

Preservation rule: a `KEY_CHANGED` state blocks new outbound messages until re-verification unless the user takes an explicit downgrade action, and downgrade must be recorded as a security event.

---

## B-013 — Account / Device Lifecycle (amended v1.3)

The following items supersede `docs/authority/B025/TRACK_B/B013_LIFECYCLE.md` v1.2 for the clauses listed.

### 1. License expiry restricted mode

When an entitlement becomes `EXPIRED`:

- Discovery is server-authoritative; a local cache may be used for UI but must not override server truth.
- Operations that remain permitted:
  - reading existing local message history and attachments already present on the device;
  - local key management unrelated to new service access;
  - Device Auth key material remains stored for later re-activation.
- Operations that are denied:
  - sending new messages or attachments;
  - receiving new sync events from server (server may stop delivery);
  - any operation that requires an `ACTIVE` entitlement.
- Device Auth behavior: Device Auth key is not deleted, but server rejects authentication for service actions while entitlement is `EXPIRED`.
- Renewal: when a valid renewal is accepted and entitlement becomes `ACTIVE`, all previously denied operations resume. Renewal preserves E2EE identity, account, and device bindings.
- Offline at expiry: client may continue to display local history; upon next online sync, it reconciles server expiry. No new sending is allowed before reconciliation.
- Clock/server-time: client does not unilaterally enforce expiry from local clock; it relies on server-provided entitlement state.

Expiry does **not** delete E2EE private keys or message history.

---

## B-020 — Product + UX (amended v1.2)

The following items supersede `docs/authority/B025/TRACK_B/B020_PRODUCT_UX.md` v1.1 for the clauses listed.

### 1. Security-critical UX semantics

V1 product/UX must explicitly define user-facing semantics for:

- license status and impending/actual expiry;
- restricted mode and what operations are available while restricted;
- renewal success/failure;
- irreversible account deletion;
- irreversible local wipe;
- identity/key security change (e.g., `KEY_CHANGED`) and required user action;
- update trust / re-verification of a changed contact key.

These are not visual designs. They are required product decisions about what the user can and cannot do and what confirmation/explanation is shown for irreversible or security-sensitive actions.

---

## B-022 — Independent Security Audit (amended v1.1)

The following items supersede `docs/authority/B025/TRACK_B/B022_INDEPENDENT_AUDIT.md` for the clauses listed.

### 1. Pre-product audit vs release audit gates

There are two distinct gates:

- **B027 `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`**: internal pre-product development audit. It determines whether Product implementation may resume. It includes MAIN, Workforce, Security, and Legacy audit sessions plus mandatory remediation/retest and a human final-gate decision. Completing it does **not** authorize commercial release.
- **B-022/B-023 release audit**: independent, named-human-reviewer security audit and Release Definition of Done. It is stricter, later, and governs commercial/release authorization.

The B027 pre-product audit does **not** satisfy or replace B-022/B-023. B-022 remains a release gate with its own blocking criteria, independent named reviewers, and public-audit-summary requirements where frozen. B-022's `MEDIUM` blocking semantics apply to the release gate, not to the pre-product gate.

---

## B-025 ULTIMATE MAIN ARCHITECTURE — Development/Workforce Trust Boundary (amended v1.1)

The following items amend `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` and related architecture surfaces.

### 1. B-027 development/AI workforce trust boundary

The MAIN architecture includes a development-system trust boundary governed by B-027:

- AI agents are untrusted executors. They do not possess project Authority.
- AI may not create, modify, or approve architecture, security, or release policy autonomously.
- AI is prohibited from D4/secret exposure and from external writes to the repository, remote services, or CI.
- Source, build, and release artifacts produced with AI assistance still require normal repository, CI, and human verification.
- Human Product & Security Owner retains exclusive authority for merges, releases, signing, break-glass, and accepted-risk decisions.

This is a **development-governance** trust boundary. It does not alter the E2EE product trust model or the server/client runtime trust boundaries.

---

## Historical provenance

This amendment document does not modify the B-025 historical snapshot in `docs/authority/B025/`. The B-025 snapshot files remain immutable provenance. The freeze registry (`docs/authority/B_FREEZE_REGISTRY.md`) and authority index (`docs/authority/AUTHORITY_INDEX.md`) record the amended current versions.
