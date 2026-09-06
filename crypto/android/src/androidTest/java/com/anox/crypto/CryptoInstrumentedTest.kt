package com.anox.crypto

import android.content.Context
import java.io.File
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Instrumented tests for the Android → Kotlin → JNI → Rust → vodozemac crypto path.
 *
 * These tests use the REAL native library loaded via CryptoNative and do not mock
 * any cryptographic operation. They validate the full JNI integration on an Android
 * runtime.
 */
@RunWith(AndroidJUnit4::class)
class CryptoInstrumentedTest {

    private lateinit var bridge: CryptoBridge
    private lateinit var context: Context

    @Before
    fun setUp() {
        context = InstrumentationRegistry.getInstrumentation().targetContext
        bridge = CryptoBridge.getInstance(context)
    }

    @After
    fun tearDown() {
        // No global teardown; individual tests manage their own identities.
    }

    @Test
    fun nativeLibraryLoads() {
        // This triggers the static init block of CryptoNative.
        assertTrue("Native library should be loaded", CryptoNative.cryptoInit())
    }

    @Test
    fun createAndDestroyIdentity() {
        val identity = bridge.createIdentity().getOrThrow()
        assertTrue("Identity handle must be non-zero", identity != 0L)

        val destroy = bridge.destroyIdentity(identity)
        assertTrue("Destroy identity must succeed", destroy is CryptoResult.Success)
    }

    @Test
    fun getPublicKeys() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            val curve25519 = bridge.getCurve25519PublicKey(identity).getOrThrow()
            assertEquals("Curve25519 public key must be 32 bytes", 32, curve25519.size)
            assertFalse("Curve25519 key must not be all zeros", curve25519.all { it == 0.toByte() })

            val ed25519 = bridge.getEd25519PublicKey(identity).getOrThrow()
            assertEquals("Ed25519 public key must be 32 bytes", 32, ed25519.size)
            assertFalse("Ed25519 key must not be all zeros", ed25519.all { it == 0.toByte() })
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun oneTimeKeyGeneration() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            assertTrue("OTK generation must succeed", bridge.generateOneTimeKeys(identity, 5) is CryptoResult.Success)
            val count = bridge.oneTimeKeysCount(identity).getOrThrow()
            assertEquals("There should be 5 one-time keys", 5, count)
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun getOneTimeKey() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            bridge.generateOneTimeKeys(identity, 1)
            val otk = bridge.getOneTimeKey(identity, 0).getOrThrow()
            assertEquals("One-time key must be 32 bytes", 32, otk.size)
            assertFalse("One-time key must not be all zeros", otk.all { it == 0.toByte() })
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun identitySerializationAndRestoration() {
        val identity = bridge.createIdentity().getOrThrow()
        val originalCurve: ByteArray
        val originalEd: ByteArray
        val serialized: ByteArray
        try {
            originalCurve = bridge.getCurve25519PublicKey(identity).getOrThrow()
            originalEd = bridge.getEd25519PublicKey(identity).getOrThrow()
            serialized = bridge.serializeIdentity(identity).getOrThrow()
        } finally {
            bridge.destroyIdentity(identity)
        }

        // Recreate identity from serialized bytes
        val restored = bridge.deserializeIdentity(serialized).getOrThrow()
        try {
            val restoredCurve = bridge.getCurve25519PublicKey(restored).getOrThrow()
            val restoredEd = bridge.getEd25519PublicKey(restored).getOrThrow()
            assertArrayEquals(originalCurve, restoredCurve)
            assertArrayEquals(originalEd, restoredEd)
        } finally {
            bridge.destroyIdentity(restored)
        }
    }

    @Test
    fun corruptedStateRejectsDeserialization() {
        val identity = bridge.createIdentity().getOrThrow()
        val serialized = try {
            bridge.serializeIdentity(identity).getOrThrow()
        } finally {
            bridge.destroyIdentity(identity)
        }

        val corrupted = serialized.copyOf()
        if (corrupted.isNotEmpty()) {
            corrupted[0] = (corrupted[0].toInt() xor 0xFF).toByte()
        }

        val result = bridge.deserializeIdentity(corrupted)
        assertTrue("Corrupted state must be rejected", result is CryptoResult.Failure)
    }

