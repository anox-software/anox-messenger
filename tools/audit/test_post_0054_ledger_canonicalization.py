#!/usr/bin/env python3
"""Adversarial fail-closed tests for the post-ANOX-EVENT-0054 ledger
canonicalization authorized by ANOX-DECISION-POST-0054-LEDGER-CANONICALIZATION-001
(ONE_TIME_CHANGE_SPECIFIC).

The canonical Project History Ledger may carry exactly the pinned chain
ANOX-EVENT-0060..0066 after ANOX-EVENT-0054 (PR #35/#36/#38/#39/#40/#41 merges
plus this correction's sealed delivery checkpoint).  These tests exercise the
tail extension in both ledger validators and the shared-file ratification pin
in the S0 contract-freeze validator.  Canonical evidence is never mutated.

Run:  python3 -m unittest tools.audit.test_post_0054_ledger_canonicalization
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_AUDIT = REPO_ROOT / "tools" / "audit"

S0EP_VALIDATOR = TOOLS_AUDIT / "validate_s0_evidence_preservation.py"
SAEP_VALIDATOR = TOOLS_AUDIT / "validate_security_audit_evidence_preservation.py"
CF_VALIDATOR = TOOLS_AUDIT / "validate_s0_contract_freeze.py"

LEDGER = "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl"
STATE = "docs/continuity/CURRENT_STATE.json"
DECISIONS = "docs/workforce/registries/decisions.jsonl"
SAEP = "tools/audit/validate_security_audit_evidence_preservation.py"
CANON_REPORT = "docs/reports/security/decisions/POST-0054-LEDGER-CANONICALIZATION-001.md"
CANON_DECISION_ID = "ANOX-DECISION-POST-0054-LEDGER-CANONICALIZATION-001"

# Independent mirror of the pinned chain (fields the validators must enforce).
M1 = "ea838fa5803f5088a1ce39d6ac026f8295a281a6"   # PR #35 merge
M2 = "29a6643189242a47c4a79c38acd04c1eca748787"   # PR #36 merge
M3 = "2dc6b7453ef292c30f32c02e0eb213e1ef5496cb"   # PR #38 merge
M4 = "cb9aee039bd2816c38c11a5e9084be56aa8cde15"   # PR #39 merge
M5 = "02179ecd34fde81a0cc8866a09653cab8ff40f38"   # PR #40 merge
M6 = "270cdb92762965eea3236177710c88c259d4b33f"   # PR #41 merge
P5 = "0f932520393feee6d479cc099f179f5766323125"  # parent before PR #35
CHK = "f" * 40  # fixture placeholder for the delivery checkpoint end_head

CHAIN_SPECS = (
    ("ANOX-EVENT-0060", "canonical_merge", "hotfix/ci-android-sdk-packages-001", P5, M1),
    ("ANOX-EVENT-0061", "canonical_merge", "ANOX-TASK-SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001", M1, M2),
    ("ANOX-EVENT-0062", "canonical_merge", "ANOX-TASK-S1-CLEAN-REBUILD-CONTINUITY-TRANSITION-001", M2, M3),
    ("ANOX-EVENT-0063", "canonical_merge", "ANOX-TASK-S1-POST-MERGE-CONTINUITY-SYNC-001", M3, M4),
    ("ANOX-EVENT-0064", "canonical_merge", "ANOX-TASK-S2-BOOTSTRAP-LIFETIME-GOVERNANCE-AND-SCOPE-FREEZE-001", M4, M5),
    ("ANOX-EVENT-0065", "canonical_merge", "ANOX-TASK-S2-C01-PREAUTHORIZATION-001", M5, M6),
)
CHECKPOINT_SPEC = ("ANOX-EVENT-0066", "post_0054_ledger_canonicalization",
                   "ANOX-TASK-POST-0054-LEDGER-CANONICALIZATION-001", M6)


def _load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def _write_jsonl(path, records):
    Path(path).write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _chain_events():
    events = []
    for eid, etype, task, start, merge in CHAIN_SPECS:
        events.append({
            "event_id": eid, "date": "2026-09-16", "type": etype, "task": task,
            "summary": f"{eid} canonical merge {merge[:12]}", "status": "merged",
            "start_head": start, "end_head": merge, "merge_head": merge,
            "gate_after": "fixture gate", "findings": [], "tests": {},
            "refs": [f"git:{merge[:8]}..."], "evidence": ["canonical-merge"],
        })
    eid, etype, task, start = CHECKPOINT_SPEC
    events.append({
        "event_id": eid, "date": "2026-09-30", "type": etype, "task": task,
        "summary": f"{eid} post-0054 ledger canonicalization checkpoint", "status": "READY_FOR_REMOTE",
        "start_head": start, "end_head": CHK, "merge_head": None,
        "gate_after": "fixture gate", "findings": [], "tests": {},
        "refs": [f"git:{CHK}", CANON_REPORT], "evidence": [],
    })
    return events


def _run(validator, env_key, root):
    env = dict(os.environ)
    env[env_key] = str(root)
    return subprocess.run([sys.executable, str(validator)],
                          cwd=root, env=env, capture_output=True, text=True)


def _trim_ledger(root, keep_id="ANOX-EVENT-0054"):
    recs = _load_jsonl(root / LEDGER)
    while recs and recs[-1].get("event_id") != keep_id:
        recs.pop()
    return recs


def _sync_latest(root, event_id):
    p = root / STATE
    state = json.loads(p.read_text(encoding="utf-8"))
    state["latest_material_event_id"] = event_id
    p.write_text(json.dumps(state, indent=1), encoding="utf-8")


class _Base(unittest.TestCase):
    VALIDATOR = None
    ENV_KEY = None
    FIXTURE = ()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in self.FIXTURE:
            src = REPO_ROOT / rel
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    def tearDown(self):
        self.tmp.cleanup()

    def run_validator(self):
        return _run(self.VALIDATOR, self.ENV_KEY, self.root)

    def build_chain_fixture(self):
        """Trim the fixture ledger to ANOX-EVENT-0054 and append the pinned chain."""
        recs = _trim_ledger(self.root)
        recs.extend(_chain_events())
        _write_jsonl(self.root / LEDGER, recs)
        _sync_latest(self.root, "ANOX-EVENT-0066")

    def mutate_event(self, eid, fn):
        recs = _load_jsonl(self.root / LEDGER)
        for r in recs:
            if r.get("event_id") == eid:
                fn(r)
        _write_jsonl(self.root / LEDGER, recs)


class Post0054ChainS0PreservationTests(_Base):
    """tools/audit/validate_s0_evidence_preservation.py must accept exactly the
    pinned post-0054 chain after ANOX-EVENT-0054 and fail closed otherwise."""

    VALIDATOR = S0EP_VALIDATOR
    ENV_KEY = "S0_EVIDENCE_PRESERVATION_REPO"
    FIXTURE = (
        "docs/reports/security/remediation/REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md",
        "docs/reports/security/retests/INDEPENDENT-ARCHITECTURE-RETEST-S0-001.md",
        "docs/reports/security/retests/TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001.md",
        "docs/reports/security/remediation/SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001.md",
        "docs/reports/security/decisions/S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001.md",
        "docs/reports/security/decisions/S0-F01-FILE-OWNERSHIP-RATIFICATION-001.md",
        CANON_REPORT,
        "docs/security/audit-evidence/audit_registry.jsonl",
        "docs/security/audit-evidence/audit_traceability.jsonl",
        "docs/security/audit-evidence/evidence_hashes.json",
        LEDGER, STATE, DECISIONS,
        "docs/workforce/registries/findings.jsonl",
        "docs/authority/contracts/S0_CONTRACT_FREEZE_MANIFEST.json",
        "tools/audit/test_s0_contract_freeze.py",
        "tools/audit/test_security_audit_evidence_preservation.py",
        "tools/audit/test_s0_evidence_preservation.py",
        "tools/audit/test_post_0054_ledger_canonicalization.py",
    )

    def setUp(self):
        super().setUp()
        self.build_chain_fixture()

    def assert_fails(self, needle=None):
        r = self.run_validator()
        self.assertNotEqual(r.returncode, 0, f"validator must FAIL; stdout:\n{r.stdout}\n{r.stderr}")
        self.assertIn("FAIL", r.stdout)
        if needle:
            self.assertIn(needle, r.stdout, f"missing expected failure detail {needle!r}:\n{r.stdout}")
        return r

    def test_00_control_chain_accepted(self):
        r = self.run_validator()
        self.assertEqual(r.returncode, 0, f"validator must PASS; stdout:\n{r.stdout}\n{r.stderr}")
        self.assertIn("pinned post-0054 canonicalization chain", r.stdout)

    def test_01_historical_0054_tail_still_accepted(self):
        recs = _trim_ledger(self.root)
        _write_jsonl(self.root / LEDGER, recs)
        _sync_latest(self.root, "ANOX-EVENT-0054")
        r = self.run_validator()
        self.assertEqual(r.returncode, 0, f"0054-tail state must stay PASS; stdout:\n{r.stdout}")

    def test_02_chain_event_dropped(self):
        recs = [r for r in _load_jsonl(self.root / LEDGER) if r.get("event_id") != "ANOX-EVENT-0063"]
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_fails()

    def test_03_chain_reordered(self):
        recs = _load_jsonl(self.root / LEDGER)
        i = [k for k, r in enumerate(recs) if r.get("event_id") == "ANOX-EVENT-0061"][0]
        j = [k for k, r in enumerate(recs) if r.get("event_id") == "ANOX-EVENT-0062"][0]
        recs[i], recs[j] = recs[j], recs[i]
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_fails()

    def test_04_extra_event_appended(self):
        recs = _load_jsonl(self.root / LEDGER)
        extra = dict(_chain_events()[-1])
        extra["event_id"] = "ANOX-EVENT-0067"
        recs.append(extra)
        _write_jsonl(self.root / LEDGER, recs)
        _sync_latest(self.root, "ANOX-EVENT-0067")
        self.assert_fails()

    def test_05_duplicate_chain_event(self):
        recs = _load_jsonl(self.root / LEDGER)
        i = [k for k, r in enumerate(recs) if r.get("event_id") == "ANOX-EVENT-0060"][0]
        recs.insert(i + 1, dict(recs[i]))
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_fails()

    def test_06_wrong_task_on_merge_event(self):
        self.mutate_event("ANOX-EVENT-0064", lambda r: r.__setitem__("task", "ANOX-TASK-SOMETHING-ELSE-001"))
        self.assert_fails()

    def test_07_wrong_start_head(self):
        self.mutate_event("ANOX-EVENT-0060", lambda r: r.__setitem__("start_head", "0" * 40))
        self.assert_fails()

    def test_08_wrong_merge_head(self):
        self.mutate_event("ANOX-EVENT-0065", lambda r: r.__setitem__("merge_head", "0" * 40))
        self.assert_fails()

    def test_09_wrong_type(self):
        self.mutate_event("ANOX-EVENT-0061", lambda r: r.__setitem__("type", "gate_transition"))
        self.assert_fails()

    def test_10_reserved_event_id_rejected(self):
        self.mutate_event("ANOX-EVENT-0062", lambda r: r.__setitem__("event_id", "ANOX-EVENT-0058"))
        self.assert_fails()

    def test_11_interposed_event_rejected(self):
        recs = _load_jsonl(self.root / LEDGER)
        i = [k for k, r in enumerate(recs) if r.get("event_id") == "ANOX-EVENT-0060"][0]
        interposed = dict(recs[i])
        interposed["event_id"] = "ANOX-EVENT-0099"
        recs.insert(i, interposed)
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_fails()

    def test_12_altered_predecessor_0054(self):
        self.mutate_event("ANOX-EVENT-0054", lambda r: r.__setitem__("task", "ANOX-TASK-TAMPERED-001"))
        self.assert_fails()

    def test_13_stale_state_pointer(self):
        _sync_latest(self.root, "ANOX-EVENT-0054")
        self.assert_fails("latest_material_event_id")

    def test_14_future_state_pointer(self):
        _sync_latest(self.root, "ANOX-EVENT-0067")
        self.assert_fails("latest_material_event_id")

    def test_15_canon_decision_dropped(self):
        recs = [r for r in _load_jsonl(self.root / DECISIONS)
                if r.get("decision_id") != CANON_DECISION_ID]
        _write_jsonl(self.root / DECISIONS, recs)
        self.assert_fails(CANON_DECISION_ID)

    def test_16_canon_decision_wrong_task(self):
        recs = _load_jsonl(self.root / DECISIONS)
        for r in recs:
            if r.get("decision_id") == CANON_DECISION_ID:
                r["ratified_task"] = "ANOX-TASK-SOMETHING-ELSE-001"
        _write_jsonl(self.root / DECISIONS, recs)
        self.assert_fails("ratified_task")

    def test_17_canon_report_missing(self):
        (self.root / CANON_REPORT).unlink()
        self.assert_fails()

    def test_18_checkpoint_wrong_type(self):
        self.mutate_event("ANOX-EVENT-0066", lambda r: r.__setitem__("type", "canonical_merge"))
        self.assert_fails()

    def test_19_checkpoint_missing_ref(self):
        self.mutate_event("ANOX-EVENT-0066",
                          lambda r: r.__setitem__("refs", [x for x in r["refs"] if not x.endswith(".md")]))
        self.assert_fails()

    def test_20_partial_chain_rejected(self):
        recs = _trim_ledger(self.root)
        recs.extend(_chain_events()[:5])  # stops at 0064 — chain incomplete
        _write_jsonl(self.root / LEDGER, recs)
        _sync_latest(self.root, "ANOX-EVENT-0064")
        self.assert_fails()


class Post0054ChainSharedValidatorTests(_Base):
    """tools/audit/validate_security_audit_evidence_preservation.py must accept
    the pinned post-0054 tail and print the chain-sync line; the era-pinned
    remainder of that validator is covered by its own suite."""

    VALIDATOR = SAEP_VALIDATOR
    ENV_KEY = "SECURITY_AUDIT_PRESERVATION_REPO"
    FIXTURE = (
        "docs/security/audit-evidence/AUDIT_EVIDENCE_INDEX.md",
        "docs/security/audit-evidence/audit_registry.jsonl",
        "docs/security/audit-evidence/audit_traceability.jsonl",
        "docs/security/audit-evidence/evidence_hashes.json",
        "docs/security/audit-evidence/reproductions/README.md",
        "docs/reports/security/audits/AUDIT-SECURITY-ARCHITECTURE.md",
        "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-001.md",
        "docs/reports/security/audits/AUDIT-SECURITY-CODEBASE-002.md",
        "docs/reports/security/audits/CODEBASE-SECURITY-CONSENSUS-001.md",
        "docs/reports/security/audits/AUDIT-SECURITY-BUILD-SUPPLYCHAIN-001.md",
        "docs/reports/security/audits/AUDIT-SECURITY-CRYPTO-JNI-001.md",
        "docs/reports/security/audits/AUDIT-SECURITY-AUTH-DPOP-001.md",
        "docs/reports/security/audits/AUDIT-SECURITY-ANDROID-STORAGE-001.md",
        "docs/reports/security/audits/AUDIT-SECURITY-ATTACKCHAIN-001.md",
        "docs/reports/security/consolidation/MASTER-SPECIALIST-CONSOLIDATION-001.md",
        "docs/reports/security/gates/SECURITY-REMEDIATION-COVERAGE-GATE-001.md",
        "docs/reports/security/decisions/HUMAN-PRE-REMEDIATION-DECISIONS-001.md",
        "docs/reports/security/remediation/REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001.md",
        "docs/reports/security/remediation/SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001.md",
        "docs/reports/security/retests/INDEPENDENT-ARCHITECTURE-RETEST-S0-001.md",
        "docs/reports/security/retests/TARGETED-INDEPENDENT-RETEST-S0-CORRECTIONS-001.md",
        "docs/reports/security/decisions/S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001.md",
        CANON_REPORT,
        "docs/workforce/WORKFORCE_STATE.json",
        "docs/workforce/registries/findings.jsonl",
        "docs/workforce/registries/tasks.jsonl",
        DECISIONS,
        "docs/workforce/registries/implementation_readiness.json",
        STATE,
        "docs/continuity/CURRENT_HANDOFF.md",
        "docs/continuity/CURRENT_GIT_STATE.md",
        LEDGER,
        "tools/audit/validate_security_architecture_findings_freeze.py",
        "tools/audit/validate_legacy_retest01_ingest.py",
        "tools/audit/validate_mainarch_fix03.py",
        "tools/audit/validate_mainarch_retest01_ingest.py",
        "tools/audit/validate_mainarch_retest02_ingest.py",
        "tools/audit/validate_mainarch_retest03_ingest.py",
        "tools/audit/validate_workforce_fix01.py",
        "tools/audit/validate_workforce_fix02.py",
        "tools/audit/validate_workforce_retest_closure_ingest.py",
        "tools/audit/validate_workforce_continuity_sync_fix01.py",
        "tools/audit/validate_security_audit_evidence_preservation.py",
        "tools/continuity/validate_continuity.py",
        "tools/workforce/validate_b027a.py",
        "tools/workforce/validate_b027b.py",
        "tools/workforce/validate_b027_integrity.py",
        "tools/security/b017_lite_policy_validator.py",
    )

    def setUp(self):
        super().setUp()
        self.build_chain_fixture()

    def assert_memory_ok(self):
        r = self.run_validator()
        self.assertIn("pinned post-0054 canonicalization chain", r.stdout,
                      f"chain tail must be accepted; stdout:\n{r.stdout}")
        self.assertNotIn("last ledger event must be", r.stdout)

    def assert_memory_fails(self):
        r = self.run_validator()
        self.assertIn("last ledger event must be", r.stdout,
                      f"chain-tail rejection line missing; stdout:\n{r.stdout}")
        return r

    def test_00_chain_tail_accepted(self):
        self.assert_memory_ok()

    def test_01_chain_event_dropped(self):
        recs = [r for r in _load_jsonl(self.root / LEDGER) if r.get("event_id") != "ANOX-EVENT-0063"]
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_memory_fails()

    def test_02_chain_reordered(self):
        recs = _load_jsonl(self.root / LEDGER)
        i = [k for k, r in enumerate(recs) if r.get("event_id") == "ANOX-EVENT-0061"][0]
        j = [k for k, r in enumerate(recs) if r.get("event_id") == "ANOX-EVENT-0062"][0]
        recs[i], recs[j] = recs[j], recs[i]
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_memory_fails()

    def test_03_future_event_appended(self):
        recs = _load_jsonl(self.root / LEDGER)
        extra = dict(_chain_events()[-1])
        extra["event_id"] = "ANOX-EVENT-0067"
        recs.append(extra)
        _write_jsonl(self.root / LEDGER, recs)
        _sync_latest(self.root, "ANOX-EVENT-0067")
        self.assert_memory_fails()

    def test_04_duplicate_chain_event(self):
        recs = _load_jsonl(self.root / LEDGER)
        i = [k for k, r in enumerate(recs) if r.get("event_id") == "ANOX-EVENT-0060"][0]
        recs.insert(i + 1, dict(recs[i]))
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_memory_fails()

    def test_05_wrong_task_on_merge_event(self):
        self.mutate_event("ANOX-EVENT-0064", lambda r: r.__setitem__("task", "ANOX-TASK-SOMETHING-ELSE-001"))
        self.assert_memory_fails()

    def test_06_wrong_start_head(self):
        self.mutate_event("ANOX-EVENT-0060", lambda r: r.__setitem__("start_head", "0" * 40))
        self.assert_memory_fails()

    def test_07_wrong_merge_head(self):
        self.mutate_event("ANOX-EVENT-0065", lambda r: r.__setitem__("merge_head", "0" * 40))
        self.assert_memory_fails()

    def test_08_wrong_status(self):
        self.mutate_event("ANOX-EVENT-0063", lambda r: r.__setitem__("status", "READY_FOR_REMOTE"))
        self.assert_memory_fails()

    def test_09_reserved_event_id_rejected(self):
        self.mutate_event("ANOX-EVENT-0062", lambda r: r.__setitem__("event_id", "ANOX-EVENT-0057"))
        self.assert_memory_fails()

    def test_10_interposed_event_rejected(self):
        recs = _load_jsonl(self.root / LEDGER)
        i = [k for k, r in enumerate(recs) if r.get("event_id") == "ANOX-EVENT-0060"][0]
        interposed = dict(recs[i])
        interposed["event_id"] = "ANOX-EVENT-0099"
        recs.insert(i, interposed)
        _write_jsonl(self.root / LEDGER, recs)
        self.assert_memory_fails()

    def test_11_altered_predecessor_0054(self):
        self.mutate_event("ANOX-EVENT-0054", lambda r: r.__setitem__("task", "ANOX-TASK-TAMPERED-001"))
        self.assert_memory_fails()

    def test_12_stale_state_pointer(self):
        _sync_latest(self.root, "ANOX-EVENT-0054")
        r = self.run_validator()
        self.assertIn("latest_material_event_id", r.stdout)

    def test_13_0054_tail_still_accepted(self):
        recs = _trim_ledger(self.root)
        _write_jsonl(self.root / LEDGER, recs)
        _sync_latest(self.root, "ANOX-EVENT-0054")
        r = self.run_validator()
        self.assertIn("ANOX-EVENT-0054", r.stdout)
        self.assertNotIn("last ledger event must be", r.stdout)

    def test_14_0053_tail_still_accepted(self):
        recs = _trim_ledger(self.root, keep_id="ANOX-EVENT-0053")
        _write_jsonl(self.root / LEDGER, recs)
        _sync_latest(self.root, "ANOX-EVENT-0053")
        r = self.run_validator()
        self.assertIn("ANOX-EVENT-0053", r.stdout)
        self.assertNotIn("last ledger event must be", r.stdout)

    def test_15_checkpoint_missing_ref(self):
        self.mutate_event("ANOX-EVENT-0066",
                          lambda r: r.__setitem__("refs", [x for x in r["refs"] if not x.endswith(".md")]))
        self.assert_memory_fails()

    def test_16_checkpoint_wrong_type(self):
        self.mutate_event("ANOX-EVENT-0066", lambda r: r.__setitem__("type", "canonical_merge"))
        self.assert_memory_fails()

    def test_17_checkpoint_wrong_task(self):
        self.mutate_event("ANOX-EVENT-0066", lambda r: r.__setitem__("task", "ANOX-TASK-SOMETHING-ELSE-001"))
        self.assert_memory_fails()


class Post0054ContractFreezeRatificationTests(_Base):
    """tools/audit/validate_s0_contract_freeze.py must accept the ratified
    canonicalization content of the protected shared file only while the exact
    Human ratification record stands, and fail closed otherwise."""

    VALIDATOR = CF_VALIDATOR
    ENV_KEY = "S0_CONTRACT_FREEZE_REPO"
    FIXTURE = (
        "docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md",
        "docs/authority/contracts/S0_CONTRACT_FREEZE_MANIFEST.json",
        "docs/authority/AUTHORITY_INDEX.md",
        "docs/authority/B_FREEZE_REGISTRY.md",
        "docs/current/DATABASE_ARCHITECTURE.md",
        "docs/current/BACKEND_ARCHITECTURE.md",
        "docs/workforce/registries/findings.jsonl",
        "docs/workforce/registries/implementation_readiness.json",
        DECISIONS,
        "docs/reports/security/decisions/S0-F01-FILE-OWNERSHIP-RATIFICATION-001.md",
        "docs/reports/security/decisions/S0-PRESERVATION-SHARED-VALIDATOR-RATIFICATION-001.md",
        CANON_REPORT,
        SAEP,
    )

    def edit_decision(self, fn):
        recs = _load_jsonl(self.root / DECISIONS)
        for r in recs:
            if r.get("decision_id") == CANON_DECISION_ID:
                fn(r)
        _write_jsonl(self.root / DECISIONS, recs)

    def assert_fails(self, needle=None):
        r = self.run_validator()
        self.assertNotEqual(r.returncode, 0, f"validator must FAIL; stdout:\n{r.stdout}\n{r.stderr}")
        if needle:
            self.assertIn(needle, r.stdout, f"missing expected failure detail {needle!r}:\n{r.stdout}")
        return r

    def test_00_control_ratified_content_accepted(self):
        r = self.run_validator()
        self.assertEqual(r.returncode, 0, f"validator must PASS; stdout:\n{r.stdout}\n{r.stderr}")

    def test_01_decision_dropped_fails(self):
        recs = [r for r in _load_jsonl(self.root / DECISIONS)
                if r.get("decision_id") != CANON_DECISION_ID]
        _write_jsonl(self.root / DECISIONS, recs)
        self.assert_fails("no valid Human ratification")

    def test_02_wrong_ratified_task(self):
        self.edit_decision(lambda r: r.__setitem__("ratified_task", "ANOX-TASK-SOMETHING-ELSE-001"))
        self.assert_fails("ratified_task")

    def test_03_wrong_ratified_files(self):
        self.edit_decision(lambda r: r.__setitem__("ratified_files", ["tools/security/validate_apk_contents.py"]))
        self.assert_fails("ratified_files")

    def test_04_wrong_ratified_digest(self):
        self.edit_decision(lambda r: r.__setitem__(
            "ratified_sha256", {"tools/audit/validate_security_audit_evidence_preservation.py": "de" * 32}))
        self.assert_fails("ratified_sha256")

    def test_05_scope_widened(self):
        self.edit_decision(lambda r: r.__setitem__("scope", "STANDING_PERMISSION"))
        self.assert_fails("ONE_TIME_CHANGE_SPECIFIC")

    def test_06_grants_future_event_numbers(self):
        self.edit_decision(lambda r: r.__setitem__("grants_future_event_numbers", True))
        self.assert_fails("grants_future_event_numbers")

    def test_07_grants_registry_growth(self):
        self.edit_decision(lambda r: r.__setitem__("grants_arbitrary_registry_growth", True))
        self.assert_fails("grants_arbitrary_registry_growth")

    def test_08_not_human_authority(self):
        self.edit_decision(lambda r: r.__setitem__("authority_actor", "Devin CLI"))
        self.assert_fails("Human Product & Security Owner")

    def test_09_report_missing(self):
        (self.root / CANON_REPORT).unlink()
        self.assert_fails("canonical record")

    def test_10_protected_file_arbitrary_change(self):
        p = self.root / SAEP
        p.write_text(p.read_text(encoding="utf-8") + "\n# unauthorized change\n", encoding="utf-8")
        self.assert_fails("unauthorized modification")


if __name__ == "__main__":
    unittest.main()
