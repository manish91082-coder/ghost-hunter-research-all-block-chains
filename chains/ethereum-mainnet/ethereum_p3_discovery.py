#!/usr/bin/env python3
"""Ethereum Mainnet P3 multi-source protocol/DEX discovery.

Discovery evidence only. No address, pool, liquidity or profitability is promoted
to VERIFIED by this script.
"""
import hashlib, json, re, time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
EVID=ROOT/"automation"/"evidence"
LLAMA_URL="https://api.llama.fi/protocols"
DEXSCREENER_URL="https://api.dexscreener.com/token-profiles/latest/v1"
GECKO_URL="https://api.geckoterminal.com/api/v2/networks/eth/dexes"
SAMPLES=2
MIN_OVERLAP=3

def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def sha(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def normalize(s):
    s=str(s or "").strip().lower()
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return re.sub(r"s+"," ",s).strip()

def fetch(url, timeout=25, retries=2):
    last=None
    for attempt in range(retries+1):
        req=Request(url,headers={"Accept":"application/json","User-Agent":"ghost-hunter-ethereum-p3-discovery/1.0"},method="GET")
        try:
            with urlopen(req,timeout=timeout) as resp:
                return resp.status,json.loads(resp.read()),None
        except HTTPError as e:
            last=f"HTTP {e.code}: {e}"
        except (URLError,TimeoutError,ValueError) as e:
            last=f"{type(e).__name__}: {e}"
        if attempt<retries: time.sleep(1.5*(attempt+1))
    return None,None,last

def llama_extract(payload):
    rows=payload if isinstance(payload,list) else []
    eth=[p for p in rows if "ethereum" in [str(x).lower() for x in (p.get("chains") or [])]]
    dex=[p for p in eth if normalize(p.get("category")) in {"dex","dexs","dexes"}]
    names=sorted({normalize(p.get("name") or p.get("slug")) for p in eth if normalize(p.get("name") or p.get("slug"))})
    dex_names=sorted({normalize(p.get("name") or p.get("slug")) for p in dex if normalize(p.get("name") or p.get("slug"))})
    return eth,dex,names,dex_names

def dexscreen_extract(payload):
    rows=payload if isinstance(payload,list) else []
    eth=[]
    for r in rows:
        cid=normalize(r.get("chainId"))
        if cid in {"ethereum","eth"}:
            eth.append(r)
    names=sorted({normalize(r.get("label") or r.get("name") or r.get("tokenAddress")) for r in eth if normalize(r.get("label") or r.get("name") or r.get("tokenAddress"))})
    return eth,names

def gecko_extract(payload):
    rows=payload.get("data") if isinstance(payload,dict) else []
    if not isinstance(rows,list): rows=[]
    names=sorted({normalize((r.get("attributes") or {}).get("name")) for r in rows if isinstance(r,dict) and normalize((r.get("attributes") or {}).get("name"))})
    return rows,names

def sample():
    st1,llama,e1=fetch(LLAMA_URL)
    st2,dex,e2=fetch(DEXSCREENER_URL)
    st3,gecko,e3=fetch(GECKO_URL)
    llama_eth,llama_dex,llama_names,llama_dex_names=llama_extract(llama)
    dex_eth,dex_names=dexscreen_extract(dex)
    gecko_rows,gecko_names=gecko_extract(gecko)
    overlap=sorted(set(llama_dex_names)&set(gecko_names))
    normalized={
      "llama_ethereum_protocols":llama_names,
      "llama_ethereum_dexes":llama_dex_names,
      "dexscreener_ethereum_profile_labels":dex_names,
      "gecko_ethereum_dexes":gecko_names
    }
    return {
      "time":now(),
      "http":{"defillama":st1,"dexscreener":st2,"geckoterminal":st3},
      "errors":{"defillama":e1,"dexscreener":e2,"geckoterminal":e3},
      "counts":{
        "ethereum_protocols":len(llama_eth),
        "ethereum_dex_protocols":len(llama_dex),
        "dexscreener_ethereum_profiles":len(dex_eth),
        "gecko_ethereum_dexes":len(gecko_rows)
      },
      "dex_name_overlap":overlap,
      "dex_name_overlap_count":len(overlap),
      "llama_duplicate_dex_names":len(llama_dex_names)-len(set(llama_dex_names)),
      "gecko_duplicate_dex_names":len(gecko_names)-len(set(gecko_names)),
      "normalized_universe":normalized,
      "fingerprint":sha(normalized)
    }

def main():
    EVID.mkdir(parents=True,exist_ok=True)
    closure=EVID/"ETHEREUM_P3_CLOSURE_STATE.json"
    previous=json.loads(closure.read_text()) if closure.exists() else {}
    samples=[]
    for _ in range(SAMPLES):
        samples.append(sample())
        time.sleep(1.0)
    first,second=samples[-2],samples[-1]
    checks={
      "defillama_ok": all(x["http"]["defillama"]==200 and not x["errors"]["defillama"] for x in samples),
      "dexscreener_ok": all(x["http"]["dexscreener"]==200 and not x["errors"]["dexscreener"] for x in samples),
      "geckoterminal_ok": all(x["http"]["geckoterminal"]==200 and not x["errors"]["geckoterminal"] for x in samples),
      "overlap_ok": all(x["dex_name_overlap_count"]>=MIN_OVERLAP for x in samples),
      "duplicate_free": all(x["llama_duplicate_dex_names"]==0 and x["gecko_duplicate_dex_names"]==0 for x in samples),
      "consecutive_sample_stable": first["fingerprint"]==second["fingerprint"]
    }
    gate=all(checks.values())
    out={
      "schema_version":"ethereum-p3-protocol-discovery-v1",
      "task":"ethereum_p3_protocol_discovery",
      "network":"ethereum",
      "chain_id":1,
      "sources":[LLAMA_URL,DEXSCREENER_URL,GECKO_URL],
      "samples":samples,
      "checks":checks,
      "stage_gate":"CLOSED" if gate else "OPEN",
      "evidence_class":"DISCOVERY",
      "boundary":"Discovery candidates only; no protocol/address/pool/liquidity/profitability VERIFIED claim.",
      "previous_fingerprint":previous.get("fingerprint"),
      "current_fingerprint":second["fingerprint"]
    }
    out["fingerprint"]=sha({"current":second["fingerprint"],"checks":checks})
    (EVID/"ETHEREUM_P3_PROTOCOL_SNAPSHOT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\\n")
    state={
      "fingerprint":second["fingerprint"],
      "stable_runs": 2 if first["fingerprint"]==second["fingerprint"] else 1,
      "stage_gate":"CLOSED" if gate else "OPEN",
      "updated_at":now()
    }
    closure.write_text(json.dumps(state,indent=2,sort_keys=True)+"\\n")
    if not gate:
        raise SystemExit("Ethereum P3 discovery failed closed")
    print("Ethereum P3 discovery CLOSED")
    print(second["fingerprint"])

if __name__=="__main__":
    main()
