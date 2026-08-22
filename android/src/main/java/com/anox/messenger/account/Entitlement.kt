package com.anox.messenger.account

import java.time.Instant

/**
 * A server-reported entitlement snapshot.
 *
 * Both [state] and [expiresAt] are values the server returned; the client never computes them
 * independently, and in particular never treats the local device clock as authoritative for
 * expiry (see [EntitlementRenewal]).
 */
data class Entitlement(
    val state: EntitlementState,
    val expiresAt: Instant
)
