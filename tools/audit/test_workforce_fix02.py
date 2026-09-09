#!/usr/bin/env python3
"""WORKFORCE-FIX-02 adversarial and archive tests.

Tests the handoff generator's archive effective-state rendering and the
preservation/transition invariants for findings 001, 002 and 005.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VALIDATOR = REPO / "tools" / "continuity" / "validate_continuity.py"
GENERATOR = REPO / "tools" / "continuity" / "generate_handoff.py"
FIX02_VALIDATOR = REPO / "tools" / "audit" / "validate_workforce_fix02.py"


def git(args, cwd=None, check=True):
    result = subprocess.run(["git"] + list(args), cwd=str(cwd) if cwd else None, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed (rc={result.returncode}): {result.stderr or result.stdout}")
    return result


def load_jsonl(path):
    if isinstance(path, str):
        path = Path(path)
    if not path.is_absolute():
        path = REPO / path
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def make_bare_repo():
    td = Path(tempfile.mkdtemp(prefix="anox_workforce_fix02_"))
    git(["init", "--quiet"], td)
    git(["config", "user.email", "test@anox.software"], td)
    git(["config", "user.name", "Test"], td)
    return td


def copy_tree(src, dst, ignore=None):
    if dst.exists():
        shutil.rmtree(dst)
    if src.is_dir():
        if ignore:
            shutil.copytree(src, dst, ignore=ignore)
        else:
            shutil.copytree(src, dst)


def copy_project_skeleton(dst, source_repo=REPO):
    """Copy the current docs/tools tree into a fresh repo and commit as main."""
    git(["checkout", "-B", "main"], dst, check=False)
    for sub in ("docs", "tools", "PROJECT_STATE.md", "FORTSCHRITT.md", "DEVIN_PROMPT_OUTPUT_ARCHIV.md"):
        src = source_repo / sub
        if src.exists():
            if src.is_dir():
                copy_tree(src, dst / sub, ignore=shutil.ignore_patterns(".DS_Store"))
            else:
                shutil.copy2(src, dst / sub)
    # Sanitize surfaces that carry stale/contradictory checks for the fixture.
    safe = {
        "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md": "# CURRENT IMPLEMENTATION STATE\n\n- Product: BLOCKED_PENDING_FINAL_AUDIT\n- B-003: MERGED\n- B-004: NOT_STARTED\n- B-005: NOT_STARTED\n",
        "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md": "# CURRENT NEXT DEVIN TASK\n\nNext candidate: WORKFORCE-RETEST-02 (pending human authorization).\n",
        "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md": "# PROJECT MEMORY SURFACE INDEX\n\n- Latest event: ANOX-EVENT-0040\n",
    }
    for rel, text in safe.items():
        p = dst / rel
        if p.exists():
            p.write_text(text, encoding="utf-8")
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    git(["add", "-A"], dst)
    git(["commit", "-m", "skeleton base"], dst)
    return git(["rev-parse", "HEAD"], dst).stdout.strip()


def setup_fixture_state(dst, described, pre_gate, post_gate, state_for_fixture=None):
    """Write a fixture CURRENT_STATE.json and WORKFORCE_STATE.json into dst."""
    state = {
        "schema_version": "B026-1.2",
        "memory_schema_version": "M2B-v1",
        "recorded_at": "2026-09-07",
        "repository": "https://github.com/anox-software/anox-messenger",
        "legacy_repository": "https://github.com/anox-admin/ax-messenger.git",
        "canonical_branch": "main",
        "delivery_branch": "remediation/workforce-fix-02-handoff-archive",
        "baseline_branch": "main",
        "described_head": described,
        "baseline_tag": "v1-foundation-baseline",
        "baseline_tag_sha": "7db20fa4df8dc70392afd803fabaaf20c0b50d7d",
        "latest_merge_to_baseline": "8385f4019184be9b568f65ec4748194595ef339c",
        "previous_baseline_head": "7eede96b3830a9b4a49e43494b60d4163c1e5cb3",
        "handoff_branch": "__HANDOFF_BRANCH__",
        "handoff_head": "__HANDOFF_HEAD__",
        "working_tree": "__WORKING_TREE__",
        "open_pr": None,
        "open_pr_target": "main",
        "continuity_001_status": "ACCEPTED",
        "current_task": "ANOX-TASK-WORKFORCEFIX02 — HANDOFF ARCHIVE EFFECTIVE-STATE RENDERING (Ready For Remote; awaits human merge and independent retest).",
        "current_gate": "__EFFECTIVE_GATE__",
        "pre_merge_gate": pre_gate,
        "post_merge_gate": post_gate,
        "authority_index": "docs/authority/AUTHORITY_INDEX.md",
        "security_invariants_path": "docs/authority/B025/SECURITY_INVARIANTS_V1_1.md",
        "freeze_registry_path": "docs/authority/B_FREEZE_REGISTRY.md",
        "ultimate_architecture_path": "docs/authority/B025/ULTIMATE_MAIN_ARCHITECTURE_B025.md",
        "project_history_ledger_path": "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl",
        "project_memory_surface_index_path": "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md",
        "latest_material_event_id": "ANOX-EVENT-0040",
        "latest_material_event_type": "remediation",
        "latest_human_history_event_id": "ANOX-EVENT-0040",
        "latest_agent_history_event_id": "ANOX-EVENT-0040",
        "project_memory_freshness": "PASS",
        "next_devin_task_path": "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md",
        "handoff_workflow_path": "docs/continuity/HANDOFF_WORKFLOW.md",
        "notes": ["fixture state"],
        "main_baseline_head": "8385f4019184be9b568f65ec4748194595ef339c",
    }
    if state_for_fixture:
        state.update(state_for_fixture)
    (dst / "docs" / "continuity" / "CURRENT_STATE.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    ws = {
        "schema_version": "B027C-v1.1",
        "authority_version": "docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md",
        "canonical_branch": "main",
        "delivery_branch": "remediation/workforce-fix-02-handoff-archive",
        "described_head": described,
        "current_gate": pre_gate,
        "active_roles": ["ROLE-003", "ROLE-009"],
        "blocked_tasks": [],
        "authorized_tasks": ["ANOX-TASK-WORKFORCEFIX02"],
        "current_writer": {"task_id": "ANOX-TASK-WORKFORCEFIX02", "role_id": "ROLE-009", "branch": "remediation/workforce-fix-02-handoff-archive"},
        "pending_human_remote_actions": [],
        "latest_decision_id": None,
        "latest_finding_id": "ANOX-WORKFORCE-AUDIT-002",
        "latest_run_id": "ANOX-RUN-WORKFORCEFIX0002",
        "latest_work_candidate_id": "ANOX-WORK-FINAL-HANDOFF-ACCEPTANCE-001",
        "final_pre_product_audit": {
            "required": True,
            "status": "IN_PROGRESS",
            "completed_audit_ids": [
                "AUDIT-MAIN-ARCHITECTURE",
                "ANOX-AUDIT-WORKFORCE-ARCH-001",
                "LEGACY-AUDIT-B002",
                "LEGACY-AUDIT-B003",
                "LEGACY-AUDIT-CRYPTO",
                "LEGACY-AUDIT-ANDROID-SEC",
                "LEGACY-AUDIT-BUILD",
                "LEGACY-AUDIT-INTEGRATION",
            ],
            "required_audits": ["AUDIT-MAIN-ARCHITECTURE", "AUDIT-WORKFORCE-ARCHITECTURE", "AUDIT-SECURITY-ARCHITECTURE"],
            "product_development_state": "BLOCKED_PENDING_FINAL_AUDIT",
            "main_architecture_audit": "COMPLETE",
            "main_architecture_remediation_phase": "COMPLETE",
            "workforce_architecture_audit": "COMPLETE_WITH_FINDINGS",
            "security_architecture_audit": "NOT_STARTED",
            "next_phase": "WORKFORCE-RETEST-02",
        },
        "pre_merge_state": {
            "described_head": described,
            "current_gate": pre_gate,
            "current_writer": {"task_id": "ANOX-TASK-WORKFORCEFIX02", "role_id": "ROLE-009", "branch": "remediation/workforce-fix-02-handoff-archive"},
            "next_phase": "WORKFORCE-RETEST-02",
            "current_task": "ANOX-TASK-WORKFORCEFIX02",
            "active_task": "ANOX-TASK-WORKFORCEFIX02",
        },
        "post_merge_state": {
            "described_head": described,
            "current_gate": post_gate,
            "current_writer": None,
            "next_phase": "WORKFORCE-RETEST-02",
            "current_task": "WORKFORCE-FIX-02 merged — awaiting independent retest",
            "active_task": None,
        },
        "previous_merges": [
            {
                "merge_head": "8385f4019184be9b568f65ec4748194595ef339c",
                "pre_merge_state": {
                    "described_head": "3cc663e00a23e6a0cc342d3ad941a8e926772cd6",
                    "current_gate": "WORKFORCE-FIX-01 — WORKFORCE GOVERNANCE / CONTINUITY HARDENING (Ready For Remote; awaiting human merge)",
                    "current_writer": {"task_id": "ANOX-TASK-WORKFORCEFIX01", "role_id": "ROLE-003", "branch": "remediation/workforce-fix-01-governance-continuity"},
                    "next_phase": "WORKFORCE-RETEST-01",
                    "current_task": "ANOX-TASK-WORKFORCEFIX01",
                    "active_task": "ANOX-TASK-WORKFORCEFIX01",
                },
                "post_merge_state": {
                    "described_head": "3cc663e00a23e6a0cc342d3ad941a8e926772cd6",
                    "current_gate": "WORKFORCE-RETEST-01 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST (Candidate, pending human authorization)",
                    "current_writer": None,
                    "next_phase": "WORKFORCE-RETEST-01",
                    "current_task": "WORKFORCE-FIX-01 merged — awaiting independent retest",
                    "active_task": None,
                },
            }
        ],
        "final_operational_handoff_acceptance_gate": {
            "gate_id": "FINAL-OPERATIONAL-HANDOFF-BOOTSTRAP-ACCEPTANCE",
            "title": "FINAL-OPERATIONAL-HANDOFF-BOOTSTRAP-ACCEPTANCE",
            "status": "NOT_EXECUTED",
            "result": "PENDING",
            "work_candidate_id": "ANOX-WORK-FINAL-HANDOFF-ACCEPTANCE-001",
            "rationale": "Before the product final gate opens, the project must prove the complete development/workforce system can be reconstructed from the repository and handoff archive without chat history.",
        },
        "product_development_state": "BLOCKED_PENDING_FINAL_AUDIT",
        "next_phase": "WORKFORCE-RETEST-02",
        "main_architecture_audit": "COMPLETE",
        "main_architecture_remediation_phase": "COMPLETE",
        "workforce_architecture_audit": "COMPLETE_WITH_FINDINGS",
        "legacy_audit_set_status": "6/6 COMPLETE",
    }
    (dst / "docs" / "workforce" / "WORKFORCE_STATE.json").write_text(json.dumps(ws, indent=2), encoding="utf-8")


def _next_event_id(ledger_path):
    """Return the next sequential ANOX-EVENT ID not already in the ledger."""
    max_n = 0
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                m = re.match(r"ANOX-EVENT-(\d+)", event.get("event_id", ""))
                if m:
                    max_n = max(max_n, int(m.group(1)))
            except json.JSONDecodeError:
                continue
    return f"ANOX-EVENT-{max_n + 1:04d}"


def synchronize_project_memory(dst, end_head, event_id=None):
    """Append a sealed fixture event to the ledger and update memory surfaces."""
    if event_id is None:
        event_id = _next_event_id(dst / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl")
    ledger_path = dst / "docs" / "continuity" / "PROJECT_HISTORY_LEDGER.jsonl"
    event = {
        "event_id": event_id,
        "date": "2026-09-07",
        "type": "remediation",
        "task": "WORKFORCE-FIX-02",
        "summary": "WORKFORCE-FIX-02 archive effective-state rendering remediated; next WORKFORCE-RETEST-02.",
        "status": "remediated",
        "start_head": "8385f4019184be9b568f65ec4748194595ef339c",
        "end_head": end_head,
        "gate_after": "WORKFORCE-RETEST-02 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST",
        "findings": ["ANOX-WORKFORCE-AUDIT-002:ready_for_retest"],
        "tests": {"validate_workforce_fix02": 1, "test_workforce_fix02": 9, "validate_continuity_archive": 1, "b027a": 1, "b027b": 1, "b027_integrity": 1},
        "refs": [f"git:{end_head}", "tools/continuity/generate_handoff.py", "tools/audit/validate_workforce_fix02.py", "tools/audit/test_workforce_fix02.py", "docs/continuity/CURRENT_HANDOFF.md", "docs/workforce/WORKFORCE_STATE.json"],
        "evidence": ["workforce-fix02-validator", "workforce-fix02-adversarial-tests", "archive-effective-state-render"],
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    # Update surface index and CURRENT_STATE to point at the new fixture event.
    pmi = dst / "docs" / "continuity" / "PROJECT_MEMORY_SURFACE_INDEX.md"
    pmi.write_text(f"# PROJECT MEMORY SURFACE INDEX\n\n- Latest event: {event_id}\n", encoding="utf-8")
    cs = dst / "docs" / "continuity" / "CURRENT_STATE.json"
    state = json.loads(cs.read_text(encoding="utf-8"))
    state["latest_material_event_id"] = event_id
    state["latest_human_history_event_id"] = event_id
    state["latest_agent_history_event_id"] = event_id
    cs.write_text(json.dumps(state, indent=2), encoding="utf-8")

    (dst / "PROJECT_STATE.md").write_text(
        f"# PROJECT STATE\n\n- Branch: `main`\n- Latest material event: `{event_id}`\n- Product: BLOCKED_PENDING_FINAL_AUDIT\n\n<!-- ANOX_EVENT: {event_id} -->\n",
        encoding="utf-8",
    )
    (dst / "FORTSCHRITT.md").write_text(
        f"# FORTSCHRITT\n\n## Latest\n\n- {event_id}: WORKFORCE-FIX-02 archive effective-state rendering remediated; next WORKFORCE-RETEST-02.\n\n<!-- ANOX_EVENT: {event_id} -->\n",
        encoding="utf-8",
    )


def update_handoff_git_state(dst, described, branch, pre_gate, post_gate):
    handoff = dst / "docs" / "continuity" / "CURRENT_HANDOFF.md"
    text = handoff.read_text(encoding="utf-8")
    # Update the hardcoded lines that are not runtime-derived.
    text = re.sub(r"^Delivery branch: `.*`$", f"Delivery branch: `{branch}`", text, flags=re.MULTILINE)
    text = re.sub(r"^Described HEAD: `.*`$", f"Described HEAD: `{described}`", text, flags=re.MULTILINE)
    text = re.sub(r"^Main baseline HEAD: `.*`$", "Main baseline HEAD: `8385f4019184be9b568f65ec4748194595ef339c`", text, flags=re.MULTILINE)
    handoff.write_text(text, encoding="utf-8")

    git_state = dst / "docs" / "continuity" / "CURRENT_GIT_STATE.md"
    gst = git_state.read_text(encoding="utf-8")
    gst = re.sub(r"^(- Main baseline: ).*$", r"\g<1>8385f4019184be9b568f65ec4748194595ef339c", gst, flags=re.MULTILINE)
    gst = re.sub(r"^(- Described HEAD: ).*$", r"\g<1>" + described, gst, flags=re.MULTILINE)
    gst = re.sub(r"^(- Pre-merge gate: ).*$", r"\g<1>" + pre_gate, gst, flags=re.MULTILINE)
    gst = re.sub(r"^(- Post-merge gate: ).*$", r"\g<1>" + post_gate, gst, flags=re.MULTILINE)
    git_state.write_text(gst, encoding="utf-8")


def generate_and_extract(repo, output_dir, emergency=False):
    """Run the temp repo's generator, extract the archive, and return (zip_path, extract_dir)."""
    generator = repo / "tools" / "continuity" / "generate_handoff.py"
    cmd = [sys.executable, str(generator)]
    if emergency:
        cmd.append("--emergency")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo / "tools" / "continuity") + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"generate_handoff failed:\n{r.stdout}\n{r.stderr}")
    m = re.search(r"ZIP PATH:\s+(\S+)", r.stdout)
    if not m:
        raise RuntimeError(f"could not find ZIP PATH in:\n{r.stdout}")
    zip_path = Path(m.group(1))
    if not zip_path.exists():
        raise RuntimeError(f"zip path does not exist: {zip_path}")
    extract_dir = output_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    return zip_path, extract_dir


