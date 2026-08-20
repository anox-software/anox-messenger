# Current Upload Requirements

**Authority:** B-026

## Preferred workflow

### If the new AI has direct repository access

Provide only:

- `artifacts/handoff/ANOX_HANDOFF_*.zip` (latest generated package)
- Repository URL: `https://github.com/anox-admin/ax-messenger.git`

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
