package com.anox.messenger.security.deviceauth

import android.content.Context
import com.anox.messenger.storage.AtomicFileWriter
import java.io.File

/**
 * Persistent [DeviceAuthBindingStore] backed by a small file in the app's no-backup private
 * storage.
 *
 * B-003 foundation note: PROMPT-007 intentionally shipped only an in-memory
 * [DeviceAuthBindingStore] because no registration flow existed yet to actually bind a key.
 * This class provides the minimum safe persistent implementation now that B-003 registration
 * exists, per the frozen constraints:
 *  - never contains Device Auth private key material, E2EE private material, access-token
 *    plaintext or license plaintext (it stores a single boolean-shaped marker, nothing else);
 *  - lives under [Context.getNoBackupFilesDir], which Android excludes from both classic backup
 *    and device-to-device transfer regardless of `dataExtractionRules`, in addition to this
 *    app's existing `allowBackup="false"` / `dataExtractionRules` exclusion of the entire
 *    private storage root;
 *  - fails closed on malformed/corrupt state: an unreadable or corrupt marker file is reported
 *    as **bound**, not unbound. Treating ambiguous state as bound is the safe direction here,
 *    because [isBound] `== true` only ever blocks new-key creation
 *    ([DeviceAuthKeyStateResolver.requireCreationAllowed]); it can never cause a silent Device
 *    Auth key replacement for what might in fact be an already-bound installation.
 */
class FileDeviceAuthBindingStore(context: Context) : DeviceAuthBindingStore {

    private val file: File = File(context.noBackupFilesDir, FILE_NAME)

    @Synchronized
    override fun isBound(): Boolean {
        if (!file.exists()) return false
        val bytes = try {
            file.readBytes()
        } catch (e: Exception) {
            return true // fail closed: unreadable state is treated as bound.
        }
        return parse(bytes) ?: true // fail closed: unparseable content is treated as bound.
    }

    @Synchronized
    override fun markBound() {
        write(true)
    }

    @Synchronized
    override fun clearBinding() {
        write(false)
    }

    private fun write(bound: Boolean) {
        val payload = MAGIC + byteArrayOf(FORMAT_VERSION, if (bound) 1 else 0)
        AtomicFileWriter.write(file, payload)
    }

    /** Returns the stored flag, or null if [bytes] is not a recognised marker file. */
    private fun parse(bytes: ByteArray): Boolean? {
        if (bytes.size != MAGIC.size + 2) return null
        for (i in MAGIC.indices) {
            if (bytes[i] != MAGIC[i]) return null
        }
        val version = bytes[MAGIC.size]
        if (version != FORMAT_VERSION) return null
        return when (bytes[MAGIC.size + 1].toInt()) {
            0 -> false
            1 -> true
            else -> null
        }
    }

    companion object {
        private const val FILE_NAME = "anox_deviceauth_binding.state"
        private val MAGIC = "ANXB".toByteArray(Charsets.US_ASCII)
        private const val FORMAT_VERSION: Byte = 1
    }
}
