#!/usr/bin/env python3
import gzip,json,shutil,time
from pathlib import Path

P=Path("chains/polygon-pos")
PAIR_FILE=P/"PAIR_UNIVERSE.jsonl"
P6=Path("automation/evidence/P6_ROUTE_SNAPSHOT.json")

def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def main():
    pairs=rows(PAIR_FILE)
    edges=[];nodes=set();seen=set()
    for r in pairs:
        a=str((r.get("base_token") or {}).get("address") or "").lower()
        b=str((r.get("quote_token") or {}).get("address") or "").lower()
        pool=str(r.get("pair_address") or "").lower()
        if not a or not b or not pool or a==b or pool in seen:
            continue
        seen.add(pool);edges.append((a,b,pool));nodes.update((a,b))

    ts=sorted(nodes); idx={x:i for i,x in enumerate(ts)}
    adj=[[] for _ in ts]
    for i,(a,b,p) in enumerate(edges):
        u,v=idx[a],idx[b]
        adj[u].append((v,i,p));adj[v].append((u,i,p))
    for a in adj:a.sort(key=lambda x:(x[2],ts[x[0]]))

    used=[False]*len(edges)
    np=[0]*4;ep=[0]*3
    count=0;sample=[]
    out=P/"ROUTE_UNIVERSE.jsonl.gz"
    tmp=P/"ROUTE_UNIVERSE.jsonl.gz.tmp"

    with gzip.open(tmp,"wt",encoding="utf-8",compresslevel=6) as gz:
        def emit(s,d,p):
            nonlocal count
            count+=1
            rec={
                "route_id":f"P137-R{count:06d}",
                "hop_count":d+1,
                "tokens":[ts[np[i]] for i in range(d+1)]+[ts[s]],
                "pools":[edges[ep[i]][2] for i in range(d)]+[p],
                "route_policy":{"max_hops":3,"no_repeated_pool":True}
            }
            gz.write(json.dumps(rec,separators=(",",":"))+"\n")
            if len(sample)<5000: sample.append(rec)

        def dfs(s,n,d,vis):
            if d>=3:return
            for nx,ei,p in adj[n]:
                if used[ei]:continue
                if nx==s:
                    if d>=2:emit(s,d,p)
                    continue
                if nx in vis:continue
                np[d+1]=nx;ep[d]=ei;used[ei]=True
                dfs(s,nx,d+1,vis|{nx})
                used[ei]=False

        for s in range(len(ts)):
            np[0]=s
            dfs(s,s,0,{s})

    shutil.move(tmp,out)
    with gzip.open(P/"ROUTE_SAMPLE_5000.jsonl.gz","wt",encoding="utf-8") as f:
        for r in sample:f.write(json.dumps(r,separators=(",",":"))+"\n")

    expected=None
    if P6.exists():
        expected=json.loads(P6.read_text()).get("route_count_total")
        if expected is not None and count!=int(expected):
            raise SystemExit(f"ROUTE_COUNT_MISMATCH generated={count} expected={expected}")

    rules=json.loads((P/"ROUTE_RULES.json").read_text()) if (P/"ROUTE_RULES.json").exists() else {}
    rules.update({
        "max_hops":3,
        "no_repeated_pool":True,
        "full_route_artifact":"ROUTE_UNIVERSE.jsonl.gz",
        "route_count":count,
        "route_generation":"DETERMINISTIC_FROM_CANONICAL_PAIR_UNIVERSE",
        "dynamic_state_excluded":True
    })
    (P/"ROUTE_RULES.json").write_text(json.dumps(rules,indent=2,sort_keys=True)+"\n")

    m=json.loads((P/"MASTER_INDEX.json").read_text())
    m.setdefault("static_inputs",{})["route_universe"]="ROUTE_UNIVERSE.jsonl.gz"
    m["route_artifact_status"]="COMPLETE_STATIC_ROUTE_TOPOLOGY"
    (P/"MASTER_INDEX.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")

    s=json.loads((P/"STATIC_SATURATION_MANIFEST.json").read_text())
    s["route_artifact"]={"status":"COMPLETE","count":count,"file":"ROUTE_UNIVERSE.jsonl.gz","sample":"ROUTE_SAMPLE_5000.jsonl.gz"}
    s["status"]="STATIC_MARKET_UNIVERSE_READY_WITH_EXPLICIT_LIVE_RESIDUALS"
    (P/"STATIC_SATURATION_MANIFEST.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")

    print(json.dumps({"status":"GREEN","pairs":len(pairs),"nodes":len(ts),"routes":count,"artifact":str(out)},sort_keys=True))

if __name__=="__main__":
    main()
