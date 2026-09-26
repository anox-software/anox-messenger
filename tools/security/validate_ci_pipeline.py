#!/usr/bin/env python3
"""Structural + EXECUTION-SEMANTIC fail-closed gate for the S1 CI pipeline
(MSC-001/002/003/038).

The workflow is parsed into a structure (strict YAML subset, stdlib only) and
every mandatory job / gate is checked for BOTH presence and mandatoriness:

  * required jobs exist, carry no job-level ``if`` (``if: false`` and every
    other static or dynamic disabling condition), no job-level
    ``continue-on-error``, and run on the required GitHub-HOSTED runner class
    (public repository: ``[self-hosted, macOS, ARM64]`` routing is prohibited);
  * every required security step (policy gates, secret scan, B-021 gate,
    cargo audit, producer check-toolchain/build/rebuild-compare/verify,
    artifact download, consumer re-verify, Gradle lint/test/assemble/
    connected, APK<->manifest binding) exists, has no ``if``, no
    ``continue-on-error``, and its shell body cannot mask the exit status
    (``||``, ``;`` chaining, ``set +e``, ``exit 0``, trailing ``true``/``:``),
    and its matcher must hit an EXECUTABLE command position — a quoted,
    commented, condition-masked, backgrounded or no-op-argument occurrence
    (``echo``/``printf``/``:``/``true`` prefixes, heredoc bodies) does not
    count, and ``uses:`` matchers only inspect the ``uses`` field;
  * the artifact lineage graph is enforced: ``needs`` edges, consumers
    descend from ``native-build``, download exactly the uploaded artifact
    into ``build/native``, re-verify before the first Gradle step, never
    rebuild native code; the producer uploads only after verify with
    ``if-no-files-found: error``.

Parsing is fail-closed: any construct outside the supported subset (anchors,
aliases, tags, flow mappings, multi-document streams, tabs, duplicate keys)
makes the validator FAIL rather than guess. No substring-presence check is
sufficient on its own.
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ".github/workflows/ci.yml"


# ==========================================================================
# strict YAML subset parser (block mappings / sequences / scalars / block
# scalars / flat flow sequences). Everything else is an error.
# ==========================================================================

class YamlSubsetError(ValueError):
    pass


_DOC_MARKER = re.compile(r"^(---|\.\.\.)(\s|$)")


def _strip_inline_comment(s):
    """Remove ` #...` outside quotes from a plain scalar / line remainder."""
    q = None
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
        elif ch in ("'", '"'):
            q = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
    return s.rstrip()


def _split_key(content):
    """Return (key, rest) if `content` is `key: rest` / `key:`, else None."""
    q = None
    for i, ch in enumerate(content):
        if q:
            if ch == q:
                q = None
        elif ch in ("'", '"') and i == 0:
            q = ch
        elif ch == ":" and (i + 1 == len(content) or content[i + 1] in " \t"):
            key = content[:i].strip()
            if not key:
                return None
            if key[0] in ("'", '"'):
                key = key[1:-1]
            return key, content[i + 1:].strip()
    return None


def _parse_scalar(raw, line_no):
    s = raw.strip()
    if s == "":
        return None
    if s[0] in ("&", "*", "!", "{", "%", "@", "`"):
        raise YamlSubsetError(f"line {line_no}: unsupported YAML construct starting with {s[0]!r}")
    if s[0] == "'":
        if not (len(s) >= 2 and s.endswith("'")) or _strip_inline_comment(s) != s:
            # allow trailing comment after closing quote
            body = _strip_inline_comment(s)
            if not body.endswith("'"):
                raise YamlSubsetError(f"line {line_no}: unterminated single-quoted scalar")
            s = body
        return s[1:-1].replace("''", "'")
    if s[0] == '"':
        body = _strip_inline_comment(s)
        if len(body) < 2 or not body.endswith('"'):
            raise YamlSubsetError(f"line {line_no}: unterminated double-quoted scalar")
        inner = body[1:-1]
        return re.sub(r'\\(["\\/nt])', lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), inner)
    s = _strip_inline_comment(s)
    if s.startswith("["):
        if not s.endswith("]"):
            raise YamlSubsetError(f"line {line_no}: unterminated flow sequence")
        inner = s[1:-1].strip()
        if "[" in inner or "{" in inner:
            raise YamlSubsetError(f"line {line_no}: nested flow collections unsupported")
        return [_parse_scalar(x, line_no) for x in inner.split(",") if x.strip()] if inner else []
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if s in ("null", "Null", "NULL", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


class _Parser:
    def __init__(self, text):
        self.lines = []  # (line_no, indent, content, raw)
        raw_lines = text.split("\n")
        if any("\t" in (l[: len(l) - len(l.lstrip(" \t"))]) for l in raw_lines):
            raise YamlSubsetError("tab character in indentation")
        for i, raw in enumerate(raw_lines, 1):
            if _DOC_MARKER.match(raw):
                raise YamlSubsetError(f"line {i}: multi-document stream / document marker unsupported")
            stripped = raw.strip()
            indent = len(raw) - len(raw.lstrip(" "))
            self.lines.append((i, indent, raw[indent:].rstrip("\r"), raw))
        self.pos = 0

    def _skip_blank(self):
        while self.pos < len(self.lines):
            _, _, content, _ = self.lines[self.pos]
            if content.strip() == "" or content.lstrip().startswith("#"):
                self.pos += 1
            else:
                break

    def parse(self):
        self._skip_blank()
        if self.pos >= len(self.lines):
            return None
        value = self._block(self.lines[self.pos][1])
        self._skip_blank()
        if self.pos < len(self.lines):
            ln, ind, content, _ = self.lines[self.pos]
            raise YamlSubsetError(f"line {ln}: unexpected content at indent {ind}: {content[:40]!r}")
        return value

    def _block(self, indent):
        self._skip_blank()
        ln, ind, content, _ = self.lines[self.pos]
        if ind != indent:
            raise YamlSubsetError(f"line {ln}: bad indentation ({ind} != {indent})")
        if content == "-" or content.startswith("- "):
            return self._sequence(indent)
        return self._mapping(indent)

    def _mapping(self, indent):
        out = {}
        while True:
            self._skip_blank()
            if self.pos >= len(self.lines):
                return out
            ln, ind, content, _ = self.lines[self.pos]
            if ind < indent:
                return out
            if ind > indent:
                raise YamlSubsetError(f"line {ln}: unexpected deeper indentation")
            if content == "-" or content.startswith("- "):
                raise YamlSubsetError(f"line {ln}: sequence item inside mapping")
            kv = _split_key(content)
            if kv is None:
                raise YamlSubsetError(f"line {ln}: expected `key:` mapping entry, got {content[:40]!r}")
            key, rest = kv
            if key == "<<":
                raise YamlSubsetError(f"line {ln}: merge keys unsupported")
            if key in out:
                raise YamlSubsetError(f"line {ln}: duplicate key {key!r}")
            self.pos += 1
            out[key] = self._value(rest, indent, ln)

    def _sequence(self, indent):
        out = []
        while True:
            self._skip_blank()
            if self.pos >= len(self.lines):
                return out
            ln, ind, content, _ = self.lines[self.pos]
            if ind < indent:
                return out
            if ind > indent:
                raise YamlSubsetError(f"line {ln}: unexpected deeper indentation in sequence")
            if not (content == "-" or content.startswith("- ")):
                return out
            item = content[1:].strip()
            if item == "":
                self.pos += 1
                self._skip_blank()
                if self.pos < len(self.lines) and self.lines[self.pos][1] > indent:
                    out.append(self._block(self.lines[self.pos][1]))
                else:
                    out.append(None)
                continue
            kv = _split_key(item)
            if kv is not None and not item.startswith(("'", '"', "[")):
                # inline mapping start: re-anchor this line at the key column
                key_col = indent + 1 + (len(content[1:]) - len(content[1:].lstrip()))
                self.lines[self.pos] = (ln, key_col, item, self.lines[self.pos][3])
                out.append(self._mapping(key_col))
                continue
            self.pos += 1
            out.append(self._value(item, indent, ln, allow_block=False))

    def _value(self, rest, indent, ln, allow_block=True):
        m = re.fullmatch(r"([|>])([+-]?)(\d?)(?:\s+#.*)?", rest or "")
        if m:
            return self._block_scalar(m.group(1), m.group(2), indent, ln)
        if rest == "" or rest.startswith("#"):
            self._skip_blank()
            if self.pos < len(self.lines) and self.lines[self.pos][1] > indent:
                return self._block(self.lines[self.pos][1])
            if allow_block and self.pos < len(self.lines) and self.lines[self.pos][1] == indent \
                    and (self.lines[self.pos][2] == "-" or self.lines[self.pos][2].startswith("- ")):
                return self._sequence(indent)
            return None
        return _parse_scalar(rest, ln)

    def _block_scalar(self, style, chomp, indent, ln):
        body = []
        block_indent = None
        while self.pos < len(self.lines):
            _, ind, content, raw = self.lines[self.pos]
            if content.strip() == "":
                body.append("")
                self.pos += 1
                continue
            if ind <= indent:
                break
            if block_indent is None:
                block_indent = ind
            if ind < block_indent:
                raise YamlSubsetError(f"line {self.lines[self.pos][0]}: block scalar dedent below first line")
            body.append(raw[block_indent:].rstrip("\r"))
            self.pos += 1
        while body and body[-1] == "":
            body.pop()
        if style == "|":
            text = "\n".join(body)
        else:
            folded, para = [], []
            for line in body:
                if line == "":
                    folded.append(" ".join(para))
                    para = []
                else:
                    para.append(line.strip())
            folded.append(" ".join(para))
            text = "\n".join(folded)
        if chomp == "-":
            return text
        return text + "\n" if text else text


def parse_workflow(text):
    return _Parser(text).parse()


# ==========================================================================
# policy model
# ==========================================================================

REQUIRED_JOBS = {
    "supply-chain-policy", "gradle-wrapper-validation", "rust", "native-build",
    "android-debug", "android-release", "instrumented-arm64", "instrumented-x86_64",
}

# job -> set of jobs that MUST appear in its `needs:` (direct edges).
REQUIRED_NEEDS = {
    "rust": {"supply-chain-policy"},
    "gradle-wrapper-validation": {"supply-chain-policy"},
    "native-build": {"rust", "gradle-wrapper-validation"},
    "android-debug": {"native-build"},
    "android-release": {"native-build", "android-debug"},
    "instrumented-arm64": {"native-build", "android-debug"},
    "instrumented-x86_64": {"native-build", "android-debug"},
}
ARTIFACT_CONSUMERS = {"android-debug", "android-release", "instrumented-arm64", "instrumented-x86_64"}
NATIVE_ARTIFACT_NAME = "native-artifacts-${{ github.sha }}"

# Runner policy (public repository): required jobs run on GitHub-hosted
# runners only. The arm64 instrumented job needs an Apple-silicon hosted
# runner; everything else runs on hosted Ubuntu.
HOSTED_UBUNTU = re.compile(r"^ubuntu-(latest|\d{2}\.\d{2})$")
HOSTED_MACOS_ARM64 = re.compile(r"^macos-(latest|1[4-9]|[2-9]\d)(-xlarge|-large)?$")
RUNNER_POLICY = {j: HOSTED_UBUNTU for j in REQUIRED_JOBS}
RUNNER_POLICY["instrumented-arm64"] = HOSTED_MACOS_ARM64

def _rx(p):
    return re.compile(p)


# Required security steps: (label, job, kind, matcher).
# Every matched step is MANDATORY: no `if`, no `continue-on-error`, no shell
# masking. `job=None` means: must exist somewhere, and wherever it exists it
# is mandatory.
#
# kind "uses": the matcher must appear in the step's `uses:` field (an action
#   reference can only be satisfied by the field that selects the action — a
#   `run: echo actions/download-artifact@x` decoy does not count).
# kind "run": the matcher must match at an EXECUTABLE command position in the
#   step's `run:` shell body — it must head a simple command whose exit status
#   reaches the step result. Arguments of no-op commands (`echo`, `printf`,
#   `:`, `true`, ...), comments, quoted literals, `if`/`while`/`until`/`!`
#   conditions, backgrounded (`&`), piped-away (`| tee`) or `||`-RHS
#   occurrences, and heredoc bodies do NOT satisfy a mandatory step.
# kind "run-any": same executable-position requirement, but a status-masked
#   position (condition / non-final pipeline element) still counts — used only
#   for content markers (e.g. a file being read by grep|sed) where the real
#   assertion lives in a separate `test` command.
#
# Canonical executable heads used below: `python3`, `cargo`, `./gradlew`,
# and file-reader commands for the toolchain-pin marker.

_PY = r"python3\s+"
_NB = _PY + r"tools/security/native_build\.py\s+"
_GR = r"(?:\./)?gradlew\b[^\n;&|(){}]*"
# the remainder of a mandatory command may not cross a command separator —
# otherwise `cmd1 && echo --flag` could lend flags to a decoy tail
_RX_APK = _rx(_PY + r"tools/security/validate_apk_contents\.py[^\n;&|(){}]*--native-manifest\b")
RX_NB = {
    "check-toolchain": _rx(_NB + r"check-toolchain\b"),
    "build": _rx(_NB + r"build\b"),
    "rebuild-compare": _rx(_NB + r"rebuild-compare\b"),
    "verify": _rx(_NB + r"verify\b"),
}
_RX_GRADLE_CONSUME = _rx(_GR + r"(?:assemble|connected|test|lint)")

REQUIRED_STEPS = [
    ("policy gate: b017-lite validator", "supply-chain-policy", "run", _rx(_PY + r"tools/security/b017_lite_policy_validator\.py")),
    ("policy gate: CI pipeline structure", "supply-chain-policy", "run", _rx(_PY + r"tools/security/validate_ci_pipeline\.py")),
    ("policy gate: S1 provenance static gate", "supply-chain-policy", "run", _rx(_PY + r"tools/audit/validate_s1_build_provenance\.py")),
    ("policy gate: secret scan", "supply-chain-policy", "run", _rx(_PY + r"tools/security/secret_scan\.py")),
    ("policy gate: B-021 matrix validator", "supply-chain-policy", "run", _rx(_PY + r"tools/audit/validate_b021_verification_matrix\.py")),
    ("policy gate: cargo audit advisory scan", "supply-chain-policy", "run", _rx(r"cargo\s+audit\b")),
    ("gradle wrapper validation action", "gradle-wrapper-validation", "uses", _rx(r"gradle/actions/wrapper-validation@")),
    ("rust job: toolchain pin assertion", "rust", "run-any", _rx(r"(?:grep|sed|awk|cat|rg)\b[^\n;&|(){}]*rust-toolchain\.toml")),
    ("rust job: locked tests", "rust", "run", _rx(r"cargo\s+test\b[^\n;&|(){}]*--locked\b")),
    ("native-build: toolchain assertion", "native-build", "run", RX_NB["check-toolchain"]),
    ("native-build: authoritative build step", "native-build", "run", RX_NB["build"]),
    ("native-build: reproducibility (two clean builds)", "native-build", "run", RX_NB["rebuild-compare"]),
    ("native-build: artifact verify", "native-build", "run", RX_NB["verify"]),
    ("native-build: artifact upload", "native-build", "uses", _rx(r"actions/upload-artifact@")),
    ("android-debug: downloads native artifacts", "android-debug", "uses", _rx(r"actions/download-artifact@")),
    ("android-debug: re-verify", "android-debug", "run", RX_NB["verify"]),
    ("android-debug: JVM unit tests", "android-debug", "run", _rx(_GR + r"testDebugUnitTest\b")),
    ("android-debug: lint gate", "android-debug", "run", _rx(_GR + r"lintDebug\b")),
    ("android-debug: assemble", "android-debug", "run", _rx(_GR + r"assembleDebug\b")),
    ("android-debug: APK provenance binding", "android-debug", "run", _RX_APK),
    ("android-release: downloads native artifacts", "android-release", "uses", _rx(r"actions/download-artifact@")),
    ("android-release: re-verify", "android-release", "run", RX_NB["verify"]),
    ("android-release: assemble", "android-release", "run", _rx(_GR + r"assembleRelease\b")),
    ("android-release: APK provenance binding", "android-release", "run", _RX_APK),
    ("instrumented arm64: consumes native artifacts", "instrumented-arm64", "uses", _rx(r"actions/download-artifact@")),
    ("instrumented arm64: re-verify", "instrumented-arm64", "run", RX_NB["verify"]),
    ("instrumented job: arm64", "instrumented-arm64", "run", _rx(_GR + r"connectedDebugAndroidTest\b")),
    ("instrumented arm64: tested APK bound to manifest", "instrumented-arm64", "run", _RX_APK),
    ("instrumented x86_64: consumes native artifacts", "instrumented-x86_64", "uses", _rx(r"actions/download-artifact@")),
    ("instrumented x86_64: re-verify", "instrumented-x86_64", "run", RX_NB["verify"]),
    ("instrumented job: x86_64", "instrumented-x86_64", "run", _rx(_GR + r"connectedDebugAndroidTest\b")),
    ("instrumented x86_64: tested APK bound to manifest", "instrumented-x86_64", "run", _RX_APK),
]
# backwards-compatible name used by the summary line
REQUIREMENTS = REQUIRED_STEPS

# Shell masking patterns applied to the run body of mandatory steps.
SOFTFAIL_OR = re.compile(r"\|\|")
# `;` chaining masks status unless it is shell control syntax (`; then`,
# `; do`, `;;`) — those do not swallow a failing command's exit status under
# `set -e`.
SOFTFAIL_SEMI = re.compile(r";(?!;|\s*(then|do|else|fi|done|esac)\b)")
SOFTFAIL_SET_PLUS_E = re.compile(r"^\s*set\s+(?:[-+][A-Za-z]*\s+)*\+[A-Za-z]*e", re.M)
SOFTFAIL_EXIT_ZERO = re.compile(r"^\s*exit\s+0\s*$", re.M)
SOFTFAIL_NOOP_TAIL = re.compile(r"^\s*(?:true|:)\s*$", re.M)
SOFTFAIL_RUN = re.compile(r"\|\||;")  # legacy name kept for external callers


def _strip_shell_quotes(body):
    """Blank out quoted string CONTENT so `;` / `||` inside literals are not
    treated as operators. Double-quoted segments that contain command
    substitution (`$(` or backtick) are kept verbatim because their contents
    DO execute; single-quoted segments never execute."""
    out, i, n = [], 0, len(body)
    while i < n:
        ch = body[i]
        if ch == "\\" and i + 1 < n:
            out.append("\\\\")
            i += 2
            continue
        if ch == "'":
            j = body.find("'", i + 1)
            if j < 0:
                out.append(body[i:])
                break
            out.append("''")
            i = j + 1
            continue
        if ch == '"':
            j = i + 1
            while j < n:
                if body[j] == "\\":
                    j += 2
                    continue
                if body[j] == '"':
                    break
                j += 1
            seg = body[i:j + 1]
            out.append(seg if ("$(" in seg or "`" in seg) else '""')
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def shell_masks_failure(body, strict_semicolon=True):
    """Return a reason if a mandatory step's shell body can mask failure."""
    if not body:
        return None
    code = _strip_shell_quotes(body)
    if SOFTFAIL_OR.search(code):
        return "shell chaining (|| / ;)"
    if strict_semicolon and SOFTFAIL_SEMI.search(code):
        return "shell chaining (|| / ;)"
    if SOFTFAIL_SET_PLUS_E.search(body):
        return "errexit relaxation (set +e)"
    if SOFTFAIL_EXIT_ZERO.search(body):
        return "forced success (exit 0)"
    if SOFTFAIL_NOOP_TAIL.search(body):
        return "trailing no-op success builtin (true / :)"
    return None


