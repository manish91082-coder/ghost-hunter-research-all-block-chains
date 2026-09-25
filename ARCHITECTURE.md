# System Architecture

## 1. Layer Model
0. Infrastructure: RPC mesh, WebSocket/event sources, local cache, persistence, health scoring.
1. Chain State Fabric: blocks, logs, pool state, token metadata, protocol state and chain-specific execution metadata.
2. Opportunity Graph: token -> pool -> DEX -> protocol -> chain relationships plus cross-chain edges.
3. Scanner Fabric: shared scanner kernel with configurable detectors. Initial target ~150 logical scanners.
4. Opportunity Bus: normalizes, fingerprints, deduplicates, ranks and expires signals.
5. Calculation: exact fees, flash premium, gas, slippage, price impact, liquidity, settlement and minimum-profit calculations.
6. Simulation: fresh-state simulation, fork replay, adversarial simulation and execution-probability assessment.
7. Execution Governor: final authorization. Applies risk, confidence, competition and expiry rules.
8. On-chain Guard: transaction-level profit/repayment assertions.
9. Verification: receipt parsing, token/native balance deltas, realized net PnL and failure classification.
10. Learning: missed-opportunity ledger, route memory, competitor memory, strategy health and scanner optimization.

## 2. Key Principle
All scanners are always eligible to run, but no scanner can bypass the execution governor.

## 3. Performance Principle
Use event-driven incremental recomputation. Do not poll every pair on every chain at a fixed high frequency.

## 4. AI Placement
Do not put LLM calls in the critical execution hot path.
