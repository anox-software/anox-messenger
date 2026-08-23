package com.anox.messenger.account

/**
 * Thrown when the encrypted registration-session store cannot be read or authenticated.
 *
 * This is a terminal/audit event: callers must not silently downgrade the installation to
 * [RegistrationState.NotStarted] without first checking whether the Device Auth binding store
 * already marks this device as bound to an account. See [RegistrationOrchestrator].
 */
class RegistrationSessionSecurityException(
    message: String,
    cause: Throwable? = null
) : RuntimeException(message, cause)