def validate_archive(extract_dir):
    r = subprocess.run([sys.executable, str(VALIDATOR), "--mode", "archive", "--archive", str(extract_dir)],
                       cwd=REPO, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def extract_effective_gate(handoff_path):
    text = handoff_path.read_text(encoding="utf-8")
    m = re.search(r"^Effective gate: `([^`]+)`", text, re.MULTILINE)
    return m.group(1) if m else None


class ArchiveEffectiveStateTests(unittest.TestCase):
    """Tests for the archive effective-state renderer."""

    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="anox_fix02_archive_"))

    def tearDown(self):
        shutil.rmtree(self.scratch)

    def _sanitize_for_fixture(self, dst):
        safe = {
            "docs/continuity/CURRENT_IMPLEMENTATION_STATE.md": "# CURRENT IMPLEMENTATION STATE\n\n- Product: BLOCKED_PENDING_FINAL_AUDIT\n- B-003: MERGED\n- B-004: NOT_STARTED\n- B-005: NOT_STARTED\n",
            "docs/continuity/CURRENT_NEXT_DEVIN_TASK.md": "# CURRENT NEXT DEVIN TASK\n\nNext candidate: WORKFORCE-RETEST-02 (pending human authorization).\n",
            "docs/continuity/PROJECT_MEMORY_SURFACE_INDEX.md": "# PROJECT MEMORY SURFACE INDEX\n\n- Latest event: ANOX-EVENT-0039\n",
        }
        for rel, text in safe.items():
            (dst / rel).write_text(text, encoding="utf-8")

    def test_01_real_post_merge_regression_fixture(self):
        """Use current canonical merged main as a regression fixture.

        Copy the new generator and CURRENT_HANDOFF.md template onto a checkout
        of the canonical FIX-01 merge SHA, generate a handoff, and validate that
        the archive shows the post-merge effective gate WORKFORCE-RETEST-01.
        """
        tmp = self.scratch / "real_fixture"
        git(["clone", "--quiet", str(REPO), str(tmp)])
        git(["checkout", "-B", "main", "8385f4019184be9b568f65ec4748194595ef339c"], tmp)
        self._sanitize_for_fixture(tmp)
        # Overlay the new generator and template.
        shutil.copy2(REPO / "tools" / "continuity" / "generate_handoff.py",
                     tmp / "tools" / "continuity" / "generate_handoff.py")
        shutil.copy2(REPO / "docs" / "continuity" / "CURRENT_HANDOFF.md",
                     tmp / "docs" / "continuity" / "CURRENT_HANDOFF.md")
        git(["add", "-A"], tmp)
        git(["commit", "-m", "overlay FIX-02 handoff generator and template"], tmp)

        zip_path, extract = generate_and_extract(tmp, self.scratch, emergency=True)
        code, out, err = validate_archive(extract)
        self.assertEqual(code, 0, f"archive validation failed:\n{out}\n{err}")

        gate = extract_effective_gate(extract / "docs" / "continuity" / "CURRENT_HANDOFF.md")
        self.assertIsNotNone(gate)
        self.assertIn("WORKFORCE-RETEST-01", gate)
        self.assertIn("(Candidate, pending human authorization)", gate)

    def test_02_synthetic_future_merge(self):
        """A canonical Human merge of the FIX-02 delivery advances the effective
        gate to WORKFORCE-RETEST-02 without requiring a third bookkeeping commit.
        """
        tmp = make_bare_repo()
        base = copy_project_skeleton(tmp, source_repo=REPO)

        # Substantive commit on delivery branch.
        git(["checkout", "-b", "remediation/workforce-fix-02-handoff-archive"], tmp)
        setup_fixture_state(tmp, described="__SUBSTANTIVE__",
                            pre_gate="WORKFORCE-FIX-02 — HANDOFF ARCHIVE EFFECTIVE-STATE RENDERING (Ready For Remote; awaiting human merge)",
                            post_gate="WORKFORCE-RETEST-02 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST (Candidate, pending human authorization)")
        git(["add", "-A"], tmp)
        git(["commit", "-m", "FIX-02 substantive"], tmp)
        sub = git(["rev-parse", "HEAD"], tmp).stdout.strip()

        # Metadata commit: described_head, surface values, Project Memory.
        setup_fixture_state(tmp, described=sub,
                            pre_gate="WORKFORCE-FIX-02 — HANDOFF ARCHIVE EFFECTIVE-STATE RENDERING (Ready For Remote; awaiting human merge)",
                            post_gate="WORKFORCE-RETEST-02 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST (Candidate, pending human authorization)")
        update_handoff_git_state(
            tmp, sub,
            "remediation/workforce-fix-02-handoff-archive",
            "WORKFORCE-FIX-02 — HANDOFF ARCHIVE EFFECTIVE-STATE RENDERING (Ready For Remote; awaiting human merge)",
            "WORKFORCE-RETEST-02 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST (Candidate, pending human authorization)",
        )
        synchronize_project_memory(tmp, sub)
        git(["add", "-A"], tmp)
        git(["commit", "-m", "FIX-02 metadata"], tmp)

        # Merge to main and generate from main.
        git(["checkout", "main"], tmp)
        git(["merge", "--no-ff", "-m", "Merge FIX-02", "remediation/workforce-fix-02-handoff-archive"], tmp)

        # No third bookkeeping commit should be necessary: the post-merge head
        # is exactly the merge commit.
        main_head = git(["rev-parse", "HEAD"], tmp).stdout.strip()
        parents = git(["rev-list", "--parents", "-n", "1", main_head], tmp).stdout.strip().split()
        self.assertEqual(len(parents), 3, "merge should have exactly two parents")

        zip_path, extract = generate_and_extract(tmp, self.scratch, emergency=True)
        code, out, err = validate_archive(extract)
        self.assertEqual(code, 0, f"archive validation failed:\n{out}\n{err}")

        gate = extract_effective_gate(extract / "docs" / "continuity" / "CURRENT_HANDOFF.md")
        self.assertIsNotNone(gate)
        self.assertIn("WORKFORCE-RETEST-02", gate)

        # Verify no third task-authored commit: only the merge commit on main.
        count = git(["rev-list", "--count", f"{base}..{main_head}"], tmp).stdout.strip()
        # base..main = merge (one) plus the two delivery-branch commits reachable through it
        # but the first-parent path from base contains just the merge.
        first_parent_commits = git(["rev-list", "--first-parent", "--count", f"{base}..{main_head}"], tmp).stdout.strip()
        self.assertEqual(first_parent_commits, "1", "main first-parent path should have only the merge (no third commit)")

    def test_03_pre_merge_state_on_delivery_branch(self):
        """On the delivery branch, the archive renders the pre-merge effective gate."""
        tmp = make_bare_repo()
        copy_project_skeleton(tmp, source_repo=REPO)
        git(["checkout", "-b", "remediation/workforce-fix-02-handoff-archive"], tmp)

        sub = git(["rev-parse", "HEAD"], tmp).stdout.strip()

        setup_fixture_state(tmp, described=sub,
                            pre_gate="WORKFORCE-FIX-02 — HANDOFF ARCHIVE EFFECTIVE-STATE RENDERING (Ready For Remote; awaiting human merge)",
                            post_gate="WORKFORCE-RETEST-02 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST (Candidate, pending human authorization)")
        update_handoff_git_state(
            tmp, sub,
            "remediation/workforce-fix-02-handoff-archive",
            "WORKFORCE-FIX-02 — HANDOFF ARCHIVE EFFECTIVE-STATE RENDERING (Ready For Remote; awaiting human merge)",
            "WORKFORCE-RETEST-02 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST (Candidate, pending human authorization)",
        )
        synchronize_project_memory(tmp, sub)
        git(["add", "-A"], tmp)
        git(["commit", "-m", "FIX-02 state"], tmp)

        zip_path, extract = generate_and_extract(tmp, self.scratch, emergency=True)
        code, out, err = validate_archive(extract)
        self.assertEqual(code, 0, f"archive validation failed:\n{out}\n{err}")

        gate = extract_effective_gate(extract / "docs" / "continuity" / "CURRENT_HANDOFF.md")
        self.assertIsNotNone(gate)
        self.assertIn("WORKFORCE-FIX-02", gate)

    def test_04_wrong_merge_fails_closed(self):
        """A non-canonical merge where the described_head is not the delivery
        parent must not be accepted as a post-merge gate advancement.
        """
        sys.path.insert(0, str(REPO / "tools" / "audit"))
        import lifecycle_legality as ll

        tmp = make_bare_repo()
        base = copy_project_skeleton(tmp, source_repo=REPO)

        # Build a real delivery branch.
        git(["checkout", "-b", "remediation/workforce-fix-02-handoff-archive"], tmp)
        setup_fixture_state(tmp, described=base,
                            pre_gate="WORKFORCE-FIX-02 — HANDOFF ARCHIVE EFFECTIVE-STATE RENDERING",
                            post_gate="WORKFORCE-RETEST-02 — INDEPENDENT TARGETED WORKFORCE GOVERNANCE DELTA RETEST")
        git(["add", "-A"], tmp)
        git(["commit", "-m", "FIX-02 delivery"], tmp)
        sub = git(["rev-parse", "HEAD"], tmp).stdout.strip()

        # Make a fake merge on main that uses a different second parent.
        git(["checkout", "main"], tmp)
        git(["checkout", "-b", "fake-delivery"], tmp)
        (tmp / "docs" / "continuity" / "PROJECT_MEMORY_SURFACE_INDEX.md").write_text("# tamper\n", encoding="utf-8")
        git(["add", "-A"], tmp)
        git(["commit", "-m", "fake delivery"], tmp)
        git(["checkout", "main"], tmp)
        git(["merge", "--no-ff", "-m", "fake merge", "fake-delivery"], tmp)

        ok, dp, sh, reason = ll.canonical_two_commit_delivery(
            base, sub, git(["rev-parse", "HEAD"], tmp).stdout.strip(),
            canonical_branch="main",
            delivery_branch="remediation/workforce-fix-02-handoff-archive",
            cwd=tmp,
        )
        self.assertFalse(ok, f"fake merge should be rejected: {reason}")

    def test_05_archive_contradiction_detected(self):
        """A deliberately contradictory effective gate in CURRENT_HANDOFF.md must
        be rejected by the archive-mode continuity validator.
        """
        tmp = make_bare_repo()
        base = copy_project_skeleton(tmp, source_repo=REPO)
        git(["checkout", "-b", "remediation/workforce-fix-02-handoff-archive"], tmp)
        setup_fixture_state(tmp, described=base,
                            pre_gate="WORKFORCE-FIX-02",
                            post_gate="WORKFORCE-RETEST-02")
        update_handoff_git_state(
            tmp, base,
            "remediation/workforce-fix-02-handoff-archive",
            "WORKFORCE-FIX-02",
            "WORKFORCE-RETEST-02",
        )
        synchronize_project_memory(tmp, base)
        git(["add", "-A"], tmp)
        git(["commit", "-m", "state"], tmp)

        zip_path, extract = generate_and_extract(tmp, self.scratch, emergency=True)
        # Tamper with the extracted handoff.
        handoff = extract / "docs" / "continuity" / "CURRENT_HANDOFF.md"
        text = handoff.read_text(encoding="utf-8")
        text = re.sub(r"^Effective gate: `.*`$", "Effective gate: `FAKE-GATE`", text, flags=re.MULTILINE)
        handoff.write_text(text, encoding="utf-8")

        code, out, err = validate_archive(extract)
        self.assertNotEqual(code, 0, "archive validator should catch contradiction")
        self.assertIn("effective gate", (out + err).lower())

    def test_06_later_main_history_excluded(self):
        """A later commit on main must not alter the canonical delivery commit count."""
        sys.path.insert(0, str(REPO / "tools" / "audit"))
        import lifecycle_legality as ll

        tmp = make_bare_repo()
        base = copy_project_skeleton(tmp, source_repo=REPO)
        git(["checkout", "-b", "remediation/workforce-fix-02-handoff-archive"], tmp)

        # Substantive commit.
        setup_fixture_state(tmp, described=base,
                            pre_gate="WORKFORCE-FIX-02",
                            post_gate="WORKFORCE-RETEST-02")
        git(["add", "-A"], tmp)
        git(["commit", "-m", "FIX-02 substantive"], tmp)
        sub = git(["rev-parse", "HEAD"], tmp).stdout.strip()

        # Metadata-only second commit.
        setup_fixture_state(tmp, described=sub,
                            pre_gate="WORKFORCE-FIX-02",
                            post_gate="WORKFORCE-RETEST-02")
        update_handoff_git_state(
            tmp, sub,
            "remediation/workforce-fix-02-handoff-archive",
            "WORKFORCE-FIX-02",
            "WORKFORCE-RETEST-02",
        )
        synchronize_project_memory(tmp, sub)
        git(["add", "-A"], tmp)
        git(["commit", "-m", "FIX-02 metadata"], tmp)

        git(["checkout", "main"], tmp)
        git(["merge", "--no-ff", "-m", "Merge FIX-02", "remediation/workforce-fix-02-handoff-archive"], tmp)

        # Add a later metadata-only commit on main.
        pmi = tmp / "docs" / "continuity" / "PROJECT_MEMORY_SURFACE_INDEX.md"
        pmi.write_text(pmi.read_text(encoding="utf-8") + "\n<!-- post-merge metadata touch -->\n", encoding="utf-8")
        git(["add", "-A"], tmp)
        git(["commit", "-m", "post-merge metadata"], tmp)
        live = git(["rev-parse", "HEAD"], tmp).stdout.strip()

        ok, dp, sh, reason = ll.canonical_two_commit_delivery(
            base, sub, live,
            canonical_branch="main",
            delivery_branch="remediation/workforce-fix-02-handoff-archive",
            cwd=tmp,
        )
        self.assertTrue(ok, f"later history should not break delivery proof: {reason}")

    def test_07_generator_no_tracked_mutation(self):
        """generate_handoff.py must not modify tracked files in the repository."""
        # Use a disposable clone because generating from the real repo may be dirty.
        tmp = Path(tempfile.mkdtemp(prefix="anox_fix02_notracked_"))
        git(["clone", "--quiet", str(REPO), str(tmp)])
        git(["checkout", "-B", "main", "8385f4019184be9b568f65ec4748194595ef339c"], tmp)
        shutil.copy2(REPO / "tools" / "continuity" / "generate_handoff.py",
                     tmp / "tools" / "continuity" / "generate_handoff.py")
        shutil.copy2(REPO / "docs" / "continuity" / "CURRENT_HANDOFF.md",
                     tmp / "docs" / "continuity" / "CURRENT_HANDOFF.md")
        git(["add", "-A"], tmp)
        git(["commit", "-m", "overlay"], tmp)

        before = {p.relative_to(tmp): sha256_bytes(p.read_bytes()) for p in tmp.rglob("*") if p.is_file()}
        out_dir = tmp / "out"
        out_dir.mkdir()
        try:
            generate_and_extract(tmp, out_dir, emergency=True)
        finally:
            pass
        after = {p.relative_to(tmp): sha256_bytes(p.read_bytes()) for p in tmp.rglob("*") if p.is_file()}

        changed = [str(p) for p in before if before[p] != after.get(p, None)]
        # Only the generated artifact directory should be new (it is not tracked).
        tracked_changed = [p for p in changed if not str(p).startswith("out/") and str(p) != "artifacts/handoff/"]
        self.assertEqual(tracked_changed, [], f"tracked files changed: {tracked_changed}")
        shutil.rmtree(tmp)

    def test_08_001_005_regression_guards(self):
        """Findings 001 and 005 must still be Ready For Retest and not closed."""
        findings = load_jsonl("docs/workforce/registries/findings.jsonl")
        by_id = {f["finding_id"]: f for f in findings}
        for fid in ("ANOX-WORKFORCE-AUDIT-001", "ANOX-WORKFORCE-AUDIT-005"):
            f = by_id.get(fid)
            self.assertIsNotNone(f, f"{fid} missing")
            self.assertEqual(f.get("status"), "Ready For Retest")
            self.assertIsNone(f.get("closure_evidence"))
            self.assertTrue(any("WORKFORCE-FIX-01" in r for r in f.get("remediation_refs", [])),
                            f"{fid} should still reference WORKFORCE-FIX-01 evidence")

        target = by_id.get("ANOX-WORKFORCE-AUDIT-002")
        self.assertIsNotNone(target)
        self.assertEqual(target.get("status"), "Ready For Retest")
        self.assertTrue(any("WORKFORCE-FIX-02" in r for r in target.get("remediation_refs", [])),
                        "002 should reference WORKFORCE-FIX-02")

    def test_09_no_product_scope_leak(self):
        """The working-tree diff must not contain product/backend/SQL/CI/secret paths."""
        result = subprocess.run(["git", "diff", "--name-only"], cwd=REPO, capture_output=True, text=True)
        changed = result.stdout.splitlines()
        forbidden = (
            r"^android/",
            r"^crypto/",
            r"^backend/",
            r"^supabase/",
            r"\.sql$",
            r"\.github/workflows/",
            r"\.env",
            r"\.jks$",
            r"\.keystore$",
        )
        bad = [p for p in changed if any(re.search(pat, p) for pat in forbidden)]
        self.assertEqual(bad, [], f"product/backend/SQL/CI/secret paths changed: {bad}")


