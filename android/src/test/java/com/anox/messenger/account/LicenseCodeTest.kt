package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** B-003 license code structural validation and secret-safety tests. */
class LicenseCodeTest {

    @Test
    fun `well formed code is accepted`() {
        val code = LicenseCode.parse("anox-AB12-CD34-EF56")
        assertNotNull(code)
        assertEquals("anox-AB12-CD34-EF56", code!!.value)
    }

    @Test
    fun `lowercase groups are rejected`() {
        assertNull(LicenseCode.parse("anox-ab12-cd34-ef56"))
    }

    @Test
    fun `wrong prefix is rejected`() {
        assertNull(LicenseCode.parse("anoxx-AB12-CD34-EF56"))
        assertNull(LicenseCode.parse("axon-AB12-CD34-EF56"))
    }

    @Test
    fun `malformed separators are rejected`() {
        assertNull(LicenseCode.parse("anox_AB12_CD34_EF56"))
        assertNull(LicenseCode.parse("anoxAB12CD34EF56"))
        assertNull(LicenseCode.parse("anox-AB12CD34EF56"))
    }

    @Test
    fun `wrong group length is rejected`() {
        assertNull(LicenseCode.parse("anox-AB1-CD34-EF56"))
        assertNull(LicenseCode.parse("anox-AB123-CD34-EF56"))
    }

    @Test
    fun `wrong group count is rejected`() {
        assertNull(LicenseCode.parse("anox-AB12-CD34"))
        assertNull(LicenseCode.parse("anox-AB12-CD34-EF56-GH78"))
    }

    @Test
    fun `empty string is rejected`() {
        assertNull(LicenseCode.parse(""))
    }

    @Test
    fun `toString never discloses the plaintext value`() {
        val code = LicenseCode.parse("anox-AB12-CD34-EF56")!!
        assertFalse(code.toString().contains("AB12"))
        assertFalse(code.toString().contains("CD34"))
        assertFalse(code.toString().contains("EF56"))
    }

    @Test
    fun `equal codes compare equal despite masked toString`() {
        val a = LicenseCode.parse("anox-AB12-CD34-EF56")!!
        val b = LicenseCode.parse("anox-AB12-CD34-EF56")!!
        assertTrue(a == b)
        assertEquals(a.hashCode(), b.hashCode())
    }

    @Test
    fun `client never generates a license code`() {
        // There is no factory method on LicenseCode other than parse(); this test documents
        // and locks in that license generation is a server responsibility (B-003).
        val members = LicenseCode.Companion::class.java.declaredMethods.map { it.name }
        assertTrue(members.contains("parse"))
        assertFalse(members.any { it.contains("generate", ignoreCase = true) })
        assertFalse(members.any { it.contains("create", ignoreCase = true) })
    }
}
