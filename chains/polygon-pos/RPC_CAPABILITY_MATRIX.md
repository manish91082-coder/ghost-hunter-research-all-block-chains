# Polygon PoS RPC Capability Matrix

**Scope:** Polygon PoS Mainnet, chain ID 137
**Purpose:** deterministic capability discovery for the read-only live-verification batch.
**Status:** specification only. No endpoint is execution-trusted until live observations pass the acceptance gates.

## 1. Capability classes

| Class | Methods | Why required | Acceptance |
|---|---|---|---|
| Identity | eth_chainId, net_version, web3_clientVersion | chain/client identity | chain ID 137; coherent response |
| Head | eth_blockNumber, eth_getBlockByNumber | current state anchor | repeated head samples; hash/parent coherent |
| Code | eth_getCode | runtime identity | expected code; cross-RPC hash agreement |
| State | eth_call | roles/proxy/function probes | deterministic response or explicit error |
| Logs | eth_getLogs | deployment/events/state evidence | bounded range succeeds; limits recorded |
| History | block/tx/receipt calls | creation and historical evidence | requested historical object resolvable |
| Gas | eth_gasPrice, eth_feeHistory | cost-model inputs | fresh, valid response |
| Simulation | eth_estimateGas, eth_call | pre-execution certification | deterministic read-only result |
| Trace | trace_call, trace_replayTransaction, etc. | deep execution analysis | optional; requirements recorded |
| WS | eth_subscribe:newHeads, logs | event-driven freshness | optional; reconnect/error behavior measured |

Bor officially documents the Parity-compatible trace namespace and notes that trace methods are disabled by default and require archive-node configuration. Trace support is therefore a measured capability, not a universal RPC assumption. (Official 0xPolygon Bor documentation.)

## 2. Endpoint observation record

Every endpoint gets one immutable observation record:

- endpoint_id
- endpoint_url_hash (never publish credentials)
- timestamp_utc
- chain_id
- client_version
- capability
- method
- latency_ms
- HTTP status
- JSON-RPC error code/message
- result_hash
- observation_block
- stale_head flag
- timeout flag
- retry_count
- rate_limit flag
- historical_state flag
- archive/trace flag
- websocket flag
- notes

## 3. Probe order

1. eth_chainId
2. net_version
3. web3_clientVersion
4. eth_blockNumber
5. eth_getBlockByNumber(latest,false)
6. eth_getCode for a bounded registry sample
7. eth_call identity/control probes
8. bounded eth_getLogs
9. historical block/transaction/receipt probes
10. gas/fee probes
11. optional trace probes
12. optional WebSocket newHeads

**No write method is permitted.**

## 4. Endpoint classification

- **CANDIDATE:** basic identity is coherent.
- **PARTIAL:** useful methods work but required capability is missing.
- **STALE:** head materially lags the freshest coherent head.
- **DEGRADED:** repeated timeout/error/rate-limit behavior.
- **CONFLICTED:** critical identity/code/implementation observations disagree.
- **EXECUTION-TRUSTED:** only after all execution-critical gates pass. Documentation or reputation alone never grants this label.

## 5. Cross-RPC quorum

Compare independent endpoints for:
- chain ID
- latest block number
- latest block hash
- target runtime code hash
- proxy implementation
- critical owner/admin/role state

A disagreement is retained as evidence. The verifier must not silently choose the majority result.

## 6. Historical-state rule

A successful latest-state call does not prove historical availability. Historical probes explicitly record the requested block/tag and endpoint result.

## 7. Zero-cost execution profile

The verifier must support bounded async concurrency, endpoint rotation, exponential backoff, deterministic request IDs, local response cache, resumable checkpoints, append-only JSONL evidence, SHA-256 evidence hashing, and no private keys or transaction submission.

Official Polygon tooling documents standard JSON-RPC probing such as net_version, eth_blockNumber, eth_getBlockByNumber, eth_getBalance, and eth_getCode, supporting this probe-first design. (Official 0xPolygon polygon-cli documentation.)

## 8. Hard safety boundary

The verifier is **read-only** and must reject eth_sendRawTransaction, eth_sendTransaction, signing operations, private-key material, and state-changing contract calls.

The verifier produces evidence. It does not authorize trading.

## 9. Required output artifacts

- polygon_rpc_observations.jsonl
- polygon_address_verification.jsonl
- polygon_address_verification_summary.md
- polygon_evidence_manifest.json
- polygon_verifier_checkpoint.json

## 10. Gate

P1 live-verification passes only when:
1. chain ID is consistently 137;
2. current head is coherent across independent endpoints;
3. execution-critical addresses have live code evidence;
4. proxy/implementation/control state is reconciled;
5. historical/current classifications are explicit;
6. unresolved conflicts are enumerated;
7. evidence is reproducible from recorded requests;
8. no write operation occurred.

Only after this gate can DEX/protocol discovery begin.