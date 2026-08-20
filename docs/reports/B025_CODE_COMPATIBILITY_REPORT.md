# B025 Code Compatibility Report — STEP-3B

**Task ID:** STEP-3B  
**Branch:** `architecture/b025-main-sync`  
**Starting HEAD:** `c076528e26e5e3ed05b4d0aeed794894f1f78b5e`  
**Authority:** `ANOX_MASTER_HANDOFF_B025_2026-08-20` (extracted to `/tmp/anox_b025/ANOX_MASTER_HANDOFF_B025_2026-08-20`)  
**Date:** 2026-08-20

---

## A. Baseline verified

| Check | Result |
|-------|--------|
| Repository identity | `https://github.com/anox-admin/ax-messenger.git` |
| Branch | `main` |
| HEAD | `c076528e26e5e3ed05b4d0aeed794894f1f78b5e` |
| `v1-foundation-baseline` tag | `7db20fa4df8dc70392afd803fabaaf20c0b50d7d` unchanged |
| Working tree at start | clean |
| TOOLCHAIN-001 merged | yes — `AGP 8.13.2`, `KGP 2.4.10`, `Compose plugin 2.4.10`, `Gradle 9.3.1` |

---

## B. Productive code compatibility result

The existing Rust crypto/Android local-state foundation was inspected against B-025. No direct conflict was found that requires a primitive or E2EE redesign. The B-025 authority confirms the current local protected-state envelope, Keystore-wrapped state key, typed JNI handles and vodozemac 0.10.0 direction remain valid.

The only productive-code change in STEP-3B was the Android backup/D2D hardening (`android:allowBackup="false"` retained, `dataExtractionRules` added). No protected foundation source was modified.

---

## C. Documentation drift corrected

- Added `docs/authority/B025/` with the exact frozen B-025 material and an index.
- Overwrote repository working docs with B-025 authority for:
  - `PROJECT_STATE.md`
  - `FORTSCHRITT.md`
  - `docs/current/SECURITY_INVARIANTS.md`
  - `docs/current/SYSTEM_ARCHITECTURE.md`
  - `docs/current/OPEN_ARCHITECTURE_ITEMS.md`
- Prepend B-025 authority notices to the remaining `docs/current/*.md` files.
- Marked `docs/reports/current-code-gap-audit.md` as SUPERSEDED and pointed to the B-025 gap matrix.
- Updated `README.md`, `CHANGELOG.md`, `MAIN_PLAN_DE.md`, `docs/README.md` with B-025 authority status.

Key drift corrected:
- Device Auth target is P-256 / ES256 / Android Keystore + RFC9449-style DPoP (not Ed25519).
- No refresh token.
- Exactly one active device; no account recovery; no multi-device.
- QR is discovery only; SAS is cryptographic verification.
- Same-account/device `KEY_CHANGED` blocks communication; no "trust changed key" shortcut.
- FCM is optional wake-only transport; `/sync` is authoritative.
- Attachment encryption is endpoint-side before upload; backend never receives attachment key.
- Certificate pinning is not a V1 requirement.
- Behavioral analytics are none.

---

## D. Android backup / D2D finding

The `AndroidManifest.xml` already had `android:allowBackup="false"`. For Android 12+ the application additionally now declares `android:dataExtractionRules="@xml/data_extraction_rules"`.

After STEP-3B.1 architect review, the resource `android/src/main/res/xml/data_extraction_rules.xml` fail-closed excludes the full applicable set of app-owned storage domains from both `cloud-backup` and `device-transfer`:

- `root`
- `file`
- `database`
- `sharedpref`
- `external`
- `device_root`
- `device_file`
- `device_database`
- `device_sharedpref`

For Android 11 and below, `android:allowBackup="false"` is the authoritative control that disables full app backup to Google servers; `dataExtractionRules` are only consulted on Android 12+ (API 31+). No legacy `fullBackupContent` rule is necessary.

---

## E. Protected foundation status

No unauthorized changes were made to:

