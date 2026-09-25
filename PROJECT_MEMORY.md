# Project Memory

## Durable Project Context

Ghost Hunter Universal Profit Mesh is a separate research/architecture track from the existing Ghost Hunter AI Smart implementation repository.

### Canonical Research Repository
manish91082-coder/ghost-hunter-research-all-block-chains

### Repository Safety Lock
- This research track works only in the canonical repository above.
- Legacy implementation repositories must not be modified by research steps.
- Before any GitHub write, verify repository identity, branch, PROJECT_STATUS.md and latest HEAD.
- Next means one atomic, evidence-backed, verified progression step.

### Current Scope Lock
Polygon PoS Mainnet only, chain ID 137.

No other blockchain research begins until Polygon reaches its explicit saturation gate.

### Objective
Create a continuously operating, multi-chain opportunity intelligence and execution system that can observe economically relevant DeFi/MEV/orderflow surfaces and safely convert validated opportunities into realized net PnL.

### Polygon Saturation Objective
Build an evidence-backed Polygon knowledge base containing:

- chain/runtime ground truth
- RPC/node fabric
- system and bridge contracts
- protocol/DEX universe
- token universe
- pool/pair universe
- route/combination universe
- flash-liquidity/lending/liquidation surfaces
- MEV/orderflow/intent/solver surfaces
- strategy universe
- technical-analysis features
- AI/ML prediction surfaces
- exact economic/cost model
- unknown and negative-space registry

### Evidence Doctrine
No address, pair, pool, protocol, liquidity figure or profitability claim is accepted as VERIFIED without reproducible evidence.

Evidence must distinguish:
- VERIFIED
- PARTIAL
- HISTORICAL
- UNVERIFIED
- CONFLICTED
- STALE
- DEPRECATED

### Profit Doctrine
The project does not promise mathematical certainty of profit in the external market.

The engineering target is stricter: never knowingly authorize a transaction unless fresh state, exact simulation, all costs, risk, competition and minimum-profit gates pass. Realized on-chain PnL is the final truth.

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


## 2026-09-25 — P1 execution wiring memory
- Canonical live-verification target file: `chains/polygon-pos/verification_targets.txt`.
- First pass intentionally covers only Polygon-side critical system contracts. Ethereum-side bridge/governance objects are not mixed into the chain-137 code probe.
- GitHub Actions now syntax-checks and runs the verifier with the target file.
- Actual live evidence is still unconfirmed until workflow artifacts/results are observed. Never promote an address to VERIFIED from workflow configuration alone.


## 2026-09-25 — Input integrity lock
- Verification targets are validated as 20-byte hexadecimal EVM addresses before RPC calls.
- Changing the target file now triggers the Polygon read-only workflow.
- Workflow configuration is not evidence. Only observed runner output/artifacts can advance P1.


## 2026-09-25 — Reconciliation memory lock
- P1 evidence now has a dedicated deterministic reconciliation layer in the canonical repo.
- Conflicting RPC observations are preserved/quarantined; no majority vote is used to manufacture agreement.
- GitHub Actions uploads the reconciliation artifact alongside raw JSONL/checkpoint/head evidence.


## 2026-09-25 — CI command-path lock
- The Polygon workflow uses explicit multiline shell commands to avoid command-concatenation ambiguity.
- Validation, verification, reconciliation, and artifact upload remain separate stages.

## 2026-09-25 — Run #13 canonical memory
- Parallel RPC verifier speed hardening introduced a newline serialization defect; commit `84fadf926ee9cd96c3b2b0a228458ebb28d9b1a8` repaired it.
- Run #13 artifact `10876891277` is valid JSONL: 51 records, 51 physical lines, zero literal `\\n` serialization artifacts, zero JSON parsing errors.
- Run #13 still fails P1 correctly: one RPC supplied chain ID 137 and block 94,433,671; independent two-RPC quorum was not achieved.
- Four of eleven critical addresses returned code from only that one endpoint; all eleven remain unverified under the cross-RPC gate.
- Do not weaken quorum, target coverage, or fail-closed behavior to obtain a green workflow. Next work must improve independent RPC accessibility/rate-limit coverage or move the unchanged verifier to another permitted execution environment.
