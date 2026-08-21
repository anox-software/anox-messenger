# Required Uploads / Inputs for a New Chat

## Minimum set

1. `ANOX_MASTER_HANDOFF_B025_2026-08-20.zip` — this package.
2. The **latest** anoX Messenger repository/project folder or ZIP if it is newer than the repository snapshot inside the pack.
3. Any Devin/Claude/Windsurf output produced **after** this package date that has not yet been incorporated into `FORTSCHRITT.md`.

## Strongly recommended when continuing coding

- Access to the actual Git repository or a fresh project export including `.git`, so branch/commit/diff status can be proven.
- Latest CI output if newer than the evidence inside the pack.
- Real Android/GrapheneOS test output when available.

## Do not require

- Old Raw1.1 files separately if this pack is supplied; they are already archived here.
- Historical build caches (`.gradle`, `build`, Rust `target`).
- Production secrets, signing private keys, service-role keys or user data.

## If inputs conflict

Repository source/tests decide what is currently implemented. Frozen B-specs decide what the implementation must become. A stale historical document never overrides either.
