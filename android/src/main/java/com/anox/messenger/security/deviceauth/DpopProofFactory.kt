package com.anox.messenger.security.deviceauth

import com.nimbusds.jose.JOSEObjectType
import com.nimbusds.jose.JWSAlgorithm
import com.nimbusds.jose.JWSHeader
import com.nimbusds.jwt.JWTClaimsSet
import com.nimbusds.jwt.SignedJWT
import java.util.Date

/**
 * Creates RFC9449 DPoP proof JWTs signed by the B-002 Device Auth key.
 *
 * The proof is a standard JWS compact serialisation produced by the JOSE library. No
 * custom canonical signing format is used anywhere in this class.
 *
 * Header: `typ=dpop+jwt`, `alg=ES256`, `jwk` = public Device Auth key.
 * Claims: `jti`, `htm`, `htu`, `iat`, plus `ath` when a token is bound and `nonce` when the
 * server supplied one.
 */
class DpopProofFactory(
    private val signer: DeviceAuthSigner,
    private val clock: DeviceAuthClock = SystemDeviceAuthClock,
    private val jtiGenerator: JtiGenerator = SecureRandomJtiGenerator()
) {

    /**
     * Creates a DPoP proof for a single request.
     *
     * @param httpMethod the HTTP method, uppercased into the `htm` claim.
     * @param targetUri the request target URI; query and fragment are stripped for `htu`.
     * @param accessToken when non-null, the proof is bound to this token via `ath`.
     * @param nonce when non-null, included as the `nonce` claim.
     * @return the compact-serialised DPoP proof JWT.
     */
    fun createProof(
        httpMethod: String,
        targetUri: String,
        accessToken: String? = null,
        nonce: String? = null
    ): String {
        val header = JWSHeader.Builder(JWSAlgorithm.ES256)
            .type(DPOP_JWT_TYPE)
            .jwk(signer.publicJwk)
            .build()

        val claims = JWTClaimsSet.Builder()
            .jwtID(jtiGenerator.newJti())
            .claim(CLAIM_HTM, httpMethod.uppercase())
            .claim(CLAIM_HTU, DpopHtu.normalize(targetUri))
            .issueTime(Date(clock.nowEpochSeconds() * 1000L))
            .apply {
                accessToken?.let {
                    claim(CLAIM_ATH, DeviceAuthAccessTokenContract.accessTokenHash(it))
                }
                nonce?.let { claim(CLAIM_NONCE, it) }
            }
            .build()

        return SignedJWT(header, claims)
            .apply { sign(signer.jwsSigner()) }
            .serialize()
    }

    companion object {
        /** RFC9449 required `typ` header value. */
        val DPOP_JWT_TYPE: JOSEObjectType = JOSEObjectType("dpop+jwt")

        const val CLAIM_HTM: String = "htm"
        const val CLAIM_HTU: String = "htu"
        const val CLAIM_ATH: String = "ath"
        const val CLAIM_NONCE: String = "nonce"
    }
}
