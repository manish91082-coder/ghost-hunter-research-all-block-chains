# Project Memory

## Durable Project Context
Ghost Hunter Universal Profit Mesh is a separate research/architecture track from the existing Ghost Hunter AI Smart implementation repository.

### Objective
Create a continuously operating, multi-chain opportunity intelligence and execution system that can observe economically relevant DeFi/MEV/orderflow surfaces and safely convert validated opportunities into realized net PnL.

### Scope
- ~28–30+ economically relevant chains initially, with universe expansion based on evidence.
- All economically relevant pairs/pools/routes, not blind brute-force polling.
- DEX/DEX, intra-DEX, triangular, multi-hop, cross-chain, CEX/DEX, backrun, liquidation, intent/RFQ/filler, solver/relayer, liquidity/state-transition and meta-opportunity surfaces.
- Initial scanner target: ~150 logical scanners using a shared kernel/fabric.
- Scalable detector fabric: 300+ and eventually 1000+ configurable detectors without 1000 independent processes.

### Core Doctrine
Scanner -> Opportunity Signal -> Fresh-State Recheck -> Exact Simulation -> Risk/Competition Gate -> Execution Governor -> Profit Guard -> Chain Execution -> Receipt Verification -> Realized PnL -> Learning.

### Testing Doctrine
Zero-cost-first. Public/free RPC mesh, local state cache, event-driven updates, local fork simulation, shadow mode, tiny canary, then controlled scale.

### AI Doctrine
Hot path: deterministic low-latency code.
Warm path: ML/statistical prediction.
Cold path: LLM/research/strategy discovery.

### Explicit Non-Goal
Never force a trade simply to make a profit appear every minute. Continuous scanning is required; continuous trading is not.
