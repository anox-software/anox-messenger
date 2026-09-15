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


def check_static(repo_root):
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

    # 6. no behavioral Rust source change --------------------------------------
    if (root / ".git").is_dir():
        proc = subprocess.run(
            ["git", "diff", "--name-only", S1_BASE_SHA, "--", "crypto/rust/src/"],
            cwd=root, capture_output=True, text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            errors.append(
                "crypto/rust/src/** changed vs S1 base (behavior change forbidden): "
                + proc.stdout.strip()
            )
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
