# Polygon Flash-Loan Profit Research — Layer 2: Exact Economic Equations

Date: 2026-09-27
Chain: Polygon PoS, chain ID 137
Status: ACTIVE / NO EXECUTION / NO CODE
Purpose: Convert the Layer-1 mechanism taxonomy into exact economic functions that can later be evaluated against verified Polygon state.

## 1. Core economic object

For every candidate, the research object is NetPnL(Q,S,O), where Q is initial flash-funded quantity, S is verified chain/protocol state at the observation block, and O is execution/order-flow conditions.

The decision problem is Q* = argmax_Q NetPnL(Q,S,O), subject to protocol invariants, full flash repayment, executable settlement, allowed slippage/impact bounds, gas and execution costs, and the minimum profit floor.

This means a trade can be profitable at small size and loss-making at large size, or have the reverse pattern when fixed costs dominate. Profitability is therefore trade-size dependent.

## 2. Universal economic decomposition

NetPnL = Value(final assets) - Value(flash principal + premium) - variable execution costs - fixed execution costs - failure/competition costs.

The cost vector remains explicit: flash premium; AMM/venue fees; price impact; token transfer fee/tax; gas; relay/private-orderflow cost where applicable; protocol liquidation fee/haircut; settlement fee; opportunity-specific cost; minimum required surplus.

No cost may disappear into a generic slippage field.

## 3. V2 constant-product route

For a standard constant-product pool with reserves R_in and R_out and input fee fraction f:

amount_after_fee = Q(1-f)

Out(Q) = amount_after_fee * R_out / (R_in + amount_after_fee).

For a multi-pool route, the output of pool 1 becomes the input of pool 2: Q_(i+1)=F_i(Q_i,S_i). Therefore final output is the composition of all route functions.

Uniswap V2 documents the constant-product architecture and flash swaps. QuickSwap documents its V2 flash-swap repayment condition. Protocol-specific fee and repayment rules must be used rather than assuming one universal fee.

## 4. V2 arbitrage condition

For A -> B on Pool 1 -> A on Pool 2:

Profit(Q) = F_2(F_1(Q)) - Q - C_fixed - C_other.

The candidate exists only if max_Q Profit(Q) exceeds the minimum profit floor.

The maximum cannot be inferred from the percentage difference between two displayed spot prices.

Key consequence: the economically relevant signal is marginal executable output after every pool state transition, not the displayed reserve ratio.

## 5. Native flash-swap repayment economics

A Uniswap-V2-style flash swap permits assets to be sent before payment as long as the pair is made whole by transaction end. QuickSwap documentation gives the corresponding repayment condition and shows that same-token repayment under its documented 0.3% model has an effective fee of about 0.3009027% on the withdrawn amount.

Therefore required return is not simply principal plus an arbitrary fee. The exact pair repayment rule must be evaluated.

This creates a distinct family: borrow from pool A -> trade elsewhere -> repay pool A, where the borrowing mechanism itself is a DEX pair.

## 6. Concentrated-liquidity route

For V3/Algebra-style pools, the route function is piecewise over active liquidity ranges.

Conceptually: Out(Q) = F(Q; sqrtPrice, L, tick, fee, initializedTicks).

Active liquidity changes when the swap crosses initialized ticks. Therefore a single average price is insufficient.

The eventual economic model must know current sqrt price, active liquidity, initialized tick boundaries, liquidity changes at boundaries, fee configuration, amount remaining before crossing and output after each crossing.

QuickSwap's Polygon V3 surface is Algebra-based, while Uniswap publishes a separate Polygon V3 deployment set. They must be modeled independently.

## 7. Split-route optimization

Suppose Q can be split: Q = q1 + q2 + ... + qn, with total output O = sum F_i(q_i). Then the optimization is max over q_i of [sum F_i(q_i) - Q - C], subject to q_i >= 0 and sum q_i = Q.

A split such as 60% + 25% + 15% can outperform every single-pool route because price impact is nonlinear.

Therefore route optimization is itself an economic mechanism, not merely an implementation detail.

## 8. Triangular arbitrage

For A -> B -> C -> A:

Q_B = F_1(Q_A), Q_C = F_2(Q_B), Q_A' = F_3(Q_C).

Gross cycle surplus = Q_A' - Q_A.

Net cycle PnL = Q_A' - Q_A - flash cost - gas - other costs.

The cycle is valid only when net PnL exceeds the profit floor. A cycle can exist even when no individual pair presents an obvious two-venue spread.

## 9. Flash premium is a state variable

