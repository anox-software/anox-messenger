package com.anox.crypto

/**
 * Native methods for cryptographic operations
 * These methods are implemented in Rust and exposed via JNI
 */
object CryptoNative {
    init {
        System.loadLibrary("anox_crypto")
    }
    
    /**
     * Initialize the crypto library
     * @return true if successful, false otherwise
     */
    external fun cryptoInit(): Boolean
    
    /**
     * Create a new cryptographic identity
     * @return pointer to the native identity object
     */
    external fun cryptoCreateIdentity(): Long
    
    /**
     * Destroy an identity and securely clear its memory
     * @param identity pointer to the identity object
     */
    external fun cryptoDestroyIdentity(identity: Long)
    
    /**
     * Get the Curve25519 public key (32 bytes)
     * @param identity pointer to the identity object
     * @param out output buffer for the public key
     * @return number of bytes written, or negative error code
     */
    external fun cryptoGetCurve25519PublicKey(identity: Long, out: ByteArray): Int
    
    /**
     * Get the Ed25519 public key (32 bytes)
     * @param identity pointer to the identity object
     * @param out output buffer for the public key
     * @return number of bytes written, or negative error code
     */
    external fun cryptoGetEd25519PublicKey(identity: Long, out: ByteArray): Int
    
    /**
     * Generate one-time keys
     * @param identity pointer to the identity object
     * @param count number of one-time keys to generate
     * @return 0 if successful, negative error code otherwise
     */
    external fun cryptoGenerateOneTimeKeys(identity: Long, count: Int): Int
    
    /**
     * Get one-time keys count
     * @param identity pointer to the identity object
     * @return number of one-time keys, or negative error code
     */
    external fun cryptoOneTimeKeysCount(identity: Long): Int
    
    /**
     * Get one-time key by index
     * @param identity pointer to the identity object
     * @param index index of the one-time key
     * @param out output buffer for 32-byte one-time key
     * @return 0 on success, negative error code
     */
    external fun cryptoGetOneTimeKey(identity: Long, index: Int, out: ByteArray): Int
    
    /**
     * Serialize identity to encrypted format
     * @param identity pointer to the identity object
     * @param key encryption key (32 bytes)
     * @param out output buffer for serialized data
     * @return number of bytes written, or negative error code
     */
    external fun cryptoSerializeIdentity(identity: Long, key: ByteArray, out: ByteArray): Int
    
    /**
     * Deserialize identity from encrypted format
     * @param data serialized identity data
     * @param key decryption key (32 bytes)
     * @return pointer to the identity object, or 0 on error
     */
    external fun cryptoDeserializeIdentity(data: ByteArray, key: ByteArray): Long
    
    /**
     * Create outbound session
     * @param identity pointer to the identity object
     * @param theirIdentityKey their Curve25519 public key (32 bytes)
     * @param theirOneTimeKey their one-time key (32 bytes)
     * @return pointer to the session object, or 0 on error
     */
    external fun cryptoCreateOutboundSession(
        identity: Long,
        theirIdentityKey: ByteArray,
        theirOneTimeKey: ByteArray
    ): Long
    
    /**
     * Create inbound session and decrypt initial PreKey message
     * @param identity pointer to the identity object
     * @param theirIdentityKey their Curve25519 public key (32 bytes)
     * @param preKeyMessage PreKey message bytes
     * @param outPlaintext output buffer for decrypted plaintext
     * @param outSession output array for session pointer (single Long element)
     * @return plaintext length (negative error code on failure)
     */
    external fun cryptoCreateInboundSession(
        identity: Long,
        theirIdentityKey: ByteArray,
        preKeyMessage: ByteArray,
        outPlaintext: ByteArray,
        outSession: LongArray
    ): Int
    
    /**
     * Encrypt message
     * @param session pointer to the session object
     * @param plaintext message to encrypt
     * @param out output buffer for encrypted message
     * @param outLen output array for ciphertext length (single Int element)
     * @return message type (0=PreKey, 1=Normal) on success, negative error code on failure
     */
    external fun cryptoEncrypt(session: Long, plaintext: ByteArray, out: ByteArray, outLen: IntArray): Int
    
    /**
     * Decrypt message
     * @param session pointer to the session object
     * @param messageType message type (0=PreKey, 1=Normal)
     * @param ciphertext encrypted message
     * @param out output buffer for decrypted message
     * @return number of bytes written, or negative error code
     */
    external fun cryptoDecrypt(
        session: Long,
        messageType: Int,
        ciphertext: ByteArray,
        out: ByteArray
    ): Int
    
    /**
     * Destroy session and securely clear its memory
     * @param session pointer to the session object
     */
    external fun cryptoDestroySession(session: Long)
    
    /**
     * Serialize session to encrypted format
     * @param session pointer to the session object
     * @param key encryption key (32 bytes)
     * @param out output buffer for serialized data
     * @return number of bytes written, or negative error code
     */
    external fun cryptoSerializeSession(session: Long, key: ByteArray, out: ByteArray): Int
    
    /**
     * Deserialize session from encrypted format
     * @param data serialized session data
     * @param key decryption key (32 bytes)
     * @return pointer to the session object, or 0 on error
     */
    external fun cryptoDeserializeSession(data: ByteArray, key: ByteArray): Long
}