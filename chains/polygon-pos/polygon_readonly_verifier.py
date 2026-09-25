#!/usr/bin/env python3
"""Read-only Polygon PoS verification runner.

No transaction submission, signing, private keys, or state-changing calls.
Writes JSONL observations and a resumable checkpoint.
"""
import argparse, hashlib, json, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ALLOWED = {
    "eth_chainId", "net_version", "web3_clientVersion",
    "eth_blockNumber", "eth_getBlockByNumber", "eth_getCode",
    "eth_call", "eth_getLogs", "eth_getTransactionByHash",
    "eth_getTransactionReceipt", "eth_getBlockByHash",
    "eth_gasPrice", "eth_feeHistory", "eth_estimateGas",
}
DENIED = {
    "eth_sendRawTransaction", "eth_sendTransaction",
    "personal_sign", "eth_sign", "eth_signTransaction",
}

def sha256(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def rpc(url, method, params, request_id, timeout):
    if method in DENIED or method not in ALLOWED:
        raise ValueError(f"method not allowed: {method}")
    payload = json.dumps({"jsonrpc": "2.0", "id": request_id,
                          "method": method, "params": params}).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"},
                 method="POST")
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read())
            status = response.status
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return {"ok": False, "latency_ms": round((time.perf_counter()-started)*1000, 2),
                "error": type(exc).__name__ + ": " + str(exc)}
    return {"ok": "error" not in body, "latency_ms": round((time.perf_counter()-started)*1000, 2),
            "http_status": status, "body": body}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", action="append", required=True)
    ap.add_argument("--out", default="polygon_rpc_observations.jsonl")
    ap.add_argument("--checkpoint", default="polygon_verifier_checkpoint.json")
    ap.add_argument("--timeout", type=float, default=12)
    args = ap.parse_args()

    methods = [
        ("eth_chainId", []),
        ("net_version", []),
        ("web3_clientVersion", []),
        ("eth_blockNumber", []),
        ("eth_getBlockByNumber", ["latest", False]),
        ("eth_gasPrice", []),
    ]
    checkpoint = {"version": 1, "chain_id_expected": 137, "completed": []}
    cp = Path(args.checkpoint)
    if cp.exists():
        checkpoint.update(json.loads(cp.read_text()))

    with open(args.out, "a", encoding="utf-8") as out:
        for endpoint_index, url in enumerate(args.rpc):
            endpoint_id = f"rpc-{endpoint_index+1}"
            for method, params in methods:
                key = f"{endpoint_id}:{method}"
                if key in checkpoint["completed"]:
                    continue
                obs = rpc(url, method, params, key, args.timeout)
                body = obs.get("body")
                result = body.get("result") if isinstance(body, dict) else None
                error = body.get("error") if isinstance(body, dict) else None
                record = {
                    "record_type": "polygon_verification",
                    "object_id": key,
                    "network": "polygon-pos-mainnet",
                    "chain_id": 137,
                    "observation_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "rpc_endpoint_id": endpoint_id,
                    "method": method,
                    "request": {"jsonrpc": "2.0", "id": key, "method": method, "params": params},
                    "outcome": {
                        "ok": bool(obs.get("ok")),
                        "result_hash_sha256": sha256(result) if result is not None else None,
                        "error_code": error.get("code") if isinstance(error, dict) else None,
                        "error_message": error.get("message") if isinstance(error, dict) else obs.get("error"),
                        "latency_ms": obs.get("latency_ms", 0),
                        "http_status": obs.get("http_status"),
                        "timeout": "Timeout" in str(obs.get("error", "")),
                        "rate_limited": False,
                        "stale_head": False,
                    },
                    "evidence_state": "PARTIAL" if obs.get("ok") else "UNVERIFIED",
                    "cross_rpc_agreement": None,
                    "notes": "Initial read-only capability probe; address verification is a later batch."
                }
                out.write(json.dumps(record, sort_keys=True) + "\n")
                out.flush()
                checkpoint["completed"].append(key)
                cp.write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(f"Wrote {args.out}; checkpoint {args.checkpoint}")

if __name__ == "__main__":
    main()
