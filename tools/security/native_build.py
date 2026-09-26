#!/usr/bin/env python3
"""Authoritative native build driver for the anox_crypto Android library.

S1 build provenance (MSC-UNIT-001): the committed ``.so`` bypass is
eliminated. The only trusted way to obtain ``libanox_crypto.so`` for Android
packaging is this script, which

  * asserts the repository-pinned Rust toolchain (crypto/rust/rust-toolchain.toml)
  * asserts the pinned Android NDK and cargo-ndk versions
  * builds every required ABI from reviewed source with ``--locked``
  * applies deterministic path remapping so clean rebuilds are comparable
  * emits a machine-readable provenance manifest binding source revision,
    toolchain, ABI, artifact path and SHA-256 for each produced library
  * verifies JNI symbol parity between the Kotlin ``external fun`` surface,
    the Rust ``#[no_mangle]`` exports and the produced binary — ``verify``
    parses each .so's ELF dynamic symbol table itself (stdlib) and requires
    three-way agreement: ACTUAL binary exports == source-derived surface ==
    manifest-declared export list/fingerprint; a manifest fingerprint is never
    accepted as proof of inspection
  * checks the ELF architecture of every artifact against its ABI, refuses
    non-ELF placeholders, and fails on any uncontrolled alternative native
    input (committed/stale .so, .aar, .jar under android/ or crypto/android/)
  * refuses provenance from a dirty working tree (an unqualified repo SHA must
    never describe a tree that differs from the commit it names)

Uses only the Python 3 standard library. Never prints secrets.
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

# Required Android ABI -> Rust target triple. The authoritative pipeline must
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


# --------------------------------------------------------------------------
# Actual-binary inspection. The verifier derives the export surface from the
# ELF dynamic symbol table ITSELF (stdlib parser) — a manifest fingerprint is
# never accepted as proof that anybody looked at the binary. When llvm-nm is
# available it is used as a second, independent reader and must agree.

ELF_MACHINE = {"arm64-v8a": 183, "x86_64": 62}  # EM_AARCH64, EM_X86_64
_SHT_DYNSYM = 11
_SHN_UNDEF = 0
_STB_GLOBAL, _STB_WEAK = 1, 2


class ElfError(ValueError):
    pass


def elf_inspect(path):
    """Parse an ELF64 shared object and return
    {"e_machine": int, "exports": set[str]} where exports are the DEFINED
    GLOBAL/WEAK symbols of .dynsym. Raises ElfError on anything that is not
    a well-formed little-endian ELF64 with a dynamic symbol table."""
    import struct
    data = Path(path).read_bytes()
    if len(data) < 64 or data[:4] != b"\x7fELF":
        raise ElfError("not an ELF file")
    if data[4] != 2:
        raise ElfError("not ELFCLASS64")
    if data[5] != 1:
        raise ElfError("not little-endian ELF")
    e_type, e_machine = struct.unpack_from("<HH", data, 16)
    if e_type != 3:  # ET_DYN
        raise ElfError(f"not a shared object (e_type={e_type})")
    e_shoff, = struct.unpack_from("<Q", data, 40)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 58)
    if e_shoff == 0 or e_shnum == 0 or e_shentsize < 64:
        raise ElfError("no section header table")
    if e_shoff + e_shnum * e_shentsize > len(data):
        raise ElfError("section header table out of bounds")
    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = \
            struct.unpack_from("<IIQQQQIIQQ", data, off)
        sections.append((sh_type, sh_offset, sh_size, sh_link, sh_entsize))
    dynsyms = [s for s in sections if s[0] == _SHT_DYNSYM]
    if len(dynsyms) != 1:
        raise ElfError(f"expected exactly one .dynsym, found {len(dynsyms)}")
    _, sym_off, sym_size, sym_link, sym_ent = dynsyms[0]
    sym_ent = sym_ent or 24
    if sym_ent != 24 or sym_off + sym_size > len(data) or sym_link >= len(sections):
        raise ElfError(".dynsym malformed")
    _, str_off, str_size, _, _ = sections[sym_link]
    if str_off + str_size > len(data):
        raise ElfError(".dynstr out of bounds")
    strtab = data[str_off:str_off + str_size]
    exports = set()
    for i in range(sym_size // sym_ent):
        st_name, st_info, st_other, st_shndx, st_value, st_sz = \
            struct.unpack_from("<IBBHQQ", data, sym_off + i * sym_ent)
        if st_shndx == _SHN_UNDEF or (st_info >> 4) not in (_STB_GLOBAL, _STB_WEAK):
            continue
        end = strtab.find(b"\x00", st_name)
        if st_name >= len(strtab) or end < 0:
            raise ElfError("symbol name outside .dynstr")
        name = strtab[st_name:end].decode("ascii", errors="replace")
        if name:
            exports.add(name)
    return {"e_machine": e_machine, "exports": exports}


def dynamic_symbols(so_path, llvm_nm=None):
    """Exported (defined) dynamic symbols of an ELF .so, read from the ELF
    itself. Returns None if the file is not a parseable ELF64 shared object."""
    try:
        info = elf_inspect(so_path)
    except (ElfError, OSError, ValueError):
        return None
    tool = llvm_nm or shutil.which("llvm-nm")
    if tool is not None:
        proc = _run([str(tool), "-D", "--defined-only", str(so_path)])
        if proc.returncode == 0:
            nm_syms = set()
            for line in proc.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[-2] not in ("U", "u"):
                    nm_syms.add(parts[-1])
            nm_jni = {s for s in nm_syms if s.startswith(JNI_PREFIX)}
            elf_jni = {s for s in info["exports"] if s.startswith(JNI_PREFIX)}
            if nm_jni != elf_jni:
                return None  # two readers disagree — not trustworthy
    return info["exports"]


def actual_jni_exports(so_path, abi, errors, llvm_nm=None):
    """Independently derive the ACTUAL JNI export surface of a produced .so
    and check its ELF architecture against the claimed ABI. Returns the set
    of JNI exports, or None (with errors appended) when the binary cannot be
    trusted."""
    try:
        info = elf_inspect(so_path)
    except (ElfError, OSError, ValueError) as e:
        errors.append(f"{so_path}: not a verifiable ELF64 shared object ({e})")
        return None
    want_machine = ELF_MACHINE.get(abi)
    if want_machine is not None and info["e_machine"] != want_machine:
        errors.append(f"{so_path}: ELF e_machine {info['e_machine']} does not match ABI {abi} "
                      f"(expected {want_machine})")
        return None
    syms = dynamic_symbols(so_path, llvm_nm=llvm_nm)
    if syms is None:
        errors.append(f"{so_path}: dynamic symbol readers disagree or binary unreadable — refusing to trust")
        return None
    return {s for s in syms if s.startswith(JNI_PREFIX)}


def check_symbol_parity(so_path, expected, errors, llvm_nm=None, abi=None):
    exported = actual_jni_exports(so_path, abi, errors, llvm_nm=llvm_nm)
    if exported is None:
        return None
    missing = expected - exported
    extra = exported - expected
    if missing:
        errors.append(f"{so_path}: missing expected JNI exports: " + ", ".join(sorted(missing)))
    if extra:
        errors.append(f"{so_path}: unexpected JNI exports (stale/foreign surface): " + ", ".join(sorted(extra)))
    return exported


# Native input sources OTHER than the authoritative produced directory. Any
# native library / prebuilt archive under these trees is an uncontrolled
# alternative JNI source and fails verification (Gradle must never be able to
# fall back to a committed / stale library).
ALTERNATIVE_NATIVE_INPUT_ROOTS = ("android", "crypto/android")
ALTERNATIVE_NATIVE_SUFFIXES = (".so", ".aar", ".jar")
_SKIP_DIRS = {"build", ".gradle", ".cxx", ".idea"}


def find_alternative_native_inputs(repo_root, produced_dir=None):
    root = Path(repo_root)
    produced = Path(produced_dir).resolve() if produced_dir else None
    found = []
    for rel in ALTERNATIVE_NATIVE_INPUT_ROOTS:
        base = root / rel
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in ALTERNATIVE_NATIVE_SUFFIXES:
                continue
            parts = p.relative_to(root).parts
            if any(part in _SKIP_DIRS for part in parts[:-1]):
                continue
            if produced and produced in p.resolve().parents:
                continue
            found.append(str(p.relative_to(root)))
    return found


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
    """Return ("clean", []) or ("dirty", [paths]) or (None, [reason]).

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
        shown = ", ".join(detail[:8]) + (" ..." if len(detail) > 8 else "")
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

    ``source.working_tree`` is recorded and (by default) a dirty tree is an
    error — the manifest never claims an unqualified clean SHA for a modified
    tree. ``build.reproducible_build_confirmed`` is a boolean that is only
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
        exports = check_symbol_parity(so, expected, errors, llvm_nm=llvm_nm, abi=abi) or set()
        artifacts.append({
            "abi": abi,
            "rust_target": REQUIRED_ABIS[abi],
            "elf_machine": ELF_MACHINE[abi],
            "file": f"{abi}/{LIB_NAME}",
            "sha256": sha256_file(so),
            "size": so.stat().st_size,
            "jni_export_count": len(exports),
            "jni_exports": sorted(exports),
            "jni_exports_sha256": sha256_text("\n".join(sorted(exports))),
        })
    for alt in find_alternative_native_inputs(root, out_dir):
        errors.append(f"uncontrolled alternative native input present: {alt}")

    head = _git_head(root) or "UNKNOWN"
    channel, _, _ = parse_toolchain_toml(root / TOOLCHAIN_FILE)
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
            "cargo_ndk": REQUIRED_CARGO_NDK,
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


