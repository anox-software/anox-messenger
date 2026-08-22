package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.Instant

/** B-003 registration grant contract and secret-safety tests. */
class RegistrationGrantTest {

    @Test
    fun `frozen contract constants`() {
        assertEquals(256, RegistrationGrant.ENTROPY_BITS)
        assertEquals(32, RegistrationGrant.ENTROPY_BYTES)
        assertEquals(30L, RegistrationGrant.TTL_MINUTES)
    }

    @Test
    fun `generated grant expires exactly 30 minutes after issuance`() {
        val issuedAt = Instant.parse("2026-08-22T00:00:00Z")
        val grant = RegistrationGrantGenerator().newGrant(issuedAt)
        assertEquals(issuedAt.plusSeconds(30 * 60), grant.expiresAt)
    }

    @Test
    fun `grant is not expired before its ttl`() {
        val issuedAt = Instant.parse("2026-08-22T00:00:00Z")
        val grant = RegistrationGrantGenerator().newGrant(issuedAt)
        assertFalse(grant.isExpired(issuedAt.plusSeconds(29 * 60)))
    }

    @Test
    fun `grant is expired at and after its ttl`() {
        val issuedAt = Instant.parse("2026-08-22T00:00:00Z")
        val grant = RegistrationGrantGenerator().newGrant(issuedAt)
        assertTrue(grant.isExpired(issuedAt.plusSeconds(30 * 60)))
        assertTrue(grant.isExpired(issuedAt.plusSeconds(31 * 60)))
    }

    @Test
    fun `generated grants are unique`() {
        val generator = RegistrationGrantGenerator()
        val now = Instant.now()
        val grants = (1..50).map { generator.newGrant(now).value }
        assertEquals(grants.size, grants.toSet().size)
    }

    @Test
    fun `toString never discloses the grant value`() {
        val grant = RegistrationGrantGenerator().newGrant(Instant.now())
        assertFalse(grant.toString().contains(grant.value))
    }

    @Test
    fun `different grants are not equal`() {
        val generator = RegistrationGrantGenerator()
        val now = Instant.now()
        assertNotEquals(generator.newGrant(now), generator.newGrant(now))
    }
}
