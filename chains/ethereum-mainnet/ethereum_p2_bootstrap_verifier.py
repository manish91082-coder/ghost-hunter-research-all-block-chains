#!/usr/bin/env python3
"""Read-only Ethereum Mainnet P2 bootstrap verifier.

Purpose:
- Establish live chain-1 RPC identity/head evidence.
- Measure a bounded read-only JSON-RPC capability matrix.
- Preserve endpoint-specific diagnostics and deterministic quorum fingerprints.
- Never sign, broadcast, or alter chain state.

This is a P2 infrastructure sub-gate only. It does not verify contracts,
protocol addresses, pools, routes, economics, or profitability.
"""
import argparse
import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CHAIN_ID = 1
ALLOWED_METHODS = {
    "eth_chainId",
    "net_version",
    "web3_clientVersion",
    "eth_blockNumber",
    "eth_getBlockByNumber",
    "eth_gasPrice",
    "eth_feeHistory",
    "eth_getBalance",
    "eth_getCode",
    "eth_getStorageAt",
}
DENIED_METHODS = {
    "eth_sendRawTransaction",
    "eth_sendTransaction",
    "personal_sign",
    "eth_sign",
    "eth_signTransaction",
    "eth_sendUnsignedTransaction",
}

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ZERO_SLOT = "0x" + "00" * 32


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_endpoint(url):
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError("Only HTTPS RPC endpoints are permitted")
    authority = url.split("://", 1)[1].split("/", 1)[0]
    if "@" in authority:
        raise ValueError("Embedded endpoint credentials are forbidden")


def load_endpoints(path):
    entries = []
    seen = set()
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            endpoint_id, url = [x.strip() for x in line.split("|", 1)]
        else:
            endpoint_id, url = "", line
        validate_endpoint(url)
        if url in seen:
            continue
        seen.add(url)
        entries.append(
            {"id": endpoint_id or f"rpc-{len(entries)+1:02d}", "url": url}
        )
    if not entries:
        raise ValueError("RPC candidate pool is empty")
    return entries


