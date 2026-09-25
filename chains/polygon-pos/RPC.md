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

Source: https://docs.polygon.technology/pos/reference/rpc-endpoints

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

The list above is reproduced from Polygon's current RPC reference page. It does **not** establish that every endpoint is unrestricted, healthy, low-latency, archive-capable, trace-capable, or suitable for execution.

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

The execution layer must compare state from independent sources and quarantine conflicting/stale observations.## 2026-09-25 — GitHub-hosted runner RPC access reconnaissance
- Read-only GitHub Actions reconnaissance run `36165023744` tested the existing public candidate set with only `eth_chainId` and `eth_blockNumber`.
- From the GitHub-hosted runner, Tatum (`https://polygon-mainnet.gateway.tatum.io/`) and QuickNode public (`https://rpc-mainnet.matic.quiknode.pro`) both returned chain ID 137 and a block number. The other tested public endpoints returned HTTP 403, HTTP 429, or DNS failure from this runner context.
- A later reconnaissance run `36165547555` added PublicNode Bor and Llama; both remained unusable from the runner. Run `36165720300` added Ankr and BlastAPI; Ankr reported that an API key is required, while BlastAPI returned HTTP 403. Run `36166095405` added NodeFlare public; it returned HTTP 403 from the runner.
- Main verification runs showed QuickNode public can return all 11 target code observations, while anonymous Tatum became HTTP 429-limited during the code phase. Tatum's current documentation states that its Free Plan provides 3 requests/second and that an API key is used for authenticated access. Source: https://docs.tatum.io/docs/plans-limits and https://docs.tatum.io/reference/rpc-polygon
- The verifier now supports an optional `TATUM_API_KEY` environment variable. The GitHub workflow maps the repository secret `TATUM_API_KEY` to that environment variable without storing the key in source or artifacts.
- This evidence does not mark any endpoint EXECUTION-TRUSTED. It only establishes runner-specific reachability and the next evidence-collection path.
