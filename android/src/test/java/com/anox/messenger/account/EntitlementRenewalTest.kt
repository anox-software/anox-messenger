package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.Duration
import java.time.Instant

/** B-003 renewal calculation preview tests. */
class EntitlementRenewalTest {

    private val serverNow: Instant = Instant.parse("2026-08-22T00:00:00Z")

    @Test
    fun `active entitlement extends from existing expiry`() {
        val currentExpiry = Instant.parse("2026-09-01T00:00:00Z")
        val result = EntitlementRenewal.preview(
            currentState = EntitlementState.ACTIVE,
            currentExpiresAt = currentExpiry,
            serverNow = serverNow,
            duration = LicenseDuration.DAYS_30
        )
        assertTrue(result is RenewalPreview.NewExpiry)
        val expected = currentExpiry.plus(Duration.ofDays(30))
        assertEquals(expected, (result as RenewalPreview.NewExpiry).expiresAt)
    }

    @Test
    fun `active entitlement extension ignores server now`() {
        // Extension must be relative to the existing expiry, not to serverNow, even though
        // serverNow is earlier than the existing expiry in this scenario.
        val currentExpiry = Instant.parse("2026-12-25T00:00:00Z")
        val result = EntitlementRenewal.preview(
            EntitlementState.ACTIVE, currentExpiry, serverNow, LicenseDuration.DAYS_90
        ) as RenewalPreview.NewExpiry
        assertEquals(currentExpiry.plus(Duration.ofDays(90)), result.expiresAt)
    }

    @Test
    fun `expired entitlement restarts from server now`() {
        val result = EntitlementRenewal.preview(
            currentState = EntitlementState.EXPIRED,
            currentExpiresAt = Instant.parse("2020-01-01T00:00:00Z"), // long past, must be ignored
            serverNow = serverNow,
            duration = LicenseDuration.DAYS_180
        )
        assertTrue(result is RenewalPreview.NewExpiry)
        assertEquals(serverNow.plus(Duration.ofDays(180)), (result as RenewalPreview.NewExpiry).expiresAt)
    }

    @Test
    fun `expired entitlement renewal works even with null previous expiry`() {
        val result = EntitlementRenewal.preview(
            EntitlementState.EXPIRED, null, serverNow, LicenseDuration.DAYS_30
        )
        assertTrue(result is RenewalPreview.NewExpiry)
    }

    @Test
    fun `revoked entitlement is not renewable`() {
        val result = EntitlementRenewal.preview(
            EntitlementState.REVOKED, null, serverNow, LicenseDuration.DAYS_30
        )
        assertTrue(result is RenewalPreview.NotRenewable)
    }

    @Test
    fun `active entitlement without known expiry is not renewable`() {
        val result = EntitlementRenewal.preview(
            EntitlementState.ACTIVE, null, serverNow, LicenseDuration.DAYS_30
        )
        assertTrue(result is RenewalPreview.NotRenewable)
    }

    @Test
    fun `all three frozen durations are usable in renewal`() {
        for (duration in LicenseDuration.entries) {
            val result = EntitlementRenewal.preview(
                EntitlementState.EXPIRED, null, serverNow, duration
            )
            assertTrue(result is RenewalPreview.NewExpiry)
            assertEquals(
                serverNow.plus(Duration.ofDays(duration.days)),
                (result as RenewalPreview.NewExpiry).expiresAt
            )
        }
    }
}
