# Polygon PoS Bridge and State-Sync Surface

## Scope

This document isolates bridge/state-sync infrastructure from ordinary DEX liquidity. The goal is to model every economically relevant cross-domain state surface before Polygon saturation is declared.

Polygon's official repositories describe the PoS architecture as an Ethereum root chain plus Polygon child chain. The state-sync mechanism includes a root-side sender and a child-side receiver; the Fx Portal repository describes Fx Portal as an implementation of Polygon's state-sync mechanism.

## Core state-sync path

Conceptual flow:

`Ethereum StateSender`
→ validator/state-sync relay
→ `Polygon StateReceiver`
→ target child contract `onStateReceive()`
→ child-chain state transition

This path is a state-transition surface, not automatically an arbitrage venue.

## Primary documented surfaces

| Surface | Address | Domain | Current state | Research role |
|---|---|---|---|---|
| StateSender | `0x28e4F3a7f651294B9564800b2D01f35189A5bFbE` | Ethereum | DOCUMENTED | Root state-sync emission |
| StateReceiver | `0x0000000000000000000000000000000000001001` | Polygon | DOCUMENTED | Child state-sync reception |
| ChildChainManagerProxy | `0xA6FA4fB5f76172d178d61B04b0ecd319C5d1C0aa` | Polygon | DOCUMENTED | PoS token/bridge management |
| RootChainManagerProxy | `0xA0c68C638235ee32657e8f720a23ceC1bFc77C77` | Ethereum | DOCUMENTED | Root bridge coordination |
| FxRoot | `0xfe5e5D361b2ad62c541bAb87C45a0B9B018389a2` | Ethereum | DOCUMENTED | Fx Portal root |
| FxChild | `0x8397259c983751DAf40400790063935a11afa28a` | Polygon | DOCUMENTED | Fx Portal child |
| ERC20PredicateProxy | `0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf` | Ethereum | DOCUMENTED | ERC-20 bridge predicate |
| ERC721PredicateProxy | `0xE6F45376f64e1F568BD1404C155e5fFD2F80F7AD` | Ethereum | DOCUMENTED | ERC-721 bridge predicate |
| ERC1155PredicateProxy | `0x0B9020d4E32990D67559b1317c7BF0C15D6EB88f` | Ethereum | DOCUMENTED | ERC-1155 bridge predicate |

## Downstream state-sync consumers

State sync can be consumed by application contracts. The Polygon sPOL repository documents an L2 `sPOLChild` contract and a `PolBridger` used with Polygon PoS state-sync/bridging. These are application-layer consumers, not replacements for the core bridge.

Current documented Polygon sPOLChild:

`0xd1CD49A08AeF3Af93457aEc17C786C2b7F48eCd7`

It remains DOCUMENTED until chain-137 live verification.

## Bridge opportunity surfaces to test later

These are **research hypotheses**, not claims of profitable opportunities:

1. asynchronous token representation/state transitions;
2. delayed liquidity arrival or withdrawal;
3. state-sync timing versus venue price changes;
4. bridge-induced inventory imbalance;
5. cross-domain settlement constraints;
6. application contracts reacting to state-sync messages;
7. retry/failure/replay paths where economically relevant;
8. upgrade/control events that change execution semantics;
9. bridge asset mapping changes;
10. cross-domain opportunities where the total latency and capital constraints still permit positive expected value.

No bridge strategy enters the execution set without exact current state, complete costs, competition analysis and simulation.

## Newly identified predicate/control surfaces

Polygon PIP-54 documents additional Ethereum-side predicate proxies and bridge-control surfaces, including Mintable ERC20/ERC721/ERC1155 predicates, EtherPredicateProxy and ChainExitERC1155Predicate. It also identifies Plasma-era DepositManagerProxy, WithdrawManagerProxy and EventsHubProxy. These are discovery evidence only and require current-vs-historical classification and live verification before any execution use. citeturn0search4

## Remaining census work

The bridge layer is **not saturated**. Required next discovery passes:

- enumerate all current Polygon PoS root/child bridge contracts from authoritative deployments;
- enumerate predicate/manager/exit/withdrawal components and historical replacements;
- enumerate state-sync target consumers that can alter economically relevant state;
- reconcile PoS Portal and Fx Portal surfaces so the two are not conflated;
- capture upgrade/admin/timelock/control relationships;
- capture event signatures and state-transition functions;
- identify deprecated/historical contracts without treating them as live;
- verify every execution-relevant Polygon address on chain 137.

## Verification gate

A bridge/state-sync object becomes VERIFIED only when:

`chain + address + code + runtime hash + proxy/implementation + creation evidence + behavior probes + observation block + source/ABI provenance`

are all sufficiently reconciled.

## Evidence discipline

The authoritative [0xPolygon security scope](https://github.com/0xPolygon/security/blob/main/scope-pos-contracts.md) publishes the core deployed contract addresses. The official [0xPolygon Fx Portal repository](https://github.com/0xPolygon/fx-portal) documents the FxRoot/FxChild deployment surface. These sources establish discovery provenance, not live execution state.

## Current limitation

Direct JSON-RPC POST execution is unavailable in the current research environment. No live bytecode, current state, implementation address or runtime behavior is therefore claimed here.
