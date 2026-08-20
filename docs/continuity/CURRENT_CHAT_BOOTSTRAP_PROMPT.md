# Current Chat Bootstrap Prompt

**Authority:** B-026

---

You are bootstrapping into an existing anoX Messenger V1 project. Do not write or modify code in this first pass. Return a read-only bootstrap audit.

## Steps

1. Inventory all supplied anoX files. Accept either:
   - an `ANOX_HANDOFF_*.zip` package, or
   - direct access to the repository at `https://github.com/anox-admin/ax-messenger.git`.

2. Read the current authority in this order:
   - `docs/authority/AUTHORITY_INDEX.md`
   - `docs/authority/SECURITY_INVARIANTS_V1_1.md`
   - `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
   - `docs/authority/B025/B_FREEZE_REGISTRY.md`

3. Read the current state in this order:
   - `docs/continuity/CURRENT_HANDOFF.md`
   - `docs/continuity/CURRENT_GIT_STATE.md`
   - `PROJECT_STATE.md`
   - `FORTSCHRITT.md`
   - `DEVIN_PROMPT_OUTPUT_ARCHIV.md`

4. Inspect the actual repository and Git state:
   - `git remote -v`
   - `git branch --show-current`
   - `git rev-parse HEAD`
   - `git status --short`
   - `git tag --list`
   - `git log --oneline -n 15`

5. Compare the recorded `CURRENT_GIT_STATE.md` with the live Git state. Report any discrepancy.

6. Verify the presence of:
   - `docs/authority/B025/`
   - `docs/continuity/`
   - `tools/continuity/generate_handoff.py`
   - `tools/continuity/validate_continuity.py`
   - `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`

7. Verify the working tree is clean. If it is not, list the dirty files and declare `BLOCKED` unless the handoff is explicitly marked as an emergency dirty handoff.

8. Read the `README.md` for the high-level project description.

9. Distinguish target truth from implementation truth:
   - B-025 frozen architecture = what must be built
   - repository code and tests = what is actually implemented

10. Treat historical `docs/history/raw1.1/` material as provenance only. Never reactivate superseded RAW rules. Never invent Raw1.0.

11. Do not modify source code, Gradle versions, NDK, or build configuration in this bootstrap pass.

12. Return a structured bootstrap report with:
    - A. BASELINE
    - B. HEAD
    - C. WORKING TREE
    - D. ARCHITECTURE AUTHORITY PRESENT
    - E. CONTINUITY FILES PRESENT
    - F. STATE MATCHES LIVE REPO
    - G. SECURITY INVARIANTS CURRENT
    - H. NEXT GATE
    - I. RESULT: `PASS` or `BLOCKED`

End with exactly:

```
BOOTSTRAP RESULT: PASS — READY TO ACCEPT HANDOFF
```

or

```
BOOTSTRAP RESULT: BLOCKED — <reason>
```

Then stop. Do not start the next engineering task.
