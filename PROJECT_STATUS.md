# Project Status

Status date: 2026-09-25
Overall phase: Polygon-first saturation research
Current research scope: Polygon PoS Mainnet only (chain ID 137)
Implementation status: Not yet started in this research repository
Live trading status: OFF
Real-money deployment: OFF

## Repository Lock
- Canonical repository: manish91082-coder/ghost-hunter-research-all-block-chains
- Canonical branch: main
- Legacy implementation repositories are out of scope for this research track.
- Before every write: verify repository identity, branch, PROJECT_STATUS.md and latest HEAD.
- No repository switching is permitted without an explicit project decision.

## Research Discipline
- No fabricated facts.
- No unverified address/pair/pool/protocol is entered as VERIFIED.
- Facts, assumptions, hypotheses, historical data and unknowns remain separated.
- Execution-critical addresses require live/on-chain verification.
- Positive quoted profit is not treated as guaranteed profit.
- No live execution is enabled by this research repository.

## Polygon Work Completed
- Polygon-only scope lock created.
- Polygon evidence README created.
- Polygon PoS base profile created.
- Pre-transaction static-data saturation checklist created.
- Polygon saturation research plan created.
- Polygon RPC evidence file created with documented public RPC candidates and a live verification checklist.
- Polygon block/timing/finality evidence file created.
- Recent protocol-generation evidence recorded.
- Polygon system/bridge contract discovery census created with address-level evidence and explicit live-verification state.
- Proxy/control/upgradeability requirements recorded.
- Polygon machine-readable-oriented address registry created.
- Polygon bridge/state-sync surface map created, including PoS Portal, Fx Portal and downstream state-sync consumer separation.
- Polygon live-verification batch specification created for read-only chain/address/control verification.

## Polygon Work Not Yet Complete
- Live RPC ground-truth capture.
- Current block/header/finality measurements.
- RPC endpoint census and health measurements.
- Live bytecode verification of system/bridge addresses.
- Current-vs-historical reconciliation of the expanded Polygon Plasma/PoS discovery registry.
- Proxy implementation/control verification.
- Full bridge/state-sync surface census.
- Remaining bridge/predicate/exit/withdrawal/control surface reconciliation.
- Live verification execution of the expanded address registry.
- Additional predicate/control and Plasma-era bridge candidates added to the discovery registry for current-vs-historical classification.
- DEX/protocol address census.
- Token universe census.
- Pool/pair census.
- Route/combination enumeration.
- Flash-liquidity/lending/liquidation census.
- MEV/orderflow/intent/solver census.
- Strategy evidence matrix.
- Exact profitability certification.
- Technical-analysis/AI feature and prediction validation.
- Negative-space/unknown opportunity audit.

## Current source of truth
This repository plus the latest committed research/evidence files.

## Safety state
No live execution should be enabled from this repository until all required validation gates are explicitly satisfied.

## Next gate
P1 continuation: execute the read-only Polygon live-verification batch against independent RPC endpoints, reconcile critical identity/control conflicts, then complete the remaining bridge/state-sync census. DEX discovery remains blocked until the infrastructure gate is sufficiently verified.


## Latest P1 Execution Wiring
- A bounded Polygon-side critical-address target file is now canonical at `chains/polygon-pos/verification_targets.txt`.
- GitHub Actions now syntax-checks the verifier and invokes it with that target file, so the next push-triggered/manual run can perform actual `eth_getCode` probes rather than only network capability probes.
- This is execution wiring, not live evidence. P1 remains NOT PASSED until run artifacts/results are observed and reconciled.


## Latest Verification Hardening
- Verifier now rejects malformed/non-hex EVM target addresses before network access.
- Target-file changes are included in the GitHub Actions trigger paths.
- P1 remains NOT PASSED pending actual live execution evidence.


## Latest P1 Reconciliation Layer
- Automated deterministic reconciliation is now part of the GitHub verification workflow.
- It produces `polygon_verification_reconciliation.json` and preserves conflicts instead of majority-selecting an RPC.
- P1 remains NOT PASSED until actual runner output is observed.


## Latest CI Integrity Check
- Workflow command blocks were normalized into explicit multiline shell commands.
- Python validation and live verification are separate steps.
- Reconciliation runs after verifier execution and artifacts upload remains unconditional.
- P1 remains NOT PASSED until actual live evidence is observed.


## 2026-09-25 — First GitHub-hosted live-run evidence and false-green correction
- GitHub Actions run `36155696574` on main commit `cf4f955efebb797068e5e902c727c1864a1e2f72` completed with workflow status **Success** and produced artifact `polygon-readonly-verification`.
- Artifact inspection showed all three configured public RPC endpoints returned HTTP **403 Forbidden** for chain identity, block/head and address-code probes. No live chain ID, latest block, or runtime code observation was obtained.
- The reconciliation artifact classified the evidence as **PARTIAL**, with chain-ID agreement false, head agreement false, and all 11 target code observations unsuccessful. Therefore P1 was correctly **NOT PASSED**.
- Root cause of the misleading green workflow: the verifier previously exited successfully when zero RPC chain IDs/heads were observed because its failure condition only checked non-empty observations. This has now been corrected.

