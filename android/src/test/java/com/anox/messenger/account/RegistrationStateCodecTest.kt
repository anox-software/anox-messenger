package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.Instant
import java.util.UUID

/**
 * Tests the dependency-free text codec used by [FileRegistrationSessionStore], independent of
 * the Android file I/O it wraps.
 */
class RegistrationStateCodecTest {

    private val username = (Username.validate("alice") as UsernameValidation.Valid).username
    private val registrationId = RegistrationId.parse(UUID.randomUUID().toString())!!
    private val grant = RegistrationGrant("grant-value-abc", Instant.parse("2026-08-22T00:30:00Z"))

    private fun roundTrip(state: RegistrationState): RegistrationState? =
        RegistrationStateCodec.decode(RegistrationStateCodec.encode(state))

    @Test
    fun `not started round trips`() {
        assertEquals(RegistrationState.NotStarted, roundTrip(RegistrationState.NotStarted))
    }

    @Test
    fun `reserved round trips`() {
        val state = RegistrationState.Reserved(registrationId, grant, username)
        assertEquals(state, roundTrip(state))
    }

    @Test
    fun `device auth registered round trips`() {
        val state = RegistrationState.DeviceAuthRegistered(registrationId, grant, username, "jkt-value")
        assertEquals(state, roundTrip(state))
    }

    @Test
    fun `public identity uploaded round trips`() {
        val state = RegistrationState.PublicIdentityUploaded(registrationId, grant, username, "jkt-value")
        assertEquals(state, roundTrip(state))
    }

    @Test
    fun `committed round trips`() {
        val state = RegistrationState.Committed(
            AccountId.parse(UUID.randomUUID().toString())!!,
            DeviceId.parse(UUID.randomUUID().toString())!!,
            username
        )
        assertEquals(state, roundTrip(state))
    }

    @Test
    fun `expired round trips`() {
        val state = RegistrationState.Expired(registrationId)
        assertEquals(state, roundTrip(state))
    }

    @Test
    fun `failed round trips`() {
        val state = RegistrationState.Failed("some safe diagnostic reason")
        assertEquals(state, roundTrip(state))
    }

    @Test
    fun `garbage content decodes to null`() {
        assertNull(RegistrationStateCodec.decode("not a real state file\nwith random content"))
        assertNull(RegistrationStateCodec.decode(""))
        assertNull(RegistrationStateCodec.decode("RESERVED\nmissingFields=true"))
    }

    @Test
    fun `truncated reserved record decodes to null rather than partial state`() {
        val truncated = "RESERVED\nregistrationId=${registrationId.value}\n"
        assertNull(RegistrationStateCodec.decode(truncated))
    }
}
