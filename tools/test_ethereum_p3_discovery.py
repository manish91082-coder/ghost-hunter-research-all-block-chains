import importlib.util, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/"chains"/"ethereum-mainnet"/"ethereum_p3_discovery.py"
def load():
    s=importlib.util.spec_from_file_location("p3",MOD); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
class Tests(unittest.TestCase):
    def test_normalize(self):
        m=load()
        self.assertEqual(m.normalize("  Uniswap   V3!! "),"uniswap v3")
    def test_source_urls(self):
        m=load()
        self.assertIn("/protocols",m.LLAMA_URL)
        self.assertIn("/dexes",m.GECKO_URL)
        self.assertIn("token-profiles",m.DEXSCREENER_URL)
if __name__=="__main__": unittest.main()
