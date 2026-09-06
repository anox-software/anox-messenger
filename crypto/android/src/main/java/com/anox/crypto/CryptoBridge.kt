package com.anox.crypto

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.security.KeyStore
import java.util.concurrent.locks.ReentrantLock
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import kotlin.concurrent.withLock

/**
 * CryptoBridge - Main interface for cryptographic operations
 * Handles lifecycle, secure storage integration, and error translation
 *
 * IMPORTANT: This is the ONLY way Android code should interact with cryptography
 * Direct Rust calls are only allowed through this bridge
 */
class CryptoBridge private constructor(private val context: Context) {

    companion object {
        private const val TAG = "CryptoBridge"
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val MASTER_KEY_ALIAS = "anox_crypto_master_key"
        private const val MASTER_KEY_SIZE = 256

        @Volatile
        private var instance: CryptoBridge? = null

        /**
         * Get the singleton instance of CryptoBridge
         */
        fun getInstance(context: Context): CryptoBridge {
            return instance ?: synchronized(this) {
                instance ?: CryptoBridge(context.applicationContext).also {
                    it.initialize()
                }
            }
        }
    }

    /**
     * Initialize the crypto library and secure storage
     */
    private fun initialize() {
        try {
            // Initialize native crypto library
            if (!CryptoNative.cryptoInit()) {
                Log.e(TAG, "Failed to initialize native crypto library")
                return
            }

            // Initialize Android Keystore master key
            initializeMasterKey()

            Log.i(TAG, "CryptoBridge initialized successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize CryptoBridge", e)
        }
    }

