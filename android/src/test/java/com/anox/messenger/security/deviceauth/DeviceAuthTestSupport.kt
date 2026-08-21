package com.anox.messenger.security.deviceauth

import com.nimbusds.jose.JOSEObjectType
import com.nimbusds.jose.JWSAlgorithm
import com.nimbusds.jose.JWSHeader
import com.nimbusds.jose.JWSSigner
import com.nimbusds.jose.crypto.ECDSASigner
import com.nimbusds.jose.jwk.Curve
import com.nimbusds.jose.jwk.ECKey
import com.nimbusds.jose.util.Base64URL
import com.nimbusds.jwt.JWTClaimsSet
import com.nimbusds.jwt.SignedJWT
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.interfaces.ECPrivateKey
import java.security.interfaces.ECPublicKey
import java.security.spec.ECGenParameterSpec
import java.util.Date

/**
 * JVM [DeviceAuthSigner] over a locally generated P-256 key pair.
 *
 * TEST SCOPE ONLY. Exists so the RFC9449 protocol logic can be exercised without an Android
 * Keystore. Production signing always goes through
 * [AndroidKeystoreDeviceAuthKeyManager.signer].
 */
class TestDeviceAuthSigner private constructor(val keyPair: KeyPair) : DeviceAuthSigner {

    override val publicJwk: ECKey =
        ECKey.Builder(Curve.P_256, keyPair.public as ECPublicKey).build().toPublicJWK()

    override fun jwsSigner(): JWSSigner = ECDSASigner(keyPair.private as ECPrivateKey)

    /** Private JWK including `d`. Used only to prove the verifier rejects it in a header. */
    fun privateJwk(): ECKey = ECKey.Builder(Curve.P_256, keyPair.public as ECPublicKey)
        .privateKey(keyPair.private as ECPrivateKey)
        .build()

    companion object {
        fun generate(): TestDeviceAuthSigner {
            val generator = KeyPairGenerator.getInstance("EC")
            generator.initialize(ECGenParameterSpec("secp256r1"))
            return TestDeviceAuthSigner(generator.generateKeyPair())
        }
    }
}

/** Controllable clock for deterministic `iat` and replay-window tests. */
class MutableTestClock(private var millis: Long = 1_760_000_000_000L) : DeviceAuthClock {
    override fun nowMillis(): Long = millis
    fun advanceSeconds(seconds: Long) {
        millis += seconds * 1000L
    }
}

/** Fixed `jti` generator, so replay behaviour can be forced deterministically. */
class FixedJtiGenerator(private val jti: String) : JtiGenerator {
    override fun newJti(): String = jti
}

/**
 * Builds a DPoP proof with individually overridable header/claim parts so that malformed and
 * hostile proofs can be constructed for negative tests.
 */
object CustomProofBuilder {

    fun build(
        signer: TestDeviceAuthSigner,
        typ: String? = "dpop+jwt",
        algorithm: JWSAlgorithm = JWSAlgorithm.ES256,
        includeJwk: Boolean = true,
        jti: String? = "AAAAAAAAAAAAAAAAAAAAAA",
        htm: String? = "POST",
        htu: String? = "https://api.example.test/v1/resource",
        iatEpochSeconds: Long? = 1_760_000_000L,
        ath: String? = null,
        nonce: String? = null,
        jwsSigner: JWSSigner = signer.jwsSigner()
    ): String {
        val headerBuilder = JWSHeader.Builder(algorithm)
        typ?.let { headerBuilder.type(JOSEObjectType(it)) }
        if (includeJwk) {
            headerBuilder.jwk(signer.publicJwk)
        }

        val claimsBuilder = JWTClaimsSet.Builder()
        jti?.let { claimsBuilder.jwtID(it) }
        htm?.let { claimsBuilder.claim(DpopProofFactory.CLAIM_HTM, it) }
        htu?.let { claimsBuilder.claim(DpopProofFactory.CLAIM_HTU, it) }
        iatEpochSeconds?.let { claimsBuilder.issueTime(Date(it * 1000L)) }
        ath?.let { claimsBuilder.claim(DpopProofFactory.CLAIM_ATH, it) }
        nonce?.let { claimsBuilder.claim(DpopProofFactory.CLAIM_NONCE, it) }

        return SignedJWT(headerBuilder.build(), claimsBuilder.build())
            .apply { sign(jwsSigner) }
            .serialize()
    }