# --------------------------------------------------------------------------
# executable command position (S1CRC-R-002)
#
# A mandatory command only counts if it HEADS a simple command whose exit
# status reaches the step result. `_command_segments` splits a run body into
# simple-command segments and marks each segment that occupies a masking or
# non-executing position:
#
#   * `if`/`elif`/`while`/`until` conditions and `!`-negated commands run but
#     their exit status does not propagate -> masked;
#   * `cmd &` backgrounds cmd and `a | b`/`a || b` make `a`'s status invisible
#     to the pipeline/list result -> masked;
#   * `x || cmd` runs cmd only on failure -> conditionally executed -> masked;
#   * `for`/`select`/`case` heads are spec words, not commands -> masked;
#   * `$( )` and backquote substitutions RESET the mask (their contents run
#     normally); `( )`, `{ }`, `;`, `&&` and newlines preserve it.
#
# `command_executes` then requires the pattern to match at the START of an
# acceptable segment after stripping env assignments and transparent exec
# wrappers — so `echo python3 tools/security/native_build.py verify`,
# `printf '…'`, `: cmd`, `true cmd`, `# cmd`, `if cmd`, and heredoc-body text
# can never satisfy a mandatory step.
# --------------------------------------------------------------------------

_ENV_ASSIGN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=\S*")
_TRANSPARENT_WRAPPER = re.compile(
    r"(?:command|exec|builtin|noglob|time|nice|nohup|stdbuf|env|sudo|doas)\s+")
