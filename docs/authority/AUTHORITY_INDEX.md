# anoX V1 Architecture Authority Index

**Status:** CURRENT  
**Date:** 2026-08-28

---

## Precedence

1. `B025/SECURITY_INVARIANTS_V1_1.md` — always first.
2. `B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` — development continuity and handoff governance.
3. `B_FREEZE_REGISTRY.md` — current registry of frozen Track B specifications B-001…B-026.
4. `CLOUD_AI_SECRET_PROTECTION.md` — cloud-AI secret / private-key protection.
5. `DEVELOPMENT_SECURITY_WORKFLOW_V1.md` — S0–S4 workflow, AI audit timing, PR-only-main governance.
6. `GITHUB_REMOTE_ACTIVITY_SAFETY.md` — GitHub remote activity safety, no rapid repetitive remote automation.
7. `B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` — consolidated V1 target architecture.
7. `B025/TRACK_B/B0xx_*.md` — individual frozen B specifications B-001…B-025.
8. Historical RAW / Raw1.1 documents in `docs/history/` — provenance only, superseded.

---

## Contents

| Document | Authority | Purpose |
|----------|-----------|---------|
| `B025/SECURITY_INVARIANTS_V1_1.md` | Binding | anoX V1 security invariants |
| `B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md` | Frozen | Chat handoff, governance, and Devin output contracts |
| `B_FREEZE_REGISTRY.md` | Current | Track B freeze registry B-001…B-026 |
| `CLOUD_AI_SECRET_PROTECTION.md` | Binding | Cloud-AI secret / private-key protection |
| `DEVELOPMENT_SECURITY_WORKFLOW_V1.md` | Current | S0–S4 workflow, AI audit timing, PR-only-main governance |
| `GITHUB_REMOTE_ACTIVITY_SAFETY.md` | Current | GitHub remote activity safety, no rapid repetitive remote automation |
| `B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md` | Frozen | Consolidated V1 product architecture |
| `B025/IMPLEMENTATION_GAP_MATRIX.md` | Current | B-025 implementation gap matrix |
| `B025/TRACK_B/B001_MASTER_COMPLETENESS.md` … `B025/TRACK_B/B025_NEW_CHAT_HANDOFF.md` | Frozen | Individual B specifications B-001…B-025 |

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
