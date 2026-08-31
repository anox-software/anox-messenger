#!/usr/bin/env python3
"""B027-B deterministic state/gate resolver.

Fail-closed.  No network.  No external dependencies beyond Python stdlib.
"""

import fnmatch
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLE_REGISTRY = REPO_ROOT / "docs" / "workforce" / "registries" / "roles.json"
TASKS_REGISTRY = REPO_ROOT / "docs" / "workforce" / "registries" / "tasks.jsonl"
ROLES_DIR = REPO_ROOT / "docs" / "workforce" / "roles"

STATES = [
    "Candidate", "Authorized", "In Progress", "Awaiting Evidence",
    "Awaiting Review", "Ready For Remote", "Awaiting Human Remote Action",
    "CI Pending", "Ready To Merge", "Merged", "Closed", "Blocked",
]

ACTIVE_WRITING_STATES = {
    "In Progress", "Awaiting Evidence", "Awaiting Review", "Ready For Remote",
    "Awaiting Human Remote Action", "CI Pending", "Ready To Merge",
}

HUMAN_ACTIONS = {
    "remote push", "merge", "release", "signing", "break-glass", "e4", "d4",
    "remote_push", "break_glass",
}

EGRESS_MAX = {"D0": 0, "D1": 1, "D2": 2, "D3": 3, "D4": 4}
REMOTE_PERM = {"NONE": 0, "READ_ONLY": 1, "HUMAN_REMOTE_ACTION_REQUIRED": 2}

TRANSITION_RULES = {
    ("Candidate", "Authorized"): {"authorize": True, "actor": ["human", "resolver"]},
    ("Authorized", "In Progress"): {"actor": ["assigned", "resolver", "human"]},
    ("In Progress", "Awaiting Evidence"): {"actor": ["assigned", "resolver", "human"]},
    ("Awaiting Evidence", "Awaiting Review"): {"actor": ["assigned", "resolver", "human"]},
    ("Awaiting Review", "Ready For Remote"): {"actor": ["reviewer", "resolver", "human"]},
    ("Awaiting Review", "Blocked"): {"actor": ["assigned", "reviewer", "resolver", "human"]},
    ("Ready For Remote", "Awaiting Human Remote Action"): {"actor": ["assigned", "resolver", "human"]},
    ("Awaiting Human Remote Action", "CI Pending"): {"actor": ["human"], "condition": "human_action"},
    ("CI Pending", "Ready To Merge"): {"actor": ["assigned", "reviewer", "resolver", "human"], "condition": "ci_pass"},
    ("CI Pending", "Blocked"): {"actor": ["assigned", "reviewer", "resolver", "human"]},
    ("Ready To Merge", "Merged"): {"actor": ["human"]},
    ("Merged", "Closed"): {"actor": ["assigned", "resolver", "human"]},
    ("Blocked", "Candidate"): {"actor": ["human", "role001"]},
}


def _allow(reason="allowed"):
    return {"result": "ALLOWED", "reason": reason}


def _block(reason="blocked"):
    return {"result": "BLOCKED", "reason": reason}


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _normalize_roles(roles):
    if roles is None:
        try:
            roles = _load_json(ROLE_REGISTRY)
        except Exception:
            return []
    if isinstance(roles, dict):
        roles = roles.get("roles", [])
    return list(roles)


def _role_by_id(roles, rid):
    for r in roles:
        if r.get("role_id") == rid:
            return r
    return None


