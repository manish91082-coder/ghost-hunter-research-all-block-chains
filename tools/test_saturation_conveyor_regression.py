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

    def test_critical_lane_skips_already_closed_tasks_and_runs_two(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn("def critical_task_complete(task, state):", source)
        self.assertIn("if critical_task_complete(task, state):", source)
        self.assertIn("--max-critical 2", self.workflow)

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

    def test_provenance_requires_complete_transaction_and_receipt(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_complete", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        ok_tx = {"ok": True, "body": {"result": {"hash": "0xabc"}}}
        ok_receipt = {"ok": True, "body": {"result": {"status": "0x1"}}}
        null_tx = {"ok": True, "body": {"result": None}}
        rpc_error = {"ok": False, "body": {"error": {"code": -32000}}}

        self.assertTrue(module.complete_provenance_observation(ok_tx, ok_receipt))
        self.assertFalse(module.complete_provenance_observation(null_tx, ok_receipt))
        self.assertFalse(module.complete_provenance_observation(ok_tx, rpc_error))


    def test_provenance_replay_has_bounded_recovery(self):
        source = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("recovery_rounds=2", source)
        self.assertIn("for recovery_round in range(1,recovery_rounds + 1):", source)
        self.assertIn("cooldown_until", source)
        self.assertIn('"endpoint_diagnostics"', source)


    def test_provenance_fingerprint_excludes_rpc_transport_metadata(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        a = {"rpc": "tatum", "tx": {"hash": "0xabc", "blockNumber": "0x10"}, "receipt": {"status": "0x1", "logs": []}}
        b = {"rpc": "quicknode-public", "tx": {"hash": "0xabc", "blockNumber": "0x10"}, "receipt": {"status": "0x1", "logs": []}}
        c = {"rpc": "quicknode-public", "tx": {"hash": "0xdef", "blockNumber": "0x10"}, "receipt": {"status": "0x1", "logs": []}}
        self.assertEqual(module.provenance_fingerprint(a), module.provenance_fingerprint(b))
        self.assertNotEqual(module.provenance_fingerprint(a), module.provenance_fingerprint(c))

    def test_control_reconciliation_is_fail_closed(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn("Reconciliation skipped because live verifier did not produce a valid observation set", source)

    def test_shadow_lane_prioritizes_earliest_missing_work(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('if not checks[1][1]:', source)
        self.assertIn('if not checks[2][1]:', source)
        self.assertIn('if int(load_json(p6,{}).get("pair_nodes",0)) <= 0:', source)

    def test_code_epoch_resets_stale_cooldowns_after_fixes(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn("def current_code_epoch():", source)
        self.assertIn("if ts.get('code_epoch') != epoch:", source)
        self.assertIn("ts['cooldown_until']=0", source)

    def test_shadow_dependency_override_backfills_empty_queues(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('if not checks[1][1]:', source)
        self.assertIn('if not checks[2][1]:', source)
        self.assertIn('if int(load_json(p6,{}).get("pair_nodes",0)) <= 0:', source)

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
