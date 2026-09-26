#!/usr/bin/env python3
"""Autonomous Polygon universe evidence worker for P3-P10 plus P2 provenance replay.
stdlib-only; every external snapshot is labeled discovery evidence, never VERIFIED.
"""
import hashlib, json, math, os, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from pathlib import Path

ROOT = Path(".")
EVID = ROOT / "automation" / "evidence"
UNIV = ROOT / "automation" / "universe"
RPC_POOL = ROOT / "chains" / "polygon-pos" / "rpc_pool.txt"
P2_PROV = ROOT / "chains" / "polygon-pos" / "P2_EXTERNAL_PROVENANCE_CANDIDATES.md"

DexProfilesURL = "https://api.dexscreener.com/token-profiles/latest/v1"
DefiLlamaProtocolsURL = "https://api.llama.fi/protocols"

def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
def sha(v): return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def ensure(): EVID.mkdir(parents=True, exist_ok=True); UNIV.mkdir(parents=True, exist_ok=True)

def http_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"ghost-hunter-saturation/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read()), None
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"

def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {} if default is None else default


def write_json(name, payload):
    ensure(); p=EVID/name; p.write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n", encoding="utf-8"); return str(p)

def append_jsonl(path, rows):
    ensure();
    with open(path,"a",encoding="utf-8") as f:
        for row in rows: f.write(json.dumps(row, sort_keys=True)+"\n")

def load_jsonl(path):
    p=Path(path)
    if not p.exists(): return []
    raw=p.read_text(encoding="utf-8")
    records=[]
    for line in raw.splitlines():
        # Recover legacy artifacts where a writer emitted the two-character
        # sequence "\\n" instead of a real line feed.
        for chunk in line.split("\\n"):
            if chunk.strip():
                records.append(json.loads(chunk))
    return records

def provenance_fingerprint(observation):
    """Fingerprint semantic transaction+receipt payload, excluding transport metadata."""
    return sha({
        "tx": observation.get("tx"),
        "receipt": observation.get("receipt"),
    })


def complete_provenance_observation(tx_response, receipt_response):
    """Require both transaction and receipt objects before counting an RPC observation."""
    if not tx_response.get("ok") or not receipt_response.get("ok"):
        return False
    tx_body = tx_response.get("body")
    receipt_body = receipt_response.get("body")
    if not isinstance(tx_body, dict) or not isinstance(receipt_body, dict):
        return False
    tx_result = tx_body.get("result")
    receipt_result = receipt_body.get("result")
    return isinstance(tx_result, dict) and isinstance(receipt_result, dict)


def task_p2_provenance_replay():
    text=P2_PROV.read_text(encoding="utf-8") if P2_PROV.exists() else ""
    import re
    txs=sorted(set(re.findall(r"(?im)(?:tx|creation tx)\s*=\s*(0x[a-fA-F0-9]{64})", text)))
    result={"task":"p2_provenance_replay","time":now(),"status":"DISCOVERY_ONLY","transactions":[],"source":"canonical provenance candidate file"}
    try:
        import sys
        sys.path.insert(0, str(Path('chains/polygon-pos').resolve()))
        from polygon_readonly_verifier import RpcPool, load_rpc_endpoints
    except Exception as e:
        result["status"]="BLOCKED_IMPORT"; result["error"]=f"{type(e).__name__}: {e}"; return write_json("P2_PROVENANCE_REPLAY.json",result)
    if not RPC_POOL.exists(): result["status"]="BLOCKED_NO_RPC_POOL"; return write_json("P2_PROVENANCE_REPLAY.json",result)

    endpoints=load_rpc_endpoints(None,str(RPC_POOL))
    pool=RpcPool(endpoints,1.0)
    recovery_rounds=2

    for tx in txs:
        obs=[]
        observed_endpoints=set()
        diagnostics=[]

        for recovery_round in range(1,recovery_rounds + 1):
            for item in pool.ordered():
                eid=item["id"]
                if eid in observed_endpoints:
                    continue

                a=pool.request(eid,"eth_getTransactionByHash",[tx],f"{eid}:tx:{tx}:r{recovery_round}",12,1)
                b=pool.request(eid,"eth_getTransactionReceipt",[tx],f"{eid}:receipt:{tx}:r{recovery_round}",12,1)

                complete=complete_provenance_observation(a,b)
                diagnostics.append({
                    "rpc":eid,
                    "round":recovery_round,
                    "transaction_ok":bool(a.get("ok")),
                    "receipt_ok":bool(b.get("ok")),
                    "transaction_http_status":a.get("http_status"),
                    "receipt_http_status":b.get("http_status"),
                    "transaction_error":a.get("message") or ((a.get("body") or {}).get("error") if isinstance(a.get("body"),dict) else None),
                    "receipt_error":b.get("message") or ((b.get("body") or {}).get("error") if isinstance(b.get("body"),dict) else None),
                    "complete":complete,
                })

                if a.get("ok") or b.get("ok"):
                    pool.mark_success(eid)
                else:
                    pool.mark_failure(eid,b if not b.get("ok") else a)

                if complete:
                    observed_endpoints.add(eid)
                    obs.append({
                        "rpc":eid,
                        "tx":a["body"]["result"],
                        "receipt":b["body"]["result"],
                    })
                    if len(obs)>=2:
                        break

            if len(obs)>=2:
                break

            if recovery_round < recovery_rounds:
                cooldowns=[
                    pool.state[eid]["cooldown_until"] - time.monotonic()
                    for eid in pool.state
                    if eid not in observed_endpoints
                    and pool.state[eid]["cooldown_until"] > time.monotonic()
                ]
                if cooldowns:
                    time.sleep(min(max(0.0,max(cooldowns)),60.0))

        fingerprints=[provenance_fingerprint(x) for x in obs]
        result["transactions"].append({
            "tx_hash":tx,
            "independent_observations":len(obs),
            "matching":len(obs)>=2 and len(set(fingerprints))==1,
            "semantic_fingerprints":fingerprints,
            "observations":obs,
            "endpoint_diagnostics":diagnostics,
            "recovery_rounds":recovery_rounds,
        })

    result["status"]="REPLAYED" if txs and all(x["independent_observations"]>=2 and x["matching"] for x in result["transactions"]) else "PARTIAL"
    return write_json("P2_PROVENANCE_REPLAY.json",result)

def normalize_market_name(value):
    import re
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def p3_dex_sets(protocols, gecko_rows):
    llama = set()
    for row in protocols:
        category = normalize_market_name(row.get("category"))
        if category in {"dexs", "dex", "dexes"}:
            key = normalize_market_name(row.get("name") or row.get("slug"))
            if key:
                llama.add(key)
    gecko = set()
    for row in gecko_rows:
        attrs = row.get("attributes") if isinstance(row, dict) else {}
        raw = attrs.get("name") if isinstance(attrs, dict) else None
        key = normalize_market_name(raw or (row.get("id") if isinstance(row, dict) else None))
        if key:
            gecko.add(key)
    return llama, gecko


def p3_closure_ready(snapshot, previous_state):
    checks = snapshot.get("checks", {})
    current_fp = snapshot.get("universe_fingerprint")
    previous_fp = previous_state.get("fingerprint")
    stable_count = int(previous_state.get("stable_runs", 0) or 0)
    return (
        checks.get("defillama_protocols_ok") is True
        and checks.get("geckoterminal_dexes_ok") is True
        and int(snapshot.get("polygon_protocol_count", 0)) > 0
        and int(snapshot.get("polygon_dex_protocol_count", 0)) > 0
        and int(snapshot.get("geckoterminal_dex_count", 0)) > 0
        and int(snapshot.get("dex_name_overlap_count", 0)) >= 3
        and int(snapshot.get("llama_duplicate_dex_names", 0)) == 0
        and int(snapshot.get("gecko_duplicate_dex_names", 0)) == 0
        and current_fp
        and current_fp == previous_fp
        and stable_count >= 1
    )


def task_p3_protocols():
    st, llama, err = http_json(DefiLlamaProtocolsURL)
    st2, dex, err2 = http_json(DexProfilesURL)
    gt_url = "https://api.geckoterminal.com/api/v2/networks/polygon_pos/dexes"
    st3, gecko, err3 = http_json(gt_url)

    protocols = []
    if isinstance(llama, list):
        for p in llama:
            chains = [str(x).lower() for x in (p.get("chains") or [])]
            if "polygon" in chains:
                protocols.append(p)

    profiles = []
    if isinstance(dex, list):
        profiles = [x for x in dex if str(x.get("chainId", "")).lower() == "polygon"]

    gecko_rows = []
    if isinstance(gecko, dict):
        data = gecko.get("data")
        if isinstance(data, list):
            gecko_rows = data

    llama_dex, gecko_dex = p3_dex_sets(protocols, gecko_rows)
    overlap = sorted(llama_dex & gecko_dex)
    llama_names = [
        normalize_market_name(x.get("name") or x.get("slug"))
        for x in protocols
        if normalize_market_name(x.get("name") or x.get("slug"))
        and normalize_market_name(x.get("category")) in {"dexs", "dex", "dexes"}
    ]
    llama_duplicate_count = len(llama_names) - len(set(llama_names))
    gecko_names = [
        normalize_market_name(
            (x.get("attributes") or {}).get("name") if isinstance(x, dict) else ""
        )
        for x in gecko_rows
    ]
    gecko_names = [x for x in gecko_names if x]
    gecko_duplicate_count = max(0, len(gecko_names) - len(set(gecko_names)))

    normalized_universe = {
        "llama_protocols": sorted(
            normalize_market_name(x.get("name") or x.get("slug"))
            for x in protocols
            if normalize_market_name(x.get("name") or x.get("slug"))
        ),
        "llama_dexes": sorted(llama_dex),
        "gecko_dexes": sorted(gecko_dex),
        "dexscreener_polygon_profiles": sorted(
            str(x.get("tokenAddress", "")).lower()
            for x in profiles
            if x.get("tokenAddress")
        ),
    }
    universe_fingerprint = sha(normalized_universe)

    closure_path = EVID / "P3_CLOSURE_STATE.json"
    previous = load_json(closure_path, {})
    previous_fp = previous.get("fingerprint")
    stable_runs = int(previous.get("stable_runs", 0) or 0)
    if universe_fingerprint and universe_fingerprint == previous_fp:
        stable_runs += 1
    else:
        stable_runs = 1

    snapshot = {
        "task": "p3_protocol_discovery",
        "time": now(),
        "network": "polygon",
        "chain_id": 137,
        "sources": [
            DefiLlamaProtocolsURL,
            DexProfilesURL,
            gt_url,
        ],
        "http": {
            "defillama_protocols": st,
            "dexscreener_token_profiles": st2,
            "geckoterminal_dexes": st3,
        },
        "errors": {
            "defillama_protocols": err,
            "dexscreener_token_profiles": err2,
            "geckoterminal_dexes": err3,
        },
        "polygon_protocol_count": len(protocols),
        "polygon_dex_protocol_count": len(llama_dex),
        "dexscreener_polygon_profile_count": len(profiles),
        "geckoterminal_dex_count": len(gecko_dex),
        "dex_name_overlap_count": len(overlap),
        "dex_name_overlap": overlap,
        "llama_duplicate_dex_names": llama_duplicate_count,
        "gecko_duplicate_dex_names": gecko_duplicate_count,
        "universe_fingerprint": universe_fingerprint,
        "stable_runs": stable_runs,
        "checks": {
            "defillama_protocols_ok": st == 200 and isinstance(llama, list),
            "geckoterminal_dexes_ok": st3 == 200 and isinstance(gecko, dict),
            "dexscreener_profiles_ok": st2 == 200 and isinstance(dex, list),
        },
        "evidence_class": "DISCOVERY",
    }
    snapshot["stage_gate"] = "CLOSED" if p3_closure_ready(snapshot, {
        "fingerprint": previous_fp,
        "stable_runs": stable_runs,
    }) else "OPEN"

    write_json(
        "P3_CLOSURE_STATE.json",
        {
            "fingerprint": universe_fingerprint,
            "stable_runs": stable_runs,
            "updated_at": snapshot["time"],
            "stage_gate": snapshot["stage_gate"],
        },
    )
    return write_json("P3_PROTOCOL_SNAPSHOT.json", snapshot)