_SEG_HEAD = re.compile(r"[A-Za-z_!][\w!.-]*")
_COND_OPEN = {"if", "elif", "while", "until"}
_COND_CLOSE = {"then", "do", "else", "fi", "done", "esac"}
_HEAD_NONEXEC = {"for", "select", "case", "function", "!"}
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _command_segments(code):
    """Split shell text into ``(masked, segment)`` simple-command tuples."""
    segs = []
    masked = False
    once = False            # mask just the next segment (RHS of `||`)
    stack = []              # masks enclosing `(` / `$(` / backquote regions
    in_bt = False
    i, n = 0, len(code)
    start = 0

    def emit(end):
        nonlocal start, masked, once
        s = code[start:end].lstrip()
        start = end
        if not s:
            return
        m = _SEG_HEAD.match(s)
        w = m.group(0) if m else ""
        if w in _COND_OPEN:
            segs.append((True, s[m.end():]))
            masked = True
        elif w in _COND_CLOSE:
            segs.append((False, s[m.end():]))
            masked = False
        elif w in _HEAD_NONEXEC:
            segs.append((True, s[m.end():]))
        else:
            segs.append((masked or once, s))
            once = False

    while i < n:
        ch = code[i]
        if ch == "#" and (i == start or not code[start:i].strip()
                          or code[i - 1] in " \t"):
            emit(i)
            j = code.find("\n", i)
            i = j if j >= 0 else n
            start = i
            continue
        if ch == "`":
            emit(i)
            if in_bt:
                masked = stack.pop() if stack else masked
                in_bt = False
            else:
                stack.append(masked)
                masked = False
                in_bt = True
            i += 1
            start = i
            continue
        if ch == "$" and code[i + 1:i + 2] == "(":
            emit(i)
            stack.append(masked)
            masked = False
            i += 2
            start = i
            continue
        if ch == "(":
            emit(i)
            stack.append(masked)
            i += 1
            start = i
            continue
        if ch == ")":
            emit(i)
            masked = stack.pop() if stack else masked
            i += 1
            start = i
            continue
        if ch == "&":
            nxt = code[i + 1:i + 2]
            prv = code[i - 1:i]
            if nxt == "&":
                emit(i)
                i += 2            # `a && b`: a's failure propagates
            elif prv in (">", "|") or nxt == ">":
                i += 1            # `>&`, `&>`, `&>>`, `|&` redirections
                continue
            else:
                emit(i)
                if segs:
                    segs[-1] = (True, segs[-1][1])   # `cmd &` backgrounds cmd
                i += 1
            start = i
            continue
        if ch == "|":
            nxt = code[i + 1:i + 2]
            emit(i)
            if nxt == "|":
                if segs:
                    segs[-1] = (True, segs[-1][1])   # `a || b` masks a
                once = True                          # and b runs conditionally
                i += 2
            else:
                if segs:
                    segs[-1] = (True, segs[-1][1])   # non-final pipeline element
                i += 1
            start = i
            continue
        if ch in ";\n":
            emit(i)
            i += 1
            start = i
            continue
        if ch in "{}":
            emit(i)
            i += 1
            start = i
            continue
        i += 1
    emit(n)
    return segs


