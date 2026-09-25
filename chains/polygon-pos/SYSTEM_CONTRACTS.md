# Polygon PoS System and Bridge Contract Census

## Evidence date
2026-09-25

## Classification rule

The addresses below are **documented discovery evidence**, not yet live-RPC VERIFIED records.

A contract becomes VERIFIED in this repository only after:
- chain ID 137 code is observed at the exact address;
- runtime bytecode is captured;
- proxy/implementation relationship is checked where applicable;
- creation/deployment evidence is captured where available;
- expected contract identity/function/event behavior is checked;
- source/ABI evidence is reconciled;
- observation block and timestamp are recorded.

No address in this document should be treated as execution-authorized merely because it appears in documentation.

## Polygon PoS child-chain addresses

| Contract | Address | Evidence source | Current state |
|---|---|---|---|
| ChildChainManagerProxy | 0xA6FA4fB5f76172d178d61B04b0ecd319C5d1C0aa | 0xPolygon security scope + Polygon PIP-54 | PARTIAL / LIVE CODE VERIFIED; PROXY-CONTROL PENDING |
| EIP1559Burn | 0x7A8ed27F4C30512326878652d20fC85727401854 | 0xPolygon security scope + Polygon PIP-54 | PARTIAL / LIVE CODE VERIFIED; PROXY-CONTROL PENDING |
| MaticToken | 0x0000000000000000000000000000000000001010 | 0xPolygon security scope | PARTIAL / LIVE CODE VERIFIED; PROXY-CONTROL PENDING |
| WMATIC | 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270 | 0xPolygon security scope | PARTIAL / LIVE CODE VERIFIED; PROXY-CONTROL PENDING |
| StateReceiver | 0x0000000000000000000000000000000000001001 | 0xPolygon security scope | PARTIAL / LIVE CODE VERIFIED; PROXY-CONTROL PENDING |
| BorValidatorSet | 0x0000000000000000000000000000000000001000 | 0xPolygon security scope | PARTIAL / LIVE CODE VERIFIED; PROXY-CONTROL PENDING |
| ChildChain | 0xD9c7C4ED4B66858301D0cb28Cc88bf655Fe34861 | 0xPolygon security scope | PARTIAL / LIVE CODE VERIFIED; PROXY-CONTROL PENDING |
| MaticWeth | 0x8cc8538d60901d19692F5ba22684732Bc28F54A3 | 0xPolygon security scope | PARTIAL / LIVE CODE VERIFIED; PROXY-CONTROL PENDING |

## Ethereum-side bridge/control addresses relevant to Polygon PoS

These are not Polygon-chain contracts. They are recorded because the Polygon PoS bridge/security model crosses Ethereum and must not be confused with chain-137 execution contracts.

| Contract | Ethereum address | Evidence source | State |
|---|---|---|---|
| RootChainManagerProxy | 0xA0c68C638235ee32657e8f720a23ceC1bFc77C77 | 0xPolygon security scope + PIP-54 | DOCUMENTED |
| StateSender | 0x28e4F3a7f651294B9564800b2D01f35189A5bFbE | 0xPolygon security scope | DOCUMENTED |
| ERC20PredicateProxy | 0x40ec5B33f54e0E8A33A975908C5BA1c14e5BbbDf | Polygon PIP-54 | DOCUMENTED |
| ERC721PredicateProxy | 0xE6F45376f64e1F568BD1404C155e5fFD2F80F7AD | Polygon PIP-54 | DOCUMENTED |
| ERC1155PredicateProxy | 0x0B9020d4E32990D67559b1317c7BF0C15D6EB88f | Polygon PIP-54 | DOCUMENTED |

## FX Portal surface

Polygon's official Fx Portal repository documents:
- FxRoot on Ethereum mainnet: 0xfe5e5D361b2ad62c541bAb87C45a0B9B018389a2
- FxChild on Polygon mainnet: 0x8397259c983751DAf40400790063935a11afa28a

These are recorded as bridge-related discovery evidence and still require chain-137 live verification before entering the execution registry.

## Why bridge contracts matter to Ghost Hunter

Bridge/state-sync contracts are not automatically arbitrage venues. They are economically relevant because they can create:

- cross-domain state transitions;
- token representation changes;
- delayed liquidity arrival;
- asynchronous price/liquidity dislocations;
- bridge-specific settlement constraints;
- state-sync events;
- cross-domain opportunity surfaces.

They must therefore be represented in the Polygon knowledge graph even when they do not belong to the ordinary DEX pair graph.

## Upgradeability and control surface

Polygon documentation and PIP-54 identify proxy contracts and upgrade/control roles. Therefore the research schema must retain:

- proxy address;
- implementation address;
- proxy admin/control;
- role holders;
- upgrade mechanism;
- timelock;
- pause/emergency controls;
- observation block;
- historical implementation versions.

A proxy address alone is insufficient to determine current runtime behavior.

## Next verification action

Build the live address verifier for every candidate:

address -> eth_getCode -> bytecode hash -> proxy detection -> implementation -> ABI/function probes -> event probes -> creation evidence -> observation block -> evidence record.

Until that verifier runs successfully, these addresses remain DOCUMENTED rather than VERIFIED.

## 2026-09-25 — P1 Run #30 live code verification

Run `36169503083` verified the bounded Polygon-side P1 target set at block `94,435,638`.

- 11/11 canonical targets observed;
- at least 2 independent RPC endpoints per target;
- matching normalized runtime-code hashes;
- chain ID 137 quorum across 3 endpoints;
- head quorum across 3 endpoints;
- reconciliation state: VERIFIED.

Full per-address evidence: `chains/polygon-pos/P1_LIVE_VERIFICATION_RUN_30.md`.

Boundary: runtime-code verification does not yet certify proxy implementation, admin/owner/roles, creation evidence, ABI/source identity, selector/event behavior or current-vs-historical classification.

## 2026-09-25 — P2 ERC-1967 storage verification

Run `36171378222` verified implementation/admin/beacon slot consistency for all 11 bounded Polygon-side targets.

The only non-zero standard ERC-1967 values observed were:
- EIP1559Burn implementation `0xae88570eb386a9c902488a6535f0957a46a68765`
- EIP1559Burn admin `0x409834270b6f2591dd6c1e9f351e4194b112da44`
- sPOLChild implementation `0x3c05a871e867fde9a8364fc8d38d97a7d42541c8`
- sPOLChild admin `0xf68a9a2417a10e7d907a28b9876db8ad3dbbab7d`

All four values matched across independent RPC observations. Zero values on other targets are retained as observations only and do not prove absence of non-standard upgradeability.
