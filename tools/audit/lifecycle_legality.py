#!/usr/bin/env python3
"""Canonical finding-lifecycle legality helpers for the anoX audit validators.

Historical validators must distinguish *snapshot expectations* (the state a
given milestone recorded) from *current live lifecycle state* (the registry as
legally evolved). A finding may legally progress

    Open -> Ready For Retest -> Closed

only when each transition is backed by recorded remediation evidence and, for
closure, a passing recorded DELTA retest covering the finding. Any other
mutation — unauthorized closure, disappearance, status regression, invented
status — must still fail.

This module is the single source of truth for that check so all validators
agree on the legal-transition contract. It also centralizes the structured
Claude-audit-trigger detection (a prose prohibition such as
"Immediate Claude/security audit" inside a task's non_goals is NOT a trigger;
only structured trigger/provider fields count).
"""

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Finding status model
# ---------------------------------------------------------------------------

OPEN_STATUS = "Open"
RFR_STATUS = "Ready For Retest"
TERMINAL_STATUSES = frozenset({"Closed", "Accepted Risk", "Deferred", "Superseded"})
LEGAL_STATUSES = frozenset(
    {
        "Open",
        "Triaged",
        "Remediation In Progress",
        "Ready For Retest",
        "Closed",
        "Accepted Risk",
        "Deferred",
        "Superseded",
    }
)

FIX_REF_RE = re.compile(r"(?:FIX|FIXATION|REMEDIATION)-?\d+|LEGACY-FIX-\d+", re.IGNORECASE)
RETEST_REF_RE = re.compile(r"RETEST-\d+", re.IGNORECASE)
GIT_REF_RE = re.compile(r"^git:[0-9a-f]{4,40}$")
VALIDATOR_REF_RE = re.compile(r"validate_\w+\.py|tools/audit/", re.IGNORECASE)

# Fields that carry prose (scope text, prohibitions, notes, titles) and must
# NEVER be treated as an audit trigger. A prohibition that *mentions* an
# external model/audit provider is not an authorization or a trigger.
_PROSE_FIELD_DENYLIST = frozenset(
    {
        "scope",
        "non_goals",
        "notes",
        "title",
        "summary",
        "description",
        "stop_conditions",
        "authority_refs",
        "required_evidence",
        "closure_notes",
        "evidence",
        "rationale",
        "security_reassessment",
        "allowed_paths",
        "forbidden_paths",
    }
)

# Structured fields that can represent an actual Claude/external-audit trigger
# or provider selection. Only these may fire the check.
_TRIGGER_FIELDS = frozenset(
    {
        "claude_audit_triggered",
        "claude_audit",
        "external_audit_triggered",
        "security_audit_trigger",
        "security_audit_triggered",
        "security_reassessment_trigger",
        "immediate_security_audit",
        "requires_claude_audit",
    }
)
_PROVIDER_FIELDS = frozenset(
    {
        "provider",
        "model",
        "model_provider",
        "model_name",
        "audit_provider",
        "audit_model",
    }
)
_PROVIDER_NAME_RE = re.compile(r"claude|anthropic", re.IGNORECASE)


def load_jsonl(path):
    p = Path(path)
    if not p.is_absolute():
        p = REPO / p
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def load_json(path):
    p = Path(path)
    if not p.is_absolute():
        p = REPO / p
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Remediation / closure evidence
# ---------------------------------------------------------------------------


def _has_fix_reference(refs):
    return any(isinstance(r, str) and FIX_REF_RE.search(r) for r in refs)


def _has_retest_reference(refs):
    return any(isinstance(r, str) and RETEST_REF_RE.search(r) for r in refs)


def _has_validator_reference(refs):
    return any(isinstance(r, str) and VALIDATOR_REF_RE.search(r) for r in refs)


def _has_git_reference(refs):
    return any(isinstance(r, str) and GIT_REF_RE.match(r) for r in refs)


def has_remediation_evidence(f):
    """A finding may be 'Ready For Retest' only when recorded remediation
    evidence exists: a FIX/remediation reference plus a validator/tooling
    reference in remediation_refs."""
    refs = f.get("remediation_refs") or []
    return _has_fix_reference(refs) and _has_validator_reference(refs)


