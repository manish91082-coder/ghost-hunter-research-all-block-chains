# Polygon Flash-Loan Profit Research — Research Constitution & Layer 1

**Track:** Post-saturation Polygon economic/profit research  
**Chain:** Polygon PoS Mainnet, chain ID 137  
**Status:** ACTIVE RESEARCH / NO EXECUTION  
**Code:** NONE in this track until explicit user authorization  
**Primary goal:** Identify every economically legitimate, evidence-backed mechanism by which an atomic flash-funded transaction can produce **realized positive net PnL after all applicable costs** on Polygon.

## 1. Non-negotiable interpretation of "profit"

The flash loan itself is not the source of profit. It is temporary balance-sheet capacity.

A candidate is economically interesting only when a source of value exists, such as:
- price dislocation;
- route inefficiency;
- pool-state inconsistency across venues;
- liquidation incentive;
- protocol-defined reward/rebate;
- orderflow/filler compensation;
- cross-market basis/spread;
- other lawful protocol-state transition that leaves a deterministic surplus.

The canonical quantity is:

`REALIZED_NET_PNL = FINAL_ASSET_VALUE - FLASH_PRINCIPAL - FLASH_PREMIUM - DEX_FEES - SLIPPAGE/PRICE_IMPACT - GAS - EXECUTION/RELAY_COST - TRANSFER_TAXES - OTHER_APPLICABLE_COSTS`

Quoted PnL, mid-price spread, theoretical spread or gross output is not profit certification.

**No mathematical or engineering process can guarantee that a future market opportunity will actually be included and filled at the predicted state.** The research target is deterministic rejection of economically unsafe trades plus maximum coverage of positive-edge states.

## 2. Evidence classes

Every finding is one of:
1. VERIFIED_ONCHAIN — independently reproduced from current chain state.
2. VERIFIED_PROTOCOL — directly supported by current official protocol documentation and contract/deployment evidence.
3. HISTORICAL_OBSERVED — historical transaction/event evidence.
4. DERIVED — mathematically derived from verified inputs.
5. HYPOTHESIS — plausible but not yet proven.
6. UNKNOWN — not enough evidence.
7. DISPROVED/REJECTED — contradicted by evidence or economics.

No hypothesis is promoted by repetition.

## 3. Research boundary

This track does NOT reopen Polygon census gates P2-P11. The Polygon research universe is already sealed as a census. The economic track uses that sealed universe as its search space and independently deepens unresolved economic candidates.

Current sealed research counts are:
- 469 token records;
- 2,821 unique pair records;
- 617,622 route candidates;
- 18 strategy families;
- 1,891 feature groups;
- 420 exact-economic candidate groups;
- historical exact-profit-certified count: 0/420.

These numbers describe research-universe coverage, not profitable-trade count.

## 4. Initial profit mechanism taxonomy

### A. Cross-venue price arbitrage
Buy the same economic asset where its executable price is lower and sell where executable price is higher, inside one atomic transaction where possible.

Subfamilies:
- DEX A -> DEX B;
- DEX A -> DEX B -> DEX C;
- same token across V2/V3/CL/weighted pools;
- stablecoin pool dislocations;
- wrapped/native-equivalent dislocations;
- correlated-asset temporary dislocations.

The real edge is **executable output differential**, not displayed spot price.

### B. Intra-venue route arbitrage
A single venue can expose multiple routes or pool types whose executable prices differ. Examples include V2 versus concentrated liquidity, different fee tiers, or alternative pool paths.

Profit condition must use actual state transitions for the selected route.

### C. Triangular and cyclic arbitrage
A -> B -> C -> A can be profitable even when no direct A/B cross-venue spread appears.

The source may be:
- inconsistent pair ratios;
- fee-tier differences;
- thin-pool state;
- stablecoin/correlated-asset divergence;
- route topology.

The atomic cycle must return enough A to repay the flash obligation plus every cost.

### D. Multi-hop and split-route optimization
A nominal two-leg trade may be inferior to a route using several pools or splitting size across independent liquidity surfaces.

This creates a combinatorial profit surface:
- route choice;
- split percentage;
- hop count;
- pool fee;
- liquidity depth;
- state-dependent price impact.

