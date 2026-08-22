package com.anox.messenger.account

import com.anox.messenger.security.deviceauth.DeviceAuthBindingStore
import com.anox.messenger.security.deviceauth.DeviceAuthKeyManager
import com.anox.messenger.security.deviceauth.DeviceAuthKeyStatus
import com.anox.messenger.security.deviceauth.DeviceAuthTerminalStateException
import java.time.Instant

/**
 * Drives the frozen B-003 registration transaction one explicit step at a time:
 * reserve -> register Device Auth (proof-of-possession) -> upload public E2EE identity ->
 * atomic commit.
 *
 * Design notes:
 *  - The account is never treated as bound/active before [commit] observes
 *    [CommitResult.Committed]. [DeviceAuthBindingStore.markBound] is called from exactly one
 *    place: immediately after a successful commit.
 *  - Each step persists its resulting [RegistrationState] via [sessionStore] before returning,
 *    so a crash/process death is resumable by simply reading [currentState] again and calling
 *    the next appropriate step. This is transaction resume, never account recovery or device
 *    replacement.
 *  - [nowForGrantStalenessCheck] is used ONLY as a local courtesy check against the
 *    registration grant's 30-minute TTL, to avoid an obviously-stale local retry. This is
 *    unrelated to, and must not be confused with, the frozen rule that *entitlement* expiry is
 *    never computed from the local device clock (see [EntitlementRenewal]); the server remains
 *    the sole authority for whether a grant is actually still valid.
 *  - Reuses the existing B-002 [DeviceAuthKeyManager] boundary as-is; it never duplicates or
 *    modifies the P-256/ES256/DPoP implementation.
 *  - Reuses the existing E2EE foundation only through [LocalE2eeIdentityStep]; it never reads
 *    or transmits private key material.
 */
