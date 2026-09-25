# Project Constitution

## 1. Purpose
This repository is the canonical research, architecture, continuity and evidence record for Ghost Hunter Universal Profit Mesh.

## 2. Non-Negotiable Rules
- Goal drift is prohibited.
- Never fabricate blockchain, protocol, liquidity, profitability or execution facts.
- Distinguish observed facts, researched facts, assumptions and hypotheses.
- Scanner detection is not execution authorization.
- Never force a trade to satisfy a frequency target.
- Never knowingly execute a negative expected-value transaction.
- Final execution requires fresh state and exact simulation.
- Critical state disagreement triggers quarantine/freeze.
- Smart-contract profit guard must be able to reject an economically unsafe execution.
- Every live result must be measured by realized on-chain PnL, not quoted PnL.
- Public repository must never contain secrets, seed phrases, private keys or credentials.
- New strategies enter through shadow/canary validation before unrestricted live execution.
- Research and architecture must remain compatible with zero-cost-first testing.
- Paid infrastructure is enabled only when its incremental expected value is demonstrated.

## 3. Continuity Rules
- GitHub is the project source of truth after each committed milestone.
- PROJECT_STATUS.md records where the project is now.
- PROJECT_PROGRESS.md records what changed and what remains.
- PROJECT_MEMORY.md records durable decisions and architecture context.
- DECISIONS.md records material design decisions.
- RESEARCH_LOG.md records research claims and evidence.
- CHAIN_UNIVERSE.md and chain records are updated as chain-by-chain research is completed.
- Every substantive change must have a commit with a descriptive message.
- Do not silently rewrite historical evidence; append corrections with provenance.

## 4. Definition of Done
A component is not considered complete until:
1. implementation or design is documented,
2. assumptions are explicit,
3. tests or validation evidence exist where applicable,
4. status is updated,
5. Git state is committed,
6. remaining gaps are recorded.

## 5. Profit-Safety Principle
The project does not promise guaranteed profit. It guarantees a stricter engineering rule: no transaction should be intentionally authorized unless the current state, cost model, execution path and minimum-profit condition pass all required gates.
