package com.anox.messenger.account

import com.nimbusds.jose.jwk.ECKey
import java.time.Instant
import java.util.UUID

/**
 * Configurable [RegistrationApi] test double.
 *
 * TEST SCOPE ONLY. Exercises [RegistrationOrchestrator] without a real network stack or a fake
 * production backend.
 */
class FakeRegistrationApi : RegistrationApi {

    var reservationResult: ReservationResult =
        ReservationResult.Reserved(
            RegistrationId.parse(UUID.randomUUID().toString())!!,
            RegistrationGrantGenerator().newGrant(Instant.now())
        )
    var deviceAuthResult: DeviceAuthRegistrationResult = DeviceAuthRegistrationResult.Accepted
    var publicIdentityResult: PublicIdentityResult = PublicIdentityResult.Accepted
    var commitResult: CommitResult = CommitResult.Committed(
        AccountId.parse(UUID.randomUUID().toString())!!,
        DeviceId.parse(UUID.randomUUID().toString())!!
    )
    var renewalResult: RenewalResult = RenewalResult.Renewed(Instant.now())

    var reserveCallCount = 0
        private set
    var registerDeviceAuthCallCount = 0
        private set
    var submitPublicIdentityCallCount = 0
        private set
    var commitCallCount = 0
        private set
    var lastSubmittedPublicIdentity: PublicE2eeIdentityMaterial? = null
        private set
    var lastDpopProof: String? = null
        private set
    var lastPublicJwk: ECKey? = null
        private set

    override fun reserveRegistration(username: Username, licenseCode: LicenseCode): ReservationResult {
        reserveCallCount++
        return reservationResult
    }

    override fun registerDeviceAuth(
        registrationId: RegistrationId,
        grant: RegistrationGrant,
        publicJwk: ECKey,
        dpopProof: String
    ): DeviceAuthRegistrationResult {
        registerDeviceAuthCallCount++
        lastDpopProof = dpopProof
        lastPublicJwk = publicJwk
        return deviceAuthResult
    }

    override fun submitPublicIdentity(
        registrationId: RegistrationId,
        grant: RegistrationGrant,
        publicIdentity: PublicE2eeIdentityMaterial
    ): PublicIdentityResult {
        submitPublicIdentityCallCount++
        lastSubmittedPublicIdentity = publicIdentity
        return publicIdentityResult
    }

    override fun commitRegistration(registrationId: RegistrationId, grant: RegistrationGrant): CommitResult {
        commitCallCount++
        return commitResult
    }

    override fun renewEntitlement(
        accountId: AccountId,
        deviceId: DeviceId,
        duration: LicenseDuration
    ): RenewalResult {
        return renewalResult
    }
}

/**
 * Fixed/failable [LocalE2eeIdentityStep] test double.
 *
 * TEST SCOPE ONLY. Never touches the real `crypto/rust` / `CryptoBridge` foundation.
 */
class FakeLocalE2eeIdentityStep(
    private val material: PublicE2eeIdentityMaterial = PublicE2eeIdentityMaterial(
        curve25519PublicKey = ByteArray(32) { 1 },
        ed25519PublicKey = ByteArray(32) { 2 },
        oneTimeKeys = listOf(ByteArray(32) { 3 })
    ),
    private val failWith: LocalE2eeIdentityStepException? = null
) : LocalE2eeIdentityStep {

    var callCount = 0
        private set

    override fun ensurePublicIdentityMaterial(oneTimeKeyCount: Int): PublicE2eeIdentityMaterial {
        callCount++
        failWith?.let { throw it }
        return material
    }
}

/**
 * Fault-injecting [RegistrationSessionStore] for crash-consistency tests.
 *
 * TEST SCOPE ONLY.
 */
class FaultyInMemoryRegistrationSessionStore(
    private val delegate: InMemoryRegistrationSessionStore = InMemoryRegistrationSessionStore()
) : RegistrationSessionStore {

    var failNextSave: Boolean = false
    /** If > 0, fail on the Nth call to [save] instead of the next one. */
    var failOnNthSave: Int = -1
    var saveCallCount: Int = 0
        private set

    override fun load(): RegistrationState = delegate.load()

    override fun save(state: RegistrationState) {
        saveCallCount++
        if (failNextSave || (failOnNthSave > 0 && saveCallCount == failOnNthSave)) {
            failNextSave = false
            failOnNthSave = -1
            throw RegistrationSessionSecurityException("injected save fault")
        }
        delegate.save(state)
    }

    override fun clear() = delegate.clear()
}
