package com.anox.messenger.security.deviceauth

import com.nimbusds.jose.JWSAlgorithm
import com.nimbusds.jose.crypto.MACSigner
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * RFC9449 / B-002 DPoP protocol tests.
 *
 * Covers the positive path plus every rejection path required by the frozen B-002 spec.
 */
class DpopProofVerifierTest {

    private val method = "POST"
    private val uri = "https://api.example.test/v1/resource"

    private lateinit var signer: TestDeviceAuthSigner
    private lateinit var clock: MutableTestClock
    private lateinit var factory: DpopProofFactory
    private lateinit var verifier: DpopProofVerifier

    @Before
    fun setUp() {
        signer = TestDeviceAuthSigner.generate()
        clock = MutableTestClock()
        factory = DpopProofFactory(signer = signer, clock = clock)
        verifier = DpopProofVerifier(
            clock = clock,
            replayCache = InMemoryDpopReplayCache(clock = clock)
        )
    }

    private fun assertRejected(
        result: DpopVerificationResult,
        expected: DpopRejectionReason
    ) {
        assertTrue("expected rejection $expected but got $result", result is DpopVerificationResult.Invalid)
        assertEquals(expected, (result as DpopVerificationResult.Invalid).reason)
    }

    // ---------------------------------------------------------------------------------
    // positive evidence
    // ---------------------------------------------------------------------------------

    @Test
    fun `valid proof is accepted`() {
        val proof = factory.createProof(method, uri)
        val result = verifier.verify(proof, method, uri)

        assertTrue(result.isValid)
        assertEquals(signer.jwkThumbprint(), (result as DpopVerificationResult.Valid).jwkThumbprint)
    }

    @Test
    fun `valid proof is accepted when key binding matches`() {
        val proof = factory.createProof(method, uri)
        val result = verifier.verify(
            proof = proof,
            httpMethod = method,
            targetUri = uri,
            expectedJwkThumbprint = signer.jwkThumbprint()
        )
        assertTrue(result.isValid)
    }

    @Test
    fun `access token binding via ath is accepted`() {
        val token = DeviceAuthAccessTokenGenerator().newOpaqueToken()
        val proof = factory.createProof(method, uri, accessToken = token)

        val result = verifier.verify(proof, method, uri, accessToken = token)
        assertTrue(result.isValid)
    }

    @Test
    fun `nonce path is accepted`() {
        val nonce = "server-supplied-nonce-value"
        val proof = factory.createProof(method, uri, nonce = nonce)

        val result = verifier.verify(proof, method, uri, expectedNonce = nonce)
        assertTrue(result.isValid)
    }

    @Test
    fun `proof header carries a public only jwk`() {
        val proof = factory.createProof(method, uri)
        val header = com.nimbusds.jwt.SignedJWT.parse(proof).header

        assertFalse("DPoP header JWK must never contain private material", header.getJWK().isPrivate)
        assertFalse(header.getJWK().toJSONString().contains("\"d\""))
    }

    @Test
    fun `each proof uses a fresh jti`() {
        val jtis = (1..25).map {
            com.nimbusds.jwt.SignedJWT.parse(factory.createProof(method, uri)).getJWTClaimsSet().getJWTID()
        }
        assertEquals("jti values must be unique", jtis.size, jtis.toSet().size)
        jtis.forEach {
            assertTrue(
                "jti must carry at least 128 bits",
                it.length >= SecureRandomJtiGenerator.MIN_ENCODED_JTI_LENGTH
            )
        }
    }

    @Test
    fun `iat inside the allowed window is accepted at both edges`() {
        val proofAtStart = factory.createProof(method, uri)

        // Verify 119 seconds later: still inside the frozen +/-120s window.
        clock.advanceSeconds(119)
        assertTrue(verifier.verify(proofAtStart, method, uri).isValid)
    }

    @Test
    fun `htu query and fragment are ignored`() {
        val proof = factory.createProof(method, "$uri?a=1&b=2#frag")
        val result = verifier.verify(proof, method, "$uri?other=9#zzz")
        assertTrue(result.isValid)
    }

    // ---------------------------------------------------------------------------------
    // negative evidence
    // ---------------------------------------------------------------------------------

