#!/usr/bin/env python3
"""B-028 deterministic continuity-surface renderer.

Resolves the placeholder set consumed by ``generate_handoff.py`` in the
``CURRENT_*`` surfaces from the authoritative state files plus live Git, and
either rewrites the surfaces (``--write``) or verifies they already match
(``--check``, the dual-run drift gate).

Prose sections stay human-authored. Only placeholder markers are rendered.
Unresolved markers and unparsable source JSON fail closed.

Python 3 standard library only. No network.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

STATE_PATH = "docs/continuity/CURRENT_STATE.json"
WORKFORCE_PATH = "docs/workforce/WORKFORCE_STATE.json"

KNOWN_MARKERS = (
    "__EFFECTIVE_GATE__",
    "__HANDOFF_BRANCH__",
    "__HANDOFF_HEAD__",
    "__WORKING_TREE__",
    "__CANONICAL_BASE__",
    "__CANONICAL_BRANCH__",
    "__DESCRIBED_HEAD__",
    "__DELIVERY_BRANCH__",
    "__LATEST_EVENT__",
    "__PRE_MERGE_GATE__",
    "__POST_MERGE_GATE__",
)

# Markers whose values come from live Git rather than state files.
RUNTIME_MARKERS = {"__HANDOFF_BRANCH__", "__HANDOFF_HEAD__", "__WORKING_TREE__"}

# Derivable JSON fields: field name -> the marker that stands for its value.
# In --check mode a JSON surface must carry either the placeholder or the
# resolved value for each of these fields that is present — anything else is
# semantic drift (e.g. a stale described_head) and fails closed.
JSON_FIELD_MARKERS = {
    "handoff_head": "__HANDOFF_HEAD__",
    "working_tree": "__WORKING_TREE__",
    "handoff_branch": "__HANDOFF_BRANCH__",
    "current_gate": "__EFFECTIVE_GATE__",
    "described_head": "__DESCRIBED_HEAD__",
    "delivery_branch": "__DELIVERY_BRANCH__",
    "canonical_branch": "__CANONICAL_BRANCH__",
    "latest_merge_to_baseline": "__CANONICAL_BASE__",
    "main_baseline_head": "__CANONICAL_BASE__",
    "latest_material_event_id": "__LATEST_EVENT__",
    "pre_merge_gate": "__PRE_MERGE_GATE__",
    "post_merge_gate": "__POST_MERGE_GATE__",
}


class RenderError(Exception):
    pass


def _git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True,
                            text=True, timeout=60)
    if result.returncode:
        raise RenderError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _load_json(root, rel):
    try:
        return json.loads((root / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RenderError(f"{rel}: {exc}")


def resolve_markers(root, state=None, workforce=None, live_git=True):
    """Return {marker: value} for the deterministic placeholder set."""
    state = state if state is not None else _load_json(root, STATE_PATH)
    workforce = workforce if workforce is not None else _load_json(root, WORKFORCE_PATH)

    delivery = state.get("delivery_branch")
    described = state.get("described_head")
    pre = state.get("pre_merge_gate")
    post = state.get("post_merge_gate")
    canonical = state.get("canonical_branch")

    for name, value in (("delivery_branch", delivery), ("described_head", described),
                        ("pre_merge_gate", pre), ("post_merge_gate", post),
                        ("canonical_branch", canonical)):
        if not isinstance(value, str) or not value:
            raise RenderError(f"CURRENT_STATE.json missing required field: {name}")
    if state.get("current_gate") not in (None, "__EFFECTIVE_GATE__"):
        pass  # literal gates allowed; placeholder is canonical form
    if workforce.get("described_head") != described:
        raise RenderError("WORKFORCE_STATE.json described_head != CURRENT_STATE.json")

    # Effective gate rule (B-026): runtime delivery branch -> pre-merge gate;
    # runtime canonical branch -> post-merge gate. In live mode read the real
    # branch; offline falls back to the declared delivery branch (pre-merge).
    if live_git:
        runtime_branch = _git(root, "branch", "--show-current")
        head = _git(root, "rev-parse", "HEAD")
        dirty = bool(_git(root, "status", "--porcelain=v1", "--untracked-files=all"))
    else:
        runtime_branch = delivery
        head = described
        dirty = None

    effective = pre if runtime_branch == delivery else post

    base = state.get("latest_merge_to_baseline") or state.get("main_baseline_head")
    if live_git and canonical:
        try:
            base = _git(root, "rev-parse", f"refs/remotes/origin/{canonical}")
        except RenderError:
            base = base or "UNRESOLVED"

    return {
        "__EFFECTIVE_GATE__": effective,
        "__HANDOFF_BRANCH__": runtime_branch,
        "__HANDOFF_HEAD__": head,
        "__WORKING_TREE__": ("CLEAN" if dirty is False else ("DIRTY" if dirty else "UNKNOWN")),
        "__CANONICAL_BASE__": base or "UNRESOLVED",
        "__CANONICAL_BRANCH__": canonical,
        "__DESCRIBED_HEAD__": described,
        "__DELIVERY_BRANCH__": delivery,
        "__LATEST_EVENT__": state.get("latest_material_event_id", "UNKNOWN"),
        "__PRE_MERGE_GATE__": pre,
        "__POST_MERGE_GATE__": post,
    }


def render_text(text, markers):
    """Replace known markers. Fail closed on leftover __X__ markers."""
    for marker, value in markers.items():
        text = text.replace(marker, str(value))
    import re
    leftover = re.findall(r"__[A-Z0-9_]+__", text)
    known = set(KNOWN_MARKERS)
    unknown = [m for m in leftover if m not in known]
    if unknown:
        raise RenderError(f"unresolved unknown markers: {sorted(set(unknown))}")
    if leftover:
        raise RenderError(f"markers unresolved after render: {sorted(set(leftover))}")
    return text


def check_json_fields(original, markers):
    """Verify derivable JSON fields against the resolved marker set.

    For each known derivable field present in the JSON, the value must be
    either the field's placeholder marker or the resolved marker value —
    anything else is drift that placeholder substitution alone cannot see.
    Returns a list of problems (empty = consistent)."""
    try:
        data = json.loads(original)
    except ValueError:
        return []  # not JSON — text-only surface, no field-level check
    if not isinstance(data, dict):
        return []
    problems = []
    for field, marker in JSON_FIELD_MARKERS.items():
        if field not in data:
            continue
        value = data[field]
        expected = markers.get(marker)
        if value == marker:
            continue  # canonical placeholder form
        if expected and value == expected:
            continue  # concrete resolved value
        if expected is None:
            problems.append(f"field '{field}': marker {marker} not derivable")
        else:
            problems.append(
                f"field '{field}': stale/divergent value "
                f"{str(value)[:60]!r} (expected {str(expected)[:60]!r} or {marker})")
    return problems


def process_file(root, rel, markers, write=False, strict=False):
    path = root / rel
    try:
        original = path.read_text(encoding="utf-8")
    except OSError as exc:
        return rel, "FAIL", str(exc)
    try:
        rendered = render_text(original, markers)
    except RenderError as exc:
        return rel, "FAIL", str(exc)
    if rendered == original:
        return rel, "MATCH", "deterministic fields already rendered"
    # Marker substitution is tautological on placeholder files — the
    # substantive drift check is field-level: derivable JSON fields must
    # carry the placeholder or the resolved value, never a stale third
    # value. --strict additionally requires the fully rendered form
    # (archive verification).
    if not write and not strict:
        problems = check_json_fields(original, markers)
        if problems:
            return rel, "DRIFT", "; ".join(problems)
        return rel, "MATCH", "consistent modulo placeholder representation"
    if write:
        try:
            path.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            return rel, "FAIL", str(exc)
        return rel, "RENDERED", "rewritten"
    return rel, "DRIFT", "surface differs from rendered truth"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+",
                        help="surface files to render/check (repo-relative)")
    parser.add_argument("--check", action="store_true",
                        help="dual-run drift check: fail if surfaces diverge")
    parser.add_argument("--write", action="store_true", help="rewrite surfaces")
    parser.add_argument("--offline", action="store_true",
                        help="no live Git; runtime markers resolve to declared state")
    parser.add_argument("--strict", action="store_true",
                        help="check requires the fully rendered form (archive verification)")
    parser.add_argument("--root", default=None)
    args = parser.parse_args(argv)
    if args.check == args.write:
        parser.error("exactly one of --check or --write is required")

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    try:
        markers = resolve_markers(root, live_git=not args.offline)
    except RenderError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    failures = 0
    for rel in args.files:
        rel, status, detail = process_file(root, rel, markers, write=args.write,
                                           strict=args.strict)
        print(f"{status}: {rel} — {detail}")
        if status in ("FAIL", "DRIFT"):
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
