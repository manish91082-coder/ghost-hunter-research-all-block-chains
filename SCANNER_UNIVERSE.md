# Scanner Universe

## Initial Target
~150 logical scanners implemented through a shared Scanner Fabric.

## Scanner Families
1. DEX/DEX price dislocation
2. Intra-DEX/pool dislocation
3. Route and triangular arbitrage
4. Cross-chain dislocation
5. Event-driven state-transition
6. Mempool/orderflow
7. Liquidation
8. Intent/RFQ/filler
9. Cross-chain solver/relayer
10. Liquidity imbalance
11. Oracle/state-transition
12. CEX/DEX and derivatives
13. Meta scanners: missed opportunities, scanner disagreement, competitor behavior, dead routes

## Suggested logical allocation
- Data/state integrity: 8–12
- DEX price: 15–20
- Pair/route: 20–30
- Cross-chain: 10–15
- Event-driven: 10–15
- Mempool/orderflow: 8–12
- Liquidation: 8–12
- Intent/RFQ: 8–12
- Solver/relayer: 6–10
- Liquidity/state/oracle: 10–15
- CEX/perps: 8–12
- Meta: 10–15

These are architecture targets, not claims that every detector is currently implemented.

## Scanner Contract
Every scanner emits a normalized opportunity signal. It does not execute transactions.

## Expansion Rule
New scanners must demonstrate a distinct opportunity source, useful incremental coverage, or materially better detection/execution quality. Duplicate scanners that only reproduce the same economic signal should be clustered rather than counted as independent coverage.
