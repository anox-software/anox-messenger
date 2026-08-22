package com.anox.messenger.security.deviceauth

/**
 * Lifecycle state of the B-002 Device Authentication key.
 *
 * The distinction between [AbsentNotBound] and [TerminalKeyLoss] is security critical.
 *
 * B-002 (FROZEN v1.1): "Device Auth key invalidation is terminal for old-account network
 * access in V1; do not silently generate replacement key."
 */
sealed class DeviceAuthKeyStatus {

    /**
     * No Device Auth key exists and this device has never been bound to an account.
     *
     * This is the legitimate first-run state. Key creation is allowed.
     */
    object AbsentNotBound : DeviceAuthKeyStatus()

    /** A Device Auth key exists. */
    data class Present(val hardwareSecurityLevel: HardwareSecurityLevel) : DeviceAuthKeyStatus()

    /**
     * A Device Auth key was previously bound to an account but is now missing or
     * permanently invalidated (for example: key invalidated by the platform, keystore
     * cleared, biometric/credential reset that invalidated the key).
     *
     * This is TERMINAL for the old account's network access in V1.
     *
     * The subsystem MUST NOT silently create a replacement key in this state, and MUST NOT
     * re-bind a new key to the old account. There is no account recovery and no device
     * replacement flow in V1. Local E2EE identity and local protected state are NOT
     * affected by this state and MUST NOT be deleted because of it.
     */
    object TerminalKeyLoss : DeviceAuthKeyStatus()
}

/**
 * Raised when an operation requires a usable Device Auth key but the key is in a
 * terminal state, or when replacement-key creation was attempted after terminal loss.
 */
class DeviceAuthTerminalStateException(message: String) : IllegalStateException(message)

/** Raised when a Device Auth key exists but is not eligible for production use. */
class DeviceAuthNotProductionEligibleException(
    val hardwareSecurityLevel: HardwareSecurityLevel
) : IllegalStateException(
    "Device Auth key is not production eligible: hardware security level " +
        "$hardwareSecurityLevel. B-002 requires StrongBox or TEE."
)
