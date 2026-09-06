# B-025 Mandatory Amendments V1.3

**Status:** FROZEN / CURRENT  
**Date:** 2026-09-05  
**Authority:** Human-authorized `MAINARCH-FIX-03` traceability / test-matrix / release-governance / implementation-readiness architecture remediation (ANOX-MAINARCH-011, 024, 026, 027, 036).  
**Supersedes:** This document is an authoritative successor amendment to specific provisions in `docs/authority/B025/TRACK_B/` for **B-018, B-019, B-021, and B-023**, and it establishes the canonical **Security Invariant Traceability**, **Verification/Evidence State Model**, and **Implementation-Readiness State Model**. `B025_MANDATORY_AMENDMENTS_V1_1.md` and `B025_MANDATORY_AMENDMENTS_V1_2.md` remain in force for their respective domains.

This document does **not** modify the B-025 historical snapshot in `docs/authority/B025/TRACK_B/`. The snapshot files remain immutable provenance. `docs/authority/B_FREEZE_REGISTRY.md` and `docs/authority/AUTHORITY_INDEX.md` record the amended current versions.

This is an **architecture/governance-only** freeze. No Product implementation, no signing keys, no secrets, no CI workflow changes, and no GitHub repository configuration changes are created by this amendment.

---

## Security Invariant Traceability (remediates ANOX-MAINARCH-011)

The 35 binding Security Invariants in `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md` now have a canonical, deterministic traceability architecture.

### 1. Canonical surfaces

- **Canonical invariant text:** `docs/authority/B025/SECURITY_INVARIANTS_V1_1.md` — the only authoritative source of invariant prose. Nothing in this amendment, the traceability registry, or any document may restate or redefine invariant text.
- **Machine-readable traceability registry:** `docs/workforce/registries/security_invariant_traceability.jsonl` — one row per invariant `INV-01` … `INV-35`.
- **Human-readable architecture:** `docs/security/SECURITY_INVARIANT_TRACEABILITY.md` — model description and summary matrix.
- **Deterministic enforcement:** `tools/audit/validate_mainarch_fix03.py` validates completeness, uniqueness, authority references, and state-model consistency.

### 2. Per-invariant record contract

Each traceability row records, at minimum:

| Field | Meaning |
|-------|---------|
| `invariant_id` / `invariant_number` | Stable ID `INV-NN` bound to the invariant's ordinal in `SECURITY_INVARIANTS_V1_1.md`. |
| `source` | Pointer to the authoritative source (`SECURITY_INVARIANTS_V1_1.md#<n>`). Never a copy of the text. |
| `domains` | Affected B-domain(s) (e.g. `B-004`, `B-005`). |
| `enforcement_surfaces` | Expected enforcement surface classes: `ARCHITECTURE_GOVERNANCE`, `CLIENT_ANDROID`, `RUST_CRYPTO`, `BACKEND_B004`, `DB_B005`, `API_B007`, `LOCAL_STORAGE_B009`, `INFRA_B016`, `REPO_CI_B017`, `RELEASE_GOVERNANCE`, `DOCS_COPY`. |
| `verification_ids` | Stable verification/test IDs from the B-021 matrix (`ANOX-TEST-*`). |
| `implementation_state` | `NOT_APPLICABLE` / `NOT_STARTED` / `PARTIAL` / `IMPLEMENTED`. |
| `automated_state` | `NOT_APPLICABLE` / `NOT_RUN` / `PARTIAL` / `PASS` (PASS requires `automated_evidence`). |
| `physical_state` | `NOT_APPLICABLE` / `REQUIRED_PENDING` / `VERIFIED`. |
| `external_state` | `NOT_APPLICABLE` / `REQUIRED_PENDING` / `VERIFIED`. |
| `verification_state` | Highest attained rung: `SPECIFIED` < `IMPLEMENTED` < `TESTED` < `PHYSICALLY_VERIFIED` < `EXTERNALLY_VERIFIED`. |
| `evidence_state` | Current evidence state, see §3. |
| `pre_product_gate` / `release_gate` | Gate applicability for the B027-C pre-product gate and the B-022/B-023 release gate. |

