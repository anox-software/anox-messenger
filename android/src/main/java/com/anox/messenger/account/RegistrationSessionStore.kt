package com.anox.messenger.account

/**
 * Durable storage for the in-progress registration transaction, so that a crash/process death
 * before [RegistrationState.Committed] can resume rather than restart.
 *
 * This is transaction-resume storage only. It is bounded by the registration grant's 30-minute
 * TTL, is never treated as an account-recovery credential, and never permits a different device
 * installation to resume someone else's registration (there is no cross-device transport for
 * this state).
 */
interface RegistrationSessionStore {

    /** The last durably recorded state, or [RegistrationState.NotStarted] if none. */
    fun load(): RegistrationState

    /** Durably records [state], overwriting any previous state. */
    fun save(state: RegistrationState)

    /** Clears any recorded state (transaction finished, expired, or explicitly abandoned). */
    fun clear()
}

/** In-memory [RegistrationSessionStore]. Intended for tests and foundation wiring. */
class InMemoryRegistrationSessionStore : RegistrationSessionStore {

    @Volatile
    private var state: RegistrationState = RegistrationState.NotStarted

    override fun load(): RegistrationState = state

    override fun save(state: RegistrationState) {
        this.state = state
    }

    override fun clear() {
        state = RegistrationState.NotStarted
    }
}
