#!/usr/bin/env python3
import hashlib,json,re,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.request import Request,urlopen

P=Path("chains/polygon-pos")
TOKEN_FILE=P/"TOKEN_UNIVERSE.jsonl"
PAIR_FILE=P/"PAIR_UNIVERSE.jsonl"
POOL_FILE=P/"POOL_UNIVERSE.jsonl"
DEX_FILE=P/"DEX_UNIVERSE.json"
RPC_FILE=P/"rpc_pool.txt"
TOKEN_CHUNK=25
PAIR_CHUNK=30
CROSS_PAIR_CHUNK=20
CROSS_TOKEN_CHUNK=20
TIMEOUT=25

def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def jl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def wjl(p,rows):
    with p.open("w",encoding="utf-8") as f:
        for x in rows: f.write(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n")
def rpcs():
    out=[]
    for line in RPC_FILE.read_text().splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "|" in line:
            a,b=line.split("|",1); out.append((a.strip(),b.strip()))
    return out
def rpc(url,calls):
    payload=[{"jsonrpc":"2.0","id":i,"method":m,"params":p} for i,(m,p) in enumerate(calls)]
    req=Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urlopen(req,timeout=TIMEOUT) as res: body=json.loads(res.read())
    if isinstance(body,list): return {int(x["id"]):x for x in body if isinstance(x,dict) and isinstance(x.get("id"),int)}
    if len(calls)==1 and isinstance(body,dict): return {0:body}
    raise RuntimeError("bad_batch_response")
def code_ok(v): return isinstance(v,str) and v.startswith("0x") and len(v)>2
def code_sha(v):
    if not code_ok(v): return None
    try: return hashlib.sha256(bytes.fromhex(v[2:])).hexdigest()
    except ValueError: return None
def uint(v):
    if not isinstance(v,str) or not v.startswith("0x") or len(v[2:])<64: return None
    try: return int(v[2:66],16)
    except ValueError: return None
def addr(v):
    if not isinstance(v,str) or not v.startswith("0x") or len(v[2:])<64: return None
    return "0x"+v[2:][-40:].lower()

def probe(item,token,pair):
    name,url=item
    try:
        r=rpc(url,[("eth_chainId",[]),("eth_blockNumber",[]),("eth_getCode",[token,"latest"]),("eth_getCode",[pair,"latest"])])
        return {"name":name,"url":url,"chain_ok":str(r.get(0,{}).get("result")).lower()=="0x89",
                "block":r.get(1,{}).get("result"),"token_code_ok":code_ok(r.get(2,{}).get("result")),
                "pair_code_ok":code_ok(r.get(3,{}).get("result"))}
    except Exception as e:
        return {"name":name,"url":url,"chain_ok":False,"token_code_ok":False,"pair_code_ok":False,
                "error":f"{type(e).__name__}: {e}"}

def select(tokens,pairs):
    token=str(tokens[0]["address"]).lower(); pair=str(pairs[0]["pair_address"]).lower()
    probes=[probe(x,token,pair) for x in rpcs()]
    capable=[x for x in probes if x.get("chain_ok") and x.get("token_code_ok") and x.get("pair_code_ok")]
    if len(capable)<3:
        raise SystemExit("NEED_3_SEMANTIC_RPC "+json.dumps(probes,sort_keys=True))
    return capable[:3],probes

def run_token_batch(url,chunk):
    calls=[];meta=[]
    for a in chunk:
        calls += [("eth_getCode",[a,"latest"]),("eth_call",[{"to":a,"data":"0x313ce567"},"latest"])]
        meta += [(a,"code"),(a,"decimals")]
    r=rpc(url,calls); out={}
    for i,(a,k) in enumerate(meta): out.setdefault(a,{})[k]=r.get(i,{}).get("result")
    return out

def run_pair_batch(url,chunk,with_factory=False):
    calls=[];meta=[]
    for a in chunk:
        calls += [("eth_getCode",[a,"latest"]),("eth_call",[{"to":a,"data":"0x0dfe1681"},"latest"]),
                  ("eth_call",[{"to":a,"data":"0xd21220a7"},"latest"])]
        meta += [(a,"code"),(a,"token0"),(a,"token1")]
        if with_factory:
            calls.append(("eth_call",[{"to":a,"data":"0xc45a0155"},"latest"])); meta.append((a,"factory"))
    r=rpc(url,calls); out={}
    for i,(a,k) in enumerate(meta): out.setdefault(a,{})[k]=r.get(i,{}).get("result")
    return out

def round_robin_batches(addrs,endpoints,size,worker):
    jobs=[]
    for i in range(0,len(addrs),size):
        idx=(i//size)%len(endpoints)
        jobs.append((endpoints[idx],addrs[i:i+size]))
    results={}
    with ThreadPoolExecutor(max_workers=len(endpoints)) as ex:
        futs={ex.submit(worker,ep["url"],chunk): (ep,chunk) for ep,chunk in jobs}
        for fut in as_completed(futs):
            ep,chunk=futs[fut]
            try: results.update(fut.result())
            except Exception as e:
                for a in chunk: results[a]={"_error":f"{ep[0]}:{type(e).__name__}:{e}"}
    return results

def main():
    tokens=jl(TOKEN_FILE); pairs=jl(PAIR_FILE); pools=jl(POOL_FILE); dex=json.loads(DEX_FILE.read_text())
    endpoints,probes=select(tokens,pairs)

    token_addrs=sorted(str(x["address"]).lower() for x in tokens)
    token_obs=round_robin_batches(token_addrs,endpoints,TOKEN_CHUNK,run_token_batch)
    for row in tokens:
        a=str(row["address"]).lower(); o=token_obs.get(a,{})
        row["onchain_identity"]={
            "status":"VERIFIED_PRIMARY" if code_sha(o.get("code")) else "OPEN",
            "rpc_endpoint": next((e["name"] for e in endpoints if e[1]),None),
            "code_sha256":code_sha(o.get("code")),
            "code_bytes":(len(o.get("code",""))-2)//2 if code_ok(o.get("code")) else None,
            "decimals":uint(o.get("decimals")),
            "error":o.get("_error")
        }

    pair_addrs=sorted(str(x["pair_address"]).lower() for x in pairs)
    pair_obs=round_robin_batches(pair_addrs,endpoints,PAIR_CHUNK,lambda url,c:run_pair_batch(url,c,False))
    pair_by={str(x["pair_address"]).lower():x for x in pairs}
    for a,row in pair_by.items():
        o=pair_obs.get(a,{})
        t0=addr(o.get("token0")); t1=addr(o.get("token1"))
        base=str((row.get("base_token") or {}).get("address") or "").lower()
        quote=str((row.get("quote_token") or {}).get("address") or "").lower()
        token_match=bool(t0 and t1 and {t0,t1}=={base,quote})
        row["onchain_binding"]={
            "status":"VERIFIED_PRIMARY" if code_sha(o.get("code")) else "OPEN",
            "code_sha256":code_sha(o.get("code")),
            "code_bytes":(len(o.get("code",""))-2)//2 if code_ok(o.get("code")) else None,
            "token0":t0,"token1":t1,
            "token_binding_status":"VERIFIED" if token_match else ("UNAVAILABLE_OR_NONSTANDARD" if code_sha(o.get("code")) else "OPEN"),
            "error":o.get("_error")
        }

    # Deterministic cross-check: first observed pair in every DEX namespace.
    rep={}
    for row in sorted(pairs,key=lambda x:str(x["pair_address"]).lower()):
        ns=str(row.get("dex_namespace") or "").lower()
        if ns and ns not in rep: rep[ns]=str(row["pair_address"]).lower()
    reps=sorted(rep.values())
    cross={a:endpoints[(i+1)%len(endpoints)] for i,a in enumerate(reps)}
    cross_results={}
    with ThreadPoolExecutor(max_workers=len(endpoints)) as ex:
        futs={}
        for i in range(0,len(reps),CROSS_PAIR_CHUNK):
            chunk=reps[i:i+CROSS_PAIR_CHUNK]
            ep=endpoints[(i//CROSS_PAIR_CHUNK+1)%len(endpoints)]
            futs[ex.submit(run_pair_batch,ep["url"],chunk,True)]=(ep,chunk)
        for fut in as_completed(futs):
            ep,chunk=futs[fut]
            try:
                vals=fut.result()
                for a,o in vals.items(): cross_results[a]=(ep,o)
            except Exception as e:
                for a in chunk: cross_results[a]=(ep,{"_error":f"{type(e).__name__}:{e}"})

    dex_by_ns={str(x.get("dex_namespace") or "").lower():x for x in dex.get("records",[])}
    for ns,pair_addr in rep.items():
        rec=dex_by_ns.get(ns)
        if not rec: continue
        ep,o=cross_results.get(pair_addr,(None,{}))
        primary=pair_by.get(pair_addr,{}).get("onchain_binding",{})
        cross_code=code_sha(o.get("code"))
        factories=[addr(o.get("factory"))] if addr(o.get("factory")) else []
        rec["factory_addresses"]=sorted(set(rec.get("factory_addresses",[])+factories))
        rec["representative_pair"]=pair_addr
        rec["cross_rpc_endpoint"]=ep["name"] if ep else None
        rec["cross_rpc_code_match"]=bool(cross_code and primary.get("code_sha256") and cross_code==primary.get("code_sha256"))
        rec["onchain_binding_status"]="VERIFIED_CROSS_RPC" if rec["cross_rpc_code_match"] else ("VERIFIED_PRIMARY_ONLY" if primary.get("code_sha256") else "OPEN")

    # Pools inherit exact contract identity. Dynamic reserves/liquidity/fees remain excluded.
    pool_by={str(x.get("pool_ref")).lower():x for x in pools}
    for p in pairs:
        a=str(p["pair_address"]).lower(); b=p.get("onchain_binding",{})
        if a in pool_by:
            pool_by[a]["onchain_binding_status"]=b.get("status")
            pool_by[a]["code_sha256"]=b.get("code_sha256")
            pool_by[a]["token0"]=b.get("token0")
            pool_by[a]["token1"]=b.get("token1")
            pool_by[a]["token_binding_status"]=b.get("token_binding_status")
    wjl(TOKEN_FILE,tokens); wjl(PAIR_FILE,pairs); wjl(POOL_FILE,list(sorted(pool_by.values(),key=lambda x:str(x.get("pool_ref")).lower())))
    DEX_FILE.write_text(json.dumps(dex,indent=2,sort_keys=True)+"\n")

    token_primary=sum(1 for x in tokens if (x.get("onchain_identity") or {}).get("status")=="VERIFIED_PRIMARY")
    pair_primary=sum(1 for x in pairs if (x.get("onchain_binding") or {}).get("status")=="VERIFIED_PRIMARY")
    pair_token_verified=sum(1 for x in pairs if (x.get("onchain_binding") or {}).get("token_binding_status")=="VERIFIED")
    dex_cross=sum(1 for x in dex.get("records",[]) if x.get("cross_rpc_code_match"))
    status="GREEN" if token_primary==len(tokens) and pair_primary==len(pairs) and dex_cross==len(dex.get("records",[])) else "OPEN"
    result={
        "schema":"polygon-static-identity-fast-v1","chain_id":137,"observed_at":now(),
        "primary_rpc_endpoints":[x["name"] for x in endpoints],
        "primary_rpc_blocks":{x["name"]:x.get("block") for x in endpoints},
        "semantic_rpc_probe":probes,
        "tokens":len(tokens),"token_primary_bound":token_primary,
        "pairs":len(pairs),"pair_primary_bound":pair_primary,
        "pair_token_binding_verified":pair_token_verified,
        "dex_namespaces":len(dex.get("records",[])),"dex_cross_rpc_verified":dex_cross,
        "status":status,
        "dynamic_boundary":["latest_block","gas","reserves","slot0","ticks","liquidity","fees","prices","spreads","orderflow","competition","estimateGas","slippage"],
        "note":"Static identity gate proves deployed contract code and deterministic market references. Dynamic execution state is intentionally excluded."
    }
    (P/"STATIC_ONCHAIN_BINDING.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    m=json.loads((P/"MASTER_INDEX.json").read_text())
    m.setdefault("static_inputs",{})["onchain_binding"]="STATIC_ONCHAIN_BINDING.json"
    m["onchain_binding_status"]=status
    m["static_closure_status"]="STATIC_MARKET_UNIVERSE_GREEN_WITH_PRIMARY_BINDING_AND_DEX_CROSSCHECK" if status=="GREEN" else "STATIC_MARKET_UNIVERSE_OPEN"
    (P/"MASTER_INDEX.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    s=json.loads((P/"STATIC_SATURATION_MANIFEST.json").read_text())
    s["onchain_binding"]=result
    s["status"]=m["static_closure_status"]
    (P/"STATIC_SATURATION_MANIFEST.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")
    if status!="GREEN": raise SystemExit("STATIC_IDENTITY_OPEN "+json.dumps(result,sort_keys=True))
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
