package com.anox.messenger.storage

import java.io.File
import java.io.FileOutputStream

/**
 * Minimal atomic-file-write helper shared by small local state files (Device Auth binding
 * marker, registration session state).
 *
 * Mirrors the write-temp-then-rename pattern already used by the existing protected-state
 * persistence in `CryptoBridge`, without depending on or modifying that class.
 */
object AtomicFileWriter {

    fun write(file: File, data: ByteArray) {
        val tmp = File(file.parentFile, file.name + ".tmp")
        FileOutputStream(tmp).use { out ->
            out.write(data)
            out.flush()
            out.fd.sync()
        }
        if (!tmp.renameTo(file)) {
            tmp.delete()
            throw IllegalStateException("Atomic rename failed for ${file.absolutePath}")
        }
    }
}
