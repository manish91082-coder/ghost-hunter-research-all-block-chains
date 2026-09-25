# Polygon PoS RPC Evidence

## Evidence date
2026-09-25

## Verified documentation

Polygon's official RPC reference states:

- Network: Polygon
- Parent chain: Ethereum
- Chain ID: 137
- Gas token: POL
- Official documented RPC endpoint: https://polygon.drpc.org
- Official documented WSS endpoint: wss://polygon.drpc.org
- Explorer: https://polygonscan.com
- JSON-RPC methods follow the JSON-RPC standard.
- Polygon documents a public-RPC set and explicitly warns that public RPCs may have rate limits or traffic restrictions.

Source: Polygon Developer Docs, RPC endpoints. citeturn1view0

## Documented public RPC candidates

These are **discovery candidates**, not yet execution-trusted endpoints:

| Provider | Endpoint | Evidence state |
|---|---|---|
| dRPC | https://polygon.drpc.org | DOCUMENTED |
| Tenderly | https://tenderly.rpc.polygon.community | DOCUMENTED |
| Allnodes | https://polygon.publicnode.com | DOCUMENTED |
| Tatum | https://polygon-mainnet.gateway.tatum.io/ | DOCUMENTED |
| Nodies | https://polygon-public.nodies.app/ | DOCUMENTED |
| 1RPC | https://1rpc.io/matic | DOCUMENTED |
| QuickNode | https://rpc-mainnet.matic.quiknode.pro | DOCUMENTED |
| OnFinality | https://polygon.api.onfinality.io/public | DOCUMENTED |
| Spectrum/Simplystaking | https://spectrumnodes.com/ | DOCUMENTED |

The list above is reproduced from Polygon's current RPC reference page. It does **not** establish that every endpoint is unrestricted, healthy, low-latency, archive-capable, trace-capable, or suitable for execution. citeturn1view0

## Required live verification

For every candidate endpoint, the evidence collector must record:

1. DNS/TLS success
2. `eth_chainId`
3. `net_version`
4. `eth_blockNumber`
5. `eth_getBlockByNumber("latest", false)`
6. block hash
7. parent hash
8. timestamp
9. gas fields
10. transaction count
11. repeated head observations
12. latency distribution
13. timeout/error distribution
14. stale-head detection
15. cross-RPC head/hash agreement
16. `eth_getLogs` range behavior
17. WebSocket subscription behavior where available
18. trace/debug support where available
19. rate-limit behavior
20. historical-state availability

## Important evidence limitation

This research turn could verify the official documentation, but it could not directly execute JSON-RPC POST calls from the research environment. Therefore:

- no current block number is claimed here;
- no live RPC health score is claimed here;
- no latency number is claimed here;
- no endpoint is marked EXECUTION-TRUSTED.

Those fields remain **PENDING LIVE COLLECTION**.

## Execution architecture implication

The eventual RPC fabric must use multiple independently observed endpoints.

A single endpoint cannot become the sole source of truth for:

- opportunity discovery,
- fresh-state validation,
- simulation,
- or execution authorization.

The execution layer must compare state from independent sources and quarantine conflicting/stale observations.
