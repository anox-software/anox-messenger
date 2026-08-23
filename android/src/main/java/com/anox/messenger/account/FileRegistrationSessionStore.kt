package com.anox.messenger.account

import android.content.Context
import androidx.core.util.AtomicFile
import com.anox.messenger.security.keystore.RegistrationSessionKey
import java.io.File

/**
 * Persistent, encrypted [RegistrationSessionStore] using a dedicated Android Keystore
 * AES-256-GCM key and [AtomicFile] from AndroidX for atomic file replacement.
 *
 * Properties:
 *  - lives under [Context.getNoBackupFilesDir], excluded from backup and D2D transfer;
 *  - never stores the 256-bit registration grant in plaintext on disk;
 *  - uses a fresh IV for every write;
 *  - returns [RegistrationState.NotStarted] only when no file exists;
 *  - treats any read/decrypt/parse failure as a [RegistrationSessionSecurityException];
 *  - does not silently fall back to a fresh in-progress state if the encrypted session
 *    becomes unreadable (the orchestrator checks [DeviceAuthBindingStore] to fail closed).
 *
 * The old `anox_registration_session.state` file name is intentionally changed to
 * `anox_registration_session.enc` because the on-disk format is now an authenticated binary
 * envelope, not text. A stale unencrypted file from a previous install is simply ignored.
 */
class FileRegistrationSessionStore(
    context: Context,
    private val key: RegistrationSessionKey = RegistrationSessionKey()
) : RegistrationSessionStore {

    private val file = File(context.noBackupFilesDir, FILE_NAME)
    private val atomicFile = AtomicFile(file)

    @Synchronized
    override fun load(): RegistrationState {
        if (!file.exists()) return RegistrationState.NotStarted
        val envelope = try {
            atomicFile.readFully()
        } catch (e: Exception) {
            throw RegistrationSessionSecurityException("registration session file could not be read", e)
        }
        if (envelope.isEmpty()) return RegistrationState.NotStarted

        val plaintext = try {
            key.decrypt(envelope)
        } catch (e: Exception) {
            throw RegistrationSessionSecurityException("registration session could not be authenticated", e)
        }
        return BinaryRegistrationStateCodec.decode(plaintext)
            ?: throw RegistrationSessionSecurityException("registration session payload is malformed")
    }

    @Synchronized
    override fun save(state: RegistrationState) {
        val plaintext = BinaryRegistrationStateCodec.encode(state)
        val envelope = key.encrypt(plaintext)
        val out = try {
            atomicFile.startWrite()
        } catch (e: Exception) {
            throw RegistrationSessionSecurityException("registration session write could not start", e)
        }
        try {
            out.write(envelope)
            out.flush()
            atomicFile.finishWrite(out)
        } catch (e: Exception) {
            atomicFile.failWrite(out)
            throw RegistrationSessionSecurityException("registration session write failed", e)
        }
    }

    @Synchronized
    override fun clear() {
        atomicFile.delete()
    }

    companion object {
        private const val FILE_NAME = "anox_registration_session.enc"
    }
}
