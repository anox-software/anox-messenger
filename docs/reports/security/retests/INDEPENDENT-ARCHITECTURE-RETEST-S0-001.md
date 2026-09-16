# INDEPENDENT-ARCHITECTURE-RETEST-S0-001 — PROVENANCE-MARKED CANONICAL RECONSTRUCTION

**Record class:** `S0_INDEPENDENT_ARCHITECTURE_RETEST` (reconstructed provenance record — NOT the original transcript)
**Retest ID:** `INDEPENDENT-ARCHITECTURE-RETEST-S0-001`
**Subject:** `REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001` (original unmerged S0 delivery, substantive `d9c7872d0c895573e220a4c9e0572d10f847bf04` — later superseded in place by corrected `8756a94824ba9baef678176ef2ee24a2c302f1d0`)
**Model (original retest):** `Devin SWE-2 (Max effort)` per authorized retest model records

---

## 0. PROVENANCE — READ FIRST

```
VERBATIM_ORIGINAL_TRANSCRIPT_AVAILABLE = NO
RECONSTRUCTED = YES
RECONSTRUCTION_HUMAN_AUTHORIZED = YES
SOURCE_CLASS = HUMAN_AUTHORIZED_RECONSTRUCTED_SECURITY_EVIDENCE
ORIGINAL_RESULT = PASS_WITH_FINDINGS
ORIGINAL_FINDING_COUNT = 10
ORIGINAL_RESULT_NOT_UPGRADED = YES
REASON = ORIGINAL_READ_ONLY_SESSION_OUTPUT_WAS_NOT_INGESTED_BEFORE_SESSION_LOSS
RECONSTRUCTION_AUTHORIZED_BY = Human Product & Security Owner
  (§4 amendment to SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001; recorded under
   ANOX-DECISION-S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001)
```

The original retest was a **read-only** session whose complete output lived only in its own transcript and was never ingested into a repository artifact before the session context was lost. This file does **not** claim byte-exact preservation, does **not** contain invented quotes, does **not** assert an original report SHA-256 (none exists), and does **not** alter finding substance. Every section below cites the canonical sources that support it.

Canonical sources used (all already-preserved evidence):