### 3. Evidence state model

Canonical evidence states (repository-compatible, mapped to B-027 evidence levels E0–E4 without redefining them):

| Evidence state | Meaning | B-027 mapping |
|----------------|---------|---------------|
| `NOT_APPLICABLE` | No verification applicable (pure doctrine/process constraint). | E0 |
| `SPEC_ONLY` | Only specification/freeze exists; no implementation or verification evidence. | E1 (spec artifact exists) |
| `IMPLEMENTED_UNVERIFIED` | Implementation or partial enforcement exists; no verification evidence attained. | E1 |
| `AUTOMATED_VERIFIED` | Deterministic/automated evidence exists and is recorded. | E2 |
| `PHYSICAL_VERIFICATION_REQUIRED` | Binding next requirement is physical-device verification that no repository artifact can substitute. | requires E3 on hardware |
| `EXTERNAL_REVIEW_REQUIRED` | Binding next requirement is independent/external review. | requires E3/E4 |
| `VERIFIED` | All required verification dimensions satisfied. | E3–E4 |

**No-false-verification rule:** architecture/specification correctness must never be recorded as implementation or verification evidence. A frozen specification yields at most `SPEC_ONLY` (E1). `SPECIFIED` ≠ `IMPLEMENTED` ≠ `TESTED` ≠ `PHYSICALLY_VERIFIED` ≠ `EXTERNALLY_VERIFIED`. The dimensional fields (`implementation_state`, `automated_state`, `physical_state`, `external_state`) are independently recorded so these can never collapse into one flag. Examples that are explicitly invalid: "B-004 spec exists" ⇒ implementation of B-004; "B-005 schema frozen" ⇒ SQL/RLS deployed; "StrongBox requirement exists" ⇒ physical StrongBox verified.

### 4. Current traceability result

All 35 invariants are traced. No invariant currently attains `PHYSICALLY_VERIFIED` or `EXTERNALLY_VERIFIED`; physical GrapheneOS/StrongBox verification remains pending under ANOX-MAINARCH-018, and independent external review remains pending under B-022.

---

## B-021 — Global Security Test Matrix (amended v1.2-f03; remediates ANOX-MAINARCH-026)

The frozen B-021 v1.1 text remains in force and is extended by this deterministic implementation-level verification architecture. The B-021 prose gate (`FAIL=0`, `NOT RUN=0`, `UNVERIFIED=0` for release) is now machine-evaluable.

### 1. Canonical matrix

- **Machine-readable matrix:** `docs/workforce/registries/b021_verification_matrix.jsonl` — one row per required verification.
- **Deterministic enforcement:** `tools/audit/validate_mainarch_fix03.py` validates ID uniqueness, domain coverage, result-state honesty, and gate semantics.

### 2. Stable test ID namespace

- `ANOX-TEST-B0NN-MMM` — domain-level verification for B-domain `B-0NN` (e.g. `ANOX-TEST-B002-001`).
- `ANOX-TEST-INV-NN` — invariant-level verification for Security Invariant `NN`.
- IDs are assigned once, are never reused for a different security property, and remain stable across later implementation. Retiring a test requires an explicit superseded-by record, never ID reuse.

### 3. Execution classes

Every matrix row is classified by exactly one execution class:

