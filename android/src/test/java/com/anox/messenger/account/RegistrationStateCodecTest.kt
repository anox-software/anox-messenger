package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.Instant
import java.util.UUID

/**
 * Tests the versioned length-prefixed binary codec used by [FileRegistrationSessionStore],
 * independent of the Android file I/O and Keystore encryption it wraps.
 */
class RegistrationStateCodecTest {

    private val username = (Username.validate("alice") as UsernameValidation.Valid).username
    private val registrationId = RegistrationId.parse(UUID.randomUUID().toString())!!
    private val grant = RegistrationGrant("grant-value-abc", Instant.parse("2026-08-22T00:30:00Z"))

    private fun roundTrip(state: RegistrationState): RegistrationState? =
        BinaryRegistrationStateCodec.decode(BinaryRegistrationStateCodec.encode(state))

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
    fun `commit armed round trips`() {
        val state = RegistrationState.CommitArmed(registrationId, grant, username, "jkt-value")
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
    fun `arbitrary reason text cannot inject fields`() {
        val reason = "line1\nline2\r\n=foo\u0000bar\uD83D\uDE00"
        val state = RegistrationState.Failed(reason)
        assertEquals(state, roundTrip(state))
    }

    @Test
    fun `garbage content decodes to null`() {
        assertNull(BinaryRegistrationStateCodec.decode(byteArrayOf(0xFF.toByte(), 0x00, 0x01)))
        assertNull(BinaryRegistrationStateCodec.decode(byteArrayOf()))
        assertNull(BinaryRegistrationStateCodec.decode(byteArrayOf(BinaryRegistrationStateCodec.VERSION, 0x42)))
    }

    @Test
    fun `truncated reserved record decodes to null rather than partial state`() {
        val truncated = BinaryRegistrationStateCodec.encode(
            RegistrationState.Reserved(registrationId, grant, username)
        ).copyOfRange(0, 20)
        assertNull(BinaryRegistrationStateCodec.decode(truncated))
    }

    @Test
    fun `codec version is fixed`() {
        val encoded = BinaryRegistrationStateCodec.encode(RegistrationState.NotStarted)
        assertEquals(BinaryRegistrationStateCodec.VERSION, encoded[0])
    }
}
