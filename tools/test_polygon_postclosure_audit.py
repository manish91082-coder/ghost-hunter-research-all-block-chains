import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PolygonAuditSchema(unittest.TestCase):
 def test_manifest(self):
  j=json.loads((ROOT/"chains/polygon-pos/POLYGON_SATURATION_V2.json").read_text())
  self.assertEqual(j["sealed_universe"]["tokens"],469); self.assertEqual(j["sealed_universe"]["pairs"],2821)
  self.assertEqual(j["sealed_universe"]["routes"],617622)
 def test_pool_identity(self):
  j=json.loads((ROOT/"chains/polygon-pos/POLYGON_SATURATION_V2.json").read_text())
  self.assertIn("SINGLETON_POOL_MANAGER",j["pool_identity"]["kinds"])
  self.assertIn("BALANCER_POOL_ID",j["pool_identity"]["kinds"])
 def test_surfaces(self):
  j=json.loads((ROOT/"chains/polygon-pos/POLYGON_SATURATION_V2.json").read_text())
  need={"DEX_AGGREGATOR","RFQ_INTENT_SOLVER","FLASH_LIQUIDITY","LENDING_LIQUIDATION","MEV_PRIVATE_ORDERFLOW","CROSS_DOMAIN_AGGLAYER","STAKING_LIQUID_STAKING","RWA_TOKENIZATION","DERIVATIVES_PREDICTION"}
  self.assertTrue(need.issubset(set(j["opportunity_surfaces"])))
if __name__=="__main__": unittest.main()
