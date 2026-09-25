# GitHub Governance

## Current State
Repository is public and main is the canonical branch.

## Desired Main Protection
Enable a GitHub ruleset for main with pull-request review, required status checks once CI exists, no force pushes, and no branch deletion.

## Connector Limitation
The connected GitHub capability currently exposes read access to rulesets but not a write operation for creating repository rulesets. Therefore an active GitHub ruleset is NOT claimed until GitHub itself shows one.

## Audit Rule
Future status reports must distinguish repository constitution, GitHub enforcement active, and GitHub enforcement pending.
