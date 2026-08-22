package com.anox.messenger.account

import com.anox.messenger.security.deviceauth.DeviceAuthSigner
import com.nimbusds.jose.jwk.ECKey
import java.time.Instant

/**
 * Narrow client-side contract for the B-003 registration/renewal network boundary.
 *
 * This interface represents only the domain operations required by the registration flow. It
 * deliberately does NOT implement a real HTTP stack, a fake Supabase/PostgreSQL backend,
 * service-role access, SQL, RLS, Edge Functions or production token issuance: those belong to
 * B-004 (backend service) and B-005 (database schema/RLS). The expected future topology is
 * Android -> authenticated HTTPS `/v1` -> anoX backend -> PostgreSQL/Supabase/private storage,
 * with no privileged direct Supabase access from the APK.
 *
 * A future B-004 implementation of this interface owns the actual network/threading model;
 * this contract intentionally stays synchronous and dependency-free at the foundation stage.
 */
interface RegistrationApi {

    /** Reserves [licenseCode] and [username] together, starting a registration transaction. */
    fun reserveRegistration(username: Username, licenseCode: LicenseCode): ReservationResult

    /**
     * Registers this device's Device Auth public key for [registrationId], proven by [dpopProof]
     * (a DPoP proof produced by the existing B-002 [DeviceAuthSigner] boundary; never a private
     * key or raw signature).
     */
    fun registerDeviceAuth(
        registrationId: RegistrationId,
        grant: RegistrationGrant,
        publicJwk: ECKey,
        dpopProof: String
    ): DeviceAuthRegistrationResult

    /** Uploads the public E2EE identity material prepared by [LocalE2eeIdentityStep]. */
    fun submitPublicIdentity(
        registrationId: RegistrationId,
        grant: RegistrationGrant,
        publicIdentity: PublicE2eeIdentityMaterial
    ): PublicIdentityResult

    /**
     * Requests the atomic final commit of account, device, Device Auth binding, E2EE public
     * identity and entitlement redemption.
     */
    fun commitRegistration(
        registrationId: RegistrationId,
        grant: RegistrationGrant
    ): CommitResult

    /** Requests renewal of the entitlement for an already-registered account/device. */
    fun renewEntitlement(
        accountId: AccountId,
        deviceId: DeviceId,
        duration: LicenseDuration
    ): RenewalResult
}

/** Result of [RegistrationApi.reserveRegistration]. */
sealed class ReservationResult {
    data class Reserved(
        val registrationId: RegistrationId,
        val grant: RegistrationGrant
    ) : ReservationResult()

    data class Rejected(val reason: String) : ReservationResult()
}

/** Result of [RegistrationApi.registerDeviceAuth]. */
sealed class DeviceAuthRegistrationResult {
    object Accepted : DeviceAuthRegistrationResult()
    data class Rejected(val reason: String) : DeviceAuthRegistrationResult()
}

/** Result of [RegistrationApi.submitPublicIdentity]. */
sealed class PublicIdentityResult {
    object Accepted : PublicIdentityResult()
    data class Rejected(val reason: String) : PublicIdentityResult()
}

/** Result of [RegistrationApi.commitRegistration]. */
sealed class CommitResult {
    data class Committed(val accountId: AccountId, val deviceId: DeviceId) : CommitResult()
    data class Rejected(val reason: String) : CommitResult()
}

/** Result of [RegistrationApi.renewEntitlement]. */
sealed class RenewalResult {
    data class Renewed(val newExpiresAt: Instant) : RenewalResult()
    data class Rejected(val reason: String) : RenewalResult()
}
