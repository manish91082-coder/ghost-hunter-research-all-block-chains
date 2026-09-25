# Ghost Hunter Research — All Blockchains

## Project Identity
Project: Ghost Hunter Universal Profit Mesh (research + architecture track)
Repository: manish91082-coder/ghost-hunter-research-all-block-chains
Visibility: Public
Default branch: main

## North Star
Build a lightweight, zero-cost-first, continuously running multi-chain opportunity intelligence and execution architecture that can monitor economically relevant blockchain state, pools, pairs, routes, events, orderflow and strategy surfaces, then pass fresh opportunities through a hardened executor.

The system is NOT allowed to force trades merely to create activity. A transaction is authorized only after fresh-state validation, exact economic simulation, risk checks and an on-chain profit guard.

## Current Architecture
Chain/RPC Fabric
  -> Event + State Ingestion
  -> Scanner Fabric (~150 logical scanners initially)
  -> Opportunity Bus
  -> Deduplication + Ranking
  -> Fresh-State Recheck
  -> Exact Simulation / Risk / Competition
  -> Execution Governor
  -> Smart-Contract Profit Guard
  -> Chain-specific Executor
  -> On-chain Receipt + Realized PnL
  -> Missed-Opportunity / Learning Loop

## Operating Doctrine
1. Scan continuously; execute selectively.
2. No forced trade.
3. No intentional negative-EV execution.
4. Scanner signals are never execution authorization.
5. Executor is the final decision layer.
6. Stale or conflicting state causes rejection/freeze.
7. Every important research/design decision is versioned in Git.
8. Secrets, private keys and credentials never enter this public repository.
9. Research claims must be evidence-backed and marked as verified, provisional or unknown.
10. Every substantive project response should advance the project and update the relevant canonical project records.

## Validation Path
Shadow -> Local/Fork Simulation -> Tiny Canary -> Verified Live Hunting -> Controlled Scale -> Paid Infrastructure migration.

## Important Limitation
Mathematically guaranteed positive PnL every minute cannot be promised because market opportunities are stochastic. The engineering target is maximum opportunity coverage, maximum execution reliability and zero intentional loss trades.

See:
- PROJECT_CONSTITUTION.md
- ARCHITECTURE.md
- SCANNER_UNIVERSE.md
- ZERO_COST_ARCHITECTURE.md
- CONTINUITY_PROTOCOL.md
- PROJECT_STATUS.md
