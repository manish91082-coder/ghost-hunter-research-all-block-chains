#!/usr/bin/env python3
"""One-endpoint P4 evidence shard for parallel GitHub Actions fan-out."""
import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(".")
EVID = ROOT / "automation" / "evidence"
POOL = ROOT / "chains" / "polygon-pos" / "rpc_pool.txt"
SNAPSHOT = EVID / "P4_TOKEN_SNAPSHOT.json"
VERIFY = EVID / "P4_VERIFICATION_STATE.json"
SHARDS = EVID / "fanout_shards"

MIN_INTERVAL = 1.0
START_CHUNK = 6
MIN_CHUNK = 1
MAX_RETRY_WAIT = 20


class RateLimited(RuntimeError):
    def __init__(self, retry_after=5.0):
        super().__init__("RPC rate limited")
        self.retry_after = retry_after


def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pool_map():
    result = {}
    if not POOL.exists():
        return result
    for raw in POOL.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "|" not in raw:
            continue
        endpoint_id, url = raw.split("|", 1)
        result[endpoint_id.strip()] = url.strip()
    return result


def retry_after(headers):
    try:
        return max(1.0, min(float(headers.get("Retry-After")), MAX_RETRY_WAIT))
    except (TypeError, ValueError, AttributeError):
        return 5.0


def post(url, payload, timeout=30):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if "tatum.io" in url and os.environ.get("TATUM_API_KEY"):
        req.add_header("X-API-Key", os.environ["TATUM_API_KEY"])
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RateLimited(retry_after(exc.headers))
        raise


def single(url, method, params, request_id):
    body = post(url, {"jsonrpc":"2.0","id":request_id,"method":method,"params":params})
    if not isinstance(body, dict):
        raise ValueError("non-dict single JSON-RPC response")
    return body


def batch(url, calls):
    payload = [
        {"jsonrpc":"2.0","id":request_id,"method":method,"params":params}
        for request_id, method, params in calls
    ]
    body = post(url, payload)
    if not isinstance(body, list):
        raise ValueError("endpoint rejected JSON-RPC batch response")
    return {str(x.get("id")): x for x in body if isinstance(x, dict)}


def result_of(row):
    return row.get("result") if isinstance(row, dict) else None


def candidate_addresses():
    snapshot = load_json(SNAPSHOT, {})
    verify = load_json(VERIFY, {}).get("verification", {})
    addresses = snapshot.get("candidate_addresses") or []
    return [
        address for address in addresses
        if not verify.get(address, {}).get("matching")
    ]


def observation(endpoint_id, code, decimals, supply):
    valid_code = isinstance(code, str) and code not in {"", "0x", "0X"}
    valid_decimals = isinstance(decimals, str) and decimals.startswith("0x")
    valid_supply = isinstance(supply, str) and supply.startswith("0x")
    if not (valid_code and valid_decimals and valid_supply):
        return None
    try:
        if not 0 <= int(decimals, 16) <= 255:
            return None
    except ValueError:
        return None
    return {
        "rpc": endpoint_id,
        "code_hash": hashlib.sha256(code.lower().encode()).hexdigest(),
        "decimals": decimals.lower(),
        "total_supply": supply.lower(),
    }


def probe(endpoint_id):
    pools = pool_map()
    url = pools.get(endpoint_id)
    if not url:
        return {
            "endpoint_id": endpoint_id,
            "status": "UNKNOWN_ENDPOINT",
            "observations": [],
        }

    try:
        chain = single(url, "eth_chainId", [], f"fanout:{endpoint_id}:chain")
        if str(result_of(chain)).lower() != "0x89":
            return {
                "endpoint_id": endpoint_id,
                "status": "NOT_POLYGON_137",
                "chain_id": result_of(chain),
                "observations": [],
            }

        addresses = candidate_addresses()
        observations = []
        errors = []
        offset = 0
        chunk_size = START_CHUNK

        while offset < len(addresses):
            chunk = addresses[offset:offset + chunk_size]
            calls = []
            for address in chunk:
                calls.extend([
                    (f"fanout:{endpoint_id}:{address}:code","eth_getCode",[address,"latest"]),
                    (f"fanout:{endpoint_id}:{address}:decimals","eth_call",[{"to":address,"data":"0x313ce567"},"latest"]),
                    (f"fanout:{endpoint_id}:{address}:supply","eth_call",[{"to":address,"data":"0x18160ddd"},"latest"]),
                ])

            try:
                rows = batch(url, calls)
                offset += len(chunk)
            except RateLimited as exc:
                if chunk_size > MIN_CHUNK:
                    chunk_size = max(MIN_CHUNK, chunk_size // 2)
                    time.sleep(exc.retry_after)
                    continue
                rows = {}
                for request_id, method, params in calls:
                    try:
                        rows[request_id] = single(url, method, params, request_id)
                    except Exception as single_exc:
                        errors.append({
                            "request_id": request_id,
                            "error": f"{type(single_exc).__name__}: {single_exc}",
                        })
                offset += len(chunk)

            for address in chunk:
                code = result_of(rows.get(f"fanout:{endpoint_id}:{address}:code", {}))
                decimals = result_of(rows.get(f"fanout:{endpoint_id}:{address}:decimals", {}))
                supply = result_of(rows.get(f"fanout:{endpoint_id}:{address}:supply", {}))

                valid_code = isinstance(code, str) and code not in {"", "0x", "0X"}
                valid_decimals = isinstance(decimals, str) and decimals.startswith("0x")
                valid_supply = isinstance(supply, str) and supply.startswith("0x")
                if valid_decimals:
                    try:
                        valid_decimals = 0 <= int(decimals, 16) <= 255
                    except ValueError:
                        valid_decimals = False

                obs = None
                if valid_code:
                    obs = {
                        "rpc": endpoint_id,
                        "code_hash": hashlib.sha256(code.lower().encode()).hexdigest(),
                        "decimals": decimals.lower() if valid_decimals else None,
                        "total_supply": supply.lower() if valid_supply else None,
                        "code_valid": True,
                        "decimals_valid": bool(valid_decimals),
                        "total_supply_valid": bool(valid_supply),
                    }

                if obs:
                    observations.append({
                        "address": address,
                        "observation": obs,
                        "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    })
            time.sleep(MIN_INTERVAL)

        return {
            "endpoint_id": endpoint_id,
            "status": "OK",
            "chain_id": 137,
            "candidate_count": len(addresses),
            "observation_count": len(observations),
            "observations": observations,
            "errors": errors[-50:],
        }
    except Exception as exc:
        return {
            "endpoint_id": endpoint_id,
            "status": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
            "observations": [],
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint-id", required=True)
    args = parser.parse_args()
    SHARDS.mkdir(parents=True, exist_ok=True)
    result = probe(args.endpoint_id)
    write_json(SHARDS / f"P4_SHARD_{args.endpoint_id}.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
