package com.anox.messenger.security.deviceauth

/**
 * Records the fact that this installation's Device Auth key has been bound to an account
 * or device registration.
 *
 * This marker is what allows the subsystem to tell apart:
 *  - a legitimate first run (no key, never bound) -> key creation allowed; and
 *  - terminal Device Auth key loss (no key, but previously bound) -> fail closed.
 *
 * The marker itself is NOT a secret and NOT cryptographic material. It must survive the
 * disappearance of the Keystore key in order to be useful, which is exactly why it is
 * stored separately from the key.
 */
interface DeviceAuthBindingStore {

    /** Whether the Device Auth key has ever been marked as bound. */
    fun isBound(): Boolean

    /**
     * Marks the Device Auth key as bound. Called by a future registration flow (B-003)
     * once the backend has accepted this device's public key.
     */
    fun markBound()

    /**
     * Clears the bound marker.
     *
     * This is an explicitly destructive local operation. It does NOT constitute account
     * recovery or device re-binding: the old account remains permanently unreachable per
     * B-002. It exists so that a full local reset (new account from scratch) is possible.
     */
    fun clearBinding()
}

/** In-memory binding store. Intended for tests and for foundation wiring. */
class InMemoryDeviceAuthBindingStore(initiallyBound: Boolean = false) : DeviceAuthBindingStore {

    @Volatile
    private var bound: Boolean = initiallyBound

    override fun isBound(): Boolean = bound

    override fun markBound() {
        bound = true
    }

    override fun clearBinding() {
        bound = false
    }
}
