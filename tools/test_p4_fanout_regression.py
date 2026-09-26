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
