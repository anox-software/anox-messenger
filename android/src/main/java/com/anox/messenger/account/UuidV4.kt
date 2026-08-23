package com.anox.messenger.account

import java.util.UUID

/**
 * Parsing helper shared by [AccountId], [DeviceId] and [RegistrationId].
 *
 * B-003 (FROZEN v1.4): `account_id` and `device_id` are server-generated UUIDv4. The Android
 * client never manufactures canonical account/device/registration identities; it only parses
 * and validates identifiers received from the server.
 */
internal object UuidV4 {

    /**
     * Parses [raw] as a UUID and verifies it is version 4 (RFC 4122 variant 1, version 4).
     *
     * @return the parsed [UUID], or null if [raw] is not a syntactically valid UUID or is not
     *   version 4. Non-v4 UUIDs are deliberately rejected: this project's canonical account,
     *   device and registration identifiers are always v4, so accepting any UUID version would
     *   widen the accepted identifier space beyond what the server actually issues.
     */
    fun parse(raw: String): UUID? {
        val uuid = try {
            UUID.fromString(raw)
        } catch (e: IllegalArgumentException) {
            return null
        }
        return if (uuid.version() == 4) uuid else null
    }
}