## 2026-09-25 — P1 quorum fail-closed hardening committed
- Commit `1d6a3ae20417e32450da7b162b605a6f053dddd4`: verifier now requires at least two independent successful chain-ID observations, unanimous chain ID 137, at least two successful block observations, and exact latest-block agreement before returning success.
- Commit `8fd9d0699b64aaf610905edb13b5a8927b518f49`: reconciliation now requires the exact canonical target set, at least two successful independent code observations per target, matching code hashes, chain-ID quorum, and head agreement before classifying evidence as VERIFIED.
- Latest canonical main HEAD: `8fd9d0699b64aaf610905edb13b5a8927b518f49`.
- Expected next CI behavior: if the public RPCs continue returning 403, the workflow must fail rather than appear green. This is intentional fail-closed behavior and is evidence-quality progress, not a project failure.

## Gate state
- P1 live verification: **NOT PASSED**.
- Polygon saturation gate: **OPEN**.
- DEX/protocol discovery remains blocked until P1 infrastructure evidence is genuinely verified.


## 2026-09-25 — RPC pool rotation after GitHub-runner access evidence
- Run `36157003942` failed as intended after the fail-closed verifier detected zero successful RPC identity/head observations.
- Artifact evidence showed HTTP 403 from all three prior CI endpoints: dRPC, PublicNode and 1RPC. This is evidence of access failure from the GitHub-hosted runner context, not proof that the providers are globally offline.
- The CI RPC probe pool has therefore been rotated to three other Polygon-documented public endpoints: Tenderly public RPC, Nodies public RPC, and OnFinality public RPC. Polygon's current documentation lists these among public RPC options and notes that public RPCs may have rate limits or traffic restrictions. citeturn2view0
- This is an infrastructure-access experiment, not a relaxation of the P1 evidence gate.

## Gate state
- P1 live verification: **NOT PASSED**.
- Polygon saturation gate: **OPEN**.
- DEX/protocol discovery remains blocked.

