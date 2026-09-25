# Project Progress

## 2026-09-25 — Foundation Freeze
### Added
- Canonical project constitution.
- Architecture and scanner doctrine.
- Zero-cost-first operating model.
- Chain-wise research/data model.
- Continuity and auto-save protocol.
- Status, progress, memory and decision ledgers.
- Research evidence structure.
- GitHub governance state record.
- Chain research registry and reusable chain template.

## 2026-09-25 — Polygon Saturation Track Locked

### Scope
- Polygon PoS Mainnet only.
- Chain ID 137.
- No other blockchain research until Polygon saturation gate closes.
- Research repository remains manish91082-coder/ghost-hunter-research-all-block-chains.

### Completed
- Polygon evidence track folder.
- Polygon base profile.
- Static-data saturation checklist.
- Polygon saturation research plan.
- Explicit pre-transaction data requirements.
- Evidence-state discipline: VERIFIED / PARTIAL / HISTORICAL / UNVERIFIED / CONFLICTED / STALE / DEPRECATED.
- No guaranteed-profit claim policy. Economic certification must use exact state, costs and simulation.
- Polygon RPC evidence model with official public-RPC discovery list.
- Polygon block/timing/finality evidence model.
- Recent mainnet protocol-generation evidence recorded.
- Polygon system/bridge contract discovery census with documented addresses.
- Upgradeability/proxy/control-surface research requirements.

### Important evidence discipline
Documented addresses are not yet marked VERIFIED. Live chain-137 bytecode, proxy implementation, creation and behavior checks remain mandatory.

### Current verification limitation
The research environment does not currently execute direct JSON-RPC POST calls. Therefore live bytecode and latest-state values are not fabricated.

### Next gate
P1 continuation:
1. live-verify documented Polygon system/bridge addresses;
2. discover remaining bridge/state-sync contracts;
3. capture bytecode and proxy implementation evidence;
4. build machine-readable address registry;
5. only after the chain infrastructure layer is verified, start DEX/protocol discovery.

### Git Verification
Repository and branch remain locked to:
- manish91082-coder/ghost-hunter-research-all-block-chains
- main

### Rule
Each future milestone must update this file, PROJECT_STATUS.md and the relevant Polygon research/evidence files in the same project progression.


## 2026-09-25 — Polygon Bridge/State-Sync Registry Step

### Added
- `chains/polygon-pos/ADDRESS_REGISTRY.md` as the canonical discovery-layer address registry.
- `chains/polygon-pos/BRIDGE_STATE_SYNC.md` separating PoS Portal, Fx Portal and application-layer state-sync consumers.
- Documented bridge/state-sync opportunity hypotheses without treating them as profitable or execution-ready.
- Explicit verification schema for code, runtime hash, proxy/implementation, creation evidence, behavior probes and observation block.

### Evidence result
- Authoritative Polygon security-scope evidence confirms the published core PoS deployed-address set.
- Official Fx Portal evidence confirms the FxRoot/FxChild deployment surface.
- A new Polygon sPOL surface was recorded as an application-layer state-sync consumer, not conflated with the core bridge.
- No new object was promoted to VERIFIED because live chain-137 JSON-RPC verification remains unavailable in the current environment.

### Gate state
- Polygon saturation gate remains OPEN.
- DEX/protocol discovery remains blocked until the chain infrastructure and bridge/state-sync layer is sufficiently reconciled.
- Next atomic step: expand the bridge/predicate/exit/withdrawal/control census and prepare the live-verification batch without fabricating runtime state.

### Git verification
- Pre-write HEAD: `2c318960675c8bc29ff0434a2e5b1d2b5631d1ef`.
- Canonical repository: `manish91082-coder/ghost-hunter-research-all-block-chains`.
- Canonical branch: `main`.


## 2026-09-25 — Polygon Bridge Predicate Census Expansion

### Added
- Expanded the Polygon address registry with Mintable ERC20/ERC721/ERC1155 predicate proxies, EtherPredicateProxy and ChainExitERC1155Predicate.
- Added Plasma-era DepositManagerProxy, WithdrawManagerProxy, EventsHubProxy, RootChain and StakeManager candidates for current-vs-historical classification.
- Updated bridge/state-sync documentation to explicitly separate discovery evidence from live verification.

