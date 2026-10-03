#!/usr/bin/env python3
"""B-028 canonical CI-verdict ingest.

Validates a CI verdict record and appends it to
``docs/workforce/registries/ci_verdicts.jsonl``, or re-verifies an existing
registry (``--verify``). A verdict is admissible only when bound to:

- a canonical commit SHA (40-hex),
- an identifiable CI run id + workflow + job,
- the current ``test_map.jsonl`` version, and
- declared covered units that exist in the test map.

Locally produced output is never canonical CI evidence: records must carry a
real ``run_id``/``workflow``/``job`` triple; ``local``/``manual`` markers fail
closed.

Python 3 standard library only. Offline (no network).
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REGISTRY_PATH = "docs/workforce/registries/ci_verdicts.jsonl"
TEST_MAP_PATH = "docs/workforce/registries/test_map.jsonl"

VERDICT_ID_RE = re.compile(r"^ANOX-CIV-[A-Z0-9-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RUN_ID_RE = re.compile(r"^[0-9]{6,}$")
LOCAL_MARKERS = {"local", "manual", "localhost", "dev-machine", "adhoc"}

REQUIRED = {"verdict_id", "commit_sha", "run_id", "workflow", "job",
            "map_version", "result", "units", "created_at"}
OPTIONAL = {"result_detail", "artifact_sha256", "notes"}
RESULTS = {"PASS", "FAIL", "PARTIAL", "CANCELLED"}


def load_jsonl(path):
    records = []
    p = Path(path)
    if not p.exists():
        return records
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def current_map_version(root):
    records = load_jsonl(Path(root) / TEST_MAP_PATH)
    versions = {r.get("map_version") for r in records if r.get("map_version")}
    if len(versions) != 1:
        return None, sorted(versions)
    return versions.pop(), sorted(versions)


def known_units(root):
    return {r.get("unit") for r in load_jsonl(Path(root) / TEST_MAP_PATH)
            if r.get("unit")}


def check_record(rec, root, seen_ids):
    problems = []
    if not isinstance(rec, dict):
        return ["record is not a JSON object"]
    missing = REQUIRED - set(rec)
    unknown = set(rec) - REQUIRED - OPTIONAL
    if missing:
        problems.append(f"missing fields: {sorted(missing)}")
    if unknown:
        problems.append(f"unknown fields (fail closed): {sorted(unknown)}")
    if problems:
        return problems

    if not VERDICT_ID_RE.match(str(rec["verdict_id"])):
        problems.append("verdict_id malformed (need ANOX-CIV-*)")
    elif rec["verdict_id"] in seen_ids:
        problems.append(f"duplicate verdict_id: {rec['verdict_id']}")
    if not SHA_RE.match(str(rec["commit_sha"])):
        problems.append("commit_sha must be a 40-hex canonical commit")
    if not RUN_ID_RE.match(str(rec["run_id"])):
        problems.append("run_id must be a numeric CI run id")
    for field in ("workflow", "job"):
        value = str(rec.get(field, "")).strip()
        if not value:
            problems.append(f"{field} must be non-empty")
        elif value.lower() in LOCAL_MARKERS:
            problems.append(f"{field}='{value}' is local evidence — not canonical CI")
    if rec["result"] not in RESULTS:
        problems.append(f"result must be one of {sorted(RESULTS)}")
    if not isinstance(rec["units"], list) or not rec["units"]:
        problems.append("units must be a non-empty list")
    else:
        known = known_units(root)
        for unit in rec["units"]:
            if unit not in known:
                problems.append(f"unit {unit} has no test_map binding (map-coverage gap)")
    if "artifact_sha256" in rec and not re.fullmatch(r"[0-9a-f]{64}", str(rec["artifact_sha256"])):
        problems.append("artifact_sha256 malformed")

    version, _ = current_map_version(root)
    if version is None:
        problems.append("test_map.jsonl has ambiguous/no map_version — cannot bind verdict")
    elif rec["map_version"] != version:
        problems.append(f"map_version {rec['map_version']} != current test map {version}")
    return problems


def verify_registry(root):
    path = Path(root) / REGISTRY_PATH
    problems = []
    try:
        records = load_jsonl(path)
    except (OSError, ValueError) as exc:
        return False, [f"cannot read registry: {exc}"]
    seen = set()
    bootstrap_seen = False
    for i, rec in enumerate(records):
        if rec.get("record_type") == "registry_bootstrap":
            if i != 0 or bootstrap_seen:
                problems.append(f"record {i + 1}: misplaced/duplicate bootstrap record")
            bootstrap_seen = True
            continue
        problems += [f"record {i + 1}: {p}" for p in check_record(rec, root, seen)]
        if rec.get("verdict_id"):
            seen.add(rec["verdict_id"])
    return not problems, problems


def ingest(verdict_path, root):
    problems = []
    try:
        rec = json.loads(Path(verdict_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [f"cannot read verdict file: {exc}"]
    ok, reg_problems = verify_registry(root)
    if not ok:
        return None, [f"existing registry invalid; refusing to extend: {reg_problems}"]
    existing = {r.get("verdict_id") for r in load_jsonl(Path(root) / REGISTRY_PATH)}
    problems += check_record(rec, root, existing)
    if problems:
        return None, problems
    line = json.dumps(rec, ensure_ascii=False)
    try:
        with (Path(root) / REGISTRY_PATH).open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:
        return None, [str(exc)]
    return rec, []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    sub = parser.add_mutually_exclusive_group(required=True)
    sub.add_argument("--verify", action="store_true", help="verify registry integrity")
    sub.add_argument("--ingest", metavar="VERDICT_JSON", help="validate + append a verdict")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]

    if args.verify:
        ok, problems = verify_registry(root)
        if ok:
            print("CI VERDICT REGISTRY: PASS")
            return 0
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1

    rec, problems = ingest(args.ingest, root)
    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1
    print(f"INGESTED: {rec['verdict_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
