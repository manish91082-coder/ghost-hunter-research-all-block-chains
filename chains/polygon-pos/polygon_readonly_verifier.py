#!/usr/bin/env python3
"""Read-only Polygon PoS RPC verifier.

Safety:
- No transaction submission.
- No signing/private keys.
- Only explicit read-only JSON-RPC allowlist.
- Evidence is append-only JSONL plus a resumable checkpoint.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ALLOWED = {
    "eth_chainId",
    "net_version",
    "web3_clientVersion",
    "eth_blockNumber",
    "eth_getBlockByNumber",
    "eth_getCode",
    "eth_call",
    "eth_getLogs",
    "eth_getTransactionByHash",
    "eth_getTransactionReceipt",
    "eth_getBlockByHash",
    "eth_gasPrice",
    "eth_feeHistory",
    "eth_estimateGas",
}
DENIED = {
    "eth_sendRawTransaction",
    "eth_sendTransaction",
    "personal_sign",
    "eth_sign",
    "eth_signTransaction",
    "eth_sendUnsignedTransaction",
}

def sha256(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def validate_endpoint(url):
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS RPC endpoints are permitted")
    if "@" in url.split("://", 1)[1].split("/", 1)[0]:
        raise ValueError("Embedded endpoint credentials are forbidden")

def rpc(url, method, params, request_id, timeout, retries):
    if method in DENIED or method not in ALLOWED:
        raise ValueError(f"Method not allowed: {method}")
    validate_endpoint(url)

    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }).encode()

    last_error = None
    for attempt in range(retries + 1):
        started = time.perf_counter()
        req = Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=timeout) as response:
                body = json.loads(response.read())
                return {
                    "ok": "error" not in body,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                    "http_status": response.status,
                    "body": body,
                    "attempt": attempt,
                }
        except HTTPError as exc:
            last_error = {
                "type": "HTTPError",
                "message": str(exc),
                "http_status": exc.code,
                "rate_limited": exc.code == 429,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "attempt": attempt,
            }
        except (URLError, TimeoutError, ValueError) as exc:
            last_error = {
                "type": type(exc).__name__,
                "message": str(exc),
                "http_status": None,
                "rate_limited": False,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "attempt": attempt,
            }
        if attempt < retries:
            time.sleep(min(2 ** attempt, 8))
    return {"ok": False, **last_error}

def make_record(endpoint_id, method, params, obs, address=None):
    body = obs.get("body")
    result = body.get("result") if isinstance(body, dict) else None
    error = body.get("error") if isinstance(body, dict) else None
    error_code = error.get("code") if isinstance(error, dict) else None
    rate_limited = bool(obs.get("rate_limited")) or error_code in {-32005, -429}
    observation_block = None

    if method == "eth_blockNumber" and isinstance(result, str):
        observation_block = result
    elif method == "eth_getBlockByNumber" and isinstance(result, dict):
        observation_block = result.get("number")

    return {
        "record_type": "polygon_verification",
        "object_id": f"{endpoint_id}:{method}:{address or 'network'}",
        "network": "polygon-pos-mainnet",
        "chain_id": 137,
        "address": address,
        "observation_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "observation_block": observation_block,
        "rpc_endpoint_id": endpoint_id,
        "method": method,
        "request": {
            "jsonrpc": "2.0",
            "id": f"{endpoint_id}:{method}:{address or 'network'}",
            "method": method,
            "params": params,
        },
        "outcome": {
            "ok": bool(obs.get("ok")),
            "result_hash_sha256": sha256(result) if result is not None else None,
            "error_code": error_code,
            "error_message": (
                error.get("message")
                if isinstance(error, dict)
                else obs.get("message")
            ),
            "latency_ms": obs.get("latency_ms", 0),
            "http_status": obs.get("http_status"),
            "timeout": "Timeout" in str(obs.get("message", "")),
            "rate_limited": rate_limited,
            "stale_head": False,
        },
        "evidence_state": "PARTIAL" if obs.get("ok") else "UNVERIFIED",
        "cross_rpc_agreement": None,
        "notes": (
            "Read-only capability probe."
            if address is None
            else "Read-only address code probe."
        ),
    }

def load_addresses(values):
    addresses = []
    for value in values or []:
        if value.startswith("@"):
            for line in Path(value[1:]).read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    addresses.append(line)
        else:
            addresses.append(value.strip())
    return list(dict.fromkeys(a for a in addresses if a))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc", action="append", required=True,
                        help="Repeat for independent HTTPS JSON-RPC endpoints")
    parser.add_argument("--address", action="append",
                        help="Repeat for addresses, or use @file.txt")
    parser.add_argument("--out", default="polygon_rpc_observations.jsonl")
    parser.add_argument("--checkpoint", default="polygon_verifier_checkpoint.json")
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--stale-block-tolerance", type=int, default=2)
    args = parser.parse_args()

    addresses = load_addresses(args.address)
    capability_methods = [
        ("eth_chainId", []),
        ("net_version", []),
        ("web3_clientVersion", []),
        ("eth_blockNumber", []),
        ("eth_getBlockByNumber", ["latest", False]),
        ("eth_gasPrice", []),
    ]

    checkpoint = {
        "version": 2,
        "chain_id_expected": 137,
        "completed": {},
    }
    cp = Path(args.checkpoint)
    if cp.exists():
        checkpoint.update(json.loads(cp.read_text()))

    block_numbers = {}
    with open(args.out, "a", encoding="utf-8") as out:
        for endpoint_index, url in enumerate(args.rpc, start=1):
            endpoint_id = f"rpc-{endpoint_index}"
            for method, params in capability_methods:
                key = f"{endpoint_id}:{method}:network"
                if checkpoint["completed"].get(key) == "ok":
                    continue
                obs = rpc(url, method, params, key, args.timeout, args.retries)
                record = make_record(endpoint_id, method, params, obs)
                out.write(json.dumps(record, sort_keys=True) + "\n")
                out.flush()
                checkpoint["completed"][key] = "ok" if obs.get("ok") else "failed"
                if method == "eth_blockNumber" and obs.get("ok"):
                    try:
                        block_numbers[endpoint_id] = int(obs["body"]["result"], 16)
                    except (KeyError, TypeError, ValueError):
                        pass
                cp.write_text(json.dumps(checkpoint, indent=2) + "\n")

            for address in addresses:
                key = f"{endpoint_id}:eth_getCode:{address}"
                if checkpoint["completed"].get(key) == "ok":
                    continue
                obs = rpc(
                    url,
                    "eth_getCode",
                    [address, "latest"],
                    key,
                    args.timeout,
                    args.retries,
                )
                record = make_record(
                    endpoint_id,
                    "eth_getCode",
                    [address, "latest"],
                    obs,
                    address=address,
                )
                out.write(json.dumps(record, sort_keys=True) + "\n")
                out.flush()
                checkpoint["completed"][key] = "ok" if obs.get("ok") else "failed"
                cp.write_text(json.dumps(checkpoint, indent=2) + "\n")

    if block_numbers:
        freshest = max(block_numbers.values())
        summary = {
            "chain_id_expected": 137,
            "freshest_observed_block": freshest,
            "stale_block_tolerance": args.stale_block_tolerance,
            "rpc_blocks": block_numbers,
            "stale_endpoints": [
                endpoint_id
                for endpoint_id, block in block_numbers.items()
                if freshest - block > args.stale_block_tolerance
            ],
        }
        Path("polygon_rpc_head_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )

    print(f"Wrote {args.out}")
    print(f"Checkpoint: {args.checkpoint}")
    if block_numbers:
        print(f"Freshest block observed: {max(block_numbers.values())}")

if __name__ == "__main__":
    main()
