# Ethereum Mainnet Chain Profile

Status: CANDIDATE_EVIDENCE_RECORDED
Last researched: 2026-09-26
Live verification: NOT YET RUN
Stage gate: P2 NOT STARTED

## Identity
- Name: Ethereum Mainnet
- Chain ID: 1
- EVM / non-EVM: EVM
- Native asset: ETH
- Block time: 12-second protocol slots; empty slots can occur.
- Finality: Proof-of-Stake checkpoint finality via Casper FFG. Finalization requires supermajority checkpoint voting and a subsequent justified checkpoint.

## Infrastructure
### RPC candidate pool
- Alchemy: advertises a public Ethereum RPC endpoint without an API key and keyed HTTP/WSS endpoints. Candidate only until repository-side live probes verify identity, freshness and method coverage.
- QuickNode: Ethereum HTTP and WSS endpoint infrastructure. Candidate only until repository-side live probes verify identity, freshness and method coverage.
- Ethereum JSON-RPC is standardized through the client interface. Candidate endpoints must be independently tested before evidence promotion.

### Required next RPC gate
1. Probe `eth_chainId` and `eth_blockNumber` across independent endpoints.
2. Require at least two independent chain-ID=1 observations.
3. Measure head-block span and define a deterministic freshness tolerance.
4. Build a capability matrix for `eth_getCode`, `eth_getStorageAt`, `eth_call`, logs, receipts and simulation methods.
5. Rotate endpoints on 429/403/timeouts without weakening quorum.
6. Preserve raw observations and reconciliation fingerprints.

## Market Surface
A 2026-09-26 web snapshot shows Ethereum with approximately $53.5B DeFi TVL, approximately $1.48B 24h DEX volume, approximately $30.7B lending TVL and approximately $19.7B active loans. These are time-sensitive external observations, not the chain's canonical on-chain state.

Current discovery candidates include:
- DEX: Uniswap, Fluid
- Aggregator/routing: 0x Protocol, CoWSwap, KyberSwap, Bebop, 1inch, Velora
- Lending/liquidation: Aave, SparkLend, Morpho, Sky

This is intentionally a candidate list, not a saturation claim. A complete Ethereum DEX/pool census must be constructed from reproducible sources and live verification.

## Flash Liquidity
### Aave V3
Aave documents `flashLoan()` and `flashLoanSimple()` as atomic same-transaction liquidity mechanisms. Its documentation states that the flash-loan premium is governance-configurable and was initialized at 0.05%. The current premium must be queried from live contract state before economic certification.

### Balancer Vault
Balancer documents Vault-level flash loans using consolidated token balances. The loan plus protocol fee must be returned within the same transaction or the operation reverts.

### Uniswap V2
The Uniswap V2 whitepaper documents flash swaps, where assets can be received and used elsewhere before repayment at the end of the transaction.

## Lending / Liquidation
Candidate research surfaces:
- Aave
- SparkLend
- Morpho
- Sky

The exact Ethereum deployment addresses, reserve lists, debt parameters, liquidation incentives, health-factor behavior and liquidation execution surfaces remain to be verified.

## Orderflow / MEV
Ethereum's current architecture includes a public transaction-propagation layer plus private/permissioned orderflow and builder/validator paths associated with MEV and PBS. Exact reachable endpoints, latency, inclusion behavior and privacy characteristics must be measured experimentally.

## Intent / RFQ / Solver
CoW Protocol is a permissionless trading protocol using fair combinatorial batch auctions and should be treated as a first-class research surface. Current Ethereum aggregator data also exposes 0x, KyberSwap, Bebop, 1inch and Velora. Exact RFQ, intent, solver, filler and settlement semantics remain a protocol-by-protocol research task.

## Cross-Chain
Bridge and cross-domain surfaces are not yet promoted. Discovery and live-address verification are pending.

## Gas / Execution
Ethereum uses EIP-1559 fee mechanics with a protocol base fee and priority fee. The base fee is burned. Exact current gas conditions, base fee, priority-fee market and inclusion behavior must be sampled from live headers/orderflow before P9-style economics.

## Strategy Candidates
- Atomic multi-venue DEX arbitrage
- Flash-liquidity-assisted arbitrage
- Liquidation capture
- Aggregator/routing arbitrage
- MEV-aware backrun research
- Intent/RFQ/solver opportunity research

These are research candidates only. No profitability, execution authorization or live-trade readiness is implied.

## Validation State
- Candidate evidence: RECORDED
- Live RPC verification: NOT RUN
- DEX/pool census: NOT RUN
- Route universe: NOT RUN
- Strategy closure: NOT RUN
- Exact economic certification: NOT RUN
- Live execution/canary: BLOCKED

## Evidence
1. EIP-2228: https://eips.ethereum.org/EIPS/eip-2228
2. Ethereum blocks: https://ethereum.org/developers/docs/blocks/
3. Ethereum PoS: https://ethereum.org/developers/docs/consensus-mechanisms/pos/
4. Ethereum JSON-RPC: https://ethereum.org/developers/docs/apis/json-rpc/
5. EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
6. Ethereum MEV: https://ethereum.org/developers/docs/mev
7. Aave V3 Flash Loans: https://www.aave.com/docs/aave-v3/guides/flash-loans
8. Balancer flash loans: https://github.com/balancer/docs-developers/blob/main/resources/flash-loans.md
9. Uniswap V2 whitepaper: https://docs.uniswap.org/whitepaper.pdf
10. DeFiLlama Ethereum chain: https://defillama.com/chain/ethereum
11. DeFiLlama Ethereum DEXs: https://defillama.com/dexs/chain/ethereum
12. DeFiLlama Ethereum DEX aggregators: https://defillama.com/dex-aggregators/chain/ethereum
13. DeFiLlama Ethereum lending: https://investors.defillama.com/protocols/lending/ethereum
14. CoW Protocol docs: https://docs.cow.fi/
15. Alchemy Ethereum RPC: https://www.alchemy.com/rpc/ethereum
16. QuickNode Ethereum endpoints: https://www.quicknode.com/docs/ethereum/endpoints

## Explicit Unknowns / Next Evidence
- Independent Ethereum RPC quorum and method capability
- Current DEX + pool universe
- Complete token universe
- Flash-loan provider set and current fee state
- Exact lending/liquidation address matrix
- Mempool/orderflow/provider accessibility
- Builder/private relay surface
- Bridge/cross-domain universe
- Deterministic route/strategy universe
- Exact state-replay economics and realized-profit boundary

## Saturation Boundary
This profile is a bootstrap research record only. It does not close P2 or any later stage and does not claim Ethereum saturation.
