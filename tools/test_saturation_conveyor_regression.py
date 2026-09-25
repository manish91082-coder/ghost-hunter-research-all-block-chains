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

    def test_conveyor_heartbeat_and_bootstrap_trigger_are_narrow(self):
        self.assertIn("cron: '2-59/5 * * * *'", self.workflow)
        self.assertIn("  push:\n    paths:\n      - 'automation/conveyor_bootstrap.trigger'", self.workflow)
        push_block = self.workflow.split("  push:\n", 1)[1].split("concurrency:\n", 1)[0]
        self.assertNotIn("tools/saturation_conveyor.py", push_block)

    def test_checkpoint_and_actions_read_permission(self):
        self.assertIn("actions: read", self.workflow)
        self.assertIn("saturation-conveyor-state", self.workflow)
        self.assertIn("automation/evidence/", self.workflow)
        self.assertIn("automation/universe/", self.workflow)

    def test_state_store_uses_runner_native_artifact_restore(self):
        source = (ROOT / "tools" / "automation_state_store.py").read_text(encoding="utf-8")
        self.assertIn('"gh", "run", "list"', source)
        self.assertIn('"gh", "run", "download"', source)
        self.assertIn("safe_member", source)
        self.assertIn("automation/saturation_state.json", source)

    def test_provenance_replay_requires_matching_observations(self):
        source = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('all(x["independent_observations"]>=2 and x["matching"] for x in result["transactions"])', source)

    def test_shadow_dependency_override_backfills_empty_queues(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('if task=="P5" and not Path("automation/universe/tokens.jsonl").exists()', source)
        self.assertIn('if task=="P6" and not Path("automation/universe/pairs.jsonl").exists()', source)

    def test_pair_snapshot_deduplicates_pair_addresses(self):
        source = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('by_address={str(x.get("pairAddress","")).lower():x for x in existing_pairs if x.get("pairAddress")}', source)
        self.assertIn('"new_unique_pairs"', source)

    def test_jsonl_recovery_and_real_newlines_are_present(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('for chunk in line.split("\\\\n"):', worker)
        self.assertIn('json.dumps(x,sort_keys=True)+"\\n"', worker)

    def test_polygon_seed_manifest_and_pair_expansion_are_present(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        seed = (ROOT / "chains" / "polygon-pos" / "p4_seed_tokens.txt").read_text(encoding="utf-8")
        self.assertIn("polygon_seed_manifest", worker)
        self.assertIn("dexscreener_pair_token", worker)
        self.assertIn("0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", seed)
        self.assertIn("0xc2132D05D31c914a87C6611C10748AEb04B58e8F", seed)

    def test_no_conveyor_subprocess_accepts_shell(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "run" and node.args:
                    self.assertFalse("shell=True" in ast.unparse(node))


if __name__ == "__main__":
    unittest.main()
