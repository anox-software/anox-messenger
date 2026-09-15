# Security Remediation State — MSC Stage Registry

Machine-enforced by `tools/audit/validate_b021_verification_matrix.py`
(MSC-UNIT-038, REMEDIATION_SESSION_S1).

`msc_state.jsonl` holds one record per `MSC-UNIT-*` tracking the canonical
remediation stage chain:

```
IMPLEMENTED → AUTOMATED_TESTED → RUNTIME_TESTED → INDEPENDENTLY_RETESTED
            → ATTACKCHAIN_RETESTED → PHYSICAL_VERIFIED → EVIDENCE_PRESERVED
            → CLOSED
```

Rules enforced by the validator (fail-closed):

- A stage may be `PASS` only when every earlier stage is `PASS` (or
  `NOT_APPLICABLE` where the frozen coverage-gate table marks the stage `-`).
  `IMPLEMENTED → CLOSED` jumps are impossible.
- Frozen stage requirements per unit (gate `Stages` column: `R` =
  RUNTIME_TESTED, `C` = ATTACKCHAIN_RETESTED, `P` = PHYSICAL_VERIFIED) may
  never be `NOT_APPLICABLE`.
- `PASS` requires non-empty `evidence_refs` that resolve inside the repo (or
  `git:`/`ANOX-` identifier refs).
- `RUNTIME_TESTED = PASS` on a provenance-required unit (gate `Prov = Y`)
  requires evidence refs binding to the authoritative native build lineage
  (`native-manifest.json` / `BUILD_ARTIFACT_HASH_PROOF` /
  `PROVENANCE_VERIFIED_NATIVE_RUNTIME`) — FCP-1.
- `INDEPENDENTLY_RETESTED` / `ATTACKCHAIN_RETESTED` / `PHYSICAL_VERIFIED`
  marked `PASS` must be recorded by a different authority than the
  implementing session — FCP-7.
- `CLOSED = PASS` requires all stages resolved.

Record shape:

```json
{
  "record_type": "msc_unit_remediation_state",
  "msc_unit": "MSC-UNIT-001",
  "implementing_session": "REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001",
  "stages": {
    "IMPLEMENTED": {"result": "PASS", "evidence_refs": ["..."], "recorded_by": "...", "recorded_at": "2026-09-15"},
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