Aave documentation states that its flash-loan premium was initialized at 0.05% and can be changed by governance, and directs integrators to read the current FLASHLOAN_PREMIUM_TOTAL.

Therefore 0.05% is initialization evidence, not a permanent production constant.

FlashCost(Q) = Q * current_flash_premium(state).

Hard-coding the historical/default value creates false-positive risk.

## 10. Liquidation economics

For a lending liquidation, debt repaid is D and the liquidator receives collateral according to the protocol's current liquidation parameters.

At simplified level: CollateralReceived ≈ D * P_D/P_C * (1+b), where b is the applicable liquidation bonus, subject to protocol rules, close factors, collateral availability, fees and rounding.

Net liquidation PnL = Value(CollateralReceived) - D - FlashCost - Gas - DisposalCost - ProtocolFee - CompetitionCost.

Aave documentation states that positions with health factor below 1 can be liquidated, liquidators repay debt and receive discounted collateral, and the liquidation bonus is reserve-specific and surfaced through on-chain configuration. Its referenced V3 Pool implementation documents a 50% close factor, with protocol-specific conditions that can permit more.

Thus liquidation profitability is a protocol-state calculation, not a generic percentage.

## 11. Liquidation has a second optimization

The problem is not only whether bonus exceeds costs. It is max_D NetLiquidationPnL(D), subject to health-factor eligibility, close factor, debt outstanding, collateral availability, bonus, disposal liquidity, flash capacity, price impact, gas and competition.

A positive theoretical bonus can still produce negative realized PnL if seized collateral cannot be disposed of cheaply enough.

## 12. Fixed-cost versus variable-cost regimes

Fixed-dominated regime: transaction gas or another fixed cost dominates a small gross edge. Increasing Q can improve economics until price impact destroys the edge.

Variable-dominated regime: price impact, venue fee or proportional flash cost dominates, so larger Q can rapidly reduce profitability.

Mixed regime: most real opportunities satisfy Profit(Q) = Edge(Q) - VariableCost(Q) - FixedCost.

Therefore a single minimum-spread threshold such as spread > X% is mathematically inadequate.

## 13. Profitability boundary

Define B(Q) = GrossEconomicEdge(Q) - AllCosts(Q).

B(Q) < 0 means reject; B(Q) = 0 means break-even; B(Q) > 0 means theoretical positive; B(Q) above ProfitFloor plus a safety margin is eligible for executable simulation.

The research must identify the interval Q in which B(Q) exceeds the floor, rather than returning one arbitrary amount.

## 14. Polygon's low gas is not sufficient

Low transaction cost improves the fixed-cost term, but does not remove pool fees, flash premiums, price impact, liquidity fragmentation, token taxes, competition, ordering failure or protocol-specific settlement costs.

LowGas does not imply GuaranteedProfit.

The relevant Polygon advantage, if any, must be measured as GrossEdge minus TotalPolygonExecutionCost.

## 15. Current Polygon venue implications

Official Uniswap documentation confirms the Polygon V3 deployment set and chain ID 137.

QuickSwap documentation confirms Polygon PoS V2 router/factory, Polygon PoS V3 Algebra factory/pool deployment, V2 flash swaps, V2 and V3 liquidity, and routing across V2/V3 liquidity.

This creates an important research surface: V2 ↔ V3 ↔ other Polygon liquidity venues, where fee curves, liquidity depth, price response, callback/flash mechanics and routing constraints differ.

## 16. First-principles profit hierarchy

ProfitSource -> ExecutableState -> RouteFunction -> OptimalSize -> AllCosts -> Competition -> AtomicSettlement -> RealizedPnL.

A missing layer means the candidate is incomplete.

## 17. New research insight: profit is a surface, not a number

The correct object is P(Q,S,O), not spread minus fees.

The research surface spans amount, block/state, venue, route, liquidity, fee, gas, ordering and competitor state. A profitable point can disappear one block later.

## 18. Layer-2 conclusion

A flash-funded opportunity is valuable only when the post-trade state contains more repayable economic value than the complete cost of creating that state.

The flash loan is an enabling constraint-relaxation mechanism, not the economic edge.

Next layer: Polygon venue-by-venue protocol-native economics, beginning with Uniswap V2, QuickSwap V2, Uniswap V3, QuickSwap Algebra V3, other sealed Polygon AMM families, Aave liquidation/flash liquidity, Balancer and other flash-liquidity sources, and RFQ/intent/orderflow surfaces.

Each venue must be treated as a separate mathematical machine. No universal fee or AMM formula may substitute for its actual rules.