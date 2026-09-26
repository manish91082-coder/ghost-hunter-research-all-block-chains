#!/usr/bin/env python3
import collections,gzip,hashlib,json,shutil,time
from pathlib import Path
from urllib.request import Request,urlopen

P=Path("chains/polygon-pos"); U=Path("automation/universe"); E=Path("automation/evidence")
KEEP={"README.md","PROFILE.md","RPC.md","RPC_CAPABILITY_MATRIX.md","SYSTEM_CONTRACTS.md","BRIDGE_STATE_SYNC.md",
"STATIC_DATA_REQUIRED.md","POLYGON_SATURATION_V2.json","STATIC_SATURATION_PLAN.md","MASTER_INDEX.json",
"STATIC_SATURATION_MANIFEST.json","TOKEN_UNIVERSE.jsonl","PAIR_UNIVERSE.jsonl","POOL_UNIVERSE.jsonl",
"ROUTE_UNIVERSE.jsonl.gz","ROUTE_SAMPLE_5000.jsonl.gz","ROUTE_RULES.json","DEX_UNIVERSE.json",
"PROTOCOL_UNIVERSE.json","STATIC_CONTRACT_UNIVERSE.json","FLASH_LIQUIDITY_UNIVERSE.json",
"STRATEGY_UNIVERSE.json","FEATURE_SCHEMA.json","ECONOMIC_FRONTIER.json","UNKNOWN_NEGATIVE_SPACE.json",
"STATIC_EVIDENCE_MANIFEST.json","rpc_pool.txt"}
def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def j(p,d=None): return json.loads(p.read_text()) if p.exists() else ({} if d is None else d)
def w(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
def jl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def wjl(p,rows):
    with p.open("w") as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")
def api(u):
    q=Request(u,headers={"Accept":"application/json","User-Agent":"ghost-hunter-static/1.0"})
    with urlopen(q,timeout=30) as r:return json.loads(r.read())
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""):h.update(c)
    return h.hexdigest()
def cleanup():
    for x in P.iterdir():
        if x.name not in KEEP:
            shutil.rmtree(x) if x.is_dir() else x.unlink()

def routes(rows):
    edges=[]; nodes=set(); seen=set()
    for r in rows:
        a=str((r.get("baseToken") or {}).get("address") or "").lower()
        b=str((r.get("quoteToken") or {}).get("address") or "").lower()
        p=str(r.get("pairAddress") or "").lower()
        k=(a,b,p)
        if not a or not b or not p or a==b or k in seen: continue
        seen.add(k); edges.append(k); nodes.update((a,b))
    ts=sorted(nodes); idx={x:i for i,x in enumerate(ts)}; adj=[[] for _ in ts]
    for i,(a,b,p) in enumerate(edges):
        u,v=idx[a],idx[b]; adj[u].append((v,i,p)); adj[v].append((u,i,p))
    for a in adj:a.sort(key=lambda x:(x[2],ts[x[0]]))
    used=[False]*len(edges); np=[0]*4; ep=[0]*3; count=0; sample=[]; tmp=P/"ROUTE_UNIVERSE.jsonl.gz.tmp"; gz=None
    def emit(s,d,p):
        nonlocal count,gz
        count+=1
        rec={"route_id":f"P137-R{count:06d}","hop_count":d+1,
             "tokens":[ts[np[i]] for i in range(d+1)]+[ts[s]],
             "pools":[edges[ep[i]][2] for i in range(d)]+[p],
             "route_policy":{"max_hops":3,"no_repeated_pool":True}}
        if len(sample)<5000: sample.append(rec)
        if count<=2000000:
            if gz is None: gz=gzip.open(tmp,"wt",encoding="utf-8",compresslevel=6)
            gz.write(json.dumps(rec,separators=(",",":"))+"\n")
    def dfs(s,n,d,vis):
        if d>=3:return
        for nx,ei,p in adj[n]:
            if used[ei]:continue
            if nx==s:
                if d>=2:emit(s,d,p)
                continue
            if nx in vis:continue
            np[d+1]=nx; ep[d]=ei; used[ei]=True; dfs(s,nx,d+1,vis|{nx}); used[ei]=False
    for s in range(len(ts)):np[0]=s;dfs(s,s,0,{s})
    if gz is not None:gz.close(); shutil.move(tmp,P/"ROUTE_UNIVERSE.jsonl.gz")
    elif tmp.exists():tmp.unlink()
    with gzip.open(P/"ROUTE_SAMPLE_5000.jsonl.gz","wt",encoding="utf-8") as f:
        for r in sample:f.write(json.dumps(r,separators=(",",":"))+"\n")
    return count,len(edges),len(ts)

