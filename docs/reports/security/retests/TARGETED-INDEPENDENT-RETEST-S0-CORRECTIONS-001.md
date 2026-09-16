# TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001 — VERBATIM PRESERVED REPORT

**Record class:** `S0_TARGETED_CORRECTION_RETEST` (verbatim transcript output preserved by `SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001`)
**Provenance:** independent fresh read-only session output, recovered from the session transcript. One table cell (F-07 evidence detail) was compressed by the session-history summarizer; the compressed span is explicitly marked `[compressed in persisted transcript — substance restored from canonical record]` and restores only facts already recorded in `REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md` and `S0_CONTRACT_FREEZE_MANIFEST.json`. No other text altered. No invented quotes.

---

# TARGETED INDEPENDENT SECURITY RETEST — FINAL REPORT

**RESULT: `PASS_WITH_FINDINGS`** (all 10 dispositions satisfy the §23 merge-blocker rule; 2 residual **LOW** observations, no MEDIUM-or-higher)

**TASK** `TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001`
**MODEL** Claude Opus 5 — Medium (fresh independent session)
**CORRECTED S0 HEAD** `0be57335adaa25ad584357dde74666eb97339a01`

> Note on §2: the implementer's `8756a94` is the **substantive** commit, not HEAD. `git rev-parse HEAD` = `0be5733…`, which is the metadata commit. The two-commit topology is intact, so this is a correct delivery, not a mismatch. Repo: `/Users/3xpress/Desktop/anoX Messanger` (branch `security/remediation-s0-contract-freeze-001`), clean, 2 task-authored commits above `0f93252`.

**TWO-COMMIT TOPOLOGY: PASS** — `0f93252` → `8756a94` (substantive, 14 files) → `0be5733` (metadata, 12 files, all inside `METADATA_ALLOWLIST`). No authority file smuggled into the metadata commit.

## Findings

| ID | Disposition | Evidence |
|---|---|---|
| **F-01** | **`RATIFIED_DISCLOSED_FILE_OWNERSHIP_DEVIATION`** | `docs/reports/security/decisions/S0-F01-FILE-OWNERSHIP-RATIFICATION-001.md` + machine record `ANOX-DECISION-S0-F01-RATIFICATION-001`. Human Product & Security Owner authority, exact task/file/deviation, `scope=ONE_TIME_CHANGE_SPECIFIC`, `grants_general_ownership/s1_permission/future_sessions = false`, `s1_prohibited_before_integration = true`. I independently recomputed both pinned hashes — ratified `756141b3…` = current file, pre-S0 `2ab59295…` = content at `0f93252`. Prospective and content-pinned, **not** historical rewriting: the Coverage Gate text is untouched (`original_rule_preserved: true`, gate file byte-identical since base). |
| **F-02** | **`FIXED`** | Base is now validator-owned (`AUTHORIZED_S0_BASE_SHA`), never manifest-driven. My own 7 probes **all FAIL, zero SKIP**: malformed `not-a-sha`; nonexistent `deadbeef…`; zero SHA; valid-but-unauthorized commit; `base_sha` removed; **true non-ancestor topology** (orphan HEAD → `"not an ancestor of HEAD — the S0 scope gate cannot be evaluated and must not be skipped"`); unauthorized S1-file change committed → `FAIL`. |
| **F-03** | **`FIXED`** | `PROTECTED_SHARED_GOVERNANCE_FILE` classification + content pin. All **10** of my probes fail closed: ratification removed; `ratified_files`→other file; `ratified_task`→other task; extra unauthorized edit to the protected file; blanket/future grant; `grants_s1_permission=true`; `authority_actor`→AI Agent; `ratified_sha256` repointed; canonical record deleted; file reverted to pre-S0. |
| **F-04** | **`FIXED`** | `REQUIRED_DEFERRING_DOCUMENTS` is validator-owned; manifest may only agree, never narrow. Case A (DB doc dropped from manifest + `"schema is not frozen"` restored) → FAIL; Case B (BACKEND) → FAIL; list emptied → FAIL; **manifest left intact, doc alone reasserts competing authority** → FAIL. |
| **F-05** | **`FIXED`** | Validator-owned anchors (`SC_/CC_/BREAKER_ANCHOR_CLAUSES`, `AC_ANCHORS`) defeat coherent manifest+table rewrites. Coherent SC-6 → `S0-042-*` in **both** sources → FAIL; CC-12 → FAIL; `SERVER_BREAKER_S7` → FAIL; AC-001 breakers and rule → FAIL; AC-003 clauses and rule → FAIL; AC-010 clauses and breakers → FAIL. *(Residual LOW — see below.)* |
| **F-06** | **`FIXED`** | Direct regression coverage present and passing: `test_238` valid EVENT-0053 accepted; `239` altered task; `240` altered `start_head`; `241` altered type; `242/243` altered/malformed refs; `244` EVENT-0054 arbitrary successor; `245` interposed; `246` duplicate; `247` EVENT-0052 removed; `248` second successor; `236` third task commit; `237` smuggled metadata file; `249/250/251` prior-evidence tampering. **253 tests, OK.** |
| **F-07** | **`FIXED`** | `[S0-000-02]` now reads "11 **primary** S0 contract units" + "**one supporting contract entry** `MSC-UNIT-022`… `[compressed in persisted transcript — substance restored from canonical record]` `MSC-UNIT-022` is a supporting contract entry only: not added to `msc_stage_proposals`, not advanced in the closure state machine, not claimed closed, keeps its frozen primary remediation ownership (session S4); `s0_role` is machine-enforced per contract (tests 77–81 fail closed on a supporting unit appearing as primary or in stage proposals). |
| **F-08** | **`FIXED`** | `[S0-000-15]` — evidence is not authority. All 14 CC rules now name an AUTHORITY_INDEX-indexed normative home, verified against **real primary authority rather than assuming**: Invariants 23/24 exist verbatim at `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md` (lines 28–29), the narrow Kotlin→JNI→Rust boundary at `ULTIMATE_MAIN_ARCHITECTURE_B025.md:27`, `[S0-033-07]` is a real V1.4 clause — and all three are AUTHORITY_INDEX-indexed (ranks 1, 7, 11). No new competing authority introduced. Naming consolidation or the Coverage Gate as owner fails closed. *(Residual LOW — see below.)* |
| **F-09** | **`FIXED`** | `DANGLING_INTERNAL_REFERENCES = 0`, machine-enforced. `§8.4` is **absent** from the whole amendment and manifest. Prior affected contexts corrected: `S0-033-01` `§8.4/§9` → `[S0-018-05]/§9`; `S0-018-03` → `[S0-018-05]`; `S0-032-01` reset reference resolved. `[S0-018-05]` is the real explicit-reset deletion-order clause. All 12 remaining `§n.m` refs resolve to existing `###` subsections. |
| **F-10** | **`FIXED`** | B-002 → `TRACK_B/B002_DEVICE_AUTHENTICATION.md` (base v1.1) **+** V1.4 (S0 amendments); B-009 → `TRACK_B/B009_LOCAL_DATABASE.md` (base v1.4) **+** V1.4. Diff is **Location column only** — Status/version strings byte-identical; no normative content changed for bookkeeping. |

