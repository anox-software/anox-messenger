package com.anox.messenger.account

import com.anox.crypto.CryptoBridge
import com.anox.crypto.CryptoResult

/**
 * [LocalE2eeIdentityStep] backed by the existing, unmodified [CryptoBridge].
 *
 * This class only calls [CryptoBridge]'s existing public API (`getLocalStateStatus`,
 * `createAndPersistFirstIdentity`, `getCurve25519PublicKey`, `getEd25519PublicKey`,
 * `generateOneTimeKeys`, `oneTimeKeysCount`, `getOneTimeKey`). It does not modify
 * `CryptoBridge`, `CryptoNative`, `crypto/rust` or the vodozemac/`K_STATE` foundation, and it
 * never reads or exposes private key material.
 */
class CryptoBridgeLocalE2eeIdentityStep(
    private val cryptoBridge: CryptoBridge
) : LocalE2eeIdentityStep {

    override fun ensurePublicIdentityMaterial(oneTimeKeyCount: Int): PublicE2eeIdentityMaterial {
        val identity = resolveIdentityHandle()

        val curve25519 = requireSuccess(
            cryptoBridge.getCurve25519PublicKey(identity),
            "Curve25519 public key"
        )
        val ed25519 = requireSuccess(
            cryptoBridge.getEd25519PublicKey(identity),
            "Ed25519 public key"
        )

        val existingCount = requireSuccess(
            cryptoBridge.oneTimeKeysCount(identity),
            "one-time key count"
        )
        if (existingCount < oneTimeKeyCount) {
            requireSuccess(
                cryptoBridge.generateOneTimeKeys(identity, oneTimeKeyCount - existingCount),
                "one-time key generation"
            )

            // CRITICAL: the identity has been mutated by OTK generation. Persist the updated
            // identity BEFORE public OTK material is returned for upload, so a crash after this
            // point still has matching private OTK state locally.
            requireSuccess(
                cryptoBridge.saveIdentity(identity),
                "persist identity after one-time key generation"
            )
        }

        val oneTimeKeys = (0 until oneTimeKeyCount).map { index ->
            requireSuccess(cryptoBridge.getOneTimeKey(identity, index), "one-time key $index")
        }

        return PublicE2eeIdentityMaterial(
            curve25519PublicKey = curve25519,
            ed25519PublicKey = ed25519,
            oneTimeKeys = oneTimeKeys
        )
    }

    private fun resolveIdentityHandle(): Long =
        when (val status = cryptoBridge.getLocalStateStatus()) {
            is CryptoBridge.LocalStateStatus.IdentityReady -> status.identity
            is CryptoBridge.LocalStateStatus.FirstRun -> {
                when (val created = cryptoBridge.createAndPersistFirstIdentity()) {
                    is CryptoResult.Success -> created.value
                    is CryptoResult.Failure -> throw LocalE2eeIdentityStepException(
                        "Failed to create local E2EE identity: ${created.error}"
                    )
                }
            }
            else -> throw LocalE2eeIdentityStepException(
                "Local E2EE state is not usable for registration: $status"
            )
        }

    private fun <T> requireSuccess(result: CryptoResult<T>, what: String): T = when (result) {
        is CryptoResult.Success -> result.value
        is CryptoResult.Failure -> throw LocalE2eeIdentityStepException(
            "Failed to obtain $what: ${result.error}"
        )
    }
}