| Class | Meaning |
|-------|---------|
| `REPO_STATIC` | Deterministic repository/static validation (validators, linters, policy scans). |
| `JVM_UNIT` | JVM/Kotlin unit tests. |
| `RUST` | Rust-side tests (vodozemac/JNI boundary). |
| `ANDROID_EMULATOR` | Android instrumentation/emulator tests. |
| `PHYSICAL_GRAPHENEOS` | Physical GrapheneOS device tests (StrongBox/TEE, no-Google mode, device loss). No emulator or repository artifact may substitute. |
| `BACKEND_INTEGRATION` | Backend/API/DB/RLS integration tests. |
| `INFRA_DR` | Infrastructure, backup/PITR/restore, DR, multi-node tests. |
| `HUMAN_RELEASE_PROCEDURE` | Human-controlled release/signing/ops procedures with recorded evidence. |
| `INDEPENDENT_AUDIT` | Independent external review under B-022. |

No class may be silently substituted by another: a repository validator cannot satisfy a `PHYSICAL_GRAPHENEOS`, `HUMAN_RELEASE_PROCEDURE`, or `INDEPENDENT_AUDIT` requirement.

### 4. Result states

| Result | Meaning |
|--------|---------|
| `PASS` | Executed and passed, with recorded evidence. |
| `FAIL` | Executed and failed. |
| `NOT_RUN` | Defined but not executed (e.g. implementation dependency not yet built). |
| `BLOCKED` | Cannot be executed because a recorded finding/dependency blocks it. |
| `NOT_APPLICABLE` | Not applicable, with recorded rationale. |
| `UNVERIFIED` | Requires a verification class not yet attainable (physical device, external audit, unbuilt infrastructure). |

`NOT_RUN`, `BLOCKED`, and `UNVERIFIED` are **not** PASS and are never counted as PASS by any gate.

### 5. Gate semantics — pre-product gate vs release gate

Two distinct gates consume the matrix and must not be conflated:

- **Pre-product gate (B027-C / `FINAL_PRE_PRODUCT_ARCHITECTURE_SECURITY_AUDIT`):** determines whether Product implementation may resume. Matrix rows for unimplemented Product domains are expected to be `NOT_RUN`/`UNVERIFIED`/`BLOCKED` and do **not** by themselves block the pre-product gate. What the pre-product gate requires is that the matrix exists, is complete (all B-002…B-020 domains and all 35 invariants covered), is deterministic, and honestly records states — i.e. rows marked `pre_product_required` must be `PASS` or `NOT_APPLICABLE`.
- **Release gate (B-022/B-023):** determines whether a release may ship. Every row marked `release_required` must evaluate to `PASS` (or `NOT_APPLICABLE` with recorded rationale). `FAIL=0`, `NOT_RUN=0`, `BLOCKED=0`, `UNVERIFIED=0` among `release_required` rows is a hard condition for release authorization.

A Product feature not yet implemented may legitimately be `NOT_RUN` pre-product; the same missing verification is a hard blocker at release.

### 6. Coverage

The matrix covers every applicable implemented/frozen domain B-002 through B-020, the B-021 matrix-integrity self-check, and all 35 Security Invariants (`ANOX-TEST-INV-01…35`). Coverage marked `NOT_RUN`/`UNVERIFIED`/`BLOCKED` for unimplemented or physically unverifiable domains is `PLANNED / NOT IMPLEMENTABLE YET` — explicitly **not** a PASS.

---

## Implementation-Readiness State Model (remediates ANOX-MAINARCH-036)

### 1. Canonical state axes

Every B-domain is tracked on three independent, machine-checkable axes. Canonical surface: `docs/workforce/registries/implementation_readiness.json`.

| Axis | States |
|------|--------|
| `architecture_state` | `NOT_DEFINED` / `DEFINED` / `FROZEN` |
| `implementation_state` | `NOT_STARTED` / `IN_PROGRESS` / `IMPLEMENTED_UNVERIFIED` / `VERIFIED` |
| `release_readiness` | `NOT_RELEASE_READY` / `RELEASE_CANDIDATE` / `RELEASE_AUTHORIZED` |

### 2. The separation axiom

