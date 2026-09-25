# Executor Architecture

## Executor Is Final Judge
A scanner signal never authorizes a trade.

## Mandatory Gates
1. Current block/state verification.
2. RPC quorum or trusted state consistency.
3. Liquidity availability.
4. Exact route quote.
5. Exact fee calculation.
6. Gas estimate.
7. Slippage/price-impact calculation.
8. Flash-loan premium read from current configuration when applicable.
9. Execution probability / competition check.
10. Fresh transaction simulation.
11. Minimum-profit check.
12. Smart-contract profit/repayment guard.
13. Appropriate transaction routing.
14. Receipt verification.

## No-Trade Conditions
- stale state
- conflicting state
- insufficient liquidity
- negative or uncertain expected net
- expired opportunity
- simulation disagreement
- unsafe token behavior
- execution probability below threshold
- unavailable settlement/repayment path

## Post-Execution
Record actual balance deltas and realized net PnL. Never mark a trade profitable from a quote alone.
