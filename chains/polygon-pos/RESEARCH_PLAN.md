# Polygon Saturation Research Plan

## Scope lock

अगले सभी Next steps केवल **Polygon PoS Mainnet, chain ID 137** पर होंगे।

किसी दूसरे blockchain, chain family या unrelated implementation repository पर काम नहीं किया जाएगा जब तक Polygon saturation gate formally close नहीं होता।

## Phase P0: Repository and evidence lock

- canonical repository identity verify
- branch verify
- project constitution verify
- current HEAD verify
- research file schema verify
- Polygon folder created
- evidence states frozen
- no-fabrication rule active

## Phase P1: Chain ground truth

Collect and independently verify:

- network identity
- chain ID
- native gas token
- latest block
- block/header schema
- gas model
- transaction model
- log/event model
- reorg/finality observations
- Bor/Heimdall architecture
- node/RPC interfaces
- public RPC mesh candidates

Deliverables:

- PROFILE.md
- RPC.md
- SYSTEM_CONTRACTS.md
- BLOCK_AND_FINALITY.md
- raw evidence snapshots

## Phase P2: Address universe

Build an address census with independent discovery:

- official Polygon system contracts
- bridge contracts
- token mappings
- DEX factories
- routers
- quoters
- pool managers
- position managers
- universal routers
- settlement contracts
- lending markets
- flash-loan providers
- liquidation contracts
- MEV/orderflow contracts
- intent/RFQ/solver infrastructure
- aggregators
- infrastructure contracts

Every address must pass on-chain code/creation verification before it enters VERIFIED inventory.

## Phase P3: Protocol / DEX universe

Discover broadly, then verify narrowly:

- constant-product AMMs
- concentrated-liquidity AMMs
- stable-swap AMMs
- hybrid curves
- weighted pools
- RFQ systems
- aggregators
- limit-order systems
- intent systems
- solver/filler systems
- custom exchange/settlement mechanisms
- protocol-specific liquidity surfaces

Output:

DEX_UNIVERSE.md + protocol-specific evidence files.

## Phase P4: Token universe

Construct token registry and risk classes.

Discovery sources must be reconciled. No single explorer list will be treated as exhaustive.

Output:

- token registry
- canonical/wrapped/bridged relationships
- token risk registry
- active token subset
- dormant/unknown subset

## Phase P5: Pool and pair universe

For every verified venue:

- enumerate factories/managers
- enumerate pools
- verify pool bytecode
- read token addresses
- read fee/tick/reserve state
- record creation block
- record last activity
- build pair graph

The pair graph becomes the substrate for route enumeration.

## Phase P6: Route and combination saturation

Enumerate:

- 2-leg
- 3-leg
- N-hop
- triangular
- cyclic
- split-route
- same-venue
- cross-venue
- flash-funded
- liquidation
- backrun
- orderflow/filler
- cross-domain

Do not execute from this graph. It is a candidate universe.

## Phase P7: Strategy saturation

Strategy matrix will include at minimum:

1. DEX/DEX arbitrage
2. intra-DEX arbitrage
3. triangular arbitrage
4. multi-hop
5. split routing
6. flash-loan arbitrage
7. liquidation
8. backrun
9. orderflow/MEV
10. intent/RFQ/filler
11. solver/relayer
12. liquidity/state-transition
13. cross-domain
14. statistical/temporal opportunities
15. gas-regime opportunities
16. failed-transaction/retry-state opportunities
17. protocol-specific structural opportunities
18. non-obvious/hypothesis strategies

For every strategy:

- mechanism
- prerequisites
- exact contracts
- state dependencies
- cost model
- failure modes
- competition model
- simulation method
- historical evidence
- live/shadow evidence
- profitability status
- confidence
- unknowns

## Phase P8: Technical analysis + AI

Technical analysis is treated as a feature generator, not a profit guarantee.

Features may include:

- spread
- volatility
- volume
- liquidity
- imbalance
- regime
- momentum/reversion
- route recurrence
- opportunity persistence
- gas regime
- block activity
- flow toxicity proxies

Prediction stack:

- deterministic rules
- statistical models
- online calibration
- ML ranking
- anomaly detection
- sequence models
- graph models
- LLM research assistant for cold-path discovery

No model may bypass exact state/simulation/profit gates.

## Phase P9: Economic certification

For each strategy/route family:

- exact state replay
- exact swap math
- gas
- flash premium
- fees
- slippage
- transfer taxes
- failure cost
- competition
- min-profit threshold
- sensitivity analysis
- realized-vs-simulated error

A quoted positive number is not a profit proof.

## Phase P10: Saturation audit

Before declaring Polygon saturated:

- independent source reconciliation
- address census reconciliation
- pair/pool census reconciliation
- strategy coverage audit
- unknown/negative-space audit
- stale-data audit
- economic viability audit
- security audit
- reproducibility audit

Only then move to another chain.

## Next contract

हर Next पर:

INSPECT → VERIFY → RESEARCH/IMPLEMENT → TEST → EVIDENCE CAPTURE → UPDATE CANONICAL FILES → COMMIT → MAIN HEAD VERIFY → REPORT

एक Next में जितना सत्यापित और reproducibly complete हो सके उतना ही आगे बढ़ेगा। Unverified bulk data डालकर speed नहीं बढ़ाई जाएगी।
