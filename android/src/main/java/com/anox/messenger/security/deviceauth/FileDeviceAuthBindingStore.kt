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
 *    plaintext or license plaintext (it stores a small flags marker, nothing else);
 *  - lives under [Context.getNoBackupFilesDir], which Android excludes from both classic backup
 *    and device-to-device transfer regardless of `dataExtractionRules`, in addition to this
 *    app's existing `allowBackup="false"` / `dataExtractionRules` exclusion of the entire
 *    private storage root;
 *  - fails closed on malformed/corrupt state: an unreadable or corrupt marker file is reported
 *    as both **bound** and **armed**, not unbound. Treating ambiguous state as bound/armed is
 *    the safe direction here, because these markers only ever block new-key creation
 *    ([DeviceAuthKeyStateResolver.requireCreationAllowed]); they can never cause a silent Device
 *    Auth key replacement for what might in fact be an already-committed installation.
 */
class FileDeviceAuthBindingStore(context: Context) : DeviceAuthBindingStore {

    private val file: File = File(context.noBackupFilesDir, FILE_NAME)

    @Synchronized
    override fun isBound(): Boolean = readFlags().first

    @Synchronized
    override fun isArmed(): Boolean = readFlags().second

    private fun readFlags(): Pair<Boolean, Boolean> {
        if (!file.exists()) return false to false
        val bytes = try {
            file.readBytes()
        } catch (e: Exception) {
            return true to true // fail closed: unreadable state is treated as bound + armed.
        }
        return parse(bytes) ?: (true to true) // fail closed: unparseable content is treated as bound + armed.
    }

    @Synchronized
    override fun markArmed() {
        val (bound, _) = readFlags()
        write(bound = bound, armed = true)
    }

    @Synchronized
    override fun markBound() {
        write(bound = true, armed = true)
    }

    @Synchronized
    override fun clearBinding() {
        write(bound = false, armed = false)
    }

    private fun write(bound: Boolean, armed: Boolean) {
        val flags: Int = (if (bound) FLAG_BOUND.toInt() else 0) or (if (armed) FLAG_ARMED.toInt() else 0)
        val payload = MAGIC + byteArrayOf(FORMAT_VERSION, flags.toByte())
        AtomicFileWriter.write(file, payload)
    }

    /** Returns the stored flags, or null if [bytes] is not a recognised marker file. */
    private fun parse(bytes: ByteArray): Pair<Boolean, Boolean>? {
        if (bytes.size != MAGIC.size + 2) return null
        for (i in MAGIC.indices) {
            if (bytes[i] != MAGIC[i]) return null
        }
        val version = bytes[MAGIC.size]
        val flags = bytes[MAGIC.size + 1].toInt()
        return when (version) {
            FORMAT_VERSION -> {
                val bound = (flags and FLAG_BOUND.toInt()) != 0
                val armed = (flags and FLAG_ARMED.toInt()) != 0
                bound to armed
            }
            FORMAT_VERSION_1 -> {
                // Version 1 only stored a single bound flag in the second byte.
                val bound = flags == 1
                bound to false
            }
            else -> null
        }
    }

    companion object {
        private const val FILE_NAME = "anox_deviceauth_binding.state"
        private val MAGIC = "ANXB".toByteArray(Charsets.US_ASCII)
        private const val FORMAT_VERSION_1: Byte = 1
        private const val FORMAT_VERSION: Byte = 2
        private const val FLAG_BOUND: Byte = 0x01
        private const val FLAG_ARMED: Byte = 0x02
    }
}