    @Test
    fun invalidHandleIsRejected() {
        val result = bridge.getCurve25519PublicKey(0L)
        assertTrue("Zero handle must fail", result is CryptoResult.Failure)
    }

    @Test
    fun destroyedHandleDoesNotCrash() {
        val identity = bridge.createIdentity().getOrThrow()
        bridge.destroyIdentity(identity)
        // Calling get on a destroyed identity must be a safe failure, not a crash.
        val result = bridge.getCurve25519PublicKey(identity)
        assertTrue("Use of destroyed handle must fail", result is CryptoResult.Failure)
    }

    @Test
    fun endToEndAliceBob() {
        val alice = bridge.createIdentity().getOrThrow()
        val bob = bridge.createIdentity().getOrThrow()

        try {
            bridge.generateOneTimeKeys(bob, 1)
            val bobIdentityKey = bridge.getCurve25519PublicKey(bob).getOrThrow()
            val bobOtk = bridge.getOneTimeKey(bob, 0).getOrThrow()

            // Alice creates an outbound session to Bob
            val aliceSession = bridge.createOutboundSession(alice, bobIdentityKey, bobOtk).getOrThrow()

            val plaintext = "test message".toByteArray(Charsets.UTF_8)
            val (messageType, ciphertext) = bridge.encrypt(aliceSession, plaintext).getOrThrow()
            assertEquals("First message must be PreKey (0)", 0, messageType)

            // Bob creates an inbound session from Alice's PreKey message
            val (bobSession, decrypted) = bridge.createInboundSession(bob, bridge.getCurve25519PublicKey(alice).getOrThrow(), ciphertext).getOrThrow()

            assertArrayEquals(plaintext, decrypted)

            // Bob -> Alice reply
            val reply = "reply from bob".toByteArray(Charsets.UTF_8)
            val (replyType, replyCipher) = bridge.encrypt(bobSession, reply).getOrThrow()
            assertEquals("Second message must be Normal (1)", 1, replyType)

            val aliceReply = bridge.decrypt(aliceSession, replyType, replyCipher).getOrThrow()
            assertArrayEquals(reply, aliceReply)

            bridge.destroySession(bobSession)
            bridge.destroySession(aliceSession)
        } finally {
            bridge.destroyIdentity(alice)
            bridge.destroyIdentity(bob)
        }
    }

    @Test
    fun invalidCiphertextRejectsDecryption() {
        val identity = bridge.createIdentity().getOrThrow()
        val other = bridge.createIdentity().getOrThrow()
        try {
            val invalidCipher = ByteArray(32) { 0xFF.toByte() }
            val result = bridge.decrypt(other, 1, invalidCipher)
            assertTrue("Invalid ciphertext must fail", result is CryptoResult.Failure)
        } finally {
            bridge.destroyIdentity(identity)
            bridge.destroyIdentity(other)
        }
    }

    @Test
    fun invalidMessageTypeRejectsDecryption() {
        val identity = bridge.createIdentity().getOrThrow()
        val other = bridge.createIdentity().getOrThrow()
        try {
            val result = bridge.decrypt(other, 5, ByteArray(32) { 0xAB.toByte() })
            assertTrue("Invalid message type must fail", result is CryptoResult.Failure)
        } finally {
            bridge.destroyIdentity(identity)
            bridge.destroyIdentity(other)
        }
    }

    @Test
    fun malformedMessageRejectsDecryption() {
        val identity = bridge.createIdentity().getOrThrow()
        val other = bridge.createIdentity().getOrThrow()
        try {
            val result = bridge.decrypt(other, 1, ByteArray(8) { 0x01.toByte() })
            assertTrue("Malformed message must fail", result is CryptoResult.Failure)
        } finally {
            bridge.destroyIdentity(identity)
            bridge.destroyIdentity(other)
        }
    }

    @Test
    fun errorMessagesDoNotContainSecrets() {
        val result = bridge.getCurve25519PublicKey(0L) as CryptoResult.Failure
        val message = result.error.message ?: ""
        assertFalse("Error must not mention 'key'", message.contains("key", ignoreCase = true))
        assertFalse("Error must not mention 'secret'", message.contains("secret", ignoreCase = true))
        assertFalse("Error must not mention 'private'", message.contains("private", ignoreCase = true))
    }

