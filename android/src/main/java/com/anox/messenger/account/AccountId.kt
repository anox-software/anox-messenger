package com.anox.messenger.account

import java.util.UUID

/**
 * Server-issued account identifier.
 *
 * B-003 (FROZEN v1.4): `account_id` is a server-generated UUIDv4. There is no client-side
 * factory that mints a new [AccountId]; instances only come from parsing a value the server
 * returned.
 */
@ConsistentCopyVisibility
data class AccountId private constructor(val value: UUID) {

    override fun toString(): String = value.toString()

    companion object {
        /** Parses [raw] as a server-issued account id. Returns null if not a valid UUIDv4. */
        fun parse(raw: String): AccountId? = UuidV4.parse(raw)?.let { AccountId(it) }
    }
}
