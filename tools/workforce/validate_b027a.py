#!/usr/bin/env python3
"""B027-A workforce foundation validator.

Validates the B027-A foundation deterministically and fail-closed.
No network access. No external dependencies beyond Python 3 stdlib.
"""

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFORCE_DIR = REPO_ROOT / "docs" / "workforce"
SCHEMA_DIR = WORKFORCE_DIR / "schemas"
REGISTRY_DIR = WORKFORCE_DIR / "registries"

B027_AUTHORITY = REPO_ROOT / "docs" / "authority" / "B027_AI_WORKFORCE_GOVERNANCE.md"
RUNTIME_CONTRACT = WORKFORCE_DIR / "ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md"
MODEL_POLICY = WORKFORCE_DIR / "MODEL_PROVIDER_POLICY.md"
ROLE_REGISTRY = REGISTRY_DIR / "roles.json"
WORKFORCE_STATE = WORKFORCE_DIR / "WORKFORCE_STATE.json"

REQUIRED_FILE_RELS = [
    "docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md",
    "docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md",
    "docs/workforce/MODEL_PROVIDER_POLICY.md",
    "docs/workforce/registries/roles.json",
    "docs/workforce/WORKFORCE_STATE.json",
    "docs/workforce/schemas/task-package.schema.json",
    "docs/workforce/schemas/finding.schema.json",
    "docs/workforce/schemas/decision.schema.json",
    "docs/workforce/schemas/run.schema.json",
    "docs/workforce/schemas/derived-work.schema.json",
    "docs/workforce/schemas/workforce-state.schema.json",
    "docs/workforce/registries/tasks.jsonl",
    "docs/workforce/registries/findings.jsonl",
    "docs/workforce/registries/decisions.jsonl",
    "docs/workforce/registries/runs.jsonl",
    "docs/workforce/registries/derived_work.jsonl",
]

TASK_STATES = [
    "Candidate",
    "Authorized",
    "In Progress",
    "Awaiting Evidence",
    "Awaiting Review",
    "Ready For Remote",
    "Awaiting Human Remote Action",
    "CI Pending",
    "Ready To Merge",
    "Merged",
    "Closed",
    "Blocked",
]

FINDING_STATES = [
    "Open",
    "Triaged",
    "Remediation In Progress",
    "Ready For Retest",
    "Closed",
    "Accepted Risk",
    "Deferred",
    "Duplicate",
    "Superseded",
]

EVIDENCE_LEVELS = ["E0", "E1", "E2", "E3", "E4"]
EGRESS_LEVELS = ["D0", "D1", "D2", "D3"]
PRIORITY_LEVELS = ["P0", "P1", "P2", "P3"]
SECURITY_CLASSES = ["S0", "S1", "S2", "S3", "S4"]
REMOTE_PERMISSIONS = ["NONE", "READ_ONLY", "HUMAN_REMOTE_ACTION_REQUIRED"]
RUN_RESULTS = ["PASS", "FAIL", "PARTIAL", "BLOCKED", "IN_PROGRESS"]

_STABLE_ID_RE = re.compile(r"^ANOX-(TASK|FINDING|DECISION|RUN|WORK|MAINARCH|LEGACY|WORKFORCE|SECURITY)-[A-Z0-9-]+$")
_ROLE_ID_RE = re.compile(r"^ROLE-(0[0-9][0-9]|1[0-9])$")
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_START_SHA_UNBOUND_RE = re.compile(r"^NOT YET BOUND")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    entries = []
    if not path.exists():
        return entries
    if path.stat().st_size == 0:
        return entries
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def fail(msg, errors):
    errors.append(msg)


def validate_required_files(errors):
    for rel in REQUIRED_FILE_RELS:
        p = REPO_ROOT / rel
        if p.exists():
            print(f"  OK   {rel}")
        else:
            fail(f"missing required file: {rel}", errors)


def validate_schemas(errors):
    for p in SCHEMA_DIR.glob("*.schema.json"):
        try:
            data = load_json(p)
            if not isinstance(data, dict):
                fail(f"schema {p.name} is not a JSON object", errors)
                continue
            if data.get("$schema") is None:
                fail(f"schema {p.name} missing $schema", errors)
                continue
            print(f"  OK   schema parses: {p.name}")
        except json.JSONDecodeError as e:
            fail(f"schema {p.name} is not valid JSON: {e}", errors)


