package com.anox.messenger.security.deviceauth

import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyInfo
import android.security.keystore.KeyPermanentlyInvalidatedException
import android.security.keystore.KeyProperties
import com.nimbusds.jose.JWSSigner
import com.nimbusds.jose.crypto.ECDSASigner
import com.nimbusds.jose.jwk.Curve
import com.nimbusds.jose.jwk.ECKey
import java.security.KeyFactory
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.PrivateKey
import java.security.UnrecoverableKeyException
import java.security.interfaces.ECPublicKey
import java.security.spec.ECGenParameterSpec

/**
 * Android Keystore backed [DeviceAuthKeyManager] for B-002 Device Authentication.
 *
 * Key properties:
 *  - P-256 (secp256r1) / ES256;
 *  - generated inside the Android Keystore, so the private key is non-exportable;
 *  - StrongBox requested when the platform supports it, TEE otherwise;
 *  - no per-use user authentication (B-002 forbids a per-sign biometric requirement);
 *  - completely separate keystore alias from the `K_STATE` state-protection key and from
 *    the E2EE identity, which is not stored in the Android Keystore at all.
 */
class AndroidKeystoreDeviceAuthKeyManager(
    private val bindingStore: DeviceAuthBindingStore,
    private val keyAlias: String = DEFAULT_KEY_ALIAS
) : DeviceAuthKeyManager {

    private val keyStore: KeyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }

    override fun status(): DeviceAuthKeyStatus {
        val privateKey = loadPrivateKeyOrNull()
        return DeviceAuthKeyStateResolver.resolve(
            keyPresent = privateKey != null,
            hardwareSecurityLevel = privateKey?.let { resolveHardwareSecurityLevel(it) },
            isBound = bindingStore.isBound(),
            isArmed = bindingStore.isArmed()
        )
    }

    override fun createKeyIfAbsent(): DeviceAuthKeyStatus {
        val current = status()
        if (current is DeviceAuthKeyStatus.Present) return current

        // Throws on terminal key loss; never silently replaces a bound key.
        DeviceAuthKeyStateResolver.requireCreationAllowed(current)

        generateKey()
        return status()
    }

    override fun hardwareSecurityLevel(): HardwareSecurityLevel? =
        loadPrivateKeyOrNull()?.let { resolveHardwareSecurityLevel(it) }

    override fun isProductionEligible(): Boolean =
        hardwareSecurityLevel()?.isProductionEligible == true

    override fun signer(): DeviceAuthSigner {
        val privateKey = loadPrivateKeyOrNull() ?: throw DeviceAuthTerminalStateException(
            "No usable Device Auth key is available. Current status: ${status()}"
        )
        val certificate = keyStore.getCertificate(keyAlias)
            ?: throw DeviceAuthTerminalStateException(
                "Device Auth key entry has no certificate; public key unavailable."
            )
        val publicKey = certificate.publicKey as? ECPublicKey
            ?: throw DeviceAuthTerminalStateException("Device Auth key is not an EC key.")

        return KeystoreDeviceAuthSigner(privateKey, publicKey)
    }

    override fun deleteKeyDestructively() {
        if (keyStore.containsAlias(keyAlias)) {
            keyStore.deleteEntry(keyAlias)
        }
    }

    // ---------------------------------------------------------------------------------
    // internals
    // ---------------------------------------------------------------------------------

    /**
     * Loads the private key handle, or null when the entry is absent or permanently
     * invalidated. A permanently invalidated key is treated exactly like an absent key
     * here; [status] then decides whether that is first-run or terminal loss.
     */
    private fun loadPrivateKeyOrNull(): PrivateKey? = try {
        if (!keyStore.containsAlias(keyAlias)) {
            null
        } else {
            keyStore.getKey(keyAlias, null) as? PrivateKey
        }
    } catch (e: KeyPermanentlyInvalidatedException) {
        null
    } catch (e: UnrecoverableKeyException) {
        null
    }

    private fun generateKey() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            // Prefer StrongBox. Any failure here (including StrongBoxUnavailableException)
            // falls back to TEE, which B-002 explicitly accepts for production.
            try {
                generateKey(strongBoxBacked = true)
                return
            } catch (e: Exception) {
                deleteKeyDestructively()
            }
        }
        generateKey(strongBoxBacked = false)
    }

    private fun generateKey(strongBoxBacked: Boolean) {
        val builder = KeyGenParameterSpec.Builder(
            keyAlias,
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        )
            .setAlgorithmParameterSpec(ECGenParameterSpec(EC_CURVE_NAME))
            .setDigests(KeyProperties.DIGEST_SHA256)
            // B-002: no mandatory per-use biometric / credential prompt.
            .setUserAuthenticationRequired(false)

        if (strongBoxBacked && Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            builder.setIsStrongBoxBacked(true)
        }

        val generator = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_EC,
            ANDROID_KEYSTORE
        )
        generator.initialize(builder.build())
        generator.generateKeyPair()
    }

    /**
     * Resolves the hardware backing level using only what the platform can actually prove.
     *
     * On API 31+ the exact security level is reported by the platform. On API 26..30 the
     * platform only exposes a boolean "inside secure hardware", so a hardware-backed key is
     * conservatively reported as [HardwareSecurityLevel.TRUSTED_EXECUTION_ENVIRONMENT] even
     * if it was in fact generated in StrongBox. StrongBox is never claimed without proof.
     * Both levels are production eligible, so this conservatism costs no functionality.
     */
    private fun resolveHardwareSecurityLevel(privateKey: PrivateKey): HardwareSecurityLevel {
        val keyInfo = try {
            KeyFactory.getInstance(privateKey.algorithm, ANDROID_KEYSTORE)
                .getKeySpec(privateKey, KeyInfo::class.java)
        } catch (e: Exception) {
            return HardwareSecurityLevel.UNKNOWN
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            return when (keyInfo.securityLevel) {
                KeyProperties.SECURITY_LEVEL_STRONGBOX ->
                    HardwareSecurityLevel.STRONGBOX
                KeyProperties.SECURITY_LEVEL_TRUSTED_ENVIRONMENT ->
                    HardwareSecurityLevel.TRUSTED_EXECUTION_ENVIRONMENT
                KeyProperties.SECURITY_LEVEL_SOFTWARE ->
                    HardwareSecurityLevel.SOFTWARE
                else ->
                    HardwareSecurityLevel.UNKNOWN
            }
        }

        @Suppress("DEPRECATION")
        return if (keyInfo.isInsideSecureHardware) {
            HardwareSecurityLevel.TRUSTED_EXECUTION_ENVIRONMENT
        } else {
            HardwareSecurityLevel.SOFTWARE
        }
    }

    /**
     * [DeviceAuthSigner] over a non-extractable Keystore private key handle.
     *
     * Uses Nimbus `ECDSASigner(PrivateKey, Curve)`, the constructor explicitly intended for
     * EC keys held in a store that does not expose private key parameters. The DER-to-JOSE
     * signature transcoding required by RFC7518 ES256 is performed by the library.
     */
    private class KeystoreDeviceAuthSigner(
        private val privateKey: PrivateKey,
        publicKey: ECPublicKey
    ) : DeviceAuthSigner {

        override val publicJwk: ECKey =
            ECKey.Builder(Curve.P_256, publicKey).build().toPublicJWK()

        override fun jwsSigner(): JWSSigner = ECDSASigner(privateKey, Curve.P_256)
    }

    companion object {
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val EC_CURVE_NAME = "secp256r1"

        /**
         * Dedicated alias. Deliberately distinct from any `K_STATE` alias so that the
         * Device Auth key and the local state-protection key remain separate per
         * Security Invariant 24.
         */
        const val DEFAULT_KEY_ALIAS: String = "anox.deviceauth.p256.v1"
    }
}
