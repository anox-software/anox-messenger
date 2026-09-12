# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-09-11
**Latest material event:** `ANOX-EVENT-0045` — SECURITY-AUDIT-EVIDENCE-PRESERVATION-001: all five Security Hardening audit reports preserved byte-exact + hash-bound registry/traceability; AUDIT-SECURITY-CRYPTO-JNI-001 recorded as Candidate.
**Memory schema:** M2B-v1

<!-- ANOX_EVENT: ANOX-EVENT-0021 -->
<!-- ANOX_EVENT: ANOX-EVENT-0022 -->
<!-- ANOX_EVENT: ANOX-EVENT-0023 -->
<!-- ANOX_EVENT: ANOX-EVENT-0024 -->
<!-- ANOX_EVENT: ANOX-EVENT-0025 -->
<!-- ANOX_EVENT: ANOX-EVENT-0026 -->
<!-- ANOX_EVENT: ANOX-EVENT-0027 -->
<!-- ANOX_EVENT: ANOX-EVENT-0028 -->
<!-- ANOX_EVENT: ANOX-EVENT-0029 -->
<!-- ANOX_EVENT: ANOX-EVENT-0030 -->
<!-- ANOX_EVENT: ANOX-EVENT-0031 -->
<!-- ANOX_EVENT: ANOX-EVENT-0032 -->
<!-- ANOX_EVENT: ANOX-EVENT-0033 -->
<!-- ANOX_EVENT: ANOX-EVENT-0034 -->
<!-- ANOX_EVENT: ANOX-EVENT-0035 -->
<!-- ANOX_EVENT: ANOX-EVENT-0036 -->
<!-- ANOX_EVENT: ANOX-EVENT-0037 -->
<!-- ANOX_EVENT: ANOX-EVENT-0038 -->
<!-- ANOX_EVENT: ANOX-EVENT-0039 -->
<!-- ANOX_EVENT: ANOX-EVENT-0040 -->
<!-- ANOX_EVENT: ANOX-EVENT-0041 -->
<!-- ANOX_EVENT: ANOX-EVENT-0042 -->
<!-- ANOX_EVENT: ANOX-EVENT-0043 -->
<!-- ANOX_EVENT: ANOX-EVENT-0044 -->
<!-- ANOX_EVENT: ANOX-EVENT-0045 -->

## Repository truth