### Evidence result
Polygon's current published security scope lists the core deployed PoS/Plasma contract addresses, while PIP-54 documents additional predicate proxies and control/upgrade surfaces. These sources expand discovery coverage but do not replace live chain verification. 

### Gate state
- Polygon saturation gate remains OPEN.
- No newly discovered address is VERIFIED.
- DEX discovery remains blocked while bridge/state-sync and infrastructure classification is incomplete.

### Next atomic step
Build the live-verification batch specification for the expanded registry: exact RPC calls, proxy-slot checks, bytecode hashing, ABI/function probes, creation evidence, and reproducible evidence records. Do not fabricate live results.


## 2026-09-25 — Polygon Live Verification Batch Specification

### Added
- `chains/polygon-pos/LIVE_VERIFICATION_BATCH.md`
- Read-only verification protocol covering chain identity, code hash, proxy slots, implementation, roles, creation evidence, event probes and cross-RPC consistency.
- Explicit state-transition rules for VERIFIED / PARTIAL / CONFLICTED / HISTORICAL / DEPRECATED / UNVERIFIED.
- Zero-cost-first, resumable, evidence-hash based batch design.

### Research update
- Polygon control-plane discovery was expanded with RootSetter and GovernanceProxy references.
- PIP-54 governance/control evidence is now explicitly separated from current on-chain role state.
- PIP-86 confirms Polygon's 2026 block-time reduction program, reinforcing that current timing must be measured rather than inherited from old documentation. [Polygon PIP-86](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/main/PIPs/PIP-86.md).

### Gate state
- Polygon saturation gate remains OPEN.
- The next execution-capable step is to run the read-only verification batch in an environment with direct JSON-RPC POST access.
- No address has been promoted to VERIFIED in this repository.

### Next atomic step
Prepare the verifier implementation contract/schema and endpoint capability matrix, then execute it only in a permitted live-RPC environment. DEX discovery remains blocked until critical infrastructure verification is complete.


## 2026-09-25 — Polygon Discovery Baseline + Governance Freshness Step

### Added
- Expanded address registry with Polygon security-scope Plasma/PoS discovery objects: Registry, ValidatorShare, Plasma predicates, Plasma EIP1559Burn and Ethereum MaticToken.
- Strengthened live-verification specification with governance-freshness and current-vs-historical classification.
- Explicitly separated published PIP/security evidence from observed on-chain ownership, roles and proxy state.

### Evidence result
The official Polygon security scope publishes the deployed contract census, while PIP-54 describes upgradeability/control responsibilities. These are discovery and governance evidence layers; current runtime ownership still requires on-chain verification. citeturn0search2turn0search1

### Gate state
- Polygon saturation gate remains OPEN.
- Bridge/system discovery baseline is substantially expanded.
- No address is promoted to VERIFIED without live chain-137 evidence.
- DEX discovery remains blocked pending live verification and reconciliation.

### Next atomic step
Implement the read-only verifier schema/output contract and endpoint capability matrix so the same batch can run from Colab or another permitted JSON-RPC environment without changing the evidence model.


## 2026-09-25 — Polygon RPC Capability Matrix

Added `chains/polygon-pos/RPC_CAPABILITY_MATRIX.md` defining the deterministic, read-only capability probe order, endpoint classification, cross-RPC quorum, historical-state handling, zero-cost/resumable profile, safety boundary, and P1 acceptance gate. Official Polygon Bor documents optional trace support with archive-node requirements, while Polygon tooling documents standard JSON-RPC probes. Live endpoint results remain intentionally unclaimed until the verifier runs in a permitted JSON-RPC environment.

### Next atomic step
Build the machine-readable verifier output schema and Colab runner contract, then execute only read-only probes against independent Polygon RPC endpoints. DEX discovery remains blocked until P1 passes.

## 2026-09-25 — Machine-readable verifier contract

Added `polygon-verification-record.schema.json` and `COLAB_VERIFIER_RUNNER.md`. The schema fixes the evidence record shape, while the runner contract defines deterministic read-only probing, method allowlisting, secret exclusion, bounded retries, resumable checkpoints, SHA-256 normalization, cross-RPC reconciliation, and P1 acceptance criteria. Official Bor documentation confirms trace APIs are optional and archive-node dependent, reinforcing capability measurement rather than assumption. citeturn0search0

