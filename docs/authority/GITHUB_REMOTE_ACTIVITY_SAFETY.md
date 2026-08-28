# anoX V1 GitHub Remote Activity Safety Governance

**Authority:** Additive development-governance authority under B-026.  
**Status:** CURRENT  
**Date:** 2026-08-28

---

## Scope

This document governs all AI-assisted and human-assisted Git/GitHub remote activity for anoX Messenger V1. It applies to every current and future agent: Devin, Claude, ChatGPT-controlled workflows, Codex-style coding agents, future anoX workforce agents, and any automation operating on behalf of an AI employee.

The canonical authority precedence is `docs/authority/AUTHORITY_INDEX.md`. This document is additive under that index. In case of any apparent conflict, `AUTHORITY_INDEX.md` is the winner.

---

## Hard invariant

```text
NO RAPID REPETITIVE REMOTE AUTOMATION
```

AI development must behave like controlled professional software engineering, not a high-frequency automated GitHub activity loop.

---

## Local-first development

```text
assigned task
→ local implementation
→ local testing
→ local diff review
→ coherent development checkpoint
→ logical commit
→ additional local work if needed
→ final relevant local validation
→ remote checkpoint only when justified
```

GitHub must not be used as an AI progress log.

---

## Commit policy

Commits must represent meaningful, reviewable development units. AI agents MUST NOT create repetitive tiny commits merely to record:

- individual file edits;
- individual text changes;
- every failed test;
- every intermediate reasoning step;
- every continuity note;
- conversational progress.

Closely related work should be grouped into a coherent commit. A local checkpoint commit does not automatically require a remote push.

---

## Push policy

`PUSH_AFTER_EVERY_COMMIT = PROHIBITED`

Remote pushes are synchronization checkpoints. Before an AI-originated push can be recommended, the work unit must have:

- coherent scope;
- local validation;
- reviewed diff;
- known target branch;
- no unexplained working-tree state.

Rapid sequences of push-after-edit or push-after-test are prohibited.

---

## Prohibited automation loop

The following autonomous pattern is prohibited:

```text
edit → commit → push → GitHub query → edit → commit → push → GitHub query → repeat
```

The same applies to rapid loops involving branches, PRs, issues, comments, labels, review requests, merge attempts, or GitHub API requests.

---

## GitHub API discipline

AI agents must not use GitHub as a tight polling target. Prohibited examples include frequent automated loops checking PR state, CI state, branch state, review state, issue state, or mergeability.

Queries must be:

- purposeful;
- bounded;
- triggered by an actual workflow need;
- reasonably spaced or event-driven.

No high-frequency polling architecture may be introduced.

---

## Remote failure policy

Any remote response indicating possible authorization, abuse, throttling, or account restriction must stop automated remote activity. Examples: HTTP 401, 403, 429, authentication/permission failure, rate-limit response, abuse-detection response, account restriction, or suspension.

Required behavior:

```text
REMOTE ERROR
→ STOP AUTOMATED REMOTE ACTIVITY
→ record blocker
→ report exact error
→ human review / controlled recovery
```

No rapid retry loop. No credential cycling. No alternative account or remote used automatically.

---

## Account-enforcement rule

AI agents must not attempt to bypass platform restrictions. If an account or credential is rejected or suspended:

- stop;
- report;
- require human-controlled account/repository resolution.

Account migration is a separate explicit human-controlled workflow.

---

## Branch policy

Normal expectation: `ONE COHERENT WORKSTREAM → ONE CONTROLLED BRANCH`.

Do not automatically create:

- branch per tiny task;
- disposable branches for every repair;
- repeated replacement branches;
- branch-create/delete loops.

Parallel writers require explicitly separate scopes/worktrees.

---

## PR policy

Normal expectation: `ONE COHERENT BRANCH / WORKSTREAM → ONE PR`.

Agents must not repeatedly:

- open replacement PRs;
- close/recreate the same PR;
- produce status comments for every minor event;
- spam review requests;
- repeatedly modify labels/statuses without material workflow changes.

---

## Parallel AI writers

Two AI writers must not independently push competing changes to the same remote branch. A writing task must be governed by:

- TASK_ID;
- owner;
- branch/worktree;
- explicit scope;
- controlled synchronization checkpoint.

Until B-027 formally implements task leases, parallel remote-writing AI work should be avoided.

---

## Initial remote-write safety mode

After migration to the new GitHub environment, anoX initially operates in:

```text
HUMAN-CONTROLLED REMOTE WRITE MODE
```

### AI may

- modify local assigned source;
- run local tests;
- create coherent local commits when authorized;
- prepare/recommend a push.

### AI may NOT initially

- autonomously push;
- create remote PRs;
- mutate GitHub through loops;
- manage remote credentials.

A human performs remote synchronization until remote-write governance has been proven stable.

---

## Future AI remote-write activation

Autonomous or controlled AI remote write may only be introduced after explicit governance authorization. Future prerequisites must eventually include:

- least-privilege credentials;
- branch protection;
- defined agent identity;
- stop-on-auth/error behavior;
- no rapid automation loops;
- controlled checkpoint policy;
- auditable activity;
- B-027 access/workforce policy when available.

No agent gains remote write merely because it can technically authenticate.

---

## Normal activity principle

This policy is not intended to disguise AI activity or imitate humans. It is intended to enforce legitimate, disciplined development behavior:

- meaningful commits;
- sensible branches;
- coherent PRs;
- purposeful API usage;
- no artificial activity generation;
- no spam;
- no platform-enforcement circumvention.

GitHub activity should exist only because a genuine engineering action requires it.

---

## Summary for bootstrap and handoff

- Local-first development is mandatory.
- Rapid repetitive commits/pushes are prohibited.
- GitHub errors stop automation.
- Remote-write authority must be explicit.
- Absence of remote-write permission means no push.

`REMOTE WRITE AUTHORITY IS EXPLICIT, NEVER ASSUMED.`
