package com.anox.messenger.account

import android.content.Context
import com.anox.messenger.storage.AtomicFileWriter
import java.io.File
import java.time.Instant

/**
 * Persistent [RegistrationSessionStore] backed by a small text file in the app's no-backup
 * private storage.
 *
 * Lives under [Context.getNoBackupFilesDir] for the same reasons as
 * [com.anox.messenger.security.deviceauth.FileDeviceAuthBindingStore]: excluded from classic
 * backup and device-to-device transfer independent of `dataExtractionRules`, in addition to
 * this app's existing root-level backup exclusion.
 *
 * Unlike the Device Auth binding marker, a corrupt/unparseable session file fails closed to
 * [RegistrationState.NotStarted] rather than to a "blocking" state: there is no security
 * asymmetry to preserve here (an abandoned/unreadable in-progress registration simply restarts
 * cleanly; the corresponding server-side reservation is separately released once the grant's
 * 30-minute TTL elapses), so the simplest and most predictable recovery is to start over rather
 * than guess at a partially-recovered transaction state.
 */
class FileRegistrationSessionStore(context: Context) : RegistrationSessionStore {

    private val file: File = File(context.noBackupFilesDir, FILE_NAME)

    @Synchronized
    override fun load(): RegistrationState {
        if (!file.exists()) return RegistrationState.NotStarted
        val text = try {
            file.readText(Charsets.UTF_8)
        } catch (e: Exception) {
            return RegistrationState.NotStarted
        }
        return RegistrationStateCodec.decode(text) ?: RegistrationState.NotStarted
    }

    @Synchronized
    override fun save(state: RegistrationState) {
        AtomicFileWriter.write(file, RegistrationStateCodec.encode(state).toByteArray(Charsets.UTF_8))
    }

    @Synchronized
    override fun clear() {
        if (file.exists()) file.delete()
    }

    companion object {
        private const val FILE_NAME = "anox_registration_session.state"
    }
}

/**
 * Minimal, dependency-free text codec for [RegistrationState].
 *
 * Kept intentionally simple: one tag line followed by `key=value` lines. No JSON/serialization
 * library dependency is introduced for this narrow, internal-only file format.
 */
internal object RegistrationStateCodec {

    fun encode(state: RegistrationState): String = when (state) {
        is RegistrationState.NotStarted -> "NOT_STARTED\n"
        is RegistrationState.Reserved -> buildString {
            appendLine("RESERVED")
            appendLine("registrationId=${state.registrationId.value}")
            appendLine("grantValue=${state.grant.value}")
            appendLine("grantExpiresAt=${state.grant.expiresAt.epochSecond}")
            appendLine("username=${state.username.value}")
        }
        is RegistrationState.DeviceAuthRegistered -> buildString {
            appendLine("DEVICE_AUTH_REGISTERED")
            appendLine("registrationId=${state.registrationId.value}")
            appendLine("grantValue=${state.grant.value}")
            appendLine("grantExpiresAt=${state.grant.expiresAt.epochSecond}")
            appendLine("username=${state.username.value}")
            appendLine("jkt=${state.deviceAuthJwkThumbprint}")
        }
        is RegistrationState.PublicIdentityUploaded -> buildString {
            appendLine("PUBLIC_IDENTITY_UPLOADED")
            appendLine("registrationId=${state.registrationId.value}")
            appendLine("grantValue=${state.grant.value}")
            appendLine("grantExpiresAt=${state.grant.expiresAt.epochSecond}")
            appendLine("username=${state.username.value}")
            appendLine("jkt=${state.deviceAuthJwkThumbprint}")
        }
        is RegistrationState.Committed -> buildString {
            appendLine("COMMITTED")
            appendLine("accountId=${state.accountId.value}")
            appendLine("deviceId=${state.deviceId.value}")
            appendLine("username=${state.username.value}")
        }
        is RegistrationState.Expired -> buildString {
            appendLine("EXPIRED")
            appendLine("registrationId=${state.registrationId.value}")
        }
        is RegistrationState.Failed -> buildString {
            appendLine("FAILED")
            appendLine("reason=${state.reason}")
        }
    }

    fun decode(text: String): RegistrationState? {
        val lines = text.lines().filter { it.isNotBlank() }
        if (lines.isEmpty()) return null
        val tag = lines[0].trim()
        val fields = lines.drop(1).mapNotNull { line ->
            val idx = line.indexOf('=')
            if (idx < 0) null else line.substring(0, idx) to line.substring(idx + 1)
        }.toMap()

        return try {
            when (tag) {
                "NOT_STARTED" -> RegistrationState.NotStarted
                "RESERVED" -> RegistrationState.Reserved(
                    registrationId = requireRegistrationId(fields, "registrationId"),
                    grant = requireGrant(fields),
                    username = requireUsername(fields)
                )
                "DEVICE_AUTH_REGISTERED" -> RegistrationState.DeviceAuthRegistered(
                    registrationId = requireRegistrationId(fields, "registrationId"),
                    grant = requireGrant(fields),
                    username = requireUsername(fields),
                    deviceAuthJwkThumbprint = fields.getValue("jkt")
                )
                "PUBLIC_IDENTITY_UPLOADED" -> RegistrationState.PublicIdentityUploaded(
                    registrationId = requireRegistrationId(fields, "registrationId"),
                    grant = requireGrant(fields),
                    username = requireUsername(fields),
                    deviceAuthJwkThumbprint = fields.getValue("jkt")
                )
                "COMMITTED" -> RegistrationState.Committed(
                    accountId = AccountId.parse(fields.getValue("accountId")) ?: return null,
                    deviceId = DeviceId.parse(fields.getValue("deviceId")) ?: return null,
                    username = requireUsername(fields)
                )
                "EXPIRED" -> RegistrationState.Expired(
                    registrationId = requireRegistrationId(fields, "registrationId")
                )
                "FAILED" -> RegistrationState.Failed(reason = fields.getValue("reason"))
                else -> null
            }
        } catch (e: Exception) {
            null
        }
    }

    private fun requireRegistrationId(fields: Map<String, String>, key: String): RegistrationId =
        RegistrationId.parse(fields.getValue(key)) ?: throw IllegalArgumentException("bad $key")

    private fun requireGrant(fields: Map<String, String>): RegistrationGrant = RegistrationGrant(
        value = fields.getValue("grantValue"),
        expiresAt = Instant.ofEpochSecond(fields.getValue("grantExpiresAt").toLong())
    )

    private fun requireUsername(fields: Map<String, String>): Username {
        val validation = Username.validate(fields.getValue("username"))
        return (validation as? UsernameValidation.Valid)?.username
            ?: throw IllegalArgumentException("bad username")
    }
}
