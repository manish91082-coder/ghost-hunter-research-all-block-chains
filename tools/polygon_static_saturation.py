#!/usr/bin/env python3
"""Build the canonical Polygon pre-transaction static hunting layer.

Read-only research/data build. No signing, no broadcast, no execution.
The sealed conveyor artifact remains the immutable source for the 469-token /
2,821-pair market graph. Current source registries are refreshed only for
discovery/census metadata; no profitability claim is produced.
"""
from __future__ import annotations
import argparse, collections, gzip, hashlib, json, shutil, time
from pathlib import Path
from urllib.request import Request, urlopen

CHAIN_ID = 137
REPO = Path(".")
POLY = REPO / "chains" / "polygon-pos"
UNIV = REPO / "automation" / "universe"
EVID = REPO / "automation" / "evidence"
MAX_HOPS = 3

KEEP_FILES = {
    "README.md","PROFILE.md","RPC.md","RPC_CAPABILITY_MATRIX.md","SYSTEM_CONTRACTS.md",
    "BRIDGE_STATE_SYNC.md","STATIC_DATA_REQUIRED.md","POLYGON_SATURATION_V2.json",
    "STATIC_SATURATION_PLAN.md","MASTER_INDEX.json","STATIC_SATURATION_MANIFEST.json",
    "TOKEN_UNIVERSE.jsonl","PAIR_UNIVERSE.jsonl","POOL_UNIVERSE.jsonl",
    "ROUTE_UNIVERSE.jsonl.gz","ROUTE_SAMPLE_5000.jsonl.gz","ROUTE_RULES.json",
    "DEX_UNIVERSE.json","PROTOCOL_UNIVERSE.json","STATIC_CONTRACT_UNIVERSE.json",
    "FLASH_LIQUIDITY_UNIVERSE.json","STRATEGY_UNIVERSE.json","FEATURE_SCHEMA.json",
    "ECONOMIC_FRONTIER.json","UNKNOWN_NEGATIVE_SPACE.json","STATIC_EVIDENCE_MANIFEST.json",
    "rpc_pool.txt",
}

def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_json(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

def fetch_json(url: str, timeout=30):
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "ghost-hunter-static-saturation/1.0"})
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def find_sealed_root(explicit: str | None):
    candidates = [Path(explicit)] if explicit else []
    candidates += [
        Path("/tmp/polygon-sealed/saturation-conveyor-state"),
        Path("/tmp/polygon-closure/saturation-conveyor-state"),
        Path("/tmp/saturation-conveyor-state"),
    ]
    for p in candidates:
        if (p / "universe" / "tokens.jsonl").exists() and (p / "universe" / "pairs.jsonl").exists():
            return p
    raise SystemExit("sealed conveyor artifact not found")

def cleanup_polygon_folder():
    POLY.mkdir(parents=True, exist_ok=True)
    for p in POLY.iterdir():
        if p.name not in KEEP_FILES:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

