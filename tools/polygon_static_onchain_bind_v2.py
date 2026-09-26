#!/usr/bin/env python3
import hashlib, json, re, time
from pathlib import Path
from urllib.request import Request, urlopen

P=Path("chains/polygon-pos")
TOKEN_FILE=P/"TOKEN_UNIVERSE.jsonl"
PAIR_FILE=P/"PAIR_UNIVERSE.jsonl"
POOL_FILE=P/"POOL_UNIVERSE.jsonl"
DEX_FILE=P/"DEX_UNIVERSE.json"
RPC_FILE=P/"rpc_pool.txt"
BATCH_SIZE=18
TIMEOUT=30

def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def jl(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def wjl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",",":"))+"\n")

def rpc_pool():
    rows=[]
    for line in RPC_FILE.read_text().splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        name,url=line.split("|",1)
        rows.append((name.strip(),url.strip()))
    return rows

def rpc(url, calls):
    payload=[{"jsonrpc":"2.0","id":i,"method":m,"params":p} for i,(m,p) in enumerate(calls)]
    req=Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urlopen(req,timeout=TIMEOUT) as r:
        body=json.loads(r.read())
    if isinstance(body,list):
        return {int(x["id"]):x for x in body if isinstance(x,dict) and isinstance(x.get("id"),int)}
    if len(calls)==1 and isinstance(body,dict):
        return {0:body}
    raise RuntimeError("batch_response_shape")

def valid_code(raw):
    return isinstance(raw,str) and raw.startswith("0x") and len(raw)>2

def code_sha(raw):
    if not valid_code(raw):
        return None
    try:
        return hashlib.sha256(bytes.fromhex(raw[2:])).hexdigest()
    except ValueError:
        return None

def uint(raw):
    if not isinstance(raw,str) or not raw.startswith("0x") or len(raw[2:])<64:
        return None
    try:
        return int(raw[2:66],16)
    except ValueError:
        return None

def address(raw):
    if not isinstance(raw,str) or not raw.startswith("0x") or len(raw[2:])<64:
        return None
    return "0x"+raw[2:][-40:].lower()

def strret(raw):
    if not isinstance(raw,str) or not raw.startswith("0x"):
        return None
    h=raw[2:]
    try:
        if len(h)==64:
            return bytes.fromhex(h).rstrip(b"\x00").decode("utf-8",errors="ignore").strip() or None
        if len(h)>=128:
            off=int(h[:64],16)*2
            if off+64<=len(h):
                n=int(h[off:off+64],16)
                b=bytes.fromhex(h[off+64:off+64+n*2])
                return b.decode("utf-8",errors="ignore").strip() or None
    except (ValueError,UnicodeError):
        return None
    return None

def probe_endpoint(name,url,token_probe,pair_probe):
    try:
        calls=[
            ("eth_chainId",[]),
            ("eth_blockNumber",[]),
            ("eth_getCode",[token_probe,"latest"]),
            ("eth_getCode",[pair_probe,"latest"]),
        ]
        r=rpc(url,calls)
        chain=r.get(0,{}).get("result")
        block=r.get(1,{}).get("result")
        token_code=r.get(2,{}).get("result")
        pair_code=r.get(3,{}).get("result")
        return {
            "name":name,"url":url,
            "chain_ok":str(chain).lower()=="0x89",
            "block":block,
            "token_code_ok":valid_code(token_code),
            "pair_code_ok":valid_code(pair_code),
        }
    except Exception as exc:
        return {"name":name,"url":url,"chain_ok":False,"token_code_ok":False,"pair_code_ok":False,
                "error":f"{type(exc).__name__}: {exc}"}

def select_endpoints(tokens,pairs):
    token_probe=str(tokens[0]["address"]).lower()
    pair_probe=str(pairs[0]["pair_address"]).lower()
    probes=[probe_endpoint(name,url,token_probe,pair_probe) for name,url in rpc_pool()]
    capable=[x for x in probes if x.get("chain_ok") and x.get("token_code_ok") and x.get("pair_code_ok")]
    if len(capable)<2:
        raise SystemExit("ONCHAIN_BINDING_NOT_ENOUGH_SEMANTIC_RPC "+json.dumps(probes))
    return capable[:2],probes

