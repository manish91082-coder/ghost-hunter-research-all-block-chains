#!/usr/bin/env python3
"""Reconcile P2 parent control-function eth_call evidence without majority selection."""
import json
from pathlib import Path


def load_targets(path):
    targets = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parent, probe_id, calldata, semantic = [part.strip() for part in line.split("|")]
        targets.append(
            {
                "parent": parent,
                "probe_id": probe_id,
                "calldata": calldata.lower(),
                "semantic_candidate": semantic,
            }
        )
    return targets


def load_rows(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def fingerprint(row):
    outcome = row.get("outcome", {})
    # Semantic evidence requires an HTTP 200 response that reached the JSON-RPC
    # execution layer. Provider entitlement errors and malformed-request errors
    # are not contract observations even when wrapped in HTTP 200.
    if outcome.get("http_status") != 200:
        return None
    if outcome.get("ok") is True:
        return ("success", str(outcome.get("result", "")).lower())

    error_code = outcome.get("error_code")
    if error_code is not None:
        try:
            code = int(error_code)
        except (TypeError, ValueError):
            code = None
        # EVM execution/revert responses are semantic; JSON-RPC protocol/request
        # errors and known provider-policy errors are not.
        if code == 3 or (code is not None and -32099 <= code <= -32000):
            return ("error", str(code))
        return None

    return None


def main():
    targets = load_targets("chains/polygon-pos/p2_control_function_targets.txt")
    rows = load_rows("polygon_p2_control_function_observations.jsonl")

    grouped = {}
    for row in rows:
        if row.get("method") != "eth_call":
            continue
        key = (row.get("address"), row.get("probe_id"))
        if key in {(t["parent"], t["probe_id"]) for t in targets}:
            grouped.setdefault(key, {})[row.get("rpc_endpoint_id")] = row

    results = {}
    conflicts = []
    incomplete = []

    for target in targets:
        key = (target["parent"], target["probe_id"])
        endpoint_rows = grouped.get(key, {})
        fps = {
            endpoint: fingerprint(row)
            for endpoint, row in endpoint_rows.items()
            if fingerprint(row) is not None
        }
        unique = set(fps.values())
        matched = len(fps) >= 2 and len(unique) == 1

        results[f"{target['parent']}:{target['probe_id']}"] = {
            "parent": target["parent"],
            "probe_id": target["probe_id"],
            "semantic_candidate": target["semantic_candidate"],
            "selector_calldata": target["calldata"],
            "successful_or_reproducible_rpc_count": len(fps),
            "rpc_endpoints": sorted(fps),
            "fingerprints": fps,
            "matching": matched,
            "raw_outcomes": {
                endpoint: endpoint_rows[endpoint].get("outcome", {})
                for endpoint in sorted(endpoint_rows)
            },
        }

        if len(fps) < 2:
            incomplete.append(
                {
                    "parent": target["parent"],
                    "probe_id": target["probe_id"],
                    "observations": fps,
                }
            )
        elif len(unique) != 1:
            conflicts.append(
                {
                    "parent": target["parent"],
                    "probe_id": target["probe_id"],
                    "observations": fps,
                }
            )

    head = json.loads(
        Path("polygon_p2_control_function_head_summary.json").read_text(encoding="utf-8")
    )
    state = (
        "VERIFIED"
        if not incomplete
        and not conflicts
        and head.get("head_quorum_agreement") is True
        and head.get("chain_ids", {})
        and all(value == 137 for value in head.get("chain_ids", {}).values())
        else "PARTIAL"
        if rows
        else "UNVERIFIED"
    )

    summary = {
        "network": "polygon-pos-mainnet",
        "chain_id": 137,
        "evidence_state": state,
        "probe_count": len(targets),
        "observed_record_count": len(rows),
        "head_quorum_endpoints": head.get("head_quorum_endpoints", []),
        "head_quorum_block_span": head.get("head_quorum_block_span"),
        "rpc_blocks": head.get("rpc_blocks", {}),
        "results": results,
        "conflicts": conflicts,
        "insufficient_independent_observations": incomplete,
        "semantic_interpretation_status": "NOT_INFERRED_FROM_SELECTOR_ALONE",
    }

    Path("polygon_p2_control_function_reconciliation.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if state != "VERIFIED":
        raise SystemExit(f"P2 control-function reconciliation gate not passed: {state}")


if __name__ == "__main__":
    main()
