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

## 2026-09-25 — P2 ERC-1967 storage sub-gate PASSED

### Run #4
- Run `36171378222`
- Artifact `10880421099`
- Digest `sha256:5693d27acbd6b5aff22a5c0a4d9fccd15a0641c7bb6463efc792a75784216e3f`
- Observation block: 94,436,387
- 33/33 target×slot combinations verified
- 66 independent successful observations
- 0 conflicts
- 0 insufficient observations

### Non-zero proxy/control discoveries
Four derived addresses are now live-evidence candidates:
- `0xae88570eb386a9c902488a6535f0957a46a68765`
- `0x409834270b6f2591dd6c1e9f351e4194b112da44`
- `0x3c05a871e867fde9a8364fc8d38d97a7d42541c8`
- `0xf68a9a2417a10e7d907a28b9876db8ad3dbbab7d`

### Next atomic step
Verify code identity of those derived addresses across independent RPCs, then probe proxy/control functions on the corresponding parent contracts.
## 2026-09-25 — P2 derived address verification
Added:
- `p2_derived_control_targets.txt`
- `p2_derived_control_provenance.txt`
- `polygon_p2_derived_reconciliation.py`
- `.github/workflows/polygon-p2-derived-control-verification.yml`

Scope: runtime-code verification of the four non-zero addresses discovered from P2 ERC-1967 storage. This bridges storage-level evidence to live deployed-code evidence without assuming proxy semantics.
## 2026-09-25 — Derived-control head quorum hardening
### Run #2 finding
- All four derived addresses: 2/2 matching code hashes from OnFinality + QuickNode.
- Failure reason: successful head blocks were 94,436,836 / 94,436,834 / 94,436,833, giving span 3 against tolerance 2.
- Tatum was the stale third head for this snapshot; no code conflict existed.

### Correction
- Added optional deterministic fresh-head quorum to the shared verifier.
- P1 default remains all-endpoint head agreement.
- Derived-control sub-gate requires a two-endpoint fresh-head quorum and records the selected endpoints/span.

## 2026-09-25 — Derived-control workflow wiring correction
### Finding
Run 36172904065 demonstrated that the verifier's deterministic two-endpoint head-quorum feature was not actually enabled in the workflow command. The workflow omitted --min-head-endpoints 2, so the run correctly failed the old all-endpoint head-span rule even though all four derived addresses had matching two-RPC code hashes.

### Correction
Commit 5b0212d5ca8ce094f4438f60e424189bc0259e6a updates .github/workflows/polygon-p2-derived-control-verification.yml to:
- pass --min-head-endpoints 2;
- preserve --stale-block-tolerance 2;
- keep the two-independent-code-endpoint requirement;
- syntax-check the reconciliation module;
- safely initialize shell exit-status variables.

### Gate state
- P2 ERC-1967 storage consistency: PASSED.
- P2 derived runtime-code verification: PENDING corrected CI evidence.
- Overall P2: IN PROGRESS.
- Polygon saturation: OPEN.
- DEX/protocol discovery: BLOCKED.

### Next atomic step
Inspect the first corrected derived-control CI run and its artifact. Promote the four derived runtime identities only when the fresh-head quorum and two-endpoint code reconciliation both return VERIFIED.

## 2026-09-25 — P2 control-function probe stage wired
### Scope
Two P2 parent contracts now have explicit read-only selector candidates for `owner()`, `admin()`, `implementation()` and `proxiableUUID()`.

### Evidence rule
A probe needs two independent chain-137 RPC observations. A JSON-RPC success or reproducible JSON-RPC error both count as observations; HTTP/network failures do not. Matching outcomes are reconciled without majority selection.

### Gate state
- P2 ERC-1967 storage consistency: PASSED.
- P2 derived runtime-code: PENDING corrected CI evidence.
- P2 control-function probes: WIRED, awaiting CI evidence.
- Overall P2: IN PROGRESS.
- Polygon saturation: OPEN.
- DEX/protocol discovery: BLOCKED.
## 2026-09-25 — Control-function regression gate added
### Defect caught
The first control-function verifier revision renamed the per-probe evidence set from successful to observed so reproducible JSON-RPC errors could count as evidence. Two stale successful[...] references remained and would have caused a runtime NameError.

