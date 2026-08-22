package com.anox.messenger.security.deviceauth

/** Why a DPoP proof was rejected. Values are safe to log: they carry no secret material. */
enum class DpopRejectionReason {
    /** Not a parseable JWS / JWT. */
    MALFORMED,

    /** `typ` header is missing or is not `dpop+jwt`. */
    INVALID_TYP,

    /** `alg` is not ES256. Prevents algorithm confusion and `alg=none`. */
    UNSUPPORTED_ALG,

    /** The `jwk` header is missing, not an EC P-256 key, or is not usable. */
    INVALID_JWK,

    /** The `jwk` header carried private key material. Always fatal. */
    PRIVATE_KEY_IN_JWK,

    /** The JWS signature did not verify under the embedded public key. */
    INVALID_SIGNATURE,

    /** The embedded key does not match the key the token/device is bound to (`jkt`). */
    KEY_BINDING_MISMATCH,

    /** `htm` does not match the actual HTTP method. */
    HTM_MISMATCH,

    /** `htu` does not match the actual target URI. */
    HTU_MISMATCH,

    /** `iat` is missing. */
    MISSING_IAT,

    /** `iat` is older than the accepted window. */
    IAT_STALE,

    /** `iat` is further in the future than the accepted window. */
    IAT_FUTURE,

    /** `jti` is missing or carries less than the frozen 128-bit minimum. */
    INVALID_JTI,

    /** `jti` was already seen inside the replay window. */
    REPLAYED_JTI,

    /** `ath` is missing while an access token was presented. */
    MISSING_ATH,

    /** `ath` does not match the SHA-256 of the presented access token. */
    ATH_MISMATCH,

    /** A nonce was required but the proof carried none. */
    MISSING_NONCE,

    /** The `nonce` claim did not match the expected server nonce. */
    NONCE_MISMATCH
}

/** Outcome of verifying a DPoP proof. */
sealed class DpopVerificationResult {

    /**
     * The proof is valid.
     *
     * @param jwkThumbprint RFC7638 SHA-256 thumbprint (`jkt`) of the proving key. A future
     *   backend binds the issued access token to this value.
     * @param jti the accepted, now-consumed replay identifier.
     */
    data class Valid(val jwkThumbprint: String, val jti: String) : DpopVerificationResult()

    /** The proof was rejected. */
    data class Invalid(val reason: DpopRejectionReason) : DpopVerificationResult()

    val isValid: Boolean get() = this is Valid
}
