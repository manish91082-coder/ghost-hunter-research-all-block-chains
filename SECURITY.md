# Security and Safety

## Public Repository
Never commit:
- private keys
- seed phrases
- wallet passwords
- API secrets
- RPC credentials
- signed raw transactions containing secrets
- personal access tokens

Use environment variables or local secret stores.

## Execution Safety
- Live execution defaults OFF.
- Shadow mode is default for new strategies.
- Canary size must be explicitly controlled.
- Profit guard is mandatory.
- Stale/conflicting chain state causes rejection.
- Unknown token behavior causes rejection until verified.

## Repository Safety
Main should eventually be protected with GitHub rulesets/branch protection requiring review and passing checks before merges. GitHub documents rulesets as the current flexible mechanism for branch/tag protection.
