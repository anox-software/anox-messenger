package com.anox.messenger.security.deviceauth

/**
 * Storage location / provable hardware backing of the B-002 Device Authentication private key.
 *
 * B-002 (FROZEN v1.1): StrongBox preferred, TEE fallback accepted in production,
 * software-only fails production registration.
 */
enum class HardwareSecurityLevel {

    /** Key lives in a dedicated StrongBox secure element. Preferred. */
    STRONGBOX,

    /** Key lives in the Trusted Execution Environment. Accepted for production per B-002. */
    TRUSTED_EXECUTION_ENVIRONMENT,

    /** Key is software-backed only. NOT production eligible. */
    SOFTWARE,

    /**
     * Hardware backing could not be proven by the platform.
     *
     * Treated as NOT production eligible (fail closed). Absence of proof is never
     * interpreted as presence of hardware protection.
     */
    UNKNOWN;

    /**
     * Whether a Device Auth key at this level may be used for production registration
     * and production network authentication.
     *
     * Fail-closed: only levels where the platform positively proved hardware backing
     * are eligible.
     */
    val isProductionEligible: Boolean
        get() = this == STRONGBOX || this == TRUSTED_EXECUTION_ENVIRONMENT
}
