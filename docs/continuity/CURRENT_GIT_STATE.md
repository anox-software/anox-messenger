# CURRENT GIT STATE

**Recorded:** 2026-08-20

---

## Model — baseline vs handoff state

This document distinguishes the **merged baseline** on `main` from the **current handoff / work state** on the feature/governance branch.

The handoff package is generated from the current work branch. Its exact HEAD is recorded in `GIT_SNAPSHOT.txt` at the moment of generation and in the live repository, not in a hard-coded line that can become stale.

The machine-readable canonical state is in `docs/continuity/CURRENT_STATE.json`.

## Merged baseline

- Repository: `https://github.com/anox-admin/ax-messenger.git`
- Baseline branch: `main`
- Baseline HEAD: `648b70391085ea5252cc9f88375064420f1b78d9`
- Latest merge to `main`: PR #2 → `75c11c823ec68cea576912b4095fa7a26ed33a33` (B-025 sync + Android backup hardening)
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- Latest CI on `main`: `32377964672` — Rust, Android debug, Android release compile smoke PASS

## Current handoff / work state

- Current handoff branch: `governance/continuity-001`
- Current handoff HEAD: `__HANDOFF_HEAD__` (resolve with `git rev-parse HEAD` or `GIT_SNAPSHOT.txt`)
- Working tree: `__WORKING_TREE__` (resolve with `git status --short`)
- Open relevant PR: `#3` to `main`
- Latest correction: `CONTINUITY-001.4` APK content / secret leakage release gate
- Next gate: `CONTINUITY-001.4 — APK content / secret leakage release gate`

## GitHub governance limitations

- Branch protection: UNAVAILABLE (free private plan)
- Secret scanning / push protection: UNAVAILABLE (free private plan)

## Rule

A future AI must verify the live Git state using `git` commands, not blindly trust this file. Compare `CURRENT_STATE.json`, `CURRENT_HANDOFF.md`, and `GIT_SNAPSHOT.txt` with the actual repository.