    /**
     * Initialize the master key in Android Keystore
     * This key is used to wrap the AES-256-GCM state-protection key; it is not itself
     * the state key and it is non-extractable. The state key is randomly generated,
     * wrapped (encrypted) by the Keystore key, and stored in the app's private files.
     */
    private fun initializeMasterKey() {
        try {
            val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE)
            keyStore.load(null)

            if (!keyStore.containsAlias(MASTER_KEY_ALIAS)) {
                val keyGenerator = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES,
                    ANDROID_KEYSTORE
                )

                keyGenerator.init(
                    KeyGenParameterSpec.Builder(
                        MASTER_KEY_ALIAS,
                        KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
                    )
                        .setKeySize(MASTER_KEY_SIZE)
                        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                        .setUserAuthenticationRequired(false) // V1: no device lock requirement
                        .build()
                )

                keyGenerator.generateKey()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize master key", e)
        }
    }

    /**
     * Get the Keystore key (used only to wrap the state key; cannot be extracted)
     */
    private fun getMasterKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE)
        keyStore.load(null)
        return keyStore.getKey(MASTER_KEY_ALIAS, null) as SecretKey
    }

    /**
     * Thrown when the wrapped state-protection key is expected to exist but is missing.
     *
     * This MUST be distinguishable from corrupted ciphertext or first run so callers can
     * report [LocalStateStatus.MissingStateKey] rather than a generic
     * [CryptoError.DeserializationFailed].
     */
    class MissingStateKeyException(message: String) : IllegalStateException(message)

    /**
     * Get or create the 32-byte state-protection key.
     *
     * Allowed only for creation paths: first initialization and state write/serialization.
     * It MUST NOT be called from any read path where the state key is expected to already
     * exist, because creating a new key would decrypt as garbage and silently manufacture
     * a replacement [K_STATE].
     *
     * The state key is encrypted (wrapped) by the non-extractable Keystore master key
     * and persisted in the app’s private directory. This keeps the actual key bound to
     * the device while still allowing it to be passed to the Rust crypto layer.
     */
    internal fun getOrCreateStateKey(): ByteArray {
        val wrappedKeyFile = File(context.filesDir, "anox_state_key.enc")

        return if (wrappedKeyFile.exists()) {
            val wrapped = wrappedKeyFile.readBytes()
            unwrapStateKey(wrapped)
        } else {
            val stateKey = ByteArray(32).apply {
                val secureRandom = java.security.SecureRandom()
                secureRandom.nextBytes(this)
            }
            val wrapped = wrapStateKey(stateKey)
            writeFileAtomic(wrappedKeyFile, wrapped)
            stateKey
        }
    }

    /**
     * Read the existing wrapped state-protection key.
     *
     * Allowed only for existing-state read paths (deserialize / load). It NEVER creates a
     * new key; missing state key is a deterministic failure.
     */
    internal fun getExistingStateKey(): ByteArray {
        val wrappedKeyFile = File(context.filesDir, "anox_state_key.enc")

        if (!wrappedKeyFile.exists()) {
            throw MissingStateKeyException("Wrapped state-protection key is missing")
        }

        val wrapped = wrappedKeyFile.readBytes()
        return unwrapStateKey(wrapped)
    }

    /**
     * Encrypt the 32-byte state key with the non-extractable Keystore key.
     * Output: [12-byte nonce][ciphertext + 16-byte GCM tag]
     */
    private fun wrapStateKey(stateKey: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.ENCRYPT_MODE, getMasterKey())
        }
        val iv = cipher.iv // 12 bytes generated by Cipher for GCM
        val ciphertext = cipher.doFinal(stateKey)
        return iv + ciphertext
    }

    /**
     * Decrypt the wrapped state key with the non-extractable Keystore key.
     * Input: [12-byte nonce][ciphertext + 16-byte GCM tag]
     */
    private fun unwrapStateKey(wrapped: ByteArray): ByteArray {
        if (wrapped.size < 28) { // 12 nonce + 16 tag minimum
            throw IllegalStateException("Wrapped state key is too short")
        }
        val iv = wrapped.copyOfRange(0, 12)
        val ciphertext = wrapped.copyOfRange(12, wrapped.size)
        val spec = GCMParameterSpec(128, iv)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.DECRYPT_MODE, getMasterKey(), spec)
        }
        return cipher.doFinal(ciphertext)
    }

    /**
     * Create a new cryptographic identity.
     * The identity keys are generated in Rust and stored securely.
     */
    fun createIdentity(): CryptoResult<Long> {
        return try {
            cryptoLock.withLock {
                val identityPtr = CryptoNative.cryptoCreateIdentity()
                if (identityPtr == 0L) {
                    CryptoResult.failure(CryptoError.KeyGenerationFailed)
                } else {
                    CryptoResult.success(identityPtr)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create identity", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Destroy an identity and securely clear its memory.
     */
    fun destroyIdentity(identity: Long): CryptoResult<Unit> {
        return try {
            cryptoLock.withLock {
                CryptoNative.cryptoDestroyIdentity(identity)
                CryptoResult.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to destroy identity", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Get the Curve25519 public key (32 bytes)
     */
    fun getCurve25519PublicKey(identity: Long): CryptoResult<ByteArray> {
        return try {
            cryptoLock.withLock {
                val out = ByteArray(32)
                val result = CryptoNative.cryptoGetCurve25519PublicKey(identity, out)
                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    CryptoResult.success(out)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get Curve25519 public key", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Get the Ed25519 public key (32 bytes)
     */
    fun getEd25519PublicKey(identity: Long): CryptoResult<ByteArray> {
        return try {
            cryptoLock.withLock {
                val out = ByteArray(32)
                val result = CryptoNative.cryptoGetEd25519PublicKey(identity, out)
                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    CryptoResult.success(out)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get Ed25519 public key", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Generate one-time keys for session establishment
     */
    fun generateOneTimeKeys(identity: Long, count: Int): CryptoResult<Unit> {
        return try {
            cryptoLock.withLock {
                val result = CryptoNative.cryptoGenerateOneTimeKeys(identity, count)
                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    CryptoResult.success(Unit)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to generate one-time keys", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Get one-time key by index (for test/debug, not for normal UI use)
     */
    fun getOneTimeKey(identity: Long, index: Int): CryptoResult<ByteArray> {
        return try {
            cryptoLock.withLock {
                val out = ByteArray(32)
                val result = CryptoNative.cryptoGetOneTimeKey(identity, index, out)
                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    CryptoResult.success(out)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get one-time key", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Get the number of stored one-time keys
     */
    fun oneTimeKeysCount(identity: Long): CryptoResult<Int> {
        return try {
            cryptoLock.withLock {
                val result = CryptoNative.cryptoOneTimeKeysCount(identity)
                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    CryptoResult.success(result)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get one-time keys count", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Serialize identity with encryption.
     * The identity is encrypted using the master key before storage.
     */
    fun serializeIdentity(identity: Long): CryptoResult<ByteArray> {
        return try {
            cryptoLock.withLock {
                val key = getOrCreateStateKey()

                // Calculate required buffer size (estimate)
                val out = ByteArray(4096) // Conservative estimate
                val result = CryptoNative.cryptoSerializeIdentity(identity, key, out)

                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    // Trim to actual size
                    val actualData = out.copyOfRange(0, result)
                    CryptoResult.success(actualData)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to serialize identity", e)
            CryptoResult.failure(CryptoError.SerializationFailed)
        }
    }

    /**
     * Deserialize identity from encrypted format.
     *
     * Uses [getExistingStateKey] because loading an existing identity must never create a
     * replacement state key.
     */
    fun deserializeIdentity(data: ByteArray): CryptoResult<Long> {
        return try {
            cryptoLock.withLock {
                val key = getExistingStateKey()

                val identityPtr = CryptoNative.cryptoDeserializeIdentity(data, key)
                if (identityPtr == 0L) {
                    CryptoResult.failure(CryptoError.DeserializationFailed)
                } else {
                    CryptoResult.success(identityPtr)
                }
            }
        } catch (e: MissingStateKeyException) {
            Log.w(TAG, "Identity exists but state key is missing", e)
            CryptoResult.failure(CryptoError.MissingStateKey)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to deserialize identity", e)
            CryptoResult.failure(CryptoError.DeserializationFailed)
        }
    }

    /**
     * Create outbound session (for initiating communication)
     */
    fun createOutboundSession(
        identity: Long,
        theirIdentityKey: ByteArray,
        theirOneTimeKey: ByteArray
    ): CryptoResult<Long> {
        return try {
            cryptoLock.withLock {
                if (theirIdentityKey.size != 32 || theirOneTimeKey.size != 32) {
                    return CryptoResult.failure(CryptoError.InvalidInput)
                }

                val sessionPtr = CryptoNative.cryptoCreateOutboundSession(
                    identity,
                    theirIdentityKey,
                    theirOneTimeKey
                )

                if (sessionPtr == 0L) {
                    CryptoResult.failure(CryptoError.CryptoFailure)
                } else {
                    CryptoResult.success(sessionPtr)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create outbound session", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Create inbound session and decrypt initial PreKey message
     * Returns a pair of (session, plaintext) where plaintext is the first decrypted message
     */
    fun createInboundSession(
        identity: Long,
        theirIdentityKey: ByteArray,
        preKeyMessage: ByteArray
    ): CryptoResult<Pair<Long, ByteArray>> {
        return try {
            cryptoLock.withLock {
                if (theirIdentityKey.size != 32) {
                    return CryptoResult.failure(CryptoError.InvalidInput)
                }

                val outPlaintext = ByteArray(preKeyMessage.size + 256) // Extra space for plaintext
                val outSession = LongArray(1)

                val result = CryptoNative.cryptoCreateInboundSession(
                    identity,
                    theirIdentityKey,
                    preKeyMessage,
                    outPlaintext,
                    outSession
                )

                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    val sessionPtr = outSession[0]
                    val plaintext = outPlaintext.copyOfRange(0, result)
                    CryptoResult.success(Pair(sessionPtr, plaintext))
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create inbound session", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Encrypt a message
     * Returns a pair of (messageType, ciphertext) where messageType is 0=PreKey, 1=Normal
     */
    fun encrypt(session: Long, plaintext: ByteArray): CryptoResult<Pair<Int, ByteArray>> {
        return try {
            cryptoLock.withLock {
                val out = ByteArray(plaintext.size + 512) // Extra space for encryption overhead
                val outLen = IntArray(1)
                val result = CryptoNative.cryptoEncrypt(session, plaintext, out, outLen)

                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    val messageType = result
                    val ciphertextLen = outLen[0]
                    val ciphertext = out.copyOfRange(0, ciphertextLen)
                    CryptoResult.success(Pair(messageType, ciphertext))
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to encrypt message", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Decrypt a message
     * @param messageType 0=PreKey, 1=Normal
     */
    fun decrypt(session: Long, messageType: Int, ciphertext: ByteArray): CryptoResult<ByteArray> {
        return try {
            cryptoLock.withLock {
                val out = ByteArray(ciphertext.size + 256) // Extra space for decryption overhead
                val result = CryptoNative.cryptoDecrypt(session, messageType, ciphertext, out)

                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    val actualData = out.copyOfRange(0, result)
                    CryptoResult.success(actualData)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to decrypt message", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Destroy session and securely clear its memory
     */
    fun destroySession(session: Long): CryptoResult<Unit> {
        return try {
            cryptoLock.withLock {
                CryptoNative.cryptoDestroySession(session)
                CryptoResult.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to destroy session", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Serialize session with encryption
     */
    fun serializeSession(session: Long): CryptoResult<ByteArray> {
        return try {
            cryptoLock.withLock {
                val key = getOrCreateStateKey()

                val out = ByteArray(4096) // Conservative estimate
                val result = CryptoNative.cryptoSerializeSession(session, key, out)

                if (result < 0) {
                    CryptoResult.failure(CryptoError.fromCode(result))
                } else {
                    val actualData = out.copyOfRange(0, result)
                    CryptoResult.success(actualData)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to serialize session", e)
            CryptoResult.failure(CryptoError.SerializationFailed)
        }
    }

    /**
     * Deserialize session from encrypted format.
     *
     * Uses [getExistingStateKey] because loading an existing session must never create a
     * replacement state key.
     */
    fun deserializeSession(data: ByteArray): CryptoResult<Long> {
        return try {
            cryptoLock.withLock {
                val key = getExistingStateKey()

                val sessionPtr = CryptoNative.cryptoDeserializeSession(data, key)
                if (sessionPtr == 0L) {
                    CryptoResult.failure(CryptoError.DeserializationFailed)
                } else {
                    CryptoResult.success(sessionPtr)
                }
            }
        } catch (e: MissingStateKeyException) {
            Log.w(TAG, "Session exists but state key is missing", e)
            CryptoResult.failure(CryptoError.MissingStateKey)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to deserialize session", e)
            CryptoResult.failure(CryptoError.DeserializationFailed)
        }
    }

    /**
     * Securely destroy all cryptographic state
     * This should be called when the app is uninstalled or on explicit user request
     */
    fun destroyAllCrypto(): CryptoResult<Unit> {
        return wipeLocalCrypto()
    }

    // Thread-safe lock for all state-changing crypto operations.
    private val cryptoLock = ReentrantLock()

    /**
     * Status of the local cryptographic identity state.
     */
    sealed class LocalStateStatus {
        /** No local crypto state exists; legitimate first install / explicit wipe. */
        object FirstRun : LocalStateStatus()
        /** A usable identity could be loaded. */
        data class IdentityReady(val identity: Long) : LocalStateStatus()
        /** State file exists and state key exists, but the protected identity could not be authenticated/decrypted. */
        data class CorruptedIdentityState(val reason: String) : LocalStateStatus()
        /** Identity file exists but the Keystore-wrapped state key is missing. */
        object MissingStateKey : LocalStateStatus()
        /** State key exists but no identity file exists. */
        object WipedState : LocalStateStatus()
        /** The Keystore wrapping key could not be retrieved or is missing. */
        object MissingKeystore : LocalStateStatus()
    }

    /**
     * Inspect the local crypto state without creating or modifying anything.
     */
    fun getLocalStateStatus(identityName: String = "anox_identity.enc"): LocalStateStatus {
        return try {
            cryptoLock.withLock {
                // Attempting to unwrap the state key also validates the Keystore key exists.
                val stateKeyFile = File(context.filesDir, "anox_state_key.enc")
                val identityFile = File(context.filesDir, identityName)

                if (!identityFile.exists() && !stateKeyFile.exists()) {
                    return LocalStateStatus.FirstRun
                }

                if (stateKeyFile.exists() && !identityFile.exists()) {
                    return LocalStateStatus.WipedState
                }

                if (!stateKeyFile.exists() && identityFile.exists()) {
                    return LocalStateStatus.MissingStateKey
                }

                val stateKey = getExistingStateKey()
                val data = identityFile.readBytes()
                when (val result = deserializeIdentity(data)) {
                    is CryptoResult.Success -> LocalStateStatus.IdentityReady(result.value)
                    is CryptoResult.Failure -> LocalStateStatus.CorruptedIdentityState(result.error.message ?: "unknown")
                }
            }
        } catch (e: MissingStateKeyException) {
            LocalStateStatus.MissingStateKey
        } catch (e: Exception) {
            if (isKeystoreOrUnwrapFailure(e)) {
                LocalStateStatus.MissingKeystore
            } else {
                LocalStateStatus.CorruptedIdentityState(e.message ?: "unknown")
            }
        }
    }

    /**
     * Create a new E2EE identity and persist it atomically as the canonical local identity.
     * Must only be called when no valid identity already exists.
     */
    fun createAndPersistFirstIdentity(identityName: String = "anox_identity.enc"): CryptoResult<Long> {
        return try {
            cryptoLock.withLock {
                // Ensure we are not silently rotating an existing identity.
                val identityFile = File(context.filesDir, identityName)
                if (identityFile.exists()) {
                    return CryptoResult.failure(CryptoError.InvalidInput)
                }
                val identity = createIdentity().getOrThrow()
                val data = serializeIdentity(identity).getOrThrow()
                writeFileAtomic(identityFile, data)
                CryptoResult.success(identity)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create and persist first identity", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Persist a protected identity to a named file using an atomic write.
     */
    fun saveIdentity(identity: Long, name: String = "anox_identity.enc"): CryptoResult<Unit> {
        return try {
            cryptoLock.withLock {
                val data = serializeIdentity(identity).getOrThrow()
                writeFileAtomic(File(context.filesDir, name), data)
                CryptoResult.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to save identity", e)
            CryptoResult.failure(CryptoError.SerializationFailed)
        }
    }

    /**
     * Load a protected identity from a named file.
     */
    fun loadIdentity(name: String = "anox_identity.enc"): CryptoResult<Long> {
        return try {
            cryptoLock.withLock {
                val file = File(context.filesDir, name)
                if (!file.exists()) {
                    return CryptoResult.failure(CryptoError.DeserializationFailed)
                }
                val data = file.readBytes()
                deserializeIdentity(data)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load identity", e)
            CryptoResult.failure(CryptoError.DeserializationFailed)
        }
    }

    /**
     * Persist a protected session to a named file using an atomic write.
     */
    fun saveSession(session: Long, name: String = "anox_session.enc"): CryptoResult<Unit> {
        return try {
            cryptoLock.withLock {
                val data = serializeSession(session).getOrThrow()
                writeFileAtomic(File(context.filesDir, name), data)
                CryptoResult.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to save session", e)
            CryptoResult.failure(CryptoError.SerializationFailed)
        }
    }

    /**
     * Load a protected session from a named file.
     */
    fun loadSession(name: String = "anox_session.enc"): CryptoResult<Long> {
        return try {
            cryptoLock.withLock {
                val file = File(context.filesDir, name)
                if (!file.exists()) {
                    return CryptoResult.failure(CryptoError.DeserializationFailed)
                }
                val data = file.readBytes()
                deserializeSession(data)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load session", e)
            CryptoResult.failure(CryptoError.DeserializationFailed)
        }
    }

    /**
     * Cryptographically wipe local crypto state.
     * Removes Keystore wrapping key, wrapped state key, and protected identity/session files.
     */
    fun wipeLocalCrypto(): CryptoResult<Unit> {
        return try {
            cryptoLock.withLock {
                val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE)
                keyStore.load(null)
                keyStore.deleteEntry(MASTER_KEY_ALIAS)

                File(context.filesDir, "anox_state_key.enc").delete()
                File(context.filesDir, "anox_identity.enc").delete()
                File(context.filesDir, "anox_session.enc").delete()

                CryptoResult.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to wipe local crypto", e)
            CryptoResult.failure(CryptoError.CryptoFailure)
        }
    }

    /**
     * Fail-closed classifier for Keystore/unwrap failures.
     *
     * Does NOT reference [android.security.KeyStoreException] directly, because that class
     * only exists on API 33+. On API 26–32 a direct reference would cause a class-loading
     * crash. Instead the class name is checked by string, which is safe on all supported
     * API levels.
     */
    private fun isKeystoreOrUnwrapFailure(e: Throwable): Boolean {
        return isThrowableNamed(e, "android.security.KeyStoreException") ||
            isThrowableNamed(e, "javax.crypto.AEADBadTagException") ||
            isThrowableNamed(e, "java.security.UnrecoverableKeyException")
    }

    private fun isThrowableNamed(error: Throwable?, className: String): Boolean {
        var current: Throwable? = error
        while (current != null) {
            if (current.javaClass.name == className) return true
            current = current.cause
        }
        return false
    }

    /**
     * Atomically write bytes to a file.
     * Writes to a temporary file, fsyncs, then renames over the target.
     */
    private fun writeFileAtomic(file: File, data: ByteArray) {
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
