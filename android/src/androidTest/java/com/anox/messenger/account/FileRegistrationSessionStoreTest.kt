package com.anox.messenger.account

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.time.Instant
import java.util.UUID

/**
 * Instrumentation tests for [FileRegistrationSessionStore] against the real Android no-backup
 * file storage.
 */
@RunWith(AndroidJUnit4::class)
class FileRegistrationSessionStoreTest {

    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private lateinit var file: File
    private lateinit var store: FileRegistrationSessionStore

    private val username = (Username.validate("alice") as UsernameValidation.Valid).username
    private val registrationId = RegistrationId.parse(UUID.randomUUID().toString())!!
    private val grant = RegistrationGrant("grant-value", Instant.parse("2026-08-22T00:30:00Z"))

    @Before
    fun setUp() {
        file = File(context.noBackupFilesDir, "anox_registration_session.state")
        file.delete()
        store = FileRegistrationSessionStore(context)
    }

    @After
    fun tearDown() {
        file.delete()
    }

    @Test
    fun defaultsToNotStarted() {
        assertEquals(RegistrationState.NotStarted, store.load())
    }

    @Test
    fun savedStatePersistsAcrossInstances() {
        val state = RegistrationState.Reserved(registrationId, grant, username)
        store.save(state)

        val reopened = FileRegistrationSessionStore(context)
        assertEquals(state, reopened.load())
    }

    @Test
    fun clearResetsToNotStarted() {
        store.save(RegistrationState.Reserved(registrationId, grant, username))
        store.clear()
        assertEquals(RegistrationState.NotStarted, store.load())

        val reopened = FileRegistrationSessionStore(context)
        assertEquals(RegistrationState.NotStarted, reopened.load())
    }

    @Test
    fun storedUnderNoBackupFilesDir() {
        store.save(RegistrationState.Reserved(registrationId, grant, username))
        assertTrue(file.exists())
        assertTrue(
            "registration session state must live under noBackupFilesDir",
            file.absolutePath.startsWith(context.noBackupFilesDir.absolutePath)
        )
    }

    @Test
    fun corruptFileFailsClosedToNotStarted() {
        file.parentFile?.mkdirs()
        file.writeBytes(byteArrayOf(1, 2, 3, 4, 5))
        assertEquals(RegistrationState.NotStarted, store.load())
    }

    @Test
    fun overwriteReplacesPreviousState() {
        store.save(RegistrationState.Reserved(registrationId, grant, username))
        val committed = RegistrationState.Committed(
            AccountId.parse(UUID.randomUUID().toString())!!,
            DeviceId.parse(UUID.randomUUID().toString())!!,
            username
        )
        store.save(committed)
        assertEquals(committed, store.load())
    }
}
