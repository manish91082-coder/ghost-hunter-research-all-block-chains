#!/usr/bin/env python3
"""Autonomous Polygon universe evidence worker for P3-P10 plus P2 provenance replay.
stdlib-only; every external snapshot is labeled discovery evidence, never VERIFIED.
"""
import hashlib, json, os, time, urllib.error, urllib.parse, urllib.request
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

    for resource in resources:
        if not isinstance(resource, dict):
            continue
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
            for rel in relationships.values():
                if not isinstance(rel, dict):
                    continue
                rel_data = rel.get("data")
                if isinstance(rel_data, dict):
                    rel_data = [rel_data]
                if isinstance(rel_data, list):
                    for item in rel_data:
                        if isinstance(item, dict):
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
P4_ENDPOINT_SCAN_MAX = 12
P4_CHAIN_RECOVERY_ROUNDS = 2
P4_RECOVERY_WAIT_MAX = 60


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
    except urllib.error.HTTPError:
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
        if len(seeds) >= 2:
            break
    return seeds[:2]


def _p4_endpoint_semantic_probe(pool, endpoint_id, addresses):
    calls = []
    for address in addresses:
        calls.append((f"p4:probe:{endpoint_id}:{address}:code", "eth_getCode", [address, "latest"]))
        calls.append((f"p4:probe:{endpoint_id}:{address}:decimals", "eth_call", [{"to": address, "data": "0x313ce567"}, "latest"]))
        calls.append((f"p4:probe:{endpoint_id}:{address}:supply", "eth_call", [{"to": address, "data": "0x18160ddd"}, "latest"]))

    _, rows = _p4_rpc_batch_endpoint(pool, endpoint_id, calls, timeout=30)
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
    pool = RpcPool(endpoints, 0.35)
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
        calls = []
        for address in batch:
            calls.append((f"p4:{eid}:{address}:code", "eth_getCode", [address, "latest"]))
            calls.append((f"p4:{eid}:{address}:decimals", "eth_call", [{"to": address, "data": "0x313ce567"}, "latest"]))
            calls.append((f"p4:{eid}:{address}:supply", "eth_call", [{"to": address, "data": "0x18160ddd"}, "latest"]))
        try:
            try:
                _, rows = _p4_rpc_batch_endpoint(pool, eid, calls, timeout=30)
            except ValueError as exc:
                rows = _p4_rpc_single_calls(pool, eid, calls, timeout=30)
                if not rows:
                    raise exc
            return eid, True, rows, ""
        except Exception as exc:
            return eid, False, {}, f"{type(exc).__name__}: {exc}"

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

        fingerprints = {(x["code_hash"], x["decimals"], x["total_supply"]) for x in observations}
        matching = len(observations) >= 2 and len(fingerprints) == 1
        conflict = len(observations) >= 2 and len(fingerprints) > 1

        verification_state[address] = {
            "chain_id": 137 if chain_ok else None,
            "rpc_endpoints": [x["rpc"] for x in observations],
            "observations": observations,
            "matching": matching,
            "conflict": conflict,
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


def task_p5_pairs():
    rows=[]; token_file=UNIV/"tokens.jsonl"
    tokens=load_jsonl(token_file)
    cursor_file=EVID/"P5_CURSOR.json"; cursor=0
    if cursor_file.exists(): cursor=int(json.loads(cursor_file.read_text()).get("cursor",0))
    batch=tokens[cursor:cursor+30]
    for t in batch:
        a=t.get("address");
        st,pairs,err=http_json(f"https://api.dexscreener.com/token-pairs/v1/polygon/{a}",timeout=20)
        if st==200 and isinstance(pairs,list):
            for pair in pairs:
                if str(pair.get("chainId","")).lower()=="polygon" and pair.get("pairAddress"):
                    pair["_snapshot_time"]=now(); pair["_source"]="dexscreener_token_pairs"; rows.append(pair)
    pair_path=UNIV/"pairs.jsonl"
    existing_pairs=load_jsonl(pair_path)
    by_address={str(x.get("pairAddress","")).lower():x for x in existing_pairs if x.get("pairAddress")}
    before=len(by_address)
    discovered_tokens={}
    for row in rows:
        address=str(row.get("pairAddress","")).lower()
        if address:
            by_address[address]=row
        for side in ("baseToken","quoteToken"):
            token=(row.get(side) or {}).get("address")
            if token and len(str(token))==42 and str(token).lower().startswith("0x"):
                discovered_tokens[str(token).lower()]={"address":str(token),"source":"dexscreener_pair_token","first_seen":now()}
    merged=list(by_address.values())
    token_path=UNIV/"tokens.jsonl"
    existing_tokens={str(x.get("address","")).lower():x for x in load_jsonl(token_path)}
    tokens_before=len(existing_tokens)
    existing_tokens.update(discovered_tokens)
    token_path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in existing_tokens.values()),encoding="utf-8")
    new_tokens=max(0,len(existing_tokens)-tokens_before)
    pair_path.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in merged),encoding="utf-8")
    cursor=min(len(tokens),cursor+len(batch))
    write_json("P5_CURSOR.json",{"cursor":cursor,"total_tokens":len(tokens)})
    return write_json("P5_PAIR_SNAPSHOT.json",{
        "task":"p5_pair_discovery",
        "time":now(),
        "processed_tokens":len(batch),
        "observed_pair_rows":len(rows),
        "new_unique_pairs":max(0,len(merged)-before),
        "new_unique_tokens":new_tokens,
        "cursor":cursor,
        "total_pair_records":len(merged),
        "evidence_class":"DISCOVERY"
    })

