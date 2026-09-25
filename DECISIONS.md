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
