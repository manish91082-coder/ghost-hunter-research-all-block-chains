# Continuity Protocol

## Source of Truth
GitHub repository state is the external project continuity layer.

## Every Substantive Project Turn
The project lead should:
1. Inspect current Git state before making a new project decision.
2. Reconcile the request with PROJECT_CONSTITUTION.md.
3. Update the relevant canonical files.
4. Record important decisions.
5. Update PROJECT_STATUS.md and PROJECT_PROGRESS.md.
6. Commit the changes.
7. Verify the resulting main HEAD.
8. Report the commit and current status.

## Memory vs Git
Chat memory preserves durable context and rules. Git preserves detailed project artifacts, evidence, status, decisions and history. Neither should be treated as a substitute for the other.

## Recovery
A fresh chat should be able to recover the project from README + PROJECT_STATUS + PROJECT_MEMORY + PROJECT_PROGRESS + CONSTITUTION + relevant architecture/research files.

## Automatic Save Policy
There is no silent background write between messages. Auto-save means every substantive project response/change is followed by a Git update when the connected GitHub tool is available and the change is material.