`ARCHITECTURE_FROZEN` does **not** imply implementation complete; `IMPLEMENTED` does **not** imply security verified; `VERIFIED` does **not** imply release ready. These are different state axes and are never merged.

### 3. Current canonical states

- `B-004`: `architecture_state = FROZEN`, `implementation_state = NOT_STARTED`, `release_readiness = NOT_RELEASE_READY`.
- `B-005`: `architecture_state = FROZEN`, `implementation_state = NOT_STARTED`, `release_readiness = NOT_RELEASE_READY`.

All other domain states are recorded in `implementation_readiness.json`. Product development remains `BLOCKED_PENDING_FINAL_AUDIT`.

---

## B-018 — Release Signing + Secure Updates (amended v1.1-f03; remediates ANOX-MAINARCH-024 signing half)

The frozen B-018 text remains in force and is extended by the following canonical release-signing security contract. **No keys are generated, no secret locations are chosen, and no signing environment is built by this amendment.**

### 1. Release signing authority — `K_APK_RELEASE`

- The V1 release-signing private key is designated `K_APK_RELEASE`. Its custodian role is the human-only `ROLE-018` (Human Release Approver / Signing / Break-glass), accountable to `ROLE-001` (Human Product & Security Owner). No other role may custody or use it.
- **AI may never possess, see, or use the `K_APK_RELEASE` private key.** Release-signing secret material is `D4`-class under B-027 and `docs/authority/CLOUD_AI_SECRET_PROTECTION.md`: prohibited AI-secret class. Development machines, AI coding sessions, agents, and CI never receive D4 signing secrets.
- The signing operation requires an explicit human-controlled action by `ROLE-018` (or a higher Authority-defined human). No automated pipeline, agent, or CI job may perform release signing.
- The build artifact presented for signing must be **hash-bound**: the exact artifact hash is recorded before signing, and the signed artifact's hash is recorded after signing. The signature applies to the recorded artifact only.
- Release approval evidence is recorded as a B-027 Decision/E4 attestation: approver role, artifact hash, source commit, SBOM/provenance references, and timestamp.
- **Release signing is a distinct operation from build creation.** CI may produce unsigned/candidate artifacts; production signing is offline/hardware-protected and human-performed (consistent with frozen B-017: "Production signing private key never exists in CI").

### 2. Signing environment requirements (later implementation)

The later signing environment must satisfy:

- isolation from routine AI coding sessions and general development machines;
- least-privilege access limited to the designated human custodian(s);
- human-controlled secret access (the key never enters prompts, logs, repositories, tickets, or AI context);
- an auditable release record (who/what/when/hash);
- a documented backup/recovery policy for signing material with a tested recovery rehearsal that actually restores and signs a test artifact (possession of an unused backup is not sufficient);
- revocation/compromise handling: documented steps to revoke, mark compromised, and rotate;
- an emergency rotation procedure (see §4 emergency release).

This amendment deliberately does **not** choose passwords, seed phrases, HSM credentials, key storage locations, or any secret material.

### 3. Update / downgrade trust state machine

Release/update evaluation must implement at least the following deterministic trust states:

| State | Trigger | Required behavior |
|-------|---------|-------------------|
| `UPDATE_ACCEPT` | Valid signature by the production signer, newer version, intact hash, compatible min-version metadata. | Install after user consent per product UX. |
| `REJECT_INVALID_SIGNATURE` | Signature invalid, corrupt, or hash mismatch. | Refuse install; record security event. |
| `REJECT_UNKNOWN_SIGNER` | Signature valid but not by the production signer (incl. debug/dev keys). | Refuse install; record security event. |
| `REJECT_DOWNGRADE` | Version lower than installed, or below the signed minimum-compatibility floor in update metadata. | Refuse install; record security event. Downgrade is never a silent path. |
| `EMERGENCY_UPDATE` | Security update issued under the §4 emergency path. | Normal signature and metadata checks still apply; only the human-authorized emergency channel may shorten notice windows, never skip verification. |
| `SIGNING_KEY_COMPROMISE` | `K_APK_RELEASE` compromise declared by human incident process. | Mark key compromised; suspend trust in new artifacts from the compromised key per incident decision; initiate rotation procedure; require explicit human decision for any continued-trust period. |
| `REVOKED_RELEASE` | A specific release is revoked after distribution. | Refuse install/update to the revoked artifact; keep installed devices on a safe state per incident runbook. |
| `ROLLBACK_AUTHORIZED` | Rollback only when explicitly human-authorized under emergency policy. | Requires recorded `ROLE-001`/`ROLE-018` decision; never automatic; must preserve DB compatibility (no destructive DB downgrade, per frozen B-018). |