def command_executes(run_body, rx, allow_masked=False):
    """True iff ``rx`` matches at the head of a simple command in ``run_body``.

    Quoted string content is blanked first, so quoted command text is never a
    match. Matches in masked positions (see `_command_segments`), comments and
    heredoc bodies do not count. ``allow_masked`` is for content markers only.
    """
    code = _strip_shell_quotes(run_body)
    code = code.replace("\\\r\n", " ").replace("\\\n", " ")
    heredoc = None
    for masked, seg in _command_segments(code):
        s = seg.strip()
        if heredoc is not None:
            if s == heredoc:
                heredoc = None
            continue
        if not s or (masked and not allow_masked):
            continue
        while True:
            m = _ENV_ASSIGN.match(s)
            if m:
                s = s[m.end():].lstrip()
                continue
            m = _TRANSPARENT_WRAPPER.match(s)
            if m:
                s = s[m.end():].lstrip()
                continue
            break
        if rx.match(s):
            return True
        hm = _HEREDOC.search(s)
        if hm:
            heredoc = hm.group(2)
    return False


def _step_matches(step, kind, rx):
    """The step carries the matcher where it takes effect: the ``uses`` field
    for actions, or an executable command position in ``run`` — including
    status-masked positions so they can be reported as masking rather than
    silently re-satisfying the requirement."""
    if kind == "uses":
        uses = step.get("uses")
        return isinstance(uses, str) and bool(rx.search(uses))
    run = step.get("run")
    return isinstance(run, str) and command_executes(run, rx, allow_masked=True)


