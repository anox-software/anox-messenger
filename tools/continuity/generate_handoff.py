#!/usr/bin/env python3
"""Generate an anoX V1 handoff ZIP."""

import argparse
import hashlib
import io
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "handoff"

EXCLUDED_DIRS = {
    ".git",
    "build",
    ".gradle",
    "target",
    "__pycache__",
    ".kotlin",
    "artifacts",
}

EXCLUDED_FILES = {
    ".DS_Store",
    "local.properties",
    ".env",
    ".env.local",
    ".env.production",
}

EXCLUDED_SUFFIXES = (
    ".jks",
    ".keystore",
    ".p12",
    ".apk",
    ".aab",
    ".dex",
    ".class",
    ".o",
    ".so",
    ".dylib",
    ".pyc",
    ".pyo",
    ".zip",
)


def git_cmd(args):
    result = subprocess.run(
        ["git"] + args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip(), result.returncode


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_excluded(rel_path):
    parts = Path(rel_path).parts
    if any(p in EXCLUDED_DIRS for p in parts):
        return True
    name = parts[-1]
    if name in EXCLUDED_FILES:
        return True
    if name.startswith(".") and (name.endswith(".env") or name.endswith(".local")):
        return True
    if name.endswith(EXCLUDED_SUFFIXES):
        return True
    return False


def collect_files():
    files = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        # Prune excluded directories in place to avoid walking them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            full = Path(dirpath) / name
            rel = full.relative_to(REPO_ROOT).as_posix()
            if is_excluded(rel):
                continue
            files.append(rel)
    return sorted(files)


def build_git_snapshot():
    lines = []
    for cmd, label in [
        (["remote", "-v"], "git remote -v"),
        (["branch", "--show-current"], "git branch --show-current"),
        (["rev-parse", "HEAD"], "git rev-parse HEAD"),
        (["status", "--short"], "git status --short"),
        (["tag", "--list"], "git tag --list"),
        (["log", "--oneline", "-n", "15"], "git log --oneline -n 15"),
    ]:
        out, _ = git_cmd(cmd)
        lines.append(f"### {label}")
        lines.append(out if out else "(empty)")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate an anoX handoff package.")
    parser.add_argument(
        "--emergency",
        action="store_true",
        help="Allow a dirty working tree and label the package as emergency/dirty.",
    )
    args = parser.parse_args()

    head, _ = git_cmd(["rev-parse", "HEAD"])
    short = head[:12]
    branch, _ = git_cmd(["branch", "--show-current"])
    status, _ = git_cmd(["status", "--short"])

    dirty = status.strip() != ""
    if dirty and not args.emergency:
        print("ERROR: Working tree is dirty. Clean it or use --emergency.", file=sys.stderr)
        print(status, file=sys.stderr)
        return 1

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    status_label = "EMERGENCY_DIRTY" if (dirty and args.emergency) else "CLEAN"
    zip_name = f"ANOX_HANDOFF_{date_str}_{short}.zip"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = ARTIFACT_DIR / zip_name

    rel_files = collect_files()

    manifest = io.StringIO()
    manifest.write(f"# ANOX V1 Handoff Manifest\n")
    manifest.write(f"# Date: {date_str}\n")
    manifest.write(f"# HEAD: {head}\n")
    manifest.write(f"# Branch: {branch}\n")
    manifest.write(f"# Status: {status_label}\n")
    manifest.write(f"# File count: {len(rel_files)}\n")
    manifest.write("\n")

    sha_manifest = io.StringIO()
    sha_manifest.write(f"# SHA-256 manifest for {zip_name}\n")
    sha_manifest.write(f"# HEAD: {head}\n\n")

    git_snapshot = build_git_snapshot()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in rel_files:
            full = REPO_ROOT / rel
            zf.write(full, rel)
            digest = sha256_file(full)
            manifest.write(f"{rel}\n")
            sha_manifest.write(f"{digest}  {rel}\n")

        # Git snapshot
        zf.writestr("GIT_SNAPSHOT.txt", git_snapshot)

        # Manifests
        zf.writestr("MANIFEST.txt", manifest.getvalue())
        zf.writestr("SHA256_MANIFEST.txt", sha_manifest.getvalue())

    zip_digest = sha256_file(zip_path)
    total_files = len(rel_files) + 3  # 3 generated text files

    print(f"ZIP PATH:     {zip_path}")
    print(f"ZIP SHA-256:  {zip_digest}")
    print(f"FILE COUNT:   {total_files}")
    print(f"HEAD:         {head}")
    print(f"STATUS:       {status_label}")

    if dirty:
        print("\nWARNING: EMERGENCY / DIRTY HANDOFF")
        print("Dirty files:")
        print(status)

    return 0


if __name__ == "__main__":
    sys.exit(main())
