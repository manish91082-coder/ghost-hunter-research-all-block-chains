#!/usr/bin/env python3
"""Read-only Polygon PoS RPC verifier with adaptive request-level RPC rotation.

Safety:
- No transaction submission.
- No signing/private keys.
- Only explicit read-only JSON-RPC allowlist.
- Evidence is append-only JSONL plus a resumable checkpoint.

Rotation doctrine:
- The configured RPC set is a candidate pool, not a trust list.
- Network identity/head probes are used to build an eligible pool.
- Address-code probes rotate across eligible endpoints when an endpoint is
  rate-limited, forbidden, unavailable or otherwise unhealthy.
- A critical target only counts toward the P1 code gate when two distinct
  independent endpoint IDs successfully return code.
- No majority vote is used to resolve conflicting code hashes.
"""
import argparse
import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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
    "eth_getStorageAt",
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


def parse_retry_after(value):
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def rpc(url, method, params, request_id, timeout, retries, min_request_interval=0.0):
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
        if min_request_interval > 0:
            time.sleep(min_request_interval)
        started = time.perf_counter()
        headers = {"Content-Type": "application/json"}
        if "tatum.io" in url and os.environ.get("TATUM_API_KEY"):
            headers["X-API-Key"] = os.environ["TATUM_API_KEY"]
        req = Request(
            url,
            data=payload,
            headers=headers,
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
                    "retry_after_seconds": None,
                }
        except HTTPError as exc:
            retry_after = parse_retry_after(exc.headers.get("Retry-After"))
            last_error = {
                "type": "HTTPError",
                "message": str(exc),
                "http_status": exc.code,
                "rate_limited": exc.code == 429,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "attempt": attempt,
                "retry_after_seconds": retry_after,
            }
        except (URLError, TimeoutError, ValueError) as exc:
            last_error = {
                "type": type(exc).__name__,
                "message": str(exc),
                "http_status": None,
                "rate_limited": False,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "attempt": attempt,
                "retry_after_seconds": None,
            }
        if attempt < retries:
            retry_after = last_error.get("retry_after_seconds") if last_error else None
            time.sleep(min(retry_after if retry_after is not None else 2 ** attempt, 8))
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
            "retry_after_seconds": obs.get("retry_after_seconds"),
        },
        "evidence_state": "PARTIAL" if obs.get("ok") else "UNVERIFIED",
        "cross_rpc_agreement": None,
        "notes": (
            "Read-only capability probe."
            if address is None
            else "Read-only address code probe with adaptive RPC rotation."
        ),
    }


def validate_address(value):
    if len(value) != 42 or not value.startswith("0x"):
        raise ValueError(f"Invalid EVM address: {value}")
    try:
        int(value[2:], 16)
    except ValueError as exc:
        raise ValueError(f"Invalid EVM address: {value}") from exc


def load_addresses(values):
    addresses = []
    for value in values or []:
        if value.startswith("@"):
            for line in Path(value[1:]).read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    addresses.append(line)
        else:
            addresses.append(value.strip())
    addresses = list(dict.fromkeys(a for a in addresses if a))
    for address in addresses:
        validate_address(address)
    return addresses


def load_rpc_endpoints(values, pool_file=None):
    """Return stable endpoint IDs and URLs from direct args and/or a pool file.

    Pool-file format:
      endpoint-id|https://example-rpc.invalid

    A URL-only line is accepted and receives a deterministic rpc-NN ID.
    """
    entries = []
    seen_urls = set()

    def add(endpoint_id, url):
        url = url.strip()
        if not url or url.startswith("#") or url in seen_urls:
            return
        validate_endpoint(url)
        seen_urls.add(url)
        entries.append((endpoint_id, url))

    for value in values or []:
        if value.startswith("@"):
            path = Path(value[1:])
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "|" in line:
                    endpoint_id, url = [part.strip() for part in line.split("|", 1)]
                else:
                    endpoint_id, url = "", line
                add(endpoint_id or f"rpc-{len(entries) + 1:02d}", url)
        else:
            add(f"rpc-{len(entries) + 1:02d}", value)

    if pool_file:
        path = Path(pool_file)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                endpoint_id, url = [part.strip() for part in line.split("|", 1)]
            else:
                endpoint_id, url = "", line
            add(endpoint_id or f"rpc-{len(entries) + 1:02d}", url)

    if not entries:
        raise ValueError("At least one RPC endpoint is required")
    return entries