def task_p6_routes():
    pairs=load_jsonl(UNIV/"pairs.jsonl"); adj=defaultdict(list); seen=set()
    for p in pairs:
        b=(p.get("baseToken") or {}).get("address"); q=(p.get("quoteToken") or {}).get("address"); pair=p.get("pairAddress")
        if not b or not q or not pair or b.lower()==q.lower(): continue
        key=(b.lower(),q.lower(),pair.lower());
        if key in seen: continue
        seen.add(key); adj[b.lower()].append((q.lower(),pair)); adj[q.lower()].append((b.lower(),pair))
    routes=[]
    def dfs(start,node,path,used):
        if 2<=len(path)<=4 and node==start: routes.append(list(path)); return
        if len(path)>=4: return
        for nxt,pair in adj.get(node,[])[:100]:
            if pair in used: continue
            if nxt==start and len(path)>=3:
                routes.append(path+[(start,pair)])
                continue
            if nxt in [x[0] for x in path]: continue
            dfs(start,nxt,path+[(nxt,pair)],used|{pair})
    for token in list(adj)[:200]: dfs(token,token,[(token,"")],set())
    return write_json("P6_ROUTE_SNAPSHOT.json",{"task":"p6_route_enumeration","time":now(),"pair_nodes":len(adj),"unique_pairs":len(seen),"route_candidates":routes[:5000],"route_count_sampled":len(routes),"evidence_class":"DERIVED"})

STRATEGIES=["dex_dex","intra_dex","triangular","multi_hop","split","flash_loan","liquidation","backrun","orderflow_mev","intent_rfq_filler","solver_relayer","liquidity_state_transition","cross_domain","statistical_temporal","gas_regime","failed_tx_retry_state","protocol_structural","negative_space_hypothesis"]
def task_p7_strategies():
    routes=json.loads((EVID/"P6_ROUTE_SNAPSHOT.json").read_text()).get("route_count_sampled",0) if (EVID/"P6_ROUTE_SNAPSHOT.json").exists() else 0
    rows=[{"strategy":s,"candidate":True,"route_context_count":routes,"status":"RESEARCH_CANDIDATE"} for s in STRATEGIES]
    return write_json("P7_STRATEGY_MATRIX.json",{"task":"p7_strategy_matrix","time":now(),"strategies":rows,"count":len(rows),"evidence_class":"DERIVED"})