def passing_retests_covering(fid, audits):
    """Return the DELTA audit records with result PASS that cover `fid`."""
    covered = []
    for a in audits or []:
        if a.get("result") != "PASS":
            continue
        ids = set()
        if a.get("finding_id"):
            ids.add(a["finding_id"])
        for key in ("finding_ids", "closed_findings", "closure_eligible_ids", "targets"):
            v = a.get(key)
            if isinstance(v, list):
                ids.update(x for x in v if isinstance(x, str))
        fnd = a.get("findings")
        if isinstance(fnd, list):
            ids.update(x for x in fnd if isinstance(x, str))
        elif isinstance(fnd, dict):
            ids.update(fnd.keys())
        if fid in ids:
            covered.append(a)
    return covered


def has_legal_closure(f, audits):
    """A finding may be in a terminal status only when the full transition
    chain is recorded:

    - non-empty closure_actor;
    - closure_evidence containing a FIX/remediation reference, a RETEST
      reference, and at least one pinned git SHA;
    - a recorded DELTA retest with result PASS that covers the finding.
    """
    reasons = []
    if not f.get("closure_actor"):
        reasons.append("missing closure_actor")
    ev = f.get("closure_evidence") or []
    if not _has_fix_reference(ev):
        reasons.append("closure_evidence missing FIX/remediation reference")
    if not _has_retest_reference(ev):
        reasons.append("closure_evidence missing RETEST reference")
    if not _has_git_reference(ev):
        reasons.append("closure_evidence missing pinned git SHA")
    if not passing_retests_covering(f.get("finding_id"), audits):
        reasons.append("no recorded PASS delta retest covers the finding")
    return (not reasons), reasons


def finding_status_legal(f, audits):
    """Return (ok, reason) for the current live lifecycle state of a finding.

    Snapshot history is preserved separately by each validator; this check
    answers only whether the *current* status is a legal live state.
    """
    st = f.get("status")
    fid = f.get("finding_id", "?")
    if st not in LEGAL_STATUSES:
        return False, f"{fid} has illegal/unknown status {st!r}"
    if st == OPEN_STATUS:
        # An Open finding carrying closure evidence is a silent reopen —
        # regressions of recorded closures are not legal.
        if f.get("closure_evidence"):
            return False, f"{fid} reopened to Open while retaining closure_evidence"
        return True, "Open"
    if st == RFR_STATUS:
        if f.get("closure_evidence"):
            return False, f"{fid} Ready For Retest while retaining closure_evidence"
        if has_remediation_evidence(f):
            return True, "Ready For Retest with recorded remediation evidence"
        return False, f"{fid} Ready For Retest without FIX/validator remediation evidence"
    if st in TERMINAL_STATUSES:
        ok, reasons = has_legal_closure(f, audits)
        if ok:
            return True, f"{st} with complete remediation->retest closure chain"
        return False, f"{fid} {st} without legal closure chain: {'; '.join(reasons)}"
    # Intermediate workflow states need remediation intent evidence.
    if has_remediation_evidence(f):
        return True, f"{st} with recorded remediation evidence"
    return False, f"{fid} status {st} without remediation evidence"


def canonical_finding_ids(findings, audits):
    """Return the set of canonical finding IDs.

    The 36 ANOX-MAINARCH-001..036 IDs are canonical from the main architecture
    audit. Any other finding is canonical only when it was introduced by a
    recorded audit (its `discovered_in` references an existing audit_id) or is
    explicitly listed inside a recorded audit's findings mapping.
    """
    audit_ids = {a.get("audit_id") for a in audits or [] if a.get("audit_id")}
    audit_listed = set()
    for a in audits or []:
        fnd = a.get("findings")
        if isinstance(fnd, dict):
            audit_listed.update(fnd.keys())
        elif isinstance(fnd, list):
            audit_listed.update(x for x in fnd if isinstance(x, str))
        for key in ("finding_ids", "new_findings", "closed_findings", "closure_eligible_ids"):
            v = a.get(key)
            if isinstance(v, list):
                audit_listed.update(x for x in v if isinstance(x, str))
            elif isinstance(v, dict):
                audit_listed.update(v.keys())
        cand = a.get("candidate_mapping")
        if isinstance(cand, dict):
            audit_listed.update(cand.values())
    ids = set()
    for f in findings:
        fid = f.get("finding_id")
        if not fid:
            continue
        if fid.startswith("ANOX-MAINARCH-"):
            ids.add(fid)
        elif fid in audit_listed:
            ids.add(fid)
        elif f.get("discovered_in") in audit_ids:
            ids.add(fid)
    return ids


