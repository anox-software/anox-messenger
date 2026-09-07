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
