#!/usr/bin/env python3
"""Aggregate independent P4 RPC fan-out shards into canonical evidence."""
import json
import importlib.util
from pathlib import Path

ROOT = Path(".")
EVID = ROOT / "automation" / "evidence"
UNIV = ROOT / "automation" / "universe"
SHARDS = EVID / "fanout_shards"


def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reconcile_observations(observations):
    code_hashes = {x.get("code_hash") for x in observations if x.get("code_hash")}
    decimal_values = {
        x.get("decimals") for x in observations
        if x.get("decimals") is not None and x.get("decimals_valid", True)
    }
    supplies = {
        x.get("total_supply") for x in observations
        if x.get("total_supply") is not None and x.get("total_supply_valid", True)
    }

    code_identity_match = len(observations) >= 2 and len(code_hashes) == 1
    decimals_consistent = len(decimal_values) <= 1
    erc20_semantic_seen = len(decimal_values) >= 1
    matching = code_identity_match and decimals_consistent and erc20_semantic_seen
    conflict = len(observations) >= 2 and (
        len(code_hashes) > 1 or len(decimal_values) > 1
    )

    return {
        "matching": matching,
        "conflict": conflict,
        "code_identity_match": code_identity_match,
        "erc20_semantic_seen": erc20_semantic_seen,
        "total_supply_equal": len(supplies) <= 1,
        "semantic_fingerprint_fields": ["code_hash", "decimals"],
        "identity_transport": "runtime_code_plus_optional_erc20_semantics",
    }


