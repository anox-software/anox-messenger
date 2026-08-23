package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** B-003 username syntax validation tests. */
class UsernameTest {

    private fun reasonOf(raw: String): UsernameInvalidReason {
        val result = Username.validate(raw)
        assertTrue("expected $raw to be invalid but was valid", result is UsernameValidation.Invalid)
        return (result as UsernameValidation.Invalid).reason
    }

    @Test
    fun `minimum length is accepted`() {
        val result = Username.validate("abc")
        assertTrue(result.isValid)
        assertEquals("abc", (result as UsernameValidation.Valid).username.value)
    }

    @Test
    fun `maximum length is accepted`() {
        val raw = "a".repeat(32)
        val result = Username.validate(raw)
        assertTrue(result.isValid)
    }

    @Test
    fun `digits underscore and dot are accepted`() {
        assertTrue(Username.validate("a1_2.3").isValid)
    }

    @Test
    fun `too short is rejected`() {
        assertEquals(UsernameInvalidReason.TOO_SHORT, reasonOf("ab"))
    }

    @Test
    fun `empty is rejected as too short`() {
        assertEquals(UsernameInvalidReason.TOO_SHORT, reasonOf(""))
    }

    @Test
    fun `one below minimum length is rejected`() {
        assertEquals(UsernameInvalidReason.TOO_SHORT, reasonOf("ab"))
    }

    @Test
    fun `too long is rejected`() {
        assertEquals(UsernameInvalidReason.TOO_LONG, reasonOf("a".repeat(33)))
    }

    @Test
    fun `uppercase is rejected`() {
        assertEquals(UsernameInvalidReason.INVALID_CHARACTERS, reasonOf("Alice"))
    }

    @Test
    fun `uppercase is not silently lowercased`() {
        // The proposed username must be rejected outright, not normalised to "alice".
        val result = Username.validate("Alice")
        assertTrue(result is UsernameValidation.Invalid)
    }

    @Test
    fun `non ascii is rejected`() {
        assertEquals(UsernameInvalidReason.INVALID_CHARACTERS, reasonOf("caf\u00e9user"))
    }

    @Test
    fun `punctuation is rejected`() {
        assertEquals(UsernameInvalidReason.INVALID_CHARACTERS, reasonOf("alice!"))
        assertEquals(UsernameInvalidReason.INVALID_CHARACTERS, reasonOf("alice bob"))
        assertEquals(UsernameInvalidReason.INVALID_CHARACTERS, reasonOf("alice@bob"))
        assertEquals(UsernameInvalidReason.INVALID_CHARACTERS, reasonOf("alice-bob"))
    }

    @Test
    fun `hyphen is rejected`() {
        assertEquals(UsernameInvalidReason.INVALID_CHARACTERS, reasonOf("al-ice"))
    }
}
