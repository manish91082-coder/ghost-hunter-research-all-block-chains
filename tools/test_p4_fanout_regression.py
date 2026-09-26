#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def aggregator():
    spec = importlib.util.spec_from_file_location(
        "p4_fanout_aggregate", ROOT / "tools" / "p4_fanout_aggregate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class P4FanoutRegressionTests(unittest.TestCase):
    def test_dynamic_supply_is_not_identity_conflict(self):
        mod = aggregator()
        observations = [
            {"rpc":"quicknode-public","code_hash":"abc","decimals":"0x12","total_supply":"0x100"},
            {"rpc":"tenderly-gateway","code_hash":"abc","decimals":"0x12","total_supply":"0x101"},
        ]
        result = mod.reconcile_observations(observations)
        self.assertTrue(result["matching"])
        self.assertFalse(result["conflict"])
        self.assertFalse(result["total_supply_equal"])

    def test_missing_validity_flags_are_backward_compatible(self):
        mod = aggregator()
        observations = [
            {"rpc":"a","code_hash":"abc","decimals":"0x12","total_supply":"0x1"},
            {"rpc":"b","code_hash":"abc","decimals":"0x12","total_supply":"0x2"},
        ]
        result = mod.reconcile_observations(observations)
        self.assertTrue(result["matching"])
        self.assertFalse(result["conflict"])

    def test_code_identity_plus_one_semantic_probe_is_sufficient(self):
        mod = aggregator()
        observations = [
            {
                "rpc":"quicknode-public",
                "code_hash":"abc",
                "decimals":None,
                "decimals_valid":False,
                "total_supply":None,
                "total_supply_valid":False,
            },
            {
                "rpc":"tenderly-gateway",
                "code_hash":"abc",
                "decimals":"0x12",
                "decimals_valid":True,
                "total_supply":"0x101",
                "total_supply_valid":True,
            },
        ]
        result = mod.reconcile_observations(observations)
        self.assertTrue(result["matching"])
        self.assertFalse(result["conflict"])
        self.assertTrue(result["code_identity_match"])
        self.assertTrue(result["erc20_semantic_seen"])

    def test_real_identity_conflict_stays_fail_closed(self):
        mod = aggregator()
        observations = [
            {"rpc":"a","code_hash":"abc","decimals":"0x12","total_supply":"0x1"},
            {"rpc":"b","code_hash":"abc","decimals":"0x12","total_supply":"0x1"},
            {"rpc":"c","code_hash":"different","decimals":"0x12","total_supply":"0x1"},
        ]
        result = mod.reconcile_observations(observations)
        self.assertFalse(result["matching"])
        self.assertTrue(result["conflict"])


if __name__ == "__main__":
    unittest.main()
