# SUPERSEDED

> **Status:** SUPERSEDED by the B-025 architecture package.
>
> The current implementation gap matrix is at `docs/authority/B025/IMPLEMENTATION_GAP_MATRIX.md` and is mirrored in `docs/current/OPEN_ARCHITECTURE_ITEMS.md`.
>
> The historical body below is retained for reference.

---

# anoX V1 — Current Code Gap Audit

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

This report records known code gaps identified during the repository audit. It does **not** claim these issues are fixed. Implementation is explicitly out of scope for DOCSYNC-001.

## CODE-CRITICAL-001 — Raw JNI Handles

**Observation:** Native `Identity` and `Session` handles are distributed to Kotlin as `jlong` (`Box::into_raw`), and destroyed with `Box::from_raw`.

**Potential issues:**
- use-after-free
- double-free
- type confusion (e.g., passing an Identity handle to a Session-expecting API)
- stale handle dereference

**Mitigation status:** A runtime active-handle registry was added to reject destroyed/unknown handles in the current implementation, but this does not eliminate all stale-handle risks.

## CODE-CRITICAL-002 — Untyped Long Handles

**Observation:** Kotlin passes `Long` handles to native APIs without compile-time type distinction between `Identity` and `Session`.

**Potential issue:** Native type confusion and undefined behavior.

**Status:** OPEN.

## CODE-HIGH-003 — Panic Containment

**Observation:** No centralized panic containment around the JNI `extern` boundary.

**Status:** OPEN.

## CODE-MEDIUM-004 — Session Pointer Leak

**Observation:** In the inbound-session JNI error path, a `Session` pointer may be allocated and not freed or returned to Kotlin.

**Status:** OPEN.

## CODE-MEDIUM-005 — No State Serialization Version

**Observation:** The serialized crypto state has no explicit version byte/envelope version.

**Status:** OPEN hardening item.

## CODE-MEDIUM-006 — `CryptoSerializer::new()` Panic

**Observation:** `CryptoSerializer::new()` assumes a 32-byte key and can panic if misused.

**Status:** OPEN.

## CODE-MEDIUM-007 — Logging Redaction

**Observation:** Production logging uses `Log.e(..., exception)` and requires later redaction/hardening review.

**Status:** OPEN.

## CODE-MEDIUM-008 — `destroyAllCrypto()` Incomplete Wipe

**Observation:** `destroyAllCrypto()` deletes the Keystore entry but does not itself remove all wrapped/local/future DB/temp artifacts.

**Status:** OPEN.

## CODE-INFO-009 — Instrumentation Tests

**Observation:** Instrumentation tests existed prior to runtime verification; now **19/19 PASS** on `anox_api34_arm64` API 34 emulator. See `docs/security/android-runtime-crypto-validation-report.md`.

## CODE-INFO-010 — NDK Already Pinned

**Observation:** NDK is pinned in `android/build.gradle.kts` as `26.2.11394342`. Older docs claiming "NDK not pinned" are stale.
