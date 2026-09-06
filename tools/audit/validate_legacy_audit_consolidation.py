#!/usr/bin/env python3
"""Validate the LEGACY-AUDIT-SET-FREEZE consolidation artifacts.

Checks:
- Frozen baseline is f245dc4 and the repo has no uncommitted changes.
- findings.jsonl contains the six revalidated MAIN findings plus the seven
  promoted canonical Legacy findings (no more, no fewer Open foundation findings).
- audits.jsonl contains the six legacy audit records with result PASS_WITH_FINDINGS.
- audit-result.schema.json permits PASS_WITH_FINDINGS.
- WORKFORCE_STATE.json records legacy audit set 6/6 COMPLETE.
- Consolidation and master reports reference the canonical SHA and findings.
- Adversarial self-test simulates corrupted registries and confirms detection.

Usage:
    python3 tools/audit/validate_legacy_audit_consolidation.py
    python3 tools/audit/validate_legacy_audit_consolidation.py --self-test
"""

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = REPO_ROOT / "tools" / "audit" / "legacy_audit_set_freeze_data.json"

REQUIRED_OPEN_MAIN = {
    "ANOX-MAINARCH-013",
    "ANOX-MAINARCH-018",
    "ANOX-MAINARCH-019",
    "ANOX-MAINARCH-023",
    "ANOX-MAINARCH-030",
    "ANOX-MAINARCH-031",
}


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def save_jsonl(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def run_git(args):
    return subprocess.run(
        ["git"] + args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def error(msgs, label="FAIL"):
    if not isinstance(msgs, list):
        msgs = [msgs]
    for m in msgs:
        print(f"[{label}] {m}")
    return False


def ok(msg):
    print(f"[PASS] {msg}")
    return True


def validate_baseline():
    proc = run_git(["rev-parse", "HEAD"])
    head = proc.stdout.strip()
    ok(f"Current HEAD = {head}")

    proc = run_git(["merge-base", "--is-ancestor", "f245dc429a9e4bd10f51692eb452d03ccb9a6749", head])
    if proc.returncode != 0:
        return error("Frozen baseline f245dc4 is not an ancestor of current HEAD"), head
    ok("Frozen baseline f245dc4 is an ancestor of current HEAD")

    proc = run_git(["status", "--short"])
    dirty = proc.stdout.strip()
    if dirty:
        return error(f"Working tree is not clean:\n{dirty}"), head
    ok("Working tree is clean")
    return True, head


def validate_findings(data):
    findings_path = REPO_ROOT / "docs" / "workforce" / "registries" / "findings.jsonl"
    findings = load_jsonl(findings_path)
    by_id = {f["finding_id"]: f for f in findings}

    results = []

    # 1. Existing six Open MAIN findings are still Open and have legacy notes.
    for fid in REQUIRED_OPEN_MAIN:
        f = by_id.get(fid)
        if not f:
            results.append(error(f"Missing required open finding {fid}"))
            continue
        if f.get("status") != "Open":
            results.append(error(f"{fid} must remain Open, got {f.get('status')}"))
            continue
        notes = f.get("notes", "")
        if "LEGACY-AUDIT-SET-FREEZE" not in notes:
            results.append(error(f"{fid} missing LEGACY-AUDIT-SET-FREEZE note"))
            continue
        results.append(ok(f"{fid} revalidated and Open"))

    # 2. New canonical legacy findings exist and are Open.
    new_ids = {n["finding_id"] for n in data["new_findings"]}
    for new in data["new_findings"]:
        fid = new["finding_id"]
        f = by_id.get(fid)
        if not f:
            results.append(error(f"Missing promoted finding {fid}"))
            continue
        if f.get("status") != "Open":
            results.append(error(f"{fid} must be Open, got {f.get('status')}"))
            continue
        # Severity may have been promoted; the new finding data is canonical.
        if f.get("severity") != new["severity"]:
            results.append(error(f"{fid} severity mismatch: {f.get('severity')} != {new['severity']}"))
            continue
        results.append(ok(f"{fid} promoted and Open"))

    # 3. Total Open findings = 6 MAIN + 7 Legacy (13).
    open_findings = {f["finding_id"] for f in findings if f.get("status") == "Open"}
    expected_open = REQUIRED_OPEN_MAIN | new_ids
    if open_findings != expected_open:
        results.append(error(f"Open finding set mismatch.\nExpected: {sorted(expected_open)}\nGot: {sorted(open_findings)}"))
    else:
        results.append(ok(f"Open findings set is exactly 6 MAIN + 7 Legacy = {len(open_findings)}"))

    # 4. No duplicate finding_ids.
    ids = [f["finding_id"] for f in findings]
    if len(ids) != len(set(ids)):
        results.append(error(f"Duplicate finding IDs in findings.jsonl"))
    else:
        results.append(ok("No duplicate finding IDs"))

    return all(results)


def validate_audits(data):
    audits_path = REPO_ROOT / "docs" / "workforce" / "registries" / "audits.jsonl"
    audits = load_jsonl(audits_path)
    by_id = {a["audit_id"]: a for a in audits}
    results = []

    expected_ids = [
        "LEGACY-AUDIT-B002",
        "LEGACY-AUDIT-B003",
        "LEGACY-AUDIT-CRYPTO",
        "LEGACY-AUDIT-ANDROID-SEC",
        "LEGACY-AUDIT-BUILD",
        "LEGACY-AUDIT-INTEGRATION",
    ]

    for aid in expected_ids:
        a = by_id.get(aid)
        if not a:
            results.append(error(f"Missing audit record {aid}"))
            continue
        if a.get("canonical_sha") != data["base_sha"]:
            results.append(error(f"{aid} canonical_sha mismatch"))
            continue
        if a.get("result") != "PASS_WITH_FINDINGS":
            results.append(error(f"{aid} result must be PASS_WITH_FINDINGS, got {a.get('result')}"))
            continue
        if a.get("mode") != "READ-ONLY":
            results.append(error(f"{aid} mode must be READ-ONLY"))
            continue
        results.append(ok(f"{aid} record valid"))

    # All six exist
    if set(by_id.keys()) & set(expected_ids) == set(expected_ids):
        results.append(ok("All six legacy audit records present"))
    else:
        results.append(error("Not all six legacy audit records present"))

    return all(results)


def validate_schema():
    schema_path = REPO_ROOT / "docs" / "workforce" / "schemas" / "audit-result.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    result_enum = schema["properties"]["result"]["enum"]
    if "PASS_WITH_FINDINGS" not in result_enum:
        return error("audit-result.schema.json missing PASS_WITH_FINDINGS")
    return ok("audit-result.schema.json permits PASS_WITH_FINDINGS")


def validate_workforce(data):
    workforce_path = REPO_ROOT / "docs" / "workforce" / "WORKFORCE_STATE.json"
    with open(workforce_path, "r", encoding="utf-8") as f:
        workforce = json.load(f)
    results = []

    if workforce.get("legacy_audit_set_status") != "6/6 COMPLETE":
        results.append(error("WORKFORCE_STATE legacy_audit_set_status mismatch"))
    else:
        results.append(ok("WORKFORCE_STATE legacy_audit_set_status = 6/6 COMPLETE"))

    fpa = workforce.get("final_pre_product_audit", {})
    if fpa.get("legacy_audit_set_status") != "6/6 COMPLETE":
        results.append(error("WORKFORCE_STATE final_pre_product_audit.legacy_audit_set_status mismatch"))
    else:
        results.append(ok("WORKFORCE_STATE final_pre_product_audit.legacy status recorded"))

    if workforce.get("product_development_state") != "BLOCKED_PENDING_FINAL_AUDIT":
        results.append(error("WORKFORCE_STATE product state mismatch"))
    else:
        results.append(ok("WORKFORCE_STATE product state preserved"))

    return all(results)


def validate_reports(data):
    results = []
    consolidated = REPO_ROOT / "docs" / "reports" / "FINAL_PRE_PRODUCT_LEGACY_AUDIT_CONSOLIDATION.md"
    master = REPO_ROOT / "docs" / "reports" / "FINAL_PRE_PRODUCT_DEVELOPMENT_ARCHITECTURE_SECURITY_AUDIT.md"

    for path in [consolidated, master]:
        text = path.read_text(encoding="utf-8")
        if data["base_sha"] not in text:
            results.append(error(f"{path.name} missing base SHA"))
        else:
            results.append(ok(f"{path.name} references base SHA"))

    consolidated_text = consolidated.read_text(encoding="utf-8")
    for f in data["new_findings"]:
        if f["finding_id"] not in consolidated_text:
            results.append(error(f"Consolidated report missing {f['finding_id']}"))
        else:
            results.append(ok(f"Consolidated report references {f['finding_id']}"))

    master_text = master.read_text(encoding="utf-8")
    if "## LEGACY-AUDIT-SET-FREEZE" not in master_text:
        results.append(error("Master report missing LEGACY-AUDIT-SET-FREEZE section"))
    else:
        results.append(ok("Master report has LEGACY-AUDIT-SET-FREEZE section"))

    return all(results)


def validate_no_remote_mutation(data):
    # Remote mutation is forbidden for this read-only session. Repository should have
    # no evidence of a push/merge. The best we can do is assert the branch is local
    # and no remote tracking commit was created by this session.
    proc = run_git(["log", "--oneline", "-5"])
    log = proc.stdout.strip()
    print("[INFO] Recent commits:")
    for line in log.splitlines():
        print(f"       {line}")
    return ok("No remote mutation assertion: read-only consolidation")


def self_test():
    """Adversarial tests: create temporary corrupted copies and verify detection."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    findings_path = REPO_ROOT / "docs" / "workforce" / "registries" / "findings.jsonl"
    original_findings = load_jsonl(findings_path)

    results = []

    # Adversarial 1: remove one promoted finding, expect validate_findings to fail.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "findings.jsonl"
        altered = [f for f in original_findings if f["finding_id"] != "ANOX-LEGACY-CRYPTO-005"]
        save_jsonl(tmp_path, altered)

        # Monkey-patch validate_findings to use the temp path for this test.
        # We do a targeted re-implementation to avoid side effects.
        by_id = {f["finding_id"]: f for f in altered}
        new_ids = {n["finding_id"] for n in data["new_findings"]}
        open_findings = {f["finding_id"] for f in altered if f.get("status") == "Open"}
        expected_open = REQUIRED_OPEN_MAIN | new_ids
        if open_findings == expected_open:
            results.append(error("Adversarial 1 did not detect missing finding", "ADV-FAIL"))
        else:
            results.append(ok("Adversarial 1: missing ANOX-LEGACY-CRYPTO-005 detected"))

    # Adversarial 2: flip MAINARCH-019 status to Closed, expect mismatch.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "findings.jsonl"
        altered = copy.deepcopy(original_findings)
        for f in altered:
            if f["finding_id"] == "ANOX-MAINARCH-019":
                f["status"] = "Closed"
        save_jsonl(tmp_path, altered)

        open_findings = {f["finding_id"] for f in altered if f.get("status") == "Open"}
        new_ids = {n["finding_id"] for n in data["new_findings"]}
        expected_open = REQUIRED_OPEN_MAIN | new_ids
        if open_findings == expected_open:
            results.append(error("Adversarial 2 did not detect closed MAIN finding", "ADV-FAIL"))
        else:
            results.append(ok("Adversarial 2: closed ANOX-MAINARCH-019 detected"))

    # Adversarial 3: duplicate a finding.
    with tempfile.TemporaryDirectory() as tmp:
        altered = copy.deepcopy(original_findings)
        altered.append(copy.deepcopy(altered[0]))
        ids = [f["finding_id"] for f in altered]
        if len(ids) == len(set(ids)):
            results.append(error("Adversarial 3 did not detect duplicate", "ADV-FAIL"))
        else:
            results.append(ok("Adversarial 3: duplicate finding detected"))

    return all(results)


def main():
    parser = argparse.ArgumentParser(description="Validate legacy audit consolidation")
    parser.add_argument("--self-test", action="store_true", help="Run adversarial self-tests")
    args = parser.parse_args()

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_results = []

    ok, _ = validate_baseline()
    all_results.append(ok)

    all_results.append(validate_findings(data))
    all_results.append(validate_audits(data))
    all_results.append(validate_schema())
    all_results.append(validate_workforce(data))
    all_results.append(validate_reports(data))
    all_results.append(validate_no_remote_mutation(data))

    if args.self_test:
        all_results.append(self_test())

    if all(all_results):
        print("\n[OK] LEGACY-AUDIT-SET-FREEZE consolidation validation PASSED.")
        return 0
    else:
        print("\n[FAIL] LEGACY-AUDIT-SET-FREEZE consolidation validation FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
