package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Test

/** Proves only the frozen B-003 states exist for account, device and entitlement. */
class AccountDeviceEntitlementStateTest {

    @Test
    fun `account states are exactly the frozen set`() {
        assertEquals(
            setOf("ACTIVE", "SUSPENDED", "REVOKED", "DELETED"),
            AccountState.entries.map { it.name }.toSet()
        )
    }

    @Test
    fun `device states are exactly the frozen set`() {
        assertEquals(
            setOf("ACTIVE", "REVOKED"),
            DeviceState.entries.map { it.name }.toSet()
        )
    }

    @Test
    fun `entitlement states are exactly the frozen set`() {
        assertEquals(
            setOf("ACTIVE", "EXPIRED", "REVOKED"),
            EntitlementState.entries.map { it.name }.toSet()
        )
    }
}
