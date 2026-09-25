# Opportunity Bus

## Purpose
Provide a low-latency normalized handoff from scanner fabric to execution candidates.

## Signal Fields
- opportunity_id
- fingerprint
- chain
- block
- timestamp
- strategy
- token_path
- pool_path
- gross_value
- flash_cost
- dex_fees
- gas_cost
- slippage
- execution_cost
- expected_net
- confidence vector
- required liquidity
- expiry block/time
- simulator version
- scanner provenance

## Pipeline
Scanner -> normalize -> fingerprint -> deduplicate -> freshness check -> priority rank -> executor queue.

## Priority
Priority should be based on expected realized value, execution probability, freshness, liquidity confidence and inclusion probability.

## Expiry
Every signal has an explicit TTL/expiry. Expired signals are rejected without execution.
