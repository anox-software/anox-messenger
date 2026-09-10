#!/usr/bin/env python3
"""Adversarial tests for validate_security_architecture_findings_freeze.py."""
import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ORIGIN = Path(__file__).resolve().parents[2]
VALIDATOR = ORIGIN / "tools" / "audit" / "validate_security_architecture_findings_freeze.py"

def _git(cmd, cwd):
    return subprocess.run(["git"] + cmd, cwd=cwd, capture_output=True, text=True)

def _setup(mutation=None):
    tmp = tempfile.mkdtemp(prefix="secarch-freeze-adv-")
    git_src = ORIGIN / ".git"
    if git_src.exists():
        shutil.copytree(git_src, Path(tmp) / ".git", symlinks=True)
    _git(["config","user.email","test@anox.software"], tmp)
    _git(["config","user.name","Test Runner"], tmp)
    # materialize the committed final state (HEAD is the metadata commit)
    _git(["reset","--hard","HEAD"], tmp)
    _git(["checkout","-b","test-adversarial"], tmp)
    if mutation:
        mutation(tmp)
        _git(["add","-A"], tmp)
        _git(["commit","-m","adversarial mutation","--amend","--no-edit","--no-verify"], tmp)
    # overlay current lifecycle_legality
    (Path(tmp)/"tools"/"audit").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ORIGIN/"tools"/"audit"/"lifecycle_legality.py", Path(tmp)/"tools"/"audit"/"lifecycle_legality.py")
    return tmp

def _run(tmp):
    env = os.environ.copy()
    env["SECURITY_ARCH_FREEZE_REPO"] = str(tmp)
    r = subprocess.run([sys.executable, str(VALIDATOR)], cwd=tmp, env=env, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr

def _read_jsonl(tmp, rel):
    p = Path(tmp)/rel
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

def _write_jsonl(tmp, rel, lines):
    p = Path(tmp)/rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")

class SecarchFreezeTests(unittest.TestCase):
    def test_base_pass(self):
        tmp = _setup()
        try:
            code, out, _ = _run(tmp)
            self.assertEqual(code, 0, f"base pass\n{out}")
        finally: shutil.rmtree(tmp)

    def test_missing_candidate(self):
        def m(tmp):
            a = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for x in a:
                if x.get("audit_id") == "ANOX-AUDIT-SECURITY-ARCH-001":
                    x["source_candidates"] = [c for c in x["source_candidates"] if c.get("candidate_id") != "CANDIDATE-001"]
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", a)
        tmp = _setup(m)
        try:
            code, out, _ = _run(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("CANDIDATE-001", out)
        finally: shutil.rmtree(tmp)

    def test_candidate_closed_as_not_finding(self):
        def m(tmp):
            a = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for x in a:
                if x.get("audit_id") == "ANOX-AUDIT-SECURITY-ARCH-001":
                    for c in x["source_candidates"]:
                        if c.get("candidate_id") == "CANDIDATE-002":
                            c["disposition"] = "NOT_A_FINDING"
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", a)
        tmp = _setup(m)
        try:
            code, out, _ = _run(tmp)
            self.assertNotEqual(code, 0)
        finally: shutil.rmtree(tmp)

    def test_severity_changed(self):
        def m(tmp):
            f = _read_jsonl(tmp, "docs/workforce/registries/findings.jsonl")
            for x in f:
                if x.get("finding_id") == "ANOX-SECURITY-ARCH-001":
                    x["severity"] = "MEDIUM"
            _write_jsonl(tmp, "docs/workforce/registries/findings.jsonl", f)
        tmp = _setup(m)
        try:
            code, out, _ = _run(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("severity", out)
        finally: shutil.rmtree(tmp)

    def test_b004_blocker_promoted_to_low(self):
        def m(tmp):
            f = _read_jsonl(tmp, "docs/workforce/registries/findings.jsonl")
            for x in f:
                if x.get("finding_id") == "ANOX-SECURITY-ARCH-004":
                    x["severity"] = "LOW"
            _write_jsonl(tmp, "docs/workforce/registries/findings.jsonl", f)
        tmp = _setup(m)
        try:
            code, out, _ = _run(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("blocking", out.lower())
        finally: shutil.rmtree(tmp)

    def test_existing_product_finding_closed(self):
        def m(tmp):
            f = _read_jsonl(tmp, "docs/workforce/registries/findings.jsonl")
            for x in f:
                if x.get("finding_id") == "ANOX-MAINARCH-013":
                    x["status"] = "Closed"
                    x["closure_actor"] = "AI"
                    x["closure_evidence"] = ["test"]
            _write_jsonl(tmp, "docs/workforce/registries/findings.jsonl", f)
        tmp = _setup(m)
        try:
            code, out, _ = _run(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("ANOX-MAINARCH-013", out)
        finally: shutil.rmtree(tmp)

    def test_product_unblocked(self):
        def m(tmp):
            s = json.loads((Path(tmp)/"docs"/"workforce"/"WORKFORCE_STATE.json").read_text())
            s["product_development_state"] = "READY_FOR_B004"
            (Path(tmp)/"docs"/"workforce"/"WORKFORCE_STATE.json").write_text(json.dumps(s, indent=2))
        tmp = _setup(m)
        try:
            code, out, _ = _run(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("BLOCKED", out)
        finally: shutil.rmtree(tmp)

    def test_audit_result_pass(self):
        def m(tmp):
            a = _read_jsonl(tmp, "docs/workforce/registries/audits.jsonl")
            for x in a:
                if x.get("audit_id") == "ANOX-AUDIT-SECURITY-ARCH-001":
                    x["result"] = "PASS"
            _write_jsonl(tmp, "docs/workforce/registries/audits.jsonl", a)
        tmp = _setup(m)
        try:
            code, out, _ = _run(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("PASS_WITH_FINDINGS", out)
        finally: shutil.rmtree(tmp)

if __name__ == "__main__":
    unittest.main()
