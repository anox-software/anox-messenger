# Devin Final Output Contract

**Authority:** B-026 + `DEVELOPMENT_SECURITY_WORKFLOW_V1.md`
**Applies to:** every future Devin implementation task

Every Devin task must end with the following sections, in order, and exactly one of the two final result lines.

---

## Required sections

A. TASK — task ID and short purpose
B. BASELINE — repository, branch, HEAD, and authority used
C. BRANCH — branch worked on
D. FILES CHANGED — key files changed
E. IMPLEMENTATION — what was done
F. TESTS ACTUALLY RUN — tests executed, with results
G. TESTS NOT RUN / UNVERIFIED — tests not executed, with reason
H. SECURITY INVARIANTS — whether any invariant was affected or violated
I. PROJECT_STATE UPDATE — whether `PROJECT_STATE.md` was updated
J. FORTSCHRITT UPDATE — whether `FORTSCHRITT.md` was updated
K. DEVIN ARCHIVE UPDATE — whether `DEVIN_PROMPT_OUTPUT_ARCHIV.md` was updated
L. COMMITS — commit SHAs and messages
M. PR — PR number and URL, merge status
N. CI — CI run ID(s) and results
O. BLOCKERS — active blockers or `NONE`
P. ARCHITECTURE IMPACT — whether architecture changed and how
Q. SECURITY CLASS — `S0` / `S1` / `S2` / `S3` / `S4`
R. CLOUD-AI SECRET STATUS — `NO CONFIRMED CLOUD-AI SECRET EXPOSURE` or blocker
S. IMPLEMENTATION / VERIFIED / PARTIAL / MISSING / UNVERIFIED — explicit status for each changed area
T. NEXT RECOMMENDED GATE — the next authorized gate (not an automatic feature start)

---

## Final result line

Exactly one of:

```
RESULT: PASS — READY FOR ARCHITECT REVIEW
```

or

```
RESULT: BLOCKED — ARCHITECT DECISION REQUIRED
```

---

## Clarifications

- Do not include a model recommendation field.
- `SECURITY CLASS` must be chosen from S0–S4 for the most sensitive part of the task.
- `CLOUD-AI SECRET STATUS` is mandatory for every security-relevant task.
- Distinguish `IMPLEMENTED` from `VERIFIED` from `UNVERIFIED`; do not conflate them.