The best gross route is not necessarily the best net route.

### E. Concentrated-liquidity/tick dislocations
V3/Algebra-style pools create discontinuous liquidity depth around ticks. The opportunity can be caused by:
- liquidity concentrated on one side of price;
- exhausted tick ranges;
- stale external price versus local pool state;
- different fee tiers;
- multi-pool inventory fragmentation.

The important object is not merely price but the piecewise liquidity curve.

### F. Weighted/Stable/Hybrid AMM dislocations
Non-constant-product pools can have different marginal-price responses from constant-product pools. A cross-model route may create opportunities invisible to a simple x*y=k scanner.

Research must therefore calculate protocol-native swap math rather than applying a universal AMM formula.

### G. Reactive/backrun arbitrage
A large state-changing transaction can create a temporary price imbalance. A subsequent atomic transaction can potentially restore equilibrium and capture the difference, subject to ordering, inclusion and competition constraints.

This is a timing/ordering problem, not simply a price-snapshot problem.

### H. RFQ / intent / solver spread capture
A quote or intent can create a tradable spread between:
- requested execution price;
- available on-chain liquidity;
- alternative liquidity sources;
- filler/solver compensation.

The opportunity is protocol-specific and must honor the protocol's settlement and competition rules.

### I. Liquidation incentive capture
Aave and other lending protocols can pay a liquidation bonus to liquidators. Flash liquidity can supply the capital needed to repay debt and receive discounted collateral.

Profit source:
**liquidation bonus minus flash premium, swap/repayment fees, gas, price impact, collateral disposal cost and competition cost.**

Aave documentation states that positions become liquidatable when health factor is below 1 and liquidators receive collateral at a discount/bonus defined per reserve and surfaced through on-chain views.

### J. Collateral/debt restructuring
Flash liquidity can atomically:
- repay an existing position;
- swap collateral;
- reopen debt under a different asset or protocol;
- capture a protocol-defined fee/reward or economic discount.

This is only a profit strategy when a deterministic surplus exists. Operational convenience alone is not profit.

### K. Protocol incentive/rebate arbitrage
Economic surplus can come from explicit protocol incentives, rebates or fee mechanics rather than price spread.

The research must distinguish:
- recurring genuine incentive;
- temporary campaign;
- user fee paid by the protocol;
- reward token with unstable mark-to-market value.

### L. Spot/perpetual/future/basis dislocation
Where Polygon venues expose sufficiently atomic settlement, spot and derivative prices can diverge.

Potential structures include:
- spot buy + derivative sell;
- derivative buy + spot sell;
- funding/fee compensation.

This is much harder than DEX/DEX arbitrage because margin, funding, settlement and venue-specific state must be modeled exactly.

### M. Stablecoin/depeg convergence
A stablecoin may trade away from its reference value or from another venue's price.

Potential profit source:
- temporary redemption/market imbalance;
- stable-pool curve dislocation;
- cross-venue stablecoin spread.

The research must avoid assuming a peg is guaranteed. A stablecoin can remain depegged or become impaired.

### N. Bridged-asset / representation dislocation on the SAME chain
Different representations of economically related assets can temporarily diverge.

This is not automatically arbitrage because:
- representations can have different redemption rights;
- bridge/security risk may be embedded in price;
- liquidity can be non-fungible in practice.

Only same-chain, atomically executable convergence is eligible for the first research class.

### O. Protocol-state transition surplus
Beyond swaps, certain protocol actions may create a deterministic economic surplus:
- liquidation;
- bad-debt cleanup;
- auction settlement;
- collateral auction discount;
- fee claim/rebate;
- protocol-specific balance-sheet state transition.

These are to be treated as first-class strategy families rather than forcing every opportunity into a DEX arbitrage template.

## 5. Explicitly excluded strategy classes

The research does not treat:
- oracle manipulation;
- smart-contract exploitation;
- theft/draining;
- reentrancy abuse;
- access-control bypass;
- malicious price manipulation;
- sandwiching users for extraction;
- attacks intended to leave protocols insolvent;
- unauthorized use of private/orderflow information

as legitimate profit strategies.

Security research may analyze these mechanisms as **risk surfaces** because the executor must defend against them, but they are not part of the project's authorized profit universe.

