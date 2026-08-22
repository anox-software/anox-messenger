package com.anox.messenger.security.deviceauth

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/**
 * Instrumentation tests for [FileDeviceAuthBindingStore] against the real Android no-backup
 * file storage.
 */
@RunWith(AndroidJUnit4::class)
class FileDeviceAuthBindingStoreTest {

    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private lateinit var file: File
    private lateinit var store: FileDeviceAuthBindingStore

    @Before
    fun setUp() {
        file = File(context.noBackupFilesDir, "anox_deviceauth_binding.state")
        file.delete()
        store = FileDeviceAuthBindingStore(context)
    }

    @After
    fun tearDown() {
        file.delete()
    }

    @Test
    fun firstRunIsNotBound() {
        assertFalse(store.isBound())
    }

    @Test
    fun markBoundPersistsAcrossInstances() {
        store.markBound()
        assertTrue(store.isBound())

        val reopened = FileDeviceAuthBindingStore(context)
        assertTrue("bound state must survive process/instance restart", reopened.isBound())
    }

    @Test
    fun clearBindingPersistsAcrossInstances() {
        store.markBound()
        store.clearBinding()
        assertFalse(store.isBound())

        val reopened = FileDeviceAuthBindingStore(context)
        assertFalse(reopened.isBound())
    }

    @Test
    fun storedUnderNoBackupFilesDir() {
        store.markBound()
        assertTrue(file.exists())
        assertTrue(
            "binding marker must live under noBackupFilesDir",
            file.absolutePath.startsWith(context.noBackupFilesDir.absolutePath)
        )
    }

    @Test
    fun corruptFileFailsClosedToBound() {
        file.parentFile?.mkdirs()
        file.writeBytes(byteArrayOf(1, 2, 3))
        assertTrue("corrupt binding state must fail closed (treated as bound)", store.isBound())
    }

    @Test
    fun truncatedFileFailsClosedToBound() {
        file.parentFile?.mkdirs()
        file.writeBytes("ANXB".toByteArray(Charsets.US_ASCII))
        assertTrue(store.isBound())
    }

    @Test
    fun corruptStateDoesNotPermitSilentUnbinding() {
        store.markBound()
        // Corrupt the file in place.
        file.writeBytes(byteArrayOf(9, 9, 9, 9, 9, 9))
        assertTrue("corruption must never be interpreted as an unbound/first-run state", store.isBound())
    }
}
