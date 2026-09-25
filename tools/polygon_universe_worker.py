#!/usr/bin/env python3
"""Autonomous Polygon universe evidence worker for P3-P10 plus P2 provenance replay.
stdlib-only; every external snapshot is labeled discovery evidence, never VERIFIED.
"""
import hashlib, json, time, urllib.error, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(".")
EVID = ROOT / "automation" / "evidence"
UNIV = ROOT / "automation" / "universe"
RPC_POOL = ROOT / "chains" / "polygon-pos" / "rpc_pool.txt"
P2_PROV = ROOT / "chains" / "polygon-pos" / "P2_EXTERNAL_PROVENANCE_CANDIDATES.md"

DexProfilesURL = "https://api.dexscreener.com/token-profiles/latest/v1"
DefiLlamaProtocolsURL = "https://api.llama.fi/protocols"

def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
def sha(v): return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def ensure(): EVID.mkdir(parents=True, exist_ok=True); UNIV.mkdir(parents=True, exist_ok=True)

def http_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"ghost-hunter-saturation/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read()), None
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"

def write_json(name, payload):
    ensure(); p=EVID/name; p.write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n", encoding="utf-8"); return str(p)

def append_jsonl(path, rows):
    ensure();
    with open(path,"a",encoding="utf-8") as f:
        for row in rows: f.write(json.dumps(row, sort_keys=True)+"\n")

def load_jsonl(path):
    p=Path(path)
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

def task_p2_provenance_replay():
    text=P2_PROV.read_text(encoding="utf-8") if P2_PROV.exists() else ""
    import re
    txs=sorted(set(re.findall(r"(?im)(?:tx|creation tx)\s*=\s*(0x[a-fA-F0-9]{64})", text)))
    result={"task":"p2_provenance_replay","time":now(),"status":"DISCOVERY_ONLY","transactions":[],"source":"canonical provenance candidate file"}
    try:
        import sys
        sys.path.insert(0, str(Path('chains/polygon-pos').resolve()))
        from polygon_readonly_verifier import RpcPool, load_rpc_endpoints
    except Exception as e:
        result["status"]="BLOCKED_IMPORT"; result["error"]=f"{type(e).__name__}: {e}"; return write_json("P2_PROVENANCE_REPLAY.json",result)
    if not RPC_POOL.exists(): result["status"]="BLOCKED_NO_RPC_POOL"; return write_json("P2_PROVENANCE_REPLAY.json",result)
    endpoints=load_rpc_endpoints(None,str(RPC_POOL)); pool=RpcPool(endpoints,1.0)
    for tx in txs:
        obs=[]
        for item in pool.ordered():
            eid=item["id"];
            a=pool.request(eid,"eth_getTransactionByHash",[tx],f"{eid}:tx:{tx}",12,1)
            b=pool.request(eid,"eth_getTransactionReceipt",[tx],f"{eid}:receipt:{tx}",12,1)
            if a.get("ok") or b.get("ok"): pool.mark_success(eid)
            else: pool.mark_failure(eid,b if not b.get("ok") else a)
            if a.get("ok") and b.get("ok"):
                obs.append({"rpc":eid,"tx":a["body"].get("result"),"receipt":b["body"].get("result")})
            if len(obs)>=2: break
        result["transactions"].append({"tx_hash":tx,"independent_observations":len(obs),"matching":len(obs)>=2 and len({json.dumps(x,sort_keys=True) for x in obs})==1,"observations":obs})
    result["status"]="REPLAYED" if txs and all(x["independent_observations"]>=2 and x["matching"] for x in result["transactions"]) else "PARTIAL"
    return write_json("P2_PROVENANCE_REPLAY.json",result)

def task_p3_protocols():
    st, llama, err=http_json(DefiLlamaProtocolsURL)
    st2, dex, err2=http_json(DexProfilesURL)
    protocols=[]
    if isinstance(llama,list):
        for p in llama:
            chains=[str(x).lower() for x in (p.get("chains") or [])]
            if "polygon" in chains: protocols.append(p)
    profiles=[]
    if isinstance(dex,list): profiles=[x for x in dex if str(x.get("chainId","")).lower()=="polygon"]
    payload={"task":"p3_protocol_discovery","time":now(),"sources":[DefiLlamaProtocolsURL,DexProfilesURL],"http":[st,st2],"protocol_candidates":protocols,"dex_profile_candidates":profiles,"evidence_class":"DISCOVERY"}
    return write_json("P3_PROTOCOL_SNAPSHOT.json",payload)

def load_seed_tokens():
    path=ROOT/"chains/polygon-pos/p4_seed_tokens.txt"
    seeds=[]
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if not line or line.startswith("#"): continue
            parts=line.split("|",2)
            if len(parts)>=2:
                address=parts[0].strip()
                label=parts[1].strip()
                if len(address)==42 and address.lower().startswith("0x"):
                    seeds.append({"address":address,"label":label,"source":"polygon_seed_manifest","first_seen":now()})
    return seeds