def _role_contract(rid):
    p = ROLES_DIR / f"{rid}.md"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def _role_ceilings(rid, roles):
    roles = _normalize_roles(roles)
    role = _role_by_id(roles, rid)
    ai = role.get("ai_allowed", True) if role else True
    text = _role_contract(rid)

    dm = re.search(r"\*\*Data-egress ceiling:\*\*\s*(.*?)$", text, re.M | re.I)
    dline = dm.group(1) if dm else ""
    dvals = [int(m) for m in re.findall(r"D(\d)", dline)]
    if dvals:
        dmax = max(dvals)
        if ai and dmax >= 4:
            dmax = 3
    else:
        dmax = 3 if ai else 4

    rm = re.search(r"\*\*Remote permission ceiling:\*\*\s*(.*?)$", text, re.M | re.I)
    rline = rm.group(1) if rm else ""
    rmax = 0
    if re.search(r"HUMAN_REMOTE_ACTION_REQUIRED", rline, re.I):
        rmax = 2
    elif re.search(r"Human remote write|remote write", rline, re.I) and not ai:
        rmax = 2
    elif re.search(r"READ_ONLY", rline, re.I):
        rmax = 1
    elif re.search(r"\bNONE\b", rline, re.I):
        rmax = 0
    else:
        rmax = 2 if not ai else 0

    return {
        "data_egress_max": f"D{dmax}",
        "remote_permission_max": _perm_name(rmax),
        "ai_allowed": ai,
    }


def _perm_name(level):
    for k, v in REMOTE_PERM.items():
        if v == level:
            return k
    return "NONE"


def _perm_level(name):
    return REMOTE_PERM.get(name, -1)


def _is_valid_sha(s):
    return isinstance(s, str) and re.fullmatch(r"[0-9a-f]{40}", s) is not None


def _role_id(actor):
    if isinstance(actor, str):
        return actor
    if isinstance(actor, dict):
        return actor.get("role_id")
    return None


def _is_human(actor, roles):
    if isinstance(actor, dict) and actor.get("human"):
        return True
    if actor == "human":
        return True
    rid = _role_id(actor)
    if rid in ("ROLE-001", "ROLE-018"):
        return True
    if roles:
        role = _role_by_id(_normalize_roles(roles), rid)
        if role and role.get("ai_allowed") is False:
            return True
    return False


def _is_resolver(actor):
    return _role_id(actor) == "ROLE-003" or (isinstance(actor, dict) and actor.get("resolver"))


def _is_assigned(actor, task):
    return _role_id(actor) == task.get("role_id")


def _is_reviewer(actor, task):
    return _role_id(actor) == task.get("reviewer_role")


def _human_action_recorded(task, state):
    state = state or {}
    for a in state.get("pending_human_remote_actions", []):
        if a.get("task_id") == task.get("task_id"):
            return True
    return False


def _active_tasks(state):
    if state is None:
        tasks = []
    else:
        tasks = state.get("tasks")
    if tasks is None:
        try:
            tasks = _load_jsonl(TASKS_REGISTRY)
        except Exception:
            tasks = []
    cw = state.get("current_writer") if isinstance(state, dict) else None
    if cw:
        found = False
        for t in tasks:
            if t.get("task_id") == cw.get("task_id"):
                found = True
                t.setdefault("status", "In Progress")
                break
        if not found:
            tasks.append({
                "task_id": cw.get("task_id"),
                "role_id": cw.get("role_id"),
                "branch": cw.get("branch"),
                "status": "In Progress",
            })
    return [t for t in tasks if t.get("status") in ACTIVE_WRITING_STATES]


def _extract_state(current, task=None):
    if isinstance(current, str):
        return current
    if isinstance(current, dict):
        return current.get("state") or current.get("status")
    if task and isinstance(task, dict):
        return task.get("status")
    return None


def _path_matches(path, pattern):
    return fnmatch.fnmatch(path, pattern)


def _path_allowed(path, allowed, forbidden):
    for fp in forbidden or []:
        if _path_matches(path, fp):
            return False, "forbidden_path"
    for ap in allowed or []:
        if path == ap:
            return True, "allowed"
        if ap.endswith("/") and path.startswith(ap):
            return True, "allowed"
        if not ap.endswith("/") and (path == ap or path.startswith(ap + "/")):
            return True, "allowed"
        if _path_matches(path, ap):
            return True, "allowed"
    return False, "path_outside_allowed"


def load_roles(path=None):
    path = Path(path) if path else ROLE_REGISTRY
    return _load_json(path)


