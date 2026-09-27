# Research Log

## 2026-09-25 — Architecture Research Freeze
### Evidence themes reviewed
- DEX arbitrage and MEV are highly competitive.
- Cross-chain arbitrage can depend heavily on pre-positioned inventory and settlement latency.
- Intent/RFQ/filler systems create opportunity surfaces beyond classic DEX/DEX arbitrage.
- Public/free RPC infrastructure is useful for prototyping but has rate-limit and reliability constraints.
- GitHub rulesets/branch protections can protect the canonical branch.

### Important interpretation
These findings support the architecture direction but do not guarantee profitability or continuous positive PnL.

### Evidence policy
Fresh research should be appended with:
- source
- publication/update date where available
- claim
- relevance
- confidence
- limitations

Detailed evidence packs should be stored under docs/research/ when added.
## 2026-09-27 — Polygon Flash-Loan Profit Research Layer 1
### Sources reviewed
- Aave V3 official flash-loan documentation.
- Aave V3 official overview/liquidation documentation.
- Uniswap official Polygon V3 deployments.
- Uniswap V2 official whitepaper/flash-swap specification.
- QuickSwap current official documentation and Polygon contract registry.
- 0x current official documentation for Polygon routing/aggregation.
- Polygon Labs current network/finality/fee documentation.
- Chainlink flash-loan educational material for use-case taxonomy and attack-surface framing.
- Academic evidence on flash-loan atomicity and DeFi arbitrage/attack economics.
- Income Tax Department current VDA tax documentation for legal/tax boundary awareness.
### Initial verified claims
- Aave flash loans require repayment plus fee within the same transaction; official documentation states the initialized premium is 0.05% and can change by governance, so current production logic must read on-chain state.
- Aave liquidations provide liquidators collateral at a discount/bonus when eligible positions are liquidated; the exact bonus is reserve-specific and on-chain.
- Uniswap V2 documents flash swaps and the atomic make-whole requirement.
- Polygon/Uniswap/QuickSwap provide multiple distinct AMM and routing surfaces on chain 137.
- Polygon infrastructure has materially improved throughput/finality, but low network fees do not eliminate DEX fees, flash premiums, price impact, ordering competition or other execution costs.
- Income Tax Department documentation currently states VDA gains are subject to a 30% rate under the applicable VDA tax regime and provides transaction-level VDA disclosure/TDS mechanisms; exact tax treatment of a specific flash-arbitrage structure remains a professional tax-advice question.
### Important conclusion
The first-principles profit problem is not "how to borrow cheaply"; it is "where does an executable surplus survive every cost and ordering constraint?"
### Research status
Layer 1 = taxonomy + evidence discipline. Next layer = exact venue math and Polygon-specific opportunity conditions.

## 2026-09-27 — Polygon Flash-Loan Profit Research Layer 2
### Exact-economic findings
- Profit must be modeled as NetPnL(Q,S,O), not as a static spread percentage.
- Trade size Q is an optimization variable because AMM output, price impact, fees and flash cost are nonlinear or proportional in different ways.
- V2 constant-product routes can be modeled as sequential state-transition functions; the output of each pool becomes the input of the next.
- Concentrated-liquidity venues require piecewise liquidity/tick-aware math; average spot price is insufficient.
- Split routing is itself an economic optimization problem because nonlinear price impact can make a multi-pool allocation superior to every single-pool route.
- Aave flash premium is a live protocol state variable; the documented 0.05% is initialization evidence and must not be hard-coded as permanent.
- Liquidation profitability depends on current health factor, close factor, liquidation bonus, collateral liquidity and disposal economics, not bonus percentage alone.
- Low Polygon gas reduces one cost component but cannot certify profitability.
### Evidence sources
- Aave official flash-loan and Pool documentation.
- Aave official liquidation documentation.
- Uniswap official Polygon deployment documentation and V2 whitepaper.
- QuickSwap official Polygon contract, pools and flash-swap documentation.
- Balancer official protocol documentation/whitepaper for non-constant-product AMM architecture.
### Layer-2 conclusion
The fundamental object is a profit surface P(Q,S,O). The next layer must map this mathematics venue-by-venue on Polygon, preserving protocol-specific fee, callback, liquidity and settlement rules.
