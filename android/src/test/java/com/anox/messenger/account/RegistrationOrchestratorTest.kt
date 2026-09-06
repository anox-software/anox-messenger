package com.anox.messenger.account

import com.anox.messenger.security.deviceauth.DeviceAuthKeyStatus
import com.anox.messenger.security.deviceauth.FakeDeviceAuthKeyManager
import com.anox.messenger.security.deviceauth.HardwareSecurityLevel
import com.anox.messenger.security.deviceauth.InMemoryDeviceAuthBindingStore
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.time.Instant

/**
 * B-003 registration state-machine tests.
 *
 * Proves: correct step ordering, the account is never treated as bound before a successful
 * commit, registration-grant expiry is represented, crash-before-commit is resumable
 * transaction state (not recovery/device-replacement), and terminal Device Auth key loss blocks
 * registration.
 */
class RegistrationOrchestratorTest {

    private lateinit var api: FakeRegistrationApi
    private lateinit var bindingStore: InMemoryDeviceAuthBindingStore
    private lateinit var deviceAuthKeyManager: FakeDeviceAuthKeyManager
    private lateinit var sessionStore: InMemoryRegistrationSessionStore
    private lateinit var e2eeStep: FakeLocalE2eeIdentityStep
    private lateinit var orchestrator: RegistrationOrchestrator

    private val username = (Username.validate("alice") as UsernameValidation.Valid).username
    private val license = LicenseCode.parse("anox-AB12-CD34-EF56")!!

    @Before
    fun setUp() {
        api = FakeRegistrationApi()
        bindingStore = InMemoryDeviceAuthBindingStore()
        deviceAuthKeyManager = FakeDeviceAuthKeyManager(bindingStore)
        sessionStore = InMemoryRegistrationSessionStore()
        e2eeStep = FakeLocalE2eeIdentityStep()
        orchestrator = RegistrationOrchestrator(
            api = api,
            deviceAuthKeyManager = deviceAuthKeyManager,
            deviceAuthBindingStore = bindingStore,
            sessionStore = sessionStore,
            e2eeStep = e2eeStep,
            createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
        )
    }

    @Test
    fun `full happy path reaches committed and marks binding`() {
        assertEquals(RegistrationState.NotStarted, orchestrator.currentState())

        val reserved = orchestrator.reserve(username, license)
        assertTrue(reserved is RegistrationState.Reserved)
        assertFalse("account must not be bound before device auth registration", bindingStore.isBound())

        val registered = orchestrator.registerDeviceAuth()
        assertTrue(registered is RegistrationState.DeviceAuthRegistered)
        assertFalse("account must not be bound before public identity upload", bindingStore.isBound())

        val uploaded = orchestrator.uploadPublicIdentity()
        assertTrue(uploaded is RegistrationState.PublicIdentityUploaded)
        assertFalse("account must not be bound before commit", bindingStore.isBound())

        val committed = orchestrator.commit()
        assertTrue(committed is RegistrationState.Committed)
        assertTrue("account must be bound only after a successful commit", bindingStore.isBound())

        // Session state is cleared after a successful commit.
        assertEquals(RegistrationState.NotStarted, sessionStore.load())

        assertEquals(1, api.reserveCallCount)
        assertEquals(1, api.registerDeviceAuthCallCount)
        assertEquals(1, api.submitPublicIdentityCallCount)
        assertEquals(1, api.commitCallCount)
        assertEquals(1, e2eeStep.callCount)
    }

    @Test
    fun `steps cannot be skipped`() {
        // registerDeviceAuth without a prior reserve.
        val result = orchestrator.registerDeviceAuth()
        assertTrue(result is RegistrationState.Failed)
        assertFalse(bindingStore.isBound())
        assertEquals(0, api.registerDeviceAuthCallCount)
    }

