package com.anox.messenger.account

import java.io.ByteArrayInputStream
import java.io.DataInputStream
import java.io.DataOutputStream
import java.nio.charset.StandardCharsets
import java.time.Instant

/**
 * Deterministic, versioned, length-prefixed binary codec for [RegistrationState].
 *
 * Replaces the previous newline/equals text format. Every string is length-prefixed, every
 * numeric is fixed-size, and the payload is authenticated by the AES-GCM envelope in
 * [FileRegistrationSessionStore]. Unknown state type bytes are rejected. The format is safe
 * against arbitrary server-supplied reason text because embedded newlines, equals signs, and
 * null bytes are just payload bytes under an explicit length prefix.
 *
 * This codec deliberately knows nothing about encryption; it only produces/validates the
 * cleartext payload that the Keystore-backed layer then seals.
 */
internal object BinaryRegistrationStateCodec {

    const val VERSION: Byte = 1

    /** Absolute ceiling for any length-prefixed string in this format. */
    private const val MAX_STRING_BYTES: Int = 16_384

    /** State-type tags. */
    private const val TAG_NOT_STARTED: Byte = 0
    private const val TAG_RESERVED: Byte = 1
    private const val TAG_DEVICE_AUTH_REGISTERED: Byte = 2
    private const val TAG_PUBLIC_IDENTITY_UPLOADED: Byte = 3
    private const val TAG_COMMITTED: Byte = 4
    private const val TAG_EXPIRED: Byte = 5
    private const val TAG_COMMIT_ARMED: Byte = 7
    private const val TAG_FAILED: Byte = 6

    fun encode(state: RegistrationState): ByteArray {
        val out = java.io.ByteArrayOutputStream()
        DataOutputStream(out).use { d ->
            d.writeByte(VERSION.toInt())
            when (state) {
                is RegistrationState.NotStarted -> d.writeByte(TAG_NOT_STARTED.toInt())
                is RegistrationState.Reserved -> {
                    d.writeByte(TAG_RESERVED.toInt())
                    writeString(d, state.registrationId.value.toString())
                    writeString(d, state.grant.value)
                    d.writeLong(state.grant.expiresAt.epochSecond)
                    writeString(d, state.username.value)
                }
                is RegistrationState.DeviceAuthRegistered -> {
                    d.writeByte(TAG_DEVICE_AUTH_REGISTERED.toInt())
                    writeString(d, state.registrationId.value.toString())
                    writeString(d, state.grant.value)
                    d.writeLong(state.grant.expiresAt.epochSecond)
                    writeString(d, state.username.value)
                    writeString(d, state.deviceAuthJwkThumbprint)
                }
                is RegistrationState.PublicIdentityUploaded -> {
                    d.writeByte(TAG_PUBLIC_IDENTITY_UPLOADED.toInt())
                    writeString(d, state.registrationId.value.toString())
                    writeString(d, state.grant.value)
                    d.writeLong(state.grant.expiresAt.epochSecond)
                    writeString(d, state.username.value)
                    writeString(d, state.deviceAuthJwkThumbprint)
                }
                is RegistrationState.CommitArmed -> {
                    d.writeByte(TAG_COMMIT_ARMED.toInt())
                    writeString(d, state.registrationId.value.toString())
                    writeString(d, state.grant.value)
                    d.writeLong(state.grant.expiresAt.epochSecond)
                    writeString(d, state.username.value)
                    writeString(d, state.deviceAuthJwkThumbprint)
                }
                is RegistrationState.Committed -> {
                    d.writeByte(TAG_COMMITTED.toInt())
                    writeString(d, state.accountId.value.toString())
                    writeString(d, state.deviceId.value.toString())
                    writeString(d, state.username.value)
                }
                is RegistrationState.Expired -> {
                    d.writeByte(TAG_EXPIRED.toInt())
                    writeString(d, state.registrationId.value.toString())
                }
                is RegistrationState.Failed -> {
                    d.writeByte(TAG_FAILED.toInt())
                    writeString(d, state.reason)
                }
            }
        }
        return out.toByteArray()
    }

    fun decode(data: ByteArray): RegistrationState? = try {
        val input = DataInputStream(ByteArrayInputStream(data))
        val version = input.readByte()
        if (version != VERSION) throw IllegalStateException("unsupported codec version: $version")
        when (input.readByte()) {
            TAG_NOT_STARTED -> RegistrationState.NotStarted
            TAG_RESERVED -> RegistrationState.Reserved(
                registrationId = requireRegistrationId(input),
                grant = requireGrant(input),
                username = requireUsername(input)
            )
            TAG_DEVICE_AUTH_REGISTERED -> RegistrationState.DeviceAuthRegistered(
                registrationId = requireRegistrationId(input),
                grant = requireGrant(input),
                username = requireUsername(input),
                deviceAuthJwkThumbprint = readString(input)
            )
            TAG_PUBLIC_IDENTITY_UPLOADED -> RegistrationState.PublicIdentityUploaded(
                registrationId = requireRegistrationId(input),
                grant = requireGrant(input),
                username = requireUsername(input),
                deviceAuthJwkThumbprint = readString(input)
            )
            TAG_COMMIT_ARMED -> RegistrationState.CommitArmed(
                registrationId = requireRegistrationId(input),
                grant = requireGrant(input),
                username = requireUsername(input),
                deviceAuthJwkThumbprint = readString(input)
            )
            TAG_COMMITTED -> RegistrationState.Committed(
                accountId = AccountId.parse(readString(input)) ?: throw IllegalStateException("bad accountId"),
                deviceId = DeviceId.parse(readString(input)) ?: throw IllegalStateException("bad deviceId"),
                username = requireUsername(input)
            )
            TAG_EXPIRED -> RegistrationState.Expired(
                registrationId = requireRegistrationId(input)
            )
            TAG_FAILED -> RegistrationState.Failed(reason = readString(input))
            else -> null
        }
    } catch (e: Exception) {
        null
    }

    private fun requireRegistrationId(input: DataInputStream): RegistrationId =
        RegistrationId.parse(readString(input)) ?: throw IllegalStateException("bad registrationId")

    private fun requireGrant(input: DataInputStream): RegistrationGrant = RegistrationGrant(
        value = readString(input),
        expiresAt = Instant.ofEpochSecond(input.readLong())
    )

    private fun requireUsername(input: DataInputStream): Username {
        val raw = readString(input)
        val validation = Username.validate(raw)
        return (validation as? UsernameValidation.Valid)?.username
            ?: throw IllegalStateException("bad username: ${validation is UsernameValidation.Invalid}")
    }

    private fun writeString(d: DataOutputStream, s: String) {
        val bytes = s.toByteArray(StandardCharsets.UTF_8)
        require(bytes.size <= MAX_STRING_BYTES) { "string too long: ${bytes.size} bytes" }
        d.writeInt(bytes.size)
        d.write(bytes)
    }

    private fun readString(input: DataInputStream): String {
        val length = input.readInt()
        if (length < 0 || length > MAX_STRING_BYTES) throw IllegalStateException("bad string length: $length")
        val bytes = ByteArray(length)
        input.readFully(bytes)
        return String(bytes, StandardCharsets.UTF_8)
    }
}
