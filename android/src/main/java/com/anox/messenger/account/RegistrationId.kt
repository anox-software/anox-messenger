package com.anox.messenger.account

import java.util.UUID

/**
 * Server-issued registration session identifier.
 *
 * B-003 (FROZEN v1.4): `registration_id` is a UUIDv4 minted by the server when a registration
 * (license + username reservation) is created. The Android client never manufactures this
 * value; it only holds the one the server returned for the duration of the registration
 * transaction.
 */
@ConsistentCopyVisibility
data class RegistrationId private constructor(val value: UUID) {

    override fun toString(): String = value.toString()

    companion object {
        /** Parses [raw] as a server-issued registration id. Returns null if not a valid UUIDv4. */
        fun parse(raw: String): RegistrationId? = UuidV4.parse(raw)?.let { RegistrationId(it) }
    }
}