class RegistrationOrchestrator(
    private val api: RegistrationApi,
    private val deviceAuthKeyManager: DeviceAuthKeyManager,
    private val deviceAuthBindingStore: DeviceAuthBindingStore,
    private val sessionStore: RegistrationSessionStore,
    private val e2eeStep: LocalE2eeIdentityStep,
    private val createDeviceAuthProof: (RegistrationId) -> String,
    private val oneTimeKeyCount: Int = DEFAULT_ONE_TIME_KEY_COUNT
) {

    /** The last durably recorded registration state; safe to call after a crash/restart. */
    fun currentState(): RegistrationState = sessionStore.load()

    /** Step 1: reserve [licenseCode] and [username] together. */
    fun reserve(username: Username, licenseCode: LicenseCode): RegistrationState {
        val current = sessionStore.load()
        check(canStartNew(current)) {
            "cannot start a new registration while one is already in progress: $current"
        }
        val next = when (val result = api.reserveRegistration(username, licenseCode)) {
            is ReservationResult.Reserved ->
                RegistrationState.Reserved(result.registrationId, result.grant, username)
            is ReservationResult.Rejected ->
                RegistrationState.Failed("reservation rejected: ${result.reason}")
        }
        sessionStore.save(next)
        return next
    }

    /** Step 2: register this device's Device Auth public key with proof-of-possession. */
    fun registerDeviceAuth(nowForGrantStalenessCheck: Instant = Instant.now()): RegistrationState {
        val reserved = sessionStore.load() as? RegistrationState.Reserved
            ?: return failStep("registerDeviceAuth requires Reserved state, was ${sessionStore.load()}")

        expiredOrNull(reserved.registrationId, reserved.grant, nowForGrantStalenessCheck)
            ?.let { return it }

        if (deviceAuthKeyManager.status() is DeviceAuthKeyStatus.TerminalKeyLoss) {
            return failStep(
                "Device Auth key is in a terminal state for this installation; " +
                    "registration cannot proceed. There is no recovery or re-binding in V1."
            )
        }
        val signer = try {
            deviceAuthKeyManager.createKeyIfAbsent()
            deviceAuthKeyManager.signer()
        } catch (e: DeviceAuthTerminalStateException) {
            return failStep("Device Auth key is in a terminal state: ${e.message}")
        }
        val proof = createDeviceAuthProof(reserved.registrationId)

        val next = when (
            val result = api.registerDeviceAuth(
                reserved.registrationId,
                reserved.grant,
                signer.publicJwk,
                proof
            )
        ) {
            is DeviceAuthRegistrationResult.Accepted -> RegistrationState.DeviceAuthRegistered(
                reserved.registrationId,
                reserved.grant,
                reserved.username,
                signer.jwkThumbprint()
            )
            is DeviceAuthRegistrationResult.Rejected ->
                RegistrationState.Failed("Device Auth registration rejected: ${result.reason}")
        }
        sessionStore.save(next)
        return next
    }

    /** Step 3: create/reuse the local E2EE identity and upload its public material. */
    fun uploadPublicIdentity(nowForGrantStalenessCheck: Instant = Instant.now()): RegistrationState {
        val registered = sessionStore.load() as? RegistrationState.DeviceAuthRegistered
            ?: return failStep(
                "uploadPublicIdentity requires DeviceAuthRegistered state, was ${sessionStore.load()}"
            )

        expiredOrNull(registered.registrationId, registered.grant, nowForGrantStalenessCheck)
            ?.let { return it }

        val material = try {
            e2eeStep.ensurePublicIdentityMaterial(oneTimeKeyCount)
        } catch (e: LocalE2eeIdentityStepException) {
            return failStep("local E2EE identity material unavailable: ${e.message}")
        }
        val next = when (
            val result = api.submitPublicIdentity(registered.registrationId, registered.grant, material)
        ) {
            is PublicIdentityResult.Accepted -> RegistrationState.PublicIdentityUploaded(
                registered.registrationId,
                registered.grant,
                registered.username,
                registered.deviceAuthJwkThumbprint
            )
            is PublicIdentityResult.Rejected ->
                RegistrationState.Failed("public identity upload rejected: ${result.reason}")
        }
        sessionStore.save(next)
        return next
    }

    /** Step 4: request the atomic final commit. Only this step may result in [markBound]. */
    fun commit(nowForGrantStalenessCheck: Instant = Instant.now()): RegistrationState {
        val uploaded = sessionStore.load() as? RegistrationState.PublicIdentityUploaded
            ?: return failStep(
                "commit requires PublicIdentityUploaded state, was ${sessionStore.load()}"
            )

        expiredOrNull(uploaded.registrationId, uploaded.grant, nowForGrantStalenessCheck)
            ?.let { return it }

        val next = when (val result = api.commitRegistration(uploaded.registrationId, uploaded.grant)) {
            is CommitResult.Committed ->
                RegistrationState.Committed(result.accountId, result.deviceId, uploaded.username)
            is CommitResult.Rejected -> RegistrationState.Failed("commit rejected: ${result.reason}")
        }
        sessionStore.save(next)

        if (next is RegistrationState.Committed) {
            // Only now, after the atomic server commit succeeded, is this key considered
            // bound to an account. This is the ONLY call site for markBound() in this class.
            deviceAuthBindingStore.markBound()
            sessionStore.clear()
        }
        return next
    }

    /** Explicitly abandons an in-progress registration transaction. Not account deletion. */
    fun abandon() {
        sessionStore.clear()
    }

    private fun canStartNew(state: RegistrationState): Boolean = when (state) {
        is RegistrationState.NotStarted,
        is RegistrationState.Expired,
        is RegistrationState.Failed -> true
        else -> false
    }

    private fun expiredOrNull(
        registrationId: RegistrationId,
        grant: RegistrationGrant,
        now: Instant
    ): RegistrationState? {
        if (!grant.isExpired(now)) return null
        val expired = RegistrationState.Expired(registrationId)
        sessionStore.save(expired)
        return expired
    }

    private fun failStep(reason: String): RegistrationState {
        val failed = RegistrationState.Failed(reason)
        sessionStore.save(failed)
        return failed
    }

    companion object {
        /** Foundation default; the real value is a future B-004/B-005 decision. */
        const val DEFAULT_ONE_TIME_KEY_COUNT: Int = 20
    }
}
