package com.anox.messenger.account

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.time.Instant
import java.util.UUID

/**
 * Instrumentation tests for [FileRegistrationSessionStore] against the real Android no-backup
 * file storage and the dedicated Android Keystore AES-GCM key.
 */
@RunWith(AndroidJUnit4::class)
class FileRegistrationSessionStoreTest {

    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val file = File(context.noBackupFilesDir, "anox_registration_session.enc")
    private val backupFile = File(context.noBackupFilesDir, "anox_registration_session.enc.bak")
    private lateinit var store: FileRegistrationSessionStore

    private val username = (Username.validate("alice") as UsernameValidation.Valid).username
    private val registrationId = RegistrationId.parse(UUID.randomUUID().toString())!!
    private val grant = RegistrationGrant("grant-value-ascii-plaintext", Instant.parse("2026-08-22T00:30:00Z"))

    @Before
    fun setUp() {
        file.delete()
        backupFile.delete()
        store = FileRegistrationSessionStore(context)
    }

    @After
    fun tearDown() {
        file.delete()
        backupFile.delete()
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
    fun corruptFileThrowsSecurityException() {
        file.parentFile?.mkdirs()
        file.writeBytes(byteArrayOf(1, 2, 3, 4, 5))
        try {
            store.load()
            fail("expected RegistrationSessionSecurityException")
        } catch (e: RegistrationSessionSecurityException) {
            // expected: corrupt data must not silently become a fresh registration
        }
    }

    @Test
    fun tamperedCiphertextThrowsSecurityException() {
        store.save(RegistrationState.Reserved(registrationId, grant, username))
        val bytes = file.readBytes()
        if (bytes.isNotEmpty()) {
            bytes[bytes.size - 1] = (bytes[bytes.size - 1].toInt() xor 0xFF).toByte()
        }
        file.writeBytes(bytes)
        try {
            store.load()
            fail("expected RegistrationSessionSecurityException")
        } catch (e: RegistrationSessionSecurityException) {
            // expected: AES-GCM authentication must fail
        }
    }

    @Test
    fun persistedGrantIsNotPlaintext() {
        store.save(RegistrationState.Reserved(registrationId, grant, username))
        val bytes = file.readBytes()
        val asString = String(bytes, Charsets.ISO_8859_1)
        assertFalse(
            "grant value must not appear as plaintext in the session file",
            asString.contains(grant.value)
        )
        assertFalse(
            "username must not appear as plaintext",
            asString.contains(username.value)
        )
    }

    @Test
    fun noTmpOrPlaintextBackupArtifacts() {
        store.save(RegistrationState.Reserved(registrationId, grant, username))
        store.save(
            RegistrationState.Committed(
                AccountId.parse(UUID.randomUUID().toString())!!,
                DeviceId.parse(UUID.randomUUID().toString())!!,
                username
            )
        )

        val tmpFile = File(context.noBackupFilesDir, "anox_registration_session.enc.tmp")
        assertFalse("old .tmp plaintext artifact must not exist", tmpFile.exists())

        // The AndroidX AtomicFile may create a `.bak` backup; if it exists, it must also not
        // contain the grant in plaintext.
        if (backupFile.exists()) {
            val backup = String(backupFile.readBytes(), Charsets.ISO_8859_1)
            assertFalse("grant must not appear as plaintext in backup file", backup.contains(grant.value))
        }
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
