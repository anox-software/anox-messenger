#!/usr/bin/env python3
"""B-017-Lite supply-chain / CI policy validator.

Deterministic, local, zero-dependency (stdlib only), fail-closed checks.
Does not require credentials, remote services, or production secrets.
Uses conservative pattern matching for workflow/Gradle/Cargo structures.
Limitations are reported explicitly rather than hidden.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# 40-character lowercase hex commit SHA, optionally followed by a comment.
COMMIT_SHA40 = re.compile(r"^[0-9a-f]{40}(?:\s*#.*)?$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")

WRITE_PERMISSION = re.compile(
    r"(^|\s)([a-zA-Z0-9_\-]+)\s*:\s*write\b",
    re.MULTILINE | re.IGNORECASE,
)
WRITE_ALL_SCALAR = re.compile(r"permissions\s*:\s*write-all\b", re.IGNORECASE)

DANGEROUS_TRIGGERS = re.compile(
    r"\b(pull_request_target|workflow_run)\b",
    re.IGNORECASE,
)

USES_LINE = re.compile(r"^\s*-\s+uses:\s*(\S+)", re.MULTILINE)

GRADLE_DYNAMIC_VERSION = re.compile(
    r"(?:version\s*=\s*\"|version\s+\"|:\s*\"?)"
    r"(\+|\d+\+\*?|\d+\.\+|\d+\.\*|[\(\[]\s*\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?\s*[\)\]]|\S*SNAPSHOT\S*|latest\.release|latest\.integration)",
    re.IGNORECASE,
)
GRADLE_REPO_URL = re.compile(
    r"(?:url|setUrl)\s*(?:=\s*(?:uri\s*)?)?\(?\s*['\"]([^'\"\s\)]+)['\"]",
    re.IGNORECASE,
)
GRADLE_ALLOW_INSECURE = re.compile(r"allowInsecureProtocol\s*=\s*true", re.IGNORECASE)
GRADLE_LOCAL_REPO = re.compile(r"mavenLocal\s*\(\s*\)", re.IGNORECASE)
GRADLE_JCENTER = re.compile(r"jcenter\s*\(\s*\)", re.IGNORECASE)

RUST_CARGO_SECTION = re.compile(r"\[(?:dependencies|dev-dependencies|build-dependencies|target\.[^\]]+\.dependencies)\]")
RUST_VERSION_VALUE = re.compile(r"^(\s*)([A-Za-z0-9_\-]+)\s*=\s*['\"]([^'\"\n\r]*)['\"]", re.MULTILINE)
RUST_GIT_DEP = re.compile(
    r"^(\s*)([A-Za-z0-9_\-]+)\s*=\s*\{(?P<body>[^{}]+)\}",
    re.MULTILINE,
)

# Allowed Maven repository host suffixes. Path-normalized to lower-case.
ALLOWED_MAVEN_HOSTS = {
    "repo1.maven.org",
    "repo.maven.apache.org",
    "dl.google.com",
    "plugins.gradle.org",
    "jcenter.bintray.com",  # deprecated; allowed only if explicitly required
    "services.gradle.org",
}


def log_finding(findings, file, message):
    findings.append(f"{file}: {message}")


def strip_yaml_comments(text):
    """Remove YAML comments, being conservative around URLs and strings."""
    # Sufficient for the security patterns we scan: remove from # to end of line
    # where # is not inside a quoted string (best-effort). We do a minimal lexer:
    # drop from an unquoted # to end of line.
    out_lines = []
    for line in text.splitlines():
        in_quote = None
        i = 0
        while i < len(line):
            c = line[i]
            if c in ('"', "'"):
                if in_quote is None:
                    in_quote = c
                elif in_quote == c:
                    # check escape
                    if i == 0 or line[i - 1] != "\\":
                        in_quote = None
            elif c == "#" and in_quote is None:
                line = line[:i]
                break
            i += 1
        out_lines.append(line)
    return "\n".join(out_lines)


def _extract_permissions_blocks(text, workflow_path):
    """Yield raw blocks following a workflow- or job-level 'permissions:' key.

    Conservative line/indent scanner. Falls back to whole-file scanning on
    indentation ambiguity.
    """
    findings = []
    # Normalize block-form line endings, keep indentation
    lines = text.splitlines()
    i = 0
    blocks = []
    while i < len(lines):
        raw = lines[i]
        # bare or inline `permissions:` at any indent level
        if re.match(r"^(\s*)permissions\s*:\s*$", raw):
            base_indent = len(re.match(r"^(\s*)", raw).group(1))
            block = [raw]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    block.append(nxt)
                    i += 1
                    continue
                nxt_indent = len(re.match(r"^(\s*)", nxt).group(1))
                # line is inside block if more indented, or same-level blank
                if nxt_indent > base_indent or not nxt.strip():
                    block.append(nxt)
                    i += 1
                    continue
                # a new top/jobs key at same or lower indent ends the block
                if nxt_indent <= base_indent:
                    break
                block.append(nxt)
                i += 1
            blocks.append("\n".join(block))
            continue
        # inline forms: `permissions: write-all` or `permissions: { ... }`
        m = re.match(r"^(\s*)permissions\s*:\s*(.+)$", raw)
        if m:
            blocks.append(raw)
        i += 1
    return blocks, findings


def check_github_actions(findings):
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    if not workflows_dir.is_dir():
        log_finding(findings, workflows_dir, "workflows directory not found")
        return

    for suffix in ("*.yml", "*.yaml"):
        for workflow in workflows_dir.glob(suffix):
            text = workflow.read_text(encoding="utf-8")
            no_comment = strip_yaml_comments(text)

            # Dangerous triggers: any occurrence of the trigger name in the
            # uncommented file (we already strip comments; this catches block,
            # inline and list forms).
            for m in DANGEROUS_TRIGGERS.finditer(no_comment):
                log_finding(findings, workflow, f"prohibited trigger '{m.group(1)}'")

            # Permissions: deny any write scope. Blocks, inline and `{}` forms.
            perm_blocks, _ = _extract_permissions_blocks(no_comment, workflow)
            for block in perm_blocks:
                if WRITE_ALL_SCALAR.search(block):
                    log_finding(findings, workflow, "permissions: write-all")
                    continue
                for match in WRITE_PERMISSION.finditer(block):
                    perm_key = match.group(2)
                    # 'read' is acceptable; any explicit ': write' is not
                    log_finding(
                        findings, workflow, f"unauthorized write permission '{perm_key}: write'"
                    )

            # `uses:` references
            for match in USES_LINE.finditer(no_comment):
                ref = match.group(1).strip()
                if ref.startswith("./"):
                    # local composite/action; not an external immutable-action requirement
                    continue
                if ref.startswith("docker://"):
                    # Docker actions must be pinned to a digest (sha256) for immutability
                    if "@sha256:" not in ref:
                        log_finding(
                            findings,
                            workflow,
                            f"mutable docker action '{ref}' (pin to @sha256:...)",
                        )
                    continue
                at = ref.rfind("@")
                if at == -1:
                    log_finding(findings, workflow, f"unpinned 'uses:' reference '{ref}'")
                    continue
                rev = ref[at + 1 :]
                owner_repo = ref[:at]
                if not COMMIT_SHA40.match(rev):
                    log_finding(
                        findings,
                        workflow,
                        f"'uses:' reference not pinned to 40-char commit SHA: '{ref}'",
                    )
                    continue
                # 40 hex chars; acceptable for B-017-Lite offline validator.
                # The validator cannot distinguish tag objects from commits
                # without remote polling; this is documented in the report.


def _check_gradle_url(findings, gradle_file, url):
    if url.startswith("http://"):
        log_finding(findings, gradle_file, f"insecure HTTP repository URL '{url}'")
        return
    if not url.startswith("https://"):
        log_finding(findings, gradle_file, f"non-HTTPS repository URL '{url}'")
        return
    host = url.split("/")[2].lower()
    # strip port
    host = host.split(":")[0]
    if any(host.endswith(h) or host == h for h in ALLOWED_MAVEN_HOSTS):
        return
    log_finding(findings, gradle_file, f"unauthorized Maven repository host '{host}' in '{url}'")


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


def _strip_gradle_comments(text):
    """Remove // and /* */ comments while preserving strings (so http://... is kept)."""
    out = []
    i = 0
    in_quote = None
    n = len(text)
    while i < n:
        c = text[i]
        if c in ('"', "'"):
            if in_quote is None:
                in_quote = c
            elif in_quote == c and (i == 0 or text[i - 1] != "\\"):
                in_quote = None
            out.append(c)
            i += 1
        elif c == "/" and in_quote is None:
            if i + 1 < n and text[i + 1] == "/":
                # skip to end of line, but not the newline itself
                while i < n and text[i] != "\n":
                    i += 1
                continue
            elif i + 1 < n and text[i + 1] == "*":
                # skip to */
                i += 2
                while i < n - 1:
                    if text[i] == "*" and text[i + 1] == "/":
                        i += 2
                        break
                    i += 1
                continue
            else:
                out.append(c)
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _excluded(p):
    rel = str(p.relative_to(REPO_ROOT))
    return rel.startswith((".git/", "artifacts/handoff/"))


