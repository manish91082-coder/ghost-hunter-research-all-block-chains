# Decisions

## D-001 — Separate Architecture Track
Date: 2026-09-25
Decision: Use this public repository as a separate research/architecture continuity track, distinct from the existing Ghost Hunter AI Smart implementation repository.
Reason: Avoid project mixing and preserve a clean source of truth.

## D-002 — Scanner Fabric
Decision: Start with ~150 logical scanners through a shared kernel; scale by configuration and evidence rather than spawning hundreds of independent processes.

## D-003 — Event-Driven Scanning
Decision: Prefer event/block-triggered incremental recalculation over brute-force polling of every pair at fixed frequency.

## D-004 — Executor Separation
Decision: Scanner signals cannot directly authorize execution. Executor performs final fresh-state and safety validation.

## D-005 — No Forced Trading
Decision: Continuous monitoring is mandatory; continuous trading is not. No trade is forced merely to make every minute active.

## D-006 — Zero-Cost-First
Decision: Prove detection, simulation and controlled hunting with free/public infrastructure first. Paid infrastructure is a later optimization.

## D-007 — AI Hot Path
Decision: Keep LLM calls out of the critical execution path. Use deterministic code for hot execution, ML for prediction/ranking, and LLMs for research/strategy discovery.

## D-008 — Polygon-First Saturation Lock
Date: 2026-09-25
Decision: Until the Polygon saturation gate is formally closed, all substantive research work in this track is restricted to Polygon PoS Mainnet, chain ID 137.
Reason: Achieve a deep, evidence-backed chain-specific knowledge base before expanding to another blockchain.

## D-009 — Address-Level Evidence Gate
Date: 2026-09-25
Decision: A protocol, DEX, pool, pair, token, router, factory, quoter, lending market, flash-liquidity source, MEV/orderflow surface or other execution-relevant object is not marked VERIFIED until its on-chain identity and relevant behavior are independently verified.
Reason: Prevent stale, copied, guessed or fictitious data from entering the execution knowledge base.

## D-010 — Profit Claim Discipline
Date: 2026-09-25
Decision: Research may rank positive-EV candidates only after exact state, all known costs, execution constraints and simulation gates are satisfied. No external-market outcome is represented as mathematically guaranteed profit.
Reason: Avoid confusing deterministic calculation under assumptions with guaranteed realized profit.
## D-011 — Post-Saturation Polygon Economic Deep-Dive
Date: 2026-09-27
Decision: Polygon P2-P11 census gates remain sealed; exact economic/profit research proceeds as a separate post-saturation track using the sealed universe as the bounded search space.
Reason: Census completeness and profitability certification are different problems and must not be conflated.

## D-012 — Three-Level Profit Certification
Date: 2026-09-27
Decision: Profit claims are separated into theoretical positive, executable positive and realized positive. Only confirmed on-chain realized PnL is called realized profit.
Reason: Prevent theoretical spread and simulation output from being mistaken for actual economic outcome.

## D-013 — No-Code Economic Research Lock
Date: 2026-09-27
Decision: The Polygon profit research track contains no implementation/code work until the user explicitly authorizes coding. Technical requirements may be documented conceptually.
Reason: Keep this stage focused on mechanism discovery, evidence and exact economics.

## D-014 — Authorized Profit Universe
Date: 2026-09-27
Decision: Oracle manipulation, contract exploitation, theft, sandwiching, access-control bypass and other malicious extraction are excluded from the authorized profit universe. They may be studied only as defense/risk surfaces.
Reason: Separate legitimate economic arbitrage from adversarial protocol abuse.
