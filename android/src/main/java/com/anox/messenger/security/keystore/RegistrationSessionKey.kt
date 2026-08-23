package com.anox.messenger.security.keystore

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Purpose-specific Android Keystore AES-256-GCM key for B-003 registration session secrets.
 *
 * This key is:
 *  - non-exportable (generated inside the Android Keystore);
 *  - distinct from `K_STATE` (CryptoBridge), from the B-002 Device Auth P-256 key, and from
 *    any E2EE identity material;
 *  - used only to protect the temporary 30-minute registration session, never for long-lived
 *    account state or for server-side material;
 *  - AES-256 in GCM with a fresh 96-bit IV for every encryption.
 *
 * The on-disk envelope is: `[version (1 byte)][iv (12 bytes)][ciphertext + 128-bit GCM tag]`.
 */
class RegistrationSessionKey(
    private val alias: String = DEFAULT_ALIAS
) {

    private val keyStore: KeyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }

    /** Encrypts [plaintext] with a fresh IV. Returns the versioned envelope. */
    fun encrypt(plaintext: ByteArray): ByteArray {
        val cipher = Cipher.getInstance(TRANSFORMATION).apply {
            init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        }
        val iv = cipher.iv // 12 bytes for GCM
        val ciphertext = cipher.doFinal(plaintext)
        return byteArrayOf(ENVELOPE_VERSION) + iv + ciphertext
    }

    /**
     * Decrypts an envelope produced by [encrypt].
     *
     * Any authentication failure, version mismatch, or malformed input throws a
     * [javax.crypto.AEADBadTagException] or [IllegalStateException] and MUST be treated as a
     * fail-closed security event by the caller.
     */
    fun decrypt(envelope: ByteArray): ByteArray {
        if (envelope.isEmpty() || envelope[0] != ENVELOPE_VERSION) {
            throw IllegalStateException("unsupported registration session envelope version")
        }
        if (envelope.size < 13) { // 1 byte version + 12 byte IV + at least a tag
            throw IllegalStateException("registration session envelope too short")
        }
        val iv = envelope.copyOfRange(1, 13)
        val ciphertext = envelope.copyOfRange(13, envelope.size)
        val spec = GCMParameterSpec(128, iv)
        val cipher = Cipher.getInstance(TRANSFORMATION).apply {
            init(Cipher.DECRYPT_MODE, getOrCreateKey(), spec)
        }
        return cipher.doFinal(ciphertext)
    }

    private fun getOrCreateKey(): SecretKey {
        val existing = keyStore.getEntry(alias, null)
        if (existing is KeyStore.SecretKeyEntry) {
            return existing.secretKey
        }
        return generateKey()
    }

    private fun generateKey(): SecretKey {
        val generator = KeyGenerator.getInstance(KEY_ALGORITHM, ANDROID_KEYSTORE)
        val spec = KeyGenParameterSpec.Builder(
            alias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .setUserAuthenticationRequired(false) // B-003 has no per-use biometric requirement.
            .build()
        generator.init(spec)
        return generator.generateKey()
    }

    companion object {
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val KEY_ALGORITHM = "AES"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val ENVELOPE_VERSION: Byte = 1

        /** Deliberately distinct from any `K_STATE` or Device Auth alias. */
        const val DEFAULT_ALIAS: String = "anox.b003.session.v1"
    }
}