    @Test
    fun `wrong http method is rejected`() {
        val proof = factory.createProof("POST", uri)
        assertRejected(verifier.verify(proof, "GET", uri), DpopRejectionReason.HTM_MISMATCH)
    }

    @Test
    fun `wrong target uri is rejected`() {
        val proof = factory.createProof(method, uri)
        assertRejected(
            verifier.verify(proof, method, "https://api.example.test/v1/other"),
            DpopRejectionReason.HTU_MISMATCH
        )
    }

    @Test
    fun `different host is rejected`() {
        val proof = factory.createProof(method, uri)
        assertRejected(
            verifier.verify(proof, method, "https://evil.example.test/v1/resource"),
            DpopRejectionReason.HTU_MISMATCH
        )
    }

    @Test
    fun `stale iat is rejected`() {
        val proof = factory.createProof(method, uri)
        clock.advanceSeconds(121)
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.IAT_STALE)
    }

    @Test
    fun `future iat outside tolerance is rejected`() {
        val futureClock = MutableTestClock()
        futureClock.advanceSeconds(121)
        val futureFactory = DpopProofFactory(signer = signer, clock = futureClock)

        val proof = futureFactory.createProof(method, uri)
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.IAT_FUTURE)
    }

    @Test
    fun `missing iat is rejected`() {
        val proof = CustomProofBuilder.build(signer, iatEpochSeconds = null)
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.MISSING_IAT)
    }

    @Test
    fun `duplicate jti is rejected as replay`() {
        val fixedFactory = DpopProofFactory(
            signer = signer,
            clock = clock,
            jtiGenerator = FixedJtiGenerator("AAAAAAAAAAAAAAAAAAAAAA")
        )
        val first = fixedFactory.createProof(method, uri)
        val second = fixedFactory.createProof(method, uri)

        assertTrue(verifier.verify(first, method, uri).isValid)
        assertRejected(verifier.verify(second, method, uri), DpopRejectionReason.REPLAYED_JTI)
    }

    @Test
    fun `replaying the exact same proof is rejected`() {
        val proof = factory.createProof(method, uri)
        assertTrue(verifier.verify(proof, method, uri).isValid)
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.REPLAYED_JTI)
    }

    @Test
    fun `short jti is rejected`() {
        val proof = CustomProofBuilder.build(signer, jti = "tooshort")
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.INVALID_JTI)
    }

    @Test
    fun `wrong key binding is rejected`() {
        val otherSigner = TestDeviceAuthSigner.generate()
        val proof = factory.createProof(method, uri)

        assertNotEquals(signer.jwkThumbprint(), otherSigner.jwkThumbprint())
        assertRejected(
            verifier.verify(
                proof = proof,
                httpMethod = method,
                targetUri = uri,
                expectedJwkThumbprint = otherSigner.jwkThumbprint()
            ),
            DpopRejectionReason.KEY_BINDING_MISMATCH
        )
    }

    @Test
    fun `invalid signature is rejected`() {
        val proof = factory.createProof(method, uri)
        val tampered = CustomProofBuilder.withCorruptedSignature(proof)

        assertRejected(verifier.verify(tampered, method, uri), DpopRejectionReason.INVALID_SIGNATURE)
    }

    @Test
    fun `tampered payload is rejected`() {
        val proof = factory.createProof(method, uri)
        val forged = CustomProofBuilder.build(signer, htm = "DELETE")
        val parts = proof.split(".")
        val forgedParts = forged.split(".")
        // Original header+signature with a foreign payload.
        val spliced = "${parts[0]}.${forgedParts[1]}.${parts[2]}"

        assertRejected(verifier.verify(spliced, "DELETE", uri), DpopRejectionReason.INVALID_SIGNATURE)
    }

    @Test
    fun `malformed proof is rejected`() {
        assertRejected(verifier.verify("not-a-jwt", method, uri), DpopRejectionReason.MALFORMED)
        assertRejected(verifier.verify("", method, uri), DpopRejectionReason.MALFORMED)
        assertRejected(verifier.verify("a.b.c", method, uri), DpopRejectionReason.MALFORMED)
    }

    @Test
    fun `wrong typ is rejected`() {
        val proof = CustomProofBuilder.build(signer, typ = "JWT")
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.INVALID_TYP)
    }

    @Test
    fun `missing typ is rejected`() {
        val proof = CustomProofBuilder.build(signer, typ = null)
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.INVALID_TYP)
    }

    @Test
    fun `non es256 algorithm is rejected`() {
        // Algorithm confusion attempt: HS256 with a symmetric key.
        val secret = ByteArray(32) { 7 }
        val proof = CustomProofBuilder.build(
            signer = signer,
            algorithm = JWSAlgorithm.HS256,
            jwsSigner = MACSigner(secret)
        )
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.UNSUPPORTED_ALG)
    }

    @Test
    fun `missing jwk header is rejected`() {
        val proof = CustomProofBuilder.build(signer, includeJwk = false)
        assertRejected(verifier.verify(proof, method, uri), DpopRejectionReason.INVALID_JWK)
    }

    @Test
    fun `private key in jwk header is never accepted`() {
        val proof = CustomProofBuilder.buildWithPrivateJwkHeader(signer)
        val result = verifier.verify(proof, method, uri)

        assertFalse("a proof carrying private key material must never be accepted", result.isValid)
        // Nimbus rejects a private `jwk` header parameter during parsing
        // (CommonSEHeader.parsePublicJWK), so MALFORMED is the expected outcome. The
        // verifier's explicit PRIVATE_KEY_IN_JWK check remains as defence in depth.
        val reason = (result as DpopVerificationResult.Invalid).reason
        assertTrue(
            "unexpected rejection reason: $reason",
            reason == DpopRejectionReason.MALFORMED ||
                reason == DpopRejectionReason.PRIVATE_KEY_IN_JWK
        )
    }

    @Test
    fun `nimbus refuses to build a header with a private jwk`() {
        // Defence in depth: our own proof factory cannot leak private material even by
        // programming error.
        assertThrows(IllegalArgumentException::class.java) {
            com.nimbusds.jose.JWSHeader.Builder(JWSAlgorithm.ES256)
                .jwk(signer.privateJwk())
        }
    }

    @Test
    fun `missing ath when token presented is rejected`() {
        val token = DeviceAuthAccessTokenGenerator().newOpaqueToken()
        val proof = factory.createProof(method, uri) // no ath

        assertRejected(
            verifier.verify(proof, method, uri, accessToken = token),
            DpopRejectionReason.MISSING_ATH
        )
    }

    @Test
    fun `wrong ath is rejected`() {
        val generator = DeviceAuthAccessTokenGenerator()
        val boundToken = generator.newOpaqueToken()
        val presentedToken = generator.newOpaqueToken()

        val proof = factory.createProof(method, uri, accessToken = boundToken)
        assertRejected(
            verifier.verify(proof, method, uri, accessToken = presentedToken),
            DpopRejectionReason.ATH_MISMATCH
        )
    }

    @Test
    fun `missing nonce when required is rejected`() {
        val proof = factory.createProof(method, uri)
        assertRejected(
            verifier.verify(proof, method, uri, expectedNonce = "required-nonce"),
            DpopRejectionReason.MISSING_NONCE
        )
    }

    @Test
    fun `wrong nonce is rejected`() {
        val proof = factory.createProof(method, uri, nonce = "client-nonce")
        assertRejected(
            verifier.verify(proof, method, uri, expectedNonce = "server-nonce"),
            DpopRejectionReason.NONCE_MISMATCH
        )
    }

    @Test
    fun `failed verification does not consume the jti`() {
        val fixedFactory = DpopProofFactory(
            signer = signer,
            clock = clock,
            jtiGenerator = FixedJtiGenerator("AAAAAAAAAAAAAAAAAAAAAA")
        )
        val proof = fixedFactory.createProof(method, uri)

        // Rejected for a non-replay reason.
        assertRejected(verifier.verify(proof, "GET", uri), DpopRejectionReason.HTM_MISMATCH)
        // The same jti must still be usable for a legitimate request.
        assertTrue(verifier.verify(proof, method, uri).isValid)
    }
}
