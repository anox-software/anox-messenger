#!/usr/bin/env python3
"""Adversarial tests for tools/audit/validate_s1_integration_evidence.py
(REMEDIATION-S1-CANONICAL-INTEGRATION-001 — shared-validator follow-up in its
governance-compliant form).

Exactly one recorded integration event (`ANOX-EVENT-0055`, pinned fields) may
follow the S0 preservation event `ANOX-EVENT-0054`; the registry holds exactly
one additional `SEC-AUDIT-REG-0014` record (14 total); the protected shared
validator must remain at its Human-ratified content; the prepared ratification
proposal must be tamper-evident. Every acceptance condition has a paired
rejection here. Canonical evidence is never mutated by these tests.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "audit" / "validate_s1_integration_evidence.py"

spec = importlib.util.spec_from_file_location("anox_s1_integration_validator", VALIDATOR)
VAL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(VAL)

# Reuse the ratified central suite's fixture list so the verbatim S0 protections
# have their inputs, plus the S1-era surfaces.
_central_tests = importlib.util.spec_from_file_location(
    "anox_central_tests", REPO_ROOT / "tools/audit/test_security_audit_evidence_preservation.py")
_ct = importlib.util.module_from_spec(_central_tests)
_central_tests.loader.exec_module(_ct)
FIXTURE_FILES = list(_ct.FIXTURE_FILES) + [
    "docs/reports/security/remediation/REMEDIATION-S1-CANONICAL-INTEGRATION-001.md",
    "docs/reports/security/retests/INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001.md",
    "docs/security/remediation/S1_PROVENANCE_VERIFIED_NATIVE_RUNTIME.md",
    "docs/security/remediation/S1_TASK_REPORT.md",
    "docs/reports/security/decisions/S1-INTEGRATION-SHARED-VALIDATOR-RATIFICATION-PROPOSAL-001.md",
    "docs/reports/security/decisions/proposals/S1_SHARED_VALIDATOR_EXTENSION.patch",
    "tools/audit/lifecycle_legality.py",
    "tools/audit/validate_s1_integration_evidence.py",
]


def _load_jsonl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def _write_jsonl(p, recs):
    Path(p).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")


class S1IntegrationEvidenceAdversarialTests(unittest.TestCase):
    LEDGER = "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl"
    CS = "docs/continuity/CURRENT_STATE.json"
    REGISTRY = "docs/security/audit-evidence/audit_registry.jsonl"
    CENTRAL = "tools/audit/validate_security_audit_evidence_preservation.py"
    EVENT = "ANOX-EVENT-0055"
    PRIOR = "ANOX-EVENT-0054"
    S1_ID = "REMEDIATION-S1-CANONICAL-INTEGRATION-001"
    S1_TASK = "ANOX-TASK-REMEDIATION-S1-CANONICAL-INTEGRATION-001"
    S1_ORIG_TASK = "ANOX-TASK-REMEDIATION-SESSION-S1-BUILD-PROVENANCE-001"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in FIXTURE_FILES:
            src = REPO_ROOT / rel
            if not src.exists():
                continue
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    def tearDown(self):
        self.tmp.cleanup()

    def run_validator(self):
        env = dict(os.environ)
        env["SECURITY_AUDIT_PRESERVATION_REPO"] = str(self.root)
        return subprocess.run([sys.executable, str(VALIDATOR)], cwd=self.root, env=env,
                              capture_output=True, text=True)

    def assert_fails(self, needle=None):
        r = self.run_validator()
        self.assertNotEqual(r.returncode, 0, f"validator must FAIL; stdout:\n{r.stdout}\n{r.stderr}")
        self.assertIn("FAIL", r.stdout)
        if needle:
            self.assertIn(needle, r.stdout, f"missing expected failure detail {needle!r}:\n{r.stdout}")
        return r

    # -- helpers ------------------------------------------------------------
    def _ledger(self):
        return _load_jsonl(self.root / self.LEDGER)

    def _write(self, recs):
        _write_jsonl(self.root / self.LEDGER, recs)

    def _registry(self):
        return _load_jsonl(self.root / self.REGISTRY)

    def _write_registry(self, recs):
        _write_jsonl(self.root / self.REGISTRY, recs)

    def _state(self):
        return json.loads((self.root / self.CS).read_text(encoding="utf-8"))

    def _write_state(self, st):
        (self.root / self.CS).write_text(json.dumps(st, indent=1), encoding="utf-8")

    def _sync_latest(self, event_id):
        st = self._state(); st["latest_material_event_id"] = event_id; self._write_state(st)

    def _mutate_event(self, **fields):
        recs = self._ledger()
        self.assertEqual(recs[-1].get("event_id"), self.EVENT, "fixture must end with the S1 integration event")
        recs[-1].update(fields)
        self._write(recs)

    def _s1_record(self):
        recs = self._registry()
        return recs, next(r for r in recs if r.get("audit_id") == self.S1_ID)

    # -- control ------------------------------------------------------------
    def test_300_valid_s1_integration_accepted(self):
        r = self.run_validator()
        self.assertEqual(r.returncode, 0, f"recorded S1 integration state must be accepted:\n{r.stdout}\n{r.stderr}")
        self.assertIn(f"Project Memory synced to {self.EVENT}", r.stdout)
        self.assertIn("NONCANONICAL", r.stdout)
        self.assertIn("S0 registry protections executed verbatim", r.stdout)
        self.assertIn("awaiting Human ratification", r.stdout)

    # -- protected shared validator -----------------------------------------
    def test_301_modified_shared_validator_refused(self):
        p = self.root / self.CENTRAL
        p.write_text(p.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
        self.assert_fails("is not the Human-ratified content")

    def test_302_missing_shared_validator_refused(self):
        (self.root / self.CENTRAL).unlink()
        self.assert_fails("protected shared validator missing")

    # -- event chain --------------------------------------------------------
    def test_303_missing_s1_event_while_state_claims_it_rejected(self):
        self._write([r for r in self._ledger() if r.get("event_id") != self.EVENT])
        self.assert_fails("stale")

    def test_304_duplicate_s1_event_rejected(self):
        recs = self._ledger(); recs.append(dict(recs[-1])); self._write(recs)
        self.assert_fails("duplicate event ids")

    def test_305_skipped_event_number_rejected(self):
        self._mutate_event(event_id="ANOX-EVENT-0056"); self._sync_latest("ANOX-EVENT-0056")
        self.assert_fails("S1 integration recorded under wrong event id")

    def test_306_arbitrary_future_event_after_s1_rejected(self):
        recs = self._ledger()
        recs.append(dict(recs[-1], event_id="ANOX-EVENT-0056", task="ANOX-TASK-FUTURE-001", type="something_new"))
        self._write(recs); self._sync_latest("ANOX-EVENT-0056")
        self.assert_fails("last ledger event must be the pinned S1 integration event")

    def test_307_provisional_isolated_0054_as_canonical_rejected(self):
        recs = self._ledger()
        recs.insert(len(recs) - 1, {"event_id": "ANOX-EVENT-0054", "type": "remediation_session_build_provenance",
                                    "task": self.S1_ORIG_TASK, "start_head": "0" * 40, "refs": []})
        self._write(recs)
        self.assert_fails("admits the isolated S1 provisional event")

    def test_308_s1_original_task_under_any_other_id_rejected(self):
        recs = self._ledger()
        recs.append(dict(recs[-1], event_id="ANOX-EVENT-0056", task=self.S1_ORIG_TASK))
        self._write(recs); self._sync_latest("ANOX-EVENT-0056")
        self.assert_fails("admits the isolated S1 provisional event")

    def test_309_altered_task_rejected(self):
        self._mutate_event(task="ANOX-TASK-SOMETHING-ELSE-001")
        self.assert_fails("pinned S1 integration event")

    def test_310_altered_type_rejected(self):
        self._mutate_event(type="audit_evidence_preservation")
        self.assert_fails("pinned S1 integration event")

    def test_311_altered_start_head_rejected(self):
        self._mutate_event(start_head="0" * 40)
        self.assert_fails("pinned S1 integration event")

    def test_312_altered_merged_head_rejected(self):
        self._mutate_event(merged_head="0" * 40)
        self.assert_fails("pinned S1 integration event")

    def test_313_missing_supersedes_marker_rejected(self):
        recs = self._ledger(); recs[-1].pop("supersedes_provisional_event", None); self._write(recs)
        self.assert_fails("pinned S1 integration event")

    def test_314_missing_report_ref_rejected(self):
        recs = self._ledger()
        recs[-1]["refs"] = [x for x in (recs[-1].get("refs") or []) if "S1-CANONICAL-INTEGRATION-001" not in x]
        self._write(recs)
        self.assert_fails("pinned S1 integration event")

    def test_315_s1_directly_after_0053_rejected(self):
        self._write([r for r in self._ledger() if r.get("event_id") != self.PRIOR])
        self.assert_fails("must directly follow the pinned chain")

    def test_316_interposed_event_rejected(self):
        recs = self._ledger(); recs.insert(-1, dict(recs[-2], event_id="ANOX-EVENT-0054B")); self._write(recs)
        self.assert_fails("must directly follow the pinned chain")

    def test_317_historical_0054_mutation_rejected(self):
        recs = self._ledger()
        for r in recs:
            if r.get("event_id") == self.PRIOR:
                r["task"] = "ANOX-TASK-EVIL-001"
        self._write(recs)
        self.assert_fails("must directly follow the pinned chain")

    def test_318_historical_0052_mutation_rejected(self):
        recs = self._ledger()
        for r in recs:
            if r.get("event_id") == "ANOX-EVENT-0052":
                r["event_id"] = "ANOX-EVENT-0052X"
        self._write(recs)
        self.assert_fails("must directly follow the pinned chain")

    def test_319_s0_exception_not_reusable_for_s1(self):
        st = self._state()
        st["current_task"] = "ANOX-TASK-SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001"
        st["delivery_branch"] = "governance/security-remediation-s0-evidence-preservation-001"
        self._write_state(st)
        self.assert_fails("S0 one-time exception is not reusable for S1")

    def test_320_wrong_delivery_branch_in_state_rejected(self):
        st = self._state(); st["delivery_branch"] = "feature/whatever"; self._write_state(st)
        self.assert_fails("not reusable for S1")

    def test_321_overlong_ledger_line_rejected(self):
        recs = self._ledger(); recs[-1]["summary"] = "x" * 5000; self._write(recs)
        self.assert_fails("line-size violation")

    # -- registry -----------------------------------------------------------
    def test_330_registry_at_13_rejected(self):
        self._write_registry([r for r in self._registry() if r.get("audit_id") != self.S1_ID])
        self.assert_fails("exactly 14 records")
        self.assert_fails(f"{self.S1_ID} registry record missing")

    def test_331_registry_at_15_rejected(self):
        recs = self._registry()
        recs.append(dict(recs[-1], audit_id="SOME-OTHER-RECORD-001", record_id="SEC-AUDIT-REG-0015"))
        self._write_registry(recs)
        self.assert_fails("unexpected records")

    def test_332_duplicate_s1_record_rejected(self):
        recs, rec = self._s1_record(); recs.append(dict(rec, record_id="SEC-AUDIT-REG-0015")); self._write_registry(recs)
        self.assert_fails()

    def test_333_s0_record_still_pinned_verbatim(self):
        recs = self._registry()
        rec = next(r for r in recs if r.get("record_id") == "SEC-AUDIT-REG-0013")
        rec["msc_closed_by_s0"] = 1
        self._write_registry(recs)
        self.assert_fails("msc_closed_by_s0")

    def test_334_s0_record_dropped_rejected(self):
        self._write_registry([r for r in self._registry() if r.get("record_id") != "SEC-AUDIT-REG-0013"])
        self.assert_fails("SECURITY-REMEDIATION-S0-EVIDENCE-PRESERVATION-001 registry record missing")

    def test_335_false_msc_closure_by_s1_rejected(self):
        recs, rec = self._s1_record(); rec["msc_closed_by_s1"] = 1; self._write_registry(recs)
        self.assert_fails("msc_closed_by_s1")

    def test_336_open_msc_changed_rejected(self):
        recs, rec = self._s1_record(); rec["open_msc_units"] = 38; self._write_registry(recs)
        self.assert_fails("open_msc_units")

    def test_337_b004_started_rejected(self):
        recs, rec = self._s1_record(); rec["b004"] = "STARTED"; self._write_registry(recs)
        self.assert_fails("b004")

    def test_338_finding_disposition_weakened_rejected(self):
        recs, rec = self._s1_record(); rec["findings_final_disposition"]["F-1"] = "WONT_FIX"; self._write_registry(recs)
        self.assert_fails("findings_final_disposition")

    def test_339_provisional_event_relabelled_canonical_rejected(self):
        recs, rec = self._s1_record(); rec["s1_provisional_event_status"] = "CANONICAL"; self._write_registry(recs)
        self.assert_fails("s1_provisional_event_status")

    def test_340_runtime_evidence_overclaim_rejected(self):
        recs, rec = self._s1_record(); rec["x86_64_runtime_evidence"] = "PASS"; self._write_registry(recs)
        self.assert_fails("x86_64_runtime_evidence")
        recs, rec = self._s1_record(); rec["arm64_runtime_evidence"] = "INDEPENDENT_PASS"; self._write_registry(recs)
        self.assert_fails("arm64_runtime_evidence")

    def test_341_wrong_original_s1_sha_rejected(self):
        recs, rec = self._s1_record(); rec["s1_original_final_head_sha"] = "0" * 40; self._write_registry(recs)
        self.assert_fails("s1_original_final_head_sha")

    def test_342_wrong_merge_sha_rejected(self):
        recs, rec = self._s1_record(); rec["s1_integration_merge_sha"] = "0" * 40; self._write_registry(recs)
        self.assert_fails("s1_integration_merge_sha")

    def test_343_shared_validator_claimed_ratified_rejected(self):
        recs, rec = self._s1_record(); rec["shared_validator_followup"] = "RATIFIED"; self._write_registry(recs)
        self.assert_fails("shared_validator_followup")

    def test_344_report_tamper_rejected(self):
        p = self.root / "docs/reports/security/remediation/REMEDIATION-S1-CANONICAL-INTEGRATION-001.md"
        p.write_text(p.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
        self.assert_fails("integration report hash mismatch")

    def test_345_preserved_retest_report_tamper_rejected(self):
        p = self.root / "docs/reports/security/retests/INDEPENDENT-BUILD-SUPPLY-RETEST-S1-001.md"
        p.write_text(p.read_text(encoding="utf-8").replace("PASS_WITH_FINDINGS", "PASS", 1), encoding="utf-8")
        self.assert_fails("preserved source hash mismatch")

    def test_346_preserved_source_dropped_rejected(self):
        recs, rec = self._s1_record(); rec["preserved_sources"].pop("independent_retest"); self._write_registry(recs)
        self.assert_fails("preserved_sources keys")

    def test_347_native_behavior_changed_claim_rejected(self):
        recs, rec = self._s1_record(); rec["native_behavior_source_changed"] = "YES"; self._write_registry(recs)
        self.assert_fails("native_behavior_source_changed")

    def test_348_status_claims_closed_rejected(self):
        recs, rec = self._s1_record(); rec["status"] = "CLOSED"; self._write_registry(recs)
        self.assert_fails("status=")

    # -- ratification proposal integrity --------------------------------------
    def test_350_proposal_patch_tamper_rejected(self):
        p = self.root / VAL.PROPOSAL_PATCH
        p.write_text(p.read_text(encoding="utf-8").replace("ANOX-EVENT-0055", "ANOX-EVENT-0099"), encoding="utf-8")
        self.assert_fails("ratification proposal yields")

    def test_351_proposal_patch_missing_rejected(self):
        (self.root / VAL.PROPOSAL_PATCH).unlink()
        self.assert_fails("ratification proposal patch missing")

    def test_352_proposal_record_missing_hash_rejected(self):
        p = self.root / VAL.PROPOSAL_RECORD
        p.write_text(p.read_text(encoding="utf-8").replace(VAL.CENTRAL_PROPOSED_SHA256, "0" * 64), encoding="utf-8")
        self.assert_fails("does not carry the proposed post-change SHA-256")

    def test_353_proposal_is_not_a_decision(self):
        text = (REPO_ROOT / VAL.PROPOSAL_RECORD).read_text(encoding="utf-8")
        self.assertIn("NOT a decision", text)
        decisions = _load_jsonl(REPO_ROOT / "docs/workforce/registries/decisions.jsonl")
        self.assertFalse(any("S1-INTEGRATION-SHARED-VALIDATOR" in str(d.get("decision_id", "")) for d in decisions),
                         "the integration task must not record a Human decision")

    # -- scope constants --------------------------------------------------------
    def test_360_scope_constants_reject_product_and_authority_paths(self):
        for p in ("crypto/rust/src/lib.rs", "android/src/main/java/A.kt", "backend/x.ts",
                  "supabase/f.sql", "migrations/001.sql", "docs/authority/AUTHORITY_INDEX.md"):
            self.assertTrue(p.startswith(VAL.S1_FORBIDDEN_PREFIXES) or p.endswith(".sql"), p)
            self.assertFalse(p in VAL.S1_ALLOWED_EXACT or p.startswith(VAL.S1_ALLOWED_PREFIXES), p)
        self.assertNotIn(VAL.CENTRAL, VAL.S1_ALLOWED_EXACT)


class S1IntegrationTopologyTests(unittest.TestCase):
    """canonical_integration_delivery against real scratch repositories."""

    def setUp(self):
        sys.path.insert(0, str(REPO_ROOT / "tools" / "audit"))
        import lifecycle_legality as ll
        self.ll = ll
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        self.g("init", "-q")
        self.g("config", "user.email", "t@t"); self.g("config", "user.name", "t")
        self.g("commit", "-q", "--allow-empty", "-m", "b0")
        self.base0 = self.g("rev-parse", "HEAD")
        self.c("s1a"); self.s1a = self.g("rev-parse", "HEAD")
        self.c("s1b"); self.s1b = self.g("rev-parse", "HEAD")
        self.g("checkout", "-q", "-b", "main", self.base0)
        self.c("main1"); self.c("main2"); self.main = self.g("rev-parse", "HEAD")
        self.g("branch", "-q", "s1", self.s1b)
        self.g("merge", "-q", "--no-ff", "-m", "M", "s1"); self.merge = self.g("rev-parse", "HEAD")
        self.c("C1"); self.c1 = self.g("rev-parse", "HEAD")
        self.c("PROJECT_STATE.md"); self.c2 = self.g("rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def g(self, *a):
        return subprocess.run(["git", *a], cwd=self.r, capture_output=True, text=True, check=True).stdout.strip()

    def c(self, name):
        (self.r / name).write_text(name + "\n")
        self.g("add", name); self.g("commit", "-q", "-m", name)

    def prove(self, **kw):
        args = dict(base_sha=self.main, merged_head=self.s1b, merged_base=self.base0,
                    described_head=self.c1, live_head=self.c2, cwd=self.r,
                    metadata_allowlist={"PROJECT_STATE.md"})
        args.update(kw)
        return self.ll.canonical_integration_delivery(**args)

    def test_400_control_topology_accepted(self):
        ok, m, s, meta, reason = self.prove()
        self.assertTrue(ok, reason); self.assertEqual((m, s, meta), (self.merge, self.c1, self.c2))

    def test_401_wrong_merged_head_rejected(self):
        ok, *_, reason = self.prove(merged_head=self.s1a)
        self.assertFalse(ok); self.assertIn("pinned merged head", reason)

    def test_402_extra_task_commit_rejected(self):
        self.c("C3")
        ok, *_, reason = self.prove(live_head=self.g("rev-parse", "HEAD"))
        self.assertFalse(ok); self.assertIn("expected exactly 3 first-parent commits", reason)

    def test_403_metadata_touching_non_metadata_rejected(self):
        ok, *_, reason = self.prove(metadata_allowlist={"OTHER.md"})
        self.assertFalse(ok); self.assertIn("non-metadata files", reason)

    def test_404_described_head_mismatch_rejected(self):
        ok, *_, reason = self.prove(described_head=self.merge)
        self.assertFalse(ok); self.assertIn("!= described_head", reason)

    def test_405_smuggled_foreign_commit_rejected(self):
        # a third foreign commit on the S1 side is integrated instead of the pinned two
        self.g("checkout", "-q", "s1"); self.c("s1c"); s1c = self.g("rev-parse", "HEAD")
        self.g("checkout", "-q", "main"); self.g("reset", "-q", "--hard", self.main)
        self.g("merge", "-q", "--no-ff", "-m", "M2", "s1"); self.c("C1x"); c1 = self.g("rev-parse", "HEAD")
        self.c("PROJECT_STATE.md"); c2 = self.g("rev-parse", "HEAD")
        ok, *_, reason = self.prove(merged_head=s1c, described_head=c1, live_head=c2)
        self.assertFalse(ok); self.assertIn("exactly 2 commits", reason)

    def test_406_no_merge_rejected(self):
        self.g("reset", "-q", "--hard", self.main); self.c("X"); self.c("PROJECT_STATE.md")
        x1 = self.g("rev-parse", "HEAD~1"); x2 = self.g("rev-parse", "HEAD")
        ok, *_, reason = self.prove(described_head=x1, live_head=x2)
        self.assertFalse(ok); self.assertIn("not an ancestor", reason)


class S0EraPrecisionTests(unittest.TestCase):
    """Paired tests for the two era-precision corrections applied to S0-owned
    validators by REMEDIATION-S1-CANONICAL-INTEGRATION-001 (documented, not
    silent; S0 test counts stay pinned at 98/40, so the pairs live here).

    1. validate_s0_evidence_preservation: 0054 is a sealed chain position —
       later canonical events may follow, but 0054 exactly once, no S0 task
       re-recorded after it, ids strictly ascending, Project Memory fresh.
    2. validate_s0_contract_freeze: the S0 scope diff is S0's own pinned range
       base..final-head (a later delivery touching S1-owned files does not
       retro-fail S0), while protected-shared-file content is still checked at
       HEAD.
    """

    S0_PRES = REPO_ROOT / "tools/audit/validate_s0_evidence_preservation.py"
    S0_CONTRACT = REPO_ROOT / "tools/audit/validate_s0_contract_freeze.py"

    def setUp(self):
        s0spec = importlib.util.spec_from_file_location("anox_s0_pres_tests", REPO_ROOT / "tools/audit/test_s0_evidence_preservation.py")
        s0t = importlib.util.module_from_spec(s0spec); s0spec.loader.exec_module(s0t)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in list(s0t.FIXTURE_FILES) + FIXTURE_FILES:
            src = REPO_ROOT / rel
            if src.exists():
                dst = self.root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
        self.LEDGER = self.root / "docs/continuity/PROJECT_HISTORY_LEDGER.jsonl"
        self.CS = self.root / "docs/continuity/CURRENT_STATE.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _run_pres(self):
        env = dict(os.environ); env["S0_EVIDENCE_PRESERVATION_REPO"] = str(self.root)
        return subprocess.run([sys.executable, str(self.S0_PRES)], cwd=self.root, env=env, capture_output=True, text=True)

    def _ledger(self):
        return _load_jsonl(self.LEDGER)

    def _write(self, recs):
        _write_jsonl(self.LEDGER, recs)
        st = json.loads(self.CS.read_text()); st["latest_material_event_id"] = recs[-1]["event_id"]
        self.CS.write_text(json.dumps(st, indent=1))

    def test_500_control_0054_followed_by_canonical_0055_passes(self):
        r = self._run_pres()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_501_duplicate_0054_rejected(self):
        recs = self._ledger(); ev = next(e for e in recs if e["event_id"] == "ANOX-EVENT-0054")
        recs.insert(recs.index(ev) + 1, dict(ev)); self._write(recs)
        r = self._run_pres(); self.assertNotEqual(r.returncode, 0); self.assertIn("must occur exactly once", r.stdout)

    def test_502_s0_task_rerecorded_after_preservation_rejected(self):
        recs = self._ledger()
        recs.append(dict(recs[-1], event_id="ANOX-EVENT-0056", task="ANOX-TASK-REMEDIATION-SESSION-S0-CONTRACT-FREEZE-001"))
        self._write(recs)
        r = self._run_pres(); self.assertNotEqual(r.returncode, 0); self.assertIn("S0 task re-recorded after preservation", r.stdout)

    def test_503_non_ascending_id_after_0054_rejected(self):
        recs = self._ledger(); recs[-1]["event_id"] = "ANOX-EVENT-0053"; self._write(recs)
        r = self._run_pres(); self.assertNotEqual(r.returncode, 0); self.assertIn("non-ascending/illegal id", r.stdout)

    def test_504_stale_project_memory_rejected(self):
        st = json.loads(self.CS.read_text()); st["latest_material_event_id"] = "ANOX-EVENT-0054"; self.CS.write_text(json.dumps(st, indent=1))
        r = self._run_pres(); self.assertNotEqual(r.returncode, 0); self.assertIn("Project Memory stale", r.stdout)

    def test_505_0054_removed_still_rejected(self):
        self._write([e for e in self._ledger() if e["event_id"] != "ANOX-EVENT-0054"])
        r = self._run_pres(); self.assertNotEqual(r.returncode, 0); self.assertIn("ANOX-EVENT-0054", r.stdout)

    def test_510_s0_scope_uses_pinned_s0_range(self):
        src = self.S0_CONTRACT.read_text(encoding="utf-8")
        self.assertIn('AUTHORIZED_S0_FINAL_HEAD_SHA = "0be57335adaa25ad584357dde74666eb97339a01"', src)
        self.assertIn('["git", "diff", "--name-only", base, AUTHORIZED_S0_FINAL_HEAD_SHA]', src)
        # protected shared files remain checked against HEAD content
        self.assertIn("if p in PROTECTED_SHARED_FILES}", src)

    def test_511_s0_scope_live_repo_passes_with_s1_integrated(self):
        # In a real clone the S0 scope gate must PASS although S1 (legitimately)
        # changed S1-owned files after S0's range; requires git — skip in fixture-only CI.
        if not (REPO_ROOT / ".git").exists():
            self.skipTest("no git context")
        env = dict(os.environ); env.pop("S0_CONTRACT_FREEZE_REPO", None)
        r = subprocess.run([sys.executable, str(self.S0_CONTRACT)], cwd=REPO_ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:])
        self.assertNotIn("S0 changed product/S1-owned paths", r.stdout)


if __name__ == "__main__":
    unittest.main()
