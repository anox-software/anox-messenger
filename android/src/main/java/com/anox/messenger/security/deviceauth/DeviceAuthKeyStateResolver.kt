package com.anox.messenger.security.deviceauth

/**
 * Pure decision logic for the B-002 Device Auth key lifecycle.
 *
 * Deliberately free of Android APIs so that the security-critical distinction between
 * first-run key absence and terminal key loss is directly unit testable on the JVM.
 */
object DeviceAuthKeyStateResolver {

    /**
     * Resolves the key status.
     *
     * @param keyPresent whether a usable, non-invalidated key entry exists.
     * @param hardwareSecurityLevel provable hardware backing when [keyPresent] is true.
     * @param isBound whether this installation's key has been bound to a successful account.
     * @param isArmed whether a final commit has been armed and may have succeeded server-side.
     *   Either [isBound] or [isArmed] is sufficient to make key loss terminal.
     */
    fun resolve(
        keyPresent: Boolean,
        hardwareSecurityLevel: HardwareSecurityLevel?,
        isBound: Boolean,
        isArmed: Boolean
    ): DeviceAuthKeyStatus = when {
        keyPresent -> DeviceAuthKeyStatus.Present(
            hardwareSecurityLevel ?: HardwareSecurityLevel.UNKNOWN
        )
        // Previously bound or armed but the key is gone or invalidated -> terminal, fail closed.
        isBound || isArmed -> DeviceAuthKeyStatus.TerminalKeyLoss
        else -> DeviceAuthKeyStatus.AbsentNotBound
    }

    /**
     * Guards Device Auth key creation.
     *
     * @throws DeviceAuthTerminalStateException when [status] is
     *   [DeviceAuthKeyStatus.TerminalKeyLoss]. B-002 forbids silently generating a
     *   replacement key for an already bound or armed account.
     */
    fun requireCreationAllowed(status: DeviceAuthKeyStatus) {
        if (status is DeviceAuthKeyStatus.TerminalKeyLoss) {
            throw DeviceAuthTerminalStateException(
                "Device Auth key for an already bound or armed account is missing or permanently " +
                    "invalidated. B-002 forbids silently generating a replacement key. " +
                    "Old-account network access is terminal in V1; there is no recovery " +
                    "and no device re-binding."
            )
        }
    }
}
