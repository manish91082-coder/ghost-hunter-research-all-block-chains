import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "chains" / "ethereum-mainnet" / "ethereum_p4_token_universe.py"

def load():
    spec = importlib.util.spec_from_file_location("p4", MOD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class Tests(unittest.TestCase):
    def test_normalize_address(self):
        m = load()
        self.assertEqual(m.normalize_address("0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD"),
                         "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd")
        self.assertIsNone(m.normalize_address("not-an-address"))

    def test_token_list_extract_and_dedupe(self):
        m = load()
        payload = {
            "tokens": [
                {"chainId": 1, "address": "0x0000000000000000000000000000000000000001", "symbol": "A", "name": "A", "decimals": 18},
                {"chainId": 1, "address": "0x0000000000000000000000000000000000000001", "symbol": "A2", "name": "A2", "decimals": 18},
                {"chainId": 137, "address": "0x0000000000000000000000000000000000000002", "symbol": "P", "name": "P", "decimals": 18}
            ]
        }
        rows = m.extract_token_list(payload, "src")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["address"], "0x0000000000000000000000000000000000000001")

    def test_gecko_extract(self):
        m = load()
        payload = {
            "data": [
                {"id": "eth_0x0000000000000000000000000000000000000003",
                 "attributes": {"name": "C", "symbol": "C", "decimals": 18}},
                {"id": "solana_X"}
            ]
        }
        rows = m.extract_gecko_recent(payload, "gt")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["address"], "0x0000000000000000000000000000000000000003")

    def test_classify(self):
        m = load()
        self.assertEqual(m.classify_token({"observations": 2, "successful_observations": 2, "code_hashes": {"x"}, "code_nonempty": 2}),
                         "VERIFIED_DEPLOYED_CONTRACT")
        self.assertEqual(m.classify_token({"observations": 2, "successful_observations": 2, "code_hashes": set(), "code_nonempty": 0}),
                         "VERIFIED_NON_CONTRACT")
        self.assertEqual(m.classify_token({"observations": 2, "successful_observations": 2, "code_hashes": {"a", "b"}, "code_nonempty": 2}),
                         "CODE_HASH_CONFLICT")
        self.assertEqual(m.classify_token({"observations": 1, "successful_observations": 1, "code_hashes": {"a"}, "code_nonempty": 1}),
                         "INCOMPLETE_RPC_EVIDENCE")

if __name__ == "__main__":
    unittest.main()
