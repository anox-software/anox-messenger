package com.anox.messenger.security.deviceauth

/**
 * Lifecycle owner of the B-002 Device Authentication key.
 *
 * Frozen properties this contract preserves:
 *  - the key is independent from E2EE identity, account identity, license and `K_STATE`;
 *  - the private key is non-exportable and is never returned as bytes;
 *  - StrongBox is preferred, TEE is accepted for production, software-only is rejected;
 *  - terminal key loss never triggers silent replacement-key creation.
 */
interface DeviceAuthKeyManager {

    /** Current key lifecycle state. */
    fun status(): DeviceAuthKeyStatus

    /**
     * Creates the Device Auth key if and only if the current state is
     * [DeviceAuthKeyStatus.AbsentNotBound].
     *
     * If a key already exists, this is a no-op and the existing state is returned.
     *
     * @throws DeviceAuthTerminalStateException if the state is
     *   [DeviceAuthKeyStatus.TerminalKeyLoss]. Creating a replacement key for an already
     *   bound account is forbidden by B-002.
     */
    fun createKeyIfAbsent(): DeviceAuthKeyStatus

    /** Provable hardware backing of the existing key, or null when no key exists. */
    fun hardwareSecurityLevel(): HardwareSecurityLevel?

    /**
     * Whether the existing key may be used for production registration / production
     * network authentication. False when no key exists or hardware backing is not proven.
     */
    fun isProductionEligible(): Boolean

    /**
     * Signing handle for the existing key.
     *
     * @throws DeviceAuthTerminalStateException if there is no usable key.
     */
    fun signer(): DeviceAuthSigner

    /**
     * Deletes the Device Auth key.
     *
     * Explicitly destructive and never called implicitly by any recovery, retry or
     * error-handling path. Deleting the key does NOT delete the E2EE identity or the local
     * protected state, and does not restore access to a previously bound account.
     */
    fun deleteKeyDestructively()
}
