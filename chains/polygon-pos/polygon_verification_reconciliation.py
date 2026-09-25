#!/usr/bin/env python3
"""Reconcile Polygon read-only verifier evidence without selecting a majority."""

import hashlib
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


def main():
    rows = load_jsonl("polygon_rpc_observations.jsonl")
    by_method = {}
    for row in rows:
        by_method.setdefault(row["method"], []).append(row)

    summary = {
        "record_count": len(rows),
        "chain_id": {"values": [], "agreement": False},
        "head": {"values": {}, "agreement": False, "stale_endpoints": []},
        "code": {"targets": {}, "cross_rpc_agreement": {}},
        "evidence_state": "UNVERIFIED",
        "conflicts": [],
    }

    chain_values = {}
    for row in by_method.get("eth_chainId", []):
        if row["outcome"]["ok"]:
            try:
                chain_values[row["rpc_endpoint_id"]] = int(
                    next(
                        r["outcome"]["result_hash_sha256"]
                        for r in [row]
                    ) and int(row["request"]["params"][0], 16)
                )
            except (KeyError, TypeError, ValueError):
                pass

    # The raw result is not retained by the verifier, so chain quorum is
    # represented by the verifier's head-summary artifact when available.
    head_path = Path("polygon_rpc_head_summary.json")
    if head_path.exists():
        head = json.loads(head_path.read_text(encoding="utf-8"))
        chain_values = head.get("chain_ids_observed", chain_values)
        summary["head"]["values"] = head.get("rpc_blocks", {})
        summary["head"]["stale_endpoints"] = head.get("stale_endpoints", [])
        summary["chain_id"]["values"] = sorted(set(chain_values.values()))
        summary["chain_id"]["agreement"] = bool(head.get("chain_id_agreement"))

    code_rows = by_method.get("eth_getCode", [])
    for row in code_rows:
        address = row.get("address")
        endpoint = row.get("rpc_endpoint_id")
        if not address:
            continue
        summary["code"]["targets"].setdefault(address, {})[endpoint] = row["outcome"].get(
            "result_hash_sha256"
        )

    for address, observations in summary["code"]["targets"].items():
        hashes = [v for v in observations.values() if v is not None]
        agreement = len(set(hashes)) == 1 and len(hashes) >= 2
        summary["code"]["cross_rpc_agreement"][address] = agreement
        if hashes and not agreement:
            summary["conflicts"].append({
                "type": "code_hash_disagreement_or_missing",
                "address": address,
                "observations": observations,
            })

    all_code_agree = bool(summary["code"]["cross_rpc_agreement"]) and all(
        summary["code"]["cross_rpc_agreement"].values()
    )
    if summary["chain_id"]["agreement"] and not summary["conflicts"] and all_code_agree:
        summary["evidence_state"] = "VERIFIED"
    elif summary["record_count"]:
        summary["evidence_state"] = "PARTIAL"

    Path("polygon_verification_reconciliation.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