class LifecycleAwareValidatorTests(unittest.TestCase):
    """Adversarial tests for the lifecycle-aware WORKFORCE-FIX-02 validator."""

    @classmethod
    def setUpClass(cls):
        cls.scratch = Path(tempfile.mkdtemp(prefix="anox_fix02_lifecycle_"))
        cls.base_clone = cls.scratch / "base_clone"
        git(["clone", "--quiet", str(REPO), str(cls.base_clone)])
        # Supporting validators resolve refs like `main` from local branches,
        # but a fresh clone only creates the active branch.
        git(["branch", "main", "origin/main"], cls.base_clone, check=False)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.scratch, ignore_errors=True)

    def setUp(self):
        self.clone = self.scratch / f"clone_{self.id().split('.')[-1]}"
        if self.clone.exists():
            shutil.rmtree(self.clone)
        shutil.copytree(self.base_clone, self.clone)

    def tearDown(self):
        shutil.rmtree(self.clone, ignore_errors=True)

    def _run_validator(self, clone, expect_ok=True):
        env = os.environ.copy()
        env["ANOX_REPO_ROOT"] = str(clone)
        r = subprocess.run([sys.executable, str(FIX02_VALIDATOR)], cwd=clone, env=env,
                           capture_output=True, text=True)
        if expect_ok:
            self.assertEqual(r.returncode, 0, f"expected PASS:\n{r.stdout}\n{r.stderr}")
        else:
            self.assertNotEqual(r.returncode, 0, f"expected FAIL but passed:\n{r.stdout}")
        return r

    def _load_json(self, rel):
        return json.loads((self.clone / rel).read_text(encoding="utf-8"))

    def _write_json(self, rel, data):
        (self.clone / rel).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_jsonl(self, rel):
        p = self.clone / rel
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

    def _write_jsonl(self, rel, rows):
        (self.clone / rel).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    def _current_head(self):
        return git(["rev-parse", "HEAD"], self.clone).stdout.strip()

    def test_10_harness_fix_state_pass(self):
        """Legal progression: CURRENT_STATE may advance to WORKFORCE-TEST-HARNESS-FIX-01."""
        head = self._current_head()
        # Add the harness fix task record that the metadata commit will also add.
        tasks_path = self.clone / "docs" / "workforce" / "registries" / "tasks.jsonl"
        tasks = self._load_jsonl("docs/workforce/registries/tasks.jsonl")
        tasks.append({
            "task_id": "ANOX-TASK-WORKFORCE-TEST-HARNESS-FIX-01",
            "title": "WORKFORCE-TEST-HARNESS-FIX-01 — Workforce/Handoff test fixture repair",
            "role_id": "ROLE-009",
            "start_sha": "81e091f3346a7c8653c100a334a1dbfe2c54d464",
            "branch": "remediation/workforce-test-harness-fix-01",
            "allowed_paths": ["tools/audit/test_workforce_fix02.py", "tools/continuity/test_handoff_and_validator.py"],
            "forbidden_paths": ["android/", "crypto/rust/", "backend/"],
            "scope": "Test fixture repair only.",
            "non_goals": ["product code"],
            "security_class": "S2",
            "data_egress": "D2",
            "priority": "P1",
            "required_evidence": "E3",
            "reviewer_role": "ROLE-002",
            "remote_permission": "NONE",
            "stop_conditions": ["validate_workforce_fix02 PASS"],
            "authority_refs": ["docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md"],
            "created_at": "2026-09-08",
            "status": "Closed",
        })
        self._write_jsonl("docs/workforce/registries/tasks.jsonl", tasks)

        # Append a sealed event for the harness fix.
        ledger = self._load_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
        ledger.append({
            "event_id": "ANOX-EVENT-0041",
            "date": "2026-09-08",
            "type": "remediation",
            "task": "WORKFORCE-TEST-HARNESS-FIX-01",
            "summary": "Harness fix.",
            "status": "remediated",
            "start_head": "81e091f3346a7c8653c100a334a1dbfe2c54d464",
            "end_head": head,
            "gate_after": "WORKFORCE-HARNESS-RECHECK-01",
            "findings": ["ANOX-WORKFORCE-AUDIT-001:ready_for_retest", "ANOX-WORKFORCE-AUDIT-002:ready_for_retest", "ANOX-WORKFORCE-AUDIT-005:ready_for_retest"],
            "tests": {},
            "refs": [f"git:{head}"],
            "evidence": [],
        })
        self._write_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl", ledger)

        state = self._load_json("docs/continuity/CURRENT_STATE.json")
        state["described_head"] = head
        state["delivery_branch"] = "remediation/workforce-test-harness-fix-01"
        state["pre_merge_gate"] = "WORKFORCE-TEST-HARNESS-FIX-01"
        state["post_merge_gate"] = "WORKFORCE-HARNESS-RECHECK-01"
        state["current_task"] = "ANOX-TASK-WORKFORCE-TEST-HARNESS-FIX-01"
        state["current_gate"] = "WORKFORCE-TEST-HARNESS-FIX-01"
        state["latest_material_event_id"] = "ANOX-EVENT-0041"
        state["latest_human_history_event_id"] = "ANOX-EVENT-0041"
        state["latest_agent_history_event_id"] = "ANOX-EVENT-0041"
        self._write_json("docs/continuity/CURRENT_STATE.json", state)

        self._run_validator(self.clone, expect_ok=True)

    def test_11_harness_recheck_future_state_pass(self):
        """Legal later progression to the harness recheck candidate."""
        head = self._current_head()
        tasks = self._load_jsonl("docs/workforce/registries/tasks.jsonl")
        for t in tasks:
            if t.get("task_id") == "ANOX-TASK-HARNESSRECHECK01":
                t["branch"] = "audit/workforce-harness-recheck-01"
                t["status"] = "Candidate"
                break
        else:
            tasks.append({
                "task_id": "ANOX-TASK-HARNESSRECHECK01",
                "title": "WORKFORCE-HARNESS-RECHECK-01 — INDEPENDENT TARGETED HARNESS RECHECK",
                "role_id": "ROLE-009",
                "start_sha": "NOT YET BOUND",
                "branch": "audit/workforce-harness-recheck-01",
                "allowed_paths": [],
                "forbidden_paths": ["android/"],
                "scope": "Recheck.",
                "non_goals": ["product code"],
                "security_class": "S2",
                "data_egress": "D2",
                "priority": "P1",
                "required_evidence": "E3",
                "reviewer_role": "ROLE-002",
                "remote_permission": "NONE",
                "stop_conditions": [],
                "authority_refs": [],
                "created_at": "2026-09-08",
                "status": "Candidate",
            })
        self._write_jsonl("docs/workforce/registries/tasks.jsonl", tasks)

        ledger = self._load_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
        ledger.append({
            "event_id": "ANOX-EVENT-0042",
            "date": "2026-09-09",
            "type": "remediation",
            "task": "WORKFORCE-HARNESS-RECHECK-01",
            "summary": "Harness recheck candidate.",
            "status": "candidate",
            "start_head": "NOT YET BOUND",
            "end_head": head,
            "gate_after": "AUDIT-SECURITY-ARCHITECTURE",
            "findings": ["ANOX-WORKFORCE-AUDIT-001:ready_for_retest", "ANOX-WORKFORCE-AUDIT-002:ready_for_retest", "ANOX-WORKFORCE-AUDIT-005:ready_for_retest"],
            "tests": {},
            "refs": [f"git:{head}"],
            "evidence": [],
        })
        self._write_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl", ledger)

        state = self._load_json("docs/continuity/CURRENT_STATE.json")
        state["described_head"] = head
        state["delivery_branch"] = "audit/workforce-harness-recheck-01"
        state["pre_merge_gate"] = "WORKFORCE-HARNESS-RECHECK-01"
        state["post_merge_gate"] = "AUDIT-SECURITY-ARCHITECTURE"
        state["current_task"] = "ANOX-TASK-HARNESSRECHECK01"
        state["current_gate"] = "WORKFORCE-HARNESS-RECHECK-01"
        state["latest_material_event_id"] = "ANOX-EVENT-0042"
        state["latest_human_history_event_id"] = "ANOX-EVENT-0042"
        state["latest_agent_history_event_id"] = "ANOX-EVENT-0042"
        self._write_json("docs/continuity/CURRENT_STATE.json", state)

        self._run_validator(self.clone, expect_ok=True)

    def test_12_illegal_finding_002_closure_fail(self):
        """Finding 002 silently Closed must be rejected."""
        findings = self._load_jsonl("docs/workforce/registries/findings.jsonl")
        for f in findings:
            if f.get("finding_id") == "ANOX-WORKFORCE-AUDIT-002":
                f["status"] = "Closed"
                f["closure_evidence"] = ["git:0000000000000000000000000000000000000000", "RETEST-02"]
                break
        self._write_jsonl("docs/workforce/registries/findings.jsonl", findings)
        self._run_validator(self.clone, expect_ok=False)

    def test_13_finding_002_disappearance_fail(self):
        """Removing finding 002 must be rejected."""
        findings = self._load_jsonl("docs/workforce/registries/findings.jsonl")
        findings = [f for f in findings if f.get("finding_id") != "ANOX-WORKFORCE-AUDIT-002"]
        self._write_jsonl("docs/workforce/registries/findings.jsonl", findings)
        self._run_validator(self.clone, expect_ok=False)

    def test_14_retest01_history_rewrite_fail(self):
        """Changing RETEST-01 result/verdicts must be rejected."""
        runs = self._load_jsonl("docs/workforce/registries/runs.jsonl")
        for r in runs:
            if r.get("run_id") == "ANOX-RUN-WORKFORCERETEST01":
                r["result"] = "PASS"
                verdicts = r.get("per_finding_verdicts") or {}
                verdicts["ANOX-WORKFORCE-AUDIT-002"] = "PASS — REMEDIATED"
                r["per_finding_verdicts"] = verdicts
                break
        self._write_jsonl("docs/workforce/registries/runs.jsonl", runs)
        self._run_validator(self.clone, expect_ok=False)

    def test_15_product_premature_unlock_fail(self):
        """Product leaving BLOCKED_PENDING_FINAL_AUDIT must be rejected."""
        ws = self._load_json("docs/workforce/WORKFORCE_STATE.json")
        ws["product_development_state"] = "READY"
        ws["final_pre_product_audit"]["product_development_state"] = "READY"
        self._write_json("docs/workforce/WORKFORCE_STATE.json", ws)
        self._run_validator(self.clone, expect_ok=False)

    def test_16_broken_task_reference_fail(self):
        """A CURRENT_STATE pointing to a nonexistent task must be rejected."""
        head = self._current_head()
        ledger = self._load_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl")
        ledger.append({
            "event_id": "ANOX-EVENT-0042",
            "date": "2026-09-09",
            "type": "remediation",
            "task": "FAKE-TASK",
            "summary": "Fake",
            "status": "remediated",
            "start_head": head,
            "end_head": head,
            "gate_after": "FAKE-NEXT",
            "findings": [],
            "tests": {},
            "refs": [f"git:{head}"],
            "evidence": [],
        })
        self._write_jsonl("docs/continuity/PROJECT_HISTORY_LEDGER.jsonl", ledger)
        state = self._load_json("docs/continuity/CURRENT_STATE.json")
        state["described_head"] = head
        state["pre_merge_gate"] = "FAKE-TASK"
        state["post_merge_gate"] = "FAKE-NEXT"
        state["delivery_branch"] = "remediation/fake"
        state["current_task"] = "ANOX-TASK-NONEXISTENT"
        state["latest_material_event_id"] = "ANOX-EVENT-0042"
        state["latest_human_history_event_id"] = "ANOX-EVENT-0042"
        state["latest_agent_history_event_id"] = "ANOX-EVENT-0042"
        self._write_json("docs/continuity/CURRENT_STATE.json", state)
        self._run_validator(self.clone, expect_ok=False)

    def test_17_historical_delivery_tampering_fail(self):
        """A described_head that is not a sealed ancestor must be rejected."""
        state = self._load_json("docs/continuity/CURRENT_STATE.json")
        state["described_head"] = "0000000000000000000000000000000000000000"
        self._write_json("docs/continuity/CURRENT_STATE.json", state)
        self._run_validator(self.clone, expect_ok=False)


if __name__ == "__main__":
    unittest.main()
