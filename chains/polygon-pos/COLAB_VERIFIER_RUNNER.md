# Polygon Colab Verifier Runner Contract

**Purpose:** define the exact behavior of the future zero-cost, read-only live verifier. This document is an execution contract, not a claim that live RPC calls have already run.

## Inputs
- `RPC_ENDPOINTS`: independent HTTPS JSON-RPC endpoints, supplied at runtime.
- `ADDRESS_REGISTRY`: canonical Polygon address registry from this repository.
- `PROBE_PLAN`: deterministic method/parameter list.
- `CHECKPOINT`: optional resumable state.

## Runtime sequence
1. Load and validate inputs.
2. Reject any endpoint missing an explicit HTTPS scheme or containing embedded credentials.
3. For each endpoint, probe identity and head methods first.
4. Record every request/result/error as append-only JSONL.
5. Hash normalized results with SHA-256.
6. Compare critical observations across independent endpoints.
7. Probe code, proxy slots, implementation, roles and selected events for registry objects.
8. Classify each object using the evidence-state rules.
9. Persist checkpoint after each bounded batch.
10. Produce summary and manifest.

## Mandatory safety controls
- Allowlist methods. Default allowlist is read-only `eth_*`, `net_version`, `web3_clientVersion`, plus explicitly configured trace/debug reads.
- Explicit denylist includes transaction submission and signing methods.
- No private keys, seed phrases, cookies, API secrets or authorization headers in outputs.
- Never mutate chain state.
- Never use an endpoint merely because it is faster if critical state conflicts with independent endpoints.

## Determinism
- Stable probe IDs.
- Stable JSON normalization before hashing.
- UTC timestamps.
- Explicit block tags.
- No hidden retries that change the probe definition.
- Retry metadata recorded separately from the original observation.

## Batching and resilience
- Bounded concurrency.
- Per-endpoint timeout.
- Exponential backoff with a maximum retry count.
- Adaptive `eth_getLogs` ranges based on observed provider limits.
- Endpoint rotation only for the next independent observation, never for silently replacing a failed result.
- Resume from checkpoint after interruption.

## Output contract
- `polygon_rpc_observations.jsonl`: endpoint/method observations.
- `polygon_address_verification.jsonl`: address-level evidence records conforming to `polygon-verification-record.schema.json`.
- `polygon_address_verification_summary.md`: human-readable gate summary.
- `polygon_evidence_manifest.json`: file hashes, run metadata and source/probe versions.
- `polygon_verifier_checkpoint.json`: resumable progress.

## P1 pass criteria
- At least two independent endpoints agree on chain ID and coherent head state.
- Critical addresses have non-empty expected code and cross-RPC runtime-code agreement.
- Proxy implementation/admin/role evidence is reconciled where applicable.
- Historical/current status is explicit.
- Every unresolved conflict is retained.
- No write method executed.
- Output files validate against the declared schema.

## Important limitation
Public RPC documentation establishes method semantics, not current endpoint health. Live endpoint capability, latency, head freshness, historical retention and cross-RPC agreement must be measured during the run.