P4_VERIFY_STATE = EVID / "P4_VERIFICATION_STATE.json"
P4_VERIFY_BATCH_SIZE = 24


def p4_verification_batch(candidates, verification_state, batch_size=P4_VERIFY_BATCH_SIZE):
    """Select only currently unverified/non-matching candidates for bounded progress."""
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


def _p4_rpc_token_verification(candidates, verification_state):
    try:
        import sys
        sys.path.insert(0, str((ROOT / "chains" / "polygon-pos").resolve()))
        from polygon_readonly_verifier import RpcPool, load_rpc_endpoints
    except Exception as exc:
        return {
            "state": verification_state,
            "verified_count": sum(1 for x in verification_state.values() if x.get("matching")),
            "chain_137_verified_count": sum(1 for x in verification_state.values() if x.get("matching")),
            "identity_conflict_count": sum(1 for x in verification_state.values() if x.get("conflict")),
            "error": f"{type(exc).__name__}: {exc}",
            "batch": [],
            "cycle_complete": False,
        }

    if not RPC_POOL.exists():
        return {
            "state": verification_state,
            "verified_count": sum(1 for x in verification_state.values() if x.get("matching")),
            "chain_137_verified_count": sum(1 for x in verification_state.values() if x.get("matching")),
            "identity_conflict_count": sum(1 for x in verification_state.values() if x.get("conflict")),
            "error": "RPC pool file missing",
            "batch": [],
            "cycle_complete": False,
        }

    endpoints = load_rpc_endpoints(None, str(RPC_POOL))
    pool = RpcPool(endpoints, 0.35)
    chain_ok = []

    # Two matching observations are the hard evidence requirement. A third
    # Polygon endpoint is retained only as bounded failover if one provider fails.
    for item in pool.ordered():
        eid = item["id"]
        obs = pool.request(eid, "eth_chainId", [], f"p4:{eid}:chain", 12, 1)
        if obs.get("ok"):
            pool.mark_success(eid)
        else:
            pool.mark_failure(eid, obs)
        result = ((obs.get("body") or {}).get("result") if isinstance(obs.get("body"), dict) else None)
        if str(result).lower() == "0x89":
            chain_ok.append(eid)
        if len(chain_ok) >= 3:
            break

    batch = p4_verification_batch(candidates, verification_state)
    conflicts = 0

    for address in batch:
        observations = []
        errors = []

        def result_of(obs):
            body = obs.get("body")
            return body.get("result") if isinstance(body, dict) else None

        for eid in chain_ok:
            code_obs = pool.request(eid, "eth_getCode", [address, "latest"], f"p4:{eid}:{address}:code", 12, 1)
            dec_obs = pool.request(eid, "eth_call", [{"to": address, "data": "0x313ce567"}, "latest"], f"p4:{eid}:{address}:decimals", 12, 1)
            supply_obs = pool.request(eid, "eth_call", [{"to": address, "data": "0x18160ddd"}, "latest"], f"p4:{eid}:{address}:supply", 12, 1)
            for obs in (code_obs, dec_obs, supply_obs):
                if obs.get("ok"):
                    pool.mark_success(eid)
                else:
                    pool.mark_failure(eid, obs)

            code = result_of(code_obs)
            decimals = result_of(dec_obs)
            total_supply = result_of(supply_obs)

            valid_code = isinstance(code, str) and code not in {"", "0x", "0X"}
            valid_decimals = isinstance(decimals, str) and decimals.startswith("0x")
            valid_supply = isinstance(total_supply, str) and total_supply.startswith("0x")

            if valid_decimals:
                try:
                    valid_decimals = 0 <= int(decimals, 16) <= 255
                except ValueError:
                    valid_decimals = False

            if valid_code and valid_decimals and valid_supply:
                observations.append({
                    "rpc": eid,
                    "code_hash": hashlib.sha256(code.lower().encode()).hexdigest(),
                    "decimals": decimals.lower(),
                    "total_supply": total_supply.lower(),
                })
            else:
                errors.append({
                    "rpc": eid,
                    "code": code,
                    "decimals": decimals,
                    "total_supply": total_supply,
                })

            if len(observations) >= 2:
                break

        if len(observations) >= 2:
            fingerprints = {(x["code_hash"], x["decimals"], x["total_supply"]) for x in observations[:2]}
            matching = len(fingerprints) == 1
            conflict = not matching
            if conflict:
                conflicts += 1
            verification_state[address] = {
                "chain_id": 137,
                "rpc_endpoints": [x["rpc"] for x in observations[:2]],
                "observations": observations[:2],
                "matching": matching,
                "conflict": conflict,
                "last_verified_at": now(),
            }
        else:
            verification_state[address] = {
                "chain_id": 137 if chain_ok else None,
                "rpc_endpoints": [x["rpc"] for x in observations],
                "observations": observations,
                "matching": False,
                "conflict": False,
                "errors": errors[-3:],
                "last_verified_at": now(),
            }

    candidate_set = set(candidates)
    verification_state = {
        address: row
        for address, row in verification_state.items()
        if address in candidate_set
    }

    verified_count = sum(1 for x in verification_state.values() if x.get("matching"))
    conflict_count = sum(1 for x in verification_state.values() if x.get("conflict"))
    cycle_complete = verified_count == len(candidates) and len(candidates) > 0

    save_json(P4_VERIFY_STATE, {
        "universe_fingerprint_context": sha(candidates),
        "updated_at": now(),
        "batch_size": P4_VERIFY_BATCH_SIZE,
        "last_batch": batch,
        "candidate_count": len(candidates),
        "verified_count": verified_count,
        "verification_cycle_complete": cycle_complete,
        "verification": verification_state,
    })

    return {
        "state": verification_state,
        "verified_count": verified_count,
        "chain_137_verified_count": verified_count,
        "identity_conflict_count": conflict_count,
        "error": "" if chain_ok else "No Polygon RPC endpoint returned chainId=137",
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
        url = "https://api.dexscreener.com/tokens/v1/polygon/" + ",".join(batch)
        st_dex, dex_rows, _ = http_json(url, timeout=20)
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

    universe_fingerprint = sha({
        "candidates": candidate_list,
        "provider_overlap": sorted(provider_overlap),
    })

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