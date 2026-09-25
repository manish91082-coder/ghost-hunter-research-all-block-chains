#!/usr/bin/env python3
"""Reconcile P2 derived-control runtime code evidence without majority selection."""
import json
from pathlib import Path


def load_addresses(path):
    return [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def load_rows(path):
    rows=[]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main():
    targets=load_addresses("chains/polygon-pos/p2_derived_control_targets.txt")
    rows=load_rows("polygon_rpc_observations.jsonl")
    by={}
    for row in rows:
        if row.get("method")!="eth_getCode" or row.get("outcome",{}).get("ok") is not True:
            continue
        address=row.get("address")
        endpoint=row.get("rpc_endpoint_id")
        if address in targets and endpoint:
            by.setdefault(address,{})[endpoint]=row.get("outcome",{}).get("result_hash_sha256")

    target_results={}
    conflicts=[]
    incomplete=[]
    for address in targets:
        obs=by.get(address,{})
        unique=set(obs.values())
        matching=len(obs)>=2 and len(unique)==1
        target_results[address]={
            "successful_rpc_count":len(obs),
            "rpc_endpoints":sorted(obs),
            "hashes":obs,
            "matching":matching,
        }
        if len(obs)<2:
            incomplete.append({"address":address,"observations":obs})
        elif len(unique)!=1:
            conflicts.append({"address":address,"observations":obs})

    head=json.loads(Path("polygon_rpc_head_summary.json").read_text(encoding="utf-8"))
    state="VERIFIED" if (
        len(targets)==4
        and head.get("chain_id_agreement")
        and head.get("head_agreement")
        and not incomplete
        and not conflicts
    ) else "PARTIAL" if rows else "UNVERIFIED"

    summary={
        "evidence_state":state,
        "target_count":len(targets),
        "targets":target_results,
        "conflicts":conflicts,
        "incomplete":incomplete,
        "chain_ids_observed":head.get("chain_ids_observed",{}),
        "rpc_blocks":head.get("rpc_blocks",{}),
        "observation_block":head.get("freshest_observed_block"),
    }
    Path("polygon_p2_derived_reconciliation.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,sort_keys=True))
    if state!="VERIFIED":
        raise SystemExit(f"P2 derived-control gate not passed: {state}")


if __name__=="__main__":
    main()
