# anoX V1 Architecture Authority Index

**Status:** CURRENT  
**Date:** 2026-09-14

---

## Precedence

1. `B025/SECURITY_INVARIANTS_V1_1.md` — always first.
2. `B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` — development continuity and handoff governance.
3. `B_FREEZE_REGISTRY.md` — current registry of frozen Track B specifications B-001…B-027.
4. `CLOUD_AI_SECRET_PROTECTION.md` — cloud-AI secret / private-key protection.
5. `DEVELOPMENT_SECURITY_WORKFLOW_V1.md` — S0–S4 workflow, AI audit timing, PR-only-main governance.
6. `GITHUB_REMOTE_ACTIVITY_SAFETY.md` — GitHub remote activity safety, no rapid repetitive remote automation.
7. `B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` — consolidated V1 target architecture.
8. `B025_MANDATORY_AMENDMENTS_V1_1.md` — mandatory amendments to specific B-025 Track B items (B-003, B-008, B-010, B-013, B-020, B-022, ULTIMATE B027 trust boundary). Supersedes the enumerated v1.x provisions; unamended B-025 Track B items remain in force.
9. `B025_MANDATORY_AMENDMENTS_V1_2.md` — mandatory amendments to specific B-025 Track B items (B-004, B-005, B-006, B-007, B-011, B-012, B-014, B-015, B-016, ULTIMATE server trust boundaries). Supersedes the enumerated v1.x provisions; V1.1 and unamended B-025 Track B items remain in force.
10. `B025_MANDATORY_AMENDMENTS_V1_3.md` — mandatory amendments to specific B-025 Track B items (B-018, B-019, B-021, B-023) plus the canonical Security Invariant Traceability, Verification/Evidence State Model, and Implementation-Readiness State Model. Supersedes the enumerated v1.x provisions; V1.1/V1.2 and unamended B-025 Track B items remain in force.
11. `B025_MANDATORY_AMENDMENTS_V1_4.md` — **Pre-B004 Security Contract Freeze** (`REMEDIATION_SESSION_S0`; contract version `S0-CONTRACT-FREEZE v1`): device/JKT/account binding invariants, server DPoP/registration verifier contract, HTU/HTM canonicalization, DPoP nonce lifecycle, typed registration proof-of-possession, registration-store/binding-marker/first-run contract, `RejectedAfterArm` lifecycle, wipe/logout/delete domain matrix, backup/restore/reinstall expected state, publication epoch (S15), hardware-trust decision, and the SC-1…SC-14 / CC-1…CC-14 / SERVER_BREAKER_S1…S18 authority maps. Supersedes only the provisions enumerated in its §18; V1.1/V1.2/V1.3 and unamended B-025 Track B items remain in force. Machine index: `contracts/S0_CONTRACT_FREEZE_MANIFEST.json`; validator: `tools/audit/validate_s0_contract_freeze.py`.
12. `B025/TRACK_B/B0xx_*.md` — individual frozen B specifications B-001…B-025 (historical snapshot; amended items are superseded by `B025_MANDATORY_AMENDMENTS_V1_1.md`, `B025_MANDATORY_AMENDMENTS_V1_2.md`, `B025_MANDATORY_AMENDMENTS_V1_3.md`, or `B025_MANDATORY_AMENDMENTS_V1_4.md`).
13. `B027_AI_WORKFORCE_GOVERNANCE.md` — AI workforce / work-control governance (B027-A/B/C implemented; FINAL_PRE_PRODUCT_AUDIT required; Product development blocked).
14. Historical RAW / Raw1.1 documents in `docs/history/` — provenance only, superseded.

### Schema authority (single source of truth)

`DB-SCHEMA-V1-FROZEN` has exactly one authority home: `B025_MANDATORY_AMENDMENTS_V1_2.md §B-005` **as amended by** `B025_MANDATORY_AMENDMENTS_V1_4.md §1–§2, §11` (V1.4 wins on conflict). `docs/current/DATABASE_ARCHITECTURE.md`, `docs/current/BACKEND_ARCHITECTURE.md` and `B025/TRACK_B/B005_DATABASE_SCHEMA_RLS.md` are informative and defer to it. No second equal-precedence schema authority may exist (`CANONICAL CONTRACT AMBIGUITIES = 0`).

### Contract precedence rule for B004 / B005 implementation

Where B004 (backend), B005 (schema/RLS), or the client sessions S2/S3/S4 need a security contract for Device Authentication, Registration, DPoP, local storage, wipe/logout/deletion, backup/restore, OTK publication epoch or hardware trust, the current contract is `B025_MANDATORY_AMENDMENTS_V1_4.md` (clauses `[S0-…]`); older documents listed in its §18 are informative for the superseded provisions only.

---

## Contents

| Document | Authority | Purpose |
|----------|-----------|---------|
| `B025/SECURITY_INVARIANTS_V1_1.md` | Binding | anoX V1 security invariants |
| `B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` | Frozen | Chat handoff, governance, and Devin output contracts |
| `B_FREEZE_REGISTRY.md` | Current | Track B freeze registry B-001…B-027 |
| `CLOUD_AI_SECRET_PROTECTION.md` | Binding | Cloud-AI secret / private-key protection |
| `DEVELOPMENT_SECURITY_WORKFLOW_V1.md` | Current | S0–S4 workflow, AI audit timing, PR-only-main governance |
| `GITHUB_REMOTE_ACTIVITY_SAFETY.md` | Current | GitHub remote activity safety, no rapid repetitive remote automation |
| `B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` | Frozen | Consolidated V1 product architecture |
| `B025/IMPLEMENTATION_GAP_MATRIX.md` | Current | B-025 implementation gap matrix |
| `B025_MANDATORY_AMENDMENTS_V1_3.md` | Current | Traceability / test-matrix / release-governance / implementation-readiness amendments (B-018, B-019, B-021, B-023) |
| `B025_MANDATORY_AMENDMENTS_V1_4.md` | Frozen / Current | Pre-B004 Security Contract Freeze (S0): B-002, B-003, B-004, B-005, B-006, B-007, B-009, B-013 security contracts; SC/CC/S-breaker authority maps |
| `contracts/S0_CONTRACT_FREEZE_MANIFEST.json` | Current (machine index) | Clause registry for V1.4 consumed by `tools/audit/validate_s0_contract_freeze.py`; non-normative |
| `B025/TRACK_B/B001_MASTER_COMPLETENESS.md` … `B025/TRACK_B/B025_NEW_CHAT_HANDOFF.md` | Frozen | Individual B specifications B-001…B-025 |
|| `B027_AI_WORKFORCE_GOVERNANCE.md` | B027-A implemented / B027-B,C deferred | AI workforce / work-control governance |

---

## Canonical source

`docs/authority/AUTHORITY_INDEX.md` is the single canonical source for authority precedence.
All other governance, continuity, and handoff documents must reference this file rather than
duplicating or redefining the precedence list. If any other surface appears to define a competing
precedence, `AUTHORITY_INDEX.md` wins.

## Authority versioning rule

- `docs/authority/B025/` is the immutable historical snapshot of the B-025 handoff. It is not edited.
- `docs/authority/B_FREEZE_REGISTRY.md` is the current registry. New accepted B IDs (B-026, B-027, …) are appended here.
- This `AUTHORITY_INDEX.md` always points to the current registry.