def _step_executes_unmasked(step, kind, rx):
    """Stricter: the matcher must sit in a status-propagating position."""
    if kind == "uses":
        return _step_matches(step, kind, rx)
    run = step.get("run")
    return isinstance(run, str) and command_executes(run, rx)


# --------------------------------------------------------------------------
# text-fragment helpers (kept for callers/tests that pass raw step text)

def run_body(step_text):
    """Return the shell body of a step's `run:` key (block or inline), or ''."""
    m = re.search(r"^([ \t]*)run[ \t]*:[ \t]*(\|[-+]?\d*|>[-+]?\d*)?[ \t]*(.*)$", step_text, re.M)
    if not m:
        return ""
    indent, block, inline = m.group(1), m.group(2), m.group(3)
    if not block:
        return inline
    body, started = [], False
    for line in step_text[m.end():].splitlines():
        if not line.strip():
            body.append("")
            continue
        cur = len(line) - len(line.lstrip())
        if cur <= len(indent):
            break
        started = True
        body.append(line)
    return "\n".join(body)


def softfail_reason(step_text):
    """Human-readable reason if a mandatory step (raw text) can mask failure."""
    return shell_masks_failure(run_body(step_text))


def parse_needs(block):
    """Extract the `needs:` set of a raw job block (scalar, inline or block list)."""
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


