package com.anox.messenger.security.deviceauth

import com.nimbusds.jose.JWSSigner
import com.nimbusds.jose.jwk.ECKey

/**
 * Signing capability of the Device Auth key, decoupled from where the key lives.
 *
 * This boundary intentionally exposes ONLY:
 *  - the public JWK, and
 *  - an opaque JOSE signing capability.
 *
 * It never exposes private key bytes. Implementations backed by the Android Keystore hold
 * a non-extractable [java.security.PrivateKey] handle; the raw private scalar is not
 * obtainable through this interface or through the underlying platform API.
 */
interface DeviceAuthSigner {

    /**
     * Public P-256 key as a JWK.
     *
     * Implementations MUST return a public-only JWK (no `d` parameter). This is the value
     * embedded in the DPoP proof header and the value a future registration flow would
     * submit to the backend.
     */
    val publicJwk: ECKey

    /** RFC7638 SHA-256 JWK thumbprint (`jkt`) of [publicJwk], base64url encoded. */
    fun jwkThumbprint(): String = publicJwk.computeThumbprint().toString()

    /** A standards-compliant ES256 JOSE signer bound to the Device Auth private key. */
    fun jwsSigner(): JWSSigner
}
