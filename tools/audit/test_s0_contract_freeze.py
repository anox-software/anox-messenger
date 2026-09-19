#!/usr/bin/env python3
"""Adversarial fail-closed tests for tools/audit/validate_s0_contract_freeze.py.

Each test copies the S0 authority surfaces into a temporary tree, applies one
contract-weakening mutation, and asserts that the S0 contract-freeze validator
FAILS.  A baseline test asserts the unmodified tree PASSES.

Run:  python3 -m unittest tools.audit.test_s0_contract_freeze
"""
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import validate_s0_contract_freeze as v  # noqa: E402

FIXTURE_FILES = (
    v.AMENDMENT_PATH,
    v.MANIFEST_PATH,
    v.AUTHORITY_INDEX_PATH,
    v.FREEZE_REGISTRY_PATH,
    "docs/current/DATABASE_ARCHITECTURE.md",
    "docs/current/BACKEND_ARCHITECTURE.md",
    v.FINDINGS_PATH,
    v.IMPL_READINESS_PATH,
    # correction pass (F-01/F-03): Human ratification surfaces + the protected shared file
    v.DECISIONS_PATH,
    v.F01_RATIFICATION_REPORT,
    v.PRESERVATION_RATIFICATION_REPORT,
    "tools/audit/validate_security_audit_evidence_preservation.py",
    # four-path ratification transaction (REMEDIATION-S1-FOUR-FILE-RATIFICATION-
    # TRANSACTION-001): the fixture must carry the WHOLE package, otherwise the
    # third authorized content could never have its post-images verified here.
    v.S1_INTEGRATION_RATIFICATION_REPORT,
    "tools/audit/test_security_audit_evidence_preservation.py",
    "tools/audit/test_s0_contract_freeze.py",
    "tools/audit/validate_s0_contract_freeze.py",
)


def run_validator(root):
    v.REPO_ROOT = Path(root)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        errors = v.run()
    return errors, buf.getvalue()


