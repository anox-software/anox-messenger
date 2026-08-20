# B-021 — Global Security Test Matrix
**Status:** FROZEN v1.1

Release-blocking matrix spans unit, property/negative, integration, Android instrumentation, crash/process-kill, API/authz/RLS, multi-node abuse, infrastructure, update/signing, backup/restore/DR and physical GrapheneOS tests.

Mandatory classes include: real vodozemac Alice↔Bob flows, malformed/modified/wrong-session messages; JNI handle/stale/double-destroy/error safety; local envelope/Keystore corruption; Device Auth nonce/DPoP/token binding/replay/key invalidation; license/register races/idempotency; RLS/BOLA/IDOR; OTK/fallback atomic claims and 15d fallback boundary; outgoing/incoming/prekey crash atomicity; duplicate/replay/sync cursor replay; KEY_CHANGED substitution; SAS commitment/MAC/transcript flows; FCM loss/duplicate/no-Google mode; attachment boundary sizes/wrong key/hash/truncation/reorder/final-tag/path/authorization/cleanup; logout/expiry/revoke/delete/wipe/no-recovery; deletion-journal restore; retention cleanup; release signer/update metadata/rollback; backup/DR; admin MFA/RBAC/break-glass.

Production gate: required FAIL=0, required NOT RUN=0, required UNVERIFIED=0. Emulators do not replace physical GrapheneOS for release. Tests are evidence, not proof of complete security; B-022 independent audit still required.

**Export note:** This file preserves the frozen test domains and specific boundaries visible in current accepted evidence. The final test implementation should map every current B-spec requirement to test IDs rather than rely on this prose alone.
