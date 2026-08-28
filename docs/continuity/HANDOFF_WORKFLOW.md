# Handoff Workflow

**Authority:** B-026

## Normal handoff lifecycle

1. Chat A becomes slow or context too large.
2. Finish the current Devin task cleanly.
3. Ensure the working tree is clean and the state is documented.
4. Update current-state surfaces:
   - `PROJECT_STATE.md`
   - `FORTSCHRITT.md`
   - `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
   - `docs/continuity/CURRENT_HANDOFF.md`
   - `docs/continuity/CURRENT_GIT_STATE.md`
   - `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md`
   - `docs/continuity/CURRENT_OPEN_WORK.md`
   - `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md`
   - `docs/continuity/CURRENT_STATE.json`
5. Run live repository validation:
   ```bash
   python3 tools/continuity/validate_continuity.py --mode live
   ```
   This mode requires `.git` and validates live Git state as well as current-state consistency.
6. Generate a handoff package:
   ```bash
   python3 tools/continuity/generate_handoff.py
   ```
7. Extract the generated ZIP into a clean temporary directory and run archive validation:
   ```bash
   python3 tools/continuity/validate_continuity.py --mode archive --archive <extracted-dir>
   ```
   This mode validates package integrity and recorded state without `.git`.
   A package is not fully validated until both live and archive modes PASS.
8. Upload `artifacts/handoff/ANOX_HANDOFF_*.zip` or provide direct repository access.
9. The new AI runs the bootstrap from `docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md`,
   choosing either `LIVE SOURCE MODE` or `SNAPSHOT MODE`.
10. On `PASS`, perform handoff acceptance review.
11. Chat A becomes archive; development continues only in Chat B.

## Emergency handoff

If a chat must be abandoned mid-task, the handoff package must be labeled `EMERGENCY / DIRTY HANDOFF`
and list all uncommitted and partial changes. The new AI must resolve the dirty state before
continuing. Live-source reconciliation is required before new write work.

## HANDOFF SNAPSHOT INVARIANT

`HANDOFF SNAPSHOT != LIVE SOURCE`

A valid handoff proves the integrity and internal consistency of the generated snapshot. It does
not prove that the live repository has not changed since handoff generation. Archive-only bootstrap
may reconstruct state. Before new productive write work, live-source reconciliation is required
whenever live Git becomes available.
