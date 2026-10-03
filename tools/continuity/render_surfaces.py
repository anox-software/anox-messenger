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
    "__DESCRIBED_HEAD__",
    "__DELIVERY_BRANCH__",
    "__LATEST_EVENT__",
    "__PRE_MERGE_GATE__",
    "__POST_MERGE_GATE__",
)

# Markers whose values come from live Git rather than state files.
RUNTIME_MARKERS = {"__HANDOFF_BRANCH__", "__HANDOFF_HEAD__", "__WORKING_TREE__"}


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


def process_file(root, rel, markers, write=False):
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
        rel, status, detail = process_file(root, rel, markers, write=args.write)
        print(f"{status}: {rel} — {detail}")
        if status in ("FAIL", "DRIFT"):
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