MANIFEST_TOP_KEYS = {"schema_version", "source", "toolchain", "build", "abis", "artifacts"}
MANIFEST_SOURCE_KEYS = {"repo_sha", "crate", "crate_manifest", "cargo_lock_sha256", "rust_toolchain_file", "working_tree"}
MANIFEST_TOOLCHAIN_KEYS = {"channel", "rustc", "cargo_ndk", "ndk_revision", "host"}
MANIFEST_BUILD_KEYS = {"build_id", "profile", "locked", "path_remapped", "reproducible_build_confirmed", "reproducibility"}
MANIFEST_ARTIFACT_KEYS = {"abi", "rust_target", "elf_machine", "file", "sha256", "size",
                          "jni_export_count", "jni_exports", "jni_exports_sha256"}
REPRO_METHOD = "two-clean-builds-three-way-compare"


def verify_manifest(repo_root, manifest_path, produced_dir, expected_source_sha=None, errors=None,
                    require_clean_live_tree=True, llvm_nm=None):
    """Verify produced artifacts against the manifest — fail closed.

    Mandatory manifest semantics (exact schema): source Git SHA (bound to the
    expected anchor — the live HEAD or an explicit ``expected_source_sha``),
    Cargo.lock hash, pinned toolchain versions, exact ABI set, per-artifact
    hash / size / architecture, the ACTUAL JNI export list, its fingerprint,
    and the two-clean-build reproducibility attestation with its details.

    JNI verification is three-way and performed on the ACTUAL binary: the
    export surface parsed from each .so's ELF dynamic symbol table must equal
    the source-derived expected surface AND the manifest-declared export
    list/fingerprint. A manifest fingerprint alone proves nothing.
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
    if not isinstance(m, dict):
        errors.append("manifest is not a JSON object")
        return errors

    # ---- exact schema -----------------------------------------------------
    if m.get("schema_version") != MANIFEST_SCHEMA:
        errors.append(f"manifest schema_version != {MANIFEST_SCHEMA}")
    if set(m) != MANIFEST_TOP_KEYS:
        errors.append(f"manifest top-level keys {sorted(set(m) ^ MANIFEST_TOP_KEYS)} differ from exact schema")
    src = m.get("source") if isinstance(m.get("source"), dict) else {}
    tc = m.get("toolchain") if isinstance(m.get("toolchain"), dict) else {}
    build = m.get("build") if isinstance(m.get("build"), dict) else {}
    arts = m.get("artifacts") if isinstance(m.get("artifacts"), list) else []
    for label, got, want in (("source", src, MANIFEST_SOURCE_KEYS), ("toolchain", tc, MANIFEST_TOOLCHAIN_KEYS),
                             ("build", build, MANIFEST_BUILD_KEYS)):
        if set(got) != want:
            errors.append(f"manifest {label} keys {sorted(set(got) ^ want)} differ from exact schema")

    # ---- source anchor ------------------------------------------------------
    # The expected anchor is the live HEAD unless an explicit anchor is given.
    # A syntactically valid but unanchored SHA is NOT provenance.
    want_sha = expected_source_sha or _git_head(root)
    if not re.fullmatch(r"[0-9a-f]{40}", str(src.get("repo_sha") or "")):
        errors.append("manifest source.repo_sha is not a 40-hex SHA")
    elif not want_sha:
        errors.append("no expected source anchor available (not a git checkout and no --expect-source-sha): "
                      "manifest source.repo_sha cannot be verified")
    elif src.get("repo_sha") != want_sha:
        errors.append(
            f"manifest source.repo_sha {src.get('repo_sha')} != expected {want_sha}"
        )
    if src.get("crate") != CRATE_DIR or src.get("crate_manifest") != f"{CRATE_DIR}/Cargo.toml" \
            or src.get("rust_toolchain_file") != TOOLCHAIN_FILE:
        errors.append("manifest source crate/crate_manifest/rust_toolchain_file do not name the reviewed crate")
    lock = root / CARGO_LOCK
    if not lock.exists():
        errors.append(f"{CARGO_LOCK} missing — Cargo.lock identity cannot be verified")
    elif src.get("cargo_lock_sha256") != sha256_file(lock):
        errors.append("manifest cargo_lock_sha256 does not match Cargo.lock")
    # A manifest may only claim an unqualified clean source SHA when the
    # producing tree was clean, and the live tree must still be clean.
    if src.get("working_tree") != "clean":
        errors.append(
            f"manifest source.working_tree={src.get('working_tree')!r} — provenance from a "
            "non-clean tree is not accepted"
        )
    if require_clean_live_tree:
        require_clean_tree(root, errors)

    # ---- toolchain ----------------------------------------------------------
    channel, _, _ = parse_toolchain_toml(root / TOOLCHAIN_FILE)
    if not channel:
        errors.append("pinned rust toolchain channel unavailable — cannot verify manifest toolchain")
    elif tc.get("channel") != channel:
        errors.append(f"manifest toolchain.channel {tc.get('channel')!r} != pinned {channel!r}")
    if channel and not re.fullmatch(r"rustc " + re.escape(channel) + r"(?: \([0-9a-f]+ \d{4}-\d{2}-\d{2}\))?",
                                    str(tc.get("rustc") or "")):
        errors.append(f"manifest toolchain.rustc {tc.get('rustc')!r} is not the pinned rustc {channel}")
    if tc.get("cargo_ndk") != REQUIRED_CARGO_NDK:
        errors.append(f"manifest cargo_ndk {tc.get('cargo_ndk')!r} != pinned {REQUIRED_CARGO_NDK}")
    if tc.get("ndk_revision") != REQUIRED_NDK_REVISION:
        errors.append(f"manifest ndk_revision {tc.get('ndk_revision')!r} != pinned {REQUIRED_NDK_REVISION}")

    # ---- build / reproducibility attestation --------------------------------
    if build.get("profile") != "release" or build.get("locked") is not True or build.get("path_remapped") is not True:
        errors.append("manifest build is not release/--locked/path-remapped")
    if not str(build.get("build_id") or "").strip():
        errors.append("manifest build.build_id missing")
    art_hashes = {a.get("abi"): a.get("sha256") for a in arts if isinstance(a, dict)}
    if build.get("reproducible_build_confirmed") is not True:
        errors.append(
            "manifest build.reproducible_build_confirmed is not True — run "
            "`native_build.py rebuild-compare` (two clean builds) before verify/packaging"
        )
    else:
        rep = build.get("reproducibility") if isinstance(build.get("reproducibility"), dict) else {}
        att = rep.get("per_abi_sha256") if isinstance(rep.get("per_abi_sha256"), dict) else {}
        ids = rep.get("build_ids")
        if rep.get("builds") != 2 or rep.get("method") != REPRO_METHOD:
            errors.append("manifest build.reproducibility attestation malformed (builds/method)")
        if not (isinstance(ids, list) and len(ids) == 2 and all(isinstance(i, str) and i.strip() for i in ids)
                and ids[0] != ids[1]):
            errors.append("manifest build.reproducibility.build_ids must name two distinct clean rebuilds")
        if att != art_hashes or set(att) != set(REQUIRED_ABIS):
            errors.append("manifest build.reproducibility.per_abi_sha256 does not equal artifact hashes")

    # ---- ABI set ------------------------------------------------------------
    if sorted(m.get("abis") or []) != sorted(REQUIRED_ABIS.keys()):
        errors.append("manifest ABI set does not equal required ABI set")

    # ---- artifacts: hash, size, architecture, ACTUAL JNI surface -----------
    expected = expected_jni_exports(root, errors)
    expected_fp = sha256_text("\n".join(sorted(expected)))
    if llvm_nm is None:
        ndk = resolve_ndk_path()
        llvm_nm = find_llvm_nm(ndk) if ndk else None

    seen_abis = set()
    inspected = 0
    for art in arts:
        if not isinstance(art, dict):
            errors.append("manifest artifact entry is not an object")
            continue
        abi = art.get("abi")
        rel = art.get("file") or ""
        if set(art) != MANIFEST_ARTIFACT_KEYS:
            errors.append(f"manifest artifact {abi!r} keys {sorted(set(art) ^ MANIFEST_ARTIFACT_KEYS)} differ from exact schema")
        if abi in seen_abis:
            errors.append(f"manifest lists ABI {abi!r} twice")
        seen_abis.add(abi)
        if not rel or rel.startswith("/") or ".." in rel.split("/"):
            errors.append(f"manifest artifact has invalid file path: {rel!r}")
            continue
        if abi not in REQUIRED_ABIS:
            errors.append(f"manifest artifact has unexpected ABI: {abi!r}")
            continue
        if rel != f"{abi}/{LIB_NAME}":
            errors.append(f"manifest artifact path {rel!r} != {abi}/{LIB_NAME}")
        if art.get("rust_target") != REQUIRED_ABIS[abi]:
            errors.append(f"{rel}: rust_target {art.get('rust_target')!r} != {REQUIRED_ABIS[abi]}")
        if art.get("elf_machine") != ELF_MACHINE[abi]:
            errors.append(f"{rel}: manifest elf_machine {art.get('elf_machine')!r} != {ELF_MACHINE[abi]} for {abi}")
        fpath = produced_dir / rel
        if not fpath.is_file():
            errors.append(f"manifest artifact missing on disk: {rel}")
            continue
        actual = sha256_file(fpath)
        if art.get("sha256") != actual:
            errors.append(f"{rel}: sha256 mismatch (manifest {art.get('sha256')} != produced {actual})")
        if art.get("size") != fpath.stat().st_size:
            errors.append(f"{rel}: size mismatch vs manifest")
        # --- actual binary inspection (architecture + dynamic exports) ---
        actual_exports = actual_jni_exports(fpath, abi, errors, llvm_nm=llvm_nm)
        if actual_exports is None:
            continue
        inspected += 1
        declared = art.get("jni_exports")
        if not isinstance(declared, list) or not all(isinstance(s, str) for s in declared):
            errors.append(f"{rel}: manifest jni_exports list missing")
            declared_set = None
        else:
            declared_set = set(declared)
            if declared != sorted(declared_set):
                errors.append(f"{rel}: manifest jni_exports not sorted/unique")
        actual_fp = sha256_text("\n".join(sorted(actual_exports)))
        # three-way agreement: actual binary == source-derived == manifest
        if actual_exports != expected:
            missing = sorted(expected - actual_exports)
            extra = sorted(actual_exports - expected)
            errors.append(f"{rel}: ACTUAL binary JNI exports differ from source-derived surface"
                          f"{' (missing: ' + ', '.join(missing) + ')' if missing else ''}"
                          f"{' (extra: ' + ', '.join(extra) + ')' if extra else ''}")
        if declared_set is not None and declared_set != actual_exports:
            errors.append(f"{rel}: manifest jni_exports differ from the ACTUAL binary export surface")
        if art.get("jni_exports_sha256") != expected_fp:
            errors.append(f"{rel}: JNI export fingerprint differs from source-derived expected surface")
        if art.get("jni_exports_sha256") != actual_fp:
            errors.append(f"{rel}: JNI export fingerprint differs from the ACTUAL binary export surface")
        if art.get("jni_export_count") != len(actual_exports):
            errors.append(f"{rel}: jni_export_count {art.get('jni_export_count')!r} != actual {len(actual_exports)}")
    if seen_abis != set(REQUIRED_ABIS.keys()):
        errors.append("manifest artifacts do not cover exactly the required ABI set")
    if inspected != len(REQUIRED_ABIS):
        errors.append(f"actual binary inspection completed for {inspected}/{len(REQUIRED_ABIS)} ABIs — "
                      "JNI is NOT verified")

    # no stray native library beyond the manifest (any case / suffix variant)
    if produced_dir.is_dir():
        manifest_files = {a.get("file") for a in arts if isinstance(a, dict)}
        for so in produced_dir.rglob("*"):
            if so.is_file() and (".so" in so.name.lower()) and str(so.relative_to(produced_dir)) not in manifest_files:
                errors.append(f"produced dir contains artifact not in manifest: {so.relative_to(produced_dir)}")
    # no uncontrolled alternative JNI input anywhere Gradle could pick up
    for alt in find_alternative_native_inputs(root, produced_dir):
        errors.append(f"uncontrolled alternative native input present: {alt}")
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
    # Refuse to build provenance from a dirty tree before spending any time.
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
    print("RESULT: PASS — produced artifacts match manifest; ELF architecture + ACTUAL-binary JNI surface "
          "(three-way: binary == source == manifest) + source anchor + Cargo.lock + toolchain + clean-tree + "
          "reproducibility attestation verified; no alternative native inputs")
    return 0


def attest_reproducibility(primary_manifest_path, m1, m2, build_ids):
    """Three-way compare primary vs two clean rebuilds; on success write the
    attestation INTO the primary manifest. Returns list of errors."""
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
    reproducibility attestation into the primary manifest."""
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
