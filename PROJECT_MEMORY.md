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

## 2026-09-25 — Current P1 memory
- GitHub runner-specific public RPC access is constrained: QuickNode public is fully usable for the 11 target code probes; Tatum is reachable for identity/head but becomes 429-limited for the code phase under anonymous access.
- Head quorum logic now uses the configured stale-block tolerance. Run #23 observed Tatum block 94,434,648 and QuickNode block 94,434,649 and classified the fresh one-block span as head agreement.
- Verifier supports `TATUM_API_KEY` via environment variable; workflow maps GitHub secret `TATUM_API_KEY` without exposing it.
- Do not weaken the two-endpoint code-hash agreement gate. The remaining dependency is authenticated/free-tier Tatum capacity or an equivalent second independent code-capable RPC environment.

## 2026-09-25 — RPC rotation memory lock
- The Polygon P1 verifier now treats RPC access as a dynamic candidate pool rather than a fixed pair.
- Rotation happens at request level for critical `eth_getCode` probes. An endpoint that returns 429/403/other failure is cooled down and the next eligible endpoint is tried.
- The verifier first proves chain ID 137 before an endpoint becomes eligible for address-code evidence.
- Two distinct endpoint IDs with successful code responses remain mandatory per critical target. Matching runtime/code hashes are reconciled later; there is no majority selection.
- Per-endpoint request pacing is enforced independently, so one provider's rate limit does not globally slow or terminate the pool.
- Tatum authentication remains optional via the `TATUM_API_KEY` GitHub Actions secret only.
- Fresh-state rule remains in force: checkpoint reuse is opt-in, not the default, to avoid silently reusing stale live evidence.
- This rotation architecture is the research-repo precedent for the future production RPC fabric: health-aware routing + cooldown + evidence diversity + fail-closed authorization.
## 2026-09-25 — Run #26 rotation proof and serializer lesson
- The adaptive pool successfully found two live Polygon endpoints from the 14-candidate pool: OnFinality and QuickNode public.
- Their observed chain ID was 137 and their latest blocks differed by one block, satisfying the configured head tolerance.
- Several critical targets received two independent code observations in the verifier output, proving request-level rotation is functioning.
- The verifier must preserve the evidence schema exactly. In Run #26 a serializer regression omitted the top-level method field, causing reconciliation to see zero method records even though the raw JSONL contained successful probes.
- Canonical evidence record fields are now treated as regression-sensitive. Future verifier changes must preserve both top-level and nested request metadata required by the reconciler/schema.
- No evidence threshold was relaxed to accommodate the serializer defect.
## 2026-09-25 — Rotation recovery lock
- RPC rotation is now health-aware and recoverable, not a single-pass failover list.
- 429 causes local backoff/cooldown and a later recovery pass may retry the provider.
- Per-endpoint pacing adapts independently, so one provider's rate limit does not globally throttle the pool.
- Recovery is bounded to prevent CI hangs or endless retries.
- The P1 independence rule remains unchanged: two distinct successful endpoint observations per critical target are mandatory.

## 2026-09-25 — P1 verified memory lock

Run #30 (`36169503083`) is the canonical live-evidence checkpoint for the bounded Polygon P1 target set.

Locked facts:
- chain ID 137;
- observation block 94,435,638;
- 3 live identity/head endpoints: OnFinality, QuickNode public, Tatum;
- all 11 critical Polygon-side target addresses have >=2 independent successful `eth_getCode` observations;
- all 11 code hashes reconcile exactly;
- reconciliation state VERIFIED;
- no unresolved code conflicts.

Boundary: runtime-code identity is verified, but proxy implementation/admin, owner/roles, creation evidence, ABI/source, function/event behavior and historical/current classification remain P2 work.

## 2026-09-25 — P2 control-plane execution lock
- P1 evidence is frozen in Run #30.
- P2 starts from the same 11-target chain-137 set and the same adaptive RPC pool.
- First P2 slice is deliberately narrow: ERC-1967 implementation/admin/beacon storage slots only.
- Two independent matching results per target/slot are mandatory; no majority selection.
- P2 read-only storage verification does not by itself prove proxy semantics for non-standard proxies. Further function/control probes remain required even after this slice passes.

