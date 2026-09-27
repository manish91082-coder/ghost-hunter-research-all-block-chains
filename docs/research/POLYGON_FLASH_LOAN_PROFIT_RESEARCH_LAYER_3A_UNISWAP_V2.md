# Polygon Flash-Loan Profit Research — Layer 3A: Uniswap V2 Economic Machine

Date: 2026-09-27
Chain: Polygon PoS, chain ID 137
Status: ACTIVE RESEARCH / NO EXECUTION / NO CODE

## 1. Verified protocol boundary

Current official Uniswap deployment documentation lists the Polygon Uniswap V2 Factory as `0x9e5A52f57b3038F1B8EeE45F28b3C1967e22799C` and V2 Router02 as `0xedf6066a2b290C185783862C7F4776A2C8077AD1`. These are documented deployment references, not yet current on-chain verification records in this research track. [Official deployment source: Uniswap Developers, accessed 2026-09-27.]

The canonical Uniswap V2 Pair contract exposes `getReserves()`, `swap()`, `skim()`, `sync()`, cumulative price state and the pair token identities. The pair contract's swap invariant applies the 997/1000 input adjustment, equivalent to a 0.3% swap fee in the standard implementation.

## 2. Economic primitive

For input amount x, input reserve R_in, output reserve R_out and standard fee multiplier gamma = 0.997:

amountInWithFee = 997*x

amountOut = (997*x*R_out)/(1000*R_in + 997*x)

This is the protocol/library integer-arithmetic model, not a floating-point approximation.

The inverse calculation is:

amountIn = floor((1000*R_in*amountOut)/(997*(R_out-amountOut))) + 1

The +1 is economically relevant because the on-chain/library implementation rounds upward to ensure sufficient input.

## 3. State transition

Before trade:

R_in, R_out

After an exact input trade:

R_in' = R_in + x
R_out' = R_out - amountOut

The pair then updates reserves from actual token balances.

Therefore the scanner must treat the pair as a state-transition machine, not as a static price oracle.

## 4. The invariant is fee-adjusted

The pair contract checks:

(balance0*1000 - amount0In*3) * (balance1*1000 - amount1In*3)
>= reserve0*reserve1*1000^2

This matters for flash swaps because output can be transferred before the final input is known, provided the post-callback balances satisfy the invariant.

## 5. Flash-swap economic family

A Uniswap V2 pair can optimistically transfer output and invoke the recipient callback when non-empty callback data is supplied.

Economic sequence:

Pair A -> temporary asset -> external venue(s) -> return required asset(s) -> pair invariant check.

The transaction succeeds only if the pair is made whole under its exact invariant.

This is distinct from an Aave-style flash loan. The liquidity source is the AMM pair itself and repayment economics are encoded by the pair invariant.

## 6. Two-venue arbitrage

Let Pool 1 have A/B reserves (A1,B1) and Pool 2 have B/A reserves (B2,A2).

For input Q of A:

B = F1(Q)

A_final = F2(B)

Net pre-fixed-cost surplus:

S(Q) = A_final - Q

The economic candidate requires:

max_Q S(Q) > all fixed and downstream costs.

A displayed reserve-price difference is only a screening signal.

## 7. Necessary first-order condition

For a differentiable approximation, an interior optimum satisfies:

d/dQ [A_final(Q)-Q] = 0.

Equivalently, the marginal A received from the second leg equals one additional unit of A committed to the cycle.

The exact production model must not rely on a symbolic closed form when integer rounding, fee-on-transfer behavior, unusual tokens or protocol-specific mechanics invalidate the assumptions. It should evaluate the actual route function and search Q over the permitted domain.

## 8. No universal 'minimum spread'

For infinitesimal Q, the cycle's marginal exchange rate is determined by both pools and the fee multiplier.

As Q increases:
- the first pool's marginal price moves;
- the second pool's marginal price moves;
- both pools incur price impact;
- integer rounding changes outputs;
- fixed gas does not scale with Q;
- proportional fees do scale with Q.

Therefore the condition is not 'spot spread > 0.3% + 0.3%'.

The correct condition is:

max_Q [F2(F1(Q)) - Q - C_total(Q)] > ProfitFloor.

