package com.anox.messenger.security.deviceauth

import com.nimbusds.jose.util.Base64URL
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.MessageDigest

/** Frozen B-002 access token contract tests. */
class DeviceAuthAccessTokenContractTest {

    @Test
    fun `frozen contract constants`() {
        assertEquals(256, DeviceAuthAccessTokenContract.TOKEN_ENTROPY_BITS)
        assertEquals(32, DeviceAuthAccessTokenContract.TOKEN_ENTROPY_BYTES)
        assertEquals(15L * 60L, DeviceAuthAccessTokenContract.TOKEN_TTL_SECONDS)
        assertFalse(
            "V1 must not support refresh tokens",
            DeviceAuthAccessTokenContract.REFRESH_TOKEN_SUPPORTED
        )
    }

    @Test
    fun `generated token carries 256 bits`() {
        val token = DeviceAuthAccessTokenGenerator().newOpaqueToken()
        assertEquals(32, Base64URL(token).decode().size)
    }

    @Test
    fun `generated tokens are unique`() {
        val generator = DeviceAuthAccessTokenGenerator()
        val tokens = (1..200).map { generator.newOpaqueToken() }
        assertEquals(tokens.size, tokens.toSet().size)
    }

    @Test
    fun `ath is base64url sha256 of the ascii token`() {
        val token = "example-access-token-value"
        val expected = Base64URL.encode(
            MessageDigest.getInstance("SHA-256").digest(token.toByteArray(Charsets.US_ASCII))
        ).toString()

        assertEquals(expected, DeviceAuthAccessTokenContract.accessTokenHash(token))
    }

    @Test
    fun `ath is deterministic and token specific`() {
        val a = DeviceAuthAccessTokenContract.accessTokenHash("token-a")
        val b = DeviceAuthAccessTokenContract.accessTokenHash("token-b")

        assertEquals(a, DeviceAuthAccessTokenContract.accessTokenHash("token-a"))
        assertNotEquals(a, b)
    }

    @Test
    fun `server stored value is the hash and never the token`() {
        val token = DeviceAuthAccessTokenGenerator().newOpaqueToken()
        val stored = DeviceAuthAccessTokenContract.serverStoredTokenHash(token)

        assertNotEquals(token, stored)
        assertFalse(stored.contains(token))
        assertEquals(DeviceAuthAccessTokenContract.accessTokenHash(token), stored)
        // SHA-256 base64url without padding is 43 characters.
        assertEquals(43, stored.length)
    }

    @Test
    fun `ttl boundary behaviour`() {
        val issuedAt = 1_760_000_000L
        val ttl = DeviceAuthAccessTokenContract.TOKEN_TTL_SECONDS

        assertFalse(DeviceAuthAccessTokenContract.isTokenExpired(issuedAt, issuedAt))
        assertFalse(DeviceAuthAccessTokenContract.isTokenExpired(issuedAt, issuedAt + ttl - 1))
        assertTrue(DeviceAuthAccessTokenContract.isTokenExpired(issuedAt, issuedAt + ttl))
        assertTrue(DeviceAuthAccessTokenContract.isTokenExpired(issuedAt, issuedAt + ttl + 1))
    }
}