# ---------------------------------------------------------------------------
# Structured Claude / external-audit trigger detection
# ---------------------------------------------------------------------------


def _scan_structured_fields(record, label, out):
    """Inspect only structured trigger/provider fields of a record.

    Prose fields (non_goals, scope, notes, stop_conditions, ...) are
    deliberately skipped: a prohibition that names a provider is not a
    trigger."""
    if not isinstance(record, dict):
        return
    for key, value in record.items():
        k = str(key).lower()
        if key in _PROSE_FIELD_DENYLIST or k in _PROSE_FIELD_DENYLIST:
            continue
        if k in _TRIGGER_FIELDS:
            if value not in (None, "", False, "NO", "no", "NONE"):
                out.append(f"{label}: trigger field {key}={value!r}")
        elif k in _PROVIDER_FIELDS:
            if isinstance(value, str) and _PROVIDER_NAME_RE.search(value):
                out.append(f"{label}: provider field {key}={value!r}")


def detect_claude_trigger(tasks=None, audits=None, workforce_state=None):
    """Return a list of structured evidence that a Claude/external audit was
    triggered or authorized. Empty list = no trigger.

    Deliberately does NOT scan prose — a non_goal such as
    'Immediate Claude/security audit' is a prohibition, not a trigger.
    """
    evidence = []
    for t in tasks or []:
        _scan_structured_fields(t, f"task {t.get('task_id', '?')}", evidence)
    for a in audits or []:
        _scan_structured_fields(a, f"audit {a.get('audit_id', '?')}", evidence)
    ws = workforce_state or {}
    if isinstance(ws, dict):
        _scan_structured_fields(ws, "WORKFORCE_STATE", evidence)
        for key in ("required_audits", "completed_audit_ids"):
            for item in ws.get(key) or []:
                if isinstance(item, str) and _PROVIDER_NAME_RE.search(item):
                    evidence.append(f"WORKFORCE_STATE {key} contains provider-named audit {item!r}")
    return evidence


# ---------------------------------------------------------------------------
# Next canonical gate resolution
# ---------------------------------------------------------------------------


def uncompleted_required_audits(ws):
    """Return required Final Pre-Product audits (canonical order) that are not
    in completed_audit_ids."""
    fpa = (ws or {}).get("final_pre_product_audit", {})
    required = fpa.get("required_audits") or []
    completed = set(fpa.get("completed_audit_ids") or [])
    return [a for a in required if a not in completed]


def next_canonical_gate(ws):
    """The first uncompleted required audit in canonical order, or None."""
    remaining = uncompleted_required_audits(ws)
    return remaining[0] if remaining else None


def gate_is_legal_successor(ws, gate, lifecycle_tokens=("LEGACY", "MAINARCH", "RETEST", "FIX")):
    """A gate is a legal successor when it names an uncompleted required audit
    (or its task-level lifecycle step) or an authorized lifecycle token."""
    gate = gate or ""
    remaining = uncompleted_required_audits(ws)
    if any(token in gate for token in remaining):
        return True
    if any(tok in gate.upper() for tok in lifecycle_tokens):
        return True
    return False


# ---------------------------------------------------------------------------
# Merge-aware canonical delivery proof
# ---------------------------------------------------------------------------


def _git(args, cwd=REPO):
    try:
        return subprocess.check_output(["git"] + list(args), cwd=cwd, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None


def _git_is_ancestor(ancestor, descendant, cwd=REPO):
    return subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant],
                          cwd=cwd, capture_output=True).returncode == 0


