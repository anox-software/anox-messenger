# Next Engineering Gate

The next **feature** remains Device Authentication, but only after the B-025 compatibility/docs synchronization PR is complete and main is green.

Why: the existing repo has no Device Auth implementation, while old current docs still describe superseded Ed25519/Open decisions. Implementing immediately risks an agent following stale docs. The compatibility pass is small compared with a feature build and protects the architecture boundary.

Current crypto/local-state foundation should be preserved unless STEP 3 proves a real conflict. Do not refactor it merely to modernize style.
