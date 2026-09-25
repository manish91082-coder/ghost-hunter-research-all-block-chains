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
