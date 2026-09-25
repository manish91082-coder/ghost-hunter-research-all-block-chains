# Zero-Cost-First Architecture

## Goal
Validate the hunting architecture with minimal/no paid infrastructure before scaling.

## Compute
- Lightweight asynchronous Python for orchestration/scanning.
- Local persistence/cache.
- Multiprocessing only for proven CPU bottlenecks.
- Rust only after profiling identifies a critical hot path.

## Data
- Free/public RPC mesh.
- Multiple providers per chain where possible.
- Provider health scoring: latency, freshness, error rate, consistency and rate-limit pressure.
- Local event/state cache.
- Periodic reconciliation against chain state.

## Simulation
- Local EVM fork where supported.
- Shadow mode before live.
- Tiny canary after fork validation.

## Cost Boundary
The project must not claim literally zero operational cost for all live environments. Free public infrastructure has rate limits, variable latency and availability constraints. Zero-cost-first means no paid infrastructure is required to prove the architecture and hunting logic.

## Migration
Provider interfaces must be abstract so paid RPC, dedicated nodes, private relays or specialized data feeds can be substituted later without redesigning scanners or the executor.