class RpcPool:
    """Small adaptive pool with per-endpoint pacing and failure cooldowns."""

    def __init__(self, endpoints, min_request_interval):
        self.endpoints = [
            {"id": endpoint_id, "url": url, "index": index}
            for index, (endpoint_id, url) in enumerate(endpoints)
        ]
        self.state = {
            item["id"]: {
                "failures": 0,
                "cooldown_until": 0.0,
                "last_request_at": 0.0,
                "request_interval": max(0.0, min_request_interval),
                "lock": threading.Lock(),
            }
            for item in self.endpoints
        }
        self.min_request_interval = max(0.0, min_request_interval)
        self.state_lock = threading.Lock()

    def ordered(self, eligible_ids=None):
        now = time.monotonic()
        allowed = set(eligible_ids) if eligible_ids is not None else None
        with self.state_lock:
            rows = []
            for item in self.endpoints:
                if allowed is not None and item["id"] not in allowed:
                    continue
                state = self.state[item["id"]]
                rows.append((
                    state["cooldown_until"] > now,
                    state["failures"],
                    item["index"],
                    item,
                ))
        rows.sort(key=lambda row: (row[0], row[1], row[2]))
        return [row[3] for row in rows]

    def request(self, endpoint_id, method, params, request_id, timeout, retries):
        state = self.state[endpoint_id]
        with state["lock"]:
            now = time.monotonic()
            wait = state["request_interval"] - (now - state["last_request_at"])
            if wait > 0:
                time.sleep(wait)
            state["last_request_at"] = time.monotonic()
            return rpc(
                self.endpoint_url(endpoint_id),
                method,
                params,
                request_id,
                timeout,
                retries,
                min_request_interval=0.0,
            )

    def endpoint_url(self, endpoint_id):
        for item in self.endpoints:
            if item["id"] == endpoint_id:
                return item["url"]
        raise KeyError(endpoint_id)

    def mark_success(self, endpoint_id):
        with self.state_lock:
            state = self.state[endpoint_id]
            state["failures"] = 0
            state["cooldown_until"] = 0.0
            state["request_interval"] = max(
                self.min_request_interval,
                state["request_interval"] * 0.85,
            )

    def mark_failure(self, endpoint_id, obs):
        status = obs.get("http_status")
        retry_after = obs.get("retry_after_seconds")
        if retry_after is not None:
            cooldown = min(max(retry_after, 1.0), 120.0)
        elif status == 429 or obs.get("rate_limited"):
            cooldown = 15.0
        elif status in {401, 403, 404}:
            cooldown = 120.0
        else:
            cooldown = 5.0

        with self.state_lock:
            state = self.state[endpoint_id]
            state["failures"] += 1
            if status == 429 or obs.get("rate_limited"):
                state["request_interval"] = min(
                    max(self.min_request_interval, state["request_interval"] * 2.0),
                    4.0,
                )
            state["cooldown_until"] = max(
                state["cooldown_until"],
                time.monotonic() + cooldown,
            )


