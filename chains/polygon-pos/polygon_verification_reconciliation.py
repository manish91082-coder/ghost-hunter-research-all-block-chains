#!/usr/bin/env python3
"""Reconcile Polygon read-only verifier evidence without selecting a majority."""

import json
from pathlib import Path


def load_jsonl(path):
    rows = []
    if not Path(path).exists():
        return rows
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_expected_targets(path="chains/polygon-pos/verification_targets.txt"):
    targets = []
    p = Path(path)
    if not p.exists():
        return targets
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            targets.append(line)
    return list(dict.fromkeys(targets))


def main():
    rows = load_jsonl("polygon_rpc_observations.jsonl")
    expected_targets = load_expected_targets()
    expected_set = set(expected_targets)

    by_method = {}
    for row in rows:
        by_method.setdefault(row.get("method"), []).append(row)

    summary = {
        "record_count": len(rows),
        "expected_target_count": len(expected_targets),
        "observed_target_count": 0,
        "target_set_exact": False,
        "chain_id": {"values": [], "agreement": False},
        "head": {
            "values": {},
            "agreement": False,
            "fresh_endpoint_count": 0,
            "stale_endpoints": [],
        },
        "code": {
            "targets": {},
            "cross_rpc_agreement": {},
            "coverage": {},
        },
        "evidence_state": "UNVERIFIED",
        "conflicts": [],
    }

    head_path = Path("polygon_rpc_head_summary.json")
    if head_path.exists():
        head = json.loads(head_path.read_text(encoding="utf-8"))
        chain_ids = head.get("chain_ids_observed", {})
        summary["chain_id"]["values"] = sorted(set(chain_ids.values()))
        summary["chain_id"]["agreement"] = bool(head.get("chain_id_agreement"))
        summary["head"]["values"] = head.get("rpc_blocks", {})
        summary["head"]["stale_endpoints"] = head.get("stale_endpoints", [])
        summary["head"]["fresh_endpoint_count"] = max(
            0,
            len(summary["head"]["values"]) - len(summary["head"]["stale_endpoints"]),
        )
        fresh = {
            endpoint: block
            for endpoint, block in summary["head"]["values"].items()
            if endpoint not in summary["head"]["stale_endpoints"]
        }
        summary["head"]["agreement"] = bool(head.get("head_agreement")) and len(fresh) >= 2

    code_rows = by_method.get("eth_getCode", [])
    for row in code_rows:
        address = row.get("address")
        endpoint = row.get("rpc_endpoint_id")
        if not address or not endpoint:
            continue
        if row.get("outcome", {}).get("ok") is not True:
            continue
        summary["code"]["targets"].setdefault(address, {})[endpoint] = row["outcome"].get(
            "result_hash_sha256"
        )

    observed_set = set(summary["code"]["targets"])
    summary["observed_target_count"] = len(observed_set)
    summary["target_set_exact"] = observed_set == expected_set

    for address in expected_targets:
        observations = summary["code"]["targets"].get(address, {})
        hashes = [value for value in observations.values() if value]
        unique_hashes = set(hashes)
        agreement = len(unique_hashes) == 1 and len(hashes) >= 2
        summary["code"]["coverage"][address] = {
            "successful_rpc_count": len(hashes),
            "rpc_endpoints": sorted(observations),
            "agreement": agreement,
        }
        summary["code"]["cross_rpc_agreement"][address] = agreement

        if len(hashes) < 2:
            summary["conflicts"].append({
                "type": "insufficient_independent_code_observations",
                "address": address,
                "observations": observations,
            })
        elif len(unique_hashes) != 1:
            summary["conflicts"].append({
                "type": "code_hash_disagreement",
                "address": address,
                "observations": observations,
            })

    all_targets_verified = (
        bool(expected_targets)
        and summary["target_set_exact"]
        and all(summary["code"]["cross_rpc_agreement"].values())
    )
    p1_head_ready = (
        summary["chain_id"]["agreement"]
        and summary["head"]["fresh_endpoint_count"] >= 2
        and summary["head"]["agreement"]
    )

    if p1_head_ready and all_targets_verified and not summary["conflicts"]:
        summary["evidence_state"] = "VERIFIED"
    elif summary["record_count"]:
        summary["evidence_state"] = "PARTIAL"

    Path("polygon_verification_reconciliation.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["evidence_state"] != "VERIFIED":
        raise SystemExit(
            f"Polygon reconciliation gate not passed: {summary['evidence_state']}"
        )


if __name__ == "__main__":
    main()
