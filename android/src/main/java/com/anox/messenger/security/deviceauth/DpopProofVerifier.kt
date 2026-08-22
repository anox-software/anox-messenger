package com.anox.messenger.security.deviceauth

import com.nimbusds.jose.JWSAlgorithm
import com.nimbusds.jose.crypto.ECDSAVerifier
import com.nimbusds.jose.jwk.Curve
import com.nimbusds.jose.jwk.ECKey
import com.nimbusds.jwt.SignedJWT
import java.security.MessageDigest

/**
 * Verification boundary for RFC9449 DPoP proofs.
 *
 * SCOPE: this is the protocol/policy boundary required to prove the frozen B-002 semantics
 * are implemented correctly. It is NOT the production authentication backend (B-004): it
 * does not issue tokens, does not own sessions, does not consult a device registry and does
 * not enforce entitlement. A production deployment supplies the real token/session/device
 * lookup and a shared [DpopReplayCache], then applies this same claim validation.
 *
 * Validation follows RFC9449 section 4.3 plus the frozen B-002 parameters:
 *  - `iat` acceptance window +/- 120 seconds;
 *  - `jti` at least 128 random bits;
 *  - replay cache window 5 minutes;
 *  - ES256 only.
 */
class DpopProofVerifier(
    private val clock: DeviceAuthClock = SystemDeviceAuthClock,
    private val replayCache: DpopReplayCache = InMemoryDpopReplayCache(),
    private val iatToleranceSeconds: Long = DEFAULT_IAT_TOLERANCE_SECONDS
) {

    /**
     * Verifies [proof] against the observed request.
     *
     * @param proof compact-serialised DPoP proof JWT.
     * @param httpMethod the HTTP method actually observed.
     * @param targetUri the target URI actually observed.
     * @param expectedJwkThumbprint when non-null, the `jkt` the token/device is bound to.
     * @param accessToken when non-null, the access token presented on the request; the
     *   proof must carry a matching `ath`.
     * @param expectedNonce when non-null, a server nonce that the proof must echo.
     */
    fun verify(
        proof: String,
        httpMethod: String,
        targetUri: String,
        expectedJwkThumbprint: String? = null,
        accessToken: String? = null,
        expectedNonce: String? = null
    ): DpopVerificationResult {

        val signedJwt = try {
            SignedJWT.parse(proof)
        } catch (e: Exception) {
            return reject(DpopRejectionReason.MALFORMED)
        }

        val header = signedJwt.header

        if (header.type != DpopProofFactory.DPOP_JWT_TYPE) {
            return reject(DpopRejectionReason.INVALID_TYP)
        }
        if (header.algorithm != JWSAlgorithm.ES256) {
            return reject(DpopRejectionReason.UNSUPPORTED_ALG)
        }

        // Explicit Java getter calls are used for the all-caps JOSE accessors so that
        // Kotlin synthetic-property naming cannot be misapplied.
        val jwk = header.getJWK() ?: return reject(DpopRejectionReason.INVALID_JWK)
        if (jwk.isPrivate) {
            return reject(DpopRejectionReason.PRIVATE_KEY_IN_JWK)
        }
        val ecKey = jwk as? ECKey ?: return reject(DpopRejectionReason.INVALID_JWK)
        if (ecKey.curve != Curve.P_256) {
            return reject(DpopRejectionReason.INVALID_JWK)
        }

        val signatureValid = try {
            signedJwt.verify(ECDSAVerifier(ecKey))
        } catch (e: Exception) {
            return reject(DpopRejectionReason.INVALID_SIGNATURE)
        }
        if (!signatureValid) {
            return reject(DpopRejectionReason.INVALID_SIGNATURE)
        }

        val thumbprint = try {
            ecKey.computeThumbprint().toString()
        } catch (e: Exception) {
            return reject(DpopRejectionReason.INVALID_JWK)
        }
        if (expectedJwkThumbprint != null && !constantTimeEquals(thumbprint, expectedJwkThumbprint)) {
            return reject(DpopRejectionReason.KEY_BINDING_MISMATCH)
        }

        val claims = try {
            signedJwt.getJWTClaimsSet()
        } catch (e: Exception) {
            return reject(DpopRejectionReason.MALFORMED)
        }

        val htm = claims.getStringClaim(DpopProofFactory.CLAIM_HTM)
        if (htm == null || htm != httpMethod.uppercase()) {
            return reject(DpopRejectionReason.HTM_MISMATCH)
        }

        val htu = claims.getStringClaim(DpopProofFactory.CLAIM_HTU)
        val expectedHtu = try {
            DpopHtu.normalize(targetUri)
        } catch (e: Exception) {
            return reject(DpopRejectionReason.HTU_MISMATCH)
        }
        if (htu == null || htu != expectedHtu) {
            return reject(DpopRejectionReason.HTU_MISMATCH)
        }

        val issueTime = claims.issueTime ?: return reject(DpopRejectionReason.MISSING_IAT)
        val iat = issueTime.time / 1000L
        val now = clock.nowEpochSeconds()
        if (iat < now - iatToleranceSeconds) {
            return reject(DpopRejectionReason.IAT_STALE)
        }
        if (iat > now + iatToleranceSeconds) {
            return reject(DpopRejectionReason.IAT_FUTURE)
        }

        val jti = claims.getJWTID()
        if (jti.isNullOrEmpty() || jti.length < SecureRandomJtiGenerator.MIN_ENCODED_JTI_LENGTH) {
            return reject(DpopRejectionReason.INVALID_JTI)
        }

        if (accessToken != null) {
            val ath = claims.getStringClaim(DpopProofFactory.CLAIM_ATH)
                ?: return reject(DpopRejectionReason.MISSING_ATH)
            val expectedAth = DeviceAuthAccessTokenContract.accessTokenHash(accessToken)
            if (!constantTimeEquals(ath, expectedAth)) {
                return reject(DpopRejectionReason.ATH_MISMATCH)
            }
        }

        if (expectedNonce != null) {
            val nonce = claims.getStringClaim(DpopProofFactory.CLAIM_NONCE)
                ?: return reject(DpopRejectionReason.MISSING_NONCE)
            if (!constantTimeEquals(nonce, expectedNonce)) {
                return reject(DpopRejectionReason.NONCE_MISMATCH)
            }
        }

        // Replay is checked last so that a proof failing any earlier check does not consume
        // a jti slot.
        if (!replayCache.recordIfAbsent(jti)) {
            return reject(DpopRejectionReason.REPLAYED_JTI)
        }

        return DpopVerificationResult.Valid(jwkThumbprint = thumbprint, jti = jti)
    }

    private fun reject(reason: DpopRejectionReason): DpopVerificationResult =
        DpopVerificationResult.Invalid(reason)

    private fun constantTimeEquals(a: String, b: String): Boolean =
        MessageDigest.isEqual(a.toByteArray(Charsets.UTF_8), b.toByteArray(Charsets.UTF_8))

    companion object {
        /** Frozen B-002 `iat` acceptance window: +/- 120 seconds. */
        const val DEFAULT_IAT_TOLERANCE_SECONDS: Long = 120L
    }
}