def read_existing_rows(path):
    if not Path(path).exists():
        return []
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_checkpoint(path, completed):
    payload = {
        "version": 3,
        "chain_id_expected": 137,
        "completed": completed,
        "updated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rpc",
        action="append",
        help="Repeat for independent HTTPS JSON-RPC endpoints, or use @pool-file",
    )
    parser.add_argument(
        "--rpc-pool-file",
        help="Pool file with endpoint-id|URL lines; endpoints rotate on failure",
    )
    parser.add_argument(
        "--address",
        action="append",
        help="Repeat for addresses, or use @file.txt",
    )
    parser.add_argument("--out", default="polygon_rpc_observations.jsonl")
    parser.add_argument("--checkpoint", default="polygon_verifier_checkpoint.json")
    parser.add_argument("--timeout", type=float, default=12)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--min-request-interval",
        type=float,
        default=0.5,
        help="Minimum seconds between attempts on the same RPC endpoint",
    )
    parser.add_argument("--stale-block-tolerance", type=int, default=2)
    parser.add_argument(
        "--min-code-endpoints",
        type=int,
        default=2,
        help="Minimum distinct successful RPC endpoints required per critical target",
    )
    parser.add_argument(
        "--code-recovery-rounds",
        type=int,
        default=2,
        help="Total address-code passes, allowing cooled RPCs to re-enter after rate limits",
    )
    parser.add_argument(
        "--reuse-checkpoint",
        action="store_true",
        help="Reuse successful probes already present in both checkpoint and JSONL output",
    )
    args = parser.parse_args()

    addresses = load_addresses(args.address)
    endpoints = load_rpc_endpoints(args.rpc, args.rpc_pool_file)
    pool = RpcPool(endpoints, args.min_request_interval)
    existing_rows = read_existing_rows(args.out)

    checkpoint = {
        "version": 3,
        "chain_id_expected": 137,
        "completed": {},
    }
    cp = Path(args.checkpoint)
    if cp.exists():
        checkpoint.update(json.loads(cp.read_text(encoding="utf-8")))

    existing_success_keys = {
        row["object_id"]
        for row in existing_rows
        if row.get("outcome", {}).get("ok") is True and row.get("object_id")
    }

    # Phase A: cheap network identity/head discovery across the full pool.
    identity_methods = [
        ("eth_chainId", []),
        ("eth_blockNumber", []),
    ]

    def probe_identity(item):
        endpoint_id = item["id"]
        records = []
        chain_id = None
        block_number = None
        completed = {}

        for method, params in identity_methods:
            key = f"{endpoint_id}:{method}:network"
            if (
                args.reuse_checkpoint
                and checkpoint["completed"].get(key) == "ok"
                and key in existing_success_keys
            ):
                continue

            obs = pool.request(
                endpoint_id,
                method,
                params,
                key,
                args.timeout,
                args.retries,
            )
            record = make_record(endpoint_id, method, params, obs)
            records.append(record)
            completed[key] = "ok" if obs.get("ok") else "failed"

            if obs.get("ok"):
                pool.mark_success(endpoint_id)
            else:
                pool.mark_failure(endpoint_id, obs)

            if method == "eth_chainId" and obs.get("ok"):
                try:
                    chain_id = int(obs["body"]["result"], 16)
                except (KeyError, TypeError, ValueError):
                    pass
            if method == "eth_blockNumber" and obs.get("ok"):
                try:
                    block_number = int(obs["body"]["result"], 16)
                except (KeyError, TypeError, ValueError):
                    pass

        return endpoint_id, records, completed, chain_id, block_number

    identity_results = []
    with ThreadPoolExecutor(max_workers=min(len(endpoints), 8)) as executor:
        futures = [executor.submit(probe_identity, item) for item in pool.endpoints]
        for future in futures:
            identity_results.append(future.result())

    identity_results.sort(key=lambda item: item[0])

    all_records = []
    chain_ids = {}
    block_numbers = {}
    checkpoint_completed = dict(checkpoint.get("completed", {}))

    for endpoint_id, records, completed, chain_id, block_number in identity_results:
        all_records.extend(records)
        checkpoint_completed.update(completed)
        if chain_id is not None:
            chain_ids[endpoint_id] = chain_id
        if block_number is not None:
            block_numbers[endpoint_id] = block_number

    # Rebuild identity/head observations from the current evidence file too.
    for row in existing_rows:
        if row.get("method") == "eth_chainId" and row.get("outcome", {}).get("ok") is True:
            result_hash = row.get("outcome", {}).get("result_hash_sha256")
            body_value = row.get("request", {}).get("params")
            if body_value == []:
                # The result value itself is not retained, so trust only fresh current-run
                # observations for numeric quorum calculations.
                pass

    eligible_for_code = {
        endpoint_id
        for endpoint_id, value in chain_ids.items()
        if value == 137
    }

    # Phase B: enrich only endpoints that proved Polygon identity.
    enrichment_methods = [
        ("net_version", []),
        ("web3_clientVersion", []),
        ("eth_getBlockByNumber", ["latest", False]),
        ("eth_gasPrice", []),
    ]

    def probe_enrichment(endpoint_id):
        records = []
        completed = {}
        for method, params in enrichment_methods:
            key = f"{endpoint_id}:{method}:network"
            if (
                args.reuse_checkpoint
                and checkpoint["completed"].get(key) == "ok"
                and key in existing_success_keys
            ):
                continue
            obs = pool.request(
                endpoint_id,
                method,
                params,
                key,
                args.timeout,
                args.retries,
            )
            records.append(make_record(endpoint_id, method, params, obs))
            completed[key] = "ok" if obs.get("ok") else "failed"
            if obs.get("ok"):
                pool.mark_success(endpoint_id)
            else:
                pool.mark_failure(endpoint_id, obs)
        return endpoint_id, records, completed

    if eligible_for_code:
        with ThreadPoolExecutor(max_workers=min(len(eligible_for_code), 8)) as executor:
            futures = [
                executor.submit(probe_enrichment, endpoint_id)
                for endpoint_id in sorted(eligible_for_code)
            ]
            for future in futures:
                endpoint_id, records, completed = future.result()
                all_records.extend(records)
                checkpoint_completed.update(completed)

    # Phase C: adaptive address-level rotation.
    code_successes = {address: set() for address in addresses}
    for row in existing_rows + all_records:
        if (
            row.get("method") == "eth_getCode"
            and row.get("outcome", {}).get("ok") is True
            and row.get("address") in code_successes
            and row.get("rpc_endpoint_id") in eligible_for_code
        ):
            code_successes[row["address"]].add(row["rpc_endpoint_id"])

    for address in addresses:
        if len(code_successes[address]) >= args.min_code_endpoints:
            continue

        for item in pool.ordered(eligible_for_code):
            endpoint_id = item["id"]
            if endpoint_id in code_successes[address]:
                continue

            key = f"{endpoint_id}:eth_getCode:{address}"
            if (
                args.reuse_checkpoint
                and checkpoint["completed"].get(key) == "ok"
                and key in existing_success_keys
            ):
                code_successes[address].add(endpoint_id)
                if len(code_successes[address]) >= args.min_code_endpoints:
                    break
                continue

            obs = pool.request(
                endpoint_id,
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
            all_records.append(record)
            checkpoint_completed[key] = "ok" if obs.get("ok") else "failed"

            if obs.get("ok"):
                pool.mark_success(endpoint_id)
                code_successes[address].add(endpoint_id)
                if len(code_successes[address]) >= args.min_code_endpoints:
                    break
            else:
                pool.mark_failure(endpoint_id, obs)

    # Recovery passes let rate-limited endpoints re-enter the rotation pool
    # after their cooldown instead of permanently losing the rest of the batch.
    for recovery_round in range(1, max(1, args.code_recovery_rounds)):
        incomplete_addresses = [
            address
            for address in addresses
            if len(code_successes[address]) < args.min_code_endpoints
        ]
        if not incomplete_addresses:
            break

        cooldown_waits = []
        now = time.monotonic()
        for endpoint_id in eligible_for_code:
            state = pool.state[endpoint_id]
            if state["cooldown_until"] > now:
                cooldown_waits.append(state["cooldown_until"] - now)
        if cooldown_waits:
            time.sleep(min(max(0.0, min(cooldown_waits)), 30.0))

        for address in incomplete_addresses:
            for item in pool.ordered(eligible_for_code):
                endpoint_id = item["id"]
                if endpoint_id in code_successes[address]:
                    continue

                key = f"{endpoint_id}:eth_getCode:{address}"
                obs = pool.request(
                    endpoint_id,
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
                all_records.append(record)
                checkpoint_completed[key] = "ok" if obs.get("ok") else "failed"

                if obs.get("ok"):
                    pool.mark_success(endpoint_id)
                    code_successes[address].add(endpoint_id)
                    if len(code_successes[address]) >= args.min_code_endpoints:
                        break
                else:
                    pool.mark_failure(endpoint_id, obs)

        print(
            f"RPC code recovery round {recovery_round}: "
            f"remaining_targets={sum(1 for value in code_successes.values() if len(value) < args.min_code_endpoints)}"
        )

    # Append only this invocation's new evidence records.
    if all_records:
        with open(args.out, "a", encoding="utf-8") as out:
            for record in all_records:
                out.write(json.dumps(record, sort_keys=True) + "\n")
                out.flush()

    write_checkpoint(args.checkpoint, checkpoint_completed)

    chain_id_values = sorted(set(chain_ids.values()))
    freshest = max(block_numbers.values()) if block_numbers else None
    stale_endpoints = [
        endpoint_id
        for endpoint_id, block in block_numbers.items()
        if freshest is not None and freshest - block > args.stale_block_tolerance
    ]
    head_span = (
        max(block_numbers.values()) - min(block_numbers.values())
        if len(block_numbers) >= 2
        else None
    )
    head_agreement = (
        len(block_numbers) >= 2
        and head_span is not None
        and head_span <= args.stale_block_tolerance
    )

    summary = {
        "chain_id_expected": 137,
        "chain_ids_observed": chain_ids,
        "chain_id_agreement": len(chain_ids) >= 2 and chain_id_values == [137],
        "chain_id_values": chain_id_values,
        "freshest_observed_block": freshest,
        "stale_block_tolerance": args.stale_block_tolerance,
        "rpc_blocks": block_numbers,
        "stale_endpoints": stale_endpoints,
        "successful_chain_id_endpoint_count": len(chain_ids),
        "successful_block_endpoint_count": len(block_numbers),
        "head_block_span": head_span,
        "head_agreement": head_agreement,
        "eligible_code_endpoint_count": len(eligible_for_code),
        "eligible_code_endpoints": sorted(eligible_for_code),
        "min_code_endpoints_required": args.min_code_endpoints,
        "code_successful_endpoint_counts": {
            address: len(endpoints_for_address)
            for address, endpoints_for_address in code_successes.items()
        },
        "rpc_rotation_enabled": True,
        "rpc_pool_size": len(endpoints),
    }
    Path("polygon_rpc_head_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    if len(chain_ids) < 2:
        raise SystemExit(
            "P1 identity failure: fewer than 2 independent RPC endpoints returned a valid chain ID "
            f"(observed={len(chain_ids)})"
        )
    if chain_id_values != [137]:
        raise SystemExit(
            f"P1 identity failure: observed successful RPC chain IDs are {chain_id_values}, expected unanimous 137"
        )
    if len(block_numbers) < 2:
        raise SystemExit(
            "P1 head failure: fewer than 2 independent RPC endpoints returned a valid block number "
            f"(observed={len(block_numbers)})"
        )
    if not head_agreement:
        raise SystemExit(
            "P1 head failure: fresh independent RPC latest blocks exceed the allowed span "
            f"(blocks={block_numbers}, tolerance={args.stale_block_tolerance})"
        )

    incomplete = {
        address: sorted(code_successes[address])
        for address in addresses
        if len(code_successes[address]) < args.min_code_endpoints
    }
    if incomplete:
        raise SystemExit(
            "P1 code failure: adaptive RPC rotation could not obtain the required independent "
            f"code observations for targets={incomplete}"
        )

    print(f"Wrote {args.out}")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"RPC pool size: {len(endpoints)}")
    print(f"Identity endpoints: {len(chain_ids)}")
    print(f"Head endpoints: {len(block_numbers)}")
    print(f"Code quorum: {args.min_code_endpoints} independent endpoints per target")
    if block_numbers:
        print(f"Freshest block observed: {freshest}")


if __name__ == "__main__":
    main()