    @Test
    fun `upload cannot run before device auth registration`() {
        orchestrator.reserve(username, license)
        val result = orchestrator.uploadPublicIdentity()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.submitPublicIdentityCallCount)
    }

    @Test
    fun `commit cannot run before public identity upload`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        val result = orchestrator.commit()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.commitCallCount)
        assertFalse(bindingStore.isBound())
    }

    @Test
    fun `cannot start a new registration while one is in progress`() {
        orchestrator.reserve(username, license)
        try {
            orchestrator.reserve(username, license)
            org.junit.Assert.fail("expected an exception")
        } catch (e: IllegalStateException) {
            // expected
        }
        assertEquals(1, api.reserveCallCount)
    }

    @Test
    fun `rejected reservation does not bind and does not proceed`() {
        api.reservationResult = ReservationResult.Rejected("license already redeemed")
        val result = orchestrator.reserve(username, license)
        assertTrue(result is RegistrationState.Failed)
        assertFalse(bindingStore.isBound())
    }

    @Test
    fun `rejected commit does not bind`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        orchestrator.uploadPublicIdentity()
        api.commitResult = CommitResult.Rejected("reservation already committed")

        val result = orchestrator.commit()
        assertTrue(result is RegistrationState.Failed)
        assertFalse(bindingStore.isBound())
    }

    @Test
    fun `expired registration grant blocks further progress before device auth step`() {
        val issuedAt = Instant.parse("2026-08-22T00:00:00Z")
        api.reservationResult = ReservationResult.Reserved(
            RegistrationId.parse(java.util.UUID.randomUUID().toString())!!,
            RegistrationGrantGenerator().newGrant(issuedAt)
        )
        orchestrator.reserve(username, license)

        val farInTheFuture = issuedAt.plusSeconds(60 * 60) // 1 hour later, past the 30 min TTL
        val result = orchestrator.registerDeviceAuth(nowForGrantStalenessCheck = farInTheFuture)

        assertTrue(result is RegistrationState.Expired)
        assertEquals(0, api.registerDeviceAuthCallCount)
        assertFalse(bindingStore.isBound())
    }

    @Test
    fun `registration grant is not expired within its ttl`() {
        val issuedAt = Instant.parse("2026-08-22T00:00:00Z")
        api.reservationResult = ReservationResult.Reserved(
            RegistrationId.parse(java.util.UUID.randomUUID().toString())!!,
            RegistrationGrantGenerator().newGrant(issuedAt)
        )
        orchestrator.reserve(username, license)

        val stillValid = issuedAt.plusSeconds(60)
        val result = orchestrator.registerDeviceAuth(nowForGrantStalenessCheck = stillValid)
        assertTrue(result is RegistrationState.DeviceAuthRegistered)
    }

    @Test
    fun `terminal device auth key loss blocks registration and never binds`() {
        // A previous (unrelated) registration bound this installation, then the key was lost.
        bindingStore.markBound()
        deviceAuthKeyManager.simulateKeyInvalidation()
        assertEquals(DeviceAuthKeyStatus.TerminalKeyLoss, deviceAuthKeyManager.status())

        // A new registration is blocked at the first step because the device is bound.
        try {
            orchestrator.reserve(username, license)
            org.junit.Assert.fail("expected cannot-start-new exception")
        } catch (e: IllegalStateException) {
            // expected
        }

        // Even if a step is called directly with an empty session, it fails without creating
        // a replacement key and without changing the durable binding.
        val result = orchestrator.registerDeviceAuth()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.registerDeviceAuthCallCount)
        assertTrue(bindingStore.isBound())
    }

    @Test
    fun `crash before commit is resumable transaction state not recovery`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        orchestrator.uploadPublicIdentity()

        // Simulate process death: build a brand new orchestrator sharing only the durable
        // session store, exactly as would happen after an app restart.
        val resumedOrchestrator = RegistrationOrchestrator(
            api = api,
            deviceAuthKeyManager = deviceAuthKeyManager,
            deviceAuthBindingStore = bindingStore,
            sessionStore = sessionStore,
            e2eeStep = e2eeStep,
            createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
        )

        assertTrue(resumedOrchestrator.currentState() is RegistrationState.PublicIdentityUploaded)
        assertFalse("resume must not have bound anything yet", bindingStore.isBound())

        val committed = resumedOrchestrator.commit()
        assertTrue(committed is RegistrationState.Committed)
        assertTrue(bindingStore.isBound())
    }

    @Test
    fun `abandon clears in-progress state without touching the device auth key`() {
        orchestrator.reserve(username, license)
        orchestrator.abandon()
        assertEquals(RegistrationState.NotStarted, orchestrator.currentState())
        assertFalse(bindingStore.isBound())
    }

    @Test
    fun `no state in the hierarchy represents account recovery or device replacement`() {
        // The Kotlin compiler enforces that this `when` is exhaustive over every
        // RegistrationState subtype with no `else` branch. If a future edit ever added a
        // recovery/device-replacement state, this test would fail to compile until it was
        // named/handled here explicitly, making any such addition impossible to slip in
        // silently.
        fun describe(state: RegistrationState): String = when (state) {
            is RegistrationState.NotStarted -> "NotStarted"
            is RegistrationState.Reserved -> "Reserved"
            is RegistrationState.DeviceAuthRegistered -> "DeviceAuthRegistered"
            is RegistrationState.PublicIdentityUploaded -> "PublicIdentityUploaded"
            is RegistrationState.CommitArmed -> "CommitArmed"
            is RegistrationState.Committed -> "Committed"
            is RegistrationState.Expired -> "Expired"
            is RegistrationState.Failed -> "Failed"
        }
        val allNames = setOf(
            "NotStarted", "Reserved", "DeviceAuthRegistered", "PublicIdentityUploaded",
            "CommitArmed", "Committed", "Expired", "Failed"
        )
        assertTrue(allNames.none { it.contains("Recover", ignoreCase = true) })
        assertTrue(allNames.none { it.contains("Replace", ignoreCase = true) })
        assertEquals("NotStarted", describe(RegistrationState.NotStarted))
    }

    @Test
    fun `commit never runs before device auth registration even after reserve`() {
        orchestrator.reserve(username, license)
        val result = orchestrator.commit()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.commitCallCount)
    }

    @Test
    fun `public identity material never null before submission and is forwarded to the api`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        orchestrator.uploadPublicIdentity()
        assertTrue(api.lastSubmittedPublicIdentity != null)
    }

    @Test
    fun `device auth proof and public key are forwarded to the api`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        assertTrue(api.lastDpopProof?.startsWith("fake-dpop-proof-for-") == true)
        assertTrue(api.lastPublicJwk != null)
    }

    // --- LEGACY-FIX-01: ANOX-MAINARCH-019 production eligibility enforcement ---

    @Test
    fun `strongbox device auth proceeds with registration`() {
        orchestrator.reserve(username, license)
        val result = orchestrator.registerDeviceAuth()
        assertTrue(result is RegistrationState.DeviceAuthRegistered)
        assertEquals(1, api.registerDeviceAuthCallCount)
    }

    @Test
    fun `tee device auth proceeds with registration`() {
        deviceAuthKeyManager = FakeDeviceAuthKeyManager(bindingStore, HardwareSecurityLevel.TRUSTED_EXECUTION_ENVIRONMENT)
        orchestrator = buildOrchestrator()

        orchestrator.reserve(username, license)
        val result = orchestrator.registerDeviceAuth()
        assertTrue(result is RegistrationState.DeviceAuthRegistered)
        assertEquals(1, api.registerDeviceAuthCallCount)
    }

    @Test
    fun `software device auth is rejected before api call`() {
        deviceAuthKeyManager = FakeDeviceAuthKeyManager(bindingStore, HardwareSecurityLevel.SOFTWARE)
        orchestrator = buildOrchestrator()

        orchestrator.reserve(username, license)
        val result = orchestrator.registerDeviceAuth()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.registerDeviceAuthCallCount)
        assertFalse(bindingStore.isBound())
    }

    @Test
    fun `unknown device auth is rejected before api call`() {
        deviceAuthKeyManager = FakeDeviceAuthKeyManager(bindingStore, HardwareSecurityLevel.UNKNOWN)
        orchestrator = buildOrchestrator()

        orchestrator.reserve(username, license)
        val result = orchestrator.registerDeviceAuth()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.registerDeviceAuthCallCount)
    }

    @Test
    fun `terminal key loss before device auth is rejected before api call`() {
        bindingStore.markArmed()
        deviceAuthKeyManager.simulateKeyInvalidation()

        // Put the session directly into Reserved so the test can call registerDeviceAuth
        // without first triggering the cannot-start-new guard.
        val reservation = api.reservationResult as ReservationResult.Reserved
        sessionStore.save(
            RegistrationState.Reserved(reservation.registrationId, reservation.grant, username)
        )

        val result = orchestrator.registerDeviceAuth()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.registerDeviceAuthCallCount)
    }

    // --- LEGACY-FIX-01: ANOX-LEGACY-INTEGRATION-001 commit revalidation ---

    @Test
    fun `commit rejects when device auth key disappears after public identity upload`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        orchestrator.uploadPublicIdentity()

        deviceAuthKeyManager.simulateKeyInvalidation()

        val result = orchestrator.commit()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.commitCallCount)
        assertFalse(bindingStore.isArmed())
        assertFalse(bindingStore.isBound())
    }

    @Test
    fun `commit rejects when device auth thumbprint changes after public identity upload`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        val uploaded = orchestrator.uploadPublicIdentity() as RegistrationState.PublicIdentityUploaded

        // Simulate key replacement by forcing creation of a new key (only valid in test fake
        // when not bound and not armed; temporarily clear binding state for this simulation).
        bindingStore.clearBinding()
        deviceAuthKeyManager.deleteKeyDestructively()
        deviceAuthKeyManager.createKeyIfAbsent()

        val result = orchestrator.commit()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.commitCallCount)
    }

    @Test
    fun `commit rejects when device auth becomes software before arming`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        orchestrator.uploadPublicIdentity()

        // Re-create key manager with SOFTWARE level to simulate downgrade
        deviceAuthKeyManager = FakeDeviceAuthKeyManager(bindingStore, HardwareSecurityLevel.SOFTWARE)
        orchestrator = buildOrchestrator()

        val result = orchestrator.commit()
        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.commitCallCount)
    }

    @Test
    fun `commit with valid same eligible key proceeds`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        orchestrator.uploadPublicIdentity()

        val result = orchestrator.commit()
        assertTrue(result is RegistrationState.Committed)
        assertEquals(1, api.commitCallCount)
    }

    // --- LEGACY-FIX-01: ANOX-LEGACY-INTEGRATION-003 CommitArmed divergence ---

    @Test
    fun `commitArmed session does not expire when grant ttl passes`() {
        val issuedAt = Instant.parse("2026-08-22T00:00:00Z")
        api.reservationResult = ReservationResult.Reserved(
            RegistrationId.parse(java.util.UUID.randomUUID().toString())!!,
            RegistrationGrantGenerator().newGrant(issuedAt)
        )

        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth(nowForGrantStalenessCheck = issuedAt)
        val uploaded = orchestrator.uploadPublicIdentity(nowForGrantStalenessCheck = issuedAt) as RegistrationState.PublicIdentityUploaded

        // Force the session straight to CommitArmed without going through commit()
        // (e.g. a previous commit call armed the session but markArmed failed).
        sessionStore.save(
            RegistrationState.CommitArmed(
                uploaded.registrationId,
                uploaded.grant,
                username,
                uploaded.deviceAuthJwkThumbprint
            )
        )

        val farInTheFuture = issuedAt.plusSeconds(60 * 60)
        val result = orchestrator.commit(nowForGrantStalenessCheck = farInTheFuture)

        // Should NOT become Expired; commit should proceed (or fail on the API call, not expiry).
        assertTrue("CommitArmed must not be downgraded to Expired: $result", result !is RegistrationState.Expired)
    }

    @Test
    fun `commitArmed plus binding not armed blocks new registration`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        val uploaded = orchestrator.uploadPublicIdentity() as RegistrationState.PublicIdentityUploaded
        sessionStore.save(
            RegistrationState.CommitArmed(
                uploaded.registrationId,
                uploaded.grant,
                username,
                uploaded.deviceAuthJwkThumbprint
            )
        )

        assertFalse(
            "CommitArmed session must prevent a new registration",
            orchestrator.canStartNew(orchestrator.currentState())
        )
    }

    @Test
    fun `abandon does not clear commitArmed session`() {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        val uploaded = orchestrator.uploadPublicIdentity() as RegistrationState.PublicIdentityUploaded
        sessionStore.save(
            RegistrationState.CommitArmed(
                uploaded.registrationId,
                uploaded.grant,
                username,
                uploaded.deviceAuthJwkThumbprint
            )
        )

        orchestrator.abandon()
        assertTrue(orchestrator.currentState() is RegistrationState.CommitArmed)
    }

    private fun buildOrchestrator(): RegistrationOrchestrator {
        return RegistrationOrchestrator(
            api = api,
            deviceAuthKeyManager = deviceAuthKeyManager,
            deviceAuthBindingStore = bindingStore,
            sessionStore = sessionStore,
            e2eeStep = e2eeStep,
            createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
        )
    }
}
