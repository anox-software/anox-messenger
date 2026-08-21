# B-025 Package Manifest

This package is designed so a new chat can understand both **where anoX is going** and **where the actual code currently is**.

- `00_START/`: start instruction, bootstrap prompt, required inputs.
- `01_CURRENT_AUTHORITY/`: current security/architecture truth and all B-001…B-025 files.
- `02_STATE/`: current project, progress, Git and test-evidence state.
- `03_WORKFLOWS/`: AI workflow plus Step 3 code compatibility and Step 4 Git/resume workflows.
- `04_REPOSITORY/`: clean source at Git HEAD `c076528e26e5e3ed05b4d0aeed794894f1f78b5e` plus full Git bundle/provenance manifest.
- `05_ENGINEERING_NEXT/`: next gate and non-executable draft Device Auth prompt.
- `06_AUDITS/`: B-024/B-025 and repository audit/validation reports.
- `07_DEVIN_HISTORY/`: current and historical Devin prompt/output archives.
- `90_HISTORICAL/`: Raw1.1/superseded docs, old progress, old MAIN/current-RAW/audit material.

The clean source snapshot intentionally omits local build caches and untracked machine-specific `local.properties`. The Git bundle preserves available commit history.
