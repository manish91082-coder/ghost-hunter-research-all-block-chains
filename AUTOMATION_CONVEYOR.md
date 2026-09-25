# Autonomous Saturation Conveyor

## Objective
Continuously advance Polygon saturation research from P2 through P11 without requiring a manual Next turn for every evidence batch.

The conveyor is fail-closed:
- scanners and discovery workers only collect evidence;
- no live trading or transaction submission;
- a stage may run in shadow mode while an earlier critical gate is open;
- promotion requires explicit evidence predicates;
- transport failures never become semantic evidence.

## Why this architecture
GitHub Actions scheduled workflows can run as often as every five minutes. The repository therefore uses one persistent state-machine workflow instead of a long chain of P2 -> P3 -> P4 workflows. GitHub documents that workflow_run chaining cannot exceed three levels, while concurrency controls can serialize a stateful conveyor. The conveyor therefore uses schedule + manual dispatch + one checkpoint state artifact. SOURCES: GitHub Workflow Syntax and Events documentation.

## Two lanes

### Critical lane
P2 remains the promotion blocker until all required P2 evidence predicates close.

Current P2 critical tasks:
1. regression suite
2. derived-control runtime-code verification
3. parent control-function verification
4. provenance replay

When P2 closes, the critical lane automatically advances through P3 -> P4 -> ... -> P11.

### Shadow lane
While P2 is still open, the machine prepares P3-P10 data without promoting those stages.

This prevents idle time. Shadow outputs are labeled DISCOVERY, DERIVED, SCREENING_ONLY, or CLOSURE_GATE and do not override the P2 promotion gate.

## Evidence persistence
The checkpoint is retained as a GitHub Actions artifact. The repository commits state to main only when a real gate or stage transition occurs, avoiding commit spam.

## Source adapters
Current first-pass public discovery adapters:
- DefiLlama protocol universe for Polygon.
- DEX Screener token profiles.
- DEX Screener token-pairs endpoint for Polygon.

## P3-P10 first-pass outputs
- P3: protocol and DEX discovery snapshot.
- P4: token candidate queue.
- P5: incremental pair/pool snapshot queue.
- P6: route graph and bounded route candidates.
- P7: 18-family strategy matrix.
- P8: deterministic TA and market features.
- P9: gross-spread economic screening marked NOT_EXACTLY_CERTIFIED.
- P10: saturation audit with explicit open blockers.
- P11: research-closure and next-chain-unlock gate.

## Second-pass upgrades
The intended second pass will add:
- source fusion and contradiction resolution;
- protocol-specific factory and registry discovery;
- richer token provenance and creation history;
- ABI, event and trace enrichment;
- venue-specific pool state reconstruction;
- exact swap math and gas, fee, slippage simulation;
- route graph expansion and negative-space enumeration;
- historical time-series feature store;
- model-backed anomaly, sequence and graph intelligence;
- independent saturation audit sources.

No second-pass component may weaken the evidence gates established by the first pass.

## Current automation status
The conveyor is implemented but P2 remains the research promotion gate. The machine can therefore collect P3-P10 preparatory evidence continuously while P2 is being resolved, without falsely declaring Polygon saturated.