    @Test
    fun persistenceRoundTrip() {
        val identity = bridge.createIdentity().getOrThrow()
        val originalPublic: ByteArray
        val saved: ByteArray
        try {
            originalPublic = bridge.getCurve25519PublicKey(identity).getOrThrow()
            saved = bridge.serializeIdentity(identity).getOrThrow()
        } finally {
            bridge.destroyIdentity(identity)
        }

        // Persist encrypted state to a file (simulating app persistence)
        val stateFile = context.getDir("anox_test_state", Context.MODE_PRIVATE)
        val stateFilePath = java.io.File(stateFile, "identity.enc")
        stateFilePath.writeBytes(saved)

        // Simulate reload from storage by reading the file back and deserializing
        val loaded = stateFilePath.readBytes()
        val restored = bridge.deserializeIdentity(loaded).getOrThrow()
        try {
            val restoredPublic = bridge.getCurve25519PublicKey(restored).getOrThrow()
            assertArrayEquals("Restored identity must match original", originalPublic, restoredPublic)
        } finally {
            bridge.destroyIdentity(restored)
        }
    }

    @Test
    fun missingStateFailsSafely() {
        val missing = ByteArray(0)
        val result = bridge.deserializeIdentity(missing)
        assertTrue("Missing/empty state must fail", result is CryptoResult.Failure)
    }

    @Test
    fun stateEncryptionUsesFreshNonces() {
        val identity = bridge.createIdentity().getOrThrow()
        val s1: ByteArray
        val s2: ByteArray
        try {
            s1 = bridge.serializeIdentity(identity).getOrThrow()
            s2 = bridge.serializeIdentity(identity).getOrThrow()
        } finally {
            bridge.destroyIdentity(identity)
        }

        // Two encryptions of the same plaintext with the same key should produce
        // different ciphertext because the nonce is freshly random each time.
        assertFalse("Serialized blobs must differ due to fresh nonce", s1.contentEquals(s2))
    }

    @Test
    fun stateKeyDeterministicWrap() {
        // getOrCreateStateKey should return the same 32-byte key across calls
        // because it is encrypted/decrypted by the Keystore key, not regenerated.
        val bridge2 = CryptoBridge.getInstance(context)
        val key1 = bridge.getOrCreateStateKey()
        val key2 = bridge2.getOrCreateStateKey()
        assertArrayEquals("Wrapped state key must be stable", key1, key2)
    }

    @Test
    fun identityHandleUsedAsSessionDecryptFails() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            val result = bridge.decrypt(identity, 1, ByteArray(32) { 0xAB.toByte() })
            assertTrue("Identity handle must be rejected by session decrypt", result is CryptoResult.Failure)
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun identityHandleUsedAsSessionEncryptFails() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            val result = bridge.encrypt(identity, "test".toByteArray())
            assertTrue("Identity handle must be rejected by session encrypt", result is CryptoResult.Failure)
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun sessionHandleUsedAsIdentitySerializeFails() {
        val alice = bridge.createIdentity().getOrThrow()
        val bob = bridge.createIdentity().getOrThrow()
        try {
            bridge.generateOneTimeKeys(bob, 1)
            val bobIdentity = bridge.getCurve25519PublicKey(bob).getOrThrow()
            val bobOtk = bridge.getOneTimeKey(bob, 0).getOrThrow()
            val session = bridge.createOutboundSession(alice, bobIdentity, bobOtk).getOrThrow()
            try {
                val result = bridge.serializeIdentity(session)
                assertTrue("Session handle must be rejected by identity serialize", result is CryptoResult.Failure)
            } finally {
                bridge.destroySession(session)
            }
        } finally {
            bridge.destroyIdentity(alice)
            bridge.destroyIdentity(bob)
        }
    }

