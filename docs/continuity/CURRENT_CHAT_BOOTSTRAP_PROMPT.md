# Current Chat Bootstrap Prompt

**Authority:** B-026 + `DEVELOPMENT_SECURITY_WORKFLOW_V1.md`

---

You are bootstrapping into an existing anoX Messenger V1 project. Do not write or modify code in this first pass. Return a read-only bootstrap audit.

## Steps

1. Inventory all supplied anoX files. Accept either:
   - an `ANOX_HANDOFF_*.zip` package, or
   - direct access to the repository at `https://github.com/anox-admin/ax-messenger.git`.

2. Read the current authority in this order:
   - `docs/authority/AUTHORITY_INDEX.md`
   - `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
   - `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
   - `docs/authority/CLOUD_AI_SECRET_PROTECTION.md`
   - `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`
   - `docs/authority/B_FREEZE_REGISTRY.md`
   - `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md`

3. Read the current state in this order:
   - `docs/continuity/CURRENT_HANDOFF.md`
   - `docs/continuity/CURRENT_GIT_STATE.md`
   - `docs/continuity/CURRENT_STATE.json`
   - `PROJECT_STATE.md`
   - `FORTSCHRITT.md`
   - `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
   - `GIT_SNAPSHOT.txt`

4. Inspect the actual repository and Git state:
   - `git remote -v`
   - `git branch --show-current`
   - `git rev-parse HEAD`
   - `git status --short`
   - `git tag --list`
   - `git log --oneline -n 15`

5. Compare the recorded `CURRENT_GIT_STATE.md`, `CURRENT_STATE.json`, and `GIT_SNAPSHOT.txt` with the live Git state. Report any discrepancy.

6. Verify the presence of:
   - `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
   - `docs/authority/CLOUD_AI_SECRET_PROTECTION.md`
   - `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`
   - `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
   - `docs/authority/B_FREEZE_REGISTRY.md`
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

10. Treat historical `docs/history/B025/` material as provenance only. Never reactivate superseded RAW rules. Never invent Raw1.0.

11. Do not modify source code, Gradle versions, NDK, or build configuration in this bootstrap pass.

12. Return a structured bootstrap report with:
    - A. MERGED BASELINE
    - B. CURRENT HANDOFF HEAD
    - C. WORKING TREE
    - D. ARCHITECTURE AUTHORITY PRESENT
    - E. CONTINUITY FILES PRESENT
    - F. STATE MATCHES LIVE REPO
    - G. SECURITY INVARIANTS CURRENT
    - H. NEXT GATE
    - I. RESULT: `PASS` or `BLOCKED`

    The report must also answer these required governance reconstruction questions:
    1. Is B-002 merged?
    2. Is B-003 merged?
    3. What comes next?
    4. What is S0–S4?
    5. Are per-PR Frontier audits mandatory during normal V1 development? (expected: NO)
    6. What happens to known HIGH/CRITICAL findings? (expected: IMMEDIATE MERGE BLOCKERS)
    7. What is the Cloud-AI secret invariant?
    8. Are production user private keys allowed in Cloud AI? (expected: NO)
    9. When does B-017-Lite occur? (expected: AFTER GOVERNANCE/HANDOFF HARDENING, BEFORE B-004/B-005)
    10. When does the full READ-ONLY AI audit occur? (expected: AFTER FUNCTIONAL V1)
    11. Is an external human audit still required? (expected: YES)
    12. Is `main` PR-only under the new governance? (expected: YES)
    13. Should model recommendations be embedded inside Devin prompts? (expected: NO)

End with exactly:

```
BOOTSTRAP RESULT: PASS — READY TO ACCEPT HANDOFF
```

or

```
BOOTSTRAP RESULT: BLOCKED — <reason>
```

Then stop. Do not start the next engineering task.