- `S1` — `docs/reports/security/remediation/REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md` (correction appendix recording all ten findings verbatim-by-disposition, §"CORRECTION PASS").
- `S2` — `docs/reports/security/decisions/S0-F01-FILE-OWNERSHIP-RATIFICATION-001.md` + `docs/workforce/registries/decisions.jsonl` `ANOX-DECISION-S0-F01-RATIFICATION-001` (F-01 verdict detail, 10-condition verification matrix, 13/13-probe evidence, scope pins).
- `S3` — `docs/continuity/PROJECT_HISTORY_LEDGER.jsonl` `ANOX-EVENT-0053` + `docs/continuity/CURRENT_STATE.json` + `docs/workforce/WORKFORCE_STATE.json` (recorded retest result `PASS_WITH_FINDINGS`, dispositions, base SHAs).
- `S4` — `docs/reports/security/retests/TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001.md` (independent final verification of every finding's disposition on the corrected head).
- `S5` — `tools/audit/validate_s0_contract_freeze.py` + `tools/audit/test_s0_contract_freeze.py` + `tools/audit/validate_security_audit_evidence_preservation.py` + `tools/audit/test_security_audit_evidence_preservation.py` (machine-enforced corrections and test counts).

## 1. ORIGINAL RESULT

`INDEPENDENT-ARCHITECTURE-RETEST-S0-001 = PASS_WITH_FINDINGS` — the architecture retest **passed** the S0 contract freeze's core correctness criteria (eleven primary contract obligations independently verified) while recording **ten findings F-01…F-10** requiring correction or ratification before merge.

Provenance: `S1` appendix header; `S3` ledger `ANOX-EVENT-0053` findings/status; `S4` final dispositions.

## 2. FINDINGS F-01…F-10 (verbatim-by-disposition)

| ID | Subject (canonical substance) | Original disposition recorded | Provenance |
|---|---|---|---|
| F-01 | Disclosed file-ownership deviation — S0 edited `tools/audit/validate_security_audit_evidence_preservation.py`, outside the frozen Coverage Gate ownership matrix | `JUSTIFIED_MINIMAL_SUCCESSOR_SUPPORT` → `HUMAN_RATIFIED` | S1, S2 |
| F-02 | `check_scope` trusted the manifest-declared base SHA; invalid/non-ancestor bases could `SKIP` instead of fail | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |
| F-03 | Protected shared governance validator itself not content-pinned; unauthorized modification would pass | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |
| F-04 | Deferring-document set and schema markers were manifest-owned, so the manifest could narrow the enforced deference set | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |
| F-05 | Contract-to-authority mappings (SC/CC/breakers/attack chains) lacked validator-independent anchors — a coherent two-file remap could pass | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |
| F-06 | Successor-event acceptance added to the central validator without in-repo adversarial tests | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |
| F-07 | `[S0-000-02]` said "no other MSC unit is touched" while MSC-022 appeared as a supporting contract entry — role ambiguity | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |
| F-08 | CC rules named the Master consolidation as authority home — evidence presented as authority | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |
| F-09 | Dangling internal references `§8.4` in three clauses (should be `[S0-018-05]`) | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |
| F-10 | `B-002`/`B-009` freeze-registry rows lost their TRACK_B base pointers | `FIXED_PENDING_TARGETED_RETEST` → `FIXED` | S1, S4, S5 |

The reconstruction of each row is supported by the correction appendix's per-finding record (`S1`) and by the targeted retest's independent final dispositions (`S4`); finding substance is not altered.

## 3. F-01 VERDICT DETAIL (independently preserved evidence)

From `S2` (the Human ratification record, which preserves the retest's F-01 verdict detail):

- Retest verdict: `JUSTIFIED_MINIMAL_SUCCESSOR_SUPPORT` — the modification was additive successor-event acceptance required to record the S0 ledger event; it did not weaken existing validation.
- 10-condition verification matrix: all 10 conditions verified satisfied by the retest (additive-only diff, no weakened checks, pinned values, no generic acceptance, correct task/branch/head pins, no S1 use, no historical rewrite).
- 13-of-13 fail-closed adversarial probes verified against the modified validator.
- Human disposition: `RATIFIED_DISCLOSED_FILE_OWNERSHIP_DEVIATION`, `scope = ONE_TIME_CHANGE_SPECIFIC`, `grants_general_ownership = false`, `grants_s1_permission = false`, `grants_future_sessions = false`; content-pinned SHA-256 `756141b3…` (`S0_SUCCESSOR_EVENT_SUPPORT`); `S1_MUST_NOT_MODIFY_BEFORE_INTEGRATION = YES`; Coverage Gate matrix **not** rewritten.

## 4. WHAT THE ORIGINAL RETEST VERIFIED (recorded scope)

Per `S3`/`S4` and the freeze manifest's recorded verification surface:

- S0 contract validator `PASS`; adversarial tests `98/98` (53 original + 45 correction-hardening) — final count after correction.
- Central evidence validator `PASS`; central tests `253/253` (235 + 18 F-06 successor-event tests).
- 11 primary S0 contract units `FROZEN_IN_AUTHORITY`; MSC-022 supporting-only; MSC-039 consumed-not-reopened; `MSC_CLOSED_BY_S0 = 0`; `GLOBAL_OPEN_MSC = 42`.
- Contract coverage anchors: SC `14/14`, CC `14/14`, `SERVER_BREAKER_S1..S18` `18/18`, attack chains `9/9`, ambiguities `0`.
- Contract-only freeze: no server/client product implementation claimed or verified.

## 5. LIMITS OF THIS RECORD

- This file is **not** the original retest output and must not be cited as such.
- Where the original transcript contained prose beyond what the canonical sources preserve, that prose is **lost**; only the recorded result, finding set, dispositions, F-01 verdict detail and verified counts are preserved.
- Final merge-relevant dispositions (`F-01 = RATIFIED`, `F-02…F-10 = FIXED`, two residual LOW follow-ups) are established by `S4` — the later targeted retest — not by this record.
