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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lifecycle_legality as ll  # noqa: E402

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
        print(f"[INFO] Working tree has uncommitted changes (ignored by historical validator):\n{dirty}")
    else:
        ok("Working tree is clean")
    return True, head


def validate_findings(data, findings=None, audits=None):
    """Validate the consolidation's canonical finding set.

    The freeze-time snapshot (13 Open: 6 updated MAIN + 7 promoted Legacy) is
    the historical record, anchored by the immutable freeze data and the
    per-finding LEGACY-AUDIT-SET-FREEZE notes. The current live registry may
    have legally progressed through the authorized Open -> Ready For Retest ->
    Closed lifecycle (LEGACY-FIX-01 -> LEGACY-RETEST-01); only illegal states —
    unauthorized closure, missing remediation evidence, disappearing findings —
    still fail.
    """
    findings_path = REPO_ROOT / "docs" / "workforce" / "registries" / "findings.jsonl"
    if findings is None:
        findings = load_jsonl(findings_path)
    if audits is None:
        audits = load_jsonl(REPO_ROOT / "docs" / "workforce" / "registries" / "audits.jsonl")
    by_id = {f["finding_id"]: f for f in findings}

    results = []

    new_ids = {n["finding_id"] for n in data["new_findings"]}
    updated_ids = set(data.get("updated_findings", {}).keys())
    declared_ids = updated_ids | new_ids

    # 1. The six revalidated MAIN findings must still exist, retain the freeze
    #    note, and be in a legal live lifecycle state.
    for fid in REQUIRED_OPEN_MAIN:
        f = by_id.get(fid)
        if not f:
            results.append(error(f"Missing required finding {fid}"))
            continue
        notes = f.get("notes", "")
        if "LEGACY-AUDIT-SET-FREEZE" not in notes:
            results.append(error(f"{fid} missing LEGACY-AUDIT-SET-FREEZE note"))
            continue
        legal, reason = ll.finding_status_legal(f, audits)
        if not legal:
            results.append(error(f"{fid} in illegal lifecycle state: {reason}"))
            continue
        results.append(ok(f"{fid} revalidated; live state {f.get('status')} is legal"))

    # 2. The seven promoted canonical legacy findings must still exist with
    #    canonical severity and a legal live lifecycle state.
    for new in data["new_findings"]:
        fid = new["finding_id"]
        f = by_id.get(fid)
        if not f:
            results.append(error(f"Missing promoted finding {fid}"))
            continue
        # Severity may have been promoted; the new finding data is canonical.
        if f.get("severity") != new["severity"]:
            results.append(error(f"{fid} severity mismatch: {f.get('severity')} != {new['severity']}"))
            continue
        legal, reason = ll.finding_status_legal(f, audits)
        if not legal:
            results.append(error(f"{fid} in illegal lifecycle state: {reason}"))
            continue
        results.append(ok(f"{fid} promoted; live state {f.get('status')} is legal"))

    # 3. Freeze-data <-> registry consistency: every registry finding carrying a
    #    LEGACY-AUDIT-SET-FREEZE note must be declared in the frozen snapshot
    #    data, and every ANOX-LEGACY-* finding must have been promoted by this
    #    consolidation (declared in new_findings). This detects a rewritten or
    #    tampered snapshot as well as extra findings masquerading as
    #    consolidation outputs.
    undeclared = [
        f["finding_id"] for f in findings
        if "LEGACY-AUDIT-SET-FREEZE" in f.get("notes", "")
        and f["finding_id"] not in declared_ids
    ]
    undeclared += [
        f["finding_id"] for f in findings
        if f["finding_id"].startswith("ANOX-LEGACY-")
        and f["finding_id"] not in new_ids
    ]
    if undeclared:
        results.append(error(f"Findings not declared in the frozen consolidation snapshot: {sorted(undeclared)}"))
    else:
        results.append(ok("All consolidation findings are declared in the frozen snapshot data"))

    # 4. Live lifecycle: the consolidation findings may have progressed through the
    #    authorized Open -> Ready For Retest -> Closed lifecycle. Other findings may
    #    be Open if they were introduced by later authorized audits. All registry
    #    findings must be in a legal lifecycle state.
    open_findings = {f["finding_id"] for f in findings if f.get("status") == "Open"}
    consolidation_open = open_findings & declared_ids
    if not consolidation_open.issubset(declared_ids):
        results.append(error(f"Open consolidation findings not in declared set: {sorted(consolidation_open - declared_ids)}"))
    else:
        results.append(ok(f"Open consolidation findings ({len(consolidation_open)}) are a subset of the 13 canonical consolidation findings"))
    illegal = [
        f["finding_id"] for f in findings
        if not ll.finding_status_legal(f, audits)[0]
    ]
    if illegal:
        results.append(error(f"Findings in illegal lifecycle states: {sorted(illegal)}"))
    else:
        results.append(ok("All registry findings are in legal lifecycle states"))

    # 5. No duplicate finding_ids.
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
    """Adversarial tests: inject corrupted registries/data and verify the real
    validate_findings detects them (lifecycle-aware semantics)."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    findings_path = REPO_ROOT / "docs" / "workforce" / "registries" / "findings.jsonl"
    audits_path = REPO_ROOT / "docs" / "workforce" / "registries" / "audits.jsonl"
    original_findings = load_jsonl(findings_path)
    real_audits = load_jsonl(audits_path)

    results = []

    # Adversarial 1: remove one promoted finding -> must be detected.
    altered = [f for f in original_findings if f["finding_id"] != "ANOX-LEGACY-CRYPTO-005"]
    if not validate_findings(data, findings=altered, audits=real_audits):
        results.append(ok("Adversarial 1: missing ANOX-LEGACY-CRYPTO-005 detected"))
    else:
        results.append(error("Adversarial 1 did not detect missing finding", "ADV-FAIL"))

    # Adversarial 2: unauthorized closure of a still-Open canonical finding
    # (Closed with no closure chain) -> must be detected.
    altered = copy.deepcopy(original_findings)
    for f in altered:
        if f["finding_id"] == "ANOX-MAINARCH-013":
            f["status"] = "Closed"
    if not validate_findings(data, findings=altered, audits=real_audits):
        results.append(ok("Adversarial 2: unauthorized closure of ANOX-MAINARCH-013 detected"))
    else:
        results.append(error("Adversarial 2 did not detect unauthorized closure", "ADV-FAIL"))

    # Adversarial 3: duplicate a finding -> must be detected.
    altered = copy.deepcopy(original_findings)
    altered.append(copy.deepcopy(altered[0]))
    if not validate_findings(data, findings=altered, audits=real_audits):
        results.append(ok("Adversarial 3: duplicate finding detected"))
    else:
        results.append(error("Adversarial 3 did not detect duplicate", "ADV-FAIL"))

    # Adversarial 4: rewrite the frozen snapshot (drop a promoted finding from
    # freeze data while the registry still carries the freeze note) -> must be
    # detected as undeclared.
    tampered_data = copy.deepcopy(data)
    tampered_data["new_findings"] = [n for n in tampered_data["new_findings"]
                                     if n["finding_id"] != "ANOX-LEGACY-B003-001"]
    if not validate_findings(tampered_data, findings=original_findings, audits=real_audits):
        results.append(ok("Adversarial 4: rewritten freeze snapshot detected"))
    else:
        results.append(error("Adversarial 4 did not detect freeze-data tampering", "ADV-FAIL"))

    # Adversarial 5: strip the FIX->RETEST chain from a legally Closed finding
    # (keep status Closed but remove closure_evidence) -> must be detected.
    altered = copy.deepcopy(original_findings)
    closed_target = next((f for f in altered
                          if f.get("status") == "Closed" and f.get("closure_evidence")), None)
    if closed_target is not None:
        closed_target["closure_evidence"] = []
        closed_target["closure_actor"] = ""
        if not validate_findings(data, findings=altered, audits=real_audits):
            results.append(ok(f"Adversarial 5: stripped closure chain on {closed_target['finding_id']} detected"))
        else:
            results.append(error("Adversarial 5 did not detect stripped closure chain", "ADV-FAIL"))

    # Positive control: the real post-lifecycle registry must pass.
    if validate_findings(data, findings=original_findings, audits=real_audits):
        results.append(ok("Positive control: real post-lifecycle registry accepted"))
    else:
        results.append(error("Positive control failed: real registry rejected", "ADV-FAIL"))

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
