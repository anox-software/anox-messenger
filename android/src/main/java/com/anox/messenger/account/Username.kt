package com.anox.messenger.account

/**
 * A syntactically valid username.
 *
 * B-003 (FROZEN v1.4): lowercase ASCII `[a-z0-9_.]`, length 3-32. Immutable after successful
 * activation. There is no unrestricted global username directory and no client-side prefix
 * search.
 *
 * This class only encodes client-side UX validation. The server remains authoritative for
 * acceptance, including reserved-name rejection and uniqueness; this task does not invent a
 * reserved-name list because the current authority does not enumerate one.
 */
@ConsistentCopyVisibility
data class Username private constructor(val value: String) {

    override fun toString(): String = value

    companion object {
        const val MIN_LENGTH: Int = 3
        const val MAX_LENGTH: Int = 32

        private val ALLOWED_PATTERN = Regex("^[a-z0-9_.]+$")

        /**
         * Validates [raw] against the frozen B-003 syntax rules.
         *
         * The input is validated exactly as submitted. An invalid proposed username (for
         * example containing uppercase letters) is rejected rather than silently normalised,
         * so the user always explicitly submits the canonical username they intend to register.
         */
        fun validate(raw: String): UsernameValidation {
            if (raw.isEmpty()) {
                return UsernameValidation.Invalid(UsernameInvalidReason.TOO_SHORT)
            }
            if (raw.length < MIN_LENGTH) {
                return UsernameValidation.Invalid(UsernameInvalidReason.TOO_SHORT)
            }
            if (raw.length > MAX_LENGTH) {
                return UsernameValidation.Invalid(UsernameInvalidReason.TOO_LONG)
            }
            if (!ALLOWED_PATTERN.matches(raw)) {
                return UsernameValidation.Invalid(UsernameInvalidReason.INVALID_CHARACTERS)
            }
            return UsernameValidation.Valid(Username(raw))
        }
    }
}

/** Why a proposed username failed client-side validation. Server validation remains authoritative. */
enum class UsernameInvalidReason {
    TOO_SHORT,
    TOO_LONG,
    INVALID_CHARACTERS
}

/** Outcome of validating a proposed username. */
sealed class UsernameValidation {
    data class Valid(val username: Username) : UsernameValidation()
    data class Invalid(val reason: UsernameInvalidReason) : UsernameValidation()

    val isValid: Boolean get() = this is Valid
}
