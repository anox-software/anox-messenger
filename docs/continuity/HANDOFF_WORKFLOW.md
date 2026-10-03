# Handoff Workflow

**Authority:** B-026

## Live continuity and on-demand export

Apply the canonical [ON-DEMAND HANDOFF GENERATION](../authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md#on-demand-handoff-generation) and [MERGE-SAFE DELIVERY FINALIZATION INVARIANT](../authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md#merge-safe-delivery-finalization-invariant). `CURRENT_HANDOFF.md` is live continuity, not a generated package. Keep live state current when it changes. Default: `HANDOFF_REQUESTED = NO`, `HANDOFF_PACKAGE_GENERATION = NOT_EXECUTED`; normal development and repository bootstrap need no ZIP.

## Human-requested handoff lifecycle

1. Human explicitly requests `GENERATE CURRENT HANDOFF` or `GENERATE FINAL HANDOFF` (for example, when Chat A becomes slow or context too large).
2. Finish the current Devin task cleanly.
3. Ensure the working tree is clean and the state is documented.
4. Update current-state surfaces:
   - `PROJECT_STATE.md`
   - `FORTSCHRITT.md`
   - `DEVIN_PROMPT_OUTPUT_ARCHIV.md`
   - `docs/continuity/CURRENT_HANDOFF.md`
   - `docs/continuity/CURRENT_GIT_STATE.md`
   - `docs/continuity/CURRENT_IMPLEMENTATION_STATE.md`
   - `docs/continuity/CURRENT_OPEN_WORK.md`
   - `docs/continuity/CURRENT_NEXT_DEVIN_TASK.md`
   - `docs/continuity/CURRENT_STATE.json`
5. Run live repository validation:
   ```bash
   python3 tools/continuity/validate_continuity.py --mode live
   ```
   This mode requires `.git` and validates live Git state as well as current-state consistency.
6. Generate a handoff package:
   ```bash
   python3 tools/continuity/generate_handoff.py
   ```
7. Extract the generated ZIP into a clean temporary directory and run archive validation:
   ```bash
   python3 tools/continuity/validate_continuity.py --mode archive --archive <extracted-dir>
   ```
   This mode validates package integrity and recorded state without `.git`.
   A package is not fully validated until both live and archive modes PASS.
8. Upload `artifacts/handoff/ANOX_HANDOFF_*.zip` or provide direct repository access.
9. The new AI runs the bootstrap from `docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md`,
   choosing either `LIVE SOURCE MODE` or `SNAPSHOT MODE`.
10. On `PASS`, perform handoff acceptance review.
11. Chat A becomes archive; development continues only in Chat B.

## Emergency handoff

If a chat must be abandoned mid-task, the handoff package must be labeled `EMERGENCY / DIRTY HANDOFF`
and list all uncommitted and partial changes. The new AI must resolve the dirty state before
continuing. Live-source reconciliation is required before new write work.

## Unsealed handoff packages (declared exception)

**Authority:** `ANOX-DECISION-HANDOFF-UNSEALED-EXCEPTION-001` (Human Owner, 2026-10-03).

By default `generate_handoff.py` fails closed when the repository-described
`described_head` is not anchored to the last sealed ledger event — archive
validation reports `FAIL — AUTHORED MATERIAL CHECKPOINT WITHOUT LEDGER EVENT`.
Sealing the checkpoint via `seal_event.py --seal` (separate human decision)
remains the recommended path for canonical anchors.

When a package is needed before sealing, an operator may pass:

```bash
python3 tools/continuity/generate_handoff.py --allow-unsealed
```

Semantics:

- Without `--allow-unsealed`, behavior is unchanged: unsealed state fails, the
  manifest carries no seal fields, and no other check is weakened.
- With the flag on an unsealed state, generation proceeds and `MANIFEST.txt`
  is stamped with three explicit comment fields:
  - `# SEAL_STATUS: UNSEALED_AT_GENERATION`
  - `# SEAL_DESCRIBED_HEAD: <described_head at generation>`
  - `# SEAL_LAST_SEALED: <last sealed ledger event head at generation>`
- On a sealed state the flag is a no-op: no stamp is written and the manifest
  is byte-identical to a run without the flag.
- Archive-mode validation reads the stamp: a declared package whose stamped
  values exactly match the packaged `CURRENT_STATE.json` `described_head` and
  the packaged ledger tail is reported as
  `PASS — DECLARED_UNSEALED` (`HANDOFF_ARCHIVE_VALIDATION: PASS`).
- A stamp that is missing required fields, mismatches the packaged state or
  ledger tail, uses an unknown `SEAL_STATUS` value, or appears on a package
  that is actually sealed fails closed as tamper. An undeclared unsealed
  package fails exactly as before.

Consumer duties are unchanged and explicitly include:

- An unsealed package must never be treated as sealed: the declaration records
  that `described_head` had **no** ledger event at generation time.
- `HANDOFF SNAPSHOT != LIVE SOURCE` still applies in full; live-source
  reconciliation is mandatory before any write work.
- No ledger/seal semantics change; no other continuity, security, placeholder,
  manifest, or surface check is weakened by the exception.

## HANDOFF SNAPSHOT INVARIANT

`HANDOFF SNAPSHOT != LIVE SOURCE`

A valid handoff proves the integrity and internal consistency of the generated snapshot. It does
not prove that the live repository has not changed since handoff generation. Archive-only bootstrap
may reconstruct state. Before new productive write work, live-source reconciliation is required
whenever live Git becomes available.

## Remote-write authority

Every handoff must preserve `docs/authority/GITHUB_REMOTE_ACTIVITY_SAFETY.md`. Remote write is not
assumed. A new AI session must not push, create remote PRs, poll GitHub, or manage credentials unless
explicit authority is present. In the initial post-migration mode, remote synchronization is
human-controlled.

## Continuity-sync runs

A narrowly scoped run whose sole purpose is archive/continuity synchronization does not require a
follow-on run to archive the current run. Its provenance is the resulting Git commit, the updated
`DEVIN_PROMPT_OUTPUT_ARCHIV.md` record of the prior substantive task, and the updated `CURRENT_*`,
`PROJECT_STATE.md`, and `FORTSCHRITT.md` surfaces. Substantive Devin tasks must still be archived in
`DEVIN_PROMPT_OUTPUT_ARCHIV.md` as completed historical records.

## HEAD semantics

Tracked continuity state stores `described_head`: the substantive Git commit the
metadata describes. `live_head` is always `git rev-parse HEAD` and is not stored
as authoritative truth. A generated Handoff ZIP records `handoff_snapshot_head`
in its external manifest.

A `described_head` that is an ancestor of `live_head` is valid only when every
intermediate change is on the explicit metadata-only allowlist (e.g.,
`CURRENT_*.md`, `PROJECT_STATE.md`, `FORTSCHRITT.md`). Any product, CI,
authority, or tool/validator change requires a new substantive commit and a new
`described_head`.
