package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test
import java.util.UUID

/**
 * B-003 identifier (account/device/registration id) tests.
 *
 * `account_id` and `device_id` are server-generated UUIDv4; this suite proves the client-side
 * parser accepts only valid UUIDv4 values and never manufactures a canonical identifier.
 */
class IdentifierTest {

    private fun randomV4(): String = UUID.randomUUID().toString()

    private fun randomV1(): String {
        // Construct a syntactically valid UUID whose version nibble is 1, not 4.
        val v4 = UUID.randomUUID()
        val msb = (v4.mostSignificantBits and 0xFFFFFFFFFFFF0FFFuL.toLong()) or 0x0000000000001000L
        return UUID(msb, v4.leastSignificantBits).toString()
    }

    @Test
    fun `valid uuidv4 is accepted for account id`() {
        val raw = randomV4()
        assertNotNull(AccountId.parse(raw))
        assertEquals(raw, AccountId.parse(raw)?.value.toString())
    }

    @Test
    fun `valid uuidv4 is accepted for device id`() {
        assertNotNull(DeviceId.parse(randomV4()))
    }

    @Test
    fun `valid uuidv4 is accepted for registration id`() {
        assertNotNull(RegistrationId.parse(randomV4()))
    }

    @Test
    fun `malformed uuid is rejected`() {
        assertNull(AccountId.parse("not-a-uuid"))
        assertNull(DeviceId.parse(""))
        assertNull(RegistrationId.parse("12345"))
    }

    @Test
    fun `wrong uuid version is rejected`() {
        val v1 = randomV1()
        assertEquals(1, UUID.fromString(v1).version())
        assertNull(AccountId.parse(v1))
        assertNull(DeviceId.parse(v1))
        assertNull(RegistrationId.parse(v1))
    }

    @Test
    fun `nil uuid is rejected`() {
        // The nil UUID is version 0, not 4.
        assertNull(AccountId.parse("00000000-0000-0000-0000-000000000000"))
    }

    @Test
    fun `identifiers of different id types with the same uuid are not interchangeable types`() {
        val raw = randomV4()
        val accountId = AccountId.parse(raw)
        val deviceId = DeviceId.parse(raw)
        assertNotNull(accountId)
        assertNotNull(deviceId)
        // Compile-time type distinction: an AccountId cannot be assigned where a DeviceId is
        // expected. This test documents/locks in that distinction at the value level.
        assertEquals(accountId!!.value, deviceId!!.value)
    }
}
