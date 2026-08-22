# CURRENT OPEN WORK

**Date:** 2026-08-22

---

## ARCHITECTURE OPEN

None. B-024 closed the last known architecture-open items. B-025 is frozen. B-026 is frozen.

## RECENTLY MERGED

- `PROMPT-007` — B-002 Device Authentication client foundation. Merged into `main` at
  `d281df66a3471dfd6a9bab0bd899be701317afb4` (PR #4) after independent security/architecture
  review (APPROVE, no merge-blocking findings) and empirical dependency-tree verification.

## IN REVIEW

- `PROMPT-008` — B-003 Account/License client domain/state foundation on
  `feature/b003-account-license-foundation`, PR `#5` open against `main`, awaiting architect
  review.

## IMPLEMENTATION MISSING

All B-004…B-020 product features are not implemented. B-002 has a merged client foundation and
B-003 has a client domain/state foundation in review, but no backend, license generation, or DB
enforcement exists yet. See `CURRENT_IMPLEMENTATION_STATE.md` and
`docs/authority/B025/IMPLEMENTATION_GAP_MATRIX.md`.

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
