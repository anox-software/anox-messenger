package com.anox.messenger.account

/**
 * Frozen B-003 device states. Server-authoritative; the client never derives this locally.
 *
 * V1 supports exactly one active device per account. There is no add-device, replace-device,
 * transfer-device or multi-device flow, and no state here represents one.
 */
enum class DeviceState {
    ACTIVE,
    REVOKED
}
