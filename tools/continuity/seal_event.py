#!/usr/bin/env python3
"""B-028 deterministic Project History Ledger event sealing.

Appends hash-chained ANOX-EVENT records to PROJECT_HISTORY_LEDGER.jsonl and
verifies chain integrity offline (no Git required -> archive-mode capable).

Each record sealed by this tool carries ``prev_event_hash`` = SHA-256 of the
canonicalized previous record. Historical records without the field remain
authoritative for their era; chain enforcement starts at the first chained
record and fails closed on gaps, duplicates, reordering, or hash mismatch.

Python 3 standard library only. No network.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

EVENT_ID_RE = re.compile(r"^ANOX-EVENT-(\d{4,})$")
CANONICAL_TYPES = {
    "canonical_merge",
    "post_0054_ledger_canonicalization",
    "remediation_session",
    "audit_evidence_preservation",
    "human_decision",
    "governance_transition",
    "b028_cutover",
}
REQUIRED_FIELDS = (
    "event_id", "date", "type", "task", "summary", "status",
    "start_head", "end_head", "gate_after",
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SealError(Exception):
    pass


def canonical_bytes(record):
    """Deterministic byte serialization of a ledger record."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_hash(record):
    return hashlib.sha256(canonical_bytes(record)).hexdigest()


def load_ledger(path):
    path = Path(path)
    records = []
    try:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SealError(f"line {lineno}: invalid JSON: {exc}")
            if not isinstance(obj, dict):
                raise SealError(f"line {lineno}: record is not a JSON object")
            records.append(obj)
    except OSError as exc:
        raise SealError(str(exc))
    return records


def _event_num(event_id):
    match = EVENT_ID_RE.match(str(event_id))
    return int(match.group(1)) if match else None


def verify_ledger(path, require_full_chain=False):
    """Verify sequence + hash chain. Returns (ok, problems)."""
    problems = []
    try:
        records = load_ledger(path)
    except SealError as exc:
        return False, [str(exc)]
    if not records:
        return False, ["ledger is empty"]

    seen_ids = set()
    seen_nums = []
    first_chain_idx = None

    for i, rec in enumerate(records):
        where = f"record {i + 1} ({rec.get('event_id', '?')})"
        eid = rec.get("event_id")
        if not isinstance(eid, str) or _event_num(eid) is None:
            problems.append(f"{where}: malformed event_id")
            continue
        if eid in seen_ids:
            problems.append(f"{where}: duplicate event_id")
        seen_ids.add(eid)
        num = _event_num(eid)
        if seen_nums and num <= seen_nums[-1]:
            problems.append(f"{where}: non-monotonic event sequence ({num} after {seen_nums[-1]})")
        seen_nums.append(num)
        if "prev_event_hash" in rec and first_chain_idx is None:
            first_chain_idx = i

    for i, rec in enumerate(records):
        where = f"record {i + 1} ({rec.get('event_id', '?')})"
        if i == 0:
            if "prev_event_hash" in rec:
                problems.append(f"{where}: genesis record must not carry prev_event_hash")
            if require_full_chain:
                problems.append(f"{where}: full chain required but genesis has no anchor")
            continue
        prev = records[i - 1]
        if first_chain_idx is not None and i >= first_chain_idx:
            expected = record_hash(prev)
            actual = rec.get("prev_event_hash")
            if not isinstance(actual, str) or not re.fullmatch(r"[0-9a-f]{64}", actual or ""):
                problems.append(f"{where}: missing/malformed prev_event_hash")
            elif actual != expected:
                problems.append(f"{where}: prev_event_hash mismatch (chain broken)")
        else:
            if "prev_event_hash" in rec:
                pass  # pre-cutover chained records are tolerated only at chain start
            if require_full_chain:
                problems.append(f"{where}: record predates chain anchor (full chain required)")

    return not problems, problems


def validate_event_fields(ev):
    problems = []
    for field in REQUIRED_FIELDS:
        if field not in ev:
            problems.append(f"missing required field: {field}")
    if problems:
        return problems
    if _event_num(ev["event_id"]) is None:
        problems.append("event_id must match ANOX-EVENT-NNNN")
    if not DATE_RE.match(str(ev["date"])):
        problems.append("date must be YYYY-MM-DD")
    if ev["type"] not in CANONICAL_TYPES:
        problems.append(f"type must be one of {sorted(CANONICAL_TYPES)}")
    for fld in ("start_head", "end_head"):
        if ev[fld] is not None and not SHA_RE.match(str(ev[fld])):
            problems.append(f"{fld} must be a 40-char sha or null")
    if ev.get("merge_head") is not None and not SHA_RE.match(str(ev["merge_head"])):
        problems.append("merge_head must be a 40-char sha or null")
    for fld in ("findings", "refs", "evidence"):
        if fld in ev and not isinstance(ev[fld], list):
            problems.append(f"{fld} must be a list")
    if "tests" in ev and not isinstance(ev["tests"], dict):
        problems.append("tests must be an object")
    if not isinstance(ev["summary"], str) or not ev["summary"].strip():
        problems.append("summary must be non-empty")
    if not isinstance(ev["task"], str) or not ev["task"].strip():
        problems.append("task must be non-empty")
    return problems


