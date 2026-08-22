# CURRENT OPEN WORK

**Date:** 2026-08-21

---

## ARCHITECTURE OPEN

None. B-024 closed the last known architecture-open items. B-025 is frozen. B-026 is frozen.

## IN REVIEW

- `PROMPT-007` — B-002 Device Authentication client foundation on
  `feature/b002-device-auth-foundation`, PR #4 open and unmerged, awaiting architect review.

## IMPLEMENTATION MISSING

All B-003…B-020 product features are not implemented. B-002 has a client foundation in review
but no backend, registration binding or entitlement enforcement. See
`CURRENT_IMPLEMENTATION_STATE.md` and `docs/authority/B025/IMPLEMENTATION_GAP_MATRIX.md`.

## VERIFICATION MISSING

- GrapheneOS physical-device tests
- D2D transfer runtime verification
- Connected Android instrumentation in CI
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