def validate_role_registry(errors):
    try:
        data = load_json(ROLE_REGISTRY)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        fail(f"role registry is not valid JSON: {e}", errors)
        return None

    roles = data.get("roles", [])
    seen_ids = set()
    expected_ids = {f"ROLE-{i:03d}" for i in range(1, 20)}
    actual_ids = set()

    if data.get("schema_version") is None:
        fail("role registry missing schema_version", errors)

    for role in roles:
        rid = role.get("role_id")
        if not rid:
            fail("role entry missing role_id", errors)
            continue
        actual_ids.add(rid)
        if rid in seen_ids:
            fail(f"duplicate role_id: {rid}", errors)
        seen_ids.add(rid)
        if not _ROLE_ID_RE.match(rid):
            fail(f"malformed role_id: {rid}", errors)
        if role.get("activation_class") not in ("active", "gate_activated", "dormant"):
            fail(f"role {rid} has unknown activation_class", errors)

    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    for m in sorted(missing):
        fail(f"role registry missing {m}", errors)
    for e in sorted(extra):
        fail(f"role registry contains unexpected role {e}", errors)

    active = set(data.get("activation_classes", {}).get("active", []))
    gate = set(data.get("activation_classes", {}).get("gate_activated", []))
    dormant = set(data.get("activation_classes", {}).get("dormant", []))

    if active != {"ROLE-001", "ROLE-002", "ROLE-003", "ROLE-004"}:
        fail(f"active roles mismatch: {sorted(active)}", errors)
    if gate != {"ROLE-005", "ROLE-007", "ROLE-008", "ROLE-009", "ROLE-010"}:
        fail(f"gate-activated roles mismatch: {sorted(gate)}", errors)
    expected_dormant = {
        "ROLE-006",
        "ROLE-011",
        "ROLE-012",
        "ROLE-013",
        "ROLE-014",
        "ROLE-015",
        "ROLE-016",
        "ROLE-017",
        "ROLE-018",
        "ROLE-019",
    }
    if dormant != expected_dormant:
        fail(f"dormant roles mismatch: {sorted(dormant)}", errors)

    return data


def _check_known_values(obj, field, allowed, label, errors):
    value = obj.get(field)
    if value is not None and value not in allowed:
        fail(f"{label} has unknown {field}: {value}", errors)
        return False
    return True


def _check_sha(field, obj, label, errors, required=True):
    value = obj.get(field)
    if not value and not required:
        return True
    if value and _START_SHA_UNBOUND_RE.match(value):
        # Unbound start_sha is permitted only for Candidate tasks awaiting
        # human authorization of a future base.
        if obj.get("status") == "Candidate":
            return True
        fail(f"{label} {field} unbound but task is not Candidate", errors)
        return False
    if not value or not _SHA40_RE.match(value):
        fail(f"{label} {field} malformed: {value}", errors)
        return False
    return True


def _check_stable_id(field, obj, label, prefix, errors):
    value = obj.get(field)
    if not value:
        fail(f"{label} missing {field}", errors)
        return None
    prefixes = prefix if isinstance(prefix, (list, tuple)) else (prefix,)
    if not _STABLE_ID_RE.match(value) or not any(value.startswith(p) for p in prefixes):
        fail(f"{label} {field} malformed: {value}", errors)
        return None
    return value


def _check_date(field, obj, label, errors, required=True, datetime=False):
    value = obj.get(field)
    if not value and not required:
        return True
    pattern = _DATETIME_RE if datetime else _DATE_RE
    if not value or not pattern.match(value):
        fail(f"{label} {field} malformed: {value}", errors)
        return False
    return True


