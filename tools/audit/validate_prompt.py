#!/usr/bin/env python3
"""B-028 prompt-registry validator.

Validates a ``prompts.jsonl`` record against the task package it claims to
derive from — the prompt is the highest-leverage injection point in the
coordinator model and must stay inside authorized scope.

Checks (fail closed):
- ``prompt_id`` unique, pattern-valid, task exists exactly once
- task status is a delivery-authorized status
- ``role_id``, ``branch`` consistency with the task
- prompt ``allowed_paths ⊆ task.allowed_paths``
- prompt ``forbidden_paths ⊇ task.forbidden_paths`` (never narrower)
- ``data_egress``/``remote_permission`` never exceed the task ceiling
- ``authority_refs`` non-empty; no model selection embedded in content
- required baseline binding: prompt content must carry the task ``start_sha``

Python 3 standard library only; offline.
"""

import argparse
import json
import re
import sys
from pathlib import Path

TASKS_PATH = "docs/workforce/registries/tasks.jsonl"
PROMPTS_PATH = "docs/workforce/registries/prompts.jsonl"

PROMPT_ID_RE = re.compile(r"^ANOX-PROMPT-[A-Z0-9]+$")
TASK_ID_RE = re.compile(r"^ANOX-TASK-[A-Z0-9-]+$")

DELIVERY_STATUSES = {
    "Authorized", "In Progress", "Awaiting Evidence", "Awaiting Review",
    "Ready For Remote", "Awaiting Human Remote Action", "CI Pending",
    "Ready To Merge",
}
EGRESS_ORDER = {"D0": 0, "D1": 1, "D2": 2, "D3": 3}
REMOTE_ORDER = {"NONE": 0, "READ_ONLY": 1, "HUMAN_REMOTE_ACTION_REQUIRED": 2}
MODEL_TOKENS = ("devin2max", "gpt-5", "gpt-4", "claude", "opus", "sonnet",
                "fable", "gemini", "swe-1", "swe-2")


def load_jsonl(path):
    records = []
    p = Path(path)
    if not p.exists():
        return records
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _norm(path):
    return path.replace("\\", "/").strip()


def _match(path, pattern):
    import fnmatch
    return fnmatch.fnmatch(_norm(path), _norm(pattern))


def _subset(inner, outer):
    """Every inner pattern must be covered by some outer pattern or be an
    exact declared path of it."""
    for p in inner:
        if not any(_match(p, o) or _match(o, p) or p == o for o in outer):
            return p
    return None


def validate_record(rec, tasks, existing_ids):
    problems = []
    if not isinstance(rec, dict):
        return ["record is not a JSON object"]
    required = {"prompt_id", "task_id", "role_id", "content", "authority_refs"}
    missing = required - set(rec)
    if missing:
        problems.append(f"missing fields: {sorted(missing)}")
        return problems

    if not PROMPT_ID_RE.match(str(rec["prompt_id"])):
        problems.append("prompt_id malformed (need ANOX-PROMPT-XXXX)")
    elif rec["prompt_id"] in existing_ids:
        problems.append(f"duplicate prompt_id: {rec['prompt_id']}")
    if not TASK_ID_RE.match(str(rec["task_id"])):
        problems.append("task_id malformed")
        return problems

    matches = [t for t in tasks if t.get("task_id") == rec["task_id"]]
    if len(matches) != 1:
        problems.append(f"task {rec['task_id']}: {len(matches)} registry matches")
        return problems
    task = matches[0]

    if task.get("status") not in DELIVERY_STATUSES:
        problems.append(f"task status {task.get('status')} is not delivery-authorized")
    if rec["role_id"] != task.get("role_id"):
        problems.append(f"role_id {rec['role_id']} != task role {task.get('role_id')}")
    if "branch" in rec and rec["branch"] != task.get("branch"):
        problems.append(f"branch {rec['branch']} != task branch {task.get('branch')}")

    uncovered = _subset(rec.get("allowed_paths", []), task.get("allowed_paths", []))
    if uncovered:
        problems.append(f"prompt allowed_path exceeds task scope: {uncovered}")
    narrowed = _subset(task.get("forbidden_paths", []), rec.get("forbidden_paths", []))
    if narrowed and task.get("forbidden_paths"):
        problems.append(f"prompt weakens forbidden path: {narrowed}")

    if "data_egress" in rec:
        if EGRESS_ORDER.get(rec["data_egress"], 99) > EGRESS_ORDER.get(task.get("data_egress"), -1):
            problems.append(f"data_egress {rec['data_egress']} exceeds task ceiling {task.get('data_egress')}")
    if "remote_permission" in rec:
        if REMOTE_ORDER.get(rec["remote_permission"], 99) > REMOTE_ORDER.get(task.get("remote_permission"), -1):
            problems.append(f"remote_permission {rec['remote_permission']} exceeds task ceiling {task.get('remote_permission')}")

    if not rec.get("authority_refs"):
        problems.append("authority_refs must be non-empty")

    content = str(rec.get("content", ""))
    if not content.strip():
        problems.append("content must be non-empty")
    else:
        lowered = content.lower()
        for token in MODEL_TOKENS:
            if token in lowered:
                problems.append(f"model selection token in prompt content: '{token}'")
        start_sha = str(task.get("start_sha", ""))
        if re.fullmatch(r"[0-9a-f]{40}", start_sha) and start_sha not in content:
            problems.append("prompt does not bind the task baseline start_sha")
        if "baseline" not in lowered and "baseline_sha" not in lowered:
            problems.append("prompt lacks a baseline binding declaration")
    return problems


def validate_registry(root):
    problems = []
    try:
        tasks = load_jsonl(Path(root) / TASKS_PATH)
    except (OSError, ValueError) as exc:
        return False, [f"tasks registry: {exc}"]
    try:
        prompts = load_jsonl(Path(root) / PROMPTS_PATH)
    except (OSError, ValueError) as exc:
        return False, [f"prompts registry: {exc}"]
    seen = set()
    for i, rec in enumerate(prompts):
        problems += [f"record {i + 1}: {p}" for p in validate_record(rec, tasks, seen)]
        if rec.get("prompt_id"):
            seen.add(rec["prompt_id"])
    return not problems, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    sub = parser.add_mutually_exclusive_group(required=True)
    sub.add_argument("--verify", action="store_true", help="verify prompts.jsonl")
    sub.add_argument("--check", metavar="PROMPT_JSON",
                     help="validate one prompt record file (does not append)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]

    if args.verify:
        ok, problems = validate_registry(root)
        if ok:
            print("PROMPT REGISTRY: PASS")
            return 0
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1

    try:
        rec = json.loads(Path(args.check).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL: cannot read prompt file: {exc}", file=sys.stderr)
        return 1
    tasks = load_jsonl(Path(root) / TASKS_PATH)
    existing = {r.get("prompt_id") for r in load_jsonl(Path(root) / PROMPTS_PATH)}
    problems = validate_record(rec, tasks, existing)
    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1
    print("PROMPT RECORD: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
