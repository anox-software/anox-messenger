package com.anox.crypto

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * LEGACY-FIX-01: ANOX-MAINARCH-031 JNI buffer error domain mapping tests.
 *
 * These are pure JVM tests: they do not need the Android runtime or a real Rust native
 * library, but they prove the Kotlin-side error contract that the JNI layer depends on.
 */
class CryptoErrorMappingTest {

    @Test
    fun `buffer too small maps to dedicated BufferTooSmall error`() {
        assertEquals(CryptoError.BufferTooSmall, CryptoError.fromCode(-11))
    }

    @Test
    fun `invalid ciphertext remains a real crypto error`() {
        assertEquals(CryptoError.InvalidCiphertext, CryptoError.fromCode(-2))
    }

    @Test
    fun `invalid input remains a real crypto error`() {
        assertEquals(CryptoError.InvalidInput, CryptoError.fromCode(-1))
    }

    @Test
    fun `unknown codes are not buffer too small`() {
        val unknown = CryptoError.fromCode(-12345)
        assertTrue(unknown is CryptoError.UnknownError)
        assertEquals(-12345, (unknown as CryptoError.UnknownError).code)
    }
}
