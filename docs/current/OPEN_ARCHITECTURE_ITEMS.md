> **B-025 Authority Notice**
>
> This file is the B-025 implementation gap matrix. The canonical matrix lives at `docs/authority/B025/IMPLEMENTATION_GAP_MATRIX.md`.
>
# Implementation Gap Matrix — B-025

| Area | Current repository | B-025 target | Classification |
|---|---|---|---|
| Android starter UI | minimal | full B-020 UX | MISSING_FEATURE |
| Rust/vodozemac | implemented foundation, 0.10.0 | keep narrow Rust/vodozemac boundary | COMPLIANT, regression required |
| JNI handle safety | implemented/tested historically | narrow typed boundary | COMPLIANT, regression required |
| Local crypto envelope | implemented files + Keystore | retained for E2EE state, later migrate into B-009 DB | COMPLIANT FOUNDATION / FUTURE MIGRATION |
| Device Auth | absent; docs incorrectly say Ed25519 | P-256/ES256/DPoP | MISSING_FEATURE + DOC_ONLY drift |
| Refresh token | no production auth implemented; old docs mention refresh | no refresh token | DOC_ONLY now; ensure future code follows B-002 |
| Account/license | absent | B-003 | MISSING_FEATURE |
| Backend/API | placeholder | B-004/B-007 | MISSING_FEATURE |
| PostgreSQL/RLS | absent | B-005 | MISSING_FEATURE |
| Key distribution server flow | absent | B-006 | MISSING_FEATURE |
| Network messaging/sync | absent | B-008 | MISSING_FEATURE |
| SQLCipher local DB | absent | B-009 | MISSING_FEATURE |
| Contacts/SAS | absent; old docs ambiguous SAS/QR | B-010 | MISSING_FEATURE + DOC_ONLY drift |
| Push | absent; old docs provider OPEN | FCM HTTP v1 optional wake-only | MISSING_FEATURE + DOC_ONLY drift |
| Attachments | absent; old docs crypto OPEN | secretstream/libsodium | MISSING_FEATURE + DOC_ONLY drift |
| Lifecycle server actions | absent | B-013 | MISSING_FEATURE |
| Privacy/retention workers | absent | B-014 | MISSING_FEATURE |
| Abuse controls | absent | B-015 | MISSING_FEATURE |
| Production infra | absent | B-016 | MISSING_FEATURE |
| CI | minimal current CI | B-017 hardened CI/supply-chain | UPDATE_REQUIRED before production; not a crypto-foundation rewrite |
| Signing/update | absent | B-018 | MISSING_FEATURE |
| Ops/IR | docs/planning only | B-019 | MISSING_FEATURE |
| Security matrix/audit/DoD | not executed for full product | B-021/B-022/B-023 | FUTURE RELEASE GATE |

## Preliminary recommendation

Do **not** broadly rewrite the current crypto/local-state foundation just because the architecture expanded. Static inspection found no obvious direct conflict requiring a new primitive or a new vodozemac design. The first necessary update is documentation/authority synchronization and a targeted regression/compatibility audit. Existing local state will need an explicit B-009 migration when the encrypted messenger DB is implemented. CI/supply-chain controls also need later hardening under B-017.