### Next atomic step
Implement the actual Colab-ready verifier script against this contract, with only read-only JSON-RPC methods and no credentials embedded. Then run it in an environment that permits outbound JSON-RPC POST and bring the resulting evidence artifacts back into the canonical repository.

## 2026-09-25 — First Colab-ready read-only verifier implementation

Added `chains/polygon-pos/polygon_readonly_verifier.py`. It implements the first deterministic, dependency-light JSON-RPC probe runner: explicit read-only allowlist, hard denylist for transaction/signing methods, endpoint-by-endpoint identity/head/gas probes, normalized SHA-256 result hashes, append-only JSONL observations, and resumable checkpoints. It is intentionally limited to capability probes in this milestone; address/proxy/role verification remains a subsequent batch. Official Bor documents the underlying RPC/trace architecture and archive requirements. citeturn0search0turn0search5

### Execution status
The script is committed but has **not** been run against live Polygon RPCs from this environment. No live result, endpoint health score, current block, or address has been promoted to VERIFIED.

### Next atomic step
Run the verifier in a permitted outbound-JSON-RPC environment with multiple independent Polygon endpoints, capture the raw evidence artifacts, reconcile chain/head results, then expand into address-level code/proxy/control probes.

## 2026-09-25 — Verifier hardening checkpoint

Hardened `polygon_readonly_verifier.py` before any live run: HTTPS-only endpoint guard, embedded-credential rejection, explicit read-only allowlist/transaction denylist, bounded retries with recorded failures, address-level `eth_getCode` probes, resumable per-probe checkpoint state, and cross-RPC head-staleness summary generation.

A connector-side static integrity check confirmed all required safety/probing guards are present. Full Python execution and live JSON-RPC POST remain unavailable in this environment, so no live Polygon result is claimed.

Official Bor documentation confirms that trace APIs are optional and archive-node dependent; therefore trace remains a separately measured capability rather than a universal endpoint requirement. citeturn635553search0

### Gate decision
The verifier implementation is now ready for external live execution. The Polygon P1 gate is **not passed yet** because live multi-RPC evidence has not been captured.

### Next atomic step
Run the hardened verifier from an outbound JSON-RPC environment against independent Polygon endpoints, then ingest the resulting head/code evidence into the canonical registry. Do not start DEX discovery until the P1 gate passes.

## 2026-09-25 — P1 identity quorum hardening

The live verifier now records every observed RPC chain ID and enforces the Polygon P1 identity rule: independent endpoints must unanimously report chain ID 137 before the run can proceed as a successful P1 identity probe. It also preserves the freshest-block/stale-endpoint summary and address code probes.

A static integrity check of the committed verifier confirmed the chain quorum, stale-head tracking, read-only denylist, checkpoint, and address-probe paths are present.

Live RPC execution is still pending. The GitHub workflow exists and is configured for push/manual execution, but the available GitHub connector does not expose push-triggered workflow runs, so no run result is being inferred or claimed.

Official Polygon JSON-RPC tooling documents the same core probe family: net_version, eth_blockNumber, eth_getBlockByNumber and eth_getCode. citeturn0search3turn0search0

### Next atomic step
Use the GitHub-hosted runner as the primary live execution path. If its run output becomes accessible, capture and verify artifacts. If runner/network policy prevents live RPC, fall back to a user-run Colab/laptop execution without changing the verifier or evidence schema.
## 2026-09-25 — GitHub P1 verification execution wiring

### Added
- Added `chains/polygon-pos/verification_targets.txt` with a bounded, Polygon-side critical system-contract target set for the first live read-only code-verification pass.
- Updated `.github/workflows/polygon-readonly-verification.yml` so the GitHub-hosted runner performs a Python syntax check and then passes the canonical target file to the hardened verifier.
- Kept the target set bounded and Polygon-side only. Ethereum-side governance/bridge objects remain separately classified and are not mixed into this first chain-137 code pass.

### Safety/evidence rule
- The workflow remains read-only and uses the verifier's HTTPS-only endpoint guard and RPC method allowlist.
- No transaction submission, signing, credentials, or mutation capability was added.
- The workflow still does not constitute a successful live verification until its actual run output/artifacts are observed and reconciled.

