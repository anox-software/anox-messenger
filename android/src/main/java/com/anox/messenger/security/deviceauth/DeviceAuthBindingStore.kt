package com.anox.messenger.security.deviceauth

/**
 * Records the fact that this installation's Device Auth key has been bound to an account
 * or is about to be committed in a way that may succeed server-side.
 *
 * This marker is what allows the subsystem to tell apart:
 *  - a legitimate first run (no key, never bound, never armed) -> key creation allowed; and
 *  - terminal Device Auth key loss (no key, but bound or armed) -> fail closed.
 *
 * Two flags are intentionally tracked:
 *  - [isBound]: a commit has been authoritatively accepted and the key is bound to an account;
 *  - [isArmed]: a commit has been armed locally and the remote endpoint may be called; until an
 *    authoritative response is received, the key must be treated as non-replaceable to prevent
 *    a replacement key from being bound to an account that may already have been committed
 *    server-side.
 *
 * The marker itself is NOT a secret and NOT cryptographic material. It must survive the
 * disappearance of the Keystore key in order to be useful, which is exactly why it is
 * stored separately from the key.
 */
interface DeviceAuthBindingStore {

    /** Whether the Device Auth key has ever been marked as bound. */
    fun isBound(): Boolean

    /**
     * Whether a final commit has been armed (the remote commit endpoint may have been or is
     * about to be called). While armed, key loss is treated as terminal even if [isBound] is
     * not yet true.
     */
    fun isArmed(): Boolean

    /**
     * Arms the pre-commit fail-closed guard. This is persisted before the remote commit
     * endpoint is called, so a crash/timeout/unknown-outcome never leaves the installation in a
     * state where a missing Device Auth key could be silently replaced.
     */
    fun markArmed()

    /**
     * Marks the Device Auth key as bound. Called by the B-003 registration flow once the
     * backend has authoritatively accepted this device. This also implies the key is armed.
     */
    fun markBound()

    /**
     * Clears the bound and armed markers.
     *
     * This is an explicitly destructive local operation. It does NOT constitute account
     * recovery or device re-binding: the old account remains permanently unreachable per
     * B-002. It exists so that a full local reset (new account from scratch) is possible.
     */
    fun clearBinding()
}

/** In-memory binding store. Intended for tests and for foundation wiring. */
class InMemoryDeviceAuthBindingStore(
    initiallyBound: Boolean = false,
    initiallyArmed: Boolean = false
) : DeviceAuthBindingStore {

    @Volatile
    private var bound: Boolean = initiallyBound

    @Volatile
    private var armed: Boolean = initiallyArmed

    override fun isBound(): Boolean = bound

    override fun isArmed(): Boolean = armed

    override fun markArmed() {
        armed = true
    }

    override fun markBound() {
        bound = true
        armed = true
    }

    override fun clearBinding() {
        bound = false
        armed = false
    }
}
