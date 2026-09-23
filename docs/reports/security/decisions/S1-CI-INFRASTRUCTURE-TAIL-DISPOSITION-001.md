# ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001

**Canonical Human authorization record — S1 post-R2 CI-infrastructure tail disposition**

- **Decision ID:** `ANOX-DECISION-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001`
- **Date:** 2026-09-22
- **Authority:** Human Product & Security Owner (explicit written approval; this record is the canonical evidence of that approval — no invented signature)
- **Scope:** `ONE_TIME_CHANGE_SPECIFIC` — exactly the commits, paths, and governance transaction enumerated below. No standing permission, no blanket grant, no reusable slot.
- **Task:** `ANOX-TASK-S1-CI-INFRASTRUCTURE-TAIL-DISPOSITION-001`
- **Branch:** `integration/s1-after-s0-001`
- **Sealing ledger event:** `ANOX-EVENT-0058`

## 1. Authorized object

The Human Owner ratifies, as **authorized CI-infrastructure work only**, the five
`.github/workflows/ci.yml`-only commits below — their SHA identity, their exact
order, and their position immediately after the completed R1/R2 ratification
tail are all bound. The first four already existed on the delivery branch and
were forensically audited; the fifth (`T5`) was authorized by the same decision
as exactly one additional ci.yml-only commit:

| # | SHA | Parent | Changed paths | Purpose |
|---|-----|--------|---------------|---------|
| T1 | `e7bd2c6547fb23de44a8aa762fe5d046c34d318e` | `05dbcad25ab78a7ad468b6aede5a112cf8fd5e5f` | `.github/workflows/ci.yml` | full Git history (`fetch-depth: 0`) so the S1 provenance gate sees required history |
| T2 | `0636a4ee81e2e7ea9dd4ca7615d06bf80ae80827` | `e7bd2c6547fb23de44a8aa762fe5d046c34d318e` | `.github/workflows/ci.yml` | bind the authoritative native build to the pinned NDK path (`ANDROID_NDK_HOME`/`ANDROID_NDK_ROOT` from `setup-ndk` output) |
| T3 | `793246022c0501e85350113871d00db9ee843826` | `0636a4ee81e2e7ea9dd4ca7615d06bf80ae80827` | `.github/workflows/ci.yml` | bounded fail-fast emulator boot (10-minute cap, process-death detection), deterministic `ANDROID_AVD_HOME` for both instrumented jobs |
| T4 | `45d1e4a63de45fe10d2fc8f455b321bb675e390a` | `793246022c0501e85350113871d00db9ee843826` | `.github/workflows/ci.yml` | route seven compatible jobs to the self-hosted `[macOS, ARM64]` runner; x86_64 job untouched |
| T5 | `4fc5263ff6763768088f0f13856d704bd1772178` | `45d1e4a63de45fe10d2fc8f455b321bb675e390a` | `.github/workflows/ci.yml` | `ANOX-TASK-S1-CI-ARM64-ISOLATION-001`: deterministic stale-emulator isolation for the persistent ARM64 self-hosted runner |

For every one of the five commits the allowed changed-path set is exactly
`{ .github/workflows/ci.yml }`. Any commit in this position touching any other
path is outside this authorization.

## 2. What this decision does NOT authorize

- **No product code.** No `android/src/main/**`, `crypto/rust/**`, `backend/`,
  `supabase/`, `migrations/`, or `*.sql` change is authorized. None occurred in
  the ratified tail; the validators continue to forbid them.
- **No crypto/protocol change.** The ratified commits contain no cryptographic,
  protocol, key-management, or native-code modification.
- **No required-gate removal or weakening.** No required check was removed,
  made optional, skipped, or substituted. `connectedDebugAndroidTest` and the
  APK↔native-manifest binding verification are unchanged. Timeouts were not
  increased to mask failures.
- **x86_64 remains a required gate.** The instrumented `ubuntu-latest` x86_64
  job is untouched by this disposition and may not be removed, optionalized, or
  rerouted to ARM64. Its current non-execution is a GitHub billing/spending
  infrastructure blocker, not a code or security result.
- **ARM64 is not made optional either.** T5 hardens device isolation so the
  required ARM64 instrumented job (ABI `arm64-v8a`) runs deterministically on
  the persistent self-hosted runner; it does not weaken any assertion — it
  adds a fail-closed single-device assertion and unconditional cleanup.
- **No history rewrite.** R1 (`e65c23d0b8a9e7cf5a8abe25c85989bc3729ec11`) and
  R2 (`05dbcad25ab78a7ad468b6aede5a112cf8fd5e5f`) are untouched; no rebase,
  amend, squash, or force-push is authorized. The previously consumed fourth
  correction pair `7120aedd452bd77bbe208bb76a6d2c421394c820` /
  `c57485d7c54f57ab03cb2c896d796b2da787fc13` is promoted into the pinned
  `CONSUMED_CORRECTION_PAIRS` set and the last open correction slot is closed —
  no new generic slot is created.
- **No S2/S3/S4, no MSC closure, no B-004/B-005 start, no product
  development.**

## 3. Security rationale

Forensic re-verification showed every tail commit *strengthens or preserves* a
required gate rather than weakening one: provenance history availability (T1),
pinned-NDK binding (T2), bounded fail-fast emulator boot (T3), runner routing
with x86_64 preserved (T4), and deterministic stale-device isolation with a
fail-closed single-emulator assertion plus `if: always()` cleanup (T5).
Ratifying them by **exact SHA pins** — not by path signature alone — is
strictly stronger than the signature mechanism used for correction pairs:
substitution, reordering, omission, extra commits, and non-ci.yml paths all
fail closed.