    /**
     * Produces a proof whose header embeds the PRIVATE JWK, by raw header surgery.
     *
     * Surgery is required because Nimbus refuses to construct such a header:
     * `JWSHeader.Builder.jwk` throws `IllegalArgumentException("The JWK must be public")`,
     * and `JWSHeader.parse` routes the `jwk` parameter through
     * `CommonSEHeader.parsePublicJWK`. Both are defence in depth we rely on, but the
     * verifier must still never accept such a proof, which is what this exercises.
     */
    fun buildWithPrivateJwkHeader(signer: TestDeviceAuthSigner): String {
        val valid = build(signer)
        val payload = valid.split(".")[1]
        val signature = valid.split(".")[2]
        val headerJson =
            """{"typ":"dpop+jwt","alg":"ES256","jwk":${signer.privateJwk().toJSONString()}}"""
        val header = Base64URL.encode(headerJson).toString()
        return "$header.$payload.$signature"
    }

    /** Returns [proof] with its signature bytes corrupted in a way decoding cannot absorb. */
    fun withCorruptedSignature(proof: String): String {
        val parts = proof.split(".")
        val signatureBytes = Base64URL(parts[2]).decode()
        // Flip every bit of a byte well inside `r` so the ECDSA signature cannot verify.
        // Tampering the final base64url character would be unreliable: for a 64-byte
        // signature the last character carries 4 unused bits that decoding discards.
        signatureBytes[10] = (signatureBytes[10].toInt() xor 0xFF).toByte()
        return "${parts[0]}.${parts[1]}.${Base64URL.encode(signatureBytes)}"
    }
}

/**
 * In-memory [DeviceAuthKeyManager] that delegates its lifecycle decisions to the production
 * [DeviceAuthKeyStateResolver].
 *
 * TEST SCOPE ONLY. Used to exercise the full lifecycle contract, including the rule that
 * terminal key loss must never silently produce a replacement key.
 */
class FakeDeviceAuthKeyManager(
    private val bindingStore: DeviceAuthBindingStore,
    private val hardwareLevel: HardwareSecurityLevel = HardwareSecurityLevel.STRONGBOX
) : DeviceAuthKeyManager {

    private var signerOrNull: TestDeviceAuthSigner? = null
    var generateCallCount: Int = 0
        private set

    override fun status(): DeviceAuthKeyStatus = DeviceAuthKeyStateResolver.resolve(
        keyPresent = signerOrNull != null,
        hardwareSecurityLevel = if (signerOrNull != null) hardwareLevel else null,
        isBound = bindingStore.isBound()
    )

    override fun createKeyIfAbsent(): DeviceAuthKeyStatus {
        val current = status()
        if (current is DeviceAuthKeyStatus.Present) return current
        DeviceAuthKeyStateResolver.requireCreationAllowed(current)
        signerOrNull = TestDeviceAuthSigner.generate()
        generateCallCount++
        return status()
    }

    override fun hardwareSecurityLevel(): HardwareSecurityLevel? =
        signerOrNull?.let { hardwareLevel }

    override fun isProductionEligible(): Boolean =
        hardwareSecurityLevel()?.isProductionEligible == true

    override fun signer(): DeviceAuthSigner = signerOrNull
        ?: throw DeviceAuthTerminalStateException("No usable Device Auth key: ${status()}")

    override fun deleteKeyDestructively() {
        signerOrNull = null
    }

    /** Simulates platform invalidation / keystore loss without touching the bound marker. */
    fun simulateKeyInvalidation() {
        signerOrNull = null
    }
}
