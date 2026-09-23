# S1 — GitHub Action Pin Provenance Classification (retest finding F8)

Task: `REMEDIATION-S1-CANONICAL-INTEGRATION-001`
Source: `INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001` finding F-8 (INFORMATIONAL)

## Rule

Every external `uses:` in `.github/workflows/*.yml` is pinned to a full
40-character commit SHA (enforced by `tools/security/b017_lite_policy_validator.py`).
**Immutable SHA pins are the control and are never replaced by mutable tags
(`@v4`, `@main`, `@stable`) — not to silence IDE/linters, not for convenience.**

Two properties are tracked separately and must not be conflated:

| Property | Meaning |
|---|---|
| `PIN_IMMUTABLE` | The reference is a full commit SHA that resolves in the intended official repository. |
| `RELEASE_LINEAGE_VERIFIED` | An official release tag of that repository dereferences to exactly the pinned SHA. |

## Classification (verified 2026-09-15 against the upstream repositories)

| Action | Pinned SHA | Official repo resolves | Release lineage | Classification |
|---|---|---|---|---|
| `actions/checkout` | `11d5960a326750d5838078e36cf38b85af677262` | YES | `v4`, `v4.4.0` | `PIN_IMMUTABLE` + `RELEASE_LINEAGE_VERIFIED` |
| `actions/download-artifact` | `d3f86a106a0bac45b974a628896c90dbdf5c8093` | YES | `v4`, `v4.3.0` | `PIN_IMMUTABLE` + `RELEASE_LINEAGE_VERIFIED` |
| `actions/setup-java` | `cf277c60eb25467037889841efdb72551f06f6c3` | YES | `v4`, `v4.9.1` | `PIN_IMMUTABLE` + `RELEASE_LINEAGE_VERIFIED` |
| `actions/upload-artifact` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | YES | `v4`, `v4.6.2` | `PIN_IMMUTABLE` + `RELEASE_LINEAGE_VERIFIED` |
| `android-actions/setup-android` | `40fd30fb8d7440372e1316f5d1809ec01dcd3699` | YES | `v4`, `v4.0.1` | `PIN_IMMUTABLE` + `RELEASE_LINEAGE_VERIFIED` |
| `gradle/actions/wrapper-validation` | `9c971963bec38e04b3d30dcc455b5382be2fdbfb` | YES | annotated tag `v6.3.0` → exact SHA | `PIN_IMMUTABLE` + `RELEASE_LINEAGE_VERIFIED` |
| `nttld/setup-ndk` | `afb4c9964b521afb97c864b7d40b11e6911bd410` | YES | annotated tag `v1.5.0` → exact SHA | `PIN_IMMUTABLE` + `RELEASE_LINEAGE_VERIFIED` |
| `dtolnay/rust-toolchain` | `4360b52568e2003a75bf9bc1d59f33a8e3fc893c` | YES | **none** — no tag; `stable` branch is force-moved upstream and reports `diverged` from this commit | `PIN_IMMUTABLE` + **`PIN_PROVENANCE_UNVERIFIED`** |

## Disposition of `dtolnay/rust-toolchain`

- The pin is immutable and resolves to a real commit of the official repository
  (HTTP 200). That is the security property the pin provides, and it is intact.
- Independent release/tag provenance **was not established** and is not claimed.
  This is a truthful limitation of that upstream's release model (tag-less,
  force-moved branches), not a repository defect.
- No stronger provenance is fabricated. The comment `# stable` beside the pin
  is descriptive of the upstream branch family only, not a verified tag.
- Any future re-pin of this action must record the new SHA, the date, and the
  upstream branch tip observed at that time in this document.

## IDE / linter diagnostics

"Unable to resolve action …" diagnostics emitted by editors that cannot resolve
SHA refs offline are **not findings** and must not be "fixed" by reverting to
mutable refs (`REPOSITORY_SECURITY_POLICY.md`, B-017-Lite).