## 2026-09-25 — Run #13: verifier serialization repaired, P1 remains blocked
- Commit `84fadf926ee9cd96c3b2b0a228458ebb28d9b1a8` repaired the verifier's JSONL/checkpoint newline serialization introduced by the parallelization patch. The source now writes real newline characters rather than literal `\\n` text.
- GitHub Actions run `36164386940` (#13) completed with **failure** at the intentional P1 quorum gate; source validation succeeded and artifact upload succeeded.
- Artifact `10876891277` was independently parsed: `polygon_rpc_observations.jsonl` contains 51 physical lines, 51 valid JSON records, zero literal newline escape artifacts, and zero JSON parsing errors. This confirms the serialization defect is fixed.
- Live evidence from Run #13: only RPC-3 (OnFinality) returned a valid chain ID and block. Observed chain ID is 137 and observed latest block is 94,433,671. The other two configured RPCs did not provide successful identity/head evidence. Therefore the mandatory two-independent-RPC quorum is not met.
- Run #13 reconciliation observed code from only 4 of 11 critical targets, with only one independent endpoint for each observed target. Evidence state is **PARTIAL** and exact target-set coverage is false.
- The current failure is therefore an **infrastructure evidence/quorum limitation**, not the previously confirmed serialization defect.

## Gate state
- P1 live verification: **NOT PASSED**.
- Polygon saturation gate: **OPEN**.
- DEX/protocol discovery remains blocked.
- Next engineering action: preserve the corrected verifier and solve independent-RPC accessibility/rate-limit coverage without weakening the quorum or evidence gates.

## 2026-09-25 — Runner RPC saturation diagnosis and P1 gate hardening
- GitHub runner reconnaissance established two endpoints with basic Polygon reachability: Tatum and QuickNode public. QuickNode returned all 11 critical target code probes in the main verification run; anonymous Tatum was progressively rate-limited with HTTP 429 during the code phase.
- The verifier was strengthened so reconciliation must itself pass before CI can be green. A partial reconciliation can no longer produce a successful workflow.
- Head quorum was corrected to use the existing explicit stale-block tolerance rather than requiring identical latest block numbers. Two fresh endpoints within the configured tolerance now satisfy the head agreement condition; exact code-hash agreement remains mandatory for every critical target.
- Tatum's current public documentation states a free plan with 3 RPS and free API keys. The workflow now supports an optional GitHub Actions secret named `TATUM_API_KEY`; the secret is never written to the repository.
- P1 remains **NOT PASSED** until two independent RPC endpoints provide matching critical-address code evidence for all 11 targets and reconciliation classifies the evidence as VERIFIED.

## 2026-09-25 — Adaptive RPC rotation implemented
- The previous fixed two-endpoint CI invocation has been replaced by a canonical multi-endpoint Polygon RPC candidate pool at `chains/polygon-pos/rpc_pool.txt`.
- The verifier now performs a cheap identity/head pass across the pool, builds a chain-137 eligible set, and then rotates critical-address `eth_getCode` requests across eligible endpoints.
- HTTP 429 responses honor `Retry-After` when present and place the endpoint into cooldown. HTTP 403/401/404 and transient failures also receive cooldowns instead of being hammered repeatedly.
- Each critical target still requires two distinct successful RPC endpoint observations. No majority-selection or quorum weakening was introduced.
- Head agreement now uses the configured stale-block tolerance consistently, rather than requiring exact same-block equality.
- Optional `TATUM_API_KEY` authentication remains secret-only through GitHub Actions.
- This changes the access strategy, not the evidence standard. P1 remains NOT PASSED until reconciliation reports VERIFIED.

### Gate state
- P1 live verification: **NOT PASSED** pending the new adaptive-pool CI artifact.
- Polygon saturation gate: **OPEN**.
- DEX/protocol discovery remains blocked until P1 is genuinely verified.

### Next atomic step
Inspect the first CI run using the full adaptive RPC pool. If fewer than two independent code-capable endpoints are reachable, preserve that evidence and move the same verifier to the permitted outbound-RPC environment rather than weakening the gate.
## 2026-09-25 — Run #26 adaptive-rotation evidence
- Run 36169111299 / #26 executed the adaptive RPC pool after the worker-input fix.
- Live identity/head evidence came from OnFinality and QuickNode public: chain ID 137 on both; latest blocks 94,435,462 and 94,435,461; head span 1 with tolerance 2; head agreement true.
- The 14-endpoint pool was actually exercised. The verifier produced two-endpoint code coverage for several critical targets and reported the exact targets still short of two independent observations.
- This proves the new rotation path is functioning and that provider-specific failures are being bypassed rather than terminating the verifier at the first bad RPC.
- Reconciliation did not consume the verifier records in Run #26 because the rewritten record serializer accidentally omitted the required top-level method field. This was a verifier serialization regression, not an RPC/evidence failure.
- Commit bcdd68f7b662c20f247062be326b72656513d97e restores the top-level method field required by the reconciliation schema.
- P1 remains NOT PASSED until the corrected run produces reconciliation VERIFIED.

### Gate state
- P1 live verification: NOT PASSED.
- Polygon saturation gate: OPEN.
- DEX/protocol discovery remains blocked.

### Next atomic step
Inspect the corrected adaptive-pool run. Its decisive artifact is expected to show chain/head quorum plus per-target independent code counts through the reconciliation layer.
## 2026-09-25 — RPC cooldown recovery added
- Adaptive rotation now has a bounded recovery phase for rate-limited endpoints.
- HTTP 429 increases that endpoint's local request interval and applies cooldown; after cooldown, the endpoint is eligible to re-enter the address-code rotation.
- The workflow now uses 1.0 second base per-endpoint pacing and two total address-code passes.
- This is intended to convert temporary provider throttling into a recoverable condition while retaining the two-independent-endpoint evidence requirement.
- P1 remains NOT PASSED until the corrected run reconciles all 11 targets as VERIFIED.

## 2026-09-25 — P1 PASSED: live Polygon code reconciliation

Run `36169503083` completed successfully.
- Artifact: `10879647689`
- Artifact digest: `sha256:bc53e3255ac12c2e99d62a5ef189c60fe26f1deb6e1c67178f043cc296546bbe`
- Observation block: 94,435,638
- Chain ID: 137
- Independent identity/head endpoints: 3
- Exact target set: 11/11
- Independent successful code observations: >=2 per target
- Matching code hashes: 11/11
- Reconciliation: VERIFIED
- Conflicts: 0

### Gate transition
- **P1 live infrastructure + bounded critical runtime-code gate: PASSED.**
- The 11 bounded target entries are PARTIAL in the registry because runtime-code identity is verified but proxy/control/creation/behavior fields remain pending.
- Polygon saturation gate: OPEN.
- DEX/protocol discovery remains blocked pending P2 address/control/bridge reconciliation.

### Next gate
P2: reconcile proxy implementations, admin/owner/roles, creation evidence, contract-specific probes and current-vs-historical classification.

## 2026-09-25 — P2 control-plane verification launched
- P1 is closed from Run #30 with VERIFIED runtime-code reconciliation for the 11 bounded Polygon targets.
- P2 now probes the standardized ERC-1967 implementation, admin and beacon storage slots across the same target set.
- P2 workflow: `polygon-p2-control-verification.yml`
- P2 run: `36170466071`
- Current runner state at checkpoint: **IN_PROGRESS**.
- P2 remains read-only and fail-closed. At least two independent chain-137 RPC observations must match for every target/slot combination; conflicts are preserved.
- ERC-1967 slot definitions follow the standard's published implementation/admin/beacon slots. citeturn422867search0

### Current gate
- P1: **PASSED**
- P2 ERC-1967 storage consistency: **RUNNING**
- Polygon saturation: **OPEN**
- DEX/protocol discovery: **BLOCKED pending P2 completion**

## 2026-09-25 — P2 #1 verifier failure and minimal fix
- P2 run `36170466071` failed before producing evidence because the shared read-only RPC allowlist rejected `eth_getStorageAt`.
- This was an implementation-layer method allowlist omission, not a Polygon RPC availability failure.
- Commit `5a0e31ca66c4d252b742f5d5c4c1f7c145be4b12` adds `eth_getStorageAt` to the existing read-only allowlist.
- No write/sign/send capability was added.
- Corrected P2 run: `36170624761`, currently **IN_PROGRESS** at the latest checkpoint.
- P1 rerun is also triggered by the shared verifier change. P1 remains semantically frozen and must still pass its existing gate.

## 2026-09-25 — P2 storage coverage hardening
- P2 Run #2 `36170624761` produced 66 storage observations from QuickNode + Tatum.
- QuickNode returned all 33 probes successfully. Tatum returned 16 successful probes and 17 HTTP 429 responses.
- P2 reconciliation therefore remained PARTIAL because 17 target/slot combinations had only one independent successful observation.
- No slot-value conflicts were observed in the available dual observations.
- The P2 verifier has now been hardened to perform request-level rotation per target/slot and bounded recovery rounds. Chain-137 endpoints with a valid identity can participate in storage rotation even when their head probe is temporarily unavailable; a separate two-endpoint fresh-head quorum remains mandatory.
- This preserves the two-independent-endpoint rule while giving temporarily rate-limited RPCs a chance to recover.

## 2026-09-25 — P2 ERC-1967 storage sub-gate PASSED

Run `36171378222` completed successfully.

Evidence:
- artifact `10880421099`;
- digest `sha256:5693d27acbd6b5aff22a5c0a4d9fccd15a0641c7bb6463efc792a75784216e3f`;
- observation block **94,436,387**;
- target×slot matrix **33/33**;
- independent successful observations **66**;
- conflicts **0**;
- insufficient observations **0**;
- reconciliation **VERIFIED**.

### P2 state
- ERC-1967 storage consistency: **PASSED**
- Overall P2: **IN PROGRESS**
- Next P2 atomic work: verify the four non-zero derived implementation/admin addresses, then owner/role/control functions and creation evidence.
- Polygon saturation: **OPEN**
- DEX/protocol discovery: **BLOCKED**
## 2026-09-25 — P2 derived-control code verification launched
- P2 ERC-1967 storage sub-gate is PASSED.
- Four non-zero derived control addresses are now in a dedicated runtime-code verification queue.
- New workflow: `.github/workflows/polygon-p2-derived-control-verification.yml`
- The four addresses must each obtain matching `eth_getCode` hashes from at least two independent chain-137 RPC endpoints.
- Overall P2 remains IN PROGRESS.
## 2026-09-25 — Derived-control head freshness correction
- Derived-control Run #2 proved all four derived addresses had matching runtime-code hashes from OnFinality + QuickNode, but the run failed because a third successful Tatum head was three blocks behind the freshest head and the verifier's all-endpoint head agreement was too strict for this sub-gate.
- Added an optional deterministic fresh-head quorum mode. The default P1 behavior remains unchanged; derived-control verification explicitly requires any two independent fresh endpoints within the configured tolerance.
- No majority vote is used. The verifier chooses the smallest-span deterministic pair and records the chosen endpoints, span and excluded stale endpoints as evidence.
- Corrected derived-control workflow now uses `--min-head-endpoints 2` and reconciliation consumes `head_quorum_agreement`.

## 2026-09-25 — Derived-control workflow invocation defect corrected
- Derived-control Run #4 (36172904065) failed because the workflow checked out commit 310e9f9837cd9b06f2bfa05f93e5a26823b3071a but its live shell invocation omitted the newly supported --min-head-endpoints 2 argument.
- The verifier itself was already quorum-capable, and Run #4 still obtained matching runtime-code hashes for all four derived addresses from OnFinality + QuickNode. The failure was therefore a workflow wiring defect, not a derived-code conflict.
- Commit 5b0212d5ca8ce094f4438f60e424189bc0259e6a fixes the workflow: it passes --min-head-endpoints 2, syntax-checks the reconciliation source, and initializes optional shell status variables safely.
- A fresh CI artifact from the corrected workflow is now required before the derived-control sub-gate can be marked VERIFIED.
- Overall P2 remains IN PROGRESS; Polygon saturation remains OPEN; DEX/protocol discovery remains BLOCKED.

## 2026-09-25 — P2 control-function probe harness added
- Added `chains/polygon-pos/p2_control_function_targets.txt` for read-only selector candidates on the two parent contracts identified by P2 ERC-1967 provenance.
- Added `polygon_p2_control_function_verifier.py` and reconciliation logic with adaptive RPC rotation, two-endpoint fresh-head quorum, and evidence-preserving handling of JSON-RPC success or error outcomes.
- A reproducible revert/error is now treated as RPC evidence rather than as a missing observation; transport failures such as HTTP 403/429 are still not counted as evidence.
- Added GitHub Actions workflow `polygon-p2-control-function-verification.yml` with fail-closed reconciliation and unconditional artifact upload.
- Overall P2 remains IN PROGRESS. No control-function semantics are promoted from selector identity alone.
## 2026-09-25 — P2 control-function verifier regression hardening
- A runtime audit found stale successful[...] references after the control-function evidence model was changed to observed[...].
- Commit b24a9820ad632a983c44873cb4c3c98e9564b109 removes the stale references.
- Deterministic regression coverage was added at chains/polygon-pos/test_p2_control_function_regression.py.
- The control-function workflow now runs that regression suite before any live RPC probes and triggers when the test file changes.
- The test also locks the read-only eth_call allowlist and verifies deterministic matching/conflict fingerprints for successful calls and JSON-RPC errors.
- No live control-function gate is promoted from source inspection. CI evidence is still required.

## 2026-09-25 — Canonical CI state extraction added
- Added read-only tools/github_ci_state.py.
- It resolves main HEAD and inspects the four canonical Polygon workflows, including run status, job conclusions and artifact metadata for recent main runs.
- It never dispatches, reruns or mutates GitHub Actions.
- GITHUB_TOKEN is optional and is used only as an HTTP bearer token when present.
- This reduces dependence on connector-side Actions listing limitations while preserving the repository as the source of truth.

## 2026-09-25 — Automated CI evidence collector wired
- Added `.github/workflows/github-ci-state-evidence.yml` using `workflow_run` completion triggers for the four canonical Polygon verification workflows.
- The collector has `actions: read` permission, runs the read-only CI state extractor, validates the report shape, and uploads `github-ci-state-evidence` as an artifact.
- The report now includes triggering workflow context when available, plus main HEAD, recent runs, jobs and artifact metadata.
- This collector is observational only. It does not dispatch or rerun workflows.

## 2026-09-25 — Fresh P2 evidence reacquisition triggered
- The derived-control verification workflow was deliberately re-triggered from main through a deterministic workflow-marker-only change.
- The control-function verification workflow was likewise deliberately re-triggered from main.
- Trigger commits:
  - derived control: b97b8fb44583b25f7eda96f8d7da8fdb434d3e39
  - control function: bfe36c431d56de65e1b0164429d48d387ca30f7f
- These commits are evidence-acquisition triggers only. They do not relax thresholds or promote any gate.
- P2 derived runtime-code and P2 control-function remain pending until their actual CI job conclusions and artifacts are inspected.

## 2026-09-25 — Control-function transport-evidence false-positive closed
- Reconciliation was hardened so only HTTP 200 JSON-RPC responses can become semantic call fingerprints.
- HTTP 403/429/timeouts and other transport failures are explicitly excluded from evidence matching.
- Added a regression test proving an HTTP 403 response is not evidence.
- Commit fc126f0f2e06db43de6d9082f8d07e2e7d0b773e adds the regression guard; the reconciliation correction is commit b6539dcf941a718018f915e274e3a03763e167ca.
- The control-function workflow is automatically re-triggered by these path changes. Its gate remains pending until the resulting artifact is inspected.

## 2026-09-26 — P2 provenance and control-surface expansion
- Added `chains/polygon-pos/P2_EXTERNAL_PROVENANCE_CANDIDATES.md` separating explorer/forum discovery from live verification.
- External evidence identified historical deployment/control relationships for the EIP1559Burn proxy, the sPOL parent/admin pair, and the current sPOL implementation candidate. These remain EXTERNAL/HISTORICAL candidates only.
- Expanded `p2_control_function_targets.txt` from 8 to 17 read-only probes, adding sPOL `authority()` plus ProxyAdmin owner/pendingOwner and proxy relationship probes for the two derived admin addresses.
- Added regression coverage for the expanded manifest.
- No external explorer claim has been promoted to VERIFIED.

## 2026-09-26 — Autonomous P2-P11 saturation conveyor implemented
- Added `tools/saturation_conveyor.py`, `tools/polygon_universe_worker.py`, `tools/automation_state_store.py` and `.github/workflows/saturation-conveyor.yml`.
- The conveyor runs on a 5-minute schedule plus manual dispatch, maintains a persistent checkpoint artifact, and commits to main only on actual gate/stage transitions.
- P2 remains the critical promotion gate. P3-P10 run in a shadow preparation lane while P2 evidence is being resolved.
- The first-pass worker now continuously prepares protocol, token, pair, route, strategy, feature, economic-screening and saturation-audit evidence.
- P11 is defined as research closure / next-chain-unlock candidate, not an automatic next-chain authorization.
- This automation changes execution cadence, not evidence standards.

## 2026-09-26 — Automation quality hardening
- Conveyor task cursors are persistent across runs, so work does not restart at the first task every heartbeat.
- Critical promotion is strictly ordered P2 -> P3 -> P4 -> P5 -> P6 -> P7 -> P8 -> P9 -> P10 -> P11.
- Stage promotion predicates are content-aware; file existence alone is not treated as completion.
- P10 -> P11 requires the P10 audit to explicitly report stage_gate=CLOSED.
- P4 token candidates are deduplicated and P6 route enumeration now permits cyclic route closure.
- Checkpoint restore uses GitHub Actions artifact state, while real stage/gate transitions are the only automation commits to main.

## 2026-09-26 — Conveyor red-run root cause and persistence repair
- Screenshot review showed the Autonomous Polygon Saturation Conveyor repeatedly failing across rapid push-triggered runs while the CI State Evidence Collector was green.
- Root cause identified in the P2 regression fixtures: after the reconciler was hardened to require HTTP 200, two matching success/error fixtures lacked `http_status=200`, causing valid fingerprints to become `None` and the match tests to fail.
- Fixed the fixtures and added conveyor-specific regression coverage.
- Removed the conveyor push trigger. It now runs on the 5-minute schedule or manual dispatch, preventing development-commit storms.
- Fixed persistent checkpointing so the state artifact restores `automation/saturation_state.json`, `automation/evidence/`, and `automation/universe/` across runs.
- Artifact API/restore failures are now fail-closed instead of silently resetting state.
- Stage promotion remains explicit and content-aware; first-pass snapshots cannot be promoted to CLOSED merely because a file exists.

## 2026-09-26 — Saturation integrity hardening
- P2 provenance replay now reaches `REPLAYED` only when every candidate transaction has at least two independent observations and those observations match exactly.
- P5 pair universe now canonicalizes by `pairAddress`, preventing duplicate pair rows from cross-token discovery calls from inflating saturation counts.
- Regression coverage now guards both invariants.

## 2026-09-26 — P2 derived runtime verification
- P2 derived runtime-code sub-gate is now VERIFIED from conveyor Run #14 at Polygon observation block 94,439,097.
- Four derived addresses were matched across two independent RPC observations each with zero conflicts and zero incomplete targets.
- Canonical evidence: `chains/polygon-pos/P2_DERIVED_CONTROL_CODE_RUN_4.md`.

## 2026-09-26 — P2 provenance reconciliation defect repaired
- Canonical live checkpoint before repair: main HEAD `2c9426d9feb0ac1f8ba46de2ee0c18971bd72ad4`.
- Conveyor Run `36179352109` was green at the job/step level, but its evidence reported P2 provenance `PARTIAL` because semantic matching incorrectly included the provider-specific `rpc` field.
- The two candidate transactions each had two independent observations from different RPCs; their transaction/receipt payloads matched. No semantic chain-data conflict was identified.
- Commit `8f6867b95de5430a6726e47fc572dbde4b260e5a` repaired the semantic fingerprint in `tools/polygon_universe_worker.py`.
- Commit `2c9426d9feb0ac1f8ba46de2ee0c18971bd72ad4` added executable regression coverage in `tools/test_saturation_conveyor_regression.py`.

### Gate state
- P1: PASSED.
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: VERIFIED.
- P2 control-function: OPEN.
- P2 provenance: pending corrected live replay.
- Polygon saturation gate: OPEN.
- DEX/protocol discovery remains shadow-only until P2 closes.

## 2026-09-26 — P2 control-function recovery defect repaired
- Main HEAD at this checkpoint: `b2fe8738b28ee77670edb7a72994fcd039c793bb`.
- Run `36179352109` showed the control-function verifier failing with a four-block head span against a two-block tolerance.
- Static live-code audit found the recovery loop exited merely because a candidate endpoint pair existed, not because the pair satisfied the freshness tolerance.
- Commit `4f6391f80246c50812b7693177d0c11268b06269` introduced `head_quorum_ready()` and corrected the recovery stop condition.
- Commit `b2fe8738b28ee77670edb7a72994fcd039c793bb` added executable regression coverage.
- Dedicated control-function CI run `36180198453` is pending on this corrected HEAD.

### Gate state
- P1: PASSED.
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: VERIFIED.
- P2 provenance: pending corrected live replay.
- P2 control-function: pending corrected live replay.
- Polygon saturation gate: OPEN.

## 2026-09-26 — Conveyor throughput optimization locked
- Main HEAD: `798525a31e9f3486844acfc83653bb8c78f18e0c`.
- Critical-lane scheduling now avoids repeating already-closed P2 tasks and permits two independent critical tasks per bounded round.
- This is an execution-efficiency improvement only; evidence standards and P2 gate predicates remain unchanged.
- The next fresh conveyor run must validate both the scheduler and repaired P2 evidence paths on GitHub Actions.


## 2026-09-26 — P2 control-function evidence classification repair
- Run `36180198453` provided the decisive failure evidence: head quorum passed, but ten probe results were marked conflicts.
- Artifact inspection showed Tatum `-16401` responses were provider plan restrictions rather than contract outcomes. Tatum's current gateway documentation identifies `-16401` as a method-plan restriction. citeturn402236search0turn402236search6
- Artifact inspection also identified a malformed calldata encoding for the second parent ProxyAdmin probes, yielding `-32602`.
- Commits `e9c1d90c68bbf78a39daf2ed4b4fd6e28b0be140`, `93ed26ec64fa8b79d2d63e4ad08e1815f08b9a30`, and `f418b3a58e9fb5b6f75b09f48eb80ebbe9e2d429` repair the evidence classifier, add regression tests, and correct the calldata.
- Latest main HEAD: `f418b3a58e9fb5b6f75b09f48eb80ebbe9e2d429`.
- Fresh corrected control-function workflow run: `36181173124`, currently queued. Earlier intermediate runs `36181163798` and `36181167860` are on the immediately preceding repair commits and are not authoritative for the final HEAD.

### Gate state
- P1: PASSED.
- P2 ERC-1967 storage: PASSED.
- P2 derived runtime-code: VERIFIED.
- P2 provenance: OPEN/PARTIAL pending another independent observation for one candidate transaction.
- P2 control-function: OPEN pending corrected artifact.
- Polygon saturation gate: OPEN.
- No P2 promotion is made from queued/pending state.


## 2026-09-25 — Current P2 control-function repair checkpoint
- Run `36181173124` raw artifact was PARTIAL with 17 probes, 0 semantic conflicts, and 8 probes lacking two semantic RPC observations.
- Root cause isolated to evidence-slot accounting and recovery timing: provider-policy errors such as Tatum `-16401` were counted as attempted observations, while cooled independent RPCs were not given a full recovery window.
- Repair commit: `b722866860fb2d3a919fd388eac38260a08d9383`.
- Regression commit: `357969627248bea4be97dff542fab0cde73deaa5`.
- The new verifier only counts semantic HTTP-200 contract evidence toward the two-independent-RPC quorum and honors the requested recovery-round count with cooldown-aware recovery.
- Run #20 on the first repair commit was cancelled by the workflow concurrency policy when the regression commit arrived.
- Run #21 on `357969627248bea4be97dff542fab0cde73deaa5` is currently in the live-probe step; source validation is GREEN, but the workflow is not GREEN until the complete artifact is reconciled.

## Gate state
- P2 control-function: **OPEN / VERIFICATION IN PROGRESS**.
- P2 provenance: still requires **REPLAYED** evidence.
- Polygon saturation: **OPEN**.
- DEX/protocol promotion: **BLOCKED** until P2 closes.
\n\n## CURRENT CANONICAL STATUS — 2026-09-25\n- Canonical main HEAD: `b9bbd925eeeeb350381027d6c0d626f8c00a2a22`.\n- Polygon research gate: **P2_CLOSED**.\n- Critical stage: **P3**.\n- P2 storage: VERIFIED.\n- P2 derived runtime code: VERIFIED.\n- P2 control-function evidence: VERIFIED, 17/17 matching, zero conflicts/incomplete.\n- P2 provenance: REPLAYED, both canonical candidate transactions independently matched across two RPC endpoints.\n- P3-P10 remain preparation/shadow evidence until each stage-specific closure predicate becomes explicit.\n- P11 remains locked until P10 closure.\n- Live trading: OFF. Real-money deployment: OFF.\n\n### Immediate operating rule\nP3 discovery work may continue, but no protocol/address/venue is promoted to VERIFIED from discovery snapshots alone. Every later stage must preserve the same fail-closed evidence discipline used for P2.\n

## CURRENT CANONICAL STATUS — P3 CLOSED / P4 ACTIVE
- Canonical main HEAD: `5362d2db433ffbd320babd11bcfe9975195fa18f`.
- Research gate: **P2_CLOSED**.
- Critical stage: **P4**.
- P2: CLOSED.
- P3 protocol/DEX discovery: **CLOSED** after two consecutive stable multi-source snapshots.
- P4 token discovery: active critical stage, still discovery evidence until an explicit P4 closure predicate passes.
- P5-P10: shadow/preparation.
- P11: locked.
- Live trading: OFF. Real-money deployment: OFF.

### P3 evidence boundary
P3 closure confirms multi-source discovery convergence and snapshot stability only. It does not verify on-chain protocol contracts, pools, liquidity, or profitability. Those remain downstream evidence tasks.


## CURRENT CANONICAL STATUS — 2026-09-26 — P6 CLOSED / P7 ACTIVE
- Canonical main HEAD: `027144a08419651f29e3274a4f39e3a6f3dadef6`.
- Research gate: **P2_CLOSED**.
- P2: **CLOSED**.
- P3: **CLOSED**.
- P4: **CLOSED**.
- P5: **CLOSED**.
- P6 route/combinations: **CLOSED** after a complete matching recheck.
- Current critical stage: **P7 OPEN**.
- P6 graph evidence: 451 nodes, 2,821 unique pair records, 0 invalid pair records, 617,622 total route candidates.
- P6 graph fingerprint: `e3fa1495cc17172b95dd76c7f1e87655d356d4c8445c60a4733acf8b72e6caa5`.
- P6 closure stability: `stable_runs=3` in the persisted closure state.
- GitHub Actions Run #136 (`36230852577`) completed **SUCCESS** and performed the gate transition to P7.
- Live trading: **OFF**. Exact economic certification remains downstream.

### P6 evidence boundary
P6 closure certifies complete deterministic route-graph enumeration over the persisted P5 pair universe and matching graph stability. It does not certify swap execution, gas, slippage, competition, profitability, or live-trade viability. Those remain downstream P8/P9/P10 evidence tasks.


## CURRENT CANONICAL STATUS — 2026-09-26 — P8 CLOSED / P9 ACTIVE
- Canonical main HEAD before this documentation lock: `e521154057005e5cc08544fd4cd46d9226fdaea7`.
- Research gate: **P2_CLOSED**.
- P2, P3, P4, P5, P6, P7 and P8: **CLOSED**.
- Current critical stage: **P9 OPEN**.
- P6: 451 graph nodes, 2,821 unique pairs, 617,622 route candidates, stable graph fingerprint `e3fa1495cc17172b95dd76c7f1e87655d356d4c8445c60a4733acf8b72e6caa5`.
- P7: 18/18 required strategy families, schema-complete matrix, explicit unresolved/economic boundaries, stable fingerprint `69f240c85a75cfba73d189e94650c72271ed3368f4268349263d81176c8c949a`.
- P8: 1,891 pair groups over 2,821 pair records, 12 deterministic/proxy feature domains, explicit unavailable domains, stable fingerprint `5138bae6d46712f79b83d7ad908ad120087529bd52d2917abbfe63969bdff068`.
- P8 closure: `stable_runs=2`, stage_gate=CLOSED.
- GitHub Actions Run #143 (`36231631950`) completed **SUCCESS** and advanced the critical stage to P9.
- Live trading: **OFF**. P9 remains the exact economic certification boundary.

### P7/P8 evidence boundary
P7 closure certifies strategy-family coverage and matrix schema completeness, not exact contract discovery or profitability. P8 closure certifies deterministic feature coverage over the available pair snapshot; proxy features and unavailable domains are explicitly labeled. Neither stage certifies profitable execution.


## 2026-09-26 — POLYGON FULL SATURATION / P11 READY
- Canonical main HEAD before documentation lock: `b7b497a15596131240eba4df907c34cb41928726`.
- P6: CLOSED.
- P7: CLOSED.
- P8: CLOSED.
- P9: CLOSED.
- P10: CLOSED.
- P11: **READY**.
- Polygon census lock: **TRUE**.
- Next-chain unlock: **TRUE**.
- Polygon universe audit counts:
  - 469 tokens
  - 2,821 pair records
  - 617,622 route candidates
  - 18 strategy families
  - 1,891 feature groups
  - 1,233 P9 capability pair addresses, all processed with two-endpoint observations
  - 420 P9 economic candidate groups
- P9 exact-profit certification count: **0/420**.
- P9 residuals: 420 economic adapter/certification work items, 112 non-EVM pool references requiring adapters.
- Live signing/public broadcast: **OFF**.
- Final boundary: Polygon universe/census is closed; exact profitability/execution economics remain a separate downstream research track.

### Final evidence
- P10 `stage_gate=CLOSED`, `polygon_universe_status=CENSUS_COMPLETE_FOR_AUDIT`.
- P11 `status=READY`, `polygon_census_lock=true`, `next_chain_unlock=true`.


## CURRENT CANONICAL STATUS — 2026-09-26 — POLYGON P11 READY / GLOBAL CHAIN EXPANSION
- Canonical main HEAD: `0f7f881a25c5a8cabbdb35ae9be13f30ca5c3fd7`.
- Polygon P2-P10: CLOSED.
- Polygon P11: **READY**.
- Polygon census lock: **true**.
- Polygon exact-economic residual: **420 candidate groups**, explicitly not profit-certified.
- Global chain expansion queue is now seeded at `automation/CHAIN_UNIVERSE_QUEUE.json`.
- Next research target: **Ethereum Mainnet (chain ID 1)**, marked CANDIDATE_SEEDED rather than permanently ranked.
- The permanent chain order remains evidence-driven and recalculated from fresh research.