## 6. Polygon-specific initial surfaces

The canonical repository currently records Polygon flash-liquidity candidates including:
- Aave V3 Pool;
- Balancer V2 Vault;
- DEX-native flash/atomic callback surfaces requiring venue-level verification.

Aave's current documentation states that flash-loan fees are initialized at 0.05% and can be changed by governance; production logic must read the current on-chain premium rather than hard-code the historical/default value.

QuickSwap documentation currently describes a 0.25% V2 pool trading fee and a V3 concentrated-liquidity model. Its current deployment page provides Polygon V2/V3/V4 contract addresses.

Uniswap's official Polygon V3 deployment documentation confirms Polygon chain ID 137 and the official V3 deployment set. Uniswap V2's whitepaper documents flash swaps, where assets can be sent before payment provided the pool is made whole by the end of the transaction.

These are venue/protocol facts; they do not imply that a profitable route currently exists.

## 7. Minimum economic gate

For a candidate amount Q:

NetProfit(Q) > MinimumProfitFloor

AND

- exact flash premium known;
- exact venue fee(s) known;
- executable route output known;
- price impact/slippage known from current state;
- gas estimate known;
- gas price/cost known;
- token transfer tax/fee behavior known;
- route execution constraints known;
- ordering/inclusion risk assessed;
- competition assessed;
- all legs are atomic or the residual settlement risk is explicitly modeled;
- profit guard is deterministic and fail-closed.

The research must optimize over Q, not merely test one arbitrary trade size.

## 8. What "confirm profit" will mean

Three different certifications are required:

**Theoretical positive:** verified state + exact protocol math produces positive surplus under fixed assumptions.

**Executable positive:** a full transaction simulation against a sufficiently fresh state produces positive surplus after all modeled costs.

**Realized positive:** an actual confirmed on-chain receipt shows positive final asset delta after every applicable cost.

Only the third is realized profit.

No amount of theoretical or simulated evidence will be relabeled as realized.

## 9. AI-agent doctrine for this research

The AI research agent:
- must stay goal-centric;
- must not optimize for activity, number of trades or response length;
- must prefer verified evidence over plausible narratives;
- must preserve negative and contradictory evidence;
- must not turn a stale quote into a live opportunity;
- must separate discovery, ranking and authorization;
- must never infer current fees/liquidity from historical snapshots;
- must never assume a protocol is unchanged;
- must calculate complete cost, not only gross spread;
- must keep alternative hypotheses alive until evidence resolves them;
- must explicitly search negative space after each major mechanism family;
- must reject duplicate mechanisms that merely use different terminology;
- must maintain provenance for every high-impact claim;
- must treat rate-limit/provider errors as infrastructure evidence, not blockchain-state evidence;
- must never enable signing or broadcast during research.

## 10. Research sequence

Each future "NEXT" descends one level:

1. Mechanism taxonomy.
2. Protocol-native economic equations.
3. Polygon venue-by-venue surface mapping.
4. Current fee/premium/liquidity rules.
5. Historical on-chain examples.
6. Current state reconstruction.
7. Opportunity-generation conditions.
8. Exact amount optimization.
9. Competition/orderflow effects.
10. Failure economics.
11. Sensitivity analysis.
12. Shadow execution requirements.
13. Realized-PnL certification design.
14. Unknown/negative-space sweep.

The research terminates only when additional searches stop producing new economically distinct mechanisms or materially new evidence.

## 11. Source hierarchy

Priority:
1. Current on-chain state and transaction receipts.
2. Official protocol documentation/contracts/governance.
3. Primary academic/research papers.
4. High-quality independent analytics.
5. Secondary commentary only for leads.

A single blog or social-media claim is never sufficient for execution-critical facts.

## 12. Current Layer-1 conclusion

The strongest first principle is:

**Flash loans do not create profit. They remove the upfront-capital constraint from an already-existing economic edge.**

Therefore the central research problem is:

**Where, on Polygon, can a deterministic executable surplus exist after protocol fees, flash premium, gas, price impact, ordering and competition?**

The next layer must attack that question mechanism-by-mechanism, with exact formulas and Polygon-specific evidence, rather than adding more generic flash-loan descriptions.