def aggregate():
    snapshot_path = EVID / "P4_TOKEN_SNAPSHOT.json"
    verify_path = EVID / "P4_VERIFICATION_STATE.json"
    closure_path = EVID / "P4_CLOSURE_STATE.json"
    snapshot = load_json(snapshot_path, {})
    verify = load_json(verify_path, {})
    current = verify.get("verification", {})

    shard_files = sorted(SHARDS.glob("P4_SHARD_*.json"))
    for shard_file in shard_files:
        shard = load_json(shard_file, {})
        endpoint_id = shard.get("endpoint_id")
        if shard.get("status") != "OK":
            continue
        for item in shard.get("observations", []):
            address = item.get("address")
            obs = item.get("observation")
            if not address or not obs:
                continue
            row = current.setdefault(address, {
                "chain_id": 137,
                "rpc_endpoints": [],
                "observations": [],
                "matching": False,
                "conflict": False,
            })
            by_rpc = {
                str(entry.get("rpc")): entry
                for entry in row.get("observations", [])
                if entry.get("rpc")
            }
            by_rpc[str(endpoint_id)] = obs
            row["observations"] = sorted(by_rpc.values(), key=lambda x: str(x.get("rpc","")))
            row["rpc_endpoints"] = [x.get("rpc") for x in row["observations"]]
            row.update(reconcile_observations(row["observations"]))
            row["chain_id"] = 137
            row["last_verified_at"] = item.get("observed_at")
            row["transport"] = "github_matrix_rpc_fanout"

    candidates = snapshot.get("candidate_addresses") or []
    current = {
        address: current.get(address, {
            "chain_id": 137,
            "rpc_endpoints": [],
            "observations": [],
            "matching": False,
            "conflict": False,
        })
        for address in candidates
    }

    verified = sum(1 for row in current.values() if row.get("matching"))
    conflicts = sum(1 for row in current.values() if row.get("conflict"))
    complete = verified == len(candidates) and bool(candidates)

    verify.update({
        "candidate_count": len(candidates),
        "verified_count": verified,
        "verification_cycle_complete": complete,
        "verification": current,
        "transport": "github_matrix_rpc_fanout",
        "fanout_shard_count": len(shard_files),
        "fanout_shards": [p.name for p in shard_files],
    })
    save_json(verify_path, verify)

    token_path = UNIV / "tokens.jsonl"
    if token_path.exists():
        tokens = {}
        for line in token_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                tokens[str(row.get("address","")).lower()] = row
        for address, row in current.items():
            if row.get("matching") and address in tokens:
                tokens[address]["identity"] = row
                tokens[address]["evidence_class"] = "ONCHAIN_SEMANTIC"
        token_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in tokens.values()),
            encoding="utf-8",
        )

    snapshot["verified_token_count"] = verified
    snapshot["chain_137_verified_count"] = verified
    snapshot["identity_conflict_count"] = conflicts
    snapshot["verification_cycle_complete"] = complete
    snapshot["verified_addresses"] = sorted(
        address for address, row in current.items() if row.get("matching")
    )
    snapshot["fanout_shard_count"] = len(shard_files)
    save_json(snapshot_path, snapshot)

    previous = load_json(closure_path, {})
    fingerprint = snapshot.get("universe_fingerprint")
    if complete and fingerprint and fingerprint == previous.get("fingerprint") and previous.get("verification_cycle_complete"):
        stable_runs = int(previous.get("stable_runs", 0) or 0) + 1
    elif complete:
        stable_runs = 1
    else:
        stable_runs = 0

    worker_spec = importlib.util.spec_from_file_location(
        "polygon_universe_worker", ROOT / "tools" / "polygon_universe_worker.py"
    )
    worker = importlib.util.module_from_spec(worker_spec)
    worker_spec.loader.exec_module(worker)

    stage_gate = "CLOSED" if worker.p4_closure_ready(
        snapshot,
        {
            "fingerprint": previous.get("fingerprint"),
            "stable_runs": stable_runs,
            "verification_cycle_complete": previous.get("verification_cycle_complete", False),
        },
    ) else "OPEN"

    closure = {
        "fingerprint": fingerprint,
        "stable_runs": stable_runs,
        "updated_at": snapshot.get("time"),
        "stage_gate": stage_gate,
        "verification_cycle_complete": complete,
        "candidate_count": len(candidates),
        "verified_token_count": verified,
    }
    save_json(closure_path, closure)
    snapshot["stable_runs"] = stable_runs
    snapshot["stage_gate"] = stage_gate
    save_json(snapshot_path, snapshot)

    state_path = ROOT / "automation" / "saturation_state.json"
    report_path = ROOT / "automation" / "conveyor_report.json"
    state = load_json(state_path, {})
    commit_required = False

    if stage_gate == "CLOSED" and state.get("research_gate") == "P2_CLOSED" and state.get("critical_stage") == "P4":
        state["critical_stage"] = "P5"
        order = ["P2","P3","P4","P5","P6","P7","P8","P9","P10","P11"]
        stages = state.setdefault("stages", {})
        for stage in order:
            entry = stages.setdefault(stage, {})
            if stage == "P11":
                entry["mode"] = "SHADOW"
                entry["status"] = "LOCKED"
            elif order.index(stage) < order.index("P5"):
                entry["status"] = "CLOSED"
            elif stage == "P5":
                entry["mode"] = "CRITICAL"
                entry["status"] = "OPEN"
            else:
                entry["mode"] = "SHADOW"
                entry["status"] = "PREPARE"
        commit_required = True

    state["commit_required"] = False
    save_json(state_path, state)
    save_json(report_path, {
        "time": snapshot.get("time"),
        "critical_stage": state.get("critical_stage","P4"),
        "research_gate": state.get("research_gate","P2_CLOSED"),
        "commit_required": commit_required,
        "p4_stage_gate": stage_gate,
        "p4_candidate_count": len(candidates),
        "p4_verified_token_count": verified,
        "p4_identity_conflict_count": conflicts,
        "p4_verification_cycle_complete": complete,
        "fanout_shard_count": len(shard_files),
    })

    print(json.dumps({
        "stage_gate": stage_gate,
        "verified_token_count": verified,
        "identity_conflict_count": conflicts,
        "verification_cycle_complete": complete,
        "commit_required": commit_required,
        "fanout_shards": len(shard_files),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    aggregate()
