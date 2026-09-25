# P2 Derived Control Runtime Code — Verification Run 4

**Status:** VERIFIED  
**Observed block:** 94,439,097  
**Chain ID:** 137  
**Independent RPC observations:** 2 per target minimum  
**Reconciliation:** no conflicts, no incomplete targets

## Scope

The four ERC-1967-derived control addresses identified by the P2 storage run were checked for deployed runtime bytecode through independent Polygon RPC endpoints.

## Verified derived targets

| Derived address | Independent endpoints | Matching runtime-code hash |
|---|---|---|
| `0xae88570eb386a9c902488a6535f0957a46a68765` | OnFinality + QuickNode Public | `8af03072ee81785f1f9fe9349559b05dfd71019ca0e90a6fadb6ce3b5cb01aef` |
| `0x409834270b6f2591dd6c1e9f351e4194b112da44` | OnFinality + QuickNode Public | `f47c3e3430393ec3ab29fa7ba9b8993a3c1dd4637e3e08aa704dcba14e0a824e` |
| `0x3c05a871e867fde9a8364fc8d38d97a7d42541c8` | OnFinality + QuickNode Public | `211fb57c8df3bd36788186a0e64840044dc1f6ad58367af4544e1edbef970de4` |
| `0xf68a9a2417a10e7d907a28b9876db8ad3dbbab7d` | QuickNode Public + Tatum | `b7c973ba1e0eb0085357da3ae0d9f5bbbe3af4c0ccdbd5520bf4b7c66dc09aff` |

## Reconciliation result

- Target count: 4
- Successful independent observations per target: 2
- Matching: true for all targets
- Conflicts: 0
- Incomplete: 0
- Freshest observation block: 94,439,097
- Evidence class: live read-only runtime-code verification

This sub-gate is closed. Overall P2 remains open until the control-function and provenance sub-gates are also closed.