## Residual observations (LOW — non-blocking)

1. **F-05 / CC-2, CC-4, CC-13, CC-14 have no anchor.** These four carry `clauses: []` by design (homed in pre-existing invariants/Track-B docs, no V1.4 clause). Consequently a *bogus* V1.4 clause can be **added** to their manifest `clauses` and still pass. No anchored security rule is lost and `owner`/`authority_home` remain enforced, so this is traceability noise, not a normative remap. CC-12 — the CC the task names — is anchored and fails closed.
2. **F-08 / `authority_home` is not cross-validated against AUTHORITY_INDEX.** The validator checks it is non-empty and does not name consolidation/gate evidence, but the string itself is free text — repointing CC-2 to an invented home passes, despite the error message promising "AUTHORITY_INDEX-indexed normative document". The F-08 requirement itself is met; the enforcement is one notch weaker than its own wording.

Also informational: `check_scope` still prints `SKIP git-diff checks` in fixture mode (no `.git`). Not reachable via any attacker-editable in-repo content, since the base is validator-owned.

## Suite results

| Check | Result |
|---|---|
| S0 CONTRACT VALIDATOR | **PASS** |
| S0 ADVERSARIAL TESTS | **98 tests — OK** |
| CENTRAL EVIDENCE VALIDATOR | **PASS** |
| CENTRAL EVIDENCE TESTS | **253 tests — OK** |
| `validate_continuity.py --mode live` | **PASS** (real repo; the clone's `LIVE_GIT_VERIFICATION` FAIL is the §21 clone artifact) |
| b027a / b027b / b027_integrity / b017_lite | **PASS** / **58 OK** / **PASS** / **PASS** |

**PREVIOUS SECURITY EVIDENCE WEAKENED: NO** — `validate_security_audit_evidence_preservation.py` untouched by the correction pass; `docs/reports/security/audits`, `docs/security/audit-evidence`, `docs/reports/security/gates` unchanged across the entire S0 range.
**S1-OWNED FILES CHANGED: 0** — none of the six listed paths; no Kotlin/Rust/backend/SQL/native changes. **PRODUCT BEHAVIOR CHANGED: NO**.
**S0_SHARED_VALIDATOR_EXCEPTION** = `SPECIFIC / HUMAN_RATIFIED / NON_GENERALIZABLE`; **S1_PERMISSION_TO_EDIT_SHARED_VALIDATOR** = `NO`.
**EVENT** `ANOX-EVENT-0053` remains the S0 event; no correction-only EVENT-0054. `described_head = 8756a94824ba9baef678176ef2ee24a2c302f1d0` (the substantive commit).
**MSC CLOSED: 0** · **GLOBAL OPEN MSC: 42**

**INDEPENDENT TARGETED RETEST: PASS**
**REPOSITORY MODIFIED: NO** · **WORKING TREE: CLEAN** · **REMOTE MUTATION: NONE** (all mutation testing done in scratch clone `/tmp/s0rt`; `origin/main` still `0f93252`)

## NEXT ACTION

`PRESERVE/FREEZE S0 REMEDIATION + INDEPENDENT RETEST EVIDENCE → MERGE S0 INTO MAIN`

Optionally hand the two LOW observations to a later hardening pass — they do not block merge under §23.
