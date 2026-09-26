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

    def test_checkpoint_and_actions_write_permission(self):
        self.assertIn("actions: write", self.workflow)
        self.assertIn("gh workflow run saturation-conveyor.yml --ref main", self.workflow)
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
            "stable_runs": 1,
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
        self.assertIn("P4_RPC_WORKERS = 6", worker)
        self.assertIn("ThreadPoolExecutor", worker)
        self.assertIn("as_completed", worker)
        self.assertIn('"rpc_workers": P4_RPC_WORKERS', worker)

    def test_p4_capability_probe_falls_back_to_single_rpc_calls(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("except ValueError:", worker)
        self.assertIn("rows = _p4_rpc_single_calls(pool, endpoint_id, calls, timeout=30)", worker)

    def test_checkpoint_restore_ignores_failed_runs(self):
        source = (ROOT / "tools" / "automation_state_store.py").read_text(encoding="utf-8")
        self.assertIn('and r.get("conclusion") == "success"', source)

    def test_checkpoint_restore_supports_p4_fanout_workflow(self):
        source = (ROOT / "tools" / "automation_state_store.py").read_text(encoding="utf-8")
        self.assertIn('"p4-rpc-fanout.yml"', source)

    def test_p4_identity_fingerprint_excludes_dynamic_total_supply(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('semantic_fingerprints = {(x["code_hash"], x["decimals"]) for x in observations}', worker)
        self.assertIn('"semantic_fingerprint_fields": ["code_hash", "decimals"]', worker)
        self.assertIn('"dynamic_state_note": "totalSupply is dynamic state and is not an identity conflict"', worker)
        self.assertIn('"total_supply_equal": len(total_supply_values) <= 1', worker)

    def test_p4_has_adaptive_429_chunk_backoff(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("class P4RateLimitedError", worker)
        self.assertIn("P4_RPC_MIN_CHUNK_TOKENS = 1", worker)
        self.assertIn("chunk_size = max(P4_RPC_MIN_CHUNK_TOKENS, chunk_size // 2)", worker)
        self.assertIn("_p4_rpc_single_calls(pool, eid, calls, timeout=30)", worker)

    def test_p4_uses_low_risk_capability_probe_and_micro_batches(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P4_RPC_MIN_INTERVAL = 1.0", worker)
        self.assertIn("P4_RPC_CHUNK_TOKENS = 12", worker)
        self.assertIn("return seeds[:1]", worker)
        self.assertIn("while offset < len(batch):", worker)

    def test_p4_has_bounded_429_recovery_and_batch_fallback(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P4_CHAIN_RECOVERY_ROUNDS = 2", worker)
        self.assertIn("P4_RECOVERY_WAIT_MAX = 60", worker)
        self.assertIn('if obs.get("http_status") == 429 or obs.get("rate_limited")', worker)
        self.assertIn("except P4RateLimitedError as exc:", worker)
        self.assertIn("rows = _p4_rpc_single_calls", worker)

    def test_p4_pool_order_is_normalized_to_endpoint_ids(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('candidates = [item["id"] for item in pool.ordered()[:max_endpoints]]', worker)

    def test_p4_rpc_pool_expands_and_scan_cap_covers_candidates(self):
        pool = (ROOT / "chains" / "polygon-pos" / "rpc_pool.txt").read_text(encoding="utf-8")
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("lava|https://polygon.lava.build", pool)
        self.assertIn("subquery|https://polygon.rpc.subquery.network/public", pool)
        self.assertIn("zan|https://api.zan.top/polygon-mainnet", pool)
        self.assertIn("tenderly-gateway|https://polygon.gateway.tenderly.co", pool)
        self.assertIn("P4_ENDPOINT_SCAN_MAX = 18", worker)

    def test_p4_scans_multiple_rpc_candidates_in_parallel(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P4_ENDPOINT_SCAN_MAX = 18", worker)
        self.assertIn("def _p4_discover_chain_endpoints", worker)
        self.assertIn('"chain_probe": chain_probe', worker)
        self.assertIn("P4_RPC_WORKERS = 6", worker)

    def test_p4_capability_aware_quorum_is_required(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("def _p4_select_capable_endpoints", worker)
        self.assertIn("max_endpoints=3", worker)
        self.assertIn('"selected_endpoints": selected_endpoints', worker)
        self.assertIn("Fewer than two independent semantically capable Polygon batch endpoints", worker)



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



    def test_gecko_token_extractor_rejects_pool_resource_ids(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_gecko_filter", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        token_a = "0x1111111111111111111111111111111111111111"
        token_b = "0x2222222222222222222222222222222222222222"
        pool = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        payload = {
            "data": [{
                "type": "pool",
                "id": pool,
                "relationships": {
                    "base_token": {"data": {"type": "token", "id": f"token_polygon_pos_{token_a}"}},
                    "quote_token": {"data": {"type": "token", "id": f"token_polygon_pos_{token_b}"}},
                },
            }],
            "included": [
                {"type": "token", "id": f"token_polygon_pos_{token_a}", "attributes": {"address": token_a}},
                {"type": "token", "id": f"token_polygon_pos_{token_b}", "attributes": {"address": token_b}},
            ],
        }
        result = module.extract_gecko_token_addresses(payload)
        self.assertEqual(result, sorted([token_a, token_b]))
        self.assertNotIn(pool, result)

    def test_p5_token_eligibility_ignores_stale_noneligible_rows(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p5_eligibility", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertFalse(module.p5_token_eligible({"address": "0x1", "source": "geckoterminal_top_pools", "p5_scan_eligible": False}))
        self.assertTrue(module.p5_token_eligible({"address": "0x2", "evidence_class": "ONCHAIN_SEMANTIC"}))
        self.assertTrue(module.p5_token_eligible({"address": "0x3", "source": "polygon_seed_manifest"}))
        self.assertTrue(module.p5_token_eligible({"address": "0x3", "source": "dexscreener_pair_token"}))

    def test_p5_duplicate_observations_do_not_equal_identity_conflict(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p5_identity", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        a = {
            "pairAddress": "0x1111111111111111111111111111111111111111",
            "chainId": "polygon",
            "baseToken": {"address": "0x2222222222222222222222222222222222222222"},
            "quoteToken": {"address": "0x3333333333333333333333333333333333333333"},
            "dexId": "quickswap",
        }
        b = dict(a)
        self.assertEqual(module.p5_pair_identity(a), module.p5_pair_identity(b))

    def test_p5_parallel_batch_is_bounded_and_fast(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P5_PAIR_BATCH_SIZE = 120", worker)
        self.assertIn("P5_PAIR_WORKERS = 12", worker)


    def test_p5_stability_state_writer_is_defined_in_worker(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertNotIn("save_json(", worker)
        self.assertIn("P5_STABILITY_STATE.write_text(", worker)


    def test_p5_schema_migration_does_not_reuse_old_closure_baseline(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("stability_schema_compatible", worker)
        self.assertIn("stability_schema_compatible\n        and not baseline_fp", worker)

    def test_p5_fingerprint_uses_merged_pair_universe_not_current_batch(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p5_fp", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        eligible = [{"address": "0x1111111111111111111111111111111111111111"}]
        pair = {
            "pairAddress": "0x2222222222222222222222222222222222222222",
            "chainId": "polygon",
            "baseToken": {"address": "0x1111111111111111111111111111111111111111"},
            "quoteToken": {"address": "0x3333333333333333333333333333333333333333"},
            "dexId": "quickswap",
        }
        fp1, conflicts1 = module.p5_pair_universe_fingerprint(eligible, [pair])
        fp2, conflicts2 = module.p5_pair_universe_fingerprint(eligible, [dict(pair)])
        self.assertEqual(fp1, fp2)
        self.assertEqual(conflicts1, 0)
        self.assertEqual(conflicts2, 0)

    def test_p5_stability_baseline_persists_across_partial_runs(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P5_STABILITY_STATE = EVID / \"P5_STABILITY_STATE.json\"", worker)
        self.assertIn("baseline_fingerprint", worker)
        self.assertIn("if not baseline_fp", worker)
        self.assertIn("stability_processed_addresses", worker)

    def test_p5_stability_recheck_is_chunked_and_rate_limit_aware(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P5_STABILITY_WORKERS = 4", worker)
        self.assertIn("stability_processed_addresses", worker)
        self.assertIn("P5_REQUEST_RETRIES = 3", worker)
        self.assertIn('if err and "429" in str(err)', worker)

    def test_p5_checkpoint_uses_processed_addresses_not_integer_cursor(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("processed_addresses", worker)
        self.assertIn("successful_addresses", worker)
        self.assertIn("recheck_mode", worker)


    def test_p5_closure_uses_current_snapshot_stability(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p5_gate", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        snapshot = {
            "coverage_complete": True,
            "stable_runs": 1,
            "duplicate_pair_observation_count": 0,
            "pair_identity_conflict_count": 0,
            "total_pair_records": 10,
            "universe_fingerprint": "abc",
            "checks": {
                "source_requests_complete": True,
                "eligible_token_universe_nonempty": True,
            },
        }
        self.assertTrue(module.p5_closure_ready(
            snapshot,
            {"fingerprint": "abc", "coverage_complete": True, "stable_runs": 0},
        ))

    def test_p5_closure_requires_complete_stable_pair_universe(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p5_closure", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        snapshot = {
            "coverage_complete": True,
            "stable_runs": 1,
            "duplicate_pair_count": 0,
            "total_pair_records": 10,
            "universe_fingerprint": "abc",
            "checks": {
                "source_requests_complete": True,
                "eligible_token_universe_nonempty": True,
            },
        }
        self.assertFalse(module.p5_closure_ready(
            snapshot,
            {"fingerprint": "abc", "stable_runs": 0, "coverage_complete": False},
        ))
        snapshot["pair_identity_conflict_count"] = 0
        self.assertTrue(module.p5_closure_ready(
            snapshot,
            {"fingerprint": "abc", "stable_runs": 1, "coverage_complete": True},
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
        self.assertIn('"P4":"p4-parallel-endpoint-discovery-v3"', source)

    def test_p3_revision_resets_stale_cooldown(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('"P3":"p3-multisource-closure-v1"', source)
        self.assertIn('"P4":"p4-parallel-endpoint-discovery-v3"', source)
        self.assertIn('"P5":"p5-closure-contract-v4"', source)
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

    def test_p5_parallel_closure_revision_is_registered(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('"P5":"p5-closure-contract-v4"', source)

    def test_pair_snapshot_deduplicates_pair_addresses(self):
        source = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('by_address = {', source)
        self.assertIn('x.get("pairAddress")', source)
        self.assertIn('"new_unique_pairs"', source)

    def test_jsonl_recovery_and_real_newlines_are_present(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('for chunk in line.split("\\\\n"):', worker)
        self.assertTrue(
            'json.dumps(row, sort_keys=True) + "\\n"' in worker
            or 'json.dumps(x,sort_keys=True)+"\\n"' in worker
        )

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





    def test_p6_route_closure_requires_matching_complete_graph_recheck(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p6_gate", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        snapshot = {
            "pair_nodes": 4,
            "unique_pairs": 6,
            "graph_fingerprint": "abc",
            "stable_runs": 1,
            "route_enumeration_complete": True,
            "checks": {
                "p5_pair_universe_aligned": True,
                "all_pair_records_consumed": True,
                "no_invalid_pair_records": True,
                "route_enumeration_complete": True,
            },
        }
        self.assertFalse(module.p6_route_closure_ready(
            snapshot,
            {"fingerprint": "abc", "stable_runs": 0, "route_enumeration_complete": False},
        ))
        self.assertTrue(module.p6_route_closure_ready(
            snapshot,
            {"fingerprint": "abc", "stable_runs": 1, "route_enumeration_complete": True},
        ))


    def test_p6_route_enumeration_uses_full_graph_not_hidden_sampling_caps(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("for token in sorted(adj):", worker)
        self.assertIn("route_count_total", worker)
        self.assertIn("P6_ROUTE_STORAGE_LIMIT = 5000", worker)
        self.assertNotIn("list(adj)[:200]", worker)
        self.assertNotIn("adj.get(node,[])[:100]", worker)


    def test_p6_worker_writes_explicit_closure_state_and_stage_gate(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('P6_CLOSURE_STATE = EVID / "P6_CLOSURE_STATE.json"', worker)
        self.assertIn("def p6_route_closure_ready(", worker)
        self.assertIn('snapshot["stage_gate"] = "CLOSED"', worker)
        self.assertIn('"route_enumeration_complete": True', worker)


    def test_p6_revision_resets_stale_cooldown(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('"P6":"p6-route-closure-v1"', source)





    def test_p7_strategy_matrix_has_exact_18_family_set_and_required_schema(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        expected = [
            "dex_dex","intra_dex","triangular","multi_hop","split","flash_loan",
            "liquidation","backrun","orderflow_mev","intent_rfq_filler",
            "solver_relayer","liquidity_state_transition","cross_domain",
            "statistical_temporal","gas_regime","failed_tx_retry_state",
            "protocol_structural","negative_space_hypothesis",
        ]
        for strategy in expected:
            self.assertIn('"' + strategy + '"', worker)
        for field in [
            '"mechanism"',
            '"prerequisites"',
            '"exact_contracts"',
            '"state_dependencies"',
            '"cost_model"',
            '"failure_modes"',
            '"competition_model"',
            '"simulation_method"',
            '"historical_evidence"',
            '"live_shadow_evidence"',
            '"profitability_status"',
            '"confidence"',
            '"unknowns"',
        ]:
            self.assertIn(field, worker)


    def test_p7_closure_requires_stable_complete_matrix(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p7_gate", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        row = {
            "strategy_id": module.STRATEGIES[0],
            "mechanism": {"status": "HYPOTHESIS_ONLY"},
            "prerequisites": {"status": "UNRESOLVED"},
            "exact_contracts": {"status": "NOT_IDENTIFIED"},
            "state_dependencies": {"status": "UNRESOLVED"},
            "cost_model": {"status": "NOT_CERTIFIED"},
            "failure_modes": {"status": "UNRESOLVED"},
            "competition_model": {"status": "UNRESOLVED"},
            "simulation_method": {"status": "EXACT_SIMULATION_REQUIRED"},
            "historical_evidence": {"status": "NOT_COLLECTED"},
            "live_shadow_evidence": {"status": "NOT_COLLECTED"},
            "profitability_status": "NOT_CERTIFIED",
            "confidence": {"level": "LOW"},
            "unknowns": ["x"],
            "status": "RESEARCH_CANDIDATE_UNRESOLVED",
        }
        snapshot = {
            "strategy_count": len(module.STRATEGIES),
            "matrix_fingerprint": "abc",
            "stable_runs": 1,
            "matrix_complete": True,
            "checks": {
                "p6_route_source_closed": True,
                "strategy_set_complete": True,
                "unique_strategy_ids": True,
                "required_fields_complete": True,
                "unresolved_fields_explicit": True,
            },
        }
        self.assertFalse(module.p7_strategy_closure_ready(
            snapshot, {"fingerprint": "abc", "stable_runs": 0, "matrix_complete": False}
        ))
        self.assertTrue(module.p7_strategy_closure_ready(
            snapshot, {"fingerprint": "abc", "stable_runs": 1, "matrix_complete": True}
        ))


    def test_p7_revision_resets_stale_cooldown(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('"P7":"p7-strategy-matrix-v2"', source)





    def test_p8_feature_schema_and_explicit_unavailable_domains(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        for field in [
            '"spread"',
            '"volatility"',
            '"volume"',
            '"liquidity"',
            '"imbalance"',
            '"regime"',
            '"momentum_reversion"',
            '"route_recurrence"',
            '"opportunity_persistence"',
            '"gas_regime"',
            '"block_activity"',
            '"flow_toxicity_proxy"',
        ]:
            self.assertIn(field, worker)
        self.assertIn('P8_FEATURE_SCHEMA_VERSION = "p8-feature-matrix-v2"', worker)
        self.assertIn('"NOT_AVAILABLE"', worker)
        self.assertIn('"NOT_CLASSIFIED"', worker)


    def test_p8_closure_requires_stable_complete_feature_matrix(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p8_gate", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        snapshot = {
            "pair_groups": 10,
            "feature_fingerprint": "abc",
            "stable_runs": 1,
            "feature_matrix_complete": True,
            "checks": {
                "p7_strategy_source_closed": True,
                "pair_universe_nonempty": True,
                "feature_schema_complete": True,
                "deterministic_observed_features_present": True,
                "unavailable_features_explicit": True,
            },
        }
        self.assertFalse(module.p8_feature_closure_ready(
            snapshot, {"fingerprint": "abc", "stable_runs": 0, "feature_matrix_complete": False}
        ))
        self.assertTrue(module.p8_feature_closure_ready(
            snapshot, {"fingerprint": "abc", "stable_runs": 1, "feature_matrix_complete": True}
        ))


    def test_p8_revision_resets_stale_cooldown(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('"P8":"p8-feature-matrix-v2"', source)





    def test_conveyor_fails_closed_when_an_executed_task_fails(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn("failed_executed = [", source)
        self.assertIn("raise SystemExit(1)", source)


    def test_p8_runtime_dependency_imports_math(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("import hashlib, json, math, os, time", worker)




    def test_p8_route_recurrence_uses_p6_closure_fingerprint_fallback(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('p6.get("graph_fingerprint") or p6.get("fingerprint")', worker)





    def test_p9_economic_schema_is_exact_and_fail_closed(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('P9_SCHEMA_VERSION = "p9-economic-certification-v2"', worker)
        for field in [
            '"exact_state_replay"', '"math_family"', '"exact_fee"', '"gas_cost"',
            '"flash_premium"', '"slippage"', '"transfer_tax"', '"failure_cost"',
            '"competition"', '"minimum_profit"', '"sensitivity"', '"realized_simulation_error"',
        ]:
            self.assertIn(field, worker)
        self.assertIn('stage_gate', worker)
        self.assertIn('EXACT_CERTIFIED', worker)


    def test_p9_closure_requires_complete_capability_coverage(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p9_gate", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        snapshot = {
            "checks": {
                "p8_feature_source_closed": True,
                "candidate_universe_complete": True,
                "all_capability_batches_complete": True,
                "all_candidates_have_explicit_certification_status": True,
                "all_processed_pairs_have_two_endpoint_observations": True,
            },
            "exactly_certified_count": 0,
            "uncertified_count": 10,
            "economic_fingerprint": "abc",
            "stable_runs": 1,
        }
        self.assertFalse(module.p9_economic_closure_ready(
            snapshot, {"fingerprint": "abc", "ledger_complete": False}
        ))
        self.assertTrue(module.p9_economic_closure_ready(
            snapshot, {"fingerprint": "abc", "ledger_complete": True}
        ))


    def test_p9_revision_resets_stale_cooldown(self):
        source = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn('"P9":"p9-economic-certification-v2"', source)




    def test_p9_capability_batch_is_bounded_and_persisted(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("P9_BATCH_PAIR_LIMIT = 120", worker)
        self.assertIn("persisted_observations", worker)
        self.assertIn("merged_observations", worker)
        self.assertIn('"observations": merged_observations', worker)




    def test_p9_handles_batch_unsupported_rows_without_crashing(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p9_shape", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module._p9_exact_requirements([
            {"endpoint": "rpc-a", "surface": None, "batch_supported": False, "error": "unsupported batch"},
        ])
        self.assertEqual(result["status"], "BLOCKED_RPC_BATCH_UNSUPPORTED")




    def test_p9_non_evm_pool_refs_are_typed_not_probed_as_addresses(self):
        import importlib.util
        worker_path = ROOT / "tools" / "polygon_universe_worker.py"
        spec = importlib.util.spec_from_file_location("polygon_universe_worker_p9_refs", worker_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            module._p9_ref_type("balancer", "0xpool-0xaaa-0xbbb"),
            "balancer_pool_id",
        )
        self.assertEqual(
            module._p9_ref_type("quickswap", "0x1111111111111111111111111111111111111111"),
            "evm_pair_address",
        )





    def test_p9_closure_is_capability_complete_not_profit_claim(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn("all_processed_pairs_have_two_endpoint_observations", worker)
        self.assertIn("READINESS_CLOSED_NOT_PROFIT_CERTIFIED", worker)
        self.assertIn("economic_adapter_work", worker)


    def test_p10_and_p11_define_final_polygon_census_lock(self):
        worker = (ROOT / "tools" / "polygon_universe_worker.py").read_text(encoding="utf-8")
        self.assertIn('P10_SCHEMA_VERSION = "p10-polygon-saturation-audit-v2"', worker)
        self.assertIn('"polygon_universe_status"', worker)
        self.assertIn('"polygon_census_lock"', worker)




    def test_state_restore_has_working_tree_fallback(self):
        source = (ROOT / "tools" / "automation_state_store.py").read_text(encoding="utf-8")
        self.assertIn("RESTORE_FALLBACK=WORKING_TREE", source)
        self.assertIn("ARTIFACT_RESTORE_FALLBACK=", source)





    def test_restore_uses_saturation_workflow_only(self):
        source = (ROOT / "tools" / "automation_state_store.py").read_text(encoding="utf-8")
        self.assertIn('workflow = "saturation-conveyor.yml"', source)
        self.assertNotIn('"p4-rpc-fanout.yml"', source)


    def test_stale_runs_are_cancelled_and_p10_shadow_warms_during_p9(self):
        workflow = (ROOT / ".github" / "workflows" / "saturation-conveyor.yml").read_text(encoding="utf-8")
        conveyor = (ROOT / "tools" / "saturation_conveyor.py").read_text(encoding="utf-8")
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn('current_critical == "P9"', conveyor)


if __name__ == "__main__":
    unittest.main()