def load_seed_tokens():
    path=ROOT/"chains/polygon-pos/p4_seed_tokens.txt"
    seeds=[]
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if not line or line.startswith("#"): continue
            parts=line.split("|",2)
            if len(parts)>=2:
                address=parts[0].strip()
                label=parts[1].strip()
                if len(address)==42 and address.lower().startswith("0x"):
                    seeds.append({"address":address,"label":label,"source":"polygon_seed_manifest","first_seen":now()})
    return seeds

def _extract_address(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    lower = value.lower()
    if len(value) == 42 and lower.startswith("0x"):
        try:
            int(value[2:], 16)
        except ValueError:
            return None
        return "0x" + value[2:].lower()
    if lower.startswith("token_polygon_pos_0x") and len(value.split("_", 3)[-1]) == 42:
        return _extract_address(value.split("_", 3)[-1])
    return None


def extract_gecko_token_addresses(payload):
    found = set()
    resources = []
    if isinstance(payload, dict):
        for key in ("data", "included"):
            rows = payload.get(key)
            if isinstance(rows, list):
                resources.extend(rows)
    elif isinstance(payload, list):
        resources = payload

    token_types = {"token", "tokens"}
    token_relationships = {
        "base_token", "quote_token", "basetoken", "quotetoken",
        "token", "tokens",
    }

    for resource in resources:
        if not isinstance(resource, dict):
            continue

        resource_type = str(resource.get("type", "")).lower()
        is_token_resource = resource_type in token_types

        # Never treat an arbitrary pool/DEX resource id as a token address.
        # Only explicit token resources may contribute their own id/address.
        if is_token_resource:
            address = _extract_address(resource.get("id"))
            if address:
                found.add(address)
            attrs = resource.get("attributes")
            if isinstance(attrs, dict):
                attribute_address = _extract_address(attrs.get("address"))
                if attribute_address:
                    found.add(attribute_address)

        relationships = resource.get("relationships")
        if isinstance(relationships, dict):
            for rel_name, rel in relationships.items():
                if str(rel_name).lower() not in token_relationships:
                    continue
                if not isinstance(rel, dict):
                    continue
                rel_data = rel.get("data")
                if isinstance(rel_data, dict):
                    rel_data = [rel_data]
                if isinstance(rel_data, list):
                    for item in rel_data:
                        if not isinstance(item, dict):
                            continue
                        item_type = str(item.get("type", "")).lower()
                        if item_type and item_type not in token_types:
                            continue
                        address = _extract_address(item.get("id"))
                        if address:
                            found.add(address)
    return sorted(found)

def extract_dex_token_addresses(rows):
    found = set()
    if isinstance(rows, dict):
        rows = rows.get("pairs") or rows.get("data") or []
    if not isinstance(rows, list):
        return []

    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("chainId", "")).lower() != "polygon":
            continue
        for side in ("baseToken", "quoteToken"):
            token = row.get(side)
            if isinstance(token, dict):
                address = _extract_address(token.get("address"))
                if address:
                    found.add(address)
    return sorted(found)


P4_VERIFY_STATE = EVID / "P4_VERIFICATION_STATE.json"
P4_VERIFY_BATCH_SIZE = 48
P4_RPC_WORKERS = 6
P4_ENDPOINT_SCAN_MAX = 18
P4_CHAIN_RECOVERY_ROUNDS = 2
P4_RECOVERY_WAIT_MAX = 60
P4_RPC_MIN_INTERVAL = 1.0
P4_RPC_CHUNK_TOKENS = 12
P4_RPC_MIN_CHUNK_TOKENS = 1
P4_RPC_MAX_RETRY_WAIT = 30


def p4_verification_batch(candidates, verification_state, batch_size=P4_VERIFY_BATCH_SIZE):
    batch = []
    for address in candidates:
        row = verification_state.get(address, {})
        if row.get("matching") is True:
            continue
        batch.append(address)
        if len(batch) >= batch_size:
            break
    return batch


def p4_closure_ready(snapshot, previous_state):
    current_fp = snapshot.get("universe_fingerprint")
    previous_fp = previous_state.get("fingerprint")
    stable_count = int(previous_state.get("stable_runs", 0) or 0)
    checks = snapshot.get("checks", {})
    return (
        checks.get("geckoterminal_top_pools_ok") is True
        and checks.get("dexscreener_profiles_ok") is True
        and checks.get("dexscreener_tokens_ok") is True
        and int(snapshot.get("candidate_count", 0)) >= 8
        and int(snapshot.get("provider_overlap_count", 0)) >= 3
        and int(snapshot.get("duplicate_address_count", 0)) == 0
        and int(snapshot.get("verified_token_count", 0)) == int(snapshot.get("candidate_count", 0))
        and snapshot.get("verification_cycle_complete") is True
        and int(snapshot.get("chain_137_verified_count", 0)) == int(snapshot.get("candidate_count", 0))
        and int(snapshot.get("identity_conflict_count", 0)) == 0
        and current_fp
        and current_fp == previous_fp
        and previous_state.get("verification_cycle_complete") is True
        and stable_count >= 1
    )



class P4RateLimitedError(RuntimeError):
    def __init__(self, retry_after_seconds=5.0, message="P4 RPC rate limited"):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def _p4_retry_after(headers):
    value = headers.get("Retry-After") if headers else None
    try:
        return max(1.0, min(float(value), P4_RPC_MAX_RETRY_WAIT))
    except (TypeError, ValueError):
        return 5.0


def _p4_rpc_batch_endpoint(pool, endpoint_id, calls, timeout=30):
    """Use JSON-RPC batching, falling back only when the endpoint rejects batch shape."""
    state = pool.state[endpoint_id]
    with state["lock"]:
        now_mono = time.monotonic()
        wait = state["request_interval"] - (now_mono - state["last_request_at"])
        if wait > 0:
            time.sleep(wait)
        state["last_request_at"] = time.monotonic()

    payload = [
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        for request_id, method, params in calls
    ]
    url = pool.endpoint_url(endpoint_id)
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS RPC endpoints are permitted")

    headers = {"Content-Type": "application/json"}
    if "tatum.io" in url and os.environ.get("TATUM_API_KEY"):
        headers["X-API-Key"] = os.environ["TATUM_API_KEY"]

    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read())
            if isinstance(body, list):
                return response.status, {str(row.get("id")): row for row in body if isinstance(row, dict)}
            if len(calls) == 1 and isinstance(body, dict):
                return response.status, {str(calls[0][0]): body}
            raise ValueError("JSON-RPC endpoint rejected batch response shape")
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise P4RateLimitedError(_p4_retry_after(exc.headers))
        raise


def _p4_rpc_single_calls(pool, endpoint_id, calls, timeout=30):
    rows = {}
    for request_id, method, params in calls:
        obs = pool.request(endpoint_id, method, params, request_id, timeout, 1)
        body = obs.get("body")
        if isinstance(body, dict):
            rows[request_id] = body
        if obs.get("ok"):
            pool.mark_success(endpoint_id)
        else:
            pool.mark_failure(endpoint_id, obs)
    return rows


def _p4_endpoint_probe_addresses(candidates):
    candidate_set = set(candidates)
    seeds = []
    for row in load_seed_tokens():
        address = _extract_address(row.get("address"))
        if address and address in candidate_set and address not in seeds:
            seeds.append(address)
    for address in candidates:
        if address not in seeds:
            seeds.append(address)
        if len(seeds) >= 1:
            break
    return seeds[:1]


def _p4_endpoint_semantic_probe(pool, endpoint_id, addresses):
    calls = []
    for address in addresses:
        calls.append((f"p4:probe:{endpoint_id}:{address}:code", "eth_getCode", [address, "latest"]))
        calls.append((f"p4:probe:{endpoint_id}:{address}:decimals", "eth_call", [{"to": address, "data": "0x313ce567"}, "latest"]))
        calls.append((f"p4:probe:{endpoint_id}:{address}:supply", "eth_call", [{"to": address, "data": "0x18160ddd"}, "latest"]))

    try:
        _, rows = _p4_rpc_batch_endpoint(pool, endpoint_id, calls, timeout=30)
    except ValueError:
        rows = _p4_rpc_single_calls(pool, endpoint_id, calls, timeout=30)
    usable = True
    for address in addresses:
        code = rows.get(f"p4:probe:{endpoint_id}:{address}:code", {}).get("result")
        decimals = rows.get(f"p4:probe:{endpoint_id}:{address}:decimals", {}).get("result")
        supply = rows.get(f"p4:probe:{endpoint_id}:{address}:supply", {}).get("result")
        valid_code = isinstance(code, str) and code not in {"", "0x", "0X"}
        valid_decimals = isinstance(decimals, str) and decimals.startswith("0x")
        valid_supply = isinstance(supply, str) and supply.startswith("0x")
        if valid_decimals:
            try:
                valid_decimals = 0 <= int(decimals, 16) <= 255
            except ValueError:
                valid_decimals = False
        usable = usable and valid_code and valid_decimals and valid_supply
    return usable, rows


def _p4_select_capable_endpoints(pool, chain_ok, probe_addresses, max_endpoints=3):
    selected = []
    diagnostics = {}

    def probe(eid):
        try:
            usable, _ = _p4_endpoint_semantic_probe(pool, eid, probe_addresses)
            return eid, usable, ""
        except Exception as exc:
            return eid, False, f"{type(exc).__name__}: {exc}"

    worker_count = min(P4_RPC_WORKERS, len(chain_ok))
    if worker_count <= 0:
        return selected, diagnostics

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(probe, eid) for eid in chain_ok]
        for future in as_completed(futures):
            eid, usable, error = future.result()
            diagnostics[eid] = {"usable": usable, "error": error}
            if usable:
                selected.append(eid)
                pool.mark_success(eid)
            else:
                pool.mark_failure(
                    eid,
                    {
                        "http_status": 200 if not error else None,
                        "rate_limited": False,
                        "message": error or "semantic capability probe failed",
                    },
                )

    selected.sort(key=lambda endpoint_id: chain_ok.index(endpoint_id))
    return selected[:max_endpoints], diagnostics


def _p4_discover_chain_endpoints(pool, max_endpoints=P4_ENDPOINT_SCAN_MAX):
    candidates = [item["id"] for item in pool.ordered()[:max_endpoints]]
    chain_ok = []
    diagnostics = {}
    retryable = []

    def probe(eid):
        try:
            obs = pool.request(eid, "eth_chainId", [], f"p4:{eid}:chain", 12, 1)
            body = obs.get("body")
            result = body.get("result") if isinstance(body, dict) else None
            return eid, str(result).lower() == "0x89", obs
        except Exception as exc:
            return eid, False, {"ok": False, "message": f"{type(exc).__name__}: {exc}"}

    def apply_result(eid, is_polygon, obs):
        diagnostics[eid] = {
            "chain_id_137": is_polygon,
            "http_status": obs.get("http_status"),
            "rate_limited": bool(obs.get("rate_limited")),
            "retry_after_seconds": obs.get("retry_after_seconds"),
            "error": obs.get("message") or (
                (obs.get("body") or {}).get("error")
                if isinstance(obs.get("body"), dict) else None
            ),
        }
        if is_polygon:
            if eid not in chain_ok:
                chain_ok.append(eid)
            pool.mark_success(eid)
        else:
            pool.mark_failure(eid, obs)
            if obs.get("http_status") == 429 or obs.get("rate_limited"):
                retryable.append(eid)

    worker_count = min(P4_RPC_WORKERS, len(candidates))
    with ThreadPoolExecutor(max_workers=worker_count or 1) as executor:
        futures = [executor.submit(probe, eid) for eid in candidates]
        for future in as_completed(futures):
            apply_result(*future.result())

    for recovery_round in range(1, P4_CHAIN_RECOVERY_ROUNDS):
        if not retryable:
            break
        now_mono = time.monotonic()
        waits = [
            max(0.0, pool.state[eid]["cooldown_until"] - now_mono)
            for eid in retryable
            if eid in pool.state
        ]
        wait_for = min(max(waits, default=0.0), P4_RECOVERY_WAIT_MAX)
        if wait_for > 0:
            time.sleep(wait_for)

        retry_ids = list(dict.fromkeys(retryable))
        retryable = []
        with ThreadPoolExecutor(max_workers=min(P4_RPC_WORKERS, len(retry_ids))) as executor:
            futures = [executor.submit(probe, eid) for eid in retry_ids]
            for future in as_completed(futures):
                apply_result(*future.result())

    chain_ok.sort(key=lambda endpoint_id: candidates.index(endpoint_id))
    return chain_ok, diagnostics


