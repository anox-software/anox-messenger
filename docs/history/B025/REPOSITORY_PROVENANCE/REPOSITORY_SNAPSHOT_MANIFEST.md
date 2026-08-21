# Repository Snapshot Manifest

**Snapshot date:** 2026-08-20  
**Uploaded source:** `anoX Messanger(1).zip`  
**Canonical checked-in snapshot:** Git `HEAD` exported with `git archive`  
**Branch:** `main`  
**HEAD:** `c076528e26e5e3ed05b4d0aeed794894f1f78b5e` (`c076528` short)  
**Remote:** `https://github.com/anox-admin/ax-messenger.git`

## Why the pack uses `git archive`

The uploaded ZIP loses executable mode bits on `gradlew` and the two checked-in `.so` files when extracted in this environment. Content hashes match `HEAD`; the observed worktree differences are mode-only, not source-content changes. Therefore `CURRENT_HEAD_SOURCE/` is exported directly from Git `HEAD` so it represents the clean committed source rather than ZIP extraction metadata.

## Full history

`ax-messenger-full-history.bundle` contains the available Git history and refs so a future reviewer can inspect where checked-in code came from without relying only on prose reports.

## Current git log

```text
c076528 (HEAD -> main, origin/main) Post-TOOLCHAIN-001: update governance docs for main merge
9e13c1d Merge pull request #1 from anox-admin/toolchain-001/android-toolchain-alignment
f1a50fa (origin/toolchain-001/android-toolchain-alignment, toolchain-001/android-toolchain-alignment) TOOLCHAIN-001: add governance and alignment documentation
ee00fd4 TOOLCHAIN-001: migrate kotlinOptions to compilerOptions DSL
8bea49e TOOLCHAIN-001: align Android toolchain to KGP 2.4.10
9c9660a GIT-001C: document toolchain incompatibility and stop
1387680 GIT-001 final: update governance files and baseline report
b894058 Fix Compose compiler configuration for Kotlin 1.9.20 CI build
f08f16e Fix missing Kotlin Compose plugin version for CI
42521af Add minimal GitHub Actions CI workflow
36447a0 GIT-001 continuation: configure origin and document auth pending state
139674b Add GIT-001 secure Git/GitHub baseline report
7db20fa (tag: v1-foundation-baseline) anoX V1 baseline: crypto and local state foundation verified
```

## Uploaded-extraction status evidence

```text
# branch.oid c076528e26e5e3ed05b4d0aeed794894f1f78b5e
# branch.head main
# branch.upstream origin/main
# branch.ab +0 -0
1 .M N... 100755 100755 100644 500b7ac3af1992dae76897e308e4491b770bd246 500b7ac3af1992dae76897e308e4491b770bd246 android/src/main/jniLibs/arm64-v8a/libanox_crypto.so
1 .M N... 100755 100755 100644 1b1f456412ed1a51a904f90dbb2bf31dd93604f2 1b1f456412ed1a51a904f90dbb2bf31dd93604f2 android/src/main/jniLibs/x86_64/libanox_crypto.so
1 .M N... 100755 100755 100644 c17658edcf2ae3d669be93916a02268a1d42e253 c17658edcf2ae3d669be93916a02268a1d42e253 gradlew
```

The three `.M` entries are ZIP permission-mode artifacts. Their SHA-256 content matches `HEAD`.
