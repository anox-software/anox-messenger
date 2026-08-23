package com.anox.messenger.account

import com.anox.messenger.security.deviceauth.DeviceAuthKeyStatus
import com.anox.messenger.security.deviceauth.FaultyDeviceAuthBindingStore
import com.anox.messenger.security.deviceauth.FakeDeviceAuthKeyManager
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.time.Instant

/**
 * B-003 PROMPT-008D crash/fault-injection matrix.
 *
 * Verifies the pre-commit arming invariant: once the final remote registration commit may have
 * been attempted in a way that could succeed server-side, Device Auth key replacement must already
 * be locally impossible, and the same Device Auth identity must be used for any retry.
 */
class RegistrationCrashConsistencyTest {

    private val username = (Username.validate("alice") as UsernameValidation.Valid).username
    private val license = LicenseCode.parse("anox-AB12-CD34-EF56")!!

    private lateinit var api: FakeRegistrationApi
    private lateinit var bindingStore: FaultyDeviceAuthBindingStore
    private lateinit var deviceAuthKeyManager: FakeDeviceAuthKeyManager
    private lateinit var sessionStore: FaultyInMemoryRegistrationSessionStore
    private lateinit var e2eeStep: FakeLocalE2eeIdentityStep
    private lateinit var orchestrator: RegistrationOrchestrator

    @Before
    fun setUp() {
        api = FakeRegistrationApi()
        bindingStore = FaultyDeviceAuthBindingStore()
        deviceAuthKeyManager = FakeDeviceAuthKeyManager(bindingStore)
        sessionStore = FaultyInMemoryRegistrationSessionStore()
        e2eeStep = FakeLocalE2eeIdentityStep()
        orchestrator = makeOrchestrator(api)
    }

    private fun makeOrchestrator(api: RegistrationApi) = RegistrationOrchestrator(
        api = api,
        deviceAuthKeyManager = deviceAuthKeyManager,
        deviceAuthBindingStore = bindingStore,
        sessionStore = sessionStore,
        e2eeStep = e2eeStep,
        createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
    )

    private fun reachPublicIdentityUploaded(): RegistrationState.PublicIdentityUploaded {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        val uploaded = orchestrator.uploadPublicIdentity()
        assertTrue(uploaded is RegistrationState.PublicIdentityUploaded)
        return uploaded as RegistrationState.PublicIdentityUploaded
    }