def _git_merge_parents(sha, cwd=REPO):
    out = _git(["rev-list", "--parents", "-n", "1", sha], cwd=cwd)
    if not out:
        return None
    parts = out.split()
    if len(parts) < 2:
        return None
    return parts[1:]


def git_find_canonical_merge(described_head, live_head, canonical_branch="main",
                             delivery_branch=None, cwd=REPO):
    """Identify the canonical integration merge M and its delivery/canonical parents.

    Returns (merge_sha, delivery_parent, canonical_parent) or (None, None, None).
    Only two-parent merges are supported. Ambiguous topologies fail closed.
    """
    out = _git(["rev-list", "--merges", "--first-parent",
                f"{described_head}..{live_head}"], cwd=cwd)
    if out is None:
        return None, None, None
    candidates = out.splitlines()
    if not candidates:
        return None, None, None

    canonical_ref = _git(["rev-parse", canonical_branch], cwd=cwd) or canonical_branch
    qualifying = []
    for merge_sha in candidates:
        parents = _git_merge_parents(merge_sha, cwd=cwd)
        if not parents:
            continue
        if len(parents) != 2:
            return None, None, None

        has_desc = [_git_is_ancestor(described_head, p, cwd=cwd) for p in parents]
        if has_desc.count(True) != 1:
            continue

        delivery_idx = has_desc.index(True)
        delivery_parent = parents[delivery_idx]
        canonical_parent = parents[1 - delivery_idx]

        if not _git_is_ancestor(canonical_parent, canonical_ref, cwd=cwd):
            continue
        if not _git_is_ancestor(described_head, delivery_parent, cwd=cwd):
            continue
        qualifying.append((merge_sha, delivery_parent, canonical_parent))

    if len(qualifying) != 1:
        return None, None, None
    return qualifying[0]


def canonical_two_commit_delivery(base_sha, described_head, live_head,
                                  canonical_branch="main", delivery_branch=None,
                                  cwd=REPO, metadata_allowlist=None):
    """Verify the historical two-commit delivery invariant.

    Returns (ok, delivery_parent, substantive_head, reason) where:
      - ok is True if exactly two task-authored commits exist between base_sha
        and the delivery parent of the canonical merge;
      - delivery_parent is the parent commit that contains the delivery lineage;
      - substantive_head is the first of the two task-authored commits.
    """
    if live_head is None:
        live_head = _git(["rev-parse", "HEAD"], cwd=cwd)
    if not live_head:
        return False, None, None, "cannot resolve live HEAD"

    if not _git_is_ancestor(base_sha, live_head, cwd=cwd):
        return False, None, None, f"base {base_sha[:12]} is not an ancestor of live {live_head[:12]}"

    # If the described_head is the live head, we are on the unmerged delivery branch.
    if live_head == described_head:
        delivery_parent = live_head
    else:
        # First, try the unmerged delivery-branch case: live_head is exactly the
        # metadata commit and its parent is the substantive described_head.
        parents = _git_merge_parents(live_head, cwd=cwd)
        if parents and len(parents) == 1 and parents[0] == described_head:
            count = _git(["rev-list", "--count", f"{base_sha}..{live_head}"], cwd=cwd)
            if count == "2":
                delivery_parent = live_head
            else:
                return False, None, None, f"expected exactly 2 task-authored commits above base, found {count}"
        else:
            merge, delivery_parent, canonical_parent = git_find_canonical_merge(
                described_head, live_head, canonical_branch=canonical_branch,
                delivery_branch=delivery_branch, cwd=cwd
            )
            if merge is None:
                return False, None, None, "cannot identify canonical integration merge"

    count = _git(["rev-list", "--count", f"{base_sha}..{delivery_parent}"], cwd=cwd)
    if count is None:
        return False, None, None, "cannot count commits between base and delivery parent"
    if count != "2":
        return False, None, None, f"expected exactly 2 task-authored commits above base, found {count}"

    # Verify topology: delivery_parent parent is the substantive head, which is a
    # direct child of the base.
    parents = _git_merge_parents(delivery_parent, cwd=cwd)
    if not parents or len(parents) != 1:
        return False, None, None, "delivery parent is not a single-parent commit"
    substantive_head = parents[0]
    if substantive_head != described_head:
        return False, None, None, f"delivery parent parent {substantive_head[:12]} != described_head {described_head[:12]}"
    if not _git_is_ancestor(base_sha, substantive_head, cwd=cwd):
        return False, None, None, "substantive head is not a descendant of the base"

    # Metadata commit may only touch metadata-allowlisted files.
    if metadata_allowlist:
        meta_files = _git(["diff", "--name-only", f"{delivery_parent}~1", delivery_parent], cwd=cwd)
        if meta_files is None:
            return False, None, None, "cannot read metadata commit diff"
        bad = [p for p in meta_files.splitlines() if p not in metadata_allowlist]
        if bad:
            return False, None, None, f"metadata commit touches non-metadata files: {bad}"

    return True, delivery_parent, substantive_head, "exact two-commit delivery proven"


