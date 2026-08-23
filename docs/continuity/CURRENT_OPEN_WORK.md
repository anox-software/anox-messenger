# CURRENT OPEN WORK

**Date:** 2026-08-23 (post PROMPT-008 merge)

---

## ARCHITECTURE OPEN

None. B-024 closed the last known architecture-open items. B-025 is frozen. B-026 is frozen.

## RECENTLY MERGED

- `PROMPT-007` — B-002 Device Authentication client foundation. Merged into `main` at
  `d281df66a3471dfd6a9bab0bd899be701317afb4` (PR #4) after independent security/architecture
  review (APPROVE, no merge-blocking findings) and empirical dependency-tree verification.
- `PROMPT-008` / `PROMPT-008C` / `PROMPT-008D` — B-003 Account/License client domain/state
  foundation, security review remediation, and final commit-uncertainty closure. Merged into
  `main` at `e7ee54a713e08950c63cf2d61ec97931864b66bc` (PR #5).

## IN MERGE GATE

None. Next gate: `DEVELOPMENT SECURITY GOVERNANCE / HANDOFF HARDENING`.

## IMPLEMENTATION MISSING

All B-004…B-020 product features are not implemented. B-002 and B-003 client foundations are
merged, but no backend, license generation, or DB enforcement exists yet. See
`CURRENT_IMPLEMENTATION_STATE.md` and `docs/authority/B025/IMPLEMENTATION_GAP_MATRIX.md`.

## VERIFICATION MISSING

- GrapheneOS physical-device tests
- D2D transfer runtime verification
- Connected Android instrumentation in CI (run and passing on a local emulator during
  PROMPT-008, 58/58, but CI itself still has no emulator)
- Physical StrongBox/TEE Device Auth key behaviour
- Independent security audit (B-022)
- Release DoD (B-023)

## RELEASE BLOCKERS

None yet. V1 release is gated by B-021…B-023, all future release gates.

## FUTURE / OUT OF V1

- Multi-device
- Account recovery
- Group messaging
- Calls
- Web/desktop clients
