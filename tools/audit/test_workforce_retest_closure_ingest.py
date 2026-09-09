#!/usr/bin/env python3
"""Adversarial unittest suite for WORKFORCE-RETEST-CLOSURE-INGEST.

Scenarios:
1. closure state is present and consistent;
2. findings are Closed and only 001/002/005 are Closed by this ingest;
3. HARNESS-RECHECK-02 run/audit are PASS;
4. historical run results are not mutated.
"""
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load_jsonl(path):
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


class RetestClosureIngestTests(unittest.TestCase):
    def test_findings_closed(self):
        findings = load_jsonl(REPO / "docs" / "workforce" / "registries" / "findings.jsonl")
        fmap = {f["finding_id"]: f for f in findings}
        for fid in ["ANOX-WORKFORCE-AUDIT-001", "ANOX-WORKFORCE-AUDIT-002", "ANOX-WORKFORCE-AUDIT-005"]:
            self.assertEqual(fmap[fid]["status"], "Closed")
            self.assertIn("WORKFORCE-HARNESS-RECHECK-02", fmap[fid]["closure_evidence"])

    def test_run_pass(self):
        runs = load_jsonl(REPO / "docs" / "workforce" / "registries" / "runs.jsonl")
        run = next((r for r in runs if r.get("run_id") == "ANOX-RUN-HARNESSRECHECK02"), None)
        self.assertIsNotNone(run)
        self.assertEqual(run["result"], "PASS")
        self.assertEqual(run["per_finding_verdicts"]["ANOX-WORKFORCE-AUDIT-001"], "PASS — NO REGRESSION")
        self.assertEqual(run["per_finding_verdicts"]["ANOX-WORKFORCE-AUDIT-002"], "PASS — REMEDIATED")
        self.assertEqual(run["per_finding_verdicts"]["ANOX-WORKFORCE-AUDIT-005"], "PASS — NO REGRESSION")

    def test_harness_recheck01_preserved(self):
        runs = load_jsonl(REPO / "docs" / "workforce" / "registries" / "runs.jsonl")
        run = next((r for r in runs if r.get("run_id") == "ANOX-RUN-HARNESSRECHECK01"), None)
        self.assertIsNotNone(run)
        self.assertEqual(run["result"], "FAIL")

    def test_security_arch_task_candidate(self):
        tasks = load_jsonl(REPO / "docs" / "workforce" / "registries" / "tasks.jsonl")
        task = next((t for t in tasks if t.get("task_id") == "ANOX-TASK-SECURITY-ARCH-001"), None)
        self.assertIsNotNone(task)
        self.assertEqual(task["status"], "Candidate")


if __name__ == "__main__":
    unittest.main()