def load_tasks(path=None):
    path = Path(path) if path else TASKS_REGISTRY
    return _load_jsonl(path)


def check_path_enforcement(changed_paths, task):
    if not isinstance(changed_paths, (list, tuple)):
        return _block("changed_paths_not_list")
    allowed = task.get("allowed_paths") or []
    forbidden = task.get("forbidden_paths") or []
    bad = []
    for cp in changed_paths:
        ok, reason = _path_allowed(cp, allowed, forbidden)
        if not ok:
            bad.append({"path": cp, "reason": reason})
    if bad:
        return {"result": "BLOCKED", "reason": "unauthorized_path", "unauthorized_paths": bad}
    return {"result": "ALLOWED", "reason": "paths_allowed", "unauthorized_paths": []}


def check_one_active_writer(task, state=None):
    if not isinstance(task, dict):
        return _block("invalid_task")
    branch = task.get("branch")
    if not branch:
        return _block("missing_branch")
    new_id = task.get("task_id")
    new_role = task.get("role_id")
    for t in _active_tasks(state):
        if t.get("branch") == branch:
            if (t.get("task_id"), t.get("role_id")) != (new_id, new_role):
                return _block("active_writer_conflict")
    return _allow("one_active_writer")


def check_human_action_boundary(requested_action, role):
    action = (requested_action or "").lower().replace("_", " ").strip()
    if action not in HUMAN_ACTIONS:
        return _allow("not_human_only_action")
    if role is None:
        return _block("no_role")
    if isinstance(role, str):
        if role in ("ROLE-001", "ROLE-018", "human") or _is_human(role, None):
            return _allow("human_role_or_decision")
        return _block("ai_cannot_perform_human_action")
    if isinstance(role, dict):
        if role.get("human") or _is_human(role, role.get("roles")) or role.get("ai_allowed") is False:
            return _allow("human_role_or_decision")
        return _block("ai_cannot_perform_human_action")
    return _block("unknown_role")


def authorize_task(task, state=None, roles=None):
    if not isinstance(task, dict):
        return _block("invalid_task")
    roles = _normalize_roles(roles)
    reasons = []

    required = [
        "task_id", "title", "role_id", "start_sha", "branch", "allowed_paths",
        "scope", "non_goals", "security_class", "data_egress", "priority",
        "required_evidence", "remote_permission", "stop_conditions",
        "authority_refs", "created_at", "status",
    ]
    for k in required:
        if k not in task:
            reasons.append(f"missing_{k}")

    rid = task.get("role_id")
    role = _role_by_id(roles, rid) if rid else None
    if not role:
        reasons.append("unknown_role")
    else:
        if role.get("activation_class") == "dormant":
            reasons.append("dormant_role")
        if task.get("reviewer_role") and task.get("reviewer_role") == rid:
            reasons.append("writer_is_reviewer")

    if not task.get("branch"):
        reasons.append("missing_branch")

    start = task.get("start_sha")
    if not _is_valid_sha(start):
        reasons.append("malformed_start_sha")
    elif state and state.get("current_sha"):
        if start != state["current_sha"] and start not in state.get("ancestor_shas", []):
            reasons.append("start_sha_not_ancestor_or_match")

    if not isinstance(task.get("allowed_paths"), (list, tuple)) or not task.get("allowed_paths"):
        reasons.append("missing_allowed_paths")

    pe = check_path_enforcement(task.get("changed_paths", []), task)
    if pe["result"] == "BLOCKED":
        reasons.append(pe["reason"])

    ow = check_one_active_writer(task, state)
    if ow["result"] == "BLOCKED":
        reasons.append(ow["reason"])

    de = task.get("data_egress")
    if de not in EGRESS_MAX:
        reasons.append("unknown_data_egress")
    elif role:
        if role.get("ai_allowed") and de == "D4":
            reasons.append("d4_for_ai")
        try:
            ceilings = _role_ceilings(rid, roles)
            if EGRESS_MAX.get(de, 0) > EGRESS_MAX.get(ceilings["data_egress_max"], 3):
                reasons.append("data_egress_exceeds_role_ceiling")
        except Exception:
            pass

    rp = task.get("remote_permission")
    if rp not in REMOTE_PERM:
        reasons.append("ai_remote_write_or_unknown_remote_permission")
    elif role:
        try:
            ceilings = _role_ceilings(rid, roles)
            if _perm_level(rp) > _perm_level(ceilings["remote_permission_max"]):
                reasons.append("remote_permission_exceeds_role_ceiling")
        except Exception:
            pass

    if reasons:
        return _block(reasons[0])
    return _allow("task_authorized")


