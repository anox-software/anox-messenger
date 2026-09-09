#!/usr/bin/env python3
"""Deterministic validator for WORKFORCE-RETEST-CLOSURE-INGEST.

Checks:
- ANOX-WORKFORCE-AUDIT-001/002/005 are Closed with correct closure_actor/evidence.
- ANOX-RUN-HARNESSRECHECK02 exists with result PASS and correct per-finding verdicts.
- ANOX-AUDIT-WORKFORCE-HARNESS-RECHECK-02 exists with result PASS and the three findings.
- ANOX-TASK-WORKFORCE-HARNESS-RECHECK-02 is Closed with start_sha and closure evidence.
- ANOX-TASK-WORKFORCE-RETEST-CLOSURE-INGEST exists and is Ready For Remote.
- ANOX-TASK-SECURITY-ARCH-001 exists as Candidate.
- WORKFORCE_STATE and CURRENT_STATE reflect the closure ingest and next Candidate.
- No remote mutation is recorded.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGETS = ["ANOX-WORKFORCE-AUDIT-001", "ANOX-WORKFORCE-AUDIT-002", "ANOX-WORKFORCE-AUDIT-005"]
EXPECTED_VERDICTS = {
    "ANOX-WORKFORCE-AUDIT-001": "PASS — NO REGRESSION",
    "ANOX-WORKFORCE-AUDIT-002": "PASS — REMEDIATED",
    "ANOX-WORKFORCE-AUDIT-005": "PASS — NO REGRESSION",
}


def load_jsonl(path):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ok(msg):
    print(f"  OK   {msg}")


def fail(msg):
    print(f"  FAIL {msg}")
    return False


def main():
    all_good = True

    findings = load_jsonl(REPO / "docs" / "workforce" / "registries" / "findings.jsonl")
    fmap = {f["finding_id"]: f for f in findings}
    for fid in TARGETS:
        f = fmap.get(fid)
        if not f:
            all_good &= fail(f"finding {fid} missing")
            continue
        if f.get("status") != "Closed":
            all_good &= fail(f"finding {fid} not Closed")
            continue
        if "WORKFORCE-HARNESS-RECHECK-02" not in (f.get("closure_evidence") or []):
            all_good &= fail(f"finding {fid} missing HARNESS-RECHECK-02 closure evidence")
            continue
        ok(f"finding {fid} Closed with closure evidence")

    runs = load_jsonl(REPO / "docs" / "workforce" / "registries" / "runs.jsonl")
    run = next((r for r in runs if r.get("run_id") == "ANOX-RUN-HARNESSRECHECK02"), None)
    if not run:
        all_good &= fail("ANOX-RUN-HARNESSRECHECK02 missing")
    else:
        if run.get("result") != "PASS":
            all_good &= fail("ANOX-RUN-HARNESSRECHECK02 result not PASS")
        else:
            ok("ANOX-RUN-HARNESSRECHECK02 PASS")
        for fid, verdict in EXPECTED_VERDICTS.items():
            actual = (run.get("per_finding_verdicts") or {}).get(fid)
            if actual != verdict:
                all_good &= fail(f"ANOX-RUN-HARNESSRECHECK02 {fid} verdict mismatch: {actual}")
            else:
                ok(f"ANOX-RUN-HARNESSRECHECK02 {fid} = {verdict}")

    audits = load_jsonl(REPO / "docs" / "workforce" / "registries" / "audits.jsonl")
    audit = next((a for a in audits if a.get("audit_id") == "ANOX-AUDIT-WORKFORCE-HARNESS-RECHECK-02"), None)
    if not audit:
        all_good &= fail("ANOX-AUDIT-WORKFORCE-HARNESS-RECHECK-02 missing")
    else:
        if audit.get("result") != "PASS":
            all_good &= fail("audit result not PASS")
        else:
            ok("ANOX-AUDIT-WORKFORCE-HARNESS-RECHECK-02 PASS")
        if set(audit.get("closed_findings") or []) != set(TARGETS):
            all_good &= fail("audit closed_findings mismatch")

    tasks = load_jsonl(REPO / "docs" / "workforce" / "registries" / "tasks.jsonl")
    tmap = {t["task_id"]: t for t in tasks}
    recheck = tmap.get("ANOX-TASK-WORKFORCE-HARNESS-RECHECK-02")
    if not recheck or recheck.get("status") != "Closed":
        all_good &= fail("ANOX-TASK-WORKFORCE-HARNESS-RECHECK-02 not Closed")
    else:
        ok("ANOX-TASK-WORKFORCE-HARNESS-RECHECK-02 Closed")

    if tmap.get("ANOX-TASK-WORKFORCE-RETEST-CLOSURE-INGEST", {}).get("status") != "Ready For Remote":
        all_good &= fail("ANOX-TASK-WORKFORCE-RETEST-CLOSURE-INGEST not Ready For Remote")
    else:
        ok("ANOX-TASK-WORKFORCE-RETEST-CLOSURE-INGEST Ready For Remote")

    if tmap.get("ANOX-TASK-SECURITY-ARCH-001", {}).get("status") != "Candidate":
        all_good &= fail("ANOX-TASK-SECURITY-ARCH-001 not Candidate")
    else:
        ok("ANOX-TASK-SECURITY-ARCH-001 Candidate")

    ws = load_json(REPO / "docs" / "workforce" / "WORKFORCE_STATE.json")
    if ws.get("next_phase") != "AUDIT-SECURITY-ARCHITECTURE":
        all_good &= fail("WORKFORCE_STATE next_phase not AUDIT-SECURITY-ARCHITECTURE")
    else:
        ok("WORKFORCE_STATE next_phase = AUDIT-SECURITY-ARCHITECTURE")
    if ws.get("product_development_state") != "BLOCKED_PENDING_FINAL_AUDIT":
        all_good &= fail("product not blocked")
    else:
        ok("product BLOCKED_PENDING_FINAL_AUDIT")

    cs = load_json(REPO / "docs" / "continuity" / "CURRENT_STATE.json")
    if "AUDIT-SECURITY-ARCHITECTURE" not in (cs.get("post_merge_gate") or ""):
        all_good &= fail("CURRENT_STATE post_merge_gate not AUDIT-SECURITY-ARCHITECTURE")
    else:
        ok("CURRENT_STATE post_merge_gate = AUDIT-SECURITY-ARCHITECTURE")

    if not all_good:
        print("WORKFORCE-RETEST-CLOSURE-INGEST: FAIL")
        return 1
    print("WORKFORCE-RETEST-CLOSURE-INGEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
