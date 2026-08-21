package com.anox.messenger.security.deviceauth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B-002 Device Auth key lifecycle and hardware-policy tests.
 *
 * The critical property proven here is that terminal Device Auth key loss never results in
 * a silently generated replacement key.
 */
class DeviceAuthKeyLifecycleTest {

    // ---------------------------------------------------------------------------------
    // state resolution
    // ---------------------------------------------------------------------------------

    @Test
    fun `absent and never bound is first run`() {
        val status = DeviceAuthKeyStateResolver.resolve(
            keyPresent = false,
            hardwareSecurityLevel = null,
            isBound = false
        )
        assertSame(DeviceAuthKeyStatus.AbsentNotBound, status)
    }

    @Test
    fun `absent but previously bound is terminal`() {
        val status = DeviceAuthKeyStateResolver.resolve(
            keyPresent = false,
            hardwareSecurityLevel = null,
            isBound = true
        )
        assertSame(DeviceAuthKeyStatus.TerminalKeyLoss, status)
    }

    @Test
    fun `present key reports its hardware level`() {
        val status = DeviceAuthKeyStateResolver.resolve(
            keyPresent = true,
            hardwareSecurityLevel = HardwareSecurityLevel.STRONGBOX,
            isBound = true
        )
        assertEquals(DeviceAuthKeyStatus.Present(HardwareSecurityLevel.STRONGBOX), status)
    }

    @Test
    fun `present key with unprovable hardware level is UNKNOWN`() {
        val status = DeviceAuthKeyStateResolver.resolve(
            keyPresent = true,
            hardwareSecurityLevel = null,
            isBound = false
        )
        assertEquals(DeviceAuthKeyStatus.Present(HardwareSecurityLevel.UNKNOWN), status)
    }

    @Test
    fun `creation is allowed on first run`() {
        DeviceAuthKeyStateResolver.requireCreationAllowed(DeviceAuthKeyStatus.AbsentNotBound)
    }

    @Test
    fun `creation is refused after terminal loss`() {
        assertThrows(DeviceAuthTerminalStateException::class.java) {
            DeviceAuthKeyStateResolver.requireCreationAllowed(DeviceAuthKeyStatus.TerminalKeyLoss)
        }
    }

    // ---------------------------------------------------------------------------------
    // end-to-end lifecycle
    // ---------------------------------------------------------------------------------

    @Test
    fun `first run creates exactly one key and is idempotent`() {
        val manager = FakeDeviceAuthKeyManager(InMemoryDeviceAuthBindingStore())

        assertSame(DeviceAuthKeyStatus.AbsentNotBound, manager.status())

        manager.createKeyIfAbsent()
        manager.createKeyIfAbsent()
        manager.createKeyIfAbsent()

        assertEquals(1, manager.generateCallCount)
        assertTrue(manager.status() is DeviceAuthKeyStatus.Present)
    }

    @Test
    fun `terminal key loss does not silently regenerate`() {
        val bindingStore = InMemoryDeviceAuthBindingStore()
        val manager = FakeDeviceAuthKeyManager(bindingStore)

        manager.createKeyIfAbsent()
        // A future B-003 registration binds this device.
        bindingStore.markBound()
        assertEquals(1, manager.generateCallCount)

        // The platform invalidates or loses the key.
        manager.simulateKeyInvalidation()
        assertSame(DeviceAuthKeyStatus.TerminalKeyLoss, manager.status())

        assertThrows(DeviceAuthTerminalStateException::class.java) {
            manager.createKeyIfAbsent()
        }

        // No replacement key was created and no key became available.
        assertEquals(1, manager.generateCallCount)
        assertSame(DeviceAuthKeyStatus.TerminalKeyLoss, manager.status())
        assertThrows(DeviceAuthTerminalStateException::class.java) { manager.signer() }
    }

    @Test
    fun `explicit local reset clears binding and allows a brand new key`() {
        val bindingStore = InMemoryDeviceAuthBindingStore()
        val manager = FakeDeviceAuthKeyManager(bindingStore)

        manager.createKeyIfAbsent()
        bindingStore.markBound()
        manager.simulateKeyInvalidation()
        assertSame(DeviceAuthKeyStatus.TerminalKeyLoss, manager.status())

        // Explicit destructive local reset: a NEW account from scratch, not recovery of the
        // old one.
        bindingStore.clearBinding()
        assertSame(DeviceAuthKeyStatus.AbsentNotBound, manager.status())

        manager.createKeyIfAbsent()
        assertEquals(2, manager.generateCallCount)
    }

    @Test
    fun `logout style token revocation does not delete the device auth key`() {
        val bindingStore = InMemoryDeviceAuthBindingStore()
        val manager = FakeDeviceAuthKeyManager(bindingStore)
        manager.createKeyIfAbsent()
        bindingStore.markBound()

        val thumbprintBefore = manager.signer().jwkThumbprint()

        // Logout revokes session/token state only. No Device Auth key operation occurs.
        // (Token/session state is B-004 and is not modelled here.)

        assertTrue(manager.status() is DeviceAuthKeyStatus.Present)
        assertEquals(thumbprintBefore, manager.signer().jwkThumbprint())
    }

    // ---------------------------------------------------------------------------------
    // hardware policy
    // ---------------------------------------------------------------------------------

    @Test
    fun `strongbox and tee are production eligible`() {
        assertTrue(HardwareSecurityLevel.STRONGBOX.isProductionEligible)
        assertTrue(HardwareSecurityLevel.TRUSTED_EXECUTION_ENVIRONMENT.isProductionEligible)
    }

    @Test
    fun `software only is not production eligible`() {
        assertFalse(HardwareSecurityLevel.SOFTWARE.isProductionEligible)
    }

    @Test
    fun `unknown hardware fails closed`() {
        assertFalse(
            "absence of hardware proof must never be treated as hardware backing",
            HardwareSecurityLevel.UNKNOWN.isProductionEligible
        )
    }

    @Test
    fun `manager rejects production use of a software only key`() {
        val manager = FakeDeviceAuthKeyManager(
            InMemoryDeviceAuthBindingStore(),
            hardwareLevel = HardwareSecurityLevel.SOFTWARE
        )
        manager.createKeyIfAbsent()

        assertTrue(manager.status() is DeviceAuthKeyStatus.Present)
        assertFalse(manager.isProductionEligible())
    }

    @Test
    fun `manager accepts production use of a tee key`() {
        val manager = FakeDeviceAuthKeyManager(
            InMemoryDeviceAuthBindingStore(),
            hardwareLevel = HardwareSecurityLevel.TRUSTED_EXECUTION_ENVIRONMENT
        )
        manager.createKeyIfAbsent()
        assertTrue(manager.isProductionEligible())
    }

    @Test
    fun `no key means not production eligible`() {
        val manager = FakeDeviceAuthKeyManager(InMemoryDeviceAuthBindingStore())
        assertFalse(manager.isProductionEligible())
    }

    // ---------------------------------------------------------------------------------
    // key material exposure
    // ---------------------------------------------------------------------------------

    @Test
    fun `signer never exposes private key material`() {
        val manager = FakeDeviceAuthKeyManager(InMemoryDeviceAuthBindingStore())
        manager.createKeyIfAbsent()

        val publicJwk = manager.signer().publicJwk
        assertFalse(publicJwk.isPrivate)
        assertFalse(publicJwk.toJSONString().contains("\"d\""))
        assertNull(publicJwk.toECPrivateKey())
    }
}
