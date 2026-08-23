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
 * Crash-consistency / Device Auth safety design:
 *  - [DeviceAuthBindingStore] is the durable fail-closed guard. If it says the installation is
 *    bound, [canStartNew] is always false and the key manager treats key loss as terminal.
 *  - `commit()` first durably marks the binding via [DeviceAuthBindingStore.markBound] and only
 *    then persists [RegistrationState.Committed]. A crash between these two writes leaves
 *    `isBound == true` with the session still at [PublicIdentityUploaded]; retrying `commit()`
 *    is safe because the remote call is idempotent and `markBound()` is idempotent.
 *  - [RegistrationState.Committed] is terminal. [failStep] will never overwrite it, and
 *    [canStartNew] rejects it.
 *  - [failStep] also refuses to overwrite any in-progress state once the binding has been marked
 *    true, preventing a transient error from destroying the evidence needed to resume a bound
 *    commit.
 *  - [expiredOrNull] is skipped whenever the binding is already true, so an already-committed
 *    (or binding-marked) transaction cannot be downgraded to [Expired] by a local clock.
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
            "cannot start a new registration while one is already in progress or this device is bound: $current"
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

    /** Step 4: request the atomic final commit. */
    fun commit(nowForGrantStalenessCheck: Instant = Instant.now()): RegistrationState {
        val current = currentState()
        val uploaded = current as? RegistrationState.PublicIdentityUploaded
            ?: return failStep(current, "commit requires PublicIdentityUploaded state, was $current")

        expiredOrNull(current, nowForGrantStalenessCheck)?.let { return it }

        val result = api.commitRegistration(uploaded.registrationId, uploaded.grant)
        val next = when (result) {
            is CommitResult.Committed -> {
                // The binding marker MUST become durable before the Committed state is saved.
                // If anything fails after this point (save, clear), the installation is already
                // marked bound, so a later key loss is terminal and retrying commit is safe.
                deviceAuthBindingStore.markBound()
                RegistrationState.Committed(result.accountId, result.deviceId, uploaded.username)
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
        if (current.isTerminal || deviceAuthBindingStore.isBound()) {
            return
        }
        sessionStore.clear()
    }

    private fun canStartNew(state: RegistrationState): Boolean {
        if (deviceAuthBindingStore.isBound()) return false
        return when (state) {
            is RegistrationState.NotStarted,
            is RegistrationState.Expired,
            is RegistrationState.Failed -> true
            else -> false
        }
    }

    private fun expiredOrNull(state: RegistrationState, now: Instant): RegistrationState? {
        // Once the binding is durable, the local grant TTL is irrelevant; the server already
        // accepted (or will idempotently re-accept) the commit.
        if (deviceAuthBindingStore.isBound()) return null

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
     * Records a step failure. It is fail-closed: it never overwrites a terminal [Committed]
     * state and never overwrites any in-progress state once [DeviceAuthBindingStore] says this
     * installation is bound, because the in-progress session may be required to complete a
     * binding that has already been durably marked.
     *
     * When the binding is already true, the method still returns [RegistrationState.Failed] (so
     * the caller sees a clear failure) but does **not** save it, preserving any existing session.
     */
    private fun failStep(current: RegistrationState, reason: String): RegistrationState {
        if (current.isTerminal) return current
        if (deviceAuthBindingStore.isBound()) {
            return RegistrationState.Failed(reason)
        }
        val failed = RegistrationState.Failed(reason)
        sessionStore.save(failed)
        return failed
    }

    companion object {
        /** Foundation default; the real value is a future B-004/B-005 decision. */
        const val DEFAULT_ONE_TIME_KEY_COUNT: Int = 20
    }
}
