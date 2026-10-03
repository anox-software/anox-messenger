#!/usr/bin/env python3
"""B-028 deterministic next-step resolver (B027-D core, read-only).

Resolves the currently authorized work bundle from
``docs/workforce/WORKFORCE_STATE.json`` + ``registries/tasks.jsonl`` and emits
it as machine-readable JSON. It answers *what is authorized* — it does not
prioritize, narrate, or grant authority. External coordinators consume this
output instead of re-deriving state.

Resolution order (deterministic):
1. ``current_writer`` task, if present -> the active delivery bundle.
2. Exactly one task in a delivery-authorized status -> that bundle.
3. Otherwise -> ``NO_AUTHORIZED_NEXT_STEP`` plus the candidate list.

Python 3 standard library only; offline.
"""

import argparse
import json
import sys
from pathlib import Path

STATE_PATH = "docs/workforce/WORKFORCE_STATE.json"
TASKS_PATH = "docs/workforce/registries/tasks.jsonl"

DELIVERY_STATUSES = {
    "Authorized", "In Progress", "Awaiting Evidence", "Awaiting Review",
    "Ready For Remote", "Awaiting Human Remote Action", "CI Pending",
    "Ready To Merge",
}


def load_jsonl(path):
    records = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _bundle(task, why):
    return {
        "status": "AUTHORIZED_NEXT_STEP",
        "why": why,
        "task_id": task.get("task_id"),
        "role_id": task.get("role_id"),
        "branch": task.get("branch"),
        "start_sha": task.get("start_sha"),
        "baseline_sha": task.get("start_sha"),
        "allowed_paths": task.get("allowed_paths", []),
        "forbidden_paths": task.get("forbidden_paths", []),
        "security_class": task.get("security_class"),
        "data_egress": task.get("data_egress"),
        "required_evidence": task.get("required_evidence"),
        "reviewer_role": task.get("reviewer_role"),
        "remote_permission": task.get("remote_permission"),
        "stop_conditions": task.get("stop_conditions", []),
        "task_status": task.get("status"),
        "scope": task.get("scope"),
        "non_goals": task.get("non_goals", []),
    }


def resolve(root):
    try:
        state = json.loads((Path(root) / STATE_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": "BLOCKED", "problems": [f"WORKFORCE_STATE.json: {exc}"]}
    try:
        tasks = load_jsonl(Path(root) / TASKS_PATH)
    except (OSError, ValueError) as exc:
        return {"status": "BLOCKED", "problems": [f"tasks.jsonl: {exc}"]}

    by_id = {}
    for t in tasks:
        tid = t.get("task_id")
        if tid in by_id:
            return {"status": "BLOCKED", "problems": [f"duplicate task_id: {tid}"]}
        by_id[tid] = t

    writer = state.get("current_writer")
    if isinstance(writer, dict) and writer.get("task_id"):
        task = by_id.get(writer["task_id"])
        if task is None:
            return {"status": "BLOCKED",
                    "problems": [f"current_writer task {writer['task_id']} not in registry"]}
        if task.get("branch") != writer.get("branch"):
            return {"status": "BLOCKED",
                    "problems": ["current_writer branch mismatch vs task package"]}
        return _bundle(task, "current_writer in WORKFORCE_STATE.json")

    authorized = [t for t in tasks
                  if t.get("task_id") in set(state.get("authorized_tasks") or [])
                  and t.get("status") in DELIVERY_STATUSES]
    if len(authorized) == 1:
        return _bundle(authorized[0], "single authorized delivery task in state")
    if len(authorized) > 1:
        return {"status": "BLOCKED",
                "problems": [f"multiple authorized tasks (one-writer rule): "
                             f"{sorted(t['task_id'] for t in authorized)}"]}

    candidates = sorted(t["task_id"] for t in tasks if t.get("status") == "Candidate")
    return {
        "status": "NO_AUTHORIZED_NEXT_STEP",
        "why": "no current_writer and no delivery-authorized task",
        "candidates": candidates,
        "required_action": "human authorization of a candidate task",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    result = resolve(root)
    print(json.dumps(result, indent=1, ensure_ascii=False))
    return 0 if result["status"] != "BLOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())