# ==========================================================================
# structured validation
# ==========================================================================

def _needs_of(job):
    n = job.get("needs")
    if n is None:
        return set()
    if isinstance(n, str):
        return {n}
    if isinstance(n, list) and all(isinstance(x, str) for x in n):
        return set(n)
    return {"<malformed>"}


def _step_text(step):
    parts = []
    for k in ("uses", "run", "shell", "working-directory"):
        v = step.get(k)
        if isinstance(v, str):
            parts.append(v)
    w = step.get("with")
    if isinstance(w, dict):
        for k, v in w.items():
            parts.append(f"{k}: {v}")
    return "\n".join(parts)


def _truthy(v):
    return v is True or (isinstance(v, str) and v.strip().lower() not in ("", "false"))


def _check_mandatory_step(job_name, label, step, errors, strict_semicolon=True):
    """A mandatory step must be unconditional, fatal, and unmasked."""
    if "if" in step:
        errors.append(f"{label}: step in job '{job_name}' is conditional (if: {step.get('if')!r}) — mandatory gates may not be skipped")
    if _truthy(step.get("continue-on-error")):
        errors.append(f"{label}: step in job '{job_name}' is non-fatal (continue-on-error) — mandatory gates may not soft-fail")
    if "timeout-minutes" in step and not isinstance(step.get("timeout-minutes"), int):
        errors.append(f"{label}: step in job '{job_name}' has non-literal timeout-minutes")
    run = step.get("run")
    if isinstance(run, str):
        why = shell_masks_failure(run, strict_semicolon=strict_semicolon)
        if why:
            errors.append(f"{label}: step in job '{job_name}' masks failure via {why}")
    if not isinstance(run, str) and not isinstance(step.get("uses"), str):
        errors.append(f"{label}: step in job '{job_name}' has neither run nor uses")