These are architecture states for later implementation; no updater code is created here. Android/GrapheneOS platform realities apply: the OS enforces same-signer update rules, and this contract layers anoX release-governance on top rather than relying on platform checks alone.

### 4. Emergency release path

The emergency path exists for security incidents and is **human-controlled end to end**. It must never permit "security incident → AI self-authorizes emergency release":

```
incident declaration (ROLE-014/ROLE-013 detect & declare; ROLE-001 informed)
→ technical remediation (authorized engineering roles)
→ verification (independent of the writer where required; ROLE-007/ROLE-009)
→ human release approval (ROLE-018, recorded Decision + E4 evidence)
→ human-controlled signing (K_APK_RELEASE, §1 contract)
→ distribution
→ post-incident evidence and review (ROLE-014 record; mandatory post-incident review)
```

No step may be skipped or reordered by an AI agent. A release without the recorded human approval step is not a valid anoX release.

---

## B-019 — Operations + Incident Response (amended v1.1-f03; remediates ANOX-MAINARCH-024 ops half)

The frozen B-019 text remains in force and is extended by the following canonical incident/PSIRT artifact contract. **No personal contact details or secrets are introduced; role/function placeholders are used until real operational contacts are designated by the human owner.**

### 1. Required canonical artifacts (to be produced before release)

| Artifact | Content requirement |
|----------|---------------------|
| Vulnerability intake record | How external/internal reports are received, logged, and acknowledged. |
| `security.txt` | Published at the canonical location(s) with contact role placeholder, policy, and expiry field; content owned per §3. |
| Security contact ownership | Bound to `ROLE-014` (Incident Response / PSIRT) with `ROLE-001` accountability; no personal emails/phone numbers in the repository. |
| Severity/triage model | Severity classes, triage SLA expectations, and escalation thresholds for security reports. |
| Containment runbook | Steps for isolating compromised components (backend node, DB, credentials, signing material). |
| Credential/key compromise runbook | Rotation, revocation, blast-radius assessment, evidence preservation. |
| Malicious/compromised release runbook | Detection, revocation, user notification path, signing-key compromise procedure (B-018 §3–4). |
| Backend compromise runbook | Consistent with the server-compromise model: no plaintext exposure by design; integrity/availability/account-manipulation response. |
| Disclosure coordination policy | Coordinated disclosure expectations, embargo handling, public-summary requirements consistent with B-022. |
| Emergency update procedure | B-018 §4 path; signing remains human-only. |
| Post-incident review record | Mandatory review, root cause, corrective actions, and evidence archive. |

These artifacts are requirements, not yet produced; producing them is an operations task before release, not part of this remediation.

### 2. On-call / responsibility binding

Responsibilities bind to canonical B-027 workforce roles (see `docs/workforce/registries/roles.json`); this section references roles without duplicating or redefining them:

| Responsibility | Canonical role |
|----------------|----------------|
| Detection / observability / SOC | `ROLE-013` |
| Incident response / PSIRT / vulnerability management | `ROLE-014` |
| Architecture / security audit | `ROLE-009` |
| Human release approval / signing / break-glass | `ROLE-018` (human-only) |
| Product / Security Owner (accountable) | `ROLE-001` (human-only) |
| Abuse / trust & safety | `ROLE-015` |
| Platform / SRE / DR | `ROLE-012` |

