package com.anox.messenger.security.deviceauth

/**
 * Replay protection for DPoP `jti` values.
 *
 * B-002 (FROZEN v1.1): the replay cache window is 5 minutes and the cache is SHARED
 * server-side.
 */
interface DpopReplayCache {

    /**
     * Atomically records [jti] as seen.
     *
     * @return true if [jti] was not previously recorded within the window (accept),
     *   false if it is a replay (reject).
     */
    fun recordIfAbsent(jti: String): Boolean
}

/**
 * In-memory [DpopReplayCache] implementing the frozen 5 minute window.
 *
 * SCOPE WARNING: this is a single-process, in-memory implementation used to prove the
 * protocol semantics in tests and to provide a usable local boundary. It is explicitly
 * NOT the production replay cache. B-002 requires a shared server-side cache, which is
 * B-004 infrastructure work and is not implemented in this task. A future production
 * backend must supply its own distributed implementation of this interface.
 */
class InMemoryDpopReplayCache(
    private val clock: DeviceAuthClock = SystemDeviceAuthClock,
    private val windowSeconds: Long = DEFAULT_WINDOW_SECONDS
) : DpopReplayCache {

    private val seen = LinkedHashMap<String, Long>()

    @Synchronized
    override fun recordIfAbsent(jti: String): Boolean {
        val now = clock.nowEpochSeconds()
        evictExpired(now)
        if (seen.containsKey(jti)) return false
        seen[jti] = now
        return true
    }

    private fun evictExpired(now: Long) {
        val iterator = seen.entries.iterator()
        while (iterator.hasNext()) {
            val recordedAt = iterator.next().value
            if (now - recordedAt >= windowSeconds) {
                iterator.remove()
            } else {
                // LinkedHashMap preserves insertion order, so the first non-expired entry
                // means every later entry is also non-expired.
                break
            }
        }
    }

    companion object {
        /** Frozen B-002 replay window: 5 minutes. */
        const val DEFAULT_WINDOW_SECONDS: Long = 5L * 60L
    }
}
