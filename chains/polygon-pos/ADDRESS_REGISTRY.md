# Polygon PoS Address Registry — Discovery Layer

## Registry purpose

This file is the machine-readable-oriented human registry for execution-relevant Polygon PoS addresses discovered during the infrastructure census.

**Important:** discovery is not verification. Every entry below remains `DOCUMENTED` until live chain-137 evidence proves the exact address, runtime bytecode, proxy/implementation relationship where applicable, creation/deployment evidence, and expected behavior.

## Evidence states

- `DOCUMENTED`: supported by authoritative published source, but not live-verified here.
- `VERIFIED`: live chain-137 evidence and identity/behavior checks completed.
- `PARTIAL`: some live evidence exists, but required verification fields remain.
- `CONFLICTED`: authoritative sources disagree and reconciliation is pending.
- `HISTORICAL`: no longer current but retained for provenance.
- `STALE`: evidence freshness is insufficient for current execution use.
- `DEPRECATED`: explicitly retired.

## Polygon PoS Mainnet (chain 137)

| Object | Address | Domain | State | Primary evidence |
|---|---|---|---|---|
| ChildChainManagerProxy | `0xA6FA4fB5f76172d178d61B04b0ecd319C5d1C0aa` | Polygon | DOCUMENTED | 0xPolygon security scope |
| EIP1559Burn | `0x7A8ed27F4C30512326878652d20fC85727401854` | Polygon | DOCUMENTED | 0xPolygon security scope |
| MaticToken | `0x0000000000000000000000000000000000001010` | Polygon | DOCUMENTED | 0xPolygon security scope |
| WMATIC | `0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270` | Polygon | DOCUMENTED | 0xPolygon security scope |
| StateReceiver | `0x0000000000000000000000000000000000001001` | Polygon | DOCUMENTED | 0xPolygon security scope |
| BorValidatorSet | `0x0000000000000000000000000000000000001000` | Polygon | DOCUMENTED | 0xPolygon security scope |
| ChildChain | `0xD9c7C4ED4B66858301D0cb28Cc88bf655Fe34861` | Polygon | DOCUMENTED | 0xPolygon security scope |
| MaticWeth | `0x8cc8538d60901d19692F5ba22684732Bc28F54A3` | Polygon | DOCUMENTED | 0xPolygon security scope |
| FxChild | `0x8397259c983751DAf40400790063935a11afa28a` | Polygon | DOCUMENTED | 0xPolygon fx-portal |
| sPOLChild | `0xd1CD49A08AeF3Af93457aEc17C786C2b7F48eCd7` | Polygon | DOCUMENTED | 0xPolygon sPOL security scope |

## Ethereum-side control/bridge objects

These addresses are **not chain-137 execution contracts**. They are retained because Polygon PoS bridge/state-sync behavior spans Ethereum and Polygon.

| Object | Address | Domain | State | Primary evidence |
|---|---|---|---|---|
| RootChainManagerProxy | `0xA0c68C638235ee32657e8f720a23ceC1bFc77C77` | Ethereum | DOCUMENTED | 0xPolygon security scope |
| StateSender | `0x28e4F3a7f651294B9564800b2D01f35189A5bFbE` | Ethereum | DOCUMENTED | 0xPolygon security scope |
| ERC20PredicateProxy | `0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf` | Ethereum | DOCUMENTED | Polygon security/PIP evidence |
| ERC721PredicateProxy | `0xE6F45376f64e1F568BD1404C155e5fFD2F80F7AD` | Ethereum | DOCUMENTED | Polygon security/PIP evidence |
| ERC1155PredicateProxy | `0x0B9020d4E32990D67559b1317c7BF0C15D6EB88f` | Ethereum | DOCUMENTED | Polygon security/PIP evidence |
| FxRoot | `0xfe5e5D361b2ad62c541bAb87C45a0B9B018389a2` | Ethereum | DOCUMENTED | 0xPolygon fx-portal |
| sPOL PolBridger | `0x67a40D016EFE809a5BFcd942a8FAf2D9cF0758E2` | Ethereum + Polygon | DOCUMENTED | 0xPolygon sPOL security scope |

## Verification schema

For each registry row, the eventual evidence record must contain:

1. chain ID;
2. exact address;
3. observation block and timestamp;
4. `eth_getCode` result;
5. runtime bytecode hash;
6. proxy detection result;
7. implementation address and implementation bytecode hash when applicable;
8. admin/control/role evidence;
9. creation transaction and creation block where recoverable;
10. verified source/ABI provenance;
11. selector/function probes;
12. event/topic probes;
13. expected-vs-observed identity check;
14. historical implementation changes where relevant;
15. freshness timestamp;
16. evidence hash or reproducible query reference.

## Current limitation

The current research environment cannot execute direct JSON-RPC POST calls. Therefore this registry deliberately contains no fabricated live block, bytecode, implementation, or runtime observations.

## Saturation rule

This registry is not complete until independent discovery sources converge and the remaining bridge/state-sync surface has been enumerated. It must be reconciled before DEX/protocol discovery is treated as the next layer.
