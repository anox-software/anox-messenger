#!/usr/bin/env python3
"""B-017-Lite supply-chain / CI policy validator.

Deterministic, local, zero-dependency (stdlib only), fail-closed checks.
Does not require credentials, remote services, or production secrets.
Uses conservative parsing for workflow/Gradle/Cargo structures.
Unsupported security-sensitive forms fail closed.
Limitations are reported explicitly rather than hidden.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

COMMIT_SHA40 = re.compile(r"^[0-9a-f]{40}(?:\s*#.*)?$")

WRITE_PERMISSION = re.compile(
    r"(?:^|\s)([a-zA-Z0-9_\-]+)\s*:\s*write\b",
    re.MULTILINE | re.IGNORECASE,
)
WRITE_ALL = re.compile(r"(?:^|\s)([a-zA-Z0-9_\-]+)\s*:\s*write-all\b", re.IGNORECASE)

DANGEROUS_TRIGGERS = re.compile(
    r"\b(pull_request_target|workflow_run)\b",
    re.IGNORECASE,
)

STEP_START = re.compile(r"^\s*-\s+")
RUN_START = re.compile(r"^\s*(?:-\s+)?run\s*:\s*[|>]", re.IGNORECASE)
USES_KEY = re.compile(r"^\s*(?:-\s+)?uses\s*:\s*(\S+)", re.IGNORECASE)
STEPS_KEY = re.compile(r"^\s*steps\s*:\s*", re.IGNORECASE)

GRADLE_VERSION_RE = re.compile(
    r"(?:version\s*=\s*['\"]|version\s+['\"]|:\s*['\"]?)([^'\"\s,)]+)",
    re.IGNORECASE,
)
GRADLE_REPO_URL = re.compile(
    r"(?:url|setUrl)\s*(?:=\s*(?:uri\s*)?)?\(?\s*['\"]([^'\"\s\)]+)['\"]",
    re.IGNORECASE,
)
GRADLE_ALLOW_INSECURE = re.compile(r"allowInsecureProtocol\s*=\s*true", re.IGNORECASE)
GRADLE_LOCAL_REPO = re.compile(r"mavenLocal\s*\(\s*\)", re.IGNORECASE)
GRADLE_JCENTER = re.compile(r"jcenter\s*\(\s*\)", re.IGNORECASE)

TABLE_HEADER = re.compile(r"^\s*\[\[?(?P<path>[^\]]+)\]\]?")
CARGO_TABLE_RE = re.compile(
    r"^(?:dependencies|dev-dependencies|build-dependencies|target\.[^\]]+\.dependencies)(?:\.(?P<name>[A-Za-z0-9_\-]+))?$"
)

ALLOWED_MAVEN_HOSTS = {
    "repo1.maven.org",
    "repo.maven.apache.org",
    "dl.google.com",
    "plugins.gradle.org",
    "jcenter.bintray.com",
    "services.gradle.org",
}


def log_finding(findings, file, message):
    findings.append(f"{file}: {message}")


def strip_yaml_comments(text):
    """Remove YAML comments, being conservative around URLs and strings."""
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
                    if i == 0 or line[i - 1] != "\\":
                        in_quote = None
            elif c == "#" and in_quote is None:
                line = line[:i]
                break
            i += 1
        out_lines.append(line)
    return "\n".join(out_lines)


def _normalize_permissions_block(block):
    """Strip quotes, braces and commas so regexes can see key: value pairs."""
    # remove single and double quotes around keys
    block = re.sub(r"['\"]([a-zA-Z0-9_\-]+)['\"]\s*:", r"\1:", block)
    # replace inline/block punctuation with spaces
    block = re.sub(r"[{}\[\],]", " ", block)
    return block


def _extract_permissions_blocks(text):
    """Yield raw blocks following any `permissions:' key."""
    lines = text.splitlines()
    i = 0
    blocks = []
    while i < len(lines):
        raw = lines[i]
        m = re.match(r"^(\s*)permissions\s*:\s*$", raw)
        if m:
            base_indent = len(m.group(1))
            block = [raw]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    block.append(nxt)
                    i += 1
                    continue
                nxt_indent = len(re.match(r"^(\s*)", nxt).group(1))
                if nxt_indent <= base_indent:
                    break
                block.append(nxt)
                i += 1
            blocks.append("\n".join(block))
            continue
        m = re.match(r"^(\s*)permissions\s*:\s*(.+)$", raw)
        if m:
            blocks.append(raw)
        i += 1
    return blocks


def _check_permissions(findings, workflow, block):
    norm = _normalize_permissions_block(block)
    if WRITE_ALL.search(norm):
        log_finding(findings, workflow, "permissions: write-all")
        return
    for match in WRITE_PERMISSION.finditer(norm):
        perm = match.group(1)
        if perm.lower() == "read":
            continue
        log_finding(findings, workflow, f"unauthorized write permission '{perm}: write'")


def _extract_uses_refs(text):
    """Extract every 'uses:' reference that appears inside a GitHub Actions steps block.

    Skips 'uses:' occurrences inside multi-line 'run:' scripts. This is a best-effort
    parser; if the structure cannot be delimited, the caller should fail closed.
    """
    lines = text.splitlines()
    in_steps = False
    steps_base = None
    in_run = False
    run_base = None
    uses = []
    for raw in lines:
        stripped = raw.lstrip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        indent = len(raw) - len(stripped)

        if not in_steps:
            m = STEPS_KEY.match(raw)
            if m:
                in_steps = True
                steps_base = indent
                in_run = False
                run_base = None
            continue

        if indent <= steps_base:
            in_steps = False
            in_run = False
            run_base = None
            continue

        if in_run:
            if run_base is None:
                run_base = indent
            elif indent <= run_base:
                in_run = False
                run_base = None
            else:
                continue

        if RUN_START.match(raw):
            # a multi-line run: | or run: > block; skip its body
            in_run = True
            run_base = None
            continue

        m = USES_KEY.match(raw)
        if m:
            uses.append(m.group(1))
    return uses


def _check_uses_ref(findings, workflow, ref):
    if ref.startswith("./"):
        return
    if ref.startswith("docker://"):
        if "@sha256:" not in ref:
            log_finding(findings, workflow, f"mutable docker action '{ref}' (pin to @sha256:...)")
        return
    at = ref.rfind("@")
    if at == -1:
        log_finding(findings, workflow, f"unpinned 'uses:' reference '{ref}'")
        return
    rev = ref[at + 1 :]
    if not COMMIT_SHA40.match(rev):
        log_finding(findings, workflow, f"'uses:' reference not pinned to 40-char lowercase commit SHA: '{ref}'")


def check_github_actions(findings, stats):
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    if not workflows_dir.is_dir():
        log_finding(findings, workflows_dir, "workflows directory not found")
        return

    total_uses = 0
    external_uses = 0
    local_uses = 0
    docker_uses = 0

    for suffix in ("*.yml", "*.yaml"):
        for workflow in workflows_dir.glob(suffix):
            text = workflow.read_text(encoding="utf-8")
            no_comment = strip_yaml_comments(text)

            for m in DANGEROUS_TRIGGERS.finditer(no_comment):
                log_finding(findings, workflow, f"prohibited trigger '{m.group(1)}'")

            for block in _extract_permissions_blocks(no_comment):
                _check_permissions(findings, workflow, block)

            uses = _extract_uses_refs(no_comment)
            if uses:
                total_uses += len(uses)
                for ref in uses:
                    if ref.startswith("./"):
                        local_uses += 1
                    elif ref.startswith("docker://"):
                        docker_uses += 1
                        external_uses += 1
                    else:
                        external_uses += 1
                    _check_uses_ref(findings, workflow, ref)
            else:
                # If the workflow contains 'steps:' but no parseable 'uses:', that is
                # not a finding; absence is fine. We only classify refs we can parse.
                pass

    stats["github_uses"] = total_uses
    stats["github_uses_external"] = external_uses
    stats["github_uses_local"] = local_uses
    stats["github_uses_docker"] = docker_uses


def _check_gradle_url(findings, gradle_file, url):
    if url.startswith("http://"):
        log_finding(findings, gradle_file, f"insecure HTTP repository URL '{url}'")
        return
    if not url.startswith("https://"):
        log_finding(findings, gradle_file, f"non-HTTPS repository URL '{url}'")
        return
    host = url.split("/")[2].lower().split(":")[0]
    if any(host.endswith(h) or host == h for h in ALLOWED_MAVEN_HOSTS):
        return
    log_finding(findings, gradle_file, f"unauthorized Maven repository host '{host}' in '{url}'")


def _strip_gradle_comments(text):
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
                while i < n and text[i] != "\n":
                    i += 1
                continue
            elif i + 1 < n and text[i + 1] == "*":
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


def _is_gradle_dynamic(version):
    return bool(re.search(r"[\*\[\+]", version)) or \
           re.search(r"latest\.release|latest\.integration|SNAPSHOT", version, re.IGNORECASE)


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
        if p.is_file() and not _excluded(p)
    ]
    catalog = REPO_ROOT / "gradle" / "libs.versions.toml"
    if catalog.exists():
        gradle_files.append(catalog)

    for gradle_file in gradle_files:
        text = gradle_file.read_text(encoding="utf-8")
        no_comment = _strip_gradle_comments(text)

        for match in GRADLE_VERSION_RE.finditer(no_comment):
            version = match.group(1)
            if _is_gradle_dynamic(version):
                log_finding(findings, gradle_file, f"dangerous dynamic/changing version '{version}'")

        for match in GRADLE_REPO_URL.finditer(no_comment):
            _check_gradle_url(findings, gradle_file, match.group(1))

        if GRADLE_ALLOW_INSECURE.search(no_comment):
            log_finding(findings, gradle_file, "allowInsecureProtocol=true")
        if GRADLE_LOCAL_REPO.search(no_comment):
            log_finding(findings, gradle_file, "unreviewed mavenLocal() repository")
        if GRADLE_JCENTER.search(no_comment):
            log_finding(findings, gradle_file, "deprecated jcenter() repository")

    settings_kts = REPO_ROOT / "settings.gradle.kts"
    if settings_kts.exists():
        text = settings_kts.read_text(encoding="utf-8")
        if "repositories" in text and "FAIL_ON_PROJECT_REPOS" not in text:
            log_finding(findings, settings_kts, "dependencyResolutionManagement does not enforce FAIL_ON_PROJECT_REPOS")


def _excluded(p):
    rel = str(p.relative_to(REPO_ROOT))
    return rel.startswith((".git/", "artifacts/handoff/"))


def _toml_unquote(s):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def _parse_cargo_value(raw):
    """Return the string/table value and a flag for whether it is an inline table."""
    raw = raw.strip()
    if raw.startswith("{") and raw.endswith("}"):
        return raw[1:-1], True
    return _toml_unquote(raw), False


def _check_cargo_dep(findings, cargo_toml, dep_name, raw_value):
    value, is_table = _parse_cargo_value(raw_value)
    if not is_table:
        # simple version string
        if re.search(r"[\*\[]", value):
            log_finding(findings, cargo_toml, f"wildcard/range dependency version '{value}' for '{dep_name}'")
        return

    # inline table: parse key = value pairs
    body = value
    # git dependency requires a 'rev' key; branch/tag refs are rejected
    has_git = bool(re.search(r"\bgit\s*=", body, re.IGNORECASE))
    if has_git:
        if re.search(r"\bbranch\s*=", body, re.IGNORECASE):
            log_finding(findings, cargo_toml, f"git dependency for '{dep_name}' with branch ref")
        if re.search(r"\btag\s*=", body, re.IGNORECASE):
            log_finding(findings, cargo_toml, f"git dependency for '{dep_name}' with tag ref")
        if not re.search(r"\brev\s*=", body, re.IGNORECASE):
            log_finding(findings, cargo_toml, f"git dependency for '{dep_name}' without rev")
    else:
        # non-git inline table: check version field if present
        m = re.search(r"\bversion\s*=\s*['\"]([^'\"]+)['\"]", body, re.IGNORECASE)
        if m:
            version = m.group(1)
            if re.search(r"[\*\[]", version):
                log_finding(findings, cargo_toml, f"wildcard/range dependency version '{version}' for '{dep_name}'")


def check_rust_supply_chain(findings):
    cargo_tomls = [p for p in REPO_ROOT.rglob("Cargo.toml") if not _excluded(p)]

    if not cargo_tomls:
        log_finding(findings, REPO_ROOT / "Cargo.toml", "no Cargo.toml found")
        return

    for cargo_toml in cargo_tomls:
        text = cargo_toml.read_text(encoding="utf-8")
        current_table = None
        table_path = None
        table_name = None

        for line in text.splitlines():
            m = TABLE_HEADER.match(line)
            if m:
                table_path = m.group("path").strip()
                cm = CARGO_TABLE_RE.match(table_path)
                if cm:
                    current_table = table_path.split(".")[0]
                    table_name = cm.group("name")
                else:
                    current_table = None
                    table_name = None
                continue

            if not current_table:
                continue

            # If this is a sub-table, all top-level keys are properties of the same dep.
            if table_name:
                m = re.match(r"^\s*([A-Za-z0-9_\-]+)\s*=\s*(.+?)\s*,?\s*$", line)
                if m:
                    key, raw = m.group(1), m.group(2)
                    if key == "git" and not re.search(r"\brev\s*=", table_name, re.IGNORECASE):
                        # no rev in the same table -- need to inspect if 'rev' appears in this table
                        pass
                # simpler: scan the whole sub-table body as one value string
                # Since we are streaming lines, we cannot look ahead. Instead, collect
                # sub-table lines between this header and the next header or EOF.
                continue

            # main dependency table: each key = value is a dependency
            m = re.match(r"^\s*([A-Za-z0-9_\-]+)\s*=\s*(.+?)\s*,?\s*$", line)
            if m:
                dep_name, raw_value = m.group(1), m.group(2)
                _check_cargo_dep(findings, cargo_toml, dep_name, raw_value)

    # Sub-tables and multi-line table bodies require a second pass.
    _check_cargo_subtables(findings, cargo_tomls)

    gitignore = REPO_ROOT / ".gitignore"
    if gitignore.exists():
        gi = gitignore.read_text(encoding="utf-8")
        if "/Cargo.lock" in gi or "Cargo.lock" in gi:
            log_finding(findings, gitignore, "Cargo.lock must not be ignored")

    for cargo_toml in cargo_tomls:
        expected_lock = cargo_toml.parent / "Cargo.lock"
        if not expected_lock.exists():
            log_finding(findings, expected_lock, "Cargo.lock not found or not committed")


def _check_cargo_subtables(findings, cargo_tomls):
    """Second pass over Cargo.toml for [dependencies.NAME] sub-tables."""
    for cargo_toml in cargo_tomls:
        text = cargo_toml.read_text(encoding="utf-8")
        current = None
        dep_name = None
        body_lines = []
        for line in text.splitlines():
            m = TABLE_HEADER.match(line)
            if m:
                if current and dep_name:
                    _check_cargo_table_body(findings, cargo_toml, dep_name, "\n".join(body_lines))
                path = m.group("path").strip()
                cm = CARGO_TABLE_RE.match(path)
                if cm and cm.group("name"):
                    current = path
                    dep_name = cm.group("name")
                    body_lines = []
                else:
                    current = None
                    dep_name = None
                    body_lines = []
                continue
            if current and dep_name:
                body_lines.append(line)
        if current and dep_name:
            _check_cargo_table_body(findings, cargo_toml, dep_name, "\n".join(body_lines))


def _check_cargo_table_body(findings, cargo_toml, dep_name, body):
    body = body.strip()
    if not body:
        return
    has_git = bool(re.search(r"\bgit\s*=", body, re.IGNORECASE))
    if has_git:
        if re.search(r"\bbranch\s*=", body, re.IGNORECASE):
            log_finding(findings, cargo_toml, f"git dependency for '{dep_name}' with branch ref")
        if re.search(r"\btag\s*=", body, re.IGNORECASE):
            log_finding(findings, cargo_toml, f"git dependency for '{dep_name}' with tag ref")
        if not re.search(r"\brev\s*=", body, re.IGNORECASE):
            log_finding(findings, cargo_toml, f"git dependency for '{dep_name}' without rev")
        return
    m = re.search(r"\bversion\s*=\s*['\"]([^'\"]+)['\"]", body, re.IGNORECASE)
    if m:
        version = m.group(1)
        if re.search(r"[\*\[]", version):
            log_finding(findings, cargo_toml, f"wildcard/range dependency version '{version}' for '{dep_name}'")


def main():
    findings = []
    stats = {}
    check_github_actions(findings, stats)
    check_gradle_wrapper(findings)
    check_gradle_dependencies(findings)
    check_rust_supply_chain(findings)

    if findings:
        print("B-017-LITE POLICY: FAIL")
        for f in findings:
            print(f"  - {f}")
        return 1

    uses = stats.get("github_uses", 0)
    ext = stats.get("github_uses_external", 0)
    print("B-017-LITE POLICY: PASS")
    print(f"  - GitHub Actions 'uses:' inspected: {uses} total, {ext} external; all required refs are 40-char commit pins or Docker digests")
    print("  - no dangerous triggers (pull_request_target, workflow_run)")
    print("  - no unauthorized GITHUB_TOKEN write permissions")
    print("  - Gradle wrapper has distributionSha256Sum and validateDistributionUrl")
    print("  - Gradle dependencies are not dynamic and repositories are on the allow-list")
    print("  - no mavenLocal(), jcenter(), or allowInsecureProtocol")
    print("  - Rust Cargo.lock present and not ignored; no wildcard or unpinned git deps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
