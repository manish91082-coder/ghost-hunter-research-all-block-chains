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

    def test_p3_closure_requires_multi_source_convergence_and_stability(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p3", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        base = {
            "checks": {
                "defillama_protocols_ok": True,
                "geckoterminal_dexes_ok": True,
            },
            "polygon_protocol_count": 10,
            "polygon_dex_protocol_count": 4,
            "geckoterminal_dex_count": 5,
            "dex_name_overlap_count": 3,
            "llama_duplicate_dex_names": 0,
            "gecko_duplicate_dex_names": 0,
            "universe_fingerprint": "abc",
        }

        self.assertFalse(
            module.p3_closure_ready(base, {"fingerprint": "xyz", "stable_runs": 4})
        )
        self.assertFalse(
            module.p3_closure_ready(base, {"fingerprint": "abc", "stable_runs": 0})
        )
        self.assertTrue(
            module.p3_closure_ready(base, {"fingerprint": "abc", "stable_runs": 1})
        )

    def test_p3_dex_duplicate_detection_uses_normalized_names(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p3_dupes", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        llama = [
            {"name": "QuickSwap", "chains": ["Polygon"], "category": "Dexs"},
            {"name": "QUICK-SWAP", "chains": ["Polygon"], "category": "Dexs"},
            {"name": "Uniswap", "chains": ["Polygon"], "category": "Dexs"},
        ]
        gecko = [
            {"attributes": {"name": "Quickswap"}},
            {"attributes": {"name": "Uniswap"}},
            {"attributes": {"name": "RamsesX"}},
        ]
        llama_set, gecko_set = module.p3_dex_sets(llama, gecko)
        self.assertEqual(len(llama_set), 3)
        self.assertIn("quickswap", llama_set)
        self.assertIn("uniswap", llama_set)
        self.assertIn("ramsesx", gecko_set)
        self.assertEqual(
            module.normalize_market_name("QuickSwap"),
            module.normalize_market_name("QUICKSWAP"),
        )

    def test_p3_closure_state_loader_has_safe_default(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p3_loader", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.load_json(ROOT / "does-not-exist-p3-state.json", {"stable_runs": 0}), {"stable_runs": 0})

    def test_p3_sources_and_closure_markers_are_present(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("https://api.geckoterminal.com/api/v2/networks/polygon_pos/dexes", worker)
        self.assertIn('snapshot["stage_gate"]', worker)
        self.assertIn('"CLOSED"', worker)
        self.assertIn("P3_CLOSURE_STATE.json", worker)


    def test_critical_stage_pauses_shadow_lane(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn("effective_shadow_limit = 0 if critical_open else args.max_shadow", source)
        self.assertIn("resume-safe and will automatically resume once the critical gate closes", source)

    def test_p4_parallel_rpc_and_larger_batch_are_locked(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P4_VERIFY_BATCH_SIZE = 48", worker)
        self.assertIn("P4_RPC_WORKERS = 3", worker)
        self.assertIn("ThreadPoolExecutor", worker)
        self.assertIn("as_completed", worker)
        self.assertIn('"rpc_workers": P4_RPC_WORKERS', worker)

    def test_p4_capability_aware_quorum_is_required(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("def _p4_select_capable_endpoints", worker)
        self.assertIn("max_endpoints=3", worker)
        self.assertIn('"selected_endpoints": selected_endpoints', worker)
        self.assertIn("Fewer than two independent semantically capable Polygon batch endpoints", worker)
        self.assertIn("import hashlib, json, os, time", worker)



    def test_p4_checkpoint_writer_uses_defined_writer(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertNotIn("save_json(P4_VERIFY_STATE", worker)
        self.assertIn("P4_VERIFY_STATE.write_text(", worker)
        self.assertIn('"transport": "json_rpc_batch"', worker)



    def test_p4_batch_transport_and_two_endpoint_quorum_are_explicit(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("json_rpc_batch", worker)
        self.assertIn("def _p4_rpc_batch_endpoint", worker)
        self.assertIn("for eid in selected_endpoints", worker)
        self.assertIn('"transport": "json_rpc_batch"', worker)


    def test_p4_verification_batch_is_bounded_and_skips_matches(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p4_batch", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        candidates = [f"0x{i:040x}" for i in range(50)]
        verification = {candidates[0]: {"matching": True}, candidates[2]: {"matching": True}}
        batch = module.p4_verification_batch(candidates, verification, batch_size=4)

        self.assertEqual(
            batch,
            [candidates[1], candidates[3], candidates[4], candidates[5]],
        )
        self.assertLessEqual(len(batch), 4)

    def test_p4_closure_requires_complete_verification_cycle(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p4_cycle", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        base = {
            "candidate_count": 8,
            "provider_overlap_count": 3,
            "duplicate_address_count": 0,
            "verified_token_count": 8,
            "chain_137_verified_count": 8,
            "identity_conflict_count": 0,
            "verification_cycle_complete": False,
            "universe_fingerprint": "abc",
            "checks": {
                "geckoterminal_top_pools_ok": True,
                "dexscreener_profiles_ok": True,
                "dexscreener_tokens_ok": True,
            },
        }
        self.assertFalse(module.p4_closure_ready(
            base,
            {"fingerprint": "abc", "stable_runs": 5, "verification_cycle_complete": True},
        ))



    def test_p4_helper_parses_gecko_and_dex_token_addresses(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p4_helpers", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        gecko = {
            "data": [{
                "id": "pool_polygon_pos_0x1111111111111111111111111111111111111111",
                "relationships": {
                    "base_token": {"data": {"id": "token_polygon_pos_0x2222222222222222222222222222222222222222"}},
                    "quote_token": {"data": {"id": "token_polygon_pos_0x3333333333333333333333333333333333333333"}},
                },
            }],
            "included": [{
                "type": "token",
                "id": "token_polygon_pos_0x4444444444444444444444444444444444444444",
                "attributes": {"address": "0x5555555555555555555555555555555555555555"},
            }],
        }
        got = module.extract_gecko_token_addresses(gecko)
        self.assertIn("0x2222222222222222222222222222222222222222", got)
        self.assertIn("0x3333333333333333333333333333333333333333", got)
        self.assertIn("0x4444444444444444444444444444444444444444", got)
        self.assertIn("0x5555555555555555555555555555555555555555", got)

        dex = [{
            "chainId": "polygon",
            "baseToken": {"address": "0x6666666666666666666666666666666666666666"},
            "quoteToken": {"address": "0x7777777777777777777777777777777777777777"},
        }]
        self.assertEqual(
            module.extract_dex_token_addresses(dex),
            [
                "0x6666666666666666666666666666666666666666",
                "0x7777777777777777777777777777777777777777",
            ],
        )

    def test_p4_closure_requires_verified_multisource_stable_universe(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p4_gate", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        base = {
            "candidate_count": 8,
            "provider_overlap_count": 3,
            "duplicate_address_count": 0,
            "verified_token_count": 8,
            "chain_137_verified_count": 8,
            "identity_conflict_count": 0,
            "verification_cycle_complete": True,
            "universe_fingerprint": "abc",
            "checks": {
                "geckoterminal_top_pools_ok": True,
                "dexscreener_profiles_ok": True,
                "dexscreener_tokens_ok": True,
            },
        }
        self.assertFalse(module.p4_closure_ready(base, {"fingerprint": "xyz", "stable_runs": 1}))
        self.assertFalse(module.p4_closure_ready(base, {"fingerprint": "abc", "stable_runs": 0}))
        self.assertTrue(module.p4_closure_ready(base, {"fingerprint": "abc", "stable_runs": 1, "verification_cycle_complete": True}))

    def test_p4_gate_is_explicitly_written_by_worker(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P4_CLOSURE_STATE.json", worker)
        self.assertIn('snapshot["stage_gate"] = "CLOSED"', worker)
        self.assertIn("p4_closure_ready", worker)
        self.assertIn("eth_getCode", worker)
        self.assertIn("0x313ce567", worker)
        self.assertIn("0x18160ddd", worker)


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

    def test_commit_signal_is_reported_ephemerally(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn("commit_required = (", source)
        self.assertIn("state['commit_required']=False", source)
        self.assertIn("'commit_required':commit_required", source)


    def test_stage_metadata_tracks_closed_and_current_stages(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("saturation_conveyor_stage_sync", CONVEYOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        state = {
            "critical_stage": "P4",
            "research_gate": "P2_CLOSED",
            "stages": {},
        }
        module.sync_stage_metadata(state)

        self.assertEqual(state["stages"]["P2"]["status"], "CLOSED")
        self.assertEqual(state["stages"]["P3"]["status"], "CLOSED")
        self.assertEqual(state["stages"]["P4"]["status"], "OPEN")
        self.assertEqual(state["stages"]["P4"]["mode"], "CRITICAL")
        self.assertEqual(state["stages"]["P5"]["status"], "PREPARE")
        self.assertEqual(state["stages"]["P11"]["status"], "LOCKED")


    def test_p4_revision_resets_stale_cooldown(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('"P4":"p4-batched-verification-v2"', source)

    def test_p3_revision_resets_stale_cooldown(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('TASK_REVISIONS={"P3":"p3-multisource-closure-v1","P4":"p4-batched-verification-v2"}', source)
        self.assertIn("or (revision and ts.get('revision') != revision)", source)
        self.assertIn("ts['revision']=revision", source)


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
