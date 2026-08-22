package com.anox.messenger.security.deviceauth

import com.nimbusds.jose.util.Base64URL
import java.security.SecureRandom

/**
 * Generates DPoP `jti` values.
 *
 * B-002 (FROZEN v1.1): `jti` must carry at least 128 random bits.
 */
interface JtiGenerator {
    fun newJti(): String
}

/**
 * CSPRNG-backed `jti` generator.
 *
 * Emits [JTI_ENTROPY_BYTES] bytes of [SecureRandom] output, base64url encoded without
 * padding, which satisfies the frozen 128-bit minimum.
 */
class SecureRandomJtiGenerator(
    private val secureRandom: SecureRandom = SecureRandom()
) : JtiGenerator {

    override fun newJti(): String {
        val raw = ByteArray(JTI_ENTROPY_BYTES)
        secureRandom.nextBytes(raw)
        return Base64URL.encode(raw).toString()
    }

    companion object {
        /** 16 bytes = 128 bits, the frozen B-002 minimum. */
        const val JTI_ENTROPY_BYTES: Int = 16

        /**
         * Minimum accepted length of a base64url-encoded `jti` carrying 128 bits.
         * ceil(16 / 3) * 4 = 24 with padding; unpadded base64url of 16 bytes is 22 chars.
         */
        const val MIN_ENCODED_JTI_LENGTH: Int = 22
    }
}
