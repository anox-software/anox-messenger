package com.anox.crypto

/**
 * Sealed class representing cryptographic errors
 * These errors do not expose sensitive information
 */
sealed class CryptoError(message: String) : Exception(message) {

    object InvalidInput : CryptoError("Invalid input parameters")
    object InvalidCiphertext : CryptoError("Invalid ciphertext")
    object InvalidSession : CryptoError("Invalid session")
    object StateCorrupted : CryptoError("Cryptographic state corrupted")
    object CryptoFailure : CryptoError("Cryptographic operation failed")
    object UnsupportedVersion : CryptoError("Unsupported version")
    object KeyGenerationFailed : CryptoError("Key generation failed")
    object SerializationFailed : CryptoError("Serialization failed")
    object DeserializationFailed : CryptoError("Deserialization failed")
    object SessionCreationFailed : CryptoError("Session creation failed")
    object AuthenticationFailed : CryptoError("Authentication failed (data corrupted or tampered)")
    object MissingStateKey : CryptoError("State-protection key is missing")
    object BufferTooSmall : CryptoError("Output buffer too small")

    data class UnknownError(val code: Int) : CryptoError("Unknown crypto error: $code")

    companion object {
        fun fromCode(code: Int): CryptoError {
            return when (code) {
                -1 -> InvalidInput
                -2 -> InvalidCiphertext
                -3 -> InvalidSession
                -4 -> SessionCreationFailed
                -5 -> SerializationFailed
                -6 -> DeserializationFailed
                -7 -> StateCorrupted
                -8 -> CryptoFailure
                -9 -> UnsupportedVersion
                -10 -> KeyGenerationFailed
                -11 -> BufferTooSmall
                else -> UnknownError(code)
            }
        }
    }
}