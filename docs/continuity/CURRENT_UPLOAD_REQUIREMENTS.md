# Current Upload Requirements

**Authority:** B-026

## New-AI bootstrap modes

A handoff recipient may be in one of two modes:

- **LIVE SOURCE MODE:** The new AI can access the repository. It should run `validate_continuity.py`
  in `--mode live`, inspect live Git, and compare it with the archive records.
- **SNAPSHOT MODE:** The new AI has only the `ANOX_HANDOFF_*.zip`. It should run `validate_continuity.py`
  in `--mode archive` and reconstruct state from the package. It must NOT conflate snapshot
  reconstruction with live verification.

Before any new product/governance write task from a pure snapshot bootstrap:
`LIVE SOURCE RECONCILIATION REQUIRED` unless operating under an explicitly documented
emergency/degraded process.

## Preferred workflow

### If the new AI has direct repository access

Provide only:

- `artifacts/handoff/ANOX_HANDOFF_*.zip` (latest generated package)
- Canonical repository: `https://github.com/anox-software/anox-messenger` (SSH: `git@github.com:anox-software/anox-messenger.git`)

The new AI reads the live repository and the handoff package.

### If the new AI does NOT have direct repository access

Upload:

- `artifacts/handoff/ANOX_HANDOFF_*.zip` (latest generated package)
- A clean repository snapshot as a second ZIP, only if the repository cannot be accessed

### Devin output created after the handoff

If additional Devin output was produced after the handoff package was generated, also upload that output.

## What is inside the handoff ZIP

- `docs/authority/`
- `docs/continuity/`
- `PROJECT_STATE.md`
- `FORTSCHRITT.md`
- `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- `MAIN_PLAN_DE.md`
- Relevant current reports from `docs/reports/`
- Selected historical indexes from `docs/history/`
- Git metadata snapshot
- File manifest
- SHA-256 manifest

## What is NOT in the handoff ZIP

- `.git/` object database
- `build/`, `.gradle/`, `target/`
- `local.properties`
- Keystores, `.jks`, `.p12`, `.keystore`
- `.env` or environment files
- Production credentials
- Large generated artifacts