def _permitted_actor(actor, task, allowed, roles, state=None, current=None, condition=None, to_state=None):
    if _is_human(actor, roles) and "human" in allowed:
        ok = True
    elif _is_resolver(actor) and "resolver" in allowed:
        ok = True
    elif _is_assigned(actor, task) and "assigned" in allowed:
        ok = True
    elif _is_reviewer(actor, task) and "reviewer" in allowed:
        ok = True
    elif _role_id(actor) == "ROLE-001" and "role001" in allowed:
        ok = True
    else:
        return False, "unauthorized_actor"

    if condition == "human_action" and not _is_human(actor, roles):
        if not _human_action_recorded(task, state):
            if not (isinstance(current, dict) and current.get("human_action_completed")):
                return False, "human_action_required"

    if condition == "ci_pass" and to_state == "Ready To Merge":
        ci = current.get("ci_result") if isinstance(current, dict) else None
        if ci != "pass":
            return False, "ci_not_passing"

    return True, "transition_authorized"


def resolve_transition(current, requested, actor_role, task, state=None, roles=None):
    from_state = _extract_state(current, task)
    if from_state not in STATES:
        return {"result": "BLOCKED", "reason": "unknown_current_state", "next_state": from_state}
    if requested not in STATES:
        return {"result": "BLOCKED", "reason": "unknown_requested_state", "next_state": from_state}

    roles = _normalize_roles(roles)

    if requested == "Blocked" and (from_state, requested) not in TRANSITION_RULES:
        if actor_role is None:
            return {"result": "BLOCKED", "reason": "no_actor", "next_state": from_state}
        return {"result": "ALLOWED", "reason": "blocked", "next_state": "Blocked"}

    rule = TRANSITION_RULES.get((from_state, requested))
    if not rule:
        return {"result": "BLOCKED", "reason": "invalid_state_transition", "next_state": from_state}

    if rule.get("authorize"):
        auth = authorize_task(task, state, roles)
        if auth["result"] == "BLOCKED":
            return {"result": "BLOCKED", "reason": auth["reason"], "next_state": from_state}

    ok, reason = _permitted_actor(
        actor_role, task, rule["actor"], roles,
        state=state, current=current, condition=rule.get("condition"), to_state=requested,
    )
    if not ok:
        return {"result": "BLOCKED", "reason": reason, "next_state": from_state}

    return {"result": "ALLOWED", "reason": reason, "next_state": requested}


