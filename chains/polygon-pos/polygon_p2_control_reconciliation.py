#!/usr/bin/env python3
"""Reconcile Polygon P2 ERC-1967 storage evidence without majority selection."""
import json
from pathlib import Path

SLOTS = ("implementation", "admin", "beacon")


def load_rows(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_targets(path):
    return [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def main():
    rows = load_rows("polygon_p2_control_observations.jsonl")
    targets = load_targets("chains/polygon-pos/p2_control_targets.txt")

    by_key = {}
    for row in rows:
        key = (row.get("address"), row.get("slot_name"))
        by_key.setdefault(key, []).append(row)

    summary = {
        "network": "polygon-pos-mainnet",
        "chain_id": 137,
        "target_count": len(targets),
        "slot_count_per_target": len(SLOTS),
        "expected_probe_count": len(targets) * len(SLOTS),
        "observed_successful_probe_count": 0,
        "identity_endpoint_count": 0,
        "targets": {},
        "conflicts": [],
        "insufficient_independent_observations": [],
        "evidence_state": "UNVERIFIED",
        "gate_scope": "eip1967-storage-slot-consistency",
    }

    head_path = Path("polygon_p2_control_head_summary.json")
    if head_path.exists():
        head = json.loads(head_path.read_text(encoding="utf-8"))
        summary["identity_endpoint_count"] = int(head.get("identity_endpoints", 0))
        summary["observation_block"] = head.get("observation_block")
        summary["rpc_blocks"] = head.get("rpc_blocks", {})
        summary["chain_ids"] = head.get("chain_ids", {})

    for address in targets:
        summary["targets"][address] = {}
        for slot_name in SLOTS:
            observations = [
                row for row in by_key.get((address, slot_name), [])
                if row.get("outcome", {}).get("ok") is True
            ]
            summary["observed_successful_probe_count"] += len(observations)
            by_endpoint = {
                row.get("rpc_endpoint_id"): row.get("outcome", {}).get("result")
                for row in observations
                if row.get("rpc_endpoint_id")
            }
            unique_values = set(by_endpoint.values())
            matching = len(by_endpoint) >= 2 and len(unique_values) == 1

            summary["targets"][address][slot_name] = {
                "successful_rpc_count": len(by_endpoint),
                "rpc_endpoints": sorted(by_endpoint),
                "values": by_endpoint,
                "matching": matching,
                "derived_addresses": sorted({
                    row.get("outcome", {}).get("derived_address")
                    for row in observations
                    if row.get("outcome", {}).get("derived_address")
                }),
            }

            if len(by_endpoint) < 2:
                summary["insufficient_independent_observations"].append({
                    "address": address,
                    "slot": slot_name,
                    "observations": by_endpoint,
                })
            elif len(unique_values) != 1:
                summary["conflicts"].append({
                    "address": address,
                    "slot": slot_name,
                    "observations": by_endpoint,
                })

    all_matching = all(
        summary["targets"][address][slot_name]["matching"]
        for address in targets
        for slot_name in SLOTS
    )
    if (
        len(targets) > 0
        and summary["identity_endpoint_count"] >= 2
        and all_matching
        and not summary["conflicts"]
    ):
        summary["evidence_state"] = "VERIFIED"
    elif summary["observed_successful_probe_count"] > 0:
        summary["evidence_state"] = "PARTIAL"

    Path("polygon_p2_control_reconciliation.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if summary["evidence_state"] != "VERIFIED":
        raise SystemExit(
            f"Polygon P2 storage reconciliation gate not passed: {summary['evidence_state']}"
        )


if __name__ == "__main__":
    main()
