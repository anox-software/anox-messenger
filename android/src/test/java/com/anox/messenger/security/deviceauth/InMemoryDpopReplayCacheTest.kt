package com.anox.messenger.security.deviceauth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Frozen B-002 replay window (5 minutes) tests. */
class InMemoryDpopReplayCacheTest {

    @Test
    fun `frozen window is five minutes`() {
        assertEquals(300L, InMemoryDpopReplayCache.DEFAULT_WINDOW_SECONDS)
    }

    @Test
    fun `first use is accepted and immediate reuse is rejected`() {
        val cache = InMemoryDpopReplayCache(clock = MutableTestClock())

        assertTrue(cache.recordIfAbsent("jti-1"))
        assertFalse(cache.recordIfAbsent("jti-1"))
    }

    @Test
    fun `distinct jti values are independent`() {
        val cache = InMemoryDpopReplayCache(clock = MutableTestClock())

        assertTrue(cache.recordIfAbsent("jti-a"))
        assertTrue(cache.recordIfAbsent("jti-b"))
        assertFalse(cache.recordIfAbsent("jti-a"))
        assertFalse(cache.recordIfAbsent("jti-b"))
    }

    @Test
    fun `replay is still rejected just inside the window`() {
        val clock = MutableTestClock()
        val cache = InMemoryDpopReplayCache(clock = clock)

        assertTrue(cache.recordIfAbsent("jti-1"))
        clock.advanceSeconds(299)
        assertFalse("must still be treated as a replay inside the window", cache.recordIfAbsent("jti-1"))
    }

    @Test
    fun `entry is evicted once the window elapses`() {
        val clock = MutableTestClock()
        val cache = InMemoryDpopReplayCache(clock = clock)

        assertTrue(cache.recordIfAbsent("jti-1"))
        clock.advanceSeconds(300)
        assertTrue("entry must expire after the window", cache.recordIfAbsent("jti-1"))
    }

    @Test
    fun `expired entries do not block unrelated new entries`() {
        val clock = MutableTestClock()
        val cache = InMemoryDpopReplayCache(clock = clock)

        repeat(50) { assertTrue(cache.recordIfAbsent("old-$it")) }
        clock.advanceSeconds(301)
        repeat(50) { assertTrue(cache.recordIfAbsent("new-$it")) }
        // Old entries expired, so they are accepted again.
        repeat(50) { assertTrue(cache.recordIfAbsent("old-$it")) }
    }
}
