package com.anox.messenger.account

import com.anox.messenger.security.deviceauth.FaultyDeviceAuthBindingStore
import com.anox.messenger.security.deviceauth.FakeDeviceAuthKeyManager
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.time.Instant

/**
 * B-003 crash/fault-injection matrix.
 *
 * Verifies that the local state model is fail-closed around the final atomic commit: once a
 * remote commit may have succeeded, no locally reachable state may permit Device Auth key
 * replacement.
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
        orchestrator = RegistrationOrchestrator(
            api = api,
            deviceAuthKeyManager = deviceAuthKeyManager,
            deviceAuthBindingStore = bindingStore,
            sessionStore = sessionStore,
            e2eeStep = e2eeStep,
            createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
        )
    }

    private fun reachPublicIdentityUploaded(): RegistrationState.PublicIdentityUploaded {
        orchestrator.reserve(username, license)
        orchestrator.registerDeviceAuth()
        val uploaded = orchestrator.uploadPublicIdentity()
        assertTrue(uploaded is RegistrationState.PublicIdentityUploaded)
        return uploaded as RegistrationState.PublicIdentityUploaded
    }

    private fun makeOrchestrator() = RegistrationOrchestrator(
        api = api,
        deviceAuthKeyManager = deviceAuthKeyManager,
        deviceAuthBindingStore = bindingStore,
        sessionStore = sessionStore,
        e2eeStep = e2eeStep,
        createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
    )

    @Test
    fun `A crash before remote commit call leaves unbound resumable state`() {
        val uploaded = reachPublicIdentityUploaded()

        // Simulate crash by building a fresh orchestrator and continuing with a new commit call.
        val resumed = makeOrchestrator()
        assertEquals(uploaded, resumed.currentState())
        assertFalse(bindingStore.isBound())

        val committed = resumed.commit()
        assertTrue(committed is RegistrationState.Committed)
        assertTrue(bindingStore.isBound())
    }

    @Test
    fun `B remote commit throws before known success leaves unbound resumable state`() {
        reachPublicIdentityUploaded()

        // The API throws; the orchestrator does not know the commit outcome and must not mark bound.
        val throwingApi = object : RegistrationApi by api {
            override fun commitRegistration(registrationId: RegistrationId, grant: RegistrationGrant): CommitResult {
                throw RuntimeException("network fault")
            }
        }
        val faultOrchestrator = RegistrationOrchestrator(
            api = throwingApi,
            deviceAuthKeyManager = deviceAuthKeyManager,
            deviceAuthBindingStore = bindingStore,
            sessionStore = sessionStore,
            e2eeStep = e2eeStep,
            createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
        )

        try {
            faultOrchestrator.commit()
            org.junit.Assert.fail("expected exception")
        } catch (e: RuntimeException) {
            // expected
        }

        assertFalse("binding must not be marked when commit outcome is unknown", bindingStore.isBound())
        assertTrue(sessionStore.load() is RegistrationState.PublicIdentityUploaded)

        // Retry after the network recovers.
        val recovered = makeOrchestrator()
        val committed = recovered.commit()
        assertTrue(committed is RegistrationState.Committed)
        assertTrue(bindingStore.isBound())
    }

    @Test
    fun `C crash between remote commit success and local binding markBound`() {
        reachPublicIdentityUploaded()

        // markBound is the gap; make it fail once to simulate the crash before the binding was durable.
        bindingStore.setFailNextMarkBound()
        try {
            orchestrator.commit()
            org.junit.Assert.fail("expected exception")
        } catch (e: RuntimeException) {
            // expected
        }

        assertFalse(bindingStore.isBound())
        assertTrue(sessionStore.load() is RegistrationState.PublicIdentityUploaded)

        // A new orchestrator can retry from the same key and session.
        val resumed = makeOrchestrator()
        val committed = resumed.commit()
        assertTrue(committed is RegistrationState.Committed)
        assertTrue(bindingStore.isBound())
    }

    @Test
    fun `D binding durable but Committed state save failed is recoverable with same key`() {
        reachPublicIdentityUploaded()

        // commit will: call server (success), markBound (success), save(Committed) (fail)
        sessionStore.failNextSave = true
        try {
            orchestrator.commit()
            org.junit.Assert.fail("expected exception")
        } catch (e: RegistrationSessionSecurityException) {
            // expected
        }

        assertTrue("binding must already be durable even if state save failed", bindingStore.isBound())
        // Session should still be PublicIdentityUploaded because save(Committed) did not finish.
        assertTrue(sessionStore.load() is RegistrationState.PublicIdentityUploaded)

        val resumed = makeOrchestrator()
        assertTrue(resumed.currentState() is RegistrationState.PublicIdentityUploaded)

        // Retry uses the same Device Auth key; key manager should not generate a new one.
        val generateCountBefore = deviceAuthKeyManager.generateCallCount
        val committed = resumed.commit()
        val generateCountAfter = deviceAuthKeyManager.generateCallCount

        assertTrue(committed is RegistrationState.Committed)
        assertEquals("same key must be reused; no silent replacement", generateCountBefore, generateCountAfter)
    }

    @Test
    fun `E Committed persistence succeeds then restart sees committed`() {
        reachPublicIdentityUploaded()
        val committed = orchestrator.commit()

        // Session cleared after commit.
        assertTrue(sessionStore.load() is RegistrationState.NotStarted)

        val resumed = makeOrchestrator()
        assertTrue(resumed.currentState() is RegistrationState.NotStarted)
        assertTrue(bindingStore.isBound())

        // Any future key loss is terminal.
        deviceAuthKeyManager.simulateKeyInvalidation()
        assertEquals(
            com.anox.messenger.security.deviceauth.DeviceAuthKeyStatus.TerminalKeyLoss,
            deviceAuthKeyManager.status()
        )
        assertTrue(deviceAuthKeyManager.generateCallCount == 1)
        try {
            deviceAuthKeyManager.createKeyIfAbsent()
            org.junit.Assert.fail("expected terminal state exception")
        } catch (e: com.anox.messenger.security.deviceauth.DeviceAuthTerminalStateException) {
            // expected
        }
    }

    @Test
    fun `F binding filesystem write fails before save`() {
        // Equivalent to C: markBound failure. The in-flight state must remain resumable and must
        // not permit a new registration from a possibly-already-committed server state.
        reachPublicIdentityUploaded()
        bindingStore.setFailNextMarkBound()

        try {
            orchestrator.commit()
            org.junit.Assert.fail("expected exception")
        } catch (e: RuntimeException) {
            // expected
        }

        assertFalse(bindingStore.isBound())
        assertTrue(sessionStore.load() is RegistrationState.PublicIdentityUploaded)

        // A new reservation is blocked because a commit is still in flight and may have succeeded.
        try {
            orchestrator.reserve(username, license)
            org.junit.Assert.fail("expected cannot-start-new exception")
        } catch (e: IllegalStateException) {
            // expected
        }
    }

    @Test
    fun `G Committed filesystem write fails leaves resumable bound in-flight state`() {
        // Equivalent to D.
        reachPublicIdentityUploaded()
        sessionStore.failNextSave = true

        try {
            orchestrator.commit()
            org.junit.Assert.fail("expected exception")
        } catch (e: RegistrationSessionSecurityException) {
            // expected
        }

        assertTrue("binding is already durable", bindingStore.isBound())
        assertTrue("in-flight session preserved", sessionStore.load() is RegistrationState.PublicIdentityUploaded)
    }

    @Test
    fun `H restart while commit outcome uncertain fails closed`() {
        // After remote commit returned success but markBound crashed, the installation is still
        // not bound. It must not start a *new* registration using a fresh Device Auth key.
        reachPublicIdentityUploaded()
        bindingStore.setFailNextMarkBound()

        try {
            orchestrator.commit()
            org.junit.Assert.fail("expected exception")
        } catch (e: RuntimeException) {
            // expected
        }

        assertFalse(bindingStore.isBound())
        assertTrue(sessionStore.load() is RegistrationState.PublicIdentityUploaded)

        // Simulate key loss before binding.
        deviceAuthKeyManager.simulateKeyInvalidation()

        // Key loss before binding is terminal because the commit may have succeeded on the server.
        // We cannot know, so we must fail closed: no replacement key, no new registration.
        try {
            orchestrator.reserve(username, license)
            org.junit.Assert.fail("expected cannot-start-new exception")
        } catch (e: IllegalStateException) {
            // expected: the in-progress public-identity state blocks a new start.
        }
    }

    @Test
    fun `failStep cannot overwrite a committed terminal state`() {
        reachPublicIdentityUploaded()
        val committed = orchestrator.commit()
        assertTrue(bindingStore.isBound())
        assertTrue(committed is RegistrationState.Committed)

        // After a successful commit the session is cleared; the durable binding marker is the
        // remaining truth. A stray non-commit step must not create a new key, must not restart
        // registration, and must not overwrite the cleared/terminal state.
        val generationBefore = deviceAuthKeyManager.generateCallCount
        val apiBefore = api.registerDeviceAuthCallCount
        val result = orchestrator.registerDeviceAuth()
        assertTrue(result is RegistrationState.Failed)
        assertTrue(sessionStore.load() is RegistrationState.NotStarted)
        assertEquals(
            "a stray step must not call the device auth registration API",
            apiBefore,
            api.registerDeviceAuthCallCount
        )
        assertEquals(
            "a stray step after commit must not generate a replacement key",
            generationBefore,
            deviceAuthKeyManager.generateCallCount
        )
    }

    @Test
    fun `committed state cannot start a new registration`() {
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
    fun `binding guard prevents new registration even if session store is corrupt`() {
        // Pre-bind the installation, then corrupt the session store by clearing it.
        reachPublicIdentityUploaded()
        orchestrator.commit()
        sessionStore.clear()
        bindingStore.setBoundOverride(true) // force bound regardless of session

        // With a bound marker, a new reservation is not allowed even if the session is NotStarted.
        try {
            val fresh = RegistrationOrchestrator(
                api = api,
                deviceAuthKeyManager = deviceAuthKeyManager,
                deviceAuthBindingStore = bindingStore,
                sessionStore = sessionStore,
                e2eeStep = e2eeStep,
                createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
            )
            fresh.reserve(username, license)
            org.junit.Assert.fail("expected cannot-start-new exception")
        } catch (e: IllegalStateException) {
            // expected
        }
    }

    @Test
    fun `device auth replacement is impossible after binding even if session reset to NotStarted`() {
        reachPublicIdentityUploaded()
        orchestrator.commit()
        sessionStore.clear()

        // Now the Device Auth key is gone. Because the installation is bound, this is terminal.
        deviceAuthKeyManager.simulateKeyInvalidation()
        assertEquals(
            com.anox.messenger.security.deviceauth.DeviceAuthKeyStatus.TerminalKeyLoss,
            deviceAuthKeyManager.status()
        )
        assertTrue(bindingStore.isBound())

        val fresh = RegistrationOrchestrator(
            api = api,
            deviceAuthKeyManager = deviceAuthKeyManager,
            deviceAuthBindingStore = bindingStore,
            sessionStore = sessionStore,
            e2eeStep = e2eeStep,
            createDeviceAuthProof = { "fake-dpop-proof-for-${it.value}" }
        )
        val result = fresh.registerDeviceAuth()
        assertTrue(result is RegistrationState.Failed)
        assertTrue(fresh.currentState() is RegistrationState.NotStarted)
    }
}
