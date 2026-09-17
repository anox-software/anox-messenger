# CURRENT_NEXT_DEVIN_TASK — anoX V1

**Event:** `ANOX-EVENT-0055`

`TARGETED-INDEPENDENT-INTEGRATION-RETEST-S1-001` — fresh independent session (not the implementer) retests the remediated S1 surfaces on the head of `integration/s1-after-s0-001` (substantive `ea20aaaf330c`): F-1…F-9 dispositions, S1-era central-validator extension (accept-only-ANOX-EVENT-0055; registry 13→14), S0 invariants (contract freeze, evidence preservation, CI hotfix), real clean build + `rebuild-compare` attestation, and — where an emulator is available — instrumented runs on both ABIs bound to the manifest (x86_64 runtime evidence is still PENDING). Then human push → PR → normal merge into `main`. FCP-7: the implementer of this task cannot self-certify `INDEPENDENTLY_RETESTED`.

Preserved sequencing: … → `REMEDIATION_SESSION_S0` (**merged to main**) ∥ `REMEDIATION_SESSION_S1` (**integrated on main lineage + retest findings remediated — pending targeted independent integration retest and human merge**) → `S2 ∥ S3` → `S4` → native retest acceptance (037) → Pre-B004 DoD → B004 (S5) …

Do not start B-004/B-005, product code changes, the physical campaign (`PHYSICAL_P1..P17`), S2/S3/S4 or any other remediation session without a new authorized task and the required predecessor gates.
