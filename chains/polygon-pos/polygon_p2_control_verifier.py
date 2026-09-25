#!/usr/bin/env python3
"""Polygon P2 read-only control-plane storage verifier with adaptive RPC rotation."""
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


def make_record(endpoint_id, address, slot_name, obs, observation_block=None):
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
        "observation_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "observation_block": observation_block,
        "request": {
            "jsonrpc": "2.0",
            "id": f"{endpoint_id}:eth_getStorageAt:{address}:{slot_name}",
            "method": "eth_getStorageAt",
            "params": [address, ERC1967_SLOTS[slot_name], "latest"],
        },
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


def parse_identity(pool, endpoint_id, timeout, retries):
    chain = pool.request(endpoint_id, "eth_chainId", [], f"{endpoint_id}:eth_chainId", timeout, retries)
    block = pool.request(endpoint_id, "eth_blockNumber", [], f"{endpoint_id}:eth_blockNumber", timeout, retries)

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

    if chain.get("ok"):
        pool.mark_success(endpoint_id)
    else:
        pool.mark_failure(endpoint_id, chain)

    if block.get("ok"):
        pool.mark_success(endpoint_id)
    else:
        pool.mark_failure(endpoint_id, block)

    return endpoint_id, chain_id, block_number


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc-pool-file", required=True)
    parser.add_argument("--address", action="append", required=True)
    parser.add_argument("--out", default="polygon_p2_control_observations.jsonl")
    parser.add_argument("--summary", default="polygon_p2_control_head_summary.json")
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--min-request-interval", type=float, default=1.0)
    parser.add_argument(
        "--min-slot-endpoints",
        type=int,
        default=2,
        help="Minimum distinct chain-137 RPC endpoints required per target/slot",
    )
    parser.add_argument(
        "--recovery-rounds",
        type=int,
        default=2,
        help="Additional bounded slot-recovery passes after endpoint cooldown",
    )
    args = parser.parse_args()

    addresses = load_addresses(args.address)
    endpoints = load_rpc_endpoints(None, args.rpc_pool_file)
    pool = RpcPool(endpoints, args.min_request_interval)

    with ThreadPoolExecutor(max_workers=min(8, len(pool.endpoints))) as executor:
        futures = [
            executor.submit(parse_identity, pool, item["id"], args.timeout, args.retries)
            for item in pool.endpoints
        ]
        identity = [future.result() for future in futures]

    identity.sort()
    chain_ids = {endpoint_id: chain_id for endpoint_id, chain_id, _ in identity}
    blocks = {
        endpoint_id: block_number
        for endpoint_id, chain_id, block_number in identity
        if chain_id == 137 and block_number is not None
    }
    storage_eligible = {
        endpoint_id
        for endpoint_id, chain_id, _ in identity
        if chain_id == 137
    }

    if len(blocks) < 2:
        raise SystemExit(
            f"P2 head failure: fewer than 2 fresh chain-137 RPC endpoints ({len(blocks)})"
        )

    head_span = max(blocks.values()) - min(blocks.values())
    if head_span > 2:
        raise SystemExit(
            f"P2 head failure: chain-137 head span {head_span} exceeds tolerance 2 ({blocks})"
        )

    observations = []
    successful = {(address, slot): set() for address in addresses for slot in ERC1967_SLOTS}
    values = {(address, slot): {} for address in addresses for slot in ERC1967_SLOTS}

    def probe_one(address, slot_name):
        local = []
        for item in pool.ordered(storage_eligible):
            endpoint_id = item["id"]
            if endpoint_id in successful[(address, slot_name)]:
                continue
            obs = pool.request(
                endpoint_id,
                "eth_getStorageAt",
                [address, ERC1967_SLOTS[slot_name], "latest"],
                f"{endpoint_id}:eth_getStorageAt:{address}:{slot_name}",
                args.timeout,
                args.retries,
            )
            row = make_record(
                endpoint_id,
                address,
                slot_name,
                obs,
                observation_block=blocks.get(endpoint_id),
            )
            local.append(row)
            if obs.get("ok"):
                pool.mark_success(endpoint_id)
                successful[(address, slot_name)].add(endpoint_id)
                values[(address, slot_name)][endpoint_id] = obs["body"].get("result")
                if len(successful[(address, slot_name)]) >= args.min_slot_endpoints:
                    break
            else:
                pool.mark_failure(endpoint_id, obs)
        return local

    # Initial target/slot rotation.
    pairs = [(address, slot_name) for address in addresses for slot_name in ERC1967_SLOTS]
    with ThreadPoolExecutor(max_workers=min(8, len(pairs))) as executor:
        futures = [executor.submit(probe_one, address, slot_name) for address, slot_name in pairs]
        for future in futures:
            observations.extend(future.result())

    # Bounded recovery: rate-limited endpoints re-enter after cooldown.
    for recovery_round in range(1, max(1, args.recovery_rounds)):
        incomplete = [
            pair for pair in pairs
            if len(successful[pair]) < args.min_slot_endpoints
        ]
        if not incomplete:
            break

        cooldowns = [
            pool.state[eid]["cooldown_until"] - time.monotonic()
            for eid in storage_eligible
            if pool.state[eid]["cooldown_until"] > time.monotonic()
        ]
        if cooldowns:
            time.sleep(min(max(0.0, min(cooldowns)), 30.0))

        with ThreadPoolExecutor(max_workers=min(8, len(incomplete))) as executor:
            futures = [executor.submit(probe_one, address, slot_name) for address, slot_name in incomplete]
            for future in futures:
                observations.extend(future.result())

        print(
            f"P2 recovery round {recovery_round}: "
            f"remaining_slot_quorums={sum(1 for pair in pairs if len(successful[pair]) < args.min_slot_endpoints)}"
        )

    observations.sort(key=lambda row: row["object_id"])
    with open(args.out, "w", encoding="utf-8") as handle:
        for row in observations:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "chain_id_expected": 137,
        "identity_endpoints": len(blocks),
        "storage_eligible_endpoint_count": len(storage_eligible),
        "chain_ids": chain_ids,
        "rpc_blocks": blocks,
        "head_span": head_span,
        "rpc_pool_size": len(endpoints),
        "target_count": len(addresses),
        "slot_count_per_target": len(ERC1967_SLOTS),
        "record_count": len(observations),
        "observation_block": max(blocks.values()),
        "slots": ERC1967_SLOTS,
        "min_slot_endpoints_required": args.min_slot_endpoints,
        "slot_quorum_counts": {
            f"{address}:{slot}": len(successful[(address, slot)])
            for address, slot in pairs
        },
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    incomplete = {
        f"{address}:{slot}": sorted(successful[(address, slot)])
        for address, slot in pairs
        if len(successful[(address, slot)]) < args.min_slot_endpoints
    }
    if incomplete:
        raise SystemExit(
            "P2 storage failure: adaptive RPC rotation could not obtain the required "
            f"independent slot observations: {incomplete}"
        )

    print(f"P2 identity/head endpoints: {len(blocks)}")
    print(f"P2 storage-eligible endpoints: {len(storage_eligible)}")
    print(f"P2 storage records: {len(observations)}")
    print(f"P2 observation block: {summary['observation_block']}")


if __name__ == "__main__":
    main()
