# PROJECT_STATE — anoX Messenger V1

**Date:** 2026-08-20
**Architecture:** Track B B-001…B-023 frozen/defined, B-024 PASS, B-025 complete, B-026 in review.
**Functional implementation:** approximately 27%.

## Repository truth

- Branch: `main`
- Current HEAD: `648b70391085ea5252cc9f88375064420f1b78d9`
- B-025 PR #2: merged at `75c11c823ec68cea576912b4095fa7a26ed33a33`
- Current work branch: `governance/continuity-001`
- Latest main CI: `32377964672` PASS
- Foundation baseline tag: `v1-foundation-baseline` → `7db20fa4df8dc70392afd803fabaaf20c0b50d7d`
- GIT-001: FULL PASS in repo documentation.
- TOOLCHAIN-001: PR #1 merged; main CI run `32344459447` recorded PASS for Rust/debug/release compile smoke.
- Current extracted upload showed only executable-mode changes on `gradlew` and two `.so` files; their content hashes equal HEAD. Use clean Git snapshot as implementation baseline.

## Checked-in toolchain

AGP 8.13.2; Kotlin Gradle Plugin 2.4.10; Compose plugin 2.4.10; Gradle 9.3.1; JDK 17; NDK 26.2.11394342; compileSdk/targetSdk/minSdk 34/34/26. Rust evidence reports 1.97.1/cargo-ndk 4.1.2; Cargo pins vodozemac 0.10.0 and aes-gcm 0.10.3.

## Implemented / accepted at implemented-test level

- Minimal Android/Compose app foundation.
- Rust vodozemac crypto foundation with real session round-trip/negative tests.
- JNI bridge and typed identity/session handle safety.
- AES-GCM local state protection with Android Keystore-wrapped random state key.
- Versioned state envelope `[ANOX][0x01][12-byte nonce][ciphertext+tag]`, AAD magic/version.
- Atomic file persistence, state lifecycle/fail-closed status, local wipe APIs.
- Historical accepted test evidence: Rust 15/15; Android connected 35/35; release build PASS.

## Not implemented

- B-002 Device Authentication.
- B-003 production account/license registration.
- B-004 backend service.
- B-005 production database/RLS.
- B-006 server key distribution/claims.
- B-007 production API.
- B-008 network messaging/sync.
- B-009 SQLCipher messenger DB/outbox.
- B-010 contacts/SAS product flow.
- B-011 push/offline jobs.
- B-012 attachment secretstream/storage.
- B-013 production server lifecycle.
- Production privacy/abuse/infrastructure/signing/operations/test/audit/release gates.

## STEP-3B — B-025 repository synchronization (2026-08-20)

- Branch: `architecture/b025-main-sync`
- B-025 authority area added at `docs/authority/B025/`.
- Documentation drift corrected; Device Auth, refresh token, recovery, multi-device, QR/SAS, push, attachments, and other stale statements are now aligned with B-025.
- Android backup/D2D hardening added: `android:allowBackup="false"` retained, `dataExtractionRules` excludes all 9 app-owned storage domains (`root`, `file`, `database`, `sharedpref`, `external`, `device_root`, `device_file`, `device_database`, `device_sharedpref`) from both cloud backup and device transfer.
- Protected foundation (crypto, JNI, build tooling, native `.so`) unchanged.
- `cargo test`: 15/15 PASS (local).
- GitHub Actions CI run `32372225161` on PR #2: Rust, Android debug, and Android release compile smoke all PASS.
- PR #2 merged; main HEAD `75c11c823ec68cea576912b4095fa7a26ed33a33`; post-merge CI `32376668391`: Rust, Android debug, and Android release compile smoke all PASS.
- Connected Android instrumentation: NOT RUN in CI (no emulator); historical 35/35 remains accepted.
- PROMPT-007 was not executed.

## CONTINUITY-001 — Development governance and handoff foundation

- Branch: `governance/continuity-001`
- B-026 governance specification: `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`
- Master authority index: `docs/authority/AUTHORITY_INDEX.md`
- New `docs/continuity/` directory with handoff, bootstrap, Git state, implementation state, open work, next task, output contract, workflow, and validation checklist.
- New `tools/continuity/validate_continuity.py` and `tools/continuity/generate_handoff.py` (Python 3 standard library only, no network).
- `validate_continuity.py` requires clean working tree, required files, and B-025/B-026 authority.
- `generate_handoff.py` creates `artifacts/handoff/ANOX_HANDOFF_*.zip` with file manifest and SHA-256 manifest.
- Android/Rust product source unchanged.
- Result: PASS — ready for architect review.

## CONTINUITY-001.1 — Governance registry and handoff package validation

