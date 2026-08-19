# anoX V1 — Open Architecture Items

**Status:** CURRENT  
**Architecture Baseline:** RAW1.60–RAW1.75 consolidated  
**Last synchronized:** 2026-08-19

---

These items are genuinely **OPEN** and require an explicit architecture decision record (ADR) to close.

## 1. Authentication / Token Contract

The exact production auth/token/challenge/signature contract is not frozen.

## 2. Push Provider / Transport

Provider/transport selection is not frozen.

## 3. Offline Queue TTL

Exact ciphertext TTL for offline recipients is not frozen.

## 4. DB Schema

Final DB schema is not frozen.

## 5. Attachment AEAD

XChaCha20-Poly1305 is planned only if supported by the final maintained Rust library.

## 6. Certificate Pinning

Not a mandatory V1 decision.

## 7. State Serialization Versioning

Current serialization has no explicit version byte. Adding an envelope version is a hardening item.

## 8. UnifiedPush / FCM

Do not document as the current binding architecture.

## 9. 1-Year License Plan

Not a current binding V1 plan.

## 10. Support Staff Architecture

- support virtual-device architecture
- HA/load balancing model
- support key backup
- special retention
- ticket-system integration
- server-signed support trust model

These operational support concerns are not current binding V1 cryptographic architecture.
