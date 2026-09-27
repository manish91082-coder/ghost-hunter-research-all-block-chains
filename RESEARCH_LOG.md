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
