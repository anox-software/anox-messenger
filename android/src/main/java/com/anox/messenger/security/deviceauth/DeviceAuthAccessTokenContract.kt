package com.anox.messenger.security.deviceauth

import com.nimbusds.jose.util.Base64URL
import java.security.MessageDigest
import java.security.SecureRandom

/**
 * The frozen B-002 access token contract.
 *
 * This object encodes the *contract* only. It is deliberately NOT a production
 * authentication backend: token issuance, persistence, session binding and revocation are
 * B-004 work and are not implemented in this task.
 *
 * B-002 (FROZEN v1.1):
 *  - opaque access token carrying 256 random bits;
 *  - the server stores only the SHA-256 of the token, never the token itself;
 *  - TTL is 15 minutes;
 *  - there is no refresh token.
 */
object DeviceAuthAccessTokenContract {

    /** Frozen token entropy: 256 bits. */
    const val TOKEN_ENTROPY_BITS: Int = 256

    /** Frozen token entropy in bytes. */
    const val TOKEN_ENTROPY_BYTES: Int = TOKEN_ENTROPY_BITS / 8

    /** Frozen access token TTL in seconds (15 minutes). */
    const val TOKEN_TTL_SECONDS: Long = 15L * 60L

    /**
     * There is no refresh token in V1. Exposed as an explicit constant so that any future
     * code path attempting to introduce one is visibly contradicting the frozen contract.
     */
    const val REFRESH_TOKEN_SUPPORTED: Boolean = false

    /**
     * Computes the DPoP `ath` claim for [accessToken]:
     * base64url(SHA-256(ASCII(access_token))) per RFC9449 section 4.2.
     */
    fun accessTokenHash(accessToken: String): String =
        Base64URL.encode(sha256(accessToken.toByteArray(Charsets.US_ASCII))).toString()

    /**
     * The value a server is permitted to persist for [accessToken]: the SHA-256 digest.
     *
     * Identical digest as [accessTokenHash], base64url encoded. The plaintext token is
     * never a legitimate server-side stored value.
     */
    fun serverStoredTokenHash(accessToken: String): String = accessTokenHash(accessToken)

    /** Whether [issuedAtEpochSeconds] is still inside the frozen 15 minute TTL. */
    fun isTokenExpired(issuedAtEpochSeconds: Long, nowEpochSeconds: Long): Boolean =
        nowEpochSeconds >= issuedAtEpochSeconds + TOKEN_TTL_SECONDS

    private fun sha256(input: ByteArray): ByteArray =
        MessageDigest.getInstance("SHA-256").digest(input)
}

/**
 * CSPRNG-backed generator for opaque 256-bit access tokens.
 *
 * FOUNDATION / TEST SCOPE ONLY. Production tokens are minted by the backend under B-004.
 * This exists so the DPoP `ath` binding path can be exercised without inventing a fake
 * production authentication server.
 */
class DeviceAuthAccessTokenGenerator(
    private val secureRandom: SecureRandom = SecureRandom()
) {
    /** Returns a fresh opaque token carrying 256 random bits, base64url encoded. */
    fun newOpaqueToken(): String {
        val raw = ByteArray(DeviceAuthAccessTokenContract.TOKEN_ENTROPY_BYTES)
        secureRandom.nextBytes(raw)
        return Base64URL.encode(raw).toString()
    }
}
