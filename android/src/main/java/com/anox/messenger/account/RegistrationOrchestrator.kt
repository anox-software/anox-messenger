package com.anox.messenger.account

import com.anox.messenger.security.deviceauth.DeviceAuthBindingStore
import com.anox.messenger.security.deviceauth.DeviceAuthKeyManager
import com.anox.messenger.security.deviceauth.DeviceAuthKeyStatus
import com.anox.messenger.security.deviceauth.DeviceAuthNotProductionEligibleException
import com.anox.messenger.security.deviceauth.DeviceAuthTerminalStateException
import com.anox.messenger.security.deviceauth.HardwareSecurityLevel
import java.time.Instant

/**
 * Drives the frozen B-003 registration transaction one explicit step at a time:
 * reserve -> register Device Auth (proof-of-possession) -> upload public E2EE identity ->
 * arm the pre-commit fail-closed guard -> atomic final commit.
 *
 * Crash-consistency / Device Auth safety design:
 *  - [DeviceAuthBindingStore] is the durable fail-closed guard. If it says the installation is
 *    bound or armed, [canStartNew] is always false and the key manager treats key loss as
 *    terminal.
 *  - `commit()` first persists [RegistrationState.CommitArmed] to the encrypted session store,
 *    then durably arms the binding store via [markArmed], and only then calls the remote
 *    endpoint. A crash between arming and the remote call leaves `isArmed == true` and the
 *    session at [CommitArmed]; retrying `commit()` is safe because the remote call is idempotent,
 *    `markArmed()` is idempotent, and the same Device Auth key is required.
 *  - On an authoritative [CommitResult.Committed], the binding marker is marked [markBound]
 *    before the [RegistrationState.Committed] state is persisted, then the temporary session
 *    secret material is cleared.
 *  - [RegistrationState.Committed] is terminal. [failStep] will never overwrite it, and
 *    [canStartNew] rejects it.
 *  - [failStep] also refuses to overwrite any in-progress state (Reserved, DeviceAuthRegistered,
 *    PublicIdentityUploaded, CommitArmed), preventing a transient error from destroying the
 *    evidence needed to resume an armed commit.
 *  - [expiredOrNull] is skipped whenever the binding is armed or bound, so an already-armed
 *    transaction cannot be downgraded to [Expired] by a local clock or a stale grant.
 *  - The registration grant is persisted through [RegistrationSessionStore] only as an
 *    authenticated, Keystore-wrapped AES-GCM ciphertext.
 *
 * This is transaction resume, never account recovery or device replacement.
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

    /**
     * The last durably recorded registration state; safe to call after a crash/restart.
     *
     * If the session store cannot be read or authenticated, this returns a synthetic
     * [RegistrationState.Failed] rather than pretending the state is [NotStarted]. Callers must
     * always use [canStartNew] (which consults [DeviceAuthBindingStore]) before any new
     * transaction can begin.
     */
    fun currentState(): RegistrationState = try {
        sessionStore.load()
    } catch (e: RegistrationSessionSecurityException) {
        RegistrationState.Failed("registration session is unreadable: ${e.message}")
    }

    /** Step 1: reserve [licenseCode] and [username] together. */
    fun reserve(username: Username, licenseCode: LicenseCode): RegistrationState {
        val current = currentState()
        check(canStartNew(current)) {
            "cannot start a new registration while one is already in progress or this device is bound/armed: $current"
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
        val current = currentState()
        val reserved = current as? RegistrationState.Reserved
            ?: return failStep(current, "registerDeviceAuth requires Reserved state, was $current")

        expiredOrNull(current, nowForGrantStalenessCheck)?.let { return it }

        if (deviceAuthKeyManager.status() is DeviceAuthKeyStatus.TerminalKeyLoss) {
            return failStep(
                current,
                "Device Auth key is in a terminal state for this installation; " +
                    "registration cannot proceed. There is no recovery or re-binding in V1."
            )
        }
        val signer = try {
            deviceAuthKeyManager.createKeyIfAbsent()
            deviceAuthKeyManager.signer()
        } catch (e: DeviceAuthTerminalStateException) {
            return failStep(current, "Device Auth key is in a terminal state: ${e.message}")
        } catch (e: DeviceAuthNotProductionEligibleException) {
            return failStep(current, "Device Auth key is not production eligible: ${e.message}")
        }

        // Fail closed before any remote call if the Device Auth key is not StrongBox/TEE.
        if (!deviceAuthKeyManager.isProductionEligible()) {
            val level = deviceAuthKeyManager.hardwareSecurityLevel() ?: HardwareSecurityLevel.UNKNOWN
            return failStep(
                current,
                "Device Auth key is not production eligible: $level. " +
                    "B-002 requires StrongBox or TEE."
            )
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
        val current = currentState()
        val registered = current as? RegistrationState.DeviceAuthRegistered
            ?: return failStep(current, "uploadPublicIdentity requires DeviceAuthRegistered state, was $current")

        expiredOrNull(current, nowForGrantStalenessCheck)?.let { return it }

        val material = try {
            e2eeStep.ensurePublicIdentityMaterial(oneTimeKeyCount)
        } catch (e: LocalE2eeIdentityStepException) {
            return failStep(current, "local E2EE identity material unavailable: ${e.message}")
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

    /** Step 4: arm the fail-closed guard and request the atomic final commit. */
    fun commit(nowForGrantStalenessCheck: Instant = Instant.now()): RegistrationState {
        val current = currentState()
        val payload = when (current) {
            is RegistrationState.PublicIdentityUploaded ->
                CommitPayload(current.registrationId, current.grant, current.username, current.deviceAuthJwkThumbprint)
            is RegistrationState.CommitArmed ->
                CommitPayload(current.registrationId, current.grant, current.username, current.deviceAuthJwkThumbprint)
            else -> return failStep(current, "commit requires PublicIdentityUploaded or CommitArmed state, was $current")
        }

        expiredOrNull(current, nowForGrantStalenessCheck)?.let { return it }

        // Re-validate Device Auth identity / eligibility before the irreversible arming.
        // This catches key loss / downgrade / thumbprint changes between registration steps.
        when (val validation = validateDeviceAuthForCommit(payload.deviceAuthJwkThumbprint)) {
            is DeviceAuthValidation.Valid -> { /* proceed */ }
            is DeviceAuthValidation.Invalid ->
                return failStep(current, "Device Auth revalidation failed: ${validation.reason}")
        }

        // Persist the armed state to the encrypted session store first. If this fails, the
        // durable guard has not been armed and the remote call is not attempted.
        val armed = RegistrationState.CommitArmed(
            payload.registrationId,
            payload.grant,
            payload.username,
            payload.deviceAuthJwkThumbprint
        )
        try {
            if (current !is RegistrationState.CommitArmed) {
                sessionStore.save(armed)
            }
        } catch (e: Exception) {
            return failStep(current, "could not persist armed commit state: ${e.message}")
        }

        // Arm the durable fail-closed guard next. The remote endpoint must not be called until
        // this succeeds, because from this point on a missing Device Auth key must be terminal.
        try {
            deviceAuthBindingStore.markArmed()
        } catch (e: Exception) {
            return failStep(armed, "could not arm pre-commit fail-closed guard: ${e.message}")
        }

        val result = try {
            api.commitRegistration(armed.registrationId, armed.grant)
        } catch (e: Exception) {
            return failStep(armed, "commit attempt did not produce an authoritative response; retry with the same Device Auth key")
        }
        val next = when (result) {
            is CommitResult.Committed -> {
                // The binding marker MUST become durable before the Committed state is saved.
                // If anything fails after this point (save, clear), the installation is already
                // marked bound, so a later key loss is terminal and retrying commit is safe.
                deviceAuthBindingStore.markBound()
                RegistrationState.Committed(result.accountId, result.deviceId, armed.username)
            }
            is CommitResult.Rejected -> RegistrationState.Failed("commit rejected: ${result.reason}")
        }
        sessionStore.save(next)

        if (next is RegistrationState.Committed) {
            sessionStore.clear()
        }
        return next
    }

    /** Explicitly abandons an in-progress registration transaction. Not account deletion. */
    fun abandon() {
        val current = currentState()
        if (current.isTerminal ||
            current is RegistrationState.CommitArmed ||
            deviceAuthBindingStore.isBound() ||
            deviceAuthBindingStore.isArmed()) {
            return
        }
        sessionStore.clear()
    }

    internal fun canStartNew(state: RegistrationState): Boolean {
        if (deviceAuthBindingStore.isBound() || deviceAuthBindingStore.isArmed()) return false
        return when (state) {
            is RegistrationState.NotStarted,
            is RegistrationState.Expired,
            is RegistrationState.Failed -> true
            else -> false
        }
    }

    private fun expiredOrNull(state: RegistrationState, now: Instant): RegistrationState? {
        // Once the binding is durable (armed or bound), the local grant TTL is irrelevant; the
        // server already accepted (or will idempotently re-accept) the commit.
        if (deviceAuthBindingStore.isBound() || deviceAuthBindingStore.isArmed()) return null

        // CommitArmed is a client-side safety precondition. Once the session has durably
        // reached this state, grant expiry must NOT permit a downgrade to a fresh-registration
        // state, even if the separate binding marker update failed/crashed.
        if (state is RegistrationState.CommitArmed) return null

        fun handle(s: RegistrationState): RegistrationState? = when (s) {
            is RegistrationState.Reserved ->
                if (s.grant.isExpired(now)) {
                    val expired = RegistrationState.Expired(s.registrationId)
                    sessionStore.save(expired)
                    expired
                } else null
            is RegistrationState.DeviceAuthRegistered ->
                if (s.grant.isExpired(now)) {
                    val expired = RegistrationState.Expired(s.registrationId)
                    sessionStore.save(expired)
                    expired
                } else null
            is RegistrationState.PublicIdentityUploaded ->
                if (s.grant.isExpired(now)) {
                    val expired = RegistrationState.Expired(s.registrationId)
                    sessionStore.save(expired)
                    expired
                } else null
            else -> null
        }
        return handle(state)
    }

    /**
     * Records a step failure. It is fail-closed:
     *  - it never overwrites a terminal [Committed] state;
     *  - it never overwrites a durable armed/bound session, because the in-progress state may be
     *    required to resume an armed commit;
     *  - it never overwrites any resumable in-progress state ([Reserved], [DeviceAuthRegistered],
     *    [PublicIdentityUploaded], [CommitArmed]), so a transient error does not destroy evidence;
     *  - it only persists [Failed] when the current state is [NotStarted] or already [Failed].
     *
     * The returned [RegistrationState.Failed] still lets the caller see that the step did not
     * succeed, while the durable state remains unchanged.
     */
    private fun failStep(current: RegistrationState, reason: String): RegistrationState {
        if (current.isTerminal) return current
        if (current is RegistrationState.NotStarted || current is RegistrationState.Failed) {
            val failed = RegistrationState.Failed(reason)
            sessionStore.save(failed)
            return failed
        }
        return RegistrationState.Failed(reason)
    }

    /**
     * Re-validates the Device Auth key immediately before the irreversible arming/commit step.
     *
     * Required invariant: the key must exist, be production eligible, and be the same public
     * identity that was registered earlier in this transaction.
     */
    private fun validateDeviceAuthForCommit(expectedThumbprint: String): DeviceAuthValidation {
        if (deviceAuthKeyManager.status() is DeviceAuthKeyStatus.TerminalKeyLoss) {
            return DeviceAuthValidation.Invalid("Device Auth key is in a terminal key-loss state")
        }

        if (!deviceAuthKeyManager.isProductionEligible()) {
            val level = deviceAuthKeyManager.hardwareSecurityLevel() ?: HardwareSecurityLevel.UNKNOWN
            return DeviceAuthValidation.Invalid(
                "Device Auth key is not production eligible: $level. B-002 requires StrongBox or TEE."
            )
        }

        val currentThumbprint = try {
            deviceAuthKeyManager.signer().jwkThumbprint()
        } catch (e: DeviceAuthTerminalStateException) {
            return DeviceAuthValidation.Invalid("Device Auth key is no longer usable: ${e.message}")
        }

        if (currentThumbprint != expectedThumbprint) {
            return DeviceAuthValidation.Invalid(
                "Device Auth thumbprint changed since registration: expected $expectedThumbprint, got $currentThumbprint"
            )
        }

        return DeviceAuthValidation.Valid
    }

    private sealed class DeviceAuthValidation {
        object Valid : DeviceAuthValidation()
        data class Invalid(val reason: String) : DeviceAuthValidation()
    }

    companion object {
        /** Foundation default; the real value is a future B-004/B-005 decision. */
        const val DEFAULT_ONE_TIME_KEY_COUNT: Int = 20
    }

    private data class CommitPayload(
        val registrationId: RegistrationId,
        val grant: RegistrationGrant,
        val username: Username,
        val deviceAuthJwkThumbprint: String
    )
}