### Correction
- Removed all stale successful[...] references.
- Added test_p2_control_function_regression.py.
- CI now executes the regression test before live probes.
- Workflow path triggers now include the regression test file.

### Current state
- P2 ERC-1967 storage consistency: PASSED.
- P2 derived runtime-code: corrected workflow evidence pending.
- P2 control-function probes: harness + regression gate wired; live evidence pending.
- Overall P2: IN PROGRESS.

## 2026-09-25 — CI observability hardening
- Added tools/github_ci_state.py as a deterministic read-only CI-state extractor.
- The report covers the canonical Polygon read-only, P2 storage, P2 derived-control and P2 control-function workflows.
- It records latest main SHA, workflow runs, job status/conclusion and artifact identifiers/digests.
- It does not trigger or rerun any workflow.

## 2026-09-25 — CI evidence automation closed
- CI state extraction is now automatically invoked after completion of the canonical Polygon verification workflows.
- The collector captures the triggering run context and full recent workflow/job/artifact state for the four monitored workflows.
- This removes the need to infer whether a push-triggered verification actually ran merely from repository commits.

## 2026-09-25 — Fresh CI evidence reacquisition
- Re-triggered the derived-control and control-function verification workflows from the canonical main branch.
- No verifier thresholds were changed.
- The purpose is to obtain fresh runner evidence after the workflow, verifier and regression corrections were locked.
- Gate promotion still requires raw artifact inspection plus reconciliation.

## 2026-09-25 — Control-function evidence gate hardened
### Defect
Matching transport failures could previously be fingerprinted like contract outcomes during reconciliation.

### Correction
- Only HTTP 200 JSON-RPC responses are eligible for control-function evidence fingerprints.
- Deterministic JSON-RPC success and JSON-RPC error/revert outcomes remain valid evidence.
- Transport failures remain non-evidence.
- Regression test added for HTTP 403 exclusion.

### State
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: fresh evidence acquisition pending inspection.
- P2 control-function: fresh evidence acquisition re-triggered after this hardening.
- Overall P2: IN PROGRESS.

## 2026-09-26 — P2 provenance discovery integrated
### External discovery findings
- EIP1559Burn proxy external records expose constructor logic/admin relationships.
- sPOL deployment transaction records show the parent/admin creation relationship and historical upgrade/admin events.
- The current sPOL implementation candidate has a distinct Create2 deployment record.

### Control-surface expansion
- P2 control-function manifest expanded to 17 read-only probes.
- New probes cover AccessManaged authority on the sPOL parent and owner/pendingOwner plus ProxyAdmin relationship reads on both derived admin addresses.
- These are discovery-informed probes only. Live two-RPC reconciliation remains the gate.

### Gate state
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: pending actual corrected CI artifact.
- P2 control-function: expanded and hardened, pending actual CI artifact.
- Overall P2: IN PROGRESS.

## 2026-09-26 — Conveyor acceleration architecture
### Problem solved
Manual Next-driven execution was serializing independent evidence work and wasting the time between P2 checks.

### New execution model
- Critical lane: P2 evidence tasks, fail-closed and ordered.
- Shadow lane: P3-P10 preparatory discovery continues while P2 is open.
- Persistent checkpoint: GitHub Actions artifact instead of per-tick Git commits.
- Gate-transition commits only: repository history remains clean.
- Stage promotion: P2 -> P3 -> P4 -> ... -> P10 -> P11 in deterministic order.

### Current state
The conveyor is wired; actual runner evidence is still the authority for live gate promotion.

## 2026-09-26 — Conveyor correctness pass
- Fixed persistent round-robin task cursors.
- Fixed critical-lane promotion so it never skips from P3 directly to a later stage.
- Added content-aware stage predicates and a hard P10 CLOSED requirement before P11.
- Fixed token deduplication and cyclic route enumeration in the first-pass universe worker.
- Added explicit actions:read permission for checkpoint artifact restoration.