- `crypto/rust/src/identity.rs`
- `crypto/rust/src/session.rs`
- `crypto/rust/src/serialization.rs`
- `crypto/rust/src/lib.rs`
- `crypto/rust/src/error.rs`
- `CryptoNative.kt`
- `CryptoBridge.kt`
- vodozemac architecture/version
- JNI ownership/typed handle architecture
- `K_STATE` model
- AES-256-GCM protected-state format
- `[ANOX][0x01]` envelope
- AGP / KGP / Compose plugin / Gradle / NDK versions
- checked-in native `.so` binaries

`git diff main..HEAD --stat` shows changes only in `docs/`, `PROJECT_STATE.md`, `FORTSCHRITT.md`, `README.md`, `CHANGELOG.md`, `MAIN_PLAN_DE.md`, `android/src/main/AndroidManifest.xml`, and `android/src/main/res/xml/data_extraction_rules.xml`. No Rust/JNI/CryptoBridge/Gradle files changed.

---

## F. Files changed

- `docs/authority/B025/` (new authority area)
- `PROJECT_STATE.md`
- `FORTSCHRITT.md`
- `README.md`
- `CHANGELOG.md`
- `MAIN_PLAN_DE.md`
- `docs/README.md`
- `docs/current/*.md` (B-025 notices or full overwrite)
- `docs/reports/current-code-gap-audit.md` (superseded header)
- `android/src/main/AndroidManifest.xml`
- `android/src/main/res/xml/data_extraction_rules.xml` (new)
- `docs/reports/B025_CODE_COMPATIBILITY_REPORT.md` (this report)

---

## G. Tests actually executed

| Test | Result |
|------|--------|
| `cd crypto/rust && cargo test` | **PASS** — 15/15 |
| `git diff --check` | **PASS** (after trailing-whitespace fix) |

---

## H. Tests not run / unverified

| Test | Reason |
|------|--------|
| `./gradlew :android:assembleDebug` | No local JDK/Android SDK in this environment |
| `./gradlew :android:assembleRelease` | No local JDK/Android SDK in this environment |
| `./gradlew :android:connectedDebugAndroidTest` | No emulator/device in this environment |
| Merged manifest backup policy inspection | No local Android build output; CI build is the regression proxy |
| GrapheneOS physical-device test | Not available in CI |

---

## I. CI results

GitHub Actions `anoX V1 CI` run `32372225161` on PR #2:

| Job | Result |
|-----|--------|
| Rust crypto tests | **PASS** |
| Android debug build | **PASS** |
| Android release compile smoke | **PASS** |

---

## J. Security invariants check

No security invariants were violated. The Android backup hardening directly supports Invariant 25 (private state excluded from Android/cloud backup; no recovery path may be introduced by backup/restore).

---

## K. GrapheneOS physical-device status

UNVERIFIED — not executed.

---

## L. Remaining implementation gaps

Implementation gaps are now recorded in `docs/authority/B025/IMPLEMENTATION_GAP_MATRIX.md` and summarized in `docs/current/OPEN_ARCHITECTURE_ITEMS.md`. They are architecture-frozen but not yet implemented; no new OPEN architecture questions were introduced by this sync.

---

## M. Explicit statement

**PROMPT-007 was NOT executed. Device Authentication was NOT implemented. No backend, messaging, contacts, or E2EE redesign occurred.**

---

## N. PR

https://github.com/anox-admin/ax-messenger/pull/2

---

## O. Blockers

- Branch protection / rulesets are still unavailable on the free private GitHub plan (same as before).
- Secret scanning / push protection are still unavailable on the free private GitHub plan.

---

## P. STEP-3B.1 architect-review correction

- Narrow follow-up on `data_extraction_rules.xml`.
- Added all 9 applicable app-owned backup domains to both `<cloud-backup>` and `<device-transfer>`.
- Confirmed pre-Android-12 `android:allowBackup="false"` is sufficient; no legacy `fullBackupContent` rule added.
- Re-pushed to PR #2; CI re-run passed.

## Q. Result

**STEP-3B / STEP-3B.1 RESULT: PASS — READY FOR ARCHITECT REVIEW**
