# P2 External Creation / Control Provenance Candidates

Status: EXTERNAL / HISTORICAL CANDIDATE EVIDENCE ONLY
Rule: These records are not promoted to VERIFIED until reproduced from independent
on-chain RPC evidence or independently reconciled transaction data.

## 1. EIP1559Burn parent proxy
Address:
- 0x7A8ed27F4C30512326878652d20fC85727401854

External explorer observations:
- PolygonScan identifies the address as a contract with proxy source presentation.
- PolygonScan lists contract creator 0xF3378FEf...099Ac672F.
- PolygonScan constructor arguments identify:
  - logic = 0x1bd455C30ad8E2b8dF40df44A2eF923d67B33Feb
  - admin = 0x409834270b6F2591DD6c1e9f351E4194B112dA44
  - initialization data = empty
- Polygon's PIP-24 describes this address as the new EIP-1559 burn recipient and states that the temporary holder contract was intended to be owner-controlled for future upgrades.

Classification:
- constructor/admin relationship: EXTERNAL HISTORICAL CANDIDATE
- exact creation transaction/block: PENDING INDEPENDENT RECONCILIATION
- current owner/admin semantics: PENDING LIVE RPC PROBES

Sources:
- https://polygonscan.com/address/0x7A8ed27F4C30512326878652d20fC85727401854
- https://forum.polygon.technology/t/pip-24-change-eip-1559-policy/13007

## 2. sPOL parent proxy + derived admin
Parent:
- 0xd1CD49A08AeF3Af93457aEc17C786C2b7F48eCd7

Derived admin:
- 0xf68a9a2417a10e7d907a28b9876db8ad3dbbab7d

External transaction:
- tx = 0x5c28747a85e014b1ce0c35b5af88d577893cd6531b0523b7f64e5d82ba2e7c78
- PolygonScan shows a successful Create2 Factory transaction.
- The transaction created both the sPOL parent and 0xf68a... derived admin contract.
- Receipt events include:
  - parent Upgraded event with implementation 0x4F4814ebbb5cC578CC4d238Ca643E9DE131623E3
  - parent AdminChanged with new admin 0xf68a9a2417a10e7d907A28B9876db8AD3Dbbab7D
  - 0xf68a... OwnershipTransferred from zero address to 0x2c91c02793a50f6D55168a88183da687F572d350

Classification:
- creation transaction: HISTORICAL EXTERNAL CANDIDATE
- admin creation relationship: HISTORICAL EXTERNAL CANDIDATE
- ownership event: HISTORICAL EXTERNAL CANDIDATE
- current ownership/control: PENDING LIVE RPC RECONCILIATION

Source:
- https://polygonscan.com/tx/0x5c28747a85e014b1ce0c35b5af88d577893cd6531b0523b7f64e5d82ba2e7c78

## 3. sPOL current derived implementation
Address:
- 0x3C05A871E867FDE9a8364Fc8D38D97A7D42541c8

External creation record:
- creation tx = 0xa72eaebdc560af2fa6dad4d5b275b9205c1e20ec4c3413ca6bb0a3d7d65e434f
- creation block = 86086207
- timestamp = 2026-04-27 12:20:58 UTC
- creator = 0x11222a5d...1D285AA3A
- deployment surface = Create2 Factory
- verified contract name = sPOLChild
- constructor argument _stateSyncer = 0x0000000000000000000000000000000000001001

The published ABI also exposes authority(), childChainManager(), stateSyncer(),
and other read-only control/state surfaces.

Classification:
- creation transaction/block: HISTORICAL EXTERNAL CANDIDATE
- current runtime identity: ALSO SUBJECT TO P2 TWO-RPC LIVE GATE
- authority/control semantics: PENDING LIVE RPC PROBES

Source:
- https://polygonscan.com/address/0x3c05a871e867fde9a8364fc8d38d97a7d42541c8

## 4. EIP1559Burn derived implementation
Address:
- 0xae88570eb386a9c902488a6535f0957a46a68765

External creation provenance:
- Not yet independently located in this research pass.

Classification:
- creation transaction/block/deployer: UNKNOWN
- current runtime identity: P2 derived-code gate pending
- semantic role: PENDING

## 5. EIP1559Burn derived admin
Address:
- 0x409834270b6f2591dd6c1e9f351e4194b112da44

External historical context:
- Polygon forum discussion references this address as the ProxyAdmin for the EIP1559Burn proxy and states that emitted events identify its owner as 0x355b8E02e7F5301E6fac9b7cAc1D6D9c86C0343f.
- This is forum discussion / historical interpretation, not current live-chain verification.

Classification:
- ProxyAdmin role: EXTERNAL HISTORICAL CANDIDATE
- current owner: PENDING LIVE RPC owner() probe
- creation transaction: UNKNOWN

Source:
- https://forum.polygon.technology/t/pip-24-change-eip-1559-policy/13007

## Evidence boundary
External explorer/forum data is discovery input only.
No address in this document is promoted to VERIFIED from these sources alone.