def _check_job_mandatory(name, job, errors):
    if not isinstance(job, dict):
        errors.append(f"job '{name}' is not a mapping")
        return False
    if "if" in job:
        errors.append(f"required job '{name}' carries a job-level if ({job.get('if')!r}) — mandatory jobs may not be disabled/conditional")
    if _truthy(job.get("continue-on-error")):
        errors.append(f"required job '{name}' is non-fatal (continue-on-error: {job.get('continue-on-error')!r})")
    strat = job.get("strategy")
    if isinstance(strat, dict) and strat.get("fail-fast") is False:
        errors.append(f"required job '{name}' sets strategy.fail-fast: false")
    runner = job.get("runs-on")
    pol = RUNNER_POLICY.get(name)
    if not isinstance(runner, str):
        errors.append(f"required job '{name}' runs-on must be a single hosted runner label, got {runner!r} "
                      "(label lists such as [self-hosted, macOS, ARM64] are prohibited for the public repository)")
    elif "${{" in runner or "self-hosted" in runner.lower():
        errors.append(f"required job '{name}' runs-on {runner!r} is dynamic or self-hosted — prohibited")
    elif pol is not None and not pol.match(runner):
        errors.append(f"required job '{name}' runs-on {runner!r} is not the required hosted runner class")
    steps = job.get("steps")
    if not isinstance(steps, list) or not steps or not all(isinstance(s, dict) for s in steps):
        errors.append(f"required job '{name}' has no well-formed steps list")
        return False
    if job.get("container") is not None or job.get("services") is not None:
        errors.append(f"required job '{name}' uses container/services — execution environment must be the hosted runner")
    return True


def validate_lineage(jobs, errors):
    """Enforce the job dependency graph and artifact consumption discipline."""
    graph = {j: _needs_of(b) for j, b in jobs.items() if isinstance(b, dict)}

    def transitive(job, seen=None):
        seen = set() if seen is None else seen
        for n in graph.get(job, set()):
            if n not in seen:
                seen.add(n)
                transitive(n, seen)
        return seen

    for job, required in REQUIRED_NEEDS.items():
        if job not in jobs:
            continue
        for n in sorted(required - graph.get(job, set())):
            errors.append(f"lineage: job '{job}' must declare needs: {n}")
        for n in sorted(graph.get(job, set())):
            if n not in jobs:
                errors.append(f"lineage: job '{job}' needs unknown job '{n}'")

    for job in sorted(ARTIFACT_CONSUMERS & set(jobs)):
        if "native-build" not in transitive(job):
            errors.append(f"lineage: '{job}' does not descend from native-build")
        steps = jobs[job].get("steps") if isinstance(jobs[job], dict) else None
        if not isinstance(steps, list):
            continue
        dl_idx = verify_idx = first_consume_idx = None
        for i, s in enumerate(steps):
            if not isinstance(s, dict):
                continue
            uses = s.get("uses") if isinstance(s.get("uses"), str) else ""
            run = s.get("run") if isinstance(s.get("run"), str) else ""
            with_ = s.get("with") if isinstance(s.get("with"), dict) else {}
            if "actions/download-artifact@" in uses:
                dl_idx = i if dl_idx is None else dl_idx
                if with_.get("name") != NATIVE_ARTIFACT_NAME:
                    errors.append(f"lineage: '{job}' downloads an artifact other than {NATIVE_ARTIFACT_NAME}")
                if str(with_.get("path") or "").strip() != "build/native":
                    errors.append(f"lineage: '{job}' does not download the native artifact into build/native")
                if "if" in s or _truthy(s.get("continue-on-error")):
                    errors.append(f"lineage: '{job}' artifact download step is conditional/non-fatal")
            if command_executes(run, RX_NB["verify"]):
                verify_idx = i if verify_idx is None else verify_idx
                if "if" in s or _truthy(s.get("continue-on-error")):
                    errors.append(f"lineage: '{job}' verify step is conditional/non-fatal")
            if command_executes(run, _RX_GRADLE_CONSUME):
                if first_consume_idx is None:
                    first_consume_idx = i
                    if "if" in s or _truthy(s.get("continue-on-error")):
                        errors.append(f"lineage: '{job}' first Gradle consumer step is conditional/non-fatal")
            if "validate_apk_contents.py" in run and ("if" in s or _truthy(s.get("continue-on-error"))):
                errors.append(f"lineage: '{job}' APK-binding step is conditional/non-fatal")
            if re.search(r"native_build\.py\s+build(\s|$)|cargo\s+ndk", run):
                errors.append(f"lineage: '{job}' rebuilds native artifacts instead of consuming native-build output")
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
        if first_consume_idx is None:
            errors.append(f"lineage: '{job}' never consumes the artifact with Gradle")

    nb = jobs.get("native-build")
    steps = nb.get("steps") if isinstance(nb, dict) and isinstance(nb.get("steps"), list) else []
    order = {"check-toolchain": None, "build": None, "rebuild-compare": None, "verify": None}
    up_idx = None
    for i, s in enumerate(steps):
        if not isinstance(s, dict):
            continue
        run = s.get("run") if isinstance(s.get("run"), str) else ""
        uses = s.get("uses") if isinstance(s.get("uses"), str) else ""
        for cmd in order:
            if order[cmd] is None and command_executes(run, RX_NB[cmd]):
                order[cmd] = i
        if "actions/upload-artifact@" in uses:
            up_idx = i if up_idx is None else up_idx
            w = s.get("with") if isinstance(s.get("with"), dict) else {}
            if w.get("name") != NATIVE_ARTIFACT_NAME:
                errors.append(f"lineage: native-build must upload artifact {NATIVE_ARTIFACT_NAME}")
            if w.get("if-no-files-found") != "error":
                errors.append("lineage: native-build upload must use if-no-files-found: error")
            paths = str(w.get("path") or "")
            if "build/native/jniLibs" not in paths or "build/native/native-manifest.json" not in paths:
                errors.append("lineage: native-build upload must include build/native/jniLibs and native-manifest.json")
    if steps:
        idx = [order[c] for c in ("check-toolchain", "build", "rebuild-compare", "verify")]
        if None not in idx and not (idx[0] < idx[1] < idx[2] < idx[3]):
            errors.append("lineage: native-build steps must run check-toolchain -> build -> rebuild-compare -> verify")
        if up_idx is None:
            errors.append(f"lineage: native-build must upload artifact {NATIVE_ARTIFACT_NAME}")
        elif order["verify"] is not None and up_idx < order["verify"]:
            errors.append("lineage: native-build uploads the artifact before verifying it")


