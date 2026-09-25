# Polygon P1 Live Verification Evidence — Run #30

## Run identity

- Workflow: **Polygon Read-Only Verification**
- Run: **#30**
- Run ID: `36169503083`
- Workflow commit: `bd5a4ec5c979379a85e02926f96a64e5f4974f94`
- Result: **SUCCESS**
- Artifact ID: `10879647689`
- Artifact SHA-256: `bc53e3255ac12c2e99d62a5ef189c60fe26f1deb6e1c67178f043cc296546bbe`
- Observation time: 2026-09-25T17:49:58Z to 2026-09-25T17:51:30Z
- Network: Polygon PoS Mainnet
- Chain ID: **137**
- Observation block: **94,435,638**

## P1 acceptance result

The reconciliation artifact classifies the run as:

`evidence_state = VERIFIED`

Verified conditions:

- exact canonical target set: **11 / 11**
- successful independent code observations per target: **2 / 2 minimum**
- matching code hashes across the independent endpoints
- chain-ID quorum: **3 independent endpoints**, all 137
- head quorum: **3 endpoints**, all at block 94,435,638
- head span: **0**
- stale endpoints: **0**
- unresolved conflicts: **0**

## RPC endpoints providing P1 evidence

| Endpoint | Role in Run #30 | Chain ID | Block |
|---|---|---:|---:|
| OnFinality | code + identity/head | 137 | 94,435,638 |
| QuickNode public | code + identity/head | 137 | 94,435,638 |
| Tatum | code + identity/head | 137 | 94,435,638 |

Pool size was **14** candidates. Failed/restricted candidates remained evidence and were not promoted to trust.

## Critical target code hashes

The values below are SHA-256 hashes of the normalized `eth_getCode` result returned by the verifier.

| Address | Independent endpoints | Code hash |
|---|---|---|
| `0xA6FA4fB5f76172d178d61B04b0ecd319C5d1C0aa` | OnFinality, QuickNode | `6b04a39f665b7d962a18870154f19eeebf2238a6478b4a0910f84fe705fb5b63` |
| `0x7A8ed27F4C30512326878652d20fC85727401854` | OnFinality, QuickNode | `919480aa4e26f5a53b8e0622f7d8782c3a52573cf0548ebfa200fa8632dfae5f` |
| `0x0000000000000000000000000000000000001010` | QuickNode, Tatum | `4c153ecb6976f2ccc4a0509c8c0bd262ae2c53324a0c6d280ffd0b34f8ad5b90` |
| `0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270` | QuickNode, Tatum | `bc9d8ec4478c1503540ca838d6aad4ebef5ce00074c3415d4088c6baf40f21a0` |
| `0x0000000000000000000000000000000000001001` | QuickNode, Tatum | `c76c72eea1a11bd3b544b5b66e568f979dead59cea56cc628dc6693bfd931a94` |
| `0x0000000000000000000000000000000000001000` | QuickNode, Tatum | `2cd287491f21b69f7ff87e9a1237952ad0af11e0d3f5a6675d7eec38b9a39db3` |
| `0xD9c7C4ED4B66858301D0cb28Cc88bf655Fe34861` | QuickNode, Tatum | `357ae44411c9b433c7447e15420730890137ea7768a256e6ccd595b857e971e7` |
| `0x8cc8538d60901d19692F5ba22684732Bc28F54A3` | OnFinality, QuickNode | `93d08155ad6e44f6c64f94d84ea83c0cdba0165d4c54a7f490a51c985ef28bd3` |
| `0x8397259c983751DAf40400790063935a11afa28a` | OnFinality, QuickNode | `a02b93728beb8a661bb33f39f7fd8dee3862f8a8f0021ea7c830b807553822ce` |
| `0xEb1CD9e44aB6BfE5a55EE96c468086e51B1B873a` | OnFinality, QuickNode | `bc83efbb3771aa492491b45320b964808c6fd0367e23a59ee8d6cb3485007753` |
| `0xd1CD49A08AeF3Af93457aEc17C786C2b7F48eCd7` | OnFinality, QuickNode | `c2988fa533a6f75c2d732ba99060b1152d7f086952072a3c85e7ca36e06ef2dd` |

## Important boundary

This run verifies **current chain identity/head and runtime-code consistency** for the bounded 11-address P1 target set.

It does **not** by itself verify:

- proxy implementation slots;
- proxy admin;
- owner/roles;
- creation transaction/block;
- ABI/source identity;
- function/event behavior;
- current-vs-historical bridge classification.

Those remain P2 address/control verification work.

## Gate transition

- **P1 live infrastructure/code gate: PASSED**
- **Polygon saturation gate: OPEN**
- **P2 address/control/bridge census: NEXT**
- **DEX/protocol discovery: remains blocked until the remaining P2 gate is sufficiently reconciled.**