def task_p4_tokens():
    p=EVID/"P3_PROTOCOL_SNAPSHOT.json"
    data=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    tokens={}
    for row in load_seed_tokens():
        tokens[row["address"].lower()]=row
    for x in data.get("dex_profile_candidates",[]):
        a=x.get("tokenAddress")
        if a and len(a)==42 and a.lower().startswith("0x"):
            tokens[a.lower()]={"address":a,"source":"dexscreener_profile","first_seen":now()}
    existing={x.get("address","").lower():x for x in load_jsonl(UNIV/"tokens.jsonl")}
    before=len(existing)
    for row in tokens.values(): existing[row["address"].lower()]=row
    rows=list(existing.values())
    token_path=UNIV/"tokens.jsonl"
    token_path.write_text("".join(json.dumps(x,sort_keys=True)+"\\n" for x in rows),encoding="utf-8")
    return write_json("P4_TOKEN_SNAPSHOT.json",{
        "task":"p4_token_discovery",
        "time":now(),
        "seed_candidates":len(load_seed_tokens()),
        "profile_candidates":sum(1 for x in data.get("dex_profile_candidates",[]) if x.get("tokenAddress")),
        "new_unique_candidates":max(0,len(rows)-before),
        "new_candidates":list(tokens.values()),
        "total_candidates":len(rows),
        "evidence_class":"DISCOVERY"
    })

def task_p5_pairs():
    rows=[]; token_file=UNIV/"tokens.jsonl"
    tokens=load_jsonl(token_file)
    cursor_file=EVID/"P5_CURSOR.json"; cursor=0
    if cursor_file.exists(): cursor=int(json.loads(cursor_file.read_text()).get("cursor",0))
    batch=tokens[cursor:cursor+30]
    for t in batch:
        a=t.get("address");
        st,pairs,err=http_json(f"https://api.dexscreener.com/token-pairs/v1/polygon/{a}",timeout=20)
        if st==200 and isinstance(pairs,list):
            for pair in pairs:
                if str(pair.get("chainId","")).lower()=="polygon" and pair.get("pairAddress"):
                    pair["_snapshot_time"]=now(); pair["_source"]="dexscreener_token_pairs"; rows.append(pair)
    pair_path=UNIV/"pairs.jsonl"
    existing_pairs=load_jsonl(pair_path)
    by_address={str(x.get("pairAddress","")).lower():x for x in existing_pairs if x.get("pairAddress")}
    before=len(by_address)
    discovered_tokens={}
    for row in rows:
        address=str(row.get("pairAddress","")).lower()
        if address:
            by_address[address]=row
        for side in ("baseToken","quoteToken"):
            token=(row.get(side) or {}).get("address")
            if token and len(str(token))==42 and str(token).lower().startswith("0x"):
                discovered_tokens[str(token).lower()]={"address":str(token),"source":"dexscreener_pair_token","first_seen":now()}
    merged=list(by_address.values())
    token_path=UNIV/"tokens.jsonl"
    existing_tokens={str(x.get("address","")).lower():x for x in load_jsonl(token_path)}
    tokens_before=len(existing_tokens)
    existing_tokens.update(discovered_tokens)
    token_path.write_text("".join(json.dumps(x,sort_keys=True)+"\\n" for x in existing_tokens.values()),encoding="utf-8")
    new_tokens=max(0,len(existing_tokens)-tokens_before)
    pair_path.write_text("".join(json.dumps(x,sort_keys=True)+"\\n" for x in merged),encoding="utf-8")
    cursor=min(len(tokens),cursor+len(batch))
    write_json("P5_CURSOR.json",{"cursor":cursor,"total_tokens":len(tokens)})
    return write_json("P5_PAIR_SNAPSHOT.json",{
        "task":"p5_pair_discovery",
        "time":now(),
        "processed_tokens":len(batch),
        "observed_pair_rows":len(rows),
        "new_unique_pairs":max(0,len(merged)-before),
        "new_unique_tokens":new_tokens,
        "cursor":cursor,
        "total_pair_records":len(merged),
        "evidence_class":"DISCOVERY"
    })

def task_p6_routes():
    pairs=load_jsonl(UNIV/"pairs.jsonl"); adj=defaultdict(list); seen=set()
    for p in pairs:
        b=(p.get("baseToken") or {}).get("address"); q=(p.get("quoteToken") or {}).get("address"); pair=p.get("pairAddress")
        if not b or not q or not pair or b.lower()==q.lower(): continue
        key=(b.lower(),q.lower(),pair.lower());
        if key in seen: continue
        seen.add(key); adj[b.lower()].append((q.lower(),pair)); adj[q.lower()].append((b.lower(),pair))
    routes=[]
    def dfs(start,node,path,used):
        if 2<=len(path)<=4 and node==start: routes.append(list(path)); return
        if len(path)>=4: return
        for nxt,pair in adj.get(node,[])[:100]:
            if pair in used: continue
            if nxt==start and len(path)>=3:
                routes.append(path+[(start,pair)])
                continue
            if nxt in [x[0] for x in path]: continue
            dfs(start,nxt,path+[(nxt,pair)],used|{pair})
    for token in list(adj)[:200]: dfs(token,token,[(token,"")],set())
    return write_json("P6_ROUTE_SNAPSHOT.json",{"task":"p6_route_enumeration","time":now(),"pair_nodes":len(adj),"unique_pairs":len(seen),"route_candidates":routes[:5000],"route_count_sampled":len(routes),"evidence_class":"DERIVED"})

