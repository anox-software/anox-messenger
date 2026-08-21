package com.anox.messenger.security.deviceauth

/**
 * Injectable clock so that DPoP `iat` acceptance windows and replay-cache expiry are
 * deterministically testable.
 */
interface DeviceAuthClock {
    /** Current time in milliseconds since the UNIX epoch. */
    fun nowMillis(): Long

    /** Current time in whole seconds since the UNIX epoch (DPoP `iat` granularity). */
    fun nowEpochSeconds(): Long = nowMillis() / 1000L
}

/** Production clock. */
object SystemDeviceAuthClock : DeviceAuthClock {
    override fun nowMillis(): Long = System.currentTimeMillis()
}