class S0ContractFreezeAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="s0_contract_freeze_")
        for rel in FIXTURE_FILES:
            src = REPO_ROOT / rel
            dst = Path(self.tmp) / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.addCleanup(setattr, v, "REPO_ROOT", REPO_ROOT)

    # -- helpers -----------------------------------------------------------
    def central_era(self):
        """Which Human-ratified content the protected central validator carries.

        The paired suite must pass in BOTH legitimate eras: before the four-path
        ratification transaction (`s0_preservation`) and after it
        (`s1_integration`). Era is read from content, never assumed.
        """
        rel = "tools/audit/validate_security_audit_evidence_preservation.py"
        spec = v.PROTECTED_SHARED_FILES[rel]
        digest = hashlib.sha256((REPO_ROOT / rel).read_bytes()).hexdigest()
        if digest == spec.get("s1_integration_authorized_sha256"):
            return "s1_integration"
        if digest == spec["preservation_authorized_sha256"]:
            return "s0_preservation"
        if digest == spec["authorized_sha256"]:
            return "s0_successor"
        return "unknown"

    def path(self, rel):
        return Path(self.tmp) / rel

    def read(self, rel):
        return self.path(rel).read_text(encoding="utf-8")

    def write(self, rel, text):
        self.path(rel).write_text(text, encoding="utf-8")

    def mutate_clause(self, cid, old, new):
        """Replace `old` with `new` inside the single clause line of `cid`."""
        text = self.read(v.AMENDMENT_PATH)
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if f"**[{cid}]**" in line:
                self.assertIn(old, line, f"{cid} fixture does not contain {old!r}")
                lines[i] = line.replace(old, new)
                self.write(v.AMENDMENT_PATH, "\n".join(lines) + "\n")
                return
        self.fail(f"clause {cid} not found in fixture")

    def delete_clauses(self, *cids):
        text = self.read(v.AMENDMENT_PATH)
        lines = [ln for ln in text.splitlines() if not any(f"**[{c}]**" in ln for c in cids)]
        self.write(v.AMENDMENT_PATH, "\n".join(lines) + "\n")
        # keep the manifest coherent so the failure is the invariant, not a bookkeeping mismatch
        man = json.loads(self.read(v.MANIFEST_PATH))
        for c in man["contracts"]:
            c["clauses"] = [x for x in c["clauses"] if x not in cids]
        man["framework_clauses"] = [x for x in man["framework_clauses"] if x not in cids]
        for group in ("server_contract_authority", "client_contract_authority", "server_breaker_authority"):
            for entry in man[group].values():
                entry["clauses"] = [x for x in entry.get("clauses", []) if x not in cids]
        for entry in man["attackchain_contract_coverage"].values():
            entry["clauses"] = [x for x in entry["clauses"] if x not in cids]
        self.write(v.MANIFEST_PATH, json.dumps(man, indent=2, ensure_ascii=False))

    def edit_manifest(self, fn):
        man = json.loads(self.read(v.MANIFEST_PATH))
        fn(man)
        self.write(v.MANIFEST_PATH, json.dumps(man, indent=2, ensure_ascii=False))

    def edit_decision(self, fn):
        """Mutate the F-01 ratification record in the fixture decisions registry."""
        recs = [json.loads(l) for l in self.read(v.DECISIONS_PATH).splitlines() if l.strip()]
        for r in recs:
            if r.get("decision_id") == v.F01_RATIFICATION_DECISION_ID:
                fn(r)
        self.write(v.DECISIONS_PATH, "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n")

    def drop_decision(self):
        recs = [json.loads(l) for l in self.read(v.DECISIONS_PATH).splitlines() if l.strip()]
        recs = [r for r in recs if r.get("decision_id") != v.F01_RATIFICATION_DECISION_ID]
        self.write(v.DECISIONS_PATH, "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n")

    def assert_fail(self, needle=None):
        errors, out = run_validator(self.tmp)
        self.assertTrue(errors, f"validator unexpectedly PASSED\n{out}")
        if needle:
            self.assertTrue(any(needle in e for e in errors), f"no error mentions {needle!r}: {errors}")
        return errors

    # -- baseline ------------------------------------------------------------
    def test_00_baseline_passes(self):
        errors, out = run_validator(self.tmp)
        self.assertEqual(errors, [], out)
        self.assertIn("SC 14/14 · CC 14/14 · SERVER_BREAKER 18/18", out)

    # -- 25 required adversarial mutations -------------------------------------
    def test_01_remove_global_deviceauth_key_uniqueness(self):
        self.mutate_clause("S0-028-01", "**globally unique**", "unique per account")
        self.assert_fail("S0-028-01")

    def test_02_remove_known_key_rejection(self):
        self.delete_clauses("S0-028-03")
        self.assert_fail("S0-028-03")

    def test_03_remove_immutable_jkt_device_account_binding(self):
        self.mutate_clause("S0-028-06", "**immutable** after the registration commit transaction",
                           "mutable after the registration commit transaction")
        self.assert_fail("S0-028-06")

    def test_04_remove_one_active_device_rule(self):
        self.delete_clauses("S0-028-08", "S0-028-09")
        self.assert_fail("S0-028-08")

    def test_05_remove_registration_idempotency(self):
        self.delete_clauses("S0-026-01", "S0-026-02", "S0-026-03")
        errors = self.assert_fail("S0-026-01")
        self.assertTrue(any("SC-2" in e or "S4" in e for e in errors), errors)

    def test_06_make_jkt_binding_optional(self):
        self.mutate_clause("S0-026-04", "MUST require it to equal", "MAY require it to equal")
        self.assert_fail("S0-026-04")

    def test_06b_make_jkt_binding_nullable(self):
        self.mutate_clause("S0-026-05", "non-nullable input", "nullable input")
        self.assert_fail("S0-026-05")

    def test_07_make_ath_optional(self):
        self.mutate_clause("S0-026-07", "MUST contain `ath`", "MAY contain `ath`")
        self.assert_fail("S0-026-07")

    def test_08_remove_nonce_lifecycle(self):
        self.delete_clauses(*[f"S0-025-{i:02d}" for i in range(1, 9)])
        errors = self.assert_fail("S0-025-01")
        self.assertTrue(any("SC-7" in e or "S9" in e for e in errors), errors)

    def test_08b_make_nonce_optional(self):
        self.mutate_clause("S0-025-01", "**Nonce is required, not optional**", "Nonce is optional (implementation choice)")
        self.assert_fail("S0-025-01")

    def test_09_make_replay_store_process_local(self):
        self.mutate_clause("S0-026-09", "**prohibited** as the production replay store",
                           "permitted as the production replay store")
        self.assert_fail("S0-026-09")

    def test_10_remove_rollback_safe_retention(self):
        self.mutate_clause("S0-026-12", "never by wall-clock insertion time alone", "by wall-clock insertion time")
        self.assert_fail("S0-026-12")

    def test_11_htu_decoded_path_instead_of_raw(self):
        self.mutate_clause("S0-022-01", "percent-encoded, **not decoded**, not re-encoded",
                           "the percent-decoded path, not re-encoded")
        self.assert_fail("S0-022-01")

    def test_12_permit_userinfo(self):
        self.mutate_clause("S0-022-02", "**no userinfo** (an authority component containing `@` is rejected)",
                           "userinfo is permitted (an authority component containing `@` is retained)")
        self.assert_fail("S0-022-02")

    def test_13_remove_typed_registration_pop(self):
        self.mutate_clause("S0-027-01", "An opaque, untyped `proof` field is **not** a conformant contract.",
                           "An opaque `proof` field is acceptable.")
        self.assert_fail("S0-027-01")

    def test_14_permit_deviceauth_jwk_different_from_proof_key(self):
        self.mutate_clause("S0-027-05", "A second JWK per `registration_id` is never accepted.",
                           "A second JWK per `registration_id` MAY be accepted.")
        self.assert_fail("S0-027-05")

    def test_15_remove_first_run_alias_cross_check(self):
        self.mutate_clause("S0-033-04",
                           "(c) marker `ABSENT` **AND any relevant anoX Keystore alias or local state indicates prior initialization** ⇒ **NOT FIRST RUN**, fail closed, explicit recovery-reset path only; ",
                           "")
        self.assert_fail("S0-033-04")

    def test_16_map_corrupt_empty_to_fresh_first_run(self):
        self.mutate_clause("S0-033-07", "**none** maps to `NotStarted`", "`EMPTY` maps to `NotStarted`")
        self.assert_fail("S0-033-07")

    def test_17_remove_armed_state_rejection_semantics(self):
        self.delete_clauses(*[f"S0-018-{i:02d}" for i in range(1, 7)])
        errors = self.assert_fail("S0-018-01")
        self.assertTrue(any("AC-014" in e or "SC-12" in e or "S17" in e for e in errors), errors)

    def test_17b_rejected_clears_armed_marker(self):
        self.mutate_clause("S0-018-03", "the marker stays `ARMED`", "the marker becomes `ABSENT`")
        self.assert_fail("S0-018-03")

    def test_18_remove_wipe_order(self):
        self.delete_clauses("S0-032-07")
        self.assert_fail("S0-032-07")

    def test_18b_marker_deleted_first(self):
        self.mutate_clause("S0-032-07", "delete the marker file **last**", "delete the marker file first")
        self.assert_fail("S0-032-07")

    def test_19_remove_server_revocation_requirement(self):
        text = self.read(v.AMENDMENT_PATH)
        old = "| Server `devices` row | R (`ACTIVE`) | V (wipe intent → `REVOKED`, best effort) | V (`REVOKED`, then account `DELETED`) |"
        self.assertIn(old, text)
        self.write(v.AMENDMENT_PATH, text.replace(old, "| Server `devices` row | R (`ACTIVE`) | R | R |"))
        self.assert_fail("S18")

    def test_20_remove_backup_reinstall_expected_state_contract(self):
        self.delete_clauses(*[f"S0-034-{i:02d}" for i in range(1, 9)])
        self.assert_fail("S0-034-03")

    def test_21_remove_s15_epoch_authority(self):
        self.delete_clauses("S0-034-09", *[f"S0-020-{i:02d}" for i in range(1, 8)])
        errors = self.assert_fail("S15")
        self.assertTrue(any("S0-020-01" in e for e in errors), errors)

    def test_22_treat_self_reported_strongbox_as_authorization_fact(self):
        self.mutate_clause("S0-042-03", "Self-reported StrongBox is not a server authorization fact.",
                           "Self-reported StrongBox is a server authorization fact.")
        self.assert_fail("S0-042-03")

    def test_23_retire_arch_010_immediately(self):
        self.mutate_clause("S0-017-03", "It is **not** retired by S0; B004 has not started.",
                           "It is retired by S0 effective immediately.")
        self.assert_fail("S0-017-03")

    def test_23b_arch_010_finding_marked_retired_in_registry(self):
        lines = self.read(v.FINDINGS_PATH).splitlines()
        for i, ln in enumerate(lines):
            rec = json.loads(ln)
            if rec.get("finding_id") == "ANOX-SECURITY-ARCH-010":
                rec["status"] = "Retired"
                lines[i] = json.dumps(rec, ensure_ascii=False)
        self.write(v.FINDINGS_PATH, "\n".join(lines) + "\n")
        self.assert_fail("ANOX-SECURITY-ARCH-010")

    def test_24_revive_root_016(self):
        self.mutate_clause("S0-017-02", "`ROOT-016` remains `REJECTED_NOT_A_FINDING` — **DO NOT REVIVE**.",
                           "`ROOT-016` is revived as a finding.")
        self.assert_fail("S0-017-02")

    def test_25_second_equal_precedence_schema_authority(self):
        rel = "docs/current/DATABASE_ARCHITECTURE.md"
        self.write(rel, self.read(rel) + "\n<!-- SCHEMA-AUTHORITY-HOME: DB-SCHEMA-V1-FROZEN -->\n")
        self.assert_fail("exactly one schema authority home")

    def test_25b_deferring_document_reasserts_schema_not_frozen(self):
        rel = "docs/current/BACKEND_ARCHITECTURE.md"
        self.write(rel, self.read(rel) + "\n- Final DB schema is **not frozen**.\n")
        self.assert_fail("competing authority")

    def test_25c_deferring_document_drops_deference_marker(self):
        rel = "docs/current/DATABASE_ARCHITECTURE.md"
        self.write(rel, self.read(rel).replace("DEFERS-TO: DB-SCHEMA-V1-FROZEN", "SEE ALSO: DB-SCHEMA-V1-FROZEN"))
        self.assert_fail("deference marker")

    # -- structural / authority-index / lifecycle tampering ---------------------
    def test_26_amendment_missing(self):
        self.path(v.AMENDMENT_PATH).unlink()
        self.assert_fail("missing")

    def test_27_unregistered_clause_added(self):
        self.write(v.AMENDMENT_PATH, self.read(v.AMENDMENT_PATH) + "\n- **[S0-099-01]** Unregistered normative text.\n")
        self.assert_fail("not registered")

    def test_28_duplicate_clause_identifier(self):
        text = self.read(v.AMENDMENT_PATH)
        self.write(v.AMENDMENT_PATH, text + "\n- **[S0-028-01]** Duplicate weaker restatement.\n")
        self.assert_fail("duplicate")

    def test_29_clause_moved_out_of_its_contract_section(self):
        text = self.read(v.AMENDMENT_PATH)
        lines = text.splitlines()
        idx = next(i for i, ln in enumerate(lines) if "**[S0-026-04]**" in ln)
        clause = lines.pop(idx)
        lines.append(clause)  # now under "Historical provenance"
        self.write(v.AMENDMENT_PATH, "\n".join(lines) + "\n")
        self.assert_fail("not under its contract heading")

    def test_30_sc_authority_home_removed_from_manifest(self):
        self.edit_manifest(lambda m: m["server_contract_authority"].pop("SC-7"))
        self.assert_fail("SC-7")

    def test_31_sc_authority_home_emptied(self):
        self.edit_manifest(lambda m: m["server_contract_authority"]["SC-3"].__setitem__("clauses", []))
        self.assert_fail("SC-3")

    def test_32_cc_owner_unknown(self):
        self.edit_manifest(lambda m: m["client_contract_authority"]["CC-7"].__setitem__("owner", ""))
        self.assert_fail("CC-7")

    def test_33_breaker_status_downgraded(self):
        self.edit_manifest(lambda m: m["server_breaker_authority"]["S7"].__setitem__("status", "NOT_FROZEN"))
        self.assert_fail("S7")

    def test_34_ac001_accepts_uniqueness_alone(self):
        def fn(m):
            m["attackchain_contract_coverage"]["AC-001"]["rule"] = "uniqueness_alone_sufficient"
            m["attackchain_contract_coverage"]["AC-001"]["breakers"] = ["S1"]
        self.edit_manifest(fn)
        self.assert_fail("AC-001")

    def test_35_ac003_ath_alone(self):
        self.edit_manifest(lambda m: m["attackchain_contract_coverage"]["AC-003"].__setitem__("breakers", ["S8"]))
        self.assert_fail("AC-003")

    def test_36_msc_unit_marked_closed_by_s0(self):
        self.edit_manifest(lambda m: m["msc_stage_proposals"]["units"]["MSC_UNIT_028"].__setitem__("stage", "CLOSED"))
        self.assert_fail("MSC_UNIT_028")

    def test_37_closed_by_s0_nonzero(self):
        def fn(m):
            m["msc_stage_proposals"]["closed_by_s0"] = 1
            m["msc_stage_proposals"]["open_msc_units"] = 41
        self.edit_manifest(fn)
        self.assert_fail("closed_by_s0")

    def test_38_b004_claimed_started(self):
        self.mutate_clause("S0-000-12", "`B004 = NOT_STARTED`", "`B004 = STARTED`")
        self.assert_fail("S0-000-12")

    def test_39_implementation_readiness_b005_started(self):
        ir = json.loads(self.read(v.IMPL_READINESS_PATH))
        ir["domains"]["B-005"]["implementation_state"] = "IN_PROGRESS"
        self.write(v.IMPL_READINESS_PATH, json.dumps(ir, indent=2))
        self.assert_fail("B-005")

    def test_40_authority_index_drops_v1_4(self):
        text = self.read(v.AUTHORITY_INDEX_PATH)
        text = "\n".join(ln for ln in text.splitlines() if "B025_MANDATORY_AMENDMENTS_V1_4.md" not in ln)
        self.write(v.AUTHORITY_INDEX_PATH, text + "\n")
        self.assert_fail("AUTHORITY_INDEX")

    def test_41_authority_index_ranks_v1_4_below_snapshot(self):
        text = self.read(v.AUTHORITY_INDEX_PATH)
        lines = text.splitlines()
        i4 = next(i for i, ln in enumerate(lines) if ln.startswith("11. `B025_MANDATORY_AMENDMENTS_V1_4.md`"))
        i12 = next(i for i, ln in enumerate(lines) if ln.startswith("12. `B025/TRACK_B/B0xx_*.md`"))
        l4, l12 = lines[i4], lines[i12]
        lines[i4] = "11." + l12[3:]
        lines[i12] = "12." + l4[3:]
        self.write(v.AUTHORITY_INDEX_PATH, "\n".join(lines) + "\n")
        self.assert_fail("must rank")

    def test_42_freeze_registry_b005_points_at_old_home(self):
        text = self.read(v.FREEZE_REGISTRY_PATH)
        text = re.sub(r"^\| B-005 \|.*$",
                      "| B-005 | Database Schema + RLS | FROZEN v1.11-f02 (amended by B025_MANDATORY_AMENDMENTS_V1_2.md) | `docs/authority/B025_MANDATORY_AMENDMENTS_V1_2.md#B-005` |",
                      text, flags=re.MULTILINE)
        self.write(v.FREEZE_REGISTRY_PATH, text)
        self.assert_fail("B-005")

    def test_43_root_013_severity_rewritten(self):
        self.mutate_clause("S0-017-01", "`ROOT-013` canonical severity is `MEDIUM`", "`ROOT-013` canonical severity is `LOW`")
        self.assert_fail("S0-017-01")

    def test_44_sql_ddl_smuggled_into_contract(self):
        self.write(v.AMENDMENT_PATH, self.read(v.AMENDMENT_PATH) + "\nCREATE TABLE auth.device_auth_keys (key_id uuid);\n")
        self.assert_fail("SQL")

    def test_45_manifest_lifecycle_claims_s0_closed(self):
        self.edit_manifest(lambda m: m["lifecycle"].__setitem__("remediation_session_s0", "CLOSED"))
        self.assert_fail("remediation_session_s0")

    # =====================================================================
    # CORRECTION PASS — adversarial tests for retest findings F-02…F-10.
    # Every mutation must FAIL for the intended security/governance reason.
    # =====================================================================

    # -- F-02: scope base must fail closed, never SKIP ----------------------
    def test_46_f02_base_sha_nonexistent(self):
        self.edit_manifest(lambda m: m.__setitem__("base_sha", "0" * 40))
        self.assert_fail("not the authorized S0 base")

    def test_47_f02_base_sha_malformed(self):
        self.edit_manifest(lambda m: m.__setitem__("base_sha", "not-a-sha"))
        self.assert_fail("malformed")

    def test_48_f02_base_sha_missing(self):
        self.edit_manifest(lambda m: m.pop("base_sha"))
        self.assert_fail("base_sha missing")

    def test_49_f02_base_sha_redeclared_to_other_commit(self):
        # a real-looking but unauthorized base must not silently re-scope the gate
        self.edit_manifest(lambda m: m.__setitem__("base_sha", "9e585468d081272398e022f12e76e7500d55cbee"))
        self.assert_fail("not the authorized S0 base")

    def test_50_f02_scope_gate_never_skips_on_bad_base(self):
        self.edit_manifest(lambda m: m.__setitem__("base_sha", "0" * 40))
        errors, out = run_validator(self.tmp)
        self.assertTrue(errors)
        self.assertNotIn("SKIP base", out)

    # -- F-03: protected shared governance file ----------------------------
    def test_51_f03_protected_file_changed_without_ratification(self):
        self.drop_decision()
        self.assert_fail("requires an explicit Human ratification")

    def test_52_f03_protected_file_arbitrary_second_modification(self):
        rel = "tools/audit/validate_security_audit_evidence_preservation.py"
        self.write(rel, self.read(rel) + "\n# unauthorized second change\n")
        self.assert_fail("unauthorized modification")
        # Four-path transaction integrity (era-aware): once the protected central
        # validator carries the S1 successor content, tampering with ANY
        # externally pinned member of the ratification package must also fail
        # closed, so the package can never be ratified piecemeal or half-applied.
        # Before ratification the third pin is simply not active, and asserting
        # on it would be asserting on the wrong era.
        if self.central_era() == "s1_integration":
            for member in sorted(v.S1_RATIFICATION_POST_IMAGES):
                self.setUp()
                self.write(member, self.read(member) + "\n# tampered package member\n")
                errors, out = run_validator(self.tmp)
                self.assertTrue(errors, f"tampered package member {member} must fail closed\n{out}")
                self.assertTrue(any("four-file package is not intact" in e or "unauthorized modification" in e
                                    for e in errors), f"unexpected errors for {member}: {errors}")

    def test_53_f03_protected_file_reverted_to_pre_s0(self):
        rel = "tools/audit/validate_security_audit_evidence_preservation.py"
        self.write(rel, "# stub\n")
        self.assert_fail("unauthorized modification")

    def test_54_f03_ratification_wrong_task(self):
        self.edit_decision(lambda r: r.__setitem__("ratified_task", "ANOX-TASK-SOMETHING-ELSE-001"))
        self.assert_fail("ratified_task")

    def test_55_f03_ratification_wrong_file(self):
        self.edit_decision(lambda r: r.__setitem__("ratified_files", ["tools/security/validate_apk_contents.py"]))
        self.assert_fail("ratified_files")

    def test_56_f03_ratification_wrong_digest(self):
        self.edit_decision(lambda r: r.__setitem__(
            "ratified_sha256", {"tools/audit/validate_security_audit_evidence_preservation.py": "de" * 32}))
        self.assert_fail("ratified_sha256")

    def test_57_f03_ratification_claims_blanket_ownership(self):
        self.edit_decision(lambda r: r.__setitem__("grants_general_ownership", True))
        self.assert_fail("grants_general_ownership")

    def test_58_f03_ratification_grants_s1_permission(self):
        self.edit_decision(lambda r: r.__setitem__("grants_s1_permission", True))
        self.assert_fail("grants_s1_permission")

    def test_59_f03_ratification_grants_future_sessions(self):
        self.edit_decision(lambda r: r.__setitem__("grants_future_sessions", True))
        self.assert_fail("grants_future_sessions")

    def test_60_f03_ratification_scope_widened(self):
        self.edit_decision(lambda r: r.__setitem__("scope", "STANDING_PERMISSION"))
        self.assert_fail("ONE_TIME_CHANGE_SPECIFIC")

    def test_61_f03_ratification_drops_s1_prohibition(self):
        self.edit_decision(lambda r: r.__setitem__("s1_prohibited_before_integration", False))
        self.assert_fail("s1_prohibited_before_integration")

    def test_62_f03_ratification_not_human_authority(self):
        self.edit_decision(lambda r: r.__setitem__("authority_actor", "Devin CLI"))
        self.assert_fail("Human Product & Security Owner")

    def test_63_f03_ratification_record_document_missing(self):
        self.path(v.F01_RATIFICATION_REPORT).unlink()
        self.assert_fail("canonical record")

    # -- F-04: deference set is validator-owned ----------------------------
    def test_64_f04_manifest_drops_deference_document(self):
        self.edit_manifest(lambda m: m.__setitem__("schema_deferring_documents", []))
        self.assert_fail("may not be narrowed")

    def test_65_f04_coherent_tamper_database_architecture(self):
        # manifest hides the document AND the document reasserts competing authority
        self.edit_manifest(lambda m: m.__setitem__("schema_deferring_documents", []))
        rel = "docs/current/DATABASE_ARCHITECTURE.md"
        self.write(rel, self.read(rel) + "\n- Final DB schema is **not frozen**.\n")
        errors = self.assert_fail("competing authority")
        self.assertTrue(any("DATABASE_ARCHITECTURE" in e for e in errors), errors)

    def test_66_f04_coherent_tamper_backend_architecture(self):
        self.edit_manifest(lambda m: m.__setitem__("schema_deferring_documents", []))
        rel = "docs/current/BACKEND_ARCHITECTURE.md"
        self.write(rel, self.read(rel) + "\n- Final DB schema is **not frozen**.\n")
        errors = self.assert_fail("competing authority")
        self.assertTrue(any("BACKEND_ARCHITECTURE" in e for e in errors), errors)

    def test_67_f04_deference_marker_stripped_while_manifest_hides_doc(self):
        self.edit_manifest(lambda m: m.__setitem__("schema_deferring_documents", []))
        rel = "docs/current/BACKEND_ARCHITECTURE.md"
        self.write(rel, self.read(rel).replace("DEFERS-TO: DB-SCHEMA-V1-FROZEN", "SEE ALSO:"))
        self.assert_fail("deference marker")

    def test_68_f04_home_marker_renamed_in_manifest(self):
        self.edit_manifest(lambda m: m.__setitem__("schema_authority_home_marker", "SOMETHING-ELSE"))
        self.assert_fail("schema_authority_home_marker")

    # -- F-05: coherent mapping remaps ------------------------------------
    def _remap_sc6(self):
        self.edit_manifest(lambda m: m["server_contract_authority"]["SC-6"].__setitem__("clauses", ["S0-042-01"]))
        text = self.read(v.AMENDMENT_PATH)
        old = "| SC-6 | ES256/P-256 proof; jkt binding mandatory; ath mandatory; htm equality; iat ±120 s | [S0-026-04]–[S0-026-07], [S0-026-11], [S0-026-18] | B-002 v1.1 |"
        self.assertIn(old, text)
        self.write(v.AMENDMENT_PATH, text.replace(
            old,
            "| SC-6 | ES256/P-256 proof; jkt binding mandatory; ath mandatory; htm equality; iat ±120 s | [S0-042-01] | B-002 v1.1 |"))

    def test_69_f05_coherent_sc_remap(self):
        self._remap_sc6()
        errors = self.assert_fail("SC-6")
        self.assertTrue(any("anchor" in e for e in errors), errors)

    def test_70_f05_coherent_cc_remap(self):
        self.edit_manifest(lambda m: m["client_contract_authority"]["CC-7"].__setitem__("clauses", ["S0-042-01"]))
        errors = self.assert_fail("CC-7")
        self.assertTrue(any("anchor" in e for e in errors), errors)

    def test_71_f05_coherent_breaker_remap(self):
        def fn(m):
            m["server_breaker_authority"]["S7"]["clauses"] = ["S0-042-01"]
        self.edit_manifest(fn)
        text = self.read(v.AMENDMENT_PATH)
        old = "| S7 | Mandatory jkt binding | [S0-026-04]–[S0-026-06] | FROZEN_IN_AUTHORITY |"
        self.assertIn(old, text)
        self.write(v.AMENDMENT_PATH, text.replace(
            old, "| S7 | Mandatory jkt binding | [S0-042-01] | FROZEN_IN_AUTHORITY |"))
        errors = self.assert_fail("S7")
        self.assertTrue(any("anchor" in e for e in errors), errors)

    def test_72_f05_ac001_breaker_remap(self):
        self.edit_manifest(lambda m: m["attackchain_contract_coverage"]["AC-001"].__setitem__("breakers", ["S1", "S2"]))
        self.assert_fail("AC-001")

    def test_73_f05_ac003_breaker_remap(self):
        self.edit_manifest(lambda m: m["attackchain_contract_coverage"]["AC-003"].__setitem__("breakers", ["C9"]))
        self.assert_fail("AC-003")

    def test_74_f05_ac010_breaker_remap(self):
        self.edit_manifest(lambda m: m["attackchain_contract_coverage"]["AC-010"].__setitem__("breakers", ["C10"]))
        self.assert_fail("AC-010")

    def test_75_f05_retained_breaker_given_v1_4_clause(self):
        self.edit_manifest(lambda m: m["server_breaker_authority"]["S13"].__setitem__("clauses", ["S0-020-02"]))
        self.assert_fail("S13")

    def test_76_f05_breaker_status_flipped_to_retained(self):
        self.edit_manifest(lambda m: m["server_breaker_authority"]["S1"].__setitem__("status", "RETAINED_V1_2"))
        self.assert_fail("S1")

    # -- F-07: MSC-022 role ------------------------------------------------
    def test_77_f07_msc022_added_as_primary_unit(self):
        def fn(m):
            m["msc_stage_proposals"]["units"]["MSC_UNIT_022"] = {"portion": "contract", "stage": "AUTOMATED_TESTED"}
        self.edit_manifest(fn)
        self.assert_fail("MSC_UNIT_022")

    def test_78_f07_msc022_role_upgraded(self):
        def fn(m):
            for c in m["contracts"]:
                if c["msc_unit"] == "MSC_UNIT_022":
                    c["s0_role"] = "PRIMARY_CONTRACT_UNIT"
        self.edit_manifest(fn)
        self.assert_fail("MSC_UNIT_022")

    def test_79_f07_msc039_advanced_in_lifecycle(self):
        def fn(m):
            m["msc_stage_proposals"]["units"]["MSC_UNIT_039"] = {"portion": "contract", "stage": "AUTOMATED_TESTED"}
        self.edit_manifest(fn)
        self.assert_fail("MSC_UNIT_039")

    def test_80_f07_amendment_reasserts_no_other_unit_touched(self):
        self.mutate_clause(
            "S0-000-02",
            "It additionally freezes **one supporting contract entry**",
            "No other MSC unit is touched. It additionally mentions")
        self.assert_fail("S0-000-02")

    def test_81_f07_primary_unit_role_removed(self):
        def fn(m):
            for c in m["contracts"]:
                if c["msc_unit"] == "MSC_UNIT_028":
                    c["s0_role"] = "SUPPORTING_CONTRACT_ENTRY"
        self.edit_manifest(fn)
        self.assert_fail("MSC_UNIT_028")

    # -- F-08: evidence must not become authority --------------------------
    def test_82_f08_consolidation_restored_as_normative_home(self):
        self.edit_manifest(lambda m: m["client_contract_authority"]["CC-2"].__setitem__(
            "owner", "MASTER-SPECIALIST-CONSOLIDATION-001 CC-2"))
        self.assert_fail("non-authority evidence")

    def test_83_f08_coverage_gate_cited_as_authority(self):
        self.edit_manifest(lambda m: m["client_contract_authority"]["CC-12"].__setitem__(
            "owner", "SECURITY-REMEDIATION-COVERAGE-GATE-001"))
        self.assert_fail("non-authority evidence")

    def test_84_f08_authority_home_removed(self):
        self.edit_manifest(lambda m: m["client_contract_authority"]["CC-2"].pop("authority_home"))
        self.assert_fail("authority_home")

    # -- F-09: dangling internal references --------------------------------
    def test_85_f09_dangling_section_reference_reintroduced(self):
        self.mutate_clause("S0-018-03", "the **explicit reset path** of [S0-018-05]",
                           "the **explicit reset path** of §8.4")
        self.assert_fail("dangling internal section reference")

    def test_86_f09_dangling_reference_in_marker_states(self):
        self.mutate_clause("S0-033-01", "explicit reset path of [S0-018-05]/§9",
                           "explicit reset path of §8.4/§9")
        self.assert_fail("dangling internal section reference")

    # -- F-10: freeze-registry base pointers -------------------------------
    def test_87_f10_b002_base_pointer_removed(self):
        text = self.read(v.FREEZE_REGISTRY_PATH)
        self.write(v.FREEZE_REGISTRY_PATH, re.sub(
            r"^\| B-002 \|.*$",
            "| B-002 | Device Authentication | FROZEN v1.2-f04 (amended by B025_MANDATORY_AMENDMENTS_V1_4.md) | "
            "`docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md` |",
            text, flags=re.MULTILINE))
        self.assert_fail("lost its base-document pointer")

    def test_88_f10_b009_base_pointer_removed(self):
        text = self.read(v.FREEZE_REGISTRY_PATH)
        self.write(v.FREEZE_REGISTRY_PATH, re.sub(
            r"^\| B-009 \|.*$",
            "| B-009 | Local Messenger Database | FROZEN v1.5-f04 (amended by B025_MANDATORY_AMENDMENTS_V1_4.md) | "
            "`docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md` |",
            text, flags=re.MULTILINE))
        self.assert_fail("lost its base-document pointer")

    def test_89_f10_manifest_hides_amended_row(self):
        self.edit_manifest(lambda m: m.__setitem__(
            "freeze_registry_rows_referencing_v1_4", ["B-005"]))
        self.assert_fail("omits amended row")

    def test_90_f10_base_pointer_loss_not_hidden_by_manifest(self):
        # coherent tamper: hide the row in the manifest AND strip the base pointer
        self.edit_manifest(lambda m: m.__setitem__("freeze_registry_rows_referencing_v1_4", ["B-005"]))
        text = self.read(v.FREEZE_REGISTRY_PATH)
        self.write(v.FREEZE_REGISTRY_PATH, re.sub(
            r"^\| B-002 \|.*$",
            "| B-002 | Device Authentication | FROZEN v1.2-f04 (amended by B025_MANDATORY_AMENDMENTS_V1_4.md) | "
            "`docs/authority/B025_MANDATORY_AMENDMENTS_V1_4.md` |",
            text, flags=re.MULTILINE))
        self.assert_fail("lost its base-document pointer")

    # -- F-02: linked-worktree .git detection (fail-closed, never a silent SKIP)
    def test_91_f02_linked_worktree_pointer_executes_scope_gate(self):
        # A fixture whose .git is a worktree pointer file must run the scope
        # gate, not silently skip it (the historical .is_dir() weakness).
        # `--absolute-git-dir` is required: plain `--git-dir` returns the
        # relative ".git" in a normal repository, which the validator resolves
        # against the FIXTURE root (not the real repository) and correctly
        # rejects. Using the relative form made this test pass only inside a
        # linked worktree (retest finding B-5).
        gitdir = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=REPO_ROOT,
                                capture_output=True, text=True).stdout.strip()
        self.assertTrue(gitdir, "test requires a git context")
        self.assertTrue(Path(gitdir).is_absolute(), f"gitdir must be absolute, got {gitdir!r}")
        (Path(self.tmp) / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
        errors, out = run_validator(self.tmp)
        self.assertNotIn("fixture mode", out, "scope gate must not skip in a linked worktree")
        self.assertFalse(errors, f"valid linked-worktree gitdir must evaluate cleanly\n{out}")
        self.assertIn("protected shared changes ratified", out)
        # Era-aware: with Git resolvable, the S1 successor content must have been
        # admitted by the STRUCTURAL four-path transaction proof (R1 or R1+R2),
        # never by content identity alone.
        if self.central_era() == "s1_integration":
            self.assertIn("four-path ratification transaction proven", out)
            self.assertNotIn("fixture mode", out)

    def test_92_f02_malformed_worktree_pointer_fails_closed(self):
        for content in ("gitdir:\n", "not-a-pointer\n",
                        "gitdir: /nonexistent/definitely-missing\n",
                        "gitdir: a\ngitdir: b\n"):
            (Path(self.tmp) / ".git").write_text(content, encoding="utf-8")
            errors, out = run_validator(self.tmp)
            self.assertTrue(errors, f"malformed .git pointer {content!r} must fail closed\n{out}")
            self.assertIn("Git metadata unusable", out)
            self.assertNotIn("fixture mode", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
