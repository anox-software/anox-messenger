#!/usr/bin/env python3
"""Authoritative native build driver for the anox_crypto Android library.

REMEDIATION_SESSION_S1 / MSC-UNIT-001: the committed ``.so`` bypass is
eliminated.  The only trusted way to obtain ``libanox_crypto.so`` for Android
packaging is this script, which

  * asserts the repository-pinned Rust toolchain (crypto/rust/rust-toolchain.toml)
  * asserts the pinned Android NDK and cargo-ndk versions
  * builds every required ABI from reviewed source with ``--locked``
  * applies deterministic path remapping so clean rebuilds are comparable
  * emits a machine-readable provenance manifest binding source revision,
    toolchain, ABI, artifact path and SHA-256 for each produced library
  * verifies JNI symbol parity between the Kotlin ``external fun`` surface,
    the Rust ``#[no_mangle]`` exports and the produced binary

Uses only the Python 3 standard library.  Never prints secrets.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CRATE_DIR = "crypto/rust"
TOOLCHAIN_FILE = "crypto/rust/rust-toolchain.toml"
CARGO_LOCK = "crypto/rust/Cargo.lock"
KOTLIN_NATIVE = "crypto/android/src/main/java/com/anox/crypto/CryptoNative.kt"
RUST_LIB = "crypto/rust/src/lib.rs"

REQUIRED_NDK_REVISION = "26.2.11394342"  # Android NDK r26c
REQUIRED_CARGO_NDK = "4.1.2"
LIB_NAME = "libanox_crypto.so"
JNI_PREFIX = "Java_com_anox_crypto_CryptoNative_"

# Required Android ABI -> Rust target triple.  The authoritative pipeline must
# produce exactly this set: no missing ABI, no extra unreviewed ABI.
REQUIRED_ABIS = {
    "arm64-v8a": "aarch64-linux-android",
    "x86_64": "x86_64-linux-android",
}

DEFAULT_OUT_DIR = "build/native/jniLibs"
DEFAULT_MANIFEST = "build/native/native-manifest.json"
MANIFEST_SCHEMA = "anox-native-manifest-v1"


# --------------------------------------------------------------------------
# small helpers

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run(cmd, cwd=None, env=None, capture=True):
    return subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=capture, text=True, timeout=3600
    )


def parse_toolchain_toml(path):
    """Parse the pinned toolchain file with a minimal TOML-subset parser.

    We only need ``channel`` and ``targets`` from ``[toolchain]``; keeping a
    small parser avoids a dependency on Python >= 3.11 ``tomllib``.
    """
    channel = None
    targets = []
    if not path.exists():
        return channel, targets, ["rust-toolchain.toml missing"]
    errors = []
    in_toolchain = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            in_toolchain = line.strip() == "[toolchain]"
            continue
        if not in_toolchain or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key == "channel":
            m = re.fullmatch(r'"([^"]+)"', value)
            if not m:
                errors.append(f"unparseable channel value: {value!r}")
            else:
                channel = m.group(1)
        elif key == "targets":
            m = re.fullmatch(r"\[([^\]]*)\]", value)
            if not m:
                errors.append(f"unparseable targets value: {value!r}")
            else:
                targets = [
                    t.strip().strip('"').strip("'")
                    for t in m.group(1).split(",")
                    if t.strip()
                ]
    return channel, targets, errors


# --------------------------------------------------------------------------
# toolchain assertions

def check_toolchain(repo_root, ndk_path=None, errors=None):
    """Fail-closed toolchain assertion for the authoritative build path."""
    errors = errors if errors is not None else []
    root = Path(repo_root)
    crate = root / CRATE_DIR

    channel, targets, terr = parse_toolchain_toml(root / TOOLCHAIN_FILE)
    errors.extend(terr)
    if channel is None:
        errors.append("rust-toolchain.toml declares no channel")
    elif not re.fullmatch(r"\d+\.\d+\.\d+", channel):
        errors.append(
            f"rust toolchain channel is not an exact version pin: {channel!r}"
        )
    missing_targets = sorted(set(REQUIRED_ABIS.values()) - set(targets))
    if missing_targets:
        errors.append(
            "rust-toolchain.toml missing required targets: "
            + ", ".join(missing_targets)
        )

    if channel:
        proc = _run(["rustup", "show", "active-toolchain"], cwd=crate)
        if proc.returncode != 0:
            errors.append("rustup show active-toolchain failed: " + proc.stderr.strip())
        else:
            active = proc.stdout.strip().splitlines()[0].split()[0]
            # active looks like "1.97.1-aarch64-apple-darwin" or an override name
            if not active.startswith(channel + "-") and active != channel:
                errors.append(
                    f"active rust toolchain {active!r} does not match pinned channel {channel!r}"
                )
        proc = _run(["rustc", "--version"], cwd=crate)
        if proc.returncode != 0:
            errors.append("rustc --version failed")
        else:
            m = re.search(r"rustc (\d+\.\d+\.\d+)", proc.stdout)
            if not m or m.group(1) != channel:
                errors.append(
                    f"rustc version mismatch: {proc.stdout.strip()!r} != pinned {channel}"
                )
        proc = _run(["rustup", "target", "list", "--installed"], cwd=crate)
        if proc.returncode == 0:
            installed = set(proc.stdout.split())
            for t in sorted(REQUIRED_ABIS.values()):
                if t not in installed:
                    errors.append(f"required rust target not installed: {t}")
        else:
            errors.append("rustup target list --installed failed")

    proc = _run(["cargo", "ndk", "--version"], cwd=crate)
    if proc.returncode != 0:
        errors.append("cargo-ndk not available: " + proc.stderr.strip())
    else:
        m = re.search(r"cargo-ndk (\d+\.\d+\.\d+)", proc.stdout)
        if not m or m.group(1) != REQUIRED_CARGO_NDK:
            errors.append(
                f"cargo-ndk version mismatch: {proc.stdout.strip()!r} != pinned {REQUIRED_CARGO_NDK}"
            )

    ndk = resolve_ndk_path(ndk_path)
    if ndk is None:
        errors.append("Android NDK not found (set ANDROID_NDK_HOME or pass --ndk-path)")
    else:
        props = ndk / "source.properties"
        if not props.exists():
            errors.append(f"NDK source.properties missing at {props}")
        else:
            rev = None
            for line in props.read_text(encoding="utf-8").splitlines():
                if line.startswith("Pkg.Revision"):
                    rev = line.split("=", 1)[1].strip()
            if rev != REQUIRED_NDK_REVISION:
                errors.append(
                    f"NDK revision {rev!r} != pinned {REQUIRED_NDK_REVISION}"
                )
    return errors


def resolve_ndk_path(ndk_path=None):
    """Locate the NDK. Order: explicit arg, env vars, SDK-managed dirs."""
    candidates = []
    if ndk_path:
        candidates.append(Path(ndk_path))
    for env in ("ANDROID_NDK_HOME", "ANDROID_NDK_ROOT", "ANDROID_NDK", "NDK_HOME"):
        if os.environ.get(env):
            candidates.append(Path(os.environ[env]))
    for sdk_env in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        sdk = os.environ.get(sdk_env)
        if sdk:
            sdk = Path(sdk)
            candidates.append(sdk / "ndk" / REQUIRED_NDK_REVISION)
            candidates.append(sdk / "ndk-bundle")
            ndk_dir = sdk / "ndk"
            if ndk_dir.is_dir():
                candidates.extend(sorted(ndk_dir.iterdir()))
            candidates.extend(sorted(sdk.glob("android-ndk-*")))
    home_sdk = Path.home() / "Library" / "Android" / "sdk"
    if home_sdk.is_dir():
        candidates.append(home_sdk / "ndk" / REQUIRED_NDK_REVISION)
        ndk_dir = home_sdk / "ndk"
        if ndk_dir.is_dir():
            candidates.extend(sorted(ndk_dir.iterdir()))
        candidates.extend(sorted(home_sdk.glob("android-ndk-*")))
    for c in candidates:
        if c and (c / "source.properties").exists():
            return c
    return candidates[0] if candidates else None


def find_llvm_nm(ndk):
    """Locate llvm-nm inside the NDK for dynamic symbol inspection."""
    prebuilt = Path(ndk) / "toolchains" / "llvm" / "prebuilt"
    if not prebuilt.is_dir():
        return None
    for host_dir in sorted(prebuilt.iterdir()):
        for name in ("llvm-nm", "llvm-nm.exe"):
            cand = host_dir / "bin" / name
            if cand.exists():
                return cand
    return None


# --------------------------------------------------------------------------
# JNI surface derivation (source of truth = reviewed source files)

def _jni_escape(name):
    out = []
    for ch in name:
        if ch == "_":
            out.append("_1")
        elif ch == ";":
            out.append("_2")
        elif ch == "[":
            out.append("_3")
        elif ord(ch) > 127:
            out.append("_0%04x" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def kotlin_external_fns(repo_root):
    path = Path(repo_root) / KOTLIN_NATIVE
    fns = set()
    if not path.exists():
        return fns
    for m in re.finditer(
        r"external\s+fun\s+([A-Za-z0-9_]+)\s*\(", path.read_text(encoding="utf-8")
    ):
        fns.add(m.group(1))
    return fns


def rust_jni_fns(repo_root):
    path = Path(repo_root) / RUST_LIB
    fns = set()
    if not path.exists():
        return fns
    for m in re.finditer(
        r"fn\s+(" + re.escape(JNI_PREFIX) + r"[A-Za-z0-9_]+)\s*[(<]",
        path.read_text(encoding="utf-8"),
    ):
        fns.add(m.group(1))
    return fns


def expected_jni_exports(repo_root, errors=None):
    """The expected exported JNI symbol set, derived bidirectionally.

    Kotlin ``external fun`` names and Rust ``Java_...`` symbols must agree
    exactly; any drift is an error, not a warning.
    """
    errors = errors if errors is not None else []
    kotlin = kotlin_external_fns(repo_root)
    rust = rust_jni_fns(repo_root)
    expected = {JNI_PREFIX + _jni_escape(k) for k in kotlin}
    missing_in_rust = expected - rust
    missing_in_kotlin = rust - expected
    if missing_in_rust:
        errors.append("Kotlin external fun(s) with no Rust export: " + ", ".join(sorted(missing_in_rust)))
    if missing_in_kotlin:
        errors.append("Rust JNI export(s) with no Kotlin external fun: " + ", ".join(sorted(missing_in_kotlin)))
    if not expected:
        errors.append("no JNI exports derivable from source")
    return expected


def dynamic_symbols(so_path, llvm_nm=None):
    """Return the set of exported dynamic symbols of an ELF .so."""
    tool = llvm_nm or shutil.which("llvm-nm") or shutil.which("nm")
    if tool is None:
        return None
    proc = _run([str(tool), "-D", "--defined-only", str(so_path)])
    if proc.returncode != 0:
        proc = _run([str(tool), "-D", str(so_path)])
    if proc.returncode != 0:
        return None
    syms = set()
    for line in proc.stdout.splitlines():
        parts = line.split()
        if parts:
            sym = parts[-1].strip()
            if sym:
                syms.add(sym)
    return syms


def check_symbol_parity(so_path, expected, errors, llvm_nm=None):
    syms = dynamic_symbols(so_path, llvm_nm=llvm_nm)
    if syms is None:
        errors.append(f"cannot read dynamic symbols of {so_path} (need llvm-nm)")
        return None
    exported = {s for s in syms if s.startswith(JNI_PREFIX)}
    missing = expected - exported
    extra = exported - expected
    if missing:
        errors.append(f"{so_path}: missing expected JNI exports: " + ", ".join(sorted(missing)))
    if extra:
        errors.append(f"{so_path}: unexpected JNI exports (stale/foreign surface): " + ", ".join(sorted(extra)))
    return exported


# --------------------------------------------------------------------------
# build + manifest

def _build_env(repo_root, ndk):
    env = os.environ.copy()
    repo = str(Path(repo_root).resolve())
    cargo_home = os.environ.get("CARGO_HOME") or str(Path.home() / ".cargo")
    remaps = [
        f"--remap-path-prefix={repo}=<anox-src>",
        f"--remap-path-prefix={cargo_home}=<cargo-home>",
    ]
    prior = env.get("RUSTFLAGS", "").strip()
    env["RUSTFLAGS"] = (prior + " " + " ".join(remaps)).strip()
    env["ANDROID_NDK_HOME"] = str(ndk)
    env["ANDROID_NDK_ROOT"] = str(ndk)
    return env, remaps


def cargo_ndk_build(repo_root, out_dir, ndk, target_dir=None, extra_env=None):
    """Run the authoritative cargo-ndk build for all required ABIs."""
    crate = Path(repo_root) / CRATE_DIR
    env, _ = _build_env(repo_root, ndk)
    if target_dir:
        env["CARGO_TARGET_DIR"] = str(target_dir)
    if extra_env:
        env.update(extra_env)
    cmd = ["cargo", "ndk"]
    for abi in REQUIRED_ABIS:
        cmd += ["-t", abi]
    cmd += ["-o", str(out_dir), "build", "--release", "--locked"]
    proc = _run(cmd, cwd=crate, env=env)
    return proc


def _git_head(repo_root):
    proc = _run(["git", "rev-parse", "HEAD"], cwd=repo_root)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def git_working_tree_state(repo_root):
    """Return ("clean", []) or ("dirty", [paths]) or (None, [reason]) (F7).

    Any tracked modification, staged change or untracked non-ignored file makes
    the tree dirty: an unqualified repo SHA must never describe a tree that
    differs from the commit it names. Fails closed when git is unavailable.
    """
    proc = _run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo_root)
    if proc.returncode != 0:
        return None, ["git status failed: " + (proc.stderr or "").strip()]
    paths = []
    for line in proc.stdout.splitlines():
        if line.strip():
            paths.append(line[3:].strip() if len(line) > 3 else line.strip())
    return ("clean", []) if not paths else ("dirty", paths)


def require_clean_tree(repo_root, errors):
    state, detail = git_working_tree_state(repo_root)
    if state is None:
        errors.append("cannot determine working-tree state: " + "; ".join(detail))
    elif state != "clean":
        shown = ", ".join(detail[:8]) + (" …" if len(detail) > 8 else "")
        errors.append(
            f"working tree is dirty ({len(detail)} path(s): {shown}); refusing to bind a "
            "clean repo SHA to artifacts built from a modified tree"
        )
    return state


def _rustc_version_line(repo_root):
    proc = _run(["rustc", "--version"], cwd=Path(repo_root) / CRATE_DIR)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def write_manifest(repo_root, out_dir, manifest_path, ndk, build_id=None,
                   reproducible_confirmed=False, reproducibility=None,
                   require_clean=True):
    """Emit the provenance manifest.

    F7: ``source.working_tree`` is recorded and (by default) a dirty tree is an
    error — the manifest never claims an unqualified clean SHA for a modified
    tree.  F5: ``build.reproducible_build_confirmed`` is a boolean that is only
    True when set by ``rebuild-compare`` after a successful three-way hash
    comparison; ``build.reproducibility`` carries the attestation detail.
    """
    root = Path(repo_root)
    out_dir = Path(out_dir)
    errors = []
    tree_state = require_clean_tree(root, errors) if require_clean else git_working_tree_state(root)[0]
    expected = expected_jni_exports(root, errors)
    llvm_nm = find_llvm_nm(ndk) if ndk else None

    artifacts = []
    for abi in sorted(REQUIRED_ABIS):
        so = out_dir / abi / LIB_NAME
        if not so.exists():
            errors.append(f"missing produced artifact: {so}")
            continue
        exports = check_symbol_parity(so, expected, errors, llvm_nm=llvm_nm) or set()
        artifacts.append({
            "abi": abi,
            "rust_target": REQUIRED_ABIS[abi],
            "file": f"{abi}/{LIB_NAME}",
            "sha256": sha256_file(so),
            "size": so.stat().st_size,
            "jni_export_count": len(exports),
            "jni_exports_sha256": sha256_text("\n".join(sorted(exports))),
        })

    head = _git_head(root) or "UNKNOWN"
    channel, _, _ = parse_toolchain_toml(root / TOOLCHAIN_FILE)
    cargo_ndk_v = REQUIRED_CARGO_NDK
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "source": {
            "repo_sha": head,
            "crate": CRATE_DIR,
            "crate_manifest": f"{CRATE_DIR}/Cargo.toml",
            "cargo_lock_sha256": sha256_file(root / CARGO_LOCK) if (root / CARGO_LOCK).exists() else None,
            "rust_toolchain_file": TOOLCHAIN_FILE,
            "working_tree": tree_state or "unknown",
        },
        "toolchain": {
            "channel": channel,
            "rustc": _rustc_version_line(root),
            "cargo_ndk": cargo_ndk_v,
            "ndk_revision": REQUIRED_NDK_REVISION,
            "host": os.uname().machine if hasattr(os, "uname") else "unknown",
        },
        "build": {
            "build_id": build_id or os.environ.get("GITHUB_RUN_ID") or "local",
            "profile": "release",
            "locked": True,
            "path_remapped": True,
            "reproducible_build_confirmed": bool(reproducible_confirmed),
            "reproducibility": reproducibility,
        },
        "abis": sorted(REQUIRED_ABIS.keys()),
        "artifacts": artifacts,
    }
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest, errors


def verify_manifest(repo_root, manifest_path, produced_dir, expected_source_sha=None, errors=None,
                    require_clean_live_tree=True):
    """Verify produced artifacts against the manifest — fail closed.

    Checks: schema, ABI set equality, per-artifact path/hash/size parity,
    source revision binding, JNI surface fingerprint, clean-tree attestation
    (F7) and the reproducibility attestation (F5).
    """
    errors = errors if errors is not None else []
    root = Path(repo_root)
    manifest_path = Path(manifest_path)
    produced_dir = Path(produced_dir)

    if not manifest_path.exists():
        errors.append(f"manifest missing: {manifest_path}")
        return errors
    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"manifest is not valid JSON: {e}")
        return errors

    if m.get("schema_version") != MANIFEST_SCHEMA:
        errors.append(f"manifest schema_version != {MANIFEST_SCHEMA}")

    src = m.get("source") or {}
    want_sha = expected_source_sha or _git_head(root)
    if not re.fullmatch(r"[0-9a-f]{40}", str(src.get("repo_sha") or "")):
        errors.append("manifest source.repo_sha is not a 40-hex SHA")
    elif want_sha and src.get("repo_sha") != want_sha:
        errors.append(
            f"manifest source.repo_sha {src.get('repo_sha')} != expected {want_sha}"
        )
    lock = root / CARGO_LOCK
    if lock.exists() and src.get("cargo_lock_sha256") != sha256_file(lock):
        errors.append("manifest cargo_lock_sha256 does not match Cargo.lock")
    # F7: manifest must attest a clean tree, and the live tree must still be clean
    if src.get("working_tree") != "clean":
        errors.append(
            f"manifest source.working_tree={src.get('working_tree')!r} — provenance from a "
            "non-clean tree is not accepted"
        )
    if require_clean_live_tree:
        require_clean_tree(root, errors)

    # F5: reproducibility attestation is mandatory and must be consistent
    build = m.get("build") or {}
    if build.get("reproducible_build_confirmed") is not True:
        errors.append(
            "manifest build.reproducible_build_confirmed is not True — run "
            "`native_build.py rebuild-compare` (two clean builds) before verify/packaging"
        )
    else:
        rep = build.get("reproducibility") or {}
        att = rep.get("per_abi_sha256") or {}
        want = {a.get("abi"): a.get("sha256") for a in m.get("artifacts") or []}
        if rep.get("builds") != 2 or rep.get("method") != "two-clean-builds-three-way-compare":
            errors.append("manifest build.reproducibility attestation malformed")
        if att != want:
            errors.append("manifest build.reproducibility.per_abi_sha256 does not equal artifact hashes")

    tc = m.get("toolchain") or {}
    channel, _, _ = parse_toolchain_toml(root / TOOLCHAIN_FILE)
    if channel and tc.get("channel") != channel:
        errors.append(f"manifest toolchain.channel {tc.get('channel')!r} != pinned {channel!r}")
    if tc.get("ndk_revision") != REQUIRED_NDK_REVISION:
        errors.append(f"manifest ndk_revision {tc.get('ndk_revision')!r} != pinned {REQUIRED_NDK_REVISION}")

    if sorted(m.get("abis") or []) != sorted(REQUIRED_ABIS.keys()):
        errors.append("manifest ABI set does not equal required ABI set")

    expected = expected_jni_exports(root, errors)
    expected_fp = sha256_text("\n".join(sorted(expected)))

    seen_abis = set()
    for art in m.get("artifacts") or []:
        abi = art.get("abi")
        seen_abis.add(abi)
        rel = art.get("file") or ""
        if not rel or rel.startswith("/") or ".." in rel.split("/"):
            errors.append(f"manifest artifact has invalid file path: {rel!r}")
            continue
        fpath = produced_dir / rel
        if not fpath.exists():
            errors.append(f"manifest artifact missing on disk: {rel}")
            continue
        actual = sha256_file(fpath)
        if art.get("sha256") != actual:
            errors.append(f"{rel}: sha256 mismatch (manifest {art.get('sha256')} != produced {actual})")
        if art.get("size") != fpath.stat().st_size:
            errors.append(f"{rel}: size mismatch vs manifest")
        if abi not in REQUIRED_ABIS:
            errors.append(f"manifest artifact has unexpected ABI: {abi!r}")
        elif art.get("rust_target") != REQUIRED_ABIS[abi]:
            errors.append(f"{rel}: rust_target {art.get('rust_target')!r} != {REQUIRED_ABIS[abi]}")
        if art.get("jni_exports_sha256") != expected_fp:
            errors.append(f"{rel}: JNI export fingerprint differs from source-derived expected surface")
    if seen_abis != set(REQUIRED_ABIS.keys()):
        errors.append("manifest artifacts do not cover exactly the required ABI set")

    # no stray .so beyond the manifest
    for so in produced_dir.rglob("*.so"):
        rel = str(so.relative_to(produced_dir))
        if rel not in {a.get("file") for a in m.get("artifacts") or []}:
            errors.append(f"produced dir contains artifact not in manifest: {rel}")
    return errors


def compare_manifest_hashes(m1, m2):
    """Return list of per-ABI hash differences between two manifests."""
    diffs = []
    a1 = {a.get("abi"): a.get("sha256") for a in m1.get("artifacts") or []}
    a2 = {a.get("abi"): a.get("sha256") for a in m2.get("artifacts") or []}
    for abi in sorted(set(a1) | set(a2)):
        if a1.get(abi) != a2.get(abi):
            diffs.append((abi, a1.get(abi), a2.get(abi)))
    return diffs


# --------------------------------------------------------------------------
# CLI

def _print_errors(errors):
    for e in errors:
        print(f"FAIL: {e}")


def cmd_check_toolchain(args):
    errors = check_toolchain(args.repo_root, ndk_path=args.ndk_path)
    if errors:
        _print_errors(errors)
        print("RESULT: FAIL — toolchain assertion failed")
        return 1
    print("RESULT: PASS — pinned Rust/NDK/cargo-ndk toolchain verified")
    return 0


def cmd_symbols(args):
    errors = []
    expected = expected_jni_exports(args.repo_root, errors)
    if errors:
        _print_errors(errors)
        return 1
    print("Expected JNI exports (from Kotlin + Rust source):")
    for s in sorted(expected):
        print(f"  {s}")
    print(f"RESULT: PASS — {len(expected)} exports, Kotlin/Rust surfaces agree")
    return 0


def cmd_build(args):
    errors = check_toolchain(args.repo_root, ndk_path=args.ndk_path)
    # F7: refuse to build provenance from a dirty tree before spending any time
    require_clean_tree(args.repo_root, errors)
    if errors:
        _print_errors(errors)
        print("RESULT: FAIL — toolchain/tree assertion failed; build refused")
        return 1
    ndk = resolve_ndk_path(args.ndk_path)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = cargo_ndk_build(args.repo_root, out_dir, ndk, target_dir=args.target_dir)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        print("RESULT: FAIL — cargo ndk build failed")
        return 1
    manifest, merr = write_manifest(
        args.repo_root, out_dir, args.manifest, ndk, build_id=args.build_id
    )
    if merr:
        _print_errors(merr)
        print("RESULT: FAIL — produced artifacts failed provenance checks")
        return 1
    print(f"Produced artifacts under {out_dir}")
    for a in manifest["artifacts"]:
        print(f"  {a['file']}  sha256={a['sha256']}  size={a['size']}  jni_exports={a['jni_export_count']}")
    print(f"Manifest: {args.manifest}")
    print("RESULT: PASS — native artifacts built from pinned source/toolchain")
    return 0


def cmd_verify(args):
    errors = verify_manifest(
        args.repo_root, args.manifest, args.out_dir,
        expected_source_sha=args.expect_source_sha,
    )
    if errors:
        _print_errors(errors)
        print("RESULT: FAIL — artifact/manifest verification failed")
        return 1
    print("RESULT: PASS — produced artifacts match manifest; ABI + JNI parity + clean-tree + reproducibility attestation verified")
    return 0


def attest_reproducibility(primary_manifest_path, m1, m2, build_ids):
    """Three-way compare primary vs two clean rebuilds; on success write the
    attestation INTO the primary manifest (F5). Returns list of errors."""
    errors = []
    p = Path(primary_manifest_path)
    if not p.exists():
        return [f"primary manifest missing: {p} (run `build` first)"]
    try:
        primary = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"primary manifest is not valid JSON: {e}"]
    for label, other in (("build#1", m1), ("build#2", m2)):
        for abi, h_p, h_o in compare_manifest_hashes(primary, other):
            errors.append(f"DIFF {abi}: primary {h_p} != {label} {h_o}")
    if compare_manifest_hashes(m1, m2):
        errors.append("clean rebuilds differ from each other")
    prim_abis = {a.get("abi") for a in primary.get("artifacts") or []}
    if prim_abis != set(REQUIRED_ABIS):
        errors.append("primary manifest does not cover exactly the required ABI set")
    if errors:
        return errors
    primary.setdefault("build", {})
    primary["build"]["reproducible_build_confirmed"] = True
    primary["build"]["reproducibility"] = {
        "method": "two-clean-builds-three-way-compare",
        "builds": 2,
        "build_ids": build_ids,
        "per_abi_sha256": {a["abi"]: a["sha256"] for a in primary["artifacts"]},
    }
    p.write_text(json.dumps(primary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return []


def cmd_rebuild_compare(args):
    """Two clean builds under the same pinned environment; three-way compare
    against the primary manifest; on success write the authoritative
    reproducibility attestation into the primary manifest (F5)."""
    errors = check_toolchain(args.repo_root, ndk_path=args.ndk_path)
    require_clean_tree(args.repo_root, errors)
    if errors:
        _print_errors(errors)
        print("RESULT: FAIL — toolchain/tree assertion failed; build refused")
        return 1
    ndk = resolve_ndk_path(args.ndk_path)
    manifests = []
    build_ids = []
    with tempfile.TemporaryDirectory(prefix="anox-repro-") as td:
        td = Path(td)
        for i in (1, 2):
            out = td / f"build{i}" / "jniLibs"
            tdir = td / f"target{i}"
            proc = cargo_ndk_build(args.repo_root, out, ndk, target_dir=tdir)
            if proc.returncode != 0:
                sys.stdout.write(proc.stdout)
                sys.stderr.write(proc.stderr)
                print(f"RESULT: FAIL — clean build #{i} failed")
                return 1
            mpath = td / f"build{i}" / "manifest.json"
            bid = f"{args.build_id or 'local'}-repro{i}"
            build_ids.append(bid)
            m, merr = write_manifest(args.repo_root, out, mpath, ndk, build_id=bid)
            if merr:
                _print_errors(merr)
                return 1
            manifests.append(m)
        for i, m in enumerate(manifests, 1):
            for a in m["artifacts"]:
                print(f"  build#{i} {a['abi']}: {a['sha256']}")
        aerr = attest_reproducibility(args.manifest, manifests[0], manifests[1], build_ids)
        if aerr:
            _print_errors(aerr)
            print("RESULT: FAIL — reproducibility attestation refused (hash divergence or missing primary manifest)")
            return 1
        print(f"Attestation written: {args.manifest} (build.reproducible_build_confirmed = true)")
        print("RESULT: PASS — primary manifest and two clean builds produced identical per-ABI SHA-256")
        return 0


def main():
    ap = argparse.ArgumentParser(description="Authoritative anox_crypto native build/provenance driver")
    ap.add_argument("command", choices=["check-toolchain", "symbols", "build", "verify", "rebuild-compare"])
    ap.add_argument("--repo-root", default=str(REPO_ROOT))
    ap.add_argument("--ndk-path", default=None)
    ap.add_argument("--out-dir", default=str(REPO_ROOT / DEFAULT_OUT_DIR))
    ap.add_argument("--manifest", default=str(REPO_ROOT / DEFAULT_MANIFEST))
    ap.add_argument("--target-dir", default=None, help="override CARGO_TARGET_DIR")
    ap.add_argument("--build-id", default=None)
    ap.add_argument("--expect-source-sha", default=None)
    args = ap.parse_args()
    args.repo_root = Path(args.repo_root).resolve()

    return {
        "check-toolchain": cmd_check_toolchain,
        "symbols": cmd_symbols,
        "build": cmd_build,
        "verify": cmd_verify,
        "rebuild-compare": cmd_rebuild_compare,
    }[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