## 4. Governance transaction carried by this decision

The extension is delivered as the disposition pair
`[R3a substantive, R3b metadata]` immediately after the pinned tail:

- **R3a (substantive, this transaction):** changes exactly the nine paths
  below — the lifecycle/topology validator, the S1 integration evidence
  validator, the protected shared governance validator, the frozen S0 contract
  validator, the S0 evidence-preservation validator (pinned adversarial test
  counts updated for the ratified suite growth), their three paired
  adversarial suites, and this record.
- **R3b (metadata):** a metadata-only synchronisation commit (continuity
  surfaces + sealing ledger event `ANOX-EVENT-0058`), restricted to the
  metadata allowlist.
- **`ANOX-EVENT-0058`:** a `governance`-type sealing event whose `end_head`
  equals the R3a substantive commit (recorded as `described_head`), bound to
  this record via `refs`.

The validators accept only this exact topology: merge + pinned S1 commits +
four consumed correction pairs + R1 + R2 + the five pinned tail commits +
[R3a, R3b]. Position, order, and SHA identity are all bound.

## 5. Authorized post-image pins (SHA-256 of the R3a file contents)

| File | SHA-256 |
|------|---------|
| `tools/audit/lifecycle_legality.py` | `519e99f75139df62e80084933dbbedec18459bb1b97940da057dac501754ec19` |
| `tools/audit/validate_s1_integration_evidence.py` | `7a67df1e7575116ca2bc4bcb0f54d3456065ea789dcb66fd8ee958e8c6a86493` |
| `tools/audit/validate_security_audit_evidence_preservation.py` | `fe5abd4e7a39029a679be336589d8aa766b80c72862a5bb77f05693a30034899` |
| `tools/audit/validate_s0_contract_freeze.py` | `0978b8a53ee50f411c07699c0b33ece7da451b6534c9bad5c522af9700cb77b2` |
| `tools/audit/test_s1_integration_evidence.py` | `ef40790e43d0524ac824b199f576a9dcd38a72e943fc24313e414f3725af0ea8` |
| `tools/audit/test_security_audit_evidence_preservation.py` | `29399c5ddb54909b94bf046d257608da52c39bd4ae94a76508ca21e60ac0ae0c` |
| `tools/audit/test_s0_contract_freeze.py` | `97d7896009235e5138aed86d6a7b7361d0cb333b605208d899900dc498832fa4` |
| `tools/audit/validate_s0_evidence_preservation.py` | `671aa5a9350d6b36421d5d94de9360e1414fda258cdc53af2ffbfde33e016ca2` |

The protected shared governance file
(`tools/audit/validate_security_audit_evidence_preservation.py`) post-image is
pinned both above and inside `validate_s0_contract_freeze.py`
(`s1_ci_disposition_authorized_sha256`), which is itself pinned externally in
this table — the same disclosed no-fixed-point residual pattern the R1
transaction documented, closed by this external pin record.

## 6. Validator / test effects (all fail-closed, nothing weakened)

- `lifecycle_legality.canonical_integration_delivery` gains an explicit
  `authorized_ci_tail` parameter: position-bound (only after completed R1/R2),
  SHA-pinned, order-bound, per-commit path-bound; plus the optional
  `disposition_paths` pair [R3a signature, R3b metadata].
- `validate_s1_integration_evidence.py` pins the tail SHAs, the disposition
  path signature, the sealing event `ANOX-EVENT-0058`, and the post-images
  above; the fourth correction pair is promoted into `CONSUMED_CORRECTION_PAIRS`
  and `S1_CORRECTION_TASK` is closed (`None`).
- `validate_security_audit_evidence_preservation.py` (protected shared file)
  carries the same pins (duplicated on purpose, drift-checked), the same
  topology binding, and the `ANOX-EVENT-0058` ledger-tail acceptance.
- `validate_s0_contract_freeze.py` admits the fourth authorized protected-file
  content only with the exact transaction proof (R1 signature-located, R2
  metadata-only, five pinned tail commits, R3a signature, R3b metadata-only)
  plus this record with verified live post-image pins.
- New adversarial tests cover: valid tail acceptance, SHA substitution,
  reordering, missing tail commit, extra unpinned CI commit, non-ci.yml path,
  tail before completed R1/R2, second T5-like commit, disposition without
  tail, non-metadata R3b, wrong `described_head`, tampered sealing `end_head`,
  missing decision record, manipulated post-image pins. No existing negative
  test was removed or weakened.

## 7. Final governance state

- S1 remains **not integrated**: integration completes only via Human merge of
  PR #37 into canonical `main` followed by the required post-merge audit.
- `MSC_CLOSED=0`; 42 MSC units open; `B-004`/`B-005` `NOT_STARTED`; product
  `BLOCKED_PENDING_FINAL_AUDIT`.
- Required instrumented CI: ARM64 hardened by T5; x86_64
  `INFRASTRUCTURE_BLOCKED` (GitHub billing/spending limit) — explicitly not a
  code or security pass.
- `ONE_TIME_CHANGE_SPECIFIC`: this decision is consumed by the transaction it
  authorizes and grants nothing beyond it.