def rpc_request(url, method, params, request_id, timeout, retries):
    if method in DENIED_METHODS or method not in ALLOWED_METHODS:
        raise ValueError(f"Method not allowed: {method}")
    validate_endpoint(url)

    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
    ).encode()

    last = None
    for attempt in range(retries + 1):
        started = time.perf_counter()
        req = Request(
            url,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "ghost-hunter-ethereum-p2-bootstrap/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=timeout) as response:
                body = json.loads(response.read())
                return {
                    "transport_ok": True,
                    "http_status": response.status,
                    "body": body,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                    "attempt": attempt,
                }
        except HTTPError as exc:
            last = {
                "transport_ok": False,
                "http_status": exc.code,
                "error_type": "HTTPError",
                "error_message": str(exc),
                "rate_limited": exc.code == 429,
                "retry_after_seconds": _retry_after(exc.headers.get("Retry-After")),
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "attempt": attempt,
            }
        except (URLError, TimeoutError, ValueError) as exc:
            last = {
                "transport_ok": False,
                "http_status": None,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "rate_limited": False,
                "retry_after_seconds": None,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "attempt": attempt,
            }
        if attempt < retries:
            delay = last.get("retry_after_seconds") if last else None
            time.sleep(min(max(float(delay or 2**attempt), 0.5), 8.0))
    return last or {
        "transport_ok": False,
        "http_status": None,
        "error_type": "Unknown",
        "error_message": "unknown failure",
        "rate_limited": False,
        "retry_after_seconds": None,
        "latency_ms": 0.0,
        "attempt": retries,
    }


def _retry_after(value):
    try:
        return max(0.5, min(float(value), 60.0))
    except (TypeError, ValueError):
        return None


def classify_method_observation(obs):
    if not obs.get("transport_ok"):
        if obs.get("http_status") == 429 or obs.get("rate_limited"):
            return "RATE_LIMITED"
        return "TRANSPORT_ERROR"
    body = obs.get("body")
    if not isinstance(body, dict):
        return "MALFORMED_RESPONSE"
    if "result" in body:
        return "SUCCESS"
    error = body.get("error")
    if not isinstance(error, dict):
        return "MALFORMED_RESPONSE"
    if error.get("code") == -32601:
        return "METHOD_UNAVAILABLE"
    return "EXECUTION_OR_PROVIDER_ERROR"


def probe_endpoint(endpoint, methods, timeout, retries, min_interval):
    endpoint_id = endpoint["id"]
    url = endpoint["url"]
    rows = []
    last_request = 0.0
    for method, params in methods:
        wait = min_interval - (time.monotonic() - last_request)
        if wait > 0:
            time.sleep(wait)
        result = rpc_request(
            url,
            method,
            params,
            f"{endpoint_id}:{method}",
            timeout,
            retries,
        )
        last_request = time.monotonic()
        body = result.get("body") if isinstance(result, dict) else None
        error = body.get("error") if isinstance(body, dict) else None
        value = body.get("result") if isinstance(body, dict) else None
        row = {
            "endpoint_id": endpoint_id,
            "url": url,
            "method": method,
            "params": params,
            "classification": classify_method_observation(result),
            "http_status": result.get("http_status"),
            "latency_ms": result.get("latency_ms"),
            "rate_limited": bool(result.get("rate_limited")),
            "retry_after_seconds": result.get("retry_after_seconds"),
            "error_code": error.get("code") if isinstance(error, dict) else None,
            "error_message": error.get("message") if isinstance(error, dict) else result.get("error_message"),
            "result_sha256": sha256(value) if value is not None else None,
            "raw_result": value,
        }
        rows.append(row)
    return rows


def parse_chain_id(row):
    value = row.get("raw_result")
    if not isinstance(value, str):
        return None
    try:
        return int(value, 16) if value.startswith("0x") else int(value)
    except ValueError:
        return None


def parse_block(row):
    value = row.get("raw_result")
    if not isinstance(value, str):
        return None
    try:
        return int(value, 16) if value.startswith("0x") else int(value)
    except ValueError:
        return None


def best_head_quorum(heads, minimum, tolerance):
    import itertools

    items = sorted((k, v) for k, v in heads.items() if isinstance(v, int))
    if len(items) < minimum or minimum < 2:
        return []
    candidates = []
    for combo in itertools.combinations(items, minimum):
        blocks = [b for _, b in combo]
        span = max(blocks) - min(blocks)
        if span <= tolerance:
            candidates.append((span, tuple(k for k, _ in combo)))
    candidates.sort()
    return list(candidates[0][1]) if candidates else []


def capability_matrix(rows, eligible_ids):
    methods = sorted({row["method"] for row in rows})
    matrix = {}
    for method in methods:
        matrix[method] = {}
        for endpoint_id in sorted(eligible_ids):
            observed = [
                row for row in rows
                if row["endpoint_id"] == endpoint_id and row["method"] == method
            ]
            matrix[method][endpoint_id] = (
                observed[-1]["classification"] if observed else "NOT_OBSERVED"
            )
    return matrix


def build_report(rows, tolerance, min_identity, min_heads):
    identity = {}
    heads = {}
    by_endpoint = {}

    for row in rows:
        by_endpoint.setdefault(row["endpoint_id"], []).append(row)
        if row["method"] == "eth_chainId" and row["classification"] == "SUCCESS":
            value = parse_chain_id(row)
            if value is not None:
                identity[row["endpoint_id"]] = value
        if row["method"] == "eth_blockNumber" and row["classification"] == "SUCCESS":
            value = parse_block(row)
            if value is not None:
                heads[row["endpoint_id"]] = value

    eligible = {
        endpoint_id for endpoint_id, value in identity.items() if value == CHAIN_ID
    }
    quorum = best_head_quorum(heads, min_heads, tolerance)
    chain_id_values = sorted(set(identity.values()))

    core_methods = {"eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"}
    core_matrix = {}
    for method in sorted(core_methods):
        core_matrix[method] = {
            endpoint_id: next(
                (row["classification"] for row in by_endpoint.get(endpoint_id, [])
                 if row["method"] == method),
                "NOT_OBSERVED",
            )
            for endpoint_id in sorted(eligible)
        }

    exact_identity_quorum = len(identity) >= min_identity and chain_id_values == [CHAIN_ID]
    head_quorum = len(quorum) >= min_heads

    fingerprint_input = {
        "chain_ids": identity,
        "heads": heads,
        "eligible_endpoints": sorted(eligible),
        "core_matrix": core_matrix,
    }

    return {
        "schema_version": "ethereum-p2-bootstrap-v1",
        "evidence_class": "LIVE_RPC_BOOTSTRAP",
        "generated_at": utc_now(),
        "chain": {
            "name": "Ethereum Mainnet",
            "chain_id_expected": CHAIN_ID,
        },
        "safety": {
            "read_only": True,
            "signing": False,
            "broadcast": False,
            "real_money": False,
        },
        "identity": {
            "observed_chain_ids": identity,
            "chain_id_values": chain_id_values,
            "minimum_identity_endpoints": min_identity,
            "quorum": exact_identity_quorum,
        },
        "head": {
            "observed_blocks": heads,
            "stale_block_tolerance": tolerance,
            "selected_quorum_endpoints": quorum,
            "quorum_block_span": (
                max(heads[e] for e in quorum) - min(heads[e] for e in quorum)
                if quorum else None
            ),
            "quorum": head_quorum,
        },
        "capability_matrix": core_matrix,
        "endpoint_count": len(by_endpoint),
        "eligible_chain1_endpoint_count": len(eligible),
        "deterministic_fingerprint": sha256(fingerprint_input),
        "promotion": {
            "sub_gate": "CLOSED" if exact_identity_quorum and head_quorum else "OPEN",
            "overall_ethereum_p2": "NOT_CLOSED",
            "reason": "RPC identity/head bootstrap only; contract/protocol/pool evidence is still required.",
        },
        "diagnostics": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc-pool-file", default="chains/ethereum-mainnet/rpc_pool.txt")
    parser.add_argument("--out", default="automation/evidence/ETHEREUM_P2_BOOTSTRAP_REPORT.json")
    parser.add_argument("--jsonl", default="automation/evidence/ETHEREUM_P2_BOOTSTRAP_OBSERVATIONS.jsonl")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--min-request-interval", type=float, default=1.0)
    parser.add_argument("--head-tolerance", type=int, default=2)
    parser.add_argument("--min-identity-endpoints", type=int, default=2)
    parser.add_argument("--min-head-endpoints", type=int, default=2)
    args = parser.parse_args()

    endpoints = load_endpoints(args.rpc_pool_file)
    methods = [
        ("eth_chainId", []),
        ("eth_blockNumber", []),
        ("eth_getBlockByNumber", ["latest", False]),
        ("net_version", []),
        ("web3_clientVersion", []),
        ("eth_gasPrice", []),
        ("eth_feeHistory", [1, "latest", [50]]),
        ("eth_getBalance", [ZERO_ADDRESS, "latest"]),
        ("eth_getCode", [ZERO_ADDRESS, "latest"]),
        ("eth_getStorageAt", [ZERO_ADDRESS, ZERO_SLOT, "latest"]),
    ]

    rows = []
    with ThreadPoolExecutor(max_workers=min(8, len(endpoints))) as executor:
        futures = {
            executor.submit(
                probe_endpoint,
                endpoint,
                methods,
                args.timeout,
                args.retries,
                args.min_request_interval,
            ): endpoint["id"]
            for endpoint in endpoints
        }
        for future in as_completed(futures):
            rows.extend(future.result())

    rows.sort(key=lambda r: (r["endpoint_id"], r["method"]))
    report = build_report(
        rows,
        tolerance=args.head_tolerance,
        min_identity=args.min_identity_endpoints,
        min_heads=args.min_head_endpoints,
    )

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with Path(args.jsonl).open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    if report["promotion"]["sub_gate"] != "CLOSED":
        raise SystemExit(
            "Ethereum P2 bootstrap failed closed: independent chain-1 identity/head quorum not satisfied."
        )

    print("Ethereum P2 bootstrap identity/head sub-gate CLOSED.")
    print(f"Eligible chain-1 endpoints: {report['eligible_chain1_endpoint_count']}")
    print(f"Head quorum: {report['head']['selected_quorum_endpoints']}")
    print(f"Fingerprint: {report['deterministic_fingerprint']}")


if __name__ == "__main__":
    main()
