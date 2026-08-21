# DRAFT — PROMPT-007 Device Authentication Foundation

**Do not execute until B-025 sync is merged and actual repo re-inspected.**

Objective: implement the minimum B-002 Device Authentication foundation in the existing anoX project without changing E2EE/local-state cryptography or implementing account/license/backend messaging beyond the interfaces/tests required for Device Auth.

Must use Android Keystore P-256/ES256, hardware-backed production policy, narrow Kotlin abstraction, no private-key export, no biometric-per-sign requirement, no Ed25519 Device Auth, no refresh token, no recovery/device replacement. Design proof objects around RFC9449 DPoP claims and a testable verifier boundary; do not invent custom canonical signing bytes. Add negative tests for wrong method/URL/token hash, expired/future iat, duplicate jti, wrong key/device, malformed proof and Keystore invalidation. If an API/library behavior is uncertain, STOP and report authoritative API evidence before implementing a workaround.

A final coding prompt should be generated only after the B-025 compatibility report identifies the exact modules/files and current dependency baseline.