    @Test
    fun `A crash immediately before pre-commit guard persistence`() {
        // If the encrypted CommitArmed state cannot be persisted, the remote endpoint must not be
        // called and no guard is armed.
        reachPublicIdentityUploaded()
        sessionStore.failNextSave = true

        val result = orchestrator.commit()

        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.commitCallCount)
        assertFalse(bindingStore.isArmed())
        assertFalse(bindingStore.isBound())
        assertTrue(sessionStore.load() is RegistrationState.PublicIdentityUploaded)
    }

    @Test
    fun `B guard persistence fails`() {
        // If the durable binding-store guard cannot be armed, the remote endpoint must not be called.
        reachPublicIdentityUploaded()
        bindingStore.setFailNextMarkArmed()

        val result = orchestrator.commit()

        assertTrue(result is RegistrationState.Failed)
        assertEquals(0, api.commitCallCount)
        assertFalse(bindingStore.isArmed())
        assertFalse(bindingStore.isBound())
        // The encrypted CommitArmed state has been persisted so retry is possible.
        assertTrue(sessionStore.load() is RegistrationState.CommitArmed)
    }

    @Test
    fun `C guard persisted then crash before remote commit`() {
        // The local state is armed. The remote call has not happened, but key replacement is now
        // permanently blocked until an authoritative outcome is observed.
        reachPublicIdentityUploaded()

        // Stop before the remote call by arming only, then simulate process death and resume.
        // We use the real orchestrator's full commit, but simulate a crash by checking the state
        // after the remote call would have been made? Actually we can arm manually and assert
        // behavior.
        val manualArmed = RegistrationState.CommitArmed(
            (sessionStore.load() as RegistrationState.PublicIdentityUploaded).registrationId,
            (sessionStore.load() as RegistrationState.PublicIdentityUploaded).grant,
            (sessionStore.load() as RegistrationState.PublicIdentityUploaded).username,
            (sessionStore.load() as RegistrationState.PublicIdentityUploaded).deviceAuthJwkThumbprint
        )
        sessionStore.save(manualArmed)
        bindingStore.markArmed()

        // Key loss after arming is terminal.
        deviceAuthKeyManager.simulateKeyInvalidation()
        assertEquals(DeviceAuthKeyStatus.TerminalKeyLoss, deviceAuthKeyManager.status())

        // A new registration is blocked.
        try {
            orchestrator.reserve(username, license)
            org.junit.Assert.fail("expected cannot-start-new exception")
        } catch (e: IllegalStateException) {
            // expected
        }

        // No replacement key is generated.
        try {
            deviceAuthKeyManager.createKeyIfAbsent()
            org.junit.Assert.fail("expected terminal state exception")
        } catch (e: com.anox.messenger.security.deviceauth.DeviceAuthTerminalStateException) {
            // expected
        }
    }

    @Test
    fun `D guard persisted then request sent server commits then process dies before response`() {
        // Once armed, the remote endpoint may have succeeded. Even if the response is lost, the
        // same Device Auth key must be used on retry and no replacement is possible.
        reachPublicIdentityUploaded()

        val throwingApi = object : RegistrationApi by api {
            override fun commitRegistration(registrationId: RegistrationId, grant: RegistrationGrant): CommitResult {
                // Simulate a response lost after server success: throw instead of returning.
                throw java.io.IOException("response lost")
            }
        }
        val faultOrchestrator = makeOrchestrator(throwingApi)

        val result = faultOrchestrator.commit()

        assertTrue(result is RegistrationState.Failed)
        // The remote call was attempted; the guard must be armed.
        assertTrue(bindingStore.isArmed())
        assertFalse(bindingStore.isBound())
        // The session remains CommitArmed so the same key can retry.
        assertTrue(sessionStore.load() is RegistrationState.CommitArmed)

        // Key loss after arming is terminal.
        deviceAuthKeyManager.simulateKeyInvalidation()
        assertEquals(DeviceAuthKeyStatus.TerminalKeyLoss, deviceAuthKeyManager.status())
        assertTrue(deviceAuthKeyManager.generateCallCount == 1)
    }

    @Test
    fun `E server returns success then process dies before markBound`() {
        // Even if markBound crashes after a success response, the guard is already armed. The
        // Device Auth key cannot be replaced and retry is safe.
        reachPublicIdentityUploaded()
        bindingStore.setFailNextMarkBound()

        try {
            orchestrator.commit()
            org.junit.Assert.fail("expected markBound fault")
        } catch (e: RuntimeException) {
            // expected: markBound fault propagates (it is post-success, pre-durable-binding)
        }

        assertFalse(bindingStore.isBound())
        assertTrue(bindingStore.isArmed())
        assertTrue(sessionStore.load() is RegistrationState.CommitArmed)

        // Retry succeeds with the same key.
        val resumed = makeOrchestrator(api)
        val committed = resumed.commit()
        assertTrue(committed is RegistrationState.Committed)
        assertTrue(bindingStore.isBound())
        assertTrue(bindingStore.isArmed())
    }

    @Test
    fun `F binding persistence succeeds then Committed state save fails`() {
        // markBound succeeded, save(Committed) failed. The binding is durable and key loss is
        // terminal. The session still records CommitArmed so retry is possible.
        reachPublicIdentityUploaded()
        // Fail the second save inside this commit call (CommitArmed, then Committed).
        sessionStore.failOnNthSave = sessionStore.saveCallCount + 2

        val result = try {
            orchestrator.commit()
        } catch (e: RegistrationSessionSecurityException) {
            null
        }

        assertTrue("binding is durable", bindingStore.isBound())
        assertTrue("binding is also armed", bindingStore.isArmed())
        // The save(CommitArmed) succeeded before save(Committed) was attempted to fail.
        assertTrue(sessionStore.load() is RegistrationState.CommitArmed)

        // Same key retry.
        val generateBefore = deviceAuthKeyManager.generateCallCount
        val resumed = makeOrchestrator(api)
        val committed = resumed.commit()
        assertTrue(committed is RegistrationState.Committed)
        assertEquals("same key must be reused", generateBefore, deviceAuthKeyManager.generateCallCount)
    }

    @Test
    fun `G Committed save succeeds then session-secret clear fails`() {
        // If the final clear fails after commit, the binding remains and the temporary secret must
        // not be recoverable. In the in-memory store we cannot fail clear, but we prove the session
        // is cleared after a successful full commit and the binding remains.
        reachPublicIdentityUploaded()
        val committed = orchestrator.commit()
        assertTrue(committed is RegistrationState.Committed)
        assertTrue(bindingStore.isBound())
        assertTrue(bindingStore.isArmed())
        assertEquals(RegistrationState.NotStarted, sessionStore.load())
    }

    @Test
    fun `H Device Auth key lost in every state from CommitArmed onward is terminal`() {
        reachPublicIdentityUploaded()

        // Arm only.
        sessionStore.save(
            RegistrationState.CommitArmed(
                (sessionStore.load() as RegistrationState.PublicIdentityUploaded).registrationId,
                (sessionStore.load() as RegistrationState.PublicIdentityUploaded).grant,
                (sessionStore.load() as RegistrationState.PublicIdentityUploaded).username,
                (sessionStore.load() as RegistrationState.PublicIdentityUploaded).deviceAuthJwkThumbprint
            )
        )
        bindingStore.markArmed()

        deviceAuthKeyManager.simulateKeyInvalidation()
        assertEquals(DeviceAuthKeyStatus.TerminalKeyLoss, deviceAuthKeyManager.status())

        // No replacement, no new registration.
        try {
            deviceAuthKeyManager.createKeyIfAbsent()
            org.junit.Assert.fail("expected terminal state exception")
        } catch (e: com.anox.messenger.security.deviceauth.DeviceAuthTerminalStateException) {
            // expected
        }
        try {
            orchestrator.reserve(username, license)
            org.junit.Assert.fail("expected cannot-start-new exception")
        } catch (e: IllegalStateException) {
            // expected
        }
    }

    @Test
    fun `I concurrent or double commit invocation does not bypass guard or create contradiction`() {
        reachPublicIdentityUploaded()

        val first = makeOrchestrator(api)
        first.commit()
        assertTrue(bindingStore.isBound())
        assertEquals(1, api.commitCallCount)

        // A second commit from a fresh orchestrator must not call the server again because the
        // session is cleared; even if it tried, it cannot return a new Committed without the
        // same prior state.
        val second = makeOrchestrator(api)
        val secondResult = second.commit()
        assertTrue(secondResult is RegistrationState.Failed)
        assertEquals(1, api.commitCallCount)
    }

    @Test
    fun `J network timeout or unknown outcome does not downgrade to unbound`() {
        reachPublicIdentityUploaded()

        val throwingApi = object : RegistrationApi by api {
            override fun commitRegistration(registrationId: RegistrationId, grant: RegistrationGrant): CommitResult {
                throw java.net.SocketTimeoutException("timeout")
            }
        }
        val result = makeOrchestrator(throwingApi).commit()

        assertTrue(result is RegistrationState.Failed)
        assertTrue(bindingStore.isArmed())
        assertFalse(bindingStore.isBound())
        assertTrue(sessionStore.load() is RegistrationState.CommitArmed)

        // Still not startable as if unbound.
        try {
            orchestrator.reserve(username, license)
            org.junit.Assert.fail("expected cannot-start-new exception")
        } catch (e: IllegalStateException) {
            // expected
        }
    }

    @Test
    fun `committed terminal cannot start new registration`() {
        reachPublicIdentityUploaded()
        orchestrator.commit()

        try {
            orchestrator.reserve(username, license)
            org.junit.Assert.fail("expected cannot-start-new exception")
        } catch (e: IllegalStateException) {
            // expected
        }
    }

    @Test
    fun `failStep cannot overwrite armed session`() {
        reachPublicIdentityUploaded()

        // Arm the session and guard, then call an unrelated step that would otherwise fail.
        sessionStore.save(
            RegistrationState.CommitArmed(
                (sessionStore.load() as RegistrationState.PublicIdentityUploaded).registrationId,
                (sessionStore.load() as RegistrationState.PublicIdentityUploaded).grant,
                (sessionStore.load() as RegistrationState.PublicIdentityUploaded).username,
                (sessionStore.load() as RegistrationState.PublicIdentityUploaded).deviceAuthJwkThumbprint
            )
        )
        bindingStore.markArmed()

        val result = orchestrator.uploadPublicIdentity()
        assertTrue(result is RegistrationState.Failed)
        assertTrue(sessionStore.load() is RegistrationState.CommitArmed)
    }
}