def token_bind(tokens,endpoints):
    observations={str(x["address"]).lower():[] for x in tokens}
    for ep in endpoints:
        name,url=ep["name"],ep["url"]
        addrs=sorted(observations)
        for off in range(0,len(addrs),BATCH_SIZE):
            chunk=addrs[off:off+BATCH_SIZE]
            calls=[];meta=[]
            for a in chunk:
                calls.append(("eth_getCode",[a,"latest"]));meta.append((a,"code"))
                calls.append(("eth_call",[{"to":a,"data":"0x313ce567"},"latest"]));meta.append((a,"decimals"))
                calls.append(("eth_call",[{"to":a,"data":"0x95d89b41"},"latest"]));meta.append((a,"symbol"))
                calls.append(("eth_call",[{"to":a,"data":"0x06fdde03"},"latest"]));meta.append((a,"name"))
            try:r=rpc(url,calls)
            except Exception as exc:
                for a in chunk: observations[a].append({"endpoint":name,"error":f"{type(exc).__name__}: {exc}"})
                continue
            tmp={a:{} for a in chunk}
            for i,(a,k) in enumerate(meta): tmp[a][k]=r.get(i,{}).get("result")
            for a in chunk:
                t=tmp[a]
                observations[a].append({
                    "endpoint":name,
                    "code_sha256":code_sha(t.get("code")),
                    "code_bytes":(len(t.get("code",""))-2)//2 if valid_code(t.get("code")) else None,
                    "decimals":uint(t.get("decimals")),
                    "symbol":strret(t.get("symbol")),
                    "name":strret(t.get("name")),
                })
    for row in tokens:
        a=str(row["address"]).lower()
        obs=[x for x in observations[a] if x.get("code_sha256")]
        hashes={x["code_sha256"] for x in obs}
        row["onchain_identity"]={
            "status":"VERIFIED_MULTI_RPC" if len(obs)>=2 and len(hashes)==1 else "OPEN",
            "observations":obs,
            "code_hash_consensus":len(obs)>=2 and len(hashes)==1,
        }
        if obs:
            row["static_decimals"]=obs[0].get("decimals")
            row["static_symbol"]=obs[0].get("symbol")
            row["static_name"]=obs[0].get("name")
            row["static_code_sha256"]=obs[0].get("code_sha256")
            row["static_code_bytes"]=obs[0].get("code_bytes")
    return tokens