### Gate state
- Polygon saturation gate: OPEN.
- P1 live verification: NOT PASSED yet.
- DEX/protocol discovery: still blocked by the infrastructure gate.

### Next atomic step
Observe the GitHub-hosted run and, if artifacts become accessible, reconcile chain identity, head freshness, and per-target code hashes across independent RPCs. Any disagreement remains unresolved/quarantined rather than majority-selected.


## 2026-09-25 — Verification input hardening

### Added
- Hardened the read-only verifier with strict EVM address validation before any RPC call.
- Updated the GitHub Actions path trigger to rerun when the canonical verification target file changes.
- Rechecked the workflow remains read-only and the target list remains bounded to Polygon-side critical addresses.

### Gate state
- P1 live verification: NOT PASSED until an actual GitHub runner result/artifact is observed and reconciled.
- Polygon saturation gate: OPEN.

### Next atomic step
Obtain/observe the actual GitHub Actions execution evidence. If the connector still cannot expose push-triggered runs, use an explicit workflow-dispatch-capable GitHub action if available; otherwise use the same verifier unchanged in a permitted outbound-RPC environment. No DEX expansion before P1 reconciliation.


## 2026-09-25 — Automated evidence reconciliation

### Added
- Added `chains/polygon-pos/polygon_verification_reconciliation.py` to deterministically reconcile verifier output without majority-selecting conflicting RPC observations.
- GitHub Actions now runs the reconciler after the read-only verifier, even when the verifier exits non-zero, and uploads the reconciliation artifact.
- The reconciliation layer checks chain-identity agreement from the head summary, per-address code-hash agreement, conflicts, stale endpoints, and an evidence-state classification.

### Gate state
- P1 remains NOT PASSED until an actual runner artifact is observed and independently inspected.
- No RPC disagreement is silently resolved by majority vote.
- Polygon saturation remains OPEN and DEX discovery remains blocked.

### Next atomic step
Observe the GitHub execution/artifacts and use the reconciliation artifact as the first machine-readable P1 decision input.


## 2026-09-25 — CI command-path normalization

The Polygon verification workflow was rewritten with explicit YAML block-scalar command lines and separate validation/execution steps. This removes ambiguity from command concatenation in the stored workflow representation and keeps verifier failure separate from reconciliation execution.

### Gate state
- P1 live evidence: NOT PASSED.
- No runner result is inferred from configuration.
- Polygon saturation remains OPEN.

### Next atomic step
Observe actual workflow artifacts/run output. If unavailable through the connector, use the unchanged verifier in a permitted outbound-RPC environment rather than changing evidence semantics.


## 2026-09-25 — GitHub live-run artifact audit

### Actual evidence captured
- Workflow run `36155696574` executed from main commit `cf4f955efebb797068e5e902c727c1864a1e2f72` and completed successfully.
- Artifact `polygon-readonly-verification` was retrieved and inspected directly.
- The verifier checkpoint records **51 failed probes** across the three configured RPC endpoints.
- The raw JSONL observations show HTTP 403 Forbidden from all three endpoints for chain ID, head, gas and all 11 target `eth_getCode` probes.
- Reconciliation output is `PARTIAL`; no chain-ID quorum, no head agreement, and no successful target code observations exist.

### Critical finding
The prior verifier could return exit code 0 when every RPC probe failed because it only rejected a non-empty but incorrect chain-ID observation set. This created a false-green CI result even though the artifact correctly showed no live evidence.

### Correction committed
- `1d6a3ae20417e32450da7b162b605a6f053dddd4`: fail-closed verifier quorum. Success now requires >=2 successful independent chain-ID observations, unanimous 137, >=2 successful block observations, and exact latest-block agreement.
- `8fd9d0699b64aaf610905edb13b5a8927b518f49`: hardened reconciliation. VERIFIED now requires exact target-set coverage, >=2 successful independent code observations for every target, matching hashes, chain-ID quorum, and head agreement.

### Gate state
- P1 live verification: **NOT PASSED**.
- Polygon saturation gate: **OPEN**.
- DEX/protocol discovery remains blocked.
- The next GitHub Actions run is an evidence-quality test: continued RPC 403s should now produce a **failed** workflow instead of a false green.