def validate_task_package(tp, idx, errors, known_task_ids=None, known_role_ids=None):
    label = f"tasks.jsonl line {idx}"

    if not tp.get("task_id"):
        fail(f"{label} missing task_id", errors)
    else:
        _check_stable_id("task_id", tp, label, "ANOX-TASK-", errors)

    for field in ("title", "scope"):
        if not tp.get(field):
            fail(f"{label} missing {field}", errors)

    rid = tp.get("role_id")
    if not rid or not _ROLE_ID_RE.match(rid) or (known_role_ids and rid not in known_role_ids):
        fail(f"{label} unknown or malformed role_id: {rid}", errors)

    _check_sha("start_sha", tp, label, errors)

    if not tp.get("branch"):
        fail(f"{label} missing branch", errors)

    allowed = tp.get("allowed_paths")
    if not isinstance(allowed, list) or len(allowed) == 0:
        fail(f"{label} allowed_paths missing or empty", errors)

    non_goals = tp.get("non_goals")
    if not isinstance(non_goals, list):
        fail(f"{label} non_goals must be a list", errors)

    _check_known_values(tp, "security_class", SECURITY_CLASSES, label, errors)
    _check_known_values(tp, "data_egress", EGRESS_LEVELS, label, errors)
    _check_known_values(tp, "priority", PRIORITY_LEVELS, label, errors)
    _check_known_values(tp, "required_evidence", EVIDENCE_LEVELS, label, errors)
    _check_known_values(tp, "remote_permission", REMOTE_PERMISSIONS, label, errors)
    _check_known_values(tp, "status", TASK_STATES, label, errors)

    reviewer = tp.get("reviewer_role")
    if reviewer and (not _ROLE_ID_RE.match(reviewer) or (known_role_ids and reviewer not in known_role_ids)):
        fail(f"{label} unknown reviewer_role: {reviewer}", errors)

    if reviewer and reviewer == rid:
        fail(f"{label} writer and independent reviewer are the same role: {rid}", errors)

    authority_refs = tp.get("authority_refs")
    if not isinstance(authority_refs, list) or len(authority_refs) == 0:
        fail(f"{label} authority_refs missing or empty", errors)

    stop_conditions = tp.get("stop_conditions")
    if not isinstance(stop_conditions, list) or len(stop_conditions) == 0:
        fail(f"{label} stop_conditions missing or empty", errors)

    _check_date("created_at", tp, label, errors)

    if tp.get("data_egress") == "D4":
        fail(f"{label} assigns prohibited D4 egress to AI", errors)
    if tp.get("remote_permission") == "AI_WRITE" or tp.get("remote_permission") not in REMOTE_PERMISSIONS:
        # already caught by enum check; this is an explicit guard
        pass


def validate_registries(roles_data, errors):
    known_role_ids = {r["role_id"] for r in roles_data.get("roles", [])} if roles_data else set()
    known_task_ids = set()
    known_finding_ids = set()
    known_decision_ids = set()
    known_run_ids = set()
    known_work_ids = set()

    tasks = load_jsonl(REGISTRY_DIR / "tasks.jsonl")
    for idx, tp in enumerate(tasks, start=1):
        validate_task_package(tp, idx, errors, known_task_ids, known_role_ids)
        if tp.get("task_id"):
            if tp["task_id"] in known_task_ids:
                fail(f"duplicate task_id: {tp['task_id']}", errors)
            known_task_ids.add(tp["task_id"])

    for name, path, prefix, seen in (
        ("findings", REGISTRY_DIR / "findings.jsonl", ("ANOX-FINDING-", "ANOX-MAINARCH-", "ANOX-LEGACY-", "ANOX-WORKFORCE-", "ANOX-SECURITY-"), known_finding_ids),
        ("decisions", REGISTRY_DIR / "decisions.jsonl", "ANOX-DECISION-", known_decision_ids),
        ("runs", REGISTRY_DIR / "runs.jsonl", "ANOX-RUN-", known_run_ids),
        ("derived_work", REGISTRY_DIR / "derived_work.jsonl", "ANOX-WORK-", known_work_ids),
    ):
        entries = load_jsonl(path)
        for idx, obj in enumerate(entries, start=1):
            label = f"{name}.jsonl line {idx}"
            sid = _check_stable_id("finding_id" if name == "findings" else "decision_id" if name == "decisions" else "run_id" if name == "runs" else "work_candidate_id", obj, label, prefix, errors)
            if sid:
                if sid in seen:
                    fail(f"duplicate {name} id: {sid}", errors)
                seen.add(sid)

            if name == "findings":
                _check_known_values(obj, "status", FINDING_STATES, label, errors)
                _check_known_values(obj, "severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"], label, errors)
                if obj.get("status") in ("Closed", "Accepted Risk", "Deferred", "Superseded"):
                    if not obj.get("closure_actor"):
                        fail(f"{label} terminal status without closure_actor", errors)
                    if not obj.get("closure_evidence"):
                        fail(f"{label} terminal status without closure_evidence", errors)
                rationale = obj.get("rationale_severity_downgrade")
                if rationale is not None:
                    if not rationale:
                        fail(f"{label} severity downgrade rationale empty", errors)
                    if not obj.get("closure_evidence"):
                        fail(f"{label} severity downgrade without evidence", errors)

            if name == "decisions":
                if not obj.get("authority_actor"):
                    fail(f"{label} missing authority_actor", errors)
                if not isinstance(obj.get("authority_refs"), list) or not obj["authority_refs"]:
                    fail(f"{label} missing authority_refs", errors)

            if name == "runs":
                _check_known_values(obj, "result", RUN_RESULTS, label, errors)
                _check_known_values(obj, "remote_mutation", REMOTE_PERMISSIONS, label, errors)
                if obj.get("task_id") and obj["task_id"] not in known_task_ids:
                    fail(f"{label} references unknown task_id: {obj['task_id']}", errors)
                if obj.get("role_id") and (not _ROLE_ID_RE.match(obj["role_id"]) or obj["role_id"] not in known_role_ids):
                    fail(f"{label} references unknown role_id: {obj['role_id']}", errors)

            if name == "derived_work":
                if obj.get("authorization_status") != "NON-AUTHORIZED":
                    fail(f"{label} derived work is not NON-AUTHORIZED", errors)
                if obj.get("proposed_role_id") and obj["proposed_role_id"] not in known_role_ids:
                    fail(f"{label} references unknown proposed_role_id", errors)

    return known_task_ids, known_finding_ids, known_decision_ids, known_run_ids, known_work_ids