def task_p8_features():
    pairs=load_jsonl(UNIV/"pairs.jsonl"); groups=defaultdict(list)
    for p in pairs:
        b=(p.get("baseToken") or {}).get("address"); q=(p.get("quoteToken") or {}).get("address");
        if not b or not q: continue
        k=":".join(sorted([b.lower(),q.lower()]));
        try: price=float(p.get("priceUsd")) if p.get("priceUsd") not in (None,"") else None
        except: price=None
        liq=((p.get("liquidity") or {}).get("usd")); vol=((p.get("volume") or {}).get("h24"));
        groups[k].append({"dex":p.get("dexId"),"pair":p.get("pairAddress"),"price":price,"liquidity_usd":liq,"volume_24h":vol})
    features=[]
    for k,rows in groups.items():
        prices=[x["price"] for x in rows if isinstance(x["price"],(int,float)) and x["price"]>0]
        spread=(max(prices)/min(prices)-1.0) if len(prices)>=2 else None
        features.append({"pair_key":k,"venue_count":len(rows),"price_spread":spread,"venues":rows})
    return write_json("P8_FEATURE_SNAPSHOT.json",{"task":"p8_features","time":now(),"pair_groups":len(groups),"features":features[:5000],"evidence_class":"DERIVED"})

def task_p9_economics():
    data=json.loads((EVID/"P8_FEATURE_SNAPSHOT.json").read_text()).get("features",[]) if (EVID/"P8_FEATURE_SNAPSHOT.json").exists() else []
    candidates=[{"pair_key":x["pair_key"],"gross_spread_pct":round(x["price_spread"]*100,6) if x.get("price_spread") is not None else None,"status":"NOT_EXACTLY_CERTIFIED","reason":"Requires venue-specific swap math, gas, fees, slippage, competition and fresh-state simulation"} for x in data if x.get("price_spread") is not None]
    return write_json("P9_ECONOMIC_SCREEN.json",{"task":"p9_economic_screen","time":now(),"candidates":candidates[:5000],"evidence_class":"SCREENING_ONLY"})

def task_p11_closure():
    audit_path=EVID/"P10_SATURATION_AUDIT.json"
    audit=json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else {}
    return write_json("P11_CLOSURE_REPORT.json",{
        "task":"p11_research_closure",
        "time":now(),
        "status":"LOCKED" if audit.get("stage_gate")!="CLOSED" else "READY",
        "next_chain_unlock": audit.get("stage_gate")=="CLOSED",
        "evidence_class":"CLOSURE_GATE"
    })

def task_p10_audit():
    files={p.name:p.stat().st_size for p in EVID.glob("P*.json")}
    summary={"task":"p10_saturation_audit","time":now(),"evidence_files":files,"universe_counts":{"tokens":len(load_jsonl(UNIV/"tokens.jsonl")),"pairs":len(load_jsonl(UNIV/"pairs.jsonl"))},"stage_gate":"OPEN","open_reason":["P2 live control/provenance gates pending","P3-P6 are incremental discovery snapshots","P9 exact simulation not complete"],"evidence_class":"AUDIT"}
    return write_json("P10_SATURATION_AUDIT.json",summary)

HANDLERS={"P2_PROVENANCE":task_p2_provenance_replay,"P3":task_p3_protocols,"P4":task_p4_tokens,"P5":task_p5_pairs,"P6":task_p6_routes,"P7":task_p7_strategies,"P8":task_p8_features,"P9":task_p9_economics,"P10":task_p10_audit,"P11":task_p11_closure}

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument("--task",required=True,choices=sorted(HANDLERS)); args=parser.parse_args();
    print(HANDLERS[args.task]())