def main():
    P.mkdir(parents=True,exist_ok=True);U.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
    tokens=jl(U/"tokens.jsonl"); pairs=jl(U/"pairs.jsonl")
    p5=j(E/"P5_PAIR_SNAPSHOT.json"); p6=j(E/"P6_ROUTE_SNAPSHOT.json"); p7=j(E/"P7_STRATEGY_MATRIX.json"); p8=j(E/"P8_FEATURE_SNAPSHOT.json"); p9=j(E/"P9_ECONOMIC_CERTIFICATION.json"); sat=j(P/"POLYGON_SATURATION_V2.json")
    assert p5.get("stage_gate")=="CLOSED" and len(pairs)==int(p5["total_pair_records"])>0
    assert p6.get("stage_gate")=="CLOSED"
    writejl(P/"TOKEN_UNIVERSE.jsonl",[{"record_type":"polygon_static_token","chain_id":137,"address":str(x["address"]).lower(),"source":x.get("source"),"first_seen":x.get("first_seen"),"evidence_class":x.get("evidence_class") or "DISCOVERY","dynamic_fields_excluded":["total_supply","holders","balances","price","liquidity","volume"]} for x in sorted(tokens,key=lambda z:str(z.get("address","")).lower())])
    pr=[]; pools=[]; dex=collections.defaultdict(lambda:{"pairs":0,"tokens":set(),"examples":[]})
    for x in sorted(pairs,key=lambda z:str(z.get("pairAddress","")).lower()):
        a=x.get("baseToken") or {}; b=x.get("quoteToken") or {}; pa=str(x.get("pairAddress") or "").lower(); dn=str(x.get("dexId") or "").lower(); aa=str(a.get("address") or "").lower(); bb=str(b.get("address") or "").lower()
        pr.append({"record_type":"polygon_static_pair","chain_id":137,"pair_address":pa,"dex_namespace":dn,"base_token":{"address":aa,"symbol":a.get("symbol"),"name":a.get("name")},"quote_token":{"address":bb,"symbol":b.get("symbol"),"name":b.get("name")},"pair_created_at":x.get("pairCreatedAt"),"source":x.get("_source") or "dexscreener_token_pairs","observed_at":x.get("_snapshot_time") or now(),"dynamic_fields_excluded":["priceUsd","liquidity","volume","txns","fdv","marketCap"]})
        pools.append({"record_type":"polygon_static_pool","chain_id":137,"pool_ref":pa,"pool_identity_kind":"EVM_PAIR_ADDRESS_OBSERVED","venue_namespace":dn,"token_refs":[aa,bb],"pair_created_at":x.get("pairCreatedAt"),"adapter_status":"REQUIRES_LIVE_ONCHAIN_BINDING","dynamic_state_required":["reserves_or_slot0","ticks","liquidity","fee","gas","router_path"]})
        dex[dn]["pairs"]+=1;dex[dn]["tokens"].update((aa,bb))
        if len(dex[dn]["examples"])<5:dex[dn]["examples"].append(pa)
    wjl(P/"PAIR_UNIVERSE.jsonl",pr);wjl(P/"POOL_UNIVERSE.jsonl",pools);wjl(U/"pairs.jsonl",pairs)
    dr=[{"record_type":"polygon_static_dex","chain_id":137,"dex_namespace":n,"pair_count":v["pairs"],"token_count":len(v["tokens"]),"example_pair_addresses":v["examples"],"identity_status":"OBSERVED_NAMESPACE","address_registry_status":"REQUIRES_LIVE_ONCHAIN_BINDING"} for n,v in sorted(dex.items())]
    w(P/"DEX_UNIVERSE.json",{"schema":"polygon-static-dex-v1","count":len(dr),"records":dr})
    proto={"schema":"polygon-static-protocol-v1","chain_id":137,"sources":{"defillama":"https://api.llama.fi/protocols","geckoterminal":"https://api.geckoterminal.com/api/v2/networks/polygon_pos/dexes"},"observed_dex_namespaces":[x["dex_namespace"] for x in dr]}
    try:
        d=api(proto["sources"]["defillama"]);proto["defillama_polygon_protocols"]=[x for x in d if "polygon" in [str(c).lower() for c in x.get("chains",[])]]
    except Exception as e:proto["defillama_error"]=f"{type(e).__name__}: {e}"
    try:proto["geckoterminal_dexes"]=api(proto["sources"]["geckoterminal"]).get("data",[])
    except Exception as e:proto["geckoterminal_error"]=f"{type(e).__name__}: {e}"
    w(P/"PROTOCOL_UNIVERSE.json",proto)
    rc,pn,gn=routes(pr); assert rc==int(p6["route_count_total"])
    w(P/"ROUTE_RULES.json",{"schema":"polygon-static-route-v1","chain_id":137,"max_hops":3,"no_repeated_pool":True,"exact_route_count":rc,"full_route_file":rc<=2000000,"sample_file":"ROUTE_SAMPLE_5000.jsonl.gz","excluded":["split_routes","4_plus_hops"]})
    w(P/"STRATEGY_UNIVERSE.json",{"schema":"polygon-static-strategy-v1","count":len(p7.get("strategies") or []),"stage_gate":p7.get("stage_gate"),"strategies":p7.get("strategies"),"note":"Static taxonomy only; live venue/state/profit revalidated separately."})
    dom={}
    for q in p8.get("features") or []:
        for k,v in (q.get("features") or {}).items():
            if isinstance(v,dict):dom.setdefault(k,[]).append(v.get("status"))
    w(P/"FEATURE_SCHEMA.json",{"schema":"polygon-static-feature-v1","pair_groups":p8.get("pair_groups"),"feature_fingerprint":p8.get("feature_fingerprint"),"domains":[{"feature":k,"record_count":len(v),"statuses":sorted({z for z in v if z})} for k,v in sorted(dom.items())],"dynamic_values_required_from_live_chain":True})
    w(P/"ECONOMIC_FRONTIER.json",{"schema":"polygon-static-economic-frontier-v1","historical_candidate_groups":p9.get("candidate_count"),"historical_exact_profit_certified":p9.get("exactly_certified_count"),"historical_status":p9.get("economic_certification_status"),"note":"Historical readiness frontier only, not a profitability list."})
    uni=sat.get("uniswap_v4_polygon_deployments") or {}
    aave={"POOL_ADDRESSES_PROVIDER":"0xa97684ead0e402dc232d5a977953df7ecbab3cdb","POOL":"0x794a61358d6845594f94dc1db02a252b5b4814ad","POOL_CONFIGURATOR":"0x8145edddf43f50276641b55bd3ad95944510021e","ORACLE":"0xb023e699f5a33916ea823a16485e259257ca8bd1","ACL_MANAGER":"0xa72636cbca8f5ff95b2cc47f3cdee83f3294a0b","AAVE_PROTOCOL_DATA_PROVIDER":"0x243aa95cac2a25651eda86e80bee66114413c43b"}
    bal={"VAULT":"0xba12222222228d8ba445958a75a0704d566bf2c8","HELPERS":"0x239e55f427d44c3cc793f49bfb507ebe76638a2b"}
    c=[]
    for f,s,d in [("UNISWAP_V4","https://developers.uniswap.org/docs/protocols/v4/deployments",uni),("AAVE_V3_POLYGON","https://github.com/aave-dao/aave-address-book/blob/main/src/ts/AaveV3Polygon.ts",aave),("BALANCER_V2_POLYGON","https://github.com/balancer/docs-developers/blob/main/references/valuing-balancer-lp-tokens/deployment-addresses.md",bal)]:
        c += [{"family":f,"role":k,"address":str(v).lower(),"status":"DOCUMENTED_STATIC_DEPLOYMENT","source":s} for k,v in d.items()]
    c += [{"family":"OBSERVED_DEX_NAMESPACE","role":"MARKET_NAMESPACE","namespace":x["dex_namespace"],"pair_count":x["pair_count"],"address":None,"status":"REQUIRES_LIVE_ONCHAIN_BINDING"} for x in dr]
    w(P/"STATIC_CONTRACT_UNIVERSE.json",{"schema":"polygon-static-contract-v1","chain_id":137,"records":c})
    w(P/"FLASH_LIQUIDITY_UNIVERSE.json",{"schema":"polygon-static-flash-liquidity-v1","chain_id":137,"surfaces":[{"provider":"AAVE_V3","pool":aave["POOL"],"provider_registry":aave["POOL_ADDRESSES_PROVIDER"],"mechanisms":["flashLoan","flashLoanSimple"]},{"provider":"BALANCER_V2","vault":bal["VAULT"],"mechanisms":["flashLoan"]},{"provider":"DEX_FLASH_SURFACES","status":"PAIR_UNIVERSE_PRESENT","requires":"live venue-specific callback/fee verification"}]})
    w(P/"UNKNOWN_NEGATIVE_SPACE.json",{"schema":"polygon-static-negative-space-v1","residuals":[{"area":"dynamic_chain_state","status":"LIVE_REQUIRED"},{"area":"dex_contract_binding","status":"LIVE_REQUIRED"},{"area":"split_and_4plus_hop_routes","status":"SEPARATE_EXTENSION"},{"area":"exact_profitability","status":"NOT_CERTIFIED"}]})
    w(P/"STATIC_EVIDENCE_MANIFEST.json",{"schema":"polygon-static-evidence-v1","chain_id":137,"inputs":["automation/universe/tokens.jsonl","automation/universe/pairs.jsonl","automation/evidence/P5_PAIR_SNAPSHOT.json","automation/evidence/P6_ROUTE_SNAPSHOT.json","automation/evidence/P7_STRATEGY_MATRIX.json","automation/evidence/P8_FEATURE_SNAPSHOT.json","automation/evidence/P9_ECONOMIC_CERTIFICATION.json"],"no_signing":True,"no_public_broadcast":True})
    cleanup()
    (P/"STATIC_SATURATION_PLAN.md").write_text("# Polygon Static Saturation\n\nOne compact build lane: P5 pair discovery + stability, P6 exact route graph, current protocol registries, documented contract identities, static strategy/feature/economic schemas, validation.\n\nSTATIC = identity/topology/schema/deployment data. LIVE = latest block, gas, reserves/slot0/ticks, liquidity, fees, price/spread, orderflow, competition and exact simulation.\n",encoding="utf-8")
    (P/"STATIC_DATA_REQUIRED.md").write_text("# Polygon Pre-Transaction Static Data\n\nTOKEN_UNIVERSE, PAIR_UNIVERSE, POOL_UNIVERSE, DEX_UNIVERSE, PROTOCOL_UNIVERSE, STATIC_CONTRACT_UNIVERSE, FLASH_LIQUIDITY_UNIVERSE, ROUTE_UNIVERSE, STRATEGY_UNIVERSE, FEATURE_SCHEMA, ECONOMIC_FRONTIER and UNKNOWN_NEGATIVE_SPACE are the canonical static inputs.\n\nDynamic blockchain state is a separate live layer and must be revalidated before candidate simulation.\n",encoding="utf-8")
    (P/"README.md").write_text("# Polygon PoS Static Hunting Layer\n\nChain ID 137.\n\nRead MASTER_INDEX.json first. This folder is the pre-transaction static intelligence layer for read-only flash-loan/arbitrage hunting. Live market state is separate. No file authorizes signing or broadcast.\n",encoding="utf-8")
    counts={"tokens":len(tokens),"pairs":len(pr),"pools":len(pools),"dex_namespaces":len(dr),"routes":rc,"strategies":len(p7.get("strategies") or []),"feature_groups":p8.get("pair_groups"),"economic_candidate_groups":p9.get("candidate_count"),"exact_profit_certified":0}
    files={x.name:{"bytes":x.stat().st_size,"sha256":sha(x)} for x in P.iterdir() if x.is_file()}
    w(P/"STATIC_SATURATION_MANIFEST.json",{"schema":"polygon-static-saturation-v1","generated_at":now(),"chain_id":137,"counts":counts,"p5_fingerprint":p5.get("universe_fingerprint"),"p6_graph_fingerprint":p6.get("graph_fingerprint"),"pair_nodes":pn,"graph_tokens":gn,"files":files,"status":"STATIC_MARKET_UNIVERSE_READY_WITH_LIVE_RESIDUALS"})
    w(P/"MASTER_INDEX.json",{"schema":"polygon-static-master-index-v1","chain_id":137,"static_inputs":{"tokens":"TOKEN_UNIVERSE.jsonl","pairs":"PAIR_UNIVERSE.jsonl","pools":"POOL_UNIVERSE.jsonl","dexes":"DEX_UNIVERSE.json","protocols":"PROTOCOL_UNIVERSE.json","contracts":"STATIC_CONTRACT_UNIVERSE.json","flash_liquidity":"FLASH_LIQUIDITY_UNIVERSE.json","routes":"ROUTE_UNIVERSE.jsonl.gz","route_rules":"ROUTE_RULES.json","strategies":"STRATEGY_UNIVERSE.json","features":"FEATURE_SCHEMA.json","economic_frontier":"ECONOMIC_FRONTIER.json","unknowns":"UNKNOWN_NEGATIVE_SPACE.json"},"dynamic_inputs":["latest_block","gas","reserves/slot0/ticks","liquidity","fees","prices","spreads","orderflow","competition","estimateGas","slippage","protocol_health"],"counts":counts,"status":"STATIC_MARKET_UNIVERSE_READY_WITH_LIVE_RESIDUALS"})
    print(json.dumps(counts,sort_keys=True))

if __name__=="__main__":main()
