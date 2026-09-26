#!/usr/bin/env python3
"""Read-only Ethereum P2 semantic-control verifier."""
import argparse, hashlib, itertools, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CHAIN_ID=1
MIN_ENDPOINTS=2
HEAD_TOLERANCE=2
DEPOSIT="0x00000000219ab540356cBB839Cbe05303d7705Fa"
BEACON="0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02"
WITHDRAWAL="0x00000961Ef480Eb55e80D19ad83579A64c007002"
CONSOLIDATION="0x0000BBdDc7CE488642fb579F8B00f3a590007251"

def validate_endpoint(url):
    if not isinstance(url,str) or not url.startswith("https://"): raise ValueError("HTTPS required")
    authority=url.split("://",1)[1].split("/",1)[0]
    if "@" in authority: raise ValueError("embedded credentials forbidden")

def load_pool(path):
    out=[]; seen=set()
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        s=raw.strip()
        if not s or s.startswith("#"): continue
        if "|" in s: eid,url=[x.strip() for x in s.split("|",1)]
        else: eid,url="",s
        validate_endpoint(url)
        if url in seen: continue
        seen.add(url); out.append({"id":eid or f"rpc-{len(out)+1:02d}","url":url})
    if not out: raise ValueError("empty RPC pool")
    return out

def call(url,params,timeout=12,retries=1):
    payload=json.dumps({"jsonrpc":"2.0","id":"gh-eth-p2-control","method":"eth_call","params":[params,"latest"]}).encode()
    last=None
    for attempt in range(retries+1):
        req=Request(url,data=payload,headers={"Accept":"application/json","Content-Type":"application/json","User-Agent":"ghost-hunter-ethereum-p2-control/1.0"},method="POST")
        try:
            with urlopen(req,timeout=timeout) as resp:
                body=json.loads(resp.read())
                return {"transport":True,"http":resp.status,"body":body,"attempt":attempt}
        except HTTPError as e:
            last={"transport":False,"http":e.code,"error":str(e),"attempt":attempt}
        except (URLError,TimeoutError,ValueError) as e:
            last={"transport":False,"http":None,"error":str(e),"attempt":attempt}
        if attempt<retries: time.sleep(1.25*(attempt+1))
    return last or {"transport":False,"http":None,"error":"unknown","attempt":retries}

def rpc_raw(url,method,params,timeout=12):
    payload=json.dumps({"jsonrpc":"2.0","id":"gh-eth-p2-control-meta","method":method,"params":params}).encode()
    req=Request(url,data=payload,headers={"Accept":"application/json","Content-Type":"application/json","User-Agent":"ghost-hunter-ethereum-p2-control/1.0"},method="POST")
    try:
        with urlopen(req,timeout=timeout) as resp: return {"transport":True,"http":resp.status,"body":json.loads(resp.read())}
    except (HTTPError,URLError,TimeoutError,ValueError) as e: return {"transport":False,"http":getattr(e,"code",None),"error":str(e)}

