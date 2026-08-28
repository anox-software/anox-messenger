# Handoff Validation Checklist

**Authority:** B-026

## Pre-generation live validation (requires `.git`)

- [ ] `PROJECT_STATE.md` is current
- [ ] `FORTSCHRITT.md` is current
- [ ] `DEVIN_PROMPT_OUTPUT_ARCHIV.md` is current
- [ ] `docs/continuity/CURRENT_HANDOFF.md` is current
- [ ] `docs/continuity/CURRENT_GIT_STATE.md` is current
- [ ] `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md` is current
- [ ] `docs/continuity/CURRENT_OPEN_WORK.md` is current
- [ ] `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md` is current
- [ ] Working tree is clean (or emergency dirty handoff is explicitly declared)
- [ ] All completed substantive Devin tasks preceding the current continuity synchronization are archived in `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
- [ ] The current continuity synchronization is explicitly represented by the current Git HEAD and the updated authoritative continuity surfaces (it is not required to archive itself within the same commit)
- [ ] Latest tests are recorded truthfully
- [ ] Latest CI is recorded
- [ ] Open PRs are recorded
- [ ] Architecture deviations are recorded
- [ ] Next gate is defined
- [ ] Recorded `baseline_head` matches real `main` HEAD (`git rev-parse main`)
- [ ] Recorded `handoff_branch` matches current branch

### Command

```bash
python3 tools/continuity/validate_continuity.py --mode live
```

Expected: `LIVE_GIT_VERIFICATION: PASS`

## Post-generation archive validation (no `.git` required)

- [ ] `MANIFEST.txt` and `SHA256_MANIFEST.txt` are present
- [ ] File hashes match `SHA256_MANIFEST.txt`
- [ ] Required authority/continuity files are present
- [ ] `GIT_SNAPSHOT.txt` matches `CURRENT_GIT_STATE.md` and `CURRENT_STATE.json`
- [ ] No `.git/` content is packaged
- [ ] No forbidden secret artifacts are packaged
- [ ] `CURRENT_STATE.json` placeholders were resolved before packaging

### Command

```bash
python3 tools/continuity/validate_continuity.py --mode archive --archive <extracted-dir>
```

Expected: `HANDOFF_ARCHIVE_VALIDATION: PASS` and `LIVE_GIT_VERIFICATION: UNAVAILABLE`

## Result

If both modes (when applicable) return `0`:

`HANDOFF READINESS = PASS`