def process_derived_work(candidate):
    if not isinstance(candidate, dict):
        return _block("invalid_candidate")

    status = candidate.get("status", "Detected")
    auth_status = candidate.get("authorization_status", "NON-AUTHORIZED")
    suggested = candidate.get("suggested_by", "")
    authorized_by = candidate.get("authorized_by")
    proposed = candidate.get("proposed_authorization")

    if auth_status not in ("NON-AUTHORIZED", "Authorized", "Rejected", "Deferred"):
        return _block("unknown_authorization_status")

    if auth_status in ("Authorized", "Rejected", "Deferred"):
        if auth_status == "Authorized" and (suggested == "AI" or authorized_by not in ("resolver", "human")):
            return _block("ai_self_authorization")
        if suggested == "AI" and not authorized_by:
            return _block("derived_work_not_non_authorized")
        return {"result": "ALLOWED", "reason": "derived_work_finalized", "candidate": dict(candidate)}

    out = dict(candidate)
    if status == "Detected":
        out["status"] = "Candidate"
        return {"result": "ALLOWED", "reason": "derived_work_advanced", "candidate": out}
    if status == "Candidate":
        out["status"] = "Evaluated"
        return {"result": "ALLOWED", "reason": "derived_work_advanced", "candidate": out}
    if status == "Evaluated":
        if proposed in ("Authorized", "Rejected", "Deferred"):
            if suggested == "AI":
                return _block("ai_self_authorization")
            if authorized_by in ("resolver", "human"):
                out["status"] = proposed
                out["authorization_status"] = proposed
                return {"result": "ALLOWED", "reason": "derived_work_authorized", "candidate": out}
            return _block("authorization_requires_resolver_or_human")
        return {"result": "ALLOWED", "reason": "derived_work_evaluated", "candidate": out}

    return _block("unknown_lifecycle_status")


def route_finding(finding):
    text = (finding.get("category") or finding.get("title") or "").lower()

    if "crypto" in text or "protocol" in text:
        return {"roles": ["ROLE-005", "ROLE-007"], "independent_reviewer": "ROLE-007"}
    if "appsec" in text or "application security" in text:
        return {"roles": ["ROLE-008", "ROLE-007"], "independent_reviewer": "ROLE-007"}
    if "architecture" in text or "privacy" in text or "security audit" in text:
        return {"roles": ["ROLE-009", "ROLE-007"], "independent_reviewer": "ROLE-007"}
    if "build" in text or "supply-chain" in text or "supply chain" in text:
        return {"roles": ["ROLE-010", "ROLE-007"], "independent_reviewer": "ROLE-007"}
    if "implementation" in text:
        return {"roles": ["ROLE-004"], "independent_reviewer": None}
    if "human-only" in text or "human only" in text:
        return {"roles": ["ROLE-001"], "independent_reviewer": "ROLE-009"}

    return {"roles": ["ROLE-001"], "independent_reviewer": "ROLE-009"}


def evaluate_security_trigger(changed_domains):
    if not changed_domains:
        return {"triggered": False, "level": None, "rationale": "no domains changed", "candidates": []}

    docs_typos = {"docs", "typos", "spelling", "comments", "markdown", "formatting"}
    if all(d in docs_typos for d in changed_domains):
        return {"triggered": False, "level": None, "rationale": "docs/typos: no reassessment", "candidates": []}

    sec_c = {
        "security_invariants", "trust_boundaries", "cryptography", "e2ee",
        "key_lifecycle", "state_gate_resolver", "role_permissions",
    }
    sec_b = {"auth", "crypto", "backend", "rls", "android_security", "build_release"}

    candidates = []
    for d in changed_domains:
        if d in docs_typos:
            continue
        role = "ROLE-009"
        if d in ("cryptography", "e2ee", "key_lifecycle", "crypto", "protocol"):
            role = "ROLE-005"
        elif d in ("appsec", "android_security"):
            role = "ROLE-008"
        elif d in ("build", "build_release", "supply_chain", "dependency", "supply-chain"):
            role = "ROLE-010"
        candidates.append({
            "work_candidate_id": f"ANOX-WORK-SEC{d.replace('/', '').replace('_', '').replace('-', '').upper()}",
            "suggested_by": "resolver",
            "source_run": "ANOX-RUN-TRIGGER",
            "affected_domain": d,
            "proposed_role_id": role,
            "independent_reviewer": "ROLE-007",
            "authorization_status": "NON-AUTHORIZED",
            "rationale": f"domain {d} triggered security review",
        })

    if any(d in sec_c for d in changed_domains) or len(changed_domains) > 1:
        level = "SEC-C"
        rationale = "critical or multiple security domains touched"
    elif any(d in sec_b for d in changed_domains):
        level = "SEC-B"
        rationale = "domain-wide security domain touched"
    else:
        level = "SEC-A"
        rationale = "localized security change"

    return {"triggered": True, "level": level, "rationale": rationale, "candidates": candidates}


