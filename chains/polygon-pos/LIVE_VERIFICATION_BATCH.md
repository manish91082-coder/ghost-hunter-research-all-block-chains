# Polygon PoS Live Verification Batch Specification

## Purpose

Turn the Polygon address discovery registry into a reproducible live-verification batch.

This document is an execution specification for a **read-only verifier**. It does not authorize transactions and does not require private keys.

## Input

Source registry:

`chains/polygon-pos/ADDRESS_REGISTRY.md`

For every candidate record:

- domain/network;
- chain ID;
- address;
- expected object type;
- authoritative discovery source;
- expected proxy/control classification;
- historical/current classification if known.

## Batch A — Network identity

For Polygon candidates, query at minimum:

1. `eth_chainId`
2. `net_version`
3. `eth_blockNumber`
4. `eth_getBlockByNumber("latest", false)`
5. repeated latest-head samples from multiple independent RPC endpoints.

Acceptance:

- chain ID must equal `137`;
- latest block must be internally coherent;
- endpoint head disagreement must be recorded, not hidden.

## Batch B — Address existence and runtime code

For each chain-137 address:

1. `eth_getCode(address, "latest")`
2. capture returned bytecode;
3. compute deterministic runtime-bytecode hash locally;
4. repeat against at least one independent RPC;
5. compare code hashes.

Classification:

- same non-empty code hash across independent RPCs → code-consistent;
- empty code where contract expected → unresolved/mismatch;
- disagreement → CONFLICTED;
- historical address with empty current code → candidate for HISTORICAL/DEPRECATED classification, not automatically invalid.

## P1 completion record — Batch A + Batch B

Run `36169503083` completed the network identity/head and bounded chain-137 runtime-code batches.

- chain ID quorum: VERIFIED;
- head quorum: VERIFIED;
- exact 11-target set: VERIFIED;
- minimum two independent successful code observations per target: VERIFIED;
- code-hash reconciliation: VERIFIED;
- conflicts: none.

Evidence: `chains/polygon-pos/P1_LIVE_VERIFICATION_RUN_30.md`.

The P1 gate is **PASSED** for the bounded critical target set.

## Batch C — Proxy and implementation discovery

For proxy candidates, inspect standard EIP-1967 storage slots where applicable:

- implementation slot;
- admin slot;
- beacon slot.

Also probe:

- `implementation()` where safely callable;
- `admin()` where exposed;
- `owner()`;
- `hasRole(bytes32,address)`;
- `getRoleAdmin(bytes32)`.

Do not assume a proxy standard solely from the word "Proxy" in a contract name.

## Batch D — Identity/function probes

Probe only read-only selectors appropriate to the expected contract:

- `name()`
- `symbol()`
- `decimals()`
- `owner()`
- `paused()`
- `totalSupply()`
- contract-specific getters;
- role membership;
- bridge mappings;
- root/child manager references;
- checkpoint configuration;
- exit-period configuration;
- validator/control references.

Expected selector sets must be stored by object type.

## Batch E — Event probes

Use `eth_getLogs` with narrowly bounded block ranges.

Capture:

- block number;
- transaction hash;
- log index;
- address;
- topic0..topicN;
- decoded event when ABI is authoritative.

Do not use unbounded historical scans against public RPCs.

## Batch F — Creation/deployment evidence

Where recoverable:

- creation transaction;
- creation block;
- deployer/creator;
- implementation deployment;
- proxy deployment;
- initialization transaction.

Explorer data is supporting evidence. On-chain transaction/receipt evidence is preferred.

## Batch G — Control-plane verification

For every upgradeable/control-sensitive contract record:

- proxy admin;
- implementation;
- owner;
- DEFAULT_ADMIN_ROLE;
- MAPPER_ROLE;
- MANAGER_ROLE;
- timelock;
- multisig/control address;
- upgrade path;
- emergency path;
- current observation block.