def canonical_integration_delivery(base_sha, merged_head, merged_base, described_head,
                                   live_head, cwd=REPO, metadata_allowlist=None,
                                   s1_substantive_sha=None, s1_metadata_sha=None,
                                   correction_task=None):
    """Verify the canonical *integration* delivery invariant (REMEDIATION-S1-
    CANONICAL-INTEGRATION-001 era extension, extended by
    REMEDIATION-S1-PRE-RATIFICATION-CORRECTIONS-001).

    Topology (first-parent chain above ``base_sha``)::

        base ── M ── C1 ── C2            (original delivery)
        base ── M ── C1 ── C2 ── D1 ── D2   (delivery + authorized correction pair)
                │
                └── merged_head (pinned foreign delivery, unmodified)

    Requirements, all fail-closed:
      * ``base_sha`` and ``merged_head`` are ancestors of the live head;
      * the first-parent chain above base is exactly [M, C1, C2] — or exactly
        [M, C1, C2, D1, D2] when ``correction_task`` is given (a Human-authorized
        pre-ratification correction pair on the same delivery branch);
      * M is a two-parent merge whose parents are exactly (base_sha, merged_head);
      * C1 (substantive) and C2 (metadata) are single-parent;
      * without a correction pair, C1 == described_head; with one, C1 must equal
        the pinned ``s1_substantive_sha``, C2 must equal the pinned
        ``s1_metadata_sha``, and the correction substantive D1 == described_head;
      * D1 and D2 are single-parent; D2 touches only metadata-allowlisted paths;
      * the only commits above base that are not on the first-parent chain are
        exactly the pinned foreign delivery ``merged_base..merged_head`` — no
        other history is smuggled in through the merge;
      * ``merged_head`` itself is exactly two commits above ``merged_base``;
      * C2 touches only metadata-allowlisted paths.
    Returns (ok, merge_sha, substantive_head, metadata_head, reason).
    """
    if live_head is None:
        live_head = _git(["rev-parse", "HEAD"], cwd=cwd)
    if not live_head:
        return False, None, None, None, "cannot resolve live HEAD"
    for label, sha in (("base", base_sha), ("merged head", merged_head), ("merged base", merged_base)):
        if not _git_is_ancestor(sha, live_head, cwd=cwd):
            return False, None, None, None, f"{label} {sha[:12]} is not an ancestor of live {live_head[:12]}"
    if not _git_is_ancestor(merged_base, merged_head, cwd=cwd):
        return False, None, None, None, "merged base is not an ancestor of merged head"
    if _git_is_ancestor(merged_head, base_sha, cwd=cwd):
        return False, None, None, None, "merged head is already contained in base (nothing to integrate)"

    fp = _git(["rev-list", "--first-parent", f"{base_sha}..{live_head}"], cwd=cwd)
    chain = fp.splitlines() if fp else []
    corr_sub = corr_meta = None
    if len(chain) == 3:
        metadata_head, substantive_head, merge_sha = chain[0], chain[1], chain[2]
    elif len(chain) == 5 and correction_task and s1_substantive_sha and s1_metadata_sha:
        corr_meta, corr_sub, metadata_head, substantive_head, merge_sha = chain
    else:
        shape = "3 first-parent commits above base (merge + 2 task-authored)"
        if correction_task:
            shape += " or 5 (incl. the authorized pre-ratification correction pair)"
        return False, None, None, None, f"expected exactly {shape}, found {len(chain)}"

    mparents = _git_merge_parents(merge_sha, cwd=cwd) or []
    if len(mparents) != 2:
        return False, None, None, None, "integration commit is not a two-parent merge"
    if mparents[0] != base_sha or mparents[1] != merged_head:
        return False, None, None, None, (
            f"integration merge parents {[p[:12] for p in mparents]} != (base, pinned merged head)")
    for label, sha in (("substantive", substantive_head), ("metadata", metadata_head)):
        ps = _git_merge_parents(sha, cwd=cwd) or []
        if len(ps) != 1:
            return False, None, None, None, f"{label} commit is not a single-parent commit"

    if corr_sub is not None:
        # Correction phase: the S1 delivery commits are pinned exactly and the
        # correction substantive is bound to CURRENT_STATE's described_head.
        if substantive_head != s1_substantive_sha:
            return False, None, None, None, (
                f"S1 substantive commit {substantive_head[:12]} != pinned {s1_substantive_sha[:12]}")
        if metadata_head != s1_metadata_sha:
            return False, None, None, None, (
                f"S1 metadata commit {metadata_head[:12]} != pinned {s1_metadata_sha[:12]}")
        for label, sha in (("correction substantive", corr_sub), ("correction metadata", corr_meta)):
            ps = _git_merge_parents(sha, cwd=cwd) or []
            if len(ps) != 1:
                return False, None, None, None, f"{label} commit is not a single-parent commit"
        if corr_sub != described_head:
            return False, None, None, None, (
                f"correction substantive commit {corr_sub[:12]} != described_head {described_head[:12]}")
        if metadata_allowlist:
            corr_files = _git(["diff", "--name-only", f"{corr_meta}~1", corr_meta], cwd=cwd)
            if corr_files is None:
                return False, None, None, None, "cannot read correction metadata commit diff"
            bad = [p for p in corr_files.splitlines() if p not in metadata_allowlist]
            if bad:
                return False, None, None, None, f"correction metadata commit touches non-metadata files: {bad}"
    else:
        if substantive_head != described_head:
            return False, None, None, None, (
                f"substantive commit {substantive_head[:12]} != described_head {described_head[:12]}")
        if s1_substantive_sha and substantive_head != s1_substantive_sha:
            return False, None, None, None, (
                f"S1 substantive commit {substantive_head[:12]} != pinned {s1_substantive_sha[:12]}")
        if s1_metadata_sha and metadata_head != s1_metadata_sha:
            return False, None, None, None, (
                f"S1 metadata commit {metadata_head[:12]} != pinned {s1_metadata_sha[:12]}")

    all_above = set((_git(["rev-list", f"{base_sha}..{live_head}"], cwd=cwd) or "").splitlines())
    foreign = set((_git(["rev-list", f"{merged_base}..{merged_head}"], cwd=cwd) or "").splitlines())
    if len(foreign) != 2:
        return False, None, None, None, f"pinned foreign delivery must be exactly 2 commits, found {len(foreign)}"
    extra = all_above - set(chain) - foreign
    if extra:
        return False, None, None, None, f"unexpected commits integrated beyond pinned delivery: {sorted(x[:12] for x in extra)}"

    if metadata_allowlist:
        meta_files = _git(["diff", "--name-only", f"{metadata_head}~1", metadata_head], cwd=cwd)
        if meta_files is None:
            return False, None, None, None, "cannot read metadata commit diff"
        bad = [p for p in meta_files.splitlines() if p not in metadata_allowlist]
        if bad:
            return False, None, None, None, f"metadata commit touches non-metadata files: {bad}"
    return True, merge_sha, substantive_head, metadata_head, "exact integration delivery proven"


def historical_file_at(sha, rel_path, cwd=REPO):
    """Return the contents of a repository file at a specific commit, or None."""
    out = _git(["show", f"{sha}:{rel_path}"], cwd=cwd)
    if out is None:
        return None
    return out


def historical_json_at(sha, rel_path, cwd=REPO):
    """Return a JSON object parsed from a repository file at a specific commit."""
    text = historical_file_at(sha, rel_path, cwd=cwd)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