    @Test
    fun sessionHandleUsedAsIdentityPublicKeyFails() {
        val alice = bridge.createIdentity().getOrThrow()
        val bob = bridge.createIdentity().getOrThrow()
        try {
            bridge.generateOneTimeKeys(bob, 1)
            val bobIdentity = bridge.getCurve25519PublicKey(bob).getOrThrow()
            val bobOtk = bridge.getOneTimeKey(bob, 0).getOrThrow()
            val session = bridge.createOutboundSession(alice, bobIdentity, bobOtk).getOrThrow()
            try {
                val result = bridge.getCurve25519PublicKey(session)
                assertTrue("Session handle must be rejected by identity public-key", result is CryptoResult.Failure)
            } finally {
                bridge.destroySession(session)
            }
        } finally {
            bridge.destroyIdentity(alice)
            bridge.destroyIdentity(bob)
        }
    }

    @Test
    fun destroyedIdentityReusedFails() {
        val identity = bridge.createIdentity().getOrThrow()
        bridge.destroyIdentity(identity)
        val result = bridge.getCurve25519PublicKey(identity)
        assertTrue("Destroyed identity must be rejected", result is CryptoResult.Failure)
    }

    @Test
    fun destroyedSessionReusedFails() {
        val alice = bridge.createIdentity().getOrThrow()
        val bob = bridge.createIdentity().getOrThrow()
        try {
            bridge.generateOneTimeKeys(bob, 1)
            val bobIdentity = bridge.getCurve25519PublicKey(bob).getOrThrow()
            val bobOtk = bridge.getOneTimeKey(bob, 0).getOrThrow()
            val session = bridge.createOutboundSession(alice, bobIdentity, bobOtk).getOrThrow()
            bridge.destroySession(session)
            val result = bridge.encrypt(session, "test".toByteArray())
            assertTrue("Destroyed session must be rejected", result is CryptoResult.Failure)
        } finally {
            bridge.destroyIdentity(alice)
            bridge.destroyIdentity(bob)
        }
    }

    @Test
    fun identityDestroyTwiceIsSafe() {
        val identity = bridge.createIdentity().getOrThrow()
        bridge.destroyIdentity(identity)
        bridge.destroyIdentity(identity)
        // No crash and no success requirement; test passes if we reach here.
    }

    @Test
    fun sessionDestroyTwiceIsSafe() {
        val alice = bridge.createIdentity().getOrThrow()
        val bob = bridge.createIdentity().getOrThrow()
        try {
            bridge.generateOneTimeKeys(bob, 1)
            val bobIdentity = bridge.getCurve25519PublicKey(bob).getOrThrow()
            val bobOtk = bridge.getOneTimeKey(bob, 0).getOrThrow()
            val session = bridge.createOutboundSession(alice, bobIdentity, bobOtk).getOrThrow()
            bridge.destroySession(session)
            bridge.destroySession(session)
            // No crash and no success requirement; test passes if we reach here.
        } finally {
            bridge.destroyIdentity(alice)
            bridge.destroyIdentity(bob)
        }
    }

    @Test
    fun saveAndLoadIdentityPreservesPublicKey() {
        val identity = bridge.createIdentity().getOrThrow()
        val originalPublic: ByteArray
        try {
            originalPublic = bridge.getCurve25519PublicKey(identity).getOrThrow()
            assertTrue("Save identity must succeed", bridge.saveIdentity(identity, "test_identity_v1.enc") is CryptoResult.Success)
        } finally {
            bridge.destroyIdentity(identity)
        }

        val loaded = bridge.loadIdentity("test_identity_v1.enc").getOrThrow()
        try {
            val loadedPublic = bridge.getCurve25519PublicKey(loaded).getOrThrow()
            assertArrayEquals("Loaded identity must match original public key", originalPublic, loadedPublic)
        } finally {
            bridge.destroyIdentity(loaded)
            File(context.filesDir, "test_identity_v1.enc").delete()
        }
    }

    @Test
    fun firstRunStatusIsDetected() {
        bridge.wipeLocalCrypto().getOrThrow()
        val status = bridge.getLocalStateStatus("test_identity_v1.enc")
        assertTrue("After wipe the status must be FirstRun", status is CryptoBridge.LocalStateStatus.FirstRun)
    }