PIP-54 documents the Protocol Council governance model and legacy control surfaces, but published proposal state is not a substitute for current on-chain role state. The official Polygon security scope also publishes the deployed contract census used as the discovery baseline. [Polygon security scope](https://github.com/0xPolygon/security/blob/main/scope-pos-contracts.md).

## Batch H — Governance freshness and historical classification

For each control-plane object, record two separate dimensions:

- **published governance state**: what authoritative PIP/security documentation says;
- **observed chain state**: what current on-chain storage/roles/proxy slots say.

If they differ, classify the object as CONFLICTED until the difference is explained. A proposal, even a final one, does not prove current runtime ownership.

Also retain historical deployments and legacy contracts because they are needed to explain migration paths, but exclude them from the active execution registry until current relevance is proven.

## Batch I — Cross-RPC consistency

Each critical result should be compared across independent endpoints.

Record:

- endpoint identifier;
- timestamp;
- block number;
- block hash;
- result hash;
- latency;
- error/timeout;
- stale-head indicator.

Minimum critical consistency set:

- chain ID;
- latest block;
- code hash;
- implementation address;
- critical role/control values.

## Batch J — Evidence record

Each verified object should produce a structured record equivalent to:

```text
object_id
network
chain_id
address
state
observation_block
observation_timestamp
rpc_sources[]
code_hash
proxy_type
implementation
implementation_code_hash
admin
owner
roles[]
creation_tx
creation_block
abi_source
function_probes[]
event_probes[]
cross_rpc_agreement
historical_status
unknowns[]
evidence_hash
```

## State transition rules

### VERIFIED

Only when all execution-critical identity fields are sufficiently reconciled and independent RPC observations agree.

### PARTIAL

Identity is strongly supported but one or more non-critical verification fields remain unresolved.

### CONFLICTED

Independent sources or RPC observations disagree on a critical field.

### HISTORICAL

Contract is demonstrably from an earlier deployment/state and is retained for provenance.

### DEPRECATED

Authoritative evidence explicitly identifies the object as retired/replaced.

### UNVERIFIED

Discovery evidence exists but live verification has not completed.

## Safety constraints

- Read-only verification only.
- No private keys.
- No transaction submission.
- No state mutation.
- No live trading.
- No address is promoted to VERIFIED from documentation alone.
- A single RPC is insufficient for critical execution identity.
- A successful `eth_getCode` response alone is insufficient for proxy identity.
- Explorer labels are not accepted as sole proof of current runtime behavior.

## Zero-cost execution design

The batch should run with:

- public/free RPC mesh first;
- asynchronous requests with bounded concurrency;
- local result cache;
- retry with endpoint rotation;
- deterministic request payloads;
- evidence hashes;
- resumable checkpoints.

The verifier must degrade gracefully when an endpoint rate-limits or fails.

## Required output files

The eventual implementation should emit:

- `polygon_address_verification.jsonl`
- `polygon_address_verification_summary.md`
- `polygon_rpc_observations.jsonl`
- `polygon_evidence_manifest.json`

These files should be generated from the same run so the summary cannot drift from raw evidence.

## Gate

The Polygon infrastructure layer can proceed toward DEX discovery only after:

1. registry candidates are reconciled;
2. critical chain-137 addresses have live code evidence;
3. proxy/control relationships are captured;
4. current-vs-historical contracts are classified;
5. cross-RPC consistency is measured;
6. unresolved objects are explicitly listed;
7. no critical identity conflict remains unexplained.

## P2 continuation

Next work:
1. proxy implementation/admin slots where applicable;
2. owner and role/control probes;
3. creation/deployment evidence;
4. contract-specific identity/function probes;
5. bounded event probes;
6. current-vs-historical bridge/predicate classification;
7. cross-RPC reconciliation of control-plane fields.

No DEX discovery is promoted until the remaining P2 infrastructure/address-control surface is sufficiently reconciled.

## P2 execution slice — ERC-1967 storage consistency
The first P2 execution slice reads these standard proxy slots for every bounded critical Polygon target:
- implementation slot;
- admin slot;
- beacon slot.

The slot constants follow ERC-1967. citeturn422867search0

Acceptance:
- chain-137 identity on at least two independent RPC endpoints;
- every target/slot combination observed successfully on at least two independent endpoints;
- identical raw slot results across those independent endpoints;
- no unresolved slot conflicts.

Passing this slice advances P2 only for storage-slot consistency. Proxy implementation semantics, control roles, creation evidence and function/event identity remain separate P2 sub-gates.

## P2 recovery hardening
P2 storage verification now uses request-level adaptive rotation:
- target/slot is the scheduling unit;
- chain-137 identity determines storage eligibility;
- fresh head quorum is checked separately;
- 429/temporary failures trigger endpoint cooldown;
- bounded recovery rounds retry incomplete target/slot pairs;
- two distinct successful endpoint values remain mandatory.

Run #2 showed this is necessary because one endpoint (Tatum) returned a mix of successful responses and HTTP 429 responses within the same 33-probe batch.

## P2 sub-gate completed — ERC-1967 storage consistency

Run `36171378222` closed the first P2 control-plane slice:
- 11 targets × 3 standard storage slots;
- 33 expected combinations;
- 66 successful independent observations;
- reconciliation VERIFIED;
- zero conflicts;
- observation block 94,436,387.

The next P2 slice should focus on the four non-zero derived control addresses first, then extend owner/role/control probes to the full bounded set.
