# anoX V1 Documentation Guide

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

## Source of Truth

1. **Implementation source of truth:** repository code + executed tests.
2. **Architecture source of truth:** `docs/current/` + `SECURITY_INVARIANTS.md`.
3. **Historical reasoning:** `docs/history/raw1.1/`.
4. **Validation evidence:** `docs/security/` reports (marked with their original test status; newer reports supersede older ones).

## Directory Layout

```text
docs/
  current/              current canonical architecture
  history/raw1.1/       historical/superseded Raw1.1 analysis
  security/             security reports and historical validation evidence
  architecture/         historical architecture documents (current canonical is in docs/current/)
  decisions/            historical and current decision records
  specifications/       historical and current specifications
  reports/              project audit and synchronization reports
```

## Important Rule

Future coding agents must **not** use Raw1.1 historical docs as current architecture. Always verify decisions against `docs/current/` and `SECURITY_INVARIANTS.md`.