    @Test
    fun corruptedIdentityFileFailsToLoad() {
        val identity = bridge.createIdentity().getOrThrow()
        val originalPublic: ByteArray
        try {
            originalPublic = bridge.getCurve25519PublicKey(identity).getOrThrow()
            val data = bridge.serializeIdentity(identity).getOrThrow()
            // Corrupt the magic bytes at the start of the versioned envelope.
            val corrupted = data.copyOf()
            if (corrupted.isNotEmpty()) {
                corrupted[0] = (corrupted[0].toInt() xor 0xFF).toByte()
            }
            val file = File(context.filesDir, "test_corrupt_v1.enc")
            file.writeBytes(corrupted)
            val loaded = bridge.loadIdentity("test_corrupt_v1.enc")
            assertTrue("Corrupted identity must fail to load", loaded is CryptoResult.Failure)
            file.delete()
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun missingIdentityFileFails() {
        val file = File(context.filesDir, "test_missing_v1.enc")
        if (file.exists()) file.delete()
        val result = bridge.loadIdentity("test_missing_v1.enc")
        assertTrue("Missing identity file must fail", result is CryptoResult.Failure)
    }

    @Test
    fun emptyIdentityFileFails() {
        val file = File(context.filesDir, "test_empty_v1.enc")
        file.writeBytes(ByteArray(0))
        try {
            val result = bridge.loadIdentity("test_empty_v1.enc")
            assertTrue("Empty identity file must fail", result is CryptoResult.Failure)
        } finally {
            file.delete()
        }
    }

    @Test
    fun saveAndLoadSessionPreservesConversation() {
        val alice = bridge.createIdentity().getOrThrow()
        val bob = bridge.createIdentity().getOrThrow()
        try {
            bridge.generateOneTimeKeys(bob, 1)
            val bobIdentity = bridge.getCurve25519PublicKey(bob).getOrThrow()
            val bobOtk = bridge.getOneTimeKey(bob, 0).getOrThrow()

            val aliceSession = bridge.createOutboundSession(alice, bobIdentity, bobOtk).getOrThrow()
            try {
                val plaintext = "session persistence test".toByteArray(Charsets.UTF_8)
                val (msgType, ciphertext) = bridge.encrypt(aliceSession, plaintext).getOrThrow()

                assertTrue("Save session must succeed", bridge.saveSession(aliceSession, "test_session_v1.enc") is CryptoResult.Success)
                bridge.destroySession(aliceSession)

                val loadedAliceSession = bridge.loadSession("test_session_v1.enc").getOrThrow()
                try {
                    val bobSession = bridge.createInboundSession(bob, bridge.getCurve25519PublicKey(alice).getOrThrow(), ciphertext).getOrThrow().first
                    try {
                        val reply = "reply".toByteArray(Charsets.UTF_8)
                        val (replyType, replyCipher) = bridge.encrypt(bobSession, reply).getOrThrow()
                        val decrypted = bridge.decrypt(loadedAliceSession, replyType, replyCipher).getOrThrow()
                        assertArrayEquals(reply, decrypted)
                    } finally {
                        bridge.destroySession(bobSession)
                    }
                } finally {
                    bridge.destroySession(loadedAliceSession)
                }
            } finally {
                File(context.filesDir, "test_session_v1.enc").delete()
            }
        } finally {
            bridge.destroyIdentity(alice)
            bridge.destroyIdentity(bob)
        }
    }

    @Test
    fun truncatedIdentityFileFails() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            val data = bridge.serializeIdentity(identity).getOrThrow()
            val truncated = data.copyOfRange(0, data.size / 2)
            val file = File(context.filesDir, "test_truncated_v1.enc")
            file.writeBytes(truncated)
            val result = bridge.loadIdentity("test_truncated_v1.enc")
            assertTrue("Truncated identity file must fail", result is CryptoResult.Failure)
            file.delete()
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun modifiedCiphertextFailsToLoad() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            val data = bridge.serializeIdentity(identity).getOrThrow()
            val modified = data.copyOf()
            // Flip a byte in the ciphertext/tag area, well after the 17-byte header.
            if (modified.size > 20) {
                modified[20] = (modified[20].toInt() xor 0xFF).toByte()
            }
            val file = File(context.filesDir, "test_modified_v1.enc")
            file.writeBytes(modified)
            val result = bridge.loadIdentity("test_modified_v1.enc")
            assertTrue("Modified ciphertext must fail authentication", result is CryptoResult.Failure)
            file.delete()
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun corruptedWrappedStateKeyFails() {
        val wrappedFile = java.io.File(context.filesDir, "anox_state_key.enc")
        if (!wrappedFile.exists()) {
            // Trigger creation
            bridge.getOrCreateStateKey()
        }

        val wrapped = wrappedFile.readBytes()
        val corrupted = wrapped.copyOf()
        if (corrupted.size > 15) {
            corrupted[15] = (corrupted[15].toInt() xor 0xFF).toByte()
        }
        wrappedFile.writeBytes(corrupted)

        var threw = false
        try {
            // Accessing the state key after corruption must throw a Keystore/GCM exception.
            bridge.getOrCreateStateKey()
        } catch (e: Exception) {
            threw = true
        } finally {
            // Always restore the original wrapped key so other tests are not poisoned.
            wrappedFile.writeBytes(wrapped)
        }

        assertTrue("Corrupted wrapped state key must raise an exception", threw)
    }

    // --- LEGACY-FIX-01 additions ---

    @Test
    fun missingStateKeyPreventsDeserializeButDoesNotCreateOne() {
        val identity = bridge.createIdentity().getOrThrow()
        val serialized = try {
            bridge.serializeIdentity(identity).getOrThrow()
        } finally {
            bridge.destroyIdentity(identity)
        }

        val stateFile = File(context.filesDir, "test_missing_state_v1.enc")
        stateFile.writeBytes(serialized)

        // Capture the existing wrapped state key and remove it.
        val wrappedFile = File(context.filesDir, "anox_state_key.enc")
        val wrappedBackup = wrappedFile.readBytes()
        wrappedFile.delete()

        try {
            val result = bridge.loadIdentity("test_missing_state_v1.enc")
            assertTrue("Missing state key must fail deterministically", result is CryptoResult.Failure)
            assertTrue(
                "Failure must be MissingStateKey, not generic DeserializationFailed",
                (result as CryptoResult.Failure).error is CryptoError.MissingStateKey
            )
            // loadIdentity must NOT have created a new state key.
            assertFalse("Missing state key must not be silently created", wrappedFile.exists())
        } finally {
            stateFile.delete()
            if (wrappedBackup.isNotEmpty()) {
                wrappedFile.writeBytes(wrappedBackup)
            }
        }
    }

    @Test
    fun oneTimeKeysPersistAfterGenerationBeforeUpload() {
        val identity = bridge.createAndPersistFirstIdentity("test_otk_identity.enc").getOrThrow()
        try {
            val originalCurve = bridge.getCurve25519PublicKey(identity).getOrThrow()

            bridge.generateOneTimeKeys(identity, 5).getOrThrow()
            bridge.saveIdentity(identity, "test_otk_identity.enc").getOrThrow()

            // Simulate process death by loading from disk.
            val restored = bridge.loadIdentity("test_otk_identity.enc").getOrThrow()
            try {
                assertEquals(5, bridge.oneTimeKeysCount(restored).getOrThrow())
                assertArrayEquals(originalCurve, bridge.getCurve25519PublicKey(restored).getOrThrow())
            } finally {
                bridge.destroyIdentity(restored)
            }
        } finally {
            bridge.destroyIdentity(identity)
            File(context.filesDir, "test_otk_identity.enc").delete()
        }
    }

    @Test
    fun undersizedOneTimeKeyBufferReturnsBufferTooSmall() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            bridge.generateOneTimeKeys(identity, 1).getOrThrow()
            val out = ByteArray(1)
            val result = CryptoNative.cryptoGetOneTimeKey(identity, 0, out)
            assertEquals("Undersized buffer must return BufferTooSmall", -11, result)
        } finally {
            bridge.destroyIdentity(identity)
        }
    }

    @Test
    fun undersizedCurve25519BufferReturnsBufferTooSmall() {
        val identity = bridge.createIdentity().getOrThrow()
        try {
            val out = ByteArray(1)
            val result = CryptoNative.cryptoGetCurve25519PublicKey(identity, out)
            assertEquals("Undersized buffer must return BufferTooSmall", -11, result)
        } finally {
            bridge.destroyIdentity(identity)
        }
    }
}