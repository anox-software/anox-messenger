# Git / GitHub State at B-025

- Repository: `anox-admin/ax-messenger` (private per project reports).
- Branch: `main`.
- HEAD / origin-main in uploaded repository: `c076528e26e5e3ed05b4d0aeed794894f1f78b5e`.
- Tag history includes `v1-foundation-baseline` at `7db20fa`.
- TOOLCHAIN-001 PR #1 merged at `9e13c1d`; post-merge governance commit `c076528` is current HEAD.
- Reported CI branch run: `32342258423` PASS for Rust/debug/release compile.
- Reported post-merge main run: `32344459447` PASS for Rust/debug/release compile.
- Connected instrumentation is not run in GitHub CI; historical 35/35 local/emulator evidence remains the accepted test record until re-run.
- Branch protection and GitHub secret scanning were unavailable on the free private plan; B-023 makes technical branch governance a Production gate, not a reason to rewrite current foundation code.

## Important upload artifact

ZIP extraction in this environment changed executable mode bits of `gradlew` and the two checked-in `.so` files; file contents are byte-identical to HEAD. Do not create a “fix” commit solely from those ZIP permission artifacts without checking a real Git clone.
