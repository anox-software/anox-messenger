package com.anox.messenger.account

/**
 * Frozen B-003 account states. Server-authoritative; the client never derives this locally.
 *
 * No state here represents or enables account recovery or device replacement.
 */
enum class AccountState {
    ACTIVE,
    SUSPENDED,
    REVOKED,
    DELETED
}
