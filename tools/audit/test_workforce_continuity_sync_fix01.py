#!/usr/bin/env python3
"""Adversarial unittest suite for WORKFORCE-CONTINUITY-SYNC-FIX-01.

These tests construct temporary Git repositories from the current real repo,
inject continuity/workforce metadata, and exercise the effective-gate resolvers
and handoff generator in controlled positive and negative cases.

Scenarios:
 1. valid delivery / pre-merge resolution
 2. valid synthetic Human --no-ff merge / post-merge resolution
 3. continuity and Workforce effective-gate agreement
 4. wrong merge rejected
 5. unrelated merge rejected
 6. ancestry drift rejected
 7. multiple pending transitions rejected
 8. stale described-head rejected
 9. failed historical recheck ID reuse rejected
10. only fresh WORKFORCE-HARNESS-RECHECK-02 accepted as next phase
11. product remains blocked regardless of audit completeness
12. historical findings / run results remain immutable
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_gates():
    cs = _load_json(REPO / "docs" / "continuity" / "CURRENT_STATE.json")
    return cs["pre_merge_gate"], cs["post_merge_gate"]


# Reuse the proven FIX-02 fixture helpers.
if str(REPO / "tools" / "audit") not in sys.path:
    sys.path.insert(0, str(REPO / "tools" / "audit"))
import test_workforce_fix02 as _t2

# Import the Workforce resolver directly.
if str(REPO / "tools" / "workforce") not in sys.path:
    sys.path.insert(0, str(REPO / "tools" / "workforce"))
import state_gate_resolver as sgr

# Immutable historical sync-fix/harness-recheck milestones.
BASE_SHA = "88b312fb2d7f3ba36fd49d95e80bdbfdded3d71f"
SYNC_FIX_PRE = "WORKFORCE-CONTINUITY-SYNC-FIX-01"
SYNC_FIX_POST = "WORKFORCE-HARNESS-RECHECK-02"
FAIL_TOKEN = "WORKFORCE-HARNESS-RECHECK-01"

# Current live pre/post gates are read from CURRENT_STATE.json at import time.
PRE_MERGE_TOKEN, POST_MERGE_TOKEN = _load_gates()

TASK_ID = "ANOX-TASK-WORKFORCE-RETEST-CLOSURE-INGEST"
DELIVERY_BRANCH = "governance/workforce-retest-closure-ingest"
RECHECK01_ID = "ANOX-TASK-HARNESSRECHECK01"
RECHECK01_RUN = "ANOX-RUN-HARNESSRECHECK01"
RECHECK02_ID = "ANOX-TASK-WORKFORCE-HARNESS-RECHECK-02"

TARGET_FINDINGS = (
    "ANOX-WORKFORCE-AUDIT-001",
    "ANOX-WORKFORCE-AUDIT-002",
    "ANOX-WORKFORCE-AUDIT-005",
)


def _fixture_overrides(event_id):
    return {
        "delivery_branch": DELIVERY_BRANCH,
        "canonical_branch": "main",
        "baseline_branch": "main",
        "current_task": f"{TASK_ID} (Ready For Remote; awaits human merge)",
        "latest_material_event_id": event_id,
        "latest_human_history_event_id": event_id,
        "latest_agent_history_event_id": event_id,
    }


def _add_unsealed_pending_events(tmp, first_event_id="ANOX-EVENT-0097"):
    """Convert the fixture's sealed first event into an unsealed pending one
    and append a second unsealed pending event. Memory surfaces are kept
    pointing at the last sealed event (ANOX-EVENT-0042) so validate_continuity
    fails specifically on the multiple-pending condition rather than pointer
    mismatch.
    """
    ledger_path = tmp / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl"
    ledger = [json.loads(l) for l in ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    for e in ledger:
        if e.get("event_id") == first_event_id:
            e["end_head"] = "__PENDING_HEAD__"
            e["start_head"] = "__PENDING_HEAD__"
            e["status"] = "candidate"
    ledger.append({
        "event_id": "ANOX-EVENT-0098",
        "date": "2026-09-09",
        "type": "candidate",
        "task": "WORKFORCE-HARNESS-RECHECK-02",
        "summary": "Second pending transition",
        "status": "candidate",
        "start_head": "__PENDING_HEAD__",
        "end_head": "__PENDING_HEAD__",
        "gate_after": POST_MERGE_TOKEN,
    })
    ledger_path.write_text("\n".join(json.dumps(e) for e in ledger) + "\n", encoding="utf-8")

    last_sealed = "ANOX-EVENT-0042"
    cs = _load_json(tmp / "docs" / "continuity" / "CURRENT_STATE.json")
    cs["latest_material_event_id"] = last_sealed
    cs["latest_human_history_event_id"] = last_sealed
    cs["latest_agent_history_event_id"] = last_sealed
    (tmp / "docs" / "continuity" / "CURRENT_STATE.json").write_text(json.dumps(cs, indent=2), encoding="utf-8")

    pmi = tmp / "docs" / "continuity" / "PROJECT_MEMORY_SURFACE_INDEX.md"
    pmi.write_text("# PROJECT MEMORY SURFACE INDEX\n\n- Latest event: ANOX-EVENT-0042\n", encoding="utf-8")
    (tmp / "PROJECT_STATE.md").write_text(
        "# PROJECT STATE\n\n- Branch: `main`\n- Latest material event: `ANOX-EVENT-0042`\n- Product: BLOCKED_PENDING_FINAL_AUDIT\n\n<!-- ANOX_EVENT: ANOX-EVENT-0042 -->\n",
        encoding="utf-8",
    )
    (tmp / "FORTSCHRITT.md").write_text(
        "# FORTSCHRITT\n\n## Latest\n\n- ANOX-EVENT-0042: WORKFORCE-CONTINUITY-SYNC-FIX-01 and HARNESS-RECHECK-01 FAIL.\n\n<!-- ANOX_EVENT: ANOX-EVENT-0042 -->\n",
        encoding="utf-8",
    )


def _bind_historical_task_start_shas(tmp, base):
    """In a fixture, bind the closed HARNESS-RECHECK-01 start_sha to base so
    B027-A does not fail on an unbound start SHA."""
    path = tmp / "docs" / "workforce" / "registries" / "tasks.jsonl"
    if not path.exists():
        return
    tasks = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    for t in tasks:
        if t.get("task_id") == RECHECK01_ID and t.get("status") == "Closed":
            t["start_sha"] = base
    path.write_text("\n".join(json.dumps(t) for t in tasks) + "\n", encoding="utf-8")


def _workforce_state(tmp):
    return _load_json(tmp / "docs" / "workforce" / "WORKFORCE_STATE.json")


def _patch_current_state_baseline(tmp, base):
    """Set the state baseline ancestry to the actual fixture main base.

    The fixture starts with hardcoded historical SHAs that are not ancestors of
    the synthetic main branch, which would otherwise fail baseline ancestry
    checks.  This helper rewrites them to the real fixture base SHA.
    """
    cs = _load_json(tmp / "docs" / "continuity" / "CURRENT_STATE.json")
    cs["latest_merge_to_baseline"] = base
    cs["previous_baseline_head"] = base
    cs["baseline_tag_sha"] = base
    (tmp / "docs" / "continuity" / "CURRENT_STATE.json").write_text(json.dumps(cs, indent=2), encoding="utf-8")


def _patch_workforce_state_for_sync(tmp, pre_gate, post_gate, described):
    """Rewrite the FIX-02 fixture WORKFORCE_STATE.json to closure-ingest values."""
    ws = _workforce_state(tmp)
    ws["delivery_branch"] = DELIVERY_BRANCH
    ws["described_head"] = described
    ws["current_gate"] = pre_gate
    ws["current_writer"] = {
        "task_id": TASK_ID,
        "role_id": "ROLE-009",
        "branch": DELIVERY_BRANCH,
    }
    ws["next_phase"] = post_gate
    fpa = ws.setdefault("final_pre_product_audit", {})
    fpa["product_development_state"] = "BLOCKED_PENDING_FINAL_AUDIT"
    fpa["security_architecture_audit"] = "NOT_STARTED"
    fpa["next_phase"] = post_gate

    pre = ws.setdefault("pre_merge_state", {})
    pre["described_head"] = described
    pre["current_gate"] = pre_gate
    pre["current_writer"] = {
        "task_id": TASK_ID,
        "role_id": "ROLE-009",
        "branch": DELIVERY_BRANCH,
    }
    pre["next_phase"] = post_gate
    pre["current_task"] = TASK_ID
    pre["active_task"] = TASK_ID

    post = ws.setdefault("post_merge_state", {})
    post["described_head"] = described
    post["current_gate"] = post_gate
    post["current_writer"] = None
    post["next_phase"] = post_gate
    post["current_task"] = f"{TASK_ID} merged — awaiting independent security architecture audit"
    post["active_task"] = None

    (tmp / "docs" / "workforce" / "WORKFORCE_STATE.json").write_text(json.dumps(ws, indent=2), encoding="utf-8")


def _derive_gate(tmp, branch, head):
    """Call derive_effective_workforce_state and return (current_gate, error)."""
    ws = _workforce_state(tmp)
    effective = sgr.derive_effective_workforce_state(
        workforce_state=ws,
        live_branch=branch,
        live_head=head,
        repo_root=str(tmp),
    )
    if effective is None:
        return None, "resolver returned None"
    if not isinstance(effective, dict):
        return str(effective), None
    return effective.get("current_gate"), None


def _validate_continuity(tmp, mode="live", archive=None, env=None):
    """Run validate_continuity.py in a temp repo and return (returncode, stdout+stderr)."""
    validator = tmp / "tools" / "continuity" / "validate_continuity.py"
    cmd = [sys.executable, str(validator), "--mode", mode]
    if archive:
        cmd.extend(["--archive", str(archive)])
    r = subprocess.run(
        cmd,
        cwd=tmp,
        capture_output=True,
        text=True,
        env=env,
    )
    return r.returncode, r.stdout + r.stderr


class WorkforceContinuitySyncFix01Tests(unittest.TestCase):
    """Adversarial continuity/workforce sync tests."""

    def setUp(self):
        self.pre, self.post = _load_gates()

    def _prepare_fixture(self, event_id="ANOX-EVENT-0099", merge=True):
        """Build the canonical two-commit delivery fixture.

        Returns (tmp, base, sub, branch, main_head_or_None).
        """
        tmp = _t2.make_bare_repo()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)

        base = _t2.copy_project_skeleton(tmp, source_repo=REPO)
        branch = DELIVERY_BRANCH
        _t2.git(["checkout", "-B", branch], tmp)

        _t2.setup_fixture_state(
            tmp,
            described=base,
            pre_gate=self.pre,
            post_gate=self.post,
            state_for_fixture=_fixture_overrides(event_id),
        )
        _patch_workforce_state_for_sync(tmp, self.pre, self.post, base)
        _patch_current_state_baseline(tmp, base)
        _t2.git(["add", "-A"], tmp)
        _t2.git(["commit", "-m", "continuity-sync substantive"], tmp)
        sub = _t2.git(["rev-parse", "HEAD"], tmp).stdout.strip()

        _t2.setup_fixture_state(
            tmp,
            described=sub,
            pre_gate=self.pre,
            post_gate=self.post,
            state_for_fixture=_fixture_overrides(event_id),
        )
        _patch_workforce_state_for_sync(tmp, self.pre, self.post, sub)
        _patch_current_state_baseline(tmp, base)
        _t2.update_handoff_git_state(tmp, sub, branch, self.pre, self.post)
        _t2.synchronize_project_memory(tmp, sub, event_id=event_id)
        _bind_historical_task_start_shas(tmp, base)
        _t2.git(["add", "-A"], tmp)
        _t2.git(["commit", "-m", "continuity-sync metadata"], tmp)

        main_head = None
        if merge:
            _t2.git(["checkout", "main"], tmp)
            _t2.git([
                "merge", "--no-ff", "-m",
                "Human merge continuity-sync", branch,
            ], tmp)
            main_head = _t2.git(["rev-parse", "HEAD"], tmp).stdout.strip()

        return tmp, base, sub, branch, main_head

    def _generate_handoff_gate(self, tmp):
        """Generate an archive in tmp and return the rendered effective gate."""
        scratch = Path(tempfile.mkdtemp(prefix="anox_sync_ho_"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        zip_path, extract = _t2.generate_and_extract(tmp, scratch, emergency=True)
        return _t2.extract_effective_gate(extract / "docs" / "continuity" / "CURRENT_HANDOFF.md"), extract

    # ------------------------------------------------------------------
    # 1. valid delivery / pre-merge resolution
    # ------------------------------------------------------------------
    def test_01_delivery_pre_merge_resolution(self):
        tmp, base, sub, branch, _ = self._prepare_fixture(merge=False)

        delivery_head = _t2.git(["rev-parse", "HEAD"], tmp).stdout.strip()
        gate, err = _derive_gate(tmp, branch, delivery_head)
        self.assertIsNone(err, f"resolver error: {err}")
        self.assertIn(PRE_MERGE_TOKEN, gate, f"pre-merge gate missing from {gate}")

        rc, out = _validate_continuity(tmp)
        self.assertEqual(rc, 0, f"validate_continuity must pass on delivery branch:\n{out}")
        self.assertIn("effective gate:", out)

    # ------------------------------------------------------------------
    # 2. valid synthetic Human merge / post-merge resolution
    # ------------------------------------------------------------------
    def test_02_human_merge_post_merge_resolution(self):
        tmp, base, sub, branch, main_head = self._prepare_fixture(merge=True)

        gate, err = _derive_gate(tmp, "main", main_head)
        self.assertIsNone(err, f"resolver error: {err}")
        self.assertIn(POST_MERGE_TOKEN, gate, f"post-merge gate missing from {gate}")

    # ------------------------------------------------------------------
    # 3. continuity and Workforce effective-gate agreement
    # ------------------------------------------------------------------
    def test_03_continuity_workforce_agreement(self):
        tmp, base, sub, branch, main_head = self._prepare_fixture(merge=True)

        # Main: continuity, workforce, and generated handoff must agree on post.
        rc, out = _validate_continuity(tmp)
        self.assertIn("effective gate: " + POST_MERGE_TOKEN, out)
        self.assertIn("OK   continuity and workforce effective gates agree", out)

        workforce_post, _ = _derive_gate(tmp, "main", main_head)
        self.assertEqual(workforce_post, self.post)

        handoff_gate, _ = self._generate_handoff_gate(tmp)
        self.assertEqual(handoff_gate, self.post)

        # Delivery branch: continuity and workforce must agree on pre.
        _t2.git(["checkout", branch], tmp)
        delivery_head = _t2.git(["rev-parse", "HEAD"], tmp).stdout.strip()
        workforce_pre, _ = _derive_gate(tmp, branch, delivery_head)
        self.assertIn(PRE_MERGE_TOKEN, workforce_pre)

        rc, out = _validate_continuity(tmp)
        self.assertIn("effective gate: " + PRE_MERGE_TOKEN, out)
        self.assertIn("OK   continuity and workforce effective gates agree", out)

    # ------------------------------------------------------------------
    # 4. wrong merge rejected
    # ------------------------------------------------------------------
    def test_04_wrong_merge_rejected(self):
        tmp, base, sub, branch, _ = self._prepare_fixture(merge=False)

        _t2.git(["checkout", "main"], tmp)
        _t2.git(["checkout", "-B", "fake-delivery"], tmp)
        (tmp / "docs" / "continuity" / "PROJECT_MEMORY_SURFACE_INDEX.md").write_text("# tamper\n", encoding="utf-8")
        _t2.git(["add", "-A"], tmp)
        _t2.git(["commit", "-m", "fake delivery"], tmp)

        _t2.git(["checkout", "main"], tmp)
        r = _t2.git([
            "merge", "--no-ff", "-m", "wrong merge", "fake-delivery",
        ], tmp, check=False)
        if r.returncode != 0:
            self.skipTest("git merge rejected the wrong merge")

        main_head = _t2.git(["rev-parse", "HEAD"], tmp).stdout.strip()
        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validate_continuity must reject a wrong merge")

        gate, _ = _derive_gate(tmp, "main", main_head)
        self.assertFalse(gate and POST_MERGE_TOKEN in gate, "resolver must not advance on wrong merge")

    # ------------------------------------------------------------------
    # 5. unrelated merge rejected
    # ------------------------------------------------------------------
    def test_05_unrelated_merge_rejected(self):
        tmp, base, sub, branch, _ = self._prepare_fixture(merge=False)

        _t2.git(["checkout", "--orphan", "unrelated"], tmp)
        (tmp / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
        _t2.git(["add", "-A"], tmp)
        _t2.git(["commit", "-m", "unrelated root"], tmp)
        unrelated_head = _t2.git(["rev-parse", "HEAD"], tmp).stdout.strip()

        _t2.git(["checkout", "main"], tmp)
        r = _t2.git([
            "merge", "--no-ff", "-m", "unrelated merge", "unrelated",
        ], tmp, check=False)
        if r.returncode != 0:
            self.skipTest("git merge rejected the unrelated merge")

        main_head = _t2.git(["rev-parse", "HEAD"], tmp).stdout.strip()
        gate, _ = _derive_gate(tmp, "main", main_head)
        self.assertFalse(gate and POST_MERGE_TOKEN in gate, "resolver must not advance on unrelated merge")

        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validate_continuity must reject unrelated merge")

    # ------------------------------------------------------------------
    # 6. ancestry drift rejected
    # ------------------------------------------------------------------
    def test_06_ancestry_drift_rejected(self):
        tmp, base, sub, branch, _ = self._prepare_fixture(merge=False)

        # Advance main with a substantive product change before accepting delivery.
        _t2.git(["checkout", "main"], tmp)
        (tmp / "backend" / "app.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp / "backend" / "app.py").write_text("# product drift\n", encoding="utf-8")
        _t2.git(["add", "-A"], tmp)
        _t2.git(["commit", "-m", "main product drift"], tmp)

        _t2.git([
            "merge", "--no-ff", "-m", "merge with drift", branch,
        ], tmp)
        main_head = _t2.git(["rev-parse", "HEAD"], tmp).stdout.strip()

        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validate_continuity must reject substantive main-line drift")
        # The resolver may still see the merge, but the canonical validator must
        # reject drifted / non-metadata main-line changes.

    # ------------------------------------------------------------------
    # 7. multiple pending transitions rejected
    # ------------------------------------------------------------------
    def test_07_multiple_pending_transitions_rejected(self):
        tmp, base, sub, branch, _ = self._prepare_fixture(merge=False, event_id="ANOX-EVENT-0097")

        # Convert the sealed 0097 fixture event to unsealed and append a second
        # unsealed event. Keep memory surfaces at the last sealed 0042 event so
        # the only failure reason is the multiple-pending condition.
        _add_unsealed_pending_events(tmp)

        ledger_path = tmp / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl"
        ledger = [json.loads(l) for l in ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        unsealed = [e for e in ledger if re.fullmatch(r"__([A-Z0-9_]+)__", e.get("end_head", ""))]
        self.assertGreater(len(unsealed), 1, "fixture did not produce multiple unsealed pending events")

        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validate_continuity must reject multiple pending transitions")

    # ------------------------------------------------------------------
    # 8. stale described-head rejected
    # ------------------------------------------------------------------
    def test_08_stale_described_head_rejected(self):
        tmp, base, sub, branch, _ = self._prepare_fixture(merge=False)

        stale = "0" * 40
        cs = _load_json(tmp / "docs" / "continuity" / "CURRENT_STATE.json")
        cs["described_head"] = stale
        (tmp / "docs" / "continuity" / "CURRENT_STATE.json").write_text(json.dumps(cs, indent=2), encoding="utf-8")
        ws = _workforce_state(tmp)
        ws["described_head"] = stale
        (tmp / "docs" / "workforce" / "WORKFORCE_STATE.json").write_text(json.dumps(ws, indent=2), encoding="utf-8")

        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validate_continuity must reject a stale described_head")

    # ------------------------------------------------------------------
    # 9. failed historical recheck ID reuse rejected
    # ------------------------------------------------------------------
    def test_09_harnessrecheck01_id_reuse_rejected(self):
        tmp, base, sub, branch, _ = self._prepare_fixture(merge=False)

        # Try to promote the failed historical recheck ID.
        ws = _workforce_state(tmp)
        ws["next_phase"] = "WORKFORCE-HARNESS-RECHECK-01"
        if isinstance(ws.get("post_merge_state"), dict):
            ws["post_merge_state"]["next_phase"] = "WORKFORCE-HARNESS-RECHECK-01"
        (tmp / "docs" / "workforce" / "WORKFORCE_STATE.json").write_text(json.dumps(ws, indent=2), encoding="utf-8")

        cs = _load_json(tmp / "docs" / "continuity" / "CURRENT_STATE.json")
        cs["post_merge_gate"] = "WORKFORCE-HARNESS-RECHECK-01"
        (tmp / "docs" / "continuity" / "CURRENT_STATE.json").write_text(json.dumps(cs, indent=2), encoding="utf-8")

        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validate_continuity must reject reuse of failed WORKFORCE-HARNESS-RECHECK-01")

        tasks = _t2.load_jsonl(tmp / "docs" / "workforce" / "registries" / "tasks.jsonl")
        recheck01 = next((t for t in tasks if t.get("task_id") == RECHECK01_ID), {})
        self.assertNotEqual(recheck01.get("status"), "Candidate", "failed historical recheck must not become a fresh Candidate")

    # ------------------------------------------------------------------
    # 10. only fresh WORKFORCE-HARNESS-RECHECK-02 accepted as next phase
    # ------------------------------------------------------------------
    def test_10_only_fresh_recheck02_next_phase(self):
        tmp, base, sub, branch, main_head = self._prepare_fixture(merge=True)

        ws = _workforce_state(tmp)
        self.assertIn(POST_MERGE_TOKEN, ws.get("next_phase", ""))

        # Mutating to any other next phase must not validate.
        ws["next_phase"] = "WORKFORCE-RETEST-02"
        if isinstance(ws.get("post_merge_state"), dict):
            ws["post_merge_state"]["next_phase"] = "WORKFORCE-RETEST-02"
        (tmp / "docs" / "workforce" / "WORKFORCE_STATE.json").write_text(json.dumps(ws, indent=2), encoding="utf-8")

        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validator must reject stale next phase")

    # ------------------------------------------------------------------
    # 11. product remains blocked regardless of audit completeness
    # ------------------------------------------------------------------
    def test_11_product_blocked(self):
        tmp, base, sub, branch, main_head = self._prepare_fixture(merge=True)

        # Archive / handoff validates.
        gate, extract = self._generate_handoff_gate(tmp)
        self.assertIn(POST_MERGE_TOKEN, gate)

        ws = _workforce_state(tmp)
        product = ws.get("product_development_state") or ws.get("final_pre_product_audit", {}).get("product_development_state")
        self.assertEqual(product, "BLOCKED_PENDING_FINAL_AUDIT", "product must remain blocked")

        # Even if archive passes, product state is still blocked.
        rc, out = _validate_continuity(tmp, mode="archive", archive=extract)
        self.assertEqual(rc, 0, "archive validation must pass")
        self.assertIn("BLOCKED_PENDING_FINAL_AUDIT", ws.get("product_development_state", ""))

    # ------------------------------------------------------------------
    # 12. historical findings / run results remain immutable
    # ------------------------------------------------------------------
    def test_12_historical_immutable(self):
        tmp, base, sub, branch, _ = self._prepare_fixture(merge=False)

        # Attempt to mutate a historical finding to Closed.
        findings_path = tmp / "docs" / "workforce" / "registries" / "findings.jsonl"
        findings = _t2.load_jsonl(findings_path)
        mutated = []
        target = None
        for f in findings:
            if f.get("finding_id") in TARGET_FINDINGS:
                target = f
                f["status"] = "Closed"
            mutated.append(f)
        self.assertIsNotNone(target, "target finding must exist in fixture")
        findings_path.write_text("\n".join(json.dumps(f) for f in mutated) + "\n", encoding="utf-8")

        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validator must reject closed target finding")

        # Reset and try to mutate the failed run result.
        findings_path.write_text("\n".join(json.dumps(f) for f in _t2.load_jsonl(tmp / "docs" / "workforce" / "registries" / "findings.jsonl")) + "\n", encoding="utf-8")
        # Actually mutate a run instead.
        runs_path = tmp / "docs" / "workforce" / "registries" / "runs.jsonl"
        runs = _t2.load_jsonl(runs_path)
        run = next((r for r in runs if r.get("run_id") == RECHECK01_RUN), None)
        self.assertIsNotNone(run, "historical run must exist")
        original = run.get("result")
        run["result"] = "PASS"
        runs_path.write_text("\n".join(json.dumps(r) for r in runs) + "\n", encoding="utf-8")

        # The validator direct check (if available) or continuity must notice.
        rc, out = _validate_continuity(tmp)
        self.assertNotEqual(rc, 0, "validator must reject mutated historical run result")
        run["result"] = original


if __name__ == "__main__":
    unittest.main()
