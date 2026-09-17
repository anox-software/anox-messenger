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

# F4: the artifact lineage graph is enforced structurally, not inferred from
# step names. Each entry: job -> set of jobs that MUST appear in its `needs:`
# (direct edges; the graph below is what the provenance chain relies on).
REQUIRED_NEEDS = {
    "rust": {"supply-chain-policy"},
    "gradle-wrapper-validation": {"supply-chain-policy"},
    "native-build": {"rust", "gradle-wrapper-validation"},
    "android-debug": {"native-build"},
    "android-release": {"native-build", "android-debug"},
    "instrumented-arm64": {"native-build", "android-debug"},
    "instrumented-x86_64": {"native-build", "android-debug"},
}
# Jobs that consume the authoritative native artifact. Every one of them must
# (a) download exactly the artifact uploaded by native-build, (b) re-run
# `native_build.py verify` before any build/test step consumes it, and
# (c) contain no `continue-on-error` / conditional skip on those steps.
ARTIFACT_CONSUMERS = {"android-debug", "android-release", "instrumented-arm64", "instrumented-x86_64"}
NATIVE_ARTIFACT_NAME = "native-artifacts-${{ github.sha }}"
FORBIDDEN_STEP_KEYS = re.compile(r"^\s*(continue-on-error\s*:\s*true|if\s*:)", re.M)


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


def parse_needs(block):
    """Extract the `needs:` set of a job block (scalar, inline list or block list)."""
    m = re.search(r"^    needs[ \t]*:[ \t]*(.*)$", block, re.M)
    if not m:
        return set()
    rest = m.group(1).strip()
    if rest.startswith("["):
        return {x.strip().strip("'\"") for x in rest.strip("[]").split(",") if x.strip()}
    if rest:
        return {rest.strip("'\"")}
    needs = set()
    for line in block[m.end():].splitlines()[1:]:
        lm = re.match(r"^      -\s*(.+?)\s*$", line)
        if lm:
            needs.add(lm.group(1).strip("'\""))
        elif line.strip():
            break
    return needs


def steps_of(block):
    """Split a job block into its step texts (each starting at `- name:`)."""
    parts = re.split(r"^      - (?=name\s*:)", block, flags=re.M)
    return [("- " + s) for s in parts[1:]]


def transitive_needs(job, graph, seen=None):
    seen = set() if seen is None else seen
    for n in graph.get(job, set()):
        if n not in seen:
            seen.add(n)
            transitive_needs(n, graph, seen)
    return seen


def validate_lineage(jobs, errors):
    """F4: enforce the job dependency graph and artifact consumption discipline."""
    graph = {j: parse_needs(b) for j, b in jobs.items()}
    for job, required in REQUIRED_NEEDS.items():
        if job not in jobs:
            continue
        missing = required - graph.get(job, set())
        for n in sorted(missing):
            errors.append(f"lineage: job '{job}' must declare needs: {n}")
        for n in sorted(graph.get(job, set())):
            if n not in jobs:
                errors.append(f"lineage: job '{job}' needs unknown job '{n}'")
    # every consumer must transitively descend from native-build
    for job in sorted(ARTIFACT_CONSUMERS & set(jobs)):
        if "native-build" not in transitive_needs(job, graph):
            errors.append(f"lineage: '{job}' does not descend from native-build")
        block = jobs[job]
        steps = steps_of(block)
        dl_idx = verify_idx = first_consume_idx = None
        for i, s in enumerate(steps):
            if "download-artifact@" in s:
                dl_idx = i if dl_idx is None else dl_idx
                if f"name: {NATIVE_ARTIFACT_NAME}" not in s:
                    errors.append(f"lineage: '{job}' downloads an artifact other than {NATIVE_ARTIFACT_NAME}")
                if not re.search(r"path:\s*build/native\s*$", s, re.M):
                    errors.append(f"lineage: '{job}' does not download the native artifact into build/native")
                if FORBIDDEN_STEP_KEYS.search(s):
                    errors.append(f"lineage: '{job}' artifact download step is conditional/non-fatal")
            if re.search(r"native_build\.py\s+verify\b", s):
                verify_idx = i if verify_idx is None else verify_idx
                if FORBIDDEN_STEP_KEYS.search(s):
                    errors.append(f"lineage: '{job}' verify step is conditional/non-fatal")
            if re.search(r"gradlew[^\n]*(assemble|connected|test|lint)", s) and first_consume_idx is None:
                first_consume_idx = i
                if FORBIDDEN_STEP_KEYS.search(s):
                    errors.append(f"lineage: '{job}' first Gradle consumer step is conditional/non-fatal")
        if dl_idx is None:
            errors.append(f"lineage: '{job}' never downloads the native artifact")
        if verify_idx is None:
            errors.append(f"lineage: '{job}' does not re-verify the downloaded artifact (native_build.py verify)")
        if None not in (dl_idx, verify_idx) and verify_idx < dl_idx:
            errors.append(f"lineage: '{job}' verifies before downloading")
        if None not in (verify_idx, first_consume_idx) and first_consume_idx < verify_idx:
            errors.append(f"lineage: '{job}' consumes the artifact (Gradle) before re-verifying it")
        if None not in (dl_idx, first_consume_idx) and first_consume_idx < dl_idx:
            errors.append(f"lineage: '{job}' runs Gradle before the artifact download")
        # a consumer must never rebuild native artifacts itself
        if re.search(r"native_build\.py\s+build\b|cargo\s+ndk", block):
            errors.append(f"lineage: '{job}' rebuilds native artifacts instead of consuming native-build output")
    # producer must upload exactly the pinned artifact name, fail if empty
    nb = jobs.get("native-build", "")
    if nb:
        up = [s for s in steps_of(nb) if "upload-artifact@" in s]
        if not up or f"name: {NATIVE_ARTIFACT_NAME}" not in up[0]:
            errors.append(f"lineage: native-build must upload artifact {NATIVE_ARTIFACT_NAME}")
        elif "if-no-files-found: error" not in up[0]:
            errors.append("lineage: native-build upload must use if-no-files-found: error")
        order = [
            re.search(r"native_build\.py\s+check-toolchain", nb),
            re.search(r"native_build\.py\s+build\b", nb),
            re.search(r"native_build\.py\s+rebuild-compare", nb),
            re.search(r"native_build\.py\s+verify\b", nb),
        ]
        if all(order) and not (order[0].start() < order[1].start() < order[2].start() < order[3].start()):
            errors.append("lineage: native-build steps must run check-toolchain → build → rebuild-compare → verify")
        m_up = re.search(r"upload-artifact@", nb)
        if all(order) and m_up and m_up.start() < order[3].start():
            errors.append("lineage: native-build uploads the artifact before verifying it")


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
    validate_lineage(jobs, errors)

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
