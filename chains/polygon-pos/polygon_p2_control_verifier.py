#!/usr/bin/env python3
"""Polygon P2 read-only control-plane storage verifier.

Reads ERC-1967 implementation/admin/beacon storage slots from the bounded
chain-137 target set across all currently eligible Polygon RPC endpoints.

No writes, signing or transaction submission are permitted.
"""
import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from polygon_readonly_verifier import RpcPool, load_addresses, load_rpc_endpoints

ERC1967_SLOTS = {
    "implementation": "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
    "admin": "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103",
    "beacon": "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50",
}


def sha256(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def storage_address(result):
    if not isinstance(result, str):
        return None
    raw = result[2:] if result.startswith("0x") else result
    if len(raw) != 64:
        return None
    candidate = "0x" + raw[-40:]
    return candidate if int(raw, 16) else None


def record(endpoint_id, address, slot_name, slot_value, obs):
    body = obs.get("body")
    result = body.get("result") if isinstance(body, dict) else None
    error = body.get("error") if isinstance(body, dict) else None
    return {
        "record_type": "polygon_p2_control_storage",
        "object_id": f"{endpoint_id}:eth_getStorageAt:{address}:{slot_name}",
        "network": "polygon-pos-mainnet",
        "chain_id": 137,
        "address": address,
        "rpc_endpoint_id": endpoint_id,
        "probe_type": "eip1967_storage_slot",
        "slot_name": slot_name,
        "slot": ERC1967_SLOTS[slot_name],
        "method": "eth_getStorageAt",
        "request": {
            "jsonrpc": "2.0",
            "id": f"{endpoint_id}:eth_getStorageAt:{address}:{slot_name}",
            "method": "eth_getStorageAt",
            "params": [address, ERC1967_SLOTS[slot_name], "latest"],
        },
        "observation_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "outcome": {
            "ok": bool(obs.get("ok")),
            "result": result,
            "result_hash_sha256": sha256(result) if result is not None else None,
            "derived_address": storage_address(result),
            "error_code": error.get("code") if isinstance(error, dict) else None,
            "error_message": error.get("message") if isinstance(error, dict) else obs.get("message"),
            "http_status": obs.get("http_status"),
            "latency_ms": obs.get("latency_ms", 0),
            "rate_limited": bool(obs.get("rate_limited")),
            "retry_after_seconds": obs.get("retry_after_seconds"),
        },
        "evidence_state": "PARTIAL" if obs.get("ok") else "UNVERIFIED",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc-pool-file", required=True)
    parser.add_argument("--address", action="append", required=True)
    parser.add_argument("--out", default="polygon_p2_control_observations.jsonl")
    parser.add_argument("--summary", default="polygon_p2_control_head_summary.json")
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--min-request-interval", type=float, default=1.0)
    args = parser.parse_args()

    addresses = load_addresses(args.address)
    endpoints = load_rpc_endpoints(None, args.rpc_pool_file)
    pool = RpcPool(endpoints, args.min_request_interval)

    def probe_identity(item):
        endpoint_id = item["id"]
        chain = pool.request(endpoint_id, "eth_chainId", [], f"{endpoint_id}:eth_chainId", args.timeout, args.retries)
        block = pool.request(endpoint_id, "eth_blockNumber", [], f"{endpoint_id}:eth_blockNumber", args.timeout, args.retries)
        chain_id = None
        block_number = None
        if chain.get("ok"):
            try:
                chain_id = int(chain["body"]["result"], 16)
            except (KeyError, TypeError, ValueError):
                pass
        if block.get("ok"):
            try:
                block_number = int(block["body"]["result"], 16)
            except (KeyError, TypeError, ValueError):
                pass
        if chain.get("ok") and block.get("ok") and chain_id == 137:
            pool.mark_success(endpoint_id)
        else:
            pool.mark_failure(endpoint_id, chain if not chain.get("ok") else block)
        return endpoint_id, chain_id, block_number

    identity = []
    with ThreadPoolExecutor(max_workers=min(8, len(endpoints))) as executor:
        futures = [executor.submit(probe_identity, item) for item in pool.endpoints]
        for future in futures:
            identity.append(future.result())

    identity.sort()
    eligible = {
        endpoint_id
        for endpoint_id, chain_id, block_number in identity
        if chain_id == 137 and block_number is not None
    }
    blocks = {
        endpoint_id: block_number
        for endpoint_id, chain_id, block_number in identity
        if endpoint_id in eligible
    }

    all_records = []

    def probe_endpoint(endpoint_id):
        records = []
        for address in addresses:
            for slot_name in ERC1967_SLOTS:
                request_id = f"{endpoint_id}:eth_getStorageAt:{address}:{slot_name}"
                obs = pool.request(
                    endpoint_id,
                    "eth_getStorageAt",
                    [address, ERC1967_SLOTS[slot_name], "latest"],
                    request_id,
                    args.timeout,
                    args.retries,
                )
                records.append(record(endpoint_id, address, slot_name, ERC1967_SLOTS[slot_name], obs))
                if obs.get("ok"):
                    pool.mark_success(endpoint_id)
                else:
                    pool.mark_failure(endpoint_id, obs)
        return records

    with ThreadPoolExecutor(max_workers=max(1, len(eligible))) as executor:
        futures = [executor.submit(probe_endpoint, endpoint_id) for endpoint_id in sorted(eligible)]
        for future in futures:
            all_records.extend(future.result())

    with open(args.out, "w", encoding="utf-8") as handle:
        for row in sorted(all_records, key=lambda x: x["object_id"]):
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "chain_id_expected": 137,
        "identity_endpoints": len(eligible),
        "chain_ids": {endpoint_id: chain_id for endpoint_id, chain_id, _ in identity},
        "rpc_blocks": blocks,
        "rpc_pool_size": len(endpoints),
        "target_count": len(addresses),
        "slot_count_per_target": len(ERC1967_SLOTS),
        "record_count": len(all_records),
        "observation_block": max(blocks.values()) if blocks else None,
        "slots": ERC1967_SLOTS,
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if len(eligible) < 2:
        raise SystemExit(f"P2 identity failure: fewer than 2 chain-137 RPC endpoints ({len(eligible)})")

    print(f"P2 identity endpoints: {len(eligible)}")
    print(f"P2 storage records: {len(all_records)}")
    print(f"P2 observation block: {summary['observation_block']}")


if __name__ == "__main__":
    main()