def _p4_rpc_token_verification(candidates, verification_state):
    try:
        import sys
        sys.path.insert(0, str((ROOT / "chains" / "polygon-pos").resolve()))
        from polygon_readonly_verifier import RpcPool, load_rpc_endpoints
    except Exception as exc:
        return {"state": verification_state, "verified_count": 0, "chain_137_verified_count": 0, "identity_conflict_count": 0, "error": f"{type(exc).__name__}: {exc}", "batch": [], "cycle_complete": False}

    if not RPC_POOL.exists():
        return {"state": verification_state, "verified_count": 0, "chain_137_verified_count": 0, "identity_conflict_count": 0, "error": "RPC pool file missing", "batch": [], "cycle_complete": False}

    endpoints = load_rpc_endpoints(None, str(RPC_POOL))
    pool = RpcPool(endpoints, P4_RPC_MIN_INTERVAL)
    chain_ok, chain_probe = _p4_discover_chain_endpoints(pool)

    batch = p4_verification_batch(candidates, verification_state)
    probe_addresses = _p4_endpoint_probe_addresses(candidates)
    selected_endpoints, capability_probe = _p4_select_capable_endpoints(
        pool, chain_ok, probe_addresses, max_endpoints=3
    )
    endpoint_success = {}
    endpoint_errors = {}
    candidate_map = {address: {} for address in batch}

    def run_endpoint_batch(eid):
        merged_rows = {}
        try:
            offset = 0
            chunk_size = P4_RPC_CHUNK_TOKENS
            while offset < len(batch):
                chunk = batch[offset:offset + chunk_size]
                calls = []
                for address in chunk:
                    calls.append((f"p4:{eid}:{address}:code", "eth_getCode", [address, "latest"]))
                    calls.append((f"p4:{eid}:{address}:decimals", "eth_call", [{"to": address, "data": "0x313ce567"}, "latest"]))
                    calls.append((f"p4:{eid}:{address}:supply", "eth_call", [{"to": address, "data": "0x18160ddd"}, "latest"]))
                try:
                    _, rows = _p4_rpc_batch_endpoint(pool, eid, calls, timeout=30)
                    merged_rows.update(rows)
                    offset += len(chunk)
                    chunk_size = min(P4_RPC_CHUNK_TOKENS, max(chunk_size, P4_RPC_MIN_CHUNK_TOKENS))
                except P4RateLimitedError as exc:
                    if chunk_size > P4_RPC_MIN_CHUNK_TOKENS:
                        chunk_size = max(P4_RPC_MIN_CHUNK_TOKENS, chunk_size // 2)
                        time.sleep(exc.retry_after_seconds)
                        continue
                    time.sleep(exc.retry_after_seconds)
                    rows = _p4_rpc_single_calls(pool, eid, calls, timeout=30)
                    merged_rows.update(rows)
                    offset += len(chunk)
            return eid, True, merged_rows, ""
        except Exception as exc:
            return eid, False, merged_rows, f"{type(exc).__name__}: {exc}"


    worker_count = min(P4_RPC_WORKERS, len(selected_endpoints))
    with ThreadPoolExecutor(max_workers=worker_count or 1) as executor:
        futures = [executor.submit(run_endpoint_batch, eid) for eid in selected_endpoints]
        for future in as_completed(futures):
            eid, success, rows, error = future.result()
            endpoint_success[eid] = success
            if success:
                pool.mark_success(eid)
            else:
                endpoint_errors[eid] = error
                pool.mark_failure(
                    eid,
                    {"http_status": None, "rate_limited": False, "message": error},
                )

            for address in batch:
                code_row = rows.get(f"p4:{eid}:{address}:code", {})
                dec_row = rows.get(f"p4:{eid}:{address}:decimals", {})
                supply_row = rows.get(f"p4:{eid}:{address}:supply", {})

                code = code_row.get("result")
                decimals = dec_row.get("result")
                total_supply = supply_row.get("result")
                valid_code = isinstance(code, str) and code not in {"", "0x", "0X"}
                valid_decimals = isinstance(decimals, str) and decimals.startswith("0x")
                valid_supply = isinstance(total_supply, str) and total_supply.startswith("0x")
                if valid_decimals:
                    try:
                        valid_decimals = 0 <= int(decimals, 16) <= 255
                    except ValueError:
                        valid_decimals = False

                candidate_map[address][eid] = {
                    "code": code,
                    "decimals": decimals,
                    "total_supply": total_supply,
                    "valid": bool(valid_code and valid_decimals and valid_supply),
                }

    for address in batch:
        observations = []
        for eid in selected_endpoints:
            if not endpoint_success.get(eid):
                continue
            row = candidate_map.get(address, {}).get(eid, {})
            if not row.get("valid"):
                continue
            observations.append({
                "rpc": eid,
                "code_hash": hashlib.sha256(row["code"].lower().encode()).hexdigest(),
                "decimals": row["decimals"].lower(),
                "total_supply": row["total_supply"].lower(),
            })

        semantic_fingerprints = {(x["code_hash"], x["decimals"]) for x in observations}
        total_supply_values = {x["total_supply"] for x in observations}
        matching = len(observations) >= 2 and len(semantic_fingerprints) == 1
        conflict = len(observations) >= 2 and len(semantic_fingerprints) > 1

        verification_state[address] = {
            "chain_id": 137 if chain_ok else None,
            "rpc_endpoints": [x["rpc"] for x in observations],
            "observations": observations,
            "semantic_fingerprint_fields": ["code_hash", "decimals"],
            "matching": matching,
            "conflict": conflict,
            "total_supply_equal": len(total_supply_values) <= 1,
            "dynamic_state_note": "totalSupply is dynamic state and is not an identity conflict",
            "last_verified_at": now(),
            "transport": "json_rpc_batch",
        }

    candidate_set = set(candidates)
    verification_state = {address: row for address, row in verification_state.items() if address in candidate_set}
    verified_count = sum(1 for x in verification_state.values() if x.get("matching"))
    conflict_count = sum(1 for x in verification_state.values() if x.get("conflict"))
    cycle_complete = verified_count == len(candidates) and len(candidates) > 0

    save_payload = {
        "universe_fingerprint_context": sha(candidates),
        "updated_at": now(),
        "batch_size": P4_VERIFY_BATCH_SIZE,
        "last_batch": batch,
        "candidate_count": len(candidates),
        "verified_count": verified_count,
        "verification_cycle_complete": cycle_complete,
        "verification": verification_state,
        "transport": "json_rpc_batch",
        "endpoint_success": endpoint_success,
        "endpoint_errors": endpoint_errors,
        "capability_probe": capability_probe,
        "selected_endpoints": selected_endpoints,
        "chain_probe": chain_probe,
        "rpc_workers": P4_RPC_WORKERS,
        "endpoint_scan_max": P4_ENDPOINT_SCAN_MAX,
        "chain_recovery_rounds": P4_CHAIN_RECOVERY_ROUNDS,
        "recovery_wait_max": P4_RECOVERY_WAIT_MAX,
        "rpc_min_interval": P4_RPC_MIN_INTERVAL,
        "rpc_chunk_tokens": P4_RPC_CHUNK_TOKENS,
    }
    P4_VERIFY_STATE.parent.mkdir(parents=True, exist_ok=True)
    P4_VERIFY_STATE.write_text(json.dumps(save_payload, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "state": verification_state,
        "verified_count": verified_count,
        "chain_137_verified_count": verified_count,
        "identity_conflict_count": conflict_count,
        "error": "" if len(selected_endpoints) >= 2 else "Fewer than two independent semantically capable Polygon batch endpoints",
        "batch": batch,
        "cycle_complete": cycle_complete,
    }


def task_p4_tokens():
    gt_url = "https://api.geckoterminal.com/api/v2/networks/polygon_pos/pools?page=1&include=base_token,quote_token"
    st_gt, gecko, err_gt = http_json(gt_url, timeout=20)
    st_profiles, profiles, err_profiles = http_json(DexProfilesURL, timeout=20)
    profiles = profiles if isinstance(profiles, list) else []

    provider_sources = defaultdict(set)
    candidates = {}

    for row in load_seed_tokens():
        address = _extract_address(row.get("address"))
        if address:
            candidates[address] = {"address": address, "source": "polygon_seed_manifest", "first_seen": row.get("first_seen", now())}
            provider_sources[address].add("seed")

    gecko_addresses = extract_gecko_token_addresses(gecko)
    for address in gecko_addresses:
        candidates[address] = {"address": address, "source": "geckoterminal_top_pools", "first_seen": now()}
        provider_sources[address].add("gecko")

    profile_addresses = set()
    for row in profiles:
        if str(row.get("chainId", "")).lower() != "polygon":
            continue
        address = _extract_address(row.get("tokenAddress"))
        if address:
            profile_addresses.add(address)
            candidates[address] = {"address": address, "source": "dexscreener_profile", "first_seen": now()}
            provider_sources[address].add("dexscreener")

    dex_addresses = set()
    candidate_seed_batch = sorted(candidates)[:90]
    for offset in range(0, len(candidate_seed_batch), 30):
        batch = candidate_seed_batch[offset:offset + 30]
        if not batch:
            continue
        st_dex, dex_rows, _ = http_json("https://api.dexscreener.com/tokens/v1/polygon/" + ",".join(batch), timeout=20)
        if st_dex == 200:
            for address in extract_dex_token_addresses(dex_rows):
                dex_addresses.add(address)
                candidates[address] = {"address": address, "source": "dexscreener_tokens", "first_seen": now()}
                provider_sources[address].add("dexscreener")

    source_sets = {
        "gecko": {a for a, sources in provider_sources.items() if "gecko" in sources},
        "dexscreener": {a for a, sources in provider_sources.items() if "dexscreener" in sources},
    }
    provider_overlap = source_sets["gecko"] & source_sets["dexscreener"]
    duplicate_address_count = len(candidates) - len(set(candidates))
    candidate_list = sorted(candidates)

    previous_closure = load_json(EVID / "P4_CLOSURE_STATE.json", {})
    verification_state_payload = load_json(P4_VERIFY_STATE, {})
    verification_state = verification_state_payload.get("verification", {})
    previous_context_fp = verification_state_payload.get("universe_fingerprint_context")
    universe_fingerprint = sha({"candidates": candidate_list, "provider_overlap": sorted(provider_overlap)})

    if previous_context_fp != sha(candidate_list):
        verification_state = {}

    verification = _p4_rpc_token_verification(candidate_list, verification_state)
    verified = verification.get("state", {})

    for address in candidate_list:
        identity = verified.get(address)
        if identity and identity.get("matching"):
            candidates[address]["identity"] = identity
            candidates[address]["evidence_class"] = "ONCHAIN_SEMANTIC"

    verification_cycle_complete = bool(verification.get("cycle_complete"))
    previous_complete = bool(previous_closure.get("verification_cycle_complete"))
    if verification_cycle_complete:
        if universe_fingerprint == previous_closure.get("fingerprint") and previous_complete:
            stable_runs = int(previous_closure.get("stable_runs", 0) or 0) + 1
        else:
            stable_runs = 1
    else:
        stable_runs = 0

    token_path = UNIV / "tokens.jsonl"
    existing = {str(x.get("address", "")).lower(): x for x in load_jsonl(token_path)}
    before = len(existing)
    for address in candidate_list:
        existing[address] = candidates[address]
    token_path.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in existing.values()), encoding="utf-8")

    snapshot = {
        "task": "p4_token_discovery",
        "time": now(),
        "network": "polygon",
        "chain_id": 137,
        "sources": [gt_url, DexProfilesURL, "https://api.dexscreener.com/tokens/v1/polygon/{token_addresses}"],
        "http": {"geckoterminal_top_pools": st_gt, "dexscreener_profiles": st_profiles},
        "errors": {"geckoterminal_top_pools": err_gt, "dexscreener_profiles": err_profiles},
        "candidate_count": len(candidate_list),
        "seed_candidates": len(load_seed_tokens()),
        "gecko_candidates": len(gecko_addresses),
        "dexscreener_profile_candidates": len(profile_addresses),
        "dexscreener_token_confirmations": len(dex_addresses),
        "provider_overlap_count": len(provider_overlap),
        "duplicate_address_count": duplicate_address_count,
        "verified_token_count": verification.get("verified_count", 0),
        "chain_137_verified_count": verification.get("chain_137_verified_count", 0),
        "identity_conflict_count": verification.get("identity_conflict_count", 0),
        "rpc_verification_error": verification.get("error", ""),
        "verification_batch": verification.get("batch", []),
        "verification_batch_size": P4_VERIFY_BATCH_SIZE,
        "verification_cycle_complete": verification_cycle_complete,
        "verification_checkpoint": str(P4_VERIFY_STATE),
        "verified_addresses": sorted(a for a in verified if verified[a].get("matching")),
        "stable_runs": stable_runs,
        "universe_fingerprint": universe_fingerprint,
        "new_unique_candidates": max(0, len(existing) - before),
        "universe_total_after_merge": len(existing),
        "candidate_addresses": candidate_list,
        "evidence_class": "DISCOVERY_PLUS_ONCHAIN_IDENTITY",
        "checks": {
            "geckoterminal_top_pools_ok": st_gt == 200 and isinstance(gecko, dict),
            "dexscreener_profiles_ok": st_profiles == 200 and isinstance(profiles, list),
            "dexscreener_tokens_ok": len(dex_addresses) > 0,
        },
    }

    snapshot["stage_gate"] = "CLOSED" if p4_closure_ready(snapshot, {
        "fingerprint": previous_closure.get("fingerprint"),
        "stable_runs": stable_runs,
        "verification_cycle_complete": previous_complete,
    }) else "OPEN"

    write_json("P4_CLOSURE_STATE.json", {
        "fingerprint": universe_fingerprint,
        "stable_runs": stable_runs,
        "updated_at": snapshot["time"],
        "stage_gate": snapshot["stage_gate"],
        "verification_cycle_complete": verification_cycle_complete,
        "candidate_count": len(candidate_list),
        "verified_token_count": verification.get("verified_count", 0),
    })
    return write_json("P4_TOKEN_SNAPSHOT.json", snapshot)


