# Devin Final Output Contract

**Authority:** B-026
**Applies to:** every future Devin implementation task

Every Devin task must end with the following sections, in order, and exactly one of the two final result lines.

In addition, every future completed **material** Devin task must report: event materiality classification (T0/T1/T2/T3), proposed/recorded Event ID, substantive checkpoint SHA, test summary, finding delta, gate delta, memory surfaces updated, and `PROJECT_MEMORY_FRESHNESS` result.

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

## Security subfields (required inside the sections above)

Every S2–S4 task (and any task touching secrets, keys, identity, authentication, authorization,
E2EE, cryptographic state, or supply-chain security) must also report:

- `SECURITY CLASS: S0 / S1 / S2 / S3 / S4` — normally reported within section P or as a subfield of C/H.
- `CLOUD-AI SECRET STATUS: NO CONFIRMED CLOUD-AI SECRET EXPOSURE` or the blocking status.

For every security-relevant implementation area, sections E and P must distinguish:

- `IMPLEMENTED`
- `VERIFIED`
- `PARTIAL`
- `MISSING`
- `UNVERIFIED`

Do not conflate these.

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
- S0–S4 is the sole security-classification system.
- `CLOUD-AI SECRET STATUS` is mandatory for every security-relevant task.
- Distinguish `IMPLEMENTED` from `VERIFIED` from `UNVERIFIED`; do not conflate them.
