package com.anox.messenger.account

import java.util.UUID

/**
 * Server-issued device identifier.
 *
 * B-003 (FROZEN v1.4): `device_id` is a server-generated UUIDv4, and V1 supports exactly one
 * active device per account (ultimately DB-enforced under B-005). There is no client-side
 * factory that mints a new [DeviceId] and no add-device/replace-device/transfer-device flow.
 */
@ConsistentCopyVisibility
data class DeviceId private constructor(val value: UUID) {

    override fun toString(): String = value.toString()

    companion object {
        /** Parses [raw] as a server-issued device id. Returns null if not a valid UUIDv4. */
        fun parse(raw: String): DeviceId? = UuidV4.parse(raw)?.let { DeviceId(it) }
    }
}