P5_PAIR_BATCH_SIZE = 120
P5_PAIR_WORKERS = 12
P5_STABILITY_WORKERS = 4
P5_CURSOR_STATE = EVID / "P5_CURSOR.json"
P5_STABILITY_STATE = EVID / "P5_STABILITY_STATE.json"
P5_STABILITY_RECHECK = True
P5_REQUEST_RETRIES = 3
P5_STABILITY_SCHEMA = "full-pair-universe-v2"


def p5_token_eligible(row):
    return bool(
        row.get("p5_scan_eligible") is True
        or row.get("evidence_class") == "ONCHAIN_SEMANTIC"
        or row.get("source") in {"polygon_seed_manifest", "dexscreener_pair_token"}
    )


def p5_pair_identity(row):
    return (
        str(row.get("chainId", "")).lower(),
        str((row.get("baseToken") or {}).get("address", "")).lower(),
        str((row.get("quoteToken") or {}).get("address", "")).lower(),
        str(row.get("dexId", "")).lower(),
    )




def p5_pair_universe_fingerprint(eligible_rows, pair_rows):
    pair_identity_sets = defaultdict(set)
    for row in pair_rows:
        address = str(row.get("pairAddress", "")).lower()
        if address:
            pair_identity_sets[address].add(p5_pair_identity(row))
    conflict_count = sum(1 for values in pair_identity_sets.values() if len(values) > 1)
    fingerprint = sha({
        "eligible_tokens": [
            str(row.get("address", "")).lower()
            for row in eligible_rows
        ],
        "pair_addresses": sorted(
            str(row.get("pairAddress", "")).lower()
            for row in pair_rows
            if row.get("pairAddress")
        ),
        "pair_identities": {
            address: sorted(values)
            for address, values in sorted(pair_identity_sets.items())
        },
    })
    return fingerprint, conflict_count

def p5_closure_ready(snapshot, previous_state):
    checks = snapshot.get("checks", {})
    current_fp = snapshot.get("universe_fingerprint")
    previous_fp = previous_state.get("fingerprint")
    stable_count = int(snapshot.get("stable_runs", 0) or 0)
    return (
        checks.get("source_requests_complete") is True
        and checks.get("eligible_token_universe_nonempty") is True
        and snapshot.get("coverage_complete") is True
        and int(snapshot.get("pair_identity_conflict_count", 0)) == 0
        and int(snapshot.get("total_pair_records", 0)) > 0
        and current_fp
        and current_fp == previous_fp
        and previous_state.get("coverage_complete") is True
        and stable_count >= 1
    )


