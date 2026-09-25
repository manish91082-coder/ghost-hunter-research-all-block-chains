# Polygon PoS Block, Timing and Finality Evidence

## Evidence date
2026-09-25

## Documented architecture

Polygon's published material describes Polygon PoS as a dual-layer architecture involving Bor and Heimdall.

- Bor is the EVM-compatible block-production/execution layer.
- Heimdall is the consensus/checkpoint layer.
- Heimdall v2 introduced approximately 5-second transaction finality according to Polygon's July 2025 announcement.
- Later Polygon material states that the Rio upgrade in October 2025 eliminated reorgs for confirmed blocks, while subsequent upgrades increased capacity and changed block-production behavior.

Sources:
- https://polygon.technology/blog/polygon-5-second-fast-finality-upgrade
- https://polygon.technology/blog/polygon-chain-now-supports-5000-payments-per-second-hitting-the-speed-of-a-card-network-at-a-fraction-of-the-cost
- https://polygon.technology/blog/faster-finality-with-the-aalborg-upgrade-for-polygon-proof-of-stake-network

## Current-state interpretation

The historical statements above are not sufficient to claim a live measured block-time distribution or live finality latency.

For Ghost Hunter, the important distinction is:

**protocol/documented finality property != measured execution-time observation**

Both must be stored separately.

## Live measurements required

The Polygon collector must continuously capture:

### Block cadence
- block number
- block timestamp
- wall-clock observation time
- delta from previous block
- rolling median
- p50/p90/p95/p99
- missed/late block observations
- block gas used
- block gas limit
- transaction count

### Head agreement
Across independent RPCs:

- block number
- block hash
- parent hash
- timestamp
- state-root where exposed
- observation latency

### Reorg/finality evidence
For sampled blocks:

- first-seen block hash
- later-observed block hash
- parent consistency
- replacement/reorg detection
- finalized/milestone status where exposed
- time from first observation to finality evidence

### Execution safety interpretation

Until the collector has measured the current behavior, the executor should not hard-code a historical block-time or finality assumption as if it were live truth.

For high-value opportunities, finality requirements should be expressed as explicit configurable gates.

## Important recent protocol evidence

Polygon published in August 2026 that Bor v2.10.0 (Austin) and Heimdall v0.11.0 (Kyoto) had activated on mainnet at height 51,533,000, with the releases described as mandatory for node operators. This establishes that the chain's current protocol generation is newer than the older architecture articles often found in search results.

Source:
https://forum.polygon.technology/t/security-releases-review-bor-v2-10-0-austin-hf-and-heimdall-v0-11-0-kyoto-hf/22138

This is a protocol-version fact, not a live node-version census.

## Status

- Documented chain architecture: VERIFIED
- Historical finality upgrade facts: VERIFIED
- Current block number: PENDING LIVE RPC
- Current block-time distribution: PENDING LIVE RPC
- Current reorg rate: PENDING LIVE RPC
- Current finality latency distribution: PENDING LIVE RPC
- Current node/client version distribution: PENDING NODE/RPC EVIDENCE