- Branch: `governance/security-audit-evidence-preservation-001`
- **Current HEAD:** `1d924a1182d17c504b352ea29f9e1f346f492cc9` (SECURITY-AUDIT-EVIDENCE-PRESERVATION-001 SUBSTANTIVE)
- **Canonical repository:** `https://github.com/anox-software/anox-messenger`
- **Legacy repository:** `https://github.com/anox-admin/ax-messenger.git` (historical provenance only)
- **Canonical branch:** `main`
- **Merged baseline branch:** `main`
- **Latest merge to baseline:** `869b99acac040412a29bbaadc76342070fb2085c` (SECURITY-ARCHITECTURE-FINDINGS-FREEZE-001 merge)
- **Previous baseline HEAD:** `c653a1d6a302758c0e006225987281643957f752`
- **Foundation baseline tag:** `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- **CONTINUITY-001:** ACCEPTED
- **Current effective gate:** `SECURITY-AUDIT-EVIDENCE-PRESERVATION-001` — RETROSPECTIVE + CURRENT SECURITY AUDIT EVIDENCE PRESERVATION (Ready For Remote; awaiting human merge)
- **Current authorized task:** `ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-001` (Ready For Remote; awaits human merge)
- **Open blockers:** 5 canonical Product findings remain (013, 018, 030, INTEGRATION-005, B003-001) + `ANOX-MAINARCH-018` physical verification + milestone Security Architecture review (003, 007, 024) + Final operational Handoff/Bootstrap/Employee Cold-Boot acceptance. Workforce findings 001/002/005 are Closed; 10 ANOX-SECURITY-ARCH-* findings frozen; B-004 blocking set = 001..004. Security Hardening wave evidence preserved: 18 consensus roots (12 Pre-B004), `ANOX-BUILDSC-CANDIDATE-001` EVIDENCE_INTEGRITY=CRITICAL.
- **Previously completed:** `MAINARCH-FIX-01` + `MAINARCH-RETEST-01` (17 findings Closed); `MAINARCH-FIX-02` + `MAINARCH-RETEST-02` (8 findings Closed); `MAINARCH-FIX-03` + `MAINARCH-RETEST-03` (5 findings Closed); **MAIN ARCHITECTURE AUDIT + REMEDIATION PHASE COMPLETE**; **LEGACY AUDIT SET 6/6 COMPLETE**; `LEGACY-FIX-01` + `LEGACY-RETEST-01` COMPLETE (8 findings Closed); `AUDIT-WORKFORCE-ARCHITECTURE` COMPLETE WITH FINDINGS; `WORKFORCE-FIX-01` merged to `main` at `8385f401...`; `WORKFORCE-RETEST-01` FAIL recorded; `WORKFORCE-FIX-02` remediated to Ready For Retest; `WORKFORCE-TEST-HARNESS-FIX-01` test fixture repair complete; `WORKFORCE-HARNESS-RECHECK-01` FAIL recorded.
- **Next candidate task:** `AUDIT-SECURITY-CRYPTO-JNI-001` (NOT AUTHORIZED — start only with explicit human authorization and a fresh post-merge `main` SHA).
- **Product status:** `BLOCKED_PENDING_FINAL_AUDIT`; no product/CI changes until all final/legacy/retest conditions are complete and the human final gate is recorded.

## Architecture / governance

- B-001…B-023: frozen/defined.
- B-025 V1.3: FROZEN (traceability / test-matrix / release-governance / implementation-readiness).
- B-024 Final MAIN Consistency Audit: PASS.
- B-025 New-Chat Handoff: COMPLETE.
- B-026 Continuous Development Governance: FROZEN.
- B-027-A AI Workforce / Work-Control Governance Foundation: MERGED at `38b619e...`.
- B-027-B State/Gate Resolver + Role Contracts + Task/Prompt/Communication Runtime: MERGED at `aca7a8...`.
- B-027-C / B-027-D: B027-C MERGED at `0a4910e...` (PR #8); AUDIT-MAIN-ARCHITECTURE findings frozen, merged to main, and sealed; MAINARCH-RETEST-01-INGEST completed at `ec71127...`; MAINARCH-RETEST-02-INGEST completed at `8ee4cc...`; MAINARCH-RETEST-03-INGEST completed at `876e635...`; LEGACY-AUDIT-SET-FREEZE consolidated at `1ffe6e7...`; LEGACY-FIX-01 merged at `3adf56c...`; LEGACY-RETEST-01-INGEST delivered at `f50dc79...`; AUDIT-WORKFORCE-ARCHITECTURE findings freeze delivered at `6d9c813...`; WORKFORCE-FIX-01 merged at `8385f401...`; WORKFORCE-FIX-02 substantive delivered at `c0b643c...`; WORKFORCE-TEST-HARNESS-FIX-01 merged at `88b312f...`.

## Current canonical Open / Ready For Retest findings

- `ANOX-MAINARCH-013` (build/provenance, Class D)
- `ANOX-MAINARCH-018` (physical, Class E)
- `ANOX-MAINARCH-030` (B-009 wipe/session, Class C)
- `ANOX-LEGACY-INTEGRATION-005` (native handle leak, Class F)
- `ANOX-LEGACY-B003-001` (UUIDv4 variant, Class F)


Closed by `LEGACY-FIX-01` + `LEGACY-RETEST-01` (verified PASS — REMEDIATED):
`ANOX-MAINARCH-019`, `ANOX-MAINARCH-023`, `ANOX-MAINARCH-031`,
`ANOX-LEGACY-ANDROIDSEC-001`, `ANOX-LEGACY-CRYPTO-005`,
`ANOX-LEGACY-INTEGRATION-001`, `ANOX-LEGACY-INTEGRATION-002`, `ANOX-LEGACY-INTEGRATION-003`.

---

## ANOX-EVENT-0043 — WORKFORCE-RETEST-CLOSURE-INGEST (2026-09-10)

- Substantive commit: `8572ab99f4e2e62e5be75abb3144f6f927aa9f68`
- Canonical base SHA: `1fa8ba9867fbed3936e0922c2c2b70c9afbc1ae7`
- Task: `ANOX-TASK-WORKFORCE-RETEST-CLOSURE-INGEST`
- Result: `Ready For Remote`
- Summary: WORKFORCE-HARNESS-RECHECK-02 PASS at `1fa8ba9867fbed3936e0922c2c2b70c9afbc1ae7`; per-finding verdicts 001 PASS — NO REGRESSION, 002 PASS — REMEDIATED, 005 PASS — NO REGRESSION. `ANOX-WORKFORCE-AUDIT-001/002/005` Closed with canonical closure evidence. `ANOX-TASK-WORKFORCE-HARNESS-RECHECK-02` Closed. `ANOX-TASK-SECURITY-ARCH-001` recorded as Candidate. Product remains `BLOCKED_PENDING_FINAL_AUDIT`; Security Architecture Audit `NOT_STARTED`; remote mutation `NONE`.

---

## ANOX-EVENT-0045 — SECURITY-AUDIT-EVIDENCE-PRESERVATION-001 (2026-09-11)

- Branch: `governance/security-audit-evidence-preservation-001`
- Substantive commit: `1d924a1182d17c504b352ea29f9e1f346f492cc9`
- Canonical base SHA: `869b99acac040412a29bbaadc76342070fb2085c`
- Task ID: `ANOX-TASK-SECURITY-AUDIT-EVIDENCE-PRESERVATION-001`
- Result: `Ready For Remote`
- Five audit reports preserved byte-exact under `docs/reports/security/audits/` (hash-bound in `docs/security/audit-evidence/evidence_hashes.json`): `AUDIT-SECURITY-ARCHITECTURE` (existing canonical), `AUDIT-SECURITY-CODEBASE-001`, `AUDIT-SECURITY-CODEBASE-002` (blind), `CODEBASE-SECURITY-CONSENSUS-001`, `AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001`.
- Canonical audit-evidence registry + traceability created under `docs/security/audit-evidence/`: 21/21 Audit-001 candidates, 17/17 Audit-002 candidates, 18 consensus roots, 12/12 Build/Supply candidates, gate sets, historical relations.
- `ANOX-LEGACY-CRYPTO-005` remains Closed (`LATER_AUDIT_PROVES_INEFFECTIVE_REMEDIATION` preserved); `ANOX-LEGACY-INTEGRATION-005` remains Open (`NEW_ROOT_CAUSE_RELATED_TO_HISTORICAL_FINDING`).
- New validator `tools/audit/validate_security_audit_evidence_preservation.py` + 12 adversarial tests `tools/audit/test_security_audit_evidence_preservation.py`.
- Product remains `BLOCKED_PENDING_FINAL_AUDIT`; B-004/B-005 `NOT_STARTED`; next gate `AUDIT-SECURITY-CRYPTO-JNI-001` Candidate / NOT_EXECUTED.
- No product, backend, SQL, CI, native-artifact, or secret changes; remote mutation NONE.
- Next: human merge to `main`, then `AUDIT-SECURITY-CRYPTO-JNI-001` on a fresh post-merge `main` SHA.