## 2026-09-25 — P2 method allowlist lesson
- P2 must use the same explicit read-only method policy as P1, but each new read-only method must be registered in the shared allowlist before execution.
- `eth_getStorageAt` is now explicitly allowed.
- No transaction, signing or mutation method was introduced.
- P2 #1 failure is retained as an engineering evidence point and does not change the P1 gate.

## 2026-09-25 — P2 storage rotation lock
- Run #2 established that Tatum's anonymous RPC path can handle part of the ERC-1967 workload but returns 429 for a significant subset when the workload is endpoint-sequential.
- P2 therefore adopts the same request-level adaptive rotation model proven in P1.
- Each target/slot combination is independently routed across chain-137 eligible endpoints until two successful endpoint observations are obtained.
- Endpoint cooldown and bounded recovery prevent both starvation and infinite retry loops.
- Head quorum remains a separate freshness requirement and still needs at least two fresh chain-137 endpoints.
- No P2 control field is promoted to VERIFIED until reconciliation closes the complete target×slot matrix.

## 2026-09-25 — P2 storage gate memory lock

Run #4 is the canonical P2 ERC-1967 storage checkpoint.
- 33/33 target×slot combinations passed;
- 66 independent observations;
- 0 conflicts;
- observation block 94,436,387;
- reconciliation VERIFIED.

Four non-zero implementation/admin addresses were observed and now form the immediate derived-address verification queue.

Important: non-zero ERC-1967 storage does not by itself prove the complete proxy model; runtime code, proxy callable semantics, admin/owner/roles and deployment provenance remain separate P2 checks.
## 2026-09-25 — P2 derived-address verification lock
- Four non-zero ERC-1967-derived addresses form the immediate runtime-code verification queue.
- Each derived address requires two independent matching `eth_getCode` observations.
- Passing derived-code verification does not itself establish ownership/role semantics or creation provenance.
## 2026-09-25 — Fresh-head quorum memory lock
- Head freshness and code independence are separate evidence dimensions.
- For narrow derived-control verification, a deterministic two-endpoint fresh-head quorum is sufficient when the selected pair is within the configured block-span tolerance and both independently identify chain 137.
- This is not majority voting and does not authorize conflicting state. The excluded endpoint remains recorded as stale/outlier evidence.
- P1's existing all-successful-endpoint head behavior remains the default for the primary verifier path.

## 2026-09-25 — Derived-control workflow wiring lock
- The shared verifier supports deterministic fresh-head quorum through --min-head-endpoints.
- Run 36172904065 exposed a workflow wiring gap: the derived-control workflow omitted that argument, so the verifier used its default all-successful-endpoint head requirement.
- The same run still produced matching runtime-code hashes for all four derived addresses from two independent endpoints, confirming the code evidence path itself was healthy.
- Commit 5b0212d5ca8ce094f4438f60e424189bc0259e6a is the canonical correction and explicitly passes --min-head-endpoints 2.
- Never infer enabled verifier behavior from source support alone. The live workflow invocation is part of the evidence chain and must be verified.
- Derived-code gate remains pending until a corrected CI artifact proves both fresh-head quorum and two-endpoint code agreement.

## 2026-09-25 — P2 control-function evidence lock
- Control-function probing is read-only `eth_call` only and is driven by a canonical target manifest.
- The initial parent surface is the two contracts with observed non-zero ERC-1967 control relationships: EIP1559Burn and sPOLChild.
- Candidate selectors are labeled semantic candidates, not asserted implementations.
- Two independent chain-137 RPC outcomes are required per probe. A deterministic JSON-RPC error is evidence of the call outcome and may be reproducibly reconciled; transport failures and rate limits are not evidence.
- Reconciliation deliberately stops short of semantic interpretation. Owner/admin/implementation/proxy-role conclusions require contract-specific analysis after raw call evidence is verified.
- Commit b45635d76ca7503ffd849187b3fd3a0aa5030f51 is the canonical correction for counting reproducible JSON-RPC errors as observations.
## 2026-09-25 — Control-function runtime-regression lock
- Never count a verifier implementation change as validated merely because Python syntax compiles.
- When evidence state changes from successful-only to outcome-based observation, regression tests must cover both success and deterministic error outcomes.
- The control-function verifier must contain no stale successful[...] reference after the observed evidence-set migration.
- CI runs the deterministic regression suite before touching Polygon RPCs.
- Commit b24a9820ad632a983c44873cb4c3c98e9564b109 is the canonical runtime-reference correction.

