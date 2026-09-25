#!/usr/bin/env python3
"""Polygon P2 read-only parent control-function probe verifier.

This stage probes only explicit read-only eth_call selector candidates from the
canonical manifest. It does not submit transactions or infer semantics from a
selector alone. Reconciliation is required across two independent chain-137
RPC endpoints.
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from polygon_readonly_verifier import RpcPool, load_rpc_endpoints


def load_targets(path):
    targets = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 4:
            raise ValueError(f"Invalid control-function target line: {line}")
        parent, probe_id, calldata, semantic = parts
        if len(parent) != 42 or not parent.startswith("0x"):
            raise ValueError(f"Invalid parent address: {parent}")
        int(parent[2:], 16)
        if not calldata.startswith("0x") or len(calldata) < 10:
            raise ValueError(f"Invalid calldata selector: {calldata}")
        int(calldata[2:], 16)
        targets.append(
            {
                "parent": parent,
                "probe_id": probe_id,
                "calldata": calldata,
                "semantic_candidate": semantic,
            }
        )
    if not targets:
        raise ValueError("No control-function targets supplied")
    return targets


def make_record(endpoint_id, target, obs, observation_block):
    body = obs.get("body")
    result = body.get("result") if isinstance(body, dict) else None
    error = body.get("error") if isinstance(body, dict) else None
    return {
        "record_type": "polygon_p2_control_function",
        "object_id": (
            f"{endpoint_id}:eth_call:{target['parent']}:{target['probe_id']}"
        ),
        "network": "polygon-pos-mainnet",
        "chain_id": 137,
        "address": target["parent"],
        "rpc_endpoint_id": endpoint_id,
        "probe_type": "read_only_selector_candidate",
        "probe_id": target["probe_id"],
        "selector_calldata": target["calldata"],
        "semantic_candidate": target["semantic_candidate"],
        "method": "eth_call",
        "observation_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "observation_block": observation_block,
        "request": {
            "jsonrpc": "2.0",
            "id": (
                f"{endpoint_id}:eth_call:{target['parent']}:{target['probe_id']}"
            ),
            "method": "eth_call",
            "params": [
                {"to": target["parent"], "data": target["calldata"]},
                "latest",
            ],
        },
        "outcome": {
            "ok": bool(obs.get("ok")),
            "result": result,
            "error_code": error.get("code") if isinstance(error, dict) else None,
            "error_message": (
                error.get("message")
                if isinstance(error, dict)
                else obs.get("message")
            ),
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
    parser.add_argument(
        "--target-file",
        default="chains/polygon-pos/p2_control_function_targets.txt",
    )
    parser.add_argument("--out", default="polygon_p2_control_function_observations.jsonl")
    parser.add_argument(
        "--summary",
        default="polygon_p2_control_function_head_summary.json",
    )
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--min-request-interval", type=float, default=1.0)
    parser.add_argument("--stale-block-tolerance", type=int, default=2)
    parser.add_argument("--min-head-endpoints", type=int, default=2)
    parser.add_argument("--min-probe-endpoints", type=int, default=2)
    parser.add_argument("--recovery-rounds", type=int, default=2)
    args = parser.parse_args()

    targets = load_targets(args.target_file)
    endpoints = load_rpc_endpoints(None, args.rpc_pool_file)
    pool = RpcPool(endpoints, args.min_request_interval)

    def identity(item):
        endpoint_id = item["id"]
        chain = pool.request(
            endpoint_id, "eth_chainId", [], f"{endpoint_id}:eth_chainId", args.timeout, args.retries
        )
        block = pool.request(
            endpoint_id, "eth_blockNumber", [], f"{endpoint_id}:eth_blockNumber", args.timeout, args.retries
        )
        chain_id = None
        block_number = None
        if chain.get("ok"):
            try:
                chain_id = int(chain["body"]["result"], 16)
            except (KeyError, TypeError, ValueError):
                pass
            pool.mark_success(endpoint_id)
        else:
            pool.mark_failure(endpoint_id, chain)
        if block.get("ok"):
            try:
                block_number = int(block["body"]["result"], 16)
            except (KeyError, TypeError, ValueError):
                pass
            pool.mark_success(endpoint_id)
        else:
            pool.mark_failure(endpoint_id, block)
        return endpoint_id, chain_id, block_number

    with ThreadPoolExecutor(max_workers=min(8, len(pool.endpoints))) as executor:
        identity_rows = [future.result() for future in (
            executor.submit(identity, item) for item in pool.endpoints
        )]

    identity_rows.sort()
    chain_ids = {
        endpoint_id: chain_id
        for endpoint_id, chain_id, _ in identity_rows
        if chain_id is not None
    }
    blocks = {
        endpoint_id: block_number
        for endpoint_id, chain_id, block_number in identity_rows
        if chain_id == 137 and block_number is not None
    }
    eligible = set(blocks)
    if len(blocks) < args.min_head_endpoints:
        raise SystemExit(
            f"P2 control-function head failure: only {len(blocks)} fresh chain-137 endpoints"
        )

    from itertools import combinations

    quorum_candidates = []
    for combo in combinations(sorted(blocks.items()), args.min_head_endpoints):
        span = max(block for _, block in combo) - min(block for _, block in combo)
        quorum_candidates.append(
            (span, tuple(endpoint for endpoint, _ in combo))
        )
    quorum_candidates.sort()
    best_span, quorum_endpoints = quorum_candidates[0]
    if best_span > args.stale_block_tolerance:
        raise SystemExit(
            f"P2 control-function head failure: no quorum within tolerance "
            f"(blocks={blocks}, required={args.min_head_endpoints}, tolerance={args.stale_block_tolerance})"
        )

    observed = {index: set() for index in range(len(targets))}
    observations = []

    def probe(index):
        target = targets[index]
        local = []
        for item in pool.ordered(eligible):
            endpoint_id = item["id"]
            if endpoint_id in successful[index]:
                continue
            obs = pool.request(
                endpoint_id,
                "eth_call",
                [
                    {"to": target["parent"], "data": target["calldata"]},
                    "latest",
                ],
                f"{endpoint_id}:eth_call:{target['parent']}:{target['probe_id']}",
                args.timeout,
                args.retries,
            )
            local.append(
                make_record(
                    endpoint_id,
                    target,
                    obs,
                    blocks.get(endpoint_id),
                )
            )
            if isinstance(obs.get("body"), dict) and obs.get("http_status") == 200:
                observed[index].add(endpoint_id)
                if obs.get("ok"):
                    pool.mark_success(endpoint_id)
                else:
                    pool.mark_failure(endpoint_id, obs)
                if len(observed[index]) >= args.min_probe_endpoints:
                    break
            else:
                pool.mark_failure(endpoint_id, obs)
        return local

    with ThreadPoolExecutor(max_workers=min(8, len(targets))) as executor:
        futures = [executor.submit(probe, index) for index in range(len(targets))]
        for future in futures:
            observations.extend(future.result())

    for recovery_round in range(1, max(1, args.recovery_rounds)):
        incomplete = [
            index
            for index in range(len(targets))
            if len(observed[index]) < args.min_probe_endpoints
        ]
        if not incomplete:
            break
        cooldowns = [
            pool.state[eid]["cooldown_until"] - time.monotonic()
            for eid in eligible
            if pool.state[eid]["cooldown_until"] > time.monotonic()
        ]
        if cooldowns:
            time.sleep(min(max(0.0, min(cooldowns)), 30.0))
        with ThreadPoolExecutor(max_workers=min(8, len(incomplete))) as executor:
            futures = [executor.submit(probe, index) for index in incomplete]
            for future in futures:
                observations.extend(future.result())
        print(
            f"P2 control-function recovery round {recovery_round}: "
            f"remaining_probe_quorums={sum(1 for index in range(len(targets)) if len(observed[index]) < args.min_probe_endpoints)}"
        )

    observations.sort(key=lambda row: row["object_id"])
    with open(args.out, "w", encoding="utf-8") as handle:
        for row in observations:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "chain_id_expected": 137,
        "chain_ids": chain_ids,
        "rpc_blocks": blocks,
        "head_quorum_endpoints": list(quorum_endpoints),
        "head_quorum_block_span": best_span,
        "head_quorum_agreement": True,
        "target_count": len(targets),
        "record_count": len(observations),
        "min_probe_endpoints_required": args.min_probe_endpoints,
        "probe_quorum_counts": {
            f"{targets[index]['parent']}:{targets[index]['probe_id']}": len(observed[index])
            for index in range(len(targets))
        },
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    incomplete = {
        f"{targets[index]['parent']}:{targets[index]['probe_id']}": sorted(successful[index])
        for index in range(len(targets))
        if len(observed[index]) < args.min_probe_endpoints
    }
    if incomplete:
        raise SystemExit(
            f"P2 control-function failure: insufficient independent observations: {incomplete}"
        )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
