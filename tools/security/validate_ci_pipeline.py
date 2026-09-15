#!/usr/bin/env python3
"""Structural fail-closed gate for the S1 CI pipeline (MSC-001/002/003/038).

Asserts that .github/workflows/ci.yml actually contains the security-critical
jobs/steps required by REMEDIATION_SESSION_S1.  Removing or renaming a gate
fails this validator — a green run is impossible without the gate present.

Stdlib only; uses a minimal job-block scanner (no YAML dependency).
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ".github/workflows/ci.yml"

# Each requirement: (name, job-or-None, regex that must appear inside that
# job's block; job=None means "anywhere in the workflow").
REQUIREMENTS = [
    ("policy gate: b017-lite validator", None, r"b017_lite_policy_validator\.py"),
    ("policy gate: CI pipeline structure", None, r"validate_ci_pipeline\.py"),
    ("policy gate: S1 provenance static gate", None, r"validate_s1_build_provenance\.py"),
    ("policy gate: secret scan", None, r"secret_scan\.py"),
    ("policy gate: B-021 matrix validator", None, r"validate_b021_verification_matrix\.py"),
    ("policy gate: cargo audit advisory scan", None, r"cargo\s+audit"),
    ("rust job: toolchain pin assertion", "rust", r"rust-toolchain\.toml"),
    ("rust job: locked tests", "rust", r"cargo\s+test\s+--locked"),
    ("native-build job exists", "native-build", r"native_build\.py\s+check-toolchain"),
    ("native-build: authoritative build step", "native-build", r"native_build\.py\s+build\b"),
    ("native-build: reproducibility (two clean builds)", "native-build", r"native_build\.py\s+rebuild-compare"),
    ("native-build: artifact verify", "native-build", r"native_build\.py\s+verify"),
    ("native-build: artifact upload", "native-build", r"upload-artifact@"),
    ("android-debug: downloads native artifacts", "android-debug", r"download-artifact@"),
    ("android-debug: lint gate", "android-debug", r"lintDebug|lint\b"),
    ("android-debug: APK provenance binding", "android-debug", r"validate_apk_contents\.py[\s\S]*?--native-manifest"),
    ("android-release: APK provenance binding", "android-release", r"validate_apk_contents\.py[\s\S]*?--native-manifest"),
    ("instrumented job: arm64", "instrumented-arm64", r"connectedDebugAndroidTest"),
    ("instrumented job: x86_64", "instrumented-x86_64", r"connectedDebugAndroidTest"),
    ("instrumented arm64: consumes native artifacts", "instrumented-arm64", r"download-artifact@"),
    ("instrumented x86_64: consumes native artifacts", "instrumented-x86_64", r"download-artifact@"),
    ("instrumented arm64: tested APK bound to manifest", "instrumented-arm64", r"validate_apk_contents\.py[\s\S]*?--native-manifest"),
    ("instrumented x86_64: tested APK bound to manifest", "instrumented-x86_64", r"validate_apk_contents\.py[\s\S]*?--native-manifest"),
]

REQUIRED_JOBS = {
    "supply-chain-policy",
    "gradle-wrapper-validation",
    "rust",
    "native-build",
    "android-debug",
    "android-release",
    "instrumented-arm64",
    "instrumented-x86_64",
}


def split_jobs(text):
    """Return {job_name: block_text} for top-level jobs in a workflow file."""
    lines = text.splitlines()
    jobs = {}
    in_jobs = False
    current = None
    buf = []
    for line in lines:
        if re.match(r"^jobs\s*:\s*$", line):
            in_jobs = True
            continue
        if not in_jobs:
            continue
        # end of jobs block: a new top-level key
        if re.match(r"^[A-Za-z_][\w-]*\s*:", line):
            break
        m = re.match(r"^  ([\w-]+)\s*:\s*$", line)
        if m:
            if current:
                jobs[current] = "\n".join(buf)
            current = m.group(1)
            buf = []
            continue
        if current:
            buf.append(line)
    if current:
        jobs[current] = "\n".join(buf)
    return jobs


def validate(workflow_path):
    errors = []
    p = Path(workflow_path)
    if not p.exists():
        return [f"workflow missing: {p}"]
    text = p.read_text(encoding="utf-8")
    jobs = split_jobs(text)
    if not jobs:
        errors.append("no jobs block parsed from workflow")

    missing_jobs = REQUIRED_JOBS - set(jobs)
    for j in sorted(missing_jobs):
        errors.append(f"required job missing: {j}")

    for name, job, pattern in REQUIREMENTS:
        if job is None:
            hay = text
            where = "workflow"
        else:
            if job not in jobs:
                errors.append(f"{name}: job '{job}' missing")
                continue
            hay = jobs[job]
            where = f"job '{job}'"
        if not re.search(pattern, hay):
            errors.append(f"{name}: pattern {pattern!r} not found in {where}")
    return errors


def main():
    ap = argparse.ArgumentParser(description="Validate that the CI workflow contains all S1 security gates.")
    ap.add_argument("--workflow", default=str(REPO_ROOT / WORKFLOW))
    args = ap.parse_args()
    errors = validate(args.workflow)
    print("CI PIPELINE STRUCTURE GATE (S1)")
    if errors:
        for e in errors:
            print(f"  FAIL {e}")
        print("RESULT: FAIL")
        return 1
    print(f"  OK   all {len(REQUIREMENTS)} gate requirements + {len(REQUIRED_JOBS)} required jobs present")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
