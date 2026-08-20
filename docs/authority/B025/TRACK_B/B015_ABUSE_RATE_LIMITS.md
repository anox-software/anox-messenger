# B-015 — Abuse / Rate Limits
**Status:** FROZEN

Core policy: abuse controls are centralized/shared across backend instances and never depend only on per-process RAM. Rate limit by authenticated device/account plus privacy-conscious network signals where needed, with anti-enumeration-safe responses. Cover registration/license attempts, auth/token/nonce operations, username/contact requests/invites, session-init claims, message send/sync, delivery/read receipts, push registration and attachment reservation/upload capability issuance.

Controls include bounded request body sizes, pagination, concurrency, queue depth, storage/message quotas, timeouts, backpressure and retry budgets. DoS/flooding must fail safely without bypassing authorization or deleting E2EE state. Security events should record class/rate/request-id without plaintext/secrets.

B-023 release tests require registration/auth throttles, message/contact/attachment quotas and cross-node backpressure to be active in production-like infrastructure.

**Export note:** The original verbatim B-015 turn is not present as a standalone artifact. No additional numeric thresholds are fabricated here. If a specific endpoint limit is absent from B-007/B-008/B-012 or this package, retrieve the original source or freeze it explicitly before coding that threshold.
