#!/usr/bin/env python3
"""Adversarial tests for B-028 seal_event.py — fail-closed chain integrity."""

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import seal_event


def make_event(n, **kw):
    ev = {
        "event_id": f"ANOX-EVENT-{n:04d}",
        "date": "2026-10-01",
        "type": "canonical_merge",
        "task": "ANOX-TASK-X-001",
        "summary": f"event {n}",
        "status": "merged",
        "start_head": "a" * 40,
        "end_head": "b" * 40,
        "merge_head": "c" * 40,
        "gate_after": "NEXT",
        "findings": [], "tests": {}, "refs": [], "evidence": ["canonical-merge"],
    }
    ev.update(kw)
    return ev


class LedgerFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self.tmp.name) / "ledger.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, records):
        self.ledger.write_text("".join(json.dumps(r) + "\n" for r in records),
                               encoding="utf-8")

    def chain(self, n):
        records = [make_event(1)]
        for i in range(2, n + 1):
            ev = make_event(i, prev_event_hash=seal_event.record_hash(records[-1]))
            records.append(ev)
        return records


class VerifyTests(LedgerFixture):
    def test_genesis_no_chain_field_passes(self):
        self.write([make_event(1)])
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertTrue(ok, problems)

    def test_valid_chain_passes(self):
        self.write(self.chain(4))
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertTrue(ok, problems)

    def test_tampered_record_breaks_chain(self):
        records = self.chain(3)
        records[1]["summary"] = "tampered"
        self.write(records)
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertFalse(ok)
        self.assertTrue(any("prev_event_hash mismatch" in p for p in problems))

    def test_missing_chain_field_after_anchor_fails(self):
        records = self.chain(3)
        del records[2]["prev_event_hash"]
        self.write(records)
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertFalse(ok)
        self.assertTrue(any("missing/malformed prev_event_hash" in p for p in problems))

    def test_duplicate_event_id_fails(self):
        self.write([make_event(1), make_event(1)])
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertFalse(ok)
        self.assertTrue(any("duplicate event_id" in p for p in problems))

    def test_nonmonotonic_sequence_fails(self):
        records = self.chain(2)
        records[1]["event_id"] = "ANOX-EVENT-0001"
        records[1]["prev_event_hash"] = seal_event.record_hash(records[0])
        self.write(records)
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertFalse(ok)
        self.assertTrue(any("non-monotonic" in p or "duplicate" in p for p in problems))

    def test_gap_sequence_detected_as_hash_break(self):
        # Dropping a middle record breaks the hash chain.
        records = self.chain(3)
        records = [records[0], records[2]]
        self.write(records)
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertFalse(ok)
        self.assertTrue(any("mismatch" in p for p in problems))

    def test_malformed_json_fails(self):
        self.ledger.write_text("{bad json\n", encoding="utf-8")
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertFalse(ok)

    def test_empty_ledger_fails(self):
        self.write([])
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertFalse(ok)

    def test_genesis_with_chain_field_fails(self):
        self.write([make_event(1, prev_event_hash="0" * 64)])
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertFalse(ok)

    def test_full_chain_required_rejects_unchained(self):
        self.write([make_event(1), make_event(2)])
        ok, problems = seal_event.verify_ledger(self.ledger, require_full_chain=True)
        self.assertFalse(ok)


class SealTests(LedgerFixture):
    FIELDS = {"date": "2026-10-02", "type": "governance_transition",
              "task": "ANOX-TASK-B028-001", "summary": "seal test",
              "status": "sealed", "start_head": "d" * 40,
              "end_head": "e" * 40, "merge_head": None,
              "gate_after": "NEXT", "findings": [], "tests": {},
              "refs": [], "evidence": []}

    def test_seal_appends_next_id_with_hash(self):
        self.write([make_event(1)])
        ev, problems = seal_event.seal(self.ledger, dict(self.FIELDS), "ANOX-DECISION-X")
        self.assertEqual(problems, [])
        self.assertEqual(ev["event_id"], "ANOX-EVENT-0002")
        self.assertEqual(ev["prev_event_hash"], seal_event.record_hash(self.chain(1)[0]))
        self.assertIn("decision:ANOX-DECISION-X", ev["refs"])
        ok, problems = seal_event.verify_ledger(self.ledger)
        self.assertTrue(ok, problems)

    def test_seal_refuses_broken_existing_chain(self):
        records = self.chain(2)
        records[0]["summary"] = "tampered"
        self.write(records)
        ev, problems = seal_event.seal(self.ledger, dict(self.FIELDS), "D")
        self.assertIsNone(ev)
        self.assertTrue(any("refusing to extend" in p for p in problems))

    def test_seal_dry_run_writes_nothing(self):
        self.write([make_event(1)])
        before = self.ledger.read_bytes()
        ev, problems = seal_event.seal(self.ledger, dict(self.FIELDS), "D", dry_run=True)
        self.assertEqual(problems, [])
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_seal_bad_type_fails(self):
        self.write([make_event(1)])
        fields = dict(self.FIELDS, type="invented_type")
        ev, problems = seal_event.seal(self.ledger, fields, "D")
        self.assertIsNone(ev)
        self.assertTrue(any("type must be" in p for p in problems))

    def test_seal_bad_sha_fails(self):
        self.write([make_event(1)])
        fields = dict(self.FIELDS, start_head="notasha")
        ev, problems = seal_event.seal(self.ledger, fields, "D")
        self.assertIsNone(ev)
        self.assertTrue(any("start_head" in p for p in problems))

    def test_event_id_uses_max_not_count(self):
        # Reserved/skipped ids must not collide: max+1, not len+1.
        self.write([make_event(1), make_event(10,
                    prev_event_hash=seal_event.record_hash(make_event(1)))])
        self.assertEqual(seal_event.next_event_id(seal_event.load_ledger(self.ledger)),
                         "ANOX-EVENT-0011")


class FieldValidationTests(unittest.TestCase):
    def test_missing_required_field(self):
        ev = make_event(1)
        del ev["summary"]
        problems = seal_event.validate_event_fields(ev)
        self.assertTrue(any("summary" in p for p in problems))

    def test_bad_date(self):
        problems = seal_event.validate_event_fields(make_event(1, date="01.01.2026"))
        self.assertTrue(any("date" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
