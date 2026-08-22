package com.anox.messenger.security.deviceauth

import androidx.test.ext.junit.runners.AndroidJUnit4
import com.nimbusds.jose.jwk.Curve
import com.nimbusds.jwt.SignedJWT
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.security.KeyStore
import java.security.PrivateKey

/**
 * Instrumentation tests for the real Android Keystore Device Auth key.
 *
 * NOTE ON HARDWARE CLAIMS: these tests deliberately do NOT assert StrongBox or TEE backing.
 * An emulator or CI device cannot prove a physical secure element, so the hardware security
 * level is only checked for internal consistency. Physical StrongBox/TEE behaviour on a
 * supported GrapheneOS device remains UNVERIFIED by this suite.
 */
@RunWith(AndroidJUnit4::class)
class AndroidKeystoreDeviceAuthKeyManagerTest {

    private val alias = "anox.deviceauth.test.${System.nanoTime()}"

    private lateinit var bindingStore: InMemoryDeviceAuthBindingStore
    private lateinit var manager: AndroidKeystoreDeviceAuthKeyManager

    @Before
    fun setUp() {
        bindingStore = InMemoryDeviceAuthBindingStore()
        manager = AndroidKeystoreDeviceAuthKeyManager(bindingStore, alias)
        manager.deleteKeyDestructively()
    }

    @After
    fun tearDown() {
        manager.deleteKeyDestructively()
    }

    @Test
    fun firstRunCreatesP256Key() {
        assertSame(DeviceAuthKeyStatus.AbsentNotBound, manager.status())

        val status = manager.createKeyIfAbsent()
        assertTrue(status is DeviceAuthKeyStatus.Present)

        val publicJwk = manager.signer().publicJwk
        assertEquals(Curve.P_256, publicJwk.curve)
        assertEquals("EC", publicJwk.keyType.value)
    }

    @Test
    fun createKeyIfAbsentIsIdempotent() {
        manager.createKeyIfAbsent()
        val first = manager.signer().jwkThumbprint()

        manager.createKeyIfAbsent()
        val second = manager.signer().jwkThumbprint()

        assertEquals("existing key must be reused, not replaced", first, second)
    }

    @Test
    fun privateKeyIsNotExportable() {
        manager.createKeyIfAbsent()

        val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val privateKey = keyStore.getKey(alias, null) as PrivateKey

        assertNull(
            "Android Keystore private keys must not expose encoded material",
            privateKey.encoded
        )

        val publicJwk = manager.signer().publicJwk
        assertFalse(publicJwk.isPrivate)
        assertNull(publicJwk.toECPrivateKey())
        assertFalse(publicJwk.toJSONString().contains("\"d\""))
    }

    @Test
    fun keystoreBackedProofVerifiesEndToEnd() {
        manager.createKeyIfAbsent()
        val signer = manager.signer()

        val method = "POST"
        val uri = "https://api.example.test/v1/device/token"
        val token = DeviceAuthAccessTokenGenerator().newOpaqueToken()
        val nonce = "server-nonce"

        val proof = DpopProofFactory(signer).createProof(
            httpMethod = method,
            targetUri = uri,
            accessToken = token,
            nonce = nonce
        )

        val result = DpopProofVerifier().verify(
            proof = proof,
            httpMethod = method,
            targetUri = uri,
            expectedJwkThumbprint = signer.jwkThumbprint(),
            accessToken = token,
            expectedNonce = nonce
        )

        assertTrue("Keystore-signed DPoP proof must verify: $result", result.isValid)
    }

    @Test
    fun keystoreProofIsEs256WithPublicJwkHeader() {
        manager.createKeyIfAbsent()
        val signer = manager.signer()

        val proof = DpopProofFactory(signer)
            .createProof("GET", "https://api.example.test/v1/resource")
        val header = SignedJWT.parse(proof).header

        assertEquals("ES256", header.algorithm.name)
        assertEquals("dpop+jwt", header.type.type)
        assertNotNull(header.getJWK())
        assertFalse(header.getJWK().isPrivate)
    }

    @Test
    fun wrongKeyIsRejected() {
        manager.createKeyIfAbsent()
        val signer = manager.signer()

        val otherAlias = "$alias.other"
        val otherManager = AndroidKeystoreDeviceAuthKeyManager(
            InMemoryDeviceAuthBindingStore(),
            otherAlias
        )
        try {
            otherManager.createKeyIfAbsent()

            val method = "POST"
            val uri = "https://api.example.test/v1/resource"
            val proof = DpopProofFactory(otherManager.signer()).createProof(method, uri)

            val result = DpopProofVerifier().verify(
                proof = proof,
                httpMethod = method,
                targetUri = uri,
                expectedJwkThumbprint = signer.jwkThumbprint()
            )

            assertEquals(
                DpopVerificationResult.Invalid(DpopRejectionReason.KEY_BINDING_MISMATCH),
                result
            )
        } finally {
            otherManager.deleteKeyDestructively()
        }
    }

    @Test
    fun hardwareSecurityLevelIsReportedConsistently() {
        manager.createKeyIfAbsent()

        val level = manager.hardwareSecurityLevel()
        assertNotNull(level)
        assertEquals(level!!.isProductionEligible, manager.isProductionEligible())

        // Only STRONGBOX and TEE may ever be production eligible.
        if (manager.isProductionEligible()) {
            assertTrue(
                level == HardwareSecurityLevel.STRONGBOX ||
                    level == HardwareSecurityLevel.TRUSTED_EXECUTION_ENVIRONMENT
            )
        }
    }

    @Test
    fun terminalKeyLossDoesNotSilentlyRegenerate() {
        manager.createKeyIfAbsent()
        val originalThumbprint = manager.signer().jwkThumbprint()

        // A future registration binds this device.
        bindingStore.markBound()

        // Simulate keystore loss / permanent invalidation.
        manager.deleteKeyDestructively()

        assertSame(DeviceAuthKeyStatus.TerminalKeyLoss, manager.status())
        assertThrows(DeviceAuthTerminalStateException::class.java) {
            manager.createKeyIfAbsent()
        }
        assertThrows(DeviceAuthTerminalStateException::class.java) { manager.signer() }
        assertSame(DeviceAuthKeyStatus.TerminalKeyLoss, manager.status())
        assertFalse(manager.isProductionEligible())

        // Nothing resurrected the old key.
        assertThrows(DeviceAuthTerminalStateException::class.java) {
            manager.signer().jwkThumbprint()
        }
        assertNotNull(originalThumbprint)
    }

    @Test
    fun unboundKeyLossIsTreatedAsFirstRun() {
        manager.createKeyIfAbsent()
        // Never bound, so losing the key is an ordinary first-run situation again.
        manager.deleteKeyDestructively()

        assertSame(DeviceAuthKeyStatus.AbsentNotBound, manager.status())
        assertTrue(manager.createKeyIfAbsent() is DeviceAuthKeyStatus.Present)
    }

    @Test
    fun deviceAuthAliasIsDistinctFromStateKeyAlias() {
        // Security Invariant 24: Device Auth key and K_STATE must remain distinct.
        assertFalse(
            AndroidKeystoreDeviceAuthKeyManager.DEFAULT_KEY_ALIAS.contains("state", true)
        )
        assertTrue(
            AndroidKeystoreDeviceAuthKeyManager.DEFAULT_KEY_ALIAS.contains("deviceauth")
        )
    }
}