def load_rows(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def build_routes(pairs, out_path: Path, sample_path: Path):
    addr_to_idx, tokens = {}, []
    def tid(addr):
        if addr not in addr_to_idx:
            addr_to_idx[addr] = len(tokens)
            tokens.append(addr)
        return addr_to_idx[addr]

    seen, records = set(), []
    for p in pairs:
        b = (p.get("baseToken") or {}).get("address")
        q = (p.get("quoteToken") or {}).get("address")
        pa = p.get("pairAddress")
        if not b or not q or not pa or str(b).lower() == str(q).lower():
            continue
        b, q, pa = str(b).lower(), str(q).lower(), str(pa).lower()
        key = (b, q, pa)
        if key in seen:
            continue
        seen.add(key)
        tid(b); tid(q)
        records.append((b, q, pa))

    adj = [[] for _ in tokens]
    for i, (b, q, pa) in enumerate(records):
        u, v = addr_to_idx[b], addr_to_idx[q]
        adj[u].append((v, i, pa))
        adj[v].append((u, i, pa))
    for lst in adj:
        lst.sort(key=lambda x: (x[2], tokens[x[0]]))

    used_pair = [False] * len(records)
    node_path = [0] * (MAX_HOPS + 1)
    pool_path = [0] * MAX_HOPS
    samples, count = [], 0
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(out_path, "wt", encoding="utf-8", compresslevel=6) as gz:
        def dfs(start, node, depth, visited_nodes):
            nonlocal count
            if depth >= MAX_HOPS:
                return
            for nxt, pi, pa in adj[node]:
                if used_pair[pi]:
                    continue
                if nxt == start:
                    if depth >= 2:
                        count += 1
                        rec = {
                            "route_id": f"P137-R{count:06d}",
                            "hop_count": depth + 1,
                            "tokens": [tokens[node_path[i]] for i in range(depth + 1)] + [tokens[start]],
                            "pools": [records[pool_path[i]][2] for i in range(depth)] + [pa],
                            "route_policy": {"max_hops": MAX_HOPS, "no_repeated_pool": True},
                        }
                        gz.write(json.dumps(rec, separators=(",", ":")) + "\n")
                        if len(samples) < 5000:
                            samples.append(rec)
                    continue
                if nxt in visited_nodes:
                    continue
                node_path[depth + 1] = nxt
                pool_path[depth] = pi
                used_pair[pi] = True
                dfs(start, nxt, depth + 1, visited_nodes | {nxt})
                used_pair[pi] = False

        for start in sorted(range(len(tokens)), key=lambda i: tokens[i]):
            node_path[0] = start
            dfs(start, start, 0, {start})

    if count != 617622:
        raise SystemExit(f"route count mismatch: expected 617622, got {count}")
    with gzip.open(sample_path, "wt", encoding="utf-8", compresslevel=6) as gz:
        for rec in samples:
            gz.write(json.dumps(rec, separators=(",", ":")) + "\n")
    return count

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sealed-root")
    args = ap.parse_args()
    POLY.mkdir(parents=True, exist_ok=True)
    UNIV.mkdir(parents=True, exist_ok=True)
    EVID.mkdir(parents=True, exist_ok=True)

    sealed = find_sealed_root(args.sealed_root)
    stokens = load_rows(sealed / "universe" / "tokens.jsonl")
    spairs = load_rows(sealed / "universe" / "pairs.jsonl")
    if len(stokens) != 469 or len({x["address"].lower() for x in stokens}) != 469:
        raise SystemExit("sealed token integrity mismatch")
    if len(spairs) != 2821 or len({x["pairAddress"].lower() for x in spairs}) != 2821:
        raise SystemExit("sealed pair integrity mismatch")

    # Repair project automation universe from sealed exact rows.
    shutil.copy2(sealed / "universe" / "tokens.jsonl", UNIV / "tokens.jsonl")
    shutil.copy2(sealed / "universe" / "pairs.jsonl", UNIV / "pairs.jsonl")

    p3 = read_json(EVID / "P3_PROTOCOL_SNAPSHOT.json")
    p7 = read_json(EVID / "P7_STRATEGY_MATRIX.json")
    p8 = read_json(EVID / "P8_FEATURE_SNAPSHOT.json")
    p9 = read_json(EVID / "P9_ECONOMIC_CERTIFICATION.json")
    saturation = read_json(POLY / "POLYGON_SATURATION_V2.json")

    token_rows = []
    for t in sorted(stokens, key=lambda r: r.get("address", "").lower()):
        ident = t.get("identity") or {}
        token_rows.append({
            "record_type": "polygon_static_token",
            "chain_id": CHAIN_ID,
            "address": str(t.get("address", "")).lower(),
            "source": t.get("source"),
            "first_seen": t.get("first_seen"),
            "evidence_class": t.get("evidence_class"),
            "identity_matching": ident.get("matching"),
            "semantic_conflict": ident.get("conflict"),
            "semantic_fingerprint_fields": ident.get("semantic_fingerprint_fields", []),
            "identity_observations": [
                {"rpc": o.get("rpc"), "code_hash": o.get("code_hash"), "decimals": o.get("decimals")}
                for o in ident.get("observations") or []
            ],
            "dynamic_fields_excluded": ["total_supply","holders","balance","price","liquidity","volume"],
        })
    write_jsonl(POLY / "TOKEN_UNIVERSE.jsonl", token_rows)

    pair_rows, pool_rows = [], []
    dex = collections.defaultdict(lambda: {"pairs": 0, "tokens": set(), "examples": []})
    for p in sorted(spairs, key=lambda r: str(r.get("pairAddress", "")).lower()):
        b, q = p.get("baseToken") or {}, p.get("quoteToken") or {}
        dname, pa = str(p.get("dexId") or "").lower(), str(p.get("pairAddress") or "").lower()
        baddr, qaddr = str(b.get("address") or "").lower(), str(q.get("address") or "").lower()
        pair_rows.append({
            "record_type":"polygon_static_pair","chain_id":CHAIN_ID,"pair_address":pa,
            "dex_namespace":dname,
            "base_token":{"address":baddr,"symbol":b.get("symbol"),"name":b.get("name")},
            "quote_token":{"address":qaddr,"symbol":q.get("symbol"),"name":q.get("name")},
            "pair_created_at":p.get("pairCreatedAt"),"source":p.get("_source"),"snapshot_time":p.get("_snapshot_time"),
            "dynamic_fields_excluded":["priceUsd","liquidity","volume","txns","fdv","marketCap"],
        })
        pool_rows.append({
            "record_type":"polygon_static_pool","chain_id":CHAIN_ID,"pool_ref":pa,
            "pool_identity_kind":"EVM_PAIR_ADDRESS_OBSERVED","venue_namespace":dname,
            "token_refs":[baddr,qaddr],"pair_created_at":p.get("pairCreatedAt"),"source":p.get("_source"),
            "adapter_status":"UNRESOLVED_STATIC_ADAPTER",
            "dynamic_state_required":["reserves_or_slot0","fee","liquidity","gas","router_path"],
        })
        d = dex[dname]; d["pairs"] += 1; d["tokens"].update([baddr,qaddr])
        if len(d["examples"]) < 5: d["examples"].append(pa)
    write_jsonl(POLY / "PAIR_UNIVERSE.jsonl", pair_rows)
    write_jsonl(POLY / "POOL_UNIVERSE.jsonl", pool_rows)

    dex_rows = []
    for name, d in sorted(dex.items()):
        dex_rows.append({
            "record_type":"polygon_static_dex","chain_id":CHAIN_ID,"dex_namespace":name,
            "pair_count":d["pairs"],"token_count":len(d["tokens"]),
            "example_pair_addresses":d["examples"],
            "identity_status":"OBSERVED_NAMESPACE_ONLY","address_registry_status":"REQUIRES_ONCHAIN_BINDING",
            "source":"sealed automation/universe/pairs.jsonl",
        })
    write_json(POLY / "DEX_UNIVERSE.json", {"schema":"polygon-static-dex-v2","count":len(dex_rows),"records":dex_rows})

    protocol_payload = {
        "schema":"polygon-static-protocol-universe-v2","chain_id":CHAIN_ID,
        "observed_dex_namespaces":[x["dex_namespace"] for x in dex_rows],
        "sources":{
            "defillama_protocols":"https://api.llama.fi/protocols",
            "geckoterminal_polygon_dexes":"https://api.geckoterminal.com/api/v2/networks/polygon_pos/dexes",
        },
    }
    try:
        llama = fetch_json(protocol_payload["sources"]["defillama_protocols"])
        protocol_payload["defillama_polygon_protocols"] = [
            x for x in llama if "polygon" in [str(c).lower() for c in (x.get("chains") or [])]
        ]
    except Exception as exc:
        protocol_payload["defillama_polygon_protocols"] = []
        protocol_payload["defillama_error"] = f"{type(exc).__name__}: {exc}"
    try:
        gecko = fetch_json(protocol_payload["sources"]["geckoterminal_polygon_dexes"])
        protocol_payload["geckoterminal_dexes"] = gecko.get("data") if isinstance(gecko, dict) else []
    except Exception as exc:
        protocol_payload["geckoterminal_dexes"] = []
        protocol_payload["geckoterminal_error"] = f"{type(exc).__name__}: {exc}"
    protocol_payload["artifact_census_snapshot"] = {
        "polygon_protocol_count":p3.get("polygon_protocol_count"),
        "polygon_dex_protocol_count":p3.get("polygon_dex_protocol_count"),
        "geckoterminal_dex_count":p3.get("geckoterminal_dex_count"),
        "dex_name_overlap_count":p3.get("dex_name_overlap_count"),
        "universe_fingerprint":p3.get("universe_fingerprint"),
    }
    write_json(POLY / "PROTOCOL_UNIVERSE.json", protocol_payload)

    route_count = build_routes(spairs, POLY/"ROUTE_UNIVERSE.jsonl.gz", POLY/"ROUTE_SAMPLE_5000.jsonl.gz")
    write_json(POLY / "ROUTE_RULES.json", {
        "schema":"polygon-static-route-rules-v1","chain_id":CHAIN_ID,"max_hops":MAX_HOPS,"no_repeated_pool":True,
        "enumerated_surface":"simple cyclic routes of 3 swap edges, including oriented and multi-pool variants exactly as sealed P6",
        "not_included":["split routing","4+ hop routes"],"sealed_route_count":route_count,
    })

    write_json(POLY / "STRATEGY_UNIVERSE.json", {
        "schema":"polygon-static-strategy-universe-v2","source":"automation/evidence/P7_STRATEGY_MATRIX.json",
        "stage_gate":p7.get("stage_gate"),"count":p7.get("count"),
        "route_count_total":(p7.get("route_source") or {}).get("route_count_total"),
        "research_boundary":p7.get("research_boundary"),"strategies":p7.get("strategies"),
    })

    domains = collections.defaultdict(list)
    for rec in p8.get("features") or []:
        for name,val in (rec.get("features") or {}).items():
            if isinstance(val,dict):
                domains[name].append({"status":val.get("status"),"reason":val.get("reason"),"source":val.get("source")})
    write_json(POLY / "FEATURE_SCHEMA.json", {
        "schema":"polygon-static-feature-schema-v2","source":"automation/evidence/P8_FEATURE_SNAPSHOT.json",
        "pair_groups":p8.get("pair_groups"),"feature_fingerprint":p8.get("feature_fingerprint"),
        "domains":[
            {"feature":name,"record_count":len(vals),
             "observed_statuses":sorted({v.get("status") for v in vals if v.get("status")})}
            for name,vals in sorted(domains.items())
        ],
        "dynamic_values_required_from_live_chain":True,
    })

    econ_rows=[]
    for rec in p9.get("ledger") or []:
        cert=rec.get("exact_certification") or {}
        econ_rows.append({
            "pair_key":rec.get("pair_key"),"venue_count":rec.get("venue_count"),"venues":rec.get("venues"),
            "non_evm_refs":rec.get("non_evm_refs") or [],
            "exact_certification_status":cert.get("status"),"blockers":cert.get("blockers") or [],
        })
    write_json(POLY / "ECONOMIC_FRONTIER.json", {
        "schema":"polygon-static-economic-frontier-v2","source":"automation/evidence/P9_ECONOMIC_CERTIFICATION.json",
        "candidate_count":p9.get("candidate_count"),"exactly_certified_count":p9.get("exactly_certified_count"),
        "economic_status":p9.get("economic_certification_status"),"fingerprint":p9.get("economic_fingerprint"),
        "records":econ_rows,"warning":"Candidate frontier only; not a profitability list.",
    })

    uniswap_deployments=saturation.get("uniswap_v4_polygon_deployments") or {}
    aave_contracts={
        "POOL_ADDRESSES_PROVIDER":"0xa97684ead0e402dc232d5a977953df7ecbab3cdb",
        "POOL":"0x794a61358d6845594f94dc1db02a252b5b4814ad",
        "POOL_CONFIGURATOR":"0x8145edddf43f50276641b55bd3ad95944510021e",
        "ORACLE":"0xb023e699f5a33916ea823a16485e259257ca8bd1",
        "ACL_MANAGER":"0xa72636cbca a8f5ff95b2cc47f3cdee83f3294a0b".replace(" ",""),
        "AAVE_PROTOCOL_DATA_PROVIDER":"0x243aa95cac2a25651eda86e80bee66114413c43b",
    }
    balancer_contracts={
        "VAULT":"0xba12222222228d8ba445958a75a0704d566bf2c8",
        "HELPERS":"0x239e55f427d44c3cc793f49bfb507ebe76638a2b",
        "WEIGHTED_POOL_FACTORY_V2":"0x0e39c3d9b2ec765efd9c5c70bb290b1fcd8536e3",
        "STABLE_POOL_FACTORY":"0xca96c4f198d343e251b1a01f3eba061ef3da73c1",
    }
    contract_records=[]
    for role,addr in uniswap_deployments.items():
        contract_records.append({"family":"UNISWAP_V4","role":role,"address":addr.lower(),"status":"DOCUMENTED_STATIC_DEPLOYMENT","source":"https://developers.uniswap.org/docs/protocols/v4/deployments"})
    for role,addr in aave_contracts.items():
        contract_records.append({"family":"AAVE_V3_POLYGON","role":role,"address":addr.lower(),"status":"DOCUMENTED_STATIC_DEPLOYMENT","source":"https://github.com/aave-dao/aave-address-book/blob/main/src/ts/AaveV3Polygon.ts"})
    for role,addr in balancer_contracts.items():
        contract_records.append({"family":"BALANCER_V2_POLYGON","role":role,"address":addr.lower(),"status":"DOCUMENTED_STATIC_DEPLOYMENT","source":"https://github.com/balancer/docs-developers/blob/main/references/valuing-balancer-lp-tokens/deployment-addresses.md"})
    contract_records += [
        {"family":"OBSERVED_DEX_NAMESPACE","role":"POOL_MARKET_ID","address":None,"status":"REQUIRES_ONCHAIN_BINDING",
         "namespace":x["dex_namespace"],"pair_count":x["pair_count"]}
        for x in dex_rows
    ]
    write_json(POLY / "STATIC_CONTRACT_UNIVERSE.json", {"schema":"polygon-static-contract-universe-v2","chain_id":CHAIN_ID,"records":contract_records})

    write_json(POLY / "FLASH_LIQUIDITY_UNIVERSE.json", {
        "schema":"polygon-static-flash-liquidity-v2","chain_id":CHAIN_ID,
        "surfaces":[
            {
                "provider":"AAVE_V3","pool":aave_contracts["POOL"],
                "provider_registry":aave_contracts["POOL_ADDRESSES_PROVIDER"],
                "mechanisms":["flashLoan","flashLoanSimple"],
                "source":"https://www.aave.com/docs/aave-v3/smart-contracts/pool",
                "address_source":"https://github.com/aave-dao/aave-address-book/blob/main/src/ts/AaveV3Polygon.ts",
            },
            {
                "provider":"BALANCER_V2","vault":balancer_contracts["VAULT"],
                "mechanisms":["flashLoan"],
                "source":"https://github.com/balancer/balancer-deployments/blob/master/action-ids/polygon/action-ids.json",
                "address_source":"https://github.com/balancer/docs-developers/blob/main/references/valuing-balancer-lp-tokens/deployment-addresses.md",
            },
            {"provider":"DEX_FLASH_SWAP_SURFACE","status":"EMBEDDED_IN_OBSERVED_PAIR_UNIVERSE","requires":"per-venue adapter/callback verification from live chain"},
        ],
    })

    write_json(POLY / "UNKNOWN_NEGATIVE_SPACE.json", {
        "schema":"polygon-static-unknown-negative-space-v2",
        "explicit_residuals":[
            {"area":"token_semantic_enrichment","status":"PARTIAL","note":"469-token discovery universe persisted; semantic identity evidence is incomplete for part of the universe."},
            {"area":"dex_contract_binding","status":"PARTIAL","note":"67 observed DEX namespaces are saturated at market-discovery level; factory/router/settlement bindings remain explicit live-verification work."},
            {"area":"route_extensions","status":"OPEN","note":"Split routing and 4+ hop routes are separate extensions by sealed route policy."},
            {"area":"dynamic_state","status":"DEFERRED_TO_LIVE","note":"Block, gas, reserves/slot0/ticks, liquidity, fees, price, private orderflow and competition are live inputs."},
            {"area":"economic_profit_certification","status":"NOT_CERTIFIED","note":"420 candidates are retained; 0 are exact-profit-certified."},
        ],
    })

    write_json(POLY / "STATIC_EVIDENCE_MANIFEST.json", {
        "schema":"polygon-static-evidence-manifest-v2","chain_id":CHAIN_ID,
        "sealed_artifact":{"run_id":36250240579,"artifact_id":10908543869,
            "artifact_sha256":"ef5eabb71ee181659bbaeaa1cd2be2fea15642c35fee5b41eca389304306c067",
            "state_artifact_sha256":"ad2505dceb8968c54bc7d0ae23baf44b9f4015d7b86431774c468b92b639ba48"},
        "source_families":["sealed_polygon_conveyor_artifact","DefiLlama_protocol_registry","GeckoTerminal_polygon_dex_registry","Aave_address_book","Balancer_deployment_registry","Uniswap_v4_deployments"],
        "no_profit_claim":True,"live_execution_authorized":False,
    })

    write_json(POLY / "MASTER_INDEX.json", {
        "schema":"polygon-static-master-index-v2","chain_id":CHAIN_ID,
        "purpose":"Pre-transaction static intelligence index for read-only flash-loan/arbitrage hunting.",
        "static_inputs":{
            "tokens":"TOKEN_UNIVERSE.jsonl","pairs":"PAIR_UNIVERSE.jsonl","pools":"POOL_UNIVERSE.jsonl",
            "dexes":"DEX_UNIVERSE.json","protocols":"PROTOCOL_UNIVERSE.json","contracts":"STATIC_CONTRACT_UNIVERSE.json",
            "flash_liquidity":"FLASH_LIQUIDITY_UNIVERSE.json","routes":"ROUTE_UNIVERSE.jsonl.gz","route_rules":"ROUTE_RULES.json",
            "strategies":"STRATEGY_UNIVERSE.json","features":"FEATURE_SCHEMA.json","economic_frontier":"ECONOMIC_FRONTIER.json",
            "unknowns":"UNKNOWN_NEGATIVE_SPACE.json",
        },
        "dynamic_inputs_not_stored_here":[
            "latest_block","gas_and_fee_state","token_balances_and_pool_reserves","v3_v4_ticks_and_liquidity",
            "current_prices_and_spreads","mempool_private_orderflow","execution_gas_estimate","slippage_price_impact",
            "competition_ordering","bridge_lending_and_protocol_health_state",
        ],
        "closure":{
            "sealed_tokens":len(stokens),"sealed_pairs":len(spairs),"enumerated_routes":route_count,
            "observed_dex_namespaces":len(dex_rows),"strategy_families":len(p7.get("strategies") or []),
            "feature_groups":p8.get("pair_groups"),"economic_candidate_groups":p9.get("candidate_count"),
            "exact_profit_certified":p9.get("exactly_certified_count"),
        },
        "status":"STATIC_MARKET_UNIVERSE_READY_WITH_EXPLICIT_RESIDUALS",
    })

    cleanup_polygon_folder()
    (POLY / "STATIC_SATURATION_PLAN.md").write_text(
        "# Polygon Static Saturation Plan\n\n"
        "Goal: complete the pre-transaction static intelligence layer for read-only flash-loan/arbitrage hunting on Polygon PoS (chain 137).\n\n"
        "1. Restore the sealed 469-token / 2,821-pair source and repair automation persistence.\n"
        "2. Materialize token, pair, pool, DEX, protocol, contract and flash-liquidity indexes.\n"
        "3. Enumerate the sealed P6 route surface exactly at max 3 hops with no repeated pool.\n"
        "4. Materialize strategy coverage, feature schema, economic frontier and explicit negative space.\n"
        "5. Validate counts/hashes and freeze this folder as the static input layer.\n"
        "6. Only then add the separate live-state layer for per-block revalidation and exact simulation.\n\n"
        "This is intentionally a single reproducible build, not a long sequential research program.\n",
        encoding="utf-8")
    (POLY / "STATIC_DATA_REQUIRED.md").write_text(
        "# Polygon Pre-Transaction Static Data\n\n"
        "This folder is the canonical static input layer. Static means identity/discovery/schema data stored before a hunting run.\n\n"
        "## Static\n"
        "- token identity and provenance\n- pair/pool identity and creation metadata\n"
        "- DEX/protocol registry records\n- documented contract/deployment addresses\n"
        "- flash-liquidity/lending surfaces\n- route topology and route rules\n"
        "- strategy-family coverage\n- feature schema\n- economic candidate frontier and blockers\n- explicit unknown/negative space register\n\n"
        "## Live dynamic\n"
        "- latest block, gas, fee, reserves/slot0/ticks/liquidity\n- prices, spreads, volume, state transitions\n"
        "- RPC latency/head disagreement\n- mempool/private orderflow and competition\n"
        "- exact gas/estimateGas, slippage and execution ordering\n"
        "- lending health, bridge state and other current protocol state\n\n"
        "No signing or public broadcast is part of this layer.\n",
        encoding="utf-8")
    (POLY / "README.md").write_text(
        "# Polygon PoS Static Hunting Layer\n\n"
        "Canonical chain: Polygon PoS, chain ID 137.\n\n"
        "Read MASTER_INDEX.json first. The machine-readable files here are the pre-transaction static inputs for the flash-loan/arbitrage hunter.\n\n"
        "Dynamic blockchain state is intentionally separate and must be revalidated live before exact simulation. No file here authorizes signing or broadcast.\n",
        encoding="utf-8")

    generated={}
    for p in sorted(POLY.iterdir()):
        if p.is_file():
            generated[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(POLY / "STATIC_SATURATION_MANIFEST.json", {
        "schema":"polygon-static-saturation-manifest-v2","generated_at":now(),"chain_id":CHAIN_ID,
        "sealed_source":{"run_id":36250240579,"artifact_id":10908543869,
            "artifact_sha256":"ef5eabb71ee181659bbaeaa1cd2be2fea15642c35fee5b41eca389304306c067",
            "tokens":469,"pairs":2821,"routes":route_count},
        "counts":{"tokens":len(token_rows),"pairs":len(pair_rows),"pools":len(pool_rows),
            "dex_namespaces":len(dex_rows),"routes":route_count,"strategies":len(p7.get("strategies") or []),
            "feature_groups":p8.get("pair_groups"),"economic_candidates":p9.get("candidate_count"),
            "exact_profit_certified":p9.get("exactly_certified_count")},
        "files":generated,"status":"STATIC_MARKET_UNIVERSE_READY_WITH_EXPLICIT_RESIDUALS",
    })
    print(json.dumps(read_json(POLY/"STATIC_SATURATION_MANIFEST.json"),indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