## 2026-09-25 — CI state observability lock
- The canonical research process now includes a read-only GitHub CI state extractor at tools/github_ci_state.py.
- This tool is for evidence discovery only. It must never be used to trigger, rerun or mutate Actions.
- A workflow is not GREEN merely because source code exists or a trigger was expected; the extractor observed run/job/artifact state is authoritative for CI-state reporting.

## 2026-09-25 — Automated CI evidence lock
- `.github/workflows/github-ci-state-evidence.yml` is the canonical read-only observability layer for Actions completion state.
- It listens to the four Polygon verification workflows and stores a state snapshot artifact.
- `tools/github_ci_state.py` records both current main HEAD and triggering workflow-run context when available.
- The observer never triggers or reruns workflows. Evidence promotion still requires inspection of the actual verifier/reconciliation artifacts.

## 2026-09-25 — Evidence reacquisition lock
- When a verification workflow has been materially corrected, a deterministic workflow-marker commit may be used to force a fresh run without changing verification semantics.
- Derived-control trigger commit: b97b8fb44583b25f7eda96f8d7da8fdb434d3e39.
- Control-function trigger commit: bfe36c431d56de65e1b0164429d48d387ca30f7f.
- These commits are not evidence themselves. Only subsequent GitHub Actions job/artifact output can advance the gates.

## 2026-09-25 — Control-function transport-evidence lock
- Semantic call evidence requires an actual HTTP 200 JSON-RPC response.
- HTTP 403, 429, timeout, DNS and other transport failures are never evidence, even when two providers fail in the same way.
- JSON-RPC errors returned inside an HTTP 200 response remain reproducible call outcomes and may be reconciled.
- Regression test commit fc126f0f2e06db43de6d9082f8d07e2e7d0b773e is locked as the anti-false-green guard.

## 2026-09-26 — P2 provenance/control-surface lock
- External explorer/forum material is discovery input, never direct verification.
- The sPOL parent/admin historical transaction and the current sPOL implementation creation record are now preserved in the canonical provenance candidate file.
- The control-function target manifest intentionally includes both standard proxy selectors and contract-specific authority/owner surfaces.
- ProxyAdmin owner/pendingOwner and proxy relationship calls are read-only and require two independent chain-137 outcomes before interpretation.
- No external historical claim is allowed to override live RPC evidence.

## 2026-09-26 — Saturation conveyor lock
- The project now uses an autonomous evidence conveyor instead of requiring one manual Next for every small batch.
- GitHub scheduled execution is the heartbeat; the persistent checkpoint artifact stores task cursors and retry state.
- P2 remains a hard promotion gate, while P3-P10 evidence can be prepared in shadow mode.
- A task result never equals a stage-gate result. Promotion is controlled by explicit predicates.
- The conveyor never enables live execution or weakens two-endpoint evidence rules.
- P11 is closure and next-chain-unlock candidate only; a new chain is not started until Polygon saturation audit explicitly closes.

## 2026-09-26 — Conveyor correctness lock
- Automation cadence is now decoupled from repository commit cadence.
- Checkpoint artifacts carry task cursors and retry state; main commits represent only actual stage/gate transitions.
- Shadow discovery may continue while P2 is open, but shadow evidence never bypasses the P2 promotion gate.
- Stage completion is predicate-based, not file-existence-based.
- P10 must explicitly close before P11 can become READY.

## 2026-09-26 — Conveyor failure lesson lock
- A red automation workflow must be root-caused before increasing concurrency or adding more workers.
- Regression fixtures must reflect the exact evidence contract, including transport-level metadata required by reconciliation.
- Push-triggered autonomous conveyor runs are disabled to prevent a commit storm during active engineering; schedule/manual dispatch is the heartbeat.
- The conveyor's durable working set includes checkpoint state plus evidence and universe files. Losing the latter would invalidate multi-run saturation progress.
- Artifact restore errors are fail-closed; first-run absence of an artifact is the only permitted clean bootstrap case.
- Stage files are preparation artifacts. Promotion requires an explicit CLOSED gate marker.

