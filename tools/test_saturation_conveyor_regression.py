#!/usr/bin/env python3
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONVEYOR = ROOT / "tools" / "saturation_conveyor.py"
WORKFLOW = ROOT / ".github" / "workflows" / "saturation-conveyor.yml"


class SaturationConveyorRegressionTests(unittest.TestCase):
    def setUp(self):
        self.source = CONVEYOR.read_text(encoding="utf-8")
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def test_promotion_order_is_monotonic(self):
        self.assertIn("PROMOTION=['P3','P4','P5','P6','P7','P8','P9','P10','P11']", self.source)

    def test_stage_promotion_requires_explicit_closed_marker(self):
        self.assertIn("return data.get('stage_gate') == 'CLOSED'", self.source)
        self.assertNotIn("if stage=='P9': return p.exists()", self.source)

    def test_p2_is_still_hard_gate(self):
        self.assertIn("state['critical_stage']='P2'", self.source)
        self.assertIn("P2_OPEN", self.source)

    def test_conveyor_is_scheduled_not_push_triggered(self):
        self.assertIn("cron: '*/5 * * * *'", self.workflow)
        self.assertNotIn("\n  push:", "\n" + self.workflow)

    def test_checkpoint_and_actions_read_permission(self):
        self.assertIn("actions: read", self.workflow)
        self.assertIn("saturation-conveyor-state", self.workflow)
        self.assertIn("automation/evidence/", self.workflow)
        self.assertIn("automation/universe/", self.workflow)

    def test_state_store_is_fail_closed(self):
        source = (ROOT / "tools" / "automation_state_store.py").read_text(encoding="utf-8")
        self.assertIn("return 2", source)
        self.assertIn("safe_member", source)
        self.assertIn("automation/saturation_state.json", source)

    def test_provenance_replay_requires_matching_observations(self):
        source = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('all(x["independent_observations"]>=2 and x["matching"] for x in result["transactions"])', source)

    def test_pair_snapshot_deduplicates_pair_addresses(self):
        source = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('by_address={str(x.get("pairAddress","")).lower():x for x in existing_pairs if x.get("pairAddress")}', source)
        self.assertIn('"new_unique_pairs"', source)

    def test_no_conveyor_subprocess_accepts_shell(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "run" and node.args:
                    self.assertFalse("shell=True" in ast.unparse(node))


if __name__ == "__main__":
    unittest.main()
