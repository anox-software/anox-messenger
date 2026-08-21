# Historical Handoffs

This directory contains lightweight metadata and index files for previous handoff packages.

Generated `ANOX_HANDOFF_*.zip` files are local artifacts and are not normally committed to Git.

## Index

| Handoff | Date | HEAD | Package | Notes |
|---------|------|------|---------|-------|
| B-025 | 2026-08-20 | `7db20fa...` | `ANOX_MASTER_HANDOFF_B025_2026-08-20.zip` (reference master; SHA-256 `bcc40...`) | Original manually created master handoff; contents archived in `docs/history/B025/` |
| CONTINUITY-001 | 2026-08-20 | `648b703...` | `artifacts/handoff/ANOX_HANDOFF_2026-08-20_648b703.zip` | First continuity-governance handoff |

Add new rows for each generated handoff. Store large ZIPs under `artifacts/handoff/`, not here.

## Historical provenance archive

- `docs/history/B025/` contains the full B-025 master handoff provenance (start, workflows, audits, Devin history, RAW/Raw1.1, repository provenance).
- `docs/history/B025/SOURCE_INDEX.md` maps every imported historical source to its original B-025 master path.
