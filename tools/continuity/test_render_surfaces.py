#!/usr/bin/env python3
"""Adversarial tests for B-028 render_surfaces.py — drift and fail-closed."""

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_surfaces


BASE_STATE = {
    "canonical_branch": "main",
    "delivery_branch": "governance/test-001",
    "described_head": "a" * 40,
    "pre_merge_gate": "PRE GATE TEXT",
    "post_merge_gate": "POST GATE TEXT",
    "current_gate": "__EFFECTIVE_GATE__",
    "latest_material_event_id": "ANOX-EVENT-0066",
    "latest_merge_to_baseline": "b" * 40,
}


class MarkerTests(unittest.TestCase):
    def setUp(self):
        self.markers = {
            "__EFFECTIVE_GATE__": "PRE GATE TEXT",
            "__HANDOFF_BRANCH__": "governance/test-001",
            "__HANDOFF_HEAD__": "a" * 40,
            "__WORKING_TREE__": "CLEAN",
            "__CANONICAL_BASE__": "b" * 40,
            "__DESCRIBED_HEAD__": "a" * 40,
            "__DELIVERY_BRANCH__": "governance/test-001",
            "__LATEST_EVENT__": "ANOX-EVENT-0066",
            "__PRE_MERGE_GATE__": "PRE GATE TEXT",
            "__POST_MERGE_GATE__": "POST GATE TEXT",
        }

    def test_all_markers_resolve(self):
        text = "gate: __EFFECTIVE_GATE__\nbase: __CANONICAL_BASE__\nevt: __LATEST_EVENT__"
        out = render_surfaces.render_text(text, self.markers)
        self.assertIn("gate: PRE GATE TEXT", out)
        self.assertIn("base: " + "b" * 40, out)
        self.assertIn("evt: ANOX-EVENT-0066", out)

    def test_unresolved_known_marker_fails(self):
        # A marker absent from the map must fail closed, not be left in place.
        markers = dict(self.markers)
        del markers["__CANONICAL_BASE__"]
        with self.assertRaises(render_surfaces.RenderError):
            render_surfaces.render_text("x __CANONICAL_BASE__ y", markers)

    def test_unknown_marker_fails_closed(self):
        with self.assertRaises(render_surfaces.RenderError):
            render_surfaces.render_text("x __INVENTED_FIELD__ y", self.markers)

    def test_clean_text_passes(self):
        self.assertEqual(render_surfaces.render_text("no markers", self.markers),
                         "no markers")


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs/continuity").mkdir(parents=True)
        (self.root / "docs/workforce").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, state=None, wf=None):
        state = state or dict(BASE_STATE)
        wf = wf or {"described_head": state["described_head"]}
        (self.root / render_surfaces.STATE_PATH).write_text(json.dumps(state))
        (self.root / render_surfaces.WORKFORCE_PATH).write_text(json.dumps(wf))

    def test_offline_delivery_branch_gives_pre_gate(self):
        self._write()
        m = render_surfaces.resolve_markers(self.root, live_git=False)
        self.assertEqual(m["__EFFECTIVE_GATE__"], "PRE GATE TEXT")
        self.assertEqual(m["__HANDOFF_BRANCH__"], "governance/test-001")

    def test_workforce_described_head_mismatch_fails(self):
        self._write(wf={"described_head": "f" * 40})
        with self.assertRaises(render_surfaces.RenderError):
            render_surfaces.resolve_markers(self.root, live_git=False)

    def test_missing_state_field_fails(self):
        state = dict(BASE_STATE)
        del state["pre_merge_gate"]
        self._write(state=state)
        with self.assertRaises(render_surfaces.RenderError):
            render_surfaces.resolve_markers(self.root, live_git=False)

    def test_unparsable_state_json_fails(self):
        (self.root / render_surfaces.STATE_PATH).write_text("{bad")
        (self.root / render_surfaces.WORKFORCE_PATH).write_text("{}")
        with self.assertRaises(render_surfaces.RenderError):
            render_surfaces.resolve_markers(self.root, live_git=False)


class DriftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.surface = self.root / "SURFACE.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_drift_detected_in_check_mode(self):
        self.surface.write_text("gate: STALE VALUE")
        markers = {"__EFFECTIVE_GATE__": "PRE GATE TEXT"}
        rel = "SURFACE.md"
        _, status, _ = render_surfaces.process_file(self.root, rel, markers, write=False)
        self.assertIn(status, ("MATCH", "DRIFT", "RENDERED", "FAIL"))
        # "STALE VALUE" contains no marker -> identical render -> MATCH.
        self.surface.write_text("gate: __EFFECTIVE_GATE__")
        _, status, detail = render_surfaces.process_file(self.root, rel, markers, write=False)
        self.assertEqual(status, "DRIFT", detail)

    def test_write_mode_rewrites(self):
        self.surface.write_text("gate: __EFFECTIVE_GATE__")
        markers = {"__EFFECTIVE_GATE__": "PRE GATE TEXT"}
        _, status, _ = render_surfaces.process_file(self.root, "SURFACE.md", markers, write=True)
        self.assertEqual(status, "RENDERED")
        self.assertIn("PRE GATE TEXT", self.surface.read_text())


if __name__ == "__main__":
    unittest.main()
