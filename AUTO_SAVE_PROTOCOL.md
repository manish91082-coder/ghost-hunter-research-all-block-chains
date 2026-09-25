# Auto-Save Protocol

## Meaning
Auto-save is a project operating protocol. Whenever a substantive project decision, architecture change, research conclusion, implementation milestone, test result or status change is produced, update the relevant canonical files, commit to Git, verify main HEAD, and report the resulting state.

## Minimum Continuity Set
README.md
PROJECT_CONSTITUTION.md
PROJECT_STATUS.md
PROJECT_PROGRESS.md
PROJECT_MEMORY.md
DECISIONS.md
RESEARCH_LOG.md
CHANGELOG.md

## Chain-wise Auto-Save
Each verified chain gets a canonical record under chains/<chain-slug>/. No chain record is considered verified until evidence and validation fields are populated.

## Evidence
Research records retain source URLs and research timestamps.