def task_p5_pairs():
    raw_tokens = load_jsonl(UNIV / "tokens.jsonl")
    tokens_by_address = {
        str(row.get("address", "")).lower(): row
        for row in raw_tokens
        if row.get("address")
    }

    eligible = []
    for row in tokens_by_address.values():
        if p5_token_eligible(row):
            row["p5_scan_eligible"] = True
            eligible.append(row)
    eligible.sort(key=lambda row: str(row.get("address", "")).lower())

    cursor_payload = load_json(P5_CURSOR_STATE, {})
    stability_state = load_json(P5_STABILITY_STATE, {})

    processed_addresses = {
        str(x).lower()
        for x in cursor_payload.get("processed_addresses", [])
        if isinstance(x, str)
    }
    stability_processed_addresses = {
        str(x).lower()
        for x in stability_state.get("processed_addresses", [])
        if isinstance(x, str)
    }

    eligibility_addresses = [str(row.get("address", "")).lower() for row in eligible]
    eligibility_fp = sha(eligibility_addresses)

    previous_closure = load_json(EVID / "P5_CLOSURE_STATE.json", {})
    previous_complete = bool(previous_closure.get("coverage_complete"))

    baseline_fp = stability_state.get("baseline_fingerprint")
    baseline_eligibility_fp = stability_state.get("baseline_eligibility_fingerprint")
    stability_schema = stability_state.get("schema")
    stability_schema_compatible = stability_schema == P5_STABILITY_SCHEMA

    if not stability_schema_compatible:
        baseline_fp = None
        baseline_eligibility_fp = None
        stability_processed_addresses = set()

    if baseline_eligibility_fp and baseline_eligibility_fp != eligibility_fp:
        baseline_fp = None
        baseline_eligibility_fp = None
        stability_processed_addresses = set()

    # Recovery bootstrap: if the prior run had a complete primary coverage
    # result but no stability state yet, preserve that complete result as the
    # immutable baseline for the next full stability pass.
    if (
        stability_schema_compatible
        and not baseline_fp
        and previous_complete
        and previous_closure.get("fingerprint")
    ):
        baseline_fp = previous_closure.get("fingerprint")
        baseline_eligibility_fp = (
            stability_state.get("baseline_eligibility_fingerprint")
            or cursor_payload.get("eligibility_fingerprint")
            or eligibility_fp
        )
        stability_processed_addresses = set()

    recheck_mode = bool(
        P5_STABILITY_RECHECK
        and baseline_fp
        and baseline_eligibility_fp == eligibility_fp
    )

    if recheck_mode:
        batch = [
            row for row in eligible
            if str(row.get("address", "")).lower()
            not in stability_processed_addresses
        ][:P5_PAIR_BATCH_SIZE]
        worker_limit = P5_STABILITY_WORKERS
    else:
        batch = [
            row for row in eligible
            if str(row.get("address", "")).lower()
            not in processed_addresses
        ][:P5_PAIR_BATCH_SIZE]
        worker_limit = P5_PAIR_WORKERS

    pair_results = []
    request_errors = []

    def fetch_pairs(row):
        address = str(row.get("address", "")).lower()
        started = time.monotonic()
        last_error = None

        for attempt in range(1, P5_REQUEST_RETRIES + 1):
            st, pairs, err = http_json(
                f"https://api.dexscreener.com/token-pairs/v1/polygon/{address}",
                timeout=20,
            )
            last_error = err
            if st == 200 and isinstance(pairs, list):
                return {
                    "address": address,
                    "status": st,
                    "pairs": pairs,
                    "error": None,
                    "attempts": attempt,
                    "elapsed_sec": round(time.monotonic() - started, 3),
                }

            if err and "429" in str(err) and attempt < P5_REQUEST_RETRIES:
                time.sleep(min(8, 2 ** attempt))
                continue

            return {
                "address": address,
                "status": st,
                "pairs": pairs,
                "error": last_error,
                "attempts": attempt,
                "elapsed_sec": round(time.monotonic() - started, 3),
            }

        return {
            "address": address,
            "status": None,
            "pairs": None,
            "error": last_error,
            "attempts": P5_REQUEST_RETRIES,
            "elapsed_sec": round(time.monotonic() - started, 3),
        }

    with ThreadPoolExecutor(max_workers=min(worker_limit, max(1, len(batch)))) as executor:
        futures = [executor.submit(fetch_pairs, row) for row in batch]
        for future in as_completed(futures):
            result = future.result()
            pair_results.append(result)
            if result.get("status") != 200 or not isinstance(result.get("pairs"), list):
                request_errors.append({
                    "address": result.get("address"),
                    "status": result.get("status"),
                    "error": result.get("error"),
                    "attempts": result.get("attempts"),
                })

    rows = []
    successful_addresses = set()
    for result in pair_results:
        if result.get("status") != 200 or not isinstance(result.get("pairs"), list):
            continue
        successful_addresses.add(result.get("address"))
        for pair in result["pairs"]:
            if str(pair.get("chainId", "")).lower() != "polygon":
                continue
            pair_address = pair.get("pairAddress")
            if not pair_address:
                continue
            pair = dict(pair)
            pair["_snapshot_time"] = now()
            pair["_source"] = "dexscreener_token_pairs"
            rows.append(pair)

    pair_path = UNIV / "pairs.jsonl"
    existing_pairs = load_jsonl(pair_path)
    by_address = {
        str(x.get("pairAddress", "")).lower(): x
        for x in existing_pairs
        if x.get("pairAddress")
    }
    before_pairs = len(by_address)

    discovered_tokens = {}
    for row in rows:
        address = str(row.get("pairAddress", "")).lower()
        if address:
            by_address[address] = row
        for side in ("baseToken", "quoteToken"):
            token = (row.get(side) or {}).get("address")
            if token and len(str(token)) == 42 and str(token).lower().startswith("0x"):
                token_key = str(token).lower()
                discovered_tokens[token_key] = {
                    "address": str(token),
                    "source": "dexscreener_pair_token",
                    "first_seen": now(),
                    "p5_scan_eligible": True,
                }

    batch_pair_identity_sets = defaultdict(set)
    for row in rows:
        address = str(row.get("pairAddress", "")).lower()
        if address:
            batch_pair_identity_sets[address].add(p5_pair_identity(row))
    duplicate_pair_observation_count = max(
        0,
        len(rows) - len({
            str(x.get("pairAddress", "")).lower()
            for x in rows if x.get("pairAddress")
        }),
    )

    merged_pairs = list(by_address.values())

    tokens_before = len(tokens_by_address)
    tokens_by_address.update(discovered_tokens)
    token_path = UNIV / "tokens.jsonl"
    token_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in tokens_by_address.values()),
        encoding="utf-8",
    )
    pair_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in merged_pairs),
        encoding="utf-8",
    )

    new_unique_tokens = max(0, len(tokens_by_address) - tokens_before)

    if recheck_mode:
        stability_processed_addresses.update(successful_addresses)
    else:
        processed_addresses.update(successful_addresses)

    eligible_after_merge = sorted(
        [row for row in tokens_by_address.values() if p5_token_eligible(row)],
        key=lambda row: str(row.get("address", "")).lower(),
    )

    processed_eligible_count = sum(
        1 for row in eligible_after_merge
        if str(row.get("address", "")).lower() in processed_addresses
    )
    rechecked_eligible_count = sum(
        1 for row in eligible_after_merge
        if str(row.get("address", "")).lower() in stability_processed_addresses
    )

    if recheck_mode:
        coverage_complete = (
            len(eligible_after_merge) > 0
            and rechecked_eligible_count == len(eligible_after_merge)
            and len(request_errors) == 0
            and new_unique_tokens == 0
        )
    else:
        coverage_complete = (
            len(eligible_after_merge) > 0
            and processed_eligible_count == len(eligible_after_merge)
            and len(request_errors) == 0
            and new_unique_tokens == 0
        )

    universe_fingerprint, pair_identity_conflict_count = p5_pair_universe_fingerprint(
        eligible_after_merge,
        merged_pairs,
    )

    stable_runs = 0
    stage_gate = "OPEN"

    if recheck_mode and coverage_complete:
        if (
            universe_fingerprint == baseline_fp
            and baseline_eligibility_fp == eligibility_fp
        ):
            stable_runs = int(stability_state.get("stable_runs", 0) or 0) + 1
        else:
            # Universe changed during recheck. Promote the new fingerprint to
            # the next immutable baseline and require another complete pass.
            baseline_fp = universe_fingerprint
            baseline_eligibility_fp = eligibility_fp
            stability_processed_addresses = set()
            stable_runs = 0
    elif not recheck_mode and coverage_complete:
        if not baseline_fp:
            baseline_fp = universe_fingerprint
            baseline_eligibility_fp = eligibility_fp
        stable_runs = 0

    snapshot = {
        "task": "p5_pair_discovery",
        "time": now(),
        "processed_tokens": len(batch),
        "processed_eligible_count": processed_eligible_count,
        "rechecked_eligible_count": rechecked_eligible_count,
        "eligible_token_count": len(eligible_after_merge),
        "observed_pair_rows": len(rows),
        "new_unique_pairs": max(0, len(merged_pairs) - before_pairs),
        "new_unique_tokens": new_unique_tokens,
        "total_pair_records": len(merged_pairs),
        "duplicate_pair_observation_count": duplicate_pair_observation_count,
        "pair_identity_conflict_count": pair_identity_conflict_count,
        "coverage_complete": coverage_complete,
        "stable_runs": stable_runs,
        "universe_fingerprint": universe_fingerprint,
        "request_errors": request_errors[-50:],
        "pair_workers": worker_limit,
        "pair_batch_size": P5_PAIR_BATCH_SIZE,
        "recheck_mode": recheck_mode,
        "baseline_fingerprint": baseline_fp,
        "baseline_eligibility_fingerprint": baseline_eligibility_fp,
        "stability_state_file": str(P5_STABILITY_STATE),
        "checks": {
            "source_requests_complete": len(request_errors) == 0 and (
                len(batch) > 0 or coverage_complete
            ),
            "eligible_token_universe_nonempty": len(eligible_after_merge) > 0,
        },
        "evidence_class": "DISCOVERY",
    }

    if (
        recheck_mode
        and coverage_complete
        and stable_runs >= 1
        and universe_fingerprint == baseline_fp
        and baseline_eligibility_fp == eligibility_fp
    ):
        stage_gate = "CLOSED" if p5_closure_ready(snapshot, {
            "fingerprint": baseline_fp,
            "stable_runs": max(0, stable_runs - 1),
            "coverage_complete": True,
        }) else "OPEN"

    snapshot["stage_gate"] = stage_gate

    write_json("P5_CLOSURE_STATE.json", {
        "fingerprint": universe_fingerprint,
        "stable_runs": stable_runs,
        "updated_at": snapshot["time"],
        "stage_gate": stage_gate,
        "coverage_complete": coverage_complete,
        "eligible_token_count": len(eligible_after_merge),
        "processed_eligible_count": processed_eligible_count,
        "rechecked_eligible_count": rechecked_eligible_count,
        "total_pair_records": len(merged_pairs),
    })

    P5_STABILITY_STATE.parent.mkdir(parents=True, exist_ok=True)
    P5_STABILITY_STATE.write_text(
        json.dumps({
            "schema": P5_STABILITY_SCHEMA,
            "baseline_fingerprint": baseline_fp,
            "baseline_eligibility_fingerprint": baseline_eligibility_fp,
            "processed_addresses": sorted(stability_processed_addresses),
            "stable_runs": stable_runs,
            "active": stage_gate != "CLOSED",
            "updated_at": now(),
        }, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_json("P5_CURSOR.json", {
        "processed_addresses": sorted(processed_addresses),
        "total_eligible_tokens": len(eligible_after_merge),
        "eligibility_fingerprint": eligibility_fp,
        "last_coverage_complete": coverage_complete,
    })
    return write_json("P5_PAIR_SNAPSHOT.json", snapshot)


P6_ROUTE_STORAGE_LIMIT = 5000
P6_CLOSURE_STATE = EVID / "P6_CLOSURE_STATE.json"


def p6_route_closure_ready(snapshot, previous_state):
    checks = snapshot.get("checks", {})
    current_fp = snapshot.get("graph_fingerprint")
    previous_fp = previous_state.get("fingerprint")
    stable_count = int(snapshot.get("stable_runs", 0) or 0)
    return (
        checks.get("p5_pair_universe_aligned") is True
        and checks.get("all_pair_records_consumed") is True
        and checks.get("no_invalid_pair_records") is True
        and checks.get("route_enumeration_complete") is True
        and int(snapshot.get("pair_nodes", 0)) > 0
        and int(snapshot.get("unique_pairs", 0)) > 0
        and current_fp
        and current_fp == previous_fp
        and previous_state.get("route_enumeration_complete") is True
        and stable_count >= 1
    )


def task_p6_routes():
    pairs = load_jsonl(UNIV / "pairs.jsonl")
    adj = defaultdict(list)
    seen = set()
    invalid_pair_records = 0
    graph_records = []

    for p in pairs:
        b = (p.get("baseToken") or {}).get("address")
        q = (p.get("quoteToken") or {}).get("address")
        pair = p.get("pairAddress")
        if not b or not q or not pair or b.lower() == q.lower():
            invalid_pair_records += 1
            continue
        b = str(b).lower()
        q = str(q).lower()
        pair = str(pair).lower()
        key = (b, q, pair)
        if key in seen:
            continue
        seen.add(key)
        graph_records.append(key)
        adj[b].append((q, pair))
        adj[q].append((b, pair))

    for node in adj:
        adj[node].sort(key=lambda item: (item[1], item[0]))

    routes = []
    route_count_total = 0

    def dfs(start, node, path, used):
        nonlocal route_count_total
        if len(path) >= 4:
            return
        for nxt, pair in adj.get(node, []):
            if pair in used:
                continue
            if nxt == start:
                if len(path) >= 3:
                    route_count_total += 1
                    if len(routes) < P6_ROUTE_STORAGE_LIMIT:
                        routes.append(path + [(start, pair)])
                continue
            if nxt in [x[0] for x in path]:
                continue
            dfs(start, nxt, path + [(nxt, pair)], used | {pair})

    for token in sorted(adj):
        dfs(token, token, [(token, "")], set())

    previous = load_json(P6_CLOSURE_STATE, {})
    graph_fingerprint = sha(sorted(graph_records))
    previous_fp = previous.get("fingerprint")
    previous_complete = previous.get("route_enumeration_complete") is True
    if graph_fingerprint and graph_fingerprint == previous_fp and previous_complete:
        stable_runs = int(previous.get("stable_runs", 0) or 0) + 1
    else:
        stable_runs = 1

    p5 = load_json(EVID / "P5_PAIR_SNAPSHOT.json", {})
    expected_pairs = int(p5.get("total_pair_records", 0) or 0)
    snapshot = {
        "task": "p6_route_enumeration",
        "time": now(),
        "pair_records_consumed": len(pairs),
        "valid_pair_records": len(pairs) - invalid_pair_records,
        "invalid_pair_records": invalid_pair_records,
        "pair_nodes": len(adj),
        "unique_pairs": len(seen),
        "p5_total_pair_records": expected_pairs,
        "graph_fingerprint": graph_fingerprint,
        "route_candidates": routes,
        "route_count_sampled": len(routes),
        "route_count_total": route_count_total,
        "route_storage_limit": P6_ROUTE_STORAGE_LIMIT,
        "route_storage_truncated": route_count_total > len(routes),
        "stable_runs": stable_runs,
        "route_enumeration_complete": True,
        "checks": {
            "p5_pair_universe_aligned": expected_pairs > 0 and len(seen) == expected_pairs,
            "all_pair_records_consumed": len(pairs) == len(seen) + invalid_pair_records,
            "no_invalid_pair_records": invalid_pair_records == 0,
            "route_enumeration_complete": True,
        },
        "evidence_class": "DERIVED",
    }
    snapshot["stage_gate"] = "CLOSED" if p6_route_closure_ready(
        snapshot,
        {
            "fingerprint": previous_fp,
            "stable_runs": max(0, stable_runs - 1),
            "route_enumeration_complete": previous_complete,
        },
    ) else "OPEN"

    write_json("P6_CLOSURE_STATE.json", {
        "fingerprint": graph_fingerprint,
        "stable_runs": stable_runs,
        "updated_at": snapshot["time"],
        "stage_gate": snapshot["stage_gate"],
        "route_enumeration_complete": True,
        "pair_nodes": len(adj),
        "unique_pairs": len(seen),
        "route_count_total": route_count_total,
    })
    return write_json("P6_ROUTE_SNAPSHOT.json", snapshot)

STRATEGY_SCHEMA_VERSION = "p7-strategy-matrix-v2"

STRATEGIES = [
    "dex_dex",
    "intra_dex",
    "triangular",
    "multi_hop",
    "split",
    "flash_loan",
    "liquidation",
    "backrun",
    "orderflow_mev",
    "intent_rfq_filler",
    "solver_relayer",
    "liquidity_state_transition",
    "cross_domain",
    "statistical_temporal",
    "gas_regime",
    "failed_tx_retry_state",
    "protocol_structural",
    "negative_space_hypothesis",
]

P7_REQUIRED_FIELDS = [
    "mechanism",
    "prerequisites",
    "exact_contracts",
    "state_dependencies",
    "cost_model",
    "failure_modes",
    "competition_model",
    "simulation_method",
    "historical_evidence",
    "live_shadow_evidence",
    "profitability_status",
    "confidence",
    "unknowns",
]

P7_CLOSURE_STATE = EVID / "P7_CLOSURE_STATE.json"

P7_MECHANISM_HYPOTHESES = {
    "dex_dex": "Cross-venue price discrepancy candidate.",
    "intra_dex": "Single-venue path/state discrepancy candidate.",
    "triangular": "Three-asset cyclic conversion discrepancy candidate.",
    "multi_hop": "Multi-hop path pricing/state discrepancy candidate.",
    "split": "Split-flow routing candidate across alternative paths.",
    "flash_loan": "Atomic flash-funded strategy wrapper around an eligible route or state transition.",
    "liquidation": "Protocol liquidation incentive/state-transition candidate.",
    "backrun": "Post-transaction state-change opportunity candidate.",
    "orderflow_mev": "Orderflow-dependent candidate requiring eligible transaction-order information.",
    "intent_rfq_filler": "Intent/RFQ fulfillment candidate subject to solver/filler constraints.",
    "solver_relayer": "Solver/relayer path candidate subject to protocol-specific settlement rules.",
    "liquidity_state_transition": "Liquidity-state change candidate independent of simple price spread.",
    "cross_domain": "Cross-domain opportunity candidate subject to bridge/message/settlement state.",
    "statistical_temporal": "Temporal/statistical recurrence candidate requiring historical evidence.",
    "gas_regime": "Gas-regime-dependent opportunity candidate.",
    "failed_tx_retry_state": "Failed/retried transaction-state opportunity hypothesis.",
    "protocol_structural": "Protocol-specific structural opportunity hypothesis.",
    "negative_space_hypothesis": "Explicit unknown/negative-space research hypothesis; no profitability assertion.",
}

def p7_strategy_row(strategy, route_count_total, route_fingerprint):
    return {
        "strategy_id": strategy,
        "strategy": strategy,
        "candidate": True,
        "status": "RESEARCH_CANDIDATE_UNRESOLVED",
        "evidence_class": "DERIVED_COVERAGE",
        "mechanism": {
            "status": "HYPOTHESIS_ONLY",
            "summary": P7_MECHANISM_HYPOTHESES[strategy],
        },
        "prerequisites": {
            "status": "UNRESOLVED",
            "items": [],
        },
        "exact_contracts": {
            "status": "NOT_IDENTIFIED",
            "items": [],
        },
        "state_dependencies": {
            "status": "UNRESOLVED",
            "items": [],
        },
        "cost_model": {
            "status": "NOT_CERTIFIED",
            "components": [
                "gas",
                "venue_fees",
                "slippage",
                "execution_cost",
                "strategy_specific_costs",
            ],
        },
        "failure_modes": {
            "status": "UNRESOLVED",
            "items": [],
        },
        "competition_model": {
            "status": "UNRESOLVED",
            "items": [],
        },
        "simulation_method": {
            "status": "EXACT_SIMULATION_REQUIRED",
            "method": "Pending venue/protocol-specific exact-state simulation.",
        },
        "historical_evidence": {
            "status": "NOT_COLLECTED",
            "sources": [],
        },
        "live_shadow_evidence": {
            "status": "NOT_COLLECTED",
            "sources": [],
        },
        "profitability_status": "NOT_CERTIFIED",
        "confidence": {
            "level": "LOW",
            "reason": "Strategy-family coverage is established; strategy-specific contract/state/economic evidence is still unresolved.",
        },
        "unknowns": [
            "exact contracts and protocol surfaces",
            "strategy-specific state dependencies",
            "complete cost model",
            "failure and competition behavior",
            "historical/live shadow evidence",
            "exact economic profitability",
        ],
        "route_context": {
            "available": route_count_total > 0,
            "route_count_total": route_count_total,
            "graph_fingerprint": route_fingerprint,
            "mapping_status": "NOT_CLASSIFIED_PER_STRATEGY",
        },
    }

def p7_strategy_closure_ready(snapshot, previous_state):
    checks = snapshot.get("checks", {})
    current_fp = snapshot.get("matrix_fingerprint")
    previous_fp = previous_state.get("fingerprint")
    stable_count = int(snapshot.get("stable_runs", 0) or 0)
    return (
        checks.get("p6_route_source_closed") is True
        and checks.get("strategy_set_complete") is True
        and checks.get("unique_strategy_ids") is True
        and checks.get("required_fields_complete") is True
        and checks.get("unresolved_fields_explicit") is True
        and int(snapshot.get("strategy_count", 0)) == len(STRATEGIES)
        and current_fp
        and current_fp == previous_fp
        and previous_state.get("matrix_complete") is True
        and stable_count >= 1
    )

def task_p7_strategies():
    p6_path = EVID / "P6_ROUTE_SNAPSHOT.json"
    p6 = load_json(p6_path, {}) if p6_path.exists() else {}
    p6_closed = p6.get("stage_gate") == "CLOSED"
    route_count_total = int(p6.get("route_count_total", 0) or 0)
    route_fingerprint = p6.get("graph_fingerprint", "")

    rows = [
        p7_strategy_row(strategy, route_count_total, route_fingerprint)
        for strategy in STRATEGIES
    ]

    row_ids = [row["strategy_id"] for row in rows]
    unique_ids = len(row_ids) == len(set(row_ids))
    expected = set(STRATEGIES)
    strategy_set_complete = set(row_ids) == expected

    required_fields_complete = all(
        all(field in row and row[field] not in (None, "") for field in P7_REQUIRED_FIELDS)
        for row in rows
    )
    unresolved_fields_explicit = all(
        row["status"] == "RESEARCH_CANDIDATE_UNRESOLVED"
        and row["exact_contracts"]["status"] == "NOT_IDENTIFIED"
        and row["profitability_status"] == "NOT_CERTIFIED"
        for row in rows
    )

    matrix_seed = {
        "schema": STRATEGY_SCHEMA_VERSION,
        "strategies": rows,
        "route_source": {
            "stage_gate": p6.get("stage_gate"),
            "route_count_total": route_count_total,
            "graph_fingerprint": route_fingerprint,
        },
    }
    matrix_fingerprint = sha(matrix_seed)

    previous = load_json(P7_CLOSURE_STATE, {})
    previous_fp = previous.get("fingerprint")
    previous_complete = previous.get("matrix_complete") is True

    if matrix_fingerprint and matrix_fingerprint == previous_fp and previous_complete:
        stable_runs = int(previous.get("stable_runs", 0) or 0) + 1
    else:
        stable_runs = 1

    snapshot = {
        "task": "p7_strategy_matrix",
        "time": now(),
        "schema": STRATEGY_SCHEMA_VERSION,
        "strategies": rows,
        "count": len(rows),
        "strategy_count": len(rows),
        "route_source": {
            "stage_gate": p6.get("stage_gate"),
            "route_count_total": route_count_total,
            "graph_fingerprint": route_fingerprint,
        },
        "matrix_fingerprint": matrix_fingerprint,
        "stable_runs": stable_runs,
        "matrix_complete": True,
        "checks": {
            "p6_route_source_closed": p6_closed and route_count_total > 0 and bool(route_fingerprint),
            "strategy_set_complete": strategy_set_complete,
            "unique_strategy_ids": unique_ids,
            "required_fields_complete": required_fields_complete,
            "unresolved_fields_explicit": unresolved_fields_explicit,
        },
        "evidence_class": "DERIVED_COVERAGE",
        "research_boundary": "P7 closes strategy-family coverage/schema completeness only; it does not certify exact contracts, execution, economics, or profitability.",
    }

    snapshot["stage_gate"] = "CLOSED" if p7_strategy_closure_ready(
        snapshot,
        {
            "fingerprint": previous_fp,
            "stable_runs": max(0, stable_runs - 1),
            "matrix_complete": previous_complete,
        },
    ) else "OPEN"

    write_json("P7_CLOSURE_STATE.json", {
        "fingerprint": matrix_fingerprint,
        "stable_runs": stable_runs,
        "updated_at": snapshot["time"],
        "stage_gate": snapshot["stage_gate"],
        "matrix_complete": True,
        "strategy_count": len(rows),
        "route_count_total": route_count_total,
    })
    return write_json("P7_STRATEGY_MATRIX.json", snapshot)

P8_FEATURE_SCHEMA_VERSION = "p8-feature-matrix-v2"
P8_REQUIRED_FEATURES = [
    "spread",
    "volatility",
    "volume",
    "liquidity",
    "imbalance",
    "regime",
    "momentum_reversion",
    "route_recurrence",
    "opportunity_persistence",
    "gas_regime",
    "block_activity",
    "flow_toxicity_proxy",
]
P8_CLOSURE_STATE = EVID / "P8_CLOSURE_STATE.json"


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _horizon_number(payload, horizon, key):
    value = (payload.get(horizon) or {}).get(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _horizon_change(payload, horizon):
    value = (payload.get("priceChange") or {}).get(horizon)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _imbalance(txns, horizon="h24"):
    row = txns.get(horizon) or {}
    buys = _safe_float(row.get("buys"))
    sells = _safe_float(row.get("sells"))
    if buys is None or sells is None or buys < 0 or sells < 0:
        return None
    total = buys + sells
    if total <= 0:
        return None
    return (buys - sells) / total


def _p8_group_feature(pair_key, rows, p6):
    prices = [x["price_usd"] for x in rows if isinstance(x.get("price_usd"), (int, float)) and x["price_usd"] > 0]
    spread = (max(prices) / min(prices) - 1.0) if len(prices) >= 2 else None

    changes_by_horizon = {
        horizon: [x["price_change_pct"][horizon] for x in rows if x["price_change_pct"].get(horizon) is not None]
        for horizon in ("m5", "h1", "h6", "h24")
    }
    available_changes = [
        value for values in changes_by_horizon.values() for value in values
        if isinstance(value, (int, float))
    ]
    volatility_proxy = None
    if available_changes:
        volatility_proxy = round(
            math.sqrt(sum(value * value for value in available_changes) / len(available_changes)),
            8,
        )

    h24_imbalance = [
        x["imbalance_h24"] for x in rows
        if isinstance(x.get("imbalance_h24"), (int, float))
    ]
    imbalance = (
        sum(h24_imbalance) / len(h24_imbalance)
        if h24_imbalance else None
    )

    return {
        "pair_key": pair_key,
        "venue_count": len(rows),
        "features": {
            "spread": {
                "status": "OBSERVED" if spread is not None else "UNAVAILABLE",
                "price_spread": spread,
            },
            "volatility": {
                "status": "CROSS_HORIZON_PROXY",
                "proxy_rms_pct": volatility_proxy,
                "source": "snapshot priceChange fields",
                "not_realized_time_series": True,
            },
            "volume": {
                "status": "OBSERVED",
                "h24_total_usd": round(sum(
                    x["volume_h24_usd"] for x in rows
                    if isinstance(x.get("volume_h24_usd"), (int, float))
                ), 6),
            },
            "liquidity": {
                "status": "OBSERVED",
                "h24_usd_total": round(sum(
                    x["liquidity_usd"] for x in rows
                    if isinstance(x.get("liquidity_usd"), (int, float))
                ), 6),
            },
            "imbalance": {
                "status": "H24_BUY_SELL_PROXY",
                "mean_signed_imbalance": imbalance,
            },
            "regime": {
                "status": "NOT_CLASSIFIED",
                "reason": "No explicit deterministic regime classifier is authorized in the current source contract.",
            },
            "momentum_reversion": {
                "status": "HORIZON_PROXIES_ONLY",
                "h1_pct": sum(changes_by_horizon["h1"]) / len(changes_by_horizon["h1"]) if changes_by_horizon["h1"] else None,
                "h24_pct": sum(changes_by_horizon["h24"]) / len(changes_by_horizon["h24"]) if changes_by_horizon["h24"] else None,
            },
            "route_recurrence": {
                "status": "NOT_CLASSIFIED",
                "route_graph_fingerprint": p6.get("graph_fingerprint") or p6.get("fingerprint"),
            },
            "opportunity_persistence": {
                "status": "NOT_AVAILABLE",
                "reason": "Current pair source is a single timestamped snapshot.",
            },
            "gas_regime": {
                "status": "NOT_AVAILABLE",
                "reason": "No gas time-series source is attached to this feature snapshot.",
            },
            "block_activity": {
                "status": "NOT_AVAILABLE",
                "reason": "No block-indexed event series is attached to this feature snapshot.",
            },
            "flow_toxicity_proxy": {
                "status": "IMBALANCE_PROXY_ONLY",
                "absolute_h24_imbalance": abs(imbalance) if isinstance(imbalance, (int, float)) else None,
                "not_a_toxicity_model": True,
            },
        },
        "venues": rows,
    }


def p8_feature_closure_ready(snapshot, previous_state):
    checks = snapshot.get("checks", {})
    current_fp = snapshot.get("feature_fingerprint")
    previous_fp = previous_state.get("fingerprint")
    stable_count = int(snapshot.get("stable_runs", 0) or 0)
    return (
        checks.get("p7_strategy_source_closed") is True
        and checks.get("pair_universe_nonempty") is True
        and checks.get("feature_schema_complete") is True
        and checks.get("deterministic_observed_features_present") is True
        and checks.get("unavailable_features_explicit") is True
        and int(snapshot.get("pair_groups", 0)) > 0
        and current_fp
        and current_fp == previous_fp
        and previous_state.get("feature_matrix_complete") is True
        and stable_count >= 1
    )


def task_p8_features():
    pairs = load_jsonl(UNIV / "pairs.jsonl")
    p7 = load_json(EVID / "P7_CLOSURE_STATE.json", {})
    p6 = load_json(EVID / "P6_CLOSURE_STATE.json", {})
    groups = defaultdict(list)

    for pair in pairs:
        base = (pair.get("baseToken") or {}).get("address")
        quote = (pair.get("quoteToken") or {}).get("address")
        if not base or not quote:
            continue

        key = ":".join(sorted([str(base).lower(), str(quote).lower()]))
        price = _safe_float(pair.get("priceUsd"))
        price_change = pair.get("priceChange") or {}
        txns = pair.get("txns") or {}
        groups[key].append({
            "dex": pair.get("dexId"),
            "pair": pair.get("pairAddress"),
            "price_usd": price,
            "liquidity_usd": _safe_float((pair.get("liquidity") or {}).get("usd")),
            "volume_h24_usd": _safe_float((pair.get("volume") or {}).get("h24")),
            "price_change_pct": {
                horizon: _safe_float(price_change.get(horizon))
                for horizon in ("m5", "h1", "h6", "h24")
            },
            "imbalance_h24": _imbalance(txns, "h24"),
        })

    features = [
        _p8_group_feature(key, rows, p6)
        for key, rows in sorted(groups.items())
    ]

    required_complete = all(
        set(feature["features"]) == set(P8_REQUIRED_FEATURES)
        for feature in features
    )
    observed_present = all(
        feature["features"]["volume"]["status"] == "OBSERVED"
        and feature["features"]["liquidity"]["status"] == "OBSERVED"
        and feature["features"]["spread"]["status"] in {"OBSERVED", "UNAVAILABLE"}
        for feature in features
    )
    unavailable_explicit = all(
        feature["features"]["regime"]["status"] == "NOT_CLASSIFIED"
        and feature["features"]["opportunity_persistence"]["status"] == "NOT_AVAILABLE"
        and feature["features"]["gas_regime"]["status"] == "NOT_AVAILABLE"
        and feature["features"]["block_activity"]["status"] == "NOT_AVAILABLE"
        for feature in features
    )

    feature_seed = {
        "schema": P8_FEATURE_SCHEMA_VERSION,
        "pair_group_count": len(features),
        "features": features,
        "p7_fingerprint": p7.get("fingerprint"),
        "p6_fingerprint": p6.get("fingerprint"),
    }
    feature_fingerprint = sha(feature_seed)

    previous = load_json(P8_CLOSURE_STATE, {})
    previous_fp = previous.get("fingerprint")
    previous_complete = previous.get("feature_matrix_complete") is True

    if feature_fingerprint and feature_fingerprint == previous_fp and previous_complete:
        stable_runs = int(previous.get("stable_runs", 0) or 0) + 1
    else:
        stable_runs = 1

    snapshot = {
        "task": "p8_features",
        "time": now(),
        "schema": P8_FEATURE_SCHEMA_VERSION,
        "pair_groups": len(features),
        "features": features,
        "feature_fingerprint": feature_fingerprint,
        "stable_runs": stable_runs,
        "feature_matrix_complete": True,
        "source": {
            "pair_records": len(pairs),
            "p7_strategy_gate": p7.get("stage_gate"),
            "p7_fingerprint": p7.get("fingerprint"),
            "p6_fingerprint": p6.get("fingerprint"),
        },
        "checks": {
            "p7_strategy_source_closed": p7.get("stage_gate") == "CLOSED" and bool(p7.get("fingerprint")),
            "pair_universe_nonempty": len(pairs) > 0,
            "feature_schema_complete": required_complete,
            "deterministic_observed_features_present": observed_present,
            "unavailable_features_explicit": unavailable_explicit,
        },
        "evidence_class": "DERIVED_FEATURES",
        "research_boundary": "P8 closes deterministic feature coverage over the available snapshot; it does not certify prediction, profitability, or live execution.",
    }

    snapshot["stage_gate"] = "CLOSED" if p8_feature_closure_ready(
        snapshot,
        {
            "fingerprint": previous_fp,
            "stable_runs": max(0, stable_runs - 1),
            "feature_matrix_complete": previous_complete,
        },
    ) else "OPEN"

    write_json("P8_CLOSURE_STATE.json", {
        "fingerprint": feature_fingerprint,
        "stable_runs": stable_runs,
        "updated_at": snapshot["time"],
        "stage_gate": snapshot["stage_gate"],
        "feature_matrix_complete": True,
        "pair_groups": len(features),
        "pair_records": len(pairs),
    })
    return write_json("P8_FEATURE_SNAPSHOT.json", snapshot)

P9_SCHEMA_VERSION = "p9-economic-certification-v2"
P9_CANDIDATE_BATCH_GROUPS = 100
P9_BATCH_PAIR_LIMIT = 300
P9_PROBE_CHUNK_PAIRS = 25
P9_REQUIRED_CERT_FIELDS = [
    "exact_state_replay",
    "math_family",
    "exact_fee",
    "gas_cost",
    "flash_premium",
    "slippage",
    "transfer_tax",
    "failure_cost",
    "competition",
    "minimum_profit",
    "sensitivity",
    "realized_simulation_error",
]
P9_CLOSURE_STATE = EVID / "P9_CLOSURE_STATE.json"
P9_PROGRESS_STATE = EVID / "P9_CAPABILITY_STATE.json"

def _p9_is_evm_address(value):
    return isinstance(value, str) and len(value) == 42 and value.lower().startswith("0x") and all(
        ch in "0123456789abcdef" for ch in value[2:].lower()
    )


def _p9_ref_type(dex, value):
    if _p9_is_evm_address(value):
        return "evm_pair_address"
    if str(dex or "").lower() == "balancer" and isinstance(value, str) and value.count("-") >= 2:
        return "balancer_pool_id"
    return "non_evm_pool_ref"


def _p9_candidate_rows():
    p8 = load_json(EVID / "P8_FEATURE_SNAPSHOT.json", {})
    rows = []
    for feature in p8.get("features", []):
        f = feature.get("features", {})
        spread_obj = f.get("spread", {})
        spread = spread_obj.get("price_spread")
        venues = feature.get("venues", [])
        prices = [
            v.get("price_usd")
            for v in venues
            if isinstance(v.get("price_usd"), (int, float)) and v.get("price_usd") > 0
        ]
        if len(venues) < 2 or len(prices) < 2 or spread is None:
            continue
        rows.append({
            "pair_key": feature.get("pair_key"),
            "venue_count": len(venues),
            "gross_spread_pct": round(float(spread) * 100.0, 8),
            "venues": [
                {
                    "dex": v.get("dex"),
                    "pair": v.get("pair"),
                    "ref_type": _p9_ref_type(v.get("dex"), v.get("pair")),
                }
                for v in venues
            ],
            "non_evm_refs": [
                {"dex": v.get("dex"), "pair": v.get("pair"), "ref_type": _p9_ref_type(v.get("dex"), v.get("pair"))}
                for v in venues
                if _p9_ref_type(v.get("dex"), v.get("pair")) != "evm_pair_address"
            ],
        })
    rows.sort(key=lambda row: (-row["gross_spread_pct"], row["pair_key"] or ""))
    return rows

def _p9_load_rpc():
    import sys
    sys.path.insert(0, str((ROOT / "chains" / "polygon-pos").resolve()))
    from polygon_readonly_verifier import RpcPool, load_rpc_endpoints
    endpoints = load_rpc_endpoints(None, str(RPC_POOL))
    return RpcPool(endpoints, 1.0)

def _p9_select_endpoints(pool):
    chain_ok, diagnostics = _p4_discover_chain_endpoints(pool, max_endpoints=18)
    if not chain_ok:
        return [], diagnostics
    probe_addresses = []
    for row in _p9_candidate_rows():
        for venue in row.get("venues", []):
            address = venue.get("pair")
            if venue.get("ref_type") == "evm_pair_address" and _p9_is_evm_address(address):
                probe_addresses.append(address)
                break
        if probe_addresses:
            break
    selected, capability = _p4_select_capable_endpoints(pool, chain_ok, probe_addresses, max_endpoints=2)
    return selected, {"chain": diagnostics, "capability": capability}

def _p9_capability_calls(address):
    return [
        (f"p9:{address}:code", "eth_getCode", [address, "latest"]),
        (f"p9:{address}:token0", "eth_call", [{"to": address, "data": "0x0dfe1681"}, "latest"]),
        (f"p9:{address}:token1", "eth_call", [{"to": address, "data": "0xd21220a7"}, "latest"]),
        (f"p9:{address}:reserves", "eth_call", [{"to": address, "data": "0x0902f1ac"}, "latest"]),
        (f"p9:{address}:slot0", "eth_call", [{"to": address, "data": "0x3850c7bd"}, "latest"]),
        (f"p9:{address}:fee", "eth_call", [{"to": address, "data": "0xddca3f43"}, "latest"]),
        (f"p9:{address}:liquidity", "eth_call", [{"to": address, "data": "0x1a686502"}, "latest"]),
    ]

def _p9_surface_from_rows(address, rows):
    code = rows.get(f"p9:{address}:code", {}).get("result")
    token0 = rows.get(f"p9:{address}:token0", {}).get("result")
    token1 = rows.get(f"p9:{address}:token1", {}).get("result")
    reserves = rows.get(f"p9:{address}:reserves", {}).get("result")
    slot0 = rows.get(f"p9:{address}:slot0", {}).get("result")
    fee = rows.get(f"p9:{address}:fee", {}).get("result")
    liquidity = rows.get(f"p9:{address}:liquidity", {}).get("result")
    return {
        "pair": address,
        "code_present": isinstance(code, str) and code not in {"0x", ""},
        "token_surface": isinstance(token0, str) and isinstance(token1, str) and len(token0) >= 66 and len(token1) >= 66,
        "constant_product_surface": isinstance(reserves, str) and len(reserves) >= 194,
        "cl_surface": isinstance(slot0, str) and len(slot0) >= 130,
        "fee_surface": isinstance(fee, str) and len(fee) >= 66,
        "liquidity_surface": isinstance(liquidity, str) and len(liquidity) >= 66,
        "raw_hashes": {
            "code": sha(code) if code else None,
            "token0": sha(token0) if token0 else None,
            "token1": sha(token1) if token1 else None,
            "reserves": sha(reserves) if reserves else None,
            "slot0": sha(slot0) if slot0 else None,
            "fee": sha(fee) if fee else None,
            "liquidity": sha(liquidity) if liquidity else None,
        },
    }

def _p9_probe_pairs(pool, endpoint_ids, pair_addresses):
    results = {address: [] for address in pair_addresses}
    for endpoint_id in endpoint_ids:
        for start in range(0, len(pair_addresses), P9_PROBE_CHUNK_PAIRS):
            chunk = pair_addresses[start:start + P9_PROBE_CHUNK_PAIRS]
            calls = []
            for address in chunk:
                calls.extend(_p9_capability_calls(address))
            try:
                _, rows = _p4_rpc_batch_endpoint(pool, endpoint_id, calls, timeout=30)
            except Exception as exc:
                rows = {}
                endpoint_error = f"{type(exc).__name__}: {exc}"
                for address in chunk:
                    results[address].append({
                        "endpoint": endpoint_id,
                        "surface": None,
                        "error": endpoint_error,
                        "batch_supported": False,
                    })
                continue
            for address in chunk:
                results[address].append({
                    "endpoint": endpoint_id,
                    "surface": _p9_surface_from_rows(address, rows),
                })
    return results

def _p9_exact_requirements(surface_rows, non_evm_refs=None):
    non_evm_refs = non_evm_refs or []
    if not surface_rows:
        return {
            "status": "BLOCKED_NO_RPC_OBSERVATION",
            "blockers": ["no independent RPC capability observation"],
        }
    valid_rows = [row for row in surface_rows if isinstance(row.get("surface"), dict)]
    unsupported = [row for row in surface_rows if row.get("batch_supported") is False]
    if not valid_rows:
        return {
            "status": "BLOCKED_RPC_BATCH_UNSUPPORTED",
            "blockers": ["no endpoint returned a supported JSON-RPC batch response"],
            "unsupported_endpoints": [row.get("endpoint") for row in unsupported],
        }
    all_same = True
    for key in ("code_present", "token_surface", "constant_product_surface", "cl_surface", "fee_surface", "liquidity_surface"):
        vals = {bool(row["surface"].get(key)) for row in valid_rows}
        all_same = all_same and len(vals) == 1
    if not all_same:
        return {
            "status": "BLOCKED_RPC_DISAGREEMENT",
            "blockers": ["independent RPC surface disagreement"],
        }
    surface = valid_rows[0]["surface"]
    blockers = []
    if non_evm_refs:
        blockers.append("venue-specific non-EVM pool adapter required")
    if not surface["code_present"]:
        blockers.append("pair contract code unavailable")
    if not surface["token_surface"]:
        blockers.append("token0/token1 state unavailable")
    if not (surface["constant_product_surface"] or surface["cl_surface"]):
        blockers.append("no recognized constant-product or concentrated-liquidity state surface")
    if not surface["fee_surface"]:
        blockers.append("exact fee surface unavailable")
    blockers.extend([
        "venue/router exact swap path not yet bound",
        "exact gas/estimateGas evidence not yet bound to executable call",
        "competition/ordering model not yet certified",
        "profit threshold sensitivity not yet certified",
    ])
    return {
        "status": "EXACT_MATH_READY_PENDING_ADAPTER" if not blockers[:1] else "BLOCKED_MISSING_EXACT_INPUTS",
        "blockers": blockers,
        "surfaces": surface,
    }

def p9_economic_closure_ready(snapshot, previous_state):
    checks = snapshot.get("checks", {})
    return (
        checks.get("p8_feature_source_closed") is True
        and checks.get("candidate_universe_complete") is True
        and checks.get("all_capability_batches_complete") is True
        and checks.get("all_candidates_have_explicit_certification_status") is True
        and checks.get("all_processed_pairs_have_two_endpoint_observations") is True
        and snapshot.get("economic_fingerprint")
        and snapshot.get("economic_fingerprint") == previous_state.get("fingerprint")
        and previous_state.get("ledger_complete") is True
        and int(snapshot.get("stable_runs", 0)) >= 1
    )

def task_p9_economics():
    candidates = _p9_candidate_rows()
    progress = load_json(P9_PROGRESS_STATE, {})
    processed = set(str(x).lower() for x in progress.get("processed_pairs", []))
    persisted_observations = progress.get("observations", {}) if isinstance(progress.get("observations", {}), dict) else {}
    selected_candidates = candidates[:]
    all_pairs = sorted({
        str(v.get("pair")).lower()
        for candidate in selected_candidates
        for v in candidate.get("venues", [])
        if v.get("ref_type") == "evm_pair_address"
    })
    remaining = [address for address in all_pairs if address not in processed]

    pool = _p9_load_rpc()
    endpoint_ids, endpoint_diagnostics = _p9_select_endpoints(pool)
    batch_candidates = []
    batch_pairs = []
    for candidate in selected_candidates:
        candidate_pairs = sorted({
            str(v.get("pair")).lower()
            for v in candidate.get("venues", [])
            if isinstance(v.get("pair"), str) and len(v.get("pair")) == 42
            and str(v.get("pair")).lower() in remaining
        })
        if not candidate_pairs:
            continue
        if batch_candidates and len(batch_pairs) + len(candidate_pairs) > P9_BATCH_PAIR_LIMIT:
            break
        batch_candidates.append(candidate)
        batch_pairs.extend(candidate_pairs)
        if len(batch_candidates) >= P9_CANDIDATE_BATCH_GROUPS or len(batch_pairs) >= P9_BATCH_PAIR_LIMIT:
            break

    batch_pairs = sorted(set(batch_pairs))
    observed = _p9_probe_pairs(pool, endpoint_ids, batch_pairs) if endpoint_ids else {}
    merged_observations = dict(persisted_observations)
    for address, rows in observed.items():
        merged_observations[address] = rows

    ledger = []
    for candidate in selected_candidates:
        surfaces = []
        for venue in candidate.get("venues", []):
            address = str(venue.get("pair", "")).lower()
            if address in merged_observations:
                surfaces.extend(merged_observations[address])
        cert = _p9_exact_requirements(surfaces, candidate.get("non_evm_refs", []))
        ledger.append({
            "pair_key": candidate["pair_key"],
            "gross_spread_pct": candidate["gross_spread_pct"],
            "venue_count": candidate["venue_count"],
            "venues": candidate.get("venues", []),
        "non_evm_refs": candidate.get("non_evm_refs", []),
        "exact_certification": cert,
        })

    newly_processed = set(processed)
    newly_processed.update(batch_pairs)
    complete = len(newly_processed) >= len(all_pairs)
    uncertified = sum(1 for row in ledger if row["exact_certification"]["status"] != "EXACT_CERTIFIED")
    exact = len(ledger) - uncertified
    fingerprint = sha({
        "schema": P9_SCHEMA_VERSION,
        "ledger": ledger,
        "candidate_count": len(candidates),
        "processed_pairs": sorted(newly_processed),
    })
    previous_fp = progress.get("fingerprint")
    previous_complete = progress.get("ledger_complete") is True
    stable_runs = int(progress.get("stable_runs", 0) or 0) + 1 if fingerprint == previous_fp and previous_complete else 1

    snapshot = {
        "task": "p9_economic_certification",
        "time": now(),
        "schema": P9_SCHEMA_VERSION,
        "candidate_count": len(candidates),
        "pair_addresses_total": len(all_pairs),
        "non_evm_pool_refs_total": len({
            str(ref.get("pair")) for candidate in selected_candidates for ref in candidate.get("non_evm_refs", [])
        }),
        "processed_pairs_count": len(newly_processed),
        "observations_persisted": len(merged_observations),
        "batch_groups": len(batch_candidates),
        "batch_pair_count": len(batch_pairs),
        "exactly_certified_count": exact,
        "uncertified_count": uncertified,
        "ledger": ledger,
        "economic_fingerprint": fingerprint,
        "stable_runs": stable_runs,
        "ledger_complete": complete,
        "rpc_endpoints": endpoint_ids,
        "rpc_endpoint_diagnostics": endpoint_diagnostics,
        "checks": {
            "p8_feature_source_closed": load_json(EVID / "P8_CLOSURE_STATE.json", {}).get("stage_gate") == "CLOSED",
            "candidate_universe_complete": len(candidates) > 0,
            "all_capability_batches_complete": complete,
            "all_candidates_have_explicit_certification_status": all("exact_certification" in row for row in ledger),
            "all_processed_pairs_have_two_endpoint_observations": all(
                len(merged_observations.get(address, [])) >= 2
                for address in newly_processed
            ),
        },
        "economic_certification_status": "READINESS_CLOSED_NOT_PROFIT_CERTIFIED" if complete else "IN_PROGRESS",
        "evidence_class": "ECONOMIC_CAPABILITY_AUDIT",
        "research_boundary": "P9 closes economic-input/capability coverage for the candidate frontier; it does not certify profitable execution. Exact venue math, gas, fees, slippage, competition, sensitivity and realized-vs-simulated error remain downstream audit requirements.",
    }
    snapshot["stage_gate"] = "CLOSED" if p9_economic_closure_ready(
        snapshot,
        {
            "fingerprint": previous_fp,
            "ledger_complete": previous_complete,
        },
    ) else "OPEN"
    write_json("P9_CLOSURE_STATE.json", {
        "fingerprint": fingerprint,
        "stable_runs": stable_runs,
        "updated_at": snapshot["time"],
        "stage_gate": snapshot["stage_gate"],
        "ledger_complete": complete,
        "candidate_count": len(candidates),
        "pair_addresses_total": len(all_pairs),
        "non_evm_pool_refs_total": len({
            str(ref.get("pair")) for candidate in selected_candidates for ref in candidate.get("non_evm_refs", [])
        }),
        "processed_pairs_count": len(newly_processed),
        "exactly_certified_count": exact,
    })
    P9_PROGRESS_STATE.write_text(json.dumps({
        "schema": P9_SCHEMA_VERSION,
        "fingerprint": fingerprint,
        "processed_pairs": sorted(newly_processed),
        "observations": merged_observations,
        "stable_runs": stable_runs,
        "ledger_complete": complete,
        "updated_at": now(),
    }, sort_keys=True) + "\n", encoding="utf-8")
    return write_json("P9_ECONOMIC_CERTIFICATION.json", snapshot)


def task_p11_closure():
    audit = load_json(EVID / "P10_SATURATION_AUDIT.json", {})
    status = "READY" if audit.get("stage_gate") == "CLOSED" else "LOCKED"
    return write_json("P11_CLOSURE_REPORT.json", {
        "task": "p11_research_closure",
        "time": now(),
        "status": status,
        "polygon_census_lock": status == "READY",
        "next_chain_unlock": status == "READY",
        "economic_residuals": audit.get("residuals", {}),
        "saturation_boundary": "Polygon universe census and audit are closed; exact economic profitability remains an explicitly quantified residual and is not conflated with census completeness.",
        "evidence_class": "CLOSURE_GATE",
    })

P10_SCHEMA_VERSION = "p10-polygon-saturation-audit-v2"

def task_p10_audit():
    conveyor_state = load_json(Path("automation/saturation_state.json"), {})
    p2 = load_json(EVID / "P2_CONTROL_FUNCTION_LATEST.json", {})
    p2p = load_json(EVID / "P2_PROVENANCE_REPLAY.json", {})
    p3 = load_json(EVID / "P3_CLOSURE_STATE.json", {})
    p4 = load_json(EVID / "P4_CLOSURE_STATE.json", {})
    p5 = load_json(EVID / "P5_CLOSURE_STATE.json", {})
    p6 = load_json(EVID / "P6_CLOSURE_STATE.json", {})
    p7 = load_json(EVID / "P7_CLOSURE_STATE.json", {})
    p8 = load_json(EVID / "P8_CLOSURE_STATE.json", {})
    p9 = load_json(EVID / "P9_CLOSURE_STATE.json", {})
    p9_cap = load_json(EVID / "P9_CAPABILITY_STATE.json", {})

    counts = {
        "tokens": len(load_jsonl(UNIV / "tokens.jsonl")),
        "pairs": len(load_jsonl(UNIV / "pairs.jsonl")),
        "p6_routes": int(p6.get("route_count_total", 0) or 0),
        "p7_strategies": int(p7.get("strategy_count", 0) or 0),
        "p8_pair_groups": int(p8.get("pair_groups", 0) or 0),
        "p9_candidate_groups": int(p9.get("candidate_count", 0) or 0),
        "p9_pair_addresses": int(p9.get("pair_addresses_total", 0) or 0),
        "p9_processed_pair_addresses": int(p9.get("processed_pairs_count", 0) or 0),
        "p9_exact_certified": int(p9.get("exactly_certified_count", 0) or 0),
    }
    checks = {
        "p2_closed": conveyor_state.get("research_gate") == "P2_CLOSED" and p2p.get("evidence_state") in {"REPLAYED", None},
        "p3_closed": p3.get("stage_gate") == "CLOSED",
        "p4_closed": p4.get("stage_gate") == "CLOSED",
        "p5_closed": p5.get("stage_gate") == "CLOSED",
        "p6_closed": p6.get("stage_gate") == "CLOSED" and int(p6.get("stable_runs", 0)) >= 2,
        "p7_closed": p7.get("stage_gate") == "CLOSED" and int(p7.get("stable_runs", 0)) >= 2 and int(p7.get("strategy_count", 0)) == 18,
        "p8_closed": p8.get("stage_gate") == "CLOSED" and int(p8.get("stable_runs", 0)) >= 2,
        "p9_readiness_closed": p9.get("stage_gate") == "CLOSED",
        "p9_capability_complete": bool(p9.get("ledger_complete")) and int(p9.get("processed_pairs_count", 0)) >= int(p9.get("pair_addresses_total", 0)),
        "p9_status_explicit": p9.get("economic_certification_status") in {"READINESS_CLOSED_NOT_PROFIT_CERTIFIED", "IN_PROGRESS"},
        "no_live_signing": True,
    }
    residuals = {
        "exact_profit_certification": counts["p9_exact_certified"] < counts["p9_candidate_groups"],
        "economic_adapter_work": max(counts["p9_candidate_groups"] - counts["p9_exact_certified"], 0),
        "non_evm_adapter_required": int(p9.get("non_evm_pool_refs_total", 0) or 0),
    }
    required = [
        "p2_closed", "p3_closed", "p4_closed", "p5_closed", "p6_closed",
        "p7_closed", "p8_closed", "p9_readiness_closed", "p9_capability_complete",
        "p9_status_explicit", "no_live_signing",
    ]
    audit_complete = all(checks[key] for key in required)
    summary = {
        "task": "p10_saturation_audit",
        "time": now(),
        "schema": P10_SCHEMA_VERSION,
        "stage_gate": "CLOSED" if audit_complete else "OPEN",
        "polygon_universe_status": "CENSUS_COMPLETE_FOR_AUDIT" if audit_complete else "AUDIT_INCOMPLETE",
        "checks": checks,
        "counts": counts,
        "residuals": residuals,
        "audit_domains": [
            "independent_source_reconciliation",
            "address_census_reconciliation",
            "pair_pool_census_reconciliation",
            "strategy_coverage",
            "unknown_negative_space_audit",
            "stale_data_audit",
            "economic_viability_audit",
            "security_audit",
            "reproducibility_audit",
        ],
        "economic_boundary": "P9 capability readiness does not equal profit certification; exact economics remain explicitly quantified residual work.",
        "evidence_class": "SATURATION_AUDIT",
    }
    write_json("P10_SATURATION_AUDIT.json", summary)
    return str(EVID / "P10_SATURATION_AUDIT.json")

HANDLERS={"P2_PROVENANCE":task_p2_provenance_replay,"P3":task_p3_protocols,"P4":task_p4_tokens,"P5":task_p5_pairs,"P6":task_p6_routes,"P7":task_p7_strategies,"P8":task_p8_features,"P9":task_p9_economics,"P10":task_p10_audit,"P11":task_p11_closure}

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument("--task",required=True,choices=sorted(HANDLERS)); args=parser.parse_args();
    print(HANDLERS[args.task]())