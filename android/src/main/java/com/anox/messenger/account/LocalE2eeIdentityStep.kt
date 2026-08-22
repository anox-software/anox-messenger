package com.anox.messenger.account

/**
 * Narrow boundary for the "create E2EE identity locally, prepare public material" step of B-003
 * registration.
 *
 * This interface intentionally does not redesign or re-expose the existing E2EE foundation
 * (`crypto/rust`, `CryptoNative.kt`, `CryptoBridge.kt`, vodozemac, `K_STATE`). Implementations
 * are expected to call the existing, unmodified `CryptoBridge` public API. Only public key
 * material ever crosses this boundary; private key material and any Olm/ratchet state never do
 * (Security Invariant 4).
 */
interface LocalE2eeIdentityStep {

    /**
     * Ensures a local E2EE identity exists (creating one only on legitimate first run, exactly
     * like the existing `CryptoBridge` local-state lifecycle already requires) and returns its
     * public material for upload.
     *
     * @throws LocalE2eeIdentityStepException if the local E2EE state is not in a state from
     *   which public material can be safely produced (for example corrupted or missing-keystore
     *   local state). This step never silently regenerates identity state; that decision belongs
     *   to the existing E2EE foundation's own fail-closed lifecycle.
     */
    fun ensurePublicIdentityMaterial(oneTimeKeyCount: Int): PublicE2eeIdentityMaterial
}

/** Raised when public E2EE identity material cannot be safely produced. */
class LocalE2eeIdentityStepException(message: String) : IllegalStateException(message)