- Branch: `governance/continuity-001`
- Created current `docs/authority/B_FREEZE_REGISTRY.md` (B-001…B-026) while preserving `docs/authority/B025/B_FREEZE_REGISTRY.md` as immutable B-025 snapshot.
- Updated `docs/authority/AUTHORITY_INDEX.md`, `B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`, and `validate_continuity.py` to reference the current registry.
- Generated handoff ZIP on current branch; ran `ZipFile.testzip()` (PASS), internal SHA-256 manifest verification (170/170 entries verified, 0 mismatches), exclusion scan (0 prohibited members), secret-pattern sanity scan (0 obvious secret artifacts), dirty-tree negative test (generator and validator both fail on dirty tree), and validator missing-file negative test (non-zero exit, clear reason).
- Re-ran `validate_continuity.py` and `generate_handoff.py` after commit: expected PASS.
- Product source unchanged; next gate remains `CONTINUITY-001 ARCHITECT RE-REVIEW`.

## CONTINUITY-001.2A — Historical provenance ingestion and master parity correction

- Branch: `governance/continuity-001`
- Ingested historical provenance from `ANOX_MASTER_HANDOFF_B025_2026-08-20.zip` into `docs/history/B025/`:
  - `00_START/`, `03_WORKFLOWS/`, `05_ENGINEERING_NEXT/`, `06_AUDITS/`, `07_DEVIN_HISTORY/`, `90_HISTORICAL/`
  - `REPOSITORY_PROVENANCE/` with `REPOSITORY_SNAPSHOT_MANIFEST.md` and `GIT_BUNDLE_STATUS.md`
- Created `docs/history/B025/README.md`, `SOURCE_INDEX.md`, `docs/history/README.md`.
- Updated `docs/continuity/CURRENT_HANDOFF.md` and `docs/continuity/HISTORICAL_HANDOFFS/README.md` to reference the historical archive.
- Full-history Git bundle intentionally not replicated; reason documented.
- Product source unchanged.
- Re-generated handoff `ANOX_HANDOFF_2026-08-20_c2b3afc1b93e.zip`; parity verified PASS: 241 members, 238/238 manifest entries verified, 0 prohibited, 0 secret, 20/20 reconstruction questions ANSWERABLE.
- New `docs/reports/CONTINUITY_001_2_MASTER_PARITY_AUDIT.md` created.

## CONTINUITY-001.3A — Atomic handoff state consistency fix

- Branch: `governance/continuity-001`
- Cold new-chat bootstrap for `ANOX_HANDOFF_2026-08-20_c2b3afc1b93e.zip` returned `BLOCKED` because recorded `CURRENT_GIT_STATE.md`, `PROJECT_STATE.md`, `CURRENT_NEXT_DEVIN_TASK.md`, and `CURRENT_HANDOFF.md` described the merged `main` baseline instead of the current handoff branch `governance/continuity-001`.
- Corrected `CURRENT_GIT_STATE.md` and `PROJECT_STATE.md` to explicitly separate **merged baseline** (`main`) from **current handoff / work state** (`governance/continuity-001`).
- Introduced `docs/continuity/CURRENT_STATE.json` as machine-readable canonical continuity metadata with placeholders for `handoff_head` and `working_tree` that `generate_handoff.py` resolves at generation time.
- Updated `CURRENT_HANDOFF.md` and `CURRENT_CHAT_BOOTSTRAP_PROMPT.md` to reference the canonical `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md` path.
- Extended `validate_continuity.py` to fail on branch/HEAD/authority/gate inconsistencies.
- Extended `generate_handoff.py` to validate continuity state before packaging and to fail closed if validation fails.
- Product source unchanged.

## CONTINUITY-001.3 — Cold new-chat bootstrap retest

- Tested handoff: `ANOX_HANDOFF_2026-08-21_06023258f60e.zip`
- Branch: `governance/continuity-001`, HEAD `06023258f60e086d3a8f04e6fe98dc8bab0a0493`
- Result: `BOOTSTRAP RESULT: PASS — READY TO ACCEPT HANDOFF`
- The clean ChatGPT conversation successfully reconstructed: merged baseline, current handoff/work state, authority hierarchy, Security Invariants, implementation truth, missing features, current gate, historical provenance, and Git snapshot.
- Next gate: `CONTINUITY-001 FINAL ARCHITECT REVIEW / PR #3 MERGE GATE`

## CONTINUITY-001.3B — Cold-bootstrap pass finalization

- Branch: `governance/continuity-001`
- Recorded `CONTINUITY-001.3` PASS.
- Corrected B-010 path in `docs/authority/B_FREEZE_REGISTRY.md` from `B010_CONTACTS_AND_VERIFICATION.md` to `B010_CONTACTS_VERIFICATION.md`.
- Added handoff ZIP retention/performance policy to `docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md`.
- Synchronized `README.md` test evidence with current records (15/15 Rust, 35/35 Android instrumentation historical).
- Updated `CURRENT_STATE.json`, `CURRENT_GIT_STATE.md`, `CURRENT_HANDOFF.md`, and `CURRENT_NEXT_DEVIN_TASK.md` to the final architect-review gate.
- Product source unchanged.
- PR #3 remains open and unmerged.
