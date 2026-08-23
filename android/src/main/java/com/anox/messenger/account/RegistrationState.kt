package com.anox.messenger.account

/**
 * Client-side view of the B-003 registration transaction.
 *
 * Frozen sequence: reserve license+username -> registration session/grant -> register Device
 * Auth with proof-of-possession -> create E2EE locally -> upload public E2EE material ->
 * arm the pre-commit fail-closed guard -> call the atomic final server commit of
 * account/device/Device Auth binding/E2EE public identity/entitlement redemption.
 *
 * Security-critical property: the client MUST NOT treat the account as
 * [AccountState.ACTIVE][AccountState] before [Committed] is reached. [Committed] itself only
 * means the local transaction observed a successful commit response; it is not by itself a
 * substitute for an authoritative account-state check.
 *
 * A crash/process death before [Committed] is transaction *resume*, modelled by resuming into
 * whichever intermediate state was last durably recorded (see [RegistrationSessionStore]). It
 * is never treated as account recovery or device replacement, and no state in this hierarchy
 * represents either.
 *
 * Terminal states cannot be overwritten by normal failure handling. [Committed] is the only
 * terminal success state; it is preserved because it represents a potentially successful
 * remote atomic commit. [CommitArmed] is not terminal, but it is protected by the durable
 * [com.anox.messenger.security.deviceauth.DeviceAuthBindingStore] armed marker and must not
 * be downgraded while that marker is set.
 */
sealed class RegistrationState {

    /** Whether this state is a terminal success state that must not be downgraded. */
    open val isTerminal: Boolean = false

    /** No registration transaction is in progress. */
    object NotStarted : RegistrationState()

    /** License + username reservation succeeded; a registration grant is held. */
    data class Reserved(
        val registrationId: RegistrationId,
        val grant: RegistrationGrant,
        val username: Username
    ) : RegistrationState()

    /** Device Auth registration (proof-of-possession) succeeded for this registration. */
    data class DeviceAuthRegistered(
        val registrationId: RegistrationId,
        val grant: RegistrationGrant,
        val username: Username,
        val deviceAuthJwkThumbprint: String
    ) : RegistrationState()

    /** Local E2EE identity was created and its public material was uploaded. */
    data class PublicIdentityUploaded(
        val registrationId: RegistrationId,
        val grant: RegistrationGrant,
        val username: Username,
        val deviceAuthJwkThumbprint: String
    ) : RegistrationState()

    /**
     * The pre-commit fail-closed guard has been armed and persisted.
 *
     * From this point the remote commit endpoint may be called; a missing Device Auth key
     * must be treated as terminal. This state records enough material to retry the idempotent
     * commit using the same Device Auth identity.
     */
    data class CommitArmed(
        val registrationId: RegistrationId,
        val grant: RegistrationGrant,
        val username: Username,
        val deviceAuthJwkThumbprint: String
    ) : RegistrationState()

    /**
     * The server confirmed the atomic final commit.
     *
     * This is the only state in which the client may consider the registration transaction
     * itself complete. It is still not, by itself, an authoritative live [AccountState] check.
     */
    data class Committed(
        val accountId: AccountId,
        val deviceId: DeviceId,
        val username: Username
    ) : RegistrationState() {
        override val isTerminal: Boolean = true
    }

    /** The registration grant's 30-minute TTL elapsed before commit; the reservation is released. */
    data class Expired(val registrationId: RegistrationId) : RegistrationState()

    /** A step failed. [reason] is a safe, non-secret diagnostic string. */
    data class Failed(val reason: String) : RegistrationState()
}