## 9. Why reserve snapshots are insufficient

A reserve snapshot can become stale before execution.

The candidate must ultimately carry:
- observation block;
- pair addresses;
- token identities;
- reserve values;
- reserve timestamps where relevant;
- fee configuration;
- token transfer behavior;
- expected route;
- expected amount;
- expected output;
- gas estimate;
- execution constraints.

Fresh-state recheck must occur immediately before authorization.

## 10. Token transfer-tax complication

The canonical V2 formula assumes that the amount entering the pair is the amount the pair actually receives.

Fee-on-transfer or rebasing tokens violate that assumption.

Therefore:

quoted amountIn != necessarily pair-observed amountIn.

For such tokens, the standard 997 formula cannot be blindly used as a profitability certificate.

The research classification must therefore distinguish:
- standard ERC20-compatible behavior;
- fee-on-transfer;
- rebasing/balance-changing behavior;
- unknown behavior.

Unknown transfer behavior is a fail-closed blocker for exact profitability.

## 11. Direct pair versus Router02

The V2 Router02 is a routing convenience layer. The Pair contract is the economic enforcement layer.

For exact economic research, the Pair's reserve and invariant behavior is authoritative.

Router quotes can be useful for discovery, but a router quote alone is not execution certification.

## 12. Polygon-specific deployment boundary

The official deployment page currently lists:
- Factory: `0x9e5A52f57b3038F1B8EeE45F28b3C1967e22799C`
- Router02: `0xedf6066a2b290C185783862C7F4776A2C8077AD1`

These addresses must still be live-verified against Polygon chain 137 before being promoted to VERIFIED_ONCHAIN in the research registry.

## 13. Flash-swap versus Aave comparison

Uniswap V2 flash swap:
- liquidity comes from the pair;
- callback is part of pair swap flow;
- repayment is enforced by adjusted-balance invariant;
- liquidity is limited by the pair's reserves;
- fee is embedded in the pair invariant.

Aave flash loan:
- liquidity comes from a lending pool;
- premium is a pool state variable;
- repayment plus premium is explicitly required;
- available liquidity depends on the reserve/pool.

Therefore a future opportunity engine should treat flash-source selection as an optimization dimension.

## 14. Economic failure modes

A candidate can fail despite positive displayed spread because of:
1. stale reserves;
2. another transaction moving either pool first;
3. price impact;
4. insufficient liquidity;
5. token transfer tax;
6. rounding;
7. gas cost;
8. callback/settlement constraints;
9. competition;
10. inclusion failure;
11. changed fee/configuration;
12. insufficient final repayment.

Every one of these belongs in the rejection reason taxonomy.

## 15. Negative-space research

The V2 family is not exhausted by simple A/B cross-venue arbitrage.

Required future searches include:
- V2/V2 triangular cycles;
- V2/V3 cross-family routes;
- V2/weighted-pool routes;
- stablecoin representation dislocations;
- flash-swap-funded liquidation;
- flash-swap-funded collateral restructuring;
- reserve imbalance after large state transitions;
- routing opportunities created by fragmented liquidity;
- protocol-fee-on versus fee-off state;
- unusual ERC20 behavior;
- same-block multi-pair state transitions.

These are hypotheses until evidence proves economic viability.

## 16. Exact-profit certification boundary

Layer 3A does NOT certify a profitable Polygon Uniswap V2 opportunity.

It establishes the exact economic machinery needed for later certification.

Certification requires:
- verified pair identity;
- current reserves;
- exact token behavior;
- current applicable fee;
- exact route simulation;
- current gas/execution cost;
- competition/order-flow assessment;
- deterministic profit guard;
- eventually an on-chain receipt for realized PnL.

Historical or simulated positive output remains theoretical/executable evidence, not realized profit.

## 17. Layer 3A conclusion

The most important result is:

**Uniswap V2 arbitrage is a constrained state-transition optimization problem, not a price-difference lookup.**

The correct unit of research is:

pair state -> route function -> quantity optimization -> complete cost -> fresh-state validation -> execution outcome.

Next Layer 3B:
**QuickSwap V2**, with explicit comparison against Uniswap V2 for fee mechanics, flash-swap behavior, routing/deployment surfaces and economic differences.
