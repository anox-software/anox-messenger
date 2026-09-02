> **B-025 Architecture Authority Notice**
>
> B-025 is the current architecture authority. The `docs/authority/B025/` package is the historical immutable handoff snapshot; current architecture and mandatory amendments are recorded in `docs/authority/B_FREEZE_REGISTRY.md` and `docs/authority/B025_MANDATORY_AMENDMENTS_V1_1.md`. This file is a routing guide, not an architecture source of truth.

# anoX V1 Documentation Guide

**Status:** CURRENT
**Architecture Baseline:** B-025 plus mandatory amendments
**Last synchronized:** 2026-09-02

---

## Source of Truth

1. **Authority and architecture source of truth:** `docs/authority/AUTHORITY_INDEX.md` and the current `docs/authority/B_FREEZE_REGISTRY.md`.
2. **Implementation source of truth:** repository code + executed tests.
3. **Historical reasoning:** `docs/history/B025/` and other `docs/history/**` locations (provenance only, superseded).
4. **Validation evidence:** `docs/security/` reports (marked with their original test status; newer reports supersede older ones).

`docs/current/` contains advisory summaries and implementation-oriented notes. If any `docs/current/` text conflicts with `docs/authority/`, `docs/authority/` wins.

## Directory Layout

```text
docs/
  authority/            canonical current architecture authority and freeze registry
  current/              advisory summaries and implementation notes (non-authoritative)
  history/B025/         B-025 historical/superseded handoff provenance
  history/              other historical provenance
  security/             security reports and historical validation evidence
  architecture/         historical architecture documents (provenance only)
  decisions/            historical and current decision records
  specifications/       historical and current specifications (provenance only)
  reports/              project audit and synchronization reports
```

## Important Rule

Future coding agents must read `docs/authority/AUTHORITY_INDEX.md` first and verify decisions against the current Authority documents in `docs/authority/`. Historical `docs/history/` and `docs/current/` documents are not authoritative on their own.
