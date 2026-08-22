package com.anox.messenger.account

import java.security.SecureRandom
import java.time.Instant
import java.util.Base64

/**
 * The opaque 256-bit registration grant issued by the server for a single registration
 * transaction.
 *
 * B-003 (FROZEN v1.4): the grant carries 256 random bits, the server persists only its hash,
 * and it expires after 30 minutes. It is not a refresh token and not an account-recovery
 * credential.
 *
 * The Android client holds this value only in memory / narrow registration-session storage for
 * the duration of the active registration transaction (see [RegistrationSessionStore]). It must
 * never be logged, included in crash reports, or persisted in ordinary preferences. [toString]
 * never prints the value to reduce the chance of accidental disclosure through logging or a
 * debugger preview.
 */
class RegistrationGrant(val value: String, val expiresAt: Instant) {

    override fun toString(): String = "RegistrationGrant(***, expiresAt=$expiresAt)"

    override fun equals(other: Any?): Boolean =
        other is RegistrationGrant && other.value == value && other.expiresAt == expiresAt

    override fun hashCode(): Int = value.hashCode() * 31 + expiresAt.hashCode()

    /** Whether the grant's 30-minute TTL has elapsed as of [now]. */
    fun isExpired(now: Instant): Boolean = !now.isBefore(expiresAt)

    companion object {
        /** Frozen B-003 grant TTL: 30 minutes. */
        const val TTL_MINUTES: Long = 30L

        /** Frozen B-003 grant entropy: 256 bits. */
        const val ENTROPY_BITS: Int = 256
        const val ENTROPY_BYTES: Int = ENTROPY_BITS / 8
    }
}

/**
 * CSPRNG-backed generator for opaque 256-bit registration grants.
 *
 * FOUNDATION / TEST SCOPE ONLY. In production the grant is issued by the server (B-004); this
 * exists so the registration state machine can be exercised without a fake production server.
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
