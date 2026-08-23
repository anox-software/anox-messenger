package com.anox.messenger.account

/**
 * A structurally valid license code, e.g. `anox-AB12-CD34-EF56`.
 *
 * B-003 (FROZEN v1.4): license codes are `anox-XXXX-XXXX-XXXX`, 12 unambiguous CSPRNG-generated
 * characters. License **generation is a server responsibility**; this class never generates a
 * license, only validates the external shape of a code the user typed in, and holds the
 * plaintext only for as long as it takes to submit it for server redemption.
 *
 * The plaintext value is treated as sensitive: [toString] never prints it, so it cannot be
 * disclosed accidentally through logging, string interpolation in log statements, or a debugger
 * "toString" preview. Canonical acceptance and the versioned HMAC-SHA-256 lookup remain
 * server-side; this class deliberately does not reproduce that algorithm or embed any server
 * secret.
 */
class LicenseCode private constructor(val value: String) {

    override fun toString(): String = "LicenseCode(***)"

    override fun equals(other: Any?): Boolean = other is LicenseCode && other.value == value

    override fun hashCode(): Int = value.hashCode()

    companion object {
        /**
         * `anox-` followed by three groups of four uppercase letters/digits, hyphen separated.
         *
         * The current authority specifies the code carries "12 unambiguous CSPRNG-generated
         * characters" but does not enumerate which characters are excluded as ambiguous. This
         * validator therefore checks only the gross structural shape (prefix, grouping, length,
         * uppercase alphanumeric charset) rather than inventing a specific unambiguous alphabet
         * that is not in the current authority. Server-side acceptance remains authoritative.
         */
        private val PATTERN = Regex("^anox-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")

        /** Validates the external shape of [raw]. Returns null if it does not match. */
        fun parse(raw: String): LicenseCode? =
            if (PATTERN.matches(raw)) LicenseCode(raw) else null
    }
}
