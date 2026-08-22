package com.anox.messenger.account

/**
 * Frozen B-003 entitlement states. Server-authoritative; the client never derives this locally.
 *
 * Entitlement expiry controls service access only. It never deletes the Device Auth key, the
 * E2EE identity, E2EE sessions/state or local encrypted history (Security Invariant 9).
 */
enum class EntitlementState {
    ACTIVE,
    EXPIRED,
    REVOKED
}
