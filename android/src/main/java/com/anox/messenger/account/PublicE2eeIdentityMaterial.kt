package com.anox.messenger.account

/**
 * The E2EE material that is public by design and therefore may cross the backend boundary as
 * part of registration.
 *
 * This never carries private key material, session state or ratchet state (Security Invariant
 * 4). It is produced from the existing, unmodified `crypto/rust` / `CryptoBridge` foundation via
 * [LocalE2eeIdentityStep]; this class only shapes the public bytes for the registration API
 * boundary.
 */
data class PublicE2eeIdentityMaterial(
    val curve25519PublicKey: ByteArray,
    val ed25519PublicKey: ByteArray,
    val oneTimeKeys: List<ByteArray>
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is PublicE2eeIdentityMaterial) return false
        return curve25519PublicKey.contentEquals(other.curve25519PublicKey) &&
            ed25519PublicKey.contentEquals(other.ed25519PublicKey) &&
            oneTimeKeys.size == other.oneTimeKeys.size &&
            oneTimeKeys.zip(other.oneTimeKeys).all { (a, b) -> a.contentEquals(b) }
    }

    override fun hashCode(): Int {
        var result = curve25519PublicKey.contentHashCode()
        result = 31 * result + ed25519PublicKey.contentHashCode()
        result = 31 * result + oneTimeKeys.sumOf { it.contentHashCode() }
        return result
    }
}
