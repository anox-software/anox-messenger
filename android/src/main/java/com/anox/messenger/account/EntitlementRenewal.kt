package com.anox.messenger.account

import java.time.Instant

/**
 * Non-authoritative preview of the frozen B-003 renewal calculation.
 *
 * B-003 (FROZEN v1.4):
 *  - if the entitlement is currently ACTIVE, the new expiry extends from the *existing* expiry;
 *  - if the entitlement is EXPIRED, the new expiry starts from the *current authoritative
 *    server time*.
 *  - renewal preserves the Device Auth identity, E2EE identity, `account_id` and `device_id`;
 *    it is never identity rotation.
 *
 * This object exists only to let the client preview what a renewal would produce, for example
 * to render an estimated new expiry in the UI before the request is sent. It is explicitly
 * NOT authoritative: the server computes and returns the real new expiry at renewal time.
 *
 * Both [currentExpiresAt] (when the entitlement is active) and [serverNow] MUST be values
 * obtained from the server, never `Instant.now()` / the local device clock. There is no
 * parameterless overload of [preview] specifically to make it hard to accidentally pass the
 * local clock here.
 */
object EntitlementRenewal {

    /**
     * Computes the previewed new expiry.
     *
     * @param currentState the entitlement's current, server-reported state.
     * @param currentExpiresAt the entitlement's current, server-reported expiry. Required when
     *   [currentState] is [EntitlementState.ACTIVE].
     * @param serverNow the current time as reported by the server (or another authoritative
     *   time source); never the local device clock.
     * @param duration the standard renewal duration being purchased/applied.
     */
    fun preview(
        currentState: EntitlementState,
        currentExpiresAt: Instant?,
        serverNow: Instant,
        duration: LicenseDuration
    ): RenewalPreview = when (currentState) {
        EntitlementState.ACTIVE -> {
            val base = currentExpiresAt
                ?: return RenewalPreview.NotRenewable(
                    "ACTIVE entitlement requires a known current expiry"
                )
            RenewalPreview.NewExpiry(base.plus(java.time.Duration.ofDays(duration.days)))
        }
        EntitlementState.EXPIRED ->
            RenewalPreview.NewExpiry(serverNow.plus(java.time.Duration.ofDays(duration.days)))
        EntitlementState.REVOKED ->
            RenewalPreview.NotRenewable("REVOKED entitlement is not renewable")
    }
}

/** Outcome of [EntitlementRenewal.preview]. */
sealed class RenewalPreview {
    data class NewExpiry(val expiresAt: Instant) : RenewalPreview()
    data class NotRenewable(val reason: String) : RenewalPreview()
}
