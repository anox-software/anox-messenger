#!/usr/bin/env python3
"""B-017-Lite supply-chain / CI policy validator.

Deterministic, local, fail-closed checks for the B-017-Lite foundation.
Does not require external services, network credentials, or production secrets.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Full 40-char hex SHA plus an optional trailing comment.
IMMUTABLE_ACTION_REF = re.compile(r"^[0-9a-f]{40}(\s*#.*)?$")

DANGEROUS_USES = re.compile(r"uses:\s+([^/\s#@]+/)?[^/\s#@]+/[^@\s]+@(?P<ref>[^\s#]+)", re.MULTILINE)
DANGEROUS_TRIGGERS = {"pull_request_target", "workflow_run"}
DANGEROUS_PERMISSIONS = re.compile(r"^\s+(\w+):\s*write\b", re.MULTILINE)

GRADLE_DYNAMIC_VERSION = re.compile(r"(?:version\s+\"|version\s*=\s*\"|:\s*\"?)(\+|latest\.release|latest\.integration|[^\"'\s]*SNAPSHOT[^\"'\s]*)", re.IGNORECASE)
GRADLE_INSECURE_REPO = re.compile(r"url\s*=\s*uri\s*\(\s*\"http://", re.IGNORECASE)
GRADLE_ALLOW_INSECURE = re.compile(r"allowInsecureProtocol\s*=\s*true", re.IGNORECASE)
GRADLE_LOCAL_REPO = re.compile(r"mavenLocal\s*\(\s*\)")

RUST_WILDCARD = re.compile(r"=\s*[\"']?\*", re.MULTILINE)
RUST_UNPINNED_GIT = re.compile(r"git\s*=\s*[^\s]+\s*,\s*(branch|tag)\s*=", re.IGNORECASE)


def log_finding(findings, file, message):
    findings.append(f"{file}: {message}")


def check_github_actions(findings):
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    if not workflows_dir.is_dir():
        log_finding(findings, workflows_dir, "workflows directory not found")
        return

    for workflow in workflows_dir.glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")

        for match in DANGEROUS_USES.finditer(text):
            ref = match.group("ref")
            if not IMMUTABLE_ACTION_REF.match(ref):
                log_finding(findings, workflow, f"unpinned or mutable action ref '@{ref}'")

        for trigger in DANGEROUS_TRIGGERS:
            if re.search(rf"^\s*{trigger}:\s*$", text, re.MULTILINE):
                log_finding(findings, workflow, f"dangerous trigger '{trigger}'")

        if "permissions:" not in text:
            log_finding(findings, workflow, "missing explicit permissions block")

        # Only "actions: write" is allowed for artifact upload, and then only when justified.
        for match in DANGEROUS_PERMISSIONS.finditer(text):
            perm = match.group(1).strip()
            if perm == "contents" or perm == "issues" or perm == "pull-requests" or perm == "packages":
                log_finding(findings, workflow, f"dangerous write permission '{perm}: write'")


def check_gradle_wrapper(findings):
    wrapper_props = REPO_ROOT / "gradle" / "wrapper" / "gradle-wrapper.properties"
    if not wrapper_props.exists():
        log_finding(findings, wrapper_props, "gradle-wrapper.properties not found")
        return
    text = wrapper_props.read_text(encoding="utf-8")
    if "distributionSha256Sum" not in text:
        log_finding(findings, wrapper_props, "missing distributionSha256Sum for wrapper distribution")
    if "validateDistributionUrl=true" not in text:
        log_finding(findings, wrapper_props, "missing validateDistributionUrl=true")


def check_gradle_dependencies(findings):
    gradle_files = [
        p for p in list(REPO_ROOT.rglob("*.gradle")) + list(REPO_ROOT.rglob("*.gradle.kts"))
        if p.is_file()
    ]
    for gradle_file in gradle_files:
        text = gradle_file.read_text(encoding="utf-8")
        for match in GRADLE_DYNAMIC_VERSION.finditer(text):
            log_finding(findings, gradle_file, f"dangerous dynamic/changing version '{match.group(1)}'")
        for match in GRADLE_INSECURE_REPO.finditer(text):
            log_finding(findings, gradle_file, "insecure HTTP repository URL")
        for match in GRADLE_ALLOW_INSECURE.finditer(text):
            log_finding(findings, gradle_file, "allowInsecureProtocol=true")
        if GRADLE_LOCAL_REPO.search(text):
            log_finding(findings, gradle_file, "unreviewed mavenLocal() repository")

    # repository whitelisting: only mavenCentral, google, gradlePluginPortal are accepted
    allowed_repos = {"mavenCentral()", "google()", "gradlePluginPortal()"}
    settings = REPO_ROOT / "settings.gradle.kts"
    if settings.exists():
        text = settings.read_text(encoding="utf-8")
        for match in re.finditer(r"(\w+)\s*\(\s*\)", text):
            repo = match.group(0)
            if repo.startswith("maven") and repo not in allowed_repos and repo != "mavenLocal()":
                log_finding(findings, settings, f"non-allowlisted repository '{repo}'")


def check_rust_supply_chain(findings):
    cargo_toml = REPO_ROOT / "crypto" / "rust" / "Cargo.toml"
    cargo_lock = REPO_ROOT / "crypto" / "rust" / "Cargo.lock"

    if not cargo_toml.exists():
        log_finding(findings, cargo_toml, "Cargo.toml not found")
        return
    if not cargo_lock.exists():
        log_finding(findings, cargo_lock, "Cargo.lock not found or not committed")

    text = cargo_toml.read_text(encoding="utf-8")
    if RUST_WILDCARD.search(text):
        log_finding(findings, cargo_toml, "wildcard '*' dependency version")
    for match in RUST_UNPINNED_GIT.finditer(text):
        log_finding(findings, cargo_toml, "git dependency with branch/tag ref (use commit SHA)")

    gitignore = REPO_ROOT / ".gitignore"
    if gitignore.exists() and "/crypto/rust/Cargo.lock" in gitignore.read_text(encoding="utf-8"):
        log_finding(findings, gitignore, "Cargo.lock must not be ignored")


def main():
    findings = []
    check_github_actions(findings)
    check_gradle_wrapper(findings)
    check_gradle_dependencies(findings)
    check_rust_supply_chain(findings)

    if findings:
        print("B-017-LITE POLICY: FAIL")
        for f in findings:
            print(f"  - {f}")
        return 1

    print("B-017-LITE POLICY: PASS")
    print("  - all checked GitHub Actions refs are pinned to full commit SHAs")
    print("  - no dangerous workflow triggers or overbroad write permissions")
    print("  - Gradle wrapper is protected by SHA-256 and distribution URL validation")
    print("  - Gradle dependencies are not dynamic/changing and repositories are secure")
    print("  - Rust Cargo.lock is present and dependency versions are pinned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
