#!/usr/bin/env python3
"""B-028 generic session-evidence ingest validator.

Consumes a session manifest (``docs/workforce/schemas/session.schema.json``)
and validates it fail-closed against the repository:

- schema conformance (fields, patterns, enums, no unknown keys)
- covered units exist in ``docs/security/remediation/msc_state.jsonl``
- every declared artifact exists and hashes to its pinned SHA-256
- authorized task exists in ``tasks.jsonl`` and is a legal delivery task
- required retests are satisfiable in principle: ``ci_verdict`` bindings may
  not satisfy HIGH/CRITICAL-level (E3/E4) requirements; ``independent_retest``
  requires a named evidence reference when marked SATISFIED
- closure legality: no covered unit may claim closure while any required
  retest is PENDING/FAILED

Offline: pure file checks, no Git required (archive-mode capable).
Python 3 standard library only.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA_PATH = "docs/workforce/schemas/session.schema.json"
TASKS_PATH = "docs/workforce/registries/tasks.jsonl"
MSC_PATH = "docs/security/remediation/msc_state.jsonl"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SESSION_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]+$")
TASK_ID_RE = re.compile(r"^ANOX-TASK-[A-Z0-9-]+$")
UNIT_RE = re.compile(r"^(MSC-UNIT-\d+|ANOX-[A-Z0-9-]+)$")

SESSION_REQUIRED = {
    "schema_version", "session_id", "security_class", "authorized_task_id",
    "covered_units", "artifacts", "required_retests", "provenance",
}
SESSION_OPTIONAL = {"notes"}
ARTIFACT_REQUIRED = {"path", "sha256"}
ARTIFACT_OPTIONAL = {"kind"}
RETEST_REQUIRED = {"unit", "level", "binding"}
RETEST_OPTIONAL = {"satisfied_by", "status"}
PROVENANCE_REQUIRED = {"base_sha", "delivery_branch"}
PROVENANCE_OPTIONAL = {"merge_sha"}

LEGAL_TASK_STATUSES = {
    "Authorized", "In Progress", "Awaiting Evidence", "Awaiting Review",
    "Ready For Remote", "Awaiting Human Remote Action", "CI Pending",
    "Ready To Merge", "Merged",
}


def load_jsonl(path):
    records = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_schema(manifest):
    problems = []
    if not isinstance(manifest, dict):
        return ["manifest is not a JSON object"]
    missing = SESSION_REQUIRED - set(manifest)
    unknown = set(manifest) - SESSION_REQUIRED - SESSION_OPTIONAL
    if missing:
        problems.append(f"missing required fields: {sorted(missing)}")
    if unknown:
        problems.append(f"unknown fields (fail closed): {sorted(unknown)}")
    if problems:
        return problems

    if manifest["schema_version"] != "B028-SES-v1":
        problems.append(f"unknown schema_version: {manifest['schema_version']}")
    if not SESSION_ID_RE.match(str(manifest["session_id"])):
        problems.append("session_id malformed")
    if manifest["security_class"] not in {"S0", "S1", "S2", "S3", "S4"}:
        problems.append("security_class must be S0..S4")
    if not TASK_ID_RE.match(str(manifest["authorized_task_id"])):
        problems.append("authorized_task_id malformed")
    if not manifest["covered_units"]:
        problems.append("covered_units must be non-empty")
    else:
        for unit in manifest["covered_units"]:
            if not UNIT_RE.match(str(unit)):
                problems.append(f"covered unit malformed: {unit}")
    if not manifest["artifacts"]:
        problems.append("artifacts must be non-empty")
    for i, art in enumerate(manifest["artifacts"]):
        if not isinstance(art, dict):
            problems.append(f"artifact {i}: not an object")
            continue
        if ARTIFACT_REQUIRED - set(art):
            problems.append(f"artifact {i}: missing {sorted(ARTIFACT_REQUIRED - set(art))}")
        if set(art) - ARTIFACT_REQUIRED - ARTIFACT_OPTIONAL:
            problems.append(f"artifact {i}: unknown fields {sorted(set(art) - ARTIFACT_REQUIRED - ARTIFACT_OPTIONAL)}")
        if "sha256" in art and not SHA256_RE.match(str(art["sha256"])):
            problems.append(f"artifact {i}: sha256 malformed")
        if "kind" in art and art["kind"] not in {"report", "evidence", "manifest", "log", "decision", "other"}:
            problems.append(f"artifact {i}: unknown kind")
    if not manifest["required_retests"]:
        problems.append("required_retests must be non-empty")
    covered = set(manifest.get("covered_units", []))
    for i, rt in enumerate(manifest["required_retests"]):
        if not isinstance(rt, dict):
            problems.append(f"required_retest {i}: not an object")
            continue
        if RETEST_REQUIRED - set(rt):
            problems.append(f"required_retest {i}: missing {sorted(RETEST_REQUIRED - set(rt))}")
        if set(rt) - RETEST_REQUIRED - RETEST_OPTIONAL:
            problems.append(f"required_retest {i}: unknown fields {sorted(set(rt) - RETEST_REQUIRED - RETEST_OPTIONAL)}")
        if rt.get("level") not in {"E1", "E2", "E3", "E4"}:
            problems.append(f"required_retest {i}: level must be E1..E4")
        if rt.get("binding") not in {"independent_retest", "ci_verdict", "human_attestation"}:
            problems.append(f"required_retest {i}: unknown binding")
        if rt.get("status", "PENDING") not in {"PENDING", "SATISFIED", "FAILED"}:
            problems.append(f"required_retest {i}: unknown status")
        if rt.get("unit") not in covered:
            problems.append(f"required_retest {i}: unit {rt.get('unit')} not in covered_units")
    prov = manifest["provenance"]
    if not isinstance(prov, dict):
        problems.append("provenance must be an object")
    else:
        if PROVENANCE_REQUIRED - set(prov):
            problems.append(f"provenance: missing {sorted(PROVENANCE_REQUIRED - set(prov))}")
        if set(prov) - PROVENANCE_REQUIRED - PROVENANCE_OPTIONAL:
            problems.append(f"provenance: unknown fields {sorted(set(prov) - PROVENANCE_REQUIRED - PROVENANCE_OPTIONAL)}")
        if "base_sha" in prov and not SHA_RE.match(str(prov["base_sha"])):
            problems.append("provenance.base_sha malformed")
        if "merge_sha" in prov and not SHA_RE.match(str(prov["merge_sha"])):
            problems.append("provenance.merge_sha malformed")
    return problems


def check_semantics(manifest, root):
    problems = []
    # Task exists and is a legal delivery task.
    try:
        tasks = load_jsonl(root / TASKS_PATH)
    except (OSError, ValueError) as exc:
        return [f"cannot read tasks registry: {exc}"]
    matches = [t for t in tasks if t.get("task_id") == manifest["authorized_task_id"]]
    if len(matches) != 1:
        problems.append(f"authorized_task_id {manifest['authorized_task_id']}: "
                        f"{len(matches)} registry matches (need exactly 1)")
    elif matches[0].get("status") not in LEGAL_TASK_STATUSES:
        problems.append(f"task status {matches[0].get('status')} is not a legal delivery status")

    # Covered units exist in the MSC registry (for MSC-UNIT-* ids).
    try:
        msc_units = {r.get("msc_unit") for r in load_jsonl(root / MSC_PATH)}
    except (OSError, ValueError) as exc:
        return problems + [f"cannot read MSC registry: {exc}"]
    for unit in manifest["covered_units"]:
        if str(unit).startswith("MSC-UNIT-") and unit not in msc_units:
            problems.append(f"covered unit unknown in msc_state.jsonl: {unit}")

    # Artifact hash pins.
    for art in manifest["artifacts"]:
        path = root / art["path"]
        if not path.is_file():
            problems.append(f"artifact missing: {art['path']}")
            continue
        actual = _sha256_file(path)
        if actual != art["sha256"]:
            problems.append(f"artifact hash mismatch: {art['path']} "
                            f"(pinned {art['sha256'][:12]}…, actual {actual[:12]}…)")

    # Retest legality + closure legality.
    for rt in manifest["required_retests"]:
        status = rt.get("status", "PENDING")
        if rt["binding"] == "ci_verdict" and rt["level"] in {"E3", "E4"}:
            problems.append(f"unit {rt['unit']}: ci_verdict may not satisfy {rt['level']} "
                            f"(HIGH/CRITICAL requires independent retest or human attestation)")
        if status == "SATISFIED" and not rt.get("satisfied_by"):
            problems.append(f"unit {rt['unit']}: SATISFIED without evidence reference")
        if status == "FAILED":
            problems.append(f"unit {rt['unit']}: required retest FAILED — session cannot close")
        if status == "SATISFIED" and rt["binding"] == "ci_verdict":
            ref = str(rt.get("satisfied_by", ""))
            if not ref.startswith("ANOX-CIV-"):
                problems.append(f"unit {rt['unit']}: ci_verdict reference must be an "
                                f"ANOX-CIV-* verdict id, got '{ref}'")
    pending = [rt["unit"] for rt in manifest["required_retests"]
               if rt.get("status", "PENDING") != "SATISFIED"]
    if pending:
        problems.append(f"session not closable — unsatisfied retests for: {pending}")
    return problems


def validate(manifest_path, root):
    problems = []
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, [f"cannot read manifest: {exc}"]
    problems += check_schema(manifest)
    if not problems:
        problems += check_semantics(manifest, Path(root))
    return not problems, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="path to session manifest JSON")
    parser.add_argument("--root", default=None, help="repository root")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    ok, problems = validate(args.manifest, root)
    if ok:
        print("SESSION EVIDENCE: PASS")
        return 0
    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
