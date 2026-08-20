# Handoff Workflow

**Authority:** B-026

## Normal handoff lifecycle

1. Chat A becomes slow or context too large.
2. Finish the current Devin task cleanly.
3. Ensure the working tree is clean and the state is documented.
4. Update:
   - `PROJECT_STATE.md`
   - `FORTSCHRITT.md`
   - `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
   - `docs/continuity/CURRENT_HANDOFF.md`
   - `docs/continuity/CURRENT_GIT_STATE.md`
   - `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md`
   - `docs/continuity/CURRENT_OPEN_WORK.md`
   - `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md`
5. Generate a handoff package:
   ```bash
   python3 tools/continuity/generate_handoff.py
   ```
6. Validate handoff readiness:
   ```bash
   python3 tools/continuity/validate_continuity.py
   ```
7. Create a new ChatGPT chat.
8. Upload `artifacts/handoff/ANOX_HANDOFF_*.zip` or provide direct repository access.
9. The new AI runs the bootstrap from `docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md`.
10. On `PASS`, perform handoff acceptance review.
11. Chat A becomes archive; development continues only in Chat B.

## Emergency handoff

If a chat must be abandoned mid-task, the handoff package must be labeled `EMERGENCY / DIRTY HANDOFF` and list all uncommitted and partial changes. The new AI must resolve the dirty state before continuing.