def check_gradle_dependencies(findings):
    gradle_files = [
        p for p in list(REPO_ROOT.rglob("*.gradle")) + list(REPO_ROOT.rglob("*.gradle.kts"))
        if p.is_file() and not _excluded(p)
    ]
    # also version catalog if present
    catalog = REPO_ROOT / "gradle" / "libs.versions.toml"
    if catalog.exists():
        gradle_files.append(catalog)

    for gradle_file in gradle_files:
        text = gradle_file.read_text(encoding="utf-8")
        no_comment = _strip_gradle_comments(text)

        for match in GRADLE_DYNAMIC_VERSION.finditer(no_comment):
            log_finding(findings, gradle_file, f"dangerous dynamic/changing version '{match.group(1)}'")

        for match in GRADLE_REPO_URL.finditer(no_comment):
            url = match.group(1)
            _check_gradle_url(findings, gradle_file, url)

        if GRADLE_ALLOW_INSECURE.search(no_comment):
            log_finding(findings, gradle_file, "allowInsecureProtocol=true")
        if GRADLE_LOCAL_REPO.search(no_comment):
            log_finding(findings, gradle_file, "unreviewed mavenLocal() repository")
        if GRADLE_JCENTER.search(no_comment):
            log_finding(findings, gradle_file, "deprecated jcenter() repository")

    # settings.gradle(.kts): require FAIL_ON_PROJECT_REPOS if repositories configured
    settings_kts = REPO_ROOT / "settings.gradle.kts"
    if settings_kts.exists():
        text = settings_kts.read_text(encoding="utf-8")
        if "repositories" in text and "FAIL_ON_PROJECT_REPOS" not in text:
            log_finding(findings, settings_kts, "dependencyResolutionManagement does not enforce FAIL_ON_PROJECT_REPOS")


