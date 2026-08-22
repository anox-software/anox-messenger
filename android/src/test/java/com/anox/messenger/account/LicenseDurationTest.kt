package com.anox.messenger.account

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B-003 v1.4 standard license duration tests.
 *
 * Proves exactly {30, 90, 180} days exist and that neither a 365-day standard duration nor a
 * general one-week trial duration is represented.
 */
class LicenseDurationTest {

    @Test
    fun `exactly the three frozen durations exist`() {
        val days = LicenseDuration.entries.map { it.days }.toSet()
        assertEquals(setOf(30L, 90L, 180L), days)
    }

    @Test
    fun `there are exactly three standard durations`() {
        assertEquals(3, LicenseDuration.entries.size)
    }

    @Test
    fun `no 365 day standard duration exists`() {
        assertFalse(LicenseDuration.entries.any { it.days == 365L })
    }

    @Test
    fun `no one week trial duration exists`() {
        assertFalse(LicenseDuration.entries.any { it.days == 7L })
    }

    @Test
    fun `each frozen duration maps to its exact day count`() {
        assertEquals(30L, LicenseDuration.DAYS_30.days)
        assertEquals(90L, LicenseDuration.DAYS_90.days)
        assertEquals(180L, LicenseDuration.DAYS_180.days)
    }

    @Test
    fun `duration values are distinct`() {
        val values = LicenseDuration.entries.map { it.days }
        assertTrue(values.size == values.toSet().size)
    }
}