STRATEGIES=["dex_dex","intra_dex","triangular","multi_hop","split","flash_loan","liquidation","backrun","orderflow_mev","intent_rfq_filler","solver_relayer","liquidity_state_transition","cross_domain","statistical_temporal","gas_regime","failed_tx_retry_state","protocol_structural","negative_space_hypothesis"]
def task_p7_strategies():
    routes=json.loads((EVID/"P6_ROUTE_SNAPSHOT.json").read_text()).get("route_count_sampled",0) if (EVID/"P6_ROUTE_SNAPSHOT.json").exists() else 0
    rows=[{"strategy":s,"candidate":True,"route_context_count":routes,"status":"RESEARCH_CANDIDATE"} for s in STRATEGIES]
    return write_json("P7_STRATEGY_MATRIX.json",{"task":"p7_strategy_matrix","time":now(),"strategies":rows,"count":len(rows),"evidence_class":"DERIVED"})

def task_p8_features():
    pairs=load_jsonl(UNIV/"pairs.jsonl"); groups=defaultdict(list)
    for p in pairs:
        b=(p.get("baseToken") or {}).get("address"); q=(p.get("quoteToken") or {}).get("address");
        if not b or not q: continue
        k=":".join(sorted([b.lower(),q.lower()]));
        try: price=float(p.get("priceUsd")) if p.get("priceUsd") not in (None,"") else None
        except: price=None
        liq=((p.get("liquidity") or {}).get("usd")); vol=((p.get("volume") or {}).get("h24"));
        groups[k].append({"dex":p.get("dexId"),"pair":p.get("pairAddress"),"price":price,"liquidity_usd":liq,"volume_24h":vol})
    features=[]
    for k,rows in groups.items():
        prices=[x["price"] for x in rows if isinstance(x["price"],(int,float)) and x["price"]>0]
        spread=(max(prices)/min(prices)-1.0) if len(prices)>=2 else None
        features.append({"pair_key":k,"venue_count":len(rows),"price_spread":spread,"venues":rows})
    return write_json("P8_FEATURE_SNAPSHOT.json",{"task":"p8_features","time":now(),"pair_groups":len(groups),"features":features[:5000],"evidence_class":"DERIVED"})

def task_p9_economics():
    data=json.loads((EVID/"P8_FEATURE_SNAPSHOT.json").read_text()).get("features",[]) if (EVID/"P8_FEATURE_SNAPSHOT.json").exists() else []
    candidates=[{"pair_key":x["pair_key"],"gross_spread_pct":round(x["price_spread"]*100,6) if x.get("price_spread") is not None else None,"status":"NOT_EXACTLY_CERTIFIED","reason":"Requires venue-specific swap math, gas, fees, slippage, competition and fresh-state simulation"} for x in data if x.get("price_spread") is not None]
    return write_json("P9_ECONOMIC_SCREEN.json",{"task":"p9_economic_screen","time":now(),"candidates":candidates[:5000],"evidence_class":"SCREENING_ONLY"})

def task_p11_closure():
    audit_path=EVID/"P10_SATURATION_AUDIT.json"
    audit=json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else {}
    return write_json("P11_CLOSURE_REPORT.json",{
        "task":"p11_research_closure",
        "time":now(),
        "status":"LOCKED" if audit.get("stage_gate")!="CLOSED" else "READY",
        "next_chain_unlock": audit.get("stage_gate")=="CLOSED",
        "evidence_class":"CLOSURE_GATE"
    })

def task_p10_audit():
    files={p.name:p.stat().st_size for p in EVID.glob("P*.json")}
    summary={"task":"p10_saturation_audit","time":now(),"evidence_files":files,"universe_counts":{"tokens":len(load_jsonl(UNIV/"tokens.jsonl")),"pairs":len(load_jsonl(UNIV/"pairs.jsonl"))},"stage_gate":"OPEN","open_reason":["P2 live control/provenance gates pending","P3-P6 are incremental discovery snapshots","P9 exact simulation not complete"],"evidence_class":"AUDIT"}
    return write_json("P10_SATURATION_AUDIT.json",summary)

HANDLERS={"P2_PROVENANCE":task_p2_provenance_replay,"P3":task_p3_protocols,"P4":task_p4_tokens,"P5":task_p5_pairs,"P6":task_p6_routes,"P7":task_p7_strategies,"P8":task_p8_features,"P9":task_p9_economics,"P10":task_p10_audit,"P11":task_p11_closure}

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument("--task",required=True,choices=sorted(HANDLERS)); args=parser.parse_args();
    print(HANDLERS[args.task]())