def validate_workforce_state(known_task_ids, known_role_ids, errors):
    try:
        state = load_json(WORKFORCE_STATE)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        fail(f"workforce state is not valid JSON: {e}", errors)
        return None

    required = [
        "schema_version",
        "authority_version",
        "current_gate",
        "active_roles",
        "blocked_tasks",
        "authorized_tasks",
        "current_writer",
        "pending_human_remote_actions",
        "latest_decision_id",
        "latest_finding_id",
        "latest_run_id",
        "latest_work_candidate_id",
    ]
    for key in required:
        if key not in state:
            fail(f"workforce state missing required key: {key}", errors)

    for rid in state.get("active_roles", []):
        if not _ROLE_ID_RE.match(rid) or (known_role_ids and rid not in known_role_ids):
            fail(f"workforce state active_roles unknown role: {rid}", errors)

    for tid in state.get("authorized_tasks", []):
        if tid and tid not in known_task_ids:
            fail(f"workforce state authorized_tasks references unknown task: {tid}", errors)

    for tid in state.get("blocked_tasks", []):
        if tid and tid not in known_task_ids:
            fail(f"workforce state blocked_tasks references unknown task: {tid}", errors)

    writer = state.get("current_writer")
    if isinstance(writer, dict):
        if not writer.get("task_id") or writer["task_id"] not in known_task_ids:
            fail(f"workforce state current_writer references unknown task: {writer.get('task_id')}", errors)
        if not writer.get("role_id") or writer["role_id"] not in known_role_ids:
            fail(f"workforce state current_writer references unknown role: {writer.get('role_id')}", errors)
        if not writer.get("branch"):
            fail("workforce state current_writer missing branch", errors)

    writers = {}
    if isinstance(writer, dict) and writer.get("branch") and writer.get("task_id"):
        writers[writer["task_id"]] = writer

    # Enforce one active writer per branch from in-progress tasks
    for tp in load_jsonl(REGISTRY_DIR / "tasks.jsonl"):
        status = tp.get("status", "")
        if status in ("In Progress", "Awaiting Evidence", "Awaiting Review", "Ready For Remote"):
            branch = tp.get("branch")
            tid = tp.get("task_id")
            if branch and tid and tid not in writers:
                writers[tid] = {"task_id": tid, "role_id": tp.get("role_id"), "branch": branch}

    by_branch = {}
    for w in writers.values():
        branch = w["branch"]
        if branch in by_branch:
            fail(f"multiple active writers on branch {branch}: {w['task_id']} and {by_branch[branch]['task_id']}", errors)
        by_branch[branch] = w

    # Writer/reviewer independence for in-progress tasks
    for tp in load_jsonl(REGISTRY_DIR / "tasks.jsonl"):
        reviewer = tp.get("reviewer_role")
        if reviewer and reviewer == tp.get("role_id"):
            fail(f"task {tp.get('task_id')} writer and reviewer are the same role", errors)

    # Latest ID refs
    for field, prefix, known in (
        ("latest_decision_id", "ANOX-DECISION-", None),
        ("latest_finding_id", ("ANOX-FINDING-", "ANOX-MAINARCH-", "ANOX-LEGACY-", "ANOX-WORKFORCE-", "ANOX-SECURITY-"), None),
        ("latest_run_id", "ANOX-RUN-", None),
        ("latest_work_candidate_id", "ANOX-WORK-", None),
    ):
        value = state.get(field)
        if value is None:
            continue
        if not _STABLE_ID_RE.match(value) or not value.startswith(prefix):
            fail(f"workforce state {field} malformed: {value}", errors)

    return state