## 2026-09-26 — New non-negotiable evidence rules
- `P2_PROVENANCE` status `REPLAYED` means independent observations plus exact match, not merely two successful RPC responses.
- Pair-universe counts are keyed by canonical `pairAddress`; discovery duplicates must never count as separate pairs.
- Saturation metrics must represent unique universe objects, not API observation rows.

## 2026-09-26 — Current execution checkpoint
- Canonical repository: `manish91082-coder/ghost-hunter-research-all-block-chains`.
- Current main HEAD after provenance repair + regression lock: `2c9426d9feb0ac1f8ba46de2ee0c18971bd72ad4`.
- Verified project execution model remains: live GitHub state is authoritative; CI/artifact evidence is required for promotion; no green-by-file-existence.
- Current blocker split: P2 control-function live quorum and P2 provenance semantic replay. P2 derived runtime-code is already VERIFIED.
- Provenance comparison now excludes provider identity from the semantic fingerprint while retaining provider identity in evidence metadata.

## 2026-09-26 — P2 control-function recovery checkpoint
- Current main HEAD: `b2fe8738b28ee77670edb7a72994fcd039c793bb`.
- Two independent P2 blocker repairs are now committed:
  1. provenance semantic fingerprint excludes provider transport identity;
  2. control-function head recovery continues until the selected quorum satisfies the existing stale-block tolerance.
- Both repairs have executable regression coverage.
- Corrected dedicated control-function CI run is `36180198453`, currently pending.
- A fresh conveyor run must be triggered from the corrected HEAD before P2 can be evaluated again.

## 2026-09-26 — Conveyor speed checkpoint
- Main HEAD: `798525a31e9f3486844acfc83653bb8c78f18e0c`.
- Critical P2 work is now content-aware and non-redundant across heartbeat rounds.
- Two independent critical tasks may execute per bounded run, while stage promotion remains fail-closed.


## 2026-09-26 — Current P2 execution checkpoint
- Main HEAD: `f418b3a58e9fb5b6f75b09f48eb80ebbe9e2d429`.
- P2 control-function artifact Run `36180198453` was independently inspected before repair.
- Ten apparent conflicts were decomposed: Tatum `-16401` provider entitlement errors and one malformed second-parent calldata pattern. These are not chain-state conflicts.
- Evidence classifier now excludes provider policy and malformed-request errors while retaining genuine EVM execution/revert evidence.
- Second-parent ProxyAdmin calldata was corrected.
- Corrected control-function CI run `36181173124` is queued on the latest HEAD.
- Do not promote P2 until the corrected artifact reports complete independent semantic evidence with zero unresolved conflicts.
- P2 provenance still needs a second independent observation for one candidate transaction.


## 2026-09-25 — P2 control-function semantic evidence recovery lock
- Canonical prior evidence remains Run `36181173124`, whose raw reconciliation was PARTIAL, not conflicting: 0 semantic conflicts, 17 probes, 8 probes without two semantic RPC observations.
- Tatum provider-policy `-16401` and malformed-request `-32602` must never satisfy an independent control-function evidence slot.
- The control verifier now has an explicit `semantic_probe_observation()` gate matching the repository's semantic evidence doctrine: successful HTTP-200 execution, EVM revert code 3, or execution-layer JSON-RPC codes `-32099..-32000` count; provider/request/transport failures do not.
- Recovery now honors the requested number of rounds and waits for cooled independent endpoints to re-enter before consuming a recovery pass.
- Repair commits are locked in main history: `b722866860fb2d3a919fd388eac38260a08d9383` followed by regression commit `357969627248bea4be97dff542fab0cde73deaa5`.
- Run #20 for the first repair was cancelled by concurrency when Run #21 arrived. Run #21 is the authoritative validation run for the combined repair+regression state.
- Never promote P2 from source validation. Promotion requires the completed Run #21 artifact, raw evidence inspection, reconciliation VERIFIED, and separate P2 provenance REPLAYED evidence.
