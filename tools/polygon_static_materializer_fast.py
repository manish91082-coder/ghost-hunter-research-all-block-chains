#!/usr/bin/env python3
import collections,gzip,json,hashlib,shutil,time
from pathlib import Path
from urllib.request import Request,urlopen

P=Path("chains/polygon-pos");U=Path("automation/universe");E=Path("automation/evidence")
KEEP={"README.md","PROFILE.md","RPC.md","RPC_CAPABILITY_MATRIX.md","SYSTEM_CONTRACTS.md","BRIDGE_STATE_SYNC.md","STATIC_DATA_REQUIRED.md","POLYGON_SATURATION_V2.json",
"STATIC_SATURATION_PLAN.md","MASTER_INDEX.json","STATIC_SATURATION_MANIFEST.json","TOKEN_UNIVERSE.jsonl","PAIR_UNIVERSE.jsonl","POOL_UNIVERSE.jsonl",
"ROUTE_SAMPLE_5000.jsonl.gz","ROUTE_RULES.json","DEX_UNIVERSE.json","PROTOCOL_UNIVERSE.json","STATIC_CONTRACT_UNIVERSE.json","FLASH_LIQUIDITY_UNIVERSE.json",
"STRATEGY_UNIVERSE.json","FEATURE_SCHEMA.json","ECONOMIC_FRONTIER.json","UNKNOWN_NEGATIVE_SPACE.json","STATIC_EVIDENCE_MANIFEST.json","rpc_pool.txt"}
def now():return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def j(p):return json.loads(p.read_text())
def w(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def wjl(p,rows):
    with p.open("w") as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")
def cleanup():
    for x in P.iterdir():
        if x.name not in KEEP: shutil.rmtree(x) if x.is_dir() else x.unlink()
def api(u):
    q=Request(u,headers={"Accept":"application/json","User-Agent":"ghost-hunter-static-fast/1.0"})
    with urlopen(q,timeout=30) as r:return json.loads(r.read())
def main():
    P.mkdir(parents=True,exist_ok=True)
    tokens=jl(U/"tokens.jsonl"); pairs=jl(U/"pairs.jsonl")
    p5=j(E/"P5_PAIR_SNAPSHOT.json");p6=j(E/"P6_ROUTE_SNAPSHOT.json");p7=j(E/"P7_STRATEGY_MATRIX.json");p8=j(E/"P8_FEATURE_SNAPSHOT.json");p9=j(E/"P9_ECONOMIC_CERTIFICATION.json")
    assert pairs and int(p5["total_pair_records"])==len(pairs)
    ids=[str(x.get("pairAddress","")).lower() for x in pairs]
    assert len(ids)==len(set(ids))
    # Token identity
    wjl(P/"TOKEN_UNIVERSE.jsonl",[{"record_type":"polygon_static_token","chain_id":137,"address":str(t["address"]).lower(),"source":t.get("source"),"first_seen":t.get("first_seen"),"evidence_class":t.get("evidence_class") or "DISCOVERY","dynamic_fields_excluded":["total_supply","holders","balances","price","liquidity","volume"]} for t in sorted(tokens,key=lambda x:str(x.get("address","")).lower())])
    pr=[];po=[];dx=collections.defaultdict(lambda:{"pairs":0,"tokens":set(),"examples":[]})
    for x in sorted(pairs,key=lambda z:str(z.get("pairAddress","")).lower()):
        a=x.get("baseToken") or {};b=x.get("quoteToken") or {};aa=str(a.get("address") or "").lower();bb=str(b.get("address") or "").lower();pa=str(x.get("pairAddress") or "").lower();dn=str(x.get("dexId") or "").lower()
        pr.append({"record_type":"polygon_static_pair","chain_id":137,"pair_address":pa,"dex_namespace":dn,"base_token":{"address":aa,"symbol":a.get("symbol"),"name":a.get("name")},"quote_token":{"address":bb,"symbol":b.get("symbol"),"name":b.get("name")},"pair_created_at":x.get("pairCreatedAt"),"source":x.get("_source") or "dexscreener_token_pairs","observed_at":x.get("_snapshot_time"),"dynamic_fields_excluded":["priceUsd","liquidity","volume","txns","fdv","marketCap"]})
        po.append({"record_type":"polygon_static_pool","chain_id":137,"pool_ref":pa,"pool_identity_kind":"EVM_PAIR_ADDRESS_OBSERVED","venue_namespace":dn,"token_refs":[aa,bb],"pair_created_at":x.get("pairCreatedAt"),"adapter_status":"REQUIRES_LIVE_ONCHAIN_BINDING"})
        dx[dn]["pairs"]+=1;dx[dn]["tokens"].update([aa,bb])
        if len(dx[dn]["examples"])<5:dx[dn]["examples"].append(pa)
    wjl(P/"PAIR_UNIVERSE.jsonl",pr);wjl(P/"POOL_UNIVERSE.jsonl",po)
    D=[{"record_type":"polygon_static_dex","chain_id":137,"dex_namespace":n,"pair_count":v["pairs"],"token_count":len(v["tokens"]),"example_pair_addresses":v["examples"],"status":"OBSERVED_NAMESPACE_REQUIRES_LIVE_BINDING"} for n,v in sorted(dx.items())]
    w(P/"DEX_UNIVERSE.json",{"schema":"polygon-static-dex-fast-v1","count":len(D),"records":D})
    proto={"schema":"polygon-static-protocol-fast-v1","chain_id":137,"source_snapshot":"P3_PROTOCOL_SNAPSHOT.json","observed_dex_namespaces":[x["dex_namespace"] for x in D]}
    p3=j(E/"P3_PROTOCOL_SNAPSHOT.json");proto.update({"polygon_protocol_count":p3.get("polygon_protocol_count"),"polygon_dex_protocol_count":p3.get("polygon_dex_protocol_count"),"geckoterminal_dex_count":p3.get("geckoterminal_dex_count"),"sources":p3.get("sources")})
    try:
        q=api("https://api.llama.fi/protocols");proto["defillama_polygon_protocols"]=[x for x in q if "polygon" in [str(c).lower() for c in x.get("chains",[])]]
    except Exception as e:proto["refresh_error"]=str(e)
    w(P/"PROTOCOL_UNIVERSE.json",proto)
    # Exact route count + stored sample, derived from P6.
    samples=p6.get("route_candidates") or []
    with gzip.open(P/"ROUTE_SAMPLE_5000.jsonl.gz","wt",encoding="utf-8") as f:
        for r in samples[:5000]:f.write(json.dumps(r,separators=(",",":"))+"\n")
    w(P/"ROUTE_RULES.json",{"schema":"polygon-static-route-fast-v1","chain_id":137,"max_hops":3,"no_repeated_pool":True,"exact_route_count":p6.get("route_count_total"),"sample_count":len(samples[:5000]),"excluded":["split_routes","4_plus_hops"],"route_generation":"deterministic from PAIR_UNIVERSE"})
    w(P/"STRATEGY_UNIVERSE.json",{"schema":"polygon-static-strategy-fast-v1","count":len(p7.get("strategies") or []),"stage_gate":p7.get("stage_gate"),"strategies":p7.get("strategies")})
    dom={}
    for r in p8.get("features",[]):
        for k,v in (r.get("features") or {}).items():
            if isinstance(v,dict):dom.setdefault(k,[]).append(v.get("status"))
    w(P/"FEATURE_SCHEMA.json",{"schema":"polygon-static-feature-fast-v1","pair_groups":p8.get("pair_groups"),"feature_fingerprint":p8.get("feature_fingerprint"),"domains":[{"feature":k,"record_count":len(v),"statuses":sorted({z for z in v if z})} for k,v in sorted(dom.items())],"dynamic_values_required_from_live_chain":True})
    w(P/"ECONOMIC_FRONTIER.json",{"schema":"polygon-static-economic-frontier-fast-v1","candidate_groups":p9.get("candidate_count"),"exact_profit_certified":p9.get("exactly_certified_count"),"status":p9.get("economic_certification_status"),"note":"Candidate readiness only; not live profitability."})
    sat=j(P/"POLYGON_SATURATION_V2.json");uni=sat.get("uniswap_v4_polygon_deployments") or {}
    aave={"POOL_ADDRESSES_PROVIDER":"0xa97684ead0e402dc232d5a977953df7ecbab3cdb","POOL":"0x794a61358d6845594f94dc1db02a252b5b4814ad","POOL_CONFIGURATOR":"0x8145edddf43f50276641b55bd3ad95944510021e","ORACLE":"0xb023e699f5a33916ea823a16485e259257ca8bd1","ACL_MANAGER":"0xa72636cbca8f5ff95b2cc47f3cdee83f3294a0b","AAVE_PROTOCOL_DATA_PROVIDER":"0x243aa95cac2a25651eda86e80bee66114413c43b"}
    bal={"VAULT":"0xba12222222228d8ba445958a75a0704d566bf2c8","HELPERS":"0x239e55f427d44c3cc793f49bfb507ebe76638a2b"}
    C=[]
    for f,s,d in [("UNISWAP_V4","https://developers.uniswap.org/docs/protocols/v4/deployments",uni),("AAVE_V3_POLYGON","https://github.com/aave-dao/aave-address-book/blob/main/src/ts/AaveV3Polygon.ts",aave),("BALANCER_V2_POLYGON","https://github.com/balancer/docs-developers/blob/main/references/valuing-balancer-lp-tokens/deployment-addresses.md",bal)]:
        for k,v in d.items():C.append({"family":f,"role":k,"address":str(v).lower(),"source":s,"status":"DOCUMENTED_STATIC_DEPLOYMENT"})
    C += [{"family":"OBSERVED_DEX_NAMESPACE","namespace":x["dex_namespace"],"pair_count":x["pair_count"],"address":None,"status":"REQUIRES_LIVE_ONCHAIN_BINDING"} for x in D]
    w(P/"STATIC_CONTRACT_UNIVERSE.json",{"schema":"polygon-static-contract-fast-v1","chain_id":137,"records":C})
    w(P/"FLASH_LIQUIDITY_UNIVERSE.json",{"schema":"polygon-static-flash-liquidity-fast-v1","chain_id":137,"surfaces":[{"provider":"AAVE_V3","pool":aave["POOL"],"provider_registry":aave["POOL_ADDRESSES_PROVIDER"],"mechanisms":["flashLoan","flashLoanSimple"]},{"provider":"BALANCER_V2","vault":bal["VAULT"],"mechanisms":["flashLoan"]},{"provider":"DEX_FLASH_SURFACES","status":"PAIR_UNIVERSE_PRESENT","requires":"live venue callback/fee verification"}]})
    w(P/"UNKNOWN_NEGATIVE_SPACE.json",{"schema":"polygon-static-negative-space-fast-v1","residuals":[{"area":"dynamic_chain_state","status":"LIVE_REQUIRED"},{"area":"dex_contract_binding","status":"LIVE_REQUIRED"},{"area":"split_and_4plus_hop_routes","status":"SEPARATE_EXTENSION"},{"area":"exact_profitability","status":"NOT_CERTIFIED"}]})
    w(P/"STATIC_EVIDENCE_MANIFEST.json",{"schema":"polygon-static-evidence-fast-v1","chain_id":137,"inputs":["automation/universe/tokens.jsonl","automation/universe/pairs.jsonl","automation/evidence/P5_PAIR_SNAPSHOT.json","automation/evidence/P6_ROUTE_SNAPSHOT.json","automation/evidence/P7_STRATEGY_MATRIX.json","automation/evidence/P8_FEATURE_SNAPSHOT.json","automation/evidence/P9_ECONOMIC_CERTIFICATION.json"],"no_signing":True,"no_public_broadcast":True})
    cleanup()
    (P/"STATIC_SATURATION_PLAN.md").write_text("# Polygon Static Saturation\\n\\nP5 pair universe is rechecked to an independent two-pass fingerprint stability gate; P6 computes the exact bounded route count and stores a canonical sample; protocol/DEX/contract/flash-liquidity identities are materialized; static strategy, feature and economic readiness indexes are frozen.\\n\\nDynamic chain state remains separate.\\n",encoding="utf-8")
    (P/"STATIC_DATA_REQUIRED.md").write_text("# Polygon Pre-Transaction Static Data\\n\\nStatic inputs: token, pair, pool, DEX, protocol, contract, flash-liquidity, route topology, strategy, feature, economic readiness and negative-space data.\\n\\nLive inputs: current block, gas, reserves/slot0/ticks, liquidity, fees, prices/spreads, orderflow, competition and exact simulation state.\\n",encoding="utf-8")
    (P/"README.md").write_text("# Polygon PoS Static Hunting Layer\\n\\nChain ID 137. Read MASTER_INDEX.json first. No file here authorizes signing or public broadcast.\\n",encoding="utf-8")
    counts={"tokens":len(tokens),"pairs":len(pr),"pools":len(po),"dex_namespaces":len(D),"routes":int(p6["route_count_total"]),"route_sample":len(samples[:5000]),"strategies":len(p7.get("strategies") or []),"feature_groups":p8.get("pair_groups"),"economic_candidate_groups":p9.get("candidate_count"),"exact_profit_certified":p9.get("exactly_certified_count")}
    w(P/"STATIC_SATURATION_MANIFEST.json",{"schema":"polygon-static-saturation-fast-v1","generated_at":now(),"chain_id":137,"counts":counts,"p5_fingerprint":p5.get("universe_fingerprint"),"p6_graph_fingerprint":p6.get("graph_fingerprint"),"status":"STATIC_MARKET_UNIVERSE_READY_WITH_EXPLICIT_LIVE_RESIDUALS"})
    w(P/"MASTER_INDEX.json",{"schema":"polygon-static-master-index-fast-v1","chain_id":137,"static_inputs":{"tokens":"TOKEN_UNIVERSE.jsonl","pairs":"PAIR_UNIVERSE.jsonl","pools":"POOL_UNIVERSE.jsonl","dexes":"DEX_UNIVERSE.json","protocols":"PROTOCOL_UNIVERSE.json","contracts":"STATIC_CONTRACT_UNIVERSE.json","flash_liquidity":"FLASH_LIQUIDITY_UNIVERSE.json","routes":"ROUTE_RULES.json + ROUTE_SAMPLE_5000.jsonl.gz","strategies":"STRATEGY_UNIVERSE.json","features":"FEATURE_SCHEMA.json","economic_frontier":"ECONOMIC_FRONTIER.json","unknowns":"UNKNOWN_NEGATIVE_SPACE.json"},"dynamic_inputs":["latest_block","gas","reserves/slot0/ticks","liquidity","fees","prices","spreads","orderflow","competition","estimateGas","slippage","protocol_health"],"counts":counts})
    print(json.dumps(counts,sort_keys=True))
if __name__=="__main__":main()
