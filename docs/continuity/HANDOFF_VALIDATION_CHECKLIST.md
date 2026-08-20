# Handoff Validation Checklist

**Authority:** B-026

## Required checks

- [ ] `PROJECT_STATE.md` is current
- [ ] `FORTSCHRITT.md` is current
- [ ] `DEVIN_PROMPT_OUTPUT_ARCHIV.md` is current
- [ ] `docs/continuity/CURRENT_HANDOFF.md` is current
- [ ] `docs/continuity/CURRENT_GIT_STATE.md` is current
- [ ] `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md` is current
- [ ] `docs/continuity/CURRENT_OPEN_WORK.md` is current
- [ ] `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md` is current
- [ ] Working tree is clean (or emergency dirty handoff is explicitly declared)
- [ ] Last Devin task is archived in `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- [ ] Latest tests are recorded truthfully
- [ ] Latest CI is recorded
- [ ] Open PRs are recorded
- [ ] Architecture deviations are recorded
- [ ] Next gate is defined

## Validation command

```bash
python3 tools/continuity/validate_continuity.py
```

## Result

If every item above is satisfied and the script returns `0`:

`HANDOFF READINESS = PASS`
