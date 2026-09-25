# Polygon PoS Mainnet Profile

## सत्यापित आधारभूत तथ्य

| फ़ील्ड | स्थिति | मान | प्रमाण |
|---|---|---|---|
| नेटवर्क | VERIFIED | Polygon PoS Mainnet | Polygon Developer Docs |
| Chain ID | VERIFIED | 137 | Polygon Developer Docs |
| Native gas token | VERIFIED | POL | Polygon Developer Docs |
| Mainnet explorer | VERIFIED | PolygonScan | Polygon Developer Docs |
| Public RPC example | VERIFIED | Polygon documentation में mainnet RPC configuration उपलब्ध | Polygon Developer Docs |
| Execution model | VERIFIED | EVM-compatible smart-contract execution environment | Polygon Developer Docs / ecosystem documentation |
| Bor | VERIFIED | Polygon PoS node stack का execution component | Polygon Developer Docs |
| Heimdall | VERIFIED | Polygon PoS validator/checkpoint stack का component | Polygon Developer Docs |

## महत्वपूर्ण सीमा

ऊपर के तथ्य official documentation से research-level verified हैं। इन्हें अभी **live on-chain census** का substitute नहीं माना गया है।

इस फ़ोल्डर में निम्न data को अभी VERIFIED नहीं माना जाएगा जब तक live/on-chain evidence capture न हो:

- current block number
- exact current block time distribution
- finality latency distribution
- canonical system-contract address set
- active DEX contract set
- active factory/router/quoter/pool addresses
- token count
- tradable token count
- pair count
- pool count
- liquidity by venue/pool
- active flash-liquidity capacity
- live gas distribution
- live RPC latency/error distribution
- current MEV/orderflow surface
- strategy-level realized profitability

## Research interpretation

Polygon research का पहला objective केवल “कौन-कौन से protocols हैं” नहीं है। Objective है:

**हर economically relevant state surface को machine-readable, address-level, block-referenced, reproducible evidence में बदलना।**

इसलिए हर future record को static metadata + live on-chain verification + temporal freshness के साथ रखा जाएगा।

## Evidence sources

Primary source classes:

1. Polygon official developer documentation
2. Polygon mainnet RPC / node responses
3. PolygonScan / Etherscan Polygon POS indexed data
4. Protocol's official documentation
5. Protocol's verified on-chain contracts
6. Deployment transactions / creation bytecode
7. Event logs
8. Historical state snapshots
9. Independent secondary sources only for discovery, never as sole proof of an execution-critical address

## Initial verified references

- Polygon documentation states mainnet Chain ID 137, native currency POL, and PolygonScan as explorer in its mainnet setup guidance. 
- Polygon's node documentation identifies Bor and Heimdall as required components in the Polygon PoS node stack.
- PolygonScan exposes Polygon POS data for chain ID 137, including contracts, logs, tokens, transactions and block data.

## Next verification gate

Build a live Polygon evidence collector that can independently verify:

**chain identity → latest block → block/header fields → RPC health → contract code → ABI/source metadata → logs → deployment/creation evidence → protocol registries → pool state.**

No pair/protocol/strategy saturation claim is valid before this evidence layer exists.