### Next atomic step
Inspect the post-hardening GitHub Actions run. If the public endpoints still return 403, classify them as inaccessible from GitHub-hosted runner context and switch the same unchanged verifier to another permitted outbound-JSON-RPC environment or replace the endpoint set with independently reachable public endpoints. Do not weaken the evidence gate.


## 2026-09-25 — CI RPC pool rotation

### Evidence
- Fail-closed Run 10 (`36157003942`) completed with failure because all three prior RPC endpoints returned HTTP 403 from the GitHub-hosted runner and produced no usable chain/head/code evidence.
- The failure is now correctly classified as infrastructure access failure rather than verification success.

### Action
- Rotated the GitHub Actions probe pool to Tenderly public, Nodies public, and OnFinality public Polygon endpoints, all listed by Polygon's current RPC documentation as public options. citeturn2view0
- No evidence threshold was weakened and no target was promoted to VERIFIED.

### Next atomic step
Observe the new push-triggered run and inspect its artifact. If the new pool is also inaccessible from GitHub-hosted runners, stop rotating blindly and move the unchanged verifier to another permitted outbound-RPC execution environment, while retaining every failure as evidence.

## 2026-09-25 — Run #13 progress
- Fixed the parallel-verifier JSONL/checkpoint serialization defect in commit `84fadf926ee9cd96c3b2b0a228458ebb28d9b1a8`.
- CI Run #13 `36164386940` produced a structurally valid evidence artifact: 51 JSONL records parsed successfully with real line boundaries.
- P1 still fails closed because only one independent RPC supplied chain/head evidence and only 4/11 critical targets had successful code observations from that single endpoint.
- This separates the problem into two resolved/open tracks: **serialization defect = resolved; independent RPC evidence coverage = unresolved**.
- No quorum rule, target coverage rule, or safety gate was relaxed.

## 2026-09-25 — P1 RPC access path isolated
- Runs #18 through #21 tested public Tatum pacing at 0.5s, 1s, 2s and 3s intervals. Tatum remained HTTP 429-limited during the address-code phase; the result improved with pacing but did not reach 11/11 independent code observations.
- Run #23 confirms head quorum is now correctly tolerant to a one-block tip difference while both endpoints are fresh and within the configured tolerance. Chain ID agreement is true and head agreement is true, but reconciliation remains PARTIAL because Tatum code coverage is incomplete.
- Current engineering path: use the same free public Tatum endpoint with an optional free Tatum API key supplied only through GitHub Actions secret `TATUM_API_KEY`. QuickNode remains the second independent endpoint. No key is stored in source, artifacts or chat.
- P1 remains NOT PASSED until 11/11 target code observations are independently matched across both endpoints.

## 2026-09-25 — Adaptive Polygon RPC rotation
### Added
- Added `chains/polygon-pos/rpc_pool.txt` with the known Polygon public RPC candidate pool gathered during runner reconnaissance.
- Reworked `polygon_readonly_verifier.py` into a request-level adaptive rotation model:
  - full-pool identity/head discovery first;
  - chain-137 eligibility before code probing;
  - per-endpoint pacing;
  - failure counters and cooldowns;
  - HTTP 429 `Retry-After` handling;
  - address-level rotation across eligible RPCs;
  - minimum two distinct successful code endpoints per critical target.
- Updated GitHub Actions to consume the canonical RPC pool and preserve the existing fail-closed reconciliation gate.
- Corrected head gating so the verifier and reconciliation use the configured stale-block tolerance consistently.

### Evidence discipline
- RPC pool membership is candidate status only.
- A failed/limited endpoint is recorded as evidence and skipped temporarily, not silently treated as trustworthy.
- Conflicting code hashes remain conflicts. No majority vote is used.
- P1 does not pass merely because rotation found one working endpoint.

### Current gate
- P1 live verification: **NOT PASSED** until the adaptive-pool run produces two independent matching code observations for every critical target.
- No DEX/protocol expansion before P1 passes.
## 2026-09-25 — Adaptive rotation live-run result and serializer correction
### Run #26
- Adaptive rotation executed successfully at the verifier layer.
- Chain/head quorum found OnFinality and QuickNode public at chain 137, with a one-block head span.
- Several of the 11 critical targets reached two independent successful code endpoints.
- Remaining targets had only one successful endpoint because the other eligible provider was rate-limited or unavailable for those calls.

