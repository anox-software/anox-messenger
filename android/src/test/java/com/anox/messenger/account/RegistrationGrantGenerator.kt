package com.anox.messenger.account

import java.security.SecureRandom
import java.time.Instant
import java.util.Base64

/**
 * CSPRNG-backed generator for opaque 256-bit registration grants.
 *
 * TEST SCOPE ONLY. The production client never authoritatively creates a registration grant;
 * the real grant is issued by the B-004 server. This helper exists only so the registration
 * state machine can be exercised without a fake production backend.
 */
class RegistrationGrantGenerator(
    private val secureRandom: SecureRandom = SecureRandom()
) {
    fun newGrant(issuedAt: Instant): RegistrationGrant {
        val raw = ByteArray(RegistrationGrant.ENTROPY_BYTES)
        secureRandom.nextBytes(raw)
        val encoded = Base64.getUrlEncoder().withoutPadding().encodeToString(raw)
        return RegistrationGrant(
            value = encoded,
            expiresAt = issuedAt.plusSeconds(RegistrationGrant.TTL_MINUTES * 60)
        )
    }
}
