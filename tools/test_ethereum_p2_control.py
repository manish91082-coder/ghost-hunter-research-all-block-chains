import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/"chains"/"ethereum-mainnet"/"ethereum_p2_control_verifier.py"
def load():
    spec=importlib.util.spec_from_file_location("e",MOD); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
class Tests(unittest.TestCase):
    def test_manifest(self):
        data=json.loads((ROOT/"chains"/"ethereum-mainnet"/"P2_CONTROL_TARGETS.json").read_text())
        self.assertEqual(len(data["controls"]),5)
        self.assertEqual({x["id"] for x in data["controls"]},{"deposit_root","deposit_count","beacon_root_lookup","withdrawal_fee_getter","consolidation_fee_getter"})
    def test_build_calls(self):
        m=load()
        rows=m.build_calls(123)
        self.assertEqual(rows[0][2],"0xc5f2892f")
        self.assertEqual(rows[1][2],"0x621fd130")
        self.assertEqual(rows[2][2],"0x"+format(123,"064x"))
        self.assertEqual(rows[3][2],"0x")
        self.assertEqual(rows[4][2],"0x")
if __name__=="__main__": unittest.main()