def next_event_id(records):
    max_num = 0
    for rec in records:
        num = _event_num(rec.get("event_id"))
        if num is not None:
            max_num = max(max_num, num)
    return f"ANOX-EVENT-{max_num + 1:04d}"


def seal(path, fields, decision_id, dry_run=False):
    """Append a new hash-chained event. Returns (record, problems)."""
    problems = []
    try:
        records = load_ledger(path)
    except SealError as exc:
        return None, [str(exc)]
    ok, chain_problems = verify_ledger(path)
    if not ok:
        return None, [f"existing chain invalid; refusing to extend: {chain_problems}"]

    event = {
        "event_id": next_event_id(records),
        "date": fields.get("date"),
        "type": fields.get("type"),
        "task": fields.get("task"),
        "summary": fields.get("summary"),
        "status": fields.get("status", "sealed"),
        "start_head": fields.get("start_head"),
        "end_head": fields.get("end_head"),
        "merge_head": fields.get("merge_head"),
        "gate_after": fields.get("gate_after"),
        "findings": fields.get("findings", []),
        "tests": fields.get("tests", {}),
        "refs": fields.get("refs", []),
        "evidence": fields.get("evidence", []),
    }
    if decision_id:
        if decision_id in event["refs"]:
            pass
        else:
            event["refs"] = list(event["refs"]) + [f"decision:{decision_id}"]
    if records:
        event["prev_event_hash"] = record_hash(records[-1])
        event["chain_anchor"] = records[-1].get("event_id")

    problems = validate_event_fields(event)
    if problems:
        return None, problems

    if not dry_run:
        try:
            with Path(path).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as exc:
            return None, [str(exc)]
    return event, []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default="docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
    sub = parser.add_mutually_exclusive_group(required=True)
    sub.add_argument("--verify", action="store_true", help="verify chain integrity (offline)")
    sub.add_argument("--verify-full-chain", action="store_true",
                     help="verify and require every record to be hash-chained")
    sub.add_argument("--seal", action="store_true", help="append a new sealed event")
    sub.add_argument("--dry-run-seal", action="store_true",
                     help="compute the event that would be appended without writing")
    parser.add_argument("--date")
    parser.add_argument("--type", choices=sorted(CANONICAL_TYPES))
    parser.add_argument("--task")
    parser.add_argument("--summary")
    parser.add_argument("--status", default="sealed")
    parser.add_argument("--start-head")
    parser.add_argument("--end-head")
    parser.add_argument("--merge-head")
    parser.add_argument("--gate-after", default="")
    parser.add_argument("--finding", action="append", dest="findings", default=[])
    parser.add_argument("--ref", action="append", dest="refs", default=[])
    parser.add_argument("--evidence", action="append", dest="evidence", default=[])
    parser.add_argument("--decision", help="authorizing human decision id (required for --seal)")
    args = parser.parse_args(argv)

    if args.verify or args.verify_full_chain:
        ok, problems = verify_ledger(args.ledger, require_full_chain=args.verify_full_chain)
        if ok:
            print("LEDGER CHAIN: PASS")
            return 0
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1

    if (args.seal or args.dry_run_seal) and not args.decision:
        print("FAIL: --seal requires --decision <human decision id>", file=sys.stderr)
        return 1

    fields = {
        "date": args.date, "type": args.type, "task": args.task,
        "summary": args.summary, "status": args.status,
        "start_head": args.start_head, "end_head": args.end_head,
        "merge_head": args.merge_head, "gate_after": args.gate_after,
        "findings": args.findings, "tests": {}, "refs": args.refs,
        "evidence": args.evidence,
    }
    event, problems = seal(args.ledger, fields, args.decision,
                           dry_run=args.dry_run_seal)
    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1
    print(json.dumps(event, indent=1, ensure_ascii=False))
    print("SEALED" if args.seal else "DRY-RUN (not written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
