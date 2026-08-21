package com.anox.messenger.security.deviceauth

import java.net.URI

/**
 * Normalisation of the DPoP `htu` claim.
 *
 * RFC9449 section 4.2: `htu` is the HTTP target URI of the request, "without query and
 * fragment parts". Both the proof creator and the verifier must normalise identically,
 * otherwise a legitimate request is rejected or a mismatch is missed.
 */
object DpopHtu {

    /**
     * Returns [rawUri] with any query and fragment removed.
     *
     * @throws IllegalArgumentException if [rawUri] is not a valid absolute URI.
     */
    fun normalize(rawUri: String): String {
        val uri = try {
            URI(rawUri)
        } catch (e: Exception) {
            throw IllegalArgumentException("htu is not a valid URI", e)
        }
        require(uri.isAbsolute) { "htu must be an absolute URI" }

        val scheme = uri.scheme ?: throw IllegalArgumentException("htu has no scheme")
        val authority = uri.authority ?: throw IllegalArgumentException("htu has no authority")
        val path = uri.path ?: ""

        return buildString {
            append(scheme.lowercase())
            append("://")
            append(authority.lowercase())
            append(path)
        }
    }
}
