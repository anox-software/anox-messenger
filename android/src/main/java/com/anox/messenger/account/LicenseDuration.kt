package com.anox.messenger.account

/**
 * Frozen B-003 v1.4 standard license durations.
 *
 * ONLY 30, 90 and 180 days exist in the current authority. A 365-day/one-year standard license
 * and a general one-week V1 trial are superseded historical concepts and are deliberately NOT
 * represented here. Introducing either would require an explicit architecture decision and a
 * B-003 version bump; it must not be added silently.
 */
enum class LicenseDuration(val days: Long) {
    DAYS_30(30),
    DAYS_90(90),
    DAYS_180(180)
}
