#!/usr/bin/env python3
"""Ethereum Mainnet P4 token-universe discovery and read-only runtime verification."""
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / "automation" / "evidence"
CHAIN_ID = 1
HEAD_TOLERANCE = 2
BATCH_SIZE = 50
MIN_RPC = 2
PREFERRED_RPC_IDS = ["1rpc", "blastapi", "drpc"]

SOURCES = [
    ("uniswap_default", "https://raw.githubusercontent.com/Uniswap/default-token-list/main/src/tokens/mainnet.json"),
    ("coingecko_uniswap", "https://tokens.coingecko.com/uniswap/all.json"),
    ("viaprotocol_trusted", "https://raw.githubusercontent.com/viaprotocol/tokenlists/main/tokenlists/ethereum.json"),
    ("compound", "https://raw.githubusercontent.com/compound-finance/token-list/master/compound.tokenlist.json"),
    ("geckoterminal_recent", "https://api.geckoterminal.com/api/v2/tokens/info_recently_updated?include=network&network=eth"),
]

HEX20 = re.compile(r"^0x[0-9a-fA-F]{40}$")

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def normalize_address(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not HEX20.fullmatch(value):
        return None
    return value.lower()

def http_json(url, timeout=30):
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "ghost-hunter-ethereum-p4-token-universe/1.0"}, method="GET")
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            return {
                "ok": True,
                "status": resp.status,
                "payload": body,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "error": None,
            }
    except HTTPError as exc:
        return {"ok": False, "status": exc.code, "payload": None, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": f"HTTP {exc.code}: {exc}"}
    except (URLError, TimeoutError, ValueError) as exc:
        return {"ok": False, "status": None, "payload": None, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": f"{type(exc).__name__}: {exc}"}

def extract_token_list(payload, source_id):
    items = payload.get("tokens", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []
    rows = []
    seen = set()
    for item in items:
        if not isinstance(item, dict) or item.get("chainId") != CHAIN_ID:
            continue
        address = normalize_address(item.get("address"))
        if not address or address in seen:
            continue
        seen.add(address)
        rows.append({
            "address": address,
            "name": item.get("name"),
            "symbol": item.get("symbol"),
            "decimals": item.get("decimals"),
            "source": source_id,
        })
    return rows

def extract_gecko_recent(payload, source_id):
    items = payload.get("data", []) if isinstance(payload, dict) else []
    if not isinstance(items, list):
        return []
    rows = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        token_id = str(item.get("id") or "")
        if not token_id.startswith("eth_"):
            continue
        address = normalize_address(token_id[4:])
        if not address or address in seen:
            continue
        attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
        seen.add(address)
        rows.append({
            "address": address,
            "name": attrs.get("name"),
            "symbol": attrs.get("symbol"),
            "decimals": attrs.get("decimals"),
            "source": source_id,
        })
    return rows

def source_sample():
    records = []
    all_candidates = {}
    for source_id, url in SOURCES:
        result = http_json(url)
        rows = []
        if result["ok"]:
            if source_id == "geckoterminal_recent":
                rows = extract_gecko_recent(result["payload"], source_id)
            else:
                rows = extract_token_list(result["payload"], source_id)
        records.append({
            "source_id": source_id,
            "url": url,
            "http_status": result["status"],
            "ok": result["ok"],
            "latency_ms": result["latency_ms"],
            "error": result["error"],
            "count": len(rows),
        })
        for row in rows:
            current = all_candidates.setdefault(row["address"], {
                "address": row["address"],
                "sources": set(),
                "metadata": [],
            })
            current["sources"].add(source_id)
            current["metadata"].append({
                "source": source_id,
                "name": row.get("name"),
                "symbol": row.get("symbol"),
                "decimals": row.get("decimals"),
            })
    normalized = {
        address: {
            "sources": sorted(item["sources"]),
            "metadata": sorted(item["metadata"], key=lambda x: (x["source"], str(x.get("symbol")), str(x.get("name")))),
        }
        for address, item in sorted(all_candidates.items())
    }
    return {
        "time": utc_now(),
        "sources": records,
        "candidate_count": len(normalized),
        "candidate_fingerprint": fingerprint(normalized),
        "candidates": normalized,
    }

def load_rpc_pool(path):
    endpoints = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        endpoint_id, url = line.split("|", 1)
        if not url.startswith("https://"):
            continue
        endpoints.append({"id": endpoint_id.strip(), "url": url.strip()})
    return endpoints

def rpc_call(url, method, params, request_id, timeout=15):
    payload = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}).encode()
    req = Request(url, data=payload, headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "ghost-hunter-ethereum-p4-runtime/1.0"}, method="POST")
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            return {"ok": True, "status": resp.status, "body": body, "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
    except HTTPError as exc:
        return {"ok": False, "status": exc.code, "body": None, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": f"HTTP {exc.code}: {exc}"}
    except (URLError, TimeoutError, ValueError) as exc:
        return {"ok": False, "status": None, "body": None, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": f"{type(exc).__name__}: {exc}"}

def probe_identity(endpoint):
    result = rpc_call(endpoint["url"], "eth_chainId", [], endpoint["id"] + ":chain")
    chain_id = None
    if result.get("ok") and isinstance(result.get("body"), dict):
        raw = result["body"].get("result")
        try:
            chain_id = int(raw, 16) if isinstance(raw, str) else None
        except ValueError:
            chain_id = None
    return {"endpoint_id": endpoint["id"], "url": endpoint["url"], "result": result, "chain_id": chain_id}

def probe_head(endpoint):
    result = rpc_call(endpoint["url"], "eth_blockNumber", [], endpoint["id"] + ":head")
    block = None
    if result.get("ok") and isinstance(result.get("body"), dict):
        raw = result["body"].get("result")
        try:
            block = int(raw, 16) if isinstance(raw, str) else None
        except ValueError:
            block = None
    return {"endpoint_id": endpoint["id"], "url": endpoint["url"], "result": result, "block": block}

def batch_get_code(endpoint, addresses, block_tag):
    payload = []
    for index, address in enumerate(addresses):
        payload.append({
            "jsonrpc": "2.0",
            "id": f"{endpoint['id']}:{index}",
            "method": "eth_getCode",
            "params": [address, hex(block_tag)],
        })
    req = Request(
        endpoint["url"],
        data=json.dumps(payload).encode(),
        headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "ghost-hunter-ethereum-p4-runtime/1.0"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())
            if not isinstance(body, list):
                raise ValueError("batch JSON-RPC response is not a list")
            by_id = {item.get("id"): item for item in body if isinstance(item, dict)}
            observations = []
            for index, address in enumerate(addresses):
                item = by_id.get(f"{endpoint['id']}:{index}", {})
                code = item.get("result") if isinstance(item, dict) else None
                if isinstance(code, str) and code.startswith("0x"):
                    observations.append({
                        "address": address,
                        "status": resp.status,
                        "ok": True,
                        "code_nonempty": code != "0x",
                        "code_hash": hashlib.sha256(code.encode()).hexdigest(),
                    })
                else:
                    observations.append({
                        "address": address,
                        "status": resp.status,
                        "ok": False,
                        "code_nonempty": False,
                        "code_hash": None,
                        "error": item.get("error") if isinstance(item, dict) else "missing result",
                    })
            return observations
    except HTTPError as exc:
        return [{"address": a, "status": exc.code, "ok": False, "code_nonempty": False, "code_hash": None, "error": f"HTTP {exc.code}: {exc}"} for a in addresses]
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return [{"address": a, "status": None, "ok": False, "code_nonempty": False, "code_hash": None, "error": f"{type(exc).__name__}: {exc}"} for a in addresses]
    finally:
        _ = started

def classify_token(state):
    if state.get("observations", 0) < MIN_RPC or state.get("successful_observations", 0) < MIN_RPC:
        return "INCOMPLETE_RPC_EVIDENCE"
    hashes = state.get("code_hashes", set())
    if len(hashes) > 1:
        return "CODE_HASH_CONFLICT"
    if state.get("code_nonempty", 0) == 0:
        return "VERIFIED_NON_CONTRACT"
    return "VERIFIED_DEPLOYED_CONTRACT"

def verify_candidates(candidates, rpc_pool_path):
    endpoints = load_rpc_pool(rpc_pool_path)
    identities = [probe_identity(e) for e in endpoints]
    eligible = [e for e, obs in zip(endpoints, identities) if obs["chain_id"] == CHAIN_ID]
    if len(eligible) < MIN_RPC:
        raise RuntimeError("Ethereum P4 failed closed: fewer than two chain-1 RPC identity endpoints")
    heads = [probe_head(e) for e in eligible]
    valid_heads = [h for h in heads if h["block"] is not None]
    if len(valid_heads) < MIN_RPC:
        raise RuntimeError("Ethereum P4 failed closed: fewer than two readable chain heads")
    blocks = [h["block"] for h in valid_heads]
    selected_block = min(blocks)
    if max(blocks) - min(blocks) > HEAD_TOLERANCE:
        raise RuntimeError("Ethereum P4 failed closed: chain-head spread exceeds tolerance")
    preferred = [e for wanted in PREFERRED_RPC_IDS for e in eligible if e["id"] == wanted]
    selected = preferred[:3]
    if len(selected) < MIN_RPC:
        selected = eligible[:3]
    addresses = sorted(candidates.keys())
    by_address = {
        address: {"observations": 0, "successful_observations": 0, "code_nonempty": 0, "code_hashes": set(), "endpoint_results": []}
        for address in addresses
    }
    for endpoint in selected:
        for start in range(0, len(addresses), BATCH_SIZE):
            batch = addresses[start:start + BATCH_SIZE]
            rows = batch_get_code(endpoint, batch, selected_block)
            for row in rows:
                state = by_address[row["address"]]
                state["observations"] += 1
                if row.get("ok"):
                    state["successful_observations"] += 1
                    if row.get("code_nonempty"):
                        state["code_nonempty"] += 1
                    if row.get("code_hash"):
                        state["code_hashes"].add(row["code_hash"])
                state["endpoint_results"].append({
                    "endpoint_id": endpoint["id"],
                    "status": row.get("status"),
                    "ok": row.get("ok"),
                    "code_nonempty": row.get("code_nonempty"),
                    "code_hash": row.get("code_hash"),
                    "error": row.get("error"),
                })
    output = {}
    for address in addresses:
        state = by_address[address]
        classification = classify_token(state)
        output[address] = {
            "classification": classification,
            "sources": candidates[address]["sources"],
            "metadata": candidates[address]["metadata"],
            "observations": state["observations"],
            "successful_observations": state["successful_observations"],
            "code_nonempty_observations": state["code_nonempty"],
            "code_hashes": sorted(state["code_hashes"]),
            "endpoint_results": state["endpoint_results"],
        }
    return {
        "rpc_identity": [{"endpoint_id": x["endpoint_id"], "chain_id": x["chain_id"]} for x in identities],
        "eligible_chain1_endpoints": [x["id"] for x in eligible],
        "verification_endpoints": [x["id"] for x in selected],
        "head_observations": [{"endpoint_id": x["endpoint_id"], "block": x["block"]} for x in heads],
        "verification_block": selected_block,
        "head_span": max(blocks) - min(blocks),
        "tokens": output,
    }

def main():
    policy = json.loads((ROOT / "chains" / "ethereum-mainnet" / "P4_TOKEN_UNIVERSE_POLICY.json").read_text(encoding="utf-8"))
    if len(SOURCES) != policy["required_source_count"]:
        raise SystemExit("P4 source-count policy mismatch")
    closure = EVID / "ETHEREUM_P4_CLOSURE_STATE.json"
    previous = json.loads(closure.read_text(encoding="utf-8")) if closure.exists() else {}
    samples = [source_sample(), source_sample()]
    stable = samples[0]["candidate_fingerprint"] == samples[1]["candidate_fingerprint"]
    sources_ok = all(all(src["ok"] and src["http_status"] == 200 and src["count"] > 0 for src in sample["sources"]) for sample in samples)
    if not (stable and sources_ok):
        raise SystemExit("Ethereum P4 discovery failed closed: source availability or stable candidate fingerprint incomplete")
    verification = verify_candidates(samples[-1]["candidates"], "chains/ethereum-mainnet/rpc_pool.txt")
    tokens = verification["tokens"]
    counts = {}
    for row in tokens.values():
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    all_dual = all(row["successful_observations"] >= MIN_RPC for row in tokens.values())
    no_conflicts = counts.get("CODE_HASH_CONFLICT", 0) == 0
    all_classified = all(row["classification"] != "INCOMPLETE_RPC_EVIDENCE" for row in tokens.values())
    gate = stable and sources_ok and all_dual and no_conflicts and all_classified
    normalized = {
        "candidate_fingerprint": samples[-1]["candidate_fingerprint"],
        "candidate_count": samples[-1]["candidate_count"],
        "verification_block": verification["verification_block"],
        "verification_endpoints": verification["verification_endpoints"],
        "classification_counts": counts,
    }
    report = {
        "schema_version": "ethereum-p4-token-universe-v1",
        "task": "ethereum_p4_token_universe",
        "chain_id": CHAIN_ID,
        "samples": [
            {
                "time": s["time"],
                "sources": s["sources"],
                "candidate_count": s["candidate_count"],
                "candidate_fingerprint": s["candidate_fingerprint"],
            }
            for s in samples
        ],
        "checks": {
            "all_sources_http_200_nonempty": sources_ok,
            "consecutive_candidate_fingerprint_stable": stable,
            "minimum_two_chain1_identity_endpoints": len(verification["eligible_chain1_endpoints"]) >= MIN_RPC,
            "fixed_verification_block_head_span_within_tolerance": verification["head_span"] <= HEAD_TOLERANCE,
            "all_candidates_dual_rpc_observed": all_dual,
            "code_hash_conflicts_zero": no_conflicts,
            "all_candidates_classified": all_classified,
        },
        "counts": {
            "candidate_tokens": len(tokens),
            "verified_deployed_contracts": counts.get("VERIFIED_DEPLOYED_CONTRACT", 0),
            "verified_non_contracts": counts.get("VERIFIED_NON_CONTRACT", 0),
            "code_hash_conflicts": counts.get("CODE_HASH_CONFLICT", 0),
            "incomplete_rpc_evidence": counts.get("INCOMPLETE_RPC_EVIDENCE", 0),
        },
        "verification": {
            "identity": verification["rpc_identity"],
            "eligible_chain1_endpoints": verification["eligible_chain1_endpoints"],
            "verification_endpoints": verification["verification_endpoints"],
            "head_observations": verification["head_observations"],
            "verification_block": verification["verification_block"],
            "head_span": verification["head_span"],
        },
        "candidate_universe_fingerprint": samples[-1]["candidate_fingerprint"],
        "report_fingerprint": fingerprint(normalized),
        "stage_gate": "CLOSED" if gate else "OPEN",
        "evidence_class": "TOKEN_UNIVERSE",
        "boundary": "Source-union discovery plus same-block dual-RPC runtime-code classification. ERC20 semantic compliance, pool/liquidity state, routes and economics remain downstream.",
        "safety": {"live_signing": False, "public_broadcast": False, "real_money": False},
        "previous_fingerprint": previous.get("candidate_universe_fingerprint"),
    }
    EVID.mkdir(parents=True, exist_ok=True)
    (EVID / "ETHEREUM_P4_TOKEN_SNAPSHOT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    state = {
        "candidate_universe_fingerprint": samples[-1]["candidate_fingerprint"],
        "stable_runs": 2 if stable else 1,
        "stage_gate": "CLOSED" if gate else "OPEN",
        "updated_at": utc_now(),
    }
    closure.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (EVID / "ETHEREUM_P4_TOKEN_RECORDS.json").write_text(json.dumps(tokens, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not gate:
        raise SystemExit("Ethereum P4 token-universe gate failed closed")
    print("Ethereum P4 token-universe CLOSED")
    print(samples[-1]["candidate_fingerprint"])
    print(json.dumps(counts, sort_keys=True))

if __name__ == "__main__":
    main()
