# Current Chat Bootstrap Prompt

**Authority:** B-026 + `DEVELOPMENT_SECURITY_WORKFLOW_V1.md`

---

You are bootstrapping into an existing anoX Messenger V1 project. Do not write or modify code in this first pass. Return a read-only bootstrap audit.

Determine which mode applies:

- **LIVE SOURCE MODE:** You have access to a real `.git` repository (local clone or direct repo access).
- **SNAPSHOT MODE:** You only have an extracted `ANOX_HANDOFF_*.zip` package.

Report the mode you used and clearly distinguish `STATE VERIFIED AGAINST LIVE SOURCE` from
`STATE RECONSTRUCTED FROM SNAPSHOT`.

## Shared first steps (both modes)

1. Inventory all supplied anoX files.
2. Read the current authority in this order:
   - `docs/authority/AUTHORITY_INDEX.md`
   - `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md`
   - `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
   - `docs/authority/CLOUD_AI_SECRET_PROTECTION.md`
   - `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`
   - `docs/authority/B_FREEZE_REGISTRY.md`
   - `docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md`
   (The canonical precedence list is always `AUTHORITY_INDEX.md`. If another document appears to
   define a competing precedence, `AUTHORITY_INDEX.md` wins.)
3. Read the current state in this order:
   - `docs/continuity/CURRENT_HANDOFF.md`
   - `docs/continuity/CURRENT_GIT_STATE.md`
   - `docs/continuity/CURRENT_STATE.json`
   - `PROJECT_STATE.md`
   - `FORTSCHRITT.md`
   - `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
   - `GIT_SNAPSHOT.txt` (snapshot mode)

## LIVE SOURCE MODE additional steps

4. Inspect the actual repository and Git state:
   - `git remote -v`
   - `git branch --show-current`
   - `git rev-parse HEAD`
   - `git rev-parse main`  (or the configured baseline branch)
   - `git status --short`
   - `git tag --list`
   - `git log --oneline -n 15`
5. Compare the recorded `CURRENT_GIT_STATE.md` / `CURRENT_STATE.json` / `GIT_SNAPSHOT.txt` with the live Git state.
   - `CURRENT_STATE.baseline_head` must equal the real baseline branch HEAD.
   - `CURRENT_STATE.handoff_branch` must equal the current branch (or be reconciled).
   - `CURRENT_STATE.handoff_head` must equal the current HEAD.
   - Report any drift as `BLOCKED` unless an emergency/dirty handoff is explicitly declared.
6. Return `STATE VERIFIED AGAINST LIVE SOURCE`.

## SNAPSHOT MODE additional steps

4. Validate archive integrity:
   - `SHA256_MANIFEST.txt` must match the package files.
   - `MANIFEST.txt` must list all expected files.
   - `GIT_SNAPSHOT.txt` must be present.
5. Reconstruct state from the snapshot only. Do NOT run `git` commands.
6. Verify required authority and continuity files are present.
7. Return `STATE RECONSTRUCTED FROM SNAPSHOT` and note that `LIVE SOURCE RECONCILIATION` is required
   before any new product/governance write task.

## Shared verification

8. Verify the presence of:
   - `docs/authority/AUTHORITY_INDEX.md`
   - `docs/authority/CLOUD_AI_SECRET_PROTECTION.md`
   - `docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md`
   - `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
   - `docs/authority/B_FREEZE_REGISTRY.md`
   - `docs/authority/B025/`
   - `docs/continuity/`
   - `tools/continuity/generate_handoff.py`
   - `tools/continuity/validate_continuity.py`
   - `PROJECT_STATE.md`, `FORTSCHRITT.md`, `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
9. Verify the working tree is clean if in live mode and the handoff is not emergency/dirty.
10. Read the `README.md` for the high-level project description.
11. Distinguish target truth from implementation truth:
    - B-025 frozen architecture = what must be built
    - repository code and tests = what is actually implemented
12. Treat historical `docs/history/B025/` material as provenance only. Never reactivate superseded RAW rules. Never invent Raw1.0.
13. Do not modify source code, Gradle versions, NDK, or build configuration in this bootstrap pass.
14. Return a structured bootstrap report with:
    - A. MERGED BASELINE
    - B. CURRENT HANDOFF HEAD
    - C. WORKING TREE (or SNAPSHOT STATUS)
    - D. ARCHITECTURE AUTHORITY PRESENT
    - E. CONTINUITY FILES PRESENT
    - F. STATE MATCHES LIVE REPO (or `STATE RECONSTRUCTED FROM SNAPSHOT`)
    - G. SECURITY INVARIANTS CURRENT
    - H. NEXT GATE
    - I. RESULT: `PASS` or `BLOCKED`

    The report must also answer these required governance reconstruction questions:
    1. Is B-002 merged?
    2. Is B-003 merged?
    3. What is the current `main` baseline HEAD?
    4. What is the current handoff branch/HEAD?
    5. What comes next?
    6. What is S0–S4?
    7. Are per-PR Frontier audits mandatory during normal V1 development? (expected: NO)
    8. What happens to known HIGH/CRITICAL findings? (expected: IMMEDIATE MERGE BLOCKERS)
    9. What is the Cloud-AI secret invariant?
    10. Are production user private keys allowed in Cloud AI? (expected: NO)
    11. When does B-017-Lite occur? (expected: AFTER GOVERNANCE/HANDOFF HARDENING, BEFORE B-004/B-005)
    12. When does the full READ-ONLY AI audit occur? (expected: AFTER FUNCTIONAL V1)
    13. Is an external human audit still required? (expected: YES)
    14. Is `main` PR-only under the new governance? (expected: YES)
    15. Should model recommendations be embedded inside Devin prompts? (expected: NO)

End with exactly:

```
BOOTSTRAP RESULT: PASS — READY TO ACCEPT HANDOFF
```

or

```
BOOTSTRAP RESULT: BLOCKED — <reason>
```

Then stop. Do not start the next engineering task.
