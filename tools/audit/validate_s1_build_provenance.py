#!/usr/bin/env python3
"""S1 umbrella static gate — REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001.

Fail-closed repository-surface checks proving the provenance architecture is
wired end to end:

  * pinned Rust toolchain file exists with an exact channel + required targets
  * no committed/hand-built .so under android/src/main/jniLibs (bypass path
    eliminated and git-ignored)
  * Gradle consumes the authoritative build output, never the committed path;
    packaging keeps the produced bytes byte-identical (keepDebugSymbols);
    a fail-closed verifyNativeArtifacts guard gates every package task;
    the ABI set is pinned to the frozen {arm64-v8a, x86_64}
  * the security policy document states the true provenance chain and no
    longer claims controls that do not exist (e.g. Gradle lockfiles)
  * the S1 gate tools exist (native build driver, APK validator v2, CI
    pipeline gate, secret scan, B-021 matrix validator) and msc_state.jsonl
  * crypto/rust/src/** carries zero behavioral diff vs the S1 base
    (enforced when git metadata is available)

``--check static`` requires no built artifacts and runs in the
supply-chain-policy CI job and in adversarial fixtures.
Stdlib only.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TOOLCHAIN_FILE = "crypto/rust/rust-toolchain.toml"
GRADLE_APP = "android/build.gradle.kts"
COMMITTED_JNILIBS = "android/src/main/jniLibs"
PRODUCED_JNILIBS_TOKEN = "$rootDir/build/native/jniLibs"
POLICY_DOC = "docs/current/REPOSITORY_SECURITY_POLICY.md"
GITIGNORE = ".gitignore"
CI_WORKFLOW = ".github/workflows/ci.yml"
MSC_STATE = "docs/security/remediation/msc_state.jsonl"

REQUIRED_TOOLS = [
    "tools/security/native_build.py",
    "tools/security/validate_apk_contents.py",
    "tools/security/validate_ci_pipeline.py",
    "tools/security/secret_scan.py",
    "tools/audit/validate_b021_verification_matrix.py",
    "tools/audit/validate_s1_build_provenance.py",
]

REQUIRED_RUST_TARGETS = {"aarch64-linux-android", "x86_64-linux-android"}
REQUIRED_ABIS = {"arm64-v8a", "x86_64"}
S1_BASE_SHA = "0f932520393feee6d479cc099f179f5766323125"


def _toolchain_channel(path):
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        m = re.match(r'channel\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    return None


def _toolchain_targets(path):
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        m = re.match(r"targets\s*=\s*\[([^\]]*)\]", line)
        if m:
            return {t.strip().strip('"').strip("'") for t in m.group(1).split(",") if t.strip()}
    return set()


def resolve_git_dir(repo_root):
    """Resolve the repository's git metadata directory (F2), fail closed.

    Accepts a normal ``.git`` directory or a linked-worktree ``.git`` pointer
    file (``gitdir: <path>``, absolute or relative to the repository root).
    Returns (git_dir_path, None) on success or (None, reason) on any failure:
    missing metadata, malformed pointer, unreadable file, pointer target that
    is not a directory, or a target that does not look like git metadata.
    """
    dot_git = Path(repo_root) / ".git"
    if not dot_git.exists():
        return None, ".git metadata missing (non-repository context)"
    if dot_git.is_dir():
        if not (dot_git / "HEAD").exists():
            return None, ".git directory has no HEAD (invalid repository metadata)"
        return dot_git, None
    if not dot_git.is_file():
        return None, ".git is neither a directory nor a file"
    try:
        text = dot_git.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as e:
        return None, f".git pointer file unreadable: {e.__class__.__name__}"
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) != 1 or not lines[0].startswith("gitdir:"):
        return None, ".git pointer file malformed (expected exactly one 'gitdir: <path>' line)"
    target = lines[0][len("gitdir:"):].strip()
    if not target or "\x00" in target:
        return None, ".git pointer file has empty/invalid gitdir target"
    tpath = Path(target)
    if not tpath.is_absolute():
        tpath = (Path(repo_root) / tpath)
    try:
        tpath = tpath.resolve(strict=True)
    except (OSError, RuntimeError):
        return None, f".git pointer target does not exist: {target}"
    if not tpath.is_dir():
        return None, f".git pointer target is not a directory: {target}"
    # A linked worktree gitdir carries HEAD + commondir; a bare/main gitdir carries HEAD.
    if not (tpath / "HEAD").exists():
        return None, f".git pointer target lacks HEAD (not git metadata): {target}"
    if (tpath / "commondir").exists():
        try:
            common = (tpath / (tpath / "commondir").read_text(encoding="utf-8").strip()).resolve(strict=True)
        except (OSError, RuntimeError, UnicodeDecodeError):
            return None, ".git worktree commondir target unresolvable"
        if not common.is_dir() or not (common / "HEAD").exists():
            return None, ".git worktree commondir does not point at git metadata"
    return tpath, None


def check_rust_behavior_unchanged(repo_root, base_sha=S1_BASE_SHA):
    """crypto/rust/src/** must carry zero diff vs the S1 base (scope guard).

    F2: runs in normal repositories AND linked worktrees; every failure to
    establish git context is an error, never a silent skip.
    """
    errors = []
    root = Path(repo_root)
    _, why = resolve_git_dir(root)
    if why:
        errors.append(f"git context unavailable — Rust behavior-scope check cannot run: {why}")
        return errors
    probe = subprocess.run(["git", "cat-file", "-e", f"{base_sha}^{{commit}}"], cwd=root,
                           capture_output=True, text=True)
    if probe.returncode != 0:
        errors.append(f"S1 base commit {base_sha[:12]} not present in repository; scope check cannot run")
        return errors
    proc = subprocess.run(
        ["git", "diff", "--name-only", base_sha, "--", "crypto/rust/src/"],
        cwd=root, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        errors.append("git diff for crypto/rust/src/ failed: " + proc.stderr.strip())
    elif proc.stdout.strip():
        errors.append(
            "crypto/rust/src/** changed vs S1 base (behavior change forbidden): "
            + proc.stdout.strip()
        )
    return errors


def check_static(repo_root, git_scope_check=True):
    """Static S1 gate. ``git_scope_check=False`` is a fixture-only seam for
    tests of the non-git surfaces; the CLI always runs with True (fail-closed)."""
    errors = []
    root = Path(repo_root)

    # 1. toolchain pin -------------------------------------------------------
    tc = root / TOOLCHAIN_FILE
    if not tc.exists():
        errors.append(f"{TOOLCHAIN_FILE} missing — toolchain not pinned")
    else:
        channel = _toolchain_channel(tc)
        if channel is None:
            errors.append(f"{TOOLCHAIN_FILE}: no channel pinned")
        elif not re.fullmatch(r"\d+\.\d+\.\d+", channel):
            errors.append(f"{TOOLCHAIN_FILE}: channel {channel!r} is not an exact version pin")
        missing = REQUIRED_RUST_TARGETS - _toolchain_targets(tc)
        if missing:
            errors.append(f"{TOOLCHAIN_FILE}: missing targets {sorted(missing)}")

    # 2. committed .so bypass eliminated ------------------------------------
    committed = root / COMMITTED_JNILIBS
    if committed.exists():
        stray = [p for p in committed.rglob("*.so")]
        if stray:
            errors.append(
                f"committed .so bypass present: {[str(p.relative_to(root)) for p in stray]}"
            )
    proc = subprocess.run(
        ["git", "ls-files", COMMITTED_JNILIBS], cwd=root,
        capture_output=True, text=True,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        errors.append(
            f"tracked .so files under {COMMITTED_JNILIBS}: {proc.stdout.split()}"
        )
    gi = root / GITIGNORE
    if gi.exists():
        gi_lines = {l.strip() for l in gi.read_text(encoding="utf-8").splitlines()}
        if not any(l.rstrip("/") == COMMITTED_JNILIBS for l in gi_lines):
            errors.append(f"{GITIGNORE} does not cover {COMMITTED_JNILIBS}/")
    else:
        errors.append(f"{GITIGNORE} missing")

    # 3. Gradle consumes authoritative output --------------------------------
    gradle = root / GRADLE_APP
    if not gradle.exists():
        errors.append(f"{GRADLE_APP} missing")
    else:
        g = gradle.read_text(encoding="utf-8")
        if PRODUCED_JNILIBS_TOKEN not in g:
            errors.append(
                f"{GRADLE_APP}: jniLibs does not consume {PRODUCED_JNILIBS_TOKEN}"
            )
        if re.search(r'jniLibs\s*\{[^}]*srcDir\(\s*"src/main/jniLibs"', g, re.S) or \
           'srcDir("src/main/jniLibs")' in g.replace(" ", ""):
            errors.append(f"{GRADLE_APP}: still consumes committed src/main/jniLibs path")
        if "keepDebugSymbols" not in g:
            errors.append(f"{GRADLE_APP}: keepDebugSymbols missing — packaged .so may diverge from produced artifact")
        if "verifyNativeArtifacts" not in g:
            errors.append(f"{GRADLE_APP}: verifyNativeArtifacts guard task missing")
        if "abiFilters" not in g:
            errors.append(f"{GRADLE_APP}: abiFilters missing — ABI set not pinned")
        for abi in REQUIRED_ABIS:
            if abi not in g:
                errors.append(f"{GRADLE_APP}: required ABI {abi} not pinned in abiFilters/guard")
        if not re.search(r"lint\s*\{[^}]*abortOnError\s*=\s*true", g, re.S):
            errors.append(f"{GRADLE_APP}: lint abortOnError=true missing")

    # 4. policy document truthful ---------------------------------------------
    pol = root / POLICY_DOC
    if not pol.exists():
        errors.append(f"{POLICY_DOC} missing")
    else:
        p = pol.read_text(encoding="utf-8")
        if re.search(r"Gradle lockfiles? (are |is )?(retained|committed|present|checked)", p, re.I):
            errors.append(f"{POLICY_DOC}: still claims Gradle lockfiles are retained (they do not exist)")
        for token in ("native_build.py", "native-manifest"):
            if token not in p:
                errors.append(f"{POLICY_DOC}: does not document the S1 provenance chain ({token})")

    # 5. S1 gate tools + state registry ---------------------------------------
    for rel in REQUIRED_TOOLS:
        if not (root / rel).exists():
            errors.append(f"required S1 tool missing: {rel}")
    if not (root / MSC_STATE).exists():
        errors.append(f"{MSC_STATE} missing")
    if not (root / CI_WORKFLOW).exists():
        errors.append(f"{CI_WORKFLOW} missing")

    # 6. no behavioral Rust source change (F2: normal repo + linked worktree; never skipped)
    if git_scope_check:
        errors.extend(check_rust_behavior_unchanged(root))
    return errors


def main():
    ap = argparse.ArgumentParser(description="S1 build-provenance repository gate")
    ap.add_argument("--check", choices=["static"], default="static")
    ap.add_argument("--repo-root", default=str(REPO_ROOT))
    args = ap.parse_args()

    print("S1 BUILD-PROVENANCE STATIC GATE")
    errors = check_static(args.repo_root)
    if errors:
        for e in errors:
            print(f"  FAIL {e}")
        print("RESULT: FAIL")
        return 1
    print("  OK   toolchain pinned / no committed-.so bypass / Gradle consumes produced artifacts / policy truthful / S1 tools present")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