def validate_authority_precedence(errors):
    if not B027_AUTHORITY.exists():
        return
    text = B027_AUTHORITY.read_text(encoding="utf-8")
    if "docs/authority/AUTHORITY_INDEX.md" not in text:
        fail("B027 Authority does not reference AUTHORITY_INDEX.md", errors)
    text_upper = text.upper()
    if ("FROZEN ARCHITECTURE" not in text_upper or
        "IMPLEMENTED IN B027-A" not in text_upper or
        "DEFERRED" not in text_upper or "B027-B" not in text_upper):
        fail("B027 Authority does not distinguish frozen/implemented/deferred", errors)


def validate_no_secrets(errors):
    forbidden_patterns = [
        re.compile(r"-----BEGIN\s+(?:RSA\s+)?(?:EC\s+)?(?:OPENSSH\s+)?(?:DSA\s+)?(?:ENCRYPTED\s+)?(?:PGP\s+)?(?:PRIVATE\s+)?(?:KEY|BLOCK)\s*-----", re.IGNORECASE),
        re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"\b(?:password|secret|token|api_key|private_key)\s*=\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
    ]
    scan_dirs = [WORKFORCE_DIR, REPO_ROOT / "tools" / "workforce"]
    for d in scan_dirs:
        for p in d.rglob("*"):
            if p.is_dir() or p.suffix in (".zip", ".apk", ".aab", ".jks", ".p12"):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                for pat in forbidden_patterns:
                    if pat.search(text):
                        fail(f"possible secret material in {p.relative_to(REPO_ROOT)}: {pat.pattern[:50]}", errors)
                        break
            except (OSError, UnicodeDecodeError):
                pass


def validate_role_model_separation(errors):
    if not ROLE_REGISTRY.exists():
        return
    data = load_json(ROLE_REGISTRY)
    for role in data.get("roles", []):
        rid = role.get("role_id", "")
        title = role.get("title", "")
        if "Devin" in title or "Claude" in title or "OpenAI" in title or "Anthropic" in title:
            fail(f"role {rid} title conflates role with model/provider", errors)


def validate_b027a():
    errors = []
    print("[B027-A] Required files")
    validate_required_files(errors)

    print("\n[B027-A] Schemas parse")
    validate_schemas(errors)

    print("\n[B027-A] Role registry")
    roles_data = validate_role_registry(errors)
    known_role_ids = {r["role_id"] for r in roles_data.get("roles", [])} if roles_data else set()

    print("\n[B027-A] Registries")
    known_task_ids, known_finding_ids, known_decision_ids, known_run_ids, known_work_ids = validate_registries(roles_data, errors)

    print("\n[B027-A] Workforce state")
    validate_workforce_state(known_task_ids, known_role_ids, errors)

    print("\n[B027-A] Authority precedence")
    validate_authority_precedence(errors)

    print("\n[B027-A] Role/Model separation")
    validate_role_model_separation(errors)

    print("\n[B027-A] Secret scan")
    validate_no_secrets(errors)

    if errors:
        print("\n[B027-A] Validation FAILED:")
        for e in errors:
            print(f"  FAIL {e}")
        return 1

    print("\n[B027-A] Validation PASSED")
    return 0


def main():
    return validate_b027a()


if __name__ == "__main__":
    sys.exit(main())
