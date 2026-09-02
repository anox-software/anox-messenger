#!/usr/bin/env python3
"""Validate anoX continuity / handoff readiness.

Supports two explicit modes:
  --mode live      validate the actual .git repository and current-state surfaces
  --mode archive   validate an extracted official handoff ZIP without .git
  --mode auto      choose live if .git exists, else archive if evidence exists

Mode is always printed. Live and archive results are never conflated.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "PROJECT_STATE.md",
    "FORTSCHRITT.md",
    "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
    "docs/authority/AUTHORITY_INDEX.md",
    "docs/authority/CLOUD_AI_SECRET_PROTECTION.md",
    "docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md",
    "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",
    "docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md",
    "docs/authority/B_FREEZE_REGISTRY.md",
    "docs/continuity/AUTHORITY_INDEX.md",
    "docs/continuity/CURRENT_HANDOFF.md",
    "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
    "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
    "docs/continuity/CURRENT_GIT_STATE.md",
    "docs/continuity/CURRENT_OPEN_WORK.md",
    "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
    "docs/continuity/DEVIN_OUTPUT_CONTRACT.md",
    "docs/continuity/HANDOFF_WORKFLOW.md",
    "docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md",
    "docs/continuity/CURRENT_STATE.json",
    "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
    "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
    "tools/continuity/generate_handoff.py",
    "tools/continuity/validate_continuity.py",
    "tools/security/validate_apk_contents.py",
]

REQUIRED_AUTHORITY_PATHS = {
    "authority_index": "docs/authority/AUTHORITY_INDEX.md",
    "cloud_ai_secret": "docs/authority/CLOUD_AI_SECRET_PROTECTION.md",
    "dev_security_workflow": "docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md",
    "security_invariants": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",
    "b026": "docs/authority/B026_CONTINUOUS_DEVELOPMENT_GOVERNANCE.md",
    "freeze_registry": "docs/authority/B_FREEZE_REGISTRY.md",
    "ultimate_main": "docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md",
}

PLACEHOLDER_MARKERS = ("__HANDOFF_HEAD__", "__WORKING_TREE__", "__HANDOFF_BRANCH__", "__EFFECTIVE_GATE__", "__PRE_MERGE_GATE__", "__POST_MERGE_GATE__")

# Files where runtime placeholders are intentional repository templates.
# In a generated handoff archive these placeholders MUST already be resolved.
# In live mode the validator resolves them against live Git.
PLACEHOLDER_TEMPLATE_FILES = {
    "docs/continuity/CURRENT_STATE.json",
    "docs/continuity/CURRENT_GIT_STATE.md",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Validate anoX continuity / handoff readiness.")
    parser.add_argument(
        "--mode",
        choices=["auto", "live", "archive"],
        default="auto",
        help="Validation mode: live requires .git, archive validates an extracted handoff",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        help="Path to an extracted handoff directory for archive mode",
    )
    return parser.parse_args()


def select_mode(args):
    if args.mode != "auto":
        return args.mode
    if (REPO_ROOT / ".git").is_dir():
        return "live"
    if args.archive and args.archive.exists():
        return "archive"
    if (REPO_ROOT / "MANIFEST.txt").exists() and (REPO_ROOT / "CURRENT_STATE.json").exists():
        return "archive"
    return "live"  # fallback; will fail clearly if .git is missing


def run_git(args, cwd=None, check=False):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        return None, None, -1


def git_status(cwd=None):
    out, _, code = run_git(["status", "--short"], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


def git_current_branch(cwd=None):
    out, _, code = run_git(["branch", "--show-current"], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


def git_current_head(cwd=None):
    out, _, code = run_git(["rev-parse", "HEAD"], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


def git_branch_head(branch, cwd=None):
    out, _, code = run_git(["rev-parse", branch], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


METADATA_ONLY_ALLOWLIST = frozenset(
    {
        "FORTSCHRITT.md",
        "PROJECT_STATE.md",
        "DEVIN_PROMPT_OUTPUT_ARCHIV.md",
        "docs/continuity/CURRENT_STATE.json",
        "docs/continuity/CURRENT_GIT_STATE.md",
        "docs/continuity/CURRENT_HANDOFF.md",
        "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md",
        "docs/continuity/CURRENT_OPEN_WORK.md",
        "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
        "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
        "docs/continuity/HANDOFF_WORKFLOW.md",
        "docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md",
        "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
        "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
        "docs/workforce/registries/runs.jsonl",
        "docs/workforce/registries/tasks.jsonl",
    }
)


def _is_allowed_metadata_path(rel):
    """Fail-closed metadata-only classifier.

    Unknown files and paths are substantive. Historical provenance directories
    are NOT broadly trusted; only explicitly listed current-state/project
    metadata files may qualify as metadata-only.
    """
    return rel in METADATA_ONLY_ALLOWLIST


def is_valid_sha(text):
    return bool(re.fullmatch(r"[0-9a-f]{40}", text or ""))


def git_object_exists(sha, cwd=None):
    """Return True if sha resolves to an existing Git object."""
    _, _, code = run_git(["rev-parse", "--verify", sha], cwd=cwd)
    return code == 0


def git_is_ancestor(ancestor, descendant, cwd=None):
    out, _, code = run_git(["merge-base", "--is-ancestor", ancestor, descendant], cwd=cwd)
    return code == 0


def git_merge_base(sha1, sha2, cwd=None):
    out, _, code = run_git(["merge-base", sha1, sha2], cwd=cwd)
    if code != 0 or out is None:
        return None
    return out


def git_diff_files(from_sha, to_sha, cwd=None):
    """Return all logical paths changed in the commit range [from_sha, to_sha].

    Combines an endpoint tree diff (`git diff --name-only`) with a merge-aware
    history walk (`git log -m --name-only`). The endpoint diff captures the final
    state difference, while the history walk captures paths that were added in a
    merge and later removed (merge-then-revert attacks). To avoid re-surfacing
    files that are already present in `from_sha` (e.g. a nested side branch that
    does not yet have the described payload), only history-only paths that do not
    exist in the `from_sha` tree are kept. A file added in one commit and renamed
    in a later commit within the same range is still visible to the classifier,
    and a rename exposes both the deleted source path and the added destination
    path. The metadata-only classifier must independently approve BOTH sides of a
    rename.

    Returns None if Git history inspection fails, which the caller must treat as
    a reconciliation failure.
    """
    # 1. Final tree difference.
    out, err, code = run_git(
        ["diff", "--name-only", "--no-renames", from_sha, to_sha], cwd=cwd
    )
    if code != 0 or out is None:
        print(f"  FAIL git_diff_files endpoint diff ({from_sha[:12]}..{to_sha[:12]}) could not be read: {err}")
        return None
    endpoint_paths = set()
    for line in out.splitlines():
        line = line.strip()
        if line:
            endpoint_paths.add(line)

    # 2. Merge-aware history walk to catch add-then-revert payloads.
    out, err, code = run_git(
        ["log", "-m", "--name-only", "--no-renames", "--format=", f"{from_sha}..{to_sha}"],
        cwd=cwd,
    )
    if code != 0 or out is None:
        print(f"  FAIL git_diff_files history walk ({from_sha[:12]}..{to_sha[:12]}) could not be read: {err}")
        return None
    history_paths = set()
    for line in out.splitlines():
        line = line.strip()
        if line:
            history_paths.add(line)

    # 3. Tree of `from_sha` so we can ignore history-only paths that already
    # existed there (nested merge false positives).
    out, err, code = run_git(["ls-tree", "-r", "--name-only", from_sha], cwd=cwd)
    if code != 0 or out is None:
        print(f"  FAIL git_diff_files could not list tree {from_sha[:12]}: {err}")
        return None
    from_tree = set(line.strip() for line in out.splitlines() if line.strip())

    extra = history_paths - endpoint_paths
    for p in extra:
        if p in from_tree:
            # Already existed at `from_sha`; final tree is unchanged — this is a
            # nested-merge false positive or a metadata churn that ended at the
            # same state. Do not surface it to the classifier.
            continue
        # A path that was added after `from_sha` and then removed before `to_sha`.
        endpoint_paths.add(p)

    return sorted(endpoint_paths)


def git_merge_resolution_paths(merge, delivery_parent, canonical_parent, cwd=None):
    """Return the merge resolution range as the union of:

    1. Three-way resolution paths (merge tree differs from both parents).
    2. The delivery-endpoint delta (merge tree differs from the reviewed
       delivery parent tree).

    The delivery-endpoint delta is required because a merge that silently
    reverts reviewed delivery content back to the canonical-parent version
    is still a merge-resolution mutation. The union is then classified by the
    fail-closed metadata-only allowlist.

    Returns a 4-tuple:
      (all_paths, three_way_paths, endpoint_paths, reverted_paths)
    or None on Git failure.
    """
    def tree_blobs(sha):
        """Return {path: blob} for the tree at `sha`."""
        out, err, code = run_git(["ls-tree", "-r", sha], cwd=cwd)
        if code != 0 or out is None:
            print(f"  FAIL git_merge_resolution_paths: could not list tree {sha[:12]}: {err}")
            return None
        blobs = {}
        for line in out.splitlines():
            parts = line.split(maxsplit=3)
            if len(parts) >= 4:
                path = parts[3].strip()
                blob = parts[2].strip()
                blobs[path] = blob
        return blobs

    merge_tree = tree_blobs(merge)
    delivery_tree = tree_blobs(delivery_parent)
    canonical_tree = tree_blobs(canonical_parent)
    if merge_tree is None or delivery_tree is None or canonical_tree is None:
        return None

    three_way = set()
    all_tree_paths = set(merge_tree) | set(delivery_tree) | set(canonical_tree)
    for p in all_tree_paths:
        m = merge_tree.get(p)
        d = delivery_tree.get(p)
        c = canonical_tree.get(p)
        # Three-way resolution: merge result differs from both parents.
        if m != d and m != c:
            three_way.add(p)

    # Delivery endpoint delta: any path where the final merge tree differs from
    # the reviewed delivery parent tree. This catches silent reversion to the
    # canonical parent, which the three-way rule alone would not flag.
    endpoint = git_diff_endpoint(delivery_parent, merge, cwd=cwd)
    if endpoint is None:
        return None
    endpoint = set(endpoint)

    union = sorted(three_way | endpoint)
    reverted = sorted(endpoint - three_way)
    return union, sorted(three_way), endpoint, reverted


def git_diff_endpoint(from_sha, to_sha, cwd=None):
    """Return paths where tree(to_sha) differs from tree(from_sha).

    This is a direct endpoint tree diff. It is used for the merge-resolution
    range (P2 -> merge commit) where the critical question is whether the merge
    result differs from the reviewed delivery result. It does NOT walk
    intermediate commit history; for that, use git_diff_files.
    """
    out, err, code = run_git(["diff", "--name-only", "--no-renames", from_sha, to_sha], cwd=cwd)
    if code != 0 or out is None:
        print(f"  FAIL git_diff_endpoint({from_sha[:12]}..{to_sha[:12]}) could not be read: {err}")
        return None
    paths = set()
    for line in out.splitlines():
        line = line.strip()
        if line:
            paths.add(line)
    return sorted(paths)


def git_merge_parents(sha, cwd=None):
    """Return the parent SHAs of a commit, or None on failure / not a merge."""
    out, _, code = run_git(["rev-list", "--parents", "-n", "1", sha], cwd=cwd)
    if code != 0 or out is None:
        return None
    parts = out.split()
    if len(parts) < 2:
        return None
    return parts[1:]


def git_find_canonical_merge(described_head, live_head, canonical_branch, delivery_branch, cwd=None):
    """Identify the canonical integration merge M and its delivery/canonical parents.

    Returns (merge_sha, delivery_parent, canonical_parent, error) where error is
    None on success or a descriptive diagnostic on failure.

    The delivery_parent is the parent that has described_head in its ancestry.
    The canonical_parent is the other parent and must be on the canonical branch.
    Only two-parent merges are supported. Ambiguous topologies (zero or more than
    one qualifying merge) fail closed.
    """
    # Find merge commits on the canonical branch first-parent path from
    # described_head to live_head. Using --first-parent ensures merges made inside
    # the delivery branch (nested side-merges, etc.) are not mistaken for canonical
    # integration merges, while still listing every main-line integration merge.
    out, err, code = run_git(
        ["rev-list", "--merges", "--first-parent", f"{described_head}..{live_head}"],
        cwd=cwd,
    )
    if code != 0 or out is None:
        return None, None, None, f"could not list canonical integration merges: {err}"
    candidates = out.splitlines()
    if not candidates:
        return None, None, None, "no canonical integration merge on the described..live ancestry path"

    canonical_ref = git_branch_head(canonical_branch, cwd=cwd) or canonical_branch
    qualifying = []
    for merge_sha in candidates:
        parents = git_merge_parents(merge_sha, cwd=cwd)
        if not parents:
            continue
        if len(parents) != 2:
            # V1 supports only two-parent merge commits.
            return None, None, None, f"merge {merge_sha[:12]} is not a two-parent merge"

        has_desc = [git_is_ancestor(described_head, p, cwd=cwd) for p in parents]
        if has_desc.count(True) != 1:
            # No parent or both parents have described_head: not a qualifying
            # integration transition for this described_head.
            continue

        delivery_idx = has_desc.index(True)
        delivery_parent = parents[delivery_idx]
        canonical_parent = parents[1 - delivery_idx]

        if not git_is_ancestor(canonical_parent, canonical_ref, cwd=cwd):
            # The canonical parent is not on the canonical branch.
            continue

        # Also verify described_head is an ancestor of the delivery parent (redundant safety).
        if not git_is_ancestor(described_head, delivery_parent, cwd=cwd):
            continue

        qualifying.append((merge_sha, delivery_parent, canonical_parent))

    if len(qualifying) == 0:
        return None, None, None, "cannot identify the canonical integration merge for the delivery lineage"
    if len(qualifying) > 1:
        shas = ", ".join(m[:12] for m, _, _ in qualifying)
        return None, None, None, f"ambiguous/multiple canonical integration merges: {shas}"

    return qualifying[0][0], qualifying[0][1], qualifying[0][2], None


def _paths_are_metadata_only(paths, label, quiet=False):
    """Check a path list against the fail-closed metadata-only allowlist."""
    disallowed = [p for p in paths if not _is_allowed_metadata_path(p)]
    if disallowed:
        if not quiet:
            print(f"  FAIL {label} contains non-metadata-only paths:")
            for p in disallowed[:10]:
                print(f"    - {p}")
        return False, disallowed
    return True, []


def validate_canonical_merge_lifecycle(described_head, live_head, state, live_branch, root, all_ok, label):
    """Validate the canonical merge transition and compute the effective gate.

    Returns (all_ok, effective_gate).
    """
    canonical_branch = state.get("canonical_branch") or state.get("baseline_branch", "main")
    delivery_branch = state.get("delivery_branch")
    # In lifecycle mode, pre/post gates are independently required and must not
    # fall back to current_gate (which would be self-satisfying).
    pre_gate = state.get("pre_merge_gate", "")
    post_gate = state.get("post_merge_gate", "")
    if not pre_gate or not post_gate:
        print(f"  FAIL CURRENT_STATE.json missing pre_merge_gate or post_merge_gate for canonical merge lifecycle")
        return all_ok and False, None

    if live_branch == delivery_branch:
        # Delivery context: preserve all previously reviewed R2 protections.
        changed = git_diff_files(described_head, live_head)
        if changed is None:
            return False, None
        ok, _ = _paths_are_metadata_only(changed, f"delivery tail {described_head[:12]}..{live_head[:12]}")
        if not ok:
            return all_ok and False, None
        print(f"  OK   delivery context; only metadata-only files changed")
        print(f"  OK   effective gate: {pre_gate}")
        return all_ok, pre_gate

    if live_branch != canonical_branch:
        print(f"  FAIL runtime branch {live_branch} is neither canonical {canonical_branch} nor delivery {delivery_branch}")
        return False, None

    # Canonical context: identify the controlled integration merge.
    merge, delivery_parent, canonical_parent, error = git_find_canonical_merge(
        described_head, live_head, canonical_branch, delivery_branch
    )
    if merge is None:
        print(f"  FAIL {error}")
        print("       Supported: a single two-parent --no-ff merge of the reviewed delivery branch.")
        return False, None

    print(f"\n[{label}] Canonical merge transition")
    print(f"  canonical merge: {merge[:12]}  canonical parent: {canonical_parent[:12]}  delivery parent: {delivery_parent[:12]}")

    # Base-drift policy: the canonical parent must be an ancestor of the delivery
    # parent in a no-drift integration. If it is not, the canonical branch has
    # advanced since the delivery lineage diverged; any substantive drift in the
    # canonical base is unsupported in V1 and requires resynchronization.
    if not git_is_ancestor(canonical_parent, delivery_parent):
        common = git_merge_base(canonical_parent, delivery_parent)
        if common is None:
            print(f"  FAIL cannot determine merge base between canonical parent {canonical_parent[:12]} and delivery parent {delivery_parent[:12]}")
            return False, None
        drift = git_diff_endpoint(common, canonical_parent)
        if drift is None:
            return False, None
        ok, disallowed = _paths_are_metadata_only(drift, f"canonical base drift {common[:12]}..{canonical_parent[:12]}")
        if not ok:
            print("  FAIL SUBSTANTIVE CANONICAL BASE DRIFT — RESYNCHRONIZATION REQUIRED")
            for p in disallowed[:10]:
                print(f"    - {p}")
            return False, None
        print(f"  OK   metadata-only canonical base drift accepted")

    # Range 1 — reviewed delivery tail.
    r1 = git_diff_files(described_head, delivery_parent)
    if r1 is None:
        return False, None
    ok, _ = _paths_are_metadata_only(r1, f"delivery tail {described_head[:12]}..{delivery_parent[:12]}")
    if not ok:
        all_ok = False
    else:
        print(f"  OK   range 1 (described..delivery parent) is metadata-only")

    # Range 2 — merge resolution (three-way + delivery-endpoint comparison).
    r2 = git_merge_resolution_paths(merge, delivery_parent, canonical_parent)
    if r2 is None:
        return False, None
    r2_paths, r2_three, r2_endpoint, r2_reverted = r2
    ok, disallowed = _paths_are_metadata_only(r2_paths, f"merge resolution {merge[:12]} (vs delivery/canonical parents)")
    if not ok:
        reverted_disallowed = [p for p in disallowed if p in r2_reverted]
        if reverted_disallowed:
            print("  FAIL merge resolution DISCARDED REVIEWED DELIVERY CONTENT:")
            for p in reverted_disallowed[:10]:
                print(f"    - {p}")
        else:
            print(f"  FAIL merge resolution {merge[:12]} (vs delivery/canonical parents) contains non-metadata-only paths:")
            for p in disallowed[:10]:
                print(f"    - {p}")
        all_ok = False
    else:
        print(f"  OK   range 2 (merge resolution) is metadata-only")

    # Range 3 — post-merge canonical tail.
    r3 = git_diff_files(merge, live_head)
    if r3 is None:
        return False, None
    ok, _ = _paths_are_metadata_only(r3, f"post-merge tail {merge[:12]}..{live_head[:12]}")
    if not ok:
        all_ok = False
    else:
        print(f"  OK   range 3 (post-merge tail) is metadata-only")

    if all_ok:
        print(f"  OK   canonical merge transition verified")
        print(f"  OK   effective gate: {post_gate}")
        return all_ok, post_gate

    return all_ok, None


def load_current_state(root):
    path = root / "docs" / "continuity" / "CURRENT_STATE.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_required_files(root, all_ok, label):
    print(f"\n[{label}] Required files")
    for rel in REQUIRED_FILES:
        path = root / rel
        if path.exists():
            print(f"  OK   {rel}")
        else:
            print(f"  FAIL {rel} — missing")
            all_ok = False
    return all_ok


def validate_authority_paths(root, all_ok, label):
    print(f"\n[{label}] Authority paths")
    for name, rel in REQUIRED_AUTHORITY_PATHS.items():
        path = root / rel
        if path.exists():
            print(f"  OK   {name}: {rel}")
        else:
            print(f"  FAIL {name}: {rel} — missing")
            all_ok = False
    return all_ok


def _resolve_described_head(state):
    """Return the described_head, migrating legacy baseline_head if needed.

    Canonical precedence: described_head wins when present; baseline_head is
    legacy fallback only.
    """
    return state.get("described_head") or state.get("baseline_head") or ""


def _check_required_state_keys(state, schema_class=None):
    """Return (ok, errors) for mandatory current-state keys shared by live and archive."""
    required = ["handoff_branch", "security_invariants_path",
                "freeze_registry_path", "current_gate", "continuity_001_status", "schema_version"]
    if schema_class == ArchiveSchemaClass.CURRENT_LIFECYCLE:
        required.extend(REQUIRED_LIFECYCLE_STATE_KEYS)
    errors = []
    for key in required:
        if key not in state:
            errors.append(key)
    # Legacy archive compatibility: described_head may be absent if baseline_head is present.
    if "described_head" not in state and "baseline_head" not in state:
        errors.append("described_head (or legacy baseline_head)")
    return (len(errors) == 0, errors)


def validate_state_json(state, root, all_ok, label, live_branch=None, live_head=None, mode=None, schema_class=None):
    print(f"\n[{label}] CURRENT_STATE.json")
    if state is None:
        print("  FAIL CURRENT_STATE.json missing or invalid JSON")
        return False, None

    # Determine schema class. In archive mode the class is supplied by
    # validate_archive_surface_consistency; in live mode we compute it here.
    if schema_class is None:
        snapshot_path = root / "GIT_SNAPSHOT.txt"
        snapshot_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path.exists() else ""
        surfaces = {}
        for rel in ("docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_GIT_STATE.md"):
            p = root / rel
            if p.exists():
                surfaces[rel] = p.read_text(encoding="utf-8")
        schema_class, schema_errors = _classify_schema(state, snapshot_text, surfaces, mode=mode or "live")
        if schema_errors:
            for err in schema_errors:
                print(f"  FAIL CURRENT_STATE.json schema: {err}")
            all_ok = False

    keys_ok, missing = _check_required_state_keys(state, schema_class=schema_class)
    if not keys_ok:
        for key in missing:
            print(f"  FAIL CURRENT_STATE.json missing key: {key}")
        all_ok = False

    if state.get("continuity_001_status") != "ACCEPTED":
        print(f"  FAIL continuity_001_status = {state.get('continuity_001_status')} (expected ACCEPTED)")
        all_ok = False
    else:
        print("  OK   continuity_001_status = ACCEPTED")

    effective_gate = None
    described_head = _resolve_described_head(state)
    if not described_head:
        print("  FAIL CURRENT_STATE.json described_head missing/unresolved")
        all_ok = False
    elif not is_valid_sha(described_head):
        print(f"  FAIL CURRENT_STATE.json described_head is not a valid 40-char hex SHA: {described_head}")
        all_ok = False
    else:
        if live_head is not None:
            if schema_class == ArchiveSchemaClass.CURRENT_LIFECYCLE:
                # Canonical merge lifecycle path.
                all_ok, effective_gate = validate_canonical_merge_lifecycle(
                    described_head, live_head, state, live_branch, root, all_ok, label
                )
            elif schema_class == ArchiveSchemaClass.LEGACY:
                # Legacy single-branch path.
                all_ok = validate_described_head(described_head, live_head, root, all_ok, label)
                effective_gate = state.get("current_gate", "")
            else:
                print(f"  FAIL cannot validate described_head lineage for unknown schema")
                all_ok = False
        else:
            # Archive mode: we cannot verify ancestry without .git, but we can require the value.
            print(f"  OK   described_head {described_head[:12]} present (archive mode)")
            if schema_class == ArchiveSchemaClass.UNKNOWN:
                all_ok = False
            effective_gate = state.get("current_gate", "")

    if live_branch is not None:
        expected_branch = state.get("handoff_branch")
        if expected_branch == "__HANDOFF_BRANCH__":
            print(f"  OK   handoff_branch placeholder resolvable to {live_branch}")
        elif expected_branch != live_branch:
            lifecycle_branches = {state.get("canonical_branch"), state.get("delivery_branch")}
            if lifecycle_branches and live_branch in lifecycle_branches and expected_branch in lifecycle_branches:
                print(f"  OK   handoff_branch {expected_branch} is a recognized lifecycle branch; live is {live_branch}")
            else:
                print(f"  FAIL CURRENT_STATE.json handoff_branch {expected_branch} != live branch {live_branch}")
                all_ok = False
        else:
            print(f"  OK   handoff_branch matches live {live_branch}")

    return all_ok, effective_gate


def validate_described_head(described_head, live_head, root, all_ok, label):
    print(f"\n[{label}] Described HEAD verification")
    print(f"  described_head: {described_head[:12]}")
    print(f"  live_head:      {live_head[:12]}")

    if described_head == live_head:
        print("  OK   described_head == live_head (CASE 1)")
        return all_ok

    if not is_valid_sha(live_head):
        print("  FAIL live HEAD is not a valid SHA")
        return False

    if not git_is_ancestor(described_head, live_head):
        print("  FAIL described_head is not an ancestor of live_head (CASE 4)")
        return False

    changed = git_diff_files(described_head, live_head)
    if changed is None:
        print("  FAIL could not determine diff between described_head and live_head")
        return False

    print(f"  described_head is an ancestor; {len(changed)} file(s) changed")
    disallowed = [p for p in changed if not _is_allowed_metadata_path(p)]
    if disallowed:
        print("  FAIL changes contain non-metadata-only files (CASE 3):")
        for p in disallowed[:10]:
            print(f"    - {p}")
        return False

    print("  OK   only metadata-only files changed (CASE 2 — METADATA-ONLY STATE ADVANCE)")
    return all_ok


def validate_current_state_surfaces(root, all_ok, label, live_branch=None, state=None):
    print(f"\n[{label}] Current-state surface consistency")

    allowed_branches = set()
    if state:
        for key in ("canonical_branch", "delivery_branch", "handoff_branch", "baseline_branch"):
            b = state.get(key)
            if b:
                allowed_branches.add(b)

    project_state_path = root / "PROJECT_STATE.md"
    project_state_text = project_state_path.read_text(encoding="utf-8") if project_state_path.exists() else ""
    for marker in PLACEHOLDER_MARKERS:
        if marker in project_state_text:
            print(f"  FAIL PROJECT_STATE.md contains unresolved placeholder: {marker}")
            all_ok = False

    m = re.search(r"^[-*]\s*Branch:\s*`?([^`\n]+)`?", project_state_text, re.MULTILINE)
    if m:
        declared_branch = m.group(1).strip()
        if declared_branch == "__HANDOFF_BRANCH__":
            print(f"  OK   PROJECT_STATE.md branch is a resolvable placeholder")
        elif live_branch and declared_branch != live_branch:
            if allowed_branches and declared_branch in allowed_branches and live_branch in allowed_branches:
                print(f"  OK   PROJECT_STATE.md branch {declared_branch} is a recognized lifecycle branch; live is {live_branch}")
            else:
                print(f"  FAIL PROJECT_STATE.md declares branch {declared_branch} but live branch is {live_branch}")
                all_ok = False
        elif live_branch:
            print(f"  OK   PROJECT_STATE.md branch = {declared_branch}")
    else:
        print("  WARN PROJECT_STATE.md branch line not found")

    fortschritt_path = root / "FORTSCHRITT.md"
    fortschritt_text = fortschritt_path.read_text(encoding="utf-8") if fortschritt_path.exists() else ""
    for marker in PLACEHOLDER_MARKERS:
        if marker in fortschritt_text:
            print(f"  FAIL FORTSCHRITT.md contains unresolved placeholder: {marker}")
            all_ok = False

    # CURRENT_HANDOFF.md must not contain unresolved placeholders
    handoff_path = root / "docs/continuity/CURRENT_HANDOFF.md"
    if handoff_path.exists():
        handoff_text = handoff_path.read_text(encoding="utf-8")
        for marker in PLACEHOLDER_MARKERS:
            if marker in handoff_text:
                print(f"  FAIL CURRENT_HANDOFF.md contains unresolved placeholder: {marker}")
                all_ok = False

    # Stale current-state phrases
    stale_phrases = [
        ("Approximately **27%**", "outdated functional progress"),
        ("Device Authentication work has not started", "outdated Device Auth claim"),
        ("B-003 has a client domain/state foundation in review", "outdated B-003 review claim"),
        ("PR #5 open", "stale PR #5 open claim in current-state"),
        ("not merged", "stale not-merged claim in current-state"),
        ("awaiting architect review", "stale awaiting-review claim in current-state"),
    ]
    for phrase, reason in stale_phrases:
        for path_name in ("PROJECT_STATE.md", "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md"):
            p = root / path_name
            if p.exists() and phrase in p.read_text(encoding="utf-8"):
                print(f"  FAIL {path_name} contains stale current-state phrase: {reason} ('{phrase}')")
                all_ok = False

    # CURRENT_NEXT_DEVIN_TASK.md must not contain PROMPT-008 as the current active task
    next_task_path = root / "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md"
    next_task_text = next_task_path.read_text(encoding="utf-8") if next_task_path.exists() else ""
    if re.search(r"PROMPT-008\b", next_task_text) and not re.search(r"MERGED", next_task_text):
        print("  FAIL CURRENT_NEXT_DEVIN_TASK.md still references PROMPT-008 as an active task without MERGED")
        all_ok = False

    # Contradictory B-003 status
    impl_path = root / "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md"
    impl_text = impl_path.read_text(encoding="utf-8") if impl_path.exists() else ""
    if re.search(r"B-003.*(open|not merged|in review)", impl_text, re.IGNORECASE) and re.search(r"B-003.*MERGED", impl_text):
        print("  FAIL CURRENT_IMPLEMENTATION_STATE.md contains contradictory B-003 merged and open/not-merged claims")
        all_ok = False

    return all_ok


# Project Memory / Progress Integrity V1
LEDGER_REQUIRED_FIELDS = ("event_id", "date", "type", "task", "summary", "status")
LEDGER_SHA_FIELDS = ("start_head", "end_head", "merge_head")
LEDGER_MAX_LINE_BYTES = 4096
T3_EVENT_TYPES = frozenset({"canonical_merge", "gate_transition", "migration"})

_ANOX_EVENT_PLACEHOLDER_RE = re.compile(r"^__[A-Z0-9_]+__$")
_ANOX_EVENT_ABBREV_SHA_RE = re.compile(r"^[0-9a-f]{4,39}\.\.\.$")


def _classify_event_sha_value(value):
    """Classify a value that may be a SHA, abbreviation, placeholder, or invalid."""
    if not value or not isinstance(value, str):
        return "missing"
    if _ANOX_EVENT_PLACEHOLDER_RE.match(value):
        return "placeholder"
    if _ANOX_EVENT_ABBREV_SHA_RE.match(value):
        return "abbreviated"
    if is_valid_sha(value):
        return "full"
    return "invalid"


def _resolve_event_sealed_sha(ev):
    """Return (sha, kind) for the commit that seals the event, or (None, None).

    A sealed event must declare a concrete end_head or merge_head. start_head is
    not a seal; it records where work began and may be a placeholder for a pending
    derived runtime event.
    """
    for field in ("merge_head", "end_head"):
        val = ev.get(field)
        kind = _classify_event_sha_value(val)
        if kind in ("full", "abbreviated"):
            return val, kind
    return None, None


def _sha_matches_live(sha, kind, live_head):
    if not live_head or not sha:
        return False
    if kind == "full":
        return sha == live_head
    if kind == "abbreviated":
        prefix = sha[:-3]
        return live_head.startswith(prefix)
    return False


def _resolve_git_object(prefix, cwd=None):
    """Resolve a short SHA/abbreviation to a full 40-char SHA using git, if possible."""
    if not prefix or not isinstance(prefix, str):
        return None
    if is_valid_sha(prefix):
        return prefix
    if _ANOX_EVENT_ABBREV_SHA_RE.match(prefix):
        short = prefix[:-3]
        out, _, code = run_git(["rev-parse", "--verify", short], cwd=cwd)
        if code == 0 and out:
            return out
    return None


def _extract_latest_fortschritt_section(text):
    """Return the text of the latest top-level FORTSCHRITT section.

    Markers may sit immediately before the section heading ("<!-- ANOX_EVENT: ... -->\n## ...")
    or inside the section.  Include a marker that directly precedes the last heading.
    """
    if not text:
        return ""
    heading_matches = list(re.finditer(r"^## ", text, re.MULTILINE))
    if not heading_matches:
        return text
    last_heading = heading_matches[-1]
    start = last_heading.start()
    pre = text[:start]
    # If the text right before the heading ends with an ANOX_EVENT marker, include it.
    m = re.search(r"<!--\s*ANOX_EVENT:\s*[^>]+-->\s*$", pre)
    if m:
        start = m.start()
    return text[start:]


def _event_marker_re(event_id):
    return re.compile(r"<!--\s*ANOX_EVENT:\s*" + re.escape(event_id) + r"\s*-->")


def _compute_memory_freshness_status(events, state, live_branch, live_head, mode, last_sealed_event, last_event, root):
    """Determine the PROJECT_MEMORY_FRESHNESS status after basic ledger checks."""
    if not _is_lifecycle_state(state):
        return "PASS"

    canonical_branch = state.get("canonical_branch") or state.get("baseline_branch", "main")
    if not canonical_branch:
        return "PASS"

    canonical_merges = [
        ev for ev in events
        if ev.get("type") == "canonical_merge" and _resolve_event_sealed_sha(ev)[0] is not None
    ]
    if not canonical_merges:
        return "PASS"

    # Archive mode without a live HEAD cannot verify derived runtime freshness.
    if mode == "archive" and not live_head:
        return "PASS"

    last_cm = canonical_merges[-1]
    cm_sha, cm_kind = _resolve_event_sealed_sha(last_cm)

    last_sealed_sha = None
    last_sealed_kind = None
    if last_sealed_event:
        last_sealed_sha, last_sealed_kind = _resolve_event_sealed_sha(last_sealed_event)

    live_at_cm = _sha_matches_live(cm_sha, cm_kind, live_head)

    # Is the last recorded event still an unsealed in-progress / derived runtime event?
    is_pending = last_event is not last_sealed_event

    if live_at_cm:
        if is_pending:
            start_val = last_event.get("start_head") if last_event else None
            start_kind = _classify_event_sha_value(start_val)
            if start_kind in ("full", "abbreviated") and _sha_matches_live(start_val, start_kind, live_head):
                return "PASS — ONE PENDING DERIVED RUNTIME EVENT"
            # If the last recorded event has no clear derivation, still allow one pending
            # derived event when the canonical merge is the most recent sealed T3.
            if last_sealed_event is last_cm:
                return "PASS — ONE PENDING DERIVED RUNTIME EVENT"
            return "FAIL — PENDING EVENT NOT DERIVED FROM LAST T3 GATE"
        else:
            if last_event is last_cm:
                # Canonical merge is the last recorded event and no newer material has been authored.
                return "PASS — ONE PENDING DERIVED RUNTIME EVENT"
            # A later checkpoint has already been sealed.
            return "PASS"

    # live_head is not at the canonical merge.
    # If a later sealed event matches live_head, the memory has been synced.
    if last_sealed_sha and _sha_matches_live(last_sealed_sha, last_sealed_kind, live_head):
        return "PASS"

    # If the last recorded event is an unsealed pending event derived from the canonical
    # merge and live_head has moved past the merge, a second material checkpoint has been
    # authored before the pending event was sealed.
    if is_pending:
        start_val = last_event.get("start_head") if last_event else None
        start_kind = _classify_event_sha_value(start_val)
        if start_kind in ("full", "abbreviated") and _sha_matches_live(start_val, start_kind, cm_sha):
            # In live mode with git, confirm live_head is actually ahead of the canonical merge.
            if mode == "live" and (root / ".git").is_dir() and live_head:
                cm_obj = _resolve_git_object(cm_sha, cwd=root)
                if cm_obj and git_is_ancestor(cm_obj, live_head, cwd=root):
                    return "FAIL — SECOND CHECKPOINT BEFORE SEALING PRIOR MERGE"
                elif cm_obj:
                    # live_head is not a descendant of the canonical merge; treat as simple mismatch.
                    return "FAIL — AUTHORED MATERIAL CHECKPOINT WITHOUT LEDGER EVENT"
            # Archive mode or no git: fall through to generic failure.
            pass
        return "FAIL — AUTHORED MATERIAL CHECKPOINT WITHOUT LEDGER EVENT"

    # The last event is sealed. If the live archive head has advanced past it, the advance
    # must be a metadata-only synchronization; the caller's described_head / lifecycle
    # validation already enforces that product/authority/CI/tool changes are recorded.
    if not is_pending and last_sealed_sha:
        if mode == "live" and (root / ".git").is_dir() and live_head:
            last_obj = _resolve_git_object(last_sealed_sha, cwd=root)
            if last_obj and git_is_ancestor(last_obj, live_head, cwd=root):
                return "PASS — SEALED EVENT SYNCHRONIZED; METADATA-ONLY ADVANCE"
            elif last_obj:
                # live_head is not a descendant of the last sealed event.
                pass
        elif mode == "archive" and live_head:
            # Archive mode cannot diff ancestry. A handoff whose HEAD is a metadata-only
            # synchronization beyond the described/substantive commit is valid only when the
            # packaged state explicitly records:
            #   - handoff_head == the archive live head
            #   - described_head == the last sealed material event
            #   - the last material event is not itself a canonical merge (T3), because a T3
            #     requires a recorded derived event before the next checkpoint.
            handoff_head = state.get("handoff_head") if state else None
            described_head = state.get("described_head") if state else None
            last_type = last_event.get("type") if last_event else None
            if (
                handoff_head == live_head
                and is_valid_sha(described_head)
                and described_head == last_sealed_sha
                and live_head != last_sealed_sha
                and last_type != "canonical_merge"
            ):
                return "PASS — SEALED EVENT SYNCHRONIZED; METADATA-ONLY ADVANCE (archive)"

    return "FAIL — AUTHORED MATERIAL CHECKPOINT WITHOUT LEDGER EVENT"


def validate_project_memory_freshness(root, all_ok, label, live_branch, live_head, state, mode):
    """Validate the project history ledger and current memory freshness.

    Returns (all_ok, memory_freshness_status).
    """
    print(f"\n[{label}] Project memory freshness")

    ledger_path = root / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl"
    if not ledger_path.exists():
        print("  FAIL docs/continuity/PROJECT_HISTORY_LEDGER.jsonl missing")
        return False, "FAIL — LEDGER MISSING"

    # Memory is only fully applicable when CURRENT_STATE.json exposes event pointers.
    memory_enabled = bool(
        state
        and (state.get("latest_material_event_id") is not None
             or state.get("latest_human_history_event_id") is not None
             or state.get("project_memory_freshness") is not None)
    )

    events = []
    seen_ids = set()
    diagnostics = []

    with open(ledger_path, "rb") as f:
        for idx, raw in enumerate(f, start=1):
            stripped = raw.rstrip(b"\n\r")
            if len(stripped) > LEDGER_MAX_LINE_BYTES:
                diagnostics.append(f"line {idx} exceeds {LEDGER_MAX_LINE_BYTES} bytes")
                all_ok = False
                continue
            line = stripped.decode("utf-8")
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError as e:
                diagnostics.append(f"line {idx} is not valid JSON: {e}")
                all_ok = False
                continue
            missing = [k for k in LEDGER_REQUIRED_FIELDS if k not in ev]
            if missing:
                diagnostics.append(f"line {idx} missing required fields: {', '.join(missing)}")
                all_ok = False
                continue
            eid = ev["event_id"]
            if eid in seen_ids:
                diagnostics.append(f"duplicate event_id: {eid}")
                all_ok = False
            seen_ids.add(eid)
            events.append(ev)

    if diagnostics:
        for d in diagnostics[:10]:
            print(f"  FAIL {d}")
        return all_ok and False, "FAIL — LEDGER MALFORMED"

    if not events:
        print("  FAIL ledger is empty")
        return False, "FAIL — LEDGER EMPTY"

    # Validate SHA references in commit/merge fields and git: refs.
    freshness_status = "PASS"
    sha_errors = []
    for ev in events:
        eid = ev["event_id"]
        for field in LEDGER_SHA_FIELDS:
            val = ev.get(field)
            if not val:
                continue
            kind = _classify_event_sha_value(val)
            if kind == "invalid":
                sha_errors.append(f"event {eid} {field} is not a valid SHA reference: {val}")
        for ref in ev.get("refs") or []:
            if isinstance(ref, str) and ref.startswith("git:"):
                sha = ref[4:].strip()
                kind = _classify_event_sha_value(sha)
                if kind == "invalid":
                    sha_errors.append(f"event {eid} refs git: value is not a valid SHA reference: {sha}")
    if sha_errors:
        for e in sha_errors[:10]:
            print(f"  FAIL {e}")
        all_ok = False
        freshness_status = f"FAIL — {sha_errors[0]}"

    # Determine the last sealed event (the latest event with a concrete end/merge head).
    last_sealed_event = None
    for ev in reversed(events):
        sha, _ = _resolve_event_sealed_sha(ev)
        if sha is not None:
            last_sealed_event = ev
            break
    last_event = events[-1]
    last_sealed_id = last_sealed_event["event_id"] if last_sealed_event else last_event["event_id"]

    if memory_enabled:
        # State pointers must reference the last sealed material/human event.
        mat_id = state.get("latest_material_event_id")
        hum_id = state.get("latest_human_history_event_id")
        if mat_id is not None:
            if mat_id != last_sealed_id:
                print(f"  FAIL latest_material_event_id {mat_id} != last sealed ledger event {last_sealed_id}")
                all_ok = False
                if not freshness_status.startswith("FAIL"):
                    freshness_status = f"FAIL — latest_material_event_id {mat_id} != last sealed ledger event {last_sealed_id}"
            else:
                print(f"  OK   latest_material_event_id matches last sealed ledger event {mat_id}")
        if hum_id is not None:
            if hum_id != last_sealed_id:
                print(f"  FAIL latest_human_history_event_id {hum_id} != last sealed ledger event {last_sealed_id}")
                all_ok = False
                if not freshness_status.startswith("FAIL"):
                    freshness_status = f"FAIL — latest_human_history_event_id {hum_id} != last sealed ledger event {last_sealed_id}"
            else:
                print(f"  OK   latest_human_history_event_id matches last sealed ledger event {hum_id}")

        # HTML comment markers in PROJECT_STATE.md and the latest FORTSCHRITT section.
        marker_event_id = last_sealed_id
        marker_re = _event_marker_re(marker_event_id)

        project_state_path = root / "PROJECT_STATE.md"
        if project_state_path.exists():
            ps_text = project_state_path.read_text(encoding="utf-8")
            if marker_re.search(ps_text):
                print(f"  OK   PROJECT_STATE.md references event {marker_event_id}")
            else:
                print(f"  FAIL PROJECT_STATE.md does not reference event {marker_event_id}")
                all_ok = False
                if not freshness_status.startswith("FAIL"):
                    freshness_status = f"FAIL — PROJECT_STATE.md does not reference event {marker_event_id}"
        else:
            print("  FAIL PROJECT_STATE.md missing")
            all_ok = False
            if not freshness_status.startswith("FAIL"):
                freshness_status = "FAIL — PROJECT_STATE.md missing"

        fortschritt_path = root / "FORTSCHRITT.md"
        if fortschritt_path.exists():
            ft_text = fortschritt_path.read_text(encoding="utf-8")
            latest_section = _extract_latest_fortschritt_section(ft_text)
            if marker_re.search(latest_section):
                print(f"  OK   FORTSCHRITT.md latest section references event {marker_event_id}")
            else:
                print(f"  FAIL FORTSCHRITT.md latest section does not reference event {marker_event_id}")
                all_ok = False
                if not freshness_status.startswith("FAIL"):
                    freshness_status = f"FAIL — FORTSCHRITT.md latest section does not reference event {marker_event_id}"
        else:
            print("  FAIL FORTSCHRITT.md missing")
            all_ok = False
            if not freshness_status.startswith("FAIL"):
                freshness_status = "FAIL — FORTSCHRITT.md missing"

    # Compute the canonical-merge derived runtime event freshness.
    computed = _compute_memory_freshness_status(events, state, live_branch, live_head, mode, last_sealed_event, last_event, root)

    if computed.startswith("FAIL"):
        all_ok = False
        if not freshness_status.startswith("FAIL"):
            freshness_status = computed
    elif not freshness_status.startswith("FAIL"):
        freshness_status = computed

    if freshness_status.startswith("FAIL"):
        all_ok = False
    elif not memory_enabled and all_ok and not freshness_status.startswith("FAIL"):
        freshness_status = "NOT CONFIGURED"

    return all_ok, freshness_status


def _resolve_and_check(text, marker, expected):
    """Replace a single placeholder with the expected value and confirm the text now contains it."""
    resolved = text.replace(marker, expected, 1)
    return resolved, expected in resolved


def validate_placeholders(root, all_ok, label, mode, live_state=None):
    """Validate runtime placeholders in current-state surfaces.

    Repository templates intentionally use __HANDOFF_HEAD__ and __WORKING_TREE__
    in docs/continuity/CURRENT_STATE.json and CURRENT_GIT_STATE.md; these are
    resolved by generate_handoff.py before packaging. In archive mode they MUST
    already be resolved. In live mode unresolved placeholders are acceptable only
    in the template files; all other current-state files must be concrete.
    """
    print(f"\n[{label}] Placeholder / template resolution")

    # Files that may never contain runtime placeholders
    concrete_files = [
        "PROJECT_STATE.md",
        "FORTSCHRITT.md",
        "docs/continuity/CURRENT_HANDOFF.md",
        "docs/continuity/CURRENT_OPEN_WORK.md",
        "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
        "docs/continuity/CURRENT_UPLOAD_REQUIREMENTS.md",
        "docs/continuity/HANDOFF_WORKFLOW.md",
        "docs/continuity/HANDOFF_VALIDATION_CHECKLIST.md",
    ]

    for rel in concrete_files:
        p = root / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for marker in PLACEHOLDER_MARKERS:
            if marker in text:
                print(f"  FAIL {rel} contains forbidden placeholder {marker}")
                all_ok = False

    state = load_current_state(root)

    # CURRENT_STATE.json template handling
    state_path = root / "docs/continuity/CURRENT_STATE.json"
    if state_path.exists() and state is not None:
        def _live_value_for_marker(marker):
            if live_state is None:
                return ""
            return {
                "__HANDOFF_HEAD__": live_state.get("head", ""),
                "__WORKING_TREE__": live_state.get("working_tree", ""),
                "__HANDOFF_BRANCH__": live_state.get("branch", ""),
                "__EFFECTIVE_GATE__": live_state.get("effective_gate", ""),
                "__PRE_MERGE_GATE__": live_state.get("pre_merge_gate", ""),
                "__POST_MERGE_GATE__": live_state.get("post_merge_gate", ""),
            }.get(marker, "")

        for key, marker in (("handoff_head", "__HANDOFF_HEAD__"), ("working_tree", "__WORKING_TREE__"), ("handoff_branch", "__HANDOFF_BRANCH__"), ("current_gate", "__EFFECTIVE_GATE__")):
            value = state.get(key, "")
            if value == marker:
                if mode == "archive":
                    print(f"  UNRESOLVED HANDOFF PLACEHOLDER: CURRENT_STATE.json {key} = {marker}")
                    all_ok = False
                elif live_state is not None:
                    # live repository template; confirm it is resolvable
                    resolved_value = _live_value_for_marker(marker)
                    expected = marker if resolved_value == "" else resolved_value
                    if resolved_value == "" or (resolved_value != "" and resolved_value not in (marker, "")):
                        print(f"  OK   CURRENT_STATE.json {key} placeholder is resolvable to live {key}")
                    else:
                        print(f"  FAIL CURRENT_STATE.json {key} placeholder cannot be resolved")
                        all_ok = False
                else:
                    print(f"  OK   CURRENT_STATE.json {key} placeholder (template)")
            elif value == "" or value is None:
                print(f"  FAIL CURRENT_STATE.json {key} is missing")
                all_ok = False
            else:
                if mode == "archive":
                    # resolved in archive; no further check needed
                    print(f"  OK   CURRENT_STATE.json {key} = {value[:24]}...")
                elif live_state is not None:
                    expected = _live_value_for_marker(marker)
                    if expected and value != expected:
                        print(f"  FAIL CURRENT_STATE.json {key} {value} != live {expected}")
                        all_ok = False
                    else:
                        print(f"  OK   CURRENT_STATE.json {key} matches live")

    # CURRENT_GIT_STATE.md template handling
    git_state_path = root / "docs/continuity/CURRENT_GIT_STATE.md"
    if git_state_path.exists():
        git_state_text = git_state_path.read_text(encoding="utf-8")
        for marker in PLACEHOLDER_MARKERS:
            if marker in git_state_text:
                if mode == "archive":
                    print(f"  UNRESOLVED HANDOFF PLACEHOLDER: CURRENT_GIT_STATE.md contains {marker}")
                    all_ok = False
                elif live_state is not None:
                    expected = _live_value_for_marker(marker)
                    if expected and expected not in (marker, ""):
                        resolved_text = git_state_text.replace(marker, expected)
                        if expected in resolved_text:
                            print(f"  OK   CURRENT_GIT_STATE.md {marker} resolvable to live value")
                        else:
                            print(f"  FAIL CURRENT_GIT_STATE.md {marker} does not resolve to {expected}")
                            all_ok = False
                    else:
                        print(f"  FAIL CURRENT_GIT_STATE.md {marker} cannot be resolved")
                        all_ok = False
                else:
                    print(f"  OK   CURRENT_GIT_STATE.md {marker} placeholder (template)")

    # Verify concrete resolved values in CURRENT_GIT_STATE.md match live state
    if git_state_path.exists() and live_state is not None:
        git_state_text = git_state_path.read_text(encoding="utf-8")
        # Current handoff HEAD
        m = re.search(r"[-*]\s*(?:Current handoff HEAD|Handoff HEAD|HEAD):\s*`?([^`\n]+)`?", git_state_text, re.IGNORECASE)
        if m:
            recorded_head = m.group(1).strip()
            if recorded_head and recorded_head not in PLACEHOLDER_MARKERS:
                live_head = live_state.get("head", "")
                if live_head and recorded_head != live_head:
                    print(f"  FAIL CURRENT_GIT_STATE.md recorded handoff HEAD {recorded_head} != live {live_head}")
                    all_ok = False
                else:
                    print(f"  OK   CURRENT_GIT_STATE.md handoff HEAD matches live")
        # Working tree
        m = re.search(r"[-*]\s*Working tree:\s*`?([^`\n]+)`?", git_state_text, re.IGNORECASE)
        if m:
            recorded_tree = m.group(1).strip()
            if recorded_tree and recorded_tree not in PLACEHOLDER_MARKERS:
                live_tree = live_state.get("working_tree", "")
                if live_tree and recorded_tree != live_tree:
                    print(f"  FAIL CURRENT_GIT_STATE.md recorded working tree {recorded_tree} != live {live_tree}")
                    all_ok = False
                else:
                    print(f"  OK   CURRENT_GIT_STATE.md working tree matches live")

    return all_ok


def _extract_section(text, heading):
    """Return the text from a heading up to the next same-level heading or end of file."""
    pattern = re.escape(heading) + r"\n(.*?)((?=\n## )|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""


def validate_authority_precedence(root, all_ok, label):
    """Ensure only docs/authority/AUTHORITY_INDEX.md defines a canonical numbered precedence."""
    print(f"\n[{label}] Authority precedence drift")

    canonical_path = root / "docs/authority/AUTHORITY_INDEX.md"
    if canonical_path.exists():
        canonical_text = canonical_path.read_text(encoding="utf-8")
        # Accept either "## Precedence" or "## Authority precedence"
        canonical_section = _extract_section(canonical_text, "## Precedence") or _extract_section(canonical_text, "## Authority precedence")
        if re.search(r"^\d+\.\s+", canonical_section, re.MULTILINE):
            print("  OK   AUTHORITY_INDEX.md defines canonical numbered precedence")
        else:
            print("  WARN AUTHORITY_INDEX.md does not contain a numbered precedence list")
    else:
        print("  FAIL AUTHORITY_INDEX.md missing")
        return False

    # Other authority/continuity surfaces may not independently define a competing numbered list
    surfaces = [
        "docs/authority/DEVELOPMENT_SECURITY_WORKFLOW_V1.md",
        "docs/continuity/CURRENT_HANDOFF.md",
        "docs/continuity/CURRENT_CHAT_BOOTSTRAP_PROMPT.md",
    ]
    for rel in surfaces:
        p = root / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for heading in ("## Authority precedence", "## Precedence"):
            section = _extract_section(text, heading)
            if not section:
                continue
            # Two or more numbered items in a non-canonical authority/precedence section = competing precedence
            items = re.findall(r"^\d+\.\s+", section, re.MULTILINE)
            if len(items) >= 2:
                print(f"  FAIL {rel} defines a competing numbered precedence list under {heading}")
                all_ok = False
                break
            elif len(items) == 1:
                # Single item still implies an attempt at a numbered list
                print(f"  FAIL {rel} attempts a competing numbered precedence list under {heading}")
                all_ok = False
                break

    return all_ok


def validate_b027a(root, all_ok, label):
    """Run the B027-A workforce foundation validator as a subprocess.

    Only runs when the B027 authority document is present; this avoids breaking
    synthetic or historical handoff test repos that predate B027-A.
    """
    print(f"\n[{label}] B027-A workforce foundation")
    validator = root / "tools" / "workforce" / "validate_b027a.py"
    if not validator.exists():
        print("  SKIP B027-A validator not present")
        return all_ok
    if not (root / "docs" / "authority" / "B027_AI_WORKFORCE_GOVERNANCE.md").exists():
        print("  SKIP B027-A authority not present")
        return all_ok
    try:
        result = subprocess.run(
            [sys.executable, str(validator)],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  OK   B027-A validation PASSED")
        else:
            print("  FAIL B027-A validation FAILED")
            for line in (result.stdout + result.stderr).splitlines():
                if line.startswith("  FAIL") or line.startswith("FAIL"):
                    print(f"       {line}")
            all_ok = False
    except Exception as e:
        print(f"  FAIL could not run B027-A validator: {e}")
        all_ok = False
    return all_ok


def validate_b027b(root, all_ok, label):
    """Run the B027-B runtime validator as a subprocess.

    Only runs when the B027 authority document and B027-B validator are present.
    """
    print(f"\n[{label}] B027-B runtime")
    validator = root / "tools" / "workforce" / "validate_b027b.py"
    if not validator.exists():
        print("  SKIP B027-B validator not present")
        return all_ok
    if not (root / "docs" / "authority" / "B027_AI_WORKFORCE_GOVERNANCE.md").exists():
        print("  SKIP B027-B authority not present")
        return all_ok
    try:
        result = subprocess.run(
            [sys.executable, str(validator)],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  OK   B027-B validation PASSED")
        else:
            print("  FAIL B027-B validation FAILED")
            for line in (result.stdout + result.stderr).splitlines():
                if line.startswith("  FAIL") or line.startswith("FAIL"):
                    print(f"       {line}")
            all_ok = False
    except Exception as e:
        print(f"  FAIL could not run B027-B validator: {e}")
        all_ok = False
    return all_ok


def validate_b027c(root, all_ok, label):
    """Run the B027-C final integrity validator as a subprocess.

    Only runs when the B027 authority document and B027-C validator are present.
    """
    print(f"\n[{label}] B027-C final integrity")
    validator = root / "tools" / "workforce" / "validate_b027_integrity.py"
    if not validator.exists():
        print("  SKIP B027-C validator not present")
        return all_ok
    if not (root / "docs" / "authority" / "B027_AI_WORKFORCE_GOVERNANCE.md").exists():
        print("  SKIP B027-C authority not present")
        return all_ok
    try:
        result = subprocess.run(
            [sys.executable, str(validator)],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  OK   B027-C validation PASSED")
        else:
            print("  FAIL B027-C validation FAILED")
            for line in (result.stdout + result.stderr).splitlines():
                if line.startswith("  FAIL") or line.startswith("FAIL"):
                    print(f"       {line}")
            all_ok = False
    except Exception as e:
        print(f"  FAIL could not run B027-C validator: {e}")
        all_ok = False
    return all_ok


def validate_baseline_consistency(root, all_ok, label):
    print(f"\n[{label}] Described HEAD consistency")

    handoff_path = root / "docs/continuity/CURRENT_HANDOFF.md"
    git_state_path = root / "docs/continuity/CURRENT_GIT_STATE.md"
    state = load_current_state(root)

    if state is None:
        print("  FAIL CURRENT_STATE.json missing/invalid")
        return False

    declared_head = _resolve_described_head(state)
    if not declared_head:
        print("  FAIL CURRENT_STATE.json described_head missing/unresolved")
        all_ok = False

    for path in (handoff_path, git_state_path):
        if not path.exists():
            print(f"  FAIL {path.name} missing")
            all_ok = False
            continue
        text = path.read_text(encoding="utf-8")
        # Prefer explicit described_head. Fallback to legacy baseline HEAD forms.
        m = re.search(r"(?:described_head|Described HEAD):\s*`?([^`\n]+)`?", text, re.IGNORECASE | re.MULTILINE)
        if not m:
            m = re.search(r"(?:Current\s+baseline\s+HEAD|Merged\s+baseline\s+HEAD):\s*`?([^`\n]+)`?", text, re.IGNORECASE | re.MULTILINE)
        if not m:
            print(f"  FAIL {path.name} does not declare described_head (or legacy baseline HEAD)")
            all_ok = False
        elif declared_head:
            doc_head = m.group(1).strip()
            if doc_head != declared_head:
                print(f"  FAIL {path.name} head {doc_head} != CURRENT_STATE.json {declared_head}")
                all_ok = False
            else:
                print(f"  OK   {path.name} described_head matches CURRENT_STATE.json")

    return all_ok


def validate_baseline_ancestry(state, live_baseline_head, all_ok, label):
    """Verify baseline metadata is non-self-referentially consistent.

    recorded `latest_merge_to_baseline` and `previous_baseline_head` must each
    be valid, resolvable, and ancestors of the live baseline branch head. They
    do not need to equal the live head, which breaks the old self-reference
    invariant.
    """
    print(f"\n[{label}] Baseline ancestry integrity")

    if not is_valid_sha(live_baseline_head):
        print(f"  FAIL live baseline HEAD is not a valid SHA: {live_baseline_head}")
        return False

    if state is None:
        print("  FAIL CURRENT_STATE.json missing/invalid; cannot validate baseline ancestry")
        return False

    latest = state.get("latest_merge_to_baseline", "")
    previous = state.get("previous_baseline_head", "")

    for name, value in (("latest_merge_to_baseline", latest), ("previous_baseline_head", previous)):
        if not value or value == "__HANDOFF_HEAD__":
            continue
        if not is_valid_sha(value):
            print(f"  FAIL {name} is not a valid 40-char hex SHA: {value}")
            all_ok = False
            continue
        if not git_object_exists(value):
            print(f"  FAIL {name} {value[:12]} does not resolve to a Git object")
            all_ok = False
            continue
        if not git_is_ancestor(value, live_baseline_head):
            print(f"  FAIL {name} {value[:12]} is not an ancestor of live baseline HEAD {live_baseline_head[:12]}")
            all_ok = False
            continue
        print(f"  OK   {name} {value[:12]} is an ancestor of live baseline HEAD")

    if latest and previous and is_valid_sha(latest) and is_valid_sha(previous):
        if not git_is_ancestor(previous, latest):
            print(f"  FAIL previous_baseline_head {previous[:12]} is not an ancestor of latest_merge_to_baseline {latest[:12]}")
            all_ok = False
        else:
            print("  OK   previous_baseline_head precedes latest_merge_to_baseline")

    return all_ok


def validate_archive_manifests(archive_root, all_ok):
    print("\n[ARCHIVE] Package manifests")

    manifest = archive_root / "MANIFEST.txt"
    sha_manifest = archive_root / "SHA256_MANIFEST.txt"
    snapshot = archive_root / "GIT_SNAPSHOT.txt"

    if not manifest.exists():
        print("  FAIL MANIFEST.txt missing")
        return False
    if not sha_manifest.exists():
        print("  FAIL SHA256_MANIFEST.txt missing")
        return False
    if not snapshot.exists():
        print("  FAIL GIT_SNAPSHOT.txt missing")
        return False

    # Parse SHA manifest
    entries = {}
    duplicates = []
    bad_paths = []
    with open(sha_manifest, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                bad_paths.append(f"malformed line: {line!r}")
                continue
            digest, name = parts
            # Reject path traversal, absolute paths, and the manifest hashing itself.
            if name.startswith("/") or ".." in Path(name).parts or name == "SHA256_MANIFEST.txt":
                bad_paths.append(f"disallowed path in SHA manifest: {name}")
                continue
            if name in entries:
                duplicates.append(name)
                continue
            entries[name] = digest

    if bad_paths:
        print("  FAIL SHA-256 manifest contains invalid entries:")
        for item in bad_paths[:10]:
            print(f"    {item}")
        all_ok = False
    if duplicates:
        print("  FAIL SHA-256 manifest contains duplicate paths:")
        for item in duplicates[:10]:
            print(f"    {item}")
        all_ok = False

    # Build the expected set of regular files that must be covered.
    expected_files = set()
    for p in archive_root.rglob("*"):
        if p.is_dir():
            continue
        rel = str(p.relative_to(archive_root))
        if rel.startswith(".git/"):
            continue
        if rel == "SHA256_MANIFEST.txt":
            continue
        expected_files.add(rel)

    missing_or_mismatch = []
    for rel, expected in entries.items():
        full = archive_root / rel
        if not full.exists():
            missing_or_mismatch.append(f"{rel} — missing")
            continue
        actual = sha256_file(full)
        if actual != expected:
            missing_or_mismatch.append(f"{rel} — hash mismatch (expected {expected[:16]}..., got {actual[:16]}...)")

    uncovered = sorted(expected_files - set(entries))
    if uncovered:
        missing_or_mismatch.extend(f"{rel} — not listed in SHA-256 manifest" for rel in uncovered[:10])

    if missing_or_mismatch:
        print("  FAIL SHA-256 manifest does not match package files:")
        for item in missing_or_mismatch[:10]:
            print(f"    {item}")
        all_ok = False
    else:
        print(f"  OK   {len(entries)} archive files match SHA-256 manifest")

    # Check for forbidden .git content
    git_files = [p for p in archive_root.rglob("*") if p.is_relative_to(archive_root / ".git") or str(p.relative_to(archive_root)).startswith(".git/")]
    if git_files:
        print(f"  FAIL archive contains .git/ content: {git_files[0].relative_to(archive_root)}")
        all_ok = False
    else:
        print("  OK   no .git/ content in archive")

    # Manifest metadata check
    manifest_text = manifest.read_text(encoding="utf-8")
    for key in ("Handoff branch:", "Handoff HEAD:", "Baseline HEAD:", "Status:"):
        if key not in manifest_text:
            print(f"  WARN MANIFEST.txt missing {key} metadata")

    # Cross-check manifest lifecycle fields against CURRENT_STATE.json
    state = load_current_state(archive_root)
    if state is not None:
        handoff_branch = state.get("handoff_branch")
        m = re.search(r"^Handoff branch:\s*(.+)$", manifest_text, re.MULTILINE)
        if m and handoff_branch and handoff_branch not in PLACEHOLDER_MARKERS:
            if m.group(1).strip() != handoff_branch:
                print(f"  FAIL MANIFEST.txt Handoff branch {m.group(1).strip()} != CURRENT_STATE.json {handoff_branch}")
                all_ok = False
            else:
                print(f"  OK   MANIFEST.txt Handoff branch matches CURRENT_STATE.json")

        handoff_head = state.get("handoff_head")
        m = re.search(r"^Handoff HEAD:\s*(.+)$", manifest_text, re.MULTILINE)
        if m and handoff_head and handoff_head not in PLACEHOLDER_MARKERS:
            if m.group(1).strip() != handoff_head:
                print(f"  FAIL MANIFEST.txt Handoff HEAD {m.group(1).strip()} != CURRENT_STATE.json {handoff_head}")
                all_ok = False
            else:
                print(f"  OK   MANIFEST.txt Handoff HEAD matches CURRENT_STATE.json")

    return all_ok


def _extract_labeled_value(text, labels):
    """Extract the first value after one of the given labels in a markdown-ish file.

    Labels are tried in order. The value may be backtick-quoted or plain.
    Returns the value or None.
    """
    for label in labels:
        # Markdown list item or plain line, optional backticks around value.
        pattern = re.compile(
            rf"^(?:[-*]\s*)?{re.escape(label)}\s*[:=]\s*`?([^`\n]+?)`?\s*$",
            re.MULTILINE | re.IGNORECASE,
        )
        m = pattern.search(text)
        if m:
            return m.group(1).strip()
    return None


def _parse_git_snapshot(snapshot_text):
    """Return {branch, head} from a generated GIT_SNAPSHOT.txt."""
    result = {}
    lines = snapshot_text.splitlines()
    for i, line in enumerate(lines):
        if "git branch --show-current" in line:
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    result["branch"] = lines[j].strip()
                    break
        if "git rev-parse HEAD" in line:
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    result["head"] = lines[j].strip()
                    break
    return result


LIFECYCLE_SNAPSHOT_KEYS = {
    "canonical_branch",
    "delivery_branch",
    "described_head",
    "pre_merge_gate",
    "post_merge_gate",
    "effective_gate",
}


REQUIRED_LIFECYCLE_STATE_KEYS = (
    "canonical_branch",
    "delivery_branch",
    "described_head",
    "pre_merge_gate",
    "post_merge_gate",
)


# Recognized schema versions. Only explicitly listed versions may use their
# respective validation rules; anything else is treated as an unknown format.
# Legacy archives may not contain current-lifecycle evidence, and current
# lifecycle archives may not be silently downgraded by deleting fields.
CURRENT_LIFECYCLE_SCHEMAS = frozenset({"B026-1.2"})
LEGACY_SCHEMAS = frozenset({"B026-1.0"})


class ArchiveSchemaClass:
    """Explicit archive schema classification used for fail-closed enforcement."""

    CURRENT_LIFECYCLE = "current_lifecycle"
    LEGACY = "legacy"
    UNKNOWN = "unknown"


def _snapshot_has_lifecycle_block(snapshot_text):
    """Return True if GIT_SNAPSHOT.txt contains the resolved lifecycle block."""
    return "### Resolved lifecycle metadata" in (snapshot_text or "")


def _state_has_lifecycle_keys(state):
    """Return the set of distinguishing current-lifecycle keys present in state.

    described_head is NOT a distinguishing signal because both legacy and current
    schemas may use it (or its legacy alias baseline_head).
    """
    if not state:
        return set()
    distinguishing = ("canonical_branch", "delivery_branch", "pre_merge_gate", "post_merge_gate")
    return {k for k in distinguishing if state.get(k) and state.get(k) not in PLACEHOLDER_MARKERS}


def _surface_has_lifecycle_labels(surfaces):
    """Return True if any human-readable surface carries current lifecycle labels."""
    labels = ("Canonical branch", "Delivery branch", "Pre-merge gate", "Post-merge gate")
    for text in (surfaces or {}).values():
        for label in labels:
            pattern = re.compile(
                rf"^(?:[-*]\s*)?{re.escape(label)}\s*[:=]",
                re.MULTILINE | re.IGNORECASE,
            )
            if pattern.search(text):
                return True
    return False


def _schema_lifecycle_signals(state, snapshot_text, surfaces):
    """Collect non-schema_version evidence of current lifecycle format."""
    signals = []
    if _snapshot_has_lifecycle_block(snapshot_text):
        signals.append("GIT_SNAPSHOT.txt resolved lifecycle block")
    for k in _state_has_lifecycle_keys(state):
        signals.append(f"CURRENT_STATE.json {k}")
    if _surface_has_lifecycle_labels(surfaces):
        signals.append("human-readable lifecycle labels")
    return signals


def _classify_schema(state, snapshot_text=None, surfaces=None, mode="archive"):
    """Return (class, errors).

    class is one of ArchiveSchemaClass.CURRENT_LIFECYCLE, .LEGACY, .UNKNOWN.
    errors is a list of fail-closed diagnostics; UNKNOWN archives and
    contradictory archives produce errors.

    In archive mode, a GIT_SNAPSHOT.txt lifecycle block always forces
    current-lifecycle enforcement, even if CURRENT_STATE.json is downgraded.
    In live mode, the snapshot does not exist; the decision is based on
    CURRENT_STATE.json and human surfaces.
    """
    errors = []
    version = state.get("schema_version") if state else None
    lifecycle_signals = _schema_lifecycle_signals(state, snapshot_text, surfaces)

    if version in CURRENT_LIFECYCLE_SCHEMAS:
        # Explicitly recognized current lifecycle schema.
        if mode == "archive" and not _snapshot_has_lifecycle_block(snapshot_text or ""):
            errors.append("current lifecycle schema requires Resolved lifecycle metadata block in GIT_SNAPSHOT.txt")
        for k in REQUIRED_LIFECYCLE_STATE_KEYS:
            if not state or not state.get(k) or (mode == "archive" and state.get(k) in PLACEHOLDER_MARKERS):
                errors.append(f"current lifecycle schema requires CURRENT_STATE.json {k}")
        return ArchiveSchemaClass.CURRENT_LIFECYCLE, errors

    if version in LEGACY_SCHEMAS:
        # Explicitly recognized legacy schema; must not also carry current
        # lifecycle evidence, otherwise this is a downgrade/forgery.
        if lifecycle_signals:
            errors.append(
                f"legacy schema_version {version} is incompatible with current lifecycle evidence: {lifecycle_signals[0]}"
            )
        if mode == "archive" and _snapshot_has_lifecycle_block(snapshot_text or ""):
            errors.append("legacy schema must not contain Resolved lifecycle metadata block in GIT_SNAPSHOT.txt")
        return ArchiveSchemaClass.LEGACY, errors

    # Unknown or missing schema_version.
    if version:
        errors.append(f"unknown schema_version: {version}")
    else:
        errors.append("missing schema_version")
    if lifecycle_signals:
        errors.append(
            f"current lifecycle evidence present but schema_version is not recognized: {lifecycle_signals[0]}"
        )
    return ArchiveSchemaClass.UNKNOWN, errors


def _is_lifecycle_state(state):
    """Return True when state declares canonical merge lifecycle fields.

    Kept as a quick helper for non-security contexts (e.g. live path decision
    before full schema classification). Do NOT use as the sole classifier in
    archive mode; use _classify_schema instead.
    """
    if not state:
        return False
    return all(state.get(k) for k in ("canonical_branch", "delivery_branch", "pre_merge_gate", "post_merge_gate"))


def _parse_lifecycle_snapshot(snapshot_text, requires_lifecycle=False):
    """Parse the resolved lifecycle metadata block from GIT_SNAPSHOT.txt.

    Returns (values, errors). `values` is a dict of parsed fields or None if
    the block is absent and not required. `errors` is a list of fail-closed
    diagnostics for malformed, duplicate, missing, or unresolved values.
    """
    errors = []
    values = {}
    marker = "### Resolved lifecycle metadata"

    block_start = None
    lines = snapshot_text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == marker:
            if block_start is not None:
                errors.append("duplicate resolved lifecycle metadata block")
                return None, errors
            block_start = i

    if block_start is None:
        if requires_lifecycle:
            errors.append("missing resolved lifecycle metadata block")
        return (None, errors)

    seen = set()
    i = block_start + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("### "):
            break
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if ":" not in stripped:
            errors.append(f"malformed lifecycle snapshot line: {stripped!r}")
            i += 1
            continue
        key, raw = stripped.split(":", 1)
        key = key.strip()
        value = raw.strip()
        if key not in LIFECYCLE_SNAPSHOT_KEYS:
            errors.append(f"unknown lifecycle snapshot key: {key}")
            i += 1
            continue
        if key in seen:
            errors.append(f"duplicate lifecycle snapshot key: {key}")
            i += 1
            continue
        seen.add(key)
        if not value:
            errors.append(f"empty lifecycle snapshot value for {key}")
            i += 1
            continue
        if value in PLACEHOLDER_MARKERS or any(marker in value for marker in PLACEHOLDER_MARKERS):
            errors.append(f"unresolved placeholder in lifecycle snapshot {key}: {value}")
            i += 1
            continue
        values[key] = value
        i += 1

    if requires_lifecycle:
        for key in LIFECYCLE_SNAPSHOT_KEYS:
            if key not in seen:
                errors.append(f"missing lifecycle snapshot key: {key}")

    if not requires_lifecycle and not values:
        return None, errors

    return values, errors


def _assert_surface_consistency(archive_root, state, surfaces, snapshot, all_ok, schema_class=None):
    """Cross-check state against handoff/git-state surfaces and git snapshot."""

    def _ok_or_fail(condition, ok_msg, fail_msg):
        nonlocal all_ok
        if condition:
            print(f"  OK   {ok_msg}")
        else:
            print(f"  FAIL {fail_msg}")
            all_ok = False

    is_current_lifecycle = schema_class == ArchiveSchemaClass.CURRENT_LIFECYCLE

    # canonical_branch
    canonical = state.get("canonical_branch") or state.get("baseline_branch")
    for surface, text in surfaces.items():
        val = _extract_labeled_value(text, ("Canonical branch",))
        if val:
            _ok_or_fail(
                val == canonical,
                f"{surface} canonical_branch matches CURRENT_STATE.json",
                f"{surface} canonical_branch {val} != CURRENT_STATE.json {canonical}",
            )

    # delivery_branch
    delivery = state.get("delivery_branch")
    for surface, text in surfaces.items():
        val = _extract_labeled_value(text, ("Delivery branch",))
        if val:
            _ok_or_fail(
                val == delivery,
                f"{surface} delivery_branch matches CURRENT_STATE.json",
                f"{surface} delivery_branch {val} != CURRENT_STATE.json {delivery}",
            )

    # described_head
    described = _resolve_described_head(state)
    for surface, text in surfaces.items():
        val = _extract_labeled_value(text, ("Described HEAD", "described_head"))
        if val:
            _ok_or_fail(
                val == described,
                f"{surface} described_head matches CURRENT_STATE.json",
                f"{surface} described_head {val} != CURRENT_STATE.json {described}",
            )

    # handoff_branch / head against snapshot
    handoff_branch = state.get("handoff_branch")
    if handoff_branch and handoff_branch not in PLACEHOLDER_MARKERS:
        if "branch" in snapshot:
            _ok_or_fail(
                handoff_branch == snapshot["branch"],
                "CURRENT_STATE.json handoff_branch matches GIT_SNAPSHOT branch",
                f"CURRENT_STATE.json handoff_branch {handoff_branch} != GIT_SNAPSHOT branch {snapshot['branch']}",
            )
        else:
            print("  FAIL GIT_SNAPSHOT.txt does not contain branch")
            all_ok = False

    handoff_head = state.get("handoff_head")
    if handoff_head and handoff_head not in PLACEHOLDER_MARKERS:
        if "head" in snapshot:
            _ok_or_fail(
                handoff_head == snapshot["head"],
                "CURRENT_STATE.json handoff_head matches GIT_SNAPSHOT HEAD",
                f"CURRENT_STATE.json handoff_head {handoff_head} != GIT_SNAPSHOT HEAD {snapshot['head']}",
            )
        else:
            print("  FAIL GIT_SNAPSHOT.txt does not contain HEAD")
            all_ok = False

    # working_tree
    working_tree = state.get("working_tree")
    if working_tree and working_tree not in PLACEHOLDER_MARKERS:
        _ok_or_fail(
            working_tree == "clean",
            "CURRENT_STATE.json working_tree = clean",
            f"CURRENT_STATE.json working_tree {working_tree} != clean",
        )

    # current/effective gate must be one of the lifecycle gates and consistent with handoff_branch
    current_gate = state.get("current_gate")
    # In current lifecycle mode, pre/post gates are required and must NOT fall back to current_gate.
    pre_gate = state.get("pre_merge_gate", "")
    post_gate = state.get("post_merge_gate", "")
    if is_current_lifecycle:
        if not pre_gate or not post_gate:
            if not pre_gate:
                print("  FAIL CURRENT_STATE.json pre_merge_gate missing in current lifecycle archive")
                all_ok = False
            if not post_gate:
                print("  FAIL CURRENT_STATE.json post_merge_gate missing in current lifecycle archive")
                all_ok = False
        elif current_gate and current_gate not in PLACEHOLDER_MARKERS:
            if current_gate not in (pre_gate, post_gate):
                print(f"  FAIL CURRENT_STATE.json current_gate {current_gate} is neither pre_merge_gate nor post_merge_gate")
                all_ok = False
            elif handoff_branch == canonical and current_gate != post_gate:
                print(f"  FAIL canonical context current_gate {current_gate} != post_merge_gate {post_gate}")
                all_ok = False
            elif handoff_branch == delivery and current_gate != pre_gate:
                print(f"  FAIL delivery context current_gate {current_gate} != pre_merge_gate {pre_gate}")
                all_ok = False
            else:
                print(f"  OK   current/effective gate {current_gate} is consistent with lifecycle state")

    # Cross-check pre/post lifecycle gates against human-readable surfaces.
    if is_current_lifecycle and pre_gate:
        for rel in ("docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_GIT_STATE.md"):
            p = archive_root / rel
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8")
            for label in ("Pre-merge gate", "pre_merge_gate"):
                m = re.search(rf"[-*]\s*{re.escape(label)}:\s*`?([^`\n]+)`?", text, re.IGNORECASE)
                if m:
                    declared = m.group(1).strip()
                    if declared not in PLACEHOLDER_MARKERS and declared != pre_gate:
                        print(f"  FAIL {rel} declares pre-merge gate {declared} != CURRENT_STATE.json {pre_gate}")
                        all_ok = False
                    elif declared not in PLACEHOLDER_MARKERS:
                        print(f"  OK   {rel} pre-merge gate matches CURRENT_STATE.json")
    if is_current_lifecycle and post_gate:
        for rel in ("docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_GIT_STATE.md"):
            p = archive_root / rel
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8")
            for label in ("Post-merge gate", "post_merge_gate"):
                m = re.search(rf"[-*]\s*{re.escape(label)}:\s*`?([^`\n]+)`?", text, re.IGNORECASE)
                if m:
                    declared = m.group(1).strip()
                    if declared not in PLACEHOLDER_MARKERS and declared != post_gate:
                        print(f"  FAIL {rel} declares post-merge gate {declared} != CURRENT_STATE.json {post_gate}")
                        all_ok = False
                    elif declared not in PLACEHOLDER_MARKERS:
                        print(f"  OK   {rel} post-merge gate matches CURRENT_STATE.json")

    # Cross-check the independently generated GIT_SNAPSHOT.txt lifecycle block.
    snapshot_lifecycle = snapshot.get("lifecycle")
    if is_current_lifecycle and snapshot_lifecycle:
        def _extract_effective_gate(text):
            m = re.search(
                r"^(?:[-*]\s*)?(?:Current gate|Effective gate)\s*[:=]\s*(?:`([^`\n]+)`|([^`\n]+?))(?:\s+\([^)]+\))?$",
                text,
                re.MULTILINE | re.IGNORECASE,
            )
            return (m.group(1) or m.group(2)).strip() if m else None

        lifecycle_fields = (
            ("canonical_branch", ("Canonical branch",), state.get("canonical_branch") or state.get("baseline_branch")),
            ("delivery_branch", ("Delivery branch",), state.get("delivery_branch")),
            ("described_head", ("Described HEAD", "described_head"), _resolve_described_head(state)),
            ("pre_merge_gate", ("Pre-merge gate", "pre_merge_gate"), pre_gate),
            ("post_merge_gate", ("Post-merge gate", "post_merge_gate"), post_gate),
            ("effective_gate", None, current_gate or ""),
        )
        for key, labels, expected in lifecycle_fields:
            if not expected:
                _ok_or_fail(
                    False,
                    f"GIT_SNAPSHOT {key} matches CURRENT_STATE.json",
                    f"GIT_SNAPSHOT {key} missing value in CURRENT_STATE.json",
                )
                continue
            snap = snapshot_lifecycle.get(key)
            _ok_or_fail(
                snap == expected,
                f"GIT_SNAPSHOT {key} matches CURRENT_STATE.json",
                f"GIT_SNAPSHOT {key} {snap} != CURRENT_STATE.json {expected}",
            )
            if key == "effective_gate" and snap:
                for surface, text in surfaces.items():
                    val = _extract_effective_gate(text)
                    if val:
                        _ok_or_fail(
                            val == snap,
                            f"{surface} effective gate matches GIT_SNAPSHOT",
                            f"{surface} effective gate {val} != GIT_SNAPSHOT {snap}",
                        )
            elif labels:
                for surface, text in surfaces.items():
                    val = _extract_labeled_value(text, labels)
                    if val:
                        _ok_or_fail(
                            val == snap,
                            f"{surface} {key} matches GIT_SNAPSHOT",
                            f"{surface} {key} {val} != GIT_SNAPSHOT {snap}",
                        )

    return all_ok


def validate_archive_snapshot_agreement(archive_root, all_ok):
    print("\n[ARCHIVE] Snapshot / current-state agreement")

    snapshot_path = archive_root / "GIT_SNAPSHOT.txt"
    state = load_current_state(archive_root)
    if state is None:
        print("  FAIL CURRENT_STATE.json missing/invalid in archive")
        return False

    snapshot_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path.exists() else ""
    snapshot = _parse_git_snapshot(snapshot_text)

    # recorded handoff head
    handoff_head = state.get("handoff_head")
    if handoff_head and handoff_head not in ("__HANDOFF_HEAD__", ""):
        expected = snapshot.get("head", "")
        if expected and handoff_head == expected:
            print(f"  OK   handoff_head {handoff_head[:12]} matches GIT_SNAPSHOT HEAD")
        else:
            print(f"  FAIL CURRENT_STATE.json handoff_head {handoff_head} does not match GIT_SNAPSHOT HEAD {expected}")
            all_ok = False

    # recorded handoff branch
    handoff_branch = state.get("handoff_branch")
    if handoff_branch and handoff_branch not in ("__HANDOFF_BRANCH__", ""):
        expected = snapshot.get("branch", "")
        if expected and handoff_branch == expected:
            print(f"  OK   handoff_branch {handoff_branch} matches GIT_SNAPSHOT branch")
        else:
            print(f"  FAIL CURRENT_STATE.json handoff_branch {handoff_branch} does not match GIT_SNAPSHOT branch {expected}")
            all_ok = False

    return all_ok


def _is_lifecycle_state(state):
    """Return True when state declares canonical merge lifecycle fields."""
    if not state:
        return False
    return all(state.get(k) for k in ("canonical_branch", "delivery_branch", "pre_merge_gate", "post_merge_gate"))


def validate_archive_surface_consistency(archive_root, all_ok):
    print("\n[ARCHIVE] Surface semantic consistency")

    state = load_current_state(archive_root)
    if state is None:
        print("  FAIL CURRENT_STATE.json missing/invalid in archive")
        return False, None

    snapshot_path = archive_root / "GIT_SNAPSHOT.txt"
    snapshot_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path.exists() else ""
    snapshot = _parse_git_snapshot(snapshot_text)

    surfaces = {}
    for rel in ("docs/continuity/CURRENT_HANDOFF.md", "docs/continuity/CURRENT_GIT_STATE.md"):
        p = archive_root / rel
        if p.exists():
            surfaces[rel] = p.read_text(encoding="utf-8")

    # Explicit, fail-closed schema classification. The presence of a
    # GIT_SNAPSHOT.txt lifecycle block forces current-lifecycle enforcement.
    schema_class, schema_errors = _classify_schema(state, snapshot_text, surfaces, mode="archive")
    if schema_errors:
        for err in schema_errors:
            print(f"  FAIL archive schema: {err}")
            all_ok = False

    requires_lifecycle = schema_class == ArchiveSchemaClass.CURRENT_LIFECYCLE
    lifecycle_values, lifecycle_errors = _parse_lifecycle_snapshot(snapshot_text, requires_lifecycle=requires_lifecycle)
    if requires_lifecycle:
        for err in lifecycle_errors:
            print(f"  FAIL GIT_SNAPSHOT.txt lifecycle block: {err}")
            all_ok = False
    snapshot["lifecycle"] = lifecycle_values

    all_ok = _assert_surface_consistency(archive_root, state, surfaces, snapshot, all_ok, schema_class=schema_class)
    return all_ok, schema_class


def live_validation():
    all_ok = True

    if not (REPO_ROOT / ".git").is_dir():
        print("FAIL: .git not available; live mode requires a Git repository")
        return 1

    mode_label = "LIVE"
    print("=" * 60)
    print("anoX V1 Continuity Validation — LIVE REPOSITORY MODE")
    print("=" * 60)

    all_ok = validate_required_files(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_authority_paths(REPO_ROOT, all_ok, mode_label)

    status = git_status()
    if status is None:
        print("\n[LIVE] Git working tree: FAIL — git not found")
        all_ok = False
    elif status.strip() == "":
        print("\n[LIVE] Git working tree: OK clean")
    else:
        print("\n[LIVE] Git working tree: FAIL dirty")
        for line in status.splitlines():
            print(f"       {line}")
        all_ok = False

    branch = git_current_branch()
    head = git_current_head()
    state = load_current_state(REPO_ROOT)
    baseline_branch = state.get("baseline_branch", "main") if state else "main"
    live_baseline_head = git_branch_head(baseline_branch)
    working_tree = "clean" if (status is not None and status.strip() == "") else "dirty"
    live_state = {
        "branch": branch,
        "head": head,
        "working_tree": working_tree,
        "pre_merge_gate": state.get("pre_merge_gate", "") if state else "",
        "post_merge_gate": state.get("post_merge_gate", "") if state else "",
    }

    print(f"\n[LIVE] Branch / HEAD")
    print(f"  current branch: {branch or 'FAIL'}")
    print(f"  current HEAD: {head or 'FAIL'}")
    print(f"  described_head: {(_resolve_described_head(state) or 'unresolved')[:12] if state else 'FAIL'}")
    print(f"  baseline branch: {baseline_branch}")
    print(f"  live baseline HEAD: {live_baseline_head or 'FAIL'}")

    all_ok, effective_gate = validate_state_json(state, REPO_ROOT, all_ok, mode_label, live_branch=branch, live_head=head, mode="live")
    all_ok = validate_baseline_consistency(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_baseline_ancestry(state, live_baseline_head, all_ok, mode_label)
    all_ok = validate_authority_precedence(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_b027a(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_b027b(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_b027c(REPO_ROOT, all_ok, mode_label)
    all_ok = validate_current_state_surfaces(REPO_ROOT, all_ok, mode_label, live_branch=branch, state=state)
    live_state["effective_gate"] = effective_gate or ""
    all_ok = validate_placeholders(REPO_ROOT, all_ok, mode_label, "live", live_state=live_state)
    all_ok, memory_freshness_status = validate_project_memory_freshness(
        REPO_ROOT, all_ok, mode_label, branch, head, state, "live"
    )

    print("\n" + "=" * 60)
    print(f"PROJECT_MEMORY_FRESHNESS: {memory_freshness_status}")
    if all_ok:
        print("LIVE_GIT_VERIFICATION: PASS")
        print("RESULT: PASS — handoff readiness satisfied")
        return 0
    else:
        print("LIVE_GIT_VERIFICATION: FAIL")
        print("RESULT: FAIL — handoff readiness NOT satisfied")
        return 1


def archive_validation(archive_root):
    all_ok = True

    print("=" * 60)
    print("anoX V1 Continuity Validation — HANDOFF ARCHIVE MODE")
    print("=" * 60)
    print(f"Archive root: {archive_root}")

    all_ok = validate_required_files(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_authority_paths(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_archive_manifests(archive_root, all_ok)
    all_ok = validate_archive_snapshot_agreement(archive_root, all_ok)
    all_ok, schema_class = validate_archive_surface_consistency(archive_root, all_ok)

    state = load_current_state(archive_root)
    all_ok, _ = validate_state_json(state, archive_root, all_ok, "ARCHIVE", schema_class=schema_class)
    all_ok = validate_b027a(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_b027b(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_b027c(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_baseline_consistency(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_authority_precedence(archive_root, all_ok, "ARCHIVE")
    all_ok = validate_placeholders(archive_root, all_ok, "ARCHIVE", "archive", live_state=None)
    all_ok = validate_current_state_surfaces(archive_root, all_ok, "ARCHIVE", live_branch=None, state=state)
    archive_head = state.get("handoff_head") if state else None
    archive_branch = state.get("handoff_branch") if state else None
    all_ok, memory_freshness_status = validate_project_memory_freshness(
        archive_root, all_ok, "ARCHIVE", archive_branch, archive_head, state, "archive"
    )

    print("\n" + "=" * 60)
    print(f"PROJECT_MEMORY_FRESHNESS: {memory_freshness_status}")
    if all_ok:
        print("HANDOFF_ARCHIVE_VALIDATION: PASS")
        print("LIVE_GIT_VERIFICATION: UNAVAILABLE")
        print("ARCHIVE AUTHENTICITY: UNVERIFIED — NO EXTERNAL TRUST ANCHOR PROVIDED")
        print("RESULT: PASS — archive internal validation satisfied")
        return 0
    else:
        print("HANDOFF_ARCHIVE_VALIDATION: FAIL")
        print("LIVE_GIT_VERIFICATION: UNAVAILABLE")
        print("ARCHIVE AUTHENTICITY: UNVERIFIED — NO EXTERNAL TRUST ANCHOR PROVIDED")
        print("RESULT: FAIL — archive handoff validation NOT satisfied")
        return 1


def main():
    args = parse_args()
    mode = select_mode(args)
    print(f"SELECTED MODE: {mode}")

    if mode == "live":
        return live_validation()
    elif mode == "archive":
        root = args.archive or REPO_ROOT
        return archive_validation(root)
    else:
        print("FAIL: could not determine a validation mode")
        return 1


if __name__ == "__main__":
    sys.exit(main())