The frozen B-019 staffing requirements (named primary/secondary on-call, at least two authorized security operators, at least two SUPER_ADMIN-capable owners with approved FIDO2 keys, out-of-band communication) remain binding production prerequisites and are verified by `ANOX-TEST-B019-*` rows before release — not now.

### 3. Evidence rules during incidents

Serious audit/incident findings use immediate escalation and evidence preservation **without** logging user plaintext or private keys (frozen B-019). Incident records are `D`-classed per B-027; no incident workflow may place secrets or user content into AI-reachable channels.

---

## B-023 — V1 Release Definition of Done (amended: branch-protection release gate; remediates ANOX-MAINARCH-027)

### 1. Honest current state

The repository currently operates under a documented **GitHub Free private-repository** configuration in which **server-side branch protection / ruleset enforcement is not available**. Therefore:

- No claim is made that `main` is currently protected by server-side GitHub enforcement. It is not.
- During development, the **human-controlled remote workflow** (`DEVELOPMENT_SECURITY_WORKFLOW_V1.md` "MANUAL GOVERNANCE ENFORCEMENT REQUIRED" + `GITHUB_REMOTE_ACTIVITY_SAFETY.md` human-controlled remote write mode) is the recorded **compensating control**: PR-only `main` by governance, no force-push, human-executed merges, human-controlled remote writes.
- This compensating control is a **development-phase** control only. It is not, by itself, a release-grade control.

### 2. Release requirement (deterministic)

Before Release Candidate / B-023 release authorization, **one** of the following must hold:

1. **Technical enforcement (preferred, default required):** server-side branch protection/rulesets (or equivalent hosting-enforcement mechanism) are enabled and **verified** — covering at minimum: PR-only changes to `main`, required status checks, no force-push, and audit-visible merge history — OR
2. **Approved equivalent control:** an explicit, recorded `ROLE-001` Human Decision in `docs/workforce/registries/decisions.jsonl` that (a) defines the specific equivalent control, (b) records rationale, and (c) is permitted by repository policy. No such decision exists today; recording one is a human action this task neither performs nor fabricates.

Absent (1) or (2), B-023 release authorization is **BLOCKED**. This makes the previously implicit assumption explicit and evaluable: the release gate cannot silently rely on an enforcement that does not exist, and cannot silently risk-accept the gap.

### 3. No repository configuration change by this task

This amendment changes no GitHub settings, enables no rulesets, upgrades no plan, and calls no GitHub configuration APIs. It records the requirement and the honest current state only.

---

## Milestone Security Review Flags

The following findings involve trust boundaries that must be explicitly covered by the next scheduled Security Architecture milestone review:

- `ANOX-MAINARCH-003` — server ↔ DB/RLS trust boundary (preserved from V1.2).
- `ANOX-MAINARCH-007` — server ↔ backup/PITR trust boundary (preserved from V1.2).
- `ANOX-MAINARCH-024` — signing/release custody and incident-response trust boundary: this V1.3 amendment defines the `K_APK_RELEASE` custody boundary (human-only ROLE-018, D4 secrets, isolated signing environment) and the incident/PSIRT artifact boundary for the first time; the next Security Architecture milestone must review these newly defined boundaries.

These flags are recorded in `docs/reports/FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md` and `docs/workforce/registries/findings.jsonl`. Recording a milestone flag is not an immediate security audit; `CLAUDE AUDIT TRIGGERED = NO` for this remediation.

---

## Historical provenance

This V1.3 amendment does not modify the B-025 historical snapshot in `docs/authority/B025/TRACK_B/`. The B-025 snapshot files remain immutable. The `B_FREEZE_REGISTRY.md` and `AUTHORITY_INDEX.md` record the amended current versions.
