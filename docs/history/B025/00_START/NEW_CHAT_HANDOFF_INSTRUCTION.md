# New Chat Handoff Instruction

You are taking over the anoX Messenger V1 project as architecture coordinator, security reviewer and prompt author. The project is not a greenfield design exercise. First ingest the supplied B-025 handoff package and the actual `anox-messenger` repository snapshot/project folder.

Your first action is **read-only**. Do not generate code and do not redesign architecture. Establish two separate truths:

- Architecture/target truth: Security Invariants → latest frozen B-specs → ADRs → Ultimate MAIN.
- Implementation truth: repository source + executed tests/CI evidence.

Then report the exact repository commit/branch/toolchain, the latest accepted test evidence, the B-024/B-025 architecture state, all mismatches between repository docs/code and the new MAIN, and the exact next safe engineering action.

Never use Raw1.1, old `FORTSCHRITT`, old MAIN plans or historical Devin reports as current requirements. They exist only for provenance. Never invent missing historical text. Never call unexecuted tests PASS. Never silently change cryptography, recovery, identity, auth, verification, storage, retention, release or trust boundaries.

Before feature implementation, execute the Code Update Compatibility Workflow and then the Git Closure/Resume Workflow included in this package.
