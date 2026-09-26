# Security Remediation State — MSC Stage Registry

Machine-enforced by `tools/audit/validate_b021_verification_matrix.py`
(MSC-UNIT-038, REMEDIATION-SESSION-S1-CLEAN-REBUILD-001).

`msc_state.jsonl` holds one record per `MSC-UNIT-*` tracking the canonical
remediation stage chain:

```
IMPLEMENTED → AUTOMATED_TESTED → RUNTIME_TESTED → INDEPENDENTLY_RETESTED
            → ATTACKCHAIN_RETESTED → PHYSICAL_VERIFIED → EVIDENCE_PRESERVED
            → CLOSED
```

`msc_state.jsonl` is an **overlay** on the canonical MSC universe — the 44
consolidated `msc_unit` records preserved in
`docs/security/audit-evidence/audit_traceability.jsonl` (42
`OPEN_PENDING_REMEDIATION_COVERAGE_GATE`, 2 `REJECTED_NOT_A_FINDING`). The
validator resolves that universe itself; the overlay never defines it. A
canonical OPEN unit with no overlay record remains OPEN.

Rules enforced by the validator (fail-closed):

- Universe reconciliation: canonical universe unresolvable / wrong size,
  empty overlay, unknown unit, duplicate or conflicting record, malformed unit
  id or lifecycle state — all FAIL. A record for a REJECTED unit is illegal.
- `--check integrity` is **S1 UNIT VALIDATION** and says so; `--check closure`
  is **GLOBAL REMEDIATION CLOSURE** and fails whenever `MSC OPEN > 0`.
- A stage may be `PASS` only when every earlier stage is `PASS` (or
  `NOT_APPLICABLE` where the frozen coverage-gate table marks the stage `-`).
  `IMPLEMENTED → CLOSED` jumps are impossible.
- Frozen stage requirements per unit (gate `Stages` column: `R` =
  RUNTIME_TESTED, `C` = ATTACKCHAIN_RETESTED, `P` = PHYSICAL_VERIFIED) may
  never be `NOT_APPLICABLE`.
- `IMPLEMENTED` / `AUTOMATED_TESTED` `PASS` requires non-empty `evidence_refs`
  that resolve: an existing repository path, a `git:<sha>` that is a real
  commit, or a preserved-evidence identifier. A bare identifier-shaped string
  (`ANOX-…`, `SEC-…`) never resolves on its own.
- `RUNTIME_TESTED` / `INDEPENDENTLY_RETESTED` / `ATTACKCHAIN_RETESTED` /
  `PHYSICAL_VERIFIED` / `EVIDENCE_PRESERVED` / `CLOSED` `PASS` requires EVERY
  `evidence_refs` entry to be an `ANOX-EV-*` identifier that resolves to a
  record in `evidence_registry.jsonl` of an admissible class, bound to the
  same unit, `status = PRESERVED`, with an artifact path whose SHA-256 still
  matches, an `authority_ref` that exists, and a session/actor identity.
- `RUNTIME_TESTED = PASS` on a provenance-required unit (gate `Prov = Y`)
  requires a `provenance` object carrying BOTH `build_artifact_hash_proof`
  and `provenance_verified_native_runtime`, covering every required ABI
  (`arm64-v8a` AND `x86_64`) with equal SHA-256 values — FCP-1. The
  `manifest_ref` must resolve to a `BUILD_ARTIFACT_HASH_PROOF` record whose
  recorded build carries exactly those per-ABI hashes; each per-ABI
  `evidence_ref` must resolve to a `PROVENANCE_VERIFIED_NATIVE_RUNTIME`
  record with the same `source_sha`/`build_id`, the right ABI, and an explicit
  `provenance_relation.derived_from` pointing at that hash-proof record.
- FCP-7 is NOT `implementer_name != retester_name`. A retest stage `PASS`
  must resolve to a retest-class record whose `session` and `recorded_by` are
  distinct from the implementing session, whose `retest_of` names the
  implementing session, and whose actor equals the stage's `recorded_by`.
- `CLOSED = PASS` requires all stages resolved.

`evidence_registry.jsonl` record shape:

```json
{
  "record_type": "remediation_evidence",
  "evidence_id": "ANOX-EV-<CLASS>-<NNN>",
  "evidence_type": "PROVENANCE_VERIFIED_NATIVE_RUNTIME",
  "msc_unit": "MSC-UNIT-001",
  "status": "PRESERVED",
  "recorded_by": "<actor>", "session": "<session id>", "recorded_at": "YYYY-MM-DD",
  "artifact": {"path": "docs/security/…", "sha256": "<64 hex>"},
  "build": {"source_sha": "<40 hex>", "build_id": "gha-…", "per_abi_sha256": {"arm64-v8a": "…", "x86_64": "…"}},
  "abi": "arm64-v8a",
  "provenance_relation": {"derived_from": ["ANOX-EV-HP-001"]},
  "retest_of": "<implementing session>  (retest classes only)",
  "authority_ref": "docs/…/<authorization record>"
}
```

The registry is currently empty: no RUNTIME_TESTED or INDEPENDENTLY_RETESTED
evidence exists for any S1 unit; those stages remain `PENDING`.

Current truth: MSC OPEN = 42, MSC CLOSED = 0. The four S1-scoped units
(MSC-UNIT-001/002/003/038) are tracked here; no unit is closed merely
because implementation or tooling exists.

Record shape:

```json
{
  "record_type": "msc_unit_remediation_state",
  "msc_unit": "MSC-UNIT-001",
  "implementing_session": "REMEDIATION-SESSION-S1-CLEAN-REBUILD-001",
  "stages": {
    "IMPLEMENTED": {"result": "PASS", "evidence_refs": ["..."], "recorded_by": "...", "recorded_at": "2026-09-24"},
    "AUTOMATED_TESTED": {"result": "PASS", "evidence_refs": ["..."]},
    "RUNTIME_TESTED": {"result": "PENDING", "reason": "..."},
    "INDEPENDENTLY_RETESTED": {"result": "PENDING"},
    "ATTACKCHAIN_RETESTED": {"result": "PENDING"},
    "PHYSICAL_VERIFIED": {"result": "NOT_APPLICABLE", "reason": "gate: stage '-'"},
    "EVIDENCE_PRESERVED": {"result": "PENDING"},
    "CLOSED": {"result": "PENDING"}
  },
  "notes": "..."
}
```
