import hashlib,json,re,time
from pathlib import Path
from urllib.request import Request,urlopen
AUDIT_MARKER="2026-09-26-polygon-green-verification-pass"\nROOT=Path("."); E=ROOT/"automation/evidence"; U=ROOT/"automation/universe"; P=ROOT/"chains/polygon-pos"
def J(p): return json.loads(p.read_text())
def records(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def probe(src):
 try:
  req=Request(src["url"],headers={"User-Agent":"ghost-hunter-polygon-audit/2.0"})
  with urlopen(req,timeout=20) as r:
   body=r.read(500000).decode("utf-8","ignore")
  return {"ok":all(m.lower() in body.lower() for m in src["markers"]),"http_status":r.status,"markers_found":[m for m in src["markers"] if m.lower() in body.lower()]}
 except Exception as e: return {"ok":False,"error":f"{type(e).__name__}: {e}"}
required=["automation/evidence/P11_POLYGON_CLOSURE_CERTIFICATE.json","automation/evidence/P10_SATURATION_AUDIT.json","automation/evidence/P11_CLOSURE_REPORT.json","automation/evidence/P9_ECONOMIC_CERTIFICATION.json","automation/universe/tokens.jsonl","automation/universe/pairs.jsonl","chains/polygon-pos/POLYGON_SATURATION_V2.json"]
fails=[]
if any(not Path(x).exists() for x in required): fails.append("required_artifact_missing")
s=J(P/"POLYGON_SATURATION_V2.json"); c=J(E/"P11_POLYGON_CLOSURE_CERTIFICATE.json"); t=records(U/"tokens.jsonl"); p=records(U/"pairs.jsonl")
if (len(t),len(p))!=(469,2821): fails.append("sealed_universe_count_mismatch")
if len({x.get("address","").lower() for x in t})!=469: fails.append("token_uniqueness_failure")
if len({x.get("pairAddress","").lower() for x in p})!=2821: fails.append("pair_uniqueness_failure")
p10=J(E/"P10_SATURATION_AUDIT.json"); p11=J(E/"P11_CLOSURE_REPORT.json"); p9=J(E/"P9_ECONOMIC_CERTIFICATION.json")
if p10.get("stage_gate")!="CLOSED": fails.append("P10_not_closed")
if p11.get("status")!="READY" or not p11.get("polygon_census_lock"): fails.append("P11_not_ready")
if int(p9.get("candidate_count",0))!=420 or len(p9.get("ledger",[]))!=420: fails.append("economic_ledger_incomplete")
if any(not x.get("exact_certification",{}).get("status") or "blockers" not in x.get("exact_certification",{}) for x in p9["ledger"]): fails.append("economic_disposition_incomplete")
source_results={x["id"]:probe(x) for x in s["current_sources"]}
fails += [f"source_failed:{k}" for k,v in source_results.items() if not v["ok"]]
if "SINGLETON_POOL_MANAGER" not in s["pool_identity"]["kinds"] or "BALANCER_POOL_ID" not in s["pool_identity"]["kinds"]: fails.append("pool_identity_gap")
required_surfaces={"DEX_SPOT","DEX_AGGREGATOR","RFQ_INTENT_SOLVER","FLASH_LIQUIDITY","LENDING_LIQUIDATION","MEV_PRIVATE_ORDERFLOW","CROSS_DOMAIN_AGGLAYER","STAKING_LIQUID_STAKING","RWA_TOKENIZATION","DERIVATIVES_PREDICTION"}
if not required_surfaces.issubset(set(s["opportunity_surfaces"])): fails.append("opportunity_surface_gap")
dex_ids=sorted(set(str(x.get("dexId","")).lower() for x in p if x.get("dexId")))
named={"quickswap","uniswap","sushiswap","balancer","dfyn","elkfinance","kyberswap","apeswap","comethswap","retro","radioshack","pearl","polycat","dystopia","gravityfinance","jetswap","polyzap","dooar","satin","ramses","mmfinance","dinoswap","firebird","jamonswap","fraxswap","algebra"}
custom=sum(1 for d in dex_ids if d not in named)
report={"schema_version":"polygon-postclosure-audit-v2","time":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"status":"GREEN" if not fails else "RED","scope":"POLYGON_RESEARCH_UNIVERSE_SATURATED","counts":{"tokens":len(t),"pairs":len(p),"dex_namespaces":len(dex_ids),"custom_namespaces":custom,"economic_candidates":420,"exact_profit_certified":int(p9.get("exactly_certified_count",0))},"source_results":source_results,"failures":fails,"note":"GREEN does not authorize live execution or claim exact profitability."}
Path("automation/evidence").mkdir(parents=True,exist_ok=True)
Path("automation/evidence/P11_1_POLYGON_RESIDUAL_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
raise SystemExit(0 if not fails else 1)