def validate_structure(doc):
    errors = []
    if not isinstance(doc, dict):
        return ["workflow root is not a mapping"]
    on = doc.get("on", doc.get(True))
    if on is None:
        errors.append("workflow has no `on:` trigger")
    else:
        triggers = set(on) if isinstance(on, dict) else ({on} if isinstance(on, str) else set(on or []))
        if not {"push", "pull_request"} <= triggers:
            errors.append(f"workflow must trigger on push AND pull_request (got {sorted(map(str, triggers))})")
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append("no jobs block parsed from workflow")
        return errors

    for j in sorted(REQUIRED_JOBS - set(jobs)):
        errors.append(f"required job missing: {j}")

    ok_jobs = {}
    for name in sorted(REQUIRED_JOBS & set(jobs)):
        if _check_job_mandatory(name, jobs[name], errors):
            ok_jobs[name] = jobs[name]

    # every required step must exist AND be mandatory wherever it appears
    for label, job_name, kind, rx in REQUIRED_STEPS:
        job = jobs.get(job_name)
        if not isinstance(job, dict) or not isinstance(job.get("steps"), list):
            errors.append(f"{label}: job '{job_name}' missing")
            continue
        matched = [s for s in job["steps"] if isinstance(s, dict) and _step_matches(s, kind, rx)]
        if not matched:
            errors.append(f"{label}: no step in job '{job_name}' executes {rx.pattern!r} at a command position")
            continue
        # a match only inside a masking position means the gate runs but its
        # result is discarded — it does not satisfy the requirement
        if kind == "run" and not any(_step_executes_unmasked(s, kind, rx) for s in matched):
            errors.append(f"{label}: mandatory command in job '{job_name}' appears only in "
                          "status-masked shell positions (condition, !, &, |, ||)")
        # APK-binding steps legitimately use `if [ -z ... ]; then` control syntax
        strict = "validate_apk_contents" not in rx.pattern
        for s in matched:
            _check_mandatory_step(job_name, label, s, errors, strict_semicolon=strict)

    validate_lineage(jobs, errors)
    return errors


def validate(workflow_path):
    p = Path(workflow_path)
    if not p.exists():
        return [f"workflow missing: {p}"]
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"workflow unreadable: {e}"]
    try:
        doc = parse_workflow(text)
    except YamlSubsetError as e:
        return [f"workflow YAML outside the strict supported subset (fail-closed): {e}"]
    return validate_structure(doc)


def main():
    ap = argparse.ArgumentParser(description="Validate that the CI workflow contains all S1 security gates and that they are mandatory.")
    ap.add_argument("--workflow", default=str(REPO_ROOT / WORKFLOW))
    args = ap.parse_args()
    errors = validate(args.workflow)
    print("CI PIPELINE STRUCTURE + EXECUTION-SEMANTICS GATE (S1)")
    if errors:
        for e in errors:
            print(f"  FAIL {e}")
        print("RESULT: FAIL")
        return 1
    print(f"  OK   all {len(REQUIRED_STEPS)} mandatory gate steps + {len(REQUIRED_JOBS)} required jobs present, "
          "unconditional, fatal, hosted-runner-only")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