def resolve_legacy_revalidation(changed_domains):
    mapping = {
        "device_binding": "LEGACY-AUDIT-B002",
        "registration": "LEGACY-AUDIT-B003",
        "account": "LEGACY-AUDIT-B003",
        "crypto": "LEGACY-AUDIT-CRYPTO",
        "protocol": "LEGACY-AUDIT-CRYPTO",
        "android_security": "LEGACY-AUDIT-ANDROID-SEC",
        "local_storage": "LEGACY-AUDIT-ANDROID-SEC",
        "build": "LEGACY-AUDIT-BUILD",
        "dependency": "LEGACY-AUDIT-BUILD",
        "supply_chain": "LEGACY-AUDIT-BUILD",
        "supply-chain": "LEGACY-AUDIT-BUILD",
        "cross_component": "LEGACY-AUDIT-INTEGRATION",
        "integration": "LEGACY-AUDIT-INTEGRATION",
    }
    scopes = {
        "LEGACY-AUDIT-B002": "device binding and trust assumptions",
        "LEGACY-AUDIT-B003": "registration and account lifecycle",
        "LEGACY-AUDIT-CRYPTO": "cryptographic protocols and key handling",
        "LEGACY-AUDIT-ANDROID-SEC": "Android security and local storage",
        "LEGACY-AUDIT-BUILD": "build, dependencies, and supply chain",
        "LEGACY-AUDIT-INTEGRATION": "cross-component integration",
    }
    sessions = []
    seen = set()
    for d in changed_domains:
        sid = mapping.get(d)
        if sid and sid not in seen:
            seen.add(sid)
            sessions.append({"session_id": sid, "scope": scopes[sid], "trigger_domain": d})
    return sessions


def resolve_final_product_gate(state=None):
    state = state or {}
    final = bool(state.get("final_audit_complete"))
    blocking = state.get("blocking_findings") or []
    legacy = state.get("legacy_audits") or []
    legacy_ok = all(l.get("satisfied") for l in legacy)

    if final and not blocking and legacy_ok:
        return {
            "result": "BLOCKED",
            "gate": "PRODUCT_DEVELOPMENT_BLOCKED_PENDING_FINAL_AUDIT",
            "reason": "B027-B product gate remains closed despite final audit readiness",
        }
    return {
        "result": "BLOCKED",
        "gate": "PRODUCT_DEVELOPMENT_BLOCKED_PENDING_FINAL_AUDIT",
        "reason": "final audit incomplete, blocking findings, or legacy audits unsatisfied",
    }


def main():
    data = {}
    try:
        text = sys.stdin.read().strip()
        if text:
            data = json.loads(text)
    except Exception as e:
        print(json.dumps({"result": "BLOCKED", "reason": f"invalid_input: {e}"}, separators=(",", ":")))
        return

    op = data.get("op")
    args = data.get("args", {})
    result = {"result": "BLOCKED", "reason": "unknown_operation"}

    if op == "resolve_transition":
        result = resolve_transition(**args)
    elif op == "authorize_task":
        result = authorize_task(**args)
    elif op == "check_path_enforcement":
        result = check_path_enforcement(**args)
    elif op == "check_one_active_writer":
        result = check_one_active_writer(**args)
    elif op == "check_human_action_boundary":
        result = check_human_action_boundary(**args)
    elif op == "process_derived_work":
        result = process_derived_work(args.get("candidate"))
    elif op == "route_finding":
        result = route_finding(args.get("finding"))
    elif op == "evaluate_security_trigger":
        result = evaluate_security_trigger(args.get("changed_domains", []))
    elif op == "resolve_legacy_revalidation":
        result = resolve_legacy_revalidation(args.get("changed_domains", []))
    elif op == "resolve_final_product_gate":
        result = resolve_final_product_gate(args.get("state"))

    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
