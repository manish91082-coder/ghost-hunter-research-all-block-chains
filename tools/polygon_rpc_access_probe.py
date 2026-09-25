#!/usr/bin/env python3
"""Low-cost Polygon RPC access reconnaissance.

Separate from P1 verification:
- only eth_chainId and eth_blockNumber;
- no address/code probes;
- no retries;
- one sequential request per endpoint;
- results select candidates, not P1 proof.
"""
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CANDIDATES = [
    ("drpc", "https://polygon.drpc.org"),
    ("tenderly", "https://tenderly.rpc.polygon.community"),
    ("publicnode", "https://polygon.publicnode.com"),
    ("tatum", "https://polygon-mainnet.gateway.tatum.io/"),
    ("nodies", "https://polygon-public.nodies.app/"),
    ("1rpc", "https://1rpc.io/matic"),
    ("quicknode-public", "https://rpc-mainnet.matic.quiknode.pro"),
    ("onfinality", "https://polygon.api.onfinality.io/public"),
    ("spectrum", "https://spectrumnodes.com/"),
]

def call(url, method, timeout=8):
    payload = json.dumps({"jsonrpc": "2.0", "id": method, "method": method, "params": []}).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read())
            return {
                "ok": "error" not in body,
                "http_status": response.status,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "result": body.get("result"),
                "error": body.get("error"),
            }
    except HTTPError as exc:
        return {"ok": False, "http_status": exc.code, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": str(exc)}
    except (URLError, TimeoutError, ValueError) as exc:
        return {"ok": False, "http_status": None, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": f"{type(exc).__name__}: {exc}"}

def main():
    rows = []
    for endpoint_id, url in CANDIDATES:
        chain = call(url, "eth_chainId")
        block = call(url, "eth_blockNumber") if chain["ok"] else {"ok": False, "http_status": None, "latency_ms": 0, "error": "skipped_after_chain_id_failure"}
        chain_id = None
        block_number = None
        if chain["ok"] and isinstance(chain.get("result"), str):
            try:
                chain_id = int(chain["result"], 16)
            except ValueError:
                pass
        if block["ok"] and isinstance(block.get("result"), str):
            try:
                block_number = int(block["result"], 16)
            except ValueError:
                pass
        rows.append({"endpoint_id": endpoint_id, "url": url, "chain_id": chain_id, "block_number": block_number, "chain_probe": chain, "block_probe": block, "observed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    with open("polygon_rpc_access_candidates.json", "w", encoding="utf-8") as out:
        json.dump(rows, out, indent=2, sort_keys=True)
    reachable = [r for r in rows if r["chain_id"] == 137 and r["block_number"] is not None]
    print(json.dumps({"candidate_count": len(rows), "reachable_polygon_count": len(reachable), "reachable_polygon": [{"endpoint_id": r["endpoint_id"], "block_number": r["block_number"]} for r in reachable]}, indent=2))
    if len(reachable) < 2:
        raise SystemExit("Fewer than two keyless candidates returned both chain ID 137 and a block number")

if __name__ == "__main__":
    main()
