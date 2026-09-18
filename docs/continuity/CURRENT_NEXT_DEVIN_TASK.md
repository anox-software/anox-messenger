# CURRENT_NEXT_DEVIN_TASK — anoX V1

**Event:** `ANOX-EVENT-0055`

`TARGETED-INDEPENDENT-INTEGRATION-RETEST-S1-001` — fresh independent session (not the implementer) retests the remediated S1 surfaces on the head of `integration/s1-after-s0-001` (S1 substantive `ea20aaaf330c` + Human-authorized correction pair `a79e3b3db9b4` + metadata from `REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001`): F-1…F-9 dispositions, S1-era central-validator extension (accept-only-ANOX-EVENT-0055; registry 13→14), the completed two-file ratification package (`e52f626a46f2…` + `c305c21c9405…`, 277/277 post-application), the B-1 S0-validator ownership deviation (still unresolved — requires explicit Human disposition), the corrected Git-worktree fail-closed S0 scope gate, escaped-PEM and consumer soft-fail detection, S0 invariants (contract freeze, evidence preservation, CI hotfix), real clean build + `rebuild-compare` attestation, and — where an emulator is available — instrumented runs on both ABIs bound to the manifest (x86_64 runtime evidence is still PENDING). Then a single Human decision (B-1 disposition + shared-validator ratification) → human push → PR → normal merge into `main`. FCP-7: the implementer of this task cannot self-certify `INDEPENDENTLY_RETESTED`.

Preserved sequencing: … → `REMEDIATION_SESSION_S0` (**merged to main**) ∥ `REMEDIATION_SESSION_S1` (**integrated on main lineage + retest findings remediated — pending targeted independent integration retest and human merge**) → `S2 ∥ S3` → `S4` → native retest acceptance (037) → Pre-B004 DoD → B004 (S5) …

Do not start B-004/B-005, product code changes, the physical campaign (`PHYSICAL_P1..P17`), S2/S3/S4 or any other remediation session without a new authorized task and the required predecessor gates.