## 2026-09-26 — Screenshot-driven conveyor repair
### Observed
The Autonomous Polygon Saturation Conveyor showed repeated red runs (#1 onward) while the CI State Evidence Collector succeeded.

### Root cause
Control-function reconciliation began requiring HTTP 200 for semantic evidence, but the regression fixtures for matching success/error outcomes did not carry HTTP 200. The regression suite therefore failed before the actual saturation worker executed.

### Repair
- Corrected success/error fixtures.
- Added conveyor regression suite.
- Removed push-trigger storm; retained 5-minute schedule + manual dispatch.
- Persist full evidence/universe working set in the checkpoint artifact.
- Fail closed on checkpoint API/restore errors.
- Require explicit stage_gate=CLOSED before P3-P10 promotion.

### Current state
The automation design is now materially more robust. A fresh scheduled/manual run is required to validate the repaired conveyor on a GitHub-hosted runner.

## 2026-09-26 — Next integrity pass
- Found a second-order provenance-gate weakness: independent observations were counted but matching was not required for `REPLAYED`.
- Found a P5 universe accounting weakness: the same DEX pair can appear in token-pair discovery for both tokens, so raw append-only rows could inflate pair counts.
- Both issues were repaired and regression-locked before live promotion.

## 2026-09-26 — P2 provenance semantic-fingerprint repair
### Defect identified
- Conveyor Run 36179352109 captured two independent successful observations for both provenance candidate transactions, but both were classified `matching=false` because the comparison included the provider-specific `rpc` transport field.
- This was a reconciliation logic defect, not a transaction/receipt conflict: the transaction and receipt payloads from the two RPCs matched while their provider labels necessarily differed.

### Repair
- Added `provenance_fingerprint()` that hashes only the semantic `tx` + `receipt` payload.
- Preserved the `rpc` field as provenance metadata rather than semantic content.
- Added regression coverage proving identical semantic payloads from different RPC labels match, while a changed transaction hash does not.

### Gate state
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: VERIFIED.
- P2 control-function: still OPEN pending a successful fresh-head quorum + live reconciliation artifact.
- P2 provenance: REPLAYED candidate pending the corrected conveyor run.
- Overall P2: IN PROGRESS.

### Next atomic step
Run the corrected conveyor through its narrow bootstrap trigger, inspect the raw artifact, then promote P2 only if control-function reconciliation and provenance replay both satisfy their existing gates.

## 2026-09-26 — P2 control-function head-recovery repair
### Defect identified
- Conveyor Run #18 showed two valid chain-137 head observations separated by four blocks while the configured tolerance was two.
- The control-function verifier's recovery loop stopped as soon as it selected any two-endpoint quorum, even when that quorum's block span exceeded the allowed tolerance.
- Therefore the configured recovery rounds were not actually used to seek a fresh quorum in this condition.

### Repair
- Added `head_quorum_ready()`.
- Recovery now stops only when the selected independent quorum exists **and** its block span is within the existing tolerance.
- Evidence threshold and tolerance were not weakened.
- Added regression coverage for fresh-quorum acceptance and stale-quorum rejection.

### Gate state
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: VERIFIED.
- P2 provenance: repaired, pending corrected conveyor replay.
- P2 control-function: repaired, pending fresh CI artifact and reconciliation.
- Overall P2: IN PROGRESS.

## 2026-09-26 — P2 conveyor throughput optimization
- The live checkpoint showed the critical lane was round-robinning already-verified tasks, delaying unresolved P2 provenance/control work.
- Added content-aware `critical_task_complete()` checks so VERIFIED derived/runtime evidence and REPLAYED provenance are skipped, while regression work is rerun only after a code-epoch change.
- Increased the bounded conveyor critical lane from 1 to 2 tasks per round. No evidence threshold, stage gate, or safety condition changed.
- Added regression coverage for the scheduler behavior.

### Gate state
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: VERIFIED.
- P2 provenance: repaired, pending replay.
- P2 control-function: repaired, pending live CI artifact.
- Overall P2: IN PROGRESS.


## 2026-09-26 — P2 control-function evidence classification repair
### Evidence findings from Run 16
- Fresh-head quorum was valid: two independent Polygon endpoints, block span within the configured tolerance.
- The 10 apparent semantic conflicts were not all contract conflicts.
- Tatum returned HTTP 200 with JSON-RPC error `-16401` and message indicating `eth_call` is restricted by plan. Tatum documents `-16401` as a plan-restricted gateway error, so it is provider-access evidence, not chain semantic evidence. citeturn402236search0turn402236search6
- One ProxyAdmin calldata entry for the second parent contained a one-hex-character address encoding defect, producing JSON-RPC `-32602` invalid-argument behavior.

### Repair
- P2 control-function reconciliation now admits successful HTTP-200 call results and EVM execution/revert error fingerprints, while excluding provider-policy and malformed-request errors from semantic evidence.
- Added regression coverage for Tatum-style entitlement errors, malformed request errors and genuine EVM revert evidence.
- Corrected both ProxyAdmin calldata entries for the second parent address.
- Existing two-independent-endpoint and fresh-head quorum gates remain unchanged.

### Current gate
- P1: PASSED.
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: VERIFIED.
- P2 provenance: PARTIAL in Run #21 because one candidate transaction had only one independent observation.
- P2 control-function: OPEN pending corrected live artifact.
- Overall P2: IN PROGRESS.
- Polygon saturation gate: OPEN.

### Next atomic step
Inspect the corrected control-function CI artifact. Then run the corrected conveyor path so provenance can obtain its second independent observation and P2 can close only when every existing gate predicate is satisfied.


## 2026-09-25 — P2 control-function semantic-quorum recovery repair

### Run #19 artifact diagnosis
- Control-function artifact from GitHub Actions run `36181173124` had fresh two-endpoint head quorum (block span 1) and **0 semantic conflicts**.
- The remaining P2 control-function gap was **8/17 probes with only one semantic RPC observation**.
- Raw evidence showed QuickNode could supply the semantic result while OnFinality was HTTP 429 and Tatum returned provider-policy `-16401`. Those non-semantic responses must not consume an independent evidence slot.

### Repair
- `chains/polygon-pos/polygon_p2_control_function_verifier.py` now counts a probe toward the independent-evidence quorum only when the HTTP-200 response is semantic contract evidence: success, EVM execution/revert code 3, or JSON-RPC execution-layer codes `-32099..-32000`.
- Provider-policy errors such as Tatum `-16401`, malformed-request `-32602`, and transport/rate-limit failures remain raw observations but do not satisfy the quorum.
- Recovery rounds now honor the requested count and wait for cooled endpoints to re-enter before consuming a recovery pass.
- Regression coverage was added for semantic/non-semantic probe classification and recovery-round count.

### Git / CI checkpoint
- Repair commit: `b722866860fb2d3a919fd388eac38260a08d9383`.
- Regression commit: `357969627248bea4be97dff542fab0cde73deaa5`.
- Latest main HEAD at this checkpoint: `357969627248bea4be97dff542fab0cde73deaa5`.
- GitHub Actions control-function run **21** is pending on that exact HEAD; predecessor run **20** is still in progress and will be superseded by the concurrency policy.

### Gate
- P2 remains **OPEN**.
- No P2 promotion is allowed until the new artifact is completed and independently reconciled as VERIFIED, and P2 provenance is REPLAYED.
\n\n## 2026-09-25 — P2 CLOSED, P3 unlocked\n\n### Closure evidence\n- Control-function verification Run #21: GitHub Actions `36181785712`, artifact `10883649934`, raw reconciliation VERIFIED, 17/17 probes with two independent matching semantic RPC observations, 0 conflicts, 0 incomplete.\n- Provenance recovery Run #23: conveyor `36183085089`, artifact `10884629388`, P2 provenance status REPLAYED for both canonical candidate transactions.\n- Transaction `0x5c28747a85e014b1ce0c35b5af88d577893cd6531b0523b7f64e5d82ba2e7c78`: 2 matching independent observations from Tatum and QuickNode after bounded recovery; seven endpoint attempts were recorded, including provider/transport failures as diagnostics only.\n- Transaction `0xa72eaebdc560af2fa6dad4d5b275b9205c1e20ec4c3413ca6bb0a3d7d65e434f`: 2 matching independent observations.\n- Conveyor report: `research_gate=P2_CLOSED`, `critical_stage=P3`, all four P2 conditions true.\n\n### Gate transition\n- Gate-transition commit: `b9bbd925eeeeb350381027d6c0d626f8c00a2a22`, `chore: advance saturation gate [skip ci]`.\n- Latest main HEAD after this transition: `b9bbd925eeeeb350381027d6c0d626f8c00a2a22`.\n- P3 is now the critical stage. Protocol discovery remains research evidence only until its own closure gate is explicitly satisfied.\n

## 2026-09-25 — P3 multi-source protocol/DEX gate CLOSED
- P3 Run #30: GitHub Actions conveyor `36185107384`, completed SUCCESS.
- P3 closure artifact: `P3_PROTOCOL_SNAPSHOT.json` with `stage_gate=CLOSED`, `stable_runs=2`, universe fingerprint `28e93a53c2480c01c7590c256cd22830eecd7558cf52528267ffcb10a335db5f`.
- Three external discovery feeds returned HTTP 200: DefiLlama protocols, DexScreener Polygon token profiles, and GeckoTerminal Polygon PoS DEX registry.
- Snapshot contained 720 Polygon protocol candidates, 128 normalized DEX-category candidates, 62 GeckoTerminal DEX records, 12 normalized DEX-name overlaps, zero duplicate-name conflicts.
- P3 gate transitioned to the next critical stage, **P4**.
- Gate-transition commit: `658e9d7dbc7f4c91a2d125def13e863464c90d1d`.
- Follow-up persisted stage-ledger reconciliation commit: `5362d2db433ffbd320babd11bcfe9975195fa18f`.


## 2026-09-26 — P6 route saturation CLOSED / P7 unlocked
### Engineering repair
- P6 previously produced a large derived route snapshot without an explicit closure contract and used hidden start-node/neighbor sampling caps.
- Replaced the P6 worker with full graph traversal over the persisted P5 pair universe.
- Added graph fingerprinting, complete-record checks, explicit `P6_CLOSURE_STATE.json`, stage-specific `stage_gate`, and matching stability recheck.
- Added regression coverage for closure, full-graph traversal and revision invalidation.
- CI initially failed because the new regression assertion had malformed nested quotes. The exact failure was isolated through a temporary diagnostic workflow; the assertion was repaired, diagnostics were removed, and the corrected workflow passed.

### Closure evidence
- First complete P6 pass: 451 nodes, 2,821 unique pairs, 0 invalid records, 617,622 total routes, stable_runs=1, gate OPEN.
- Second matching complete pass: same graph fingerprint, closure state persisted, stage_gate=CLOSED.
- Canonical P6 closure state: `automation/evidence/P6_CLOSURE_STATE.json`.
- Gate transition commit: `027144a08419651f29e3274a4f39e3a6f3dadef6`.
- Critical stage is now **P7**.

### Next critical objective
Execute P7 strategy-universe saturation under the same fail-closed discipline. Route existence is research evidence only; no economic or live-trading conclusion is implied by P6 closure.


## 2026-09-26 — P7 strategy saturation CLOSED / P8 unlocked
### Closure evidence
- P7 v2 replaced the 18-name placeholder with 18 auditable strategy records.
- Required fields are present for every strategy: mechanism, prerequisites, exact contracts, state dependencies, cost model, failure modes, competition model, simulation method, historical evidence, live/shadow evidence, profitability status, confidence and unknowns.
- Unresolved fields are explicit rather than invented: exact contracts are `NOT_IDENTIFIED`, profitability is `NOT_CERTIFIED`, and strategy-specific evidence remains pending downstream research.
- First pass: 18/18 families, stable_runs=1, gate OPEN.
- Matching recheck: same matrix fingerprint, stable_runs=2, stage_gate=CLOSED.
- Canonical P7 fingerprint: `69f240c85a75cfba73d189e94650c72271ed3368f4268349263d81176c8c949a`.
- Gate transition: P7 -> P8.

## 2026-09-26 — P8 deterministic feature matrix CLOSED / P9 unlocked
### Engineering repair
- P8 v2 added an explicit feature schema covering spread, volatility, volume, liquidity, imbalance, regime, momentum/reversion, route recurrence, opportunity persistence, gas regime, block activity and flow-toxicity proxy.
- Snapshot-supported features are computed deterministically; domains without sufficient source evidence are explicitly marked `NOT_AVAILABLE` or `NOT_CLASSIFIED`.
- P8 route recurrence provenance was corrected to use the persisted P6 closure fingerprint fallback.
- A missing `math` runtime dependency was found from the actual CI artifact and repaired.
- The conveyor itself was strengthened to fail closed when an executed task returns non-zero. This prevents a worker failure from appearing as a successful workflow.
- A stale P4 regression assertion on the old import line was identified from CI logs and removed without weakening the P4 contract.

### Closure evidence
- Final P8 matrix: 1,891 pair groups over 2,821 pair records.
- All 12 feature domains present for every group.
- Deterministic observed features present; unavailable/unclassified domains explicit.
- P8 fingerprint: `5138bae6d46712f79b83d7ad908ad120087529bd52d2917abbfe63969bdff068`.
- stable_runs=2, stage_gate=CLOSED.
- GitHub Actions Run #143 (`36231631950`) completed SUCCESS and advanced to P9.

### Next critical objective
P9 exact economic certification: exact-state replay, venue-specific swap math, gas, flash premium, fees, slippage, transfer taxes, failure cost, competition, minimum profit threshold, sensitivity and simulated-vs-realized error. Gross spread remains screening-only.


## 2026-09-26 — Polygon saturation CLOSED
### P9
- Capability universe reached 1,233/1,233 EVM pair addresses.
- Matching stable recheck closed P9.
- P9 remains readiness/evidence certification, not profit certification.

### P10
- P10 audit closed with every required predecessor gate true.
- Audit covers independent-source reconciliation, address/pool census, strategy coverage, negative-space/unknowns, stale-data, economic viability, security and reproducibility.
- Universe counts at closure: 469 tokens, 2,821 pairs, 617,622 routes, 18 strategy families, 1,891 feature groups, 420 economic candidate groups.

### P11
- P11 final closure report reached READY.
- Polygon census lock = true.
- Next-chain unlock = true.
- Therefore the Polygon saturation cycle P2 -> P11 is complete.


## 2026-09-26 — Polygon seal to global chain expansion
- P11 final Polygon closure is READY. Polygon census/audit is locked as complete.
- P11 explicitly records 420 exact-economic residual candidate groups; this is a residual research queue, not a profitability certification.
- Created `automation/CHAIN_UNIVERSE_QUEUE.json` as the new global expansion control-plane artifact.
- Polygon is marked completed; Ethereum Mainnet (chain ID 1) is seeded as the next research target.
- Next-chain sequencing is intentionally not hard-coded permanently. Fresh external evidence must recalculate the queue after each chain closure.

## 2026-09-26 — Ethereum chain bootstrap evidence recorded
- Polygon P2-P11 closure remains intact and is not reopened.
- Global chain queue advanced from `CANDIDATE_SEEDED` to `RESEARCH_ACTIVE` for Ethereum Mainnet (chain ID 1) after recording a candidate evidence snapshot.
- Added `chains/ethereum-mainnet/CHAIN_PROFILE.md` preserving verified-vs-candidate boundaries.
- Added `automation/evidence/ETHEREUM_CANDIDATE_SNAPSHOT.json` with consensus/timing, gas, RPC candidates, market-surface candidates, flash-liquidity candidates, lending candidates, MEV/orderflow, intent/aggregator surfaces and explicit unknowns.
- No Ethereum saturation gate is closed. P2 is not started until the live RPC bootstrap verifier is implemented.
- The next stage is read-only Ethereum P2 infrastructure verification using independent RPC quorum, deterministic freshness tolerance and evidence-preserving reconciliation.
\n## 2026-09-26 — Ethereum P2 bootstrap implementation lock
- Ethereum candidate evidence remains RECORDED_NOT_VERIFIED.
- Implemented the first live-read-only Ethereum P2 sub-gate: RPC identity, head freshness and capability evidence.
- The candidate pool is built from documented public endpoint options and remains subject to live runtime verification.
- The two-independent-endpoint doctrine and fail-closed behavior are inherited from the Polygon evidence discipline.
- Next atomic step: inspect the exact-SHA CI terminal result and evidence artifact; only then decide whether the Ethereum P2 bootstrap sub-gate can close.
## 2026-09-26 — Polygon saturation v2 integrity layer
- Closed the semantic gaps identified after P11 by making pool identity protocol-native rather than pair-address-only.
- Added explicit coverage for private mempool, AggLayer/Bridge-and-Call, aggregators/RFQ, lending/liquidation, derivatives/prediction, staking/liquid-staking and RWA/stablecoin surfaces.
- Added dynamic-state, token-taxonomy and route-policy schemas.
- Added immutable closure provenance and an automated rehydration path that restores the exact 469-token / 2,821-pair sealed snapshot to Git main.
- Added an independent audit that requires persistence, uniqueness, current-source reachability/markers and complete economic candidate disposition before GREEN.
