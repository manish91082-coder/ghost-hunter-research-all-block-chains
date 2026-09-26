import importlib.util
from pathlib import Path
import json, tempfile, unittest

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/"chains"/"ethereum-mainnet"/"ethereum_p2_system_verifier.py"

def load():
    spec=importlib.util.spec_from_file_location("e",MOD)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

class Tests(unittest.TestCase):
    def test_https_guard(self):
        m=load(); m.validate_endpoint("https://x.example")
        with self.assertRaises(ValueError): m.validate_endpoint("http://x.example")
        with self.assertRaises(ValueError): m.validate_endpoint("https://u:p@x.example")
    def test_targets_have_20_byte_hex_addresses(self):
        data=json.loads((ROOT/"chains"/"ethereum-mainnet"/"P2_SYSTEM_TARGETS.json").read_text())
        for t in data["targets"]:
            a=t["address"]
            self.assertRegex(a,r"^0x[0-9a-fA-F]{40}$")
    def test_manifest_has_four_canonical_targets(self):
        data=json.loads((ROOT/"chains"/"ethereum-mainnet"/"P2_SYSTEM_TARGETS.json").read_text())
        self.assertEqual(len(data["targets"]),4)
        self.assertEqual({t["id"] for t in data["targets"]},{"deposit_contract","beacon_roots","withdrawal_requests","consolidation_requests"})
if __name__=="__main__": unittest.main()