def sha(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def prepare_endpoint(ep,timeout):
    cid=rpc_raw(ep["url"],"eth_chainId",[],timeout)
    block=rpc_raw(ep["url"],"eth_blockNumber",[],timeout)
    latest=rpc_raw(ep["url"],"eth_getBlockByNumber",["latest",False],timeout)
    chain_id=(int(cid["body"]["result"],16) if cid.get("transport") and isinstance(cid.get("body"),dict) and isinstance(cid["body"].get("result"),str) else None)
    number=(int(block["body"]["result"],16) if block.get("transport") and isinstance(block.get("body"),dict) and isinstance(block["body"].get("result"),str) else None)
    obj=latest.get("body",{}).get("result") if isinstance(latest.get("body"),dict) else None
    ts=int(obj["timestamp"],16) if isinstance(obj,dict) and isinstance(obj.get("timestamp"),str) else None
    return {"endpoint_id":ep["id"],"chain_id":chain_id,"block":number,"timestamp":ts}

def build_calls(ts):
    beacon_data="0x"+format(ts,"064x")
    return [
      ("deposit_root",DEPOSIT,"0xc5f2892f","EXPECTED_SUCCESS"),
      ("deposit_count",DEPOSIT,"0x621fd130","EXPECTED_SUCCESS"),
      ("beacon_root_lookup",BEACON,beacon_data,"EXPECTED_SUCCESS_OR_DETERMINISTIC_REVERT"),
      ("withdrawal_fee_getter",WITHDRAWAL,"0x","EXPECTED_SUCCESS"),
      ("consolidation_fee_getter",CONSOLIDATION,"0x","EXPECTED_SUCCESS")
    ]

def run_endpoint(ep,ts,timeout):
    rows=[]
    for cid,target,data,expect in build_calls(ts):
        r=call(ep["url"],{"to":target,"data":data},timeout)
        body=r.get("body") if r.get("transport") else None
        result=body.get("result") if isinstance(body,dict) else None
        error=body.get("error") if isinstance(body,dict) else None
        classification="SUCCESS" if isinstance(result,str) else ("EVM_REVERT" if isinstance(error,dict) else "TRANSPORT_ERROR")
        rows.append({"endpoint_id":ep["id"],"control_id":cid,"target":target,"data":data,"expectation":expect,"classification":classification,"http_status":r.get("http"),"error_code":error.get("code") if isinstance(error,dict) else None,"raw_result":result,"result_sha256":sha(result) if result is not None else None,"error_message":error.get("message") if isinstance(error,dict) else r.get("error")})
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rpc-pool-file",default="chains/ethereum-mainnet/rpc_pool.txt")
    ap.add_argument("--target-file",default="chains/ethereum-mainnet/P2_CONTROL_TARGETS.json")
    ap.add_argument("--out",default="automation/evidence/ETHEREUM_P2_CONTROL_REPORT.json")
    ap.add_argument("--jsonl",default="automation/evidence/ETHEREUM_P2_CONTROL_OBSERVATIONS.jsonl")
    ap.add_argument("--timeout",type=float,default=12)
    args=ap.parse_args()
    pool=load_pool(args.rpc_pool_file)
    manifest=json.loads(Path(args.target_file).read_text(encoding="utf-8"))
    prepared=[prepare_endpoint(ep,args.timeout) for ep in pool]
    eligible=[x for x in prepared if x["chain_id"]==CHAIN_ID and x["block"] is not None and x["timestamp"] is not None]
    combos=[]
    for combo in itertools.combinations(eligible,MIN_ENDPOINTS):
        span=max(x["block"] for x in combo)-min(x["block"] for x in combo)
        if span<=HEAD_TOLERANCE: combos.append((span,combo))
    combos.sort(key=lambda x:x[0])
    quorum=combos[0][1] if combos else []
    if not quorum: raise SystemExit("Ethereum P2 control failed closed: no fresh chain-1 quorum")
    timestamp=max(x["timestamp"] for x in quorum)
    eps=[{"id":x["endpoint_id"],"url":next(ep["url"] for ep in pool if ep["id"]==x["endpoint_id"])} for x in eligible]
    rows=[]
    with ThreadPoolExecutor(max_workers=min(8,len(eps))) as ex:
        fs=[ex.submit(run_endpoint,ep,timestamp,args.timeout) for ep in eps]
        for f in as_completed(fs): rows.extend(f.result())
    rows.sort(key=lambda r:(r["endpoint_id"],r["control_id"]))
    results={}
    for cid,_,_,_ in build_calls(timestamp):
        obs={r["endpoint_id"]:(r["classification"],r["result_sha256"],r["error_code"]) for r in rows if r["control_id"]==cid and r["classification"] in ("SUCCESS","EVM_REVERT")}
        groups={}
        for eid,v in obs.items(): groups.setdefault(v,[]).append(eid)
        chosen=max(groups.items(),key=lambda kv:len(kv[1])) if groups else (None,[])
        sem_ok=len(chosen[1])>=MIN_ENDPOINTS and (chosen[0][0]=="SUCCESS" or cid=="beacon_root_lookup")
        if cid=="beacon_root_lookup": sem_ok=len(chosen[1])>=MIN_ENDPOINTS and chosen[0][0]=="SUCCESS"
        results[cid]={"observations":obs,"matching_independent_endpoints":chosen[1],"verified":sem_ok}
    verified=all(v["verified"] for v in results.values())
    report={"schema_version":"ethereum-p2-control-v1","evidence_class":"LIVE_RPC_SEMANTIC_CONTROL","chain":{"name":"Ethereum Mainnet","chain_id":1},"safety":{"read_only":True,"signing":False,"broadcast":False,"real_money":False},"fresh_quorum":{"endpoints":[x["endpoint_id"] for x in quorum],"blocks":{x["endpoint_id"]:x["block"] for x in quorum},"timestamps":{x["endpoint_id"]:x["timestamp"] for x in quorum},"span":max(x["block"] for x in quorum)-min(x["block"] for x in quorum),"tolerance":HEAD_TOLERANCE},"controls":results,"promotion":{"status":"VERIFIED" if verified else "PARTIAL","p2_control_sub_gate":"CLOSED" if verified else "OPEN"},"timestamp_used":timestamp,"fingerprint":sha({"quorum":quorum,"timestamp":timestamp,"controls":results})}
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    with Path(args.jsonl).open("w") as f:
        for row in rows: f.write(json.dumps(row,sort_keys=True)+"\n")
    if not verified: raise SystemExit("Ethereum P2 control semantic verification failed closed")
    print("Ethereum P2 semantic-control sub-gate VERIFIED")
    print(report["fingerprint"])

if __name__=="__main__": main()
