#!/usr/bin/env python3
"""Read-only Ethereum Mainnet P2 system/predeploy runtime-code verifier."""
import argparse, hashlib, itertools, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CHAIN_ID=1
MIN_ENDPOINTS=2
HEAD_TOLERANCE=2
DENIED={"eth_sendRawTransaction","eth_sendTransaction","personal_sign","eth_sign","eth_signTransaction","eth_sendUnsignedTransaction"}

def validate_endpoint(url):
    if not isinstance(url,str) or not url.startswith("https://"):
        raise ValueError("Only HTTPS endpoints are allowed")
    authority=url.split("://",1)[1].split("/",1)[0]
    if "@" in authority:
        raise ValueError("Embedded credentials are forbidden")

def load_pool(path):
    out=[]; seen=set()
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        s=raw.strip()
        if not s or s.startswith("#"): continue
        if "|" in s:
            eid,url=[x.strip() for x in s.split("|",1)]
        else:
            eid,url="",s
        validate_endpoint(url)
        if url in seen: continue
        seen.add(url); out.append({"id":eid or f"rpc-{len(out)+1:02d}","url":url})
    if not out: raise ValueError("RPC pool empty")
    return out

def rpc(url,method,params,timeout=12.0,retries=1):
    if method in DENIED: raise ValueError("Denied method")
    payload=json.dumps({"jsonrpc":"2.0","id":"gh-p2-system","method":method,"params":params}).encode()
    last=None
    for attempt in range(retries+1):
        req=Request(url,data=payload,headers={"Accept":"application/json","Content-Type":"application/json","User-Agent":"ghost-hunter-ethereum-p2-system/1.0"},method="POST")
        try:
            with urlopen(req,timeout=timeout) as resp:
                return {"ok":True,"http":resp.status,"body":json.loads(resp.read()),"attempt":attempt}
        except HTTPError as e:
            last={"ok":False,"http":e.code,"error":str(e),"attempt":attempt}
        except (URLError,TimeoutError,ValueError) as e:
            last={"ok":False,"http":None,"error":str(e),"attempt":attempt}
        if attempt<retries: time.sleep(1.5*(attempt+1))
    return last or {"ok":False,"http":None,"error":"unknown","attempt":retries}

def h(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def probe_endpoint(ep,targets,timeout):
    rows=[]
    for method,params in [("eth_chainId",[]),("eth_blockNumber",[])]+[
        ("eth_getCode",[t["address"],"latest"]) for t in targets
    ]:
        r=rpc(ep["url"],method,params,timeout=timeout)
        body=r.get("body") if r.get("ok") else None
        val=body.get("result") if isinstance(body,dict) else None
        err=body.get("error") if isinstance(body,dict) else None
        rows.append({
          "endpoint_id":ep["id"],"method":method,"address":params[0] if method=="eth_getCode" else None,
          "classification":"SUCCESS" if r.get("ok") and "result" in body else "ERROR",
          "http_status":r.get("http"),"error_code":err.get("code") if isinstance(err,dict) else None,
          "raw_result":val,"result_sha256":h(val) if val is not None else None
        })
    return rows

def parse_hex(v):
    try: return int(v,16) if isinstance(v,str) and v.startswith("0x") else None
    except ValueError: return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rpc-pool-file",default="chains/ethereum-mainnet/rpc_pool.txt")
    ap.add_argument("--target-file",default="chains/ethereum-mainnet/P2_SYSTEM_TARGETS.json")
    ap.add_argument("--out",default="automation/evidence/ETHEREUM_P2_SYSTEM_CODE_REPORT.json")
    ap.add_argument("--jsonl",default="automation/evidence/ETHEREUM_P2_SYSTEM_CODE_OBSERVATIONS.jsonl")
    ap.add_argument("--timeout",type=float,default=12)
    args=ap.parse_args()
    pool=load_pool(args.rpc_pool_file)
    manifest=json.loads(Path(args.target_file).read_text(encoding="utf-8"))
    targets=manifest["targets"]
    rows=[]
    with ThreadPoolExecutor(max_workers=min(8,len(pool))) as ex:
        fs=[ex.submit(probe_endpoint,ep,targets,args.timeout) for ep in pool]
        for f in as_completed(fs): rows.extend(f.result())
    rows.sort(key=lambda x:(x["endpoint_id"],x["method"],x["address"] or ""))
    ids={r["endpoint_id"]:parse_hex(r["raw_result"]) for r in rows if r["method"]=="eth_chainId" and r["classification"]=="SUCCESS"}
    ids={k:v for k,v in ids.items() if v is not None}
    heads={r["endpoint_id"]:parse_hex(r["raw_result"]) for r in rows if r["method"]=="eth_blockNumber" and r["classification"]=="SUCCESS"}
    heads={k:v for k,v in heads.items() if v is not None and ids.get(k)==CHAIN_ID}
    eligible=sorted(k for k,v in ids.items() if v==CHAIN_ID)
    combos=[]
    for combo in itertools.combinations(sorted(heads.items()),MIN_ENDPOINTS):
        span=max(v for _,v in combo)-min(v for _,v in combo)
        if span<=HEAD_TOLERANCE: combos.append((span,[k for k,_ in combo]))
    combos.sort()
    head_quorum=combos[0][1] if combos else []
    endpoint_results={}
    for t in targets:
        obs={}
        for r in rows:
            if r["method"]=="eth_getCode" and r["address"].lower()==t["address"].lower() and r["classification"]=="SUCCESS":
                obs.setdefault(r["endpoint_id"],r["result_sha256"])
        matching=[]
        for combo in itertools.combinations(sorted(obs),MIN_ENDPOINTS):
            if len({obs[e] for e in combo})==1: matching=list(combo); break
        endpoint_results[t["id"]]={"address":t["address"],"observations":obs,"matching_independent_endpoints":matching,"verified":len(matching)>=MIN_ENDPOINTS}
    all_verified=bool(head_quorum) and all(x["verified"] for x in endpoint_results.values())
    report={
      "schema_version":"ethereum-p2-system-code-v1",
      "evidence_class":"LIVE_RPC_SYSTEM_CODE",
      "chain":{"name":"Ethereum Mainnet","chain_id":CHAIN_ID},
      "safety":{"read_only":True,"signing":False,"broadcast":False,"real_money":False},
      "manifest":{"target_count":len(targets),"target_ids":[t["id"] for t in targets]},
      "identity":{"observed_chain_ids":ids,"eligible_endpoints":eligible,"quorum":len(eligible)>=MIN_ENDPOINTS and sorted(set(ids.values()))==[CHAIN_ID]},
      "head":{"observed_blocks":heads,"selected_quorum":head_quorum,"span":(max(heads[e] for e in head_quorum)-min(heads[e] for e in head_quorum)) if head_quorum else None,"tolerance":HEAD_TOLERANCE,"quorum":len(head_quorum)>=MIN_ENDPOINTS},
      "targets":endpoint_results,
      "promotion":{"status":"VERIFIED" if all_verified else "PARTIAL","p2_system_code_sub_gate":"CLOSED" if all_verified else "OPEN"},
      "fingerprint":h({"identity":ids,"heads":heads,"targets":endpoint_results})
    }
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    with Path(args.jsonl).open("w",encoding="utf-8") as f:
        for row in rows: f.write(json.dumps(row,sort_keys=True)+"\n")
    if not all_verified: raise SystemExit("Ethereum P2 system-code verification failed closed")
    print("Ethereum P2 system-code sub-gate VERIFIED")
    print(report["fingerprint"])

if __name__=="__main__": main()
