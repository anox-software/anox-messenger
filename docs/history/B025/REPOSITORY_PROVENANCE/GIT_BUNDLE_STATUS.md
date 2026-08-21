# Git Bundle Status — B-025 Repository Provenance

**Historical only — not current architecture authority.**

## Reference bundle

- **REFERENCE_BUNDLE_EXISTS:** YES
- **REFERENCE_MASTER_PATH:** `04_REPOSITORY/ax-messenger-full-history.bundle`
- **CURRENT_HANDOFF_INCLUSION:** NOT YET AUTHORIZED
- **REASON:** requires independent historical secret/content review before duplication
- **LIVE_CANONICAL_GIT_HISTORY:** https://github.com/anox-admin/ax-messenger.git

## Policy

The original B-025 master package contained a full Git history bundle. That bundle may contain the complete Git object graph and is therefore treated as a sensitive provenance artifact. It is not automatically replicated in the anox repository handoff system until a dedicated security review authorizes it.

Current and future development use the live GitHub repository as the authoritative Git provenance. `CURRENT_GIT_STATE.md` and `GIT_SNAPSHOT.txt` in each handoff record the exact HEAD, tag, branch, and recent log at the time of handoff.