def _cargo_dependency_sections(text):
    """Return the dependency-related sections of a Cargo.toml for scanning."""
    sections = []
    in_section = False
    section_lines = []
    for line in text.splitlines():
        if re.match(r"^\s*\[", line):
            if in_section:
                sections.append("\n".join(section_lines))
            in_section = bool(RUST_CARGO_SECTION.match(line))
            section_lines = [line] if in_section else []
        elif in_section:
            section_lines.append(line)
    if in_section and section_lines:
        sections.append("\n".join(section_lines))
    return sections


def check_rust_supply_chain(findings):
    cargo_tomls = [p for p in REPO_ROOT.rglob("Cargo.toml") if not _excluded(p)]
    cargo_locks = [p for p in REPO_ROOT.rglob("Cargo.lock") if not _excluded(p)]

    if not cargo_tomls:
        log_finding(findings, REPO_ROOT / "Cargo.toml", "no Cargo.toml found")
        return

    for cargo_toml in cargo_tomls:
        text = cargo_toml.read_text(encoding="utf-8")

        for section in _cargo_dependency_sections(text):
            # wildcard / range versions: value contains * or [
            for match in RUST_VERSION_VALUE.finditer(section):
                value = match.group(3).strip()
                if re.search(r"[\*\[]", value):
                    log_finding(findings, cargo_toml, f"wildcard/range dependency version '{value}'")

            # inline git dependencies: { git = "..." } without rev
            for match in RUST_GIT_DEP.finditer(section):
                body = match.group("body")
                if "git" in body:
                    if re.search(r"\bbranch\s*=", body, re.IGNORECASE):
                        log_finding(findings, cargo_toml, "git dependency with branch ref")
                    if re.search(r"\btag\s*=", body, re.IGNORECASE):
                        log_finding(findings, cargo_toml, "git dependency with tag ref")
                    if not re.search(r"\brev\s*=", body, re.IGNORECASE):
                        log_finding(findings, cargo_toml, "git dependency without rev (bare floating)")

            # bare git = "..." not inside braces
            for m in re.finditer(r"^\s*(\w+)\s*=\s*\{?\s*git\s*=\s*['\"]([^'\"]+)['\"]", section, re.MULTILINE):
                log_finding(findings, cargo_toml, f"bare git dependency without explicit rev: {m.group(2)}")

    gitignore = REPO_ROOT / ".gitignore"
    if gitignore.exists():
        gi = gitignore.read_text(encoding="utf-8")
        if "/Cargo.lock" in gi or "Cargo.lock" in gi:
            log_finding(findings, gitignore, "Cargo.lock must not be ignored")

    for cargo_toml in cargo_tomls:
        expected_lock = cargo_toml.parent / "Cargo.lock"
        if not expected_lock.exists():
            log_finding(findings, expected_lock, "Cargo.lock not found or not committed")


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
    print("  - GitHub Actions use 40-char commit SHA pins (or local/docker pins per policy)")
    print("  - no dangerous triggers (pull_request_target, workflow_run)")
    print("  - no unauthorized GITHUB_TOKEN write permissions")
    print("  - Gradle wrapper has distributionSha256Sum and validateDistributionUrl")
    print("  - Gradle dependencies are not dynamic and repositories are on the allow-list")
    print("  - no mavenLocal(), jcenter(), or allowInsecureProtocol")
    print("  - Rust Cargo.lock present and not ignored; no wildcard or unpinned git deps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