def pair_bind(pairs,endpoints):
    observations={str(x["pair_address"]).lower():[] for x in pairs}
    selectors=[
        ("token0","0x0dfe1681"),
        ("token1","0xd21220a7"),
        ("factory","0xc45a0155"),
        ("reserves","0x0902f1ac"),
        ("slot0","0x3850c7bd"),
        ("liquidity","0x1a686502"),
        ("fee","0xddca3f43"),
    ]
    for ep in endpoints:
        name,url=ep["name"],ep["url"]
        addrs=sorted(observations)
        for off in range(0,len(addrs),max(1,BATCH_SIZE//2)):
            chunk=addrs[off:off+max(1,BATCH_SIZE//2)]
            calls=[];meta=[]
            for a in chunk:
                calls.append(("eth_getCode",[a,"latest"]));meta.append((a,"code"))
                for k,s in selectors:
                    calls.append(("eth_call",[{"to":a,"data":s},"latest"]));meta.append((a,k))
            try:r=rpc(url,calls)
            except Exception as exc:
                for a in chunk: observations[a].append({"endpoint":name,"error":f"{type(exc).__name__}: {exc}"})
                continue
            tmp={a:{} for a in chunk}
            for i,(a,k) in enumerate(meta): tmp[a][k]=r.get(i,{}).get("result")
            for a in chunk:
                t=tmp[a]
                observations[a].append({
                    "endpoint":name,
                    "code_sha256":code_sha(t.get("code")),
                    "token0":address(t.get("token0")),
                    "token1":address(t.get("token1")),
                    "factory":address(t.get("factory")),
                    "has_reserves":isinstance(t.get("reserves"),str) and len(t.get("reserves",""))>=194,
                    "has_slot0":isinstance(t.get("slot0"),str) and t.get("slot0") not in ("0x","0x0"),
                    "has_liquidity":uint(t.get("liquidity")) is not None,
                    "fee":uint(t.get("fee")),
                })
    for row in pairs:
        a=str(row["pair_address"]).lower()
        obs=[x for x in observations[a] if x.get("code_sha256")]
        hashes={x["code_sha256"] for x in obs}
        base=str((row.get("base_token") or {}).get("address") or "").lower()
        quote=str((row.get("quote_token") or {}).get("address") or "").lower()
        binding_matches=[]
        for x in obs:
            if x.get("token0") and x.get("token1") and {x["token0"],x["token1"]}=={base,quote}:
                binding_matches.append(x)
        if any(x.get("has_slot0") and x.get("has_liquidity") and x.get("fee") is not None for x in obs):
            adapter="V3_CONCENTRATED_LIQUIDITY"
        elif any(x.get("has_reserves") for x in obs):
            adapter="V2_CONSTANT_PRODUCT"
        elif obs:
            adapter="CUSTOM_OR_UNCLASSIFIED_EVM"
        else:
            adapter="UNBOUND"
        row["onchain_binding"]={
            "status":"VERIFIED_MULTI_RPC" if len(obs)>=2 and len(hashes)==1 else "OPEN",
            "observations":obs,
            "code_hash_consensus":len(obs)>=2 and len(hashes)==1,
            "adapter_family":adapter,
            "token_binding_match":len(binding_matches)>=2,
            "factory_addresses":sorted({x["factory"] for x in obs if x.get("factory")}),
        }
    return pairs

def main():
    tokens=jl(TOKEN_FILE);pairs=jl(PAIR_FILE)
    endpoints,all_probes=select_endpoints(tokens,pairs)
    tokens=token_bind(tokens,endpoints)
    pairs=pair_bind(pairs,endpoints)
    wjl(TOKEN_FILE,tokens);wjl(PAIR_FILE,pairs)

    pools=jl(POOL_FILE); pool_map={str(x.get("pool_ref")).lower():x for x in pools}
    for p in pairs:
        a=str(p["pair_address"]).lower(); b=p.get("onchain_binding") or {}
        if a in pool_map:
            pool_map[a].update({
                "adapter_family":b.get("adapter_family"),
                "onchain_binding_status":b.get("status"),
                "code_hash_consensus":b.get("code_hash_consensus"),
                "factory_addresses":b.get("factory_addresses",[]),
                "token_binding_match":b.get("token_binding_match"),
            })
    wjl(POOL_FILE,sorted(pool_map.values(),key=lambda x:str(x.get("pool_ref")).lower()))

    d=json.loads(DEX_FILE.read_text())
    for rec in d.get("records",[]):
        ns=str(rec.get("dex_namespace") or "").lower()
        bound=[p for p in pairs if str(p.get("dex_namespace") or "").lower()==ns]
        rec["factory_addresses"]=sorted({f for p in bound for f in (p.get("onchain_binding") or {}).get("factory_addresses",[])})
        rec["adapter_families_observed"]=sorted({(p.get("onchain_binding") or {}).get("adapter_family") for p in bound})
        rec["onchain_bound_pairs"]=sum(1 for p in bound if (p.get("onchain_binding") or {}).get("status")=="VERIFIED_MULTI_RPC")
        rec["token_binding_pairs"]=sum(1 for p in bound if (p.get("onchain_binding") or {}).get("token_binding_match"))
        rec["onchain_binding_status"]="VERIFIED_COMPLETE" if bound and rec["onchain_bound_pairs"]==len(bound) else ("PARTIAL" if rec["onchain_bound_pairs"] else "OPEN")
    d["binding"]={"rpc_endpoints":[x["name"] for x in endpoints],"observed_at":now(),"semantic_probe_passed":True}
    DEX_FILE.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")

    token_multi=sum(1 for x in tokens if (x.get("onchain_identity") or {}).get("status")=="VERIFIED_MULTI_RPC")
    pair_multi=sum(1 for x in pairs if (x.get("onchain_binding") or {}).get("status")=="VERIFIED_MULTI_RPC")
    pair_token_binding=sum(1 for x in pairs if (x.get("onchain_binding") or {}).get("token_binding_match"))
    adapter_counts={}
    for x in pairs:
        k=(x.get("onchain_binding") or {}).get("adapter_family","UNBOUND")
        adapter_counts[k]=adapter_counts.get(k,0)+1
    result={
        "schema":"polygon-static-onchain-binding-v2",
        "chain_id":137,
        "observed_at":now(),
        "rpc_endpoints":[x["name"] for x in endpoints],
        "rpc_blocks":{x["name"]:x.get("block") for x in endpoints},
        "semantic_rpc_probe":[
            {"name":x["name"],"chain_ok":x.get("chain_ok"),"token_code_ok":x.get("token_code_ok"),"pair_code_ok":x.get("pair_code_ok"),"block":x.get("block")}
            for x in all_probes
        ],
        "tokens":len(tokens),
        "token_multi_rpc":token_multi,
        "token_multi_rpc_complete":token_multi==len(tokens),
        "pairs":len(pairs),
        "pair_multi_rpc":pair_multi,
        "pair_multi_rpc_complete":pair_multi==len(pairs),
        "pair_token_binding_pairs":pair_token_binding,
        "adapter_family_counts":adapter_counts,
        "status":"GREEN" if token_multi==len(tokens) and pair_multi==len(pairs) else "OPEN",
        "static_boundary":"Contract identity/code is multi-RPC bound. Dynamic reserves, liquidity, price, fee state, gas, ordering and competition remain live inputs."
    }
    (P/"STATIC_ONCHAIN_BINDING.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    m=json.loads((P/"MASTER_INDEX.json").read_text())
    m.setdefault("static_inputs",{})["onchain_binding"]="STATIC_ONCHAIN_BINDING.json"
    m["onchain_binding_status"]=result["status"]
    m["onchain_binding_endpoints"]=result["rpc_endpoints"]
    m["static_closure_status"]="STATIC_MARKET_UNIVERSE_GREEN_WITH_MULTI_RPC_BINDING" if result["status"]=="GREEN" else "STATIC_MARKET_UNIVERSE_OPEN_ONCHAIN_BINDING"
    (P/"MASTER_INDEX.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    s=json.loads((P/"STATIC_SATURATION_MANIFEST.json").read_text())
    s["onchain_binding"]=result
    s["status"]="STATIC_MARKET_UNIVERSE_GREEN_WITH_MULTI_RPC_BINDING" if result["status"]=="GREEN" else "STATIC_MARKET_UNIVERSE_OPEN_ONCHAIN_BINDING"
    (P/"STATIC_SATURATION_MANIFEST.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")
    if result["status"]!="GREEN":
        raise SystemExit("STATIC_ONCHAIN_BINDING_OPEN "+json.dumps(result,sort_keys=True))
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