### Defect found
- The rotation rewrite omitted the top-level method field from each evidence record.
- The raw JSONL contained the observations, but the reconciliation reader could not classify them by method and reported zero code observations.
- Commit bcdd68f7b662c20f247062be326b72656513d97e restores the canonical top-level field.

### Gate state
- Rotation architecture: PROVEN WORKING at live-run level.
- Evidence reconciliation: pending corrected run.
- P1: NOT PASSED.
## 2026-09-25 — RPC cooldown recovery hardening
- Added adaptive per-endpoint pacing: successful endpoints slowly return toward the configured base interval; HTTP 429 doubles the local interval up to a bounded cap.
- Added a bounded second address-code recovery pass after cooldown, allowing temporarily rate-limited providers to re-enter rotation.
- CI base pacing changed to 1.0 second per endpoint and recovery rounds fixed at 2.
- No evidence threshold changed: every target still needs two distinct successful RPC endpoints with matching code hashes.

## 2026-09-25 — Polygon P1 PASSED: Run #30

- Adaptive 14-endpoint RPC pool established 3 live Polygon identity/head endpoints.
- Run `36169503083` completed successfully.
- All three head endpoints reported chain ID 137 and block 94,435,638.
- All 11 canonical P1 targets received at least two independent successful `eth_getCode` observations.
- Runtime-code hashes matched for every target.
- Reconciliation: `evidence_state = VERIFIED`.
- Artifact: `10879647689`, digest `sha256:bc53e3255ac12c2e99d62a5ef189c60fe26f1deb6e1c67178f043cc296546bbe`.

### Gate decision
**P1 PASSED.** The bounded targets move to PARTIAL, preserving unresolved control/proxy/behavior fields. Next atomic work is P2 address/control/bridge census.

## 2026-09-25 — P2 control-plane probe launched
### Added
- `chains/polygon-pos/p2_control_targets.txt`
- `chains/polygon-pos/polygon_p2_control_verifier.py`
- `chains/polygon-pos/polygon_p2_control_reconciliation.py`
- `.github/workflows/polygon-p2-control-verification.yml`

### Scope
The first P2 slice reads the three ERC-1967 storage locations per critical Polygon target:
- implementation;
- admin;
- beacon.

Each result is captured across the dynamically eligible Polygon RPC pool and reconciled without majority selection. The standard defines these storage slots for proxy metadata. citeturn422867search0

### Execution
Run `36170466071` is **IN_PROGRESS**. P2 is not declared passed until the artifact is inspected and reconciliation returns VERIFIED.

## 2026-09-25 — P2 allowlist defect corrected
### Run #1 result
- P2 workflow `36170466071` reached source validation successfully.
- Execution failed on `ValueError: Method not allowed: eth_getStorageAt`.
- Reconciliation had no input artifact, so P2 was not advanced.
### Correction
- Added `eth_getStorageAt` to the shared read-only RPC allowlist.
- This method is read-only and is required for ERC-1967 implementation/admin/beacon storage-slot inspection.
- Corrected P2 run `36170624761` is executing against the fixed source.

## 2026-09-25 — P2 Run #2 evidence and recovery hardening
### Run #2
- Workflow run `36170624761`
- Artifact `10879519912`
- Artifact digest: `sha256:575377544f0a9ebb17cf080fc3f4a0db0909812793ba9198e3bbe836a684bfd9`
- 66 records = 33 expected target/slot combinations × 2 attempted endpoints.
- QuickNode: 33/33 success.
- Tatum: 16/33 success, 17/33 HTTP 429.
- P2 reconciliation: PARTIAL.
- No conflicts in the successful dual observations.

### Correction
- P2 now rotates at target/slot granularity instead of probing one entire endpoint serially.
- Rate-limited endpoints receive cooldown and can re-enter through bounded recovery rounds.
- Storage eligibility is based on fresh chain-137 identity; two fresh head endpoints are still required for the P2 gate.
- Workflow now enables two recovery rounds.

P2 remains NOT PASSED until every target/slot combination has two independent matching observations.
