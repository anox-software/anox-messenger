# Devin Final Output Contract

**Authority:** B-026  
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
Q. NEXT RECOMMENDED GATE — the next authorized gate (not an automatic feature start)

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
